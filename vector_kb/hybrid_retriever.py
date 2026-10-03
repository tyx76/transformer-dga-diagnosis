#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""混合检索编排：按 KB_BACKEND 选择向量库和 BM25 数据源，执行向量 + BM25 + RRF。"""

from __future__ import annotations

import importlib
import logging
import os
from collections.abc import Callable
from pathlib import Path

from vector_kb.bm25_retriever import bm25_retrieve
from vector_kb.domain_guard import is_in_domain
from vector_kb.intent_classifier import rule_classify
from vector_kb.query_expander import expand_query
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


def hybrid_retrieve(
    question: str,
    top_k: int = 3,
    candidate_k: int = 10,
    rrf_k: int = 60,
    trace: TraceCallback | None = None,
    intent: str | None = None,
) -> list[dict]:
    """Retrieve with original vector query and expanded BM25 query."""
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
    if not intent_name:
        try:
            classified = rule_classify(question)
            if isinstance(classified, dict):
                intent_name = str(classified.get("intent") or "").strip().lower()
        except Exception:
            LOGGER.warning("Failed to infer intent for query expansion", exc_info=True)

    try:
        expansion = expand_query(question, intent_name)
    except Exception:
        LOGGER.warning("Query expansion failed; using original query", exc_info=True)
        expansion = {
            "original_query": question,
            "expanded_query": question,
            "expanded_terms": [],
        }

    original_query = str(expansion.get("original_query") or question)
    expanded_query = str(expansion.get("expanded_query") or question)
    expanded_terms = list(expansion.get("expanded_terms") or [])

    if trace is not None:
        print(
            f"[查询扩展] original={original_query} expanded={expanded_query} terms={expanded_terms}",
            flush=True,
        )
        print(
            f"[向量检索] query={original_query} db_path={config['vector_db']} "
            f"embedding_source={embedding_source}",
            flush=True,
        )
        print(
            f"[BM25检索] query={expanded_query} index_path={config['bm25_index']}",
            flush=True,
        )
        trace(f"向量库路径:{config['vector_db']}", [])
        trace(f"BM25语料路径:{config['bm25_corpus']}", [])
        trace(f"BM25索引路径:{config['bm25_index']}", [])

    vector_results = retrieve(
        original_query,
        top_k=candidates,
        db_path=config["vector_db"],
        embedding_source=embedding_source,
    )
    if trace is not None:
        trace("向量检索Top-K", vector_results)

    bm25_results = bm25_retrieve(
        expanded_query,
        top_k=candidates,
        corpus_path=config["bm25_corpus"],
        index_path=config["bm25_index"],
    )
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


__all__ = ["hybrid_retrieve", "BACKEND_CONFIG"]
