#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""轻量领域过滤：在调用向量模型前排除明显无关的问题。"""

from __future__ import annotations

import re
import unicodedata

PURE_DOMAIN_TERMS = (
    "变压器",
    "主变",
    "油浸式",
    "油中",
    "绝缘油",
    "油色谱",
    "溶解气体",
    "dga",
    "色谱",
    "气体",
    "变电站",
    "电抗器",
    "乙炔",
    "c2h2",
    "氢气",
    "h2",
    "甲烷",
    "ch4",
    "乙烯",
    "c2h4",
    "乙烷",
    "c2h6",
    "总烃",
    "一氧化碳",
    "co",
    "二氧化碳",
    "co2",
    "注意值",
    "产气速率",
    "三比值",
    "局部放电",
    "电弧放电",
    "火花放电",
    "过热",
    "故障",
    "异常",
    "超标",
    "巡检",
    "油",
)

GENERAL_DOMAIN_TERMS = PURE_DOMAIN_TERMS + (
    "锅炉",
    "水冷壁",
    "过热器",
    "再热器",
    "省煤器",
    "空预器",
    "磨煤机",
    "制粉",
    "燃烧器",
    "爆管",
    "结焦",
    "吹灰",
    "汽轮机",
    "通流",
    "级组",
    "转子",
    "轴承",
    "轴系",
    "振动",
    "轴封",
    "凝汽器",
    "deh",
    "调速",
    "旁路",
    "发电机",
    "定子",
    "励磁",
    "氢冷",
    "密封油",
    "绝缘",
    "局放",
    "盖振",
    "辅机",
    "风机",
    "给水泵",
    "循环水泵",
    "油系统",
    "冷却系统",
    "轴承温度",
)

OFF_TOPIC_TERMS = (
    "吃什么",
    "吃",
    "喝",
    "炒菜",
    "做菜",
    "做饭",
    "菜谱",
    "早餐",
    "午餐",
    "晚餐",
    "外卖",
    "天气",
    "电影",
    "股票",
    "旅游",
    "唱歌",
    "游戏",
    "笑话",
    "恋爱",
    "篮球",
    "足球",
)

_SUBSCRIPT_DIGITS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")


def _normalize(text: str) -> str:
    """统一全半角和下标，并移除空白。"""
    normalized = unicodedata.normalize("NFKC", str(text or ""))
    normalized = normalized.translate(_SUBSCRIPT_DIGITS).lower()
    return "".join(normalized.split())


def _contains_term(text: str, term: str) -> bool:
    """中文按子串匹配，英数术语按词边界匹配。"""
    if term.isascii():
        pattern = rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])"
        return re.search(pattern, text) is not None
    return term in text


def is_in_domain(question: str, backend: str | None = None) -> bool:
    """判断问题是否值得进入当前后端的检索与生成流程。"""
    normalized = _normalize(question)
    if not normalized:
        return False
    if any(_contains_term(normalized, term) for term in OFF_TOPIC_TERMS):
        return False
    terms = PURE_DOMAIN_TERMS if backend == "pure_kb" else GENERAL_DOMAIN_TERMS
    return any(_contains_term(normalized, term) for term in terms)


__all__ = ["is_in_domain"]
