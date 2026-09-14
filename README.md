# 油浸式电力变压器 DGA 故障根因分析智能体

基于 RAG（检索增强生成）的工业设备故障诊断原型：用户输入故障现象（如“变压器油中乙炔含量超标”），系统从规程知识库中检索依据，由大模型生成**可溯源**的根因分析与处置建议。

- 对象：输变电/工业厂站中的**油浸式电力变压器（主变）**
- 诊断主线：**DGA（油中溶解气体分析）**，判据以 **DL/T 722-2014** 为准
- 考核：四川大学未来技术创新创业社团考核 · 考题八（技术向）；评比 2026-10-12 ~ 10-16
- 当前阶段：主干闭环已跑通，已有统一入口 `main.py`；阶段二再进行模块化、混合检索、重排与自省纠错

## 当前能力

| 能力 | 现状 |
|---|---|
| 知识库 | `vector_kb/knowledge.db`，123 块 = normative 5 + reference 118；bge-m3 1024 维；向量异常 0 |
| 检索 | `retrieve(question, top_k=3, min_score=0.35, ...) -> list[dict]`，返回 `doc_id / clause / title / text / page / score / citation` |
| 生成 | `generate(question, chunks) -> str`，调用 DeepSeek `deepseek-chat`；`chunks` 为空时不调用 API，直接拒答 |
| 统一入口 | `main.py` 支持单次问答和交互模式，复用 `vector_kb/cli.py` 的 `retrieve()` / `generate()` |
| 规则基线 | `scripts/dga_ratio.py`，基于改良三比值法，当前样本准确率 61.8% |
| 样本 | `data/samples/dga_samples_uL_per_L.csv`，3466 条，统一单位为 μL/L |

## 目录结构

| 目录/文件 | 内容 |
|---|---|
| `main.py` | 单次问答与交互模式统一入口 |
| `vector_kb/` | 本地向量知识库、`cli.py`、切条语料与构建脚本；`knowledge.db` 为本地资产 |
| `data/corpus/` | DL/T 572、DL/T 722 的语料与判据表文本 |
| `data/rules/` | DL/T 572 第 7 章规则、DL/T 722 三比值判据 JSON |
| `data/samples/` | DGA 样本数据及单位统一结果 |
| `scripts/` | 样本处理、三比值判据、规则匹配、环境检查脚本 |
| `docs/` | 00~08 项目文档、状态总览、技术路线、评测方案、日志日程和验收记录 |
| `literature/` | 标准/论文 PDF，本地保留，版权与体积原因不入库 |
| `source_materials/` | 考核题目等原始材料，本地保留不入库 |
| `venv/` | 本地虚拟环境，不提交 |
| `submissions_pending_review/` | 待审核的成员提交文件 |

## 环境要求

- Python 3.10+（本机实测 3.14.7）
- Windows PowerShell
- Ollama，以及 embedding 模型 `bge-m3:latest`
- DeepSeek API Key，用于 `generate()` 的真实调用
- 当前原型使用 SQLite 作为本地向量存储；不再依赖 Chroma 运行时

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
```

确认 Ollama 与知识库：

```powershell
ollama list
python vector_kb\cli.py info
```

检索和生成：

```powershell
# 只检索：输出 doc_id / clause / title / text / page
python vector_kb\cli.py query "乙炔超标该怎么处理"

# 检索 + 生成：先打印来源，再输出带引用的回答
python vector_kb\cli.py ask "乙炔超标该怎么处理" --show-sources

# 统一入口：单次问答
python main.py "变压器油温异常升高"

# 统一入口：交互模式，输入 exit 退出
python main.py
```

如果 PowerShell 无法直接找到 `python`，统一使用：

```powershell
.\venv\Scripts\python.exe main.py "变压器油温异常升高"
```

## 当前验证状态

- `python vector_kb\cli.py info`：知识库 123 块，向量异常 0。
- 真机检索 `变压器油温异常升高`：命中 `DL/T 572-2021 第7.1.5条`，相似度约 0.7541。
- 真机检索 `乙炔超标该怎么处理`：命中 `DL/T 572-2021 第7.1.8条`、`DL/T 722-2014 第9.3.2-表4`、`DL/T 722-2014 第9.3.1-表3`。
- `main.py` 已实现单次问答和交互模式，并完成离线逻辑验证。
- DeepSeek 真实生成由使用者在本地接入 API Key 后运行，Key 不进入仓库。

## 已知限制

- `DL/T 572-2021` 参考库暂未记录页码，检索结果中可能显示“未记录”。
- 当前默认相似度阈值为 0.35；无关问题可能命中低相关条文，阶段二需要增加领域路由、重排或证据过滤。
- 当前 `vector_kb/cli.py` 同时承担 embedding、存储、检索、生成和 CLI 职责，属于原型技术债；阶段二计划拆分为 `embeddings.py`、`store.py`、`retrieval.py`、`generation.py`、`cli.py`。
- 标准正文、第三方原始数据、PDF、本地知识库文件和 `.env` 不入库；具体以 `NOTICE.md` 与 `.gitignore` 为准。

## 数据与版权说明

> 详见 [NOTICE.md](NOTICE.md)：本仓库不收录标准原文与第三方原始数据文件；判据整理与引用边界见该说明。

- `literature/`（标准/论文 PDF）与 `source_materials/` 仅本地使用，不提交。
- `vector_kb/knowledge.db`、第三方原始样本文件和 `.env` 不提交。
- 仓库内保留项目文档、代码、规则 JSON，以及经人工整理的判据表和元数据。

## 团队分工

- 队长：环境、工程与架构
- 成员2：领域知识、数据录入、规则与标准
- 成员3：文献综述、检索评测、文档与验收记录

## 文档入口

- 项目状态与下一步：[`docs/00_project_status.md`](docs/00_project_status.md)
- 开发日志与日程：[`docs/05_dev_log_and_schedule.md`](docs/05_dev_log_and_schedule.md)
- 切条与元数据规范：[`docs/07_chunking_and_metadata_spec.md`](docs/07_chunking_and_metadata_spec.md)
- 验收记录：[`docs/08_acceptance_record.md`](docs/08_acceptance_record.md)

## 最新提交

- `9d98336 feat: 新增端到端统一入口 main.py`

当前下一步：完成 10 条端到端验收用例与检索评测，随后进入阶段二模块化重构。
