#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BM25 关键词检索层。"""

from __future__ import annotations

import json
import logging
import math
import pickle
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

import jieba
jieba.setLogLevel(60)
from rank_bm25 import BM25Okapi

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
INDEX_DEFAULT = PROJECT_ROOT / "knowledge" / "pure_kb" / "index" / "bm25_index.pkl"
INDEX_VERSION = 2
PLANT_BM25_V2_VERSION = "plant-bm25-v2"
PLANT_BM25_V2_REQUIRED_FIELDS = ("docs", "df", "avgdl", "field_weights")
LOGGER = logging.getLogger(__name__)


def _debug_enabled() -> bool:
    return "--debug" in sys.argv[1:]


UNIFIED_CORPUS = PROJECT_ROOT / "knowledge" / "pure_kb" / "data" / "clauses.jsonl"
FALLBACK_CORPUS_PATHS: tuple[Path, ...] = ()

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
_INDEX_CACHE: tuple[Path, tuple[Any, ...], list[dict[str, Any]], Any | None] | None = None


class PlantBM25V2Index:
    """Precomputed BM25 index for the plant-bm25-v2 payload."""

    def __init__(
        self,
        docs: list[dict[str, Any]],
        df: dict[str, int],
        avgdl: float,
        field_weights: dict[str, int],
        k1: float = 1.5,
        b: float = 0.75,
        epsilon: float = 0.25,
    ) -> None:
        if not isinstance(docs, list):
            raise ValueError("plant-bm25-v2 field 'docs' must be a list")
        if not isinstance(df, dict):
            raise ValueError("plant-bm25-v2 field 'df' must be a dict")
        try:
            self.avgdl = float(avgdl)
        except (TypeError, ValueError) as exc:
            raise ValueError("plant-bm25-v2 field 'avgdl' must be numeric") from exc
        if self.avgdl <= 0:
            raise ValueError("plant-bm25-v2 field 'avgdl' must be positive")
        if not isinstance(field_weights, dict):
            raise ValueError("plant-bm25-v2 field 'field_weights' must be a dict")

        self.docs = docs
        self.df = df
        self.field_weights = dict(field_weights)
        self.k1 = float(k1)
        self.b = float(b)
        self.epsilon = float(epsilon)
        self.corpus_size = len(docs)
        self.doc_tf: list[dict[str, int]] = []
        self.doc_len: list[int] = []
        self._idf_cache: dict[str, float] = {}
        self._average_idf: float | None = None

        for document in docs:
            tf = document.get("tf") if isinstance(document, dict) else None
            if not isinstance(tf, dict) or not tf:
                tokens = document.get("tokens") if isinstance(document, dict) else None
                if not tokens:
                    tokens = _v2_tokenize_fields(document or {}, self.field_weights)
                tf = Counter(tokens)
            else:
                try:
                    tf = {str(key): int(value) for key, value in tf.items() if int(value) > 0}
                except (TypeError, ValueError) as exc:
                    raise ValueError("plant-bm25-v2 document tf values must be integers") from exc
            self.doc_tf.append(tf)
            self.doc_len.append(sum(tf.values()))

    def _average_idf_value(self) -> float:
        if self._average_idf is None:
            total = 0.0
            count = 0
            for value in self.df.values():
                try:
                    freq = int(value)
                except (TypeError, ValueError):
                    continue
                if freq <= 0:
                    continue
                total += math.log(self.corpus_size - freq + 0.5) - math.log(freq + 0.5)
                count += 1
            self._average_idf = total / count if count else 0.0
        return self._average_idf

    def _idf(self, token: str) -> float:
        if token in self._idf_cache:
            return self._idf_cache[token]
        value = self.df.get(token)
        if value is None:
            return 0.0
        try:
            freq = int(value)
        except (TypeError, ValueError):
            return 0.0
        if freq <= 0:
            return 0.0
        idf = math.log(self.corpus_size - freq + 0.5) - math.log(freq + 0.5)
        if idf < 0:
            idf = self.epsilon * self._average_idf_value()
        self._idf_cache[token] = idf
        return idf

    def get_scores(self, query_tokens: list[str]) -> list[float]:
        scores = [0.0] * self.corpus_size
        if not query_tokens:
            return scores
        seen: set[str] = set()
        for token in query_tokens:
            if token in seen:
                continue
            seen.add(token)
            idf = self._idf(token)
            if idf == 0.0:
                continue
            for index, tf in enumerate(self.doc_tf):
                frequency = tf.get(token, 0)
                if not frequency:
                    continue
                denominator = frequency + self.k1 * (
                    1 - self.b + self.b * self.doc_len[index] / self.avgdl
                )
                scores[index] += idf * frequency * (self.k1 + 1) / denominator
        return scores


def _v2_normalize_text(text: Any) -> str:
    normalized = unicodedata.normalize("NFKC", str(text or "")).lower()
    return "".join(char for char in normalized if char.isalnum())


def _v2_char_ngrams(text: str) -> list[str]:
    tokens: list[str] = []
    for size in (1, 2, 3):
        tokens.extend(text[index:index + size] for index in range(max(0, len(text) - size + 1)))
    return tokens


def _v2_tokenize_fields(document: dict[str, Any], field_weights: dict[str, Any]) -> list[str]:
    parts: list[str] = []
    for field, weight in field_weights.items():
        try:
            repeat = max(0, int(weight))
        except (TypeError, ValueError):
            repeat = 0
        if repeat:
            parts.append(_v2_normalize_text(document.get(field, "")) * repeat)
    return _v2_char_ngrams("".join(parts))


def plant_bm25_v2_query_tokens(query: str) -> list[str]:
    return _v2_char_ngrams(_v2_normalize_text(query))


def _load_v2_corpus_metadata(corpus_paths: tuple[Path, ...]) -> dict[str, dict[str, Any]]:
    metadata: dict[str, dict[str, Any]] = {}
    for corpus_path in corpus_paths:
        if not corpus_path.is_file():
            continue
        with corpus_path.open("r", encoding="utf-8-sig") as stream:
            for line in stream:
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                except Exception:
                    continue
                key = str(item.get("id") or item.get("chunk_id") or "")
                if not key:
                    continue
                metadata[key] = {
                    "doc_id": item.get("doc_id") or item.get("source_file"),
                    "clause": item.get("clause"),
                    "title": item.get("title") or "",
                    "page": item.get("page"),
                    "citation": item.get("citation") or "",
                }
    return metadata


def _adapt_v2_document(document: dict[str, Any], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    extra = metadata or {}
    return {
        "doc_id": document.get("doc_id") or extra.get("doc_id") or document.get("source") or document.get("module") or document.get("domain"),
        "clause": document.get("clause") if document.get("clause") is not None else extra.get("clause"),
        "title": document.get("title") or extra.get("title") or "",
        "text": document.get("text") or "",
        "page": document.get("page") if document.get("page") is not None else extra.get("page"),
        "citation": document.get("citation") or extra.get("citation") or "",
        "domain": document.get("domain") or document.get("module") or extra.get("domain"),
        "_source_id": str(document.get("id") or ""),
    }


def load_plant_bm25_v2(payload: dict[str, Any], corpus_paths: tuple[Path, ...] = ()) -> tuple[list[dict[str, Any]], PlantBM25V2Index]:
    missing = [field for field in PLANT_BM25_V2_REQUIRED_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"plant-bm25-v2 index is missing fields: {missing}")
    docs = payload["docs"]
    df = payload["df"]
    avgdl = payload["avgdl"]
    field_weights = payload["field_weights"]
    if not isinstance(docs, list):
        raise ValueError("plant-bm25-v2 field 'docs' must be a list")
    if not isinstance(df, dict):
        raise ValueError("plant-bm25-v2 field 'df' must be a dict")
    if not isinstance(field_weights, dict):
        raise ValueError("plant-bm25-v2 field 'field_weights' must be a dict")
    record_count = payload.get("record_count")
    if record_count is not None and int(record_count) != len(docs):
        raise ValueError(f"plant-bm25-v2 record_count mismatch: {record_count} != {len(docs)}")
    metadata = _load_v2_corpus_metadata(corpus_paths)
    documents = [_adapt_v2_document(document, metadata.get(str(document.get("id") or ""))) for document in docs]
    index = PlantBM25V2Index(docs, df, avgdl, field_weights)
    return documents, index


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


def _resolve_corpus_paths(corpus_path: str | Path | list | tuple | None = None) -> tuple[Path, ...]:
    """Resolve legacy or explicitly provided JSONL corpus paths."""
    if corpus_path is None:
        if UNIFIED_CORPUS.is_file():
            return (UNIFIED_CORPUS.resolve(),)
        paths = tuple(path.resolve() for path in FALLBACK_CORPUS_PATHS if path.is_file())
        if paths:
            return paths
        candidates = [UNIFIED_CORPUS, *FALLBACK_CORPUS_PATHS]
        raise FileNotFoundError(f"未找到 BM25 条文数据：{'，'.join(str(path) for path in candidates)}")

    raw_paths = corpus_path if isinstance(corpus_path, (list, tuple)) else (corpus_path,)
    paths = tuple(Path(path) for path in raw_paths)
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"BM25 语料不存在：{'，'.join(str(path) for path in missing)}")
    return tuple(path.resolve() for path in paths)


def _source_signature(corpus_paths: tuple[Path, ...]) -> tuple[tuple[str, int, int], ...]:
    """记录语料路径、大小和修改时间，用于判断索引是否需要重建。"""
    return tuple(
        (str(path), path.stat().st_size, path.stat().st_mtime_ns)
        for path in corpus_paths
    )


def _load_corpus(corpus_paths: tuple[Path, ...]) -> list[dict[str, Any]]:
    """读取 JSONL，按 chunk_id 或文档/条号去重并保留标准字段。"""
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
                key = item.get("chunk_id") or item.get("id")
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
                    "domain": item.get("domain"),
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
    index_path: str | Path = INDEX_DEFAULT,
    corpus_path: str | Path | list | tuple | None = None,
) -> tuple[list[dict[str, Any]], Any]:
    """Load a supported BM25 index format or rebuild the legacy index."""
    global _INDEX_CACHE

    index_path = Path(index_path).resolve()
    corpus_paths = _resolve_corpus_paths(corpus_path)
    signature = _source_signature(corpus_paths)
    if _INDEX_CACHE is not None and _INDEX_CACHE[0] == index_path and _INDEX_CACHE[1] == signature:
        return _INDEX_CACHE[2], _INDEX_CACHE[3]

    documents: list[dict[str, Any]] = []
    bm25: Any = None
    version: Any = None

    if index_path.is_file():
        with index_path.open("rb") as stream:
            payload = pickle.load(stream)
        if not isinstance(payload, dict):
            raise ValueError(f"Unknown BM25 index payload: {type(payload).__name__}")

        version = payload.get("version")
        if version == PLANT_BM25_V2_VERSION:
            documents, bm25 = load_plant_bm25_v2(payload, corpus_paths)
        elif version == INDEX_VERSION or "documents" in payload:
            old_documents = payload.get("documents") or []
            if not isinstance(old_documents, list):
                raise ValueError("Legacy BM25 index field 'documents' must be a list")
            stored_signature = tuple(payload.get("source_signature") or ())
            old_bm25 = payload.get("bm25")
            old_tokens = payload.get("tokens") or []
            if version == INDEX_VERSION and stored_signature != signature:
                documents, bm25 = _build_index(corpus_paths, index_path)
            elif old_documents and old_bm25 is not None:
                documents, bm25 = old_documents, old_bm25
            elif old_documents and old_tokens:
                documents = old_documents
                bm25 = BM25Okapi(old_tokens)
            else:
                raise ValueError(
                    "Legacy BM25 index is missing documents/bm25/tokens"
                )
        else:
            raise ValueError(f"Unknown BM25 index version: {version!r}")
    else:
        documents, bm25 = _build_index(corpus_paths, index_path)
        version = INDEX_VERSION

    LOGGER.debug(
        "BM25 index loaded: version=%s documents=%d path=%s",
        version,
        len(documents),
        index_path,
    )
    if _debug_enabled():
        print(
            f"[BM25索引] version={version} documents={len(documents)} path={index_path}",
            flush=True,
        )
    _INDEX_CACHE = (index_path, signature, documents, bm25)
    return documents, bm25

def bm25_retrieve(
    question: str,
    top_k: int = 10,
    corpus_path: str | Path | list | tuple | None = None,
    index_path: str | Path | None = None,
    domains: list[str] | None = None,
    debug: bool = False,
) -> list[dict]:
    """返回与问题最匹配的 Top-K 条文；无有效结果时返回空列表。"""
    if not str(question or "").strip():
        return []
    try:
        requested = int(top_k)
    except (TypeError, ValueError):
        requested = 0
    if requested <= 0:
        return []

    resolved_index_path = Path(index_path).resolve() if index_path is not None else INDEX_DEFAULT.resolve()
    if index_path is not None and not resolved_index_path.is_file():
        raise FileNotFoundError(f"BM25 index not found: {resolved_index_path}")

    documents, bm25 = _load_or_build_index(
        index_path=resolved_index_path,
        corpus_path=corpus_path,
    )
    if not documents or bm25 is None:
        return []

    query_tokens = (
        plant_bm25_v2_query_tokens(question)
        if isinstance(bm25, PlantBM25V2Index)
        else _tokenize(question)
    )
    if not query_tokens:
        return []

    scores = bm25.get_scores(query_tokens)
    candidate_indices = list(range(len(documents)))
    before_filter = len(candidate_indices)
    if domains:
        allowed = {str(domain) for domain in domains}
        candidate_indices = [
            index for index in candidate_indices
            if not documents[index].get("domain")
            or str(documents[index].get("domain")) in allowed
        ]
    if debug:
        print(
            f"[BM25检索] domains={domains or []} "
            f"过滤前{before_filter}条 过滤后{len(candidate_indices)}条",
            flush=True,
        )
    ranked_indices = sorted(
        candidate_indices,
        key=lambda index: (-float(scores[index]), index),
    )

    results: list[dict] = []
    for index in ranked_indices:
        score = float(scores[index])
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
            "domain": document.get("domain"),
        })
        if len(results) >= requested:
            break
    return results


__all__ = ["bm25_retrieve", "PlantBM25V2Index", "load_plant_bm25_v2", "plant_bm25_v2_query_tokens", "PLANT_BM25_V2_VERSION"]