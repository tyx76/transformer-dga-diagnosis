#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成层：把检索条文组织成上下文，并调用 DeepSeek 生成带引用答案。"""

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEEPSEEK_API_BASE = os.environ.get("DEEPSEEK_API_BASE", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
SYSTEM_PROMPT = (
    "你是电力变压器故障诊断专家。请严格基于提供的规程条文回答。"
    "每条结论必须标注依据，格式为【依据：doc_id 第clause条】。"
    "如果条文无法回答问题，直接回复“资料未覆盖”，不要编造。"
    "不要给出规程之外的处置建议。"
)


def _load_env():
    """读取 DEEPSEEK_API_KEY：优先环境变量，其次项目根目录/.env。"""
    key = os.getenv("DEEPSEEK_API_KEY")
    if key:
        return key.strip()
    for cand in (ROOT / ".env", ROOT.parent / ".env"):
        if not cand.exists():
            continue
        try:
            for line in cand.read_text(encoding="utf-8-sig").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k.strip() == "DEEPSEEK_API_KEY":
                    return v.strip().strip('"').strip("'")
        except Exception:
            pass
    return ""


def _cite(doc_id, clause):
    """根据条号格式生成引用文本，不硬编码具体标准和条款。"""
    doc = str(doc_id or "").strip()
    c = str(clause or "").strip()
    if not c:
        return doc
    if c[0].isdigit():
        return f"{doc} 第{c}条" if re.fullmatch(r"[0-9.]+", c) else f"{doc} 第{c}"
    return f"{doc} {c}"


def build_context(chunks: list[dict]) -> str:
    """把 retrieve() 返回的条文拼成参考上下文。"""
    parts = []
    for chunk in chunks or []:
        doc = chunk.get("doc_id") or ""
        clause = chunk.get("clause") or ""
        text = str(chunk.get("text") or "").strip()
        parts.append(f"【依据：{_cite(doc, clause)}】{text}")
    return "\n\n".join(parts)


def generate(question: str, chunks: list[dict]) -> str:
    """基于检索条文调用 DeepSeek 生成回答。

    - chunks 为空时不调用 API，直接返回“资料未覆盖，无法回答”。
    - API Key 缺失或调用失败时抛出 RuntimeError。
    """
    if not chunks:
        return "资料未覆盖，无法回答"
    context = build_context(chunks)
    key = _load_env()
    if not key:
        raise RuntimeError("未找到 DEEPSEEK_API_KEY（请设置环境变量或写入项目根目录 .env）")
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"参考条文：\n{context}\n\n问题：{question}"},
        ],
        "temperature": 0.1,
        "max_tokens": 800,
    }
    req = urllib.request.Request(
        f"{DEEPSEEK_API_BASE}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        hint = {
            400: "请求参数有误（检查模型名与消息格式）",
            401: "API Key 无效或未设置，请检查 DEEPSEEK_API_KEY（注意不要用占位符 sk-...）",
            402: "账户余额不足，请到 platform.deepseek.com 充值后重试",
            403: "无权访问该模型或接口（检查账号权限）",
            404: "接口地址不存在（检查 DEEPSEEK_API_BASE 是否指向 https://api.deepseek.com）",
            422: "请求格式不被接受（检查 messages 结构）",
            429: "调用频率或额度超限，请稍后重试",
            500: "DeepSeek 服务端错误，请稍后重试",
            502: "DeepSeek 网关错误，请稍后重试",
            503: "DeepSeek 服务暂时不可用，请稍后重试",
        }.get(e.code, "未知 HTTP 错误")
        raise RuntimeError(f"DeepSeek API 调用失败（HTTP {e.code}）：{hint}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"无法连接 DeepSeek API（网络/代理问题）：{e.reason}") from e
    except Exception as e:
        raise RuntimeError(f"DeepSeek API 调用失败：{e}") from e
    try:
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        raise RuntimeError(f"DeepSeek 返回格式异常：{data}") from e