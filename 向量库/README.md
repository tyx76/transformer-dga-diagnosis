# bge-m3 向量知识库（整改版）

## 基本信息
- 原始生成：2026-09-12 ｜ 整改：2026-09-12
- 向量模型：Ollama `bge-m3:latest`（1024 维，float32，L2 归一化，余弦相似度）
- 数据库文件：`knowledge.db`（SQLite，WAL 模式）
- 入库脚本：`cli.py`（仅标准库；真实入库需本机 Ollama）

## 数据统计
| 集合 | 文档 | 向量块 | 说明 |
|---|---:|---:|---|
| `normative` | 1 | 5 | DL/T 722-2014 判据表（表3/表4/表6/表7 + CO2/CO） |
| `reference` | 1 | 118 | DL/T 572-2021 条款化参考库（带 clause / citation） |
| 合计 | 2 | 123 | 全部 1024 维 |

## 目录内容
```text
向量库/
├─ knowledge.db                           SQLite 向量数据库（已 checkpoint，无 -wal/-shm）
├─ cli.py                                 入库 / 查看 脚本
├─ README.md
├─ materials/                             上传素材副本目录（预留）
└─ 语料/
   ├─ clauses.jsonl                       DL/T 722-2014 规范库输入（5 行）
   └─ DLT-572-2021_clauses.jsonl          DL/T 572-2021 参考库输入（118 行）
```

## 环境要求
- Python 3.10+（脚本仅用标准库）
- Ollama 服务，模型：`ollama pull bge-m3`（默认地址 `http://localhost:11434`）

## 重建命令
```powershell
# 722 规范库
python cli.py ingest 语料/clauses.jsonl --collection normative --force --source 语料/clauses.jsonl

# 572 参考库
python cli.py ingest 语料/DLT-572-2021_clauses.jsonl --collection reference --force --source 语料/DLT-572-2021_clauses.jsonl

# 查看统计（文档数 / 块数 / 向量异常检查）
python cli.py info
```
> 无 Ollama 时可用 `--dry-run` 做结构自测（写零向量，仅供校验，不可用于检索）。

## 打包 / 备份注意
- 本库使用 WAL 模式：**复制前先关闭程序**，或执行 `PRAGMA wal_checkpoint(TRUNCATE);`，避免 `-wal` / `-shm` 残留或数据不完整。
- 本整改包已做 checkpoint + VACUUM，**不含 `-wal` / `-shm`**。
- `documents.source` 统一记为**相对路径**（`语料/...`），不写入个人机器绝对路径。

## 本次整改记录（对应审核意见 1/2/3）
1. **补齐包内容**：加入两份输入 JSONL（5 + 118 行，从库中导出、与库内容一一对应）与入库脚本 `cli.py`；README 的重建命令与之对齐。
2. **清理 WAL/SHM**：执行 `wal_checkpoint(TRUNCATE)` + `VACUUM`，重新打包不含 `-wal` / `-shm`。
3. **去掉本机路径**：`documents.source` 由 `D:\project\项目八\...` 改为 `语料/...`。

## 仍待处理（审核意见 4/5/6，由提交人完成）
4. 补 722 正文条款块（如 9.3.3 注意值应用原则、10.2.4 比值法应用原则、10.3 判断故障的步骤）。
5. 572 表格结构化（表1 顶层油温限值、表2 检测周期等）——属阶段二语料待办。
6. 附一次真实检索结果（问「乙炔超标该怎么处理」，给出 Top-k 与条号），需本机 Ollama 运行。
## 语料来源与维护顺序
数据流：`data/规则库/`（判据事实）→ `data/语料/`（源语料与导出）→ 本目录 `语料/*.jsonl`（入库输入）→ `knowledge.db`（向量库）。

> **以 `data/语料/` 版本为准**；两处不一致时先改 data 版再重新导出。详见 `语料/README.md`。