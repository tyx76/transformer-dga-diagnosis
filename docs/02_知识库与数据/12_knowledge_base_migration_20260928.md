# 知识库迁移记录：pure_kb → plant_kb（2026-09-28）

> **当前项目口径（2026-10-03）**：项目主对象已转为“通用电厂设备故障诊断”，覆盖锅炉、汽轮机、发电机及辅机。DGA 仅保留为可选专项、历史技术资产或备用能力，不再作为主链路范围；本文如涉及 DGA，请按专项资料阅读。


## 1. 迁移结论

新提交包 `plant_kb_submission_20260928.zip` 已作为项目根目录下的独立知识库包：

`D:\社团考题第八\plant_kb\`

原纯知识库：

`D:\社团考题第八\pure_kb\`

已完整复制到本地备份：

`D:\社团考题第八\backups\pure_kb_20260928\`

默认主链路以 `plant_kb` 为主知识库，`pure_kb` 不再作为首选。`vector_kb/knowledge_base_adapter.py` 默认导入 `plant_kb`；当新库没有可用结果时，默认允许旧库做空结果兜底，旧库不会优先参与正常命中。

```powershell
# 默认：plant_kb
$env:KB_BACKEND = "plant_kb"

# 仅用于回滚：pure_kb
$env:KB_BACKEND = "pure_kb"
```

## 2. plant_kb 数据概况

| domain | 数量 | 说明 |
|---|---:|---|
| `dga` | 41 | 已核验的变压器 DGA 判据、规则和案例 |
| `oil_temp` | 1028 | OCR 文档中的油温、冷却、润滑油和负荷内容 |
| `safety` | 251 | 安全操作、保护、停运和事故措施 |
| `equipment` | 843 | 锅炉、汽轮机、发电机及主要部件 |
| `dp` | 1250 | 标准条文、运行规程、检修规程和导则 |
| `cases` | 387 | 故障案例、异常分析和缺陷处理 |
| 合计 | 3800 | 数据库坏向量数：0 |

烟测结果：

```text
SMOKE_OK
total=3800
bad_vectors=0
```

适配器 DGA 烟测“乙炔超标怎么处理”返回了：

- `9.3.3`：注意值应用原则
- `9.3.1-表3`：乙炔 C2H2 注意值
- `9.3.2-表4`：产气速率注意值

## 3. 接入边界

- `plant_kb` 只负责按照调用方传入的 `domains/filters` 做向量检索，不负责意图识别、领域选择、融合、生成和引用校验。
- 现有主链路仍由 `vector_kb/retrieval_router.py` 负责意图路由和 hybrid + KB 融合。
- `dp` 领域仍由 `vector_kb/knowledge_base_adapter.py` 过滤，不进入最终生成上下文。
- `plant_kb` 默认只接受 `review_status` 非 `ocr_unreviewed` 的记录；全量 OCR 接入需显式设置 `KB_INCLUDE_UNREVIEWED=true`。
- 当 `plant_kb` 已核验结果为空时，适配器默认启用 `KB_BACKUP_FALLBACK=true`，调用旧 `pure_kb` 作为兜底；旧库仍不是主路径。
- `vector_kb/knowledge.db` 和 BM25 索引仍服务 hybrid 检索，不属于本次替换的 `pure_kb` 备份范围。
- `plant_kb/knowledge.db` 和 `plant_kb/data/knowledge.jsonl` 作为本地大文件保留，不提交 Git；`backups/` 也不提交 Git。

## 4. 质量风险与待办

- 除 DGA 来源记录外，`plant_kb` 的 OCR 记录标记为 `ocr_unreviewed`，尚未逐条人工复核。
- `equipment` 中包含锅炉、汽轮机、发电机等非主变设备，接入后必须依赖意图路由和 `doc_id/domain` 过滤控制范围，不能把全部通用设备资料当作变压器依据。
- 需要对新 KB 跑现有 50 条评测、真实生成引用校验和拒答测试，重点观察：
  - DGA 术语命中是否保持；
  - 油温、安全意图是否被通用设备资料挤占；
  - OCR 条文进入回答时是否有可靠条号和页码；
  - 引用校验是否能把无条号/无文档来源的片段拦住。
- 当前完成了接入和烟测。50 条离线用例（关闭 LLM）对比：旧 `pure_kb` 为 76.92%；`plant_kb` 只启用已核验记录为 66.67%；`plant_kb` 已核验记录 + 旧库空结果兜底为 76.92%。因此当前默认采用“新库优先 + 旧库空结果兜底”。
- 正式真实生成评测结果出来前，不建议删除 `pure_kb` 备份，也不建议直接开启未复核 OCR 全量数据。
