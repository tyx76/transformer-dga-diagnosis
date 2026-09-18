# 向量库语料说明

本目录存放**入库输入**（`cli.py ingest` 的输入），**不是源语料**。源语料在 `data/corpus/`。

## 一、文件一览

| 文件 | 来源 | 是否入库(git) |
|---|---|---|
| `clauses.jsonl`（5 行） | 由 `data/corpus/DLT-722-2014_criteria_blocks.jsonl` **增强导出**（增加 `chunk_id / citation / block_type`） | ✅ |
| `DLT-572-2021_clauses.jsonl`（118 行） | DL/T 572-2021 条款化切块结果 | ❌ 本地保留（版权原因） |

## 二、维护顺序（改数据时按此顺序，避免两处不一致）

1. **源头**：`data/rules/rules_DLT722_dga_draft.json`（判据事实参数，已核验 v0.3）
2. **导出**：`data/corpus/DLT-722-2014_criteria_tables.txt` 与 `data/corpus/DLT-722-2014_criteria_blocks.jsonl`
3. **增强**：本目录 `clauses.jsonl`（补 `chunk_id / citation / block_type`）
4. **入库**：
   ```powershell
   python cli.py ingest 语料/clauses.jsonl --collection normative --force --source 语料/clauses.jsonl
   ```

> **约定：以 `data/corpus/` 版本为准。**
> 若两处内容不一致，先修改 `data/corpus/DLT-722-2014_criteria_blocks.jsonl`（并回溯规则库），再重新导出本目录文件；**不要只改这里的副本**。

## 三、待补（审核意见第 4 条）

DL/T 722-2014 的**正文条款**（如 9.3.3 注意值应用原则、10.2.4 比值法应用原则、10.3 判断故障的步骤）尚未入库；`data/corpus/DLT-722-2014_body.txt` 中有全文可供切条。
## 四、统一语料（2026-09-18）

- 统一输出：`data/corpus/clauses.jsonl`。
- 生成方式：
  ```powershell
  python scripts/build_unified_corpus.py
  ```
- 当前预期规模：722 判据 5 条 + 572 运行维护 118 条 = 123 条。
- 该文件包含 DL/T 572 标准正文，按版权约定本地生成、不提交 Git。
- BM25 优先读取统一文件；统一文件不存在时，兼容合并本目录两份 JSONL。