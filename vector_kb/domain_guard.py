#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""轻量领域过滤：在调用向量模型前排除明显无关的问题。"""

from __future__ import annotations

import re
import sys
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

# Use longer phrases rather than short characters.  This keeps ordinary
# technical compounds such as "历史数据", "吃水", and "可编程控制器" out of
# the irrelevant bucket while still blocking typical off-topic questions.
IRRELEVANT_KEYWORDS = {
    # Food / drink
    "吃什么", "晚饭吃什么", "中午吃什么", "点外卖", "叫外卖", "外卖推荐", "外卖平台",
    "吃啥", "想吃什么", "喝什么", "想喝", "喝奶茶", "喝饮料", "喝酒",
    "炒菜", "做菜", "做饭", "菜谱", "早餐吃什么", "早餐推荐", "午餐吃什么",
    "午餐推荐", "晚餐吃什么", "晚餐推荐",
    # Entertainment / media
    "打游戏", "玩游戏", "游戏推荐", "游戏攻略", "游戏怎么玩", "电子游戏",
    "网络游戏", "游戏机", "看电影", "推荐电影", "电影推荐", "电影票", "电影院",
    "唱歌", "写诗", "写一首诗", "古诗", "诗歌", "吟诗", "讲笑话", "说个笑话",
    "笑话推荐", "娱乐新闻", "娱乐八卦", "娱乐活动", "娱乐圈",
    # Daily-life / general knowledge
    "天气怎么样", "天气预报", "今天天气", "明天天气", "天气查询",
    "周末去哪", "周末做什么", "周末怎么过", "周末计划", "周末出去玩",
    "去旅游", "旅游攻略", "旅游推荐", "旅游景点",
    "去购物", "购物推荐", "购物网站", "网上购物",
    "买股票", "股票推荐", "股票行情", "股票怎么买",
    "学编程", "学习编程", "编程题", "编程语言",
    "数学题", "学英语", "英语题", "英语翻译", "英语怎么说",
    "聊历史", "讲历史", "历史上的今天", "历史故事", "历史题", "聊政治",
    "政治题", "政治新闻", "讨论政治", "谈恋爱", "恋爱问题", "恋爱建议",
    "打篮球", "看篮球", "篮球比赛", "踢足球", "看足球", "足球比赛",
}

# Backward-compatible alias.
OFF_TOPIC_TERMS = IRRELEVANT_KEYWORDS

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


def _debug_enabled() -> bool:
    return "--debug" in sys.argv[1:]


def _emit(decision: str, reason: str) -> None:
    if _debug_enabled():
        print(f"[领域守卫] {decision}，原因：{reason}", flush=True)


def is_in_domain(question: str, backend: str | None = None) -> bool:
    """只拦截明显无关问题；未知问题默认放行。"""
    normalized = _normalize(question)
    if not normalized:
        _emit("拦截", "空问题")
        return False

    device_terms = PURE_DOMAIN_TERMS if backend == "pure_kb" else GENERAL_DOMAIN_TERMS

    # 明确无关词优先，避免“变压器怎么炒菜”这类问题因设备词而误放行。
    matched_irrelevant = next(
        (term for term in IRRELEVANT_KEYWORDS if _contains_term(normalized, term)),
        None,
    )
    if matched_irrelevant:
        _emit("拦截", f"命中无关词：{matched_irrelevant}")
        return False

    matched_device = next(
        (term for term in device_terms if _contains_term(normalized, term)),
        None,
    )
    if matched_device:
        _emit("放行", f"命中设备词：{matched_device}")
        return True

    _emit("放行", "默认放行")
    return True


def domain_guard(question: str) -> bool:
    """Backward-compatible public entry point."""
    return is_in_domain(question)


__all__ = ["is_in_domain", "domain_guard", "IRRELEVANT_KEYWORDS"]
