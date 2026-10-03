#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rule-based query expansion for BM25 retrieval."""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
RULES_DEFAULT = PROJECT_ROOT / "data" / "rules" / "synonym_rules.json"
MAX_EXPANDED_TERMS = 5
LOGGER = logging.getLogger(__name__)

_INTENT_ALIASES = {
    "generator_electrical": "generator",
}


@lru_cache(maxsize=1)
def _load_rules() -> dict | None:
    """Load and validate the synonym rule table once."""
    try:
        with RULES_DEFAULT.open("r", encoding="utf-8-sig") as stream:
            data = json.load(stream)
    except FileNotFoundError:
        LOGGER.warning("Synonym rules not found: %s", RULES_DEFAULT)
        return None
    except Exception as exc:
        LOGGER.warning("Failed to load synonym rules %s: %s", RULES_DEFAULT, exc)
        return None

    rules = data.get("rules") if isinstance(data, dict) else None
    if not isinstance(rules, dict):
        LOGGER.warning("Invalid synonym rules format: missing 'rules'")
        return None
    for domain, mapping in rules.items():
        if not isinstance(mapping, dict):
            LOGGER.warning("Invalid synonym rule domain: %s", domain)
            return None
        for source, expansions in mapping.items():
            if not isinstance(source, str) or not isinstance(expansions, list):
                LOGGER.warning("Invalid synonym rule entry: %s.%s", domain, source)
                return None
    return rules


def _empty_result(question: str) -> dict:
    return {
        "original_query": question,
        "expanded_query": question,
        "expanded_terms": [],
        "matched_rules": [],
        "source": "none",
    }


def expand_query(question: str, intent: str) -> dict:
    """Expand a query with synonyms from the rule table for one intent domain."""
    original = str(question or "")
    result = _empty_result(original)
    if not original.strip():
        return result

    rules = _load_rules()
    if not rules:
        return result

    domain = _INTENT_ALIASES.get(str(intent or "").strip().lower(), str(intent or "").strip().lower())
    mapping = rules.get(domain)
    if not isinstance(mapping, dict):
        return result

    expanded_terms: list[str] = []
    matched_rules: list[str] = []
    seen: set[str] = set()

    for source, expansions in mapping.items():
        if source not in original:
            continue
        matched_rules.append(source)
        for expansion in expansions:
            term = str(expansion).strip()
            if not term or term in seen:
                continue
            seen.add(term)
            if len(expanded_terms) >= MAX_EXPANDED_TERMS:
                break
            expanded_terms.append(term)
        if len(expanded_terms) >= MAX_EXPANDED_TERMS:
            break

    if not expanded_terms:
        result["matched_rules"] = matched_rules
        return result

    expanded_query = original
    if expanded_terms:
        expanded_query = f"{original} {' '.join(expanded_terms)}"

    return {
        "original_query": original,
        "expanded_query": expanded_query,
        "expanded_terms": expanded_terms,
        "matched_rules": matched_rules,
        "source": "rule",
    }


__all__ = ["expand_query"]
