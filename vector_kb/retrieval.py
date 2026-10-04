#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检索层：从 SQLite 向量库中召回与问题最相关的条文。"""

from __future__ import annotations

import importlib
import json
import sqlite3
import time
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


_VECTOR_CACHE: dict[str, tuple[tuple[int, int], str, list[dict[str, Any]]]] = {}


def _db_signature(path: Path) -> tuple[int, int]:
    try:
        stat = path.stat()
        return (stat.st_size, stat.st_mtime_ns)
    except OSError:
        return (0, 0)


def _domain_matches(record: dict, allowed_domains: set[str] | list[str] | tuple[str, ...]) -> bool:
    """Match primary or alternate domains; empty domain metadata remains permissive."""
    allowed = {str(domain).strip().lower() for domain in allowed_domains}
    domain = str(record.get("domain") or "").strip().lower()
    domain_alt = str(record.get("domain_alt") or "").strip().lower()
    if not domain and not domain_alt:
        return True
    return bool((domain and domain in allowed) or (domain_alt and domain_alt in allowed))


def _normalize_domains(domains: list[str] | tuple[str, ...] | None) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for raw in domains or []:
        domain = str(raw or "").strip().lower()
        if not domain or domain in seen:
            continue
        seen.add(domain)
        result.append(domain)
    return result


def _has_index_on_column(con: sqlite3.Connection, table: str, column: str) -> bool:
    for row in con.execute(f"PRAGMA index_list({table})"):
        index_name = row[1]
        columns = [item[2] for item in con.execute(f"PRAGMA index_info({index_name})")]
        if columns and columns[0] == column:
            return True
    return False


def _ensure_domain_index(con: sqlite3.Connection, db_path: Path, debug: bool = False) -> None:
    columns = {row[1] for row in con.execute("PRAGMA table_info(knowledge)")}
    if "domain" not in columns:
        return
    existed = _has_index_on_column(con, "knowledge", "domain")
    if existed:
        return
    con.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_domain ON knowledge(domain)")
    con.commit()
    if debug:
        print(f"[向量库] 已创建域索引 idx_knowledge_domain ({db_path})", flush=True)


def _cache_lookup(db_path: Path, domain: str, signature: tuple[int, int], debug: bool = False):
    key = f"{db_path.resolve()}::{domain}"
    cached = _VECTOR_CACHE.get(key)
    if cached is not None and cached[0] == signature:
        if debug:
            print(f"[向量库缓存] 命中 domain={domain}", flush=True)
        return cached[1], cached[2]
    if debug:
        print(f"[向量库缓存] 未命中 domain={domain}", flush=True)
    return None


def _cache_store(db_path: Path, domain: str, signature: tuple[int, int], schema: str, chunks: list[dict[str, Any]]) -> None:
    key = f"{db_path.resolve()}::{domain}"
    _VECTOR_CACHE[key] = (signature, schema, chunks)

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
        citation_eligible = meta.get("is_citable")
        if citation_eligible is None:
            citation_eligible = bool((meta.get("doc_id") or row[1]) and meta.get("clause"))
        out.append({
            "doc_id": meta.get("doc_id") or row[1],
            "clause": meta.get("clause"),
            "title": meta.get("title") or "",
            "text": row[2],
            "page": meta.get("page"),
            "citation": meta.get("citation") or "",
            "citation_eligible": citation_eligible,
            "domain": meta.get("domain"),
            "domain_alt": meta.get("domain_alt"),
            "vec": vector,
            "dim": row[4],
        })
    return out


def _load_knowledge(con: sqlite3.Connection, domains: list[str] | None = None) -> list[dict]:
    """Load the plant_kb knowledge schema, optionally filtered by domain in SQL."""
    columns = {
        row[1]
        for row in con.execute("PRAGMA table_info(knowledge)")
    }
    missing = [field for field in ("text", "vector", "dim") if field not in columns]
    if missing:
        raise RuntimeError(f"knowledge 表缺少字段：{missing}")

    normalized_domains = _normalize_domains(domains)
    if normalized_domains and "domain" not in columns:
        normalized_domains = []

    if normalized_domains:
        placeholders = ",".join("?" for _ in normalized_domains)
        if "domain_alt" in columns:
            query = (
                f"SELECT * FROM knowledge WHERE domain IN ({placeholders}) "
                f"OR domain_alt IN ({placeholders})"
            )
            params: tuple[Any, ...] = tuple(normalized_domains) * 2
        else:
            query = f"SELECT * FROM knowledge WHERE domain IN ({placeholders})"
            params = tuple(normalized_domains)
    else:
        query = "SELECT * FROM knowledge"
        params = ()

    out = []
    for row in con.execute(query, params):
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
        citation_eligible = record.get("is_citable")
        if citation_eligible is None:
            citation_eligible = metadata.get("is_citable")
        if citation_eligible is None:
            citation_eligible = bool(doc_id and clause)

        out.append({
            "doc_id": doc_id,
            "clause": clause,
            "title": title,
            "text": record["text"],
            "page": page,
            "citation": citation,
            "citation_eligible": citation_eligible,
            "domain": record.get("domain") or metadata.get("domain"),
            "domain_alt": record.get("domain_alt") or metadata.get("domain_alt"),
            "vec": vector,
            "dim": record.get("dim") or len(vector),
        })
    return out


def _load_vectors(
    con: sqlite3.Connection,
    schema: str,
    domains: list[str] | None = None,
) -> list[dict]:
    if schema == "chunks":
        chunks = _load_chunks(con)
        normalized_domains = _normalize_domains(domains)
        if normalized_domains:
            allowed = set(normalized_domains)
            chunks = [chunk for chunk in chunks if _domain_matches(chunk, allowed)]
        return chunks
    if schema == "knowledge":
        return _load_knowledge(con, domains=domains)
    raise ValueError(f"不支持的 schema：{schema}")
def retrieve(
    question: str,
    top_k: int = 3,
    min_score: float = 0.45,
    db: str | Path = DB_DEFAULT,
    db_path: str | Path | None = None,
    embedding_source: Any = None,
    debug: bool = False,
    domains: list[str] | None = None,
) -> list[dict]:
    """检索条文并返回标准 chunk 列表。

    按域加载只发生在首次调用时；同一域向量在当前进程内缓存。
    ``domains`` 为空时仍读取整张表，保持向后兼容。
    """
    top_k = max(1, int(top_k))
    resolved_db = Path(db_path if db_path is not None else db).resolve()
    normalized_domains = _normalize_domains(domains)
    embedder = _resolve_embedder(embedding_source)

    if not resolved_db.exists():
        initializer = connect(resolved_db)
        initializer.close()

    signature = _db_signature(resolved_db)
    chunks: list[dict[str, Any]] = []
    schema = ""
    try:
        if normalized_domains:
            for domain in normalized_domains:
                cached = _cache_lookup(resolved_db, domain, signature, debug)
                if cached is not None:
                    cached_schema, cached_chunks = cached
                    schema = schema or cached_schema
                    chunks.extend(cached_chunks)
                    continue

                con = sqlite3.connect(str(resolved_db))
                try:
                    con.row_factory = sqlite3.Row
                    schema = _detect_schema(con, resolved_db)
                    if schema == "knowledge":
                        _ensure_domain_index(con, resolved_db, debug=debug)
                    started = time.perf_counter()
                    loaded = _load_vectors(con, schema, domains=[domain])
                    elapsed = time.perf_counter() - started
                finally:
                    con.close()

                _cache_store(resolved_db, domain, _db_signature(resolved_db), schema, loaded)
                if debug:
                    print(
                        f"[向量库] 加载域={domain} 条数={len(loaded)} 耗时={elapsed:.3f}s",
                        flush=True,
                    )
                chunks.extend(loaded)
        else:
            cache_domain = "__all__"
            cached = _cache_lookup(resolved_db, cache_domain, signature, debug)
            if cached is not None:
                schema, cached_chunks = cached
                chunks = list(cached_chunks)
            else:
                con = sqlite3.connect(str(resolved_db))
                try:
                    con.row_factory = sqlite3.Row
                    schema = _detect_schema(con, resolved_db)
                    if schema == "knowledge":
                        _ensure_domain_index(con, resolved_db, debug=debug)
                    started = time.perf_counter()
                    loaded = _load_vectors(con, schema, domains=None)
                    elapsed = time.perf_counter() - started
                finally:
                    con.close()
                _cache_store(
                    resolved_db,
                    cache_domain,
                    _db_signature(resolved_db),
                    schema,
                    loaded,
                )
                if debug:
                    print(
                        f"[向量库] 加载域=all 条数={len(loaded)} 耗时={elapsed:.3f}s",
                        flush=True,
                    )
                chunks = loaded
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

    before_filter = len(chunks)
    if normalized_domains:
        allowed = set(normalized_domains)
        chunks = [chunk for chunk in chunks if _domain_matches(chunk, allowed)]
    if debug:
        print(
            f"[向量检索] domains={normalized_domains or []} "
            f"过滤前{before_filter}条 过滤后{len(chunks)}条",
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
            "citation_eligible": chunk.get("citation_eligible"),
            "domain": chunk.get("domain"),
            "domain_alt": chunk.get("domain_alt"),
        })
    return hits

__all__ = ["retrieve", "FIELD_MAPPINGS"]