# 油浸式电力变压器 DGA 故障根因分析智能体

基于 RAG（检索增强生成）的工业设备故障诊断原型：用户输入故障现象（如“变压器油中乙炔含量超标”），系统从规程知识库中检索依据，由大模型生成**可溯源**的根因分析与处置建议。

- 对象：输变电/工业厂站中的**油浸式电力变压器（主变）**
- 诊断主线：**DGA（油中溶解气体分析）**，判据以 **DL/T 722-2014** 为准
- 辅助资料：DL/T 572-2021 运行维护条款
- 考核：四川大学未来技术创新创业社团考核 · 考题八（技术向）；评比 2026-10-12 ~ 10-16
- 当前阶段：主链路已具备“领域过滤 → 向量 + BM25 → RRF → 生成 → 引用校验”；后续重点是意图路由、加权融合和评测

## 当前能力

| 能力 | 现状 |
|---|---|
| 知识库 | `vector_kb/knowledge.db`，123 块 = normative 5 + reference 118；bge-m3 1024 维 |
| 统一语料 | `data/corpus/clauses.jsonl`，本地生成 123 条；由 `scripts/build_unified_corpus.py` 合并 722 判据与 572 运维条款 |
| 向量检索 | `retrieve(question, top_k=3, min_score=0.45, ...) -> list[dict]`，返回 `doc_id / clause / title / text / page / score / citation` |
| BM25 检索 | `bm25_retrieve(question, top_k=10)`；jieba 分词、领域词典、化学式下标归一化、索引缓存 |
| 混合检索 | `hybrid_retrieve()`：领域过滤 → 向量 Top-10 + BM25 Top-10 → RRF 融合；`main.py` 最终取 Top-5 |
| 生成 | `generate(question, chunks) -> str`，调用 DeepSeek `deepseek-chat`；空 chunks 不调用 API |
| 引用校验 | `verify_citations()` 检查答案引用是否来自检索结果；失败时最多重写 2 次，再删除无依据句 |
| 调试输出 | `python main.py --debug "..."`，输出各阶段条号和分数摘要，不打印完整条文 |
| 规则基线 | `scripts/dga_ratio.py`，基于改良三比值法，当前样本准确率 61.8% |
| 样本 | `data/samples/dga_samples_uL_per_L.csv`，3466 条，统一单位为 μL/L |

## 目录结构

| 目录/文件 | 内容 |
|---|---|
| `main.py` | 当前统一入口：混合检索、生成、引用校验、`--debug` |
| `vector_kb/` | 向量库、BM25、RRF、混合检索、生成、引用校验和领域过滤模块 |
| `data/corpus/` | DL/T 572、DL/T 722 语料与判据文本；统一 JSONL 为本地生成物 |
| `data/rules/` | DL/T 572 第 7 章规则、DL/T 722 三比值判据 JSON |
| `data/samples/` | DGA 样本数据及单位统一结果 |
| `scripts/` | 样本处理、三比值判据、规则匹配、统一语料、环境检查脚本 |
| `docs/` | 00~10 项目文档、总状态、技术路线、实现方案、评测、日志和验收记录 |
| `literature/` | 标准/论文 PDF，本地保留，版权与体积原因不入库 |
| `source_materials/` | 考核题目等原始材料，本地保留不入库 |
| `venv/` | 本地虚拟环境，不提交 |

## 环境要求

- Python 3.10+（本机实测 3.14.7）
- Windows PowerShell
- Ollama 与 embedding 模型 `bge-m3:latest`
- DeepSeek API Key，用于 `generate()` 的真实调用
- SQLite 本地向量存储；不依赖 Chroma 运行时

## 快速开始

```powershell
cd D:\社团考题第八

# 1. 创建并激活虚拟环境
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 API Key（写入项目根目录 .env，不提交）
# DEEPSEEK_API_KEY=你的真实Key

# 4. 生成统一条文语料（本地生成，不入库）
python scripts\build_unified_corpus.py
```

确认 Ollama 与知识库：

```powershell
ollama list
python vector_kb\cli.py info
```

检索和生成：

```powershell
# 保留：纯向量调试和对比
python vector_kb\cli.py query "乙炔超标该怎么处理"

# 保留：纯向量检索 + 生成
python vector_kb\cli.py ask "乙炔超标该怎么处理" --show-sources

# 当前主链路：领域过滤 + 向量 + BM25 + RRF + 生成 + 引用校验
python main.py "变压器油温过高怎么处理"

# 调试摘要：步骤、条号和分数
python main.py --debug "变压器油温过高怎么处理"

# 交互模式
python main.py
```

如果 PowerShell 无法直接找到 `python`，使用：

```powershell
.\venv\Scripts\python.exe main.py "变压器油温过高怎么处理"
```

## 当前验证状态

- 统一语料共 123 条：DL/T 722-2014 5 条 + DL/T 572-2021 118 条。
- “变压器油温过高怎么处理”：BM25 Top-3 为 `7.1.5 / 7.1.6 / 7.1.8`；混合检索 Top-3 为 `7.1.5 / 7.1.8 / 7.1.6`。
- `乙炔超标怎么处理`：BM25 与混合检索 Top-1 均为 DL/T 722 `9.3.1-表3`。
- `C₂H₂注意值`：BM25 与混合检索 Top-1 均为 DL/T 722 `9.3.1-表3`。
- “今天晚上吃什么”“变压器怎么炒菜”：领域过滤后直接拒答，不调用生成模型。
- 引用校验已覆盖正常引用、伪造条号、重写成功、全部编造和无效文档号。
- `--debug` 已覆盖用户问题、查询改写、两路检索、RRF、生成、引用校验和最终输出摘要。

## 回归测试

当前自动回归共 24 项：通过 23 项、失败 0 项、已知问题 1 项。

```powershell
python scripts\run_regression.py
```

回归覆盖领域过滤、纯向量、BM25、混合检索、RRF、引用校验、主链路重试、调试输出和数据一致性。检索调用真实 Ollama + BM25，生成调用使用桩，避免 DeepSeek 费用。

- [回归测试报告](docs/exam_proof/回归测试报告_20260918.md)
- [回归测试 Excel（修订版）](docs/exam_proof/回归测试结果_20260918_修订版.xlsx)

> KNOWN-002 已撤销：该问题仅由桩响应推断，真实 API 验证无问题，不需要修复。
## 已知限制

- `vector_kb/cli.py` 的 `query/ask` 仍是**纯向量工具**，用于调试和对比；当前主链路以 `main.py` 为准。
- 统一语料后，BM25 可能出现跨文档域干扰，例如 DGA 问题混入 DL/T 572 运维条文；后续需增加意图路由、按 `doc_id` 过滤和加权 RRF。
- DL/T 572-2021 参考库暂未记录页码，检索结果中可能显示“未记录”。
- DL/T 722-2014 的 `9.3.3`、`10.2.4`、`10.3` 等正文原则条款尚未进入正式知识库。
- 当前领域过滤为规则方案，后续计划引入论文 C6 FaultSeer 的 Agentic 意图判断与路由。

## 数据与版权说明

> 详见 [NOTICE.md](NOTICE.md)：本仓库不收录标准原文与第三方原始数据文件。

- `literature/`（标准/论文 PDF）与 `source_materials/` 仅本地使用，不提交。
- `vector_kb/knowledge.db`、`vector_kb/bm25_index.pkl`、`data/corpus/clauses.jsonl`、第三方原始样本文件和 `.env` 不提交。
- 仓库保留项目代码、文档、规则 JSON，以及经人工整理的判据表和元数据。

## 团队分工

- 队长：环境、工程与架构
- 成员2：领域知识、数据录入、规则与标准
- 成员3：文献综述、检索评测、文档与验收记录

## 文档入口

- 项目状态与下一步：[`docs/00_project_status.md`](docs/00_project_status.md)
- 实现方案与未来架构：[`docs/09_implementation_plan.md`](docs/09_implementation_plan.md)
- 开发日志与日程：[`docs/05_dev_log_and_schedule.md`](docs/05_dev_log_and_schedule.md)
- 切条与元数据规范：[`docs/07_chunking_and_metadata_spec.md`](docs/07_chunking_and_metadata_spec.md)
- 验收记录：[`docs/08_acceptance_record.md`](docs/08_acceptance_record.md)
- 文献总览与路线映射：[`docs/10_all_literature_overview_and_tech_routes.md`](docs/10_all_literature_overview_and_tech_routes.md)

## 远程状态

- 当前已推送基线：`108494c feat: add hybrid BM25 and RRF retrieval`
- 2026-09-18 的调试输出、引用校验、领域过滤、统一语料和文档同步仍在当前工作区整理中，提交前请以 `git status` 为准。