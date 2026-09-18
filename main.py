#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""项目端到端统一入口：混合检索 + 生成 + 引用校验。

用法：
    python main.py "乙炔超标该怎么处理"             # 单次问答
    python main.py --debug "乙炔超标该怎么处理"     # 输出检索与生成调试信息
    python main.py                                  # 交互模式（输入 exit 退出）
"""

from __future__ import annotations

import argparse
import sys

from vector_kb.citation_verifier import (
    build_retry_prompt,
    remove_invalid_citation_sentences,
    verify_citations,
)
from vector_kb.hybrid_retriever import hybrid_retrieve
from vector_kb.generation import generate


def _trace(debug: bool, step: str, summary: str) -> None:
    """按统一格式输出调试摘要。"""
    if debug:
        print(f"[{step}] {summary}", flush=True)


def _shorten(text: str, limit: int = 120) -> str:
    """压缩调试输出中的长文本，避免打印完整条文。"""
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def _format_hits(hits: list[dict] | None, score_key: str) -> str:
    """把候选结果压缩为“条号(分数)”摘要。"""
    if not hits:
        return "无"
    parts = []
    for hit in hits:
        clause = hit.get("clause") or "（无条号）"
        score = hit.get(score_key)
        if score is None:
            parts.append(str(clause))
            continue
        try:
            parts.append(f"{clause}({float(score):.4f})")
        except (TypeError, ValueError):
            parts.append(str(clause))
    return "；".join(parts)


def _format_citations(citations: list[str] | None) -> str:
    """格式化引用列表，仅保留条号相关信息。"""
    if not citations:
        return "无"
    return "、".join(str(item) for item in citations)


def _format_output_summary(answer: str) -> str:
    """生成最终输出摘要，不展开完整回答。"""
    return f"长度={len(str(answer or ''))}；摘要={_shorten(answer, 100)}"


def _retrieval_trace(debug: bool):
    """返回供 hybrid_retrieve 使用的可选 trace 回调。"""
    if not debug:
        return None

    def callback(step: str, hits: list[dict]) -> None:
        score_key = "rrf_score" if step.startswith("RRF") else "score"
        _trace(debug, step, _format_hits(hits, score_key))

    return callback


def ask(question: str, debug: bool = False) -> str:
    """端到端问答：检索 → 生成 → 引用校验 → 必要时重写。"""
    _trace(debug, "用户问题", _shorten(question))
    _trace(debug, "查询改写结果", "无改写，使用原问题")
    chunks = hybrid_retrieve(
        question,
        top_k=5,
        trace=_retrieval_trace(debug),
    )
    if not chunks:
        final = "资料未覆盖，无法回答"
        _trace(debug, "最终输出", _format_output_summary(final))
        return final

    prompt = question
    answer = ""
    for attempt in range(3):
        _trace(debug, "生成调用", f"第{attempt + 1}次；候选条文={len(chunks)}条")
        answer = generate(prompt, chunks)
        verification = verify_citations(answer, chunks)
        _trace(
            debug,
            "引用校验结果",
            (
                f"valid={verification['valid']}；"
                f"有效引用={_format_citations(verification['valid_citations'])}；"
                f"无效引用={_format_citations(verification['invalid_citations'])}"
            ),
        )
        if verification["valid"]:
            final = answer
            _trace(debug, "最终输出", _format_output_summary(final))
            return final
        if attempt < 2:
            prompt = build_retry_prompt(question, verification, chunks)
            available = [
                str(chunk.get("clause") or "（无条号）")
                for chunk in chunks
            ]
            _trace(
                debug,
                "查询改写结果",
                (
                    f"第{attempt + 2}次生成前追加纠错提示；"
                    f"无效引用={_format_citations(verification['invalid_citations'])}；"
                    f"可用条号={_format_citations(available)}"
                ),
            )

    cleaned = remove_invalid_citation_sentences(answer, chunks)
    final = cleaned or "资料未覆盖，无法回答"
    _trace(debug, "最终输出", _format_output_summary(final))
    return final


def _print_answer(question: str, debug: bool = False) -> None:
    """交互模式输出格式：问题 → 分隔线 → 回答 → 分隔线。"""
    separator = "─" * 40
    print(f"问题：{question}")
    print(separator)
    print(ask(question, debug=debug))
    print(separator)


def main(argv=None) -> int:
    """入口：有参数=单次问答；无参数=交互模式。"""
    parser = argparse.ArgumentParser(description="油浸式变压器 DGA 诊断问答")
    parser.add_argument("--debug", action="store_true", help="输出检索与生成调试摘要")
    parser.add_argument("question", nargs="*", help="要询问的问题")
    args = parser.parse_args(argv)

    if args.question:
        question = " ".join(args.question).strip()
        try:
            print(ask(question, debug=args.debug))
        except RuntimeError as e:
            print(f"问答失败：{e}")
            return 1
        return 0

    print("进入交互模式（输入 exit 退出）")
    while True:
        try:
            question = input("请输入问题：").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not question:
            continue
        if question.lower() in ("exit", "quit", "退出"):
            break
        try:
            _print_answer(question, debug=args.debug)
        except RuntimeError as e:
            print(f"问答失败：{e}")
    print("已退出。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())