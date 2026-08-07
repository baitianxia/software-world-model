# Knowledge Update 详细设计

| 元数据 | 值 |
|---|---|
| Document ID | DD-APP-KNOWLEDGE-UPDATE |
| Version | 0.1.0 |
| Status | Accepted |
| Design Coverage | 完整应用编排、调查循环、最终准入批次、发布接受、发布请求、结果与恢复边界 |
| Document Steward | Application Services / Knowledge Update |
| Architecture Baseline | SWM-ARCH@1.2 |
| Depends On | DD-KNW-KNOWLEDGE-SCOPE@0.1.0、DD-KNW-REFERENCE-CONTEXT@0.1.0、DD-KNW-SCHEMA-CORE@0.1.0、DD-X-CAPABILITY-EXECUTION@0.1.0、DD-AI-MODEL-GATEWAY@0.1.0、DD-MGT-CAPABILITY-EVALUATION@0.1.0、DD-KNW-CONTEXT-COMPARISON@0.1.0、DD-SRC-SOURCE-ARTIFACT@0.1.0、DD-KNW-EVIDENCE@0.1.0、DD-KNW-ENTITY@0.1.0、DD-KNW-FACT@0.1.0、DD-KNW-INFERENCE-CONFLICT@0.1.0、DD-KNW-ADMISSION@0.1.0、DD-KNW-SNAPSHOT-PUBLICATION@0.1.0 |
| Conditional Depends On | DD-KNW-SCHEMA-EVOLUTION@0.1.0（仅 Schema ADOPTION） |
| Owns Contracts | APP-KNOWLEDGE-UPDATE-01、APP-CANONICAL-BUILD-TARGET-01、APP-BUILD-INTENT-01、APP-PUBLICATION-POLICY-01、APP-PUBLICATION-ASSESSMENT-01、APP-INVESTIGATION-01、APP-SOURCE-TOOL-STEP-01、APP-UPDATE-RESULT-01 |
| Supersedes | `Software_World_Model_MVP_Detailed_Design.md` V0.4 的 Knowledge Update 内容 |
| Rationale ADR | AD-076、AD-092、AD-094、AD-096、AD-100 至 AD-104、AD-109、AD-110、AD-121 至 AD-124、AD-132 至 AD-134 |
| Design Validation | None |
| Conformance Cases | None |
| Capability Evaluation | Build Target Proposal、Source Tool Planning、Candidate Proposal 与 Knowledge Verification 使用模型时分别适用 |

> 概要架构约束直接生效；本文已回填当前上游主题的完整应用契约，但在状态进入 `Accepted` 前，本文新增内容仍是拟议设计，不能作为已批准的生产实现基线。

## 1. 目的与范围

Knowledge Update 是构建和更新一个 KnowledgeScope 软件世界模型的统一应用用例。它接收显式 Build Objective，由平台解析并冻结 Build Intent，协调来源调查、知识构建、独立准入和 Scope 级 Snapshot 发布，最后返回结构化应用结果。

它适用于：

- 一个 Scope 尚无 CURRENT Snapshot 时的首次构建。
- 用户或管理员显式请求刷新知识。
- Scheduler 按配置触发更新。
- Web 任务中的 Task Execution Agent 根据明确 Knowledge Gap 提出更新 Action Proposal；只有 Conversational Task Control 完成授权和分派后才触发更新。CLI / Scheduler 等直接入口必须携带相应写授权。
- 来源变化、上游 Snapshot 变化或 Knowledge Schema 演进触发的显式或计划更新。

首次构建不是独立知识生成路径；它与后续更新的区别只是开始时该 Scope 没有 CURRENT Snapshot。

本文不定义：

- Connector、Artifact、Evidence、Entity、Fact 或 Inference 的内部算法和字段。
- Knowledge Verifier 的审核规则和 Snapshot 的物理事务实现。
- 查询、Semantic View、Sufficiency 或 Answer Review。
- 自动变化监听、持续影响传播或独立 Evolution Orchestrator。
- 某个版本、MVP 或项目的实现范围。

## 2. 职责与数据所有权

### 2.1 Knowledge Update Application Service

负责：

- 校验目标 Scope、Build Objective、Input Binding 和可选 Requirement Binding。
- 解析并固定 DataSourceBinding Definition Revision、上游 Snapshot Reference、Expected Current、目标 Knowledge Schema 和 Capability Catalog Snapshot。
- 将可选 Build Target Proposal 解析为平台拥有的 Canonical Build Target，并连同目标解析凭证、发现边界和覆盖义务冻结到 Build Intent。
- 创建有界 InvestigationRun，管理执行循环、资源政策、继续、停止、取消和应用级重试。
- 接收模型或确定性 Strategy 的 Source Tool Proposal，结合 Knowledge Engine 的 Source Information Need 执行目标包含性、权限、预算和重复动作校验，再规范化为自包含 Source Operation Intent；需要 Derived 表示时，依据冻结 Catalog 另行形成 Artifact Processing Intent。记录提议、授权、执行与观察结果。
- 在每个 Source Tool Step 分派前向 Knowledge Engine 取得 Purpose = `SOURCE_EXECUTION` 的 exact `KNW-SCOPE-STATE-ASSERTION-01`，再调用 Source Integration 的 `ResolveBindingForExecution` 取得 exact Binding Eligibility Assertion；只转交两个 Owner Assertion，不自行判断或缓存长期资格。
- 对本用例拥有的 Build Target、Source Tool、Stop 和其他模型 Proposal，在把它们加入生产 Build Intent、Investigation Working State、Transcript 或 Criterion Assessment 前，消费 `X-MODEL-RESULT-ELIGIBILITY-01`，机械校验 actual Model Fingerprint、Adapter、Authorized Input Manifest / Provider Request Digest、Isolation Receipt 与冻结 Catalog；只记录不合格 Model Call 的审计事实，不封存其领域 Proposal。
- 协调 Evidence Materialization 的 Artifact Read Requirement、完整 Read Package / Read Protection、Artifact Use Requirement 与 Use Confirmation；只转交不解析 Lineage 或 Payload。
- 冻结 Investigation Result，形成来源执行与覆盖条件的权威评估依据；Publication Candidate Manifest 封存后再签发绑定其 Digest 的最终 Criterion Assessment。
- 请求 Knowledge Engine 冻结最终 Candidate Bundle、形成完整 Admission Batch Result，并构建不可变 Publication Candidate Manifest。
- 让各 Criterion Owner 针对该精确 Manifest 形成 Assessment，确定性聚合内部 Acceptance Decision，并映射为 KNW-PUBLICATION-REQUEST-01 的 PASS Acceptance Assertion；仅在 PASS 时提交 Publication Request。
- 接收 Knowledge Engine 的权威 Publication Result，不自行切换 CURRENT 或把结果未知解释为失败。
- 汇总不可变 Knowledge Update Result，并确保失败不污染已有 CURRENT。

不负责：

- 持有来源凭据或直接读取外部来源。
- 解析 Artifact、生成 Candidate 或判断正式知识正确性。
- 替代 Knowledge Verifier 审核 Candidate。
- 执行 Snapshot 原子发布或跨 Scope 分布式事务。
- 宣告原用户任务的知识已经充分。

### 2.2 Source Integration

负责：

- 根据自包含 Source Operation Intent、冻结的 DataSourceBinding 和来源权限执行有界来源操作；不解释上游调查语义。
- 记录真实调用、分页、覆盖、截断、失败和来源 Revision。
- 来源操作产生 Source Operation Result 与 Source Artifact；独立 Artifact Processing 操作产生 Processing Result 与带 Lineage 的 Derived Artifact。
- 按当前访问政策展开并签发完整 Artifact Read Package / Read Protection（`NOT_REQUIRED_NO_EVICTION` 或 `MANAGED_EVICTION` Guard），并签发绑定确切 Materialization / Read Attempt / Package / 用途的 Artifact Use Confirmation。

不负责判断“还需要什么知识”、构造 Evidence 或宣告来源结果足以发布。

### 2.3 Knowledge Engine

负责：

- 根据 Build Intent 和已有信息判断 Source Information Need。
- 准备 Evidence Materialization 与 Artifact Read Requirement；消费授权完整 Read Closure，暂存最低可复核 Evidence Snapshot，并返回 Artifact Use Requirement。
- 在 Use Confirmation 通过后原子形成自包含 Evidence，再构造 Entity / Fact Candidate；在语义前提已解析为正式 Fact / 受控 Inference 后构造 Inference Candidate。Knowledge Engine 不直接调用 Source Integration。
- 冻结 Candidate Bundle，调用与生成隔离的 Knowledge Verifier，形成覆盖完整 Bundle Revision 的 Admission Batch Result。
- 以 Snapshot Builder 构建绑定最终成员、Admission Decision、Continuation、Schema、Expected Current 和上游依赖的 Publication Candidate Manifest。
- 由 Publisher 消费精确 Manifest、PASS Acceptance Assertion 和分类 Publication Preconditions，在单个 KnowledgeScope 的原子边界内完成最终资格检查与发布。

Knowledge Engine 不直接访问 DataSource，也不根据用户任务生成最终答案。

### 2.4 Knowledge Verifier

通过受控只读端口从 Knowledge Engine 权威 Repository 独立重读 Candidate、Evidence Snapshot、Context、Identity、正式前提和 Contract，执行机械校验与语义审核。Knowledge Verifier 不访问 Source Integration，也不重新解析 Artifact Payload；生成 Strategy 不能同时拥有准入权。审核输出 Knowledge Information Requirement 时，由 Knowledge Construction Strategy 将知识缺口解释为 Source Information Need，再由 Application Services 决定是否继续调查。

## 3. 五个不可混淆的应用对象

| 对象 | 所处生命周期 | 所有者 | 回答的问题 |
|---|---|---|---|
| Build Target Proposal | Build Intent 冻结前 | 模型或其他 Strategy 提议 | “建议调查哪些来源范围和知识目标？” |
| Canonical Build Target | Build Intent 冻结前解析并固定 | Application Services；来源身份由 Source Integration Receipt 证明 | “本次被承诺的确切目标是什么，允许在什么边界内发现子目标？” |
| Build Intent | Investigation 开始前 | Application Services | “本次更新实际承诺构建什么、基于什么、受什么限制？” |
| Publication Acceptance Criteria | Build Intent 的组成部分，发布前分别判定 | 条件的数据所有者 | “哪些来源、知识、Schema 和并发条件满足时允许发布？” |
| Knowledge Sufficiency Assessment | 发布后的 Knowledge Use | Application Services / Knowledge Use | “固定 Snapshot 是否满足某版用户任务需求？” |

Proposal 不可信，不能修改用户目标、权限或发布条件；Canonical Build Target 证明目标身份和范围，不证明知识已经构建或 Need 已满足；Build Intent 不能由模型自报；发布成功也不能替代 Sufficiency Assessment。

### 3.1 APP-CANONICAL-BUILD-TARGET-01

Application Services 从 Build Objective、可选 Requirement Binding、Build Target Proposal、Source Integration 的 `SRC-TARGET-RESOLUTION-01` Receipt 和已注册的 Knowledge Schema / Capability Contract 构造 Canonical Build Target。Target 至少固定：

- Target ID / Kind、Canonical Identity、Canonicalization Contract / Version 和 Target Digest。
- 人类可读 Display Label；它仅用于解释，不参与身份、包含性或完成判断。
- owning Scope、DataSource / Binding 或 exact Upstream Snapshot Binding。
- exact Source Target Resolution Receipt；纯知识目标则绑定其 Knowledge Type / Identity Contract 和能够机械判断的 canonical semantic key / predicate，不能只保存自由文本。
- `EXACT | DESCENDANT_DISCOVERY_ALLOWED` Boundary。允许发现子目标时必须给出可机械判断的父目标、允许的 Tool / Target Kind、Context 和深度/数量边界。
- `REQUIRED | SUPPORTING | EXCLUDED` Coverage Obligation，以及该目标所服务的 Build Objective；任务驱动更新还固定 Requirement Revision、Gap 和相关 Need / Joint Constraint Reference。
- Build Objective 对应的版本化 Target Shape Contract / Digest，以及其中要求的目标关系；例如变更影响目标必须固定 exact target revision 和适用 comparison base / parent，不能把任意同类变更知识当作该目标。
- 允许的 Knowledge Kind / Type 和 Publication Criterion Reference。类型只是约束的一部分，不能替代 exact target。

`EXACT` Source Target Resolution Receipt 才能进入 Canonical Build Target。短 Revision、branch、tag、路径片段、同名方法、重载、同名 Controller、自由文本 Endpoint 或模型生成 ID 都只是 Proposal；无法唯一解析时在 Investigation 前失败关闭或请求显式消歧。

对于开放式任务，Build Intent 可以冻结一个 canonical root 与 `DESCENDANT_DISCOVERY_ALLOWED` Boundary，而不预先枚举未知文件。调查中新发现的目标只有在平台机械证明是该 root 的允许后代时才能加入 Investigation Target Set；它不会修改 Build Intent。超出 root、Binding、Context、Target Kind 或发现边界时，当前 Attempt 停止并需要新的 Build Intent / 授权，不能以“相关”作为扩大依据。

Target Shape Contract 决定某类 Build Objective 最低需要哪些 canonical target 关系，不预编码具体项目对象。Git change-impact 等 Strategy 必须先解析 exact target revision 及其适用 parent / base，再以 `REVISION_COMPARISON` 作为 REQUIRED Target；merge、多 parent 或 shallow history 无法唯一确定比较语义时失败或显式要求选择。Changed Object / File Set 可以通过该 Comparison Target 的受控调查发现，但每个成员及 diff Coverage 都必须进入 Coverage Map，不能在 Build Intent 中伪造一份预知文件清单。

Application Services 维护不可变追加的 `Build Target Coverage Map`，把每个 REQUIRED Target 关联到：

`Source Information Need → Source Tool Step → Source Operation / Artifact → Final Candidate Bundle Closure / Disposition → Admission Decision → Publication Candidate Manifest Member`。

Coverage Map 只证明调查和发布产物对应正确目标。它不能以无关同类型知识满足目标，也不能证明原用户 Need 语义充分；后者只由新 Snapshot 上独立的 Knowledge Sufficiency Assessment 决定。

### 3.2 APP-PUBLICATION-POLICY-01：Publication Acceptance Policy

调用方和模型不能直接提交一组任意 Publication Acceptance Criteria。Application Layer 拥有版本化 Publication Acceptance Policy Profile，并根据规范化 Trigger Class、Scope Type、状态形成语义、Target Schema 变化类型和可选 Requirement Binding 选择适用 Profile。

每个 Profile 定义不可删减的最低条件及其判定所有者：

- 来源执行与覆盖条件由 Application Services 依据 Source Operation Result 判定。
- Candidate、Evidence、依赖和一致性条件以 Knowledge Engine 的完整 Admission Batch Result 为权威依据。
- Target Schema、稳定身份、兼容性和目标成员完整性由 Knowledge Engine 针对精确 Publication Candidate Manifest 判定。
- Expected Current、唯一性和本地成员关系在接受阶段只作 preflight；其严格结论由 Knowledge Engine Publisher 在最终 Scope 事务内重验，Application Acceptance 不预言 CAS 成功。
- Execution Eligibility / Revocation、资源和其他当前启用的外部资格由其 Authority Owner 产生带 Revision、Fence 或 observedAt 的分类 Assessment；Application Services 负责汇总，不替代 Owner 判断。
- 资源政策可以阻止继续执行，但不能把未完成条件改写为通过。

Profile 选择必须是平台确定性操作。没有适用 Profile、多个同优先级 Profile 冲突或必要 Evaluator 不可用时，请求在 Investigation 前失败关闭。用户目标或 Requirement 可以增加更严格条件，不能删除、弱化或把 `NOT_EVALUATED` 改成 `PASS`。

Build Intent 只保存 Profile ID/Version 和不可变的 Criterion Definition。每项 Definition 具有稳定 ID、责任 Owner、Evaluator Contract Version 和预期结果。

Snapshot Builder 封存 Publication Candidate Manifest 后，各责任 Owner 才针对该精确 Manifest 产生独立、不可变的 Criterion Assessment，记录 `PASS | FAIL | UNKNOWN | NOT_EVALUATED`、依据、执行状态和版本；若 Assessment 依赖会在发布前变化的条件，还必须记录 `TRANSACTIONAL | FENCED | OBSERVATIONAL` Publication Precondition Class 及相应 Revision / Token / observedAt。先前调查与准入结果可以作为依据，但不能产生一个不绑定最终成员集的通用 PASS。

最终 Publication Acceptance Decision 必须同时绑定 Build Intent Revision、Publication Policy Profile、Publication Candidate Manifest Revision / Digest 和全部 Assessment Digest；只有所有必需 Criterion 均为 `PASS` 才允许请求发布。成员、Admission Closure、Continuation、Schema、Expected Current、上游 Binding 或 Manifest Digest 改变时，必须创建新的 Application Attempt、Manifest 和 Assessment / Decision。Assessment 和 Decision 由 Knowledge Update Result 引用，不能回写或修改 Build Intent；即使 Decision 为 PASS，最终 CAS、唯一约束或 Fence 失败仍返回未发布。

上述 Criterion Assessment 与最终聚合决定共同构成 APP-PUBLICATION-ASSESSMENT-01。

### 3.3 正式交接对象

| 对象 | 产生者 | Application Services 的处理边界 |
|---|---|---|
| Candidate Bundle | Knowledge Engine | 只要求封存该 Application Attempt 唯一 Final Candidate Bundle Seal；不读取或修改候选语义 |
| Admission Batch Result | Knowledge Engine | 必须覆盖最终 Bundle，且 `Completeness = COMPLETE`；不把部分 ACCEPT 拼成伪完整结果 |
| Publication Candidate Manifest | Knowledge Engine / Snapshot Builder | 作为所有发布 Criterion Assessment 的唯一直接对象；不可修改 |
| Internal Publication Acceptance Decision | Application Services | 只按版本化 Policy 机械聚合 Criterion Owner 的结果；不替代 Admission 或 Publication |
| Publication Acceptance Assertion | Application Services | 将 PASS Decision 映射为 KNW-PUBLICATION-REQUEST-01 的公开封套；绑定 exact Manifest 和 Criterion Digests |
| Publication Request / Outcome | Application Services 请求、Publisher 决定 | Request 只使用 Snapshot 公开 Contract；Outcome 是 CURRENT 是否切换的唯一权威答案 |

这些对象形成单向交接。Admission ACCEPT 只允许 Closure 被 Manifest 选择，Application Acceptance PASS 只允许提交该 Manifest，二者都不会产生正式知识。

每个 Application Attempt 只允许一个 Final Candidate Bundle Seal、一个 publication-ready Manifest 和一个 Acceptance Assertion。最终 Bundle 或 Manifest 封存后的任何语义变化一律使用新 Application Attempt，不在同一 Attempt 内维护多个竞争“最终版本”；已形成 Publication Request 时按 3.4 先收口旧请求。

### 3.4 Publication Request 的替换与取消

Application Services 不拥有 Publisher 内部 Fence，也不写 Publication Attempt。每个 publication-ready Manifest 只生成一个符合 KNW-PUBLICATION-REQUEST-01 的不可变 Request；它直接携带本模块已有的 Build Intent / Application Attempt References 作为 opaque correlation，不创建第二套 Construction Attempt。

Manifest、Schema、Expected Current、Admission Batch、Acceptance Assessment 或任何语义输入变化时，Application Services 必须创建新的 Application Attempt。若旧 Attempt 尚未形成 Publication Request，可直接关闭旧 Attempt；若已形成 Request，则先调用 Publisher 的 `CancelPublicationRequest(exact Idempotency Key, Request Digest)`：

- 返回 `NOT_PUBLISHED`：旧请求已被权威收口，可以基于当前状态创建新 Request。
- 返回 `PUBLISHED`：不能假定旧请求未生效；新 Attempt 必须以新 CURRENT 为基线。
- 调用超时或返回 `OUTCOME_UNKNOWN`：只查询同一 Publisher-owned Attempt，未解析前不提交竞争 Request。
- 返回 `IDEMPOTENCY_CONFLICT`：本地 Request 身份或 Digest 有错误，失败关闭并审计。

Publisher 以唯一 Attempt Record 让 Cancel 的 `PREPARED → NOT_PUBLISHED` 与 Publish 的 `PREPARED → PUBLISHED` CAS 竞争，迟到 Submit 不能越过取消 Tombstone。该规则不需要 Application Authority Epoch、Commit Lease、Admission Gate、Abort Proof 或跨 Owner 事务。

## 4. APP-KNOWLEDGE-UPDATE-01 请求语义

请求及规范化过程至少表达以下语义：

| 语义 | 约束 |
|---|---|
| Update Request Identity | 支持应用幂等与 Attempt 追踪；不与 InvestigationRun ID 混用 |
| Target Scope | 引用一个 `ACTIVE` System、Shared Component 或 Business Domain Scope |
| Build Objective | 表达为什么更新、希望覆盖什么和哪些结果不可接受；不等同于来源 Selector |
| Requirement Binding | 仅任务 Gap 触发时绑定不可变 Requirement Revision 和 Gap；其他触发不伪造用户需求 |
| Data Source Input Bindings | 固定 DataSourceBinding ID 与 Definition Revision；运行中配置变化不漂移。每个 Source Tool Step 仍须取得当前 exact Scope State / Binding Eligibility Assertions，不能把请求时 Binding 当作执行资格 |
| Upstream Snapshot Bindings | 固定 KNW-SNAPSHOT-REF-01 定义的完整 Snapshot Reference；不读取动态 CURRENT |
| Expected Current Snapshot | 固定为 `PRESENT(exact Snapshot Reference) | NO_CURRENT`；首次构建显式使用 `NO_CURRENT`，不以空值表达“不在意” |
| Target Knowledge Schema | 固定本次候选 Snapshot 的 Schema Reference |
| Capability Catalog Snapshot | 固定可使用的 Capability Contract、Strategy、Tool 和版本 |
| Build Target Proposal | 可选且不可信的来源范围和知识目标建议；不能直接进入来源执行或发布门禁 |
| Canonical Build Target Manifest | 固定全部 REQUIRED / SUPPORTING / EXCLUDED Target、Resolution Receipt、发现边界、Coverage Obligation 和 Target Digest |
| Publication Policy Selection Context | 提供 Trigger Class、状态形成语义和其他选择 Profile 所需的受控条件；调用方不能直接删除或弱化 Criteria |
| Resource Policy | 固定时间、模型、Token、Tool、来源读取、输入体积、并发和成本限制 |
| Trigger Information | 记录用户、Agent、Scheduler、来源、上游依赖或 Schema 变化等触发原因；由重验证诊断触发时固定 exact `KNW-REVALIDATION-SIGNAL-01` Reference；触发信息不改变知识性质，也不是执行授权 |
| Schema Transition | 固定 `INITIAL | UNCHANGED | ADOPTION`、exact target Schema 与构建前 Schema Selection Receipt；只有 ADOPTION 再固定 Evolution Plan，final Target Validation 在 Manifest 形成后执行 |
| Execution Control Envelope | 贯穿 Application、Capability、模型、Tool、Connector 和审核的关联与控制上下文，不包含 Publisher 私有 Fence |

触发原因是可扩展追溯信息，不冻结为决定领域语义的封闭枚举。

## 5. APP-BUILD-INTENT-01

### 5.1 形成规则

Application Services 根据以下输入规范化 Build Intent：

- Build Objective 和可选 Requirement Binding。
- Canonical Build Target Manifest；任务驱动更新必须把 Gap / Need Binding 落到具体 REQUIRED Target，非任务更新不得伪造 Need Binding。
- Scope 类型与当前状态。
- 已冻结的 DataSourceBinding 和 Upstream Snapshot Binding。
- Expected Current、Target Knowledge Schema、Transition Mode 与成功的 Schema Selection Receipt；ADOPTION 还固定 Evolution Plan Reference。
- 可用 Capability Catalog Snapshot。
- 平台解析得到的 Publication Acceptance Policy Profile、物化 Criteria 和 Resource Policy。
- Build Target Proposal 只作为解析输入；Build Intent 保存平台重建的 Canonical Build Target、Resolution Receipt 和发现边界，不保存可执行的模型自报目标。
- 可选 `KNW-REVALIDATION-SIGNAL-01` 只作为目标和调查约束输入；Application Services 必须重新解析当前权威状态，不能把 Signal 当作 Evidence、结论或自动传播命令。

Build Intent 形成后不可原地修改。调查发现原 Intent 无法完成时，当前运行受控停止；如果仍在原始任务边界内需要改变 canonical root、Coverage Obligation、发现边界或知识目标，则创建新的 Intent Revision 和新的 Investigation Attempt，不能让模型在运行中静默扩大范围或把 REQUIRED Target 降为 SUPPORTING。父目标允许范围内发现的新子目标只追加到 Investigation Target Set，并保留父 Target / Resolution 关系。

### 5.2 状态形成语义

Build Intent 必须说明候选 Snapshot 如何形成完整状态，而不是暴露一个简单“全量/增量”算法开关：

| 语义 | 约束 |
|---|---|
| Replacement | 目标完整 Snapshot 状态表示该 Scope 在目标 Schema 下的一版完整替换；不能隐式继承未重验证知识 |
| Enrichment | 以 Schema 和 Context 兼容的确切 Base Snapshot 为基础，保留未受影响的正式知识及其依赖，并加入或替换已验证目标知识 |

来源是否逐文件重读、Artifact 是否复用和 Candidate 如何计算属于执行 Strategy。目标限定调查通常可以形成 Enrichment，但只有在平台证明 Base Schema、Context 和受影响范围兼容时才允许；否则必须扩大重验证或采用 Replacement。

Schema 演进使用正常 Build Intent：语义保持型迁移或基于来源/正式前提的重建都只产生 Candidate，不能原地修改 CURRENT，也不能只重建 Projection。

## 6. APP-INVESTIGATION-01

### 6.1 InvestigationRun 与 Investigation Result

InvestigationRun 是 Application Layer 拥有的有界执行状态，至少固定：

- Build Intent 和 Attempt 身份。
- Canonical Build Target Manifest、动态发现但仍位于允许边界内的 Investigation Target Set，以及 Build Target Coverage Map。
- Execution Control Envelope 与剩余资源。
- 已提出并处理的 Source Information Need、Source Tool Proposal / Authorization / Step / Observation。
- Source Operation / Artifact Processing Result、Artifact 引用和实际覆盖。
- Artifact Read Requirement、Logical Read Key / Read Attempt、Package / Read Protection / Closure、Evidence Materialization Result、Artifact Use Requirement 与 Use Confirmation。
- Capability、模型、Tool、Connector 与 Strategy 执行引用。
- 失败、重试、截断、取消和停止原因。

InvestigationRun 关闭后产生不可变 Investigation Result。Result 只证明本次调查实际做了什么，不宣告 Candidate 正确、Snapshot 可发布或用户 Requirement 已满足。

### 6.2 APP-SOURCE-TOOL-STEP-01：Source Information Need 与 Tool Loop

Source Information Need 是 Knowledge Construction Strategy 对缺失来源信息的领域描述；Source Tool Proposal 是模型或确定性 Planner 对“下一步如何取得该信息”的不可信执行建议。二者不能互相替代，模型也不能通过直接提出 Tool 跳过 Knowledge Engine 对所需信息的判断。

`list / search / read / compare / query / read-window` 属于 Source Integration 的来源 Tool。Candidate 状态、Verification Preview 和修正反馈由 Knowledge Engine 的受控调查接口提供，不伪装成 Source Tool，也不让 Source Integration 读取 Candidate Repository；Planner 可以在下一次 Authorized Input Manifest 中同时看到两类受控 Observation。

每个 Source Tool Proposal 至少包含：

- Proposal ID、当前 Investigation State Revision / Digest 和所服务的 Source Information Need。
- exact Canonical Build Target 或已证明位于其发现边界内的 Investigation Target Reference。
- 建议的 Source Operation Class、Provider Tool Contract、规范参数、Range / Cursor / Revision / Comparison 和预期信息增益。
- Proposal Capability / Strategy / Model Call Reference；模型自报的权限、完成度、成本和 canonical identity 不可信。

Application Services 对每个 Proposal 形成唯一 `ALLOW | DENY | REQUIRE_TARGET_RESOLUTION` Authorization Decision。只有同时满足以下条件才允许执行：

- Proposal 仍绑定当前 Build Intent、Investigation Revision 和未关闭的 Source Information Need。
- Target 具有 exact Resolution Receipt，或新目标能被机械证明位于允许的 descendant discovery boundary；否则先调用 `SRC-TARGET-RESOLUTION-01`。
- Source Operation / Tool、参数、Range、Cursor 和返回上限位于 Capability Catalog、Binding Selector、Context、数据分类和剩余 Resource Policy 内。
- 当前 `SOURCE_EXECUTION` Scope State Assertion 与 Binding Eligibility Assertion 均存在、Digest / Purpose / Scope / DataSource / Binding Revision exact 匹配；缺失或失配时不形成 ALLOW。
- Canonical Action Key 没有构成无进展重复，当前 Execution Eligibility 没有被撤销。

允许后形成不可变 Source Tool Step：

1. Application Services 在每个 Source Tool Step 真正 dispatch 前调用 Knowledge Engine 的 `ReadScopeStateAssertion(SOURCE_EXECUTION, exact Scope Revision)`，再以该 Assertion 调用 Source Integration 的 `ResolveBindingForExecution(exact Binding Revision)`。两者成功后，才把已授权 Proposal、exact Scope Assertion 和 Binding Eligibility Assertion 规范化为不携带 Need 文本或下游知识语义的 Source Operation Intent；Source Integration 在自身分派边界再次重验 Assertions、权限、目标和资源。Assertion 缺失、Purpose / Digest / Revision 失配或资格变化使当前 Step 失败关闭；只有冻结 Build Intent / Binding 未变且上游允许暂态重试时才重新取得新 Assertion，不能原地替换已经 dispatch 的 Step 输入。
2. Source Integration 执行 `list / search / read / compare / query / read-window` 等已注册、可扩展 Tool Contract，返回 Source Operation Result 与可选 Source Artifact Reference。Tool 类别是能力语义，不是固定 Provider 实现清单。
3. 如果所需表示不能由 Source Artifact 直接提供，Application Services 从冻结 Catalog 解析确切 Processing Strategy，提交独立 Artifact Processing Intent；Source Integration 返回 Processing Result 与可选 Derived Artifact Reference，不能依据目标 Kind 自行选择 Strategy。
4. Application Services 构造 Source Tool Observation，固定 Step、Operation / Processing Result、Coverage / Cursor / Truncation、Artifact Envelope / Content Digest、失败和剩余预算。Observation 中可供下一轮模型理解的内容必须经过 Source Integration 授权的有界 Artifact Read / Processing，并作为下一次 Model Call 的 `AI-AUTHORIZED-INPUT-MANIFEST-01` 项；Application Services 不解释或复制 Payload。
5. 每次 Planner 模型调用使用 `NO_EXTERNAL_ACCESS` Provider Runtime。模型只输出下一步 Proposal 或 Stop Proposal；平台在模型调用结束后独立授权和执行，因此不存在模型直接访问 shell、文件、Web、MCP、Connector 或工作区的旁路。
6. 模型响应完成后，拥有该 Proposal 的 Capability Owner 必须先执行 `X-MODEL-RESULT-ELIGIBILITY-01`。只有 `PRODUCTION` Catalog、post-call eligibility 通过且 Proposal 通过领域 Contract 校验时，Application Services 才能封存 Source Tool / Stop Proposal、Authorization 输入和对应 Investigation State Revision；不合格响应只保留在隔离 Model Call /审计记录中，并使当前 Capability Attempt 失败，不能通过重新解释为确定性 Proposal 继续。
7. Application Services 将 Observation 和 Target Coverage 追加到 Investigation Working State，再让 Knowledge Construction Strategy 继续 Candidate 构建、提出新 Need 或停止。
8. 对可能支持 Candidate 的 Artifact，Application Services 按原有边界协调 Evidence Materialization：Knowledge Engine 产生 Artifact Read Requirement，Source Integration 返回完整 Read Package / Read Protection，Knowledge Engine 暂存最低 Evidence Snapshot 并请求 Use Confirmation，确认后原子形成自包含 Evidence。
9. 只有成功 Evidence 才进入 Entity / Fact Candidate；Inference 仍必须满足正式前提规则。Source Operation Result、Tool Observation、模型 Stop Proposal 和 Investigation Transcript 均不能直接成为 Candidate、Fact、Inference 或 Answer。

Source Tool Step 的模型调用、Proposal、Authorization、Target Resolution、Source Operation、Observation 和状态前后 Digest 共同形成可回放 Investigation Transcript。Transcript 是应用执行记录，不是 Artifact、Evidence、正式知识或答案依据。

### 6.3 预算、进展与停止

Resource Policy 不硬编码统一阈值，但必须为每个 Investigation 固定可机械扣减的上限：

- Planner / Candidate / Correction 等各类模型调用次数及总 Token / 字符 / 成本。
- Source Tool Step、外部分派、分页、比较和 Artifact Processing 次数。
- 不同 Source Object / 文件、Artifact、总读取字节 / 字符、单次返回、扫描量和派生内容体积。
- 总时长、并发数和 Provider 配额。

阈值由版本化 Policy / Strategy Profile 和 Capability Evaluation 决定；模型不能申请扩容。每个子操作在分派前从父 Allocation 原子取得额度，实际消耗单调结算，失败和未知结果不能按零处理。

开放式调查默认从 canonical root、Revision / Comparison 元数据和最小搜索结果开始，根据 Observation 渐进读取。空 Target / Selector 不能解释为全部，首次 Step 也不能因“可能相关”物化整个 DataSource 或仓库。一次性批量读取只允许作为已通过同一 Capability Contract 评测的窄任务 Strategy，且仍受显式 Target、Coverage 和输入体积预算约束。

Canonical Action Key 至少覆盖 Tool Contract、exact Target、规范参数、Range / Cursor / Revision、查询和 Investigation State Digest。相同 Key 在没有新 Cursor、Target、权限 Revision 或明确暂态重试依据时再次出现，视为重复动作。平台同时追踪新增 Artifact / Content Digest、Coverage、Candidate Closure 和 unresolved Need 是否发生进展。

满足任一条件即停止或关闭循环，并记录唯一原因：

- 全部 REQUIRED Build Target 已达到 Publication Policy 要求的 Coverage / Disposition，Knowledge Construction Strategy 不再提出未解决 Source Information Need。
- 预算或时间耗尽、调用取消、Execution Revocation、权限 / Provider 失败且政策不允许重试。
- Target NOT_FOUND / AMBIGUOUS / OUT_OF_SCOPE 且无法在冻结边界内消歧。
- 连续动作没有新增 Artifact、Coverage、Candidate 或信息增益，或检测到无依据重复动作。
- 模型提出 Stop，但平台只在 REQUIRED Target、未解决 Need、Coverage 和 Candidate 状态与停止条件一致时接受；模型不能自报“完成”。

预算耗尽、无进展和来源失败都是真实 Investigation Outcome，不能静默扩大到全仓库、换用未授权来源、截断后宣称完整或把未知写成无结果。

### 6.4 来源侧发布条件

Investigation Result 冻结后，Application Services 根据真实记录形成来源侧 Publication Acceptance Criteria 的评估依据；Publication Candidate Manifest 形成后，必须再确认其成员、依赖与本次来源覆盖一致，才签发绑定 Manifest Digest 的最终 Assessment。例如：

- 所有 REQUIRED Canonical Build Target 是否在 Build Target Coverage Map 中具有与 exact Source Operation、Artifact、Candidate Disposition 和 Manifest Member 一致的闭包；无关同类型知识不能填充该映射。
- 所有必需 Source Information Need 是否完成。
- 必需来源范围是否已读取，分页是否结束。
- 是否存在未允许的失败、空选择、截断或预算耗尽。
- Artifact 是否引用正确 Binding Revision、来源 Revision 和 Context。
- Artifact Read Package / Read Protection 是否覆盖确切 Artifact / Lineage Closure、Range、Digest 和用途，且每个持久使用都有绑定当前 Materialization / Read Attempt 的 Artifact Use Confirmation；Guard 有效期只适用于 `MANAGED_EVICTION`。
- Knowledge Engine 声明必需的 Evidence 是否都已成功提交充分、自包含的最小快照；当前不接受外部 Artifact Payload 长期保留替代该条件。
- Schema Selection Receipt 是否绑定 Build Intent，Final Schema Target Validation Receipt 是否绑定 exact Manifest；ADOPTION 时 READY Package / Publication Closure 是否绑定同一 Application Attempt、source Snapshot、target Schema 和 Candidate / Admission Digests。
- Scope、DataSource、Binding、Secret 和权限在发布前是否仍满足 Profile 规定的执行资格；Execution Revocation 必须导致相应条件失败。

模型的“调查完成”陈述不能替代这些判断。来源侧条件通过也不代表知识侧条件通过。

## 7. 主流程

```mermaid
sequenceDiagram
    participant C as Caller
    participant A as Knowledge Update Application Service
    participant S as Source Integration
    participant K as Knowledge Engine
    participant V as Knowledge Verifier
    participant M as Model Gateway

    C->>A: Knowledge Update Request
    A->>A: Resolve immutable bindings, CURRENT, Schema, Catalog
    A->>S: Resolve proposed source targets within binding
    S-->>A: Exact Target Resolution Receipts or explicit ambiguity/failure
    A->>A: Normalize and freeze Build Intent
    loop While unresolved and within policy
        A->>K: Continue construction with formal Base, Evidence/Candidate state and Artifact envelopes
        K->>V: Preview Candidate for bounded gap discovery
        V-->>K: Verification Preview / information requirement
        alt Source information is required
            K-->>A: Source Information Need
            opt Model-primary or hybrid planning Strategy
                A->>M: NO_EXTERNAL_ACCESS planning call with frozen input manifest
                M-->>A: Untrusted Source Tool Proposal
            end
            A->>A: Obtain model or deterministic Source Tool Proposal
            A->>A: Bind target; check scope, eligibility, duplicate action and budget
            opt Discovered target needs canonical resolution
                A->>S: Resolve target inside frozen discovery boundary
                S-->>A: Exact Receipt or explicit failure
            end
            A->>K: ReadScopeStateAssertion(SOURCE_EXECUTION)
            K-->>A: Exact Scope State Assertion
            A->>S: ResolveBindingForExecution(assertion, exact binding)
            S-->>A: Exact Binding Eligibility Assertion
            A->>S: Authorized Source Operation Intent + assertions
            S->>S: Validate assertions and source/binding fence at dispatch
            S-->>A: Source Operation Result + optional Source Artifact refs
            opt Derived representation is required
                A->>S: ProcessArtifact(intent + frozen Strategy)
                S-->>A: Processing Result + optional Derived Artifact refs
            end
            A->>A: Append Tool Observation and Target Coverage
            A->>K: PrepareEvidenceMaterialization(artifact envelopes)
            K-->>A: Materialization Ref + Artifact Read Requirement
            A->>S: OpenArtifactRead(requirement)
            S-->>A: Complete Artifact Read Package + Read Protection
            A->>K: ContinueMaterialization(package)
            K-->>A: Artifact Use Requirement + Staged Manifest
            A->>S: ConfirmArtifactUse(exact read attempt/package/requirement)
            S-->>A: Artifact Use Confirmation
            A->>K: FinalizeMaterialization(confirmation)
            K-->>A: Evidence refs or terminal failure
        else No source call is required
            K-->>A: Construction state / completion reason
        end
    end
    A->>A: Freeze Investigation Result
    A->>K: Freeze final Candidate Bundle and run Admission
    K->>V: Verify final Closure revisions from controlled read ports
    V-->>K: Verification assessments or information requirements
    K-->>A: Complete Admission Batch Result
    A->>K: Build Publication Candidate Manifest from selected ACCEPT closures
    K-->>A: Immutable Manifest revision and digest
    A->>K: ValidateSchemaTarget(selection receipt, exact manifest)
    K-->>A: Final Schema Target Validation Receipt
    A->>A: Criterion owners assess the exact Manifest
    A->>A: Aggregate Decision and issue Acceptance Assertion
    alt All required criteria PASS
        A->>K: SubmitPublication(request + selection/final schema receipts)
        K->>K: Recheck eligibility and atomically publish one Scope
        K-->>A: PUBLISHED / NOT_PUBLISHED / OUTCOME_UNKNOWN
    else Any criterion not PASS
        A->>A: Close without Publication Request
    end
    A-->>C: Immutable Knowledge Update Result
```

该时序表达职责和门禁，不要求内部采用同步流水线。Knowledge Engine 可以在每批 Artifact 后增量构建 Candidate，并执行无准入效力的 Verification Preview；但每个 Application Attempt 只能封存一个 Final Candidate Bundle Seal，最终 Batch 必须覆盖每个 Closure 的唯一终态，只有 `COMPLETE` Batch 可以进入唯一 Manifest。Seal 后出现新信息时创建新 Application Attempt；旧 Publication Request 已存在时，先按 3.4 精确取消或解析 Outcome，不能靠本地标记让迟到请求失效。

## 8. Admission、冲突与发布边界

### 8.1 Candidate 与正式知识

- 模型或确定性 Strategy 可以从 Artifact 中发现 Entity、Fact 或 Inference Proposal；Knowledge Engine 只使用 Artifact/Evidence 构造 Entity 与 Fact Candidate。
- Inference Proposal 只有在每个语义前提解析为固定已发布 Snapshot 中的正式 Fact / 受控 Inference 后，才能构造 Inference Candidate。Artifact、Evidence、Fact Candidate，以及同一目标 Snapshot 中尚未发布的对象只能用于发现、局部身份替换与原子提交，不能成为 Inference 的语义前提。
- Knowledge Verifier 独立审核并形成 `ACCEPT` Admission Decision 后，相应 Closure 才有资格被 Publication Candidate Manifest 选择；它们仍不是已发布 Snapshot 成员。
- 拒绝、未决、缺少 Evidence 或依赖无效的 Candidate 不进入正式状态。
- Candidate、Investigation 工作状态和模型输出不能被正常 Knowledge Use 查询。
- 最终 Admission Batch Result 必须完整覆盖冻结 Candidate Bundle 中的 Closure、未解析项和构建失败项；Application Services 不得只挑出成功项后宣称整个 Bundle 已完成。

### 8.2 来源分歧

来自不同来源、带各自 Evidence 和 KnowledgeContext 且分别通过准入的独立 Fact 可以共同进入 Publication Candidate Manifest。来源分歧不能被自动覆盖，也不自动阻止发布。

只有正式 Fact 在可比较的目标、维度和 Context 中被验证为互不兼容时，才能形成 Conflict Inference Candidate；其完成独立准入后才可正式声明冲突。

### 8.3 Scope 级发布

- 一次 Knowledge Update 只发布一个 Target Scope。
- Knowledge Engine 对该 Scope 独占最终知识、Schema、依赖和并发检查及原子 CURRENT 切换。
- 不同 Scope 可以并行更新；不存在全局 CURRENT、全局发布锁或跨 Scope 分布式事务。
- 跨 Scope Candidate 固定引用确切上游 Snapshot；上游随后发布新 CURRENT 不会改变本次依赖。
- Expected Current 不匹配时拒绝陈旧发布。调用方可以根据明确政策开始新的 Attempt，但不能静默覆盖较新状态。
- 发布前条件按 `TRANSACTIONAL | FENCED | OBSERVATIONAL` 分类。Application / Management 传入 Execution Eligibility / Revocation 等 Authority Assessment；Publisher 不反向查询 Activation Repository，不把 observedAt 观察伪装为提交时不变量。
- `TRANSACTIONAL` 条件在 Scope 原子事务中重验；`FENCED` 条件必须有覆盖提交边界的权威 Revision / Lease / Fence；`OBSERVATIONAL` 条件只能按冻结 Freshness / Risk Policy 接受或拒绝。
- 撤权不改写已冻结定义。Source Integration 在分派边界后不得开始新的调用；已经越过分派边界的调用可以受控完成，但其结果必须标记撤权竞态并由 Profile 重新判定是否可用于发布。
- 发布失败时已有 CURRENT 保持不变；首次构建失败时继续保持无 CURRENT。

上游 CURRENT 变化后，下游继续绑定被保留的旧上游 Snapshot，或显式暴露依赖过期；完成重验证或重建后，再通过新的下游 Snapshot 收敛，不能原地修改旧 Snapshot。

## 9. APP-UPDATE-RESULT-01

Knowledge Update Result 至少分离以下结果维度：

| 维度 | 必须回答 |
|---|---|
| Request | 请求是否被接受，幂等请求是否复用了既有逻辑结果 |
| Execution | Attempt 是否完成、失败、取消、超时或预算耗尽 |
| Investigation | Result 是否冻结，Canonical Build Target、Tool Step、来源调用、覆盖、分页、截断、停止原因和失败如何 |
| Knowledge | 最终 Candidate Bundle / Admission Batch 是否完整，哪些 Closure 准入、拒绝、未决或因缺少依据未形成 |
| Publication | 是否形成精确 Publication Candidate Manifest、Application Acceptance 是否 PASS、是否切换 CURRENT、未发布原因是什么 |
| Versioning | 更新前后可选 CURRENT、Target Schema、Binding、上游 Snapshot、Capability 和 Strategy 版本是什么 |
| Resource | 调用、Token、时间、Tool、Connector、Resource Allocation / Settlement 与原始 Usage / Charge / Meter 的汇总引用；Telemetry Valuation 由其自身索引关联，不回写本 Result |
| Task Impact | 若存在 Requirement Binding，是否需要在新 Snapshot Read Session 上重新调查；不得直接声明已满足 |

“执行完成”“形成已准入候选”“Snapshot 发布成功”和“用户任务满足”是四个不同判断，不能压缩为一个 `success`。未发布的 ACCEPT Closure 仍不是正式知识。

Knowledge Update Result 是不可变 Result Revision。若 Publication 最初为 `OUTCOME_UNKNOWN`，后续只能依据权威 Publication Receipt / Request Idempotency Key 形成新的 `Publication Outcome Resolution Result` 并引用原 Result；不能回写旧 Result，也不能把超时本身改写为 `NOT_PUBLISHED`。对外查询可以返回最新解析状态，但必须保留完整 Revision 链。

### 9.1 Result 交付断言

Knowledge Update Result Owner 实现 `X-RESULT-DELIVERY-ASSERTION-01` 的 `ValidateResultDelivery`。请求必须固定 exact Result Revision / Digest、准备披露的字段路径、Caller / Request / Purpose / Classification 和 Task Revision。Owner 重读原 Update Attempt、最新 Publication Outcome Resolution、Publication Receipt、权限与数据分类后，逐字段返回 `ALLOW | DENY` Assertion，并固定全部依赖 Revision。

Assertion 不重新执行更新，不把 `OUTCOME_UNKNOWN` 推测为成功或失败，也不允许通过旧 Result 文本绕过最新解析状态。Artifact / Evidence 内容、凭据、模型上下文和未获准披露的内部 Candidate 不属于 Update Result 可交付字段。

## 10. 状态、幂等、取消与恢复

Knowledge Update 以一个应用 Attempt 协调多个内部状态机；不得用单一 `success` 覆盖它们：

| 状态维度 | 必须区分的语义 |
|---|---|
| Update Attempt | `PREPARING → INVESTIGATING → FINALIZING_BUNDLE → ADMITTING → BUILDING_MANIFEST → ASSESSING_PUBLICATION → PUBLISHING → COMPLETED`；任一提交前阶段可按规则进入 `FAILED | CANCELED` |
| Investigation | `NOT_STARTED | RUNNING | FROZEN`；冻结后不可追加 Source Result / Artifact 或改写覆盖结果，继续调查使用新 Investigation Revision / Attempt |
| Admission | `NOT_STARTED | RUNNING | COMPLETE | INCOMPLETE | EXECUTION_FAILED`；只有最终 Bundle 的 `COMPLETE` Batch 可继续 |
| Publication | `NOT_REQUESTED | MANIFEST_BUILT | ACCEPTANCE_FAILED | READY | PUBLISHING | PUBLISHED | NOT_PUBLISHED | OUTCOME_UNKNOWN`；进入 `PUBLISHING` 时记录 Publisher-owned Attempt Reference；其权威状态只有 `PREPARED | PUBLISHED | NOT_PUBLISHED`，`OUTCOME_UNKNOWN` 只是调用超时视图 |

约束如下：

- 同一 Update Request Identity 和等价请求返回同一逻辑更新；重新调查必须创建新的 Application Attempt。
- 每个 Application Attempt 固定 Build Intent、Input Binding Revision、Expected Current、Schema、Capability Catalog、Publication Policy 和资源政策。
- Publication Candidate Manifest 封存后，任何成员、Closure、Continuation、Binding 或 Digest 变化都必须创建新 Application Attempt、Final Bundle Seal 和 Manifest，并重新聚合 Acceptance；不能在同一 Application Attempt 原地修补或形成第二个最终 Revision。
- 暂态来源或 Provider 错误只能在剩余预算和明确政策内重试；每次重试单独记录。
- 进程中断后，只能从已经持久化且依赖版本未变化的阶段恢复。无法证明状态一致时关闭旧 Application Attempt，并创建引用旧结果的新 Application Attempt。
- 取消首先阻止新的模型、Tool 和 Connector 调用。已经进入原子发布事务时不能得到“已取消且未发布”的虚假结果，必须等待事务结果并如实返回。
- Publication 为 `OUTCOME_UNKNOWN` 时，当前 Lineage 不签发可提交的替代 Application Attempt，直至权威 Outcome 被解析。
- 失败 Attempt 产生的 Artifact 可以按其自身保留策略复用；Candidate 是否可复用由知识主题判断，不能因为来源昂贵就绕过重新验证。

### 10.1 失败分类与重试权

| 类别 | 典型原因 | 自动处理边界 |
|---|---|---|
| REQUEST_REJECTED | Scope、Binding、Schema、Objective、Policy Profile 或幂等请求无效 | 不开始 Investigation；调用方修正 |
| BUILD_TARGET_NOT_CANONICAL | 缺少 exact Resolution Receipt、目标自由文本化或身份闭包不完整 | 不冻结 Build Intent；重新解析或显式消歧 |
| BUILD_TARGET_AMBIGUOUS / NOT_FOUND | 短 Revision、同名/重载对象、多候选或目标不存在 | 不选择相近项；返回候选/失败并关闭或等待授权澄清 |
| BUILD_TARGET_OUT_OF_SCOPE | 目标或发现子目标超出 root、Binding、Context 或 Target Kind Boundary | 拒绝 Proposal；不扩大到全仓库/全来源 |
| SOURCE_TOOL_PROPOSAL_DENIED | Tool、参数、Range、目标、权限或预算不在冻结 Catalog / Intent 内 | 记录 DENY；只允许在原边界内重新提议 |
| SOURCE_EXECUTION_ELIGIBILITY_INVALID | `SOURCE_EXECUTION` Scope State Assertion 或 Binding Eligibility Assertion 缺失、陈旧、Purpose / Digest / Revision 失配 | 不 dispatch；只在冻结 Build Intent / Binding 未变且政策允许时重新取得资格 |
| SOURCE_TOOL_NO_PROGRESS | 无新 Artifact / Coverage / Candidate / Need 进展或重复 Canonical Action | 受控停止；不能靠重复调用或扩大范围追求完成 |
| MODEL_ISOLATION_UNSUPPORTED | Planner / Candidate / Criterion 模型调用无法取得有效 Isolation Receipt | 不调用或隔离结果；不得进入 Investigation State、Candidate、Assessment 或生产结果 |
| MODEL_RESULT_NOT_ELIGIBLE | actual Model / Adapter、Manifest / Request Digest、Isolation Receipt 或 Qualification 不符合冻结 Catalog | Capability Attempt 失败；不封存 Build Target / Tool / Stop Proposal 或模型生成的 Criterion Assessment，不推进依赖它的 Investigation / Acceptance 状态 |
| EXECUTION_REVOKED | Scope 退休、Source 禁用/退休、Binding 挂起/退休、Secret 或权限撤销 | 立即停止新外部调用；当前 Attempt 不自动重启 |
| DEPENDENCY_UNAVAILABLE | 必需 Provider、Capability、Tool、上游 Snapshot 或 Evaluator 不可用 | 只在政策和剩余预算内重试暂态故障 |
| RESOURCE_EXHAUSTED | 时间、调用、Token、来源读取或成本预算耗尽 | 受控关闭，不能扩大预算或宣称覆盖完成 |
| SOURCE_INCOMPLETE | 必需 Need、分页、范围或 Artifact 未完成 | 来源侧 Criterion 失败；按新 Attempt 补充 |
| ARTIFACT_ACCESS_FAILED | Read Closure 不完整、授权被拒、Read Protection 失效、Payload 不可用或 Use Confirmation 失败 | 不形成 Evidence；`MANAGED_EVICTION` Guard 过期时用新 Materialization 从头开始 |
| ARTIFACT_PROCESSING_FAILED | 冻结 Strategy、父 Artifact、Lineage 或模型加工失败 | Source Artifact 保持有效；不由 Source Integration 隐式换 Strategy |
| MATERIALIZATION_BINDING_MISMATCH | Read / Use Confirmation 与 Materialization、Request Digest、Read Attempt、Package 或 Closure 不一致 | 失败关闭，不串用确认或自动改绑 |
| MATERIALIZATION_OUTCOME_UNKNOWN | Finalize 响应丢失或提交结果未知 | 查询同一 Materialization；PENDING_CONFIRMATION 才重放相同 Finalize，SUCCEEDED 返回原 Receipt |
| CONSTRUCTION_FAILED | Contract、Context、身份、依赖或 Candidate 构建失败 | 不通过重复模型调用掩盖确定性错误 |
| ADMISSION_BLOCKED | Batch 不完整，或必需 Candidate 被拒绝、未决、构建失败、补证未完成 | 不构建可发布 Manifest；补证必须进入有界调查或新 Attempt |
| MANIFEST_INVALID | Manifest 未绑定最终完整 Batch、成员/Continuation/Disposition 不完整或 Digest 失配 | 关闭当前 Attempt；新 Application Attempt 重新封存 Bundle 与 Manifest |
| PUBLICATION_CRITERIA_FAILED | 任一必需 Criterion 为 FAIL / UNKNOWN / NOT_EVALUATED | 不发布，不允许调用方弱化条件重试 |
| CURRENT_CONFLICT | Expected Current 已陈旧 | 不覆盖；重新读取后创建新 Attempt |
| PUBLICATION_OUTCOME_UNKNOWN | 提交后无法确认原子事务结果 | 先按 Attempt ID 查询权威发布记录，禁止盲目重复提交 |
| CANCELLED | 调用方或控制策略取消 | 停止新工作；如已进入发布事务则返回真实事务结果 |

Application Services 只拥有应用级继续、停止和重试决定；Source Integration、Capability、Verifier 和 Knowledge Engine 分别报告其权威失败，不由 Application Service 重解释为成功。同一 Application Attempt 内只重试明确暂态且不改变冻结输入的步骤；需要改变 Intent、Binding、Schema、CURRENT 基线或 Policy 的处理都创建新 Application Attempt。

## 11. AI Native 执行边界

模型适合承担：

- 从 Build Objective 建议 Build Target Proposal。
- 在 Knowledge Construction Strategy 内辅助识别 Source Information Need，并针对明确 Need、已有 Artifact / Candidate 状态和上一步 Observation 提出下一步 Source Tool Proposal。
- 从非结构化 Artifact 提出 Evidence、Entity、Fact 和 Inference Proposal。
- 在 Knowledge Verifier 中进行与生成阶段隔离的语义审核。

上述每项模型能力都必须由拥有相应领域输出的 Capability Owner 在生产封存点执行 `X-MODEL-RESULT-ELIGIBILITY-01`。Application Services 对自己拥有的 Build Target / Tool / Stop Proposal 和模型辅助 Criterion Assessment 负责；Source Integration、Knowledge Engine 与 Knowledge Verifier 分别对自身 Processing、Candidate / Evidence 和 Verification 输出负责。上游只消费带 exact Model Call、Eligibility Result、Catalog 和 Qualification Proof Reference 的合格结果，不以 Gateway 调用完成、形状有效或调用方摘要替代 post-call 门禁。

平台必须控制：

- Build Objective、Canonical Build Target / Resolution Receipt、Scope、Binding、Snapshot、Schema、Capability、Tool 和预算边界。
- Source Tool Proposal 的授权、执行、观察、重复动作检测、停止和 Build Target Coverage Map；模型调用本身不持有外部访问能力。
- Artifact Lineage、Evidence 定位、稳定身份和 Context。
- Proposal 到 Candidate 的构造、机械校验和独立审核。
- Publication Acceptance Criteria 各责任分区和 Scope 级发布事务。

任何 Model-Primary 或 Hybrid Strategy 都走同一 APP-KNOWLEDGE-UPDATE-01 路径。随着模型增强，可以经 Capability Evaluation 减少特定项目、语言、文档格式、固定 Builder 和模型版本的启发式规则或 Prompt 分支，并让模型更动态地提出 Target / Tool / Candidate Proposal；canonical identity、Target Boundary、预算、稳定身份、Lineage、Context、权限、Admission、Manifest、Publication Acceptance 和原子发布等平台控制不能退化给模型，也不能增加直接来源回答旁路。

## 12. 可观测性、资源与敏感信息

- Update、Canonical Build Target / Resolution、Investigation、Capability、Model Call、Tool Proposal / Authorization / Step / Observation、Connector、Verifier 和 Publication 传播同一 Correlation 链及父子关系。
- Application Services 记录分配和剩余预算；执行边界报告实际消耗，不能自增预算。
- Knowledge Update Result 只包含用量和审计引用，不复制敏感 Payload、凭据或模型完整上下文。
- 记录对正式结果有实质影响的 Artifact、Binding、Schema、Capability、Strategy 和模型版本。
- Telemetry 不参与 Candidate 准入、发布或 Sufficiency 判断。

## 13. 拟议不变量

1. 首次构建和后续更新复用同一 Knowledge Update 契约。
2. 更新只能由显式应用动作触发；Knowledge Use 缺少知识时不能隐式访问外部来源。
3. Build Target Proposal、Canonical Build Target、Build Intent、Publication Acceptance Criteria 和 Knowledge Sufficiency Assessment 不可互相替代；Criteria 必须由平台 Policy Profile 生成，调用方和模型不能弱化。
4. Application Services 拥有调查循环、Publication Policy、Criterion 汇总和应用结果；各 Authority Owner 拥有自己的 Assessment；Knowledge Engine 拥有知识准入、Manifest、Schema、依赖、并发条件和单 Scope 发布。
5. Source Integration 只向 Knowledge Engine 提供 Artifact，不生成 Candidate 或正式知识。
6. Candidate 和半成品状态不能进入正常 Knowledge Use。
7. 一个 Attempt 固定 Canonical Build Target Manifest、Scope、Binding Revision、上游 Snapshot、Expected Current、Schema 和 Capability Catalog；发现子目标只能位于冻结 descendant boundary 内。
8. 来源 Revision 和 Context 不因目标 Snapshot 或 Build Intent 被改写。
9. Replacement 和 Enrichment 共享同一准入与发布路径；Enrichment 只能使用 Schema 和 Context 兼容的确切 Base Snapshot。
10. 单个 KnowledgeScope 是原子发布单位；不存在全局发布锁或跨 Scope 分布式事务。
11. 跨 Scope 依赖固定确切上游 Snapshot，上游 CURRENT 变化不能静默重绑定。
12. 来源分歧的独立 Fact 可以共同发布；只有正式 Conflict Inference 才能声明冲突。
13. Schema 变化只通过新 Candidate 和新 Snapshot 生效，不原地修改 CURRENT 或仅修改 Projection。
14. 发布成功不能自证用户 Requirement 已满足；任务驱动更新必须在新的 Snapshot Read Session 中独立重评。
15. 模型可以动态调查和发现 Inference Proposal，但 Inference Candidate 的语义前提只能是确切已发布 Snapshot 中的正式 Fact / 受控 Inference；同一目标 Snapshot 内尚未发布的对象不能充当前提，也不能越过 Artifact、Candidate、Verifier 和 Snapshot 路径。
16. 预算耗尽、空结果、截断、未读范围、目标歧义和无进展停止必须显式暴露，不能解释为完整覆盖。
17. 只有完整覆盖唯一 Final Candidate Bundle Seal 的 Admission Batch Result 才能进入发布候选构建；Working Bundle 只有 Preview，不能跨 Revision / Attempt 拼装 ACCEPT。
18. Publication Acceptance 必须绑定精确 Publication Candidate Manifest；Admission ACCEPT、Acceptance PASS 和 Publication PUBLISHED 是三个不可替代的结果。
19. `KNW-REVALIDATION-SIGNAL-01` 只有在正常 Application 命令授权下才能触发更新；信号本身不修改正式知识，也不保证目标仍存在或能够重验。
20. `TRANSACTIONAL | FENCED | OBSERVATIONAL` 条件必须按真实保证分类，外部时间点观察不能伪装为事务不变量。
21. 每个 Application Attempt 只封存一个最终 Bundle / Manifest / Acceptance Assertion；替代 Attempt 提交前必须通过 Publisher Cancel / Outcome 收口旧 Publication Request，不能依赖本地状态使迟到 Submit 失效。
22. 每次模型规划调用使用冻结 Authorized Input Manifest 和有效 Isolation Receipt；模型只提出 Source Tool Proposal，不能直接读取来源或执行 Tool。
23. REQUIRED Target 必须通过 Build Target Coverage Map 关联到 exact 来源执行、Artifact、Candidate Disposition 和 Manifest 成员；同类型或相近目标不能替代。该映射仍不能自证用户 Need 充分。
24. 任何模型生成的 Build Target / Tool / Stop Proposal 或 Criterion Assessment 只有在领域 Contract 与 `X-MODEL-RESULT-ELIGIBILITY-01` 同时通过后才能进入生产状态；实际模型或隔离闭包不合格时不能推进 Investigation、Acceptance 或 Result。
25. 每个 Source Tool Step 在 dispatch 前必须取得并传递 exact `SOURCE_EXECUTION` Scope State Assertion 与 Binding Eligibility Assertion；Application Services 不自判资格，Source Integration 不使用请求时 Binding 代替当前分派门禁。

## 14. 评审、验证义务与下游追溯

本文已经回填 Source / Artifact、Evidence、Entity、Fact、Inference、Admission 和 Snapshot / Publication 的当前 Contract。进入 `Accepted` 前，上述依赖必须分别 Accepted 且版本与本文一致，并完成跨文档术语、所有权、引用和失败语义复核。

进入实现前至少建立以下 Contract Conformance：

- 首次构建 `NO_CURRENT` 与后续 `PRESENT(ref)` 使用同一 Update 主干，且 CURRENT 冲突不覆盖新状态。
- 最终 Bundle 新增 Candidate / 未解析项后，旧 Batch 与旧 Manifest 不能继续取得发布资格。
- Admission Batch COMPLETE、Publication Candidate Manifest、Criterion Assessment、Acceptance Decision 和 Publication Request 的 Revision / Digest 全链路一致。
- 任一必需 Criterion 为 FAIL / UNKNOWN / NOT_EVALUATED 时不提交 Publication Request。
- Manifest 改变后原 Acceptance 不可复用；Admission ACCEPT 或 Acceptance PASS 都不能绕过 Publisher 的事务检查。
- 取消、进程中断和 `PUBLICATION_OUTCOME_UNKNOWN` 不产生虚假的“未发布”或第二个竞争 Snapshot。
- Verifier 的 Information Requirement 只能返回知识缺口，不能直接调用 Connector；Application Services 的后续调查不扩大冻结权限和资源边界。
- 短 SHA、多义 Revision、重载方法、同名 Controller / Endpoint、跨模块同名对象和越界子目标均失败关闭；只有 exact Resolution Receipt 能进入 Build Intent。
- 未预编码 Commit、Endpoint 或其他 canonical root 可以通过 `list / search / read / compare` 等注册 Tool 完成渐进调查；每一步 Proposal、Authorization、Operation、Observation 和预算均可回放。
- Tool Proposal 重复、无新增内容、分页未完成、预算耗尽和权限失败触发各自停止语义，不静默截断、扩大范围或宣告完成。
- Planner、Build Target、Stop 或 Criterion 模型输出在 post-call actual Model / Adapter、Manifest、Isolation Receipt 或 Qualification 失配时不能进入生产 Proposal、Investigation State 或 Assessment；重试只能使用新的受控 Capability Attempt。
- Investigation 关闭后，Tool Observation / Artifact 内容不能进入 Answer Context；新 Snapshot 必须在关闭调查上下文后通过 Knowledge Use 独立读取和评估。

Knowledge Schema Evolution 是后续对正常更新语义的专门化设计，不阻塞本主题进入评审；本主题只固定 Target Schema Reference、Candidate、Admission、Manifest 和新 Snapshot 发布边界，不提前定义迁移或重建算法。Knowledge Use 复用 Publication Result 开启全新 Snapshot Read Session，不能在本用例中宣告原用户任务已充分。

当前不启动新的 Demo：上述选择都可由已接受的概要边界和现有主题 Contract 静态闭合。若实现选型暴露会改变接口、一致性或恢复语义且静态分析不足的实质不确定性，再登记有界 `DVR-*` 问题和判定标准；Demo 仍不成为生产路径。
