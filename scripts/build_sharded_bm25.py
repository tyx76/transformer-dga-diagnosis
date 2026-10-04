#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按 domain 生成 plant_kb BM25 分片索引和轻量 metadata。"""

from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from vector_kb.bm25_retriever import PLANT_BM25_V2_VERSION, _v2_tokenize_fields

CORPUS_DEFAULT = PROJECT_ROOT / "knowledge" / "plant_kb" / "data" / "knowledge.jsonl"
OUTPUT_DIR_DEFAULT = PROJECT_ROOT / "knowledge" / "plant_kb" / "index"
MANIFEST_DEFAULT = "bm25_manifest.json"
METADATA_DEFAULT = "lightweight_metadata.jsonl"
FIELD_WEIGHTS = {"clause": 4, "section_path": 3, "title": 2, "text": 1}
HASH_CHUNK_SIZE = 1024 * 1024


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(HASH_CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _safe_filename(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or "unknown")).strip("._")
    return safe or "unknown"


def _json_dump_line(stream, item: dict[str, Any]) -> None:
    stream.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")


def _atomic_pickle(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as stream:
        pickle.dump(payload, stream, protocol=pickle.HIGHEST_PROTOCOL)
    temporary.replace(path)


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)

def build_shards(corpus_path: Path, output_dir: Path) -> dict[str, Any]:
    if not corpus_path.is_file():
        raise FileNotFoundError(f"语料不存在：{corpus_path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / MANIFEST_DEFAULT
    metadata_path = output_dir / METADATA_DEFAULT

    source_sha256 = _sha256_file(corpus_path)
    global_df: Counter[str] = Counter()
    total_length = 0
    total_documents = 0
    skipped = 0

    with tempfile.TemporaryDirectory(prefix="_bm25_shards_", dir=output_dir) as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        temp_streams: dict[str, Any] = {}
        seen: set[str] = set()
        metadata_temporary = metadata_path.with_suffix(metadata_path.suffix + ".tmp")

        try:
            with corpus_path.open("r", encoding="utf-8-sig") as corpus_stream, metadata_temporary.open(
                "w", encoding="utf-8"
            ) as metadata_stream:
                for line_number, line in enumerate(corpus_stream, start=1):
                    if not line.strip():
                        continue
                    try:
                        item = json.loads(line)
                    except Exception:
                        skipped += 1
                        continue

                    key = str(
                        item.get("id")
                        or item.get("chunk_id")
                        or f"{item.get('doc_id')}:{item.get('clause')}:{item.get('part')}"
                    )
                    if not key.strip(":"):
                        skipped += 1
                        continue
                    if key in seen:
                        skipped += 1
                        continue
                    seen.add(key)

                    text = str(item.get("text") or "").strip()
                    if not text:
                        skipped += 1
                        continue

                    domain = str(item.get("domain") or item.get("module") or "unknown").strip() or "unknown"
                    tokens = _v2_tokenize_fields(item, FIELD_WEIGHTS)
                    tf = Counter(tokens)
                    for token in tf:
                        global_df[token] += 1
                    total_length += sum(int(value) for value in tf.values())
                    total_documents += 1

                    doc = {
                        "id": key,
                        "doc_id": item.get("doc_id") or item.get("source_file") or item.get("source") or "",
                        "clause": item.get("clause"),
                        "title": item.get("title") or item.get("clause") or "",
                        "text": text,
                        "page": item.get("page"),
                        "citation": item.get("citation") or "",
                        "domain": domain,
                        "module": item.get("module") or domain,
                        "section_path": item.get("section_path") or item.get("clause") or "",
                        "tf": dict(tf),
                    }
                    if domain not in temp_streams:
                        temp_path = temp_dir / f"{_safe_filename(domain)}.jsonl"
                        temp_streams[domain] = temp_path.open("w", encoding="utf-8")
                    _json_dump_line(temp_streams[domain], doc)
                    _json_dump_line(
                        metadata_stream,
                        {
                            "doc_id": doc["doc_id"],
                            "clause": doc["clause"],
                            "title": doc["title"],
                            "domain": domain,
                            "citation": doc["citation"],
                            "is_citable": bool(doc["doc_id"] and doc["clause"]),
                        },
                    )
        finally:
            for stream in temp_streams.values():
                stream.close()

        metadata_temporary.replace(metadata_path)
        avgdl = float(total_length / total_documents) if total_documents else 0.0
        if avgdl <= 0:
            raise ValueError("无法生成分片：语料没有有效 token")

        manifest: dict[str, Any] = {
            "version": f"{PLANT_BM25_V2_VERSION}-sharded",
            "source": str(corpus_path),
            "source_sha256": source_sha256,
            "source_size_bytes": corpus_path.stat().st_size,
            "record_count": total_documents,
            "skipped_records": skipped,
            "avgdl": avgdl,
            "field_weights": FIELD_WEIGHTS,
            "shards": {},
        }

        for domain, stream in temp_streams.items():
            temp_path = Path(stream.name)
            docs: list[dict[str, Any]] = []
            domain_tokens: set[str] = set()
            with temp_path.open("r", encoding="utf-8-sig") as stream:
                for line in stream:
                    if not line.strip():
                        continue
                    doc = json.loads(line)
                    docs.append(doc)
                    domain_tokens.update(doc.get("tf") or {})

            if not docs:
                continue
            shard_df = {token: int(global_df[token]) for token in domain_tokens if token in global_df}
            shard_filename = f"bm25_{_safe_filename(domain)}.pkl"
            shard_path = output_dir / shard_filename
            payload = {
                "version": PLANT_BM25_V2_VERSION,
                "generated_from": str(corpus_path),
                "source_sha256": source_sha256,
                "domain": domain,
                "record_count": len(docs),
                "corpus_size": total_documents,
                "avgdl": avgdl,
                "field_weights": FIELD_WEIGHTS,
                "df": shard_df,
                "docs": docs,
                "embedded_metadata": True,
            }
            _atomic_pickle(shard_path, payload)
            manifest["shards"][domain] = {
                "file": shard_filename,
                "record_count": len(docs),
                "size_bytes": shard_path.stat().st_size,
                "sha256": _sha256_file(shard_path),
            }

    _atomic_json(manifest_path, manifest)
    print(
        f"分片完成：domains={len(manifest['shards'])} "
        f"records={manifest['record_count']} avgdl={manifest['avgdl']:.3f}"
    )
    for domain, entry in sorted(manifest["shards"].items()):
        print(
            f"  - {domain}: {entry['record_count']} 条，"
            f"{entry['size_bytes'] / (1024 * 1024):.2f} MB，{entry['file']}"
        )
    print(f"manifest: {manifest_path}")
    print(f"metadata: {metadata_path}")
    return manifest


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="按 domain 构建 plant_kb BM25 分片索引")
    parser.add_argument("--corpus", default=str(CORPUS_DEFAULT), help="knowledge.jsonl 路径")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR_DEFAULT), help="分片输出目录")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    build_shards(Path(args.corpus), Path(args.output_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())