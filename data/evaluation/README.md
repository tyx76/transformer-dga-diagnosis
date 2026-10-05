# 测试与验收用例集

> **当前项目口径（2026-10-03）**：项目主对象已转为“通用电厂设备故障诊断”，覆盖锅炉、汽轮机、发电机及辅机。DGA 仅保留为可选专项、历史技术资产或备用能力，不再作为主链路范围；本文如涉及 DGA，请按专项资料阅读。
## 0. 当前主评测集（2026-10-03）

- 项目主口径已转为通用电厂设备故障诊断，主评测题集为 `plant_kb_full_questions.jsonl`，共 138 条，覆盖锅炉、汽轮机、发电机和通用设备场景。
- 本文下方描述的 50 条 `acceptance_cases.jsonl` 主要面向旧变压器 DGA/油温/安全口径，现作为 DGA 专项和历史回归资产保留。
- 新主链路的验收重点为：通用设备路由、Top-5 来源命中、引用相关性、拒答率和真实 API 端到端表现。


> 文档状态：现行｜更新：2026-10-03
> 文件：`acceptance_cases.jsonl`（50 条）
> 用途：检索、意图路由、引用校验、拒答和端到端回归。

## 1. 字段

| 字段 | 说明 |
|---|---|
| `id` | 唯一用例编号 |
| `question` | 用户问题；空字符串用于边界测试 |
| `expected_docs` | 期望命中的文档 ID |
| `expected_clauses` | 期望命中的条号集合 |
| `category` | 用例类别 |

`expected_docs=[]`、`expected_clauses=[]` 表示应拒答或没有规范依据，不应强行生成结论。

## 2. 分类统计

| 类别 | 用例数 |
|---|---:|
| `dga_analysis` | 10 |
| `oil_temp` | 8 |
| `safety_check` | 6 |
| `equipment_spec` | 6 |
| `multi` | 6 |
| `irrelevant` | 6 |
| `boundary` | 8 |
| 合计 | 50 |

## 3. 当前评测脚本

### 3.1 回归测试

```powershell
python scripts\run_regression.py
```

输出 `docs/04_评测与回归/exam_proof/回归测试结果_20260918_修订版.xlsx`，覆盖数据一致性、检索、RRF、引用校验和主链路桩测试。

### 3.2 RRF 权重和离线批量评测

```powershell
python scripts\tune_rrf_weights.py
```

- 默认离线，不调用真实 LLM；
- 可评测 39 条有目标条号的用例；
- 2026-09-22 结果的 Top-5 命中率为 76.92%（30/39）；
- 四组 RRF 权重指标持平，当前保留 1.0/1.0；
- 结果文件为 `docs/04_评测与回归/exam_proof/RRF权重搜索结果_20260922.xlsx`。

### 3.3 真实 A/B

```powershell
python scripts\shadow_ab_test.py
```

当前内置 7 条关键用例，真实 DeepSeek 结果记录在 `docs/03_检索与排序/影子对比报告.md`。样本较小，只能作为方向性验证。

## 4. 指标口径

- **Top-5 命中率**：`expected_clauses` 是否进入最终 Top-5；只统计有目标的用例。
- **引用正确率**：回答中的引用条号是否来自实际检索结果。
- **拒答率**：`expected_docs` 和 `expected_clauses` 均为空时是否正确拒答。
- **多意图召回**：`multi` 用例是否覆盖多个领域。
- **LLM 兜底**：规则无法判断时是否进入 LLM 分类，并记录调用次数。

> 离线引用指标是结构代理，不能替代真实生成质量评测；正式汇报时必须注明口径。
