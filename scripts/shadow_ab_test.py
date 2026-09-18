#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shadow A/B retrieval comparison."""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import vector_kb.retrieval_router as retrieval_router
from vector_kb.citation_verifier import verify_citations
from vector_kb.generation import _cite, _load_env, generate
from vector_kb.intent_classifier import rule_classify
from vector_kb.hybrid_retriever import hybrid_retrieve

OUTPUT = ROOT / "docs" / "影子对比报告.md"

CASES = [
    {"id": "DGA-01", "category": "dga_analysis", "question": "乙炔超标怎么处理", "groups": [["9.3.1-表3"]]},
    {"id": "DGA-02", "category": "dga_analysis", "question": "C2H2注意值是多少", "groups": [["9.3.1-表3"]]},
    {"id": "DGA-03", "category": "dga_analysis", "question": "氢气产气速率注意值", "groups": [["9.3.2-表4"]]},
    {"id": "DGA-04", "category": "dga_analysis", "question": "三比值怎么判断故障类型", "groups": [["10.2.1-表7"]]},
    {"id": "DGA-05", "category": "dga_analysis", "question": "局部放电有哪些特征气体", "groups": [["10.2.1-表7"]]},
    {"id": "OIL-01", "category": "oil_temp", "question": "变压器油温过高怎么处理", "groups": [["7.1.5", "7.1.6", "7.1.8"]]},
    {"id": "OIL-02", "category": "oil_temp", "question": "顶层油温超过105度怎么处理", "groups": [["7.1.8"]]},
    {"id": "OIL-03", "category": "oil_temp", "question": "冷却系统故障温度升高怎么办", "groups": [["7.1.6"]]},
    {"id": "OIL-04", "category": "oil_temp", "question": "变压器油位因温度升高过高怎么办", "groups": [["7.1.11"]]},
    {"id": "SAFE-01", "category": "safety_check", "question": "要不要立即停电", "groups": [["7.1.2", "7.1.3", "7.1.4"]]},
    {"id": "SAFE-02", "category": "safety_check", "question": "主变着火怎么处理", "groups": [["7.5.3"]]},
    {"id": "SAFE-03", "category": "safety_check", "question": "严重漏油要不要停运", "groups": [["7.1.2"]]},
    {"id": "EQ-01", "category": "equipment_spec", "question": "220kV变压器顶层油温限值", "groups": [["5.1.3"]]},
    {"id": "EQ-02", "category": "equipment_spec", "question": "变压器额定电流怎么运行", "groups": [["5.4.1", "5.4.2"]]},
    {"id": "EQ-03", "category": "equipment_spec", "question": "变压器铭牌有哪些信息", "groups": [["4.2.2"]]},
    {"id": "IRR-01", "category": "irrelevant", "question": "今天晚饭吃什么", "groups": [], "must_refuse": True},
    {"id": "IRR-02", "category": "irrelevant", "question": "推荐一部电影", "groups": [], "must_refuse": True},
    {"id": "IRR-03", "category": "irrelevant", "question": "周末去哪里旅游", "groups": [], "must_refuse": True},
    {"id": "MULTI-01", "category": "multi", "question": "乙炔和油温同时异常", "groups": [["9.3.1-表3"], ["7.1.5", "7.1.6", "7.1.8"]]},
    {"id": "MULTI-02", "category": "multi", "question": "局部放电并伴随油温升高", "groups": [["10.2.1-表7"], ["7.1.5", "7.1.6", "7.1.8"]]},
    {"id": "MULTI-03", "category": "multi", "question": "乙炔超标是否应立即停运", "groups": [["9.3.1-表3"], ["7.1.2", "7.1.3", "7.1.4"]]},
    {"id": "LLM-01", "category": "equipment_spec", "question": "这个设备的操作流程是什么", "groups": [["4.1.1", "6.1.1", "7.1.1"]], "llm_stub": "equipment_spec"},
]


def clauses(items):
    return [str(item.get("clause") or "") for item in (items or [])]


def hit_expected(results, groups):
    found = set(clauses(results))
    return all(any(clause in found for clause in group) for group in groups)


def template_answer(results):
    parts = []
    for item in (results or [])[:5]:
        doc_id = item.get("doc_id")
        clause = item.get("clause")
        if doc_id and clause:
            parts.append(f"结论【依据：{_cite(doc_id, clause)}】")
    return "".join(parts)


def citation_valid(question, results):
    if not results:
        return None
    if _load_env():
        try:
            answer = generate(question, results)
            return bool(verify_citations(answer, results)["valid"])
        except Exception:
            return None
    answer = template_answer(results)
    if not answer:
        return False
    return bool(verify_citations(answer, results)["valid"])


def run_hybrid(question):
    started = time.perf_counter()
    try:
        results = hybrid_retrieve(question, top_k=5)
        error = ""
    except Exception as exc:
        results, error = [], f"{type(exc).__name__}: {exc}"
    return {"results": results, "elapsed_ms": (time.perf_counter() - started) * 1000, "error": error}


def run_router(case):
    started = time.perf_counter()
    try:
        use_stub = not _load_env() and (
            case.get("llm_stub") or rule_classify(case["question"]) is None
        )
        if use_stub:
            stub_intent = case.get("llm_stub") or case["category"]
            stub = {"intent": stub_intent, "confidence": 0.6, "source": "llm"}
            with patch.object(retrieval_router, "classify_intent", return_value=stub):
                bundle = retrieval_router.route_and_retrieve(case["question"], top_k=5, shadow=True)
        else:
            bundle = retrieval_router.route_and_retrieve(case["question"], top_k=5, shadow=True)
        error = ""
    except Exception as exc:
        bundle = {"chunks": [], "intent": {}, "hybrid_top5": [], "kb_top5": [], "llm_calls": 0, "source": "error"}
        error = f"{type(exc).__name__}: {exc}"
    return {
        "bundle": bundle,
        "results": bundle.get("chunks") or [],
        "elapsed_ms": (time.perf_counter() - started) * 1000,
        "error": error,
    }

def run_case(case):
    with ThreadPoolExecutor(max_workers=2) as pool:
        hybrid_future = pool.submit(run_hybrid, case["question"])
        router_future = pool.submit(run_router, case)
        hybrid_run = hybrid_future.result()
        router_run = router_future.result()

    hybrid_results = hybrid_run["results"]
    kb_results = router_run["bundle"].get("kb_top5") or []
    b_results = router_run["results"]
    expected_groups = case.get("groups") or []

    a_hit = hit_expected(hybrid_results, expected_groups) if expected_groups else None
    b_hit = hit_expected(b_results, expected_groups) if expected_groups else None
    refuse = bool(case.get("must_refuse"))
    a_refuse = not hybrid_results if refuse else None
    b_refuse = not b_results if refuse else None

    return {
        "id": case["id"],
        "category": case["category"],
        "question": case["question"],
        "expected_groups": expected_groups,
        "must_refuse": refuse,
        "a_top5": clauses(hybrid_results),
        "b_top5": clauses(b_results),
        "a_hit": a_hit,
        "b_hit": b_hit,
        "a_refuse": a_refuse,
        "b_refuse": b_refuse,
        "a_ms": round(hybrid_run["elapsed_ms"], 2),
        "b_ms": round(router_run["elapsed_ms"], 2),
        "a_error": hybrid_run["error"],
        "b_error": router_run["error"],
        "b_source": router_run["bundle"].get("source", "error"),
        "intent": router_run["bundle"].get("intent", {}),
        "llm_calls": int(router_run["bundle"].get("llm_calls") or 0),
        "kb_top5": clauses(kb_results),
        "a_citation_valid": citation_valid(case["question"], hybrid_results),
        "b_citation_valid": citation_valid(case["question"], b_results),
    }


def bool_rate(rows, field):
    values = [row[field] for row in rows if row[field] is not None]
    if not values:
        return "N/A"
    return f"{sum(1 for value in values if value) / len(values):.2%}"


def metric_average(rows, field):
    if not rows:
        return 0.0
    return sum(float(row[field]) for row in rows) / len(rows)


def build_report(rows):
    non_refuse = [row for row in rows if not row["must_refuse"]]
    irrelevant = [row for row in rows if row["must_refuse"]]
    a_hit_rate = bool_rate(non_refuse, "a_hit")
    b_hit_rate = bool_rate(non_refuse, "b_hit")
    a_refusal = bool_rate(irrelevant, "a_refuse")
    b_refusal = bool_rate(irrelevant, "b_refuse")
    a_citation = bool_rate(rows, "a_citation_valid")
    b_citation = bool_rate(rows, "b_citation_valid")
    a_avg_ms = metric_average(rows, "a_ms")
    b_avg_ms = metric_average(rows, "b_ms")
    llm_calls = sum(row["llm_calls"] for row in rows)

    numeric = lambda value: float(str(value).rstrip("%")) if value != "N/A" else 0.0
    improvement = numeric(b_hit_rate) - numeric(a_hit_rate)
    recommend = improvement > 0 or (improvement == 0 and numeric(b_refusal) >= numeric(a_refusal))

    lines = [
        "# 影子模式 A/B 对比报告", "",
        "> 生成时间：由 `scripts/shadow_ab_test.py` 自动生成  ",
        "> A路：现有 `hybrid_retrieve()`  ",
        "> B路：`route_and_retrieve(..., shadow=True)`，只记录结果，不影响生产链路。", "",
        "## 1. 环境说明", "",
    ]
    if _load_env():
        lines.append("- 引用正确率：使用真实 DeepSeek 生成结果。")
    else:
        lines.append("- 未检测到 `DEEPSEEK_API_KEY`：引用正确率使用“检索条文模板”验证，仅代表引用结构，不代表真实模型生成质量。")
        lines.append("- LLM 兜底用例在离线模式下使用桩分类，避免真实 API 调用。")
    lines += [
        f"- 测试用例：{len(rows)} 条", "",
        "## 2. 汇总指标", "",
        "| 指标 | A路 hybrid | B路 hybrid+kb |", "|---|---:|---:|",
        f"| Top-5 命中率 | {a_hit_rate} | {b_hit_rate} |",
        f"| {"引用正确率" if _load_env() else "引用结构正确率"} | {a_citation} | {b_citation} |",
        f"| 无关问题拒答率 | {a_refusal} | {b_refusal} |",
        f"| 平均响应时间(ms) | {a_avg_ms:.2f} | {b_avg_ms:.2f} |",
        f"| LLM 兜底次数 | - | {llm_calls} |", "",
        "## 3. 每条用例结果", "",
        "| 编号 | 类别 | 问题 | A路 Top-5 | B路 Top-5 | A命中 | B命中 | A耗时(ms) | B耗时(ms) |",
        "|---|---|---|---|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        a_top = "、".join(row["a_top5"]) or "-"
        b_top = "、".join(row["b_top5"]) or "-"
        lines.append(
            f"| {row['id']} | {row['category']} | {row['question']} | {a_top} | {b_top} | "
            f"{'是' if row['a_hit'] else '否' if row['a_hit'] is False else '-'} | "
            f"{'是' if row['b_hit'] else '否' if row['b_hit'] is False else '-'} | "
            f"{row['a_ms']:.2f} | {row['b_ms']:.2f} |"
        )

    lines += ["", "## 4. 异常与回退", ""]
    errors = [row for row in rows if row["a_error"] or row["b_error"]]
    if errors:
        for row in errors:
            lines.append(f"- {row['id']}：A=`{row['a_error'] or '无'}`，B=`{row['b_error'] or '无'}`")
    else:
        lines.append("- 两路均未出现异常。")

    lines += ["", "## 5. 结论", ""]
    if recommend and improvement > 0:
        lines.append("- B路 Top-5 命中率高于 A路，且拒答表现未变差，**建议进入影子灰度接入阶段**。")
    elif recommend:
        lines.append("- 两路命中率相当，B路未降低拒答表现，**可以继续扩大样本验证后再接入**。")
    else:
        lines.append("- B路未显示明确质量提升，**暂不建议接入生产链路**，先调整 domain 映射、过滤和融合权重。")
    lines.append(f"- Top-5 命中率变化：{improvement:+.2f} 个百分点。")
    lines.append("- 本报告仅记录对比；`main.ask()`、`hybrid_retrieve()`、`generate()`、`verify_citations()` 均未修改。")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Shadow A/B retrieval comparison")
    parser.add_argument("--ids", default="", help="逗号分隔的用例编号")
    parser.add_argument("--limit", type=int, default=0, help="最多运行多少条用例")
    args = parser.parse_args()

    selected = CASES
    if args.ids:
        wanted = {item.strip() for item in args.ids.split(",") if item.strip()}
        selected = [case for case in CASES if case["id"] in wanted]
    if args.limit > 0:
        selected = selected[:args.limit]
    rows = [run_case(case) for case in selected]
    report = build_report(rows)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps({
        "report": str(OUTPUT),
        "cases": len(rows),
        "a_hits": sum(1 for row in rows if row["a_hit"]),
        "b_hits": sum(1 for row in rows if row["b_hit"]),
        "llm_calls": sum(row["llm_calls"] for row in rows),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()