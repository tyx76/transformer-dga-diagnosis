"""SQLite storage and filtering for the pure knowledge backend."""
import json
import sqlite3
from array import array
from pathlib import Path

from .embedding import embed_texts

FIELDS = (
    "domain", "id", "doc_id", "clause", "title", "text",
    "citation", "source", "page", "metadata", "review_status",
)
SCHEMA = """
CREATE TABLE IF NOT EXISTS knowledge (
    domain TEXT NOT NULL,
    id TEXT NOT NULL,
    doc_id TEXT,
    clause TEXT,
    title TEXT NOT NULL,
    text TEXT NOT NULL,
    citation TEXT NOT NULL,
    source TEXT NOT NULL,
    page INTEGER,
    metadata TEXT NOT NULL DEFAULT '{}',
    review_status TEXT NOT NULL DEFAULT '',
    vector BLOB NOT NULL,
    dim INTEGER NOT NULL,
    PRIMARY KEY(domain, id)
);
CREATE INDEX IF NOT EXISTS idx_knowledge_domain ON knowledge(domain);
CREATE INDEX IF NOT EXISTS idx_knowledge_doc ON knowledge(doc_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_clause ON knowledge(clause);
CREATE INDEX IF NOT EXISTS idx_knowledge_review ON knowledge(review_status);
"""

COLUMN_FILTERS = {
    "domain": "domain", "id": "id", "doc_id": "doc_id", "clause": "clause",
    "title": "title", "citation": "citation", "source": "source",
    "page": "page", "review_status": "review_status",
}


def read_jsonl(path):
    records = []
    with Path(path).open(encoding="utf-8-sig") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            item = json.loads(line)
            missing = [field for field in FIELDS if field not in item]
            if missing:
                raise ValueError(f"{path}:{line_no} missing fields: {missing}")
            if not item["domain"] or not item["id"] or not item["text"]:
                raise ValueError(f"{path}:{line_no} requires non-empty domain/id/text")
            item["metadata"] = dict(item.get("metadata") or {})
            records.append(item)
    return records


def build_database(jsonl_path, db_path, model="bge-m3:latest", ollama_url="http://localhost:11434"):
    records = read_jsonl(jsonl_path)
    vectors = embed_texts(
        [record["text"] for record in records], model=model, ollama_url=ollama_url
    )
    db = Path(db_path)
    db.parent.mkdir(parents=True, exist_ok=True)
    if db.exists():
        db.unlink()
    con = sqlite3.connect(str(db))
    try:
        con.executescript(SCHEMA)
        for record, vector in zip(records, vectors):
            con.execute(
                """INSERT INTO knowledge
                (domain, id, doc_id, clause, title, text, citation, source, page,
                 metadata, review_status, vector, dim)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    record["domain"], record["id"], record.get("doc_id"),
                    record.get("clause"), record["title"], record["text"],
                    record["citation"], record["source"], record.get("page"),
                    json.dumps(record["metadata"], ensure_ascii=False),
                    record["review_status"], array("f", vector).tobytes(), len(vector),
                ),
            )
        con.commit()
    finally:
        con.close()
    return {"records": len(records), "db": str(db), "dim": len(vectors[0]) if vectors else 0}


def _filter_sql(filters):
    clauses = []
    params = []
    for key, value in (filters or {}).items():
        if key in COLUMN_FILTERS:
            column = COLUMN_FILTERS[key]
            if key == "clause" and value and "-表" not in str(value):
                clauses.append(f"({column} = ? OR {column} LIKE ?)")
                params.extend([str(value), f"{value}-%"])
            else:
                clauses.append(f"{column} = ?")
                params.append(str(value))
        else:
            clauses.append("json_extract(metadata, ?) = ?")
            params.extend([f"$.{key}", str(value)])
    return clauses, params


def load_vectors(domains, filters=None, db_path=None):
    if not domains:
        raise ValueError("domains is required")
    placeholders = ",".join("?" for _ in domains)
    where = [f"domain IN ({placeholders})"]
    params = list(domains)
    filter_clauses, filter_params = _filter_sql(filters)
    where.extend(filter_clauses)
    params.extend(filter_params)
    con = sqlite3.connect(f"file:{Path(db_path).resolve().as_posix()}?mode=ro", uri=True)
    rows = []
    try:
        cursor = con.execute(
            "SELECT domain,id,doc_id,clause,title,text,citation,source,page,metadata,"
            "review_status,vector,dim FROM knowledge WHERE " + " AND ".join(where),
            params,
        )
        for row in cursor:
            vector = array("f")
            vector.frombytes(row[11])
            rows.append({
                "domain": row[0], "id": row[1], "doc_id": row[2], "clause": row[3],
                "title": row[4], "text": row[5], "citation": row[6], "source": row[7],
                "page": row[8], "metadata": json.loads(row[9] or "{}"),
                "review_status": row[10], "vector": list(vector), "dim": row[12],
            })
    finally:
        con.close()
    return rows


def exact_rows(filters, domains=None, db_path=None):
    where = []
    params = []
    if domains:
        placeholders = ",".join("?" for _ in domains)
        where.append(f"domain IN ({placeholders})")
        params.extend(domains)
    filter_clauses, filter_params = _filter_sql(filters)
    where.extend(filter_clauses)
    params.extend(filter_params)
    if not where:
        raise ValueError("filters or domains is required")
    con = sqlite3.connect(f"file:{Path(db_path).resolve().as_posix()}?mode=ro", uri=True)
    rows = []
    try:
        cursor = con.execute(
            "SELECT domain,id,doc_id,clause,title,text,citation,source,page,metadata,review_status "
            "FROM knowledge" + (" WHERE " + " AND ".join(where) if where else ""),
            params,
        )
        for row in cursor:
            rows.append({
                "domain": row[0], "id": row[1], "doc_id": row[2], "clause": row[3],
                "title": row[4], "text": row[5], "citation": row[6], "source": row[7],
                "page": row[8], "metadata": json.loads(row[9] or "{}"),
                "review_status": row[10], "retrieval_method": "exact",
            })
    finally:
        con.close()
    return rows