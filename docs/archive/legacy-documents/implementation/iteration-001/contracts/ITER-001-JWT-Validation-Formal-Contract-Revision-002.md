# Iteration 001 JWT Architecture Validation Formal Contract — Revision 002

| 元数据 | 值 |
|---|---|
| Contract ID | `SWM-ITER-001-JWT-VALIDATION-FORMAL-CONTRACT` |
| Version | `0.2.0-candidate` |
| Status | `Candidate — Mechanical Conformance Passed; Live Model Conformance Not Run` |
| Purpose | `CAPABILITY_VALIDATION_ONLY` |
| Supersedes For New Runs | `0.1.0`；历史 Contract 与 Manifest 保持不可变 |
| Base Contract | [0.1.0](ITER-001-JWT-Validation-Formal-Contract.md) |
| Correction Evidence | [SWM-ARCH-FEAS-JWT-002](../../../validation/architecture/Architecture_Feasibility_Review_JWT_002.md) |
| Executable Witness | `demo/swm_demo/formal_validation.py` + `demo/tests/test_formal_validation.py` |
| Production Authorization | `NONE` |

> 本 Revision 只修正 JWT validation-only Contract 的可实现性和判定缺陷，不改变 `SWM-ARCH@1.2`、22 个 Accepted 详细设计主题或 production Schema。除本文明确替换的条款外，0.1.0 的 closed type、Evidence、Fact、Inference、Admission、Snapshot 和 Provider 约束继续适用。本文进入 Frozen 前必须生成新的 exact Payload Digest、文件摘要和 Demo Manifest；不得重算旧 Manifest 摘要冒充原基线仍有效。

## 1. 修订原因

0.1.0 静态审计把“有一个可引用的正式成员”误当成了完整 Sufficiency Contract，遗漏了上游 [DD-APP-KNOWLEDGE-USE](../../../detailed-design/topics/DD-APP-KNOWLEDGE-USE.md) 已经要求的 `Sufficiency Criterion`、`Criterion Obligation Manifest` 和 `Joint Knowledge Constraint`。此外还存在以下可实现性断点：

1. `RenderedMessage` 无法回指 Manifest Item 和 Rendering Step，不能机械证明 Provider Request 与授权输入双向一致。
2. Fact 要求 Entity 已正式解析，摘要拓扑却没有 Entity Materialization / Admission / Publication。
3. 本地 Envelope 检查与真实 Provider Adapter Conformance 混为一个 Case。
4. Knowledge Use Isolation Proof 没有把被拒绝的 Source / Artifact / Evidence / Investigation 访问尝试计入失败。
5. H-04 10 分量表允许不同遗漏得到同分，不能证明逐 Claim 正确性与完整性守恒。

这些问题使 0.1.0 的 `6 / 6 STATIC SUPPORTED` 结论不足以授权 Capability Run。它们属于 validation-only Formal Contract 与实验设计缺陷，不是一般架构反例。

## 2. Requirement Revision 替换条款

0.1.0 §2 的 `RequirementNeedCore` 替换为：

`CriterionObligationCore=TUPLE(ENUM(CRITERION_OBLIGATION_CORE),ID(requirementRevisionId),ID(needId),ID(obligationId),UINT64(obligationOrdinal),ENUM(DIRECT_SUPPORT|ENUMERATION_COVERAGE|COUNTEREXAMPLE_CHECK|CONFLICT_DISCLOSURE|UNKNOWN_OR_LIMITATION_DISCLOSURE),BYTES(dimensionUtf8Nfc))`。

`RequirementNeedCore=TUPLE(ENUM(REQUIREMENT_NEED_CORE),ID(requirementRevisionId),ID(needId),UINT64(needOrdinal),ENUM(REVISION_SCOPE|DEPENDENCY_CHANGE|TOKEN_GENERATION_CHANGE|TOKEN_USE_AND_VALIDATION_CHANGE|TOKEN_REFRESH_CHANGE|UNKNOWN_BOUNDARY),BYTES(questionUtf8Nfc),BYTES(sufficiencyCriterionUtf8Nfc),ORDERED_LIST(CriterionObligation),BOOL(required))`。

`JointKnowledgeConstraintCore=TUPLE(ENUM(JOINT_KNOWLEDGE_CONSTRAINT_CORE),ID(requirementRevisionId),ID(constraintId),ORDERED_LIST(ID(needId)),ENUM(SAME_REPOSITORY_TARGET_PARENT_COMPARISON_CONTEXT),BYTES(jointCriterionUtf8Nfc))`。

`RequirementRevisionCore=TUPLE(ENUM(REQUIREMENT_REVISION_CORE),ID(requirementRevisionId),ORDERED_LIST(RequirementNeed),ORDERED_LIST(JointKnowledgeConstraint))`。

不变量：

- 六个 Need 的 ordinal 连续且 ID 与验证切片逐字相等。
- 每个 Need 至少有一个 Obligation；Obligation ordinal 在 Need 内连续，ID 全局唯一。
- `dimension` 只登记必须审核的语义维度，不预填答案、黄金值或 Formal Knowledge Reference。
- 至少一个 Joint Constraint 把六个 Need 固定到同一 Repository、Target、Parent 和 Comparison Context。
- Requirement Fidelity Reviewer 在任何 Source Operation 前独立审核 Question、Criterion、Obligation 和 Joint Constraint 的双向覆盖；生成者不能审核自己，也不能静默修改 Revision。
- `RevisionImpactBuildTargetCore` 引用完整 `RequirementRevision`，不再只内联六段 Question。

## 3. Manifest 与 Provider Request 闭包替换条款

0.1.0 §3 的 `AuthorizedInputItem` 增加：

- `PROMPT_INSTRUCTION(ExactPromptContractRef,UINT64(segmentOrdinal),BYTES(contentUtf8Nfc),DIGEST(content))`；
- `OUTPUT_CONTRACT(ExactOutputContractRef)`。

Manifest Item 使用 Rendering Order 保存，完整 Item Digest 必须唯一；需要集合排序的领域成员仍在 Item 内按各自 Contract 排序。

`RenderedInputItemCore=TUPLE(ENUM(RENDERED_INPUT_ITEM_CORE),DIGEST(exactAuthorizedInputItem),ExactPromptContractRef,ID(renderingStepId),ENUM(SYSTEM|USER|ASSISTANT),BYTES(contentUtf8Nfc),DIGEST(content))`。

`RenderedMessageSequenceCore=TUPLE(ENUM(RENDERED_MESSAGE_SEQUENCE_CORE),ORDERED_LIST(RenderedInputItem))`。

Gateway 必须机械证明：

1. 每个 Manifest Item 恰好产生一个 Rendered Input Item，二者 Digest 一一对应且顺序符合 Prompt Rendering Contract。
2. 不存在无 Manifest Item 的额外消息，也不存在未渲染的 Manifest Item。
3. Structured Output Schema、Model Configuration、资源参数和 Adapter Envelope 虽不都是自然语言消息，仍由 `CanonicalProviderRequestCore` 完整覆盖。
4. Isolation Receipt 在 dispatch 前绑定完整 Request Body Digest；Recording Transport 捕获的实际 Body 必须逐字命中该 Digest。

只比较消息文本、只扫描 Canary 或只检查 Response 无 Tool Event 都不能证明输入闭包。

## 4. Entity Bootstrap 与 Publication 拓扑

0.1.0 §6“所有 Entity Term 在 Fact Attempt 开始时已经解析”的约束保留，并补充以下必需阶段：

`EntityBootstrapMemberCore=TUPLE(ENUM(ENTITY_BOOTSTRAP_MEMBER_CORE),ExactArtifactRef,ExactEvidenceRef,ExactBaseSchemaRef,ID(identityAnchorContractId),DIGEST(rebuiltEffectiveEntityIdentityKey))`。

`EntityBootstrapManifestCore=TUPLE(ENUM(ENTITY_BOOTSTRAP_MANIFEST_CORE),ValidationExecutionBoundary,RevisionImpactBuildTarget,ORDERED_LIST(EntityBootstrapMember))`。

`EntityBootstrapPublicationCore=TUPLE(ENUM(ENTITY_BOOTSTRAP_PUBLICATION_CORE),EntityBootstrapManifest,ExactSnapshotRef expectedBaseOrNoCurrent,ORDERED_LIST(ResolvedFormalKnowledgeRef entityStates),ExactSnapshotRef entitySnapshot,ExactPublicationResultRef)`。

Entity 仍只使用 Base Schema 已注册的 `git-revision`、`source-unit`、`software-module`、`code-symbol` 和 `dependency-component` Anchor Contract；本文不增加 JWT 专用 Entity Kind。Entity 必须经 Evidence 重建、Resolution、Admission 和 validation Snapshot Publication。Fact Proposal 只能引用 `entitySnapshot` 或其后继 Snapshot 中的正式 Entity，不能使用 Candidate-local Entity 或裸 ID。

新的摘要拓扑为：

`Boundary → Requirement / Obligation / Joint → BuildTarget → Tool / Artifact / Evidence → Entity Materialization / Admission / Entity Snapshot → Fact Proposal / Review / Admission / Fact Snapshot → Inference Proposal / Review / Admission / Inference Snapshot → Obligation Support / Need Assessment / Joint Assessment → Answer → Review → Isolation Proof → Authorization → Delivery → external Claim Preservation Evaluation`。

Fact 与 Inference 不得同批发布；Inference 的全部 premise 必须来自已经发布的 exact Fact Snapshot。

## 5. Obligation Support 与整体充分性

0.1.0 §9 的 `NeedSupportBinding` 替换为：

`ObligationSupportCore=TUPLE(ENUM(OBLIGATION_SUPPORT_CORE),CriterionObligation,ExactSnapshotRef,ENUM(DIRECT_SUPPORT|ENUMERATION_COVERAGE|COUNTEREXAMPLE_CHECK|CONFLICT_DISCLOSURE|UNKNOWN_OR_LIMITATION_DISCLOSURE),ORDERED_LIST(ResolvedFormalKnowledgeRef),ORDERED_LIST(DIGEST(exactSupportedConclusionMember)),ExactCoverageResultRef|ABSENT,ORDERED_LIST(TypedLimitation))`。

`NeedSupportBindingCore=TUPLE(ENUM(NEED_SUPPORT_BINDING_CORE),RequirementNeed,ExactSnapshotRef,ORDERED_LIST(ObligationSupport))`。

`JointConstraintAssessmentCore=TUPLE(ENUM(JOINT_CONSTRAINT_ASSESSMENT_CORE),JointKnowledgeConstraint,ExactSnapshotRef,ORDERED_LIST(ID(needId)),ENUM(SATISFIED|GAP|UNKNOWN|CONFLICT|INSUFFICIENT),ORDERED_LIST(AssessmentFinding),ModelExecutionRecord)`。

Sufficiency Verifier 必须双向检查每个 Need 的 Obligation Set；漏项、重复项、错误 Support Role、相关但不蕴含、Coverage 未闭合、未知未披露或跨 Snapshot 引用使该 Need 不得 `SATISFIED`。整体只有六个 Need 和全部 Joint Constraint 都 `SATISFIED` 才能 `SATISFIED`。Answer Candidate 的 Claim Support 还必须双向覆盖全部 required Obligation；只“提到六个 Need”不够。

## 6. Knowledge Use Isolation Proof

0.1.0 §10 的计数替换为：

`KnowledgeUseIsolationProofCore=TUPLE(ENUM(KNOWLEDGE_USE_ISOLATION_PROOF_CORE),ValidationExecutionBoundary,ID(knowledgeUseSessionId),ExactSnapshotRef,UINT64(sourceOperationAttemptCount),UINT64(sourceOperationExecutedCount),UINT64(artifactPayloadReadAttemptCount),UINT64(evidenceContentReadAttemptCount),UINT64(investigationAttachAttemptCount),ORDERED_LIST(SessionAuditEvent))`。

Authorization 要求五个计数全部为 `0`，并与 Event 集双向一致。被权限层拒绝的访问虽然没有泄露内容，仍证明 Answer / Review 执行尝试越过正式知识边界，当前 Candidate 不得放行；修正必须使用新的 Answer Attempt。

## 7. Direct Claim Oracle 与对照判定

Direct Claim Oracle 是被测系统外部的评分输入，禁止进入任何 Model Manifest、Artifact、Evidence、Candidate、Snapshot、Assessment 或 Answer。每个 Item 至少固定：

- Claim ID 与 canonical semantic key；
- exact Repository / Target / Parent / Context；
- `DIRECT_OBSERVATION | SOURCE_DECLARED | DERIVED | UNKNOWN_BOUNDARY` Modality；
- Source Locator / Digest、必要前提、限制、Coverage 和独立核对结果；
- 对应 Need / Obligation，以及是否为实质 Claim。

完整 Run 开始前必须重新执行 Direct Agent，冻结 Answer、逐 Claim Oracle 和评分记录。H-04 历史 10 分黄金要点只作为回归参考，不能代替 Oracle。

Capability PASS 同时要求：

1. SWM Delivered Claim semantic-key set 与全部实质 Direct Claim Oracle 双向相等；missing、extra、modality/context/target 改变均为失败。
2. SWM 没有 Direct Agent 未犯的实质错误；任何错误不能由总分抵消。
3. 在上述逐 Claim 门禁通过后，H-04 量表分数才作为可读性和回归辅助指标，且 SWM 分数不得低于 Direct Agent。

如果新的 Direct Agent / Oracle 暴露 Requirement Obligation 漏项，当前 Run 在 Source Operation 前以 `BASELINE_INVALID` 停止，发布新的 Requirement / Run Configuration；不得运行后删除 Oracle Claim 或弱化 Criterion。

## 8. Conformance 分层

Conformance 分为两层，不得合并结果：

### 8.1 Mechanical Contract Conformance

使用确定性 Fixture，验证 BuildTarget、Requirement / Obligation / Joint 双向覆盖、Manifest Rendering、Request allowlist、Entity→Fact→Inference 拓扑、Coverage、Unknown、Snapshot 隔离、Answer 访问尝试拒绝和 Digest 图。它不向真实 Provider dispatch，不签发真实 `AI-ISOLATION-RECEIPT-01`，也不证明模型质量。

当前可执行见证为：

```bash
PYTHONPATH=demo python3 -m unittest demo.tests.test_formal_validation -v
```

### 8.2 Live Adapter Conformance

完整 Capability Run 前必须另行执行 [CC-MODEL-NO-TOOLS-001](../conformance/CC-MODEL-NO-TOOLS-001.md)，固定 Adapter Implementation Source Ref、Provider Project Configuration、exact Model Reference、Prompt / Output Contract、Recording Transport 和原始结果。只有真实 Provider 的 12 个 Case 全部 PASS，Run Boundary 才能引用有效 Conformance Result 并签发 dispatch 前 Receipt。

Codex CLI、带工具的 Agent Runtime、空工作目录、事后 Tool Event 扫描或本地伪 Provider 均不满足该门禁。

## 9. Harness Source 身份

Validation Run 的实现身份使用 closed union：

- `CLEAN_GIT_SOURCE(repositoryIdentity,fullCommitOid,treeOid)`；或
- `CONTENT_MANIFEST_SOURCE(ORDERED_LIST(path,byteLength,fileSha256),manifestSha256)`。

有 Git 时优先使用第一种；分发快照缺少外层 `.git` 时允许第二种，以避免把不可取得的 Commit 伪造为实现身份。两者都必须在 Run 前冻结；运行中任一字节变化使 Result Stale。Production Implementation Baseline 仍要求受控源码仓库，不因本 validation-only fallback 放宽。

## 10. 本 Revision 的准入状态

当前机械实现已在真实 `mall` Git 对象上通过 13 个 Case，其中第 13 个只是一条确定性机制见证：它执行 BuildTarget、Source Artifact / Evidence、Entity Snapshot、Fact Snapshot、Inference Snapshot、逐 Obligation Assessment、来源关闭 Answer、Authorization 和 provisional 20-Claim 双向对照。

该见证不包含真实 Investigation Model、Knowledge Reviewer、Sufficiency Reviewer、Answer Model 或 Answer Reviewer，也没有执行 Live Adapter Conformance。因而：

- 可以判定本文修正后的对象关系与失败关闭机制可实现；
- 不得把确定性 Candidate / Review / Answer Fixture 解释为真实模型能力；
- 不得把 provisional 20-Claim 集解释为最终 Direct Claim Oracle；
- 完整 JWT Capability Run、Iteration 001 解禁和 production 编码继续保持 `NOT_RUN / PAUSED`。
