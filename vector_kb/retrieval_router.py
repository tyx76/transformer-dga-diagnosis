#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Retrieval routing: intent classification, routing, hybrid retrieval, and body-aware reranking."""

from __future__ import annotations

import logging
import sys

from vector_kb.hybrid_retriever import hybrid_retrieve
from vector_kb.intent_classifier import classify_intent
from vector_kb.intent_router import route_intent

LOGGER = logging.getLogger(__name__)
ADJACENT_WEIGHT = 0.9


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
        "expanded": False,
        "expanded_domains": [],
        "llm_calls": 1 if intent_result.get("source") == "llm" else 0,
    }


def _debug_enabled(trace) -> bool:
    return trace is not None or "--debug" in sys.argv[1:]


def _debug(message: str) -> None:
    print(message, flush=True)


def _is_citation_eligible(item: dict) -> bool:
    """Keep compatibility with hybrid results that predate the metadata field."""
    if not isinstance(item, dict):
        return False
    value = item.get("citation_eligible")
    if value is None:
        return bool(item.get("doc_id") and item.get("clause"))
    return value is True


def _has_citable_top5(results: list[dict]) -> bool:
    return any(_is_citation_eligible(item) for item in (results or [])[:5])


def _result_key(item: dict) -> tuple[str, str, str]:
    return (
        str(item.get("doc_id") or ""),
        str(item.get("clause") or ""),
        str(item.get("citation") or item.get("title") or ""),
    )


def _score(item: dict) -> float | None:
    for field in ("score", "rrf_score"):
        value = item.get(field)
        try:
            if value is not None:
                return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _merge_expanded_results(
    primary: list[dict],
    expanded: list[dict],
    weight: float = ADJACENT_WEIGHT,
) -> list[dict]:
    """Merge expanded results without letting them outrank primary results."""
    primary_unique: list[dict] = []
    expanded_unique: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    for order, item in enumerate(primary or []):
        if not isinstance(item, dict):
            continue
        key = _result_key(item)
        if key in seen:
            continue
        seen.add(key)
        copy = dict(item)
        copy["expanded"] = False
        copy["expanded_weight"] = 1.0
        copy["_merge_order"] = order
        primary_unique.append(copy)

    for order, item in enumerate(expanded or []):
        if not isinstance(item, dict):
            continue
        key = _result_key(item)
        if key in seen:
            continue
        seen.add(key)
        copy = dict(item)
        copy["expanded"] = True
        copy["expanded_weight"] = weight
        base_score = _score(item)
        if base_score is not None:
            copy["original_score"] = base_score
            copy["score"] = base_score * weight
        copy["_merge_order"] = order
        expanded_unique.append(copy)

    combined = primary_unique + expanded_unique
    if combined:
        has_primary_score = any(_score(item) is not None for item in primary_unique)
        has_expanded_score = any(_score(item) is not None for item in expanded_unique)
        if has_primary_score or has_expanded_score:
            combined.sort(
                key=lambda item: (
                    -(_score(item) if _score(item) is not None else float("-inf")),
                    1 if item.get("expanded") else 0,
                    int(item.get("_merge_order") or 0),
                )
            )
    for item in combined:
        item.pop("_merge_order", None)
    return combined


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

    primary_domains = list(route.get("domains") or [])
    hybrid_results = hybrid_retrieve(
        question,
        top_k=20,
        candidate_k=300,
        trace=trace,
        domains=primary_domains,
        intent=intent_result.get("intent"),
    )
    _emit(trace, "混合检索Top-K", hybrid_results[:5])

    expanded = False
    expanded_domains: list[str] = []
    if not hybrid_results:
        trigger_reason = "主域无结果"
    elif not _has_citable_top5(hybrid_results):
        trigger_reason = "主域Top-5无citation_eligible=true"
    else:
        trigger_reason = ""

    adjacent_domains = list(route.get("adjacent_domains") or [])
    retry_domains = [domain for domain in adjacent_domains if domain not in primary_domains]
    if trigger_reason and retry_domains:
        expanded = True
        expanded_domains = retry_domains
        if _debug_enabled(trace):
            _debug(
                f"[扩域] 主域={primary_domains}, "
                f"相邻域={expanded_domains}, 触发原因={trigger_reason}"
            )
        expanded_results = hybrid_retrieve(
            question,
            top_k=20,
            candidate_k=300,
            trace=trace,
            domains=expanded_domains,
            intent=intent_result.get("intent"),
        )
        _emit(trace, "扩域检索Top-K", expanded_results[:5])
        hybrid_results = _merge_expanded_results(hybrid_results, expanded_results)

    merged = hybrid_results[:top_k]
    _emit(trace, "最终检索Top-K", merged)

    result = {
        "chunks": merged,
        "source": "hybrid",
        "intent": intent_result,
        "route": route,
        "hybrid_top5": hybrid_results[:5],
        "kb_top5": [],
        "expanded": expanded,
        "expanded_domains": expanded_domains,
        "llm_calls": 1 if intent_result.get("source") == "llm" else 0,
    }
    if shadow:
        LOGGER.info(
            "shadow retrieval: intent=%s source=%s expanded=%s expanded_domains=%s hybrid=%s merged=%s",
            intent_result.get("intent"),
            result["source"],
            result["expanded"],
            result["expanded_domains"],
            [item.get("clause") for item in result["hybrid_top5"]],
            [item.get("clause") for item in result["chunks"]],
        )
    return result


__all__ = ["route_and_retrieve"]
