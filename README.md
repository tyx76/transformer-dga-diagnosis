# 油浸式电力变压器 DGA 故障根因分析智能体

> 文档状态：现行主文档｜更新：2026-09-27。

基于 RAG（检索增强生成）的工业设备故障诊断原型：用户输入变压器异常现象，系统从规程知识库中检索依据，再由 DeepSeek 生成**带条号、可校验、可拒答**的根因分析与处置建议。

- 对象：输变电/工业厂站中的**油浸式电力变压器（主变）**
- 诊断主线：**DGA（油中溶解气体分析）**，核心判据为 **DL/T 722-2014**
- 辅助语料：DL/T 572-2021 的运行监视与异常处理条款
- 竞赛：四川大学未来技术创新创业社团考核 · 考题八（技术向）
- 当前阶段：单轮 RAG 主链路、意图路由、pure_kb 融合、引用校验和离线评测已落地；**数值 DGA 输入自动调用规则引擎**仍未接入主链路
- 文档基线：2026-09-27

## 当前能力

| 能力 | 当前状态 |
|---|---|
| 向量知识库 | `vector_kb/knowledge.db`，123 块 = normative 5 + reference 118；Ollama `bge-m3:latest`，1024 维 |
| 纯知识库 | `pure_kb/`，198 条、六个领域；只接受显式 `domains/filters`，不自行判断意图 |
| 意图理解 | 规则优先、LLM 兜底，支持 `multi` 多意图；规则文件为 `data/rules/intent_rules.json` |
| 检索路由 | 默认 `USE_ROUTER=true`，按意图选择 domains/filters，再融合 hybrid 与 pure_kb |
| 向量检索 | `retrieve(question, top_k=3, min_score=0.45, ...)`，返回 doc_id/clause/title/text/page/score/citation |
| BM25 | jieba + rank-bm25，统一语料 123 条，索引版本 v2，源文件变化后自动重建 |
| 混合检索 | 领域过滤 → 向量 Top-K + BM25 Top-K → RRF；主链路最终取 Top-5 |
| 生成 | DeepSeek `deepseek-chat`，temperature=0.1，max_tokens=800；无证据时不调用 API |
| 引用校验 | 校验回答中的引用是否来自本次检索；失败最多重写 2 次，最后删除无依据句或拒答 |
| 调试 | `python main.py --debug "..."` 输出意图、路由、两路检索、融合、生成和校验摘要 |
| 规则基线 | 改良三比值脚本 `scripts/dga_ratio.py`；220kV 样本归并准确率 61.8% |
| 评测资产 | 50 条验收用例、24 项自动回归、7 条真实 DeepSeek A/B、RRF 四组权重实验 |
| 样本 | `data/samples/dga_samples_uL_per_L.csv`，3466 条，统一为 μL/L |

> 注意：当前 `main.py` 面向自然语言问答，尚未把数值型 DGA 输入自动交给 `scripts/dga_ratio.py` 做规则诊断。这是下一阶段优先级最高的功能缺口。

## 主链路

```text
用户问题
  → classify_intent：规则优先，必要时 DeepSeek 兜底
  → route_intent：intent → domains / filters / mode
  → USE_ROUTER=true：hybrid + pure_kb + RRF
  → USE_ROUTER=false：纯 hybrid_retrieve
  → generate：仅基于检索条文生成
  → verify_citations：引用存在性校验
  → 重写、删除无依据句或拒答
```

关键参数：

- 向量默认阈值：`min_score=0.45`
- hybrid + pure_kb 各取候选：20 条
- 最终上下文：Top-5
- RRF 平滑常数：`k=60`
- 当前融合权重：hybrid 1.0 / pure_kb 1.0
- 权重实验结论：1.0/1.2、1.0/1.5、1.0/0.8 与 1.0/1.0 指标持平，暂不调整
- 引用重写：初次生成 + 最多 2 次重写

## 目录结构

```text
.
├─ main.py                         # 统一问答入口
├─ vector_kb/                      # 向量、BM25、RRF、路由、生成、引用校验
├─ pure_kb/                        # 独立纯知识库后端与适配输入
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
# 当前主链路：路由 + hybrid + pure_kb + 生成 + 引用校验
python main.py "变压器油温过高怎么处理"

# 输出各阶段摘要
python main.py --debug "变压器油温过高怎么处理"

# 交互模式
python main.py
```

纯向量调试入口仍保留：

```powershell
python vector_kb\cli.py query "乙炔超标怎么处理"
python vector_kb\cli.py ask "乙炔超标怎么处理" --show-sources
```

`query/ask` 只走纯向量链路，不包含意图路由、pure_kb 融合或最终引用校验。

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

1. 数值型 DGA 诊断尚未接入 `main.py`，目前主要问题形式仍是自然语言现象问答。
2. 完整知识库依赖未公开的 572 本地条款，公开仓库不能单独复现全部 123 块。
3. DL/T 722-2014 的 `9.3.3`、`10.2.4`、`10.3` 等正文原则条款尚未入库。
4. DL/T 572-2021 参考库暂未记录页码，部分结果会显示“未记录”。
5. 50 条评测暴露出排序层瓶颈：目标条文已在候选池内，但可能被挤出 Top-5；下一步应评估 Reranker 和查询改写。
6. C6 FaultSeer 式完整 Agentic 路由尚未实现；当前是受控的规则 + LLM 单轮流程。
7. GB 26860-2011、572 表格结构化、中文故障案例仍待补充。
8. `vector_kb/cli.py` 的 `query/ask` 仍是纯向量调试工具，不代表正式主链路。

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