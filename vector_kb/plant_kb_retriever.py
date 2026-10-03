#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DEPRECATED: not called by the main retrieval pipeline.
# Retained for legacy/reference use only. Last main-route use before 0eadd44.
"""Cleaned BM25 retriever for the independent plant_kb corpus."""

from __future__ import annotations

import html
import json
import logging
import pickle
import re
import sys
from pathlib import Path
from typing import Any

import jieba
from rank_bm25 import BM25Okapi

try:
    from vector_kb.bm25_retriever import (
        PLANT_BM25_V2_VERSION,
        PlantBM25V2Index,
        load_plant_bm25_v2,
        plant_bm25_v2_query_tokens,
    )
except ImportError:  # pragma: no cover - direct script execution fallback
    from bm25_retriever import (
        PLANT_BM25_V2_VERSION,
        PlantBM25V2Index,
        load_plant_bm25_v2,
        plant_bm25_v2_query_tokens,
    )

jieba.setLogLevel(60)
LOGGER = logging.getLogger(__name__)


def _log_loaded(version, documents) -> None:
    LOGGER.debug(
        "BM25 index loaded: version=%s documents=%d path=%s",
        version,
        len(documents),
        INDEX_DEFAULT,
    )
    if "--debug" in sys.argv[1:]:
        print(
            f"[BM25索引] version={version} documents={len(documents)} path={INDEX_DEFAULT}",
            flush=True,
        )

ROOT = Path(__file__).resolve().parent.parent
JSONL_DEFAULT = ROOT / "knowledge" / "plant_kb" / "data" / "knowledge.jsonl"
INDEX_DEFAULT = ROOT / "knowledge" / "plant_kb" / "index" / "bm25_index.pkl"
INDEX_VERSION = 1

_CUSTOM_TERMS = (
    "过热器", "再热器", "减温水", "磨煤机", "一次风管", "动态分离器",
    "排烟温度", "高压加热器", "低压加热器", "轴承", "润滑油", "金属温度",
    "回油温度", "氢冷器", "定子线棒", "励磁电流", "盖振", "轴振动",
    "动静碰磨", "特征通流面积", "疏水", "动刚度", "汽轮机", "发电机", "锅炉",
)
for _term in _CUSTOM_TERMS:
    jieba.add_word(_term)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "").replace("\u3000", " "))


def _clean_ocr_text(value: str) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"(?i)(imgs?/|img_in_|base64|alt=[\"']?image[\"']?|\.jpg|\.png|\.jpeg)", " ", text)
    text = re.sub(r"[#*`_~]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _tokenize(value: str) -> list[str]:
    text = _normalize_text(value)
    words = [word for word in jieba.lcut_for_search(text) if len(word.strip()) > 1]
    chars = [text[index:index + 2] for index in range(max(0, len(text) - 1))]
    latin = re.findall(r"[a-z0-9_.-]{2,}", text.lower())
    return words + chars + latin


def _is_usable_text(text: str) -> bool:
    return len(text) >= 40 and not re.search(r"(?i)(<|>|img|table|http|www\.)", text)


def _source_doc_id(source: str, fallback: str) -> str:
    name = Path(str(source or "")).name
    name = re.sub(r"^预处理后_", "", name).strip()
    return name or fallback or "PLANT_KB"


def _build_documents() -> list[dict]:
    records = []
    with JSONL_DEFAULT.open("r", encoding="utf-8-sig") as stream:
        for line in stream:
            if line.strip():
                records.append(json.loads(line))

    documents = []
    for record in records:
        text = _clean_ocr_text(record.get("text", ""))
        if not _is_usable_text(text):
            continue
        source = str(record.get("source") or "")
        doc_id = _source_doc_id(source, str(record.get("doc_id") or ""))
        clause = str(record.get("id") or record.get("clause") or "").strip()
        title = _clean_ocr_text(record.get("title", "")) or clause or doc_id
        citation = str(record.get("citation") or "").strip()
        if not citation:
            citation = f"{doc_id} {clause}".strip()
        documents.append({
            "doc_id": doc_id,
            "clause": clause or doc_id,
            "title": title,
            "text": text,
            "page": record.get("page"),
            "citation": citation,
            "domain": record.get("domain"),
            "source": source,
            "review_status": record.get("review_status") or "",
        })
    return documents


def _load_index() -> tuple[list[dict], Any]:
    """Load plant-bm25-v2 or rebuild the legacy plant index."""
    if not INDEX_DEFAULT.exists():
        if not JSONL_DEFAULT.exists():
            raise FileNotFoundError(
                f"BM25 index not found: {INDEX_DEFAULT}; corpus not found: {JSONL_DEFAULT}"
            )
        documents = _build_documents()
        tokens = [
            _tokenize(f'{doc.get("title", "")} {doc.get("citation", "")} {doc.get("text", "")}')
            for doc in documents
        ]
        payload = {
            "version": INDEX_VERSION,
            "mtime": JSONL_DEFAULT.stat().st_mtime,
            "size": JSONL_DEFAULT.stat().st_size,
            "documents": documents,
            "tokens": tokens,
        }
        INDEX_DEFAULT.parent.mkdir(parents=True, exist_ok=True)
        with INDEX_DEFAULT.open("wb") as stream:
            pickle.dump(payload, stream, protocol=pickle.HIGHEST_PROTOCOL)
        _log_loaded(INDEX_VERSION, documents)
        return documents, BM25Okapi(tokens)

    with INDEX_DEFAULT.open("rb") as stream:
        payload = pickle.load(stream)
    if not isinstance(payload, dict):
        raise ValueError(f"Unknown BM25 index payload: {type(payload).__name__}")

    version = payload.get("version")
    if version == PLANT_BM25_V2_VERSION:
        documents, bm25 = load_plant_bm25_v2(payload, (JSONL_DEFAULT,))
        _log_loaded(version, documents)
        return documents, bm25

    if "documents" in payload or version == INDEX_VERSION:
        documents = payload.get("documents") or []
        bm25 = payload.get("bm25")
        tokens = payload.get("tokens") or []
        if not documents:
            raise ValueError("Legacy BM25 index is missing documents")
        if bm25 is None and tokens:
            bm25 = BM25Okapi(tokens)
        if bm25 is None:
            raise ValueError("Legacy BM25 index is missing bm25/tokens")
        _log_loaded(version, documents)
        return documents, bm25

    raise ValueError(f"Unknown BM25 index version: {version!r}")


_DOCUMENTS: list[dict] | None = None
_BM25: Any | None = None


def _ensure_index() -> tuple[list[dict], Any | None]:
    global _DOCUMENTS, _BM25
    if _DOCUMENTS is None or _BM25 is None:
        _DOCUMENTS, _BM25 = _load_index()
    return _DOCUMENTS, _BM25


def plant_bm25_retrieve(question: str, top_k: int = 20) -> list[dict]:
    """Retrieve from cleaned plant_kb records using BM25."""
    question = str(question or "").strip()
    if not question or top_k <= 0:
        return []
    documents, bm25 = _ensure_index()
    if not documents or bm25 is None:
        return []
    query_tokens = (
        plant_bm25_v2_query_tokens(question)
        if isinstance(bm25, PlantBM25V2Index)
        else _tokenize(question)
    )
    scores = bm25.get_scores(query_tokens)
    ranked = sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)
    results = []
    for index in ranked:
        if scores[index] <= 0:
            continue
        item = dict(documents[index])
        item["score"] = round(float(scores[index]), 6)
        results.append(item)
        if len(results) >= top_k:
            break
    return results


__all__ = ["plant_bm25_retrieve"]