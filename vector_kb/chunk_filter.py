#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Body-aware filtering and ranking for retrieval results."""

from __future__ import annotations

import os
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
_OVERLAP_WEIGHT = 0.15


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


def _score_value(item: dict) -> float:
    """Read the original fusion score before falling back to a generic score."""
    for field in ("rrf_score", "score"):
        if item.get(field) is not None:
            value = _normalize_score(item.get(field))
            if value:
                return value
    return 0.0


def _result_key(item: dict) -> tuple[str, ...]:
    chunk_id = str(item.get("chunk_id") or item.get("id") or "").strip()
    if chunk_id:
        return ("chunk", chunk_id)
    doc_id = str(item.get("doc_id") or "")
    clause = str(item.get("clause") or "")
    if doc_id or clause:
        return ("doc", doc_id, clause)
    return ("case", str(item.get("citation") or item.get("title") or ""))


def _fill_missing_metadata(target: dict, source: dict) -> None:
    """Backfill optional metadata when a higher-scored duplicate lacks it."""
    for field in ("citation_eligible", "is_body", "citation", "page", "domain", "title"):
        if target.get(field) is None and source.get(field) is not None:
            target[field] = source.get(field)


def _dedupe(results: list[dict]) -> list[dict]:
    """Deduplicate while preserving input order and the highest-scored copy."""
    best: dict[tuple[str, ...], dict] = {}
    order: dict[tuple[str, ...], int] = {}
    for index, item in enumerate(results or []):
        if not isinstance(item, dict):
            continue
        key = _result_key(item)
        current = best.get(key)
        candidate = dict(item)
        if current is None:
            best[key] = candidate
            order[key] = index
        elif _score_value(item) > _score_value(current):
            _fill_missing_metadata(candidate, current)
            best[key] = candidate
            order[key] = index
        else:
            _fill_missing_metadata(current, candidate)
            order.setdefault(key, index)

    return [best[key] for key in sorted(best, key=lambda item: order[item])]


def _top_keys_with_doc_limit(
    ranked_keys: list[tuple[str, ...]],
    document_by_key: dict[tuple[str, ...], dict],
    base_scores: dict[tuple[str, ...], float],
    first_seen: dict[tuple[str, ...], int],
    limit: int,
) -> list[tuple[str, ...]]:
    """Select final keys while capping each non-empty doc_id at two entries.

    Legacy pure_kb keeps its historical behavior; the diversity limit targets
    the adapted plant_kb retrieval path where one source can occupy Top-5.
    """
    backend = os.getenv("KB_BACKEND", "plant_kb").strip().lower()
    if backend == "pure_kb":
        return ranked_keys[:limit]

    keys_by_doc_id: dict[str, list[tuple[str, ...]]] = {}
    for key in ranked_keys:
        doc_id = str(document_by_key[key].get("doc_id") or "").strip()
        if doc_id:
            keys_by_doc_id.setdefault(doc_id, []).append(key)

    allowed_keys: set[tuple[str, ...]] = set()
    for keys in keys_by_doc_id.values():
        best_keys = sorted(
            keys,
            key=lambda key: (-base_scores[key], first_seen[key]),
        )[:2]
        allowed_keys.update(best_keys)

    selected_keys: list[tuple[str, ...]] = []
    for key in ranked_keys:
        doc_id = str(document_by_key[key].get("doc_id") or "").strip()
        if doc_id and key not in allowed_keys:
            continue
        selected_keys.append(key)
        if len(selected_keys) >= limit:
            break

    return selected_keys


def prioritize_results(
    results: list[dict],
    question: str | None = None,
    top_k: int = 5,
    **kwargs: Any,
) -> list[dict]:
    """Rank primarily by RRF score, with a small body/query-overlap adjustment."""
    if question is None:
        question = kwargs.pop("query", None)
    if kwargs:
        raise TypeError(f"unexpected keyword arguments: {sorted(kwargs)}")
    if top_k <= 0:
        return []

    documents = _dedupe(results or [])
    if not documents:
        return []

    question_text = str(question or "")
    base_scores: dict[tuple[str, ...], float] = {}
    overlap_scores: dict[tuple[str, ...], int] = {}
    document_by_key: dict[tuple[str, ...], dict] = {}
    first_seen: dict[tuple[str, ...], int] = {}

    for index, item in enumerate(documents):
        key = _result_key(item)
        document_by_key[key] = dict(item)
        first_seen[key] = index
        base_score = _score_value(item)
        if base_score <= 0:
            # Preserve the legacy rank-based fallback for callers that pass
            # results without a fusion score.
            base_score = 1.0 / (60.0 + index + 1)
        base_scores[key] = base_score
        overlap_scores[key] = query_overlap(document_by_key[key], question_text)

    max_overlap = max(overlap_scores.values(), default=0)
    final_scores: dict[tuple[str, ...], float] = {}
    for key, item in document_by_key.items():
        body_weight = 1.0 if is_body_text(item) else 0.5
        normalized_overlap = (
            overlap_scores[key] / max_overlap
            if max_overlap > 0
            else 0.0
        )
        final_scores[key] = (
            base_scores[key]
            * body_weight
            * (1.0 + _OVERLAP_WEIGHT * normalized_overlap)
        )

    ranked_keys = sorted(
        final_scores,
        key=lambda key: (
            -final_scores[key],
            -base_scores[key],
            -overlap_scores[key],
            first_seen[key],
        ),
    )

    # RRF remains primary. For near-ties (within 6%), a materially higher
    # query overlap is allowed to break the tie so one weak overlap signal
    # cannot dominate the whole ranking.
    for index in range(1, len(ranked_keys)):
        previous = ranked_keys[index - 1]
        current = ranked_keys[index]
        previous_score = final_scores[previous]
        current_score = final_scores[current]
        if previous_score <= 0 or current_score < previous_score * 0.94:
            continue
        if overlap_scores[current] > overlap_scores[previous] * 1.2:
            ranked_keys[index - 1], ranked_keys[index] = current, previous

    output: list[dict] = []
    for key in _top_keys_with_doc_limit(
        ranked_keys,
        document_by_key,
        base_scores,
        first_seen,
        int(top_k),
    ):
        item = dict(document_by_key[key])
        item["rrf_score"] = round(base_scores[key], 12)
        item["score"] = round(final_scores[key], 6)
        output.append(item)
    return output


__all__ = ["is_body_text", "query_overlap", "prioritize_results"]
