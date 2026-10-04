#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""混合检索编排：按 KB_BACKEND 选择向量库和 BM25 数据源，执行向量 + BM25 + RRF。"""

from __future__ import annotations

import importlib
import logging
import os
from collections import Counter
from collections.abc import Callable
from pathlib import Path

from vector_kb.bm25_retriever import bm25_retrieve
from vector_kb.chunk_filter import prioritize_results
from vector_kb.domain_guard import is_in_domain
from vector_kb.intent_classifier import rule_classify
from vector_kb.query_expander import expand_query
from vector_kb.query_planner import plan_query
from vector_kb.retrieval import retrieve
from vector_kb.rrf_fusion import rrf_fusion

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGGER = logging.getLogger(__name__)
TraceCallback = Callable[[str, list[dict]], None]
_PATH_KEYS = ("vector_db", "bm25_corpus", "bm25_index")

BACKEND_CONFIG = {
    # 旧变压器/DGA 专项后端。
    "pure_kb": {
        "vector_db": "knowledge/pure_kb/index/knowledge.db",        # 旧库向量库路径
        "bm25_corpus": "knowledge/pure_kb/data/clauses.jsonl",      # 旧库 BM25 语料路径
        "bm25_index": "knowledge/pure_kb/index/bm25_index.pkl",     # 旧库 BM25 索引路径
        "embedding_source": None,                                   # 使用 vector_kb.embeddings.embed
    },
    # 通用电厂设备目标后端。
    "plant_kb": {
        "vector_db": "knowledge/plant_kb/index/knowledge.db",        # 新库向量库路径
        "bm25_corpus": "knowledge/plant_kb/data/knowledge.jsonl",   # 新库 BM25 语料路径
        "bm25_index": "knowledge/plant_kb/index/bm25_index.pkl",    # 新库 BM25 索引路径
        "embedding_source": None,                                   # ?? vector_kb.embeddings.embed
    },
}


def _validate_embedding_source(source, backend: str):
    """启动时校验显式 embedding 模块是否可导入并包含 embed/embed_texts。"""
    if source is None:
        return None
    if not isinstance(source, str) or not source.strip():
        raise RuntimeError(
            f"KB_BACKEND={backend} 的 embedding_source 无效：{source!r}"
        )
    try:
        module = importlib.import_module(source)
    except Exception as exc:
        raise RuntimeError(
            f"KB_BACKEND={backend} 无法导入 embedding_source={source}"
        ) from exc
    if not any(callable(getattr(module, name, None)) for name in ("embed", "embed_texts")):
        raise RuntimeError(
            f"KB_BACKEND={backend} 的 embedding_source={source} "
            "必须提供 embed 或 embed_texts 函数"
        )
    return source


for _backend, _config in BACKEND_CONFIG.items():
    _config["embedding_source"] = _validate_embedding_source(
        _config.get("embedding_source"),
        _backend,
    )


def _backend_name() -> str:
    # 默认后端为 plant_kb；KB_BACKEND=pure_kb 仅用于显式回退。
    name = os.getenv("KB_BACKEND", "plant_kb").strip().lower()
    if name not in BACKEND_CONFIG:
        raise ValueError(
            f"KB_BACKEND={name!r} 无效，可选值为：{', '.join(BACKEND_CONFIG)}"
        )
    return name


def _resolve_config(name: str) -> dict:
    config = BACKEND_CONFIG[name]
    resolved = {}
    for key, value in config.items():
        if key in _PATH_KEYS:
            resolved[key] = (PROJECT_ROOT / value).resolve()
        else:
            resolved[key] = value
    return resolved


def _ensure_placeholder(path: Path, label: str, backend: str) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
    print(
        f"[hybrid_retrieve] KB_BACKEND={backend} 缺少{label}，"
        f"已创建空占位文件：{path}"
    )


def _domain_lookup(vector_results: list[dict], bm25_results: list[dict]) -> dict[tuple[str, str], str]:
    lookup: dict[tuple[str, str], str] = {}
    for item in [*(vector_results or []), *(bm25_results or [])]:
        if not isinstance(item, dict) or not item.get("domain"):
            continue
        key = (str(item.get("doc_id") or ""), str(item.get("clause") or ""))
        lookup[key] = str(item["domain"])
    return lookup


def _ensure_domain_coverage(
    fused: list[dict],
    domains: list[str] | None,
    vector_results: list[dict],
    bm25_results: list[dict],
    top_k: int,
) -> list[dict]:
    allowed = [str(domain) for domain in (domains or []) if str(domain).strip()]
    if len(set(allowed)) <= 1:
        return fused[:top_k]

    lookup = _domain_lookup(vector_results, bm25_results)
    selected: list[dict] = []
    selected_keys: set[tuple[str, str]] = set()

    # Reserve the highest-ranked result from each requested domain first.
    for domain in dict.fromkeys(allowed):
        for item in fused:
            key = (str(item.get("doc_id") or ""), str(item.get("clause") or ""))
            item_domain = item.get("domain") or lookup.get(key)
            if item_domain != domain or key in selected_keys:
                continue
            copy = dict(item)
            copy["domain"] = domain
            selected.append(copy)
            selected_keys.add(key)
            break

    for item in fused:
        key = (str(item.get("doc_id") or ""), str(item.get("clause") or ""))
        if key in selected_keys:
            continue
        copy = dict(item)
        domain = lookup.get(key)
        if domain:
            copy["domain"] = domain
        selected.append(copy)
        selected_keys.add(key)
        if len(selected) >= top_k:
            break

    return selected[:top_k]


def _dual_result_key(item: dict) -> tuple[str, str]:
    doc_id = str(item.get("doc_id") or "")
    clause = str(item.get("clause") or "")
    if doc_id or clause:
        return (doc_id, clause)
    return ("CASE", str(item.get("citation") or item.get("title") or item.get("text") or ""))


def _dedupe_path_results(results: list[dict]) -> list[dict]:
    deduped: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for item in results or []:
        if not isinstance(item, dict):
            continue
        key = _dual_result_key(item)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _fill_missing_metadata(target: dict, source: dict) -> None:
    """Preserve optional metadata when one retrieval path lacks a field."""
    for field in ("citation_eligible", "is_body", "citation", "page", "domain", "title"):
        if target.get(field) is None and source.get(field) is not None:
            target[field] = source.get(field)


def _retrieve_path(
    query: str,
    *,
    domains: list[str] | None,
    top_k: int,
    candidate_k: int,
    rrf_k: int,
    config: dict,
    embedding_source,
    trace: TraceCallback | None,
    label: str,
) -> list[dict]:
    allowed_domains = [str(domain) for domain in (domains or []) if str(domain).strip()]
    domain_set = set(allowed_domains)
    fusion_k = top_k
    if len(domain_set) > 1:
        fusion_k = max(top_k, min(100, top_k * 5))

    vector_results = retrieve(
        query,
        top_k=candidate_k,
        db_path=config["vector_db"],
        embedding_source=embedding_source,
        domains=allowed_domains or None,
        debug=trace is not None,
    )
    if trace is not None:
        trace(f"向量检索Top-K({label})", vector_results[:10])

    bm25_results = bm25_retrieve(
        query,
        top_k=candidate_k,
        corpus_path=config["bm25_corpus"],
        index_path=config["bm25_index"],
        domains=allowed_domains or None,
        debug=trace is not None,
    )
    if trace is not None:
        trace(f"BM25检索Top-K({label})", bm25_results[:10])

    fused = rrf_fusion(
        vector_results,
        bm25_results,
        k=rrf_k,
        top_k=fusion_k,
    )
    if len(domain_set) > 1:
        fused = _ensure_domain_coverage(
            fused,
            allowed_domains,
            vector_results,
            bm25_results,
            top_k,
        )
    if trace is not None:
        trace(f"RRF融合Top-K({label})", fused[:10])

    return prioritize_results(fused, question=query, top_k=top_k)


_SCOPE_PRIORITY = {
    "device_specific": 0,
    "procedure": 1,
    "component_generic": 2,
    "instrument_generic": 3,
}
_SCOPE_METADATA_CACHE: dict[Path, tuple[tuple[int, int], dict[tuple[str, str], dict]]] = {}


def _scope_signature(path: Path) -> tuple[int, int]:
    try:
        stat = path.stat()
        return (stat.st_size, stat.st_mtime_ns)
    except OSError:
        return (0, 0)


def _load_scope_metadata(config: dict) -> dict[tuple[str, str], dict]:
    path = Path(config["vector_db"]).resolve().parent / "lightweight_metadata.jsonl"
    if not path.is_file():
        return {}
    signature = _scope_signature(path)
    cached = _SCOPE_METADATA_CACHE.get(path)
    if cached is not None and cached[0] == signature:
        return cached[1]

    metadata: dict[tuple[str, str], dict] = {}
    try:
        with path.open("r", encoding="utf-8-sig") as stream:
            for line in stream:
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                except Exception:
                    continue
                key = (str(item.get("doc_id") or ""), str(item.get("clause") or ""))
                metadata[key] = item
    except Exception:
        LOGGER.warning("Failed to load scope metadata: %s", path, exc_info=True)
        return {}
    _SCOPE_METADATA_CACHE[path] = (signature, metadata)
    return metadata


def _attach_scope(results: list[dict], config: dict, source: str) -> None:
    metadata = _load_scope_metadata(config)
    for item in results:
        key = _dual_result_key(item)
        info = metadata.get(key) or {}
        scope = str(info.get("scope") or "").strip()
        if scope not in _SCOPE_PRIORITY:
            evidence_kind = str(info.get("evidence_kind") or "").strip()
            if evidence_kind == "procedure":
                scope = "procedure"
            elif evidence_kind == "direct":
                scope = "device_specific"
            elif evidence_kind == "generic_mechanism":
                scope = "component_generic"
            else:
                scope = "device_specific" if source == "device_specific" else "component_generic"
        item["scope"] = scope

_SCOPE_FACTOR = {
    "device_specific": 1.0,
    "procedure": 0.97,
    "component_generic": 0.90,
    "instrument_generic": 0.85,
}


def _merge_dual_paths(
    specific_results: list[dict],
    generic_results: list[dict],
    top_k: int,
    rrf_k: int = 60,
) -> list[dict]:
    """Merge the two retrieval paths without letting scope ordering erase Top-1."""
    specific = _dedupe_path_results(specific_results)
    generic = _dedupe_path_results(generic_results)
    if not specific and not generic:
        return []

    try:
        limit = max(1, int(top_k))
    except (TypeError, ValueError):
        limit = 1
    try:
        smooth = max(0.0, float(rrf_k))
    except (TypeError, ValueError):
        smooth = 60.0

    documents: dict[tuple[str, str], dict] = {}
    source_by_key: dict[tuple[str, str], str] = {}
    path_scores: dict[tuple[str, str], float] = {}
    first_seen: dict[tuple[str, str], int] = {}
    specific_order: list[tuple[str, str]] = []
    generic_order: list[tuple[str, str]] = []
    seen_specific: set[tuple[str, str]] = set()
    seen_generic: set[tuple[str, str]] = set()

    def ingest(results: list[dict], source: str) -> None:
        order = specific_order if source == "device_specific" else generic_order
        seen = seen_specific if source == "device_specific" else seen_generic
        for rank, item in enumerate(results or [], start=1):
            if not isinstance(item, dict):
                continue
            key = _dual_result_key(item)
            if key not in seen:
                seen.add(key)
                order.append(key)
            # Keep the first/device-specific record as primary, but backfill
            # optional metadata from the other path such as citation_eligible.
            if key not in documents:
                documents[key] = dict(item)
            else:
                _fill_missing_metadata(documents[key], item)
            source_by_key.setdefault(key, source)
            path_scores[key] = path_scores.get(key, 0.0) + 1.0 / (smooth + rank)
            first_seen.setdefault(key, len(first_seen))

    ingest(specific, "device_specific")
    ingest(generic, "generic_mechanism")

    has_scope = any(
        str(documents[key].get("scope") or "").strip() in _SCOPE_PRIORITY
        for key in documents
    )

    def scope_of(key: tuple[str, str]) -> str:
        scope = str(documents[key].get("scope") or "").strip()
        if scope in _SCOPE_PRIORITY:
            return scope
        return "device_specific" if source_by_key.get(key) == "device_specific" else "component_generic"

    def adjusted_score(key: tuple[str, str]) -> float:
        score = path_scores.get(key, 0.0)
        if not has_scope:
            return score
        return score * _SCOPE_FACTOR.get(scope_of(key), 1.0)

    ranked_keys = sorted(
        documents,
        key=lambda key: (
            -adjusted_score(key),
            -path_scores.get(key, 0.0),
            first_seen[key],
        ),
    )

    # Preserve the strongest specific-path result and one representative per
    # requested domain. Remaining slots still compete by adjusted score, so
    # scope changes order but never silently discards the specific Top-1.
    pinned: list[tuple[str, str]] = []
    if has_scope and specific_order:
        pinned.append(specific_order[0])
        seen_domains: set[str] = set()
        for key in specific_order:
            domain = str(documents[key].get("domain") or "").strip()
            if not domain or domain in seen_domains:
                continue
            seen_domains.add(domain)
            if key not in pinned:
                pinned.append(key)

    final_keys = list(pinned[:limit])
    for key in ranked_keys:
        if len(final_keys) >= limit:
            break
        if key not in final_keys:
            final_keys.append(key)

    merged: list[dict] = []
    for key in final_keys:
        item = dict(documents[key])
        item["source"] = source_by_key.get(key, "generic_mechanism")
        item["scope"] = scope_of(key)
        item["rrf_score"] = round(path_scores.get(key, 0.0), 6)
        merged.append(item)
    return merged

def hybrid_retrieve(
    question: str,
    top_k: int = 3,
    candidate_k: int = 10,
    rrf_k: int = 60,
    trace: TraceCallback | None = None,
    intent: str | None = None,
    domains: list[str] | None = None,
) -> list[dict]:
    """按查询规划执行具体设备路和通用故障模式路的混合检索。"""
    question = str(question or "").strip()
    if not question:
        return []

    backend = _backend_name()
    if not is_in_domain(question, backend=backend):
        return []

    try:
        candidates = max(1, int(candidate_k))
    except (TypeError, ValueError):
        candidates = 10

    config = _resolve_config(backend)
    _ensure_placeholder(config["vector_db"], "向量库", backend)
    _ensure_placeholder(config["bm25_corpus"], "BM25语料", backend)
    _ensure_placeholder(config["bm25_index"], "BM25索引", backend)

    embedding_source = config.get("embedding_source")
    intent_name = str(intent or "").strip().lower()
    intent_source = "router" if intent_name else "internal"
    if not intent_name:
        try:
            classified = rule_classify(question)
            if isinstance(classified, dict):
                intent_name = str(classified.get("intent") or "").strip().lower()
        except Exception:
            LOGGER.warning("Failed to infer intent for query planning", exc_info=True)

    if trace is not None:
        print(
            f"[hybrid] intent={intent_name or 'None'}, source={intent_source} "
            f"domains={domains or []}",
            flush=True,
        )

    plan: dict | None = None
    try:
        planned = plan_query(question, intent_name)
        if isinstance(planned, dict) and planned.get("source") == "rule":
            plan = planned
    except Exception:
        LOGGER.warning("Query planning failed; falling back to single-path retrieval", exc_info=True)

    if plan is not None:
        specific_query = str(plan.get("specific_query") or question)
        generic_query = str(plan.get("generic_query") or "").strip()
        if trace is not None:
            print(
                f"[查询规划] components={plan.get('components') or []} "
                f"fault_modes={plan.get('fault_modes') or []}",
                flush=True,
            )
    else:
        try:
            expansion = expand_query(question, intent_name)
        except Exception:
            LOGGER.warning("Query expansion failed; using original query", exc_info=True)
            expansion = {"expanded_query": question}
        specific_query = str(expansion.get("expanded_query") or question)
        generic_query = ""
        if trace is not None:
            print("[查询规划] 不可用，退化为单路检索", flush=True)

    # Keep a slightly wider specific-path pool so a strong RRF target just
    # outside the final Top-K can still be considered during dual-path merge.
    specific_pool_k = max(top_k, min(candidates, max(top_k, top_k * 3)))
    specific_results = _retrieve_path(
        specific_query,
        domains=domains,
        top_k=specific_pool_k,
        candidate_k=candidates,
        rrf_k=rrf_k,
        config=config,
        embedding_source=embedding_source,
        trace=trace,
        label="具体设备",
    )
    for item in specific_results:
        item["source"] = "device_specific"
    _attach_scope(specific_results, config, "device_specific")
    if trace is not None:
        print(
            f"[具体设备路] query={specific_query} domains={domains or []} "
            f"返回{len(specific_results)}条",
            flush=True,
        )

    if not generic_query:
        return specific_results[:top_k]

    generic_results: list[dict] = []
    try:
        generic_results = _retrieve_path(
            generic_query,
            domains=None,
            top_k=max(top_k, min(candidates, 100)),
            candidate_k=candidates,
            rrf_k=rrf_k,
            config=config,
            embedding_source=embedding_source,
            trace=trace,
            label="通用故障模式",
        )
        for item in generic_results:
            item["source"] = "generic_mechanism"
        _attach_scope(generic_results, config, "generic_mechanism")
    except Exception:
        LOGGER.warning("Generic mechanism retrieval failed; returning device-specific results", exc_info=True)

    if trace is not None:
        print(
            f"[通用故障模式路] query={generic_query} 返回{len(generic_results)}条",
            flush=True,
        )

    if not specific_results and not generic_results:
        return []

    if not generic_results:
        return specific_results[:top_k]

    merged = _merge_dual_paths(specific_results, generic_results, top_k=top_k, rrf_k=rrf_k)
    if trace is not None:
        print(
            f"[双路合并] 具体设备{len(specific_results)}条 "
            f"通用机理{len(generic_results)}条 去重后{len(merged)}条",
            flush=True,
        )
        scope_counts = Counter(str(item.get("scope") or "unknown") for item in merged)
        print(
            f"[分层排序] device_specific={scope_counts.get('device_specific', 0)}, "
            f"procedure={scope_counts.get('procedure', 0)}, "
            f"component_generic={scope_counts.get('component_generic', 0)}, "
            f"instrument_generic={scope_counts.get('instrument_generic', 0)}",
            flush=True,
        )
        top5_counts = Counter(str(item.get("scope") or "unknown") for item in merged[:5])
        print(f"[分层排序] Top-5 scope={dict(top5_counts)}", flush=True)
    return merged
__all__ = ["hybrid_retrieve", "BACKEND_CONFIG"]
