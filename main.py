#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""项目端到端统一入口：检索（retrieve）+ 生成（generate）。

用法：
    python main.py "乙炔超标该怎么处理"     # 单次问答
    python main.py                          # 交互模式（输入 exit 退出）

说明：检索与生成直接复用 vector_kb/cli.py 中的 retrieve() / generate()，不重复实现。
"""
import sys

from vector_kb.cli import retrieve, generate


def ask(question: str) -> str:
    """端到端问答（纯函数）：检索 → 若无条文直接拒答，否则调用生成。

    - 不读写全局状态；
    - chunks 为空时不调用生成 API。
    """
    chunks = retrieve(question)
    if not chunks:
        return "资料未覆盖，无法回答"
    return generate(question, chunks)


def _print_answer(question: str) -> None:
    """交互模式输出格式：问题 → 分隔线 → 回答 → 分隔线。"""
    separator = "─" * 40
    print(f"问题：{question}")
    print(separator)
    print(ask(question))
    print(separator)


def main(argv=None) -> int:
    """入口：有参数=单次问答；无参数=交互模式。"""
    args = list(sys.argv[1:] if argv is None else argv)

    if args:
        question = " ".join(args).strip()
        try:
            print(ask(question))
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
            _print_answer(question)
        except RuntimeError as e:
            print(f"问答失败：{e}")
    print("已退出。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())