# -*- coding: utf-8 -*-
"""环境连通性 + 规则库读取测试（纯标准库）。
要点：脚本内用相对路径/pathlib（命令行传中文路径易乱码）；JSON 读取用 utf-8-sig（.NET 写入带 BOM）。
"""
import json, sys
try:
    sys.stdout.reconfigure(encoding='utf-8')  # 避免中文输出在 GBK 控制台乱码
except Exception:
    pass
from pathlib import Path

root = Path(__file__).resolve().parent.parent
print("python:", sys.version.split()[0])
p = root / "data" / "知识库" / "rules_DLT572_ch7.json"
d = json.loads(p.read_text(encoding="utf-8-sig"))
rules = d["rules"]
print("rules loaded:", len(rules))
print("sample rules:", [r["rule_id"] for r in rules[:5]], "...")
print("OK")