#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RRF（倒数排序融合）模块。

将向量检索和 BM25 检索的排名结果按条号融合。RRF 只依赖排名而不是两种
检索器的原始分数，因此不需要对余弦分数和 BM25 分数做额外归一化。
"""

from __future__ import annotations

from typing import Any


def _clause_key(item: dict[str, Any]) -> str:
    """返回用于去重的条号键；空条号不参与融合。"""
    clause = item.get("clause")
    if clause is None:
        return ""
    return str(clause).strip()


def rrf_fusion(
    vector_results: list[dict] | None,
    bm25_results: list[dict] | None,
    k: int = 60,
    top_k: int = 3,
) -> list[dict]:
    """融合两路检索结果并返回 Top-K。

    Args:
        vector_results: 向量检索结果，按相关性从高到低排列。
        bm25_results: BM25 检索结果，按相关性从高到低排列。
        k: RRF 平滑常数，默认 60。
        top_k: 最终返回条数，默认 3。

    Returns:
        去重并按 ``rrf_score`` 降序排列的条文列表。每项保留标准元数据，
        并新增 ``rrf_score`` 字段。两路输入均为空时返回空列表。
    """
    try:
        requested = int(top_k)
    except (TypeError, ValueError):
        return []
    if requested <= 0:
        return []

    try:
        smooth = float(k)
    except (TypeError, ValueError):
        smooth = 60.0
    smooth = max(0.0, smooth)

    scores: dict[str, float] = {}
    documents: dict[str, dict[str, Any]] = {}
    seen_bm25: set[str] = set()

    # 先处理向量结果，保证相同条号优先保留向量侧更完整的元数据。
    for rank, item in enumerate(vector_results or [], start=1):
        if not isinstance(item, dict):
            continue
        key = _clause_key(item)
        if not key or key in documents:
            continue
        documents[key] = item
        scores[key] = scores.get(key, 0.0) + 1.0 / (smooth + rank)

    for rank, item in enumerate(bm25_results or [], start=1):
        if not isinstance(item, dict):
            continue
        key = _clause_key(item)
        if not key or key in seen_bm25:
            continue
        seen_bm25.add(key)
        if key not in documents:
            documents[key] = item
        scores[key] = scores.get(key, 0.0) + 1.0 / (smooth + rank)

    if not scores:
        return []

    first_seen = {key: index for index, key in enumerate(scores)}
    ranked_keys = sorted(
        scores,
        key=lambda key: (-scores[key], first_seen[key]),
    )

    results: list[dict] = []
    for key in ranked_keys[:requested]:
        source = documents[key]
        results.append({
            "doc_id": source.get("doc_id"),
            "clause": source.get("clause"),
            "title": source.get("title") or "",
            "text": source.get("text") or "",
            "page": source.get("page"),
            "rrf_score": scores[key],
        })
    return results


__all__ = ["rrf_fusion"]