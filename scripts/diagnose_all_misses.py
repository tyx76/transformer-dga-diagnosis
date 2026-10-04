#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Systematically diagnose Top-5 source misses in the 138-question exam set."""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vector_kb.bm25_retriever import bm25_retrieve
from vector_kb.chunk_filter import is_body_text, prioritize_results, query_overlap
from vector_kb.hybrid_retriever import _backend_name, _resolve_config
from vector_kb.query_planner import plan_query
from vector_kb.retrieval import retrieve
from vector_kb.rrf_fusion import rrf_fusion

DEFAULT_QUESTIONS = ROOT / "data" / "evaluation" / "plant_kb_full_questions.jsonl"
DEFAULT_DETAILS = ROOT / "docs" / "exam_proof" / "138题评测明细_20261004.jsonl"
DEFAULT_EVIDENCE = ROOT / "data" / "samples" / "测试集" / "测试集" / "evaluation_dataset_final.json"
DEFAULT_KB = ROOT / "knowledge" / "plant_kb" / "data" / "knowledge.jsonl"
DEFAULT_REPORT = ROOT / "docs" / "未命中题系统诊断.md"
DEFAULT_OUTPUT = ROOT / "docs" / "exam_proof" / "未命中题系统诊断_20261004.jsonl"
CANDIDATE_K = 300
FUZZY_THRESHOLD = 0.72
PARTIAL_THRESHOLD = 0.35
CATEGORY_ORDER = ("A", "B", "C", "D", "E", "F", "G")
CATEGORY_NAMES = {
    "A": "不在库",
    "B": "domain错误",
    "C": "切碎",
    "D": "查询不匹配",
    "E": "排名靠后",
    "F": "评分不一致",
    "G": "被过滤",
}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as stream:
        for line_number, line in enumerate(stream, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number} invalid JSON") from exc
            if isinstance(item, dict):
                rows.append(item)
    return rows


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as stream:
        return json.load(stream)


def _normalize(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).lower()
    return "".join(char for char in text if char.isalnum())


def _source_name(value: Any) -> str:
    text = str(value or "").strip().replace("\\", "/")
    text = Path(text).name or text
    if text.lower().endswith(".md"):
        text = text[:-3]
    return _normalize(text.replace("预处理后_", ""))


def _ngrams(text: str, sizes: tuple[int, ...] = (2, 3, 4)) -> set[str]:
    value = _normalize(text)
    result: set[str] = set()
    for size in sizes:
        result.update(value[index:index + size] for index in range(max(0, len(value) - size + 1)))
    return {gram for gram in result if gram}


def _source_matches(source_file: Any, row: dict[str, Any]) -> bool:
    source = _source_name(source_file)
    if not source:
        return False
    haystack = " ".join(
        str(row.get(field) or "")
        for field in ("source_file", "source", "doc_id", "title", "citation", "section")
    )
    haystack_norm = _normalize(haystack)
    if not haystack_norm:
        return False
    if source in haystack_norm or haystack_norm in source:
        return True
    source_grams = _ngrams(source, (2, 3, 4))
    if len(source) < 12 or not source_grams:
        return False
    covered = sum(1 for gram in source_grams if gram in haystack_norm)
    return covered / len(source_grams) >= 0.82


def _clauses(value: Any) -> set[str]:
    return set(re.findall(r"\d+(?:\.\d+)+", unicodedata.normalize("NFKC", str(value or ""))))


def _clause_matches(evidence_location: Any, row: dict[str, Any]) -> bool:
    expected = _clauses(evidence_location)
    if not expected:
        return False
    actual_text = " ".join(
        str(row.get(field) or "")
        for field in ("clause", "locator_value", "section", "section_path", "chapter")
    )
    actual = _clauses(actual_text)
    return any(
        left == right or right.startswith(left + ".") or left.startswith(right + ".")
        for left in expected
        for right in actual
    )


def _text_similarity(evidence_text: Any, kb_text: Any) -> float:
    expected = _normalize(evidence_text)
    actual = _normalize(kb_text)
    if not expected or not actual:
        return 0.0
    if expected in actual or actual in expected:
        return 1.0
    expected_grams = _ngrams(expected, (2, 3, 4))
    if not expected_grams:
        return 0.0
    coverage = sum(1 for gram in expected_grams if gram in actual) / len(expected_grams)
    sequence = difflib.SequenceMatcher(
        None, expected[:1600], actual[:1600], autojunk=False
    ).ratio()
    return round(0.72 * coverage + 0.28 * sequence, 6)


def _row_text(row: dict[str, Any]) -> str:
    return str(row.get("text") or row.get("clean_text") or row.get("raw_text") or "")


def _location_matches(location: Any, row: dict[str, Any]) -> bool:
    raw = unicodedata.normalize("NFKC", str(location or "")).strip()
    if not raw:
        return False
    metadata = _row_metadata(row)
    haystack = _normalize(
        " ".join(
            str(row.get(field) or metadata.get(field) or "")
            for field in (
                "title", "section", "section_path", "chapter", "clause",
                "citation", "page_start", "page_end", "page", "line_start", "line_end",
            )
        )
    )
    if not haystack:
        return False
    for page in re.findall(r"(?i)\bp0*(\d+)\b", raw):
        if _normalize(page) and _normalize(page) in haystack:
            return True
    for start, end in re.findall(r"(?:行|line)\s*(\d+)\s*[-~—]\s*(\d+)", raw, flags=re.I):
        try:
            left, right = int(start), int(end)
        except ValueError:
            continue
        raw_line_start = row.get("line_start") or metadata.get("line_start")
        raw_line_end = row.get("line_end") or metadata.get("line_end")
        try:
            row_start = int(raw_line_start)
            row_end = int(raw_line_end)
        except (TypeError, ValueError):
            continue
        if max(left, row_start) <= min(right, row_end):
            return True
    segments = re.split(r"[/；;|、,，]+", raw)
    for segment in segments:
        for token in re.findall(r"[\u4e00-\u9fffA-Za-z]{4,}", segment):
            if token and _normalize(token) and _normalize(token) in haystack:
                return True
    return False


def _row_metadata(row: dict[str, Any]) -> dict[str, Any]:
    metadata = row.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _row_domain(row: dict[str, Any]) -> str:
    return str(row.get("domain") or _row_metadata(row).get("domain") or row.get("module") or "")


def _row_citation_eligible(row: dict[str, Any]) -> bool:
    value = row.get("is_citable")
    if value is None:
        value = _row_metadata(row).get("is_citable")
    return bool(value)


def _row_is_body(row: dict[str, Any]) -> bool:
    return is_body_text(
        {
            "text": _row_text(row),
            "title": row.get("title") or "",
            "clause": row.get("clause") or "",
        }
    )


def _row_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("doc_id") or ""), str(row.get("clause") or ""))
def _compact_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "doc_id": row.get("doc_id"),
        "clause": row.get("clause"),
        "title": row.get("title"),
        "source_file": row.get("source_file") or row.get("source"),
        "domain": _row_domain(row),
        "scope": row.get("scope") or _row_metadata(row).get("scope"),
        "evidence_kind": row.get("evidence_kind") or _row_metadata(row).get("evidence_kind"),
        "is_body": _row_is_body(row),
        "citation_eligible": _row_citation_eligible(row),
        "text_preview": _row_text(row)[:280],
    }


def _score(item: dict[str, Any] | None) -> float | None:
    if not item:
        return None
    for field in ("score", "rrf_score", "similarity", "bm25_score"):
        value = item.get(field)
        try:
            if value is not None:
                return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _rank(results: list[dict[str, Any]], target_rows: list[dict[str, Any]]) -> tuple[int | None, dict[str, Any] | None]:
    if not target_rows:
        return None, None
    target_keys = {_row_key(row) for row in target_rows}
    for rank, item in enumerate(results or [], start=1):
        if not isinstance(item, dict):
            continue
        if (str(item.get("doc_id") or ""), str(item.get("clause") or "")) in target_keys:
            return rank, item
    for rank, item in enumerate(results or [], start=1):
        if not isinstance(item, dict):
            continue
        for target in target_rows:
            if _source_matches(target.get("source_file") or target.get("source"), item) and _clause_matches(
                target.get("clause") or "", item
            ):
                return rank, item
    return None, None

def _rank_label(rank: int | None, limit: int = CANDIDATE_K) -> str:
    return str(rank) if rank is not None else f">{limit}"


def _best_target_similarity(target_rows: list[dict[str, Any]], evidence_items: list[dict[str, Any]]) -> float:
    best = 0.0
    for target in target_rows:
        for evidence in evidence_items:
            best = max(best, _text_similarity(evidence.get("evidence_text"), _row_text(target)))
    return round(best, 6)


def _find_targets(evidence_items: list[dict[str, Any]], kb_rows: list[dict[str, Any]]) -> dict[str, Any]:
    details: list[dict[str, Any]] = []
    preferred_rows: list[dict[str, Any]] = []
    all_source_clause_rows: list[dict[str, Any]] = []
    all_partial_rows: list[dict[str, Any]] = []
    source_match_total = 0
    clause_match_total = 0
    exact_match_total = 0
    global_exact_match_total = 0

    normalized_rows = [
        {"row": row, "text": _normalize(_row_text(row))}
        for row in kb_rows
    ]

    for evidence_index, evidence in enumerate(evidence_items, start=1):
        evidence_text = str(evidence.get("evidence_text") or "").strip()
        source_file = str(evidence.get("source_file") or "").strip()
        location = str(evidence.get("evidence_location") or "").strip()
        evidence_norm = _normalize(evidence_text)
        candidates: list[dict[str, Any]] = []
        global_exact = 0

        for wrapped in normalized_rows:
            row = wrapped["row"]
            row_text_norm = wrapped["text"]
            exact = bool(evidence_norm and evidence_norm in row_text_norm)
            source_match = _source_matches(source_file, row)
            clause_match = _clause_matches(location, row)
            if exact:
                global_exact += 1
            if not (source_match or clause_match or exact):
                continue
            similarity = 1.0 if exact else _text_similarity(evidence_text, _row_text(row))
            candidates.append(
                {
                    "row": row,
                    "source_match": source_match,
                    "clause_match": clause_match,
                    "exact": exact,
                    "similarity": similarity,
                }
            )
            if source_match:
                source_match_total += 1
            if clause_match:
                clause_match_total += 1
            if exact:
                exact_match_total += 1

        if not candidates:
            for wrapped in normalized_rows:
                row = wrapped["row"]
                similarity = _text_similarity(evidence_text, _row_text(row))
                if similarity >= PARTIAL_THRESHOLD:
                    candidates.append(
                        {
                            "row": row,
                            "source_match": False,
                            "clause_match": False,
                            "exact": False,
                            "similarity": similarity,
                        }
                    )

        candidates.sort(
            key=lambda item: (
                bool(item["exact"]),
                bool(item["source_match"] and item["clause_match"]),
                bool(item["source_match"]),
                float(item["similarity"]),
                bool(_row_is_body(item["row"])),
            ),
            reverse=True,
        )
        source_clause = [item for item in candidates if item["source_match"] and item["clause_match"]]
        exact_items = [item for item in candidates if item["exact"]]
        fuzzy_items = [item for item in candidates if item["similarity"] >= FUZZY_THRESHOLD]
        partial_items = [item for item in candidates if item["similarity"] >= PARTIAL_THRESHOLD]
        all_source_clause_rows.extend(item["row"] for item in source_clause)
        all_partial_rows.extend(item["row"] for item in partial_items)

        preferred: list[dict[str, Any]] = []
        match_mode = "not_found"
        if exact_items:
            preferred = exact_items[:3]
            match_mode = "exact_text"
        elif fuzzy_items:
            preferred = fuzzy_items[:3]
            match_mode = "fuzzy_text"
        elif source_clause:
            preferred = source_clause[:3]
            match_mode = "source_clause_only"
        elif candidates and candidates[0]["similarity"] >= PARTIAL_THRESHOLD:
            preferred = candidates[:3]
            match_mode = "fragment_only"

        preferred_rows.extend(item["row"] for item in preferred)
        details.append(
            {
                "evidence_index": evidence_index,
                "source_file": source_file,
                "evidence_location": location,
                "evidence_text": evidence_text,
                "expected_clauses": sorted(_clauses(location)),
                "match_mode": match_mode,
                "source_match_count": sum(1 for item in candidates if item["source_match"]),
                "clause_match_count": sum(1 for item in candidates if item["clause_match"]),
                "exact_match_count": len(exact_items),
                "global_exact_match_count": global_exact,
                "partial_match_count": len(partial_items),
                "best_similarity": round(max((item["similarity"] for item in candidates), default=0.0), 6),
                "targets": [_compact_row(item["row"]) for item in preferred],
            }
        )

    deduped: dict[tuple[str, str], dict[str, Any]] = {}
    for row in preferred_rows:
        deduped.setdefault(_row_key(row), row)
    return {
        "evidence_details": details,
        "target_rows": list(deduped.values()),
        "target_found": bool(deduped),
        "source_clause_present": bool(all_source_clause_rows),
        "partial_fragments_present": bool(all_partial_rows),
        "source_match_count": source_match_total,
        "clause_match_count": clause_match_total,
        "exact_match_count": exact_match_total,
        "global_exact_match_count": global_exact_match_total,
    }
def _build_kb_indexes(kb_rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_index: dict[str, set[int]] = defaultdict(set)
    clause_index: dict[str, set[int]] = defaultdict(set)
    normalized_rows: list[str] = []
    for index, row in enumerate(kb_rows):
        text = _row_text(row)
        normalized_rows.append(_normalize(text))
        for field in ("source_file", "source", "doc_id", "title", "citation", "section"):
            value = str(row.get(field) or "")
            if not value:
                continue
            parts = [value]
            lower = value.lower()
            md_pos = lower.find(".md")
            if md_pos >= 0:
                parts.append(value[: md_pos + 3])
            for part in parts:
                name = _source_name(part)
                if name:
                    source_index[name].add(index)
        for field in ("clause", "locator_value", "section", "section_path", "chapter"):
            for clause in _clauses(row.get(field)):
                clause_index[clause].add(index)
    return {
        "source_index": source_index,
        "clause_index": clause_index,
        "normalized_rows": normalized_rows,
    }


def _source_indices(source_file: str, indexes: dict[str, Any]) -> set[int]:
    source_index = indexes["source_index"]
    key = _source_name(source_file)
    if not key:
        return set()
    direct = set(source_index.get(key, set()))
    if direct:
        return direct
    result: set[int] = set()
    for candidate, indices in source_index.items():
        if not candidate:
            continue
        if key in candidate or candidate in key:
            result.update(indices)
            continue
        grams = _ngrams(key, (2, 3, 4))
        if len(key) >= 12 and grams:
            covered = sum(1 for gram in grams if gram in candidate)
            if covered / len(grams) >= 0.82:
                result.update(indices)
    return result


def _clause_indices(location: str, indexes: dict[str, Any]) -> set[int]:
    expected = _clauses(location)
    if not expected:
        return set()
    result: set[int] = set()
    for actual, indices in indexes["clause_index"].items():
        if any(
            left == actual or actual.startswith(left + ".") or left.startswith(actual + ".")
            for left in expected
        ):
            result.update(indices)
    return result


def _find_targets_fast(
    evidence_items: list[dict[str, Any]],
    kb_rows: list[dict[str, Any]],
    indexes: dict[str, Any],
) -> dict[str, Any]:
    details: list[dict[str, Any]] = []
    preferred_rows: list[dict[str, Any]] = []
    all_source_clause_rows: list[dict[str, Any]] = []
    all_partial_rows: list[dict[str, Any]] = []
    source_match_total = 0
    clause_match_total = 0
    exact_match_total = 0
    global_exact_match_total = 0
    normalized_rows = indexes["normalized_rows"]

    for evidence_index, evidence in enumerate(evidence_items, start=1):
        evidence_text = str(evidence.get("evidence_text") or "").strip()
        source_file = str(evidence.get("source_file") or "").strip()
        location = str(evidence.get("evidence_location") or "").strip()
        evidence_norm = _normalize(evidence_text)
        source_indices = _source_indices(source_file, indexes)
        clause_indices = _clause_indices(location, indexes)
        candidate_indices = source_indices | clause_indices
        global_exact = 0
        used_global_exact = False

        if evidence_norm:
            exact_indices = {
                index
                for index, row_text in enumerate(normalized_rows)
                if evidence_norm in row_text
            }
            if exact_indices:
                candidate_indices.update(exact_indices)
                global_exact = len(exact_indices)
                used_global_exact = True

        candidates: list[dict[str, Any]] = []
        if not candidate_indices and evidence_norm:
            probes = [
                evidence_norm[start:start + 16]
                for start in range(0, min(len(evidence_norm), 480), 24)
            ]
            probes = [probe for probe in probes if len(probe) >= 8]
            for index, row_text in enumerate(normalized_rows):
                if probes and sum(1 for probe in probes if probe in row_text) >= 2:
                    candidate_indices.add(index)

        for index in candidate_indices:
            row = kb_rows[index]
            exact = bool(evidence_norm and evidence_norm in normalized_rows[index])
            source_match = index in source_indices
            clause_match = index in clause_indices
            location_match = _location_matches(location, row)
            similarity = 1.0 if exact else _text_similarity(evidence_text, _row_text(row))
            candidates.append(
                {
                    "row": row,
                    "source_match": source_match,
                    "clause_match": clause_match,
                    "location_match": location_match,
                    "exact": exact,
                    "similarity": similarity,
                }
            )
            if source_match:
                source_match_total += 1
            if clause_match:
                clause_match_total += 1

        if not used_global_exact and evidence_norm:
            global_exact = sum(1 for row_text in normalized_rows if evidence_norm in row_text)
        global_exact_match_total += global_exact

        exact_pool = [item for item in candidates if item["exact"]]
        location_candidates = [item for item in candidates if item["location_match"]]
        if exact_pool:
            ranked_candidates = list(exact_pool)
            ranked_candidates.extend(item for item in location_candidates if item not in exact_pool)
        elif location_candidates:
            ranked_candidates = list(location_candidates)
        else:
            ranked_candidates = list(candidates)
        exact_match_total += len(exact_pool)
        ranked_candidates.sort(
            key=lambda item: (
                bool(item["location_match"]),
                bool(item["exact"]),
                bool(item["source_match"] and item["clause_match"]),
                bool(item["source_match"]),
                float(item["similarity"]),
                bool(_row_is_body(item["row"])),
            ),
            reverse=True,
        )
        source_clause = [item for item in ranked_candidates if item["source_match"] and item["clause_match"]]
        exact_items = [item for item in ranked_candidates if item["exact"]]
        fuzzy_items = [item for item in ranked_candidates if item["similarity"] >= FUZZY_THRESHOLD]
        partial_items = [item for item in ranked_candidates if item["similarity"] >= PARTIAL_THRESHOLD]
        all_source_clause_rows.extend(item["row"] for item in source_clause)
        all_partial_rows.extend(item["row"] for item in partial_items)

        preferred: list[dict[str, Any]] = []
        match_mode = "not_found"
        if exact_items:
            preferred = exact_items[:3]
            match_mode = "exact_text_location" if location_candidates else "exact_text"
        elif fuzzy_items:
            preferred = fuzzy_items[:3]
            match_mode = "fuzzy_text_location" if location_candidates else "fuzzy_text"
        elif source_clause:
            preferred = source_clause[:3]
            match_mode = "source_clause_only"
        elif ranked_candidates and ranked_candidates[0]["similarity"] >= PARTIAL_THRESHOLD:
            preferred = ranked_candidates[:3]
            match_mode = "fragment_only"

        preferred_rows.extend(item["row"] for item in preferred)
        details.append(
            {
                "evidence_index": evidence_index,
                "source_file": source_file,
                "evidence_location": location,
                "evidence_text": evidence_text,
                "expected_clauses": sorted(_clauses(location)),
                "match_mode": match_mode,
                "source_match_count": sum(1 for item in candidates if item["source_match"]),
                "clause_match_count": sum(1 for item in candidates if item["clause_match"]),
                "exact_match_count": len(exact_items),
                "global_exact_match_count": global_exact,
                "partial_match_count": len(partial_items),
                "best_similarity": round(max((item["similarity"] for item in candidates), default=0.0), 6),
                "targets": [_compact_row(item["row"]) for item in preferred],
            }
        )

    deduped: dict[tuple[str, str], dict[str, Any]] = {}
    for row in preferred_rows:
        deduped.setdefault(_row_key(row), row)
    return {
        "evidence_details": details,
        "target_rows": list(deduped.values()),
        "target_found": bool(deduped),
        "source_clause_present": bool(all_source_clause_rows),
        "partial_fragments_present": bool(all_partial_rows),
        "source_match_count": source_match_total,
        "clause_match_count": clause_match_total,
        "exact_match_count": exact_match_total,
        "global_exact_match_count": global_exact_match_total,
    }

def _allowed_domains(route: dict[str, Any]) -> list[str]:
    values = route.get("domains") if isinstance(route, dict) else None
    if not values:
        return []
    return [str(value) for value in values if str(value).strip()]


def _domain_allowed(target_rows: list[dict[str, Any]], domains: list[str]) -> bool:
    if not domains or not target_rows:
        return True
    target_domains = {_row_domain(row).strip().lower() for row in target_rows if _row_domain(row).strip()}
    if not target_domains:
        return True
    return bool(target_domains & {domain.lower() for domain in domains})


def _has_allowed_body(target_rows: list[dict[str, Any]], domains: list[str]) -> bool:
    rows = [row for row in target_rows if _domain_allowed([row], domains)]
    return any(_row_is_body(row) for row in rows)


def _all_citation_eligible(target_rows: list[dict[str, Any]], domains: list[str]) -> bool:
    rows = [row for row in target_rows if _domain_allowed([row], domains)]
    return bool(rows) and all(_row_citation_eligible(row) for row in rows)


def _primary_target_row(target_rows: list[dict[str, Any]], domains: list[str]) -> dict[str, Any] | None:
    rows = [row for row in target_rows if _domain_allowed([row], domains)] or list(target_rows)
    if not rows:
        return None
    return max(rows, key=lambda row: (_row_is_body(row), _row_citation_eligible(row), len(_row_text(row))))


def _classify(case: dict[str, Any]) -> tuple[str, str]:
    domains = _allowed_domains(case.get("route") or {})
    target_rows = case.get("target_rows") or []
    if not target_rows:
        if case.get("source_clause_present") or case.get("partial_fragments_present"):
            return "C", "目标来源或条号有部分命中，但 evidence_text 未形成完整条文块。"
        return "A", "知识库中未找到与 evidence_text 足够接近的条文，且无来源/条号部分命中。"

    if not _domain_allowed(target_rows, domains):
        target_domains = sorted({_row_domain(row) for row in target_rows})
        return "B", f"目标 domain={target_domains}，路由 domain={domains}，命中 domain 过滤错配；去掉域过滤后向量={_rank_label(case.get('vector_unfiltered_rank'))}，BM25={_rank_label(case.get('bm25_unfiltered_rank'))}。"

    best_similarity = float(case.get("best_similarity") or 0.0)
    if case.get("source_clause_present") and best_similarity < FUZZY_THRESHOLD:
        return "C", f"来源+条号存在，但最高 evidence_text 相似度仅 {best_similarity:.3f}，属于标题/碎片或跨块切分。"

    if case.get("rrf_rank") is not None and case.get("prioritized_rank") is None:
        return "G", "目标进入 RRF，但正文/重叠重排后跌出候选集合，属于重排过滤。"

    recalled = any(
        isinstance(case.get(field), int) and case[field] <= CANDIDATE_K
        for field in ("vector_rank", "bm25_rank", "rrf_rank", "prioritized_rank")
    )
    if not _has_allowed_body(target_rows, domains) and recalled and best_similarity >= FUZZY_THRESHOLD:
        return "G", "目标内容存在但被 is_body 判定为非正文，且已在召回/融合阶段受到 0.5 惩罚。"

    recall_ranks = [rank for rank in (case.get("vector_rank"), case.get("bm25_rank")) if isinstance(rank, int)]
    strong_stage = any(
        isinstance(rank, int) and rank <= 5
        for rank in (
            case.get("vector_rank"),
            case.get("bm25_rank"),
            case.get("rrf_rank"),
            case.get("prioritized_rank"),
        )
    )
    if strong_stage and not (isinstance(case.get("hybrid_rank"), int) and case["hybrid_rank"] <= 5):
        return "F", "目标在向量/BM25/RRF/重排中曾进入前5，但最终融合排序跌出 Top-5。"

    if recall_ranks:
        return "E", f"目标已进入召回候选，但向量/BM25最佳排名为 {min(recall_ranks)}，仍早于最终排序落点。"
    return "D", "目标存在、domain/正文/可引用状态正常，但未进入向量或 BM25 Top-300，查询表征与目标表达不匹配。"
def _run_case(
    question_row: dict[str, Any],
    eval_row: dict[str, Any],
    evidence_item: dict[str, Any],
    kb_rows: list[dict[str, Any]],
    config: dict[str, Any],
    kb_indexes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    question = str(question_row.get("question") or "").strip()
    source_file = str(question_row.get("source_file") or "").strip()
    evidence_location = str(question_row.get("evidence_location") or "").strip()
    evidence_items = evidence_item.get("evidence") if isinstance(evidence_item, dict) else None
    evidence_items = evidence_items if isinstance(evidence_items, list) else []
    if not evidence_items and evidence_location:
        evidence_items = [{
            "source_file": source_file,
            "evidence_location": evidence_location,
            "evidence_text": question_row.get("expected_answer") or "",
        }]

    intent = eval_row.get("intent") if isinstance(eval_row.get("intent"), dict) else {}
    route = eval_row.get("route") if isinstance(eval_row.get("route"), dict) else {}
    intent_name = str(intent.get("intent") or "")
    domains = _allowed_domains(route)
    plan = plan_query(question, intent_name)
    specific_query = str(plan.get("specific_query") or question)
    generic_query = str(plan.get("generic_query") or "").strip()

    target_info = _find_targets_fast(evidence_items, kb_rows, kb_indexes or _build_kb_indexes(kb_rows))
    target_rows = target_info["target_rows"]

    vector_results = retrieve(
        specific_query,
        top_k=CANDIDATE_K,
        db_path=config["vector_db"],
        domains=domains or None,
    )
    bm25_results = bm25_retrieve(
        specific_query,
        top_k=CANDIDATE_K,
        corpus_path=config["bm25_corpus"],
        index_path=config["bm25_index"],
        domains=domains or None,
    )
    vector_rank, vector_item = _rank(vector_results, target_rows)
    bm25_rank, bm25_item = _rank(bm25_results, target_rows)
    if domains:
        vector_unfiltered = retrieve(
            specific_query,
            top_k=CANDIDATE_K,
            db_path=config["vector_db"],
            domains=None,
        )
        bm25_unfiltered = bm25_retrieve(
            specific_query,
            top_k=CANDIDATE_K,
            corpus_path=config["bm25_corpus"],
            index_path=config["bm25_index"],
            domains=None,
        )
    else:
        vector_unfiltered = vector_results
        bm25_unfiltered = bm25_results
    vector_unfiltered_rank, vector_unfiltered_item = _rank(vector_unfiltered, target_rows)
    bm25_unfiltered_rank, bm25_unfiltered_item = _rank(bm25_unfiltered, target_rows)

    fused = rrf_fusion(vector_results, bm25_results, k=60, top_k=CANDIDATE_K)
    rrf_rank, rrf_item = _rank(fused, target_rows)
    prioritized = prioritize_results(fused, question=specific_query, top_k=CANDIDATE_K)
    prioritized_rank, prioritized_item = _rank(prioritized, target_rows)

    hybrid_rank = None
    hybrid_item = None
    top5 = [item for item in (eval_row.get("top5") or [])[:5] if isinstance(item, dict)]
    cut_score = None
    target_score = _score(prioritized_item)
    score_gap = None

    primary = _primary_target_row(target_rows, domains)
    allowed_targets = [row for row in target_rows if _domain_allowed([row], domains)]
    trace = {
        "id": question_row.get("id"),
        "module": question_row.get("module"),
        "question": question,
        "source_file": source_file,
        "expected_clauses": sorted(_clauses(evidence_location)),
        "evidence_location": evidence_location,
        "evidence_texts": [str(item.get("evidence_text") or "") for item in evidence_items],
        "intent": intent,
        "route": route,
        "route_domains": domains,
        "query_plan": plan,
        "specific_query": specific_query,
        "generic_query": generic_query,
        "source_hit_saved_evaluation": eval_row.get("source_hit"),
        "saved_top5": [
            {
                "source": item.get("source"),
                "doc_id": item.get("doc_id"),
                "clause": item.get("clause"),
                "title": item.get("title"),
            }
            for item in (eval_row.get("top5") or [])[:5]
            if isinstance(item, dict)
        ],
        **target_info,
        "target_domain": _row_domain(primary) if primary else "",
        "target_domains": sorted({_row_domain(row) for row in target_rows if _row_domain(row)}),
        "target_is_body": bool(primary and _row_is_body(primary)),
        "target_citation_eligible": bool(primary and _row_citation_eligible(primary)),
        "allowed_target_count": len(allowed_targets),
        "best_similarity": _best_target_similarity(target_rows, evidence_items),
        "best_query_overlap": max((query_overlap(row, question) for row in target_rows), default=0),
        "vector_rank": vector_rank,
        "vector_score": _score(vector_item) if vector_item else None,
        "bm25_rank": bm25_rank,
        "bm25_score": _score(bm25_item) if bm25_item else None,
        "vector_unfiltered_rank": vector_unfiltered_rank,
        "vector_unfiltered_score": _score(vector_unfiltered_item) if vector_unfiltered_item else None,
        "bm25_unfiltered_rank": bm25_unfiltered_rank,
        "bm25_unfiltered_score": _score(bm25_unfiltered_item) if bm25_unfiltered_item else None,
        "rrf_rank": rrf_rank,
        "rrf_score": _score(rrf_item) if rrf_item else None,
        "prioritized_rank": prioritized_rank,
        "prioritized_score": _score(prioritized_item) if prioritized_item else None,
        "hybrid_rank": hybrid_rank,
        "hybrid_score": target_score,
        "top5_cutoff_score": cut_score,
        "score_gap": score_gap,
        "top5_targets": [
            {
                "rank": index,
                "doc_id": item.get("doc_id"),
                "clause": item.get("clause"),
                "title": item.get("title"),
                "score": _score(item),
            }
            for index, item in enumerate(top5, start=1)
        ],
    }
    category, reason = _classify(trace)
    trace["category"] = category
    trace["category_name"] = CATEGORY_NAMES[category]
    trace["reason"] = reason
    return trace
def _format_number(value: Any) -> str:
    if value is None or value == "":
        return "-"
    if isinstance(value, float):
        return f"{value:.6f}".rstrip("0").rstrip(".")
    return str(value)


def _markdown_text(value: Any, limit: int = 0) -> str:
    text = " ".join(("" if value is None else str(value)).replace("|", "\\|").split())
    if limit and len(text) > limit:
        return text[:limit - 1] + "…"
    return text


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_markdown_text(value) for value in row) + " |")
    return "\n".join(lines)


def _suggestions(counts: Counter[str], examples: dict[str, list[str]]) -> list[str]:
    actions = {
        "A": "补齐缺失规程/案例原文：按明细中的来源与条号优先入库；仅入库与 evidence_text 对应的正文，不把参考答案直接入库。",
        "B": "优先修正 domain 元数据与路由映射：重点核对 generator_electrical、boiler、turbine 等标签；本批 B 类还伴随 54/54 citation_eligible=false，应同步复核元数据，但域过滤是当前 Top-5 未命中的直接阻断项。",
        "C": "改进切块策略：对标题块与正文块建立父子关系，按条号合并“现象/原因/处理”连续段落，避免 evidence_text 跨块后无完整命中。",
        "D": "增强查询改写与术语映射：把题目现象词、检修词、规程序号词映射到知识库表达；对多来源题增加条号/设备名约束。",
        "E": "调整召回与 RRF 排序：提高目标条文所在来源/条号的权重，降低长文档泛化标题的占位影响，并扩大候选后做轻量重排。",
        "F": "复核评分一致性：检查 vector、BM25、RRF、body/overlap 分数是否经过同尺度归一化，避免单路强命中在后段被覆盖。",
        "G": "复核正文降权与重排条件：优先检查 is_body 和 prioritize_results 的 0.5 惩罚；citation_eligible/scope 作为引用元数据单独复核，不混入 Top-5 召回主因。",
    }
    ordered = sorted(counts, key=lambda key: (-counts[key], CATEGORY_ORDER.index(key)))
    result = []
    for index, category in enumerate(ordered, start=1):
        if counts[category] <= 0:
            continue
        ids = "、".join(examples.get(category, []))
        result.append(
            f"{index}. **{category}类（{CATEGORY_NAMES[category]}，{counts[category]}题）**：{actions[category]}"
            + (f" 影响题目：{ids}。" if ids else "")
        )
    return result
def _write_report(traces: list[dict[str, Any]], report_path: Path) -> None:
    counts = Counter(trace["category"] for trace in traces)
    examples: dict[str, list[str]] = defaultdict(list)
    for trace in traces:
        examples[trace["category"]].append(str(trace["id"]))
    total = len(traces)
    lines = [
        "# 未命中题系统诊断",
        "",
        "> 诊断日期：2026-10-04",
        "> 数据口径：138 题评测集；116 题有 `source_file`；当前 Top-5 来源命中 56/116；未命中 60 题。",
        "> 证据：`evaluation_dataset_final.json` 的 `evidence_text`、`knowledge/plant_kb/data/knowledge.jsonl`、`138题评测明细_20261004.jsonl` 的 Top-5。",
        "",
        "## 0. 口径与复核说明",
        "",
        "- 本报告只诊断当前评测明细中 `source_file` 非空且 `source_hit=false` 的 60 题，不把无来源标注题混入命中率。",
        "- 之前诊断的 FULL-005/033/082/129 在当前明细中已为 `source_hit=true`，因此与本次 60 题未命中集合不重叠；它们的旧诊断记录仍保留在 `docs/Top5排序诊断_4题.md`。",
        "- 对每题按原始 `evidence_text` 在 15,188 条知识库记录中做精确包含、来源+条号、章节/页码/行号和字符 n-gram 模糊匹配；目标排名分别取向量、BM25、RRF 和正文重排。最终是否命中使用保存评测的 Top-5。",
        "- 每题只给一个主因，按以下优先级判定：A → B → C → G → F → E → D。原因是先判断是否入库，再判断是否被域/正文/引用条件影响，最后才判断查询和排序问题。",
        "",
        "### 分类定义",
        "",
        _table(
            ["类别", "定义", "判定证据"],
            [
                ["A 不在库", "目标条文未进入知识库或 evidence_text 无足够接近内容", "无来源+条号、无模糊命中；记录精确/模糊匹配数和搜索范围"],
                ["B domain错误", "目标存在，但 domain 与路由允许域不一致", "目标 domain 不在 route.domains，且域过滤后不可见"],
                ["C 切碎", "来源/条号存在，但证据被标题、短块或跨块切断", "来源+条号存在但最高相似度<0.72，且只有片段"],
                ["D 查询不匹配", "目标存在且元数据正常，但未被向量/BM25 Top-300 召回", "两路排名均为“未返回”"],
                ["E 排名靠后", "目标已进入召回，但排名>5", "向量/BM25至少一路返回，最佳排名>5"],
                ["F 评分不一致", "某一路或 RRF/重排曾进前5，最终融合跌出 Top-5", "前段排名<=5，最终排名>5或未返回"],
                ["G 被过滤", "正文降权或重排阶段造成目标丢失", "is_body=false 且已召回并受 0.5 惩罚，或进入 RRF 后跌出重排；citation_eligible=false 仅登记为元数据风险"],
            ],
        ),
        "",
        "## 1. 分类汇总",
        "",
        _table(
            ["类别", "数量", "占未命中题比例", "题目"],
            [
                [
                    f"{key}类（{CATEGORY_NAMES[key]}）",
                    counts.get(key, 0),
                    f"{counts.get(key, 0) / total * 100:.2f}%" if total else "0.00%",
                    "、".join(examples.get(key, [])) or "无",
                ]
                for key in CATEGORY_ORDER
            ],
        ),
        "",
        f"合计：**{total}题**；分类计数之和等于未命中题数。",
        "",
        "## 2. 分类明细",
        "",
    ]
    for category in CATEGORY_ORDER:
        group = [trace for trace in traces if trace["category"] == category]
        lines += [f"### {category}类：{CATEGORY_NAMES[category]}（{len(group)}题）", ""]
        if not group:
            lines += ["本类无题目。", ""]
            continue
        if category == "B":
            pair_counts = Counter(
                (
                    "/".join(trace.get("target_domains") or [trace.get("target_domain") or "-"]),
                    "+".join(trace.get("route_domains") or []),
                )
                for trace in group
            )
            exact_count = sum(1 for trace in group if trace.get("exact_match_count", 0) > 0)
            body_count = sum(1 for trace in group if trace.get("target_is_body"))
            ineligible_count = sum(1 for trace in group if not trace.get("target_citation_eligible"))
            vector_recalled = sum(1 for trace in group if isinstance(trace.get("vector_unfiltered_rank"), int))
            bm25_recalled = sum(1 for trace in group if isinstance(trace.get("bm25_unfiltered_rank"), int))
            lines += [
                "B 类覆盖检查：",
                "",
                f"- evidence_text 精确命中：`{exact_count}/{len(group)}`。",
                f"- 目标 is_body=true：`{body_count}/{len(group)}`；citation_eligible=false：`{ineligible_count}/{len(group)}`。",
                f"- 去掉 domain 过滤后进入 Top-300：向量 `{vector_recalled}/{len(group)}`，BM25 `{bm25_recalled}/{len(group)}`；说明过滤本身直接排除了这些目标。",
                "",
                _table(
                    ["目标 domain", "路由 domain", "题数", "题目"],
                    [
                        [
                            pair[0],
                            pair[1],
                            count,
                            "、".join(str(trace["id"]) for trace in group if "/".join(trace.get("target_domains") or [trace.get("target_domain") or "-"]) == pair[0] and "+".join(trace.get("route_domains") or []) == pair[1]),
                        ]
                        for pair, count in sorted(pair_counts.items(), key=lambda item: (-item[1], item[0]))
                    ],
                ),
                "",
            ]
        lines += [
            _table(
                ["题号", "模块", "问题", "期望来源", "期望条号", "存在性", "domain", "is_body", "citation_eligible", "向量排名", "BM25排名", "最终排名", "主因"],
                [
                    [
                        trace["id"],
                        trace["module"],
                        trace["question"],
                        trace["source_file"],
                        " / ".join(trace["expected_clauses"]) or "-",
                        "存在" if trace["target_found"] else "未形成完整命中",
                        trace["target_domain"] or "-",
                        trace["target_is_body"],
                        trace["target_citation_eligible"],
                        _rank_label(trace["vector_rank"]),
                        _rank_label(trace["bm25_rank"]),
                        ">5" if trace.get("source_hit_saved_evaluation") is False else _rank_label(trace["hybrid_rank"]),
                        trace["reason"],
                    ]
                    for trace in group
                ],
            ),
            "",
        ]
        for trace in group:
            primary = _primary_target_row(trace["target_rows"], trace["route_domains"])
            lines += [
                f"#### {trace['id']}：{_markdown_text(trace['question'])}",
                "",
                f"- 模块：`{trace['module']}`",
                f"- 期望来源：`{trace['source_file']}`",
                f"- 期望条号：`{' / '.join(trace['expected_clauses']) or '-'}`；位置：`{_markdown_text(trace['evidence_location'])}`",
                f"- 目标存在性：`{'是' if trace['target_found'] else '否'}`；来源匹配记录 `{trace['source_match_count']}`；条号匹配 `{trace['clause_match_count']}`；精确匹配 `{trace['exact_match_count']}`；最高 evidence_text 相似度 `{_format_number(trace['best_similarity'])}`",
                f"- 目标状态：domain=`{trace['target_domain'] or '-'}`；scope=`{(primary or {}).get('scope', '-')}`；is_body=`{trace['target_is_body']}`；citation_eligible=`{trace['target_citation_eligible']}`",
                f"- 排名：向量=`{_rank_label(trace['vector_rank'])}`；BM25=`{_rank_label(trace['bm25_rank'])}`；无域过滤向量=`{_rank_label(trace.get('vector_unfiltered_rank'))}`；无域过滤BM25=`{_rank_label(trace.get('bm25_unfiltered_rank'))}`；RRF=`{_rank_label(trace['rrf_rank'])}`；正文重排=`{_rank_label(trace['prioritized_rank'])}`；保存评测最终排名=`{">5" if trace.get('source_hit_saved_evaluation') is False else _rank_label(trace['hybrid_rank'])}`.",
                f"- 分数：目标最终=`{_format_number(trace['hybrid_score'])}`；Top-5 分界=`{_format_number(trace['top5_cutoff_score'])}`；分差=`{_format_number(trace['score_gap'])}`；问题与目标文本重叠=`{trace['best_query_overlap']}`",
                f"- 判因：{trace['reason']}",
                f"- 证据：原始 evidence_text 已用于模糊匹配；保存评测中的 Top-5 来源为 `{[item.get('doc_id') for item in trace['saved_top5']]}`。",
                "",
            ]
    lines += [
        "## 3. 修复建议（按影响面排序）",
        "",
        *_suggestions(counts, examples),
        "",
        "### 执行顺序建议",
        "",
        f"1. 优先修复 B 类 domain 错配（{counts.get('B', 0)}题）；无域过滤回放显示 BM25 可将 {sum(1 for trace in traces if trace['category'] == 'B' and isinstance(trace.get('bm25_unfiltered_rank'), int))}/{counts.get('B', 0)} 个目标拉入 Top-300。",
        f"2. 随后处理 E 类排名靠后（{counts.get('E', 0)}题），重点观察 RRF 与正文重排是否继续压后。",
        f"3. 最后处理 D 类查询不匹配（{counts.get('D', 0)}题），验证现象词到规程术语的改写；本轮 A/C/F/G 均为 0 题，不需要先做对应改动。",
        "",
        "## 4. 可复现命令",
        "",
        "```powershell",
        "& .\\venv\\Scripts\\python.exe scripts\\diagnose_all_misses.py",
        "```",
        "",
        "说明：当前终端若因 venv 启动器路径乱码无法直接启动，可改为使用本机 Python 并设置 `PYTHONPATH` 指向 `venv\\Lib\\site-packages`，不影响诊断逻辑。",
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="诊断 138 题中所有 Top-5 未命中题")
    parser.add_argument("--questions", default=str(DEFAULT_QUESTIONS))
    parser.add_argument("--details", default=str(DEFAULT_DETAILS))
    parser.add_argument("--evidence", default=str(DEFAULT_EVIDENCE))
    parser.add_argument("--kb", default=str(DEFAULT_KB))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--limit", type=int, default=0, help="only process the first N misses (for smoke testing)")
    parser.add_argument("--ids", default="", help="comma-separated case ids to diagnose (for targeted checks)")
    args = parser.parse_args(argv)

    question_rows = _load_jsonl(Path(args.questions))
    evaluation_rows = _load_jsonl(Path(args.details))
    evidence_rows = _load_json(Path(args.evidence))
    kb_rows = _load_jsonl(Path(args.kb))
    evidence_by_id = {
        str(item.get("id")): item
        for item in evidence_rows
        if isinstance(item, dict) and item.get("id") is not None
    }
    evaluation_by_id = {
        str(item.get("id")): item
        for item in evaluation_rows
        if isinstance(item, dict) and item.get("id") is not None
    }
    questions_by_id = {
        str(item.get("id")): item
        for item in question_rows
        if isinstance(item, dict) and item.get("id") is not None
    }
    miss_ids = [
        str(row.get("id"))
        for row in evaluation_rows
        if row.get("source_file") and not row.get("source_hit")
    ]
    config = _resolve_config(_backend_name())
    kb_indexes = _build_kb_indexes(kb_rows)

    selected_ids = miss_ids
    if args.ids:
        wanted = {item.strip() for item in args.ids.split(",") if item.strip()}
        selected_ids = [item for item in selected_ids if item in wanted]
    if args.limit and args.limit > 0:
        selected_ids = selected_ids[: args.limit]
    traces: list[dict[str, Any]] = []
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as stream:
        for index, case_id in enumerate(selected_ids, start=1):
            question_row = questions_by_id.get(case_id)
            eval_row = evaluation_by_id.get(case_id)
            evidence_row = evidence_by_id.get(str((question_row or {}).get("source_question_id")))
            if not question_row or not eval_row or not evidence_row:
                print(f"[{index}/{len(selected_ids)}] skip {case_id}: missing source data", flush=True)
                continue
            trace = _run_case(question_row, eval_row, evidence_row, kb_rows, config, kb_indexes)
            traces.append(trace)
            stream.write(json.dumps(trace, ensure_ascii=False) + "\n")
            stream.flush()
            print(
                f"[{index}/{len(selected_ids)}] {case_id} {trace['category']} "
                f"vector={_rank_label(trace['vector_rank'])} bm25={_rank_label(trace['bm25_rank'])} "
                f"hybrid={_rank_label(trace['hybrid_rank'])}",
                flush=True,
            )

    _write_report(traces, Path(args.report))
    print(f"report={args.report}")
    print(f"details={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())