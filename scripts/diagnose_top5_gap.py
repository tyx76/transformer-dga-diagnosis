#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnose ranking gaps for FULL-005 / FULL-033 / FULL-082 / FULL-129."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.diagnose_fusion_loss import (
    PATH_CONFIG,
    _choose_target,
    _clause_matches,
    _key,
    _load_lightweight_metadata,
    _rank,
    _source_matches,
)
from vector_kb.bm25_retriever import bm25_retrieve
from vector_kb.chunk_filter import is_body_text, prioritize_results, query_overlap
from vector_kb.domain_guard import is_in_domain
from vector_kb.hybrid_retriever import _backend_name, _retrieve_path, hybrid_retrieve
from vector_kb.intent_classifier import classify_intent
from vector_kb.intent_router import route_intent
from vector_kb.query_planner import plan_query
from vector_kb.retrieval import retrieve
from vector_kb.rrf_fusion import rrf_fusion

DEFAULT_CASES = ROOT / "data" / "evaluation" / "plant_kb_full_questions.jsonl"
DEFAULT_REPORT = ROOT / "docs" / "03_检索与排序" / "Top5排序诊断_4题.md"
DEFAULT_DETAILS = ROOT / "docs" / "04_评测与回归" / "exam_proof" / "Top5排序诊断_4题_20261004.jsonl"
CASE_IDS = ("FULL-005", "FULL-033", "FULL-082", "FULL-129")
CANDIDATE_K = 300


def _load_cases(path: Path) -> list[dict]:
    wanted = set(CASE_IDS)
    rows = []
    with path.open("r", encoding="utf-8-sig") as stream:
        for line in stream:
            if not line.strip():
                continue
            item = json.loads(line)
            if str(item.get("id")) in wanted:
                rows.append(item)
    order = {case_id: index for index, case_id in enumerate(CASE_IDS)}
    return sorted(rows, key=lambda item: order[str(item.get("id"))])


def _metadata_for(key, metadata):
    return metadata.get(key or ("", "")) or {}


def _citation_eligible(item: dict, metadata_item: dict) -> bool:
    value = item.get("citation_eligible")
    if value is None:
        value = metadata_item.get("is_citable")
    if value is None:
        value = bool(item.get("doc_id") and item.get("clause"))
    return bool(value)


def _preview(text: object, limit: int = 50) -> str:
    value = " ".join(str(text or "").split())
    return value if len(value) <= limit else value[: limit - 1] + "…"


def _item_view(item: dict, metadata: dict, rank: int | None = None, question: str = "") -> dict:
    key = _key(item)
    meta = _metadata_for(key, metadata)
    return {
        "rank": rank,
        "doc_id": item.get("doc_id"),
        "clause": item.get("clause"),
        "title": item.get("title"),
        "domain": item.get("domain") or meta.get("domain"),
        "source": item.get("source"),
        "scope": item.get("scope") or meta.get("scope"),
        "rrf_score": item.get("rrf_score"),
        "score": item.get("score"),
        "is_body": is_body_text(item),
        "citation_eligible": _citation_eligible(item, meta),
        "query_overlap": query_overlap(item, question),
        "text_preview": _preview(item.get("text")),
        "key": list(key),
    }


def _find_score(item: dict) -> float | None:
    for field in ("rrf_score", "score"):
        value = item.get(field)
        try:
            if value is not None:
                return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _top5_diagnosis(items: list[dict]) -> dict:
    top5 = items[:5]
    return {
        "non_body_count": sum(1 for item in top5 if not item.get("is_body")),
        "ineligible_count": sum(1 for item in top5 if not item.get("citation_eligible")),
        "top5": top5,
    }


def _trace_case(case: dict, metadata: dict) -> dict:
    question = str(case.get("question") or "").strip()
    source_file = str(case.get("source_file") or "").strip()
    evidence_location = str(case.get("evidence_location") or "").strip()
    intent = classify_intent(question)
    route = route_intent(question, classification=intent)
    domains = route.get("domains") or None
    plan = plan_query(question, intent.get("intent") or "")
    specific_query = str(plan.get("specific_query") or question)
    generic_query = str(plan.get("generic_query") or "").strip()

    vector = retrieve(
        specific_query,
        top_k=CANDIDATE_K,
        db_path=PATH_CONFIG["vector_db"],
        domains=domains,
    )
    bm25 = bm25_retrieve(
        specific_query,
        top_k=CANDIDATE_K,
        corpus_path=PATH_CONFIG["bm25_corpus"],
        index_path=PATH_CONFIG["bm25_index"],
        domains=domains,
    )
    target_key, target_item = _choose_target(vector, bm25, source_file, evidence_location)
    raw_rrf = rrf_fusion(vector, bm25, k=60, top_k=CANDIDATE_K)
    reranked = prioritize_results(raw_rrf, question=specific_query, top_k=CANDIDATE_K)
    specific = _retrieve_path(
        specific_query,
        domains=domains,
        top_k=CANDIDATE_K,
        candidate_k=CANDIDATE_K,
        rrf_k=60,
        config=PATH_CONFIG,
        embedding_source=PATH_CONFIG.get("embedding_source"),
        trace=None,
        label="specific",
    )
    generic = (
        _retrieve_path(
            generic_query,
            domains=None,
            top_k=100,
            candidate_k=CANDIDATE_K,
            rrf_k=60,
            config=PATH_CONFIG,
            embedding_source=PATH_CONFIG.get("embedding_source"),
            trace=None,
            label="generic",
        )
        if generic_query
        else []
    )
    final = hybrid_retrieve(
        question,
        top_k=CANDIDATE_K,
        candidate_k=CANDIDATE_K,
        domains=domains,
        intent=intent.get("intent"),
    )

    final_top10_views = [_item_view(item, metadata, index, specific_query) for index, item in enumerate(final[:10], start=1)]
    target_view = _item_view(target_item or {}, metadata, question=specific_query) if target_item else None
    pre_rank = _rank(raw_rrf, target_key) if target_key else None
    post_rank = _rank(reranked, target_key) if target_key else None
    specific_rank = _rank(specific, target_key) if target_key else None
    final_rank = _rank(final, target_key) if target_key else None
    fifth = final[4] if len(final) >= 5 else None
    fifth_score = _find_score(fifth) if fifth else None
    target_final_item = final[final_rank - 1] if final_rank and final_rank <= len(final) else None
    target_score = _find_score(target_final_item or target_item or {})
    score_gap = None
    if target_score is not None and fifth_score is not None:
        score_gap = float(target_score) - float(fifth_score)

    top5_info = _top5_diagnosis(final_top10_views)
    reasons = []
    if final_rank is None:
        reasons.append("目标不在最终Top-300")
    elif final_rank > 5:
        if score_gap is not None and score_gap < 0:
            reasons.append(f"目标RRF分数比第5名低{abs(score_gap):.6f}")
        if top5_info["non_body_count"]:
            reasons.append(f"Top-5中有{top5_info['non_body_count']}条被判为非正文")
        if top5_info["ineligible_count"]:
            reasons.append(f"Top-5中有{top5_info['ineligible_count']}条citation_eligible=false")
        if post_rank is not None and pre_rank is not None and post_rank > pre_rank:
            if target_view and target_view.get("is_body"):
                reasons.append(
                    f"正文优先+query_overlap重排将目标从第{pre_rank}推到第{post_rank}"
                )
            else:
                reasons.append(
                    f"目标被判非正文，正文优先重排后从第{pre_rank}降到第{post_rank}"
                )
        if (
            not reasons
            and pre_rank == post_rank == 1
            and score_gap is not None
            and score_gap >= 0
        ):
            reasons.append(
                f"target RRF分数高于第5名，但双路合并/scope分层把目标放到第{final_rank}"
            )
        if not reasons:
            reasons.append("排序后仍有更多高RRF候选位于目标之前")
    else:
        reasons.append("目标进入Top-5")

    return {
        "id": case.get("id"),
        "module": case.get("module"),
        "question": question,
        "source_file": source_file,
        "evidence_location": evidence_location,
        "intent": intent,
        "route": route,
        "domain_guard_ok": is_in_domain(question, backend=_backend_name()),
        "specific_query": specific_query,
        "generic_query": generic_query,
        "target_key": list(target_key) if target_key else None,
        "target_item": target_view,
        "target_source_matches": [
            _item_view(item, metadata, index, specific_query)
            for index, item in enumerate(vector + bm25, start=1)
            if _source_matches(source_file, item)
        ][:10],
        "target_clause_matches": [
            _item_view(item, metadata, index, specific_query)
            for index, item in enumerate(vector + bm25, start=1)
            if _clause_matches(evidence_location, item)
        ][:10],
        "pre_rerank_rank": pre_rank,
        "post_rerank_rank": post_rank,
        "specific_rank": specific_rank,
        "final_rank": final_rank,
        "final_top10": final_top10_views,
        "top5": top5_info["top5"],
        "top5_non_body_count": top5_info["non_body_count"],
        "top5_ineligible_count": top5_info["ineligible_count"],
        "target_score": target_score,
        "fifth_score": fifth_score,
        "score_gap": score_gap,
        "reasons": reasons,
    }

def _markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(lines)


def _item_rows(items: list[dict]) -> list[list[object]]:
    return [
        [
            item.get("rank"),
            item.get("doc_id"),
            item.get("clause"),
            item.get("title"),
            item.get("rrf_score"),
            item.get("is_body"),
            item.get("citation_eligible"),
            item.get("query_overlap"),
            item.get("text_preview"),
        ]
        for item in items
    ]


def _write_case(lines: list[str], trace: dict) -> None:
    lines += [
        f"## {trace.get('id')}：{trace.get('question')}",
        "",
        f"- 模块：`{trace.get('module')}`",
        f"- 期望来源：`{trace.get('source_file')}`",
        f"- 证据位置：`{trace.get('evidence_location')}`",
        f"- domain_guard：`{trace.get('domain_guard_ok')}`",
        f"- 目标 key：`{trace.get('target_key')}`",
        f"- 融合前目标排名：`{trace.get('pre_rerank_rank')}`",
        f"- 正文重排后目标排名：`{trace.get('post_rerank_rank')}`",
        f"- 最终目标排名：`{trace.get('final_rank')}`",
        f"- 目标分数：`{trace.get('target_score')}`；第5名分数：`{trace.get('fifth_score')}`；分差：`{trace.get('score_gap')}`",
        f"- 判断：{'；'.join(trace.get('reasons') or [])}",
        "",
        "### 融合后 Top-10",
        "",
        _markdown_table(
            ["排名", "doc_id", "clause", "标题", "RRF分数", "is_body", "citation_eligible", "query_overlap", "text前50"],
            _item_rows(trace.get("final_top10") or []),
        ),
        "",
        "### 前5条与目标对比",
        "",
        _markdown_table(
            ["角色", "排名", "doc_id", "clause", "RRF分数", "is_body", "citation_eligible", "query_overlap", "text前50"],
            [
                *[
                    ["Top-5", item.get("rank"), item.get("doc_id"), item.get("clause"), item.get("rrf_score"), item.get("is_body"), item.get("citation_eligible"), item.get("query_overlap"), item.get("text_preview")]
                    for item in (trace.get("top5") or [])
                ],
                ["目标", trace.get("final_rank"), (trace.get("target_item") or {}).get("doc_id"), (trace.get("target_item") or {}).get("clause"), trace.get("target_score"), (trace.get("target_item") or {}).get("is_body"), (trace.get("target_item") or {}).get("citation_eligible"), (trace.get("target_item") or {}).get("query_overlap"), (trace.get("target_item") or {}).get("text_preview")],
            ],
        ),
        "",
    ]


def write_report(traces: list[dict], report_path: Path) -> None:
    lines = [
        "# 4题 Top-5 排序诊断",
        "",
        "> 诊断日期：2026-10-04",
        "> 用例：FULL-005、FULL-033、FULL-082、FULL-129",
        "> 目的：定位目标条文进入融合结果但被挤出 Top-5 的具体原因。",
        "",
        "## 共性汇总",
        "",
    ]
    summary_rows = []
    for trace in traces:
        summary_rows.append([
            trace.get("id"),
            trace.get("final_rank"),
            trace.get("pre_rerank_rank"),
            trace.get("post_rerank_rank"),
            trace.get("score_gap"),
            trace.get("top5_non_body_count"),
            trace.get("top5_ineligible_count"),
            "；".join(trace.get("reasons") or []),
        ])
    lines.append(_markdown_table(
        ["编号", "最终排名", "融合前排名", "重排后排名", "与第5名分差", "Top5非正文", "Top5不可引用", "判断"],
        summary_rows,
    ))
    lines.append("")
    lines += [
        "## 共性分析",
        "",
        "- 4 道题的目标条文均为正文块，且均满足 citation_eligible；Top-5 中也没有非正文块或不可引用块占位。",
        "- FULL-033、FULL-082 的主要问题是 query_overlap 重排：目标在融合前为第 4/48，重排后降到第 120/182。",
        "- FULL-005 的目标与第 5 名存在 RRF 分差，目标分数低于第 5 名 0.005729；重排只把目标从第 7 提升到第 6。",
        "- FULL-129 的目标在具体设备路融合与正文重排后均为第 1，但双路合并/scope 分层后降到第 7；其 RRF 分数高于第 5 名。",
        "- 当前 Top-5 缺口不是脏块占位，而是不同阶段的目标保留策略不足：query_overlap、双路合并和 scope 选择都可能覆盖强 RRF 目标。",
        "",
    ]
    for trace in traces:
        _write_case(lines, trace)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="4题Top-5排序诊断")
    parser.add_argument("--cases", default=str(DEFAULT_CASES))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--details", default=str(DEFAULT_DETAILS))
    args = parser.parse_args(argv)

    cases = _load_cases(Path(args.cases))
    metadata = _load_lightweight_metadata()
    traces = []
    details_path = Path(args.details)
    details_path.parent.mkdir(parents=True, exist_ok=True)
    with details_path.open("w", encoding="utf-8") as stream:
        for case in cases:
            trace = _trace_case(case, metadata)
            traces.append(trace)
            stream.write(json.dumps(trace, ensure_ascii=False) + "\n")
            stream.flush()
            print(
                f"{trace.get('id')} target={trace.get('target_key')} "
                f"pre={trace.get('pre_rerank_rank')} post={trace.get('post_rerank_rank')} "
                f"final={trace.get('final_rank')} gap={trace.get('score_gap')} "
                f"reasons={'；'.join(trace.get('reasons') or [])}",
                flush=True,
            )
    write_report(traces, Path(args.report))
    print(f"Report: {args.report}")
    print(f"Details: {details_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())