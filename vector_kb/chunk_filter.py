#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Body-aware filtering and ranking for retrieval results."""

from __future__ import annotations

import re
from typing import Any

_HEADING_START_RE = re.compile(
    r"^(?:第[一二三四五六七八九十百千万零0-9]+[章节篇]|[一二三四五六七八九十]+[、.]|[0-9]+(?:\.[0-9]+){0,3}[\s、.]?)"
)
_PUNCT_RE = re.compile(r"[。；，！？、,.!?;:\n]")
_ACTION_WORDS = (
    "应", "需", "必须", "检查", "处理", "发现", "导致",
    "原因", "建议", "更换", "调整", "运行", "采取", "防止",
    "启动", "停运", "超限", "泄漏", "温度",
)
_TITLE_TAIL_WORDS = (
    "原因分析", "概述", "技术改造", "缺陷描述",
    "处理措施", "检查情况", "处理过程", "安全措施",
    "目录", "前言", "范围", "术语和定义",
)


def _is_body_text(text: str, title: str = "", clause: str = "") -> bool:
    """Heuristically distinguish body chunks from heading/title chunks."""
    value = str(text or "").strip()
    compact = re.sub(r"\s+", "", value)
    if len(compact) < 20:
        return False
    heading_source = f"{clause or ''} {title or ''} {compact}"
    starts_like_heading = bool(_HEADING_START_RE.match(heading_source.strip()))
    has_action = any(word in compact for word in _ACTION_WORDS)
    has_punctuation = bool(_PUNCT_RE.search(value))
    if starts_like_heading and len(compact) < 60 and not has_action:
        return False
    if not has_punctuation and len(compact) < 40:
        return False
    if not has_action and not has_punctuation and len(compact) < 60:
        return False
    lines = [line.strip().lstrip("#").strip() for line in value.splitlines() if line.strip()]
    tail = lines[-1] if lines else compact
    if len(compact) < 100 and any(word in tail for word in _TITLE_TAIL_WORDS):
        return False
    if tail and len(tail) < 24 and any(word in tail for word in _TITLE_TAIL_WORDS):
        return False
    return True


def _query_features(query: str) -> set[str]:
    """Build simple CJK n-gram and alphanumeric features for overlap scoring."""
    normalized = re.sub(r"\s+", "", str(query or "").lower())
    features: set[str] = set()
    for run in re.findall(r"[\u4e00-\u9fff]+", normalized):
        if len(run) >= 2:
            features.add(run)
        for size in (2, 3, 4, 5):
            features.update(run[index:index + size] for index in range(max(0, len(run) - size + 1)))
    features.update(re.findall(r"[a-z0-9_.-]{2,}", normalized))
    return {feature for feature in features if feature}


def _query_overlap(query: str, item: dict) -> int:
    if not query or not isinstance(item, dict):
        return 0
    features = _query_features(query)
    if not features:
        return 0
    content = " ".join(
        str(item.get(field) or "")
        for field in ("doc_id", "clause", "title", "text")
    ).lower()
    return sum(len(feature) for feature in features if feature in content)


def _is_body_chunk(chunk: dict) -> bool:
    if not isinstance(chunk, dict):
        return False
    if "is_body" in chunk:
        return bool(chunk.get("is_body"))
    return _is_body_text(
        str(chunk.get("text") or ""),
        str(chunk.get("title") or ""),
        str(chunk.get("clause") or ""),
    )


def is_body_text(chunk: dict) -> bool:
    """Return whether a chunk is body text rather than a title-like block."""
    return _is_body_chunk(chunk)


def query_overlap(chunk: dict, question: str) -> int:
    """Return the existing weighted query-overlap score for a chunk."""
    return _query_overlap(question, chunk)


def _normalize_score(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _result_key(item: dict) -> tuple[str, str]:
    doc_id = str(item.get("doc_id") or "")
    clause = str(item.get("clause") or "")
    if doc_id or clause:
        return doc_id, clause
    return "CASE", str(item.get("citation") or item.get("title") or "")


def _dedupe(results: list[dict]) -> list[dict]:
    best: dict[tuple[str, str], dict] = {}
    for item in results:
        if not isinstance(item, dict):
            continue
        key = _result_key(item)
        current = best.get(key)
        if current is None or _normalize_score(item.get("score")) > _normalize_score(current.get("score")):
            best[key] = item
    return sorted(
        best.values(),
        key=lambda item: (1 if is_body_text(item) else 0, _normalize_score(item.get("score"))),
        reverse=True,
    )


def prioritize_results(
    results: list[dict],
    question: str | None = None,
    top_k: int = 5,
    **kwargs: Any,
) -> list[dict]:
    """Apply the existing body-first and query-overlap ranking to results."""
    if question is None:
        question = kwargs.pop("query", None)
    if kwargs:
        raise TypeError(f"unexpected keyword arguments: {sorted(kwargs)}")
    if top_k <= 0:
        return []

    documents = _dedupe(results or [])
    scores: dict[tuple[str, str], float] = {}
    document_by_key: dict[tuple[str, str], dict] = {}
    for index, item in enumerate(documents, start=1):
        key = _result_key(item)
        document_by_key[key] = dict(item)
        body_weight = 1.0 if is_body_text(item) else 0.5
        scores[key] = body_weight / (60.0 + index)

    ranked_keys = sorted(
        scores,
        key=lambda key: (
            1 if is_body_text(document_by_key[key]) else 0,
            query_overlap(document_by_key[key], question or ""),
            scores[key],
        ),
        reverse=True,
    )

    output: list[dict] = []
    for key in ranked_keys[: int(top_k)]:
        item = dict(document_by_key[key])
        item["score"] = round(scores[key], 6)
        output.append(item)
    return output


__all__ = ["is_body_text", "query_overlap", "prioritize_results"]
