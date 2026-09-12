# 向量库语料说明

本目录存放**入库输入**（`cli.py ingest` 的输入），**不是源语料**。源语料在 `data/语料/`。

## 一、文件一览

| 文件 | 来源 | 是否入库(git) |
|---|---|---|
| `clauses.jsonl`（5 行） | 由 `data/语料/DLT-722-2014_判据表_blocks.jsonl` **增强导出**（增加 `chunk_id / citation / block_type`） | ✅ |
| `DLT-572-2021_clauses.jsonl`（118 行） | DL/T 572-2021 条款化切块结果 | ❌ 本地保留（版权原因） |

## 二、维护顺序（改数据时按此顺序，避免两处不一致）

1. **源头**：`data/规则库/rules_DLT722_dga_draft.json`（判据事实参数，已核验 v0.3）
2. **导出**：`data/语料/DLT-722-2014_判据表_结构化.txt` 与 `data/语料/DLT-722-2014_判据表_blocks.jsonl`
3. **增强**：本目录 `clauses.jsonl`（补 `chunk_id / citation / block_type`）
4. **入库**：
   ```powershell
   python cli.py ingest 语料/clauses.jsonl --collection normative --force --source 语料/clauses.jsonl
   ```

> **约定：以 `data/语料/` 版本为准。**
> 若两处内容不一致，先修改 `data/语料/DLT-722-2014_判据表_blocks.jsonl`（并回溯规则库），再重新导出本目录文件；**不要只改这里的副本**。

## 三、待补（审核意见第 4 条）

DL/T 722-2014 的**正文条款**（如 9.3.3 注意值应用原则、10.2.4 比值法应用原则、10.3 判断故障的步骤）尚未入库；`data/语料/DLT-722-2014_变压器油中溶解气体分析和判断导则_正文.txt` 中有全文可供切条。