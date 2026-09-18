#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""意图到知识库领域的路由层。

本模块只负责把规则/LLM 的意图结果转换为显式 domains、filters 和检索模式，
不执行检索、生成或引用校验。
"""

from __future__ import annotations

import re
from typing import Any

from vector_kb.intent_classifier import classify_intent

INTENT_DOMAIN_MAP = {
    "dga_analysis": ("dga",),
    "oil_temp": ("oil_temp",),
    "safety_check": ("safety", "dp"),
    "equipment_spec": ("equipment", "dp"),
    "irrelevant": (),
}

DOC_DEFAULTS = {
    "722": "DL/T 722-2014",
    "572": "DL/T 572-2021",
}


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).upper()


def parse_query_slots(question: str) -> dict:
    """从问题中提取标准号、年份、条号和表号。"""
    text = _normalize_text(question)
    doc_number = year = doc_id = None
    match = re.search(r"DL/?T?(\d{3})(?:-(\d{4}))?", text, re.IGNORECASE)
    if match:
        doc_number = match.group(1)
        year = match.group(2)
        doc_id = f"DL/T {doc_number}-{year}" if year else DOC_DEFAULTS.get(doc_number)

    table_match = re.search(r"表(\d+)", text)
    table = table_match.group(1) if table_match else None
    clause_match = re.search(r"(?:第)?(\d+(?:\.\d+)+)(?:条)?", text)
    clause = clause_match.group(1) if clause_match else None
    if table and clause:
        clause = f"{clause}-表{table}"
    elif table and not clause:
        clause = f"表{table}"

    return {
        "doc_number": doc_number,
        "year": year,
        "doc_id": doc_id,
        "clause": clause,
        "table": table,
    }


def _domains_for_intents(intents: list[str]) -> list[str]:
    domains: list[str] = []
    for intent in intents:
        for domain in INTENT_DOMAIN_MAP.get(intent, ()):
            if domain not in domains:
                domains.append(domain)
    return domains


def route_intent(question: str, classification: dict | None = None) -> dict:
    """将意图分类结果转换为适配纯知识库的路由结果。"""
    result = dict(classification or classify_intent(question))
    intent = str(result.get("intent") or "irrelevant")
    intents = list(result.get("intents") or [intent])
    slots = parse_query_slots(question)

    filters = {}
    if slots.get("doc_id"):
        filters["doc_id"] = slots["doc_id"]
    if slots.get("clause"):
        filters["clause"] = slots["clause"]

    if intent == "irrelevant":
        mode = "refuse"
        domains = []
    elif filters.get("doc_id") and filters.get("clause") and len(intents) == 1:
        mode = "exact_lookup"
        domains = _domains_for_intents(intents)
    else:
        mode = "search"
        domains = _domains_for_intents(intents)

    return {
        "intent": intent,
        "intents": intents,
        "domains": domains,
        "filters": filters,
        "mode": mode,
        "slots": slots,
        "source": result.get("source", "rule"),
        "classification": result,
    }


__all__ = ["INTENT_DOMAIN_MAP", "DOC_DEFAULTS", "parse_query_slots", "route_intent"]