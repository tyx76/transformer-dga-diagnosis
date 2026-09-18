#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""引用校验模块：检查生成回答中的条号是否来自检索结果。"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

_CITATION_RE = re.compile(r"【\s*依据\s*[：:]\s*([^】]+?)\s*】")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?])|\n+")


def _normalize_text(value: Any) -> str:
    """统一全半角、大小写并移除空白，便于稳定比对引用。"""
    text = unicodedata.normalize("NFKC", str(value or "")).lower()
    return re.sub(r"\s+", "", text)


def _contains_clause(content: str, clause: str) -> bool:
    """判断规范化内容中是否独立包含某个条号，避免子串误命中。"""
    if not clause:
        return False
    pattern = rf"(?<![0-9.]){re.escape(clause)}(?![0-9.])"
    return re.search(pattern, content) is not None


def _matches_chunk(content: str, chunk: dict[str, Any], known_docs: set[str]) -> bool:
    """判断一条引用是否与某个检索结果匹配，优先校验文档号与条号。"""
    normalized_content = _normalize_text(content)
    clause = _normalize_text(chunk.get("clause"))
    if not _contains_clause(normalized_content, clause):
        return False

    doc_id = _normalize_text(chunk.get("doc_id"))
    if not doc_id:
        return True

    # 若引用中明确写了一个带字母/斜杠的标准文档号，必须与当前 chunk 匹配。
    doc_prefix = normalized_content.split("第", 1)[0]
    if re.search(r"[a-z/]", doc_prefix) and doc_id not in doc_prefix:
        return False
    if doc_id in normalized_content:
        return True

    # 未写文档号时可按唯一条号校验；若写了其他已知文档，则不匹配。
    mentioned_known_doc = any(
        known_doc and known_doc in normalized_content
        for known_doc in known_docs
        if known_doc != doc_id
    )
    return not mentioned_known_doc


def verify_citations(answer: str, chunks: list[dict] | None) -> dict:
    """校验回答中的所有【依据：...】引用是否存在于检索结果中。"""
    citations = [match.group(1).strip() for match in _CITATION_RE.finditer(str(answer or ""))]
    known_docs = {
        _normalize_text(chunk.get("doc_id"))
        for chunk in (chunks or [])
        if isinstance(chunk, dict) and chunk.get("doc_id")
    }
    valid_citations: list[str] = []
    invalid_citations: list[str] = []
    seen_valid: set[str] = set()
    seen_invalid: set[str] = set()

    for citation in citations:
        matched = any(
            isinstance(chunk, dict) and _matches_chunk(citation, chunk, known_docs)
            for chunk in (chunks or [])
        )
        if matched:
            if citation not in seen_valid:
                valid_citations.append(citation)
                seen_valid.add(citation)
        elif citation not in seen_invalid:
            invalid_citations.append(citation)
            seen_invalid.add(citation)

    return {
        "valid": not invalid_citations,
        "invalid_citations": invalid_citations,
        "valid_citations": valid_citations,
    }


def _format_available_citation(chunk: dict[str, Any]) -> str:
    """将可用条文格式化为模型容易复用的引用文本。"""
    doc_id = str(chunk.get("doc_id") or "").strip()
    clause = str(chunk.get("clause") or "").strip()
    if not clause:
        return doc_id
    if clause[0].isdigit():
        if re.fullmatch(r"[0-9.]+", clause):
            return f"{doc_id} 第{clause}条"
        return f"{doc_id} 第{clause}"
    return f"{doc_id} {clause}"


def build_retry_prompt(question: str, verification: dict, chunks: list[dict] | None) -> str:
    """构造追加到原问题后的引用纠错提示。"""
    invalid = verification.get("invalid_citations") or []
    available = sorted({
        _format_available_citation(chunk)
        for chunk in (chunks or [])
        if isinstance(chunk, dict) and chunk.get("doc_id") and chunk.get("clause")
    })
    invalid_text = "、".join(str(item) for item in invalid) or "（无）"
    available_text = "；".join(available) or "（无可用条号）"
    return (
        f"{question}\n\n"
        f"你上次的回答引用了以下不存在的条号：{invalid_text}。"
        f"以下是你可用的条号列表：{available_text}。"
        "请重新回答，只允许引用上述条号。"
    )


def remove_invalid_citation_sentences(answer: str, chunks: list[dict] | None) -> str:
    """删除包含无效引用的句子，仅保留引用有效的句子。"""
    parts = _SENTENCE_SPLIT_RE.split(str(answer or ""))
    kept: list[str] = []
    for part in parts:
        sentence = part.strip()
        if not sentence:
            continue
        if verify_citations(sentence, chunks)["valid"]:
            kept.append(sentence)
    return "\n".join(kept).strip()


__all__ = [
    "verify_citations",
    "build_retry_prompt",
    "remove_invalid_citation_sentences",
]