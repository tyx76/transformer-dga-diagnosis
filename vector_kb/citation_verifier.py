#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""引用校验模块：检查生成回答中的条号是否来自检索结果。"""

from __future__ import annotations

import re
import sys
import unicodedata
from typing import Any

_CITATION_RE = re.compile(r"【\s*依据\s*[：:]\s*([^】]+?)\s*】")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?])|\n+")


def _normalize_text(value: Any) -> str:
    """统一全半角、大小写并移除空白，便于稳定比对引用。"""
    text = unicodedata.normalize("NFKC", str(value or "")).lower()
    return re.sub(r"\s+", "", text)


def _debug_enabled() -> bool:
    return "--debug" in sys.argv[1:]


def _clause_part(content: str) -> str:
    """Extract the clause portion from a citation string."""
    normalized = _normalize_text(content)
    if "\u7b2c" in normalized:
        return normalized.split("\u7b2c", 1)[1]
    return normalized


def normalize_clause(clause: Any) -> list[str]:
    """Extract normalized numeric clause parts from one or more clauses."""
    normalized = unicodedata.normalize("NFKC", str(clause or "")).lower()
    normalized = normalized.replace("\uff0f", "/")
    if "\u7b2c" in normalized:
        normalized = normalized.split("\u7b2c", 1)[1]

    parts = normalized.split("/") if "/" in normalized else [normalized]
    result: list[str] = []
    for part in parts:
        base = part.split("\u8868", 1)[0]
        match = re.search(r"\d+(?:\.\d+)*", base)
        if not match:
            continue
        value = match.group(0)
        if value not in result:
            result.append(value)
    return result


def clause_matches(cited_clause: Any, valid_clause: Any) -> bool:
    """Return whether cited and valid clauses match exactly or by hierarchy."""
    cited = normalize_clause(cited_clause)
    valid = normalize_clause(valid_clause)
    if not cited or not valid:
        return False
    for left in cited:
        for right in valid:
            if left == right:
                return True
            if left.startswith(right + ".") or right.startswith(left + "."):
                return True
    return False


def _is_citation_eligible(chunk: dict[str, Any]) -> bool:
    """Return whether a chunk may be used for citation matching."""
    if not isinstance(chunk, dict):
        return False
    if "citation_eligible" in chunk:
        return bool(chunk.get("citation_eligible"))
    return bool(chunk.get("doc_id") and chunk.get("clause"))


def _matches_chunk(content: str, chunk: dict[str, Any], known_docs: set[str]) -> bool:
    """\u5224\u65ad\u4e00\u6761\u5f15\u7528\u662f\u5426\u4e0e\u67d0\u4e2a\u68c0\u7d22\u7ed3\u679c\u5339\u914d\uff0c\u4f18\u5148\u6821\u9a8c\u6587\u6863\u53f7\u4e0e\u6761\u53f7\u3002"""
    normalized_content = _normalize_text(content)
    cited_clause = _clause_part(content)
    if not clause_matches(cited_clause, chunk.get("clause")):
        return False

    doc_id = _normalize_text(chunk.get("doc_id"))
    if not doc_id:
        return True

    doc_prefix = normalized_content.split("\u7b2c", 1)[0]
    if re.search(r"[a-z/]", doc_prefix) and doc_id not in doc_prefix:
        return False
    if doc_id in normalized_content:
        return True

    mentioned_known_doc = any(
        known_doc and known_doc in normalized_content
        for known_doc in known_docs
        if known_doc != doc_id
    )
    return not mentioned_known_doc


def verify_citations(answer: str, chunks: list[dict] | None) -> dict:
    """校验回答中的引用是否存在于可引用检索结果中。"""
    citations = [match.group(1).strip() for match in _CITATION_RE.finditer(str(answer or ""))]
    eligible_chunks = [
        chunk
        for chunk in (chunks or [])
        if isinstance(chunk, dict) and _is_citation_eligible(chunk)
    ]
    known_docs = {
        _normalize_text(chunk.get("doc_id"))
        for chunk in eligible_chunks
        if chunk.get("doc_id")
    }
    valid_citations: list[str] = []
    invalid_citations: list[str] = []
    seen_valid: set[str] = set()
    seen_invalid: set[str] = set()

    for citation in citations:
        matched_chunk = next(
            (
                chunk
                for chunk in eligible_chunks
                if _matches_chunk(citation, chunk, known_docs)
            ),
            None,
        )
        if _debug_enabled():
            normalized_cited = normalize_clause(citation)
            cited_clause = "/".join(normalized_cited) or _clause_part(citation) or citation
            if matched_chunk is not None:
                print(
                    f"[\u5f15\u7528\u6821\u9a8c] {cited_clause} \u2192 \u5339\u914d\u5230 "
                    f"{matched_chunk.get('clause')}",
                    flush=True,
                )
            else:
                print(
                    f"[\u5f15\u7528\u6821\u9a8c] {cited_clause} \u2192 \u672a\u5339\u914d",
                    flush=True,
                )
        if matched_chunk is not None:
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
        if isinstance(chunk, dict)
        and chunk.get("doc_id")
        and chunk.get("clause")
        and _is_citation_eligible(chunk)
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
    "normalize_clause",
    "clause_matches",
    "verify_citations",
    "build_retry_prompt",
    "remove_invalid_citation_sentences",
]