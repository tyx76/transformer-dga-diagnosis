# vector_kb/corpus：向量库输入说明

> **当前项目口径（2026-10-03）**：项目主对象已转为“通用电厂设备故障诊断”，覆盖锅炉、汽轮机、发电机及辅机。DGA 仅保留为可选专项、历史技术资产或备用能力，不再作为主链路范围；本文如涉及 DGA，请按专项资料阅读。


> 文档状态：现行｜更新：2026-09-27
> 本目录保存向量库和 BM25 的入库输入，源语料事实来源仍以 `data/` 为准。
> 标准正文和含版权条款文件只在本机保留，不进入公开仓库。

## 1. 文件一览

| 文件 | 来源 | 是否提交 |
|---|---|---|
| `clauses.jsonl`（5 行） | 由 `data/corpus/DLT-722-2014_criteria_blocks.jsonl` 增强导出，补充 `chunk_id / citation / block_type` | 是 |
| `DLT-572-2021_clauses.jsonl`（118 行） | DL/T 572-2021 条款化切块结果 | 否，本地保留 |

## 2. 维护顺序

1. 核对源标准与规则状态；
2. 更新 `data/rules/rules_DLT722_dga_draft.json` 和 `data/corpus/` 中的导出文件；
3. 更新本目录 722 增强 JSONL；
4. 在合法材料基础上更新本地 572 JSONL；
5. 生成统一语料供 BM25 使用：

```powershell
python scripts\build_unified_corpus.py
```

6. 重建或更新向量库：

```powershell
python vector_kb\cli.py ingest vector_kb\corpus\clauses.jsonl `
  --collection normative `
  --doc-id "DL/T 722-2014" `
  --force `
  --source "vector_kb/corpus/clauses.jsonl"

python vector_kb\cli.py ingest vector_kb\corpus\DLT-572-2021_clauses.jsonl `
  --collection reference `
  --doc-id "DL/T 572-2021" `
  --force `
  --source "vector_kb/corpus/DLT-572-2021_clauses.jsonl"
```

7. 核对：

```powershell
python vector_kb\cli.py info
```

预期总块数为 123，向量异常块为 0。

## 3. 数据一致性约定

- 722 判据以 `data/corpus/DLT-722-2014_criteria_blocks.jsonl` 为准；
- 不要只修改本目录副本而不回写源头；
- 统一语料预期 722 判据 5 条 + 572 条款 118 条 = 123 条；
- BM25 优先读取 `data/corpus/clauses.jsonl`，文件缺失时才回退到本目录两份 JSONL；
- 修改条号、页码或文本后必须重新运行回归和数据一致性检查。

## 4. 待补事项

- 722 正文原则条款 `9.3.3 / 10.2.4 / 10.3`；
- 572 页码映射；
- 572 表格结构化；
- 合法取得后的 GB 26860-2011 安全条款摘录。

> 公开仓库只能独立重建 722 的 5 条事实性判据子集；完整 123 块知识库需要本地合法 572 条款文件。
