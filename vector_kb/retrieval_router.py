#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Retrieval routing: intent classification, routing, hybrid retrieval, and body-aware reranking."""

from __future__ import annotations

import logging
import re
import sys
import unicodedata

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
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "是"}
    return bool(value)


def _has_citable_top5(results: list[dict]) -> bool:
    return any(_is_citation_eligible(item) for item in (results or [])[:5])


def _normalize_source(value) -> str:
    """Normalize a source identifier for tolerant Top-5 source matching."""
    text = unicodedata.normalize("NFKC", str(value or "")).strip().lower()
    text = text.replace("\\", "/")
    text = re.sub(r"\.(?:md|txt|pdf|docx?|xlsx?)$", "", text)
    text = text.replace("预处理后_", "")
    return re.sub(r"[\s_\-—:：()（）\[\]【】,，。.;；]+", "", text)


def _iter_source_values(value):
    """Yield source identifiers from strings, dicts, and nested containers."""
    if value is None:
        return
    if isinstance(value, dict):
        preferred_keys = (
            "expected_sources",
            "expected_source",
            "expected_source_file",
            "source_file",
            "doc_id",
            "source",
            "title",
            "citation",
            "path",
        )
        yielded = False
        for key in preferred_keys:
            if key in value:
                yielded = True
                yield from _iter_source_values(value.get(key))
        if not yielded:
            for nested in value.values():
                yield from _iter_source_values(nested)
        return
    if isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _iter_source_values(item)
        return
    text = str(value or "").strip()
    if text:
        yield text


def _expected_sources(route: dict) -> list[str]:
    """Read optional expected-source metadata without changing router interfaces."""
    if not isinstance(route, dict):
        return []

    sources: list[str] = []
    containers = [
        route,
        route.get("classification"),
        route.get("filters"),
        route.get("slots"),
    ]
    for container in containers:
        if not isinstance(container, dict):
            continue
        for key in (
            "expected_sources",
            "expected_source",
            "expected_source_file",
            "source_file",
            "doc_id",
        ):
            for source in _iter_source_values(container.get(key)):
                if source not in sources:
                    sources.append(source)
    return sources


def _has_expected_source_top5(results: list[dict], expected_sources: list[str]) -> bool:
    normalized_expected = [
        _normalize_source(source) for source in (expected_sources or [])
    ]
    normalized_expected = [source for source in normalized_expected if source]
    if not normalized_expected:
        return True

    for item in (results or [])[:5]:
        if not isinstance(item, dict):
            continue
        candidate_parts = []
        for field in ("doc_id", "source_file", "title", "citation", "text"):
            candidate_parts.extend(_iter_source_values(item.get(field)))
        metadata = item.get("metadata")
        if isinstance(metadata, dict):
            candidate_parts.extend(_iter_source_values(metadata))

        for candidate in candidate_parts:
            normalized_candidate = _normalize_source(candidate)
            if not normalized_candidate:
                continue
            for expected in normalized_expected:
                if expected == normalized_candidate:
                    return True
                if min(len(expected), len(normalized_candidate)) >= 6 and (
                    expected in normalized_candidate or normalized_candidate in expected
                ):
                    return True
    return False


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


def _weight_domain_results(
    results: list[dict],
    primary_domains: list[str],
    adjacent_domains: list[str],
    weight: float = ADJACENT_WEIGHT,
) -> tuple[list[dict], dict[str, int]]:
    """Apply primary/adjacent weights to a combined-domain retrieval result."""
    primary = {
        str(domain).strip().lower()
        for domain in (primary_domains or [])
        if str(domain).strip()
    }
    adjacent = {
        str(domain).strip().lower()
        for domain in (adjacent_domains or [])
        if str(domain).strip()
    }
    adjacent_only = adjacent - primary
    weighted: list[dict] = []
    counts = {"primary": 0, "adjacent": 0}

    for order, item in enumerate(results or []):
        if not isinstance(item, dict):
            continue
        domain = str(item.get("domain") or "").strip().lower()
        is_adjacent = domain in adjacent_only
        record_weight = weight if is_adjacent else 1.0
        copy = dict(item)
        copy["domain_weight"] = record_weight
        copy["_domain_order"] = order
        if is_adjacent:
            for field in ("score", "rrf_score"):
                value = copy.get(field)
                try:
                    if value is None:
                        continue
                    value = float(value)
                except (TypeError, ValueError):
                    continue
                copy[f"original_{field}"] = value
                copy[field] = value * record_weight
        counts["adjacent" if is_adjacent else "primary"] += 1
        weighted.append(copy)

    if weighted:
        weighted.sort(
            key=lambda item: (
                -(_score(item) if _score(item) is not None else float("-inf")),
                int(item.get("_domain_order") or 0),
            )
        )
    for item in weighted:
        item.pop("_domain_order", None)
    return weighted, counts


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
        for field in ("score", "rrf_score"):
            value = item.get(field)
            try:
                if value is None:
                    continue
                base_value = float(value)
            except (TypeError, ValueError):
                continue
            copy[f"original_{field}"] = base_value
            copy[field] = base_value * weight
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

    primary_domains = list(dict.fromkeys(route.get("domains") or []))
    adjacent_domains = list(dict.fromkeys(route.get("adjacent_domains") or []))
    merged_domains = list(dict.fromkeys([*primary_domains, *adjacent_domains]))
    if _debug_enabled(trace):
        _debug(
            f"[检索域] 主域={primary_domains}, "
            f"相邻域={adjacent_domains}, 合并后={merged_domains}"
        )
    hybrid_results = hybrid_retrieve(
        question,
        top_k=20,
        candidate_k=300,
        trace=trace,
        domains=merged_domains,
        intent=intent_result.get("intent"),
    )
    hybrid_results, domain_counts = _weight_domain_results(
        hybrid_results,
        primary_domains,
        adjacent_domains,
    )
    if _debug_enabled(trace):
        _debug(
            f"[权重] 主域记录={domain_counts['primary']}条, "
            f"相邻域记录={domain_counts['adjacent']}条"
        )
    _emit(trace, "混合检索Top-K", hybrid_results[:5])

    expanded = False
    expanded_domains: list[str] = []
    expected_sources = _expected_sources(route)
    if not hybrid_results:
        trigger_reason = "主域无结果"
    elif not _has_citable_top5(hybrid_results):
        trigger_reason = "主域Top-5无citation_eligible=true"
    elif expected_sources and not _has_expected_source_top5(hybrid_results, expected_sources):
        expected_preview = "、".join(expected_sources[:2])
        trigger_reason = f"主域Top-5未命中期望来源({expected_preview})"
    else:
        trigger_reason = ""

    retry_domains = [domain for domain in adjacent_domains if domain not in primary_domains]
    if trigger_reason and retry_domains:
        expanded = True
        expanded_domains = retry_domains
        expanded_results = hybrid_retrieve(
            question,
            top_k=20,
            candidate_k=300,
            trace=trace,
            domains=adjacent_domains,
            intent=intent_result.get("intent"),
        )
        _emit(trace, "扩域检索Top-K", expanded_results[:5])
        if _debug_enabled(trace):
            _debug(
                f"[扩域] 主域={primary_domains}, "
                f"相邻域={adjacent_domains}, 触发原因={trigger_reason}, "
                f"扩域后结果数={len(expanded_results)}"
            )
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
