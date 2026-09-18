#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Retrieval routing scheduler.

This module connects intent classification, pure knowledge-base retrieval and
the existing hybrid retrieval path. It does not modify the main workflow.
"""

from __future__ import annotations

import logging

from vector_kb.hybrid_retriever import hybrid_retrieve
from vector_kb.intent_classifier import classify_intent
from vector_kb.intent_router import route_intent
from vector_kb.knowledge_base_adapter import merge_with_hybrid, search_knowledge_base

LOGGER = logging.getLogger(__name__)


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
    """Route a query and combine pure_kb with the existing hybrid retriever.

    ``shadow=True`` still executes the complete comparison path. The caller is
    responsible for using ``chunks`` only when running in non-shadow mode.
    """
    question = str(question or "").strip()
    if not question or top_k <= 0:
        return _empty_result({}, "empty")

    intent_result = classify_intent(question)
    if not isinstance(intent_result, dict):
        return _empty_result({}, "irrelevant")

    if intent_result.get("intent") == "irrelevant":
        return _empty_result(intent_result)

    route = route_intent(question, classification=intent_result)
    if route.get("mode") == "refuse" or not route.get("domains"):
        return _empty_result(intent_result)

    hybrid_results = hybrid_retrieve(question, top_k=20, trace=trace)
    kb_results = search_knowledge_base(question, route=route, top_k=20)

    if not kb_results:
        merged = hybrid_results[:top_k]
        source = "hybrid"
    elif not hybrid_results:
        merged = kb_results[:top_k]
        source = "kb"
    else:
        merged = merge_with_hybrid(hybrid_results, kb_results, top_k=top_k)
        source = "hybrid+kb"

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