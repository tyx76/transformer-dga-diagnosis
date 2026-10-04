# fault_cases 路由与相邻域扩展验收

> 日期：2026-10-04
> 修改文件：`vector_kb/intent_router.py`

## 1. 路由验收

| 输入 | 意图 | 模式 | domains | adjacent_domains | 结果 |
|---|---|---|---:|---|---|---|
| 汽轮机振动 | turbine | search | `['turbine', 'fault_cases']` | `['turbine', 'generator_electrical']` | PASS |
| 发电机定子绝缘 | generator | search | `['generator_electrical', 'fault_cases']` | `['generator_electrical', 'turbine']` | PASS |
| 锅炉过热器内漏 | boiler | search | `['boiler', 'fault_cases']` | `['boiler', 'auxiliary']` | PASS |
| 今天晚饭吃什么 | irrelevant | refuse | `[]` | `[]` | PASS |

## 2. FULL-103 / FULL-119 验证

| 题号 | 路由 domains | Top-5 中 fault_cases 条数 | 期望来源 Top-300 排名 | 期望来源 Top-5 命中 | 结论 |
|---|---|---:|---:|---|---|
| FULL-103 | `['turbine', 'fault_cases']` | 3 | 10 | 否 | fault_cases 路由已生效，目标来源已进入候选池，但尚未进入 Top-5 |
| FULL-119 | `['turbine', 'fault_cases']` | 4 | 32 | 否 | fault_cases 路由已生效，目标来源已进入候选池，但尚未进入 Top-5 |

FULL-103 期望来源：

`知识库素材/汽轮机/#4机2023年大修冷态验收报告（打印)(1)`

FULL-119 期望来源：

`知识库素材/汽轮机/1 热机分场汽机专业2024年#2机小修冷态验收报告11.07`

## 3. 回归

| 模式 | 结果 | 耗时 |
|---|---|---:|
| smoke | 8/8 通过 | 0.47s |
| core | 24/24 通过 | 26.90s |

## 4. 结论

- `fault_cases` 已加入 boiler、turbine、generator、auxiliary 的 domains。
- `adjacent_domains` 已按意图返回，turbine 与 generator_electrical 已具备扩展定义；但当前 `retrieval_router.py` 仍只传入 `route.domains`，尚未真正使用 adjacent domains，因此实体检索尚未完成扩域。
- FULL-103、FULL-119 已能检索到 fault_cases 记录，且期望来源进入 Top-300。
- 两题的期望来源仍未进入 Top-5，属于后续排序/精排问题，不是路由缺失。
