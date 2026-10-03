#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""规则优先、LLM 兜底的意图分类器。"""

from __future__ import annotations

import json
import os
import re
import unicodedata
import urllib.error
import urllib.request
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
RULES_DEFAULT = PROJECT_ROOT / "data" / "rules" / "intent_rules.json"

_SUBSCRIPT_DIGITS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
_INTENT_ORDER = ("boiler", "turbine", "generator", "auxiliary", "safety", "transformer", "irrelevant")
VALID_INTENTS = set(_INTENT_ORDER)
_INTENT_PROMPT = (
    "锅炉(boiler)：锅炉本体、水冷壁、过热器、再热器、省煤器、空预器、磨煤机、制粉系统、燃烧器；"
    "汽轮机(turbine)：汽轮机本体、通流、级组、转子、轴承、轴系、轴封、凝汽器、DEH、调速、旁路；"
    "发电机(generator)：发电机本体、定子、转子、励磁、氢冷、密封油、绝缘、局放；"
    "辅机(auxiliary)：风机、给水泵、循环水泵、油系统、冷却系统；"
    "安全操作(safety)：停机、停运、停电、隔离、检修、紧急处置；"
    "变压器(transformer)：变压器本体、DGA、油色谱、乙炔、氢气、总烃、三比值、注意值；"
    "无关问题(irrelevant)：与电厂设备诊断无关的问题"
)
_INTENT_ALIASES = {
    "锅炉": "boiler",
    "汽轮机": "turbine",
    "发电机": "generator",
    "辅机": "auxiliary",
    "安全操作": "safety",
    "安全": "safety",
    "变压器": "transformer",
    "无关问题": "irrelevant",
    "无关": "irrelevant",
}
_DEEPSEEK_API_BASE = os.environ.get("DEEPSEEK_API_BASE", "https://api.deepseek.com")
_DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
_STRONG_FEATURE_WORDS = (
    "乙炔",
    "氢气",
    "甲烷",
    "乙烯",
    "油温",
    "C2H2",
    "CH4",
    "H2",
    "停电",
    "停运",
    "限值",
    "注意值",
    "锅炉",
    "汽轮机",
    "发电机",
    "磨煤机",
    "减温水",
)


def _normalize(text: Any) -> str:
    """统一大小写、全半角、下标和空白，便于规则匹配。"""
    value = unicodedata.normalize("NFKC", str(text or ""))
    value = value.translate(_SUBSCRIPT_DIGITS).lower()
    return "".join(value.split())


@lru_cache(maxsize=1)
def _load_rules() -> dict:
    with RULES_DEFAULT.open("r", encoding="utf-8-sig") as stream:
        data = json.load(stream)
    if not isinstance(data.get("intents"), dict):
        raise ValueError(f"意图规则缺少 intents：{RULES_DEFAULT}")
    return data


def _match_keywords(question: str, keywords: list[str]) -> set[str]:
    """返回问题命中的规范化关键词集合。"""
    normalized_question = _normalize(question)
    matched: set[str] = set()
    for keyword in keywords:
        normalized_keyword = _normalize(keyword)
        if normalized_keyword and normalized_keyword in normalized_question:
            matched.add(normalized_keyword)
    return matched


def _confidence(hit_count: int, matched: set[str]) -> float:
    """按命中数分级计算单意图置信度。"""
    if hit_count >= 2:
        return 0.8
    if hit_count == 1:
        strong_words = {_normalize(word) for word in _STRONG_FEATURE_WORDS}
        return 0.7 if matched & strong_words else 0.4
    return 0.0


def _single_result(intent: str, confidence: float) -> dict:
    return {
        "intent": intent,
        "confidence": round(float(confidence), 6),
        "source": "rule",
    }


def _multi_result(intents: list[str], rules: dict) -> dict:
    modules: list[str] = []
    for intent in intents:
        for module in rules["intents"][intent].get("modules") or []:
            if module not in modules:
                modules.append(module)
    return {
        "intent": "multi",
        "intents": intents,
        "confidence": 0.8,
        "modules": modules,
        "source": "rule",
    }

def rule_classify(question: str) -> dict | None:
    """识别单意图或多意图；仅使用规则表，不调用 LLM。"""
    question = str(question or "").strip()
    if not question:
        return None

    rules = _load_rules()
    intents = rules["intents"]
    matches: dict[str, set[str]] = {}

    for intent, config in intents.items():
        matched = _match_keywords(question, list(config.get("keywords") or []))
        if matched:
            matches[intent] = matched

    if not matches:
        return None

    ranked = sorted(
        matches,
        key=lambda intent: (
            len(matches[intent]),
            int(intents[intent].get("priority") or 0),
        ),
        reverse=True,
    )

    if len(ranked) >= 2:
        return _multi_result(ranked, rules)

    best_intent = ranked[0]
    if best_intent == "general_plant" and matches[best_intent]:
        confidence = 0.7
    else:
        confidence = _confidence(len(matches[best_intent]), matches[best_intent])
    if confidence < 0.5:
        return None
    return _single_result(best_intent, confidence)


def _load_api_key() -> str:
    """从环境变量或项目 .env 读取 DeepSeek API Key。"""
    key = os.getenv("DEEPSEEK_API_KEY")
    if key:
        return key.strip()
    for path in (PROJECT_ROOT / ".env", ROOT / ".env"):
        if not path.exists():
            continue
        try:
            for line in path.read_text(encoding="utf-8-sig").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, value = line.split("=", 1)
                if name.strip() == "DEEPSEEK_API_KEY":
                    return value.strip().strip("'").strip('"')
        except Exception:
            pass
    return ""


def _extract_intent(content: str) -> str | None:
    """从模型响应中提取唯一合法意图。"""
    normalized = unicodedata.normalize("NFKC", str(content or "")).strip().lower()
    normalized = normalized.strip("`\"'。.!！:：")
    if normalized in VALID_INTENTS:
        return normalized
    if normalized in _INTENT_ALIASES:
        return _INTENT_ALIASES[normalized]
    tokens = re.findall(r"[a-z_]+", normalized)
    matches = [token for token in tokens if token in VALID_INTENTS]
    return matches[0] if len(matches) == 1 else None


def llm_classify(question: str) -> dict:
    """调用 DeepSeek 做意图兜底，只允许返回预定义类别。"""
    question = str(question or "").strip()
    fallback = {"intent": "irrelevant", "confidence": 0.3, "source": "llm"}
    if not question:
        return fallback

    key = _load_api_key()
    if not key:
        raise RuntimeError("未找到 DEEPSEEK_API_KEY，无法执行 LLM 意图兜底")

    categories = _INTENT_PROMPT
    prompt = (
        f"判断以下问题属于哪个意图类别：{categories}。"
        f"只返回类别名称。\n问题：{question}"
    )
    payload = {
        "model": _DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 20,
    }
    request = urllib.request.Request(
        f"{_DEEPSEEK_API_BASE}/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"DeepSeek 意图分类失败（HTTP {exc.code}）") from exc
    except Exception as exc:
        raise RuntimeError(f"DeepSeek 意图分类失败：{exc}") from exc

    intent = _extract_intent(content)
    if intent is None:
        return fallback
    return {"intent": intent, "confidence": 0.6, "source": "llm"}


def classify_intent(question: str) -> dict:
    """规则优先；规则无法判断时才调用 LLM。"""
    result = rule_classify(question)
    if result is not None:
        return result
    return llm_classify(question)


__all__ = ["rule_classify", "llm_classify", "classify_intent", "VALID_INTENTS"]
