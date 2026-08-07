# Knowledge Schema Evolution 详细设计

| 元数据 | 值 |
|---|---|
| Document ID | DD-KNW-SCHEMA-EVOLUTION |
| Version | 0.1.0 |
| Status | In Review |
| Document Steward | Knowledge Engine |
| Architecture Baseline | SWM-ARCH@1.2 |
| Depends On | DD-KNW-SCHEMA-CORE@0.1.0、DD-KNW-REFERENCE-CONTEXT@0.1.0、DD-KNW-EVIDENCE@0.1.0、DD-KNW-ENTITY@0.1.0、DD-KNW-FACT@0.1.0、DD-KNW-INFERENCE-CONFLICT@0.1.0、DD-KNW-ADMISSION@0.1.0、DD-KNW-SNAPSHOT-PUBLICATION@0.1.0、DD-X-CAPABILITY-EXECUTION@0.1.0、DD-AI-MODEL-GATEWAY@0.1.0、DD-MGT-CAPABILITY-EVALUATION@0.1.0 |
| Owns Contracts | KNW-SCHEMA-COMPATIBILITY-01、KNW-SCHEMA-EVOLUTION-PLAN-01、KNW-SCHEMA-DISPOSITION-01、KNW-SCHEMA-MIGRATION-01、KNW-SCHEMA-IDENTITY-CONTINUATION-01、KNW-SCHEMA-ADOPTION-01 |
| Design Coverage | exact Source Snapshot 到不同 target Schema 的兼容判断、成员处置、迁移 Candidate、身份延续与 Adoption Package |
| Rationale ADR | AD-099、AD-113、AD-121、AD-122、AD-125、AD-126、AD-129 |
| Design Validation | None |
| Conformance Cases | None |
| Capability Evaluation | Schema 差异理解、Migration Proposal 和语义审核使用模型时适用 |

> 本文是按需启用的 Schema Adoption 能力，不是普通更新的前置条件，也不建立独立 Evolution Orchestrator。Definition、Registration 与 Target Validation 由 DD-KNW-SCHEMA-CORE 提供。

## 1. 目的与范围

当 KnowledgeScope 已有 CURRENT Snapshot，且下一版 Snapshot 需要绑定不同 Knowledge Schema 时，平台必须显式说明旧成员如何处置、哪些身份可以延续，以及目标成员如何重新准入。

本文定义一个不可变 `Schema Adoption Package`。它只向普通 Knowledge Update 提供条件性输入；实际来源调查、Evidence、Candidate、Admission、Manifest 和 Publisher 仍走统一主干。

本文不定义：

- 首次构建或同 Schema 更新；它们只依赖 Schema Core。
- Schema Definition 注册。
- 数据库 DDL、Projection 重建或历史 Snapshot 原地迁移。
- 自动扫描全部 Scope、迁移排期或独立 Evolution Orchestrator。
- 当前不需要的 N:1、1:N、N:M 身份合并 / 拆分工作流。

## 2. 所有权与边界

| 对象 / 决定 | Owner | 边界 |
|---|---|---|
| Compatibility / Adoption Plan / Package | Knowledge Engine | 绑定 exact source Snapshot 与 target Schema，不读取 Data Source |
| Migration / Disposition Proposal | 模型或确定性 Strategy | 不可信；不能自证兼容或发布 |
| Schema Semantic Review | Knowledge Verifier | 与 Proposal Strategy 隔离 |
| Source Information Need | Knowledge Construction Strategy | 由 Application Services 在普通 Update 中协调 |
| Adoption Update / Publication | Application Services 与 Publisher | 下游复用普通 Knowledge Update 与 Snapshot Publication 主干 |
| Schema Registry / Target Validation | Schema Core | Adoption Package 不能替代 |

Schema Evolution 不拥有 Application Attempt、Snapshot CURRENT 或稳定 Knowledge ID，也不直接调用 Source Integration。

## 3. 核心对象

| 对象 | 含义 |
|---|---|
| Source Snapshot Inventory | 从 exact source Snapshot / Member Manifest 机械重建的完整成员集合 |
| Compatibility Decision | 对 source→target、特定 Purpose 的方向性判断 |
| Source Member Disposition | 每个 source member 在目标中的唯一处置 |
| Target Obligation Inventory | target Schema 对 final target membership 的具体必需义务 |
| Migration Candidate Set | 按普通 Entity / Fact / Inference Candidate Contract 构造的目标候选 |
| Identity Continuation Decision | 判断一个 source canonical Root 是否能一对一延续 |
| Schema Adoption Package | 供普通 Update / Publisher 使用的不可变闭包 |

## 4. KNW-SCHEMA-COMPATIBILITY-01

Compatibility Decision 固定 exact source / target Schema、Purpose、Change Set Digest、受影响 Kind / Type / Contract、机械差异、语义审核 Basis、Reviewer、Read Set 和 Decision Digest。

需要被对象构建或 Admission 消费的 ELIGIBLE Decision，必须按 Schema Core 注册为 exact `KNW-SCHEMA-TRANSITION-PROOF-REF-01`；完整 Decision 仍由本文拥有，Proof Reference 只暴露 source / target / purpose / subject / outcome / digest。

决定是方向性的，至少区分：

- STATE_CONTINUATION
- EVIDENCE_INTERPRETATION
- IDENTITY_CONTINUATION
- FORMAL_PREMISE_INTERPRETATION
- ENRICHMENT
- UPSTREAM_DEPENDENCY
- SNAPSHOT_READ

每个维度只允许：

| Outcome | 含义 |
|---|---|
| EQUIVALENT | 对该 Purpose 语义等价；具体对象仍须重验 |
| MAPPING_REQUIRED | 需要完整、可回放、无语义扩张的映射 |
| REVALIDATION_REQUIRED | 可继续调查，但不能直接延续正式 State |
| REBUILD_REQUIRED | 必须从 Evidence、来源或正式前提重建 |
| FORBIDDEN | 不允许转换 |
| UNRESOLVED | 信息不足，失败关闭 |

模型分数、字段同名、版本大小或 predecessor 关系不能自动推出 Compatibility。

## 5. KNW-SCHEMA-EVOLUTION-PLAN-01

`PrepareSchemaAdoption` 接收：

- exact source Snapshot Reference / Member Manifest Digest。
- exact target Schema Reference 与成功的 Schema Selection Receipt；此时尚未形成 Publication Manifest，不要求 Final Target Validation。
- Adoption Objective、Scope、KnowledgeContext Boundary 和资源政策。
- 可选受信任 Compatibility Decisions；缺失部分必须本轮形成。
- Capability Catalog Snapshot、Execution Envelope，以及 Compatibility / Plan / Migration Proposal / Semantic Review 各自 exact Strategy、`PRODUCTION Activation / PASS Evaluation Result / latest VALID Decision | exact EVALUATION_ONLY Grant` 和资源 Allocation。

Knowledge Engine 从 source Manifest 机械生成 Source Snapshot Inventory，并冻结 Plan Revision / Digest。Plan 至少包含：

- 每个 source member 的稳定引用、Kind / Type、Identity、Context、依赖和 Evidence / Admission 引用。
- source→target Change Set 与 Compatibility 结果。
- 每个成员待完成的 Disposition Requirement。
- target Schema 可机械展开的 required member / admission obligations。
- 需要新 Evidence、重新调查或人工决策的 Knowledge Information Requirements。

Plan 是调查和迁移的边界，不是 Migration Result 或发布资格。只有 PRODUCTION Catalog 可以封存 Plan；EVALUATION_ONLY 只返回隔离的 Plan / Compatibility Evaluation Output。source Snapshot、target Schema、Scope 或 Objective 变化时创建新 Plan；不修改旧 Plan。

## 6. KNW-SCHEMA-DISPOSITION-01

每个 source member 必须恰好一个 Disposition：

| Disposition | 含义 |
|---|---|
| CONTINUE | 语义、身份、Context 和依赖均可证明不变；仍形成普通 Continuation Candidate 与新 Admission |
| MIGRATE | 通过已审核 Mapping 形成目标 Candidate |
| REBUILD | 从可用 Evidence、正式前提或新来源调查构造目标 Candidate |
| EXCLUDE_FROM_TARGET | 新 Snapshot 不再包含；必须有 target Schema / Policy 允许的结构化 Basis |
| BLOCKED | 当前无法安全处置；整个 Adoption Package 不可发布 |

“本轮未发现”不能成为 EXCLUDE 的充分依据。Disposition Proposal 可由模型提出，但 Knowledge Engine 必须证明 source Inventory 完整、每个成员恰好一个处置，且没有成员被静默丢弃。

Target Obligation Inventory 从 exact target Schema 和 final target membership 机械重算。每个实际触发的 required obligation 必须被一个已准入 target member 满足，或有 Schema 明确允许的 NOT_APPLICABLE Basis。若条件义务无法机械收敛、存在未处置项或需要本文未支持的身份基数变化，Package 为 BLOCKED。

## 7. KNW-SCHEMA-MIGRATION-01

Migration Strategy 只产生普通 Candidate Proposal，并固定：

- source member / Evidence / formal premise references。
- exact Mapping / Compatibility / Plan Revision。
- target Schema、KnowledgeContext 与 Candidate Envelope。
- Strategy / Model / Tool / Prompt 版本及 Execution Trace。
- Capability Catalog / Execution Envelope、Production Activation / Evaluation Validity 与 post-call actual Model Fingerprint Validation Result。

平台按目标 Schema 重建 Candidate，重新计算 Proposition、Identity、Argument、Context 与 Digest；不能复制数据库字段冒充迁移。只有 PRODUCTION Catalog 且 post-call eligibility 通过时才能把 Candidate 加入生产 Bundle；EVALUATION_ONLY 输出只进入 Evaluation Run。所有生产 Candidate 经过普通 Knowledge Verifier / Admission，Migration Strategy 不拥有准入权。

需要新来源时，Plan 产生 Knowledge Information Requirement；Application Services 在普通 Knowledge Update 中协调 Artifact / Evidence 流程。Evolution 不建立来源旁路。

## 8. KNW-SCHEMA-IDENTITY-CONTINUATION-01

当前只支持可机械证明的 `1:1` Identity Continuation：

- source Root 与一个 target Effective Identity Key 对应。
- Anchor / Semantic Definition 在 target Schema 下保持相同对象含义。
- 不与已有其他 canonical Root 的 target key 冲突。
- Decision 固定 source / target references、Identity Basis、Compatibility、Reviewer 和 Digest。

无法证明时使用新 target Identity，或 BLOCKED。一个 source 拆为多个 target、多个 source 合并为一个 target、N:M 映射和跨 Root 自动去重当前返回 `IDENTITY_CARDINALITY_UNSUPPORTED`；真实项目验证出现后再专题扩展 Lineage / Cardinality Contract，不预建复杂状态机。

## 9. KNW-SCHEMA-ADOPTION-01

### 9.1 Adoption Package

成功 Package 至少固定：

- Package / Plan ID、Revision、Digest。
- source Snapshot / Schema、target Schema 与 Schema Selection Receipt；Final Target Validation Receipt 在 Manifest 形成后独立产生，不回写 Package。
- 绑定本 Package 的 Build Intent / Application Attempt References；不创建独立 Construction Attempt。
-完整 Source Snapshot Inventory。
- Compatibility Decisions。
- 对每个 source member 的唯一 Disposition。
- Target Obligation Inventory / Satisfaction Manifest。
- 1:1 Identity Continuation Decisions。
- 本 Package 使用的完整 Schema Transition Proof Reference Set；必须与 Compatibility / Identity Decisions 双向一致。
- Migration / Rebuild / Continuation Candidate Bundle Seal 与 COMPLETE Admission Batch Result。
- final target membership digest、Expected Current 和 schema-adoption-specific Validation / Precondition Digests；来源覆盖、资源、执行等通用 Criterion 仍由 Application Services 针对 exact Manifest 聚合。
- Compatibility、Disposition、Migration 与 Review 的 frozen Capability / Strategy / Activation / Evaluation / actual Model Fingerprint Provenance。

Package 只有 `READY` 或没有形成；执行失败、BLOCKED 或审核未完成不生成可供发布的 Package。Package 自身不切换 CURRENT。

### 9.2 普通 Update / Publication 复用

Application Services 先以 Schema Selection Receipt / Evolution Plan 创建 `Schema Transition Mode = ADOPTION` 的普通 Build Intent / Application Attempt。该 Attempt 负责来源调查、Migration / Rebuild / Continuation Candidate、Admission 和 final Candidate Bundle；Knowledge Engine 随后在同一 Attempt 上封存 READY Adoption Package。Snapshot Builder 再以 Package 形成完整 Manifest，Schema Core 对 actual Manifest 签发 Final Target Validation Receipt，各 Criterion Owner 对 exact Manifest 形成 Assessment，Application Services 聚合 Acceptance Assertion，Publisher 按其公开 Publication Request 契约原子发布。

Application Services 将 READY Package 映射为 Snapshot 文档定义的 `Schema Adoption Publication Closure`，并与独立 Final Target Validation Receipt 一起进入 Publication Request。Publisher 只在 ADOPTION 模式附加验证：

- Expected Current 仍是 Package 的 exact source Snapshot。
- Schema Selection / Final Target Validation Receipts 都绑定本 Scope、target Schema 与 actual Manifest。
- Source Inventory / Disposition 与 source Manifest 双向相等。
- final Manifest 满足 Target Obligation Inventory。
- Identity Continuation 均为受支持的 1:1，且唯一键未被占用。
- Candidate / Admission / Manifest Digests 与 Package 一致。

失败保持原 CURRENT；改变任何输入都创建新 Package / Application Attempt。Schema Evolution 不反向依赖 Knowledge Update 内部状态。

## 10. AI Native 与平台责任

模型适合解释开放语义差异、提出 Mapping / Disposition / Migration Candidate 和调查需求。平台不可让渡：

- exact source / target refs、Inventory 完整性和 Digest。
- target obligation 的机械展开与满足检查。
- Candidate 平台重建、Admission 和 Identity 唯一性。
- Expected Current、Package 幂等和 Snapshot 原子发布。
- 生成 / 审核隔离。

模型增强可以减少专用 Mapping 代码，不能删除可追溯性、独立审核或发布门禁。

## 11. 失败、重试与恢复

| 失败 | 处理 |
|---|---|
| SOURCE_SNAPSHOT_CHANGED | 旧 Plan / Package 不复用，创建新 Plan |
| TARGET_SCHEMA_INVALID | 返回 Schema Core 修复，不开始 Adoption |
| COMPATIBILITY_UNRESOLVED / FORBIDDEN | BLOCKED，不用模型置信度覆盖 |
| SOURCE_DISPOSITION_INCOMPLETE | 不生成 Package |
| TARGET_OBLIGATION_UNSATISFIED | 补充 Candidate / Evidence 或 BLOCKED |
| IDENTITY_CARDINALITY_UNSUPPORTED | 当前失败关闭；达到真实需求后扩展 |
| IDENTITY_UNIQUE_CONFLICT | 重新 Resolution / Package，不盲目延续 |
| ADMISSION_INCOMPLETE / REJECTED | 不生成 READY Package |
| CURRENT_CONFLICT | 原 CURRENT 保持；基于新 source Snapshot 重建 |
| OUTCOME_UNKNOWN | 查询同一 Publisher Attempt，不创建竞争 Adoption |

Plan、Decision 和 Package 不可变；相同幂等键 / Request Digest 返回原结果。当前只支持同一持久历史的事务重试，Knowledge Store 历史无法连续证明时隔离，不定义跨代恢复。

## 12. 拟议不变量

1. INITIAL / UNCHANGED 发布不依赖本文。
2. Schema Definition / Registration / Target Validation 只由 Schema Core 拥有。
3. Adoption 绑定 exact source Snapshot 与不同 target Schema，不修改旧 Snapshot。
4. Source Inventory 与 Disposition 双向完整；任何 member 不得静默丢失。
5. 每个 target required obligation 都有明确满足或合法 NOT_APPLICABLE Basis。
6. Migration 只形成普通 Candidate，必须平台重建并重新 Admission。
7. 当前 Identity Continuation 只支持可证明 1:1；其他基数失败关闭。
8. Adoption Package 不切换 CURRENT；实际发布复用普通 Publisher。
9. 模型不能自证 Compatibility、Identity Continuation、Admission 或 Publication。
10. 失败不影响原 CURRENT，输入变化创建新不可变 Plan / Package。

## 13. 验证义务

Contract Conformance 至少覆盖：

- source Inventory / Disposition 集合双向相等。
- CONTINUE / MIGRATE / REBUILD / EXCLUDE / BLOCKED 的互斥与完整。
- Target Obligation 的漏项、重复满足和非法 NOT_APPLICABLE。
- 1:1 Identity Continuation、已有 key 冲突和不支持基数。
- Candidate / Admission / Package / Manifest Digest 防串用。
- Expected Current 与并发 Publication。
- 普通 INITIAL / UNCHANGED 路径完全不请求 Adoption Package。

Schema 差异、Mapping 和 Migration Strategy 建立 Capability Evaluation。只有真实项目出现身份拆分 / 合并、递归 obligation 无法用当前有限 Contract 表达，或某种迁移质量无法静态判断时，才登记有界 DVR Demo。
