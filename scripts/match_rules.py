# -*- coding: utf-8 -*-
"""规则匹配原型（任务二·排因骨架版，先用关键词，不依赖向量/LLM）。

读取 data/知识库/rules_DLT572_ch7.json（字段：rule_id/source/trigger/content/actions/decision），
把用户现象与规则文本做关键词打分，返回最相关的规则与处置动作。

用法：
    python scripts/match_rules.py                                  # 跑内置示例
    python scripts/match_rules.py "变压器油温过高怎么办？" "气体继电器动作"
"""
import json
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KB = ROOT / "data" / "知识库" / "rules_DLT572_ch7.json"

# 同义词组：命中任一即扩展为整组，提高召回
SYNONYMS = {
    "油温": ["油温", "温度"],
    "温度": ["温度", "油温"],
    "瓦斯": ["气体继电器", "瓦斯"],
    "跳闸": ["跳闸", "停运"],
    "着火": ["着火", "灭火", "火势", "冒烟"],
    "铁芯": ["铁芯", "接地电流"],
    "套管": ["套管"],
    "油位": ["油位", "油面"],
    "漏油": ["漏油", "喷油"],
    "分接开关": ["分接开关", "有载"],
    "冷却": ["冷却", "风扇", "油泵"],
    "压力释放阀": ["压力释放阀", "释压"],
    "短路": ["短路"],
    "过载": ["过载", "超额定电流", "负载"],
}

def load_rules():
    data = json.loads(KB.read_text(encoding="utf-8-sig"))
    return data["rules"]

def expand_tokens(query: str) -> list:
    tokens = []
    for group in SYNONYMS.values():
        if any(alias in query for alias in group):
            tokens.extend(group)
    # 查询里的连续中文/字母数字片段也作为关键词
    buf = ""
    for ch in query:
        if ch.isalnum() or "\u4e00" <= ch <= "\u9fff":
            buf += ch
        else:
            if len(buf) >= 2:
                tokens.append(buf)
            buf = ""
    if len(buf) >= 2:
        tokens.append(buf)
    return sorted(set(tokens), key=len, reverse=True)

def score_rule(rule, tokens) -> int:
    text = " ".join(str(rule.get(k, "")) for k in ("trigger", "content", "title", "rule_id"))
    return sum(text.count(tok) for tok in tokens)

def match(query, rules, top_n=3):
    tokens = expand_tokens(query)
    scored = []
    for rule in rules:
        s = score_rule(rule, tokens)
        if s > 0:
            scored.append((s, rule))
    scored.sort(key=lambda x: x[0], reverse=True)
    return tokens, [r for _, r in scored[:top_n]]

def show(query, rules):
    tokens, hits = match(query, rules)
    print(f"\n问题: {query}")
    print(f"关键词: {'/'.join(tokens) if tokens else '(无)'}")
    if not hits:
        print("  未命中规则 —— 真实系统中应触发『知识库未覆盖，拒答/转人工』")
        return
    for r in hits:
        print(f"  [{r['rule_id']}] {r.get('trigger', '')}")
        print(f"       依据: {r.get('source', '')}")
        acts = r.get("actions") or []
        if acts:
            print("       处置: " + "；".join(acts))
        for d in (r.get("decision") or []):
            print(f"       判定: {d.get('if')} → {d.get('then')}")

def main():
    rules = load_rules()
    queries = sys.argv[1:] or [
        "变压器油温过高怎么办？",
        "气体继电器动作如何处理？",
        "铁芯多点接地，接地电流较大",
        "变压器着火怎么办？",
        "今天天气不错",
    ]
    for q in queries:
        show(q, rules)

if __name__ == "__main__":
    main()