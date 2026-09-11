# data/样本 —— 公开 DGA 故障样本数据集

> 用途：最小原型的**评测基线/闭环样例/消融对比**（不是训练大模型）。
> 更新：2026-09-10 ｜ 下载：全队

## 一、统一样本集
`dga_samples.csv` —— 由多来源合并，**共 3466 条**。

字段：`source, h2, ch4, c2h6, c2h4, c2h2, co, co2, scale, label_raw, label_std`
- `scale = μL/L`：原始浓度（alan456 来源）
- `scale = log10(μL/L)`：归一化特征（sguys99 来源，其中 log10 值 0 表示该气体为 0/未测）
- `label_raw`：原始标签；`label_std`：已映射的统一中文标签（仅 alan456 有；sguys99 为 0/1 数字标签，含义待确认）

## 二、来源明细
| 文件 | 来源仓库 | 条数 | 格式 |
|---|---|---|---|
| alan456__data.xlsx | github.com/alan-456/transformer-fault-dataset | 2321 | 原始浓度 + 中文故障类型 |
| alan456__dataset_589.xlsx | 同上 | 589 | 原始浓度 + 中文故障类型 |
| sguys99__Duval_Classification_1.xlsx | github.com/sguys99/datasets | 167 | 转置：行=log10 特征+Labels，列=样本 |
| sguys99__Duval_Classification_41.xlsx | 同上 | 389 | 同上 |

## 三、标签分布（alan456，label_std）
正常 740｜高温过热 662｜高能放电 458｜低能放电 396｜局部放电 232｜低温过热 229｜中温过热 193

## 四、使用注意
1. 两个来源的**量纲不同**（μL/L vs log10），用时先统一：对 alan456 取 log10 或对 sguys99 还原浓度（注意 log10=0 的语义）；
2. 标签体系不同（中文 7 类 vs 0/1），合并前需确认映射；
3. 数据集为公开来源，引用时注明上述 GitHub 仓库；
4. 与 DL/T 722-2014 判据结果对照评测时，注意标准/数据集年代与判据差异。

## 五、生成脚本
`scripts/build_sample_dataset.py`（读取本目录 xlsx → 生成 dga_samples.csv）

## 六、量纲统一（2026-09-11 更新）
**推荐直接使用：`dga_samples_uL_per_L.csv`** —— 全部样本统一为 **μL/L**，共 3466 条。

- 字段：`source, h2, ch4, c2h6, c2h4, c2h2, co, co2, scale(=μL/L), source_scale(原始量纲), label_raw, label_std`
- 换算规则：sguys99 原始为 `log10(μL/L)`，按 `10^x` 还原；其中 **log10=0 表示"该气体为 0/未测"，还原为 0**（不是 1）。
- 同时**修正了 sguys99 的键名解析**：此前 `dga_samples.csv` 中该来源（556 条）几乎全为空，现已补齐 7 种气体。
- 生成脚本：`scripts/unify_sample_units.py`
- 注意：
  1. alan456 来源**没有 CO / CO2** 两列（原始数据集只含 5 种气体）；
  2. sguys99 的标签是 **0/1**，含义待确认；
  3. sguys99 是 log10 还原值，量级可能偏大；与 alan456 合并使用前建议先做分布检查。