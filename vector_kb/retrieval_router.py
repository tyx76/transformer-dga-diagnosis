#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检索调度：串联意图分类、意图路由、hybrid 检索和配置知识库检索。"""

from __future__ import annotations

import logging

from vector_kb.hybrid_retriever import hybrid_retrieve
from vector_kb.intent_classifier import classify_intent
from vector_kb.intent_router import route_intent
from vector_kb.knowledge_base_adapter import merge_with_hybrid, search_knowledge_base

LOGGER = logging.getLogger(__name__)


def _emit(trace, step: str, payload) -> None:
    if trace is not None:
        trace(step, payload)


def _empty_result(intent_result: dict, source: str = "irrelevant") -> dict:
    return {
        "chunks": [],
        "source": source,
        "intent": intent_result,
        "route": None,
        "hybrid_top5": [],
        "kb_top5": [],
        "llm_calls": 1 if intent_result.get("source") == "llm" else 0,
    }


def route_and_retrieve(question: str, top_k: int = 5, shadow: bool = True, trace=None) -> dict:
    """执行意图识别与路由，分别调用 hybrid_retrieve 和 search_knowledge_base，并按空结果分支融合。"""
    question = str(question or "").strip()
    if not question or top_k <= 0:
        return _empty_result({}, "empty")

    # 1. 意图识别：irrelevant 直接返回空结果。
    intent_result = classify_intent(question)
    _emit(trace, "意图识别", intent_result)
    if not isinstance(intent_result, dict):
        return _empty_result({}, "irrelevant")

    if intent_result.get("intent") == "irrelevant":
        return _empty_result(intent_result)

    # 2. 领域路由：生成 domains/filters/mode。
    route = route_intent(question, classification=intent_result)
    _emit(trace, "意图路由", route)
    if route.get("mode") == "refuse" or not route.get("domains"):
        return _empty_result(intent_result)

    # 3. 两路检索：hybrid 负责向量 + BM25 + RRF，知识库适配器读取所选后端。
    hybrid_results = hybrid_retrieve(question, top_k=20, trace=trace)
    _emit(trace, "混合检索Top-K", hybrid_results[:5])

    kb_results = search_knowledge_base(question, route=route, top_k=20)
    _emit(trace, "知识库检索Top-K", kb_results[:5])

    # 4. 空结果分支：知识库为空时回退纯 hybrid，hybrid 为空时只使用知识库。
    if not kb_results:
        merged = hybrid_results[:top_k]
        source = "hybrid"
    elif not hybrid_results:
        merged = kb_results[:top_k]
        source = "kb"
    else:
        merged = merge_with_hybrid(hybrid_results, kb_results, top_k=top_k)
        source = "hybrid+kb"

    _emit(trace, "最终检索Top-K", merged)
    result = {
        "chunks": merged,
        "source": source,
        "intent": intent_result,
        "route": route,
        "hybrid_top5": hybrid_results[:5],
        "kb_top5": kb_results[:5],
        "llm_calls": 1 if intent_result.get("source") == "llm" else 0,
    }
    if shadow:
        LOGGER.info(
            "shadow retrieval: intent=%s source=%s hybrid=%s kb=%s merged=%s",
            intent_result.get("intent"),
            source,
            [item.get("clause") for item in result["hybrid_top5"]],
            [item.get("clause") for item in result["kb_top5"]],
            [item.get("clause") for item in result["chunks"]],
        )
    return result


__all__ = ["route_and_retrieve"]