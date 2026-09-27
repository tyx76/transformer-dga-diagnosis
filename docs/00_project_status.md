# 项目状态与进度总览（单点真相）

> 文档状态：现行单点真相｜更新：2026-09-27。

> 维护：全队每次功能或数据变更后同步
> 完整文档导航：[`docs/README.md`](README.md)

## 1. 项目口径

- 考题八·**技术向**：交付 GitHub 仓库，不参加产品向答辩。
- 评比：2026-10-12 ~ 10-16；建议在 2026-10-11 前完成仓库整理和最终回归。
- 对象：**油浸式电力变压器（主变）**。
- 诊断主线：**DGA（油中溶解气体分析）**，核心判据为 **DL/T 722-2014**。
- 辅助语料：DL/T 572-2021 的运行监视、异常运行和处理条款。
- IEC 60599:2022 因版权/费用原因不作为正式依据。
- 知识库未命中时必须拒答；生成结论必须可追溯到实际检索条文；处置建议保留人工复核关口。

## 2. 当前主链路

```text
用户问题
  → 规则优先 + LLM 兜底意图分类 classify_intent
  → 意图到 domains / filters / mode 路由 route_intent
  → USE_ROUTER 开关
      ├─ true：hybrid + pure_kb + RRF
      └─ false：纯 hybrid_retrieve
  → generate DeepSeek
  → verify_citations
  → 最多重写 2 次
  → 删除无依据句或拒答
  → 最终输出
```

入口：

```powershell
python main.py "变压器油温过高怎么处理"
python main.py --debug "变压器油温过高怎么处理"
python main.py
```

关键参数：

- 向量默认阈值：`min_score=0.45`
- hybrid 与 pure_kb 候选池：各 20 条
- 最终上下文：Top-5
- RRF 平滑常数：`k=60`
- 当前融合权重：hybrid 1.0 / pure_kb 1.0
- 引用重写：初次生成 + 最多 2 次重写
- DeepSeek：`deepseek-chat`，temperature=0.1，max_tokens=800

## 3. 资产与模块

| 类别 | 位置 | 状态 |
|---|---|---|
| 统一语料 | `data/corpus/clauses.jsonl`，123 条（722 判据 5 + 572 条款 118） | 本地生成，不提交 |
| 统一脚本 | `scripts/build_unified_corpus.py` | 可用 |
| 向量库 | `vector_kb/knowledge.db`，123 块，bge-m3 1024 维 | 本地资产，不提交 |
| 纯知识库 | `pure_kb/`，198 条、六领域、显式 domains/filters API | 已接入检索路由 |
| 向量检索 | `vector_kb/retrieval.py` | 可用 |
| BM25 | `vector_kb/bm25_retriever.py` + `bm25_index.pkl` | v2，源文件变化后自动重建 |
| RRF | `vector_kb/rrf_fusion.py` | 可用 |
| 混合检索 | `vector_kb/hybrid_retriever.py` | 领域过滤 + 向量 + BM25 + RRF |
| 意图分类 | `vector_kb/intent_classifier.py` + `data/rules/intent_rules.json` | 规则优先、LLM 兜底、多意图 |
| 意图路由 | `vector_kb/intent_router.py` | intent → domains/filters/mode |
| pure_kb 适配 | `vector_kb/knowledge_base_adapter.py` | 字段归一化、dp 过滤、去重、RRF |
| 检索调度 | `vector_kb/retrieval_router.py` | 意图 + hybrid + pure_kb |
| 领域过滤 | `vector_kb/domain_guard.py` | 规则版 |
| 生成 | `vector_kb/generation.py` | DeepSeek 生成 |
| 引用校验 | `vector_kb/citation_verifier.py` | 校验、重写提示、无依据句删除 |
| 调试 CLI | `vector_kb/cli.py`：`ingest/info/query/ask` | 纯向量链路，仅用于调试对比 |
| 主入口 | `main.py`：路由检索 + 生成 + 引用校验 + `--debug` | 可用 |
| 规则基线 | `scripts/dga_ratio.py`，样本归并准确率 61.8% | 可用，但尚未接入 main |
| DGA 样本 | `data/samples/dga_samples_uL_per_L.csv`，3466 条 | 可用于规则评测 |
| 验收用例 | `data/evaluation/acceptance_cases.jsonl`，50 条 | 已建立 |
| 文档 | `docs/README.md` + `docs/00–10` + notes/exam_proof | 2026-09-27 已整理 |
| 调研归档 | `survey/`，初次与第二轮分开 | 2026-09-27 已整理 |

## 4. 已验证结果

| 项目 | 结果 | 日期/口径 |
|---|---:|---|
| 规则三比值基线 | 61.8% | 220kV，归并标签口径 |
| 自动回归 | 23 通过 / 0 失败 / 1 已知项 | 2026-09-18，共 24 项 |
| 50 条离线检索评测 | Top-5 76.92%（30/39） | 2026-09-22，规则意图和非生成代理指标 |
| RRF 权重实验 | 四组持平 | A=1.0/1.0 暂定 |
| 真实 DeepSeek A/B | A 50.00% → B 83.33% | 7 条关键用例，样本小 |
| 引用正确率 | 100% | 2026-09-22 离线代理口径 |
| 无关问题拒答率 | 100% | 2026-09-22 离线代理口径 |

代表性检索结果：

| 查询 | 结果 |
|---|---|
| `变压器油温过高怎么处理` | 混合 Top-3：`7.1.5 / 7.1.8 / 7.1.6` |
| `乙炔超标怎么处理` | BM25、混合检索 Top-1 均为 `9.3.1-表3` |
| `C₂H₂注意值` | Top-1 为 `9.3.1-表3` |
| `今天晚上吃什么` | 领域过滤直接拒绝，不调用生成 |

## 5. 当前问题与待办

| 优先级 | 事项 | 状态 | 下一步 |
|---|---|---|---|
| P0 | 数值型 DGA 输入接入规则引擎 | 未完成 | `main.py` 增加结构化输入与规则诊断路径 |
| P0 | 排序层瓶颈 | 已定位 | 目标条文常已召回但被挤出 Top-5；评估 Reranker 与查询改写 |
| P1 | 722 `9.3.3 / 10.2.4 / 10.3` 正文原则条款 | 待补 | 按 `docs/07` 切条、页码校验、重新入库 |
| P1 | 572 页码映射 | 待补 | 从合法原文补齐 page 字段 |
| P1 | 真实 DeepSeek 端到端评测 | 部分完成 | 在 50 条集上扩大真实生成样本 |
| P1 | 检索质量闸门 | 设计完成 | 参考 Self-RAG/CRAG，增加相关性、支持度和拒答判断 |
| P2 | C6 FaultSeer 式 Agentic 路由 | 暂缓 | 先稳定规则、检索和评测底座 |
| P2 | embedding 参数化 | 暂缓 | 支持切换模型与测试维度 |
| P2 | 572 表格、GB 26860、中文故障案例 | 阶段二 | 取得合法材料后补充 |

已关闭：

- KNOWN-002 由桩响应推断，真实 API 未复现，已撤销。
- RRF 权重并非未验证：四组方案结果持平，当前保留 1.0/1.0。
- 意图路由、domain 过滤和 pure_kb 融合已接入，不再列为待开发项。

## 6. 当前限制

1. `main.py` 目前是自然语言单轮 RAG，不会自动解析 H2、CH4、C2H2 等数值并调用三比值脚本。
2. 公开仓库缺少版权受限的 DL/T 572 条款文件，干净 clone 无法独立重建 123 块完整向量库。
3. DL/T 572 页码缺口会降低引用展示完整度。
4. `vector_kb/cli.py query/ask` 不包含混合检索、路由和引用校验，只用于纯向量对比。
5. 评测集已有 50 条，但部分用例的预期条号和真实生成质量仍需要继续复核。

## 7. 下一步顺序

1. 让 `main.py` 支持结构化 DGA 输入，并调用 `scripts/dga_ratio.py` 返回规则诊断结果。
2. 将规则结果、hybrid/pure_kb 证据和引用校验合并为统一诊断报告。
3. 基于 50 条用例实现不依赖人工读表的自动评测汇总。
4. 评估查询改写和 Cross-Encoder/Reranker，解决排序层瓶颈。
5. 补 722 正文原则条款和 572 页码。
6. 完善受控 Agent Workflow、检索质量闸门和人工复核字段。

## 8. 远程与工作区状态

- `origin/main` 当前基线：`847077a docs: record retrieval ranking diagnosis`。
- 2026-09-27 正在整理 `survey/` 目录迁移和全部 Markdown 文档。
- 工作区存在未提交改动时，以 `git status` 为准。
- 不提交：标准/论文 PDF、第三方原始数据、`knowledge.db`、`bm25_index.pkl`、统一语料、572 条款文件和 `.env`。

## 9. 文档地图

| 编号 | 文档 | 内容 |
|---|---|---|
| 00 | 项目状态与进度（本文） | 口径、主链路、资产、验收、待办和限制 |
| 01 | 文献与标准 | 文献总表、获取状态、标准与必读清单 |
| 02 | 概念与学习路线 | 基础概念、技术学习路线和读论文方法 |
| 03 | 技术路线调研 | 知识增强路线分类、优劣与选型依据 |
| 04 | 任务二方案与评测 | 文本处理、知识组织、规则基线与评测 |
| 05 | 开发日志与日程 | 日志、日程、卡点、团队规范 |
| 06 | 文献速览与笔记索引 | 核心论文摘要与笔记导航 |
| 07 | 切条与元数据规范 | 字段、条号、切分粒度和入库校验 |
| 08 | 验收记录 | 检索、生成、RRF、引用、路由和实跑结果 |
| 09 | 实现方案 | 当前架构、数据边界、路线图和验收标准 |
| 10 | 文献通读与路线映射 | 文献总览、技术路线和设计依据索引 |
| — | `docs/README.md` | 全量导航与文档状态规范 |