#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检索层：从 SQLite 向量库中召回与问题最相关的条文。"""

import json
from array import array

from vector_kb.embeddings import embed
from vector_kb.store import DB_DEFAULT, connect


def _cosine(a, b):
    """计算余弦相似度；向量已经 L2 归一化时等同于点积。"""
    if not a or not b or len(a) != len(b):
        return 0.0
    s = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5 or 1.0
    nb = sum(y * y for y in b) ** 0.5 or 1.0
    return s / (na * nb)


def _load_vectors(con):
    """加载所有条文及其向量/元数据，忽略 clause 为空的块。"""
    out = []
    for row in con.execute("SELECT id, document_id, text, vector, dim, meta FROM chunks"):
        try:
            meta = json.loads(row[5]) if row[5] else {}
        except Exception:
            meta = {}
        if not meta.get("clause"):
            continue
        try:
            vec = array("f")
            vec.frombytes(row[3])
            vec = list(vec)
        except Exception:
            continue
        out.append({
            "id": row[0],
            "doc_id": meta.get("doc_id") or row[1],
            "text": row[2],
            "vec": vec,
            "dim": row[4],
            "meta": meta,
        })
    return out


def retrieve(question: str, top_k: int = 3, min_score: float = 0.45, db: str = DB_DEFAULT) -> list[dict]:
    """检索条文，返回 list[dict]。

    每项包含 doc_id / clause / title / text / page / score / citation。
    - 自动过滤 clause 为空的块；
    - 所有候选都低于 min_score 时返回空列表；
    - Embedding 或数据库不可用时抛出 RuntimeError。
    """
    top_k = max(1, int(top_k))
    try:
        con = connect(db)
        chunks = _load_vectors(con)
        con.close()
    except Exception as e:
        raise RuntimeError(f"数据库不可用：{db}。{e}") from e

    if not chunks:
        return []

    try:
        qvec = embed([question])[0]
    except Exception as e:
        raise RuntimeError(f"embedding unavailable: {e}") from e

    scored = [(_cosine(qvec, chunk["vec"]), chunk) for chunk in chunks]
    scored.sort(key=lambda item: item[0], reverse=True)

    hits = []
    for score, chunk in scored[:top_k]:
        if score < min_score:
            continue
        meta = chunk["meta"]
        hits.append({
            "doc_id": meta.get("doc_id") or chunk["doc_id"],
            "clause": meta.get("clause"),
            "title": meta.get("title") or "",
            "text": chunk["text"],
            "page": meta.get("page"),
            "score": score,
            "citation": meta.get("citation") or "",
        })
    return hits