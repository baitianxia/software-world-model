# Iteration 001 JWT Architecture Validation Formal Contract

| 元数据 | 值 |
|---|---|
| Contract ID | `SWM-ITER-001-JWT-VALIDATION-FORMAL-CONTRACT` |
| Version | `0.1.0` |
| Status | `Frozen for JWT Demo Harness — Runtime Conformance Pending` |
| Purpose | `CAPABILITY_VALIDATION_ONLY` |
| Contract Digest | `sha256:468db1c92419faad5e66597496c2103c92d83331ab28a9a01e90e108072f36b9` |
| Canonicalization | `SWM-JWT-VALIDATION-CONTRACT-MARKDOWN-LF@1` |
| Base Knowledge Schema | `swm.local-git.software-knowledge / iter-001.initial.1 / sha256:1ba1a4090032464b4970bbc13a2a29685bb5b7f5d00fbf35b5da914e266c64fa` |
| Local Git Provider | `ITER-001-LOCAL-GIT-PROVIDER / 0.1.0 / sha256:d1eacb1e2c61c160c239b840cc84d660fef9fe282acd465358ae41f07bf76d1f` |
| no-tools Adapter Profile | `SWM-ADAPTER-OAI-RESPONSES-001 / 0.1.0 / file-sha256:f222ea0b86db6994db2f09baa2f9ad44cd4dd8b7746b88ef09573410db8add60` |
| Validation Baseline | [SWM-ACV-SLICE-JWT-001](../../../validation/architecture/Architecture_Capability_Validation_Slice_JWT_001.md) |

> 本契约只闭合 JWT Commit 验证切片实际经过的对象。它不修改已冻结 Base Schema，不进入production Registry，不定义项目或JWT专用知识类型。运行实例可以包含目标Commit、类名和库名；Type、Predicate、Rule和Verifier不得包含这些实例常量。

`Contract Digest`只覆盖下方两个标记之间的Payload。规范输入为UTF-8、LF、Unicode NFC、无BOM、无行尾空格；从BEGIN标记后的首字节到END标记前一行的LF执行SHA-256。

<!-- BEGIN JWT VALIDATION FORMAL CONTRACT PAYLOAD -->

## 1. 适用边界与导入

本契约只适用于`CAPABILITY_VALIDATION_ONLY` Execution Boundary、单个`SYSTEM` KnowledgeScope和一个Local Git Repository。它复用Base Schema的KnowledgeContext、Evidence、Entity、Fact / Inference Root与State、Candidate、Admission、Snapshot、Reader和Publication语义，以及Provider的`list / search / read / compare`、Artifact、Source Context、Selector和预算语义。

导入引用必须使用上方元数据中的exact ID、version和digest。运行对象同时保存完整`ExactBaseSchemaRef`、`ExactProviderRef`和`ExactAdapterProfileRef`；任一依赖无法按固定摘要解析时，本契约不可用。本文新增对象不得解析到production Schema、production Snapshot或production CURRENT。

本文使用Base Provider的`SWM-LOCAL-GIT-TYPED-TUPLE@1`作为唯一canonical value codec。基础构造只有`ENUM | ID | UINT64 | BOOL | BYTES | OID | DIGEST | INSTANT | ABSENT | TUPLE | ORDERED_LIST`。所有enum均为本文显式闭集；所有可选字段使用`ABSENT`；未知tag、字段省略、任意map、实现对象序列化和动态扩展均为codec failure。

导入类型别名只指向exact Base Schema / Provider依赖中已经闭合的同名对象：`ExactArtifactRef`、`ExactEvidenceRef`、`ExactEntityIdentityTerm`、`ResolvedFormalKnowledgeRef`、`ExactKnowledgeContext`、`ExactSnapshotRef`、`ExactProviderTargetResolutionReceiptRef`、`ExactSourceOperationRef`、`BaseTypedLiteral`和`GitPath`。每个别名在运行时必须解析完整Core / Digest / Envelope或依赖契约要求的完整Reference，不能用裸ID或裸digest代替。

跨Capability / Gateway边界统一使用`ExactVersionedRecordRef=TUPLE(ENUM(EXACT_VERSIONED_RECORD_REF),ENUM(BASE_SCHEMA|PROVIDER|ADAPTER_PROFILE|CAPABILITY|STRATEGY|PROMPT_CONTRACT|OUTPUT_CONTRACT|MODEL_CONFIGURATION|ISOLATION_RECEIPT|MODEL_ELIGIBILITY|MECHANICAL_VERIFIER),ID(recordId),ID(recordVersion),DIGEST(recordDefinitionOrResult))`。本文中的`ExactBaseSchemaRef`、`ExactProviderRef`、`ExactAdapterProfileRef`、`ExactCapabilityRef`、`ExactStrategyRef`、`ExactPromptContractRef`、`ExactOutputContractRef`、`ExactModelConfigurationRef`、`ExactIsolationReceiptRef`、`ExactModelResultEligibilityRef`和`ExactMechanicalVerifierRef`分别是对应enum variant，且必须从其权威Repository解析完整Record并重算Digest；variant不能互换。

`ExactProviderToolRequestRef=TUPLE(ENUM(PROVIDER_TOOL_REQUEST_REF),ENUM(RESOLVE|LIST|SEARCH|READ|COMPARE),ID(toolContractVersion),BYTES(canonicalRequestBytes),DIGEST(BYTES(canonicalRequestBytes)))`。canonical bytes必须能由exact Provider按所选Tool的Request codec唯一解码，且解码后的DataSource、Binding、Selector、target、parameters和budget与BuildTarget授权逐字一致。

`TypedLimitation=TUPLE(ENUM(TYPED_LIMITATION),ENUM(SOURCE_BOUNDARY|LIBRARY_DEFAULT|RUNTIME_CONFIGURATION|DYNAMIC_DISPATCH|INCOMPLETE_COVERAGE),AtomicTerm|ABSENT,ExactKnowledgeContext)`。它只能收窄Conclusion的成立范围，不能承载第二个结论或自然语言补写。

`ExactThisContractRef=TUPLE(ENUM(JWT_VALIDATION_CONTRACT_REF),ID(SWM-ITER-001-JWT-VALIDATION-FORMAL-CONTRACT),ID(0.1.0),DIGEST(本文Contract Digest))`。`ExactValidationSchemaRef=TUPLE(ENUM(VALIDATION_SCHEMA_REF),ExactBaseSchemaRef,ExactThisContractRef)`；本文新增Fact / Inference、validation Snapshot、Candidate和Assessment全部绑定该复合Reference，不能只绑定Base Schema。

所有本文自校验对象统一使用：

`XCore → XDigest=SHA-256(canonical XCore bytes) → XEnvelope=TUPLE(ENUM(X),XCore,XDigest)`。

Core不得包含自身Digest、Envelope或任何后置Decision；Envelope必须逐字内联Core和Digest。普通内容摘要只有在本文明确给出完整preimage时才合法。

## 2. Execution Boundary、Requirement 与 BuildTarget

`ValidationExecutionBoundaryCore=TUPLE(ENUM(VALIDATION_EXECUTION_BOUNDARY_CORE),ID(runId),ENUM(CAPABILITY_VALIDATION_ONLY),ExactBaseSchemaRef,ExactProviderRef,ExactAdapterProfileRef,ID(knowledgeScopeId),ID(validationStoreId),ID(validationCurrentNamespace),INSTANT(createdAt))`。

`RequirementNeedCore=TUPLE(ENUM(REQUIREMENT_NEED_CORE),ID(requirementRevisionId),ID(needId),UINT64(needOrdinal),ENUM(REVISION_SCOPE|DEPENDENCY_CHANGE|TOKEN_GENERATION_CHANGE|TOKEN_USE_AND_VALIDATION_CHANGE|TOKEN_REFRESH_CHANGE|UNKNOWN_BOUNDARY),BYTES(questionUtf8Nfc),BOOL(required))`。`needOrdinal`从0连续，`required=true`；同一Revision恰有六项且按ordinal排序。Need只能通过发布新的Requirement Revision改变，不能原地修改。

`RevisionImpactBuildTargetCore=TUPLE(ENUM(REVISION_IMPACT_BUILD_TARGET_CORE),ValidationExecutionBoundary,ID(repositoryIdentity),OID(targetCommit),OID(baseCommit),ENUM(EXPLICIT_PARENT_COMPARISON),ExactProviderTargetResolutionReceiptRef,ORDERED_LIST(RequirementNeed),BuildBudget)`。

`BuildBudget=TUPLE(ENUM(BUILD_BUDGET),UINT64(maxToolSteps),UINT64(maxFilesRead),UINT64(maxSourceBytes),UINT64(maxAtomicTermBytes),UINT64(maxModelCalls),UINT64(maxDurationMillis),UINT64(maxCostMicrounits))`；全部上限必须大于0。Target Resolution Receipt必须机械证明target与base均为同一Repository的exact commit，且base是target的唯一显式选择parent。六个Need、Boundary、Repository、两个Commit和预算全部进入BuildTarget Digest。

Application Authority在调查前签发Boundary、Requirement Revision和BuildTarget。模型只能引用，不能创建、替换或缩小这些对象。短SHA、错误parent、其他Repository、少于六个Need或擅自扩大Selector均失败关闭。

## 3. 模型隔离与授权输入

`ModelCallRole`闭集为`INVESTIGATION_PLANNER|FACT_PROPOSER|KNOWLEDGE_REVIEWER|INFERENCE_PROPOSER|SUFFICIENCY_REVIEWER|ANSWER_GENERATOR|ANSWER_REVIEWER`。

`AuthorizedInputItem`是closed union：

- `BOUNDARY(ValidationExecutionBoundary)`
- `REQUIREMENT(ORDERED_LIST(RequirementNeed))`
- `BUILD_TARGET(RevisionImpactBuildTarget)`
- `SOURCE_OBSERVATION(ExactArtifactRef,ExactEvidenceRef|ABSENT)`
- `FORMAL_KNOWLEDGE(ResolvedFormalKnowledgeRef)`
- `KNOWLEDGE_PROPOSAL(ExactKnowledgeProposalRef)`
- `ASSESSMENT(NeedAssessment)`
- `ANSWER_CANDIDATE(AnswerCandidate)`
- `CONTRACT_REF(ExactBaseSchemaRef|ExactProviderRef|ExactAdapterProfileRef|ExactThisContractRef)`。

`AuthorizedInputManifestCore=TUPLE(ENUM(AUTHORIZED_INPUT_MANIFEST_CORE),ValidationExecutionBoundary,ModelCallRole,ExactCapabilityRef,ExactStrategyRef,ExactPromptContractRef,ExactModelConfigurationRef,ORDERED_LIST(AuthorizedInputItem),UINT64(totalCanonicalBytes))`。Item按`(variant,canonical item digest)`唯一升序；需要语义顺序的Need列表在Item内部保留ordinal。Manifest列表与实际rendered model messages必须双向无missing/extra。

角色输入矩阵固定如下：

| Role | 允许的领域输入 | 禁止输入 |
|---|---|---|
| Investigation Planner | Boundary、Requirement、BuildTarget、此前Tool形成的Source Observation | Formal Snapshot答案、Direct Agent答案、工作区或隐藏会话 |
| Fact Proposer | Boundary、BuildTarget、Source Observation、Contract Ref | 未授权Artifact、其他Revision、Direct Agent答案 |
| Knowledge Reviewer | Boundary、BuildTarget、待审核Proposal；Fact审核只增加Proposal列出的Source Observation，Inference审核只增加Proposal列出的Formal Knowledge | 生成模型会话、隐藏推理、未列Source或Premise |
| Inference Proposer | Boundary、Requirement、同Snapshot Formal Knowledge、Contract Ref | Artifact Payload、Evidence Quote、Source Tool结果 |
| Sufficiency Reviewer | Boundary、Requirement、同Snapshot Formal Knowledge、Contract Ref | Source Observation、Artifact、Evidence内容、调查会话 |
| Answer Generator | Boundary、Requirement、Need Assessment、同Snapshot Formal Knowledge | 所有Source Observation、Artifact、Evidence内容、调查会话 |
| Answer Reviewer | Boundary、Requirement、Need Assessment、Answer Candidate、其引用的同Snapshot Formal Knowledge | 所有Source Observation、Artifact、Evidence内容、调查会话 |

`ModelUsage=TUPLE(ENUM(MODEL_USAGE),UINT64(inputTokens),UINT64(outputTokens),UINT64(reasoningTokens),UINT64(cachedInputTokens),UINT64(durationMillis),UINT64(costMicrounits),ENUM(COMPLETE|PARTIAL|UNKNOWN))`。

`RenderedMessage=TUPLE(ENUM(SYSTEM|USER|ASSISTANT),BYTES(contentUtf8Nfc))`；`RenderedMessageSequenceCore=TUPLE(ENUM(RENDERED_MESSAGE_SEQUENCE_CORE),ORDERED_LIST(RenderedMessage))`。`CanonicalProviderRequestCore=TUPLE(ENUM(CANONICAL_PROVIDER_REQUEST_CORE),ExactAdapterProfileRef,ExactModelConfigurationRef,RenderedMessageSequence,ENUM(NO_EXTERNAL_ACCESS),BYTES(exactProviderRequestBody))`；request body必须与no-tools Adapter allowlist序列化结果逐字相等。

`ModelExecutionRecordCore=TUPLE(ENUM(MODEL_EXECUTION_RECORD_CORE),ValidationExecutionBoundary,ModelCallRole,AuthorizedInputManifest,ExactAdapterProfileRef,ExactModelConfigurationRef,ExactPromptContractRef,ExactOutputContractRef,RenderedMessageSequence,CanonicalProviderRequest,ExactIsolationReceiptRef,ExactModelConfigurationRef requestedModelRef,BYTES(actualModelFingerprintUtf8),ENUM(PINNED|OBSERVED_MUTABLE|UNRESOLVED_MUTABLE),BYTES(providerResponseBytes),DIGEST(BYTES(providerResponseBytes)),ExactModelResultEligibilityRef,ModelUsage)`。

每个含`ModelExecutionRecord`的model-produced Core都使用同一机械投影规则：先按该Record的`ExactOutputContractRef`从`providerResponseBytes`唯一解析一个canonical domain payload；payload必须逐字段等于该Core中位于ModelExecutionRecord字段之前、由对应Output Contract声明的全部模型可提议字段。Boundary、Schema、BuildTarget、Context、Artifact / Evidence / Formal Reference、ID和Digest由平台用权威对象覆盖并重新编码，但覆盖前的模型字段必须能唯一对齐，歧义、missing、extra或值冲突均失败。ModelExecutionRecord字段自身和任何平台后置Decision不属于domain payload，因此摘要图无环。

Isolation Receipt必须在dispatch前签发并证明实际请求使用no-tools Adapter：shell、文件系统、Web、MCP、Connector、Provider Tool、Agent Tool、托管检索、附件、历史会话和隐藏应用上下文均不可用。Eligibility不是`PASS`、模型身份不合格、Manifest与Request不一致或调用失败时，不得产生Proposal、Assessment或Answer。

## 4. Source Tool Loop

`SourceToolProposalCore=TUPLE(ENUM(SOURCE_TOOL_PROPOSAL_CORE),ValidationExecutionBoundary,RevisionImpactBuildTarget,UINT64(stepOrdinal),ENUM(RESOLVE|LIST|SEARCH|READ|COMPARE),ExactProviderToolRequestRef,BYTES(rationaleSummaryUtf8Nfc),DIGEST(BYTES(rationaleSummaryUtf8Nfc)),ModelExecutionRecord plannerExecution)`。Provider Tool Request必须逐字命中所选Tool的exact closed Request；`rationaleSummary`只用于审计，不授权参数。plannerExecution必须是同Boundary、同step的`INVESTIGATION_PLANNER`调用，且其Manifest只含§3矩阵允许的前序输入。

`BudgetUsage=TUPLE(ENUM(BUDGET_USAGE),UINT64(toolSteps),UINT64(filesRead),UINT64(sourceBytes),UINT64(modelCalls),UINT64(durationMillis),UINT64(costMicrounits))`；每项不得超过BuildTarget对应上限。

`SourceObservationSetCore=TUPLE(ENUM(SOURCE_OBSERVATION_SET_CORE),ORDERED_LIST(ExactArtifactRef),ORDERED_LIST(ExactEvidenceRef))`；两个列表分别按完整Reference digest唯一升序。`SourceToolStepCore=TUPLE(ENUM(SOURCE_TOOL_STEP_CORE),SourceToolProposal,ExactSourceOperationRef,ENUM(AUTHORIZED_COMPLETE|AUTHORIZED_PARTIAL|DENIED|FAILED),SourceObservationSet,BudgetUsage)`。stepOrdinal从0连续；下一Proposal只能看到Manifest授权的既有Step Observation。达到预算、重复同canonical request且无新Artifact、权限失败、BuildTarget满足或模型主动停止时终止。

Tool结果只能形成Artifact / Evidence或下一轮调查输入；Answer Generator与Answer Reviewer的Manifest不能包含本节对象。

## 5. 通用原子源码命题

本契约新增一个validation-only Fact Type：`swm.validation.fact.atomic-source-proposition@1`。

`SourceToken=TUPLE(ENUM(SOURCE_TOKEN),ENUM(JAVA|MAVEN|GENERIC),BYTES(exactSourceUtf8Nfc),DIGEST(BYTES(exactSourceUtf8Nfc)))`。Token保留来源写法，不声称已经解析为Entity或外部API语义。其bytes必须是Fact Evidence中一个受支持的词法token或一个完整表达式 /类型 /声明值节点，长度不超过BuildTarget `maxAtomicTermBytes`；不得包含完整方法、多个statement、整个文件、跨Evidence拼接或隐藏的摘要文本。

`AtomicTerm`是closed union：`ENTITY(ExactEntityIdentityTerm)|TOKEN(SourceToken)|LITERAL(BaseTypedLiteral)|ABSENT_TERM`。

`AtomicRole`闭集为`TARGET|OWNER|INPUT|OUTPUT|VALUE|TYPE|CONDITION|EXCEPTION|ORDER|DURATION|ALGORITHM|DECLARATION_SCOPE`。`AtomicRoleTerm=TUPLE(AtomicRole,UINT64(roleOrdinal),AtomicTerm)`；同Role ordinal从0连续。

`AtomicPredicate`闭集为：

`DECLARES_DEPENDENCY|DECLARES_INVOCATION|DECLARES_VALUE_BINDING|DECLARES_CONDITION|DECLARES_RETURN|DECLARES_EXCEPTION_HANDLING|DECLARES_COMMENT|DECLARES_TYPE_BRANCH|DECLARES_ORDERING`。

`AtomicSourceProposition=TUPLE(ENUM(ATOMIC_SOURCE_PROPOSITION),ExactEntityIdentityTerm subject,AtomicPredicate,ORDERED_LIST(AtomicRoleTerm),ENUM(CODE_DECLARES|BUILD_DESCRIPTOR_DECLARES|CODE_COMMENT_DECLARES))`。

RoleTerm按`(AtomicRole enum ordinal,roleOrdinal)`唯一升序，且Predicate角色基数固定如下：

| Predicate | 必需Role | 可选Role | 禁止边界 |
|---|---|---|---|
| `DECLARES_DEPENDENCY` | `TARGET[1]` | `VALUE[0..1]、DECLARATION_SCOPE[0..1]` | 不解释effective version或运行加载 |
| `DECLARES_INVOCATION` | `TARGET[1]` | `INPUT[0..n]、OUTPUT[0..1]、ORDER[0..1]` | 不解释callee内部行为或默认参数 |
| `DECLARES_VALUE_BINDING` | `TARGET[1]、VALUE[1]` | `TYPE[0..1]、CONDITION[0..1]` | 不跨语句补alias或运行值 |
| `DECLARES_CONDITION` | `CONDITION[1]` | `TARGET[0..n]、ORDER[0..1]` | 不把条件当作已满足 |
| `DECLARES_RETURN` | `OUTPUT[1]` | `CONDITION[0..1]、ORDER[0..1]` | 不声称调用方收到或使用 |
| `DECLARES_EXCEPTION_HANDLING` | `EXCEPTION[1..n]` | `CONDITION[0..1]、OUTPUT[0..1]、ORDER[0..1]` | 不补隐式异常 |
| `DECLARES_COMMENT` | `VALUE[1]` | `TARGET[0..1]` | Modality必须为`CODE_COMMENT_DECLARES` |
| `DECLARES_TYPE_BRANCH` | `TARGET[1]、TYPE[1]` | `CONDITION[0..1]、ORDER[0..1]` | 不推断runtime receiver type |
| `DECLARES_ORDERING` | `ORDER[1]` | `TARGET[0..n]、CONDITION[0..1]` | 不把词法顺序升级为运行保证 |

未列Role、超出基数、ordinal缺口或Modality与Predicate不匹配均为codec failure。

该Fact只允许一个连续`git-file-content` Evidence直接支持，或一个完整Maven dependency declaration Evidence直接支持。Proposition必须对应一个完整语法statement、expression、branch、return、catch或dependency declaration；同一Proposition不能折叠多个statement或方法级摘要。Fact Proposal可以由模型提取，但独立Knowledge Reviewer必须重新读取同一冻结Evidence并判定每个Term都由该范围直接呈现。跨文件关系、callee行为、API默认、运行时状态、作者意图和模型常识不得进入Fact。

注释使用`CODE_COMMENT_DECLARES`，只能证明注释声明；不能支持代码行为或默认算法结论。

`AtomicSourceFactProposalCore=TUPLE(ENUM(ATOMIC_SOURCE_FACT_PROPOSAL_CORE),ValidationExecutionBoundary,RevisionImpactBuildTarget,ORDERED_LIST(ID(relatedNeedId)),ExactValidationSchemaRef,ExactKnowledgeContext,AtomicSourceProposition,ExactArtifactRef,ExactEvidenceRef,ModelExecutionRecord factProposalExecution)`。relatedNeedId按Need ordinal唯一升序且必须存在于同一BuildTarget；至少一项。平台从Proposition重算候选Identity；模型提供的knowledge ID、Entity ID、Context、Evidence locator或digest一律丢弃并由平台权威对象替换。

## 6. 完整来源选择 Evidence 与 Fact

本契约新增两个validation-only Evidence Representation；每条Evidence仍然恰好引用一个Artifact。

`CompleteChangeSetEvidenceCore=TUPLE(ENUM(COMPLETE_CHANGE_SET_EVIDENCE_CORE),ExactArtifactRef,ID(repositoryIdentity),OID(baseCommit),OID(targetCommit),ORDERED_LIST(RevisionChangeMember),UINT64(cardinality),ENUM(GIT_PATH_BYTE_ASC),BOOL(reachedTerminal),ENUM(NO_CURSOR),ENUM(NO_TRUNCATION),DIGEST(artifactPayloadContent))`。Artifact必须是Provider `compare / LOCAL_GIT_TREE_CHANGESET`的完整单页结果；member、count、ordering、Commit和payload digest与Artifact双向一致。

`CompleteLiteralSelectionEvidenceCore=TUPLE(ENUM(COMPLETE_LITERAL_SELECTION_EVIDENCE_CORE),ExactArtifactRef,ID(repositoryIdentity),OID(commit),GitPath(sourcePath),SourceToken literalSelector,ORDERED_LIST(SourceLiteralMatch),UINT64(cardinality),ENUM(BYTE_OFFSET_ASC),BOOL(reachedTerminal),ENUM(NO_CURSOR),ENUM(NO_TRUNCATION),UINT64(scannedBytes),UINT64(sourceBlobBytes),DIGEST(artifactPayloadContent))`。Artifact必须是Provider `CONTENT_LITERAL`固定到该单一source path的完整单页Search Match Set或完整零结果Query Observation；`reachedTerminal=true`、`scannedBytes=sourceBlobBytes`且没有跳过适用bytes。

这两个Evidence的Identity、Context和Digest使用本文统一Core / Digest / Envelope规则；Artifact不可用、字段错配、分页、部分扫描或摘要错配时不得创建Evidence。

`ExactValidationEvidenceRef`是closed union：`CHANGE_SET_EVIDENCE(ID(evidenceId),CompleteChangeSetEvidence) | LITERAL_SELECTION_EVIDENCE(ID(evidenceId),CompleteLiteralSelectionEvidence)`。ID由平台在Evidence Materialization时分配；完整Envelope和Digest必须可回读，模型不能创建或替换该Reference。

本契约新增`swm.validation.fact.closed-revision-change-set@1`。

`RevisionChangeMember=TUPLE(UINT64(changeOrdinal),ENUM(ADDED|DELETED|MODIFIED|TYPE_CHANGED),ExactEntityIdentityTerm sourceUnit,GitPath(beforePath)|ABSENT,GitPath(afterPath)|ABSENT,OID(beforeObject)|ABSENT,OID(afterObject)|ABSENT)`。

`ClosedRevisionChangeSetProposition=TUPLE(ENUM(CLOSED_REVISION_CHANGE_SET),ExactEntityIdentityTerm baseRevision,ExactEntityIdentityTerm targetRevision,ORDERED_LIST(RevisionChangeMember),UINT64(cardinality),ENUM(GIT_PATH_BYTE_ASC),ENUM(COMPLETE))`。

该Fact只接受一个`CompleteChangeSetEvidence`。member列表必须与Evidence双向无missing/extra，cardinality和顺序可机械重算；模型不得参与该Fact的内容形成。

本契约同时新增`swm.validation.fact.closed-source-literal-selection@1`，只用于证明一个exact source unit中某个来源token的完整匹配集合：

`SourceLiteralMatch=TUPLE(UINT64(matchOrdinal),UINT64(startByte),UINT64(endByte),DIGEST(matchedBytes))`。

`ClosedSourceLiteralSelectionProposition=TUPLE(ENUM(CLOSED_SOURCE_LITERAL_SELECTION),ExactEntityIdentityTerm sourceUnit,ExactKnowledgeContext,SourceToken literalSelector,ORDERED_LIST(SourceLiteralMatch),UINT64(cardinality),ENUM(BYTE_OFFSET_ASC),ENUM(COMPLETE))`。

它只接受一个`CompleteLiteralSelectionEvidence`。每个match range必须回放到同一Artifact并逐字等于selector bytes；列表、cardinality和顺序双向重算。零项使用真实空列表并表示“该完整source unit在该exact commit中没有此literal token”，不外推到模块、仓库、依赖库或运行时。

三个新增Fact Type的Identity Scheme ID分别等于完整Fact Type ID，Canonical Proposition的完整closed bytes构成Stable Semantic Key，Identity Context Key为EMPTY；exact Git commit仍保留在State Applicability Context。所有Entity Term必须在Fact Attempt开始时已经解析为同validation Snapshot或获准上游Snapshot中的正式Entity，不使用Candidate-local Entity。

`MechanicalVerificationCheck=TUPLE(ENUM(REFERENCE|CONTEXT|MEMBER_SET|CARDINALITY|ORDERING|TERMINAL|CURSOR|TRUNCATION|PAYLOAD_DIGEST),ENUM(PASS|FAIL))`；恰含九项且按enum顺序。`MechanicalVerificationResultCore=TUPLE(ENUM(MECHANICAL_VERIFICATION_RESULT_CORE),ExactMechanicalVerifierRef,DIGEST(propositionCanonicalBytes),DIGEST(evidenceCanonicalBytes),ORDERED_LIST(MechanicalVerificationCheck),ENUM(PASS|FAIL))`；只有九项均PASS时Overall为PASS。`MechanicalFactConstructionCore=TUPLE(ENUM(MECHANICAL_FACT_CONSTRUCTION_CORE),ValidationExecutionBoundary,ExactValidationSchemaRef,ENUM(CLOSED_REVISION_CHANGE_SET|CLOSED_SOURCE_LITERAL_SELECTION),ClosedRevisionChangeSetProposition|ClosedSourceLiteralSelectionProposition,ExactValidationEvidenceRef,ExactKnowledgeContext,MechanicalVerificationResult)`。variant、Proposition与Evidence类型必须一一对应；Result中的Evidence digest从Reference内完整Envelope重算。该Envelope进入Base Candidate重建和普通Admission，不直接写Snapshot。

## 7. 原子语义变化与有界未知 Inference

本契约新增两个validation-only Inference Type：

### 7.1 `swm.validation.inference.atomic-semantic-change@1`

`ChangeAspect`闭集为`DEPENDENCY|API_CALL|DATA_FLOW|CONTROL_FLOW|EXCEPTION_FLOW|VALUE_SEMANTICS|REFRESH_BEHAVIOR`。

`SemanticRelationPredicate`闭集为`ADDS|REMOVES|REPLACES|TRANSFORMS_TO|VALIDATES_BEFORE|RETURNS_WHEN|TREATS_AS|PRESERVES_WITHIN_BOUNDARY|CHANGES_ORDER`。`SemanticRelation=TUPLE(ENUM(SEMANTIC_RELATION),SemanticRelationPredicate,AtomicTerm subject,ORDERED_LIST(AtomicRoleTerm))`。

Semantic Relation的角色基数固定如下：`ADDS|REMOVES`要求`TARGET[1]`；`REPLACES|TRANSFORMS_TO`要求`INPUT[1]、OUTPUT[1]`；`VALIDATES_BEFORE`要求`TARGET[1]、ORDER[1]`；`RETURNS_WHEN`要求`OUTPUT[1]、CONDITION[1]`；`TREATS_AS`要求`INPUT[1]、OUTPUT[1]`且可选`CONDITION[0..1]`；`PRESERVES_WITHIN_BOUNDARY`要求`OUTPUT[1]、DURATION[1]`且可选`CONDITION[0..1]`；`CHANGES_ORDER`要求`INPUT[1]、OUTPUT[1]`。其他Role、重复单值Role、ordinal缺口或空列表非法。

`AtomicSemanticChangeConclusion=TUPLE(ENUM(ATOMIC_SEMANTIC_CHANGE),ExactEntityIdentityTerm baseRevision,ExactEntityIdentityTerm targetRevision,ExactEntityIdentityTerm affectedEntity,ChangeAspect,ENUM(ADDED|REMOVED|MODIFIED),SemanticRelation,ORDERED_LIST(TypedLimitation))`。

每个Conclusion只表达一个affected entity、一个aspect和一个原子变化；不得用一条宽泛History摘要满足多个Need。允许前提只有同一固定Snapshot中的`revision-parent`、`revision-change`、`closed-revision-change-set`、`closed-source-literal-selection`和`atomic-source-proposition` Fact，以及已发布的同类型原子变化。BEFORE / AFTER Fact必须通过KnowledgeContext明确区分，且base / target逐字等于BuildTarget。

### 7.2 `swm.validation.inference.bounded-unknown@1`

`UnknownBoundaryConclusion=TUPLE(ENUM(BOUNDED_UNKNOWN),ExactEntityIdentityTerm subject,ENUM(LIBRARY_DEFAULT|RUNTIME_CONFIGURATION|DYNAMIC_DISPATCH|UNREAD_SOURCE),ExactKnowledgeContext,ORDERED_LIST(RequiredPremiseDescriptor),ENUM(NOT_ESTABLISHED_WITHIN_BOUNDARY),ORDERED_LIST(TypedLimitation))`。

`RequiredPremiseDescriptor=TUPLE(ENUM(REQUIRED_PREMISE_DESCRIPTOR),AtomicPredicate|SemanticRelationPredicate,ORDERED_LIST(AtomicRoleTerm))`，只声明建立目标结论还缺少什么正式前提，不断言全局不存在。至少一个required premise在当前授权Boundary内未被Structured Support中的available formal premises满足；如果正式知识已经满足，不能形成Unknown。

### 7.3 Structured Support

`InferenceSupportStep`是closed union：

- `ALIGN_REVISION(ResolvedFormalKnowledgeRef baseFactRef,ResolvedFormalKnowledgeRef targetFactRef)`
- `SELECT_ATOMIC_PREMISE(ResolvedFormalKnowledgeRef premise,AtomicPredicate)`
- `COMPARE_ATOMIC_TERMS(ResolvedFormalKnowledgeRef beforeRef,ResolvedFormalKnowledgeRef afterRef,ORDERED_LIST(AtomicRole))`
- `FORM_RELATION(SemanticRelation)`
- `DECLARE_LIMITATION(TypedLimitation)`
- `CHECK_MISSING_PREMISE(RequiredPremiseDescriptor,ORDERED_LIST(ResolvedFormalKnowledgeRef))`。

`DependencyEdge=TUPLE(ResolvedFormalKnowledgeRef fromInference,ResolvedFormalKnowledgeRef toPremise)`；`DependencyDagCore=TUPLE(ENUM(DEPENDENCY_DAG_CORE),ORDERED_LIST(ResolvedFormalKnowledgeRef nodes),ORDERED_LIST(DependencyEdge))`，node和edge按完整canonical digest唯一升序。`InferenceStructuredSupportCore=TUPLE(ENUM(INFERENCE_STRUCTURED_SUPPORT_CORE),ExactSnapshotRef,ORDERED_LIST(ResolvedFormalKnowledgeRef directPremises),ORDERED_LIST(ResolvedFormalKnowledgeRef flattenedFactLeaves),ORDERED_LIST(InferenceSupportStep),UINT64(depth),DependencyDag,ExactKnowledgeContext,ORDERED_LIST(TypedLimitation))`。Step ordinal由列表位置确定；输入必须来自已出现的premise或前序step。Fact leaf非空、DAG无环且所有Reference属于同一exact Snapshot。

`InferenceProposalCore=TUPLE(ENUM(INFERENCE_PROPOSAL_CORE),ValidationExecutionBoundary,RevisionImpactBuildTarget,ORDERED_LIST(ID(relatedNeedId)),ExactValidationSchemaRef,ENUM(ATOMIC_SEMANTIC_CHANGE|BOUNDED_UNKNOWN),AtomicSemanticChangeConclusion|UnknownBoundaryConclusion,InferenceStructuredSupport,ModelExecutionRecord inferenceProposalExecution)`。relatedNeedId规则与Fact Proposal相同。

两个新增Inference Type的Identity Scheme ID分别等于完整Inference Type ID，完整Conclusion closed bytes构成Stable Semantic Key，Identity Context Key为EMPTY；Context仍完整保留在Inference State。`ExactKnowledgeProposalRef`是closed union：`FACT_PROPOSAL(ID(proposalId),AtomicSourceFactProposal) | INFERENCE_PROPOSAL(ID(proposalId),InferenceProposal)`；所内联Envelope和Digest必须逐字一致。Closed revision change set和closed source literal selection由平台机械构建，不存在模型Proposal variant。

## 8. 独立Knowledge Review与Admission

`KnowledgeReviewFinding`闭集为`EVIDENCE_DOES_NOT_ENTAIL_TERM|PREMISE_NOT_IN_SNAPSHOT|REVISION_MISMATCH|CONTEXT_MISMATCH|MODALITY_OVERSTATED|RELATION_UNSUPPORTED|LIMITATION_MISSING|UNKNOWN_BOUNDARY_NOT_CLOSED|CANDIDATE_NOT_ATOMIC|UNAUTHORIZED_INPUT|DIGEST_OR_CODEC_INVALID`。

`KnowledgeReviewCore=TUPLE(ENUM(KNOWLEDGE_REVIEW_CORE),ValidationExecutionBoundary,ExactKnowledgeProposalRef,ModelExecutionRecord reviewerExecution,ENUM(PASS|REVISE|REJECT|UNKNOWN),ORDERED_LIST(TUPLE(KnowledgeReviewFinding,UINT64(targetMemberOrdinal))))`。Reviewer Execution必须是新的`KNOWLEDGE_REVIEWER`调用，model call、Strategy、Prompt revision和Authorized Manifest均不同于Proposal调用；它必须重新取得Proposal所列全部Evidence或Formal Premise，不能读取生成模型会话。

`PASS`要求finding为空；其他结果要求非空。Reviewer只提交判断，不能签发Admission Decision。Knowledge Verifier随后机械重算Boundary、BuildTarget、Evidence / Premise Reference、Context、atomicity、codec、digest、Generation / Review隔离和Model Eligibility；全部适用Obligation为PASS后才可形成Base `ACCEPT`并进入validation Snapshot。

Fact必须先发布；Inference只能在新的Application Attempt中引用已发布Fact。Candidate不能成为同轮Inference前提。validation State、Snapshot和CURRENT与production物理或逻辑隔离，不能被production Reader解析。

## 9. 逐 Need 充分性

`NeedSupportBinding=TUPLE(ENUM(NEED_SUPPORT_BINDING),RequirementNeed,ExactSnapshotRef,ORDERED_LIST(ResolvedFormalKnowledgeRef),ORDERED_LIST(DIGEST(exactSupportedConclusionMember)),ORDERED_LIST(TypedLimitation))`。每个member digest必须从引用Fact Proposition或Inference Conclusion的完整member重算；引用必须属于同一Snapshot。

`NeedAssessmentCore=TUPLE(ENUM(NEED_ASSESSMENT_CORE),ValidationExecutionBoundary,ID(requirementRevisionId),ExactSnapshotRef,RequirementNeed,ENUM(SATISFIED|GAP|UNKNOWN|CONFLICT|INSUFFICIENT),NeedSupportBinding|ABSENT,ORDERED_LIST(AssessmentFinding),ModelExecutionRecord sufficiencyReviewExecution)`。该Execution必须为独立`SUFFICIENCY_REVIEWER`调用，其Manifest只含本Need、同Snapshot正式知识和Contract Ref。

`AssessmentFinding`闭集为`NO_FORMAL_SUPPORT|TARGET_MISMATCH|SEMANTIC_NON_ENTAILMENT|MEMBER_NOT_FOUND|SNAPSHOT_MISMATCH|CONTEXT_MISMATCH|MODALITY_MISMATCH|COVERAGE_INCOMPLETE|UNKNOWN_NOT_DISCLOSED|CONFLICT_UNRESOLVED`。

只有`SATISFIED`携带非空Binding；其他结果必须携带至少一个Finding且Binding为ABSENT。Assessment先由模型提出，再由独立Sufficiency Verifier从Snapshot重读并机械检查Reference / member / Context，使用独立model review判断语义蕴含。六个required Need全部`SATISFIED`时Overall才为`SATISFIED`；答案文本不能补齐Gap。

`OverallAssessmentCore=TUPLE(ENUM(OVERALL_ASSESSMENT_CORE),ValidationExecutionBoundary,ID(requirementRevisionId),ExactSnapshotRef,ORDERED_LIST(NeedAssessment),ENUM(SATISFIED|NOT_SATISFIED))`。Need按ordinal恰好六项且双向无missing/extra；只有六项全部`SATISFIED`时Overall为`SATISFIED`。

## 10. Answer Candidate、Review 与 Delivery

`AnswerClaimCore=TUPLE(ENUM(ANSWER_CLAIM_CORE),UINT64(claimOrdinal),ID(needId),BYTES(claimUtf8Nfc),ORDERED_LIST(NeedSupportBinding),ORDERED_LIST(TypedLimitation))`。claimOrdinal从0连续；每个Claim只能绑定一个Need，但一个Need可有多个Claim。Claim文字是交付表达，不是正式知识；其语义必须被Binding中的正式member蕴含。

`AnswerCandidateCore=TUPLE(ENUM(ANSWER_CANDIDATE_CORE),ValidationExecutionBoundary,ID(requirementRevisionId),ExactSnapshotRef,ORDERED_LIST(NeedAssessment),ORDERED_LIST(AnswerClaim),BYTES(answerBodyUtf8Nfc),ModelExecutionRecord answerGenerationExecution)`。Answer Generator的Manifest只能含Requirement、Assessment及其同Snapshot Formal Knowledge；Source Observation variant出现即codec failure。

`AnswerReviewFinding`闭集为`NEED_OMITTED|CLAIM_UNSUPPORTED|CLAIM_OVERSTATED|UNKNOWN_HIDDEN|CONFLICT_HIDDEN|WRONG_REVISION|SUPPORT_OUTSIDE_SNAPSHOT|ANSWER_ADDS_SOURCE_CONTENT|UNAUTHORIZED_INPUT|DIGEST_OR_CODEC_INVALID`。

`AnswerReviewCore=TUPLE(ENUM(ANSWER_REVIEW_CORE),ValidationExecutionBoundary,AnswerCandidate,ModelExecutionRecord answerReviewerExecution,ENUM(PASS|REVISE|REJECT),ORDERED_LIST(TUPLE(AnswerReviewFinding,UINT64(claimOrdinal)|ABSENT)))`。Reviewer必须是新的`ANSWER_REVIEWER`调用，只使用§3矩阵允许的输入。`PASS`要求finding为空且六个Need均在Answer中明确覆盖；`REVISE|REJECT`要求非空finding。

Final Authorization只能由Response Control在Answer Review PASS、全部Digest / Reference / Snapshot校验通过且无Source Operation发生于Knowledge Use Session时签发。Model、Reviewer、Fixture、Direct Agent和Demo Harness均不能签发Authorization或Delivery Receipt。

`SessionAuditEvent=TUPLE(UINT64(eventOrdinal),ENUM(SESSION_OPENED|FORMAL_READ|SOURCE_OPERATION_ATTEMPT|ARTIFACT_PAYLOAD_READ_ATTEMPT|EVIDENCE_CONTENT_READ_ATTEMPT|INVESTIGATION_ATTACH_ATTEMPT|SESSION_CLOSED),ENUM(ALLOWED|DENIED),BYTES(canonicalEventRecord),DIGEST(BYTES(canonicalEventRecord)))`；ordinal从0连续。`KnowledgeUseIsolationProofCore=TUPLE(ENUM(KNOWLEDGE_USE_ISOLATION_PROOF_CORE),ValidationExecutionBoundary,ID(knowledgeUseSessionId),ExactSnapshotRef,UINT64(sourceOperationCount),UINT64(artifactPayloadReadCount),UINT64(evidenceContentReadCount),BOOL(investigationSessionAttached),ORDERED_LIST(SessionAuditEvent))`；PASS要求三个count均为0且attached=false，所有event record必须由Telemetry权威存储解析并与count双向一致。

`FinalAuthorizationCore=TUPLE(ENUM(FINAL_AUTHORIZATION_CORE),ValidationExecutionBoundary,ID(requirementRevisionId),ExactSnapshotRef,OverallAssessment,AnswerCandidate,AnswerReview,KnowledgeUseIsolationProof,ENUM(AUTHORIZED))`。`DeliveryReceiptCore=TUPLE(ENUM(DELIVERY_RECEIPT_CORE),FinalAuthorization,INSTANT(deliveredAt),DIGEST(deliveredAnswerBytes))`；delivered bytes必须逐字等于AnswerCandidate body。二者只能由Response Control权威端口形成。

## 11. 摘要拓扑与失败语义

摘要拓扑固定为：

`Boundary → Need → BuildTarget → AuthorizedInputManifest → ModelExecutionRecord → Tool Proposal / Step → Fact Proposal → Knowledge Review → Admission → Fact Snapshot → Inference Proposal → Knowledge Review → Admission → Inference Snapshot → Need Assessment → Answer Candidate → Answer Review → Final Authorization → Delivery Receipt`。

任何后置对象不得进入前置Core或摘要前像。Proposal / Review / Assessment / Answer任一codec、digest、authority、model eligibility、reference或input isolation失败时，没有下游领域对象；不能降级为文本结果。超预算、来源不足或模型拒绝形成显式Gap / controlled failure，不能触发直接Agent或来源读取回答旁路。

## 12. Demo Capability Run 前的 Conformance 最小集

Demo Harness实现必须优先落地并通过以下纯契约Case；这些Case全部通过之前不得执行或宣称完整Capability Run：

1. 六个Need、exact Commit和Parent可构造唯一BuildTarget；短SHA、错Parent和Need缺项失败。
2. Authorized Input Manifest与Provider Request双向一致；向Answer角色加入Source Observation失败。
3. no-tools Receipt在dispatch前成立；任一Tool、会话、附件或隐藏上下文能力存在时Model Execution无资格。
4. 一个合法atomic-source Fact和一个跨Evidence、包含API默认的伪Fact分别PASS / FAIL。
5. closed revision change set与closed source literal selection对missing / extra member、错误cardinality、部分扫描和非terminal coverage失败。
6. Fact未发布时Inference premise失败；发布到exact Snapshot后可构造。
7. Semantic Change必须保持一个entity / aspect / relation；宽泛History摘要失败。
8. Unknown必须列出缺失前提和边界；把Unknown改成具体默认算法失败。
9. Need Binding引用其他Snapshot、相关但不蕴含member或漏一个Need时Overall不能SATISFIED。
10. Answer阶段出现Source Operation、Artifact / Evidence内容或调查会话输入时Review和Authorization失败。
11. validation Snapshot不能由production Reader解析或作为production Premise。
12. 对每个Core篡改一个字段，Digest重算或Envelope逐字比较必须失败；完整摘要图无环。

本文静态闭包通过后可以开始实现这些Conformance Case；本节运行通过才授权完整JWT Capability Run。两者都不表示H-04已经PASS或Iteration 001生产开工。

<!-- END JWT VALIDATION FORMAL CONTRACT PAYLOAD -->

## 13. 当前状态

本文Payload已通过静态闭包与六Need Formal Mapping复核，作为JWT Demo Harness的validation-only输入冻结。第12节Runtime Conformance尚未执行，因此只能开始Harness实现，不能执行完整Capability Run或进入production Registry。
