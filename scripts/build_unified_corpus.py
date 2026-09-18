#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合并 DL/T 722 与 DL/T 572 条文，生成统一语料 JSONL。"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUTS = (
    ROOT / "vector_kb" / "corpus" / "clauses.jsonl",
    ROOT / "vector_kb" / "corpus" / "DLT-572-2021_clauses.jsonl",
)
DEFAULT_OUTPUT = ROOT / "data" / "corpus" / "clauses.jsonl"


def _dedupe_key(item: dict) -> tuple:
    if item.get("chunk_id"):
        return ("chunk_id", str(item["chunk_id"]))
    return (
        "clause",
        str(item.get("doc_id") or ""),
        str(item.get("clause") or ""),
        str(item.get("part") or ""),
    )


def build_unified_corpus(input_paths: list[Path], output_path: Path) -> dict:
    """读取并合并输入 JSONL，返回写入统计。"""
    documents = []
    seen = set()
    source_counts = Counter()

    for path in input_paths:
        if not path.is_file():
            continue
        with path.open("r", encoding="utf-8-sig") as stream:
            for line_number, line in enumerate(stream, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except Exception as exc:
                    raise ValueError(f"{path}:{line_number} 不是有效 JSON") from exc

                if not item.get("doc_id") or not item.get("clause") or not item.get("text"):
                    raise ValueError(f"{path}:{line_number} 缺少 doc_id/clause/text")
                key = _dedupe_key(item)
                if key in seen:
                    continue
                seen.add(key)
                documents.append(item)
                source_counts[str(item["doc_id"])] += 1

    if not documents:
        raise FileNotFoundError("没有找到可合并的条文 JSONL")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    with temporary_path.open("w", encoding="utf-8", newline="\n") as stream:
        for item in documents:
            stream.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")
    temporary_path.replace(output_path)

    return {
        "output": str(output_path),
        "total": len(documents),
        "by_doc": dict(sorted(source_counts.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="合并项目条文语料")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("inputs", nargs="*", type=Path)
    args = parser.parse_args()

    input_paths = args.inputs or list(DEFAULT_INPUTS)
    result = build_unified_corpus(input_paths, args.output)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())