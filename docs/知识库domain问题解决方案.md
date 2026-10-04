# 知识库 Domain 问题解决方案

> 日期：2026-10-04  
> 适用范围：`knowledge/plant_kb` 的 domain 元数据治理、索引重建与路由兼容  
> 关联诊断：[未命中题系统诊断](未命中题系统诊断.md)

## 1. 结论

当前大量 domain 错误的根因不是缺少单个关键词，而是知识库把三类不同概念混在同一个 `domain` 字段中：

1. 设备域：`boiler`、`turbine`、`generator_electrical`、`auxiliary`
2. 资料类型：`fault_cases`、`standards_safety`
3. 专项类型：`transformer_dga`

同时，很多跨设备资料只能有一个 `domain` 值：

- “机械振动……汽轮机和发电机”标准被整体标成 `generator_electrical`
- “汽轮发电机组的振动及现场平衡”被整体标成 `generator_electrical`
- 汽机/锅炉检修案例被整体标成 `fault_cases`
- 故障记录中的 `device_type` 又经常统一标成 `auxiliary`

因此应把 domain 从“单值、混合语义的标签”改造成：

> **多值设备域 + 独立资料类型 + 独立专业子域 + 可追溯来源 + 人工复核状态**

## 1.1 当前工作树已完成状态

> 截至 2026-10-04，以下内容需要按工作树实际改动理解，不能把“字段已返回”当成“检索链路已完成”。

| 方案项 | 当前状态 | 证据 | 仍需处理 |
|---|---|---|---|
| 3 道路由关键词修复 | 已完成 | `intent_rules.json`、`synonym_rules.json` 已加入低压加热器、动态分离器等词；FULL-008/013/032 规则分类通过 | 后续结合真实端到端回归复核 |
| `fault_cases` 路由 | 已完成 | `INTENT_DOMAIN_MAP` 已给 boiler/turbine/generator/auxiliary 追加 `fault_cases` | 仍需观察新域对 Top-5 精度的影响 |
| BM25 `fault_cases` 分片 | 已完成 | `bm25_fault_cases.pkl` 与 `bm25_manifest.json` 已存在 | 保持分片与知识库记录数一致 |
| 相邻域扩展计算 | 部分完成 | `ADJACENT_DOMAINS` 已定义，`route_intent()` 已返回 `adjacent_domains` | `retrieval_router.py` 仍只传 `route.domains`，相邻域尚未真正参与检索 |
| 回归断言适配 | 已完成 | CUR-001/CUR-002 已改为包含目标域；smoke 8/8、core 24/24 | 后续 domain 迁移后重新跑 |
| MULTI-DOMAIN 元数据 | 未完成 | 尚无 `equipment_domains`、`domain_primary` 等字段落地 | 需要设计迁移 schema 和 sidecar |
| 跨设备资料重标 | 未完成 | 振动标准、专著、案例仍以单一 `generator_electrical` 为主 | 需要按来源和 chunk 复核 |
| `fault_cases` 资料类型拆分 | 未完成 | 连接案例仍作为 `domain=fault_cases` 进入旧索引 | 需要改为 `source_type/evidence_kind` 并保留补充通道 |
| Domain Mapping / Review | 未完成 | 尚未生成 `domain_mapping.jsonl` | 需要增加映射、置信度、复核状态 |
| 迁移后 138 题重评 | 未完成 | 现有未命中诊断和评测报告早于最近路由改动 | 重建元数据和索引后重新评估 |

当前最需要防止的误区是：`fault_cases` 能进入候选池，不代表跨设备振动资料的 domain 问题已经解决；`adjacent_domains` 已返回，也不代表检索已经使用扩域能力。
## 2. 当前问题拆解

| 问题 | 当前表现 | 直接后果 | 目标方案 |
|---|---|---|---|
| 分类轴混用 | `fault_cases`、`standards_safety` 与设备域并列使用 | 路由到设备域时看不到资料类型域 | 拆分 `equipment_domains` 与 `source_type` |
| 跨设备资料单标签 | 汽轮机+发电机振动资料全标 `generator_electrical` | `turbine` 查询被域过滤排除 | 使用 `equipment_domains` 多值标签 |
| 文档级标签过粗 | 同一来源整篇共用一个 domain | 局部条文设备属性错误 | 文档级约束 + chunk 级分类 |
| 来源类型被当设备域 | `fault_cases` 直接加入设备域路由，资料类型语义丢失 | 设备域与案例通道边界混乱 | `fault_cases` 改为独立补充检索通道 |
| 路由域集合过窄 | `turbine` 只查 `turbine` | 通用振动、轴承、标准资料无法召回 | 增加兼容域和扩域兜底 |
| 元数据未充分复核 | 54 个 B 类目标记录均 `is_citable=false` | 即使召回，也可能影响最终引用 | 增加 Domain Review 状态和验收门槛 |

## 3. 目标设计原则

### 3.1 一个 chunk 可以属于多个设备域

设备域表示“这条证据适用于哪些设备”，而不是“资料主要讲什么设备”。

例如振动通用标准应同时属于：

- `turbine`
- `generator_electrical`
- `standards_safety`

它不应被强制选择其中唯一一个。

### 3.2 资料类型不能替代设备域

以下字段必须分离：

- `source_type`：资料属于标准、规程、案例、报告、教材、论文
- `evidence_kind`：标准条文、处置步骤、故障机理、检修记录
- `equipment_domains`：适用的设备
- `specialties`：振动、DGA、热工、保护、润滑等专业方向

### 3.3 文档级和 chunk 级同时治理

- 文档级负责给出可接受的设备范围，例如“汽轮机+发电机”。
- chunk 级负责确定具体子域、部件和证据类型，例如“轴承振动/标准条文”。
- 人工 override 优先于自动分类，并保留规则来源和置信度。

### 3.4 路由允许兼容域，不要求唯一域

路由仍可输出主域，但检索应使用：

```text
route.domains ∩ chunk.equipment_domains != ∅
```

而不是：

```text
route.domains == [chunk.domain]
```

当结果为空或来源未命中时，应提供一次受控扩域重试。
## 4. 推荐元数据 Schema

### 4.1 新增字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `equipment_domains` | `string[]` | 适用设备域，允许多值 |
| `source_type` | `string` | `standard`、`procedure`、`case`、`report`、`manual`、`paper` |
| `specialties` | `string[]` | `vibration`、`lubrication`、`protection`、`dga`、`thermal` 等 |
| `domain_primary` | `string` | 兼容旧接口的首选设备域 |
| `domain_source` | `string` | `manual`、`rule`、`path`、`content`、`inherited` |
| `domain_confidence` | `number` | 0 到 1，用于复核和低置信度告警 |
| `domain_review_status` | `string` | `pending`、`reviewed`、`rejected` |
| `domain_version` | `string` | domain 规则或迁移批次版本 |
| `supersedes_domain` | `string[]` | 记录被替换的旧 domain，便于回滚和对比 |

### 4.2 兼容字段

过渡期保留 `domain` 和 `module`，由主标签派生：

```text
domain = domain_primary = equipment_domains[0]
module = domain_primary
```

索引、API 和旧脚本可以继续读取 `domain`，新检索逐步改为读取 `equipment_domains`。

### 4.3 示例：振动通用标准

```json
{
  "domain": "turbine",
  "domain_primary": "turbine",
  "equipment_domains": [
    "turbine",
    "generator_electrical",
    "standards_safety"
  ],
  "source_type": "standard",
  "specialties": [
    "vibration",
    "rotating_machinery"
  ],
  "component": "bearing",
  "applies_to": [
    "turbine",
    "generator"
  ],
  "evidence_kind": "standard_clause",
  "domain_source": "manual",
  "domain_confidence": 0.98,
  "domain_review_status": "reviewed"
}
```

### 4.4 示例：汽机小修验收案例

```json
{
  "domain": "turbine",
  "domain_primary": "turbine",
  "equipment_domains": [
    "turbine",
    "auxiliary"
  ],
  "source_type": "report",
  "specialties": [
    "maintenance"
  ],
  "component": "heater",
  "applies_to": [
    "turbine"
  ],
  "evidence_kind": "maintenance_record",
  "domain_source": "content",
  "domain_confidence": 0.82,
  "domain_review_status": "pending"
}
```

### 4.5 重标 domain 时同步重判 `is_citable`

当前大量记录的 `is_citable=false` 是数据库元数据问题，不应继续用 `doc_id + clause` 推断可引用性。正确的做法是：在生成 domain 映射时，对每条 chunk 重新检查内容、来源、条号和 OCR 质量，并由 `is_citable` 显式派生 `citation_eligible`。

#### 判定规则

| 检查项 | `true` 条件 | `false` 条件 |
|---|---|---|
| 有正文 | 实际 chunk 文本包含可阅读的正文内容，不是纯标题、目录、页码或表头 | 文本为空、只有标题、只有页码、只有目录项 |
| 有来源 | 存在 `source_file`、`source`、`doc_id` 或可追溯的文档路径 | 只有自由文本，无法回溯原文档 |
| 有明确条号 | 有数字条号、标准条号或明确的定位值，如 `4.3`、`7.3.3`、`9.3.1-表3` | 只有“原因分析:”“处理措施:”等泛化标题，没有可定位条号 |
| 无明显 OCR 错误 | 文本可读，标点和汉字完整，表格没有被严重错位或截断 | 大量 `????`、乱码、重复页眉页脚、表格错列、句子明显残缺 |

判定公式：

```text
is_citable =
    has_body
    and has_source
    and has_explicit_clause
    and ocr_quality_ok
```

只要四项中任意一项不满足，必须设为 `false`。不能因为记录存在于知识库、能被检索到或分数较高，就自动视为可引用。

#### 推荐保存字段

每条记录除 `is_citable` 外，建议保存：

```json
{
  "is_citable": true,
  "citation_eligible": true,
  "citable_checks": {
    "has_body": true,
    "has_source": true,
    "has_explicit_clause": true,
    "ocr_quality_ok": true
  },
  "citable_reason": "正文完整，来源可追溯，条号明确，OCR质量通过",
  "citable_confidence": 0.96,
  "citable_review_status": "reviewed"
}
```

低置信度或检查项冲突的记录进入人工复核，不允许直接作为可引用证据。

#### 与 Domain 重标同步执行

每条记录的迁移流程应为：

1. 读取原始 chunk 和来源文档。
2. 重新判断 `equipment_domains`、`source_type`、`specialties`。
3. 重新检查正文、来源、条号和 OCR 质量。
4. 同时写入 domain 映射和 citable 判定。
5. 更新 `knowledge.jsonl`、`lightweight_metadata.jsonl`、向量库和 BM25 索引。
6. 对 `is_citable=true` 的记录执行引用校验回归。

建议在 `domain_mapping.jsonl` 中同时保存：

```json
{
  "chunk_id": "OCR-xxxx",
  "equipment_domains": ["turbine", "generator_electrical"],
  "source_type": "standard",
  "is_citable": true,
  "citable_checks": {
    "has_body": true,
    "has_source": true,
    "has_explicit_clause": true,
    "ocr_quality_ok": true
  },
  "review_status": "reviewed"
}
```

#### 验收要求

- `is_citable=true` 的记录必须同时具备正文、来源、明确条号，并通过 OCR 质量检查。
- 不允许仅凭 `doc_id + clause` 将记录提升为可引用。
- 重新判定后，统计可引用记录数量和增量；同时抽查 `true` 记录，确认没有把乱码、表头或半句话放行。
- `is_citable=true` 的记录重新进入 Top-5 后，引用校验和人工抽检必须通过。
- `citation_eligible` 必须与 `is_citable` 保持一致，不能出现数据库中为 `false`、检索链路中却被推断为 `true` 的情况。
## 5. 规范 Domain 清单

### 5.1 设备域

- `boiler`
- `turbine`
- `generator_electrical`
- `auxiliary`

设备域应是可多选的唯一设备分类轴。

### 5.2 资料类型

- `standard`
- `procedure`
- `case`
- `report`
- `manual`
- `paper`

`fault_cases` 不再是设备域，而是：

```text
source_type = case
```

或：

```text
source_type = report
evidence_kind = fault_case
```

### 5.3 专业子域

- `vibration`
- `lubrication`
- `protection`
- `thermal`
- `pressure`
- `electrical`
- `dga`
- `maintenance`
- `control`

专业子域用于过滤和重排，不直接替代设备域。
## 6. 迁移实施步骤

### 阶段 0：冻结与备份

1. 备份 `knowledge/plant_kb/data/knowledge.jsonl`
2. 备份向量库和 BM25 索引
3. 记录当前 138 题基线：Top-5 来源命中、B 类题号、失败来源
4. 冻结旧 `domain` 字段，禁止直接在原文件上覆盖，先生成迁移映射

### 阶段 1：建立来源级 Domain 映射

先按来源文件建立文档级默认设备域，不直接写到全部 chunks。

建议表：

| 来源类型 | 默认设备域 | 资料类型 | 备注 |
|---|---|---|---|
| 集控运行规程 | 按章节/部件逐块判断 | `procedure` | 不整篇统一 |
| 锅炉检修规程 | `boiler` | `procedure` | 发电机/变压器章节单独处理 |
| 汽轮机检修报告 | `turbine` + `auxiliary` | `report` | 按部件细化 |
| 汽轮机故障案例 | `turbine` + 相关部件域 | `case` | 不再使用 `fault_cases` |
| 振动通用标准 | `turbine` + `generator_electrical` + `standards_safety` | `standard` | 多值标签 |
| 振动专著/论文 | 按内容细分 `turbine` / `generator_electrical` | `manual`/`paper` | 不能用全篇单标签 |
| 变压器 DGA | `transformer_dga` | `standard`/`case` | 保留专项域 |

### 阶段 2：Chunk 级判定

对每个 chunk 计算：

1. 部件命中：轴承、转子、低压加热器、动态分离器、磨煤机
2. 设备命中：汽轮机、发电机、锅炉、风机、给水泵
3. 故障模式：振动、泄漏、堵粉、卡涩、过热
4. 资料路径和章节路径
5. 文档级允许域约束

输出：

- `equipment_domains`
- `domain_primary`
- `domain_confidence`
- `domain_source`

低置信度或跨域冲突的 chunk 进入人工复核队列，不自动入库为主标签。

### 阶段 3：人工复核重点来源

优先复核以下高影响来源：

| 来源 | 当前问题 | 建议 |
|---|---|---|
| 汽轮机和发电机机械振动标准 | 25/25 记录为 `generator_electrical` | 改为多域，覆盖汽轮机、发电机、标准安全 |
| 汽轮发电机组振动专著 | 607/608 记录为 `generator_electrical` | 按章节拆分设备域，轴承章节至少覆盖 turbine+generator |
| 汽轮发电机组振动案例 | 616/627 记录为 `generator_electrical` | 案例按故障设备拆分，不能以资料名代替设备 |
| 大型汽轮发电机组故障案例 | 379 条记录为 `fault_cases` | 改为按设备域归属，`source_type=case` |
| 小修/大修冷态验收报告 | 全部 `fault_cases` + `device_type=auxiliary` | 以汽机、加热器、阀门、轴承实际设备为准 |
| 锅炉检修规程 | 少量发电机/变压器混入 | 保留章节级拆分并复核 |

### 阶段 4：生成 Domain Sidecar

不要一开始直接重写数据库，先生成独立映射文件：

```text
knowledge/plant_kb/data/domain_mapping.jsonl
```

每一行至少包含：

```json
{
  "chunk_id": "OCR-xxxx-m00",
  "old_domain": "generator_electrical",
  "domain_primary": "turbine",
  "equipment_domains": ["turbine", "generator_electrical", "standards_safety"],
  "source_type": "standard",
  "specialties": ["vibration"],
  "domain_confidence": 0.98,
  "domain_source": "manual",
  "domain_review_status": "reviewed",
  "domain_version": "domain-migration-v1"
}
```

### 阶段 5：重建索引

迁移完成后：

1. 用映射更新 `knowledge.jsonl`
2. 重建向量库
3. 重建 BM25 分片和 `lightweight_metadata.jsonl`
4. 校验记录数、向量数、BM25 数与源文件一致
5. 保持旧索引备份，便于回滚
## 7. 检索与路由兼容策略

知识库迁移期间，检索层需要接受多值域，避免旧路由继续单域硬过滤。

### 7.1 检索过滤

旧行为：

```text
route_domain == chunk.domain
```

目标行为：

```text
set(route_domains) & set(chunk.equipment_domains) != empty
```

### 7.2 兼容域扩展

建议按以下规则扩展：

| 路由主域 | 兼容域 | 触发条件 |
|---|---|---|
| `turbine` | `generator_electrical`、`standards_safety` | 振动、轴承、转子、轴系 |
| `generator_electrical` | `turbine`、`standards_safety` | 汽轮发电机组振动 |
| `boiler` | `auxiliary` | 制粉、磨煤机、风机 |
| `auxiliary` | `turbine`、`boiler` | 加热器、油系统、给水泵 |
| 所有设备域 | `fault_cases` 补充通道 | 需要案例证据时 |

`fault_cases` 应作为补充召回通道，不应取代设备域。当前 `intent_router.py` 已加入该兼容通道；知识库迁移时应保留这个通道，但把案例资料的设备归属写入 `equipment_domains`，并把 `source_type=case/report` 单独保存。

### 7.3 扩域重试

当满足以下任一条件时，允许一次扩展域重试：

- 指定域结果为 0
- Top-5 没有命中任何目标来源
- Top-5 中目标来源存在但全部为低置信度
- 用户明确要求查找案例或历史记录

扩域重试必须保留原有主域结果，并记录检索 trace，不能静默替换。

## 8. 验收指标

### 8.1 数据质量

| 指标 | 目标 |
|---|---:|
| `equipment_domains` 字段覆盖率 | 100% |
| 旧 `domain` 兼容字段覆盖率 | 100% |
| 关键跨设备来源多标签覆盖率 | 100% |
| Domain Review 通过率 | 关键来源 100% |
| 无 `fault_cases` 设备域残留 | 0 |
| 同源文档 domain 分布异常告警 | 可解释，不能全部单标签 |

### 8.2 检索效果

| 指标 | 目标 |
|---|---:|
| 当前 54 个 B 类目标至少一路进入 Top-300 | 54/54 |
| BM25 无域过滤可召回目标 | 不低于当前 51/54 |
| 138 题 Top-5 来源命中 | 不低于迁移前基线 |
| FULL-008/013/032 路由 | 分别包含 turbine/boiler |
| `--smoke` | 100% |
| `--core` | 100% |
| 引用目标来源且 `is_citable=true` | 逐步提升 |

### 8.3 人工抽查

- 每个关键来源至少抽查 20 个 chunks。
- 抽查重点：设备域、资料类型、部件、证据类型是否一致。
- 发现一个 chunk 多域冲突时，必须回溯到文档级规则，不能只修单条。

## 9. 推荐执行优先级

### P0：先解决影响最大的域错配

1. 给振动标准、振动专著和振动案例增加多值设备域。
2. 将故障案例从 `fault_cases` 设备域改为：
   - `source_type=case`
   - `equipment_domains=[实际设备域]`
   - `fault_cases` 只作为补充检索通道。
3. 对 FULL-008、FULL-013、FULL-032 这类路由错误，保留关键词修复，同时补充设备域兼容映射。

### P1：重建索引并回归

1. 重建向量库。
2. 重建 BM25 分片。
3. 重跑 138 题。
4. 对比迁移前后的来源命中、条号命中、引用校验和拒答率。

### P2：建立长期治理

1. 每次新增文档必须产出 domain 映射。
2. 跨设备资料必须提供多标签。
3. 低置信度 domain 不允许直接进入主检索。
4. 每轮索引发布前执行 domain 一致性检查。

## 10. 不建议的做法

- 不要只给 `INTENT_DOMAIN_MAP` 不断增加域，避免检索噪声扩散。
- 不要把所有 `fault_cases` 直接并入 `turbine` 或 `boiler` 而不保留资料类型。
- 不要把整篇“汽轮机和发电机”资料统一改成 `turbine`，否则发电机问题会反向丢失。
- 不要只靠关键词补丁修复跨设备域问题。
- 不要在未备份索引和未跑回归的情况下直接覆盖原库。

## 11. 最终建议

Domain 治理应分成两条线：

1. **知识库线**：拆分设备域、资料类型和来源类型，引入多值 `equipment_domains`。
2. **检索线**：支持多域交集、兼容域扩展和扩域重试。

如果只做第一条，旧路由仍然会单域过滤；如果只做第二条，跨设备资料仍会被单标签误导。两条线必须同时推进。

优先从当前 54 个 B 类题涉及的高影响来源开始，完成一批 `domain_mapping.jsonl`，重建索引后再用 138 题和 smoke/core 回归验证。