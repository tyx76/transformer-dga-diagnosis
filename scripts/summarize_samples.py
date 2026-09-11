# -*- coding: utf-8 -*-
"""汇总 data/样本/ 下的数据集：行数、列、标签分布（支持 csv 与 xlsx）。"""
import csv, sys
from pathlib import Path
from collections import Counter

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

root = Path(__file__).resolve().parent.parent / "data" / "样本"

def report(name, header, data):
    print(f"\n== {name} ==")
    print(f"  行数={len(data)}  列数={len(header)}")
    print("  表头:", [str(h) for h in header[:15]])
    for i, h in enumerate(header):
        hl = str(h).lower()
        if any(k in hl for k in ("fault", "label", "class", "type", "故障", "类型", "编码", "气体", "状态")):
            c = Counter(r[i] for r in data if i < len(r))
            print(f"  标签列「{h}」 Top:", dict(c.most_common(10)))

found = False
for p in sorted(root.rglob("*.csv")):
    found = True
    with p.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        rows = list(csv.reader(f))
    if rows:
        report(p.relative_to(root), rows[0], rows[1:])

for p in sorted(root.rglob("*.xlsx")):
    found = True
    try:
        import openpyxl
    except ImportError:
        print("\n(未安装 openpyxl，跳过 xlsx)"); break
    wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            continue
        report(f"{p.relative_to(root)} [sheet: {ws.title}]", list(rows[0]), rows[1:])
    wb.close()

if not found:
    print("未发现样本文件")