# 测试用例题集

> 文件：`acceptance_cases.jsonl`  
> 用例数：50  
> 用途：检索、意图路由、引用校验和端到端评测。

## 字段

| 字段 | 说明 |
|---|---|
| `id` | 唯一用例编号 |
| `question` | 用户问题 |
| `expected_docs` | 期望命中的文档 ID |
| `expected_clauses` | 期望命中的条号集合 |
| `category` | 用例类别 |

空 `question` 用于边界测试。`expected_docs=[]`、`expected_clauses=[]` 表示应拒答或无规范依据，不应强行生成结论。

## 分类统计

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

## 评测建议

- Top-5 命中率：`expected_clauses` 是否进入最终 Top-5。
- 引用正确率：回答引用的条号是否来自实际检索结果。
- 拒答率：`expected_docs` 和 `expected_clauses` 均为空时是否正确拒答。
- 多意图召回：`multi` 用例是否同时覆盖多个领域。
- LLM 兜底：`boundary` 中规则无法判断的用例是否进入 LLM 分类。