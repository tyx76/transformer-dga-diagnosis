#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Adapt the member domain_mapping package into the main plant_kb format."""
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import re
import shutil
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from vector_kb.bm25_retriever import PLANT_BM25_V2_VERSION, _v2_tokenize_fields

PACKAGE_ROOT = PROJECT_ROOT / "submissions_pending_review" / "_unpacked_domain_mapping_20261004" / "plant_kb"
STAGING_ROOT = PROJECT_ROOT / "submissions_pending_review" / "_adapted_domain_mapping_20261005"
MAIN_ROOT = PROJECT_ROOT / "knowledge" / "plant_kb"
FIELD_WEIGHTS = {"clause": 4, "section_path": 3, "title": 2, "text": 1}
HASH_CHUNK = 1024 * 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(HASH_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_line(stream, item: dict[str, Any]) -> None:
    stream.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")


def atomic_pickle(path: Path, payload: dict[str, Any]) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("wb") as stream:
        pickle.dump(payload, stream, protocol=pickle.HIGHEST_PROTOCOL)
    temp.replace(path)


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or "unknown")).strip("._") or "unknown"


def mapping_rows() -> dict[str, dict[str, Any]]:
    path = PACKAGE_ROOT / "data" / "domain_mapping.jsonl"
    result = {}
    with path.open("r", encoding="utf-8-sig") as stream:
        for line in stream:
            if not line.strip():
                continue
            item = json.loads(line)
            result[str(item.get("chunk_id") or "")] = item
    return result


def domain_alt_value(mapping: dict[str, Any]) -> str:
    primary = str(mapping.get("domain_primary") or "").strip().lower()
    domains = {
        str(value).strip().lower()
        for value in (mapping.get("equipment_domains") or [])
        if str(value).strip()
    }
    domains.discard(primary)
    if not domains:
        return ""
    return "," + ",".join(sorted(domains)) + ","

def build_jsonl_and_lightweight(staging: Path, mappings: dict[str, dict[str, Any]]) -> dict[str, int]:
    data_dir = staging / "data"
    index_dir = staging / "index"
    data_dir.mkdir(parents=True, exist_ok=True)
    index_dir.mkdir(parents=True, exist_ok=True)
    knowledge_out = data_dir / "knowledge.jsonl"
    light_out = index_dir / "lightweight_metadata.jsonl"
    count = 0
    missing_mapping = 0
    empty_keys = 0
    with (PACKAGE_ROOT / "data" / "knowledge_domain.jsonl").open("r", encoding="utf-8-sig") as source, \
         knowledge_out.open("w", encoding="utf-8") as stream, light_out.open("w", encoding="utf-8") as light_stream:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            chunk_id = str(row.get("id") or "").strip()
            mapping = mappings.get(chunk_id)
            if mapping is None:
                missing_mapping += 1
                mapping = {}
            metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
            primary = str(mapping.get("domain_primary") or metadata.get("domain_primary") or row.get("domain") or "").strip()
            equipment_domains = mapping.get("equipment_domains") or metadata.get("equipment_domains") or ([row.get("domain")] if row.get("domain") else [])
            doc_id = str(row.get("doc_id") or metadata.get("doc_id") or row.get("source_file") or row.get("source") or "UNKNOWN").strip()
            clause = row.get("clause")
            if clause is None:
                clause = metadata.get("clause") or row.get("locator_value") or chunk_id
            clause = str(clause or chunk_id).strip()
            title = str(row.get("title") or metadata.get("title") or clause).strip()
            citation = str(row.get("citation") or metadata.get("citation") or row.get("source_file") or row.get("source") or "").strip()
            is_citable = mapping.get("is_citable")
            if is_citable is None:
                is_citable = row.get("is_citable")
            if is_citable is None:
                is_citable = metadata.get("is_citable")
            if is_citable is None:
                is_citable = bool(doc_id and clause)
            citation_eligible = mapping.get("citation_eligible")
            if citation_eligible is None:
                citation_eligible = row.get("citation_eligible")
            if citation_eligible is None:
                citation_eligible = metadata.get("citation_eligible")
            if citation_eligible is None:
                citation_eligible = bool(is_citable and doc_id and clause)
            alt = domain_alt_value(mapping)
            adapted = dict(row)
            adapted.update({
                "id": chunk_id,
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "clause": clause,
                "title": title,
                "citation": citation,
                "domain": str(row.get("domain") or primary or "").strip(),
                "domain_primary": primary,
                "domain_alt": alt,
                "equipment_domains": equipment_domains,
                "source_type": mapping.get("source_type") or metadata.get("source_type"),
                "specialties": mapping.get("specialties") or metadata.get("specialties") or [],
                "evidence_kind": mapping.get("evidence_kind") or metadata.get("evidence_kind"),
                "is_citable": bool(is_citable),
                "citation_eligible": bool(citation_eligible),
                "citable_reason": mapping.get("citable_reason") or metadata.get("citable_reason") or "",
                "citable_confidence": mapping.get("citable_confidence") or metadata.get("citable_confidence"),
                "citable_review_status": mapping.get("citable_review_status") or metadata.get("citable_review_status") or "",
                "domain_review_status": mapping.get("domain_review_status") or metadata.get("domain_review_status") or "",
                "domain_version": mapping.get("domain_version") or metadata.get("domain_version") or "",
            })
            json_line(stream, adapted)
            light = {
                "id": chunk_id,
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "clause": clause,
                "title": title,
                "citation": citation,
                "domain": adapted["domain"],
                "domain_primary": primary,
                "domain_alt": alt,
                "equipment_domains": equipment_domains,
                "source_type": adapted["source_type"],
                "specialties": adapted["specialties"],
                "evidence_kind": adapted["evidence_kind"],
                "is_citable": adapted["is_citable"],
                "citation_eligible": adapted["citation_eligible"],
                "source_file": row.get("source_file") or row.get("source") or "",
            }
            json_line(light_stream, light)
            count += 1
            if not doc_id or not clause:
                empty_keys += 1
    return {"count": count, "missing_mapping": missing_mapping, "empty_keys": empty_keys}

def migrate_database(staging: Path, mappings: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source_db = PACKAGE_ROOT / "knowledge_domain.db"
    target_db = staging / "index" / "knowledge.db"
    shutil.copy2(source_db, target_db)
    con = sqlite3.connect(str(target_db))
    cur = con.cursor()
    cur.execute("PRAGMA journal_mode=OFF")
    cur.execute("PRAGMA synchronous=OFF")
    cur.execute("PRAGMA temp_store=MEMORY")
    columns = [row[1] for row in cur.execute("PRAGMA table_info(knowledge)")]
    required = {"id", "vector", "dim"}
    if not required.issubset(columns):
        con.close()
        raise RuntimeError(f"knowledge 表缺少字段：{sorted(required - set(columns))}")

    cur.execute(
        "CREATE TABLE knowledge_domain_map("
        "chunk_id TEXT PRIMARY KEY, domain_alt TEXT, "
        "is_citable INTEGER, citation_eligible INTEGER)"
    )
    payload = []
    for chunk_id, mapping in mappings.items():
        payload.append((
            chunk_id,
            domain_alt_value(mapping),
            int(bool(mapping.get("is_citable"))),
            int(bool(mapping.get("citation_eligible"))),
        ))
    cur.executemany(
        "INSERT INTO knowledge_domain_map VALUES (?, ?, ?, ?)",
        payload,
    )
    cur.execute(
        "CREATE TABLE knowledge_new AS "
        "SELECT k.*, m.domain_alt AS domain_alt, "
        "m.is_citable AS is_citable, m.citation_eligible AS citation_eligible "
        "FROM knowledge k LEFT JOIN knowledge_domain_map m ON k.id = m.chunk_id"
    )
    cur.execute("DROP TABLE knowledge")
    cur.execute("ALTER TABLE knowledge_new RENAME TO knowledge")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_domain ON knowledge(domain)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_domain_alt ON knowledge(domain_alt)")
    con.commit()
    total = cur.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
    vectors = cur.execute("SELECT COUNT(*) FROM knowledge WHERE vector IS NOT NULL").fetchone()[0]
    dims = dict(cur.execute("SELECT dim, COUNT(*) FROM knowledge GROUP BY dim"))
    domains = dict(cur.execute("SELECT domain, COUNT(*) FROM knowledge GROUP BY domain"))
    con.close()
    return {"count": total, "vectors": vectors, "dims": dims, "domains": domains, "path": str(target_db)}

def build_bm25(staging: Path) -> dict[str, Any]:
    corpus_path = staging / "data" / "knowledge.jsonl"
    output_dir = staging / "index"
    output_dir.mkdir(parents=True, exist_ok=True)
    source_sha = sha256_file(corpus_path)
    global_df: Counter[str] = Counter()
    total_length = 0
    full_docs: list[dict[str, Any]] = []
    shard_docs: dict[str, list[dict[str, Any]]] = {}
    seen: set[str] = set()
    with corpus_path.open("r", encoding="utf-8-sig") as stream:
        for line in stream:
            if not line.strip():
                continue
            item = json.loads(line)
            chunk_id = str(item.get("chunk_id") or item.get("id") or "").strip()
            if not chunk_id or chunk_id in seen:
                continue
            seen.add(chunk_id)
            text = str(item.get("text") or "").strip()
            if not text:
                continue
            tf = Counter(_v2_tokenize_fields(item, FIELD_WEIGHTS))
            if not tf:
                continue
            total_length += sum(tf.values())
            for token in tf:
                global_df[token] += 1
            doc = {
                "id": chunk_id,
                "chunk_id": chunk_id,
                "doc_id": item.get("doc_id") or "",
                "clause": item.get("clause"),
                "title": item.get("title") or "",
                "text": text,
                "page": item.get("page"),
                "citation": item.get("citation") or "",
                "domain": item.get("domain"),
                "domain_primary": item.get("domain_primary"),
                "domain_alt": item.get("domain_alt") or "",
                "module": item.get("module") or item.get("domain") or "",
                "section_path": item.get("section_path") or item.get("clause") or "",
                "tf": dict(tf),
            }
            full_docs.append(doc)
            domains = {
                str(value or "").strip()
                for value in (item.get("equipment_domains") or [])
                if str(value or "").strip()
            }
            for value in (item.get("domain"), item.get("domain_primary")):
                value = str(value or "").strip()
                if value:
                    domains.add(value)
            for domain in domains:
                domain = str(domain or "").strip()
                if not domain:
                    continue
                shard = dict(doc)
                shard["domain"] = domain
                shard_docs.setdefault(domain, []).append(shard)

    if not full_docs:
        raise ValueError("adapted knowledge.jsonl has no BM25 documents")
    avgdl = total_length / len(full_docs)
    full_payload = {
        "version": PLANT_BM25_V2_VERSION,
        "generated_from": str(corpus_path),
        "source_sha256": source_sha,
        "record_count": len(full_docs),
        "corpus_size": len(full_docs),
        "avgdl": avgdl,
        "field_weights": FIELD_WEIGHTS,
        "df": dict(global_df),
        "docs": full_docs,
        "embedded_metadata": True,
    }
    atomic_pickle(output_dir / "bm25_index.pkl", full_payload)
    manifest = {
        "version": f"{PLANT_BM25_V2_VERSION}-sharded",
        "source": str(corpus_path),
        "source_sha256": source_sha,
        "record_count": len(full_docs),
        "avgdl": avgdl,
        "field_weights": FIELD_WEIGHTS,
        "shards": {},
    }
    for domain, docs in shard_docs.items():
        tokens = set()
        for doc in docs:
            tokens.update(doc.get("tf") or {})
        shard_df = {token: int(global_df[token]) for token in tokens if token in global_df}
        filename = f"bm25_{safe_name(domain)}.pkl"
        shard_path = output_dir / filename
        payload = {
            "version": PLANT_BM25_V2_VERSION,
            "generated_from": str(corpus_path),
            "source_sha256": source_sha,
            "domain": domain,
            "record_count": len(docs),
            "corpus_size": len(full_docs),
            "avgdl": avgdl,
            "field_weights": FIELD_WEIGHTS,
            "df": shard_df,
            "docs": docs,
            "embedded_metadata": True,
        }
        atomic_pickle(shard_path, payload)
        manifest["shards"][domain] = {
            "file": filename,
            "record_count": len(docs),
            "size_bytes": shard_path.stat().st_size,
            "sha256": sha256_file(shard_path),
        }
    atomic_json(output_dir / "bm25_manifest.json", manifest)
    return {
        "records": len(full_docs),
        "avgdl": avgdl,
        "index": str(output_dir / "bm25_index.pkl"),
        "shards": {key: value["record_count"] for key, value in manifest["shards"].items()},
    }

def copy_to_main(staging: Path) -> None:
    data_dir = MAIN_ROOT / "data"
    index_dir = MAIN_ROOT / "index"
    data_dir.mkdir(parents=True, exist_ok=True)
    index_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(staging / "data" / "knowledge.jsonl", data_dir / "knowledge.jsonl")
    for name in ("knowledge.db", "lightweight_metadata.jsonl", "bm25_index.pkl", "bm25_manifest.json"):
        shutil.copy2(staging / "index" / name, index_dir / name)
    for path in staging.glob("index/bm25_*.pkl"):
        shutil.copy2(path, index_dir / path.name)


def write_report(summary: dict[str, Any]) -> Path:
    path = PROJECT_ROOT / "docs" / "domain_mapping适配报告_20261005.md"
    lines = [
        "# domain_mapping 适配报告",
        "",
        "> 日期：2026-10-05",
        "> 输入包：`domain_mapping_and_knowledge_20261004.zip`",
        "> 向量：复用包内 DB 向量，不重新生成。",
        "",
        "## 适配结果",
        "",
        "| 项目 | 结果 |",
        "|---|---|",
        f"| knowledge.jsonl | {summary['jsonl']['count']} 条 |",
        f"| lightweight_metadata | {summary['jsonl']['count']} 条 |",
        f"| DB 记录/向量 | {summary['database']['count']}/{summary['database']['vectors']} |",
        f"| DB 维度 | {summary['database']['dims']} |",
        f"| BM25 文档数 | {summary['bm25']['records']} |",
        f"| BM25 平均文档长度 | {summary['bm25']['avgdl']:.3f} |",
        f"| BM25 分片 | {summary['bm25']['shards']} |",
        "",
        "## 文件位置",
        "",
        "- `knowledge/plant_kb/index/knowledge.db`",
        "- `knowledge/plant_kb/data/knowledge.jsonl`",
        "- `knowledge/plant_kb/index/lightweight_metadata.jsonl`",
        "- `knowledge/plant_kb/index/bm25_index.pkl`",
        "- `knowledge/plant_kb/index/bm25_manifest.json`",
        "",
        "## 适配说明",
        "",
        "- `chunk_id` 使用原始 `id`。",
        "- `domain_alt` 以逗号包裹字符串保存，支持多备选域。",
        "- DB 直接复用包内 vector/dim，仅补充 domain_alt/citation 字段。",
        "- BM25 按 equipment_domains 复制到备选域分片。",
        "- 原包和适配前主路径均已保留备份。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="适配成员 domain_mapping 知识库包")
    parser.add_argument("--apply", action="store_true", help="适配后覆盖主路径")
    args = parser.parse_args(argv)

    if STAGING_ROOT.exists():
        shutil.rmtree(STAGING_ROOT)
    STAGING_ROOT.mkdir(parents=True, exist_ok=True)
    mappings = mapping_rows()
    jsonl_summary = build_jsonl_and_lightweight(STAGING_ROOT, mappings)
    db_summary = migrate_database(STAGING_ROOT, mappings)
    bm25_summary = build_bm25(STAGING_ROOT)
    summary = {"jsonl": jsonl_summary, "database": db_summary, "bm25": bm25_summary}
    if args.apply:
        copy_to_main(STAGING_ROOT)
    report = write_report(summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Report: {report}")
    print(f"Apply: {bool(args.apply)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
