#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BM25 关键词检索层。

优先读取统一语料 ``data/corpus/clauses.jsonl``；统一文件尚未生成时，
兼容合并 722 判据和 572 运行维护两份 JSONL，避免两路检索语料不一致。
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any

import jieba
jieba.setLogLevel(60)  # 关闭 jieba 日志
from rank_bm25 import BM25Okapi

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
INDEX_DEFAULT = ROOT / "bm25_index.pkl"
INDEX_VERSION = 2

UNIFIED_CORPUS = PROJECT_ROOT / "data" / "corpus" / "clauses.jsonl"
FALLBACK_CORPUS_PATHS = (
    ROOT / "corpus" / "clauses.jsonl",
    ROOT / "corpus" / "DLT-572-2021_clauses.jsonl",
)

DOMAIN_TERMS = (
    "乙炔",
    "氢气",
    "甲烷",
    "乙烯",
    "乙烷",
    "总烃",
    "C₂H₂",
    "C₂H₄",
    "C₂H₆",
    "CH₄",
    "H₂",
    "CO",
    "CO₂",
    "注意值",
    "产气速率",
    "三比值",
    "局部放电",
    "电弧放电",
    "火花放电",
    "过热",
)

_SUBSCRIPT_DIGITS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
_DICTIONARY_READY = False
_INDEX_CACHE: tuple[Path, tuple[tuple[str, int, int], ...], list[dict[str, Any]], BM25Okapi | None] | None = None


def _normalize_text(text: Any) -> str:
    """统一大小写与化学式下标，便于中文和 DGA 术语可靠匹配。"""
    return str(text or "").translate(_SUBSCRIPT_DIGITS).lower()


def _ensure_dictionary_loaded() -> None:
    """将领域术语加入 jieba，避免化学式或专业词被切碎。"""
    global _DICTIONARY_READY
    if _DICTIONARY_READY:
        return

    for term in DOMAIN_TERMS:
        normalized = _normalize_text(term)
        jieba.add_word(term, freq=1_000_000)
        jieba.add_word(normalized, freq=1_000_000)
    _DICTIONARY_READY = True


def _tokenize(text: Any) -> list[str]:
    """对中文条文或用户问题分词，并过滤空白、标点等无检索价值 token。"""
    _ensure_dictionary_loaded()
    normalized = _normalize_text(text)
    tokens: list[str] = []
    for token in jieba.lcut(normalized, cut_all=False):
        token = token.strip()
        if token and all(ch.isalnum() for ch in token):
            tokens.append(token)
    return tokens


def _resolve_corpus_paths() -> tuple[Path, ...]:
    """优先返回统一语料；缺失时返回现有的所有兼容语料。"""
    if UNIFIED_CORPUS.is_file():
        return (UNIFIED_CORPUS.resolve(),)

    paths = tuple(path.resolve() for path in FALLBACK_CORPUS_PATHS if path.is_file())
    if paths:
        return paths

    candidates = [UNIFIED_CORPUS, *FALLBACK_CORPUS_PATHS]
    raise FileNotFoundError(f"未找到 BM25 条文数据：{ '，'.join(str(path) for path in candidates) }")


def _source_signature(corpus_paths: tuple[Path, ...]) -> tuple[tuple[str, int, int], ...]:
    """记录语料路径、大小和修改时间，用于判断索引是否需要重建。"""
    return tuple(
        (str(path), path.stat().st_size, path.stat().st_mtime_ns)
        for path in corpus_paths
    )


def _load_corpus(corpus_paths: tuple[Path, ...]) -> list[dict[str, Any]]:
    """合并读取 JSONL，按 chunk_id 或文档/条号去重并保留标准字段。"""
    documents: list[dict[str, Any]] = []
    seen: set[Any] = set()

    for corpus_path in corpus_paths:
        with corpus_path.open("r", encoding="utf-8-sig") as stream:
            for line_number, line in enumerate(stream, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except Exception as exc:
                    raise ValueError(f"{corpus_path}:{line_number} 不是有效 JSON") from exc

                text = str(item.get("text") or "").strip()
                if not text:
                    continue

                key = item.get("chunk_id")
                if not key:
                    key = (item.get("doc_id"), item.get("clause"), item.get("part"))
                if key in seen:
                    continue
                seen.add(key)

                documents.append({
                    "doc_id": item.get("doc_id"),
                    "clause": item.get("clause"),
                    "title": item.get("title") or "",
                    "text": text,
                    "page": item.get("page"),
                })
    return documents


def _build_index(
    corpus_paths: tuple[Path, ...],
    index_path: Path,
) -> tuple[list[dict[str, Any]], BM25Okapi | None]:
    """构建并原子写入 BM25 索引。"""
    documents = _load_corpus(corpus_paths)
    tokenized_corpus = [_tokenize(document["text"]) for document in documents]
    bm25 = BM25Okapi(tokenized_corpus) if tokenized_corpus else None

    payload = {
        "version": INDEX_VERSION,
        "source_paths": [str(path) for path in corpus_paths],
        "source_signature": _source_signature(corpus_paths),
        "documents": documents,
        "tokenized_corpus": tokenized_corpus,
        "bm25": bm25,
    }
    index_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = index_path.with_suffix(index_path.suffix + ".tmp")
    with temporary_path.open("wb") as stream:
        pickle.dump(payload, stream, protocol=pickle.HIGHEST_PROTOCOL)
    temporary_path.replace(index_path)
    return documents, bm25


def _load_or_build_index(
    index_path: Path = INDEX_DEFAULT,
) -> tuple[list[dict[str, Any]], BM25Okapi | None]:
    """加载未失效索引；索引缺失、损坏或源语料变化时自动重建。"""
    global _INDEX_CACHE

    index_path = Path(index_path).resolve()
    corpus_paths = _resolve_corpus_paths()
    signature = _source_signature(corpus_paths)

    if _INDEX_CACHE is not None and _INDEX_CACHE[:2] == (index_path, signature):
        return _INDEX_CACHE[2], _INDEX_CACHE[3]

    documents: list[dict[str, Any]]
    bm25: BM25Okapi | None
    if index_path.is_file():
        try:
            with index_path.open("rb") as stream:
                payload = pickle.load(stream)
            if (
                payload.get("version") == INDEX_VERSION
                and tuple(payload.get("source_signature") or ()) == signature
            ):
                documents = payload["documents"]
                bm25 = payload["bm25"]
            else:
                documents, bm25 = _build_index(corpus_paths, index_path)
        except Exception:
            documents, bm25 = _build_index(corpus_paths, index_path)
    else:
        documents, bm25 = _build_index(corpus_paths, index_path)

    _INDEX_CACHE = (index_path, signature, documents, bm25)
    return documents, bm25


def bm25_retrieve(question: str, top_k: int = 10) -> list[dict]:
    """返回与问题最匹配的 Top-K 条文；无有效结果时返回空列表。"""
    if not str(question or "").strip():
        return []
    try:
        requested = int(top_k)
    except (TypeError, ValueError):
        requested = 0
    if requested <= 0:
        return []

    documents, bm25 = _load_or_build_index()
    if not documents or bm25 is None:
        return []

    query_tokens = _tokenize(question)
    if not query_tokens:
        return []

    scores = bm25.get_scores(query_tokens)
    ranked_indices = sorted(
        range(len(documents)),
        key=lambda index: (-float(scores[index]), index),
    )

    results: list[dict] = []
    for index in ranked_indices:
        score = float(scores[index])
        # 零分表示问题没有命中任何索引 token，不应返回任意条文。
        if score <= 0.0:
            continue
        document = documents[index]
        results.append({
            "doc_id": document.get("doc_id"),
            "clause": document.get("clause"),
            "title": document.get("title") or "",
            "text": document.get("text") or "",
            "page": document.get("page"),
            "score": score,
        })
        if len(results) >= requested:
            break
    return results


__all__ = ["bm25_retrieve"]