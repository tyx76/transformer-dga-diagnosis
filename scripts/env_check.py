# -*- coding: utf-8 -*-
"""环境连通性 + 规则库读取测试（纯标准库）。
发现1：Windows 命令行传中文路径易乱码 -> 脚本内用相对路径/pathlib。
发现2：.NET WriteAllText(Encoding.UTF8) 会带 BOM -> 读取用 utf-8-sig。
"""
import json, sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
print("python:", sys.version.split()[0])
p = root / "data" / "知识库" / "rules_DLT572_ch7.json"
d = json.loads(p.read_text(encoding="utf-8-sig"))
rules = d["rules"]
print("rules loaded:", len(rules))
print("sample rules:", [r["rule_id"] for r in rules[:5]], "...")
ids = {r["rule_id"] for r in rules}
missing = [f"DLT572-7.{i}.{j}" for i in (1,2,3,4) for j in (1,2,3,4)] 
print("OK")
# 简单关键词匹配检索（先不用向量，不用LLM）
def match_rules(query, rules, top_n=3):
    """根据问题关键词，找出最匹配的规则（简化版）"""
    # 提取用户问题里的关键词
    keywords = ["油温", "绕组", "铁芯", "套管", "分接开关", "瓦斯", "绝缘"]
    matched = []
    for rule in rules:
        score = 0
        # 检查规则的description/rule_text里是否包含关键词
        text = rule.get("description", "") + rule.get("rule_text", "")
        for kw in keywords:
            if kw in query and kw in text:
                score += 1
        if score > 0:
            matched.append((score, rule))
    matched.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in matched[:top_n]]

# 测试
query = "变压器油温过高怎么办？"
matched_rules = match_rules(query, rules)
print(f"\n问题: {query}")
print(f"匹配到 {len(matched_rules)} 条相关规则：")
for r in matched_rules:
    print(f"  - {r['rule_id']}: {r.get('description', '')[:50]}...")