# 项目状态与进度总览（单点真相）

> 更新：2026-09-18 ｜ 维护：全队每周对表时同步 ｜ 文档编号为 00–10（旧编号对照见文末）

## 0. 文档地图

| 编号 | 文档 | 内容 |
|---|---|---|
| 00 | 项目状态与进度（本文） | 口径、阶段、资产、核验、验收、待办、远程状态 |
| 01 | 文献与标准 | 文献总表、获取状态、标准与必读清单 |
| 02 | 概念与学习路线 | 基础概念、学习路线、论文精读方法 |
| 03 | 技术路线调研 | 知识增强路线分类、优劣与选型依据 |
| 04 | 任务二方案与评测 | 文本处理、排因方案、规则基线评测 |
| 05 | 开发日志与日程 | 日志、日程、阶段计划、遗留问题 |
| 06 | 文献速览与笔记索引 | 核心论文速览与笔记导航 |
| 07 | 切条与元数据规范 | 字段、条号、切分粒度、入库校验 |
| 08 | 验收记录 | 检索、生成、RRF、引用校验和实跑结果 |
| 09 | 实现方案 | 目标架构、Agent 工作流和后续实施计划 |
| 10 | 全部文献通读与路线映射 | 文献总览、技术路线和设计依据索引 |
| — | `docs/notes/` | 精读卡、略读卡、论文笔记、模板 |
| — | `docs/exam_proof/` | 测试截图、相似度记录等验收佐证 |

## 1. 项目口径

- 考题八·**技术向**：交付 GitHub 仓库，不参加产品向答辩。
- 评比：2026-10-12 ~ 10-16；建议 2026-10-11 前完成仓库整理。
- 对象：**油浸式电力变压器（主变）**。
- 诊断主线：**DGA（油中溶解气体分析）**，核心判据为 **DL/T 722-2014**。
- 辅助语料：DL/T 572-2021 的油温、油位、冷却、负载和运行维护条款。
- IEC 60599:2022 因版权/费用原因不作为正式依据。
- 知识库未命中时必须拒答；生成结论必须可追溯到实际检索条文；处置建议保留人工复核关口。

## 2. 当前阶段与主链路

当前主链路已经跑通：

```text
用户问题
  → 规则优先 + LLM 兜底意图分类 classify_intent
  → 意图到 domain/filter 路由 route_intent
  → USE_ROUTER 开关
      ├─ route_and_retrieve：hybrid + pure_kb + RRF
      └─ hybrid_retrieve：纯混合检索回退
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
- 两路候选各取：`candidate_k=10`
- `main.py` 最终上下文：`top_k=5`
- RRF 平滑常数：`k=60`
- 检索开关：`USE_ROUTER=true` 默认启用路由，设为 `false` 回退纯 hybrid
- 引用重写：初次生成 + 最多 2 次重写
- DeepSeek：`deepseek-chat`，`temperature=0.1`，`max_tokens=800`

## 3. 资产与模块清单

| 类别 | 位置 | 状态 |
|---|---|---|
| 统一语料 | `data/corpus/clauses.jsonl`，123 条（722 判据 5 + 572 条款 118） | ✅ 本地生成，不入库 |
| 统一脚本 | `scripts/build_unified_corpus.py` | ✅ |
| 向量库 | `vector_kb/knowledge.db`，123 块，bge-m3 1024 维 | ✅ 本地资产 |
| 纯知识库 | `pure_kb/`，198 条、六领域、纯 domains/filters API | ✅ 已接入检索路由 |
| 向量检索 | `vector_kb/retrieval.py` | ✅ |
| BM25 | `vector_kb/bm25_retriever.py` + `bm25_index.pkl` | ✅ v2，源文件变化自动重建 |
| RRF | `vector_kb/rrf_fusion.py` | ✅ |
| 混合检索 | `vector_kb/hybrid_retriever.py` | ✅ |
| 意图分类 | `vector_kb/intent_classifier.py` + `data/rules/intent_rules.json` | ✅ 规则优先、LLM 兜底、多意图 |
| 意图路由 | `vector_kb/intent_router.py` | ✅ intent → domains/filters |
| 纯知识库适配器 | `vector_kb/knowledge_base_adapter.py` | ✅ 字段归一化、去重、RRF 融合 |
| 检索调度 | `vector_kb/retrieval_router.py` | ✅ 意图 + hybrid + pure_kb |
| 领域过滤 | `vector_kb/domain_guard.py` | ✅ 规则版 |
| 生成 | `vector_kb/generation.py` | ✅ |
| 引用校验 | `vector_kb/citation_verifier.py` | ✅ |
| CLI 调试工具 | `vector_kb/cli.py`：`ingest/info/query/ask` | ✅ 纯向量链路保留 |
| 主入口 | `main.py`：USE_ROUTER 检索调度 + 生成 + 引用校验 + `--debug` | ✅ |
| 规则基线 | `scripts/dga_ratio.py`，样本归并准确率 61.8% | ✅ |
| 样本 | `data/samples/dga_samples_uL_per_L.csv`，3466 条 | ✅ |
| 测试用例集 | `data/evaluation/acceptance_cases.jsonl`，50 条 | ✅ 已建立 |
| 文档 | `docs/00–10` + `docs/notes/` + `docs/exam_proof/` | ✅ |
| 环境 | `venv` Python 3.14.7 + `requirements.txt` | ✅ |

## 4. 关键核验与验收记录

- ✅ DL/T 722-2014 真本已取得并核验，722 判据表和正文转写已归档。
- ✅ 表6/表7 已人工核对，规则库 v0.3 标记 VERIFIED。
- ✅ DL/T 572-2021 第 7 章规则库 25 条可用。
- ✅ 公开 DGA 样本 3466 条统一为 μL/L；规则基线归并准确率 61.8%。
- ✅ 09-14：完成向量 `retrieve()`、DeepSeek `generate()` 和旧版 CLI `ask` 闭环。
- ✅ 09-18：完成 jieba + BM25、RRF、混合检索和 `main.py` 接入。
- ✅ 09-18：完成引用校验和重写：正常引用通过，伪造条号打回，最多重写 2 次，最终删除无依据句。
- ✅ 09-18：完成 `--debug`，输出问题、查询改写、向量 Top-K、BM25 Top-K、RRF、生成、校验和最终输出摘要。
- ✅ 09-18：完成统一语料合并，BM25 从 5 条扩展到 123 条。
- ✅ 09-18：完成阈值与规则过滤。无关问题“今天晚上吃什么”“变压器怎么炒菜”不会进入生成。
- ✅ 09-18：完成规则优先 + LLM 兜底意图分类，并支持 `multi` 多意图。
- ✅ 09-18：完成纯知识库适配器和 `USE_ROUTER` 直切开关。
- ✅ 09-18：真实 DeepSeek A/B 对比 7 条关键用例，Top-5 命中率从 50.00% 提升至 83.33%。
- ✅ 09-18：建立 50 条测试用例题集。

代表性结果：

| 查询 | 检索结果 |
|---|---|
| `变压器油温过高怎么处理` | BM25 Top-3：`7.1.5 / 7.1.6 / 7.1.8`；混合 Top-3：`7.1.5 / 7.1.8 / 7.1.6` |
| `乙炔超标怎么处理` | BM25、混合检索 Top-1 均为 DL/T 722 `9.3.1-表3` |
| `C₂H₂注意值` | BM25、混合检索 Top-1 均为 DL/T 722 `9.3.1-表3` |
| `油里有不好的东西` | 混合检索包含 DL/T 572 与 DL/T 722 弱相关证据 |

## 5. 当前问题与待办

| 优先级 | 事项 | 状态 |
|---|---|---|
| P0 | 基于 50 条测试用例建立批量自动评测脚本 | ⏳ 下一步 |
| P0 | RRF 动态权重和相关性门槛 | ⏳ 后续 |
| P1 | 补 722 `9.3.3 / 10.2.4 / 10.3` 正文原则条款 | ⏳ |
| P1 | 补充 572 页码映射 | ⏳ |
| P1 | 扩大真实 DeepSeek 端到端验收样本 | ⏳ |
| P2 | 引入 C6 FaultSeer 的完整 Agentic 判断与路由 | 暂缓 |
| P2 | embedding 配置参数化 | 暂缓 |
| — | KNOWN-002 桩测试误判已撤销：真实 API 验证无问题，不修复 | 已关闭 |
| P2 | 572 表格、GB 26860、中文故障案例 | 阶段二 |

## 6. 远程与工作区状态

- 当前已推送基线：`a423dd5 feat: add USE_ROUTER retrieval switch`。
- `main` 与 `origin/main` 在已推送提交上同步。
- 工作区包含测试用例题集和最新文档同步改动，提交前以 `git status` 为准。
- 标准正文、PDF、大体积样本、`knowledge.db`、`bm25_index.pkl` 和本地统一语料不提交。

## 7. 下一步顺序

1. 基于 50 条测试用例建立批量自动评测脚本。
2. 调整 RRF 动态权重和文档域策略，复测“油温过高”“乙炔超标”“无关问题”。
3. 扩大真实 DeepSeek 端到端验收样本。
4. 补 722 正文原则条款和 572 页码。
5. 完善 Agent Workflow 和 C6 Agentic 路由。

## 8. 旧编号对照（历史版本见 Git）

| 旧编号 | 现位置 |
|---|---|
| 01、05、07、08 | `01 文献与标准` |
| 02、10 | `02 概念与学习路线` |
| 03 | `03 技术路线调研` |
| 04、12 | `04 任务二方案与评测` |
| 09、13 | `05 开发日志与日程` |
| 06 | `06 文献速览与笔记索引` |
| 11 | 已删除（未定稿综述草稿） |