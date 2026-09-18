# Pure Knowledge Base

纯检索知识库后端。它只负责按照调用方给定的 `domains` 和 `filters` 查询证据，不判断意图、不选择领域、不生成回答、不做引用校验。

调用边界：

```text
project_intent_router
→ domains + filters
→ pure_kb.search(...) / pure_kb.exact_lookup(...)
→ 返回证据
```

## 文件

```text
pure_kb/
├─ __init__.py
├─ api.py
├─ build_db.py
├─ embedding.py
├─ smoke_test.py
├─ store.py
├─ knowledge.db
└─ data/
   └─ knowledge.jsonl
```

`knowledge.db` 由 `data/knowledge.jsonl` 和 `build_db.py` 重建。

## 领域

| domain | 内容 | 记录数 |
|---|---|---:|
| `dga` | DGA 判据、三比值、故障映射和 DGA 规则 | 41 |
| `oil_temp` | 油温、冷却、负载和温度限值 | 61 |
| `safety` | 停运、保护和运行安全动作 | 26 |
| `equipment` | 设备、部件、故障模式和检查方向 | 10 |
| `dp` | 其他标准条文和通用规程规则 | 39 |
| `cases` | DGA 类比案例，仅作参考 | 21 |

## 记录字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `domain` | string | 检索领域 |
| `id` | string | 知识记录唯一标识 |
| `doc_id` | string/null | 标准或数据源标识 |
| `clause` | string/null | 条号或表号 |
| `title` | string | 标题 |
| `text` | string | 用于 Embedding 和返回的正文 |
| `citation` | string | 可展示引用 |
| `source` | string | 原始来源路径或数据源 |
| `page` | integer/null | 页码 |
| `metadata` | object | 结构化附加信息 |
| `review_status` | string | 审核状态 |

`search()` 结果会额外返回：

```text
score
retrieval_method = "vector"
```

## API

### list_domains()

```python
from pure_kb import list_domains

domains = list_domains()
```

### search(query, domains, filters=None, top_k=10)

`domains` 必填，知识库不会自动猜领域。该接口始终执行向量检索。

```python
from pure_kb import search

results = search(
    "乙炔超标如何判断",
    domains=["dga"],
    filters={"doc_id": "DL/T 722-2014"},
    top_k=10,
)
```

`filters` 支持字段：

```text
id
doc_id
clause
title
citation
source
page
review_status
metadata 中的任意键
```

### exact_lookup(filters, domains=None)

独立精确查询工具，不参与、也不替换 `search()` 的向量检索语义。

```python
from pure_kb import exact_lookup

results = exact_lookup(
    {
        "doc_id": "DL/T 722-2014",
        "clause": "9.3.1",
    },
    domains=["dga"],
)
```

当 `clause` 不带表号时，会匹配该条号及其表块。例如：

```text
clause=9.3.1
```

会匹配：

```text
9.3.1-表3
```

### stats()

```python
from pure_kb import stats

print(stats())
```

返回数据库路径、总数、各领域数量和异常向量数量。

## 重建数据库

环境要求：

```text
Python 3.10+
Ollama
bge-m3:latest
```

命令：

```powershell
python -m pure_kb.build_db `
  --jsonl pure_kb\data\knowledge.jsonl `
  --db pure_kb\knowledge.db `
  --model bge-m3:latest
```

## Smoke Test

```powershell
python -m pure_kb.smoke_test
```

验证：

- 六个领域存在
- `domains=["dga"]` 只返回 DGA
- `domains=["oil_temp"]` 只返回油温资料
- `domains=["safety"]` 只返回安全资料
- `filters={"doc_id": "DL/T 722-2014"}` 生效
- `exact_lookup` 的 Top-1 为 `9.3.1-表3`
- `search()` 始终标记为 `vector`，不会静默切换成精确查询