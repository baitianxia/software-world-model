# Software World Model Design Baseline Manifest — Iteration 001 / Revision 002

| 元数据 | 值 |
|---|---|
| Manifest ID | SWM-DBM-ITER-001-REV-002 |
| Status | Frozen |
| Created At | 2026-08-05 |
| Supersedes | `SWM-DBM-ITER-001`（仅文档目录与导航包装） |
| Migration Record | [SWM-DOC-MIG-001](../../history/Documentation_Structure_Migration_Record_001.md) |
| Consumer | [SWM-IMP-ITER-001](../../implementation/iteration-001/Implementation_Plan_Iteration_001.md) |
| Acceptance Decision | [SWM-DD-ACCEPT-001](Detailed_Design_Acceptance_Record_001.md) |
| Architecture | SWM-ARCH@1.2 |
| Hash Algorithm | SHA-256 |
| Workspace VCS | None；以本文内容摘要固定基线 |

> 本 Manifest 固定首个纵向实现切片可以采用的规范性设计内容。Revision 002 只重新固定迁移后的 canonical 路径和完整文件摘要，不改变 Document ID、语义版本、主题状态或规范语义。它不把实施方案、Demo、代码或测试结果提升为设计权威。

## 1. 架构与详细设计治理基线

| Document | Version / Status | SHA-256 |
|---|---|---|
| [Software_World_Model_Architecture_Baseline.md](../../architecture/Software_World_Model_Architecture_Baseline.md) | SWM-ARCH@1.2 / Baseline | `207cd8fec7034c21a5855f7562459b58b565e2bc0a279dda2e52ce829e35616c` |
| [Software_World_Model_Detailed_Design.md](../Software_World_Model_Detailed_Design.md) | SWM-DD-GUIDE@0.1.0 / Accepted | `e643f3e7e4499eb56603d99f36ddd0ab8dbcd7b1c7ac1f44f5ccf0ca7bb836b1` |

## 2. Accepted 详细设计

| Document ID | Version / Status | Document | SHA-256 |
|---|---|---|---|
| DD-X-CAPABILITY-EXECUTION | 0.1.0 / Accepted | [Capability Execution](../topics/DD-X-CAPABILITY-EXECUTION.md) | `809d064c89ab5bb5f8cae40eacebf82169a6d0b975db03b937b3112ca4e34f2f` |
| DD-KNW-KNOWLEDGE-SCOPE | 0.1.0 / Accepted | [KnowledgeScope](../topics/DD-KNW-KNOWLEDGE-SCOPE.md) | `2e7596a893375b8794f95f33e8bd92fcae456d522d19fd161b6bd49f15298690` |
| DD-KNW-REFERENCE-CONTEXT | 0.1.0 / Accepted | [Reference / Context](../topics/DD-KNW-REFERENCE-CONTEXT.md) | `ee06915750cc3e6944429360fda57112a9b01696e3f778c9c7b9f3e4775af8fc` |
| DD-AI-MODEL-GATEWAY | 0.1.0 / Accepted | [Model Gateway](../topics/DD-AI-MODEL-GATEWAY.md) | `9eaf2c5386459a6faca93309054656f3931fa608e09bb774284688f27ccedaaf` |
| DD-MGT-CAPABILITY-EVALUATION | 0.1.0 / Accepted | [Capability Evaluation](../topics/DD-MGT-CAPABILITY-EVALUATION.md) | `751d10d3e9fc614fa521462be727f48807048fa42846186ecfa56616407864e5` |
| DD-KNW-SCHEMA-CORE | 0.1.0 / Accepted | [Schema Core](../topics/DD-KNW-SCHEMA-CORE.md) | `808d03904bb784236f13c81c1267a67885ba596ade778303c255ce0b7ce2a573` |
| DD-KNW-CONTEXT-COMPARISON | 0.1.0 / Accepted | [Context Comparison](../topics/DD-KNW-CONTEXT-COMPARISON.md) | `94df4278f868be778e4f1829127d25a9c2de82bd1465bbd062d02fa5dd3834d5` |
| DD-SRC-DATA-SOURCE | 0.1.0 / Accepted | [DataSource / Binding](../topics/DD-SRC-DATA-SOURCE.md) | `fb68795f5d5362958fd5da7362d2b4428d714b94a7e98a8b0732242ae0aaabc7` |
| DD-SRC-SOURCE-ARTIFACT | 0.1.0 / Accepted | [Source / Artifact](../topics/DD-SRC-SOURCE-ARTIFACT.md) | `1da30b71fbbd720c8fdbee1f5c870cd658f909ea0afd4c1d6a5d27aa067c2b39` |
| DD-APP-MANAGEMENT | 0.1.0 / Accepted | [Management](../topics/DD-APP-MANAGEMENT.md) | `13727b7ed7ccd21dee06450135014c16fb9bddf01b0e1b98c790471b6724c364` |
| DD-KNW-EVIDENCE | 0.1.0 / Accepted | [Evidence](../topics/DD-KNW-EVIDENCE.md) | `814e2c1e1985c6228b461b4faaaa8727e4bd8d9b3440242bf22c56903ebfd219` |
| DD-KNW-ENTITY | 0.1.0 / Accepted | [Entity](../topics/DD-KNW-ENTITY.md) | `4b5d750da2d794b7a81d8765e90c5d82b67c0790b98dc65f0d4df5a2eef09024` |
| DD-KNW-FACT | 0.1.0 / Accepted | [Fact](../topics/DD-KNW-FACT.md) | `93f1be990cf0cfbebfc30db544127de3ae047bef6a77ad66e557c908640fc77b` |
| DD-KNW-INFERENCE-CONFLICT | 0.1.0 / Accepted | [Inference / Conflict](../topics/DD-KNW-INFERENCE-CONFLICT.md) | `1cbab41786e8cdaff0da72b2c57df477dc10fedaa0b9540763746c20717abeae` |
| DD-KNW-ADMISSION | 0.1.0 / Accepted | [Admission](../topics/DD-KNW-ADMISSION.md) | `da51ac515634c102526cd61d99ecf1c7d45fe00fb2111039cd3bd1e03055dd87` |
| DD-KNW-SNAPSHOT-PUBLICATION | 0.1.0 / Accepted | [Snapshot / Publication](../topics/DD-KNW-SNAPSHOT-PUBLICATION.md) | `d6b766f5151ef09927845c98aa19a3108b43a2448b2293a0244b7e467ef49b5d` |
| DD-KNW-PERSISTENCE | 0.1.0 / Accepted | [Authority Persistence](../topics/DD-KNW-PERSISTENCE.md) | `bf679f0a250aff67208b5c76098bcbdeff686759e35c39314bd8dadc1935543a` |
| DD-APP-KNOWLEDGE-UPDATE | 0.1.0 / Accepted | [Knowledge Update](../topics/DD-APP-KNOWLEDGE-UPDATE.md) | `85392651c3ca0e4928fbdfa249674a081dae8b73150f48e1a8dfff9ea58a27b6` |
| DD-APP-KNOWLEDGE-USE | 0.1.0 / Accepted | [Knowledge Use](../topics/DD-APP-KNOWLEDGE-USE.md) | `28fda4293bbf934c9b840f6bdc4949fc8f090d3ff9795fb164f160590c20c211` |
| DD-APP-AGENTIC-TASK | 0.1.0 / Accepted | [Agentic Task](../topics/DD-APP-AGENTIC-TASK.md) | `fb438f3c301ac54f26e83d93230c77ca110fa5af5429c9925817d14e67f3aca9` |
| DD-APP-RESPONSE-CONTROL | 0.1.0 / Accepted | [Response Control](../topics/DD-APP-RESPONSE-CONTROL.md) | `a82f5ecbc78465728c08ca9938917fc71482feb32e8cfcbf67b31163b0724e28` |
| DD-X-TELEMETRY-COST | 0.1.0 / Accepted | [Telemetry / Cost](../topics/DD-X-TELEMETRY-COST.md) | `e6abd7c2b66290dc0ff8730a1a524c46f625c6c42c7f851c4476dfcbff69cd13` |

## 3. 本切片条件选择

| 条件能力 | 本 Manifest 选择 |
|---|---|
| Runtime Knowledge Path | `Formal Knowledge Single Path`；不存在运行时直接来源回答兜底 |
| Knowledge Schema Transition | `INITIAL | UNCHANGED`；不启用 ADOPTION |
| Semantic View | 不作为本切片依赖；使用 Authority Query / Sufficiency |
| Source Provider | Local Git；其他 Provider 不在本 Manifest |
| Source Retention | `NO_EVICTION`；Read Protection 为 `NOT_REQUIRED_NO_EVICTION` |
| Knowledge Cleanup | `NO_PHYSICAL_CLEANUP` |
| Projection | `DISABLED` |
| Non-contiguous Recovery | `UNSUPPORTED`；无法确认同一持久历史时部署 fail-stop |
| Model External Access | `NO_EXTERNAL_ACCESS`；模型只提出 Platform Tool Proposal |
| Scope / Publication | 单 Scope 原子 CURRENT 切换；不启用跨 Scope 聚合发布 |

## 4. 未纳入基线的主题

| Document | Status | 原因 |
|---|---|---|
| [DD-KNW-SCHEMA-EVOLUTION@0.1.0](../topics/DD-KNW-SCHEMA-EVOLUTION.md) | In Review | 本切片不执行 Schema Adoption |
| [DD-SEM-SEMANTIC-VIEW@0.1.0](../topics/DD-SEM-SEMANTIC-VIEW.md) | In Review | 本切片不依赖稳定 View |

未纳入主题的 Contract 不能被实现隐式使用。需要启用时先完成相应接受记录，并创建新的 Manifest。

## 5. 完整性规则

1. 构建、测试、CC、CE 和产品验证必须记录本 Manifest ID。
2. 启动实现前逐文件重算 SHA-256；任何不一致都使该工作副本不能声称符合本 Manifest。
3. Accepted 主题发生规范性变化时，必须按总纲升级版本、评估依赖并创建新 Manifest；不能原地更新本文摘要。
4. 状态字段、正文和链接都属于摘要内容，手工修改 `Accepted` 文档同样会破坏基线。
5. 当前没有代码提交可绑定。建立实现仓库后，后续 CC / CE Run 还必须固定实现 Commit；本文不能代替代码版本。
