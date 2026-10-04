#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RRF（倒数排序融合）模块。

将向量检索和 BM25 检索的排名结果按 ``(doc_id, clause)`` 联合键融合，
避免不同文档中的同名条号在去重时互相覆盖。RRF 只依赖排名，不需要对
余弦分数和 BM25 分数做额外归一化。
"""

from __future__ import annotations

from typing import Any


def _clause_key(item: dict[str, Any]) -> str:
    """兼容旧调用：返回单独的 clause 字符串。"""
    clause = item.get("clause")
    if clause is None:
        return ""
    return str(clause).strip()


def _result_key(item: dict[str, Any]) -> tuple[str, ...] | None:
    """返回融合去重键，优先使用 ``(doc_id, clause)``。"""
    doc_id = str(item.get("doc_id") or "").strip()
    clause = str(item.get("clause") or "").strip()

    if doc_id:
        return ("doc", doc_id, clause)
    if clause:
        source = str(
            item.get("source")
            or item.get("citation")
            or item.get("title")
            or ""
        ).strip()
        return ("source", source, clause) if source else ("clause", clause)

    chunk_id = str(
        item.get("chunk_id")
        or item.get("id")
        or item.get("citation")
        or item.get("title")
        or item.get("text")
        or ""
    ).strip()
    if chunk_id:
        return ("chunk", chunk_id)
    return None


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
        去重并按 ``rrf_score`` 降序排列的条文列表。同一条文以
        ``(doc_id, clause)`` 为联合键；缺少 ``doc_id`` 时退回来源/块号。
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

    scores: dict[tuple[str, ...], float] = {}
    documents: dict[tuple[str, ...], dict[str, Any]] = {}
    seen_bm25: set[tuple[str, ...]] = set()

    # 先处理向量结果，保证相同联合键优先保留向量侧更完整的元数据。
    def fill_missing_metadata(target: dict[str, Any], source: dict[str, Any]) -> None:
        for field in ("citation_eligible", "is_body", "citation", "page", "domain", "title"):
            if target.get(field) is None and source.get(field) is not None:
                target[field] = source.get(field)

    for rank, item in enumerate(vector_results or [], start=1):
        if not isinstance(item, dict):
            continue
        key = _result_key(item)
        if key is None or key in documents:
            continue
        documents[key] = dict(item)
        scores[key] = scores.get(key, 0.0) + 1.0 / (smooth + rank)

    for rank, item in enumerate(bm25_results or [], start=1):
        if not isinstance(item, dict):
            continue
        key = _result_key(item)
        if key is None or key in seen_bm25:
            continue
        seen_bm25.add(key)
        if key not in documents:
            documents[key] = dict(item)
        else:
            fill_missing_metadata(documents[key], item)
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
            "citation": source.get("citation") or "",
            "domain": source.get("domain"),
            "citation_eligible": source.get("citation_eligible"),
            "is_body": source.get("is_body"),
            "rrf_score": scores[key],
        })
    return results


__all__ = ["rrf_fusion"]
