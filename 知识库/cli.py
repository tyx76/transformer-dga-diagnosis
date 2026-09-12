#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知识库 CLI：从 JSONL 构建 / 查看 SQLite 向量库（Ollama bge-m3）。

用法：
    python cli.py ingest 语料/clauses.jsonl --collection normative --force
    python cli.py ingest 语料/DLT-572-2021_clauses.jsonl --collection reference --force
    python cli.py ingest 语料/clauses.jsonl --collection normative --dry-run   # 不调 Ollama，写零向量（自测）
    python cli.py info

依赖：Python 3.10+（仅标准库）；Ollama 服务 + bge-m3:latest（真实入库时需要）
"""
import argparse, datetime, hashlib, json, sqlite3, sys, urllib.request
from array import array
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
DB_DEFAULT = ROOT / "knowledge.db"
OLLAMA = "http://localhost:11434"
MODEL = "bge-m3:latest"
DIM = 1024

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    filename TEXT NOT NULL,
    sha256 TEXT NOT NULL UNIQUE,
    content_type TEXT,
    size_bytes INTEGER NOT NULL DEFAULT 0,
    char_count INTEGER NOT NULL DEFAULT 0,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'ready',
    collection TEXT NOT NULL DEFAULT 'reference',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    meta TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    char_start INTEGER,
    char_end INTEGER,
    vector BLOB NOT NULL,
    dim INTEGER NOT NULL,
    meta TEXT NOT NULL DEFAULT '{}',
    UNIQUE(document_id, chunk_index)
);
CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_documents_collection ON documents(collection);
CREATE INDEX IF NOT EXISTS idx_documents_sha ON documents(sha256);
"""

def connect(db_path):
    con = sqlite3.connect(str(db_path))
    con.executescript(SCHEMA)
    con.commit()
    return con

def l2norm(vec):
    s = sum(x * x for x in vec) ** 0.5 or 1.0
    return [x / s for x in vec]

def embed(texts):
    """调用 Ollama：优先 /api/embed（批量），失败回退 /api/embeddings（单条）。"""
    body = json.dumps({"model": MODEL, "input": texts}).encode("utf-8")
    req = urllib.request.Request(f"{OLLAMA}/api/embed", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read().decode("utf-8"))
        return [l2norm(v) for v in data["embeddings"]]
    except Exception:
        out = []
        for t in texts:
            body = json.dumps({"model": MODEL, "prompt": t}).encode("utf-8")
            req = urllib.request.Request(f"{OLLAMA}/api/embeddings", data=body,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read().decode("utf-8"))
            out.append(l2norm(data["embedding"]))
        return out

def read_jsonl(path):
    items = []
    with open(path, encoding="utf-8-sig") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if not obj.get("clause"):
                raise SystemExit(f"第 {i} 行 clause 为空，按《切条与元数据规范》拒绝入库")
            items.append(obj)
    return items

def ingest(args):
    path = Path(args.jsonl)
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    items = read_jsonl(path)
    doc_id = args.doc_id or items[0].get("doc_id")
    if not doc_id:
        raise SystemExit("JSONL 缺少 doc_id，且未指定 --doc-id")

    texts = [it["text"] for it in items]
    if args.dry_run:
        vectors = [[0.0] * DIM for _ in texts]
        print(f"[dry-run] 跳过 Ollama，写入 {len(texts)} 个零向量用于结构自测")
    else:
        vectors = embed(texts)
        if len(vectors[0]) != DIM:
            raise SystemExit(f"向量维度异常：{len(vectors[0])}（期望 {DIM}）")

    con = connect(args.db)
    cur = con.cursor()
    if args.force:
        cur.execute("DELETE FROM documents WHERE id=?", (doc_id,))
    elif cur.execute("SELECT 1 FROM documents WHERE id=?", (doc_id,)).fetchone():
        raise SystemExit(f"文档 {doc_id} 已存在，如需覆盖请加 --force")

    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    raw = path.read_bytes()
    doc_meta = {"block_type": args.collection, "doc_id": doc_id,
                "spec_source": "docs/07_切条与元数据规范.md"}
    cur.execute("""INSERT INTO documents
        (id, source, filename, sha256, content_type, size_bytes, char_count,
         chunk_count, status, collection, created_at, updated_at, meta)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (doc_id, args.source or path.name, path.name, hashlib.sha256(raw).hexdigest(),
         "application/jsonl", len(raw), sum(len(t) for t in texts), len(items),
         "ready", args.collection, now, now, json.dumps(doc_meta, ensure_ascii=False)))

    for idx, (it, text, vec) in enumerate(zip(items, texts, vectors)):
        meta = {k: it.get(k) for k in ("block_type", "doc_id", "clause", "title",
                                       "chunk_id", "citation", "section") if it.get(k)}
        meta.setdefault("doc_id", doc_id)
        cur.execute("""INSERT INTO chunks
            (document_id, chunk_index, text, char_start, char_end, vector, dim, meta)
            VALUES (?,?,?,?,?,?,?,?)""",
            (doc_id, idx, text, None, None, array("f", vec).tobytes(), DIM,
             json.dumps(meta, ensure_ascii=False)))
    con.commit()
    print(f"入库完成：{doc_id} → collection={args.collection}，{len(items)} 块，维度 {DIM}")
    con.close()

def info(args):
    con = connect(args.db)
    cur = con.cursor()
    print(f"数据库：{args.db}")
    for r in cur.execute("""SELECT id, collection, chunk_count, size_bytes, status, source
                            FROM documents ORDER BY collection, id"""):
        print(f"  [{r[1]}] {r[0]}  块数={r[2]}  输入={r[5]}  ({r[4]})")
    bad = cur.execute("SELECT COUNT(*) FROM chunks WHERE dim<>? OR length(vector)<>dim*4", (DIM,)).fetchone()[0]
    print(f"  合计块数：{cur.execute('SELECT COUNT(*) FROM chunks').fetchone()[0]}；向量异常块：{bad}")
    con.close()

def main():
    ap = argparse.ArgumentParser(description="知识库 CLI（SQLite + Ollama bge-m3）")
    ap.add_argument("--db", default=str(DB_DEFAULT), help="数据库路径，默认 ./knowledge.db")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("ingest", help="从 JSONL 入库")
    p.add_argument("jsonl")
    p.add_argument("--collection", default="reference", choices=["normative", "reference"])
    p.add_argument("--doc-id", default=None)
    p.add_argument("--source", default=None, help="documents.source 记录值（建议用相对路径）")
    p.add_argument("--force", action="store_true", help="覆盖同 id 文档")
    p.add_argument("--dry-run", action="store_true", help="不调用 Ollama，写零向量（仅结构自测）")
    p.set_defaults(func=ingest)

    q = sub.add_parser("info", help="查看库内文档与块统计")
    q.set_defaults(func=info)

    args = ap.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()