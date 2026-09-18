#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""混合检索入口：向量检索 + BM25 + RRF 融合。"""

from __future__ import annotations

from collections.abc import Callable

from vector_kb.bm25_retriever import bm25_retrieve
from vector_kb.domain_guard import is_in_domain
from vector_kb.retrieval import retrieve
from vector_kb.rrf_fusion import rrf_fusion

TraceCallback = Callable[[str, list[dict]], None]


def hybrid_retrieve(
    question: str,
    top_k: int = 3,
    candidate_k: int = 10,
    rrf_k: int = 60,
    trace: TraceCallback | None = None,
) -> list[dict]:
    """获取两路候选并经 RRF 融合；``trace`` 仅用于可选的调试观测。"""
    question = str(question or "").strip()
    if not question or not is_in_domain(question):
        return []

    try:
        candidates = max(1, int(candidate_k))
    except (TypeError, ValueError):
        candidates = 10

    vector_results = retrieve(question, top_k=candidates)
    if trace is not None:
        trace("向量检索Top-K", vector_results)

    bm25_results = bm25_retrieve(question, top_k=candidates)
    if trace is not None:
        trace("BM25检索Top-K", bm25_results)

    fused = rrf_fusion(
        vector_results,
        bm25_results,
        k=rrf_k,
        top_k=top_k,
    )
    if trace is not None:
        trace("RRF融合Top-K", fused)
    return fused


__all__ = ["hybrid_retrieve"]