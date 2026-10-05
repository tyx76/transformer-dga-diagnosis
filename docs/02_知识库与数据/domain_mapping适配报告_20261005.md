# domain_mapping 适配报告

> 日期：2026-10-05
> 输入包：`domain_mapping_and_knowledge_20261004.zip`
> 向量：复用包内 DB 向量，不重新生成。

## 适配结果

| 项目 | 结果 |
|---|---|
| knowledge.jsonl | 15188 条 |
| lightweight_metadata | 15188 条 |
| DB 记录/向量 | 15188/15188 |
| DB 维度 | {1024: 15188} |
| BM25 文档数 | 15188 |
| BM25 平均文档长度 | 1717.814 |
| BM25 分片 | {'transformer_dga': 544, 'turbine': 8105, 'generator_electrical': 5223, 'auxiliary': 6895, 'boiler': 6338, 'fault_cases': 1081, 'standards_safety': 1774} |

## 文件位置

- `knowledge/plant_kb/index/knowledge.db`
- `knowledge/plant_kb/data/knowledge.jsonl`
- `knowledge/plant_kb/index/lightweight_metadata.jsonl`
- `knowledge/plant_kb/index/bm25_index.pkl`
- `knowledge/plant_kb/index/bm25_manifest.json`

## 适配说明

- `chunk_id` 使用原始 `id`。
- `domain_alt` 以逗号包裹字符串保存，支持多备选域。
- DB 直接复用包内 vector/dim，仅补充 domain_alt/citation 字段。
- BM25 按 equipment_domains 复制到备选域分片。
- 原包和适配前主路径均已保留备份。

## 验收结果

| 验收项 | 结果 | 判定 |
|---|---|---|
| knowledge.jsonl 记录数 | 15,188 | PASS |
| chunk_id / domain_alt | 15,188 / 10,016 条非空 | PASS |
| lightweight `doc_id` / `clause` | 15,188 / 15,188 | PASS |
| DB 记录 / 向量 | 15,188 / 15,188 | PASS |
| DB 维度 | 全部 1024 | PASS |
| BM25 全量索引 | 15,188 docs，`plant-bm25-v2` | PASS |
| smoke 回归 | 8/8 | PASS |
| core 回归 | 24/24 | PASS |
| full 回归 | 138/138 引用校验通过 | PASS |

## 138 题命中率变化

| 指标 | 适配前 | 适配后 | 变化 |
|---|---:|---:|---:|
| Top-5 来源命中 | 56/116（48.28%） | 58/116（50.00%） | +2 题，+1.72pp |
| Top-5 条号命中 | 36/73 | 24/73 | -12 题 |
| 引用校验通过 | 136/138（98.55%） | 138/138（100.00%） | +2 题 |
| 拒答率 | 0.00% | 0.00% | 持平 |
| 参考答案覆盖率 | 56.97% | 54.46% | -2.51pp |
| 平均耗时 | 9731.24 ms | 12039.34 ms | +2308.10 ms |

说明：来源命中率有提升，但条号精确命中和参考答案覆盖率下降，说明适配后的 domain_alt/分片扩展改善了来源覆盖，但排序和证据选择仍需继续优化。

## 备份

适配前主路径备份：`backups/plant_kb_before_domain_adapt_20261005/`

原始提交包保留在：`submissions_pending_review/_unpacked_domain_mapping_20261004/`
