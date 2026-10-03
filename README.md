# 通用电厂设备故障根因分析与处置决策智能体

> **当前项目口径（2026-10-03）**：项目主对象已转为“通用电厂设备故障诊断”，覆盖锅炉、汽轮机、发电机及辅机。DGA 仅保留为可选专项、历史技术资产或备用能力，不再作为主链路范围；本文如涉及 DGA，请按专项资料阅读。


> 文档状态：现行主文档｜口径更新：2026-10-03。

基于 RAG（检索增强生成）的通用电厂设备故障诊断原型：用户输入锅炉、汽轮机、发电机或辅机异常现象，系统从规程、运行检修资料和故障案例中检索依据，再由 DeepSeek 生成**可溯源、可校验、可拒答**的根因分析与处置建议。

- 对象：电厂通用设备，包括锅炉、汽轮机、发电机及主要辅机
- 诊断主线：设备故障现象、运行异常、部件异常、保护与处置决策
- 典型领域：`boiler`、`turbine`、`generator_electrical`、`auxiliary`、`standards_safety`、`fault_cases`
- DGA：保留为可选专项、历史技术资产或备用能力，不再作为主链路范围
- 竞赛：四川大学未来技术创新创业社团考核 · 考题八（技术向）
- 当前阶段：单轮 RAG 主链路、意图路由、检索融合和引用校验已有基础；**通用设备领域路由、新 plant_kb 路径统一和精排**仍在迁移中
- 文档基线：2026-10-03

## 当前能力

| 能力 | 当前状态 |
|---|---|
| 旧向量库 | `vector_kb/knowledge.db`，123 块 DGA/变压器条款；作为专项和回归资产保留 |
| 目标主知识库 | `plant_kb/`，按锅炉、汽轮机、发电机、辅机等领域组织；当前存在多个候选版本，正式数据版本待统一 |
| DGA 专项备份 | `backups/pure_kb_20260928/` 与旧 DGA 规则/索引保留为专项或回退资产，不参与通用设备主口径 |
| 意图理解 | 规则表已切换为 boiler、turbine、generator、auxiliary、safety、transformer、irrelevant 七类，支持多意图；LLM 兜底类别仍待同步 |
| 检索路由 | 按七类意图路由到 boiler、turbine、generator_electrical、auxiliary、standards_safety、transformer_dga，再融合 hybrid 与 plant_kb |
| 向量检索 | `retrieve(question, top_k=3, min_score=0.45, ...)`，返回 doc_id/clause/title/text/page/score/citation |
| BM25 | 检索代码已参数化；目标是使用与 plant_kb 同源的语料和索引，旧 123 条语料仅作为 DGA 专项资产 |
| 混合检索 | 领域过滤 → 向量 Top-K + BM25 Top-K → RRF；主链路最终取 Top-5 |
| 生成 | DeepSeek `deepseek-chat`；系统提示词和报告结构需要从“变压器专家”迁移为“电厂设备诊断专家” |
| 引用校验 | 校验回答中的引用是否来自本次检索；失败最多重写 2 次，最后删除无依据句或拒答 |
| 调试 | `python main.py --debug "..."` 输出意图、路由、两路检索、融合、生成和校验摘要 |
| DGA 专项规则 | 改良三比值脚本 `scripts/dga_ratio.py`；保留为可选专项能力，不是通用设备 P0 |
| 评测资产 | 138 条通用设备题库、50 条旧 DGA 用例、24 项自动回归、真实 API A/B 和 RRF 实验 |
| 旧 DGA 样本 | `data/samples/dga_samples_uL_per_L.csv`，3466 条；仅用于 DGA 专项实验 |

> 注意：当前代码和文档正处于从“变压器 DGA 专项”向“通用电厂设备诊断”迁移阶段。当前 P0 是通用设备领域路由、plant_kb 数据源统一、检索精排和 138 题端到端评测；数值 DGA 接入降为可选专项。

## 主链路

```text
用户问题
  → classify_intent：规则优先，必要时 DeepSeek 兜底
  → route_intent：intent → domains / filters / mode
  → USE_ROUTER=true：hybrid + plant_kb + RRF
  → USE_ROUTER=false：纯 hybrid_retrieve
  → generate：仅基于检索条文生成
  → verify_citations：引用存在性校验
  → 重写、删除无依据句或拒答
```

关键参数：

- 向量默认阈值：`min_score=0.45`
- hybrid + plant_kb 各取候选：20 条
- 最终上下文：Top-5
- RRF 平滑常数：`k=60`
- 当前融合权重：hybrid 1.0 / plant_kb 1.0
- 后端切换：通过 `KB_BACKEND=pure_kb|plant_kb` 选择知识库后端
- DGA 兼容：旧的 `pure_kb`、DL/T 722/572 和 `scripts/dga_ratio.py` 仅作为专项或回退能力保留
- 权重实验结论：1.0/1.2、1.0/1.5、1.0/0.8 与 1.0/1.0 指标持平，暂不调整
- 引用重写：初次生成 + 最多 2 次重写

## 目录结构

```text
.
├─ main.py                         # 统一问答入口
├─ vector_kb/                      # 向量、BM25、RRF、路由、生成、引用校验
├─ plant_kb/                       # 当前主知识库后端与适配输入
├─ backups/                        # 旧 pure_kb 与本地备份，不提交
├─ data/
│  ├─ corpus/                      # 722 事实性判据与本地统一语料
│  ├─ rules/                       # 三比值规则、572 处置规则、意图规则
│  ├─ samples/                     # 公开 DGA 样本及统一量纲结果
│  └─ evaluation/                  # 50 条验收用例
├─ scripts/                        # 建库、规则计算、回归、A/B、RRF 调参
├─ docs/                           # 00–10 主文档、笔记、验收与证据
├─ survey/                         # 初次/第二次调研报告归档
├─ model_exam/                     # 2026-09-15 朴素 RAG 基线测评
├─ literature/                     # 版权文献，本地保留，不提交
├─ source_materials/               # 题目等原始材料，本地保留，不提交
└─ submissions_pending_review/     # 待审核成员材料，本地保留，不提交
```

## 环境要求

- Python 3.10+；开发环境实测 Python 3.14.7
- Windows PowerShell
- Ollama，并已拉取 `bge-m3:latest`
- DeepSeek API Key，用于真实生成和 LLM 兜底意图分类
- SQLite 本地向量存储
- 当前运行时**不依赖** Chroma 或 LangChain；`requirements.txt` 中的相关包保留为扩展/学习候选

## 快速开始

### 1. 安装环境

```powershell
cd D:\社团考题第八
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

在 `.env` 中填写：

```dotenv
DEEPSEEK_API_KEY=你的真实Key
USE_ROUTER=true
```

启动 Ollama 并准备模型：

```powershell
ollama pull bge-m3:latest
ollama list
```

### 2. 准备知识库

仓库公开部分可重建 722 的事实性判据库：

```powershell
python vector_kb\cli.py ingest vector_kb\corpus\clauses.jsonl `
  --collection normative `
  --doc-id "DL/T 722-2014" `
  --force `
  --source "vector_kb/corpus/clauses.jsonl"
```

完整 123 块库还需要**仅本地保留**的 DL/T 572 条款文件。取得合法材料后执行：

```powershell
python vector_kb\cli.py ingest vector_kb\corpus\DLT-572-2021_clauses.jsonl `
  --collection reference `
  --doc-id "DL/T 572-2021" `
  --force `
  --source "vector_kb/corpus/DLT-572-2021_clauses.jsonl"

python scripts\build_unified_corpus.py
python vector_kb\cli.py info
```

> 版权边界：仓库不提交标准 PDF、572 条款 JSONL、完整向量库和本地统一语料，因此干净 clone 无法独立重建 123 块全量库。详见 `NOTICE.md` 和 `docs/README.md`。

### 3. 运行

```powershell
# 当前主链路：路由 + hybrid + 知识库检索 + 生成 + 引用校验
python main.py "汽轮机振动故障"

# 输出各阶段摘要
python main.py --debug "汽轮机振动故障"

# 交互模式
python main.py
```

纯向量调试入口仍保留：

```powershell
python vector_kb\cli.py query "乙炔超标怎么处理"
python vector_kb\cli.py ask "乙炔超标怎么处理" --show-sources
```

`query/ask` 只走纯向量链路，不包含意图路由、plant_kb 融合或最终引用校验。

## 评测与证据

| 评测 | 结果 | 说明 |
|---|---:|---|
| 规则基线 | 61.8% | 220kV 样本归并后准确率，单独规则方法存在明显上限 |
| 自动回归 | 23 通过 / 0 失败 / 1 已知项 | 发表于 2026-09-18，覆盖检索、融合、引用和流程 |
| 50 条离线评测 | Top-5 76.92% | 39 条可评用例命中 30 条；引用与拒答代理指标均为 100% |
| RRF 权重实验 | 四组持平 | A=1.0/1.0 暂定为当前方案；瓶颈在精排而非召回 |
| 真实 DeepSeek A/B | A 50.00% → B 83.33% | 7 条关键用例，样本较小，只能作为方向性证据 |

复现命令：

```powershell
python scripts\run_regression.py
python scripts\shadow_ab_test.py
python scripts\tune_rrf_weights.py
```


主要证据：

- [项目状态与文档导航](docs/README.md)
- [回归测试报告（2026-09-18）](docs/exam_proof/回归测试报告_20260918.md)
- [影子模式 A/B 对比](docs/影子对比报告.md)
- [RRF 权重实验结果](docs/exam_proof/RRF权重搜索结果_20260922.xlsx)
- [验收记录](docs/08_acceptance_record.md)
- [开发日志与日程](docs/05_dev_log_and_schedule.md)

## 已知限制

1. 代码和文档仍处于从 DGA 专项向通用电厂设备诊断迁移阶段，意图类别、生成提示词、检索路径和评测口径尚未全部统一。
2. 通用设备主知识库的正式数据版本、路径和同源 BM25 索引尚未最终确定。
3. 50 条旧评测主要面向 DGA/油温，新主评测应切换到 138 条通用设备题库。
4. 通用设备问题的采样字段、设备子域和引用格式仍需完善。
5. 50 条评测暴露出排序层瓶颈：目标条文已在候选池内，但可能被挤出 Top-5；下一步应评估 Reranker 和查询改写。
6. C6 FaultSeer 式完整 Agentic 路由尚未实现；当前是受控的规则 + LLM 单轮流程。
7. GB 26860-2011、572 表格结构化、中文故障案例仍待补充。
8. `vector_kb/cli.py` 的 `query/ask` 仍是纯向量调试工具，不代表正式主链路。
9. `plant_kb` 的 `knowledge.db` 和 `data/knowledge.jsonl` 作为本地大文件未提交；干净 clone 需要单独获取提交包或按 README 重建数据库。

## 数据与版权

> 详见 [NOTICE.md](NOTICE.md)。

- 标准、论文、第三方原始数据、`knowledge.db`、BM25 索引、统一语料和 `.env` 不进入版本库。
- 仓库仅保留代码、文档、规则与经人工整理的判据参数。
- 任何涉及停运、检修、带电作业或恢复送电的建议都必须保留人工复核关口。

## 团队分工

- 队长：环境、工程与架构
- 成员2：领域知识、数据录入、规则与标准
- 成员3：文献综述、检索评测、文档与验收记录

## 文档入口

- [完整文档导航](docs/README.md)
- [项目状态与下一步](docs/00_project_status.md)
- [实现方案](docs/09_implementation_plan.md)
- [开发日志与日程](docs/05_dev_log_and_schedule.md)
- [切条与元数据规范](docs/07_chunking_and_metadata_spec.md)
- [验收记录](docs/08_acceptance_record.md)
- [文献总览与路线映射](docs/10_all_literature_overview_and_tech_routes.md)
- [调研报告归档](survey/README.md)

## 仓库状态

- `origin/main` 当前基线：`847077a docs: record retrieval ranking diagnosis`
- 2026-09-27 的工作区正在整理文档与 `survey/` 目录迁移；提交前以 `git status` 为准。
