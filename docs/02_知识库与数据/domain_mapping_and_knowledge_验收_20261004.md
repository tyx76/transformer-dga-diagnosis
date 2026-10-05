# domain_mapping_and_knowledge_20261004 验收

> 日期：2026-10-05  
> 包路径：`submissions_pending_review/domain_mapping_and_knowledge_20261004.zip`  
> 结论：**内容与 ID 一致性通过；当前目录/字段格式不能直接无缝替换主知识库，需要适配后再接入。**

## 1. 文件清单

| 文件 | 大小 |
|---|---:|
| `plant_kb/knowledge_domain.db` | 393,793,536 bytes |
| `plant_kb/data/knowledge_domain.jsonl` | 352,481,491 bytes |
| `plant_kb/data/lightweight_metadata.jsonl` | 12,330,401 bytes |
| `plant_kb/data/domain_mapping.jsonl` | 10,863,213 bytes |
| `plant_kb/data/domain_migration_manifest.json` | 1,010 bytes |

## 2. 一致性验收

| 检查项 | 结果 | 判定 |
|---|---:|---|
| Manifest 记录数 | 15,188 | PASS |
| `knowledge_domain.jsonl` 记录数 | 15,188 | PASS |
| `domain_mapping.jsonl` 记录数 | 15,188 | PASS |
| `lightweight_metadata.jsonl` 记录数 | 15,188 | PASS |
| JSONL 解析错误 | 0 | PASS |
| `id` 重复 | 0 | PASS |
| `chunk_id` 重复 | 0 | PASS |
| domain_mapping 覆盖 knowledge id | 缺失 0、额外 0 | PASS |
| lightweight 覆盖 knowledge id | 缺失 0、额外 0 | PASS |
| SQLite `knowledge` 表记录数 | 15,188 | PASS |
| SQLite 对 knowledge id 覆盖 | 15,188/15,188，缺失 0 | PASS |
| mapping 与 knowledge 的 domain_primary | 不一致 0 | PASS |
| mapping 与 knowledge 的 equipment_domains | 不一致 0 | PASS |
| mapping 与 knowledge 的 source_type | 不一致 0 | PASS |
| mapping 与 knowledge 的 citation_eligible | 不一致 0 | PASS |

## 3. 域分布

以下为 `knowledge_domain.jsonl` 实际 `domain` 分布，与 SQLite、mapping、manifest 对账一致。

| 域 | 记录数 |
|---|---:|
| turbine | 3,230 |
| generator_electrical | 4,343 |
| auxiliary | 1,378 |
| boiler | 2,864 |
| transformer_dga | 544 |
| standards_safety | 1,748 |
| fault_cases | 1,081 |
| **合计** | **15,188** |

Manifest 中的 `domain_primary_counts` 与 `equipment_domains_counts` 也已对账一致：

| 指标 | Manifest | 实际 |
|---|---:|---:|
| primary coverage | 1.0 | 1.0 |
| equipment domains coverage | 1.0 | 1.0 |
| source_type coverage | 1.0 | 1.0 |
| specialties coverage | 0.8744403476428759 | 0.874440 |
| citation_eligible coverage | 0.9431129839346852 | 0.943113 |

## 4. 审查状态

| 指标 | Manifest |
|---|---:|
| domain_review_status=pending | 11,765 |
| domain_review_status=reviewed | 3,423 |
| citable_review_status=reviewed | 10 |
| citable_review_status=pending | 15,178 |

说明：`citation_eligible_coverage` 较高不等于人工复核完成；绝大多数记录的 citable review 仍为 `pending`。

## 5. 主要风险

1. **不能直接替换当前主路径**
   - 当前代码期望：`knowledge/plant_kb/index/knowledge.db`
   - 包内实际：`plant_kb/knowledge_domain.db`
   - 当前代码期望：`knowledge/plant_kb/data/knowledge.jsonl`
   - 包内实际：`plant_kb/data/knowledge_domain.jsonl`

2. **`lightweight_metadata.jsonl` 字段不兼容当前 `_load_scope_metadata()`**
   - 当前加载器按 `(doc_id, clause)` 建 key。
   - 包内 lightweight metadata 只有 `id/domain/domain_primary/equipment_domains/.../source_file`，没有 `doc_id`、`clause`、`title`、`citation`。
   - 若直接放入 `index/lightweight_metadata.jsonl`，所有记录会塌缩成空 key，scope 元数据不可用。

3. **包内没有 BM25 索引**
   - 包中未包含 `bm25_index.pkl`。
   - 若替换 `knowledge_domain.jsonl`，现有 BM25 索引的语料 hash/记录数可能不匹配，需要重新构建索引。

4. **条号完整性风险**
   - `knowledge_domain.jsonl` 中缺少 `doc_id` 或 `clause` 的记录：1,362 条。
   - `(doc_id, clause)` 重复组合：1,479 组；去重必须使用 `(doc_id, clause)` 或 `chunk_id`，不能只按 clause。

## 6. SHA256

| 文件 | SHA256 |
|---|---|
| zip | `ad954ec02f1f1d2de2d240a5903a052f32b7ba6b72d4e754d9cae6b87af23da5` |
| knowledge_domain.db | `b2bc94dee36a9b91b4d4385f47d6e1bdefad2ff192496eaa05c8ab528ddc24dc` |
| knowledge_domain.jsonl | `f1a97189661b363206489f0f45c6f358ac9666c368fc444512e2a4d540e5ec3d` |
| domain_mapping.jsonl | `929df7b4685938fcaa00e7a27f4df25ad0e40074ca45d3b3682ee63c85eb6d01` |
| lightweight_metadata.jsonl | `1734a6248360dd5f9693b5084d30e8b01864faa3a222bbe086eaec311a305bd2` |

## 7. 验收判定

| 维度 | 判定 |
|---|---|
| 记录数量 | PASS |
| ID 覆盖 | PASS |
| domain/mapping 一致性 | PASS |
| SQLite 一致性 | PASS |
| JSONL 格式 | PASS |
| 直接替换主路径 | FAIL / 需适配 |
| BM25 完整性 | 需重建 |
| 人工复核完成度 | 不足，需确认是否为预期状态 |

建议下一步：先做适配层，将 `knowledge_domain.db` 和 `knowledge_domain.jsonl` 转换成当前主路径命名；同时生成兼容旧格式的 `index/lightweight_metadata.jsonl`，再重建 BM25 索引，最后跑 138 题回归。
