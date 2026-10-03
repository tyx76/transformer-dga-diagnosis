# Plant Knowledge Base

> 项目接入状态：作为当前默认独立知识库后端接入 `vector_kb/knowledge_base_adapter.py`；默认只启用已核验记录，OCR 未复核数据需显式开启。

纯检索知识后端，数据来自 `知识库素材OCR` 附件。该包只负责检索，不负责意图识别、领域选择、融合、生成或引用校验。

## 领域

- `dga`：变压器油中气体和油色谱相关内容
- `oil_temp`：油温、润滑油、轴承温度、冷却和负荷
- `safety`：保护、停运、跳闸、风险和事故措施
- `equipment`：锅炉、汽轮机、发电机及主要部件
- `dp`：标准条文、运行规程、检修规程和导则
- `cases`：故障案例、异常分析和缺陷处理

## 数据统计

| domain | 数据量 | 主要来源 |
|---|---:|---|
| `dga` | 41 | 已核验的变压器 DGA 判据、规则和案例 |
| `oil_temp` | 1028 | OCR 文档中的油温、冷却、润滑油和负荷内容 |
| `safety` | 251 | 安全操作、保护、停运和事故措施 |
| `equipment` | 843 | 锅炉、汽轮机、发电机及主要部件 |
| `dp` | 1250 | 运行规程、检修规程、标准和导则条款 |
| `cases` | 387 | 故障案例、异常分析和缺陷处理 |

附件 OCR 语料本身几乎没有真正的变压器 DGA 内容，因此 `dga` 领域使用已核验的变压器 DGA 数据；其余领域均来自 `知识库素材OCR`。所有记录均标记为 `ocr_unreviewed`，除 DGA 来源记录外，尚未逐条人工复核。
## 接口

```python
from plant_kb import list_domains, search, exact_lookup, stats
```

`search(query, domains, filters=None, top_k=10)` 必须显式传入 `domains`。该接口只执行向量检索。

`exact_lookup(filters, domains=None)` 是独立精确查询接口。

## 记录字段

```text
domain / id / doc_id / clause / title / text
citation / source / page / metadata / review_status
```

## 重建数据库

```powershell
python -m plant_kb.build_db `
  --jsonl plant_kb\data\knowledge.jsonl `
  --db plant_kb\knowledge.db `
  --model bge-m3:latest
```

## Smoke Test

```powershell
python -B -m plant_kb.smoke_test
```