# 文档导航与维护规范

> 文档状态：现行导航｜整理更新：2026-09-27。

- 整理日期：2026-09-27
- 适用范围：仓库内可提交的正式文档、调研归档、评测证据和阅读笔记
- 单一事实源：项目当前实现与进度以 `docs/00_project_status.md` 和根目录 `README.md` 为准

## 1. 推荐阅读顺序

| 顺序 | 文档 | 用途 |
|---:|---|---|
| 1 | [根 README](../README.md) | 项目定位、运行方式、当前能力与限制 |
| 2 | [项目状态](00_project_status.md) | 当前阶段、资产、验收、待办和远程状态 |
| 3 | [实现方案](09_implementation_plan.md) | 当前系统分层、主链路和后续路线 |
| 4 | [验收记录](08_acceptance_record.md) | 检索、生成、引用、路由和评测证据 |
| 5 | [开发日志与日程](05_dev_log_and_schedule.md) | 时间线、阶段目标、卡点与决策 |
| 6 | [数据规范](07_chunking_and_metadata_spec.md) | 切块、条号、元数据和入库规则 |

## 2. 编号文档 00–10

| 编号 | 文档 | 状态 | 说明 |
|---|---|---|---|
| 00 | [项目状态与进度](00_project_status.md) | 现行 | 项目单点真相，优先级最高 |
| 01 | [文献与标准](01_literature_and_standards.md) | 现行 | 文献编号、归档状态和标准清单 |
| 02 | [概念与学习路线](02_concepts_and_learning_path.md) | 现行 | 领域概念、技术学习路线和读论文方法 |
| 03 | [技术路线调研](03_tech_route_survey.md) | 现行 | 技术方案比较与选型依据 |
| 04 | [任务二方案与评测](04_task2_plan_and_evaluation.md) | 现行 | 知识提取方案和规则基线评测 |
| 05 | [开发日志与日程](05_dev_log_and_schedule.md) | 现行 | 开发日志、日程、卡点和团队规范 |
| 06 | [文献速览与笔记索引](06_paper_summaries_and_notes.md) | 现行 | 核心论文摘要与笔记入口 |
| 07 | [切条与元数据规范](07_chunking_and_metadata_spec.md) | 现行 | JSONL 字段、条号、切分与校验 |
| 08 | [验收记录](08_acceptance_record.md) | 现行 | 历史验收与后续状态回填 |
| 09 | [实现方案](09_implementation_plan.md) | 现行 | 当前架构、数据边界和路线图 |
| 10 | [文献通读与路线映射](10_all_literature_overview_and_tech_routes.md) | 现行 | 全部文献与设计依据索引 |

## 3. 专题文档

- [意图分类规则说明](intent_rules_说明.md)
- [影子模式 A/B 对比报告](影子对比报告.md)
- [回归测试报告（2026-09-18）](exam_proof/回归测试报告_20260918.md)
- [RAG 基线测评报告（2026-09-15）](../model_exam/RAG基线测评报告_20260915.md)
- [调研报告归档说明](../survey/README.md)
- [版权与引用说明](../NOTICE.md)

## 4. 数据与模块说明

| 文档 | 内容 |
|---|---|
| [data/corpus 语料清单](../data/corpus/corpus_inventory.md) | 当前语料、核验状态、维护顺序和版权边界 |
| [data/evaluation](../data/evaluation/README.md) | 50 条验收用例字段、分类和评测脚本 |
| [data/rules](../data/rules/README.md) | 572 处置规则、722 三比值规则和版本状态 |
| [data/samples](../data/samples/README.md) | 3466 条公开 DGA 样本、量纲和来源 |
| [pure_kb](../pure_kb/README.md) | 198 条纯知识库、六领域 API 和主链路接入状态 |
| [vector_kb](../vector_kb/README.md) | 向量、BM25、RRF、路由、生成、引用校验和已知问题 |
| [vector_kb/corpus](../vector_kb/corpus/README.md) | 向量库入库输入与维护顺序 |

## 5. 阅读笔记

| 文件 | 状态 | 说明 |
|---|---|---|
| [论文阅读笔记](notes/paper_reading_notes.md) | 历史笔记 | 精读过程中的方法判断与待验证问题 |
| [C2 RCAgent 精读](notes/C2_RCAgent_close_reading.md) | 历史笔记 | RCAgent 的证据组织和工作流分析 |
| [非核心论文略读卡](notes/skimming_cards_non_essential_papers.md) | 历史笔记 | 非关键论文的阅读分级 |
| [论文阅读卡模板](notes/template_paper_reading_card.md) | 模板 | 新增精读时复制使用 |

## 6. 状态约定

- **现行**：持续维护，内容必须与代码、数据和评测结果一致。
- **历史证据**：保留报告生成时的原始结果，不事后改写；新增状态只能通过“后续状态”章节补记。
- **历史归档**：用于竞赛调研或早期版本留痕，不代表当前实现，不应直接作为开发依据。
- **本地材料**：`literature/`、`source_materials/`、`submissions_pending_review/` 和受版权保护的语料不进入公开仓库。

## 7. 维护规则

1. 修改代码接口、数据规模、主链路或评测结论时，至少同步 `README.md`、`docs/00`、相关模块 README。
2. 历史报告只补充“后续状态”，不覆盖原始测试数字。
3. 新增文档优先放入 `docs/` 并登记到本页；调研报告统一放入 `survey/`。
4. 所有相对链接必须在 GitHub 仓库中可解析，不引用仅本机存在的绝对路径。
5. 判断标准争议时，以 DL/T 722-2014 和 DL/T 572-2021 的合法原文为准；模型输出不能替代人工复核。