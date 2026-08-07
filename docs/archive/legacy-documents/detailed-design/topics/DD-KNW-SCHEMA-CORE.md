# Knowledge Schema Core 详细设计

| 元数据 | 值 |
|---|---|
| Document ID | DD-KNW-SCHEMA-CORE |
| Version | 0.1.0 |
| Status | Accepted |
| Document Steward | Knowledge Engine / Schema Registry |
| Architecture Baseline | SWM-ARCH@1.2 |
| Depends On | DD-KNW-KNOWLEDGE-SCOPE@0.1.0、DD-KNW-REFERENCE-CONTEXT@0.1.0、DD-X-CAPABILITY-EXECUTION@0.1.0、DD-AI-MODEL-GATEWAY@0.1.0、DD-MGT-CAPABILITY-EVALUATION@0.1.0 |
| Owns Contracts | KNW-SCHEMA-DEFINITION-01、KNW-SCHEMA-REGISTRATION-01、KNW-SCHEMA-AVAILABILITY-01、KNW-SCHEMA-TARGET-VALIDATION-01、KNW-CANDIDATE-ENVELOPE-01、KNW-SCHEMA-TRANSITION-PROOF-REF-01 |
| Design Coverage | 不可变 Knowledge Schema Definition、注册、可用性和普通发布所需 Target Validation |
| Rationale ADR | AD-099、AD-113、AD-121、AD-125、AD-129 |
| Design Validation | None |
| Conformance Cases | None |
| Capability Evaluation | Schema Proposal / Semantic Review 使用模型时适用 |

> 本文拆分的是上游基础 Contract，不新增运行服务。Schema Registry 仍是 Knowledge Engine 单体内部能力；Schema Adoption、迁移和身份延续由 DD-KNW-SCHEMA-EVOLUTION 条件性扩展。

## 1. 目的与范围

本文使首次构建和普通同 Schema 更新无需依赖 Schema Evolution 流程即可合法选择并验证 target Schema。它定义：

- Knowledge Schema Definition 的闭合语义与不可变引用。
- Schema Proposal 如何被验证并原子注册。
- target Schema 对 exact Scope / Manifest 的确定性适用性验证。
- INITIAL、UNCHANGED 与 ADOPTION 共享的最小 Schema 门禁。

Compatibility、Migration、Source Member Disposition、Target Obligation fixed-point、Identity Lineage 和 Adoption Publication 不在本文范围；它们只在 Schema 变化时由 DD-KNW-SCHEMA-EVOLUTION 定义。

## 2. 所有权与边界

| 对象 / 决定 | Owner | 边界 |
|---|---|---|
| Schema Definition / Registry Record | Knowledge Engine / Schema Registry | 唯一语义写入权；不访问 Data Source |
| Registration Request | Application Services / Management | 协调身份、权限和资源；不自判注册成功 |
| Registration Decision | Knowledge Engine，生成与审核 Strategy 隔离 | 只判断 Definition 能否注册，不判断 Scope 已迁移 |
| Schema Availability | Knowledge Engine / Schema Registry | 控制新 target 是否可选择，不改写历史 Snapshot |
| Schema Target Validation Receipt | Knowledge Engine / Schema Registry | 绑定 exact Scope / Manifest / Transition Mode |

Schema Registry 与 Publisher 当前位于同一 Knowledge Store；提交边界直接重验 Registry Record / Revision，不建设跨服务 Grant、Lease 或 Epoch 协议。

## 3. KNW-SCHEMA-DEFINITION-01

`Knowledge Schema Reference = Schema ID + Version Label + Definition Digest`。Version Label 便于管理，不能代替 Digest 或推断兼容性。

闭合 Definition 至少固定：

- Schema ID、Version Label、可选 Predecessor 和全部 exact Schema Dependency References。
- `Schema Applicability Boundary`：允许的 Scope Kind / 可机械判定 Predicate、Knowledge Kind / Type 与 Context Boundary。
- Entity Kind / Origin、身份键、Anchor / Semantic Definition 和关系约束。
- Fact Proposition / Term / Predicate / Modality、Direct Support 与 Evidence Composition。
- Inference Conclusion / Argument / Premise / Modality、无环与 Conflict 规则。
- Evidence Representation / Locator / Observation 与最低可复核要求。
- KnowledgeContext Vocabulary、Identity-bearing Dimension 和 Comparison Purpose。
- Snapshot Membership / State、Admission Obligation、Canonicalization、规范 Digest 和 Reader Contract。

Definition 必须自包含或通过 exact immutable references 闭合；依赖图可展平、无环且能重算相同 Digest。运行时不得按名称解析“最新版”。

REGISTERED Definition 永不原地修改。命题、身份、Context、支持、Argument、Membership 或 Admission Obligation 的变化必须创建新 Reference。数据库列、Prompt 字段和模型版本变化若不改变正式语义，不构成 Knowledge Schema 变化。Predecessor 只说明演进来源，不自动表示兼容。

## 4. KNW-SCHEMA-REGISTRATION-01

### 4.1 请求与状态

Schema Registration Request 固定 Proposal ID / Digest、Definition、Dependency References、Change Intent、Capability Catalog Snapshot、Execution Envelope、资源分配与幂等键。使用模型时，Proposal 与独立 Semantic Review 分别固定 exact Capability / Strategy，以及 `PRODUCTION Activation / PASS Evaluation Result / latest VALID Decision | exact EVALUATION_ONLY Grant`、Model / Tool Policy；二者不能复用同一个 Capability Attempt。

Registration Attempt 使用：

`PREPARED → REGISTERED | REJECTED | EXECUTION_FAILED`

- REGISTERED：Definition、Decision 和 Registry Record 在同一事务写入。
- REJECTED：语义或机械条件确定不满足；修改使用新 Proposal。
- EXECUTION_FAILED：审核未完成或执行失败，不产生注册语义。

相同 Idempotency Key / Request Digest 返回原结果；不同 Digest 冲突。Proposal、模型输出和 Attempt 均不能预分配权威 Schema Reference。

只有 `PRODUCTION` Catalog 可以创建 Registration Attempt / Decision / Registry Record。`EVALUATION_ONLY` 只返回隔离的 Schema Proposal / Review Evaluation Output，不分配 Schema Reference、不改变 Registry / Availability。

### 4.2 注册验证

Knowledge Engine 至少执行：

1. 机械检查闭合依赖、唯一 Type / Contract ID、合法引用、无环、Canonicalization、Digest 与可实现的 Admission Obligation。
2. 对身份、命题、Context、Support、Argument 等开放语义执行与 Proposal 生成隔离的审核。
3. 重建规范 Definition；模型不能指定 Registry ID、兼容结论或稳定身份映射。
4. 以 Registry 唯一约束原子写入 Definition、Registration Decision、Availability 和审计引用。

封存 Decision 前还必须执行 X-CAPABILITY 的 post-call 实际模型指纹门禁；actual fingerprint 不在冻结 Catalog / Evaluation 覆盖内时进入 EXECUTION_FAILED，不注册 Definition。

Schema Availability 当前只区分：

- `AVAILABLE_FOR_TARGET`：允许新的 target 选择。
- `DEPRECATED_FOR_NEW_TARGET`：阻止新的 target；历史 Snapshot 继续按 exact Definition 解释。

当前 Knowledge Store 采用 `NO_PHYSICAL_CLEANUP`，不定义 Schema Metadata Retirement、反向 Retention Graph 或清理状态机。

### 4.3 KNW-SCHEMA-AVAILABILITY-01

Registration 成功时，Registry 在同一事务创建 `Availability Revision = 1, AVAILABLE_FOR_TARGET`；不存在已经 REGISTERED、但尚无 Availability 的中间状态。Availability 是指向不可变 Definition 的单调控制记录，不修改 Definition、Registration Decision 或历史 Snapshot。

`ChangeSchemaAvailability` Command 至少固定：exact Schema Reference / Definition Digest、目标状态、Expected Availability Revision、调用 Authority、结构化原因、Command Idempotency Key、canonical Request Digest 和审计关联。Schema Registry 为每个 Command 建立本地 Availability Attempt：

`PREPARED → APPLIED | NOT_APPLIED`

- `APPLIED`：以 Expected Revision CAS 追加新的不可变 Availability Decision，并推进 current Availability Revision。
- `NOT_APPLIED`：权限、状态迁移、Expected Revision 或请求绑定不满足；不改变 current Availability。
- 调用超时只返回 `OUTCOME_UNKNOWN` 视图；调用方按 Idempotency Key / Request Digest 查询同一 Attempt，不创建第二次状态变化。
- 相同 Key / Digest 返回原 Attempt / Decision；相同 Key、不同 Digest 返回 `IDEMPOTENCY_CONFLICT`。

当前最小状态策略只允许 `AVAILABLE_FOR_TARGET → DEPRECATED_FOR_NEW_TARGET`。相同 Idempotency Key / Digest 的重放返回原结果；使用新 Key 请求 current 状态不追加 Revision，而以 `NOT_APPLIED(NO_STATE_CHANGE)` 返回。`DEPRECATED_FOR_NEW_TARGET → AVAILABLE_FOR_TARGET` 不在本版运行契约中：需要重新允许新 target 时，注册新的 exact Schema Reference，并重新经过 Registration 与初始 Availability；不能原地恢复旧 Revision、覆盖 Deprecation Decision 或仅凭人工说明重新启用。该限制不影响历史 Snapshot 按旧 exact Reference 读取。

Availability Command 由有权的 Application Management 用例协调，但状态、Attempt、Decision、CAS 和审计写入只由 Schema Registry 完成；Application Services、模型和 Publisher 都不能直接写 Availability。Deprecation 与 Schema Selection / Publication 并发时：Selection Receipt 固定当时 Availability Revision；Final Target Validation 重读 current Revision；Publisher 的最终 Scope 事务再次重读同库 Registry / Availability，并以锁、Revision 条件或等价事务机制把该 Revision 与 `AVAILABLE_FOR_TARGET` 作为提交前提。Deprecation 先提交则新 target 失败关闭，Publication 先提交则该已发布 Snapshot 保持有效，之后的新 target 被阻止。

## 5. KNW-SCHEMA-TARGET-VALIDATION-01

### 5.1 Schema Selection

构建开始前调用 `ValidateSchemaSelection`，输入：

- exact target Schema Reference / Definition Digest。
- target KnowledgeScope Definition / Revision。
- `Schema Transition Mode = INITIAL | UNCHANGED | ADOPTION`。
- Expected Current / Base Snapshot Schema（如有）。

成功时返回不可变 `Schema Selection Receipt`，固定 Registry Record / Revision、Scope-level Applicability Predicate Input / Digest、Transition Mode、Result 和 Receipt Digest。它只证明“该 Schema 可以作为本次构建目标”，不预言尚未形成的 target members / contexts 都适用。

模式规则：

- INITIAL：Expected Current = NO_CURRENT；不需要 source Snapshot、Migration 或 Disposition。
- UNCHANGED：Expected Current = PRESENT，target Schema 等于 Base Snapshot 的 exact Schema Reference。
- ADOPTION：Expected Current = PRESENT，target 与 Base 不同；Selection Receipt 只允许开始 Adoption，仍须 Evolution Plan / Package。

### 5.2 KNW-CANDIDATE-ENVELOPE-01

`BeginCandidateBundle` 接收上游已有的 opaque Build Intent / Application Attempt References、owning Scope、exact target Schema / Schema Selection Receipt、Expected Current、exact Upstream Snapshot Bindings 与幂等键。Schema Core 先验证 Receipt 与 Scope、Schema、Transition Mode 和 Expected Current 一致，再返回不可变 Candidate Envelope：

- Envelope ID / Revision / Digest。
- 原样绑定的 Build Intent / Application Attempt References。
- owning Scope、target Schema、Schema Selection Receipt、Expected Current 和 Upstream Bindings。
- 唯一 Target Snapshot Local Reference。

Candidate Envelope 是所有 Entity / Fact / Inference / Continuation Candidate 的共同坐标，不是第二套 Attempt 或状态机。相同 Idempotency Key / Request Digest 返回同一 Envelope；不同 Digest 冲突。Candidate-local Reference 不得跨 Envelope；Final Candidate Bundle Seal 后的语义变化由上游创建新 Application Attempt / Envelope。

该 Contract 归 Schema Core，是因为 Envelope 必须消费并验证 Schema Selection Receipt；Reference / Context 只提供 opaque 稳定引用值类型，不能反向读取 Schema Registry。

### 5.3 Final Target Validation

Publication Candidate Manifest 形成后调用 `ValidateSchemaTarget`，输入 Selection Receipt、exact Manifest Digest，以及实际 Knowledge Kind / Type / canonical KnowledgeContext 集合。

成功的 `Schema Target Validation Receipt` 固定全部输入、Registry Revision、Applicability Boundary / Predicate Input / actual member set Digests、Result 和 Receipt Digest。Knowledge Engine 确定性检查：

1. exact Definition 仍 REGISTERED、Digest 闭合且 Availability 为 AVAILABLE_FOR_TARGET。
2. Scope Kind / Predicate、每个实际 Knowledge Kind / Type 和 KnowledgeContext 都落在 Applicability Boundary。
3. Predicate 只依赖随 Request 固定且可在提交边界重验的输入；模型判断或缓存标签不能代替。
4. Transition Mode、Expected Current / Base 与 Selection Receipt 保持一致。

Publisher 在最终 Scope 事务中重读 Registry Record / Revision，并按 actual Manifest 重算以上条件。Availability 或 Predicate 输入变化时失败关闭；当前同库重验不需要长期 Eligibility Grant。

### 5.4 KNW-SCHEMA-TRANSITION-PROOF-REF-01

为避免普通对象 / Admission 反向依赖完整 Schema Evolution Package，Schema Core 定义一个最小、不可变 Transition Proof Reference。它只包含 Proof ID / Digest、source / target Schema、Purpose、exact Subject Reference / Digest、`ELIGIBLE | INELIGIBLE`、Authority Decision Reference / Digest，以及 Purpose-specific 机械约束（Identity Continuation 当前仅允许 1:1）。

Purpose 仅覆盖跨 Schema 对象构建确实需要的 `EVIDENCE_INTERPRETATION | IDENTITY_CONTINUATION | FORMAL_PREMISE_INTERPRETATION | STATE_CONTINUATION`。条件启用的 Schema Evolution 能力作出并独立审核语义 Decision 后，向 Schema Core 注册该 Reference；Schema Core 只校验 Envelope、Authority、exact schemas / subject / digest 和当前支持的机械基数，不重新判断兼容语义。

对象构建、Admission 和 Publisher 通过 `ValidateSchemaTransitionProof(exact reference, purpose, source, target, subject)` 读取 / 重验。Proof 不包含 Evolution Plan、Source Inventory、Disposition、Target Obligation 或 Adoption Package，也不单独授权 Snapshot Publication。

## 6. AI Native 边界

模型适合提出 Schema Definition、解释自然语言语义和发现歧义；平台必须拥有 Reference、闭合依赖、规范化、Digest、Applicability、Registry 唯一性和 Target Validation。更强模型可以减少手写 Proposal 规则，不能取代注册审核或提交边界重验。

## 7. 失败、幂等与恢复

| 失败 | 处理 |
|---|---|
| DEFINITION_NOT_CLOSED / DIGEST_MISMATCH | REJECTED，不猜测缺失依赖 |
| SEMANTIC_ASSESSMENT_FAILED | EXECUTION_FAILED，不产生 Registration Decision |
| IDEMPOTENCY_CONFLICT | 返回已有 Attempt，拒绝覆盖 |
| SCHEMA_AVAILABILITY_TRANSITION_INVALID | Availability Attempt 为 NOT_APPLIED；不改变当前 Revision |
| SCHEMA_AVAILABILITY_REVISION_CHANGED | CAS 失败并返回 current Revision；调用方必须重读后发起新 Command |
| SCHEMA_NOT_AVAILABLE_FOR_TARGET | Target Validation 失败，不改写历史 Snapshot |
| SCHEMA_APPLICABILITY_INVALID | 返回越界维度，不缩小 Manifest 规避 |
| TRANSITION_MODE_INVALID | Mode 与 Expected Current / Base 不一致 |
| REGISTRY_REVISION_CHANGED | Publisher 提交失败；上游创建新 Request |
| AUTHORITY_REPOSITORY_UNAVAILABLE / INTEGRITY_FAILURE | 当前 Schema 操作失败并由部署 fail-stop；不依赖下游 Persistence 状态，不签跨代证明 |

注册、Availability 和 Target Validation 只支持当前单库同一持久历史内的事务重试。调用超时查询相同 Attempt / Request；不构造 Store Incarnation 或跨代恢复协议。

## 8. 拟议不变量

1. Knowledge Schema Reference 包含 Definition Digest；名称或 Version Label 不能代替 exact Reference。
2. REGISTERED Definition 不可变，全部语义依赖闭合且无环。
3. Proposal 生成 Strategy 不能审核自身；模型不能签发 Registration Decision。
4. Registration 不代表任何 Scope 已采用该 Schema。
5. 每个发布都必须对 actual Scope / Manifest 通过 Target Validation。
6. INITIAL 和 UNCHANGED 不依赖 Evolution Plan、Disposition、Obligation fixed-point 或 Identity Lineage。
7. ADOPTION 同时需要基础 Target Validation 与 Evolution Adoption Package。
8. Publisher 在同一 Knowledge Store 事务内重验 Registry / Applicability，不预建跨服务 Eligibility Grant。
9. Schema 被弃用不改写已发布 Snapshot；历史解释使用 Snapshot 的 exact Reference。
10. 当前 Schema 字节不物理清理；未来 Retention 不能破坏历史 Snapshot 的解释闭包。
11. Candidate Envelope 与 Transition Proof Reference 都由 Schema Core 提供；Reference / Context 不反向依赖 Schema Registry 或 Evolution。
12. 普通知识对象只消费 Schema Core 的最小 Transition Proof Reference，不依赖准入后才形成的完整 Adoption Package。
13. Registration 与初始 `AVAILABLE_FOR_TARGET` Revision 同事务形成；REGISTERED Definition 不存在 Availability 空窗。
14. Availability 只允许单调 Deprecated；本版不原地重新启用旧 Schema Reference，且所有变更使用 Expected Revision CAS 与幂等 Attempt。
15. Selection、Final Target Validation 与 Publisher 提交分别固定或重读 Availability；并发 Deprecation 不能让新的 target 绕过失败关闭，也不改写已发布 Snapshot。

## 9. 验证义务

Contract Conformance 至少覆盖：

- Definition 依赖闭合、循环、Digest、重复 Type / Contract 与非法状态。
- 相同注册请求幂等、不同 Digest 冲突、机械拒绝和语义审核失败。
- Registration 与初始 Availability 原子形成；Deprecated Command 的权限、幂等、Expected Revision CAS、同状态重放和禁止重新启用。
- INITIAL 无 CURRENT、UNCHANGED exact Schema 相等与 ADOPTION 基础 Receipt。
- Scope Kind、Predicate、Knowledge Kind / Type、Context 边界越界。
- Registry Revision / Availability 与 Selection、Final Target Validation、Publisher 提交的全部竞态；验证 Deprecation 先提交时新 target 失败、Publication 先提交时成功 Snapshot 不被回写。

Schema Proposal / Semantic Review 使用模型时建立 Capability Evaluation；Registry、Digest 和 Applicability 使用 Conformance。只有 Schema 表达无法机械判定 Applicability，或 Store 无法原子重验 Registry 时，才登记有界 DVR Demo。
