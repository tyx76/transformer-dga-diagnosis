#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Retrieval routing: intent classification, routing, hybrid retrieval, and body-aware reranking."""

from __future__ import annotations

import logging

from vector_kb.hybrid_retriever import hybrid_retrieve
from vector_kb.intent_classifier import classify_intent
from vector_kb.intent_router import route_intent

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
    """Route the intent and return body-aware hybrid retrieval results."""
    question = str(question or "").strip()
    if not question or top_k <= 0:
        return _empty_result({}, "empty")

    intent_result = classify_intent(question)
    _emit(trace, "意图识别", intent_result)
    if not isinstance(intent_result, dict):
        return _empty_result({}, "irrelevant")
    if intent_result.get("intent") == "irrelevant":
        return _empty_result(intent_result)

    route = route_intent(question, classification=intent_result)
    _emit(trace, "意图路由", route)
    if route.get("mode") == "refuse" or not route.get("domains"):
        return _empty_result(intent_result)

    hybrid_results = hybrid_retrieve(
        question,
        top_k=20,
        candidate_k=300,
        trace=trace,
        domains=route.get("domains"),
        intent=intent_result.get("intent"),
    )
    _emit(trace, "混合检索Top-K", hybrid_results[:5])

    merged = hybrid_results[:top_k]
    _emit(trace, "最终检索Top-K", merged)

    result = {
        "chunks": merged,
        "source": "hybrid",
        "intent": intent_result,
        "route": route,
        "hybrid_top5": hybrid_results[:5],
        "kb_top5": [],
        "llm_calls": 1 if intent_result.get("source") == "llm" else 0,
    }
    if shadow:
        LOGGER.info(
            "shadow retrieval: intent=%s source=%s hybrid=%s merged=%s",
            intent_result.get("intent"),
            result["source"],
            [item.get("clause") for item in result["hybrid_top5"]],
            [item.get("clause") for item in result["chunks"]],
        )
    return result


__all__ = ["route_and_retrieve"]
