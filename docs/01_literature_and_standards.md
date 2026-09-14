# 文献与标准（统一编号版）

> 更新：2026-09-14
> 文献编号规则：`A/B/C/D/E/F` 只用于 `literature/` 下的实际文献文件；标准直接使用标准号，不占用文献编号。
> 旧版“主题清单 A–H”不再作为文献编号使用，主题阅读导航见本文第六节。

## 一、编号规则

| 编号 | 类别 | 说明 |
|---|---|---|
| A | 综述 / 全景 | 大模型、PHM、故障诊断和电力系统的总体综述 |
| B | 知识增强与 RAG | RAG、GraphRAG、LLM×KG、知识增强架构 |
| C | 根因分析与 Agent | RCAgent、AIOps、Agentic RAG、电力设备智能体 |
| D | 电力 / 变压器 LLM | 电力设备、油浸式变压器、DGA、工业因果分析 |
| E | DGA 领域方法 | 传统 DGA、IEC TC10、Duval 和三比值相关方法 |
| F | 幻觉抑制与可溯源性 | ReAct、Self-RAG、CRAG、RARR 等可信生成方法 |

规则：

1. 同一篇论文只使用一个编号，编号与 `literature/` 文件名前缀一致。
2. 标准、工具、数据集、行业报道不占用论文编号。
3. 主题阅读路线只写“主题 + 相关编号”，不再产生第二套 A/B/C 编号。
4. 获取状态以本文和 `literature/README.md` 为准。

---

## 二、统一文献清单

### A. 综述 / 全景

| 编号 | 题目 | 来源 / 年份 | 状态 | 本地文件 |
|---|---|---|---|---|
| A1 | Large language models for PHM: a review of optimization techniques and applications | Autonomous Intelligent Systems, 2025 | ✅ 已归档 | `01_surveys_overview/A1_LargeLanguageModels_for_PHM_Review_2025_Yu.pdf` |
| A2 | Can Large Language Models Diagnose Machine Faults? A Comprehensive Survey from Deep Learning to Foundation Models | TechRxiv, 2026 | ✅ 已归档 | `01_surveys_overview/A2_TechRxiv2026_Can_LLMs_Diagnose_Machine_Faults.pdf` |
| A3 | A Review of Fault Diagnosis Methods: From Traditional Machine Learning to Large Language Model Fusion Paradigm | Sensors / PMC, 2026 | ✅ 已归档 | `01_surveys_overview/A3_Sensors2026_Fault_Diagnosis_ML_to_LLM_Fusion.pdf` |
| A4 | Foundation Models for Prognostics and Health Management: A Survey | arXiv, 2023 | ✅ 已归档 | `01_surveys_overview/A4_arXiv2312.06261_FoundationModels_PHM_Survey.pdf` |
| A5 | Large Models for PHM: Outline | arXiv, 2024 | ✅ 已归档 | `01_surveys_overview/A5_arXiv2407.03374_PHM_LargeModel_Outline.pdf` |
| A6 | A Comprehensive Review on the Application of Large Language Models (LLMs) in Power Systems | IEEE Access, 2025 | ✅ 已归档 | `01_surveys_overview/A6_IEEE_Access2025_LLMs_in_Power_Systems_Review.pdf` |
| A7 | 人工智能大模型在电力设备运维场景中的应用探讨 | 中国工程科学, 2025 | ✅ 已归档 | `01_surveys_overview/A7_Chinese2025_AI_LLM_Power_Equipment_OandM.pdf` |

### B. 知识增强与 RAG

| 编号 | 题目 | 来源 / 年份 | 状态 | 本地文件 |
|---|---|---|---|---|
| B0 | Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks | NeurIPS, 2020 | ✅ 已归档 | `02_knowledge_enhancement/B0_arXiv2005.11401_RAG_Lewis2020.pdf` |
| B1 | Retrieval-Augmented Generation for Large Language Models: A Survey | arXiv / RAG survey, 2023–2024 | ✅ 已归档 | `02_knowledge_enhancement/B1_arXiv2312.10997_RAG_Survey.pdf` |
| B2 | GraphRAG Survey | arXiv, 2024 | ✅ 已归档 | `02_knowledge_enhancement/B2_arXiv2408.08921_GraphRAG_Survey.pdf` |
| B2a | From Local to Global: A Graph RAG Approach to Query-Focused Summarization | arXiv, 2024 | ✅ 已归档 | `02_knowledge_enhancement/B2a_arXiv2404.16130_GraphRAG_paper.pdf` |
| B3 | Unifying Large Language Models and Knowledge Graphs: A Roadmap | IEEE TKDE, 2024 | ✅ 已归档 | `02_knowledge_enhancement/B3_arXiv2306.08302_LLM_KG_Roadmap.pdf` |
| B4 | Knowledge Graph Hallucination Survey | arXiv, 2023 | ✅ 已归档 | `02_knowledge_enhancement/B4_arXiv2311.07914_KG_Hallucination_Survey.pdf` |
| B5 | From vectors to knowledge graphs: A comprehensive analysis of modern retrieval-augmented generation architectures | Computer Science Review, 2026 | ✅ 已归档 | `02_knowledge_enhancement/B5_ComputerScienceReview2026_Modern_RAG_Architectures.pdf` |
| B6 | How can the integration of AI large language models and knowledge graph enhance fault diagnosis? A systematic literature review | Applied Soft Computing, 2026 | ✅ 已归档 | `02_knowledge_enhancement/B6_AppliedSoftComputing2026_LLM_KG_Fault_Diagnosis_Review.pdf` |

### C. 根因分析与 Agent

| 编号 | 题目 | 来源 / 年份 | 状态 | 本地文件 |
|---|---|---|---|---|
| C1 | A Survey of AIOps in the Era of Large Language Models | arXiv, 2025 | ✅ 已归档 | `03_root_cause_agent/C1_arXiv2507.12472_AIOps_LLM_Survey.pdf` |
| C2 | RCAgent: Cloud Root Cause Analysis by Autonomous Agents with Tool-Augmented Large Language Models | CIKM, 2024 | ✅ 已归档 | `03_root_cause_agent/C2_arXiv2310.16340_RCAgent.pdf` |
| C3 | Exploring LLM-based Agents for Root Cause Analysis | FSE Companion, 2024 | ✅ 已归档 | `03_root_cause_agent/C3_arXiv2403.04123_LLM_Agents_RCA.pdf` |
| C4 | Automatic Root Cause Analysis via Large Language Models for Cloud Incidents (RCACopilot) | EuroSys / arXiv, 2024 | ✅ 已归档 | `03_root_cause_agent/C4_arXiv2305.15778_Practical_RCA_LLM.pdf` |
| C5 | DiagAgent: An Agent Framework for Power Equipment Fault Diagnosis by Integrating RAG and MCP Tools | IEEE, 2026 | ✅ 已归档 | `03_root_cause_agent/C5_DiagAgent_IEEE2026_RAG_MCP_Power_Equipment.pdf` |
| C6 | FaultSeer: An Agentic Retrieval-Augmented Generation Framework for Defect Analysis and Diagnosis in Power Systems | NTCI, 2025 | ✅ 已归档 | `03_root_cause_agent/C6_FaultSeer_NTCI2025_Agentic_RAG_Power_Systems.pdf` |

### D. 电力 / 变压器 LLM

| 编号 | 题目 | 来源 / 年份 | 状态 | 本地文件或获取信息 |
|---|---|---|---|---|
| D1 | A Large Language Model Assisted Fault Diagnosis Framework for Power Equipment in New Power Systems | ECNCT, 2026 | ✅ 已归档 | `07_power_transformer_llm/D1_ECNCT2026_LLM_Power_Equipment_Fault_Diagnosis.pdf` |
| D2 | Oil-Immersed Transformer Diagnosis Based on On-Device Large Model with Multimodal Sensing and Retrieval-Augmented Generation | ICIPS, 2025 | ✅ 已归档 | `07_power_transformer_llm/D2_ICIPS2025_Oil_Immersed_Transformer_MM_RAG.pdf` |
| D3 | DGA-Based Power Transformer Fault Diagnosis via Knowledge Distillation of LLM | Springer, DOI 10.1007/978-981-95-2581-2_22 | 🔒 待获取 | 校园图书馆或导师资源 |
| D4 | CausalKGPT: Industrial structure causal knowledge-enhanced large language model for cause analysis | Advanced Engineering Informatics, 2024 | ✅ 已归档 | `07_power_transformer_llm/D4_CausalKGPT_AEI2024_Industrial_Causal_Knowledge_LLM.pdf` |
| D5 | Knowledge extraction and retrieval-augmented generation for intelligent maintenance of wind power equipment based on graph attention networks | Chinese Journal of Mechanical Engineering, 2026 | ✅ 已归档 | `07_power_transformer_llm/D5_CJME2026_Wind_Power_GAT_RAG_Maintenance.pdf` |
| D6 | 基于大语言模型的图检索增强生成技术在核电领域的应用与展望 | 发电技术, 2025 | ✅ 已归档 | `07_power_transformer_llm/D6_PowerGenerationTechnology2025_Nuclear_GRAG.pdf` |

### E. DGA 领域方法

| 编号 | 题目 | 来源 / 年份 | 状态 | 本地文件或获取信息 |
|---|---|---|---|---|
| E0 | Interpretation of Gas-in-Oil Analysis Using New IEC Publication 60599 and IEC TC 10 Databases | IEEE Electrical Insulation Magazine, 2001 | ✅ 已归档 | `06_dga_methods/E0_Duval_dePabla_IEC60599_TC10_2001.pdf` |
| E1 | Conventional methods of dissolved gas analysis using oil-immersed power transformer for fault diagnosis: A review | Electric Power Systems Research, 2023 | 🔒 待获取 | DOI: 10.1016/j.epsr.2022.109064；可尝试 NSTL 文献传递 |
| E2 | Conventional Dissolved Gases Analysis in Power Transformers: Review | Energies, 2023 | ✅ 已归档 | `06_dga_methods/E2_Energies2023_16_7219_ConventionalDGA_Review.pdf` |
| E3 | Traditional fault diagnosis methods for mineral oil-immersed power transformer based on DGA | IET Nanodielectrics, 2024 | ✅ 已归档 | `06_dga_methods/E3_IET_Nanodielectrics2024_DGA_Review_Nanfak.pdf` |

### F. 幻觉抑制与可溯源性

| 编号 | 题目 | 来源 / 年份 | 状态 | 本地文件 |
|---|---|---|---|---|
| F1 | ReAct: Synergizing Reasoning and Acting in Language Models | ICLR, 2023 | ✅ 已归档 | `04_hallucination_compliance/F1_arXiv2210.03629_ReAct.pdf` |
| F2 | Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection | ICLR, 2024 | ✅ 已归档 | `04_hallucination_compliance/F2_arXiv2310.11511_SelfRAG.pdf` |
| F3 | Corrective Retrieval Augmented Generation (CRAG) | ICLR, 2024 | ✅ 已归档 | `04_hallucination_compliance/F3_arXiv2401.15884_CRAG.pdf` |
| F4 | RARR: Researching and Revising What Language Models Say, Using Language Models | ACL, 2023 | ✅ 已归档 | `04_hallucination_compliance/F4_arXiv2210.08726_RARR.pdf` |

---

## 三、标准

| 标准 | 状态 | 用途 |
|---|---|---|
| DL/T 722-2014《变压器油中溶解气体分析和判断导则》 | ✅ 真本已获取并核验 | DGA 注意值、产气速率、三比值编码、故障类型判断的第一手依据 |
| DL/T 572-2021《电力变压器运行规程》 | ✅ 已获取 | 运行异常与处置边界 |
| GB 26860-2011《电力安全工作规程》 | 🟡 待补摘录 | 停送电、验电、工作票等安全动作边界 |
| DL/T 573 / DL/T 596 | 🔒 按需 | 检修与预防性试验补充资料 |
| IEC 60599:2022 | ❌ 弃用 | 因版权/费用原因不作为正式依据 |

---

## 四、数据、语料与评测

| 资料 | 状态 | 用途 |
|---|---|---|
| `data/samples/dga_samples_uL_per_L.csv` | ✅ 3466 条，统一 μL/L | DGA 规则与分类评测 |
| IEC TC10 / Duval 数据来源 | ✅ E0 已归档 | DGA 原始判据与样本背景 |
| IEEE DataPort / Mendeley DGA 数据 | 🔒 / 🟡 待补 | 补充外部评测样本 |
| `data/rules/` | ✅ | DL/T 572 处置规则、DL/T 722 三比值判据 |
| RAGAS、检索命中率、引用正确率 | 🟡 待补评测资料 | 评测生成答案与引用质量 |
| 公开检修案例、反事故措施 | 🟡 待补 | 合规处置和真实案例语料 |

---

## 五、获取与归档记录

### 2026-09-09：首批免费文献

- A4、A5、B2、B3、B4、C1、C3、C4、E2、E3 等已完成下载和编号归档。
- DL/T 722-2014、DL/T 572-2021 已获取并核验。

### 2026-09-14：新增归档

| 编号 | 本地文件 |
|---|---|
| A2 | `01_surveys_overview/A2_TechRxiv2026_Can_LLMs_Diagnose_Machine_Faults.pdf` |
| A3 | `01_surveys_overview/A3_Sensors2026_Fault_Diagnosis_ML_to_LLM_Fusion.pdf` |
| A6 | `01_surveys_overview/A6_IEEE_Access2025_LLMs_in_Power_Systems_Review.pdf` |
| A7 | `01_surveys_overview/A7_Chinese2025_AI_LLM_Power_Equipment_OandM.pdf` |
| B5 | `02_knowledge_enhancement/B5_ComputerScienceReview2026_Modern_RAG_Architectures.pdf` |
| B6 | `02_knowledge_enhancement/B6_AppliedSoftComputing2026_LLM_KG_Fault_Diagnosis_Review.pdf` |
| C5 | `03_root_cause_agent/C5_DiagAgent_IEEE2026_RAG_MCP_Power_Equipment.pdf` |
| C6 | `03_root_cause_agent/C6_FaultSeer_NTCI2025_Agentic_RAG_Power_Systems.pdf` |
| D1 | `07_power_transformer_llm/D1_ECNCT2026_LLM_Power_Equipment_Fault_Diagnosis.pdf` |
| D2 | `07_power_transformer_llm/D2_ICIPS2025_Oil_Immersed_Transformer_MM_RAG.pdf` |
| D4 | `07_power_transformer_llm/D4_CausalKGPT_AEI2024_Industrial_Causal_Knowledge_LLM.pdf` |
| D5 | `07_power_transformer_llm/D5_CJME2026_Wind_Power_GAT_RAG_Maintenance.pdf` |
| D6 | `07_power_transformer_llm/D6_PowerGenerationTechnology2025_Nuclear_GRAG.pdf` |

---

## 六、主题阅读导航（不使用文献编号）

- **变压器机理与 DGA**：E0、E1、E2、E3；配合 DL/T 722-2014、DL/T 572-2021。
- **大模型与故障诊断全景**：A1–A7。
- **RAG、GraphRAG 与知识图谱增强**：B0–B6。
- **根因分析、AIOps 与 Agent 工作流**：C1–C6。
- **电力设备与变压器专项应用**：D1–D6。
- **幻觉抑制、可溯源与合规生成**：F1–F4。
- **行业实践与竞品**：国家电网“光明”、南方电网“大瓦特”、微软 × 西门子 Industrial Copilot、RAGFlow / Dify 等；不占用论文编号。
- **数据、语料与评测**：DGA 样本、IEEE DataPort / Mendeley、RAGAS、检索命中率、引用正确率和危险建议拦截测试。

补充候选（暂不分配文献编号）：

- Root Cause Analysis in the Industrial Domain using Knowledge Graphs: A Case Study on Power Transformers
- 基于知识增强大语言模型的零样本电力设备本体缺陷等级识别方法
- HyDE: Precise Zero-Shot Dense Retrieval without Relevance Labels
- Reflexion: Language Agents with Verbal Reinforcement Learning
- A Method for Power Equipment Faults Knowledge Reasoning Based on Retrieval-Augmented Generation
- GitHub: Awesome-large-language-model-for-Prognostics-and-health-management

---

## 七、阅读笔记索引

- `docs/notes/C2_RCAgent_close_reading.md`
- `docs/notes/skimming_cards_non_essential_papers.md`
- `docs/notes/paper_reading_notes.md`
- `docs/notes/template_paper_reading_card.md`

## 八、仍缺资料

- D3：DGA-Based Power Transformer Fault Diagnosis via Knowledge Distillation of LLM
- E1：Conventional methods of dissolved gas analysis using oil-immersed power transformer for fault diagnosis: A review
- GB 26860-2011 的安全边界摘录
- 公开检修案例和反事故措施语料
- RAG 评测基准与评测框架资料