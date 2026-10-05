#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断 FULL-088 / FULL-089 的引用校验失败原因。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vector_kb.citation_verifier import (
    _CITATION_RE,
    _MECHANISM_RE,
    _clause_part,
    _is_citation_eligible,
    _is_direct_evidence,
    _is_generic_evidence,
    _matches_chunk,
    _normalize_text,
    _source_matches,
    clause_matches,
    normalize_clause,
    verify_citations,
)

DETAILS = ROOT / "docs" / "04_评测与回归" / "exam_proof" / "138题评测明细_20261004.jsonl"
REPORT = ROOT / "docs" / "引用校验失败诊断_FULL-088_FULL-089.md"
CASE_IDS = ("FULL-088", "FULL-089")


def load_cases() -> list[dict]:
    wanted = set(CASE_IDS)
    rows = []
    with DETAILS.open("r", encoding="utf-8-sig") as stream:
        for line in stream:
            if not line.strip():
                continue
            item = json.loads(line)
            if item.get("id") in wanted:
                rows.append(item)
    order = {case_id: index for index, case_id in enumerate(CASE_IDS)}
    return sorted(rows, key=lambda item: order.get(str(item.get("id")), 99))


def _chunk_view(chunk: dict) -> dict:
    return {
        "doc_id": chunk.get("doc_id"),
        "clause": chunk.get("clause"),
        "title": chunk.get("title"),
        "scope": chunk.get("scope"),
        "source": chunk.get("source"),
        "rrf_score": chunk.get("rrf_score"),
        "citation_eligible": _is_citation_eligible(chunk),
        "direct_evidence": _is_direct_evidence(chunk),
        "generic_evidence": _is_generic_evidence(chunk),
    }


def _extract_references(answer: str) -> dict:
    return {
        "direct": [match.group(1).strip() for match in _CITATION_RE.finditer(str(answer or ""))],
        "mechanism": [match.group(1).strip() for match in _MECHANISM_RE.finditer(str(answer or ""))],
    }


def _known_docs(chunks: list[dict]) -> set[str]:
    return {_normalize_text(chunk.get("doc_id")) for chunk in chunks if chunk.get("doc_id")}

def _inspect_direct_reference(reference: str, chunks: list[dict], known_docs: set[str]) -> dict:
    direct_chunks = [
        chunk for chunk in chunks
        if _is_citation_eligible(chunk) and _is_direct_evidence(chunk)
    ]
    matched = next(
        (chunk for chunk in direct_chunks if _matches_chunk(reference, chunk, known_docs)),
        None,
    )
    if matched is not None:
        return {
            "reference": reference,
            "valid": True,
            "reason": "有效：doc_id 与条号均匹配可引用直接依据",
            "matched_doc_id": matched.get("doc_id"),
            "matched_clause": matched.get("clause"),
        }

    full_match = next(
        (chunk for chunk in chunks if clause_matches(reference, chunk.get("clause"))),
        None,
    )
    clause_part = _clause_part(reference)
    normalized_full = normalize_clause(reference)
    normalized_part = normalize_clause(clause_part)

    if full_match is not None and normalized_full != normalized_part:
        return {
            "reference": reference,
            "valid": False,
            "reason": (
                "格式/解析不匹配：引用文本包含自由文本条号且含有多个“第”，"
                "_matches_chunk 先调用 _clause_part 截掉第一个“第”，"
                "normalize_clause 又在第二个“第”处二次截断，导致引用与有效条号解析结果不一致"
            ),
            "matched_doc_id": full_match.get("doc_id"),
            "matched_clause": full_match.get("clause"),
            "citation_eligible": _is_citation_eligible(full_match),
            "normalize_clause_reference": normalized_full,
            "clause_part": clause_part,
            "normalize_clause_clause_part": normalized_part,
            "normalize_clause_valid_clause": normalize_clause(full_match.get("clause")),
            "exact_clause_text_in_reference": str(full_match.get("clause") or "") in str(reference),
        }

    if full_match is not None and not _is_citation_eligible(full_match):
        return {
            "reference": reference,
            "valid": False,
            "reason": "引用了 citation_eligible=False 的条文，条号存在但不可引用",
            "matched_doc_id": full_match.get("doc_id"),
            "matched_clause": full_match.get("clause"),
        }

    if full_match is not None:
        return {
            "reference": reference,
            "valid": False,
            "reason": "条号匹配但 doc_id 不一致，或引用文本中的文档号无法匹配",
            "matched_doc_id": full_match.get("doc_id"),
            "matched_clause": full_match.get("clause"),
        }

    return {
        "reference": reference,
        "valid": False,
        "reason": "编造或不在本次 Top-5 可用条文中的条号",
        "normalize_clause_reference": normalized_full,
        "clause_part": clause_part,
    }


def _inspect_mechanism_reference(reference: str, chunks: list[dict]) -> dict:
    generic_chunks = [chunk for chunk in chunks if _is_generic_evidence(chunk)]
    matched = next((chunk for chunk in generic_chunks if _source_matches(reference, chunk)), None)
    if matched is None:
        direct_match = next(
            (chunk for chunk in chunks if _is_direct_evidence(chunk) and _source_matches(reference, chunk)),
            None,
        )
        if direct_match is not None:
            return {
                "reference": reference,
                "valid": True,
                "reason": "来源匹配 device_specific 条文，按同类机理参考规则被接受（可能产生误标提示）",
                "matched_doc_id": direct_match.get("doc_id"),
            }
    if matched is None:
        return {"reference": reference, "valid": False, "reason": "来源名称未匹配 Top-5 条文"}
    return {
        "reference": reference,
        "valid": True,
        "reason": "有效：来源名称匹配 generic 条文",
        "matched_doc_id": matched.get("doc_id"),
    }

def analyze_case(case: dict) -> dict:
    answer = str(case.get("answer") or "")
    chunks = [dict(chunk) for chunk in (case.get("top5") or []) if isinstance(chunk, dict)]
    known_docs = _known_docs(chunks)
    references = _extract_references(answer)
    verification = verify_citations(answer, chunks)
    direct_analysis = [
        _inspect_direct_reference(reference, chunks, known_docs)
        for reference in references["direct"]
    ]
    mechanism_analysis = [
        _inspect_mechanism_reference(reference, chunks)
        for reference in references["mechanism"]
    ]
    return {
        "id": case.get("id"),
        "module": case.get("module"),
        "question": case.get("question"),
        "intent": case.get("intent"),
        "route": case.get("route"),
        "top5": [_chunk_view(chunk) for chunk in chunks],
        "answer": answer,
        "references": references,
        "verification": verification,
        "direct_analysis": direct_analysis,
        "mechanism_analysis": mechanism_analysis,
        "generation_attempts": case.get("generation_attempts"),
        "stored_invalid_citations": case.get("invalid_citations") or [],
        "error": case.get("error") or "",
    }


def _table(headers: list[str], rows: list[list[object]]) -> str:
    def cell(value: object) -> str:
        return str(value).replace("|", "\\|").replace("\n", "<br>").replace("\r", "")

    lines = ["| " + " | ".join(cell(item) for item in headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(cell(item) for item in row) + " |")
    return "\n".join(lines)

def write_report(cases: list[dict], path: Path) -> None:
    lines = [
        "# 引用校验失败诊断：FULL-088、FULL-089",
        "",
        "> 数据来源：`docs/04_评测与回归/exam_proof/138题评测明细_20261004.jsonl` 的最终回答、Top-5 和引用校验字段。",
        "> 说明：现有评测明细未保存每次重写前的中间回答；本报告只依据已保存的实际数据，不猜测中间文本。",
        "",
        "## 结论摘要",
        "",
        "- 两题的无效引用来自同一条 Top-5 真实条文，并非模型编造条号。",
        "- 该条文的 `clause` 是自由文本：`鳍片上部存在开裂现象。13.上数第1层后数第2个人孔...`。",
        "- 模型按 `doc_id + 自由文本 clause` 生成引用，引用的 clause 文本确实存在于 Top-5。",
        "- 失败点是校验器对含多个“第”的自由文本条号发生二次截断：",
        "  `normalize_clause(引用)` 解析为 `1`，而 `normalize_clause(_clause_part(引用))` 解析为 `2`；有效条号解析为 `1`。",
        "- 因此应归类为“格式/解析不匹配”，不是“编造条号”，也不是“引用 citation_eligible=False 条文”。",
        "",
    ]

    for case in cases:
        lines += [
            f"## {case['id']}",
            "",
            "### 用户问题",
            "",
            f"```text\n{case['question']}\n```",
            "",
            "### 意图分类与路由",
            "",
            f"```json\n{json.dumps({'intent': case['intent'], 'route': case['route']}, ensure_ascii=False, indent=2)}\n```",
            "",
            "### 检索 Top-5",
            "",
            _table(
                ["排名", "doc_id", "clause", "scope", "source", "citation_eligible", "direct", "RRF"],
                [
                    [index, chunk["doc_id"], chunk["clause"], chunk["scope"], chunk["source"],
                     chunk["citation_eligible"], chunk["direct_evidence"], chunk["rrf_score"]]
                    for index, chunk in enumerate(case["top5"], start=1)
                ],
            ),
            "",
            "### 模型最终回答（完整文本）",
            "",
            f"```text\n{case['answer']}\n```",
            "",
            "### 提取出的引用",
            "",
            f"- 直接依据：{json.dumps(case['references']['direct'], ensure_ascii=False)}",
            f"- 同类机理参考：{json.dumps(case['references']['mechanism'], ensure_ascii=False)}",
            f"- 生成重写次数：{case['generation_attempts']}",
            "",
            "### 引用校验结果",
            "",
            f"```json\n{json.dumps(case['verification'], ensure_ascii=False, indent=2)}\n```",
            "",
            "### 逐引用诊断",
            "",
        ]
        analysis_rows = []
        for item in case["direct_analysis"]:
            analysis_rows.append([
                "直接依据", item["reference"], "有效" if item["valid"] else "无效",
                item.get("reason"), item.get("matched_doc_id"), item.get("matched_clause"),
                item.get("normalize_clause_reference"), item.get("clause_part"),
                item.get("normalize_clause_clause_part"), item.get("normalize_clause_valid_clause"),
            ])
        for item in case["mechanism_analysis"]:
            analysis_rows.append([
                "同类机理参考", item["reference"], "有效" if item["valid"] else "无效",
                item.get("reason"), item.get("matched_doc_id"), "", "", "", "", "",
            ])
        lines.append(_table(
            ["类型", "引用", "结果", "原因", "匹配doc_id", "匹配clause", "引用norm", "clause_part", "二次norm", "有效clause norm"],
            analysis_rows,
        ))
        lines += [
            "",
            "### 失败原因",
            "",
        ]
        for item in case["direct_analysis"]:
            if item["valid"]:
                continue
            lines.append(f"- `{item['reference']}`：{item['reason']}")
            if item.get("normalize_clause_reference") is not None:
                lines.append(
                    f"  - 解析链：引用 norm={item.get('normalize_clause_reference')}；"
                    f"clause_part={item.get('clause_part')}；"
                    f"二次 norm={item.get('normalize_clause_clause_part')}；"
                    f"有效 clause norm={item.get('normalize_clause_valid_clause')}。"
                )
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")

def main() -> int:
    cases = load_cases()
    if len(cases) != len(CASE_IDS):
        print(f"warning: expected {len(CASE_IDS)} cases, got {len(cases)}", flush=True)
    analyzed = [analyze_case(case) for case in cases]
    for case in analyzed:
        intent = case["intent"].get("intent") if isinstance(case["intent"], dict) else case["intent"]
        print(
            f"[{case['id']}] intent={intent} top5={len(case['top5'])} "
            f"citations={len(case['references']['direct'])} "
            f"mechanism={len(case['references']['mechanism'])} "
            f"invalid={case['verification'].get('invalid_citations')} "
            f"attempts={case['generation_attempts']}",
            flush=True,
        )
        for item in case["direct_analysis"]:
            print(
                f"  direct valid={item['valid']} citation={item['reference']!r} reason={item['reason']}",
                flush=True,
            )
        for item in case["mechanism_analysis"]:
            print(
                f"  mechanism valid={item['valid']} reference={item['reference']!r} reason={item['reason']}",
                flush=True,
            )
    write_report(analyzed, REPORT)
    print(f"Report: {REPORT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
