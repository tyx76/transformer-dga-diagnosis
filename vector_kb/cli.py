#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知识库 CLI：负责 ingest / info / query / ask 四个命令。

核心能力已拆分到以下模块：
    embeddings.py  embedding 调用
    store.py       SQLite 连接和表结构
    retrieval.py   条文检索
    generation.py  DeepSeek 生成
"""

import argparse
import datetime
import hashlib
import json
import sys
from array import array
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vector_kb.embeddings import DIM, MODEL, OLLAMA, embed
from vector_kb.generation import _cite, generate
from vector_kb.retrieval import retrieve
from vector_kb.store import DB_DEFAULT, connect

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def read_jsonl(path):
    """读取 JSONL 条文，拒绝 clause 为空的记录。"""
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
    """从 JSONL 构建 SQLite 向量库。"""
    path = Path(args.jsonl)
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    items = read_jsonl(path)
    doc_id = args.doc_id or items[0].get("doc_id")
    if not doc_id:
        raise SystemExit("JSONL 缺少 doc_id，且未指定 --doc-id")

    texts = [item["text"] for item in items]
    if args.dry_run:
        vectors = [[0.0] * DIM for _ in texts]
        print(f"[dry-run] 不调用 Ollama，写入 {len(texts)} 条零向量，用于结构自测")
    else:
        vectors = embed(texts)
        if len(vectors[0]) != DIM:
            raise SystemExit(f"向量维度异常：{len(vectors[0])}，期望 {DIM}")

    con = connect(args.db)
    cur = con.cursor()
    if args.force:
        cur.execute("DELETE FROM documents WHERE id=?", (doc_id,))
    elif cur.execute("SELECT 1 FROM documents WHERE id=?", (doc_id,)).fetchone():
        raise SystemExit(f"文档 {doc_id} 已存在，如需覆盖请加 --force")

    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    raw = path.read_bytes()
    doc_meta = {
        "block_type": args.collection,
        "doc_id": doc_id,
        "spec_source": "docs/07_chunking_and_metadata_spec.md",
    }
    cur.execute(
        """INSERT INTO documents
        (id, source, filename, sha256, content_type, size_bytes, char_count,
         chunk_count, status, collection, created_at, updated_at, meta)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            doc_id,
            args.source or path.name,
            path.name,
            hashlib.sha256(raw).hexdigest(),
            "application/jsonl",
            len(raw),
            sum(len(t) for t in texts),
            len(items),
            "ready",
            args.collection,
            now,
            now,
            json.dumps(doc_meta, ensure_ascii=False),
        ),
    )

    for idx, (item, text, vec) in enumerate(zip(items, texts, vectors)):
        meta = {
            key: item.get(key)
            for key in ("block_type", "doc_id", "clause", "title", "chunk_id", "citation", "section", "page")
            if item.get(key)
        }
        meta.setdefault("doc_id", doc_id)
        cur.execute(
            """INSERT INTO chunks
            (document_id, chunk_index, text, char_start, char_end, vector, dim, meta)
            VALUES (?,?,?,?,?,?,?,?)""",
            (doc_id, idx, text, None, None, array("f", vec).tobytes(), DIM, json.dumps(meta, ensure_ascii=False)),
        )
    con.commit()
    print(f"入库完成：{doc_id}｜collection={args.collection}｜{len(items)} 块｜维度 {DIM}")
    con.close()


def info(args):
    """查看知识库文档和向量统计。"""
    con = connect(args.db)
    cur = con.cursor()
    print(f"数据库：{args.db}")
    for row in cur.execute(
        """SELECT id, collection, chunk_count, size_bytes, status, source
           FROM documents ORDER BY collection, id"""
    ):
        print(f"  [{row[1]}] {row[0]}  块数={row[2]}  来源={row[5]}  ({row[4]})")
    bad = cur.execute(
        "SELECT COUNT(*) FROM chunks WHERE dim<>? OR length(vector)<>dim*4",
        (DIM,),
    ).fetchone()[0]
    total = cur.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    print(f"  合计块数：{total}；向量异常块：{bad}")
    con.close()


def query(args):
    """CLI 入口：只格式化打印 retrieve() 的结果。"""
    try:
        hits = retrieve(args.question, args.top_k, args.min_score, args.db)
    except RuntimeError as e:
        print(f"无法调用本地 Embedding/数据库（Ollama {OLLAMA} / 模型 {MODEL}）：{e}")
        print("请确认：1) ollama 服务已启动；2) 已执行 ollama pull bge-m3；3) 数据库路径正确")
        return
    if not hits:
        print("未在知识库中检索到相关条文，模型无法提供建议")
        return
    print(f"问题：{args.question}")
    print(f"检索到 {len(hits)} 条相关条文（余弦相似度 ≥ {args.min_score}）")
    for i, hit in enumerate(hits, 1):
        print("-" * 64)
        print(f"[{i}] 相似度 {hit['score']:.4f}")
        print(f"    doc_id : {hit['doc_id']}")
        print(f"    clause : {hit['clause'] or '（未记录）'}")
        print(f"    title  : {hit['title'] or '（未记录）'}")
        print(f"    page   : {hit['page'] if hit['page'] not in (None, '') else '（未记录）'}")
        if hit["citation"]:
            print(f"    citation: {hit['citation']}")
        print("    text   :")
        for line in str(hit["text"]).splitlines():
            print("      " + line)
    print("-" * 64)


def ask(args):
    """CLI 入口：检索 + 生成 + 打印。"""
    try:
        hits = retrieve(args.question, args.top_k, args.min_score, args.db)
    except RuntimeError as e:
        print(f"检索失败：{e}")
        return
    if args.show_sources:
        print(f"检索到 {len(hits)} 条条文：")
        for hit in hits:
            print(f"  - {_cite(hit.get('doc_id'), hit.get('clause'))}  {hit.get('title') or ''}")
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
    r.add_argument("--min-score", type=float, default=0.45, help="余弦相似度阈值，默认 0.45")
    r.set_defaults(func=query)

    s = sub.add_parser("ask", help="检索 + DeepSeek 生成回答（强制标注依据）")
    s.add_argument("question", help="问题文本，如：乙炔超标该怎么处理")
    s.add_argument("--top-k", type=int, default=3, help="检索条数，默认 3")
    s.add_argument("--min-score", type=float, default=0.45, help="余弦相似度阈值，默认 0.45")
    s.add_argument("--show-sources", action="store_true", help="先打印检索到的条文")
    s.set_defaults(func=ask)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()