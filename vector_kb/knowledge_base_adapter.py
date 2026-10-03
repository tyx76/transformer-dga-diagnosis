#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知识库适配层：统一 pure_kb/plant_kb 公开接口，转换为标准 chunk 格式。"""

from __future__ import annotations

import importlib
import logging
import os
import re
import sys
from typing import Any

LOGGER = logging.getLogger(__name__)


def _debug_enabled() -> bool:
    return "--debug" in sys.argv[1:]
# 支持的知识库后端。
_VALID_BACKENDS = ("pure_kb", "plant_kb")
# 默认保持旧后端；knowledge base 正式落位并验证后再切换默认值。
_REQUESTED_BACKEND = os.getenv("KB_BACKEND", "pure_kb").strip().lower()
_DOC_RE = re.compile(
    r"^(?P<doc_id>(?:DL/T|GB/T|GB|IEC)\s*\d+(?:\s*-\s*\d{4})?)",
    re.IGNORECASE,
)
_RESULT_FIELDS = ("doc_id", "clause", "title", "text", "page", "citation", "score", "citation_eligible")

# The legacy pure_kb backend still exposes the old six-domain taxonomy.
# Translate the current router domains at the adapter boundary so the main
# pipeline can keep a single seven-domain contract.
_PURE_KB_DOMAINS = {"dga", "oil_temp", "safety", "equipment", "dp", "cases"}

_BACKEND_DOMAIN_ALIASES = {
    "pure_kb": {
        "transformer_dga": ("dga",),
        "auxiliary": ("oil_temp", "equipment"),
        "standards_safety": ("safety",),
        "fault_cases": ("cases",),
    },
}


def _load_backend(name: str):
    """导入指定后端；导入失败时回退到另一个可用后端。"""
    if name not in _VALID_BACKENDS:
        raise ValueError(
            f"KB_BACKEND={name!r} 无效，可选值为：{', '.join(_VALID_BACKENDS)}"
        )

    try:
        return importlib.import_module(name), name
    except Exception as exc:
        LOGGER.warning("知识库后端 %s 导入失败：%s", name, exc)
        fallback = "plant_kb" if name == "pure_kb" else "pure_kb"
        try:
            module = importlib.import_module(fallback)
            LOGGER.warning("已回退到知识库后端 %s", fallback)
            return module, fallback
        except Exception as fallback_exc:
            raise RuntimeError(
                f"知识库后端全部不可用：{name} 和 {fallback} 均导入失败"
            ) from fallback_exc


kb_backend, _BACKEND_NAME = _load_backend(_REQUESTED_BACKEND)


def get_backend_name() -> str:
    """返回实际加载成功的后端名称。"""
    return _BACKEND_NAME


def get_backend_stats() -> dict:
    """返回当前后端统计信息；读取失败时返回空字典。"""
    if kb_backend is None:
        return {}
    try:
        return dict(kb_backend.stats())
    except Exception:
        LOGGER.exception("读取知识库统计失败：backend=%s", _BACKEND_NAME)
        return {}


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
    """Convert a backend result into the standard chunk format."""
    if not isinstance(raw, dict):
        return None

    domain = str(raw.get("domain") or raw.get("module") or "").strip()
    if domain == "dp":
        return None

    chunk_id = str(raw.get("chunk_id") or raw.get("id") or "").strip()
    doc_id = str(raw.get("doc_id") or raw.get("source_file") or "").strip() or None
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

    citation_eligible = bool(doc_id and clause)
    return {
        "doc_id": doc_id,
        "clause": clause,
        "title": title,
        "text": text,
        "page": page,
        "citation": citation,
        "score": score,
        "citation_eligible": citation_eligible,
    }


def _normalize_filters(filters: dict | None) -> dict:
    """Normalize single-item list filters to the scalar form used by KBs."""
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
        if not isinstance(chunk, dict):
            continue
        key = _result_key(chunk)
        current = best.get(key)
        if current is None or _normalize_score(chunk.get("score")) > _normalize_score(current.get("score")):
            best[key] = chunk
    result = sorted(best.values(), key=lambda item: _normalize_score(item.get("score")), reverse=True)
    return result[:keep] if keep is not None else result


def _resolve_backend_domains(domains: list[str]) -> list[str]:
    """Translate router domains to the configured backend taxonomy."""
    aliases = _BACKEND_DOMAIN_ALIASES.get(_BACKEND_NAME, {})
    resolved: list[str] = []
    for domain in domains:
        for candidate in aliases.get(domain, (domain,)):
            if _BACKEND_NAME == "pure_kb" and candidate not in _PURE_KB_DOMAINS:
                continue
            if candidate and candidate not in resolved:
                resolved.append(candidate)
    return resolved


def search_knowledge_base(question: str, route: dict, top_k: int = 20) -> list[dict]:
    """Call the configured backend with explicit domains and return chunks."""
    if not isinstance(route, dict):
        return []
    domains = _resolve_backend_domains(list(route.get("domains") or []))
    if not domains or route.get("mode") == "refuse":
        return []
    filters = _normalize_filters(route.get("filters"))
    try:
        raw_results = kb_backend.search(
            query=question,
            domains=domains,
            filters=filters or None,
            top_k=max(1, int(top_k)),
        )
    except Exception:
        LOGGER.exception("知识库检索失败：backend=%s", _BACKEND_NAME)
        return []

    chunks = []
    for raw in raw_results or []:
        chunk = adapt_chunk(raw)
        if chunk is not None:
            chunks.append(chunk)
    result = _dedupe_standard_chunks(chunks, keep=max(1, int(top_k)))
    eligible = sum(1 for chunk in result if chunk.get("citation_eligible"))
    if _debug_enabled():
        print(
            f"[引用资格] eligible={eligible} ineligible={len(result) - eligible}",
            flush=True,
        )
    return result


def _rrf_merge(
    hybrid_results: list[dict],
    kb_results: list[dict],
    top_k: int,
    k: int = 60,
    w_hybrid: float = 1.0,
    w_kb: float = 1.0,
) -> list[dict]:
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
        if "citation_eligible" not in item:
            item["citation_eligible"] = bool(item.get("doc_id") and item.get("clause"))
        else:
            item["citation_eligible"] = bool(item.get("citation_eligible"))
        merged.append(item)
    return merged


def merge_with_hybrid(
    hybrid_results: list[dict],
    kb_results: list[dict],
    top_k: int = 5,
    w_hybrid: float = 1.0,
    w_kb: float = 1.0,
) -> list[dict]:
    """Deduplicate and RRF-merge hybrid retrieval with KB results."""
    if top_k <= 0:
        return []
    return _rrf_merge(
        hybrid_results or [],
        kb_results or [],
        int(top_k),
        k=60,
        w_hybrid=w_hybrid,
        w_kb=w_kb,
    )


__all__ = [
    "adapt_chunk",
    "search_knowledge_base",
    "merge_with_hybrid",
    "get_backend_name",
    "get_backend_stats",
]