"""Minimal retrieval API for the pure knowledge backend.

This package performs retrieval only. Domain selection, intent understanding,
fusion, generation, and citation validation belong to the caller.
"""
import sqlite3
from pathlib import Path

from .embedding import embed_texts
from .store import exact_rows, load_vectors

DB_DEFAULT = Path(__file__).resolve().parent / "knowledge.db"
REQUIRED_DOMAINS = ("dga", "oil_temp", "safety", "equipment", "dp", "cases")


def list_domains():
    """Return domains present in the database."""
    return sorted(stats()["domains"])


def _public(record, score=None):
    result = {
        "domain": record["domain"],
        "id": record["id"],
        "doc_id": record.get("doc_id"),
        "clause": record.get("clause"),
        "title": record["title"],
        "text": record["text"],
        "citation": record["citation"],
        "source": record["source"],
        "page": record.get("page"),
        "metadata": record.get("metadata") or {},
        "review_status": record.get("review_status") or "",
    }
    if score is not None:
        result["score"] = round(float(score), 6)
        result["retrieval_method"] = "vector"
    return result


def _cosine(left, right):
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    na = sum(a * a for a in left) ** 0.5 or 1.0
    nb = sum(b * b for b in right) ** 0.5 or 1.0
    return dot / (na * nb)


def _validate_domains(domains):
    if not isinstance(domains, (list, tuple)) or not domains:
        raise ValueError("domains must be a non-empty list or tuple")
    domains = tuple(dict.fromkeys(str(domain) for domain in domains))
    available = set(list_domains())
    unknown = [domain for domain in domains if domain not in available]
    if unknown:
        raise ValueError(f"unknown domains: {unknown}; available={sorted(available)}")
    return domains


def search(query, domains, filters=None, top_k=10, db_path=None, model="bge-m3:latest", ollama_url="http://localhost:11434"):
    """Vector search restricted to the caller-provided domains.

    No domain inference or metadata shortcut is performed here.
    """
    query = str(query or "").strip()
    if not query:
        raise ValueError("query must be non-empty")
    domains = _validate_domains(domains)
    top_k = max(1, int(top_k))
    db_path = Path(db_path or DB_DEFAULT)
    query_vector = embed_texts([query], model=model, ollama_url=ollama_url)[0]
    rows = load_vectors(domains, filters=filters, db_path=db_path)
    scored = [(_cosine(query_vector, row["vector"]), row) for row in rows]
    scored.sort(key=lambda item: item[0], reverse=True)
    return [_public(row, score) for score, row in scored[:top_k]]


def exact_lookup(filters, domains=None, db_path=None):
    """Exact metadata lookup. This is independent from vector ``search``."""
    if not isinstance(filters, dict) or not filters:
        raise ValueError("filters must be a non-empty dict")
    if domains is not None:
        domains = _validate_domains(domains)
    rows = exact_rows(filters, domains=domains, db_path=db_path or DB_DEFAULT)

    requested_clause = str(filters.get("clause") or "")
    requested_doc = str(filters.get("doc_id") or "")

    def rank(row):
        clause = str(row.get("clause") or "")
        if requested_clause:
            if clause == requested_clause:
                clause_rank = 0
            elif clause.startswith(requested_clause + "-"):
                clause_rank = 1
            else:
                clause_rank = 2
        else:
            clause_rank = 0
        doc_rank = 0 if not requested_doc or row.get("doc_id") == requested_doc else 1
        source_rank = {"standards": 0, "rules": 1, "safety": 2}.get(
            (row.get("metadata") or {}).get("original_module"), 3
        )
        return (doc_rank, clause_rank, source_rank, len(row.get("text", "")), row["id"])

    rows.sort(key=rank)
    return [_public(row, None) for row in rows]


def stats(db_path=None):
    """Return counts and vector integrity information."""
    db_path = Path(db_path or DB_DEFAULT)
    con = sqlite3.connect(f"file:{db_path.resolve().as_posix()}?mode=ro", uri=True)
    try:
        domains = dict(con.execute("SELECT domain, COUNT(*) FROM knowledge GROUP BY domain"))
        total = con.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
        bad = con.execute(
            "SELECT COUNT(*) FROM knowledge WHERE dim<>? OR length(vector)<>dim*4", (1024,)
        ).fetchone()[0]
    finally:
        con.close()
    return {"db": str(db_path), "total": total, "domains": domains, "bad_vectors": bad}