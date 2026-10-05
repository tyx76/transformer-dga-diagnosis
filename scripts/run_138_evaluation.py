#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the 138-question plant_kb evaluation and write a Markdown report."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean

import jieba

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vector_kb.citation_verifier import (
    build_retry_prompt,
    remove_invalid_citation_sentences,
    verify_citations,
)
from vector_kb.generation import generate
from vector_kb.retrieval_router import route_and_retrieve

DEFAULT_CASES = ROOT / "data" / "evaluation" / "plant_kb_full_questions.jsonl"
DEFAULT_REPORT = ROOT / "docs" / "04_评测与回归" / "评测报告_138题_20261004.md"
DEFAULT_DETAILS = ROOT / "docs" / "04_评测与回归" / "exam_proof" / "138题评测明细_20261004.jsonl"
STOPWORDS = {
    "应该", "可以", "需要", "进行", "检查", "处理", "可能", "如果", "以及",
    "相关", "问题", "措施", "情况", "是否", "说明", "方法", "要求", "确认",
    "导致", "出现", "存在", "根据", "进行", "并", "和", "或", "的", "了",
}


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


def _source_match(source_file: str, chunks: list[dict]) -> bool:
    source = _normalize(Path(str(source_file or "")).stem.replace("预处理后_", ""))
    if not source or not chunks:
        return False
    source_grams = _ngrams(source, (2, 3, 4))
    for chunk in chunks:
        haystack = _normalize(
            " ".join(
                str(chunk.get(field) or "")
                for field in ("doc_id", "title", "citation", "text")
            )
        )
        if not haystack:
            continue
        if source in haystack or haystack in source:
            return True
        if source_grams:
            covered = sum(1 for gram in source_grams if gram in haystack)
            if covered / len(source_grams) >= 0.65:
                return True
    return False


def _clause_match(evidence_location: str, chunks: list[dict]) -> bool | None:
    expected_clauses = set(re.findall(r"\d+(?:\.\d+)+", str(evidence_location or "")))
    if not expected_clauses:
        return None
    actual = " ".join(str(chunk.get("clause") or "") for chunk in chunks)
    return any(clause in actual for clause in expected_clauses)


def _answer_coverage(expected_answer: str, answer: str) -> float:
    expected = str(expected_answer or "").strip()
    if not expected:
        return 0.0
    answer_norm = _normalize(answer)
    tokens = [token for token in jieba.lcut(_normalize(expected)) if len(token) >= 2 and token not in STOPWORDS]
    if not tokens:
        tokens = list(_ngrams(expected, (2, 3)))
    if not tokens:
        return 0.0
    matched = sum(1 for token in tokens if token in answer_norm)
    return matched / len(tokens)


def _is_refusal(answer: str) -> bool:
    text = str(answer or "")
    return "资料未覆盖" in text or "无法回答" in text


def _load_cases(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8-sig") as stream:
        for line in stream:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _safe_chunks(chunks: list[dict]) -> list[dict]:
    return [chunk for chunk in (chunks or []) if isinstance(chunk, dict)]


def run_case(case: dict, top_k: int) -> dict:
    question = str(case.get("question") or "").strip()
    started = time.perf_counter()
    error = ""
    chunks: list[dict] = []
    answer = ""
    route: dict = {}
    intent: dict = {}
    verification = {
        "valid": False,
        "valid_citations": [],
        "invalid_citations": [],
        "valid_direct_citations": [],
        "valid_mechanism_references": [],
    }
    attempts = 0
    try:
        routed = route_and_retrieve(question, top_k=top_k, shadow=False)
        intent = routed.get("intent") or {}
        route = routed.get("route") or {}
        chunks = _safe_chunks(routed.get("chunks"))
        if not chunks:
            answer = "资料未覆盖，无法回答"
            verification["valid"] = True
        else:
            prompt = question
            for attempt in range(3):
                attempts += 1
                answer = generate(prompt, chunks)
                verification = verify_citations(answer, chunks)
                if verification.get("valid"):
                    break
                if attempt < 2:
                    prompt = build_retry_prompt(question, verification, chunks)
            if not verification.get("valid"):
                answer = remove_invalid_citation_sentences(answer, chunks) or "资料未覆盖，无法回答"
                verification = verify_citations(answer, chunks)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"

    source_file = str(case.get("source_file") or "").strip()
    evidence_location = str(case.get("evidence_location") or "").strip()
    source_hit = _source_match(source_file, chunks) if source_file else None
    clause_hit = _clause_match(evidence_location, chunks) if evidence_location else None
    top_scopes = Counter(str(chunk.get("scope") or "unknown") for chunk in chunks[:top_k])
    top_sources = Counter(str(chunk.get("source") or "unknown") for chunk in chunks[:top_k])
    direct_count = len(re.findall(r"【\s*依据\s*[：:]", str(answer or "")))
    mechanism_count = len(re.findall(r"【\s*同类机理参考\s*[：:]", str(answer or "")))

    return {
        "id": case.get("id"),
        "module": case.get("module") or "未分组",
        "source_question_id": case.get("source_question_id"),
        "question": question,
        "expected_answer": case.get("expected_answer") or "",
        "source_file": source_file,
        "evidence_location": evidence_location,
        "intent": intent,
        "route": route,
        "top5": [
            {
                "doc_id": chunk.get("doc_id"),
                "clause": chunk.get("clause"),
                "title": chunk.get("title"),
                "scope": chunk.get("scope"),
                "source": chunk.get("source"),
                "rrf_score": chunk.get("rrf_score"),
            }
            for chunk in chunks[:top_k]
        ],
        "top_clauses": "；".join(str(chunk.get("clause") or "-") for chunk in chunks[:top_k]) or "-",
        "source_hit": source_hit,
        "clause_hit": clause_hit,
        "top_scopes": dict(top_scopes),
        "top_sources": dict(top_sources),
        "answer": answer,
        "answer_length": len(str(answer or "")),
        "refused": _is_refusal(answer),
        "answer_coverage": round(_answer_coverage(case.get("expected_answer") or "", answer), 6),
        "citation_valid": bool(verification.get("valid")),
        "valid_direct_count": len(verification.get("valid_direct_citations") or []),
        "valid_mechanism_count": len(verification.get("valid_mechanism_references") or []),
        "direct_reference_count": direct_count,
        "mechanism_reference_count": mechanism_count,
        "invalid_citations": verification.get("invalid_citations") or [],
        "warnings": verification.get("warnings") or [],
        "generation_attempts": attempts,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
        "error": error,
    }


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


def _module_summary(rows: list[dict]) -> list[list[object]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        groups[str(row.get("module") or "未分组")].append(row)
    output = []
    for module, items in sorted(groups.items()):
        with_source = [row for row in items if row.get("source_hit") is not None]
        source_hits = sum(1 for row in with_source if row.get("source_hit"))
        valid = sum(1 for row in items if row.get("citation_valid"))
        refused = sum(1 for row in items if row.get("refused"))
        coverage = mean([row.get("answer_coverage") or 0.0 for row in items if row.get("expected_answer")])
        avg_ms = mean([row.get("elapsed_ms") or 0.0 for row in items])
        output.append([
            module,
            len(items),
            f"{source_hits}/{len(with_source)}",
            _rate(source_hits, len(with_source)),
            _rate(valid, len(items)),
            _rate(refused, len(items)),
            f"{coverage * 100:.2f}%",
            f"{avg_ms:.2f}",
        ])
    return output


def write_report(rows: list[dict], report_path: Path) -> None:
    total = len(rows)
    with_source = [row for row in rows if row.get("source_hit") is not None]
    source_hits = sum(1 for row in with_source if row.get("source_hit"))
    clause_available = [row for row in rows if row.get("clause_hit") is not None]
    clause_hits = sum(1 for row in clause_available if row.get("clause_hit"))
    valid = sum(1 for row in rows if row.get("citation_valid"))
    refused = sum(1 for row in rows if row.get("refused"))
    direct_refs = sum(int(row.get("direct_reference_count") or 0) for row in rows)
    mechanism_refs = sum(int(row.get("mechanism_reference_count") or 0) for row in rows)
    valid_direct_refs = sum(int(row.get("valid_direct_count") or 0) for row in rows)
    valid_mechanism_refs = sum(int(row.get("valid_mechanism_count") or 0) for row in rows)
    answer_rows = [row for row in rows if row.get("expected_answer")]
    coverage = mean([row.get("answer_coverage") or 0.0 for row in answer_rows]) if answer_rows else 0.0
    avg_ms = mean([row.get("elapsed_ms") or 0.0 for row in rows]) if rows else 0.0
    errors = [row for row in rows if row.get("error")]

    summary = [
        ["总题数", total],
        ["有来源标注题数", len(with_source)],
        ["Top-5 来源命中", f"{source_hits}/{len(with_source)}"],
        ["Top-5 来源命中率", _rate(source_hits, len(with_source))],
        ["Top-5 条号命中", f"{clause_hits}/{len(clause_available)}"],
        ["引用校验通过", f"{valid}/{total}"],
        ["引用正确率", _rate(valid, total)],
        ["依据引用出现次数", direct_refs],
        ["同类机理参考出现次数", mechanism_refs],
        ["去重后有效依据引用", valid_direct_refs],
        ["去重后有效同类机理参考", valid_mechanism_refs],
        ["拒答题数", refused],
        ["拒答率", _rate(refused, total)],
        ["参考答案覆盖率", f"{coverage * 100:.2f}%"],
        ["平均耗时", f"{avg_ms:.2f} ms"],
        ["异常题数", len(errors)],
    ]
    module_rows = _module_summary(rows)
    source_miss = [row for row in with_source if not row.get("source_hit")]
    refusal_expected = [row for row in rows if row.get("refused") and row.get("expected_answer")]
    invalid_citation = [row for row in rows if not row.get("citation_valid")]

    lines = [
        "# 138 题端到端评测报告",
        "",
        f"> 评测日期：2026-10-04",
        f"> 知识库：`knowledge/plant_kb/`，15,188 条",
        f"> 数据集：`data/evaluation/plant_kb_full_questions.jsonl`",
        f"> 运行链路：查询规划 → 双路检索 → scope 分层排序 → 生成 → 分层引用校验",
        "",
        "## 1. 汇总指标",
        "",
        _markdown_table(["指标", "结果"], summary),
        "",
        "说明：Top-5 来源命中率仅统计 `source_file` 非空的题目；条号命中率仅统计 `evidence_location` 含数字条号的题目。",
        "",
        "## 2. 分模块指标",
        "",
        _markdown_table(
            ["模块", "题数", "来源命中", "来源命中率", "引用正确率", "拒答率", "答案覆盖率", "平均耗时(ms)"],
            module_rows,
        ),
        "",
        "## 3. 失败案例",
        "",
        f"### 3.1 Top-5 未命中来源（{len(source_miss)} 题）",
        "",
    ]
    if source_miss:
        lines.append(_markdown_table(
            ["编号", "模块", "问题", "期望来源", "Top-5 条号"],
            [[row.get("id"), row.get("module"), row.get("question"), row.get("source_file"), row.get("top_clauses")] for row in source_miss],
        ))
    else:
        lines.append("无。")
    lines += [
        "",
        f"### 3.2 拒答但应有答案（{len(refusal_expected)} 题）",
        "",
    ]
    if refusal_expected:
        lines.append(_markdown_table(
            ["编号", "模块", "问题", "参考答案", "最终回答"],
            [[row.get("id"), row.get("module"), row.get("question"), row.get("expected_answer"), row.get("answer")] for row in refusal_expected],
        ))
    else:
        lines.append("无。")
    lines += [
        "",
        f"### 3.3 引用校验未通过（{len(invalid_citation)} 题）",
        "",
    ]
    if invalid_citation:
        lines.append(_markdown_table(
            ["编号", "模块", "问题", "无效引用", "最终回答"],
            [[row.get("id"), row.get("module"), row.get("question"), "、".join(row.get("invalid_citations") or []), row.get("answer")] for row in invalid_citation],
        ))
    else:
        lines.append("无。")
    lines += [
        "",
        "## 4. 结论",
        "",
        f"- {total} 题中，Top-5 来源命中率为 {_rate(source_hits, len(with_source))}。",
        f"- 引用正确率为 {_rate(valid, total)}，拒答率为 {_rate(refused, total)}。",
        f"- 参考答案平均覆盖率为 {coverage * 100:.2f}%，平均耗时 {avg_ms:.2f} ms。",
        f"- 共发现来源未命中 {len(source_miss)} 题、应有答案但拒答 {len(refusal_expected)} 题、引用校验失败 {len(invalid_citation)} 题。",
        "- 本报告保留每条题目的完整明细，便于后续按域和故障模式做误差分析。",
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="138 题端到端评测")
    parser.add_argument("--cases", default=str(DEFAULT_CASES))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--details", default=str(DEFAULT_DETAILS))
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args(argv)

    cases = _load_cases(Path(args.cases))
    if args.limit > 0:
        cases = cases[:args.limit]
    details_path = Path(args.details)
    details_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []

    with details_path.open("w", encoding="utf-8") as detail_stream:
        for index, case in enumerate(cases, start=1):
            row = run_case(case, top_k=args.top_k)
            rows.append(row)
            detail_stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            detail_stream.flush()
            print(
                f"[{index}/{len(cases)}] {row.get('id')} {row.get('module')} "
                f"source_hit={row.get('source_hit')} clause_hit={row.get('clause_hit')} "
                f"citation={'OK' if row.get('citation_valid') else 'FAIL'} "
                f"refused={row.get('refused')} coverage={row.get('answer_coverage')} "
                f"ms={row.get('elapsed_ms')} error={row.get('error') or '-'}",
                flush=True,
            )

    report_path = Path(args.report)
    write_report(rows, report_path)
    print(f"Report: {report_path}")
    print(f"Details: {details_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())