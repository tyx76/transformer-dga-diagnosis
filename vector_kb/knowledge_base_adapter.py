#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pure knowledge-base adapter for the main retrieval pipeline."""

from __future__ import annotations

import re
from typing import Any

try:
    import pure_kb
except Exception:  # pragma: no cover - handled by search_knowledge_base
    pure_kb = None

_DOC_RE = re.compile(
    r"^(?P<doc_id>(?:DL/T|GB/T|GB|IEC)\s*\d+(?:\s*-\s*\d{4})?)",
    re.IGNORECASE,
)
_RESULT_FIELDS = ("doc_id", "clause", "title", "text", "page", "citation", "score")


def _result_key(item: dict) -> tuple[str, str]:
    """Return the canonical deduplication key."""
    doc_id = str(item.get("doc_id") or "")
    clause = str(item.get("clause") or "")
    if doc_id or clause:
        return doc_id, clause
    return "CASE", str(item.get("citation") or item.get("title") or "")


def _parse_doc_id(citation: str) -> str | None:
    match = _DOC_RE.match(str(citation or "").strip())
    if not match:
        return None
    return re.sub(r"\s*-\s*", "-", match.group("doc_id")).strip()


def _normalize_score(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def adapt_chunk(raw: dict) -> dict | None:
    """Convert a pure_kb result into the standard chunk format.

    Returns ``None`` for the ``dp`` domain, which must not enter the main
    retrieval/generation pipeline.
    """
    if not isinstance(raw, dict):
        return None

    domain = str(raw.get("domain") or raw.get("module") or "").strip()
    if domain == "dp":
        return None

    chunk_id = str(raw.get("chunk_id") or raw.get("id") or "").strip()
    doc_id = str(raw.get("doc_id") or "").strip() or None
    clause = str(raw.get("clause") or "").strip() or None
    citation = str(raw.get("citation") or "").strip()

    if doc_id is None and citation:
        doc_id = _parse_doc_id(citation)

    if domain == "cases":
        doc_id = f"CASE:{chunk_id}" if chunk_id else "CASE"
        clause = chunk_id or clause

    title = str(raw.get("title") or "").strip() or (clause or "")
    text = str(raw.get("text") or "").strip()
    page = raw.get("page")
    score = _normalize_score(raw.get("score", 0.0))

    return {
        "doc_id": doc_id,
        "clause": clause,
        "title": title,
        "text": text,
        "page": page,
        "citation": citation,
        "score": score,
    }


def _normalize_filters(filters: dict | None) -> dict:
    """Pure_kb filters use scalar equality; normalize single-item lists."""
    normalized = {}
    for key, value in (filters or {}).items():
        if isinstance(value, (list, tuple)):
            if len(value) == 1:
                normalized[key] = value[0]
        else:
            normalized[key] = value
    return normalized


def _dedupe_standard_chunks(chunks: list[dict], keep: int | None = None) -> list[dict]:
    best: dict[tuple[str, str], dict] = {}
    for chunk in chunks:
        if not isinstance(chunk, dict) or chunk.get("clause") is None:
            continue
        key = _result_key(chunk)
        current = best.get(key)
        if current is None or _normalize_score(chunk.get("score")) > _normalize_score(current.get("score")):
            best[key] = chunk
    result = sorted(best.values(), key=lambda item: _normalize_score(item.get("score")), reverse=True)
    return result[:keep] if keep is not None else result

def search_knowledge_base(question: str, route: dict, top_k: int = 20) -> list[dict]:
    """Call pure_kb.search with explicit domains and return standard chunks."""
    if pure_kb is None or not isinstance(route, dict):
        return []
    domains = list(route.get("domains") or [])
    if not domains or route.get("mode") == "refuse":
        return []
    filters = _normalize_filters(route.get("filters"))
    try:
        raw_results = pure_kb.search(
            query=question,
            domains=domains,
            filters=filters or None,
            top_k=max(1, int(top_k)),
        )
    except Exception:
        return []

    chunks = []
    for raw in raw_results or []:
        chunk = adapt_chunk(raw)
        if chunk is not None:
            chunks.append(chunk)
    return _dedupe_standard_chunks(chunks, keep=max(1, int(top_k)))


def _rrf_merge(hybrid_results: list[dict], kb_results: list[dict], top_k: int, k: int = 60, w_hybrid: float = 1.0, w_kb: float = 1.0) -> list[dict]:
    hybrid = _dedupe_standard_chunks([c for c in hybrid_results if isinstance(c, dict)])
    kb = _dedupe_standard_chunks([c for c in kb_results if isinstance(c, dict)])

    scores: dict[tuple[str, str], float] = {}
    documents: dict[tuple[str, str], dict] = {}

    for index, item in enumerate(hybrid, start=1):
        key = _result_key(item)
        scores[key] = scores.get(key, 0.0) + float(w_hybrid) / (k + index)
        documents[key] = dict(item)

    for index, item in enumerate(kb, start=1):
        key = _result_key(item)
        scores[key] = scores.get(key, 0.0) + float(w_kb) / (k + index)
        if key not in documents:
            documents[key] = dict(item)
        else:
            for field in _RESULT_FIELDS:
                if not documents[key].get(field) and item.get(field):
                    documents[key][field] = item[field]

    ranked = sorted(scores, key=lambda key: scores[key], reverse=True)
    merged = []
    for key in ranked[:top_k]:
        item = dict(documents[key])
        item["score"] = round(scores[key], 6)
        merged.append(item)
    return merged


def merge_with_hybrid(hybrid_results: list[dict], kb_results: list[dict], top_k: int = 5, w_hybrid: float = 1.0, w_kb: float = 1.0) -> list[dict]:
    """Deduplicate and RRF-merge hybrid retrieval with pure_kb results."""
    if top_k <= 0:
        return []
    return _rrf_merge(hybrid_results or [], kb_results or [], int(top_k), k=60, w_hybrid=w_hybrid, w_kb=w_kb)


__all__ = ["adapt_chunk", "search_knowledge_base", "merge_with_hybrid"]
