# 检索、融合与生成模块说明

> 更新：2026-09-18 ｜ 当前主入口：项目根目录 `main.py`

## 1. 当前数据资产

| 项目 | 内容 |
|---|---|
| 向量库 | `knowledge.db`，SQLite，123 块 = normative 5 + reference 118 |
| Embedding | Ollama `bge-m3:latest`，1024 维，L2 归一化 |
| 722 判据 | `corpus/clauses.jsonl`，5 条 |
| 572 运维条款 | `corpus/DLT-572-2021_clauses.jsonl`，118 条，本地不入库 |
| 统一语料 | `../data/corpus/clauses.jsonl`，本地生成 123 条 |
| BM25 索引 | `bm25_index.pkl`，v2，本地生成不入库 |

统一语料生成：

```powershell
python scripts\build_unified_corpus.py
```

## 2. 当前模块

| 文件 | 职责 |
|---|---|
| `embeddings.py` | Ollama embedding 调用 |
| `store.py` | SQLite 连接和表结构 |
| `retrieval.py` | 向量加载、余弦相似度和 `retrieve()`；默认阈值 `0.45` |
| `bm25_retriever.py` | jieba 分词、领域词典、BM25、索引缓存和自动重建 |
| `rrf_fusion.py` | 倒数排序融合，按条号去重和累加 |
| `hybrid_retriever.py` | 领域过滤 + 向量 + BM25 + RRF |
| `domain_guard.py` | 规则版领域与明显无关意图过滤 |
| `generation.py` | 上下文拼接、引用格式和 DeepSeek `generate()` |
| `citation_verifier.py` | 引用存在性校验、重写提示和删除无效句 |
| `cli.py` | 保留的 `ingest / info / query / ask` 工具，当前仍为纯向量链路 |

## 3. 目录内容

```text
vector_kb/
├─ knowledge.db                         SQLite 向量库（本地资产，不入库）
├─ bm25_index.pkl                       BM25 缓存（本地生成，不入库）
├─ main.py                              不在本目录；主入口位于项目根目录
├─ embeddings.py
├─ store.py
├─ retrieval.py
├─ bm25_retriever.py
├─ rrf_fusion.py
├─ hybrid_retriever.py
├─ domain_guard.py
├─ generation.py
├─ citation_verifier.py
├─ cli.py
├─ corpus/
│  ├─ clauses.jsonl                     DL/T 722 判据（5 条）
│  ├─ DLT-572-2021_clauses.jsonl        DL/T 572 条款（118 条，本地）
│  └─ README.md
└─ materials/
```

## 4. 当前主链路

```text
main.py
  → domain_guard.is_in_domain()
  → retrieval.retrieve(top_k=10, min_score=0.45)
  → bm25_retriever.bm25_retrieve(top_k=10)
  → rrf_fusion.rrf_fusion(top_k=5)
  → generation.generate()
  → citation_verifier.verify_citations()
  → 最多重写 2 次，仍失败则删除无依据句
```

`hybrid_retrieve()` 默认 `top_k=3`，但当前 `main.py` 显式请求 `top_k=5`。

## 5. 常用命令

### 当前主链路

```powershell
# 混合检索 + 生成 + 引用校验
python main.py "变压器油温过高怎么处理"

# 输出各阶段条号和分数摘要
python main.py --debug "变压器油温过高怎么处理"

# 交互模式
python main.py
```

### 纯向量调试工具

```powershell
# 查看知识库统计
python vector_kb\cli.py info

# 纯向量检索 Top-3
python vector_kb\cli.py query "乙炔超标该怎么处理"

# 纯向量检索 + 生成
python vector_kb\cli.py ask "乙炔超标该怎么处理" --show-sources
```

注意：`cli.py ask` 仍然只调用 `retrieve()`，不调用 `hybrid_retrieve()` 和 `verify_citations()`；当前正式主链路是根目录 `main.py`。

### 库函数调用

```python
from vector_kb.retrieval import retrieve
from vector_kb.bm25_retriever import bm25_retrieve
from vector_kb.rrf_fusion import rrf_fusion
from vector_kb.hybrid_retriever import hybrid_retrieve
from vector_kb.generation import generate
from vector_kb.citation_verifier import verify_citations
```

## 6. 返回字段

纯向量与 BM25 结果：

```text
doc_id / clause / title / text / page / score
```

RRF 融合结果：

```text
doc_id / clause / title / text / page / rrf_score
```

纯向量 `retrieve()` 额外带 `citation` 字段。

## 7. 数据与索引维护

- BM25 优先读取 `data/corpus/clauses.jsonl`。
- 若统一文件不存在，自动合并：
  - `vector_kb/corpus/clauses.jsonl`
  - `vector_kb/corpus/DLT-572-2021_clauses.jsonl`
- BM25 索引记录语料路径、大小和修改时间；源语料变化后自动重建。
- 索引版本当前为 `2`。
- 向量库仍使用原 123 块 SQLite 数据，统一语料与原库内容一致。

## 8. 已知问题

- 统一语料后，DGA 查询可能混入 DL/T 572 运维条款，BM25 存在跨文档域干扰。
- 当前 RRF 两路等权，尚未根据问题意图动态调整。
- 当前领域判断为规则方案，后续计划引入 C6 FaultSeer 的 Agentic 意图判断。
- 油温问题已经能召回 `7.1.5/7.1.6/7.1.8`，但生成器仍可能因处置流程不完整而拒答，提示词待优化。
- 572 页码暂未记录；722 `9.3.3 / 10.2.4 / 10.3` 正文条款待补。
- `cli.py query/ask` 未同步混合检索和引用校验，保留用于纯向量对比。

## 9. 环境与版权

- Python 3.10+；本机实测 3.14.7。
- 依赖：`jieba`、`rank-bm25`、Ollama、DeepSeek API Key。
- `knowledge.db`、`bm25_index.pkl`、统一语料和 572 原条款文件均为本地生成/本地资产，不提交 Git。