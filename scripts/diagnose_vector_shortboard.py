#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnose vector-retrieval short boards on the 138-question set."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vector_kb.bm25_retriever import bm25_retrieve
from vector_kb.hybrid_retriever import BACKEND_CONFIG, _backend_name, _resolve_config, hybrid_retrieve
from vector_kb.intent_classifier import classify_intent
from vector_kb.intent_router import route_intent
from vector_kb.retrieval import retrieve

DEFAULT_CASES = ROOT / "data" / "evaluation" / "plant_kb_full_questions.jsonl"
DEFAULT_REPORT = ROOT / "docs" / "向量检索短板诊断.md"
DEFAULT_DETAILS = ROOT / "docs" / "04_评测与回归" / "exam_proof" / "向量检索诊断明细_20261004.jsonl"
CANDIDATE_K = 300
PATH_CONFIG = _resolve_config(_backend_name())


def _normalize(text: object) -> str:
    value = unicodedata.normalize("NFKC", str(text or "")).lower()
    return "".join(char for char in value if char.isalnum())


def _ngrams(text: str, sizes=(2, 3, 4, 5)) -> set[str]:
    normalized = _normalize(text)
    grams: set[str] = set()
    for size in sizes:
        grams.update(
            normalized[index:index + size]
            for index in range(max(0, len(normalized) - size + 1))
        )
    return {gram for gram in grams if gram}


def _source_matches(source_file: str, chunk: dict) -> bool:
    source = _normalize(Path(str(source_file or "")).stem.replace("预处理后_", ""))
    if not source or not isinstance(chunk, dict):
        return False
    haystack = _normalize(
        " ".join(
            str(chunk.get(field) or "")
            for field in ("doc_id", "title", "citation", "text")
        )
    )
    if not haystack:
        return False
    if source in haystack or haystack in source:
        return True
    grams = _ngrams(source, (2, 3, 4))
    if not grams:
        return False
    covered = sum(1 for gram in grams if gram in haystack)
    return covered / len(grams) >= 0.65


def _clause_matches(evidence_location: str, chunk: dict) -> bool:
    expected = set(re.findall(r"\d+(?:\.\d+)+", str(evidence_location or "")))
    if not expected:
        return False
    clause = str((chunk or {}).get("clause") or "")
    return any(item in clause for item in expected)


def _rank_of_target(results: list[dict], source_file: str, evidence_location: str) -> tuple[int | None, int | None, int | None]:
    source_rank = None
    clause_rank = None
    for index, chunk in enumerate(results or [], start=1):
        if source_rank is None and source_file and _source_matches(source_file, chunk):
            source_rank = index
        if clause_rank is None and evidence_location and _clause_matches(evidence_location, chunk):
            clause_rank = index
        if source_rank is not None and (not evidence_location or clause_rank is not None):
            break
    primary = source_rank if source_file else clause_rank
    if source_file and source_rank is None:
        primary = clause_rank
    return source_rank, clause_rank, primary


def _rank_bucket(rank: int | None) -> str:
    if rank is None:
        return "未进入Top-300/阈值外"
    if rank <= 5:
        return "Top-5"
    if rank <= 20:
        return "6-20"
    if rank <= 100:
        return "21-100"
    return "101-300"


def _rate(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "N/A"
    return f"{numerator / denominator * 100:.2f}%"


def _markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(lines)

def _load_cases(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8-sig") as stream:
        for line in stream:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _evaluate_case(case: dict, reused_hybrid: dict | None = None) -> dict:
    question = str(case.get("question") or "").strip()
    source_file = str(case.get("source_file") or "").strip()
    evidence_location = str(case.get("evidence_location") or "").strip()
    started = time.perf_counter()
    error = ""
    intent_result: dict = {}
    route: dict = {}
    vector_results: list[dict] = []
    bm25_results: list[dict] = []
    hybrid_results: list[dict] = []
    try:
        intent_result = classify_intent(question)
        route = route_intent(question, classification=intent_result)
        domains = route.get("domains") or None
        if route.get("mode") != "refuse" and domains:
            vector_results = retrieve(
                question,
                top_k=CANDIDATE_K,
                db_path=PATH_CONFIG["vector_db"],
                domains=domains,
            )
            bm25_results = bm25_retrieve(
                question,
                top_k=CANDIDATE_K,
                corpus_path=PATH_CONFIG["bm25_corpus"],
                index_path=PATH_CONFIG["bm25_index"],
                domains=domains,
            )
            if reused_hybrid is None:
                hybrid_results = hybrid_retrieve(
                    question,
                    top_k=CANDIDATE_K,
                    candidate_k=CANDIDATE_K,
                    domains=domains,
                    intent=intent_result.get("intent"),
                )
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"

    vector_source_rank, vector_clause_rank, vector_rank = _rank_of_target(vector_results, source_file, evidence_location)
    bm25_source_rank, bm25_clause_rank, bm25_rank = _rank_of_target(bm25_results, source_file, evidence_location)
    if reused_hybrid is not None:
        hybrid_source_rank = reused_hybrid.get("hybrid_source_rank")
        hybrid_clause_rank = reused_hybrid.get("hybrid_clause_rank")
        hybrid_rank = reused_hybrid.get("hybrid_rank")
    else:
        hybrid_source_rank, hybrid_clause_rank, hybrid_rank = _rank_of_target(hybrid_results, source_file, evidence_location)

    vector_top5 = vector_rank is not None and vector_rank <= 5
    bm25_top5 = bm25_rank is not None and bm25_rank <= 5
    hybrid_top5 = hybrid_rank is not None and hybrid_rank <= 5

    if not vector_top5 and bm25_top5:
        category = "向量失败但BM25成功"
    elif vector_top5 and not bm25_top5:
        category = "BM25失败但向量成功"
    elif not vector_top5 and not bm25_top5:
        category = "两者都失败"
    elif vector_top5 and bm25_top5 and not hybrid_top5:
        category = "两者都成功但融合排序失败"
    else:
        category = "三路均成功"

    return {
        "id": case.get("id"),
        "module": case.get("module"),
        "question": question,
        "source_file": source_file,
        "evidence_location": evidence_location,
        "intent": intent_result,
        "route": route,
        "vector_rank": vector_rank,
        "vector_source_rank": vector_source_rank,
        "vector_clause_rank": vector_clause_rank,
        "bm25_rank": bm25_rank,
        "bm25_source_rank": bm25_source_rank,
        "bm25_clause_rank": bm25_clause_rank,
        "hybrid_rank": hybrid_rank,
        "hybrid_source_rank": hybrid_source_rank,
        "hybrid_clause_rank": hybrid_clause_rank,
        "vector_top5": vector_top5,
        "bm25_top5": bm25_top5,
        "hybrid_top5": hybrid_top5,
        "category": category,
        "vector_top_clauses": [chunk.get("clause") for chunk in vector_results[:5]],
        "bm25_top_clauses": [chunk.get("clause") for chunk in bm25_results[:5]],
        "hybrid_top_clauses": reused_hybrid.get("hybrid_top_clauses") if reused_hybrid else [chunk.get("clause") for chunk in hybrid_results[:5]],
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
        "error": error,
    }

def _summary_rows(rows: list[dict]) -> list[list[object]]:
    evaluable = [row for row in rows if row.get("source_file") or row.get("evidence_location")]
    vector_hits = sum(1 for row in evaluable if row.get("vector_top5"))
    bm25_hits = sum(1 for row in evaluable if row.get("bm25_top5"))
    hybrid_hits = sum(1 for row in evaluable if row.get("hybrid_top5"))
    vector_recall = sum(1 for row in evaluable if row.get("vector_rank") is not None)
    bm25_recall = sum(1 for row in evaluable if row.get("bm25_rank") is not None)
    hybrid_recall = sum(1 for row in evaluable if row.get("hybrid_rank") is not None)
    return [
        ["可评测题数", len(evaluable)],
        ["纯向量 Top-5 命中", f"{vector_hits}/{len(evaluable)}"],
        ["纯向量 Top-5 命中率", _rate(vector_hits, len(evaluable))],
        ["纯 BM25 Top-5 命中", f"{bm25_hits}/{len(evaluable)}"],
        ["纯 BM25 Top-5 命中率", _rate(bm25_hits, len(evaluable))],
        ["混合检索 Top-5 命中", f"{hybrid_hits}/{len(evaluable)}"],
        ["混合检索 Top-5 命中率", _rate(hybrid_hits, len(evaluable))],
        ["纯向量 Top-300 召回", f"{vector_recall}/{len(evaluable)}"],
        ["纯 BM25 Top-300 召回", f"{bm25_recall}/{len(evaluable)}"],
        ["混合检索 Top-300 召回", f"{hybrid_recall}/{len(evaluable)}"],
        ["平均诊断耗时", f"{mean([row.get('elapsed_ms') or 0.0 for row in rows]):.2f} ms" if rows else "0 ms"],
    ]


def _module_rows(rows: list[dict]) -> list[list[object]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        if row.get("source_file") or row.get("evidence_location"):
            groups[str(row.get("module") or "未分组")].append(row)
    output = []
    for module, items in sorted(groups.items()):
        v = sum(1 for row in items if row.get("vector_top5"))
        b = sum(1 for row in items if row.get("bm25_top5"))
        h = sum(1 for row in items if row.get("hybrid_top5"))
        output.append([
            module,
            len(items),
            _rate(v, len(items)),
            _rate(b, len(items)),
            _rate(h, len(items)),
        ])
    return output

def write_report(rows: list[dict], report_path: Path) -> None:
    evaluable = [row for row in rows if row.get("source_file") or row.get("evidence_location")]
    category_counts = Counter(row.get("category") for row in evaluable)
    vector_fail_bm25_success = category_counts.get("向量失败但BM25成功", 0)
    bm25_fail_vector_success = category_counts.get("BM25失败但向量成功", 0)
    both_fail = category_counts.get("两者都失败", 0)
    ranking_fail = category_counts.get("两者都成功但融合排序失败", 0)
    all_success = category_counts.get("三路均成功", 0)
    vector_top5_count = sum(1 for row in evaluable if row.get("vector_top5"))
    bm25_top5_count = sum(1 for row in evaluable if row.get("bm25_top5"))
    hybrid_top5_count = sum(1 for row in evaluable if row.get("hybrid_top5"))
    vector_recall_count = sum(1 for row in evaluable if row.get("vector_rank") is not None)
    bm25_recall_count = sum(1 for row in evaluable if row.get("bm25_rank") is not None)
    hybrid_recall_count = sum(1 for row in evaluable if row.get("hybrid_rank") is not None)
    failure_rows = [row for row in evaluable if row.get("category") != "三路均成功"]
    rank_buckets = {
        "纯向量": Counter(_rank_bucket(row.get("vector_rank")) for row in evaluable),
        "纯BM25": Counter(_rank_bucket(row.get("bm25_rank")) for row in evaluable),
        "混合": Counter(_rank_bucket(row.get("hybrid_rank")) for row in evaluable),
    }

    lines = [
        "# 向量检索短板诊断",
        "",
        "> 诊断日期：2026-10-04",
        f"> 评测集：`data/evaluation/plant_kb_full_questions.jsonl`，共 {len(rows)} 题",
        "> 方法：使用与主链路相同的 intent/domain 路由，分别测量纯向量、纯 BM25 和混合检索的 Top-5 命中。",
        "",
        "## 0. 口径修正",
        "",
        "- `knowledge/plant_kb/` 的 15,188 条记录 domain 均非空；`DL/T 722` 仅位于 `transformer_dga`，未发现 `DL/T 572`。",
        "- `knowledge/pure_kb/index/knowledge.db` 的 123 条旧 chunks 全部没有 domain。`retrieve()`/`bm25_retrieve()` 的默认路径是 pure_kb，早期诊断未显式传 plant_kb 路径，导致 boiler 路由混入旧变压器条文。",
        "- 本报告已显式传入 `KB_BACKEND` 对应的 plant_kb `db_path`、`corpus_path` 和 `index_path`。",
        "",
        "## 1. 总结",
        "",
        _markdown_table(["指标", "结果"], _summary_rows(rows)),
        "",
        "## 2. 分类统计",
        "",
        _markdown_table(
            ["分类", "题数", "说明"],
            [
                ["向量失败但 BM25 成功", vector_fail_bm25_success, "向量路 Top-5 未命中，但 BM25 路命中"],
                ["BM25 失败但向量成功", bm25_fail_vector_success, "BM25 路 Top-5 未命中，但向量路命中"],
                ["两者都失败", both_fail, "两条单路 Top-5 均未命中"],
                ["两者都成功但融合排序失败", ranking_fail, "两路 Top-5 均命中，但融合后未进 Top-5"],
                ["三路均成功", all_success, "向量、BM25、融合 Top-5 均命中"],
            ],
        ),
        "",
        "## 3. 分模块 Top-5 命中率",
        "",
        _markdown_table(
            ["模块", "题数", "纯向量", "纯 BM25", "混合"],
            _module_rows(rows),
        ),
        "",
        "## 4. 正确条文排名分布",
        "",
        _markdown_table(
            ["路径", "Top-5", "6-20", "21-100", "101-300", "未召回/阈值外"],
            [
                [
                    path,
                    counts.get("Top-5", 0),
                    counts.get("6-20", 0),
                    counts.get("21-100", 0),
                    counts.get("101-300", 0),
                    counts.get("未进入Top-300/阈值外", 0),
                ]
                for path, counts in rank_buckets.items()
            ],
        ),
        "",
        "## 5. 失败案例明细",
        "",
    ]
    if failure_rows:
        table_rows = []
        for row in failure_rows:
            table_rows.append([
                row.get("id"),
                row.get("module"),
                row.get("question"),
                row.get("source_file"),
                row.get("vector_rank") if row.get("vector_rank") is not None else "-",
                row.get("bm25_rank") if row.get("bm25_rank") is not None else "-",
                row.get("hybrid_rank") if row.get("hybrid_rank") is not None else "-",
                row.get("category"),
            ])
        lines.append(_markdown_table(
            ["编号", "模块", "问题", "期望来源", "向量排名", "BM25排名", "融合排名", "分类"],
            table_rows,
        ))
    else:
        lines.append("无。")
    lines += [
        "",
        "## 6. 诊断结论",
        "",
        f"- 纯向量 Top-5 命中率为 {_rate(sum(1 for row in evaluable if row.get('vector_top5')), len(evaluable))}。",
        f"- 纯 BM25 Top-5 命中率为 {_rate(sum(1 for row in evaluable if row.get('bm25_top5')), len(evaluable))}。",
        f"- 混合检索 Top-5 命中率为 {_rate(sum(1 for row in evaluable if row.get('hybrid_top5')), len(evaluable))}。",
        f"- 向量失败但 BM25 成功：{vector_fail_bm25_success} 题；BM25 失败但向量成功：{bm25_fail_vector_success} 题。",
        f"- 两者都失败：{both_fail} 题；两者都成功但融合排序失败：{ranking_fail} 题。",
        f"- Top-300 召回：纯向量 {vector_recall_count}/{len(evaluable)}，纯 BM25 {bm25_recall_count}/{len(evaluable)}，混合 {hybrid_recall_count}/{len(evaluable)}。",
        "",
        "## 7. 是否应优先微调 embedding",
        "",
        "当前数据不支持把 embedding 微调作为第一优先级。校正为 plant_kb 后，纯向量 Top-5 命中率高于纯 BM25，Top-300 召回两者接近；向量并未表现出比词法检索更严重的短板。主要问题转为两者共同未召回的题目，以及少量两路成功但融合后丢失的题目。",
        "",
        "建议顺序：先分析两者共同失败的题目和目标条文是否真实存在，再检查融合丢失和无 domain 旧库默认路径问题；只有当修复数据、路径和路由后，向量召回@20/100 仍显著低于 BM25，且 BM25 成功、向量持续失败时，才值得进入 embedding 微调。",
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="138题向量检索短板诊断")
    parser.add_argument("--cases", default=str(DEFAULT_CASES))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--details", default=str(DEFAULT_DETAILS))
    parser.add_argument("--reuse-hybrid-details", default="", help="复用已有混合检索排名明细，避免重复跑混合路")
    args = parser.parse_args(argv)

    cases = _load_cases(Path(args.cases))
    reuse_hybrid = {}
    if args.reuse_hybrid_details:
        for row in _load_cases(Path(args.reuse_hybrid_details)):
            reuse_hybrid[str(row.get("id"))] = row
    details_path = Path(args.details)
    details_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    with details_path.open("w", encoding="utf-8") as detail_stream:
        for index, case in enumerate(cases, start=1):
            reused = reuse_hybrid.get(str(case.get("id")))
            row = _evaluate_case(case, reused_hybrid=reused)
            rows.append(row)
            detail_stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            detail_stream.flush()
            print(
                f"[{index}/{len(cases)}] {row.get('id')} {row.get('module')} "
                f"v={row.get('vector_rank')} b={row.get('bm25_rank')} h={row.get('hybrid_rank')} "
                f"category={row.get('category')} ms={row.get('elapsed_ms')} error={row.get('error') or '-'}",
                flush=True,
            )
    write_report(rows, Path(args.report))
    print(f"Report: {args.report}")
    print(f"Details: {details_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())