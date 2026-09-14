#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [阶段交接] 接口保留：ingest()/info 为知识库构建接口；query() 检索接口已实现。详见 docs/05。
"""知识库 CLI：从 JSONL 构建 / 查看 SQLite 向量库（Ollama bge-m3）。

用法：
    python cli.py ingest 语料/clauses.jsonl --collection normative --force
    python cli.py ingest 语料/DLT-572-2021_clauses.jsonl --collection reference --force
    python cli.py ingest 语料/clauses.jsonl --collection normative --dry-run   # 不调 Ollama，写零向量（自测）
    python cli.py info
    python cli.py query "乙炔超标该怎么处理"   # 语义检索 Top-3
    python cli.py ask "乙炔超标该怎么处理"     # 检索 + DeepSeek 生成（需 DEEPSEEK_API_KEY）

依赖：Python 3.10+（仅标准库）；Ollama 服务 + bge-m3:latest（真实入库时需要）
"""
import argparse, datetime, hashlib, json, os, re, sqlite3, sys, urllib.request
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
DEEPSEEK_API_BASE = os.environ.get("DEEPSEEK_API_BASE", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
SYSTEM_PROMPT = (
    "你是电力变压器故障诊断专家。请严格基于提供的规程条文回答。"
    "每条结论必须标注依据，格式为【依据：doc_id 第clause条】。"
    "如果条文无法回答问题，直接回复“资料未覆盖”，不要编造。"
    "不要给出规程之外的处置建议。"
)

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
                "spec_source": "docs/07_chunking_and_metadata_spec.md"}
    cur.execute("""INSERT INTO documents
        (id, source, filename, sha256, content_type, size_bytes, char_count,
         chunk_count, status, collection, created_at, updated_at, meta)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (doc_id, args.source or path.name, path.name, hashlib.sha256(raw).hexdigest(),
         "application/jsonl", len(raw), sum(len(t) for t in texts), len(items),
         "ready", args.collection, now, now, json.dumps(doc_meta, ensure_ascii=False)))

    for idx, (it, text, vec) in enumerate(zip(items, texts, vectors)):
        meta = {k: it.get(k) for k in ("block_type", "doc_id", "clause", "title",
                                       "chunk_id", "citation", "section", "page") if it.get(k)}
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


def _cosine(a, b):
    """余弦相似度（两个向量都已 L2 归一化时即为点积）。"""
    if not a or not b or len(a) != len(b):
        return 0.0
    s = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5 or 1.0
    nb = sum(y * y for y in b) ** 0.5 or 1.0
    return s / (na * nb)

def _load_vectors(con):
    """读出所有块及其向量/元数据；过滤 clause 为空的块（规范要求检索结果必带条号）。"""
    out = []
    for r in con.execute("SELECT id, document_id, text, vector, dim, meta FROM chunks"):
        try:
            meta = json.loads(r[5]) if r[5] else {}
        except Exception:
            meta = {}
        if not meta.get("clause"):
            continue
        try:
            vec = array("f"); vec.frombytes(r[3]); vec = list(vec)
        except Exception:
            continue
        out.append({"id": r[0], "doc_id": meta.get("doc_id") or r[1], "text": r[2],
                    "vec": vec, "dim": r[4], "meta": meta})
    return out

def retrieve(question: str, top_k: int = 3, min_score: float = 0.35, db: str = DB_DEFAULT) -> list[dict]:
    """语义检索（可复用接口）。

    返回 list[dict]，每项含：doc_id / clause / title / text / page / score / citation。
    - 自动过滤 clause 为空的块；
    - 无命中或全部低于 min_score 时返回空列表 []；
    - Embedding 或数据库不可用时抛 RuntimeError（由调用方决定提示方式）。
    """
    top_k = max(1, int(top_k))
    try:
        con = connect(db)
        chunks = _load_vectors(con)
        con.close()
    except Exception as e:
        raise RuntimeError(f"数据库不可用（{db}）：{e}") from e
    if not chunks:
        return []
    try:
        qvec = embed([question])[0]
    except Exception as e:
        raise RuntimeError(f"embedding unavailable: {e}") from e

    scored = [(_cosine(qvec, c["vec"]), c) for c in chunks]
    scored.sort(key=lambda x: x[0], reverse=True)
    hits = []
    for score, c in scored[:top_k]:
        if score < min_score:
            continue
        m = c["meta"]
        hits.append({
            "doc_id": m.get("doc_id") or c["doc_id"],
            "clause": m.get("clause"),
            "title": m.get("title") or "",
            "text": c["text"],
            "page": m.get("page"),
            "score": score,
            "citation": m.get("citation") or "",
        })
    return hits

def query(args):
    """CLI 层：调用 retrieve()，只负责格式化打印。"""
    try:
        hits = retrieve(args.question, args.top_k, args.min_score, args.db)
    except RuntimeError as e:
        print(f"无法调用本地 Embedding/数据库（Ollama {OLLAMA} / 模型 {MODEL}）：{e}")
        print("请确认：1) ollama 服务已启动；2) 已执行 ollama pull bge-m3；3) 数据库路径正确")
        return
    if not hits:
        print("未在知识库中检索到相关条文，无法提供建议")
        return
    print(f"问题：{args.question}")
    print(f"检索到 {len(hits)} 条相关条文（余弦相似度 ≥ {args.min_score}）：")
    for i, h in enumerate(hits, 1):
        print("-" * 64)
        print(f"[{i}] 相似度 {h['score']:.4f}")
        print(f"    doc_id : {h['doc_id']}")
        print(f"    clause : {h['clause'] or '（未记录）'}")
        print(f"    title  : {h['title'] or '（未记录）'}")
        print(f"    page   : {h['page'] if h['page'] not in (None, '') else '（未记录）'}")
        if h["citation"]:
            print(f"    citation: {h['citation']}")
        print("    text   :")
        for line in str(h["text"]).splitlines():
            print("      " + line)
    print("-" * 64)


def _load_env():
    """读取 DEEPSEEK_API_KEY：优先环境变量，其次项目根/.env（标准库解析，不引入依赖）。"""
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key:
        return key.strip()
    for cand in (ROOT / ".env", ROOT.parent / ".env"):
        if not cand.exists():
            continue
        try:
            for line in cand.read_text(encoding="utf-8-sig").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k.strip() == "DEEPSEEK_API_KEY":
                    return v.strip().strip('"').strip("'")
        except Exception:
            pass
    return ""

def _cite(doc_id, clause):
    """依据标注（通用规则，非问题硬编码）：数字条号补“条”，含表号的条号保留原样。"""
    doc = str(doc_id or "").strip()
    c = str(clause or "").strip()
    if not c:
        return doc
    if c[0].isdigit():
        return f"{doc} 第{c}条" if re.fullmatch(r"[0-9.]+", c) else f"{doc} 第{c}"
    return f"{doc} {c}"

def build_context(chunks: list[dict]) -> str:
    """把 retrieve() 结果拼成参考上下文（对任意问题/任意 chunks 通用）。"""
    parts = []
    for c in chunks or []:
        doc = c.get("doc_id") or ""
        clause = c.get("clause") or ""
        text = str(c.get("text") or "").strip()
        parts.append(f"【依据：{_cite(doc, clause)}】{text}")
    return "\n\n".join(parts)

def generate(question: str, chunks: list[dict]) -> str:
    """基于检索条文调用 DeepSeek 生成回答。

    - chunks 为空：不调用 API，直接返回“资料未覆盖，无法回答”；
    - 无 API Key / 调用失败：抛 RuntimeError（由调用方提示）。
    """
    if not chunks:
        return "资料未覆盖，无法回答"
    context = build_context(chunks)
    key = _load_env()
    if not key:
        raise RuntimeError("未找到 DEEPSEEK_API_KEY（请设置环境变量或写入项目根目录 .env）")
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"参考条文：\n{context}\n\n问题：{question}"},
        ],
        "temperature": 0.1,
        "max_tokens": 800,
    }
    req = urllib.request.Request(
        f"{DEEPSEEK_API_BASE}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"DeepSeek API 调用失败：{e}") from e
    try:
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        raise RuntimeError(f"DeepSeek 返回格式异常：{data}") from e

def ask(args):
    """CLI：检索 → 生成 → 打印（对任意问题通用）。"""
    try:
        hits = retrieve(args.question, args.top_k, args.min_score, args.db)
    except RuntimeError as e:
        print(f"检索失败：{e}")
        return
    if args.show_sources:
        print(f"检索到 {len(hits)} 条条文：")
        for h in hits:
            print(f"  - {_cite(h.get('doc_id'), h.get('clause'))}  {h.get('title') or ''}")
    try:
        answer = generate(args.question, hits)
    except RuntimeError as e:
        print(f"生成失败：{e}")
        return
    print(answer)

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
    r = sub.add_parser("query", help="语义检索条文（Top-k，输出 doc_id/clause/title/text/page）")
    r.add_argument("question", help="查询文本，如：乙炔超标该怎么处理")
    r.add_argument("--top-k", type=int, default=3, help="返回条数，默认 3")
    r.add_argument("--min-score", type=float, default=0.35, help="余弦相似度阈值，默认 0.35")
    r.set_defaults(func=query)
    s = sub.add_parser("ask", help="检索 + DeepSeek 生成回答（强制标注依据）")
    s.add_argument("question", help="问题文本，如：乙炔超标该怎么处理")
    s.add_argument("--top-k", type=int, default=3, help="检索条数，默认 3")
    s.add_argument("--min-score", type=float, default=0.35, help="余弦相似度阈值，默认 0.35")
    s.add_argument("--show-sources", action="store_true", help="先打印检索到的条文")
    s.set_defaults(func=ask)

    args = ap.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
