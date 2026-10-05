#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnose clause-hit regressions after the domain mapping adaptation."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import vector_kb.hybrid_retriever as hr
from scripts.run_138_evaluation import _clause_match, _source_match
from vector_kb.citation_verifier import normalize_clause

CASES = ROOT / "data" / "evaluation" / "plant_kb_full_questions.jsonl"
POST_DETAILS = ROOT / "docs" / "04_评测与回归" / "exam_proof" / "138题评测明细_20261004.jsonl"
REPORT = ROOT / "docs" / "条号命中回退诊断.md"
PRE_ROOT = ROOT / "backups" / "plant_kb_before_domain_adapt_20261005"
PRE_CONFIG = {
    "vector_db": str(PRE_ROOT / "index" / "knowledge.db"),
    "bm25_corpus": str(PRE_ROOT / "data" / "knowledge.jsonl"),
    "bm25_index": str(PRE_ROOT / "index" / "bm25_index.pkl"),
    "embedding_source": None,
}


def load_cases() -> dict[str, dict]:
    wanted = {str(row.get("id")) for row in (json.loads(line) for line in POST_DETAILS.read_text(encoding="utf-8").splitlines() if line.strip())}
    result = {}
    for line in CASES.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if item.get("id") in wanted:
            result[str(item["id"])] = item
    return result


def load_post_rows() -> dict[str, dict]:
    return {
        str(row["id"]): row
        for row in (json.loads(line) for line in POST_DETAILS.read_text(encoding="utf-8").splitlines() if line.strip())
    }


def run_with_config(config: dict, question: str, intent: str | None, domains: list[str] | None, top_k: int, candidate_k: int = 300):
    old = hr.BACKEND_CONFIG.get("plant_kb")
    hr.BACKEND_CONFIG["plant_kb"] = config
    try:
        return hr.hybrid_retrieve(
            question,
            top_k=top_k,
            candidate_k=candidate_k,
            intent=intent,
            domains=domains,
        )
    finally:
        if old is not None:
            hr.BACKEND_CONFIG["plant_kb"] = old


def key_of(item: dict) -> tuple[str, str]:
    return (str(item.get("doc_id") or ""), str(item.get("clause") or ""))


def target_match(item: dict, case: dict) -> bool:
    clause_hit = _clause_match(str(case.get("evidence_location") or ""), [item])
    source_hit = _source_match(str(case.get("source_file") or ""), [item])
    return bool(clause_hit) and bool(source_hit)


def clause_only_match(item: dict, case: dict) -> bool:
    return bool(_clause_match(str(case.get("evidence_location") or ""), [item]))


def find_target_rank(items: list[dict], case: dict) -> tuple[int | None, dict | None]:
    for index, item in enumerate(items or [], start=1):
        if target_match(item, case):
            return index, item
    for index, item in enumerate(items or [], start=1):
        if clause_only_match(item, case):
            return index, item
    for index, item in enumerate(items or [], start=1):
        if _source_match(str(case.get("source_file") or ""), [item]):
            return index, item
    return None, None

def analyze() -> dict[str, Any]:
    cases = load_cases()
    post = load_post_rows()
    pre_hits = {}
    pre_top5 = {}
    for index, (case_id, case) in enumerate(cases.items(), start=1):
        row = post.get(case_id) or {}
        intent = (row.get("intent") or {}).get("intent")
        domains = (row.get("route") or {}).get("domains") or None
        chunks = run_with_config(PRE_CONFIG, str(case.get("question") or ""), intent, domains, top_k=5)
        pre_top5[case_id] = chunks
        value = _clause_match(str(case.get("evidence_location") or ""), chunks)
        pre_hits[case_id] = value
        if index % 10 == 0:
            print(f"pre retrieval {index}/{len(cases)}", flush=True)

    lost = []
    gained = []
    for case_id, post_row in post.items():
        post_hit = post_row.get("clause_hit")
        pre_hit = pre_hits.get(case_id)
        if pre_hit is None or post_hit is None:
            continue
        if pre_hit and not post_hit:
            lost.append(case_id)
        elif not pre_hit and post_hit:
            gained.append(case_id)

    details = []
    for case_id in lost:
        case = cases[case_id]
        row = post[case_id]
        intent = (row.get("intent") or {}).get("intent")
        domains = (row.get("route") or {}).get("domains") or None
        pre300 = run_with_config(PRE_CONFIG, str(case.get("question") or ""), intent, domains, top_k=300)
        post300 = run_with_config(hr._resolve_config("plant_kb"), str(case.get("question") or ""), intent, domains, top_k=300)
        pre_rank, pre_target = find_target_rank(pre300, case)
        post_rank, post_target = find_target_rank(post300, case)
        target_clause = (pre_target or post_target or {}).get("clause") or ""
        post_top5 = post300[:5]
        pre_top5_items = pre_top5.get(case_id) or []
        clause_competitors = [
            item for item in post_top5
            if clause_only_match(item, case) and not target_match(item, case)
        ]
        domain_alt_competitors = [item for item in clause_competitors if item.get("domain_alt")]
        if clause_competitors:
            category = "C: 同名条号/domain_alt候选覆盖"
        elif post_rank is None:
            category = "B: 适配后Top-300外"
        else:
            category = "A: Top-300内但未进Top-5"
        details.append({
            "id": case_id,
            "question": case.get("question"),
            "source_file": case.get("source_file"),
            "evidence_location": case.get("evidence_location"),
            "target_clause": target_clause,
            "pre_rank": pre_rank,
            "post_rank": post_rank,
            "category": category,
            "pre_top5": [{"doc_id": x.get("doc_id"), "clause": x.get("clause"), "domain_alt": x.get("domain_alt")} for x in pre_top5_items],
            "post_top5": [{"doc_id": x.get("doc_id"), "clause": x.get("clause"), "domain_alt": x.get("domain_alt")} for x in post_top5],
            "clause_competitors": [{"doc_id": x.get("doc_id"), "clause": x.get("clause"), "domain_alt": x.get("domain_alt")} for x in clause_competitors],
            "domain_alt_competitors": [{"doc_id": x.get("doc_id"), "clause": x.get("clause"), "domain_alt": x.get("domain_alt")} for x in domain_alt_competitors],
            "target_domain_alt": (pre_target or post_target or {}).get("domain_alt"),
        })

    category_counts = Counter(item["category"] for item in details)
    return {
        "pre_hits": pre_hits,
        "post_hits": {key: value.get("clause_hit") for key, value in post.items()},
        "lost": lost,
        "gained": gained,
        "details": details,
        "category_counts": dict(category_counts),
    }


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    def cell(value: Any) -> str:
        return str(value).replace("|", "\\|").replace("\n", "<br>").replace("\r", "")
    lines = ["| " + " | ".join(cell(x) for x in headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(cell(x) for x in row) + " |")
    return "\n".join(lines)


def write_report(result: dict[str, Any]) -> None:
    details = result["details"]
    lines = [
        "# 条号命中回退诊断",
        "",
        "> 日期：2026-10-05",
        "> 对比：适配前知识库备份 vs 适配后主路径；仅重放检索 Top-5，不重新生成回答。",
        "",
        "## 汇总",
        "",
        f"- 适配前条号命中：{sum(1 for value in result['pre_hits'].values() if value)}",
        f"- 适配后条号命中：{sum(1 for value in result['post_hits'].values() if value)}",
        f"- 回退题数：{len(result['lost'])}",
        f"- 新增命中题数：{len(result['gained'])}",
        "",
        "## 回退题清单",
        "",
        markdown_table(
            ["题号", "目标条号", "适配前目标排名", "适配后目标排名", "分类"],
            [[item["id"], item["target_clause"], item["pre_rank"], item["post_rank"], item["category"]] for item in details],
        ),
        "",
        "## 分类统计",
        "",
        markdown_table(["分类", "题数"], sorted(result["category_counts"].items())),
        "",
    ]
    for item in details:
        lines += [
            f"## {item['id']}",
            "",
            f"- 问题：{item['question']}",
            f"- 期望来源：`{item['source_file']}`",
            f"- 证据位置：`{item['evidence_location']}`",
            f"- 目标条号：`{item['target_clause']}`",
            f"- 适配前目标排名：`{item['pre_rank']}`",
            f"- 适配后目标排名：`{item['post_rank']}`",
            f"- 分类：**{item['category']}**",
            "",
            "### 适配前 Top-5",
            "",
            markdown_table(
                ["doc_id", "clause", "domain_alt"],
                [[x.get("doc_id"), x.get("clause"), x.get("domain_alt")] for x in item["pre_top5"]],
            ),
            "",
            "### 适配后 Top-5",
            "",
            markdown_table(
                ["doc_id", "clause", "domain_alt"],
                [[x.get("doc_id"), x.get("clause"), x.get("domain_alt")] for x in item["post_top5"]],
            ),
            "",
            "### 同名条号/备选域竞争者",
            "",
            markdown_table(
                ["doc_id", "clause", "domain_alt"],
                [[x.get("doc_id"), x.get("clause"), x.get("domain_alt")] for x in item["clause_competitors"]] or [["无", "", ""]],
            ),
            "",
        ]
    lines += [
        "## 建议",
        "",
        "- 若主要类别是 C，优先检查同名条号的 chunk_id 去重和 domain_alt 分片是否扩大了同条号候选，必要时对 domain_alt 结果增加轻微降权。",
        "- 若主要类别是 B，问题是适配后原始召回/索引覆盖变化，应先核对目标记录是否进入向量和 BM25 候选，再考虑索引策略。",
        "- 若主要类别是 A，目标是排序问题，应继续调整 RRF、正文排序和双路合并，而不是回滚 domain_alt。",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    result = analyze()
    write_report(result)
    print(json.dumps({
        "pre_hits": sum(1 for value in result["pre_hits"].values() if value),
        "post_hits": sum(1 for value in result["post_hits"].values() if value),
        "lost": result["lost"],
        "gained": result["gained"],
        "category_counts": result["category_counts"],
    }, ensure_ascii=False, indent=2))
    print(f"Report: {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
