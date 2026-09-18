#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""混合检索入口：向量检索 + BM25 + RRF 融合。"""

from __future__ import annotations

from vector_kb.bm25_retriever import bm25_retrieve
from vector_kb.retrieval import retrieve
from vector_kb.rrf_fusion import rrf_fusion


def hybrid_retrieve(
    question: str,
    top_k: int = 3,
    candidate_k: int = 10,
    rrf_k: int = 60,
) -> list[dict]:
    """并行获取两路候选，经 RRF 融合后返回最终 Top-K。"""
    question = str(question or "").strip()
    if not question:
        return []

    try:
        candidates = max(1, int(candidate_k))
    except (TypeError, ValueError):
        candidates = 10

    vector_results = retrieve(question, top_k=candidates)
    bm25_results = bm25_retrieve(question, top_k=candidates)
    return rrf_fusion(
        vector_results,
        bm25_results,
        k=rrf_k,
        top_k=top_k,
    )


__all__ = ["hybrid_retrieve"]