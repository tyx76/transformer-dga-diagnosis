# 通用电厂设备故障诊断项目实现方案

> **当前项目口径（2026-10-03）**：项目主对象已转为“通用电厂设备故障诊断”，覆盖锅炉、汽轮机、发电机及辅机。DGA 仅保留为可选专项、历史技术资产或备用能力，不再作为主链路范围；本文如涉及 DGA，请按专项资料阅读。

## 0. 当前口径变更（2026-10-03）

- 项目主对象已从“油浸式变压器 DGA 专项”转为“通用电厂设备故障诊断”。
- 主对象覆盖锅炉、汽轮机、发电机及主要辅机。
- 目标主知识库为 `plant_kb`，按设备领域和子域组织检索证据。
- 当前 P0 是通用设备路由、plant_kb 数据源统一、检索精排和 138 题端到端评测。
- DGA、DL/T 722/572、`pure_kb` 和三比值脚本降为可选专项、历史资产或回退能力。
- 本文后续如出现“DGA 主链路”“变压器主对象”等措辞，按历史技术资产阅读，以本节口径为准。


> 文档状态：现行｜更新：2026-10-03
> 当前主入口：根目录 `main.py`
> 目标：闭合“设备异常现象 → 领域路由 → 向量/BM25/RRF 检索 → 精排 → 引用校验 → 带依据诊断报告 → 评测”的链路。DGA 仅作为可选专项。
> 历史交接方案和已废弃的 `app/`、FastAPI、Chroma 目录设计不再作为当前实现依据。

## 1. 总体结论

技术路线为：

> **规则/机理作为确定性底座 + 向量与 BM25 检索提供可溯源证据 + 受控路由和 Agent 编排排因 + LLM 组织报告 + 引用校验与人工复核兜底。**

当前已完成单轮问答和检索基础链路，七类规则意图与域映射已切换到通用电厂设备。当前最优先事项是：

1. 将意图和领域路由迁移到 boiler、turbine、generator_electrical、auxiliary；
2. 统一 plant_kb 正式数据源、向量库和 BM25 索引；
3. 用 138 条通用设备题库做端到端评测；
4. 解决查询改写、Reranker 和引用相关性问题。

## 2. 当前系统分层

| 层级 | 当前职责 | 主要文件 |
|---|---|---|
| 数据层 | 722 判据、572 条款、规则 JSON、DGA 样本、验收用例 | `data/`、`plant_kb/data/` |
| 存储层 | SQLite 向量库、BM25 索引 | `vector_kb/store.py`、`knowledge.db` |
| 向量层 | Ollama embedding 与余弦检索 | `vector_kb/embeddings.py`、`retrieval.py` |
| 关键词层 | jieba + rank-bm25 | `vector_kb/bm25_retriever.py` |
| 融合层 | RRF 与去重归一化 | `vector_kb/rrf_fusion.py`、`knowledge_base_adapter.py` |
| 路由层 | 意图分类、domain/filter 路由 | `intent_classifier.py`、`intent_router.py`、`retrieval_router.py` |
| 领域层 | 明显无关问题拦截 | `domain_guard.py` |
| 生成层 | 上下文拼接、引用格式、DeepSeek 调用 | `generation.py` |
| 校验层 | 引用存在性检查、重写提示、删除无依据句 | `citation_verifier.py` |
| 入口层 | CLI 单轮问答和交互模式 | `main.py` |
| 评测层 | 回归、A/B、权重搜索、规则基线 | `scripts/`、`data/evaluation/` |
| 文档层 | 单点状态、方案、日志、验收和调研 | `docs/`、`survey/` |

## 3. 当前主链路

```text
用户问题
  |
  v
classify_intent
  规则优先 -> 命中直接返回
  规则不确定 -> DeepSeek LLM 兜底
  |
  v
route_intent
  intent -> domains / filters / mode
  |
  +-- irrelevant -> 直接拒答，不检索、不生成
  |
  v
USE_ROUTER=true
  +-- hybrid_retrieve：领域过滤 + 向量 + BM25 + RRF
  +-- plant_kb.search：显式 domains/filters
  +-- merge_with_hybrid：两路证据再次 RRF 融合
  |
  v
Top-5 证据
  |
  v
generate(question, chunks)
  |
  v
verify_citations(answer, chunks)
  |
  +-- valid -> 返回
  +-- invalid -> 最多重写 2 次
  +-- 仍失败 -> 删除无依据句或拒答
```

关键参数：

| 参数 | 当前值 | 位置 |
|---|---:|---|
| 向量相似度阈值 | 0.45 | `retrieval.py` |
| BM25/向量候选数 | 10 | `hybrid_retriever.py` |
| 路由两路候选数 | 各 20 | `retrieval_router.py` |
| 最终上下文 | Top-5 | `main.py` |
| RRF 平滑常数 | 60 | `rrf_fusion.py`、adapter |
| hybrid/plant_kb 权重 | 1.0 / 1.0 | `knowledge_base_adapter.py` |
| 引用重写上限 | 2 | `main.py` |

## 4. 数据组织与边界

### 4.1 公开可提交内容

- 代码、脚本和测试；
- 文档、日志、验收记录和调研报告；
- 经人工整理的事实性判据参数；
- 规则标识、条号来源和自撰摘要；
- 公开数据整理后的数值表（遵守原始仓库许可）。

### 4.2 本地不提交内容

- DL/T 572、DL/T 722 等标准 PDF 和正文转写；
- 572 条款 JSONL 和统一语料 `data/corpus/clauses.jsonl`；
- `vector_kb/knowledge.db`、`bm25_index.pkl`；
- 第三方原始 xlsx；
- `.env` 和 API Key；
- `literature/`、`source_materials/`、`submissions_pending_review/`。

### 4.3 可复现性边界

公开仓库可以重建 722 的 5 条事实性判据库。完整 123 块向量库依赖本地合法取得的 572 条款文件，干净 clone 无法单独重建全量库。文档必须明确标注这一边界，不能把本地资产写成公开可复现。

## 5. 当前数据资产

| 资产 | 规模 | 说明 |
|---|---:|---|
| 722 判据 | 5 | 表3、表4、表6、表7、CO2/CO |
| 572 条款 | 118 | 运行监视与异常处理等 |
| 统一语料 | 123 | 本地生成，用于向量与 BM25 |
| plant_kb | 3800 | dga/oil_temp/safety/equipment/dp/cases |
| DGA 样本 | 3466 | 统一为 μL/L |
| 验收用例 | 50 | 10 DGA、8 油温、6 安全、6 设备、6 多意图、6 无关、8 边界 |
| 自动回归 | 24 | 2026-09-18 产物 |

## 6. 当前接口

### 6.1 向量检索

```python
retrieve(
    question: str,
    top_k: int = 3,
    min_score: float = 0.45,
    db: str = DB_DEFAULT,
) -> list[dict]
```

返回字段：

```text
doc_id / clause / title / text / page / score / citation
```

### 6.2 生成

```python
generate(question: str, chunks: list[dict]) -> str
```

- chunks 为空时不调用 API；
- 模型默认 `deepseek-chat`；
- temperature=0.1，max_tokens=800；
- 提示词要求只依据检索条文回答。

### 6.3 引用校验

```python
verify_citations(answer: str, chunks: list[dict]) -> dict
remove_invalid_citation_sentences(answer: str, chunks: list[dict]) -> str
build_retry_prompt(question: str, verification: dict, chunks: list[dict]) -> str
```

### 6.4 路由

```python
route_and_retrieve(
    question: str,
    top_k: int = 5,
    shadow: bool = True,
    trace=None,
) -> dict
```

返回 `chunks / source / intent / route / hybrid_top5 / kb_top5 / llm_calls`。

## 7. 规则诊断接入方案

DGA 规则接入降为可选专项，不再是通用设备主链路 P0。

### 7.1 目标输入

支持自然语言和结构化输入同时存在：

```json
{
  "question": "乙炔超标该怎么处理",
  "voltage_level": "220kV",
  "gases": {
    "H2": 150,
    "CH4": 96,
    "C2H6": 446,
    "C2H4": 84,
    "C2H2": 0.87
  },
  "production_rate": null
}
```

### 7.2 目标流程

```text
输入解析
  -> 字段/单位/电压等级校验
  -> 注意值判断
  -> 产气速率判断（有数据时）
  -> 改良三比值编码
  -> 故障类型候选
  -> 检索对应条号和处置条款
  -> LLM 生成解释
  -> 规则/引用/安全校验
  -> 报告
```

### 7.3 输出结构

```json
{
  "status": "answered",
  "input_validation": {},
  "rule_diagnosis": {
    "attention_values_triggered": [],
    "ratio_codes": [],
    "fault_candidates": [],
    "evidence": []
  },
  "retrieval_evidence": [],
  "answer": "",
  "citations": [],
  "requires_human_review": true,
  "coverage_gaps": []
}
```

### 7.4 冲突处理

- 规则结论与 LLM 冲突时，以规则和合法原文为准；
- 输入缺电压等级、单位或关键气体时，列出缺失项，不强行判断；
- 规程未覆盖时标记“资料未覆盖”；
- 涉及停运、检修、灭火等操作时必须标记人工复核。

## 8. 检索优化路线

2026-09-22 的 50 条评测已把瓶颈定位到排序层：

- 目标条文通常已在向量或 BM25 候选中；
- 两路候选高度重叠；
- 目标条文可能未进入最终 Top-5；
- 四组 RRF 权重结果持平；
- 扩大候选池不能从根本解决排序。

优先级：

1. **查询改写**：抽取设备、电压等级、气体、现象和处置意图；
2. **Reranker**：对融合候选与问题逐条精排；
3. **检索质量闸门**：参考 Self-RAG/CRAG，判断证据相关性和支持度；
4. **分块优化**：检查表格、复合条款和标题是否被切坏；
5. **加权融合**：只有在召回和精排不足时再考虑，避免无依据调参。

暂不做：

- 无边界扩大 Top-K；
- 完整 GraphRAG 前置；
- 领域微调；
- 用公开 Web 作为正式标准依据。

## 9. 受控 Agent Workflow

目标不是自由 ReAct 循环，而是白名单工具和有限步骤的受控流程：

```text
route
  -> validate_input
  -> run_dga_rules
  -> retrieve_evidence
  -> check_evidence_sufficiency
  -> maybe_rewrite_query
  -> maybe_retrieve_again
  -> generate_report
  -> validate_citations
  -> validate_safety
  -> human_review_gate
```

约束：

- 最大步骤数；
- 工具白名单；
- 每个结论必须有证据 ID；
- 规则具有否决权；
- 禁止自动执行停送电、隔离、检修等高风险操作；
- 失败时明确拒答并提出补检项。

## 10. 评测方案

### 10.1 检索指标

- Recall@5；
- MRR；
- Top-5 跨域干扰率；
- 多意图覆盖；
- 无关问题拒答率；
- 平均响应时间。

### 10.2 生成与合规指标

- 引用正确率；
- 引用覆盖率；
- 无依据断言率；
- 危险建议拦截率；
- 人工复核触发正确率；
- 规则/LLM 结论一致率。

### 10.3 评测层级

1. 离线结构代理：低成本、覆盖 50 条用例，当前用于权重比较；
2. 真实 DeepSeek 生成：少量关键用例，补充回答质量与引用正确性；
3. 端到端回归：固定命令、环境、原始输出和报告；
4. 规则样本评测：3466 条 DGA 样本，单独报告 61.8% 基线，不与生成正确率混写。

### 10.4 目标

| 指标 | 建议目标 |
|---|---:|
| 核心问题 Recall@5 | ≥ 90% |
| 引用正确率 | 100% |
| 应拒答用例拒答率 | 100% |
| 危险建议 | 0 条 |
| 自动复现用例 | ≥ 50 条 |
| 人工复核标记 | 高风险建议 100% 覆盖 |

## 11. 分阶段实施计划

### 阶段 A：数据与文档基线（已完成）

- 整理文档和数据目录；
- 核验 722 真本；
- 完成判据和处置规则结构化；
- 建立切块与元数据规范；
- 建立 50 条验收用例。

### 阶段 B：检索与生成闭环（已完成）

- 向量检索、BM25、RRF、混合检索；
- 规则/LLM 意图分类和 domain 路由；
- plant_kb 适配与融合；
- DeepSeek 生成和引用校验；
- `main.py` 调试链路和自动回归。

### 阶段 C：规则诊断接入与报告统一（当前）

- [ ] 结构化输入解析和校验；
- [ ] 调用 `scripts/dga_ratio.py`；
- [ ] 把规则结论接入检索和生成；
- [ ] 输出统一诊断 JSON 与人类可读报告；
- [ ] 增加高风险建议和人工复核字段。

### 阶段 D：排序与质量闸门（下一阶段）

- [ ] 查询改写；
- [ ] Reranker 实验；
- [ ] 相关性和支持度判断；
- [ ] 复测 50 条并报告消融。

### 阶段 E：受控 Agent 与增强证据（后置）

- [ ] 有限步骤 Agent 状态机；
- [ ] 工具白名单和证据 ID；
- [ ] 轻量“气体—故障—处置”关系图；
- [ ] 多模态和案例库作为辅助证据。

## 12. 最终验收标准

- [ ] `python main.py "乙炔超标该怎么处理"` 能稳定返回带条号的诊断结果；
- [ ] 数值 DGA 输入能够输出注意值、三比值、候选故障类型和规则依据；
- [ ] “乙炔超标”能同时覆盖注意值、故障判断和处置原则；
- [ ] 所有引用都能在本次检索结果中找到；
- [ ] 知识库未命中时明确拒答，并指出缺失信息或补检项；
- [ ] 危险处置建议 100% 标记人工复核；
- [ ] 至少 50 条验收用例可以自动评测；
- [ ] 评测报告同时包含检索、引用、拒答、规则基线和响应时间；
- [ ] README、docs/00、docs/05、docs/08、docs/09 与最终代码一致；
- [ ] 公开仓库明确说明版权资产和本地可复现边界。

## 13. 当前下一步

1. 在 `main.py` 增加结构化 DGA 输入与规则诊断路径。
2. 设计规则 + 检索 + LLM 的统一输出 schema。
3. 将 50 条用例评测封装为固定 CLI 报告。
4. 选择 5–10 条低分排序用例做查询改写和 Reranker 实验。
5. 补齐 722 正文原则条款和 572 页码后重新回归。
6. 最后再考虑受控 Agent、轻量图谱和多模态扩展。
