# Snapshot 与 Publication 详细设计

| 元数据 | 值 |
|---|---|
| Document ID | DD-KNW-SNAPSHOT-PUBLICATION |
| Version | 0.1.0 |
| Status | Accepted |
| Document Steward | Knowledge Engine |
| Architecture Baseline | SWM-ARCH@1.2 |
| Depends On | DD-KNW-REFERENCE-CONTEXT@0.1.0、DD-KNW-SCHEMA-CORE@0.1.0、DD-KNW-ENTITY@0.1.0、DD-KNW-FACT@0.1.0、DD-KNW-INFERENCE-CONFLICT@0.1.0、DD-KNW-ADMISSION@0.1.0 |
| Owns Contracts | KNW-SNAPSHOT-01、KNW-SNAPSHOT-BUILD-01、KNW-PUBLICATION-REQUEST-01、KNW-SCHEMA-ADOPTION-PUBLICATION-CLOSURE-01、KNW-SNAPSHOT-PUBLICATION-01、KNW-PUBLICATION-ATTEMPT-01、KNW-SNAPSHOT-CURRENT-01、KNW-SNAPSHOT-DEPENDENCY-01、KNW-SNAPSHOT-READ-01 |
| Design Coverage | Scope 级完整 Snapshot 组装、发布门禁、原子 CURRENT 切换、上游依赖、读取与保留边界 |
| Supersedes | None |
| Rationale ADR | AD-005、AD-009、AD-079、AD-081、AD-096、AD-099、AD-113、AD-121、AD-122、AD-128 至 AD-130 |
| Design Validation | None |
| Conformance Cases | None |
| Capability Evaluation | Not Applicable to atomic publication |

> 概要架构约束直接生效；本文新增的 Candidate Snapshot、Publication 和 Read 语义在状态进入 `Accepted` 前均为拟议设计。

## 1. 目的与范围

Snapshot 是一个 KnowledgeScope 在某次成功发布后可一致读取的完整正式知识状态。Publication 的职责是将精确的已准入闭包和受控继承状态组装为一个完整 Snapshot，并在一个 Scope 内完成全或无的正式可见性切换。

本文定义：

- Snapshot Record、Member Manifest、Dependency Manifest 和 CURRENT Binding。
- Target Snapshot Local Reference 与最终 Snapshot ID 的原子替换。
- Replacement 和 Enrichment 如何形成完整 Candidate Snapshot。
- Admission ACCEPT、Publication Acceptance PASS 和最终 Publication 之间的门禁。
- Scope 级并发、幂等、发布结果未知、读取与保留语义。
- 上游 Snapshot 依赖的精确绑定与受控最终一致。

本文不定义：

- Candidate 的语义正确性；已由 Knowledge Admission 决定。
- 调查范围、来源覆盖或 Publication Acceptance Policy；由 Application Services 定义和聚合。
- 某个 Snapshot 是否足以回答用户任务；由 Knowledge Use / Sufficiency Assessment 定义。
- 数据库产品、表结构、物理分片、索引格式或历史 Snapshot 产品功能。
- 持续同步、自动影响传播或独立 Evolution Orchestrator。

## 2. 边界与所有权

| 对象 / 决定 | Owner | 语义 |
|---|---|---|
| Snapshot Build Request / Publication Acceptance Assertion | 上游 Application 用例通过本文公开 Contract 提供 | 说明目标完整状态和 exact Manifest 已通过上游发布条件；Publisher 不读取调用方私有状态 |
| Admission Decision | Knowledge Engine / Admission | 批准或拒绝一个精确 Candidate Closure；ACCEPT 仍不是正式知识 |
| Publication Candidate Manifest | Knowledge Engine / Snapshot Builder | 将一个 Scope 的目标完整成员、依赖、Base 处置和局部替换绑定成不可变发布候选；Publication Acceptance 的唯一直接对象 |
| Publication Eligibility | Knowledge Engine / Publisher | 提交前对准入、Schema、引用、依赖、并发和资格的权威判断 |
| Publication Attempt / Outcome Record | Knowledge Engine / Publisher | 以 Idempotency Key 唯一绑定 Request Digest，持久记录确定失败、提交中和成功结果 |
| Snapshot Record / State / CURRENT Binding | Knowledge Engine | 正式知识状态和当前可见版本的唯一逻辑权威 |
| Snapshot Read Session | Application Services 管理使用周期；Knowledge Engine 验证并提供读取 | 将一次知识使用固定到确切 Snapshot / Schema / Context / Purpose |
| 当前持久化政策 | Knowledge Engine | 已发布 Snapshot 采用 `NO_PHYSICAL_CLEANUP`；真实清理需求出现后再启用 Retention 状态机 |

Application Services 可以请求发布，但不能分配 Snapshot / Knowledge ID、直接写 State 或切换 CURRENT。Knowledge Verifier 不组装 Snapshot；Publisher 不重新解释 Candidate 或修改 Admission Decision。

## 3. KNW-SNAPSHOT-01

### 3.1 Snapshot Reference 与 Record

Snapshot Reference 沿用 KNW-SNAPSHOT-REF-01，完整固定：

- owning KnowledgeScope ID。
- 不可变 Snapshot ID。
- 不可变 Knowledge Schema Reference。

Snapshot Record 在此基础上至少固定：

- Publication Attempt / Request / opaque Build Intent / Application Attempt References 与 Publication Time。
- State Formation = `REPLACEMENT | ENRICHMENT`，以及可选确切 Base Snapshot Reference。
- Member Manifest Reference / Digest，包含 Entity、Fact、Inference 的完整目标成员。
- Upstream Snapshot Dependency Manifest Reference / Digest。
- Evidence / Context / Admission / Schema / Capability Provenance Dependency Manifest Reference / Digest；这些不是正式知识成员。
- Publication Acceptance Assertion、Publication Eligibility Result 和 Publication Receipt Reference。
- Target Snapshot Slot Token、Semantic Publication Digest 和 Physical Manifest Digest。

Snapshot Record 和其 Manifest 成功发布后不可修改。CURRENT、Dependency Freshness 和读取权限是独立运行状态，不能回写 Snapshot 内容；Retention / Projection 仅在条件能力启用后增加外部状态。

### 3.2 正式成员与追溯依赖

Snapshot 的正式成员只允许：

- Entity State。
- `ASSERTED` Fact State。
- `ASSERTED` Inference State。

Artifact、Evidence、KnowledgeContext、Admission Decision、Candidate、Investigation、Semantic View、Projection、Claim 和 Agent 状态不是正式成员。Fact / Inference State 必须保留它们的 Evidence、Context、Argument、Admission 和依赖引用；Snapshot Manifest 聚合这些追溯依赖以支持完整性、保留和审计，但不改变对象种类。

“某能力、接口或业务对象已弃用”若本身是软件世界语义，必须作为有证据或正式前提支持的新 Fact / Inference Candidate 准入；它不是 Fact / Inference 支持失效时的通用 State 值。

### 3.3 完整状态而非 Delta

每个已发布 Snapshot 的 Member Manifest 都是目标 Scope 在本次语义下的完整正式知识集合。Enrichment 可以用 Base + Delta 构建，但发布结果和对外读取不能依赖查询时动态叠加一条未封口 Delta 链。

物理存储可以结构共享不可变 State Content 或使用持久化数据结构，但任何 Snapshot Reference 都必须能独立解析出完整成员和精确 State，不读动态 CURRENT 或未发布 Candidate。

## 4. Target Snapshot Local Reference 与 Digest

### 4.1 发布前不伪造 Snapshot Reference

Candidate / Admission 阶段尚无成功 Snapshot，因此只使用由 Knowledge Engine 分配、绑定上游 `(Build Intent Reference, Application Attempt Reference)` 且不可查询的 `Target Snapshot Local Reference`。它同时固定 owning Scope、target Schema 和局部 Key，不是 Snapshot Reference、Formal Knowledge Reference 或 CURRENT。两项上游引用在本 Contract 中只作 opaque correlation，不引入第二套 Attempt 生命周期。

`Target Snapshot Slot Token = canonicalDigest(owning Scope + Build Intent Ref + Application Attempt Ref + target Schema + Target Snapshot Local Reference)`。候选 State、Admission Closure 和 Publication Candidate Manifest 在规范 Digest 中使用该 Slot Token，不使用伪造 Snapshot ID。

### 4.2 发布时替换

最终发布事务为成功 Snapshot 分配不透明 Snapshot ID，并将同一 Closure / Publication Candidate Manifest 中的 Target Snapshot Local Reference 全部替换为该 Snapshot Reference。Snapshot Record 持久 `actual Snapshot Reference -> Target Snapshot Slot Token` 的发布映射，使发布后重算规范语义 Digest 时仍得到原 Slot Token。

发布同时执行两类 Digest：

- `Semantic Publication Digest`：对 Target Snapshot Slot、Candidate-local Knowledge Reference 和稳定 Knowledge ID 执行已审核规范化，替换前后必须不变。
- `Physical Manifest Digest`：在最终事务内完成 ID 分配和机械替换后、提交前，对实际 Snapshot / Knowledge ID、State、Link 和 Dependency Manifest 计算，用于检测物理内容篡改。事务前只预计算不依赖实际 ID 的组件 Digest；事务后重算只用于校验，不能首次产生权威值。

发布方只能执行 Admission Decision 和 Publication Candidate Manifest 允许的机械替换。任何替换导致 Semantic Publication Digest 改变时，事务失败关闭。

## 5. KNW-SNAPSHOT-BUILD-01

### 5.1 Publication Candidate Manifest 输入

Snapshot Builder 只接收：

- 本文公开的 Snapshot Build Request：opaque Build Intent / Application Attempt References、State Formation、target Scope / Schema、Target Snapshot Local Reference。
- `Expected Current = PRESENT(exact Base Snapshot Reference) | NO_CURRENT`。
- 该 Application Attempt 唯一 Final Candidate Bundle Seal、完整 Admission Batch Result，以及每个被选中 Closure 的 `ACCEPT` Decision；Batch 必须同时覆盖新建、替换和 State Continuation Candidate。
- 确切 Upstream Snapshot Binding、Schema Compatibility / Evolution Decision 和影响判断。

Builder 不读 Source Integration、Artifact Payload、模型调查对话或动态 CURRENT，不重新生成 Candidate。它从权威 Knowledge Engine Repository 重读 Admission Decision、Base / Upstream Snapshot、State 和依赖。

Builder 先输出不可变 Publication Candidate Manifest，Application Services 再让各 Criterion Owner 对该精确 Manifest 形成 Assessment 并聚合 Publication Acceptance Decision。Acceptance 不是 Manifest 的构造输入，避免“Manifest 依赖 Acceptance、Acceptance 又绑定 Manifest”的循环。

### 5.2 Publication Candidate Manifest 内容

Publication Candidate Manifest 是 Snapshot Builder 的唯一交付对象，不再另设平行的计划对象。一个完整 Manifest 至少包含：

- Manifest ID / Revision / Digest、opaque Build Intent / Application Attempt References、Final Candidate Bundle Seal / Revision / Digest、完整且 `Completeness = COMPLETE` 的 Admission Batch Result、Target Snapshot Local Reference / Slot Token 和 Expected Current。
- 完整 Target Member Manifest：每个 Entity / Fact / Inference Identity 恰好一个目标 State Candidate / Continuation。
- Admission Selection Manifest：列出 Batch Result 中每个 Closure 的 Outcome 和 `INCLUDED | EXCLUDED_BY_POLICY | BLOCKED` 处置及其依据。
- Base Member Disposition Manifest（有 Base 时）：每个 Base Entity / Fact / Inference State 的 `CONTINUE | REPLACE | EXCLUDE_FROM_TARGET` 和对应决定。
- Candidate-local Knowledge Reference / Target Snapshot Slot 替换 Manifest。
- 本地 Entity / Premise 目标成员 Binding、Upstream Dependency Manifest、Evidence / Context / Admission Dependency Manifest。
- 每个 Target Member 对应的 Admission Decision / Closure Revision / Closure Digest（包括 Continuation）、Member / Dependency / Disposition / Semantic Publication Digest 和构造 Provenance。

`EXCLUDED_BY_POLICY` 只能用于独立 Closure，且上游冻结 Policy 明确允许本次不发布它。`BLOCKED`、Batch 不完整、Batch 不绑定该 Application Attempt 唯一 Final Candidate Bundle Seal，或必需 Closure 非 ACCEPT 时不得形成可供 Acceptance 的 Manifest。Builder 不能在 Admission 后静默丢弃一个成员或被拒绝依赖。

每个 Application Attempt 只允许封存一个 publication-ready Manifest，封存后不可修改。成员、Closure、Continuation、Disposition、Schema、Expected Current、Upstream Binding 或任一 Digest 变化时，上游必须形成新的 Application Attempt / Manifest / Acceptance Assertion。若旧 Publication Request 已存在，先按 6.2 精确取消并解析其 Outcome。原 Assertion 不可复用。

### 5.3 State Continuation

新 Snapshot 中的每个本地正式对象都必须有目标 Snapshot State。旧 Snapshot State 成功发布过不会让它自动出现在新 Snapshot。

对语义、Schema、Context、支持和依赖未变的 Base State，可以形成 `State Continuation Candidate`：

- 固定 Base Resolved Formal Knowledge Reference 与原 Admission Decision。
- 保留相同 Effective Identity Key 和完整语义 State Content。
- 把本地 Entity / Premise 重绑到 Target Member Manifest 中语义保持的目标 State；不将 Candidate 当作新语义 Premise。
- 重新检查 Evidence / Formal Premise 可用性、Context、Schema 和影响状态。
- 经对象 Contract 允许的独立 Continuation Verification Profile 得到新 Admission Decision。

大量未变 State 可以由可重放的 Deterministic Batch Continuation Strategy 验证，但每个 State 的 Base Reference、目标 Binding、检查结果和失败处置必须可追溯。新 Evidence、新 Argument、命题或 Context 变化不是 Continuation，必须构造完整新 State Candidate 并重新准入。

INFERRED Entity 的 Continuation 必须同时包含目标 Snapshot 的 EntityDerivation Inference State；Inference 的本地直接 / 传递 Premise 必须全部存在于目标 Member Manifest 中并完成语义保持 Rebinding。

### 5.4 Replacement

Replacement 不从 Base 隐式继承任何正式知识。Target Member Manifest 必须由已准入的新 State Candidate 和显式 State Continuation Candidate 完整形成。

存在 Base 时，Base Member Disposition Manifest 必须覆盖每个原成员。`EXCLUDE_FROM_TARGET` 仅表示新 Snapshot 不再 ASSERT 该正式知识，不改写旧 State，也不自动形成其反命题。排除必须有目标 Schema 允许的结构化 Basis，例如已准入替代 State、无法重验、Schema 废弃或影响分析结果；“本轮没看到”不是充分的客观不存在证明。

Replacement 的来源范围和覆盖是否足以支持“完整替换”，由 Publication Acceptance Policy 判断；Publisher 只验证决定完整且 PASS，不自己重读外部来源。

### 5.5 Enrichment

Enrichment 必须显式绑定 `Expected Current = PRESENT(Base Snapshot Reference)`，且 target Schema 与 Base Schema 相同或具有允许 Enrichment 的显式兼容决定。它从 Base 的完整成员集出发：

1. 未受影响的 Base State 通过 State Continuation 进入目标 Manifest。
2. 新或更新的 ACCEPT Closure 按 Effective Identity Key 加入或替换目标 State。
3. 对同一 Fact 增加 Evidence 时，必须以完整新 Fact State Candidate 包含经重验的 Support / Constraint Set，不在发布阶段向旧 State 追加 Link。
4. 受影响但无法重验的 State 只能按显式 Disposition 排除并记录 `KNW-REVALIDATION-SIGNAL-01`；不能创建“不可用”正式 State，也不能因为本轮调查局部就静默丢失无关知识。

Enrichment 不是局部 Snapshot、未封口 Delta 或通用增量影响传播引擎。无法证明 Base Schema、Context、成员和影响边界兼容时，失败关闭并由上层决定扩大重验或改用 Replacement。

## 6. KNW-PUBLICATION-REQUEST-01 与 Publication Eligibility

### 6.1 公开 Publication Request

Snapshot / Publisher 只消费本节定义的公开输入，不读取 Application Services 的 Build Intent、运行状态或内部 Authority Record。Publication Request 至少固定：

- Request ID、Publication Idempotency Key、Request Digest 和 opaque Build Intent / Application Attempt References；后两者仅用于追溯与防串用。
- Publication Candidate Manifest ID / Revision / Digest、target Scope / Schema / Target Snapshot Slot、State Formation 与 Expected Current。
- Base / Upstream Snapshot References、完整 Admission Batch Result 和所选 ACCEPT Decisions。
- `Publication Acceptance Assertion`：受信任 Issuer、Assessment Contract / Policy Revision、精确 Manifest Digest、全部必需 Criterion Result Digests、聚合结果 `PASS` 与 Assertion Digest。
- `Schema Transition Mode = INITIAL | UNCHANGED | ADOPTION` 及其条件性 Schema Closure。
- 分类的 Publication Preconditions、Execution / Cancellation Observation，以及每条正式 Evidence 的 `NOT_REQUIRED_SELF_CONTAINED` 声明。
- 数据分类、调用 Authority、资源结算引用和审计关联；不携带 Secret 或来源 Payload。

`Publication Acceptance Assertion` 是 Publisher 的公共消费封套。它证明受信任上游针对 exact Manifest 给出了 PASS，但 Publisher 不解释上游调查政策，也不反向查询 Application Repository。Assertion 的生成与聚合可以由任何符合 Issuer Contract 的 Application 用例承担。

请求形成后不能替换 Manifest、Decision、Schema、Base、Upstream、Admission Closure 或 Precondition。输入变化必须使用新 Request / Idempotency Key；传输重试只能重放完全相同的 Request Digest。

### 6.2 Publisher 独占的 Attempt Fence

Publication Attempt / Outcome Record 是提交、取消和幂等的唯一线性化对象；当前不设置平行的 Publication Admission Gate。

`SubmitPublication` 首先在 Publisher 本地事务中按 Idempotency Key：

1. 不存在 Record 时，创建绑定 exact Request Digest 的 `PREPARED` Publication Attempt。
2. 已存在相同 Digest 的 Record 时，返回或继续该 exact Attempt。
3. 已存在不同 Digest 时返回 `IDEMPOTENCY_CONFLICT`。
4. 已为 `PUBLISHED | NOT_PUBLISHED` 时返回原终态；不存在另一个可持久化的“提交中”业务状态。

`CancelPublicationRequest` 必须携带 exact Idempotency Key 与 Request Digest，并由 Publisher 原子执行：

- Record 不存在：直接创建 `NOT_PUBLISHED(reason=CANCELED_BEFORE_PREPARE)` Tombstone。
- Record 为同一 Digest 的 `PREPARED`：CAS 为 `NOT_PUBLISHED(reason=CANCELED)`。
- Record 已终态：返回原终态。
- Digest 不同：返回 `IDEMPOTENCY_CONFLICT`。

Cancel 的 `PREPARED → NOT_PUBLISHED` 与最终发布事务的 `PREPARED → PUBLISHED` CAS 直接竞争，只有一方成功。调用超时只产生 `OUTCOME_UNKNOWN` 视图，重查后读取权威终态或仍为可重试的 PREPARED。因此迟到 Submit 不能越过取消 Tombstone；上游在激活替代请求前必须取得旧请求的 `NOT_PUBLISHED`，或解析可能已经成功的发布结果。不需要跨 Owner Gate、Epoch 写事务或 Abort Proof。

### 6.3 通用 Eligibility

只有新建或 `PREPARED` Attempt 执行可变 preflight。Publisher 从权威 Knowledge Repository 重建并验证：

1. Acceptance Assertion 由受信任 Issuer 签发，绑定 exact Manifest，聚合结果为 PASS，全部必需 Criterion 有唯一 Result Digest。
2. Admission Batch Result 为 `COMPLETE`，并满足双向集合等式：Target Final State Candidates 恰好等于全部 INCLUDED / ACCEPT Closure 的最终成员并集；Batch 外成员、被 BLOCKED / EXCLUDED 的成员均不能进入。
3. target Scope / Schema / Expected Current / Base / Upstream / Target Slot 在 Manifest、Admission 与 Request 中一致。
4. Member、Base Disposition、Candidate-local Reference 替换、Entity / Premise Binding、Dependency DAG 与 Context 完整且无悬空引用。
5. 跨 Scope 引用只指向已成功发布的 exact Upstream Snapshot，并进入 Dependency Manifest；不存在动态 CURRENT。
6. 每条 Evidence 均存在最小可复核 Snapshot 并声明 `NOT_REQUIRED_SELF_CONTAINED`；当前不接受依赖外部 Artifact Payload 长期在线的发布。
7. Semantic Publication Digest 与 Admission 绑定值可重建，Substitution Manifest 只含允许的机械替换。
8. 每项 Publication Precondition 具有唯一 Owner、Contract / Revision、Result Digest 和 `TRANSACTIONAL | FENCED | OBSERVATIONAL` 分类；Publisher 只按公共 Contract 验证，不自行改变分类或回退 Strategy。

任一检查失败都把 exact `PREPARED` Attempt CAS 为可重放的 `NOT_PUBLISHED`，不进入可见性事务。

### 6.4 Schema 条件门禁

所有发布都必须携带同一 target Schema 的 Schema Selection Receipt 和针对 exact Manifest 的 Final Schema Target Validation Receipt。Publisher 重验 Definition 已注册、Digest 完整，且 Registry 当前 Revision 仍适用于 target Scope、实际 Knowledge Kind / Type 与 KnowledgeContext。两个 Receipt 由 Schema Core 直接产生，不依赖 Adoption 流程。

Schema Transition Mode 的附加条件为：

- `INITIAL`：Expected Current 必须为 `NO_CURRENT`；exact target Schema 已注册并适用于本 Scope / Manifest，不需要迁移、Disposition 或 Identity Lineage。
- `UNCHANGED`：Expected Current 为 `PRESENT`，target Schema 与 Base Snapshot 的 exact Schema Reference 相同；不需要 Schema Adoption Package。
- `ADOPTION`：target Schema 与 Base 不同，必须提供本文 `KNW-SCHEMA-ADOPTION-PUBLICATION-CLOSURE-01` 的不可变 Closure。Closure 固定受信任 Issuer、exact source Snapshot / target Schema、Compatibility Decision Set Digest、Source Inventory / Disposition Digest、Target Obligation Satisfaction Digest、受支持的 1:1 Identity Continuation Digest、Candidate Bundle / COMPLETE Admission Batch / final target membership Digest 和 Closure Digest。Publisher 只验证该公开形状及其权威引用；具体 Evolution Strategy 是下游实现，不成为 Publisher 依赖。

没有 Base Snapshot 的普通首次构建不能伪装为 Adoption；同 Schema 更新也不能被强制经过 Migration fixed-point。

### 6.5 Precondition 与提交时再检

Publication Precondition 的分类由其 Authority Contract 固定：

- `TRANSACTIONAL`：CURRENT、身份唯一键、本地 Membership、Manifest / Digest 在最终事务中以 CAS、唯一约束或等价机制重验。
- `FENCED`：提交边界必须验证当前 Revision / Fence；失效即不发布。
- `OBSERVATIONAL`：只按冻结 Policy 校验 owner、observedAt、freshness 与风险接受；不得冒充严格提交保证。

最终原子边界内至少再次检查：

- Attempt 仍是 exact `PREPARED`；最终事务将直接 CAS 为 `PUBLISHED`，已取消 Tombstone 无法进入。
- Scope CURRENT 符合 `PRESENT(exact ref) | NO_CURRENT`。
- canonical / alias Identity 唯一约束、本地目标 Membership 和全部实际写入 Digest。
- exact Upstream Snapshot 仍存在；当前知识采用 `NO_PHYSICAL_CLEANUP`，Dependency Edge 与新 Snapshot 同事务写入。
- Schema Selection / Final Target Validation 的 Registry Revision 仍有效；仅 ADOPTION 模式重验 Adoption Publication Closure 的 Source Inventory / Disposition、Target Obligation、1:1 Identity Continuation 与 Digest 约束。
- 全部 FENCED Preconditions 仍有效，替换后 Semantic Digest 不变，Physical Manifest Digest 与实际写入一致。

预检不替代提交时再检，也不需要在调查和准入期间持有长事务。

## 7. KNW-SNAPSHOT-PUBLICATION-01 与 KNW-PUBLICATION-ATTEMPT-01

### 7.1 逻辑原子事务

一次成功 Publication 在同一 target Scope 的逻辑事务中完成：

1. 锁定或条件读取 exact `PREPARED` Publication Attempt，并执行 6.5 的提交时再检。
2. 分配 Snapshot ID 和必要的稳定 Entity / Fact / Inference ID；它们只在整体成功后成为可查询身份。
3. 按已审核 Manifest 机械替换 Target Snapshot / Candidate-local Reference，建立 Root、Identity Index、目标 State、Link 与 Context / Evidence / Admission 依赖。
4. 建立完整 Member、Upstream 和 Provenance Dependency Manifest 与 Snapshot Record。
5. 把权威 Upstream Dependency Edge 作为 downstream Snapshot 的不可变组成写入。
6. 以 Expected Current 为条件，把 target Scope 的 CURRENT Binding 切换到新 Snapshot Reference。
7. 写入不可变 Publication Receipt、可靠发布事件，并把 Attempt 从 `PREPARED` 原子推进为 `PUBLISHED`。

以上全部成功或全部对正常查询不可见。Data Source 读取、Artifact 加工、模型调用、语义审核、Projection 和外部消息发送不进入该事务。当前 Evidence 自包含、Knowledge 正式字节不物理清理，因此没有 Source Hold 转换或跨存储提交后动作。

### 7.2 模块化单体与逻辑事务

当前以一个 ACID Knowledge Store 实现 Scope 级逻辑事务。实现可以使用乐观版本、唯一约束或按 Scope 短时串行化，但必须保证：

- 首次成功前没有 CURRENT，之后每个 Scope 恰有一个 CURRENT。
- 不存在只可见部分 Root / State / Manifest 或 CURRENT 指向未完整 Snapshot。
- 调查与准入不持有长事务，不存在跨 Scope 或跨 Source Integration 分布式事务。
- 不同 Scope 可以并行发布；Scope 是逻辑并发单元，不要求物理分库或服务拆分。

### 7.3 Outcome 与恢复

Publication Result 只区分：

| Result | 含义 |
|---|---|
| `PUBLISHED` | Snapshot、成员、依赖、Receipt、Attempt 与 CURRENT 已原子成功 |
| `NOT_PUBLISHED` | 取消、提交前或提交时门禁确定失败；原 CURRENT / NO_CURRENT 保持 |
| `OUTCOME_UNKNOWN` | 仅调用方没有收到最终事务结果；必须查询 exact Attempt，不是持久状态 |

Publication Attempt Record 固定 Idempotency Key、Request Digest、Manifest / Acceptance / Expected Current Digests、`PREPARED | PUBLISHED | NOT_PUBLISHED`、State Revision 和终态明细。PUBLISHED 固定 Snapshot / Receipt / committed CURRENT Generation；NOT_PUBLISHED 固定失败阶段、Reason 与 Retry Classification。

进程中断只使用同一持久历史的数据库事务结果、Attempt、Receipt 和 Snapshot Record恢复：

- 已提交则返回原 `PUBLISHED`。
- 确定未提交或回滚则推进为 `NOT_PUBLISHED`。
- 调用方暂不能确认时返回 `OUTCOME_UNKNOWN`；重查只会得到仍可重试 / 取消的 `PREPARED` 或两个权威终态，不创建第二个 Attempt。
- 持久历史无法连续证明时，Publication 失败，当前部署实例 fail-stop；Publisher 不写同库自证 Availability 状态、不改写 Scope 生命周期，也不构造跨代恢复证明。

旧成功的证明不要求 CURRENT 仍指向该 Snapshot；后继 Publication 可以已经推进 CURRENT。

## 8. KNW-SNAPSHOT-CURRENT-01 与并发

### 8.1 Expected Current

每次 Publication 必须显式声明：

- `NO_CURRENT`：仅当提交时该 Scope 仍然没有 CURRENT 时可成功。
- `PRESENT(exact Snapshot Reference)`：仅当提交时 CURRENT 仍然等于该引用时可成功。

不允许 `OPTIONAL`、空值同时表示“无 CURRENT / 不在意”、也不允许“当时无则创建、有则覆盖”。Expected Current 是并发语义，Compare-And-Set 只是一种实现。

并发失败后不将 Closure 自动重放到新 CURRENT；Base State、Target Binding、Admission Read Set、Impact 和 Publication Criteria 可能已改变，必须按明确政策开启新 Attempt。

### 8.2 CURRENT 解析

`ResolveCurrentSnapshot(scope)` 在一次权威读取中返回一个完整 Snapshot Reference 或 `NO_CURRENT`。一旦返回，调用方必须把它作为不可变引用使用，不在同一读取/构建上下文中反复解析 CURRENT 并混合结果。

CURRENT Binding 只能指向已成功发布且具有完整 Manifest 的 Snapshot。当前没有 Snapshot Retention State；对 CURRENT 的读取不会返回 Candidate、部分发布或等待 Projection 的伪状态。

### 8.3 纠错与重新激活

发布错误不通过回写 Snapshot 纠正。默认纠错路径是构建、准入并发布新的修正 Snapshot。

如果未来实现对已保留 Snapshot 的重新激活，必须先建立专题设计，再使用新 Publication Request、Expected Current、Publication Acceptance Decision 和当前的 Schema / Dependency / Execution Eligibility Assessment 原子切换 CURRENT。“它曾经是 CURRENT”不是重新激活资格；不兼容或依赖失效的 Snapshot 不得激活。未来物理 Retention 若启用，其可读性门禁由该专题补充；本文不预置 Retention State 或独立 Rollback 模块。

## 9. KNW-SNAPSHOT-DEPENDENCY-01

### 9.1 Upstream Snapshot Dependency

每个跨 Scope Resolved Formal Knowledge Reference 都归纳为一条随 downstream Snapshot 原子发布的 Upstream Snapshot Dependency，至少固定：

- downstream / upstream Snapshot Reference 与 upstream Scope。
- 直接引用的 Knowledge Identity / State 集合或完整 Dependency Closure Digest。
- Schema Interpretation / Compatibility Decision、Purpose 和创建时 Upstream CURRENT Observation。
- 当前持久化政策引用 `NO_PHYSICAL_CLEANUP`。

Upstream Snapshot 必须已经成功发布，且不是本轮 Candidate。依赖永远指向 exact Snapshot，不指向动态 CURRENT。权威 Dependency Edge 归属于 downstream Snapshot；反向索引只是未来可重建的查询辅助，不参与正确性。

当前正式知识 append-only 且不物理清理，因此发布不取得 Dependency Retention Reservation、Lease、Fence 或反向索引完整性水位。真实启用物理清理时，必须先定义“新依赖建立与上游删除”之间的原子保护，再改变本 Contract；不能只增加最终一致索引后直接删除。

### 9.2 Freshness 与影响

upstream Scope 后续切换 CURRENT 时：

- 已发布 downstream Snapshot 仍绑定原 upstream Snapshot，不修改 State 或 Dependency。
- Knowledge Engine 可以产生符合 `KNW-REVALIDATION-SIGNAL-01` 的 Dependency Freshness 诊断；它不是正式知识，也不自动宣告下游结论错误。
- 使用政策可以拒绝过期依赖或返回 exact 旧绑定与提示，但不能自动改读新 CURRENT。
- 收敛到新上游必须经过新的 Knowledge Update、重验与 Publication。

持续扫描、多级传播和自动重建达到真实需求后，未来 Evolution Orchestrator 可以消费同一 Dependency Contract；当前不预建调度状态机。

## 10. KNW-SNAPSHOT-READ-01

### 10.1 Snapshot Selection / Validation Receipt

Knowledge Engine 不创建或修改 Application-owned Snapshot Read Session。公开读入口 `ValidateSnapshotSelection` 接收 Caller / Purpose、owning Scope、exact Snapshot Reference、支持的 Schema / View Contract、KnowledgeContext / Coverage Boundary、权限与可选多 Scope Snapshot Set，并返回不可变 `Snapshot Selection / Validation Receipt`：

- exact Snapshot / Schema / Member Manifest Digest。
- Snapshot 已成功发布且可按当前权限读取的验证结果。
- 多 Scope Dependency Compatibility Result。
- 当前持久化政策 `NO_PHYSICAL_CLEANUP`。
- Authority、Validation Contract / Revision、Request Digest 与 Receipt Digest。

Application Services 只在 Receipt 成功后，在自己的 Repository 中原子封存 Opening Attempt 为 Snapshot Read Session，并引用该 Receipt。Knowledge Engine 不写 Session；Application 也不写 Snapshot 状态。

所有 Formal Knowledge 读取使用 `Resolved Formal Knowledge Reference = exact Snapshot Reference + Knowledge Identity Reference`，并检查对象属于该 Member Manifest。稳定 Knowledge ID、名称或 CURRENT 不能替代成员检查。每次内容读取仍按调用主体、Purpose 与 Data Classification 校验权限。

### 10.2 CURRENT 变化期间的读取

Session 固定 exact Snapshot，不随 CURRENT 变化漂移。当前没有物理 Cleanup，因此无需 Snapshot Read Lease、Protection Epoch、Store Incarnation 或 MVCC Pin；CURRENT 前进不会使旧 exact Snapshot 字节消失。

权限撤销可以阻止后续读取，但不能让同一 Session 自动改读新 CURRENT。当 Knowledge Update 后需要重新回答任务时，Application Services 关闭旧任务执行上下文并创建绑定新 Snapshot 的新 Session，不混用两个 Snapshot 的发现。

### 10.3 多 Scope 读取

多 Scope 使用不是“各自读最新”。Validation Receipt 必须固定 Snapshot Set，并证明 downstream Snapshot 的 Upstream Dependency 与集合中实际上游引用一致。例如 Domain Snapshot 绑定 System A@S1 时，同一普通读取不能替换为 System A@S2。

比较两个 Snapshot 必须使用显式比较 Purpose 和带角色的 Snapshot / Context Set，不把两个版本伪装为一个一致状态。

## 11. 物理 Retention / Cleanup 条件能力边界

### 11.1 当前策略

当前 `Knowledge Retention Strategy = NO_PHYSICAL_CLEANUP`：

- 已提交 Snapshot、正式 State、Manifest、Evidence Snapshot、Decision 与 Receipt 按权威 Store 的 append-only 语义保存。
- 不建立 Snapshot Retention State、Read / Audit Lease、Cleanup Fence、Protection Epoch、Reachability Graph 或后台清理服务。
- CURRENT 与非 CURRENT Snapshot 的字节都不因普通产品策略删除。
- 历史 Snapshot 是否向普通用户开放查询仍是产品 / 权限决定；未开放不等于物理删除。

这一选择简化当前实现，同时保留稳定 Snapshot Reference、不可变 Manifest 与 exact Dependency，使未来历史查询和物理演进有可靠基础。

### 11.2 未来启用条件

只有容量、法规删除、分层归档或恢复成本形成可验证需求时，才专题设计物理 Retention / Cleanup。启用前必须同时定义：

- CURRENT、exact Read Session、upstream / downstream Dependency、审计与未解析 Publication 的保护不变量。
- 清理候选选择、并发读取 / 新依赖竞态、失败恢复与不可复用 Tombstone。
- Evidence / Snapshot 引用失效和用户可见语义。
- 从现有 append-only 数据迁移到新策略的兼容方案与 Conformance 证明。

未满足这些条件时不定义 Snapshot Retention 公共 Contract、清理命令、状态机或 Worker；权威读取直接依赖 append-only 事实。

## 12. Schema、条件能力与发布后事件

### 12.1 Schema 边界

每个 Snapshot 恰好绑定一个 Knowledge Schema Reference，所有 Member / Context / Identity / Argument / Dependency 必须按该 Schema 可解释。基础注册与 Target Validation 使用 DD-KNW-SCHEMA-CORE；Schema 变化仅在 `ADOPTION` 模式使用 DD-KNW-SCHEMA-EVOLUTION。数据库 DDL、字段默认值或索引重建不能冒充语义迁移。

### 12.2 Projection 当前关闭

当前不启用 Projection，发布后的读取直接使用权威 Repository。本文不创建 Projection Contract、Registry、Instance、Readiness 或发布后构建任务。

真实查询性能证据触发 Projection 后，必须保持：

- 每个 Projection 绑定 exact Snapshot / Schema / Definition Revision。
- Projection 不进入发布事务，不成为正式知识或 CURRENT 条件。
- 未就绪、过期或校验失败时回到等价权威读取或明确失败，不能把旧值标为新 Snapshot。

### 12.3 发布事件

Publication Receipt 与可靠事件记录在发布事务内建立。事件只携带 Snapshot / Scope / Schema / Build Intent / Application Attempt References、Manifest / Dependency Digest 与 Publication Time，不复制 Evidence、命题或秘密。

Telemetry、Freshness 检测以及未来条件能力按 Snapshot Reference 幂等消费。重复事件不得重复发布、分配身份或改写 CURRENT。

## 13. 失败、幂等、取消与恢复

| 失败类别 | 处理 |
|---|---|
| PUBLICATION_ACCEPTANCE_ASSERTION_INVALID | exact Attempt 进入 NOT_PUBLISHED；上游以新 Request 补齐 |
| ADMISSION_NOT_ACCEPTED / STALE | 不发布相关 Closure；Publisher 不修改 Candidate |
| MANIFEST_INCOMPLETE / MEMBER_DISPOSITION_MISSING | 当前 Request NOT_PUBLISHED；新的 Application Attempt 重建 Bundle / Manifest / Assertion |
| SCHEMA_TARGET_INVALID | Schema 未注册、Digest / Applicability 失配；不发布 |
| SCHEMA_ADOPTION_INVALID | 仅 ADOPTION 模式：Compatibility / Disposition / Obligation / Identity Lineage 不完整；不发布 |
| EVIDENCE_NOT_SELF_CONTAINED | 当前不允许依赖外部 Payload 的发布 |
| LOCAL_BINDING_MISSING / DANGLING_REFERENCE | 不删除悬空成员后继续；整体不发布 |
| UPSTREAM_UNAVAILABLE | 不静默重绑新 CURRENT；以 exact Snapshot 状态决定新 Request |
| CURRENT_CONFLICT | 原状态不变；返回 Expected / Actual，由上游创建新 Application Attempt |
| IDENTITY_UNIQUE_CONFLICT | 整体事务失败；重新 Resolution / Admission |
| DIGEST / MANIFEST_MISMATCH | 事务失败并审计，不重新解释差异 |
| EXECUTION_REVOKED | 最终事务 CAS 前失败；事务已提交则返回真实 PUBLISHED |
| CANCELED | Cancel 与 Publish CAS 竞争；权威结果只能是 NOT_PUBLISHED 或 PUBLISHED |
| PUBLICATION_OUTCOME_UNKNOWN | 查询相同 Idempotency Key / Request Digest，不创建第二个 Attempt |
| IDEMPOTENCY_CONFLICT | 同一 Key 对应不同 Request Digest；拒绝并返回已有 Attempt 引用 |
| AUTHORITY_REPOSITORY_UNAVAILABLE / INTEGRITY_FAILURE | Publication 失败并由部署 fail-stop；Scope 状态不变，不写同库自证状态或构造跨代成功证明 |

Publication Idempotency Key 至少绑定 target Scope、opaque Build Intent / Application Attempt References、Manifest / Semantic Digest、Expected Current、Acceptance Assertion 与 Schema Transition Mode。同一 Key 只绑定一个 Request Digest；完全相同重放返回原 Record，不同输入必须使用新 Key。

进程中断后，只有 Outcome Record、Receipt 与 Snapshot Record 一致地证明结果时返回 PUBLISHED。事务回滚时 Record 保持 PREPARED，可由相同请求重试或精确取消；`OUTCOME_UNKNOWN` 不持久化。CURRENT 只验证该次提交记录的 Generation，不要求仍指向历史成功 Snapshot。

## 14. AI Native、可观测性与资源

### 14.1 模型与平台边界

模型可以在上游建议 State 重验、替换或排除，但只形成 Candidate / Disposition Proposal。Manifest 规范化、完整性、Digest、Reference 替换、唯一性、Expected Current、Attempt 幂等、取消 CAS、原子事务与 CURRENT 可见性全部是 Deterministic Platform Control。

模型能力增强可以优化候选构建，不能接管发布原子性或跳过 Admission / Acceptance Assertion。

### 14.2 可观测性

传播 Build Intent / Application Attempt References、Admission Batch / Decision、Acceptance Assertion、Manifest / Request、Scope / Schema、Expected / Actual Current、Upstream Dependency、Transaction / Receipt 与 Snapshot Selection Receipt 关联。

记录成员 / Continuation / Replace / Exclude 数量、Manifest 大小、preflight / commit 时延、冲突等待、事务 Outcome 与重试。Telemetry 不复制 Evidence、Proposition、Argument、Artifact Payload、Secret 或业务数据。

### 14.3 性能与逻辑分片

Candidate 组装、Continuation 验证和 Digest 组件预计算在最终事务前完成。事务内只执行必需再检、ID 分配、机械替换、Physical Manifest 根 Digest 组合、状态 / Manifest / Receipt 写入、Attempt 推进与 CURRENT 切换；不扫描外部 Payload或调用模型。

KnowledgeScope 是逻辑发布和并发单元。实现可以按 Scope 路由或分区，但一个 Scope 只有一个 CURRENT 原子边界。跨 Scope 使用 exact Dependency，不使用全局锁或分布式发布事务。

## 15. 拟议不变量

1. Snapshot 是一个 KnowledgeScope 一次原子发布的完整 Entity / Fact / Inference 正式状态，不是未封口 Delta。
2. Artifact、Evidence、Context 与 Admission 是追溯依赖，不是正式成员。
3. Candidate 阶段只使用 Target Snapshot Local Reference；稳定 ID 只在整体发布成功后可查询。
4. Publisher 只消费 exact ACCEPT Admission 与 PASS Acceptance Assertion；二者都不能单独形成正式知识。
5. Replacement 不隐式继承，Enrichment 不静默删除；完整 Target Member / Base Disposition Manifest 是发布输入。
6. 旧 State 进入新 Snapshot 必须经过可重放 Continuation Candidate 和新 Admission。
7. Manifest 只允许机械 Reference 替换，替换前后 Semantic Publication Digest 不变。
8. Root、State、Identity Index、Dependency Edge、Snapshot、Receipt、PUBLISHED Outcome 与 CURRENT 同事务全部生效或全部不可见。
9. 每次发布显式使用 `NO_CURRENT | PRESENT(exact ref)`；首次成功前无 CURRENT，之后恰有一个。
10. 跨 Scope 只依赖既有 exact Snapshot；上游 CURRENT 变化不改写下游。
11. Snapshot Selection 固定 exact Reference；Application-owned Session 不自动漂移，Knowledge Engine 不写 Session。
12. 当前正式知识 `NO_PHYSICAL_CLEANUP`，因此不预建 Lease、Protection Epoch、Retention Graph 或清理服务。
13. Projection 当前关闭；未来 Projection 也只能是 exact Snapshot / Schema 的可重建派生物。
14. Publication Attempt 是取消、提交和幂等的唯一 Fence；不存在平行 Gate。
15. Cancel 的 `PREPARED → NOT_PUBLISHED` 与 Publish 的 `PREPARED → PUBLISHED` 只有一方成功。
16. `OUTCOME_UNKNOWN` 是调用方视图，不是持久状态；相同请求不得创建第二个 Attempt。
17. INITIAL / UNCHANGED 发布不依赖 Schema Adoption；只有 ADOPTION 使用 Migration / Disposition / Identity Lineage。
18. Snapshot Publication 是确定性平台控制；模型不分配 ID、不决定 CURRENT、不改写 Manifest 或 Outcome。

## 16. 验证义务与下游追溯

进入实现前至少建立以下 Contract Conformance / 故障注入：

- NO_CURRENT 首发并发、PRESENT Base 并发、相同 Request 幂等与不同 Digest 冲突。
- Submit 与 Cancel 的所有竞态；取消 Tombstone 能阻止迟到 Submit，事务提交成功不能被改写成 CANCELED。
- 调用超时后重查 PREPARED / PUBLISHED / NOT_PUBLISHED，不出现持久 COMMITTING 或第二个 Attempt。
- 任意写入步骤失败后 CURRENT 仍指向完整旧 Snapshot，且无可查询半成品。
- Target Snapshot / Knowledge Local Reference 替换前后 Semantic Digest 一致，Physical Digest 绑定实际 ID。
- Replacement 覆盖全部 Base Disposition，Enrichment 不丢无关成员，Continuation 不绕过 Admission。
- INITIAL / UNCHANGED 的基础 Schema Target Validation 可独立执行；ADOPTION 的附加闭包只在模式变化时要求。
- 本地 Entity / Premise 完整；跨 Scope exact Dependency 不动态重绑。
- Evidence 全部自包含；Source Payload 淘汰后已发布知识仍可复核。
- Snapshot Selection Receipt 与 Application Session Owner 分离；CURRENT 变化不造成混读。
- `PHYSICAL_CLEANUP_DISABLED` 和 `PROJECTION_DISABLED` 不影响权威发布与读取。

只有存储技术暴露会改变上述 Contract 的实质不确定性时，才登记有界 `DVR-*` Demo。Demo 不成为发布旁路或第二套正式状态。

下游详细设计复用：

- DD-APP-KNOWLEDGE-UPDATE：形成公开 Snapshot Build Request / Acceptance Assertion，调用 Submit / Cancel，并把 Publication Outcome 与用户任务 Sufficiency 分离。
- DD-KNW-PERSISTENCE：实现权威 append-only Snapshot / State / Manifest / Receipt 和当前关闭的条件能力边界。
- DD-KNW-SCHEMA-CORE：提供 Schema Definition、Registration 与 Target Validation。
- DD-KNW-SCHEMA-EVOLUTION：仅在 ADOPTION 模式提供 Compatibility、Disposition、Migration 与 Identity Continuation。
- DD-APP-KNOWLEDGE-USE：拥有 Snapshot Read Session，并消费 Selection / Validation Receipt。
