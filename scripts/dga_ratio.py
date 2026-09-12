# -*- coding: utf-8 -*-
"""DL/T 722-2014 改良三比值法计算器 + 规则基线评测。

用法：
  python scripts/dga_ratio.py --h2 150 --ch4 96 --c2h6 446 --c2h4 84 --c2h2 0.87
  python scripts/dga_ratio.py --eval [--voltage 220|330]
评测口径（关键）：
  1) 三比值法只对“气体超注意值”的设备有效（DL/T 722-2014 10.2.4 a）；未触发的不纳入比值判据评测；
  2) 数据集标签与标准输出类别口径不同，比较时做归并（高能放电≈电弧放电；低温过热合并两档；低能放电含兼过热）。
规则来源：data/规则库/rules_DLT722_dga_draft.json v0.3（表6/表7，成员2人工核对）
"""
import argparse, csv, json, sys
from pathlib import Path

try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

ROOT = Path(__file__).resolve().parent.parent
KB = ROOT / "data" / "知识库" / "rules_DLT722_dga_draft.json"
SAMPLES = ROOT / "data" / "样本" / "dga_samples_uL_per_L.csv"
RATIOS = [("C2H2/C2H4", "c2h2", "c2h4"), ("CH4/H2", "ch4", "h2"), ("C2H4/C2H6", "c2h4", "c2h6")]

# 注意值（表3 变压器和电抗器）：H2/总烃 150；乙炔 330kV及以上=1、220kV及以下=5
ATTENTION = {"330": {"h2": 150, "c2h2": 1, "thc": 150}, "220": {"h2": 150, "c2h2": 5, "thc": 150}}
# 数据集标签 -> 标准输出类别的归并
LABEL_TO_GROUP = {"低温过热": "低温过热", "中温过热": "中温过热", "高温过热": "高温过热",
                  "局部放电": "局部放电", "低能放电": "低能放电", "高能放电": "电弧放电"}

def load_rules():
    d = json.loads(KB.read_text(encoding="utf-8-sig"))
    codes = {r["ratio"]: r["codes"] for r in d["ratio_coding"]["rows"]}
    return codes, d["fault_type_map"]["rows"]

def ratio_value(num, den):
    if den == 0: return (0.0 if num == 0 else float("inf")), True
    return num / den, False

def code_of(v, codes):
    if v < 0.1: i = 0
    elif v < 1: i = 1
    elif v < 3: i = 2
    else: i = 3
    return codes[i]

def parse_set(s): return {int(x) for x in str(s).replace("，", ",").split(",") if x.strip() != ""}

def lookup(a, b, c, rows):
    for r in rows:
        cd = r["codes"]
        if a in parse_set(cd["c2h2_c2h4"]) and b in parse_set(cd["ch4_h2"]) and c in parse_set(cd["c2h4_c2h6"]):
            return r["fault"], r.get("example", "")
    return None, ""

def judge(gases, codes, rows):
    vals = []
    for name, num, den in RATIOS:
        v, zero_den = ratio_value(float(gases[num]), float(gases[den]))
        vals.append((name, v, code_of(v, codes[name]), zero_den))
    a, b, c = (x[2] for x in vals)
    fault, example = lookup(a, b, c, rows)
    return vals, (a, b, c), fault, example

def group_of(fault):
    if fault is None: return None
    if fault.startswith("低温过热"): return "低温过热"
    if fault.startswith("中温过热"): return "中温过热"
    if fault.startswith("高温过热"): return "高温过热"
    if fault.startswith("局部放电"): return "局部放电"
    if fault.startswith("低能放电"): return "低能放电"
    if fault.startswith("电弧放电"): return "电弧放电"
    return fault

def triggered(g, volt):
    th = ATTENTION[volt]
    return (g["h2"] > th["h2"]) or (g["c2h2"] > th["c2h2"]) or ((g["ch4"]+g["c2h6"]+g["c2h4"]+g["c2h2"]) > th["thc"])

def main():
    ap = argparse.ArgumentParser()
    for k in ("h2","ch4","c2h6","c2h4","c2h2"): ap.add_argument("--"+k, type=float)
    ap.add_argument("--eval", action="store_true")
    ap.add_argument("--voltage", choices=["220","330"], default="220")
    args = ap.parse_args()
    codes, rows = load_rules()

    if args.eval:
        labeled = normal = not_triggered = unmapped = 0
        exact = merged = 0
        per = {}
        with SAMPLES.open(newline="", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                lab = r.get("label_std")
                if not lab: continue
                labeled += 1
                if lab == "正常": normal += 1; continue
                try: g = {k: float(r[k]) for k in ("h2","ch4","c2h6","c2h4","c2h2")}
                except (TypeError, ValueError): continue
                if not triggered(g, args.voltage): not_triggered += 1; continue
                _, _, fault, _ = judge(g, codes, rows)
                if fault is None: unmapped += 1; continue
                exact += (fault == lab)
                ok = (group_of(fault) == LABEL_TO_GROUP.get(lab))
                merged += ok
                d = per.setdefault(lab, [0,0]); d[0]+=1; d[1]+=ok
        ev = exact + 0  # 计算总数
        total_ev = sum(v[0] for v in per.values())
        print(f"评测口径：电压 {args.voltage}kV 注意值触发 + 类别归并")
        print(f"带标签样本 {labeled}｜其中‘正常’ {normal}（三比值不适用，剔除）｜未触发注意值 {not_triggered}｜未匹配 {unmapped}")
        if total_ev:
            print(f"可评测样本 {total_ev} 条：严格匹配 {exact}/{total_ev} = {exact/total_ev:.1%}；归并后匹配 {merged}/{total_ev} = {merged/total_ev:.1%}")
            print("按类别（归并后）：")
            for k, (n, c) in sorted(per.items(), key=lambda x: -x[1][0]):
                print(f"  {k}: {c}/{n} = {c/n:.1%}")
        else:
            print("无可评测样本")
        return

    if args.h2 is None:
        print("示例：")
        for g in [dict(h2=18,ch4=21,c2h6=12,c2h4=6,c2h2=2),
                  dict(h2=150,ch4=96,c2h6=446,c2h4=84,c2h2=0.87),
                  dict(h2=50,ch4=30,c2h6=20,c2h4=40,c2h2=30)]:
            vals, cds, fault, _ = judge(g, codes, rows)
            print("  ", g, "→ 编码", cds, "→", fault)
        print("\n用 --h2/--ch4/--c2h6/--c2h4/--c2h2 传浓度(μL/L)，或 --eval 评测。")
        return

    g = {k: getattr(args, k) for k in ("h2","ch4","c2h6","c2h4","c2h2")}
    vals, cds, fault, example = judge(g, codes, rows)
    print("输入(μL/L):", g, "｜是否触发注意值:", triggered(g, args.voltage))
    for name, v, c, zd in vals:
        print(f"  {name} = {v:.4g} → 编码 {c}" + (" (分母为0)" if zd else ""))
    print("编码组合:", cds, "→ 故障类型:", fault if fault else "未匹配")
    if example: print("典型故障:", example)

if __name__ == "__main__":
    main()