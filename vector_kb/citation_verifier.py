#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""引用校验模块：检查生成回答中的条号是否来自检索结果。"""

from __future__ import annotations

import re
import sys
import unicodedata
from typing import Any

_HIERARCHICAL_CLAUSE_RE = re.compile(r"\d+(?:\.\d+)+")
_CHAPTER_CLAUSE_RE = re.compile(r"\u7b2c\s*(\d+(?:\.\d+)+)\s*\u6761")
_TABLE_CLAUSE_RE = re.compile(r"\u8868\s*(\d+)")

_CITATION_RE = re.compile(r"【\s*依据\s*[：:]\s*([^】]+?)\s*】")
_MECHANISM_RE = re.compile(r"【\s*同类机理参考\s*[：:]\s*([^】]+?)\s*】")
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
    matches = _CHAPTER_CLAUSE_RE.findall(normalized)
    if matches:
        return "/".join(matches)
    return normalized


def normalize_clause(clause: Any) -> list[str]:
    """Extract standard hierarchical clause numbers or table numbers."""
    normalized = unicodedata.normalize("NFKC", str(clause or "")).lower()
    normalized = normalized.replace("\uff0f", "/")

    explicit_matches = _CHAPTER_CLAUSE_RE.findall(normalized)
    numeric_matches = (
        explicit_matches
        if explicit_matches
        else _HIERARCHICAL_CLAUSE_RE.findall(normalized)
    )
    if numeric_matches:
        return list(dict.fromkeys(numeric_matches))

    result: list[str] = []
    for table_number in _TABLE_CLAUSE_RE.findall(normalized):
        value = f"\u8868{table_number}"
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


def _scope_value(chunk: dict[str, Any]) -> str:
    return str(chunk.get("scope") or "").strip()


def _is_direct_evidence(chunk: dict[str, Any]) -> bool:
    scope = _scope_value(chunk)
    kind = str(chunk.get("evidence_kind") or "").strip()
    if scope in ("device_specific", "procedure") or kind in ("direct", "procedure"):
        return True
    if scope in ("component_generic", "instrument_generic") or kind == "generic_mechanism":
        return False
    if str(chunk.get("source") or "") == "generic_mechanism":
        return False
    return True


def _is_generic_evidence(chunk: dict[str, Any]) -> bool:
    scope = _scope_value(chunk)
    kind = str(chunk.get("evidence_kind") or "").strip()
    return (
        scope in ("component_generic", "instrument_generic")
        or kind == "generic_mechanism"
        or str(chunk.get("source") or "") == "generic_mechanism"
    )


def _source_names(chunk: dict[str, Any]) -> set[str]:
    values = (
        chunk.get("doc_id"),
        chunk.get("title"),
        chunk.get("citation"),
        chunk.get("source"),
    )
    names = {_normalize_text(value) for value in values if value}
    return {name for name in names if name}


def _source_matches(content: str, chunk: dict[str, Any]) -> bool:
    needle = _normalize_text(content)
    if not needle:
        return False
    for name in _source_names(chunk):
        if needle in name or name in needle:
            return True
    return False

def _strip_known_doc_ids(content: str, known_docs: set[str]) -> str:
    """Remove known document IDs before clause normalization."""
    normalized = _normalize_text(content)
    for doc_id in sorted((doc for doc in known_docs if doc), key=len, reverse=True):
        normalized = normalized.replace(doc_id, "")
    return normalized


def _matches_chunk(content: str, chunk: dict[str, Any], known_docs: set[str]) -> bool:
    """\u5224\u65ad\u4e00\u6761\u5f15\u7528\u662f\u5426\u4e0e\u67d0\u4e2a\u68c0\u7d22\u7ed3\u679c\u5339\u914d\uff0c\u4f18\u5148\u6821\u9a8c\u6587\u6863\u53f7\u4e0e\u6761\u53f7\u3002"""
    normalized_content = _normalize_text(content)
    cited_clauses = normalize_clause(_strip_known_doc_ids(content, known_docs))
    if cited_clauses:
        if not clause_matches(cited_clauses, chunk.get("clause")):
            return False
    else:
        chunk_clause = _normalize_text(chunk.get("clause"))
        if not chunk_clause or chunk_clause not in normalized_content:
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
    """分层校验直接依据和同类机理参考。"""
    citations = [match.group(1).strip() for match in _CITATION_RE.finditer(str(answer or ""))]
    mechanism_refs = [match.group(1).strip() for match in _MECHANISM_RE.finditer(str(answer or ""))]

    all_chunks = [chunk for chunk in (chunks or []) if isinstance(chunk, dict)]
    direct_chunks = [
        chunk for chunk in all_chunks
        if _is_citation_eligible(chunk) and _is_direct_evidence(chunk)
    ]
    generic_chunks = [chunk for chunk in all_chunks if _is_generic_evidence(chunk)]
    known_docs = {
        _normalize_text(chunk.get("doc_id"))
        for chunk in direct_chunks
        if chunk.get("doc_id")
    }

    valid_direct: list[str] = []
    invalid_direct: list[str] = []
    valid_mechanism: list[str] = []
    invalid_mechanism: list[str] = []
    warnings: list[str] = []
    seen_valid: set[str] = set()
    seen_invalid: set[str] = set()

    for citation in citations:
        normalized_cited = normalize_clause(_strip_known_doc_ids(citation, known_docs))
        if not normalized_cited:
            if _debug_enabled():
                print(f"[引用校验] {citation} → 自由文本，跳过条号校验", flush=True)
            if citation not in seen_valid:
                valid_direct.append(citation)
                seen_valid.add(citation)
            continue

        matched_chunk = next(
            (chunk for chunk in direct_chunks if _matches_chunk(citation, chunk, known_docs)),
            None,
        )
        if _debug_enabled():
            cited_clause = "/".join(normalized_cited) or _clause_part(citation) or citation
            if matched_chunk is not None:
                print(
                    f"[引用校验] {cited_clause} → 匹配到 {matched_chunk.get('clause')}",
                    flush=True,
                )
            else:
                print(f"[引用校验] {cited_clause} → 未匹配", flush=True)
        if matched_chunk is not None:
            if citation not in seen_valid:
                valid_direct.append(citation)
                seen_valid.add(citation)
        elif citation not in seen_invalid:
            invalid_direct.append(citation)
            seen_invalid.add(citation)

    for reference in mechanism_refs:
        matched_chunk = next(
            (chunk for chunk in generic_chunks if _source_matches(reference, chunk)),
            None,
        )
        if matched_chunk is None:
            direct_match = next(
                (chunk for chunk in direct_chunks if _source_matches(reference, chunk)),
                None,
            )
            if direct_match is not None:
                matched_chunk = direct_match
                warnings.append(
                    f"device_specific_mislabeled_as_mechanism: {reference}"
                )
        if _debug_enabled():
            status = "匹配到" if matched_chunk is not None else "未匹配"
            print(f"[引用校验] 同类机理参考 {reference} → {status}", flush=True)
        if matched_chunk is not None:
            if reference not in valid_mechanism:
                valid_mechanism.append(reference)
        elif reference not in invalid_mechanism:
            invalid_mechanism.append(reference)

    invalid_citations = invalid_direct + invalid_mechanism
    valid_citations = valid_direct + valid_mechanism
    if _debug_enabled():
        print(
            f"[引用校验] 依据={len(citations)}, 同类机理参考={len(mechanism_refs)}",
            flush=True,
        )
    return {
        "valid": not invalid_citations,
        "invalid_citations": invalid_citations,
        "valid_citations": valid_citations,
        "valid_direct_citations": valid_direct,
        "invalid_direct_citations": invalid_direct,
        "valid_mechanism_references": valid_mechanism,
        "invalid_mechanism_references": invalid_mechanism,
        "warnings": warnings,
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
    """构造追加到原问题后的分层引用纠错提示。"""
    invalid = verification.get("invalid_citations") or []
    available_direct = sorted({
        _format_available_citation(chunk)
        for chunk in (chunks or [])
        if isinstance(chunk, dict)
        and chunk.get("doc_id")
        and chunk.get("clause")
        and _is_citation_eligible(chunk)
        and _is_direct_evidence(chunk)
    })
    available_mechanism = sorted({
        str(
            chunk.get("doc_id")
            or chunk.get("citation")
            or chunk.get("title")
            or chunk.get("source")
            or ""
        ).strip()
        for chunk in (chunks or [])
        if isinstance(chunk, dict) and _is_generic_evidence(chunk)
    } - {""})
    invalid_text = "、".join(str(item) for item in invalid) or "（无）"
    direct_text = "；".join(available_direct) or "（无）"
    mechanism_text = "；".join(available_mechanism) or "（无）"
    return (
        f"{question}\n\n"
        f"你上次的回答引用了以下无效内容：{invalid_text}。"
        f"可用直接依据：{direct_text}。"
        f"可用同类机理参考：{mechanism_text}。"
        "请重新回答：直接依据使用【依据：doc_id 第clause条】，"
        "同类机理参考使用【同类机理参考：来源名称】，不得混用。"
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
