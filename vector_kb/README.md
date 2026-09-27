# vector_kb：检索、融合与生成模块

> 文档状态：现行｜更新：2026-09-27
> 当前主入口：项目根目录 `main.py`
> 本目录同时保留纯向量 CLI，用于调试和消融，不代表正式问答链路。

## 1. 数据资产

| 项目 | 内容 |
|---|---|
| 向量库 | `knowledge.db`，SQLite，123 块 = normative 5 + reference 118 |
| Embedding | Ollama `bge-m3:latest`，1024 维，L2 归一化 |
| 722 判据 | `corpus/clauses.jsonl`，5 条 |
| 572 条款 | `corpus/DLT-572-2021_clauses.jsonl`，118 条，本地保留 |
| 统一语料 | `../data/corpus/clauses.jsonl`，本地生成 123 条 |
| BM25 索引 | `bm25_index.pkl`，版本 v2，本地生成 |
| 纯知识库 | `../pure_kb/`，198 条、六领域 |

生成统一语料：

```powershell
python scripts\build_unified_corpus.py
```

## 2. 模块职责

| 文件 | 职责 |
|---|---|
| `embeddings.py` | Ollama embedding 调用与 L2 归一化 |
| `store.py` | SQLite 连接和表结构 |
| `retrieval.py` | 向量加载、余弦相似度、`retrieve()`，默认阈值 0.45 |
| `bm25_retriever.py` | jieba 分词、领域词典、BM25、索引缓存和自动重建 |
| `rrf_fusion.py` | 向量与 BM25 的倒数排序融合 |
| `hybrid_retriever.py` | 领域过滤 + 向量 + BM25 + RRF |
| `domain_guard.py` | 规则版领域和明显无关问题过滤 |
| `intent_classifier.py` | 规则优先、LLM 兜底、多意图 |
| `intent_router.py` | intent → domains/filters/mode |
| `knowledge_base_adapter.py` | pure_kb 字段归一化、dp 过滤、去重和二次 RRF |
| `retrieval_router.py` | hybrid + pure_kb 检索调度 |
| `generation.py` | 上下文拼接、引用格式和 DeepSeek 调用 |
| `citation_verifier.py` | 引用存在性校验、重写提示和无效句删除 |
| `cli.py` | `ingest/info/query/ask`，纯向量管理工具 |

## 3. 目录

```text
vector_kb/
├─ knowledge.db                         SQLite 向量库（本地，不提交）
├─ bm25_index.pkl                       BM25 索引（本地，不提交）
├─ embeddings.py
├─ store.py
├─ retrieval.py
├─ bm25_retriever.py
├─ rrf_fusion.py
├─ hybrid_retriever.py
├─ domain_guard.py
├─ intent_classifier.py
├─ intent_router.py
├─ knowledge_base_adapter.py
├─ retrieval_router.py
├─ generation.py
├─ citation_verifier.py
├─ cli.py
└─ corpus/
   ├─ README.md
   ├─ clauses.jsonl                     DL/T 722 判据 5 条
   └─ DLT-572-2021_clauses.jsonl        DL/T 572 条款 118 条（本地）
```

## 4. 当前链路

```text
main.py
  → route_and_retrieve
      → classify_intent
      → route_intent
      → hybrid_retrieve（向量 + BM25 + RRF）
      → pure_kb.search（domains + filters）
      → merge_with_hybrid（二次 RRF）
  → generate
  → verify_citations
  → 最多重写 2 次
  → 删除无依据句或拒答
```

`hybrid_retrieve()` 默认 `top_k=3`、`candidate_k=10`、`rrf_k=60`；路由和 `main.py` 显式使用更大的候选池并最终取 Top-5。

## 5. 常用命令

### 5.1 当前主链路

```powershell
python main.py "变压器油温过高怎么处理"
python main.py --debug "变压器油温过高怎么处理"
python main.py
```

### 5.2 纯向量调试

```powershell
python vector_kb\cli.py info
python vector_kb\cli.py query "乙炔超标怎么处理"
python vector_kb\cli.py ask "乙炔超标怎么处理" --show-sources
```

注意：`cli.py ask` 只调用 `retrieve()`，不调用 hybrid、pure_kb、路由或引用校验。

### 5.3 库函数

```python
from vector_kb.retrieval import retrieve
from vector_kb.bm25_retriever import bm25_retrieve
from vector_kb.rrf_fusion import rrf_fusion
from vector_kb.hybrid_retriever import hybrid_retrieve
from vector_kb.generation import generate
from vector_kb.citation_verifier import verify_citations
from vector_kb.retrieval_router import route_and_retrieve
```

## 6. 返回字段

纯向量和 BM25：

```text
doc_id / clause / title / text / page / score
```

RRF：

```text
doc_id / clause / title / text / page / rrf_score
```

pure_kb 适配后统一为：

```text
doc_id / clause / title / text / page / citation / score
```

## 7. 数据与索引维护

- BM25 优先读取 `data/corpus/clauses.jsonl`。
- 统一文件不存在时，兼容合并：
  - `vector_kb/corpus/clauses.jsonl`；
  - `vector_kb/corpus/DLT-572-2021_clauses.jsonl`。
- 索引记录源文件路径、大小和修改时间，源语料变化后自动重建。
- 重建向量库使用 `vector_kb/cli.py ingest`，详见根 README。
- 公开仓库只能重建 722 判据子集，完整 123 块需要本地合法 572 条款。

## 8. 当前评测结论

- 50 条用例中 39 条可评，Top-5 命中 30 条，命中率 76.92%；
- 四组 hybrid/pure_kb 权重 `1.0/1.0、1.0/1.2、1.0/1.5、1.0/0.8` 指标持平；
- 当前保留 `1.0/1.0`，瓶颈在排序层，不在召回层；
- 下一步优先查询改写和 Reranker，而非无依据扩大 Top-K。

复现：

```powershell
python scripts\tune_rrf_weights.py
python scripts\shadow_ab_test.py
python scripts\run_regression.py
```

## 9. 已知问题

- 数值 DGA 规则尚未接入 `main.py`；
- 目标条文可能已召回但未进入最终 Top-5；
- pure_kb 的 `cases` 只作类比证据，不能替代 standards/rules/safety；
- 572 页码暂未记录；
- 722 `9.3.3 / 10.2.4 / 10.3` 正文原则条款待补；
- `cli.py query/ask` 是纯向量工具，不包含正式主链路能力；
- C6 FaultSeer 式完整 Agentic 路由尚未实现。

## 10. 环境与版权

- Python 3.10+；开发机实测 3.14.7。
- 运行时依赖：Ollama、`bge-m3:latest`、jieba、rank-bm25、DeepSeek API。
- `knowledge.db`、`bm25_index.pkl`、572 条款和统一语料均为本地资产，不提交 Git。