# 意图分类规则表说明

> **当前项目口径（2026-10-03）**：项目主对象已转为“通用电厂设备故障诊断”，覆盖锅炉、汽轮机、发电机及辅机。DGA 仅保留为可选专项、历史技术资产或备用能力，不再作为主链路范围。

> 文档状态：现行规则说明｜更新：2026-10-03
> 文件：`data/rules/intent_rules.json`
> 用途：为“规则优先，LLM 兜底”的意图理解模块提供可配置关键词和领域路由规则。

## 1. 当前七类意图

| 意图 | 检索域 | 关键词数量 |
|---|---|---:|
| `boiler` | `boiler` | 13 |
| `turbine` | `turbine` | 12 |
| `generator` | `generator_electrical` | 9 |
| `auxiliary` | `auxiliary` | 7 |
| `safety` | `standards_safety` | 7 |
| `transformer` | `transformer_dga` | 8 |
| `irrelevant` | 不检索 | 5 |

## 2. 关键词

- `boiler`：锅炉、水冷壁、过热器、再热器、省煤器、空预器、磨煤机、制粉、燃烧器、爆管、泄漏、结焦、吹灰。
- `turbine`：汽轮机、通流、级组、转子、轴承、轴系、振动、轴封、凝汽器、DEH、调速、旁路。
- `generator`：发电机、定子、转子、励磁、氢冷、密封油、绝缘、局放、盖振。
- `auxiliary`：辅机、风机、给水泵、循环水泵、油系统、冷却系统、轴承温度。
- `safety`：停机、停运、停电、隔离、检修、紧急、处置。
- `transformer`：变压器、乙炔、氢气、总烃、DGA、油色谱、三比值、注意值。
- `irrelevant`：吃、天气、电影、游戏、晚饭。

## 3. 置信度与多意图

- 命中至少 2 个关键词：置信度 `0.8`。
- 命中 1 个强特征词：置信度 `0.7`。
- 命中 1 个弱特征词：置信度 `0.4`。
- 最高置信度低于 `0.5` 时，规则层返回 `None`，交给 LLM 兜底。
- 命中两个及以上意图时返回 `multi`，并合并所有命中意图的检索域。

## 4. 域映射

```python
INTENT_DOMAIN_MAP = {
    "boiler": ("boiler",),
    "turbine": ("turbine",),
    "generator": ("generator_electrical",),
    "auxiliary": ("auxiliary",),
    "safety": ("standards_safety",),
    "transformer": ("transformer_dga",),
    "irrelevant": (),
}
```

## 5. 验收示例

| 问题 | 预期意图 | 检索域 |
|---|---|---|
| 过热器爆管 | `boiler` | `boiler` |
| 汽轮机振动 | `turbine` | `turbine` |
| 发电机定子绝缘 | `generator` | `generator_electrical` |
| 乙炔超标 | `transformer` | `transformer_dga` |
| 今天晚饭吃什么 | `irrelevant` | 不检索 |
| 汽轮机振动导致轴承温度高 | `multi` | `turbine`、`auxiliary` |

## 6. 使用约定

- 规则表负责“候选意图”和“推荐检索域”。
- `irrelevant` 命中后不调用检索和生成。
- `multi` 结果必须合并所有命中域的检索结果。
- `transformer` 是专项意图，不再代表整个项目主口径。
- 修改关键词或域映射时，必须同步更新本说明并重新执行验收测试。
