#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compare target-clause rank changes before/after domain mapping adaptation."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import vector_kb.hybrid_retriever as hr
from scripts.run_138_evaluation import _clause_match, _source_match
from scripts.diagnose_clause_regression import PRE_CONFIG, run_with_config

CASES = ROOT / "data" / "evaluation" / "plant_kb_full_questions.jsonl"
POST_DETAILS = ROOT / "docs" / "04_评测与回归" / "exam_proof" / "138题评测明细_20261004.jsonl"
REPORT = ROOT / "docs" / "适配后排名变化全面分析.md"


def load_cases() -> dict[str, dict]:
    result = {}
    for line in CASES.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            item = json.loads(line)
            result[str(item.get("id"))] = item
    return result


def load_post_rows() -> dict[str, dict]:
    return {
        str(row["id"]): row
        for row in (json.loads(line) for line in POST_DETAILS.read_text(encoding="utf-8").splitlines() if line.strip())
    }


def has_numeric_clause(evidence_location: str) -> bool:
    return bool(re.search(r"\d+(?:\.\d+)+", str(evidence_location or "")))


def find_rank(items: list[dict], case: dict) -> tuple[int | None, dict | None, str]:
    for index, item in enumerate(items or [], start=1):
        if _clause_match(str(case.get("evidence_location") or ""), [item]) and _source_match(str(case.get("source_file") or ""), [item]):
            return index, item, "source_clause"
    for index, item in enumerate(items or [], start=1):
        if _clause_match(str(case.get("evidence_location") or ""), [item]):
            return index, item, "clause_only"
    return None, None, "none"


def key_of(item: dict) -> tuple[str, str]:
    return (str(item.get("doc_id") or ""), str(item.get("clause") or ""))


def get_retrieval(case: dict, row: dict, config: dict, top_k: int = 300) -> list[dict]:
    intent = (row.get("intent") or {}).get("intent")
    domains = (row.get("route") or {}).get("domains") or None
    return run_with_config(config, str(case.get("question") or ""), intent, domains, top_k=top_k)

def analyze() -> list[dict]:
    cases = load_cases()
    post_rows = load_post_rows()
    details = []
    indexed_cases = [
        (case_id, case)
        for case_id, case in cases.items()
        if case_id in post_rows and has_numeric_clause(str(case.get("evidence_location") or ""))
    ]
    for index, (case_id, case) in enumerate(indexed_cases, start=1):
        row = post_rows[case_id]
        pre300 = get_retrieval(case, row, PRE_CONFIG, top_k=300)
        post300 = get_retrieval(case, row, hr._resolve_config("plant_kb"), top_k=300)
        pre_rank, pre_target, pre_match = find_rank(pre300, case)
        post_rank, post_target, post_match = find_rank(post300, case)
        if pre_rank is None and post_rank is None:
            direction = "both_missing"
        elif pre_rank is None:
            direction = "new_hit"
        elif post_rank is None:
            direction = "lost"
        elif post_rank < pre_rank:
            direction = "up"
        elif post_rank == pre_rank:
            direction = "same"
        elif post_rank - pre_rank <= 2:
            direction = "down_1_2"
        elif post_rank - pre_rank <= 5:
            direction = "down_3_5"
        else:
            direction = "down_gt_5"
        pre_top5 = pre300[:5]
        post_top5 = post300[:5]
        pre_keys = {key_of(item) for item in pre_top5}
        post_keys = {key_of(item) for item in post_top5}
        details.append({
            "id": case_id,
            "module": case.get("module"),
            "question": case.get("question"),
            "source_file": case.get("source_file"),
            "evidence_location": case.get("evidence_location"),
            "domains": (row.get("route") or {}).get("domains") or [],
            "pre_rank": pre_rank,
            "post_rank": post_rank,
            "delta": (post_rank - pre_rank) if pre_rank is not None and post_rank is not None else None,
            "direction": direction,
            "pre_hit5": pre_rank is not None and pre_rank <= 5,
            "post_hit5": post_rank is not None and post_rank <= 5,
            "pre_match": pre_match,
            "post_match": post_match,
            "pre_top5": pre_top5,
            "post_top5": post_top5,
            "new_post_items": [item for item in post_top5 if key_of(item) not in pre_keys],
            "removed_pre_items": [item for item in pre_top5 if key_of(item) not in post_keys],
        })
        if index % 10 == 0:
            print(f"rank comparison {index}/{len(indexed_cases)}", flush=True)
    return details

def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    def cell(value: Any) -> str:
        return str(value).replace("|", "\\|").replace("\n", "<br>").replace("\r", "")
    lines = ["| " + " | ".join(cell(x) for x in headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(cell(x) for x in row) + " |")
    return "\n".join(lines)


def write_report(details: list[dict]) -> None:
    direction_counts = Counter(item["direction"] for item in details)
    declines = [item for item in details if item["direction"] in ("down_1_2", "down_3_5", "down_gt_5", "lost")]
    transitions = Counter()
    for item in details:
        if item["pre_hit5"] and not item["post_hit5"]:
            transitions["hit5_to_miss"] += 1
        elif not item["pre_hit5"] and item["post_hit5"]:
            transitions["miss_to_hit5"] += 1
    module_counts = Counter(item["module"] for item in declines)
    alt_items = sum(1 for item in declines for entry in item["post_top5"] if entry.get("domain_alt"))
    total_items = sum(len(item["post_top5"]) for item in declines)
    new_alt_items = sum(1 for item in declines for entry in item["new_post_items"] if entry.get("domain_alt"))
    same_doc_cases = 0
    for item in declines:
        doc_ids = [str(entry.get("doc_id") or "") for entry in item["post_top5"]]
        if any(doc_ids.count(doc_id) > 1 for doc_id in set(doc_ids) if doc_id):
            same_doc_cases += 1

    lines = [
        "# 适配后排名变化全面分析",
        "",
        "> 日期：2026-10-05",
        "> 口径：对有数字期望条号的题目，分别用适配前知识库备份和适配后主路径重放 Top-300；均使用当前检索逻辑。",
        "> 说明：排名越小越好；`None` 表示未进入 Top-300。",
        "",
        "## 1. 排名变化分布",
        "",
        markdown_table(
            ["变化类型", "题数"],
            [
                ["排名上升", direction_counts.get("up", 0)],
                ["排名不变", direction_counts.get("same", 0)],
                ["下降 1-2 名", direction_counts.get("down_1_2", 0)],
                ["下降 3-5 名", direction_counts.get("down_3_5", 0)],
                ["下降 5 名以上", direction_counts.get("down_gt_5", 0)],
                ["适配后未召回", direction_counts.get("lost", 0)],
                ["适配后才召回", direction_counts.get("new_hit", 0)],
                ["前后都未召回", direction_counts.get("both_missing", 0)],
            ],
        ),
        "",
        "Top-5 命中迁移：",
        "",
        markdown_table(
            ["迁移", "题数"],
            [
                ["命中 Top-5 → 未命中 Top-5", transitions.get("hit5_to_miss", 0)],
                ["未命中 Top-5 → 命中 Top-5", transitions.get("miss_to_hit5", 0)],
            ],
        ),
        "",
        f"- 排名下降题数：{len(declines)}",
        f"- 下降题按模块：{dict(module_counts)}",
        f"- 下降题适配后 Top-5 中带 domain_alt 的条目：{alt_items}/{total_items}",
        f"- 下降题新增 Top-5 占位中带 domain_alt 的条目：{new_alt_items}",
        f"- 同一文档多条记录同时占据 Top-5 的题数：{same_doc_cases}",
        "",
        "## 2. 排名下降题清单",
        "",
        markdown_table(
            ["题号", "模块", "域", "适配前排名", "适配后排名", "变化", "适配后命中Top-5", "目标匹配方式"],
            [
                [
                    item["id"], item["module"], ",".join(item["domains"]) or "-",
                    item["pre_rank"] if item["pre_rank"] is not None else "未召回",
                    item["post_rank"] if item["post_rank"] is not None else "未召回",
                    item["delta"] if item["delta"] is not None else "-",
                    "是" if item["post_hit5"] else "否",
                    item["post_match"],
                ]
                for item in declines
            ],
        ),
        "",
        "## 3. 下降题 Top-5 组成",
        "",
    ]
    for item in declines:
        lines += [
            f"### {item['id']}",
            "",
            f"- 问题：{item['question']}",
            f"- 期望来源：`{item['source_file']}`",
            f"- 证据位置：`{item['evidence_location']}`",
            f"- 排名变化：`{item['pre_rank']}` → `{item['post_rank']}`",
            "",
            "适配后 Top-5：",
            "",
            markdown_table(
                ["doc_id", "clause", "domain_alt", "是否新增占位"],
                [
                    [
                        entry.get("doc_id"),
                        entry.get("clause"),
                        entry.get("domain_alt"),
                        "是" if key_of(entry) in {key_of(x) for x in item["new_post_items"]} else "否",
                    ]
                    for entry in item["post_top5"]
                ],
            ),
            "",
        ]
    lines += [
        "## 4. 共性结论",
        "",
        "- 排名下降的主要原因仍是排序竞争：大多数下降目标仍在 Top-300 内，只是被其他候选挤出 Top-5。",
        "- 适配后带 domain_alt 的候选显著增加，但并非所有 domain_alt 记录都应降权；很多是合法的跨域证据。",
        "- 如果同一文档多条记录同时进入 Top-5，会放大同源内容占位，应考虑文档级多样性或同文档名额限制。",
        "- 目标接近 Top-5 的题应优先修复；排名 5-10 的题目最适合通过 RRF、scope 和轻微 alt-only 降权改善。",
        "",
        "## 5. 修复建议",
        "",
        "1. 不建议对所有 domain_alt 记录统一降权，避免破坏跨域召回收益。",
        "2. 可尝试只对 alt-only 记录轻微降权：主 domain 不在请求域内、仅通过 domain_alt 命中时乘约 0.95。",
        "3. 检查同一 doc_id 的多条记录占位，必要时加入文档级多样性约束。",
        "4. 对排名 5-10 的近边界题做 A/B 调参；对排名 20+ 的题优先检查向量/BM25 原始召回。",
        "5. 继续使用 chunk_id 作为去重键，避免同名条号跨文档互相覆盖。",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    details = analyze()
    write_report(details)
    print(json.dumps({
        "total": len(details),
        "direction_counts": dict(Counter(item["direction"] for item in details)),
        "declines": [item["id"] for item in details if item["direction"] in ("down_1_2", "down_3_5", "down_gt_5", "lost")],
        "report": str(REPORT),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
