#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""规则驱动的查询规划器：识别部件、故障模式和两路检索查询。"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from vector_kb.query_expander import expand_query

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
RULES_DIR = PROJECT_ROOT / "data" / "rules"
DEVICE_FAILURE_MODE_MAP = RULES_DIR / "device_failure_mode_map.json"
FAILURE_MODE_RULES = RULES_DIR / "failure_mode_rules.json"
TERM_MAPPING = RULES_DIR / "term_mapping.json"
LOGGER = logging.getLogger(__name__)

COMPONENT_MARKERS = (
    "阀",
    "门",
    "泵",
    "风机",
    "磨煤机",
    "轴承",
    "轴瓦",
    "加热器",
    "传感器",
    "变送器",
    "DCS",
    "转子",
    "汽轮机",
    "锅炉",
    "发电机",
    "过热器",
    "再热器",
    "水冷壁",
    "空预器",
    "省煤器",
    "管",
    "测点",
    "元件",
)


@lru_cache(maxsize=16)
def _load_json(path_string: str) -> dict[str, Any] | None:
    path = Path(path_string)
    try:
        with path.open("r", encoding="utf-8-sig") as stream:
            data = json.load(stream)
    except FileNotFoundError:
        LOGGER.warning("Query planner rule file not found: %s", path)
        return None
    except Exception as exc:
        LOGGER.warning("Failed to load query planner rule file %s: %s", path, exc)
        return None
    if not isinstance(data, dict):
        LOGGER.warning("Invalid query planner rule file: %s", path)
        return None
    return data


def _load_device_mapping() -> dict[str, Any] | None:
    return _load_json(str(DEVICE_FAILURE_MODE_MAP))


def _load_failure_modes() -> dict[str, Any] | None:
    return _load_json(str(FAILURE_MODE_RULES))


def _load_term_mapping() -> dict[str, Any] | None:
    return _load_json(str(TERM_MAPPING))


def _degenerate_plan(question: str, intent: str) -> dict[str, Any]:
    return {
        "original_query": question,
        "intent": intent,
        "components": [],
        "fault_modes": [],
        "specific_query": question,
        "generic_query": "",
        "source": "none",
    }


def _looks_like_component(term: Any) -> bool:
    value = str(term or "").strip()
    return bool(value) and any(marker in value for marker in COMPONENT_MARKERS)


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for raw in values:
        value = str(raw or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _matched_device_entries(question: str, mappings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matched: list[dict[str, Any]] = []
    for entry in mappings:
        if not isinstance(entry, dict):
            continue
        patterns = [str(item).strip() for item in (entry.get("device_patterns") or []) if str(item).strip()]
        if any(pattern in question for pattern in patterns):
            matched.append(entry)
    return matched


def _collect_components(
    question: str,
    matched_entries: list[dict[str, Any]],
    terms: list[dict[str, Any]],
    modes: dict[str, dict[str, Any]],
    fault_modes: list[str],
) -> tuple[list[str], set[str]]:
    candidates: dict[str, str] = {}
    component_order: list[str] = []

    def add_candidate(term: str, component_code: str | None) -> None:
        value = str(term or "").strip()
        if not _looks_like_component(value) or value not in question:
            return
        key = str(component_code or value)
        if key not in candidates or len(value) < len(candidates[key]):
            candidates[key] = value
        if key not in component_order:
            component_order.append(key)

    for entry in matched_entries:
        code = str(entry.get("component") or "").strip() or None
        for pattern in entry.get("device_patterns") or []:
            add_candidate(str(pattern), code)

    matched_component_codes = {
        str(entry.get("component") or "").strip()
        for entry in matched_entries
        if str(entry.get("component") or "").strip()
    }
    for item in terms:
        if not isinstance(item, dict):
            continue
        component_code = str(item.get("target_component") or "").strip() or None
        if matched_component_codes and component_code not in matched_component_codes:
            continue
        add_candidate(str(item.get("term") or ""), component_code)

    if not matched_component_codes:
        for mode_id in fault_modes:
            config = modes.get(mode_id) or {}
            for applied in config.get("applies_to") or []:
                value = str(applied or "").strip()
                if _looks_like_component(value) and value not in candidates:
                    candidates[value] = value
                    component_order.append(value)

    components = [candidates[key] for key in component_order if key in candidates]
    return components, matched_component_codes


def plan_query(question: str, intent: str) -> dict[str, Any]:
    """生成部件/故障模式识别结果和 specific/generic 两路查询。"""
    original = str(question or "").strip()
    normalized_intent = str(intent or "").strip()
    if not original:
        return _degenerate_plan("", normalized_intent)

    device_rule = _load_device_mapping()
    failure_rule = _load_failure_modes()
    term_rule = _load_term_mapping()
    if not isinstance(device_rule, dict) or not isinstance(failure_rule, dict) or not isinstance(term_rule, dict):
        return _degenerate_plan(original, normalized_intent)

    mappings = [
        entry for entry in (device_rule.get("mappings") or [])
        if isinstance(entry, dict)
    ]
    modes = {
        str(mode_id): config
        for mode_id, config in (failure_rule.get("modes") or {}).items()
        if isinstance(config, dict)
    }
    terms = [
        item for item in (term_rule.get("terms") or [])
        if isinstance(item, dict)
    ]

    matched_entries = _matched_device_entries(original, mappings)
    fault_modes: list[str] = []
    for entry in matched_entries:
        fault_modes.extend(str(item) for item in (entry.get("fault_modes") or []))
    for mode_id, config in modes.items():
        if any(str(keyword) in original for keyword in (config.get("keywords") or [])):
            fault_modes.append(mode_id)
    fault_modes = _dedupe(fault_modes)

    components, matched_component_codes = _collect_components(
        original,
        matched_entries,
        terms,
        modes,
        fault_modes,
    )

    try:
        expanded = expand_query(original, normalized_intent)
        specific_query = str(expanded.get("expanded_query") or original)
    except Exception:
        LOGGER.warning("Query expansion failed in query planner", exc_info=True)
        specific_query = original

    generic_terms: list[str] = []
    if fault_modes:
        for mode_id in fault_modes:
            generic_terms.extend(str(item) for item in ((modes.get(mode_id) or {}).get("keywords") or []))
        for entry in matched_entries:
            generic_terms.extend(str(item) for item in (entry.get("query_terms") or []))
        for item in terms:
            if str(item.get("target_component") or "").strip() in matched_component_codes:
                if str(item.get("target_scope") or "") == "component_generic":
                    generic_terms.append(str(item.get("term") or ""))

    deduped_generic = _dedupe(generic_terms)
    filtered_generic = [term for term in deduped_generic if term not in original]
    generic_query = " ".join((filtered_generic or deduped_generic)[:40])

    return {
        "original_query": original,
        "intent": normalized_intent,
        "components": components,
        "fault_modes": fault_modes,
        "specific_query": specific_query,
        "generic_query": generic_query,
        "source": "rule",
    }


__all__ = ["plan_query"]