#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trace FULL-005 / FULL-129 target items through fusion and reranking."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vector_kb.bm25_retriever import bm25_retrieve
from vector_kb.citation_verifier import clause_matches
from vector_kb.domain_guard import is_in_domain
from vector_kb.chunk_filter import is_body_text, prioritize_results, query_overlap
from vector_kb.hybrid_retriever import _backend_name, _resolve_config, _retrieve_path, hybrid_retrieve
from vector_kb.intent_classifier import classify_intent
from vector_kb.intent_router import route_intent
from vector_kb.query_planner import plan_query
from vector_kb.retrieval import retrieve
from vector_kb.rrf_fusion import rrf_fusion

DEFAULT_CASES = ROOT / "data" / "evaluation" / "plant_kb_full_questions.jsonl"
DEFAULT_REPORT = ROOT / "docs" / "融合丢失诊断_FULL-005_FULL-129.md"
DEFAULT_DETAILS = ROOT / "docs" / "exam_proof" / "融合丢失诊断_FULL-005_FULL-129.jsonl"
CASE_IDS = ("FULL-005", "FULL-129")
PATH_CONFIG = _resolve_config(_backend_name())


def _normalize(text: object) -> str:
    value = unicodedata.normalize("NFKC", str(text or "")).lower()
    return "".join(char for char in value if char.isalnum())


def _ngrams(text: str, sizes=(2, 3, 4, 5)) -> set[str]:
    normalized = _normalize(text)
    grams: set[str] = set()
    for size in sizes:
        grams.update(normalized[index:index + size] for index in range(max(0, len(normalized) - size + 1)))
    return {gram for gram in grams if gram}


def _source_matches(source_file: str, chunk: dict) -> bool:
    source = _normalize(Path(str(source_file or "")).stem.replace("预处理后_", ""))
    if not source or not isinstance(chunk, dict):
        return False
    haystack = _normalize(" ".join(str(chunk.get(field) or "") for field in ("doc_id", "title", "citation", "text")))
    if not haystack:
        return False
    if source in haystack or haystack in source:
        return True
    grams = _ngrams(source, (2, 3, 4))
    if len(source) < 20 or not grams:
        return False
    return sum(1 for gram in grams if gram in haystack) / len(grams) >= 0.9


def _clause_matches(evidence_location: str, chunk: dict) -> bool:
    expected = set(re.findall(r"\d+(?:\.\d+)+", str(evidence_location or "")))
    if not expected:
        return False
    clause = str((chunk or {}).get("clause") or "")
    actual = set(re.findall(r"\d+(?:\.\d+)+", clause))
    return any(
        left == right or right.startswith(left + ".")
        for left in expected
        for right in actual
    )


def _key(item: dict) -> tuple[str, str]:
    return (str(item.get("doc_id") or ""), str(item.get("clause") or ""))


def _rank(results: list[dict], target_key: tuple[str, str]) -> int | None:
    for index, item in enumerate(results or [], start=1):
        if _key(item) == target_key:
            return index
    return None


def _compact(item: dict) -> dict:
    return {
        "doc_id": item.get("doc_id"),
        "clause": item.get("clause"),
        "title": item.get("title"),
        "score": item.get("score"),
        "rrf_score": item.get("rrf_score"),
        "domain": item.get("domain"),
        "source": item.get("source"),
        "scope": item.get("scope"),
    }


def _load_cases(path: Path, ids: tuple[str, ...]) -> list[dict]:
    rows = []
    wanted = set(ids)
    with path.open("r", encoding="utf-8-sig") as stream:
        for line in stream:
            if not line.strip():
                continue
            item = json.loads(line)
            if str(item.get("id")) in wanted:
                rows.append(item)
    order = {item: index for index, item in enumerate(ids)}
    return sorted(rows, key=lambda item: order.get(str(item.get("id")), 999))


def _load_lightweight_metadata() -> dict[tuple[str, str], dict]:
    path = Path(PATH_CONFIG["vector_db"]).parent / "lightweight_metadata.jsonl"
    result: dict[tuple[str, str], dict] = {}
    if not path.is_file():
        return result
    with path.open("r", encoding="utf-8-sig") as stream:
        for line in stream:
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except Exception:
                continue
            result[(str(item.get("doc_id") or ""), str(item.get("clause") or ""))] = item
    return result


def _choose_target(vector_results: list[dict], bm25_results: list[dict], source_file: str, evidence_location: str) -> tuple[tuple[str, str] | None, dict | None]:
    results_list = [vector_results, bm25_results]
    for results in results_list:
        for item in results:
            if _source_matches(source_file, item) and _clause_matches(evidence_location, item):
                return _key(item), item
    for results in results_list:
        for item in results:
            if _source_matches(source_file, item):
                return _key(item), item
    for results in results_list:
        for item in results:
            if _clause_matches(evidence_location, item):
                return _key(item), item
    return None, None


def _clarify_drop_stage(trace: dict) -> str:
    if trace.get("domain_guard_ok") is False:
        return "domain_guard 在检索前拦截，未进入 RRF/融合"
    if trace.get("target_key") is None:
        return "未找到可追踪目标条文"
    if trace.get("rrf_rank") is None and trace.get("rrf_same_clause_winner") is not None:
        return "RRF融合时 clause-only 去重覆盖"
    if trace.get("rrf_rank") is None:
        return "RRF融合输出未包含目标key"
    if trace.get("prioritized_rank") is None:
        return "prioritize_results 阶段丢失"
    if trace.get("specific_rank") is None:
        return "具体设备路最终重排丢失"
    if trace.get("generic_query") and trace.get("hybrid_rank") is None:
        return "双路合并/scope选择阶段丢失"
    if trace.get("hybrid_rank") is not None and trace.get("hybrid_rank") > 5:
        return "目标仍存在但融合后排名>5"
    return "目标进入最终Top-5"


def _trace_case(case: dict, metadata: dict[tuple[str, str], dict]) -> dict:
    question = str(case.get("question") or "").strip()
    domain_guard_ok = is_in_domain(question, backend=_backend_name())
    source_file = str(case.get("source_file") or "").strip()
    evidence_location = str(case.get("evidence_location") or "").strip()
    intent_result = classify_intent(question)
    route = route_intent(question, classification=intent_result)
    domains = route.get("domains") or None
    plan = plan_query(question, intent_result.get("intent") or "")
    specific_query = str(plan.get("specific_query") or question)
    generic_query = str(plan.get("generic_query") or "").strip()

    vector_results = retrieve(
        specific_query,
        top_k=300,
        db_path=PATH_CONFIG["vector_db"],
        domains=domains,
    )
    bm25_results = bm25_retrieve(
        specific_query,
        top_k=300,
        corpus_path=PATH_CONFIG["bm25_corpus"],
        index_path=PATH_CONFIG["bm25_index"],
        domains=domains,
    )
    target_key, target_item = _choose_target(vector_results, bm25_results, source_file, evidence_location)
    target_clause = str((target_item or {}).get("clause") or "")
    metadata_item = metadata.get(target_key or ("", "")) or {}
    target_domain = str((target_item or {}).get("domain") or metadata_item.get("domain") or "")
    target_citation_eligible = (target_item or {}).get("citation_eligible")
    if target_citation_eligible is None:
        target_citation_eligible = metadata_item.get("is_citable")
    if target_citation_eligible is None:
        target_citation_eligible = bool((target_item or {}).get("doc_id") and (target_item or {}).get("clause"))

    rrf_results = rrf_fusion(vector_results, bm25_results, k=60, top_k=300)
    prioritized_results = prioritize_results(rrf_results, question=specific_query, top_k=300)
    specific_results = _retrieve_path(
        specific_query,
        domains=domains,
        top_k=300,
        candidate_k=300,
        rrf_k=60,
        config=PATH_CONFIG,
        embedding_source=PATH_CONFIG.get("embedding_source"),
        trace=None,
        label="specific",
    )
    generic_results = (
        _retrieve_path(
            generic_query,
            domains=None,
            top_k=100,
            candidate_k=300,
            rrf_k=60,
            config=PATH_CONFIG,
            embedding_source=PATH_CONFIG.get("embedding_source"),
            trace=None,
            label="generic",
        )
        if generic_query
        else []
    )
    hybrid_results = hybrid_retrieve(
        question,
        top_k=300,
        candidate_k=300,
        domains=domains,
        intent=intent_result.get("intent"),
    )

    same_clause_rrf = next((item for item in rrf_results if str(item.get("clause") or "") == target_clause), None)
    same_clause_prioritized = next((item for item in prioritized_results if str(item.get("clause") or "") == target_clause), None)
    same_clause_specific = next((item for item in specific_results if str(item.get("clause") or "") == target_clause), None)
    same_clause_hybrid = next((item for item in hybrid_results if str(item.get("clause") or "") == target_clause), None)
    collision_items = [
        item
        for item in [*vector_results, *bm25_results]
        if str(item.get("clause") or "") == target_clause and _key(item) != target_key
    ]
    hybrid_source_rank = None
    if source_file:
        for index, item in enumerate(hybrid_results, start=1):
            if _source_matches(source_file, item):
                hybrid_source_rank = index
                break

    trace = {
        "id": case.get("id"),
        "module": case.get("module"),
        "question": question,
        "source_file": source_file,
        "evidence_location": evidence_location,
        "intent": intent_result,
        "route": route,
        "domain_guard_ok": domain_guard_ok,
        "specific_query": specific_query,
        "generic_query": generic_query,
        "target_key": list(target_key) if target_key else None,
        "target_clause": target_clause,
        "target_domain": target_domain,
        "target_citation_eligible": bool(target_citation_eligible),
        "target_scope": metadata_item.get("scope"),
        "target_evidence_kind": metadata_item.get("evidence_kind"),
        "target_source_matches_vector": [ _compact(item) for item in vector_results if _source_matches(source_file, item) ][:10],
        "target_source_matches_bm25": [ _compact(item) for item in bm25_results if _source_matches(source_file, item) ][:10],
        "target_clause_matches_vector": [ _compact(item) for item in vector_results if _clause_matches(evidence_location, item) ][:10],
        "target_clause_matches_bm25": [ _compact(item) for item in bm25_results if _clause_matches(evidence_location, item) ][:10],
        "vector_top10": [_compact(item) for item in vector_results[:10]],
        "bm25_top10": [_compact(item) for item in bm25_results[:10]],
        "target_vector_rank": _rank(vector_results, target_key) if target_key else None,
        "target_bm25_rank": _rank(bm25_results, target_key) if target_key else None,
        "vector_count": len(vector_results),
        "bm25_count": len(bm25_results),
        "rrf_count": len(rrf_results),
        "rrf_rank": _rank(rrf_results, target_key) if target_key else None,
        "rrf_same_clause_winner": _compact(same_clause_rrf) if same_clause_rrf else None,
        "prioritized_count": len(prioritized_results),
        "prioritized_rank": _rank(prioritized_results, target_key) if target_key else None,
        "prioritized_same_clause_winner": _compact(same_clause_prioritized) if same_clause_prioritized else None,
        "specific_count": len(specific_results),
        "specific_rank": _rank(specific_results, target_key) if target_key else None,
        "specific_same_clause_winner": _compact(same_clause_specific) if same_clause_specific else None,
        "generic_count": len(generic_results),
        "generic_rank": _rank(generic_results, target_key) if target_key else None,
        "hybrid_count": len(hybrid_results),
        "hybrid_rank": _rank(hybrid_results, target_key) if target_key else None,
        "hybrid_source_rank": hybrid_source_rank,
        "hybrid_same_clause_winner": _compact(same_clause_hybrid) if same_clause_hybrid else None,
        "same_clause_collisions": [_compact(item) for item in collision_items[:20]],
        "target_is_body": is_body_text(target_item or {}),
        "target_overlap": query_overlap(target_item or {}, specific_query),
        "drop_stage": "",
    }
    trace["drop_stage"] = _clarify_drop_stage(trace)
    return trace

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
            index,
            item.get("doc_id"),
            item.get("clause"),
            item.get("domain"),
            item.get("source"),
            item.get("scope"),
            item.get("score"),
            item.get("rrf_score"),
        ]
        for index, item in enumerate(items, start=1)
    ]


def _write_case(lines: list[str], trace: dict) -> None:
    lines += [
        f"## {trace.get('id')}：{trace.get('question')}",
        "",
        f"- 模块：`{trace.get('module')}`",
        f"- 期望来源：`{trace.get('source_file')}`",
        f"- 证据位置：`{trace.get('evidence_location')}`",
        f"- 意图：`{trace.get('intent', {}).get('intent')}`；domains=`{trace.get('route', {}).get('domains')}`",
        f"- domain_guard：`{trace.get('domain_guard_ok')}`",
        f"- specific_query：`{trace.get('specific_query')}`",
        f"- generic_query：`{trace.get('generic_query')}`",
        f"- 目标 key：`{trace.get('target_key')}`",
        f"- 目标 clause：`{trace.get('target_clause')}`",
        f"- 目标 domain：`{trace.get('target_domain')}`",
        f"- citation_eligible：`{trace.get('target_citation_eligible')}`",
        f"- scope：`{trace.get('target_scope')}`；evidence_kind：`{trace.get('target_evidence_kind')}`",
        "",
        "### 向量路 Top-10",
        "",
        _markdown_table(
            ["排名", "doc_id", "clause", "domain", "source", "scope", "score", "rrf_score"],
            _item_rows(trace.get("vector_top10") or []),
        ),
        "",
        "### BM25 路 Top-10",
        "",
        _markdown_table(
            ["排名", "doc_id", "clause", "domain", "source", "scope", "score", "rrf_score"],
            _item_rows(trace.get("bm25_top10") or []),
        ),
        "",
        "### 目标条文候选",
        "",
        _markdown_table(
            ["路径", "排名", "doc_id", "clause", "domain", "source", "scope", "score"],
            [
                *[["向量来源匹配", index, item.get("doc_id"), item.get("clause"), item.get("domain"), item.get("source"), item.get("scope"), item.get("score")] for index, item in enumerate(trace.get("target_source_matches_vector") or [], start=1)],
                *[["BM25来源匹配", index, item.get("doc_id"), item.get("clause"), item.get("domain"), item.get("source"), item.get("scope"), item.get("score")] for index, item in enumerate(trace.get("target_source_matches_bm25") or [], start=1)],
                *[["向量条号匹配", index, item.get("doc_id"), item.get("clause"), item.get("domain"), item.get("source"), item.get("scope"), item.get("score")] for index, item in enumerate(trace.get("target_clause_matches_vector") or [], start=1)],
                *[["BM25条号匹配", index, item.get("doc_id"), item.get("clause"), item.get("domain"), item.get("source"), item.get("scope"), item.get("score")] for index, item in enumerate(trace.get("target_clause_matches_bm25") or [], start=1)],
            ],
        ),
        "",
        "### 融合与重排状态",
        "",
        _markdown_table(
            ["阶段", "条目数", "目标排名", "同 clause 胜出条目"],
            [
                ["向量原始", trace.get("vector_count"), trace.get("target_vector_rank"), "-"],
                ["BM25 原始", trace.get("bm25_count"), trace.get("target_bm25_rank"), "-"],
                ["RRF 融合", trace.get("rrf_count"), trace.get("rrf_rank"), trace.get("rrf_same_clause_winner")],
                ["正文优先重排", trace.get("prioritized_count"), trace.get("prioritized_rank"), trace.get("prioritized_same_clause_winner")],
                ["具体设备路最终", trace.get("specific_count"), trace.get("specific_rank"), trace.get("specific_same_clause_winner")],
                ["通用机理路", trace.get("generic_count"), trace.get("generic_rank"), "-"],
                ["domain_guard入口", 0 if trace.get("domain_guard_ok") is False else "-", "-", "拦截则未进入后续检索"],
                ["双路最终输出", trace.get("hybrid_count"), trace.get("hybrid_rank"), trace.get("hybrid_same_clause_winner")],
            ],
        ),
        "",
        "### 去重冲突与判断",
        "",
        f"- 目标是否正文块：`{trace.get('target_is_body')}`",
        f"- 目标 query overlap：`{trace.get('target_overlap')}`",
        f"- 是否存在同 clause 的其他条目：`{bool(trace.get('same_clause_collisions'))}`",
        f"- 丢失环节判断：**{trace.get('drop_stage')}**",
        "",
    ]
    collisions = trace.get("same_clause_collisions") or []
    if collisions:
        lines += [
            "同 clause 冲突条目：",
            "",
            _markdown_table(
                ["doc_id", "clause", "domain", "source", "scope", "score"],
                [[item.get("doc_id"), item.get("clause"), item.get("domain"), item.get("source"), item.get("scope"), item.get("score")] for item in collisions],
            ),
            "",
        ]


def write_report(traces: list[dict], report_path: Path) -> None:
    lines = [
        "# FULL-005 / FULL-129 融合丢失诊断",
        "",
        "> 诊断日期：2026-10-04",
        "> 目的：追踪目标条文在向量、BM25、RRF、正文重排、双路合并中的完整状态。",
        "",
    ]
    lines += ["## 结论摘要", ""]
    for trace in traces:
        lines.append(
            f"- `{trace.get('id')}`：`domain_guard={trace.get('domain_guard_ok')}`，"
            f"目标在向量/BM25/RRF/正文重排中的排名分别为 "
            f"`{trace.get('target_vector_rank')}` / `{trace.get('target_bm25_rank')}` / "
            f"`{trace.get('rrf_rank')}` / `{trace.get('prioritized_rank')}`；"
            f"最终双路输出排名 `{trace.get('hybrid_rank')}`；"
            f"判断：{trace.get('drop_stage')}。"
        )
    lines.append("")
    for trace in traces:
        _write_case(lines, trace)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="诊断 FULL-005/FULL-129 融合丢失")
    parser.add_argument("--cases", default=str(DEFAULT_CASES))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--details", default=str(DEFAULT_DETAILS))
    args = parser.parse_args(argv)

    cases = _load_cases(Path(args.cases), CASE_IDS)
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
                f"v={trace.get('target_vector_rank')} b={trace.get('target_bm25_rank')} "
                f"rrf={trace.get('rrf_rank')} prio={trace.get('prioritized_rank')} "
                f"specific={trace.get('specific_rank')} hybrid={trace.get('hybrid_rank')} "
                f"drop={trace.get('drop_stage')}",
                flush=True,
            )
    write_report(traces, Path(args.report))
    print(f"Report: {args.report}")
    print(f"Details: {details_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())