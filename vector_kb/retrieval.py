#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检索层：从 SQLite 向量库中召回与问题最相关的条文。"""

from __future__ import annotations

import importlib
import json
import sqlite3
from array import array
from pathlib import Path
from typing import Any

from vector_kb.embeddings import embed
from vector_kb.store import DB_DEFAULT, connect

FIELD_MAPPINGS = {
    "chunks": {
        "doc_id": "meta.doc_id or document_id",
        "clause": "meta.clause",
        "title": "meta.title",
        "text": "text",
        "page": "meta.page",
        "citation": "meta.citation",
        "vector": "vector",
        "dim": "dim",
    },
    "knowledge": {
        "doc_id": "doc_id or metadata.doc_id",
        "clause": "clause or metadata.clause",
        "title": "title or metadata.title",
        "text": "text",
        "page": "page or metadata.page",
        "citation": "citation or metadata.citation",
        "vector": "vector",
        "dim": "dim",
    },
}


def _resolve_embedder(embedding_source: Any):
    """Resolve a callable, module name, or module object for embeddings."""
    if embedding_source is None:
        return embed
    if callable(embedding_source):
        return embedding_source

    module = embedding_source
    if isinstance(embedding_source, str):
        module = importlib.import_module(embedding_source)

    for attribute in ("embed", "embed_texts"):
        candidate = getattr(module, attribute, None)
        if callable(candidate):
            return candidate
    raise ValueError(
        "embedding_source 必须可调用，或提供 embed/embed_texts 方法"
    )


def _cosine(a, b):
    """计算余弦相似度；向量已经 L2 归一化时等同于点积。"""
    if not a or not b or len(a) != len(b):
        return 0.0
    s = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5 or 1.0
    nb = sum(y * y for y in b) ** 0.5 or 1.0
    return s / (na * nb)


def _detect_schema(con: sqlite3.Connection, db_path: Path) -> str:
    """Detect the supported vector-table schema."""
    tables = {
        row[0]
        for row in con.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    if "knowledge" in tables:
        return "knowledge"
    if "chunks" in tables:
        return "chunks"
    raise RuntimeError(
        f"未知向量库schema：{db_path}；tables={sorted(tables)}"
    )


def _json_object(value: Any) -> dict:
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(value or "{}")
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _vector_from_blob(value: Any) -> list[float]:
    vector = array("f")
    vector.frombytes(bytes(value))
    return list(vector)


def _load_chunks(con: sqlite3.Connection) -> list[dict]:
    """Load the legacy vector_kb chunks schema."""
    out = []
    for row in con.execute(
        "SELECT id, document_id, text, vector, dim, meta FROM chunks"
    ):
        meta = _json_object(row[5])
        if not meta.get("clause"):
            continue
        try:
            vector = _vector_from_blob(row[3])
        except Exception:
            continue
        out.append({
            "doc_id": meta.get("doc_id") or row[1],
            "clause": meta.get("clause"),
            "title": meta.get("title") or "",
            "text": row[2],
            "page": meta.get("page"),
            "citation": meta.get("citation") or "",
            "vec": vector,
            "dim": row[4],
        })
    return out


def _load_knowledge(con: sqlite3.Connection) -> list[dict]:
    """Load the plant_kb knowledge schema."""
    columns = {
        row[1]
        for row in con.execute("PRAGMA table_info(knowledge)")
    }
    missing = [field for field in ("text", "vector", "dim") if field not in columns]
    if missing:
        raise RuntimeError(f"knowledge 表缺少字段：{missing}")

    out = []
    for row in con.execute("SELECT * FROM knowledge"):
        record = dict(row)
        metadata = _json_object(record.get("metadata") or record.get("meta"))
        try:
            vector = _vector_from_blob(record["vector"])
        except Exception:
            continue

        doc_id = record.get("doc_id") or metadata.get("doc_id")
        clause = record.get("clause") or metadata.get("clause")
        title = record.get("title") or metadata.get("title") or clause or ""
        page = record.get("page")
        if page is None:
            page = metadata.get("page")
        citation = record.get("citation") or metadata.get("citation") or ""

        out.append({
            "doc_id": doc_id,
            "clause": clause,
            "title": title,
            "text": record["text"],
            "page": page,
            "citation": citation,
            "vec": vector,
            "dim": record.get("dim") or len(vector),
        })
    return out


def _load_vectors(con: sqlite3.Connection, schema: str) -> list[dict]:
    if schema == "chunks":
        return _load_chunks(con)
    if schema == "knowledge":
        return _load_knowledge(con)
    raise ValueError(f"不支持的 schema：{schema}")


def retrieve(
    question: str,
    top_k: int = 3,
    min_score: float = 0.45,
    db: str | Path = DB_DEFAULT,
    db_path: str | Path | None = None,
    embedding_source: Any = None,
    debug: bool = False,
) -> list[dict]:
    """检索条文并返回标准 chunk 列表。

    ``db_path`` 优先于旧参数 ``db``。自动识别 ``chunks`` 和
    ``knowledge`` 两种 SQLite schema。
    """
    top_k = max(1, int(top_k))
    resolved_db = Path(db_path if db_path is not None else db)
    embedder = _resolve_embedder(embedding_source)

    if not resolved_db.exists():
        # Preserve the old behavior for a missing default database.
        initializer = connect(resolved_db)
        initializer.close()

    try:
        con = sqlite3.connect(str(resolved_db))
        con.row_factory = sqlite3.Row
        schema = _detect_schema(con, resolved_db)
        chunks = _load_vectors(con, schema)
        con.close()
    except Exception as exc:
        if isinstance(exc, RuntimeError):
            raise
        raise RuntimeError(f"数据库不可用：{resolved_db}。{exc}") from exc

    if debug:
        mapping = FIELD_MAPPINGS.get(schema, {})
        print(
            f"[retrieve] db={resolved_db} table={schema} mapping={mapping}",
            flush=True,
        )

    if not chunks:
        return []

    try:
        qvec = embedder([question])[0]
    except Exception as exc:
        raise RuntimeError(
            f"embedding unavailable：{resolved_db}。{exc}"
        ) from exc

    scored = [(_cosine(qvec, chunk["vec"]), chunk) for chunk in chunks]
    scored.sort(key=lambda item: item[0], reverse=True)

    hits = []
    for score, chunk in scored[:top_k]:
        if score < min_score:
            continue
        hits.append({
            "doc_id": chunk.get("doc_id"),
            "clause": chunk.get("clause"),
            "title": chunk.get("title") or "",
            "text": chunk.get("text") or "",
            "page": chunk.get("page"),
            "score": score,
            "citation": chunk.get("citation") or "",
        })
    return hits


__all__ = ["retrieve", "FIELD_MAPPINGS"]