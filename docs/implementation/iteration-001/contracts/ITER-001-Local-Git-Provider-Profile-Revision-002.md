# Iteration 001 Local Git Provider-specific Contract Profile — Revision 002

| 元数据 | 值 |
|---|---|
| Profile ID | `ITER-001-LOCAL-GIT-PROVIDER` |
| Version | `0.2.0` |
| Status | `Withdrawn Draft — Not a Current Validation Dependency` |
| Predecessor | [ITER-001-LOCAL-GIT-PROVIDER@0.1.0](ITER-001-Local-Git-Provider-Profile.md) / `sha256:d1eacb1e2c61c160c239b840cc84d660fef9fe282acd465358ae41f07bf76d1f` |
| Profile Contract Digest | `sha256:7095e6caa53c5a8c0c890b17317c31a2891e038d918c10c8ee3da294d62a89d9` |
| Contract Canonicalization | `SWM-LOCAL-GIT-PROFILE-MARKDOWN-LF@1` |
| Rule Pack Dependency | [ITER-001-FOUNDATIONAL-SOFTWARE-SEMANTICS@0.1.0](ITER-001-Foundational-Software-Semantics-Rule-Pack.md) / `sha256:6537b5868c3009b2dd6b470148475b33f8d6892c9b8e68bedd1143b715024da2` |
| Implementation Plan | [SWM-IMP-ITER-001](../Implementation_Plan_Iteration_001.md) |
| Design Baseline | [SWM-DBM-ITER-001-REV-002](../../../detailed-design/governance/Design_Baseline_Manifest_Iteration_001_Revision_002.md) |
| Proposed Schema Consumer | [iter-001.initial.2](ITER-001-Initial-Knowledge-Schema-Revision-002.md) |

> 本 Profile 创建新的 exact Provider Contract，不修改或覆盖冻结的 `0.1.0`。有效 Contract 是 exact predecessor 与本文扩展的闭合组合；本文只增加通用 Source Interpretation Observation 和单 Artifact 完整结果集选择能力，不改变 Local Git Tool、Artifact、Target、Retention、权限或错误语义。

> 撤回说明：本文仍依赖已撤回Rule Pack的旧摘要，传递依赖不成立。当前JWT验证切片只使用冻结的Provider `0.1.0`及其通用`list / search / read / compare`，不引用本文。本文保留为历史研究草案，不得进入Runtime Registry或开工基线。

`Profile Contract Digest` 只覆盖下方两个标记之间的内容。规范输入使用 UTF-8、LF、Unicode NFC，无 BOM、CRLF 或行尾空格；输入从 BEGIN 标记后的首字节开始，到 END 标记前一行的 LF 为止。

<!-- BEGIN LOCAL GIT PROFILE CONTRACT -->

## 1. Profile 身份与 Effective Contract

| 项 | 定义 |
|---|---|
| Profile Reference | `ITER-001-LOCAL-GIT-PROVIDER / 0.2.0 / 本文 Profile Contract Digest` |
| Exact Predecessor | `ITER-001-LOCAL-GIT-PROVIDER / 0.1.0 / sha256:d1eacb1e2c61c160c239b840cc84d660fef9fe282acd465358ae41f07bf76d1f` |
| Exact Rule Pack Dependency | `ITER-001-FOUNDATIONAL-SOFTWARE-SEMANTICS / 0.1.0 / sha256:6537b5868c3009b2dd6b470148475b33f8d6892c9b8e68bedd1143b715024da2` |
| Extension Scope | `COMPLETE_RESULT_SET_SELECTION@1` 与第 4 节注册的通用 Source Interpretation Observation Contract |

本 Profile 将 exact predecessor 的全部规范 Payload 作为不可变基础依赖。除本文明确新增的 Contract ID 外，`0.1.0` 的 Provider identity、typed tuple codec、Selector、Source Context、Canonical Target、`list/search/read/compare`、Artifact Kind / Payload Schema、Coverage、Cursor、预算、`NO_EVICTION`、错误和 Conformance 语义逐字节保持有效。

Predecessor 不是动态查找。实现和消费者必须以表中的 exact version/digest 展平依赖闭包；不得读取同 ID 的其他版本猜测语义。本文没有改变或重新定义 predecessor 中的任何既有 Contract ID。

## 2. 不变边界

Revision 002 继续满足：

1. 只读取单个本地非 bare Git 主工作树的 committed objects。
2. 只有 `list / search / read / compare` 四个只读 Tool；不增加 query、shell、hunk、rename、fetch 或工作树读取。
3. Artifact Kind / Payload Schema Registry 仍只有 predecessor §6.1 的六项；本文不引入新的 Source Artifact Kind。
4. 多页 Read Session 仍不聚合成新的 Payload。完整结果集选择只接受单个自身 Coverage 已为 COMPLETE 的 Artifact。
5. Source Interpretation 只对已经固化的 Artifact/Evidence 范围执行确定性typed规范化；有效Observation必须能由冻结Artifact、exact Profile及本文公开的解析/校验步骤完全重建，不使 Source Integration 成为正式知识 Owner。
6. 解释结果不能成为生产答案、正式 Fact 或 Inference；Knowledge Schema、Candidate 重建、独立 Verification 和 Admission 继续生效。

## 3. `COMPLETE_RESULT_SET_SELECTION@1`

### 3.1 责任与允许输入

该 Contract 在一个冻结 Source Artifact 内选择完整 typed result set 及其 Coverage，供 Evidence Locator 和封闭观察验证使用。只允许：

| Selection Kind | Artifact Kind / Payload Schema | Selected Value |
|---|---|---|
| `TREE_LISTING_SET` | `LOCAL_GIT_TREE_LISTING / 1` + `swm.payload.local-git.tree-listing@1` | 完整 ordered `TreeEntry` 集合与 Coverage |
| `SEARCH_MATCH_SET` | `LOCAL_GIT_SEARCH_MATCH_SET / 1` + `swm.payload.local-git.search-match-set@1` | 完整 ordered `SearchMatch` 集合与 Coverage |
| `QUERY_ZERO_SET` | `LOCAL_GIT_QUERY_OBSERVATION / 1` + `swm.payload.local-git.query-observation@1` | exact query、空成员集、cardinality=0 与 Coverage |
| `REVISION_CHANGE_SET` | `LOCAL_GIT_TREE_CHANGESET / 1` + `swm.payload.local-git.tree-changeset@1` | 完整 ordered `ChangeEntry` 集合与 Coverage |

Selection 必须绑定完整且可独立解析的 Artifact shell identity，而不是只保存 Artifact ID 或 Payload Digest。下列类型逐字复用 predecessor codec，并且所有嵌套 Reference 都必须从权威 Source Repository 解析到同一 canonical preimage：

- `ExactSelectionSourceContextRef=TUPLE(ENUM(EXACT_SELECTION_SOURCE_CONTEXT_REF),ID(sourceContextId),ID(LOCAL_GIT_SOURCE_CONTEXT_VOCABULARY@1),ID(LOCAL_GIT_SOURCE_CONTEXT_CANONICALIZATION@1),SourceContextExpression,DIGEST(sourceContextIdentity))`；`SourceContextExpression` 是 predecessor §3.2 的完整十字段 Tuple，末项 Digest 必须按 predecessor 的 `TUPLE(ENUM(SOURCE_CONTEXT_IDENTITY),ID(vocabularyId),ID(canonicalizationId),SourceContextExpression)` 重算。
- `ExactToolContractRef=TUPLE(ENUM(EXACT_TOOL_CONTRACT_REF),ID(toolContractId),ID(toolContractVersion),DIGEST(toolContract))`；`ExactProviderProfileRef=TUPLE(ENUM(EXACT_PROVIDER_PROFILE_REF),ID(ITER-001-LOCAL-GIT-PROVIDER),ID(0.2.0),DIGEST(profileContract))`，其中`profileContract`必须等于本文header的Profile Contract Digest；`ExactIdentityStrategyRef=TUPLE(ENUM(EXACT_IDENTITY_STRATEGY_REF),ID(strategyId),ID(strategyVersion),DIGEST(strategyDefinition))`；`ExactDataClassificationRef=TUPLE(ENUM(EXACT_DATA_CLASSIFICATION_REF),ID(classificationId),ID(classificationRevision),DIGEST(classificationRecord))`。这些 Ref 不接受版本范围、动态当前值、显示名称或调用方 inline 自报对象。
- `ExactSelectionArtifactShellCore=TUPLE(ENUM(EXACT_SELECTION_ARTIFACT_SHELL_CORE),ID(artifactId),TUPLE(ENUM(LOCAL_GIT_TREE_LISTING|LOCAL_GIT_SEARCH_MATCH_SET|LOCAL_GIT_QUERY_OBSERVATION|LOCAL_GIT_TREE_CHANGESET),UINT64(1)),ID(payloadSchemaId),ID(application/vnd.swm.local-git.typed-tuple),ExactSelectionSourceContextRef,ObservationBasis,DIGEST(payloadContent),DIGEST(coverage),ExactToolContractRef,ExactProviderProfileRef,ExactIdentityStrategyRef,ExactDataClassificationRef)`。`ObservationBasis`逐字复用 predecessor §3.2 的 `OBSERVATION_RESULT` variant并必须与 `SourceContextExpression` 中的值相等；`CLOSED_READ_SESSION` variant不适用于Selection。Artifact Kind、Payload Schema、Tool（分别为list、search、search、compare）、Source Context、Payload/Coverage Digest必须与§3.1对应行和已冻结 Artifact shell逐值相等。
- `ExactSelectionArtifactShellDigest=DIGEST(ExactSelectionArtifactShellCore)`；`ExactSelectionArtifactRef=TUPLE(ENUM(EXACT_SELECTION_ARTIFACT_REF),ExactSelectionArtifactShellCore,ExactSelectionArtifactShellDigest)`。Core 不含自身 Digest或Ref envelope。

Commit、Blob、partial page、Source Operation Result、Closed Read Session Result、搜索摘要和模型合并输出不适用。

### 3.2 Canonical Selector Tuple

Selector 使用 predecessor 的 `SWM-LOCAL-GIT-TYPED-TUPLE@1`。所有字段按下列顺序出现；可选项使用 typed `ABSENT`：

| Selection Kind | Canonical Selector Tuple |
|---|---|
| `TREE_LISTING_SET` | `TUPLE(ENUM(COMPLETE_RESULT_SET_SELECTION),ENUM(TREE_LISTING_SET),ID(repository),ObjectFormat,OID(commit),GitPath(tree),OID(tree),DIGEST(payloadContent),DIGEST(coverage))` |
| `SEARCH_MATCH_SET` | `TUPLE(ENUM(COMPLETE_RESULT_SET_SELECTION),ENUM(SEARCH_MATCH_SET),ID(repository),ObjectFormat,OID(commit),GitPath(searchRoot),QueryKind,DIGEST(queryBytes),DIGEST(payloadContent),DIGEST(coverage))` |
| `QUERY_ZERO_SET` | `TUPLE(ENUM(COMPLETE_RESULT_SET_SELECTION),ENUM(QUERY_ZERO_SET),ID(repository),ObjectFormat,OID(commit),GitPath(searchRoot),QueryKind,DIGEST(queryBytes),UINT64(0),DIGEST(payloadContent),DIGEST(coverage))` |
| `REVISION_CHANGE_SET` | `TUPLE(ENUM(COMPLETE_RESULT_SET_SELECTION),ENUM(REVISION_CHANGE_SET),ID(repository),ObjectFormat,OID(base),OID(target),GitPath(subtree),DIGEST(payloadContent),DIGEST(coverage))` |

`queryBytes` 的 Digest 使用 SHA-256 over `BYTES(exact non-empty query bytes)`。Payload Content Digest、Coverage Digest、OID、path 和 member list 必须逐值重算并与 Artifact shell / Source Context 相等。

### 3.3 Selection Member、Ordering 与完整 Envelope

`SelectionMemberSet` 是唯一closed union：

- `TUPLE(ENUM(TREE_LISTING_MEMBERS),ORDERED_LIST(TreeEntry))`；成员逐字复用 predecessor §6.1 `TreeEntry`，允许完整空tree，按 `GitPath(path)` raw bytes严格升序且成员唯一。
- `TUPLE(ENUM(SEARCH_MATCH_MEMBERS),ORDERED_LIST(SearchMatch)[1..n])`；成员逐字复用 predecessor §6.1 `SearchMatch`，按`path raw bytes, start`严格升序且完整成员Tuple唯一。
- `TUPLE(ENUM(QUERY_ZERO_MEMBERS),ORDERED_LIST())`；列表必须严格为零成员，不能用ABSENT、摘要或任意typed占位值替代。
- `TUPLE(ENUM(REVISION_CHANGE_MEMBERS),ORDERED_LIST(ChangeEntry))`；成员逐字复用 predecessor §6.1 `ChangeEntry`，按present时after path、否则before path的raw bytes升序，并在该顺序上从0连续分配ordinal；允许完整零变更集合。

`SelectionOrdering` 只能是 `ENUM(TREE_ENTRY_PATH_RAW_BYTES_ASC|SEARCH_MATCH_PATH_RAW_BYTES_THEN_START_ASC|QUERY_ZERO_EMPTY_ORDER|CHANGE_ENTRY_EFFECTIVE_PATH_RAW_BYTES_ASC)`，且必须分别与上述四个Member variant唯一匹配。`cardinality`必须等于对应列表的实际成员数。

`CompleteResultSetSelectionCore` 的唯一codec为：

`TUPLE(ENUM(COMPLETE_RESULT_SET_SELECTION_CORE),ENUM(TREE_LISTING_SET|SEARCH_MATCH_SET|QUERY_ZERO_SET|REVISION_CHANGE_SET),CanonicalSelectorTuple,ExactSelectionArtifactRef,SelectionMemberSet,UINT64(cardinality),SelectionOrdering,Coverage,DIGEST(payloadContent),DIGEST(coverage))`

其中 `Coverage` 是 predecessor §6.1 的完整canonical Coverage Tuple，不是Coverage Digest或引用；末两个Digest分别按已冻结 Artifact 的完整canonical Payload bytes与本Core内完整Coverage bytes重算，并且必须与Selector和Artifact shell中的同名Digest逐字相等。Selection Kind、Selector variant、Artifact Kind/Payload Schema、Member variant和Ordering必须一一对应；任何交叉组合均为codec failure。

`SelectionDigest=DIGEST(CompleteResultSetSelectionCore)`；最终 `CompleteResultSetSelection=TUPLE(ENUM(COMPLETE_RESULT_SET_SELECTION_ENVELOPE),CompleteResultSetSelectionCore,SelectionDigest)`。Core明确不含`SelectionDigest`或最终Envelope，SelectionDigest只对Core的canonical bytes执行SHA-256。

### 3.4 COMPLETE 门禁

选择成功必须同时满足：

- `Coverage.completeness=COMPLETE`。
- `reachedTerminal=true`、`nextCursor=ABSENT`、`truncationReason=ABSENT`。
- `returnedItems` 等于实际 member count和Core中的cardinality；QUERY_ZERO_SET的Selector零值、`QUERY_ZERO_MEMBERS`空列表、cardinality和returnedItems必须全部恰为 0。
- canonical request boundary、effective selector、Repository、Revision / Comparison 与 Source Context 完全一致。
- ordered members、closed Ordering enum、ordinal/path sort、Payload Content Digest、Coverage Digest、Artifact Shell Digest和Selection Digest重放一致。
- Artifact 是单次、单页且自身完整的 Observation；不得把最后一页、若干页或多个 Artifact 拼成一个 selection。

成功只输出上述closed `CompleteResultSetSelection` envelope。Canonical Selector Tuple只是Core内的选择边界字段，不等于完整Selection，也不能单独充当Locator或Selection Digest preimage。零成员只证明该 exact query boundary；不能外推到其他 path、revision、query、file kind 或 Provider。

任何 PARTIAL、cursor gap、budget exhaustion、skipped applicable object kind、member mismatch、digest mismatch 或 selector 扩张均失败关闭，不产生可供封闭 Fact 使用的 Selection。

## 4. Source Interpretation Observation Extension

### 4.1 共通 Observation Envelope

下列 Contract 只消费一个 `LOCAL_GIT_BLOB_OBSERVATION / 1` Source Artifact 的完整或连续有界 content range；输入闭包仅使用 predecessor 的 Artifact、Payload、Source Context、typed codec 和 range Digest。Provider Profile 不引用任何 Knowledge Schema Evidence / Entity / Fact / Inference Type。跨文件或不连续范围必须分别形成 Observation；组合由下游 Knowledge Schema Contract 完成。Observation的规范来源固定为`冻结Artifact bytes + exact Interpretation Profile/Tag Registry + 本文closed codec与公开确定性解析/校验步骤`；相同输入必须重建逐字相同的typed output、Coverage和Digest。模型响应、隐藏会话、模型摘要或不可回放启发式结果不属于该来源闭包。

每个 canonical Observation Envelope 使用 predecessor codec。`ExactInterpretationProfileRef` 固定为：

`TUPLE(ID(packId),ID(packVersion),DIGEST(packDigest),ID(profileId),ID(profileVersion),DIGEST(profileDefinitionDigest))`

其中前三项必须等于本 Profile 的 exact Rule Pack Dependency，后三项必须逐值命中该 Pack Payload §1.1 的封闭 Profile Catalog；`profileDefinitionDigest` 必须按 Catalog 的 Definition Record 重算一致。Profile Reference 按 `profileId` UTF-8 字节升序排列，不允许空列表、动态版本、名称别名或本机默认 Profile。

`EmittedObservationMemberListCore=TUPLE(ENUM(EMITTED_OBSERVATION_MEMBER_LIST_CORE),ENUM(contractId),ORDERED_LIST(ObservationMember))`；对十个非`CLOSED_SOURCE_REGION_OBSERVATION@1` Contract，`ObservationMember`为该Contract的完整typedPayload，列表恰含一个成员；对`CLOSED_SOURCE_REGION_OBSERVATION@1`，`ObservationMember=RegionMember`，列表逐字等于typedPayload内的`ORDERED_LIST(RegionMember)`。`EmittedObservationMemberListDigest=DIGEST(EmittedObservationMemberListCore)`；`EmittedObservationMemberList=TUPLE(ENUM(EMITTED_OBSERVATION_MEMBER_LIST),EmittedObservationMemberListCore,EmittedObservationMemberListDigest)`。Core、Digest与Envelope必须作为一个不可拆分对象保存，不能只保留摘要或从外层对象临时猜测preimage。

`ObservationOutputCore=TUPLE(ENUM(SOURCE_INTERPRETATION_OUTPUT_CORE),ENUM(contractId),typedPayload,RegionCoverage)`；typedPayload由§4.2与§5的closed codec固定，RegionCoverage必须是§4.3的完整Envelope。SourceInterpretationObservationCore与ObservationOutputCore中的contractId、从typedPayload规范派生的完整`EmittedObservationMemberList`及RegionCoverage内联的同名Envelope必须逐字一致。`ObservationOutputDigest=DIGEST(ObservationOutputCore)`；`ObservationOutput=TUPLE(ENUM(SOURCE_INTERPRETATION_OUTPUT),ObservationOutputCore,ObservationOutputDigest)`。

`SourceInterpretationObservationCore=TUPLE(ENUM(SOURCE_INTERPRETATION_OBSERVATION_CORE),ENUM(contractId),ORDERED_LIST(ExactInterpretationProfileRef),DIGEST(rulePack),ID(repository),ObjectFormat,OID(commit),GitPath(path),OID(blob),ByteRange,DIGEST(observedContent),ObservationOutput)`；`SourceInterpretationObservationDigest=DIGEST(SourceInterpretationObservationCore)`；最终Envelope为`TUPLE(ENUM(SOURCE_INTERPRETATION_OBSERVATION),SourceInterpretationObservationCore,SourceInterpretationObservationDigest)`。

`rulePack` 必须等于本 Profile 的 exact Rule Pack Dependency；`contractId` 只能取 §4.2 的十一项。两个Core都明确排除自身Digest和外层Envelope。Source Interpretation Observation 只保存语法/声明直接呈现的内容；语言、标准库、框架、mapper/query调用效果或查询运行含义需要下游 Inference 使用 exact Rule。

Contract 与 Profile Reference 的允许组合只有：

| Contract ID | 必需 Exact Interpretation Profile |
|---|---|
| `BUILD_DECLARATION_OBSERVATION@1` | `swm.profile.build.maven-pom-model@1 / 1.0.0 / sha256:ce0280467e2e7ba5f162fa26df2e1a9447faa2ce32e971bc962d5cdb781d607c` |
| `PROGRAM_CONTROL_FLOW_OBSERVATION@1`、`PROGRAM_CALL_OBSERVATION@1`、`PROGRAM_DATA_FLOW_OBSERVATION@1`、`PROGRAM_STATE_EFFECT_OBSERVATION@1`、`PROGRAM_EXCEPTION_FLOW_OBSERVATION@1`、`ANNOTATION_APPLICATION_OBSERVATION@1` | `swm.profile.java.source-17@1 / 1.0.0 / sha256:8181313b6057e5c8737411cb057067eab9c930c690421c245dadfe1ac6e3a7ec` |
| `DATA_SCHEMA_DECLARATION_OBSERVATION@1` | `swm.profile.sql.repository-core@1 / 1.0.0 / sha256:885e1674f50e5f1d6d74de6712680fc479ca0a3c5d8d248e92a7a11e48b2093f` |
| `QUERY_DECLARATION_OBSERVATION@1` | `swm.profile.mybatis.mapper-xml-3@1 / 1.0.0 / sha256:9c2f5ef0222a8d3d275194999426d8693b85695cf57256eb2207b4cc14fe86fa` 与 `swm.profile.sql.repository-core@1 / 1.0.0 / sha256:885e1674f50e5f1d6d74de6712680fc479ca0a3c5d8d248e92a7a11e48b2093f` |
| `MAPPER_QUERY_BINDING_OBSERVATION@1` | `swm.profile.mybatis.mapper-xml-3@1 / 1.0.0 / sha256:9c2f5ef0222a8d3d275194999426d8693b85695cf57256eb2207b4cc14fe86fa` |
| `CLOSED_SOURCE_REGION_OBSERVATION@1` | 与region kind对应的上述一项或多项；每项必须是完整 exact Reference，无法唯一选择时不输出该 Contract |

### 4.2 注册表

| Contract ID | 允许输入 | Canonical typed output | 失败关闭边界 |
|---|---|---|---|
| `BUILD_DECLARATION_OBSERVATION@1` | 完整 build dependency/property/profile/activation/configuration node 或完整 descriptor region | `ownerNativeKey, role, targetNativeKey, ordinal, versionExpressionOrLiteral?, scope?, condition?, sourceNode` | role/owner/target 多义、插值或 profile/activation/configuration分支被当作已解析值；source value被当作effective value/dependency |
| `PROGRAM_CONTROL_FLOW_OBSERVATION@1` | 完整 executable body 或一个完整 control node | `ownerNativeKey, fromNode, edgeKind, guardExpression?, toNodeOrOutcome, lexicalOrder` | body/range 不完整却宣称 path closure；unsupported syntax |
| `PROGRAM_CALL_OBSERVATION@1` | 完整 invocation/new expression及该source region内可机械闭合的import/type/overload输入 | `ownerNativeKey, callNode, CallBinding, guard?, lexicalOrder` | overload/dynamic target 被猜成exact；descriptor/参数不完整时却输出EXACT_SOURCE_RESOLVED |
| `PROGRAM_DATA_FLOW_OBSERVATION@1` | 完整 assignment/argument/return/lambda/collection node | `ownerNativeKey, flowKind, sourceExpression, targetLocationOrNode, guard?, programPoint` | alias/interprocedural flow 未直接呈现却被补写 |
| `PROGRAM_STATE_EFFECT_OBSERVATION@1` | 完整源码对象创建、赋值或字段/数组写节点 | `TUPLE(ownerNativeKey, ENUM(SOURCE_CREATE|SOURCE_WRITE), targetLocation, ORDERED_LIST(valueExpression), guardOrAbsent, programPoint)` | invocation、mapper/query调用、callee effect、框架/API effect或只凭方法名猜副作用 |
| `PROGRAM_EXCEPTION_FLOW_OBSERVATION@1` | 完整 throw/catch/throws/handler declaration node | `ownerNativeKey, sourceNode, eventKind, exceptionType, targetNodeOrOutcome?, guard?` | 隐式异常、传播或 handler precedence 被当作直接观察 |
| `ANNOTATION_APPLICATION_OBSERVATION@1` | 完整 declaration 与其完整 annotation node | `targetNativeKey, annotationTypeToken, orderedArguments, applicationScope, sourceNode` | annotation type/constant/default 或 composition 多义 |
| `DATA_SCHEMA_DECLARATION_OBSERVATION@1` | 完整 repository DDL/schema declaration node | `relationNativeKey, declarationRole, fieldOrConstraintNativeKey, constraintDefinition?, sourceNode` | runtime DB、migration order 或未读 schema source 被补写 |
| `QUERY_DECLARATION_OBSERVATION@1` | 完整 repository query statement node | `queryOperationNativeKey, operationKind, typedQuerySyntaxTree, parameterSlots, resultShape?, sourceNode` | dynamic branch、dialect、statement boundary 或 placeholder 多义 |
| `MAPPER_QUERY_BINDING_OBSERVATION@1` | 完整 mapper operation/mapping declaration node | `mapperNativeKey, queryOperationNativeKey, parameterBindings, resultBinding?, sourceNode` | namespace、overload、result map 或 generated provider 多义 |
| `CLOSED_SOURCE_REGION_OBSERVATION@1` | 一个完整 descriptor、declaration、executable body、query statement 或 schema declaration region | `TUPLE(RegionBoundary, RegionSelector, ORDERED_LIST(RegionMember), UINT64(cardinality), ENUM(LEXICAL_ASC|SOURCE_DECLARED_ORDER|CANONICAL_DIGEST_ASC), ORDERED_LIST(SourceNode))` | range 非完整、parser未到 terminal、unsupportedNode 与 selector相交 |

表中逗号分隔字段是按所列顺序编码的 `TUPLE` 简写，不允许增删字段。字段枚举固定为：build role=`AGGREGATES_MODULE|IDENTIFIES_COMPONENT|MANAGES_DEPENDENCY|DECLARES_DEPENDENCY|DECLARES_PARENT|DECLARES_PROPERTY|DECLARES_PROFILE|DECLARES_ACTIVATION|DECLARES_CONFIGURATION`；control edge=`ENTRY|SEQUENCE|TRUE_BRANCH|FALSE_BRANCH|LOOP_BACK|BREAK|CONTINUE|SWITCH_CASE|TRY|CATCH|FINALLY|RETURN|THROW|EXIT`；data flow=`ASSIGN|ARGUMENT|RETURN|ALIAS|TRANSFORM|COLLECTION_ELEMENT`；exception event=`EXPLICIT_THROW|CATCH|DECLARES_THROW|HANDLER_DECLARES`；annotation scope=`TYPE|METHOD|CONSTRUCTOR|FIELD|PARAMETER|LOCAL`；schema declaration role=`DECLARES_FIELD|DECLARES_CONSTRAINT`；query operation=`SELECT|INSERT|UPDATE|DELETE|CREATE_TABLE`。Program state effect只允许 `SOURCE_CREATE|SOURCE_WRITE`，不得出现query/API effect枚举。

BUILD role与target NativeKey Kind是封闭一对一映射：`AGGREGATES_MODULE→MODULE`；`IDENTIFIES_COMPONENT|MANAGES_DEPENDENCY|DECLARES_DEPENDENCY|DECLARES_PARENT→COMPONENT`；`DECLARES_PROPERTY→PROPERTY`；`DECLARES_PROFILE→PROFILE`；`DECLARES_ACTIVATION→ACTIVATION`；`DECLARES_CONFIGURATION→CONFIGURATION`。ownerNativeKey必须为MODULE。`DECLARES_PARENT` version保持literal/expression；PROPERTY/PROFILE/ACTIVATION/CONFIGURATION的value/condition只允许Typed Literal、Expression或exact Profile Tag Ref，不进行插值、激活或effective resolution。任何role-target kind错配均为codec failure，不能降级成通用MODULE/COMPONENT或按名称相似修正。

所有 owner/target/type/token/parameter/result/argument/binding 字段只能使用 §5 的 Native Key、Type Ref、Location、Expression、Call Binding、Query Expression、Constraint、Source Node或这些类型的固定tuple/list；例如parameter binding固定 `TUPLE(NativeKey(parameter),Expression)`，annotation argument固定 `TUPLE(NativeKey(name)|UINT64(ordinal),Expression)`，result shape固定 `TypeRef|ORDERED_LIST(TypeRef)|ABSENT`。任何 map、任意attributes、自由文本summary、Answer Claim或未注册嵌套对象均为 codec failure。

### 4.3 Region Coverage

`RegionCoverageCore` 的唯一 codec 为：

`TUPLE(ENUM(REGION_COVERAGE_CORE),RegionBoundary,RegionSelector,UINT64(visitedNodeCount),UINT64(emittedMemberCount),ORDERED_LIST(SourceNode unsupportedNodeSet),BOOL(reachedTerminal),ENUM(COMPLETE|PARTIAL),EmittedObservationMemberList)`

RegionCoverage Verifier必须仅凭内联的`EmittedObservationMemberListCore`重算其Digest，并验证其contractId、成员closed codec及`emittedMemberCount`；外层Observation Verifier再从typedPayload独立派生同一列表并逐字比较。只允许`CLOSED_SOURCE_REGION_OBSERVATION@1`产生零成员，零成员使用真实空`ORDERED_LIST()` bytes，不能使用ABSENT或固定常量；其他十个Contract不能用零成员Envelope表示unsupported。`RegionCoverageDigest=DIGEST(RegionCoverageCore)`；最终`RegionCoverage=TUPLE(ENUM(REGION_COVERAGE),RegionCoverageCore,RegionCoverageDigest)`。RegionCoverageCore不含RegionCoverageDigest或最终Envelope。

`RegionBoundary` 是 `TUPLE(ENUM(DESCRIPTOR|DECLARATION|EXECUTABLE_BODY|QUERY_STATEMENT|SCHEMA_DECLARATION),SourceNode)`；`RegionSelector` 是 closed union：`TUPLE(ENUM(BUILD_DECLARATION|CONTROL_EDGE|PROGRAM_CALL|DATA_FLOW|SOURCE_STATE_WRITE|EXCEPTION_DECLARATION|ANNOTATION_APPLICATION|SCHEMA_DECLARATION|QUERY_DECLARATION|MAPPER_BINDING|ALL_SUPPORTED_REGION_MEMBERS),ExactInterpretationProfileRef)`。`RegionMember` 只能是 §5 的 Source Node、Native Key、Type Ref、Location、Expression、Call Binding、Query Expression、Constraint或 Typed Literal。没有任意 predicate、map、自然语言或插件字段。

`CLOSED_SOURCE_REGION_OBSERVATION@1` 只有同时满足以下条件才能声明 COMPLETE：

1. Blob Artifact 覆盖目标 region 的全部 bytes；region boundary 由受支持 Syntax Profile 唯一重建。
2. Parser / Hybrid Verifier 对 region 中与 selector 匹配或可能匹配的全部 node 到达 terminal；此处Hybrid只表示多个确定性parser/verifier步骤的组合，每一步输入、输出与失败边界均可从冻结Artifact和exact Profile公开重放，不表示模型审核或模型与parser混合裁决。
3. `unsupportedNodeSet` 与 selector domain 不相交；无法证明不相交时只能 PARTIAL。
4. member set、source node locator、content digest、visited/emitted count 和 ordering可重放。
5. selector 只作用于该 region、exact commit 和 Syntax Profile，不能表达 repository-global absence。

一个完整 method body 可以支持“该方法内没有某类引用”；它不能支持类、模块、仓库或运行时不存在。多个 region 的闭合必须由 Knowledge Schema 以正式 member set 和 Coverage 组合，Provider 不聚合。

## 5. Canonical Component Shapes

Source Interpretation output 的嵌套 component 采用下列 closed tagged tuple；消费 Schema 可以注册等价 Value Object，但不能改变 Provider bytes：

`NativeKey = TUPLE(ENUM(SOURCE_NATIVE_KEY),ENUM(MODULE|COMPONENT|PROPERTY|PROFILE|ACTIVATION|CONFIGURATION|SOURCE_UNIT|SYMBOL|QUERY_OPERATION|RELATION|FIELD|CONSTRAINT|TYPE_TOKEN|CALL_TOKEN),BYTES(exactSourceToken),DIGEST(exactSourceToken),SourceNode|ABSENT)`。`exactSourceToken` 必须逐字来自 observed content，不能承载模型摘要或解释。PROFILE、ACTIVATION和CONFIGURATION必须由对应完整source node及其exact token/path锚定；无唯一source token/path时不生成NativeKey。

`ExactProfileTagRef`逐字复用Rule Pack Payload §1.2：

`TUPLE(ENUM(PROFILE_TAG_REF),ExactInterpretationProfileRef,ID(registryId),ID(registryVersion),DIGEST(registryDefinitionDigest),ENUM(tagKind),ID(memberId),UINT64(memberOrdinal),DIGEST(memberDefinitionDigest))`

Registry必须是该exact Profile在Pack Catalog中唯一绑定的`NO_EXTENSION` Registry。实现必须从Pack Payload重算Registry Record、Profile绑定、ordinal、`TAG|registryId|registryVersion|tagKind|memberId` Member Record与Digest。未知Registry、同Profile其他Registry、自造tagKind/member、错误ordinal或Digest一律codec failure；本Profile不接受本机parser Registry、插件Registry或动态“最新”Registry。

| Component | Canonical Shape |
|---|---|
| Source Node | `TUPLE(ENUM(SOURCE_NODE),NativeKey(owner),ExactProfileTagRef(nodeKind),ORDERED_LIST(UINT64(lexicalPath)),ByteRange,DIGEST(nodeContent))` |
| Type Ref | `TUPLE(ENUM(TYPE_REF),ExactInterpretationProfileRef,NativeKey|ExactProfileTagRef(typeIdentity),ORDERED_LIST(TypeRef),ENUM(NONNULL|NULLABLE|UNKNOWN),NumericPolicy|ABSENT)` |
| Location | `TUPLE(ENUM(LOCATION),ENUM(PARAMETER|LOCAL|FIELD|STATIC_FIELD|ARRAY_ELEMENT|COLLECTION_ELEMENT|MAP_ENTRY|RETURN_SLOT|TEMPORARY),NativeKey(base),ORDERED_LIST(AccessSegment),TypeRef)`；`AccessSegment=TUPLE(ENUM(FIELD),NativeKey)|TUPLE(ENUM(INDEX),Expression)|TUPLE(ENUM(KEY),Expression)` |
| Expression | `TUPLE(ENUM(EXPRESSION),ExactInterpretationProfileRef,ENUM(LITERAL|LOCATION|UNARY|BINARY|CONDITIONAL|CAST|CALL_RESULT|CONSTRUCT|MEMBER_ACCESS|INDEX|SLICE|CONCAT|COLLECTION_OP|AGGREGATE),ExactProfileTagRef(operator)|ABSENT,ORDERED_LIST(Expression|Location|TypedLiteral|CallBinding),TypeRef,NumericPolicy|ABSENT)` |
| Call Binding | `TUPLE(ENUM(CALL_BINDING),ENUM(EXACT_SOURCE_RESOLVED|SOURCE_DECLARED_UNRESOLVED),ENUM(FULLY_QUALIFIED|EXPLICIT_IMPORT|SAME_PACKAGE|RECEIVER_TYPE|UNRESOLVED),ENUM(STATIC|VIRTUAL|INTERFACE|SPECIAL|CONSTRUCTOR|SOURCE_UNRESOLVED),Expression|ABSENT,NativeKey(declaringTypeOrSourceToken),NativeKey(methodName),BYTES(exactJvmDescriptor)|ABSENT,ORDERED_LIST(Expression),Location|ABSENT,TypeRef|ABSENT)`；第三项为sourceTypeBindingKind，与declaring token直接保留source import/type绑定；只有import/type/overload输入在观察range与exact Profile内机械唯一时才能输出EXACT_SOURCE_RESOLVED和descriptor，否则保留SOURCE_DECLARED_UNRESOLVED |
| Query Expression | closed union：`TUPLE(ENUM(SCAN),NativeKey(relation))`、`TUPLE(ENUM(FILTER),QueryExpression,Expression)`、`TUPLE(ENUM(JOIN),ExactProfileTagRef(joinKind),QueryExpression,QueryExpression,Expression)`、`TUPLE(ENUM(PROJECT),QueryExpression,ORDERED_LIST(Expression))`、`TUPLE(ENUM(GROUP),QueryExpression,ORDERED_LIST(Expression))`、`TUPLE(ENUM(AGGREGATE),QueryExpression,ORDERED_LIST(Expression))`、`TUPLE(ENUM(SORT),QueryExpression,ORDERED_LIST(TUPLE(Expression,ENUM(ASC|DESC))))`、`TUPLE(ENUM(LIMIT),QueryExpression,Expression,Expression|ABSENT)`、`TUPLE(ENUM(SET_OP),ExactProfileTagRef(setOperator),QueryExpression,QueryExpression)` |
| Constraint | `TUPLE(ENUM(CONSTRAINT),ExactProfileTagRef(constraintType),ORDERED_LIST(NativeKey(field)),Expression|ABSENT,ENUM(COLUMN|RELATION|DECLARATION))` |

`NumericPolicy = TUPLE(ENUM(NUMERIC_POLICY),TypeRef,INT64(scale)|ABSENT,ExactProfileTagRef(roundingMode)|ABSENT,ExactProfileTagRef(overflowPolicy)|ABSENT)`。任何其他 variant、字段、未注册 tag、任意 attributes map 或自由文本均为 codec failure。

`TypedLiteral`、`ByteRange`、`ORDERED_LIST`、Digest、OID 和 path 复用 predecessor codec。未知、缺省和空集合必须使用明确判别值；字段省略和实现对象序列化非法。Parser / Hybrid Verifier 的具体实现算法不属于本 Contract，但有效输出的每个字段都必须由本文公开规则和冻结Artifact确定；Hybrid只能组合确定性parser/verifier，不能把隐藏模型输出、模型置信度或不可重放启发式作为Observation输入或裁决依据。若实现内部使用模型产生非权威hint，确定性Verifier必须在不消费该hint的条件下从冻结输入独立重建逐字相同的完整Observation，否则不得按本Profile输出。Conformance 必须证明output codec、source span、count、member set、Coverage Core/Envelope、Observation Output Core/Envelope与全部Digest均可机械重算。

### 5.1 Core → Digest → Envelope 统一不变量

本文新增的自校验对象只允许`XCore → XDigest → X envelope`：`XCore`保存完整closed preimage且不得包含`XDigest`、`X envelope`或任何由二者导出的后置对象；`XDigest=SHA-256(canonical XCore bytes)`；`X envelope=TUPLE(ENUM(exactEnvelopeTag),XCore,XDigest)`。本规则适用于`ExactSelectionArtifactRef`、`CompleteResultSetSelection`、`RegionCoverage`、`ObservationOutput`和`SourceInterpretationObservation`。Verifier必须先解码完整Core，再独立重算Digest，最后验证Envelope tag与字段一致；把Envelope、自身Digest、opaque摘要或调用方对象序列化作为Core preimage一律codec failure。Payload Content、query、source token、node content和member set等内容Digest仍按各自明示bytes计算，它们不是对象self-digest，也不得被误写成Envelope Digest。

## 6. Rule Pack Applicability Boundary

1. Source Interpretation Observation 只记录来源节点和显式语法；不执行需要已发布正式前提的跨节点、跨文件、框架保证或行为结论。
2. 使用 Rule Pack 解释 Observation 时必须单独形成 Rule Application，保存 exact Rule Reference、完整 Exact Interpretation Profile Reference、输入和 `APPLICABLE | NOT_APPLICABLE | UNKNOWN`。
3. Rule Pack 的 UNKNOWN 不得被 Provider 改成具体输出；Provider 也不能因模型认为“常见”而选择版本、API、框架配置或 query dialect。
4. 外部组件行为只允许下游使用 Rule Pack `EXTERNAL-API-SEMANTIC-INTERPRETATION@1` 形成 Inference；Provider永远只保留source-declared call。普通component basis必须来自下游`BUILD-EFFECTIVE-DEPENDENCY-RESOLUTION@1`支持的published effective dependency；Framework fallback必须由source owner module的完整effective descriptor chain(child→root→exact supported parent)及链上全部build/config closure支撑。缺任一项、无法审核exact signature或审核不一致时保持Unknown。
5. 本 Profile 不定义任何项目、具体第三方组件、认证令牌、业务对象或题目专用 Syntax Profile / Rule。
6. Provider可分别观察descriptor chain中每个文件的parent、direct/managed dependency、property、profile和activation声明，并为每个完整region形成独立Observation/Coverage；它不跨文件解析effective model、候选冲突或mediation，也不以`BUILD-EFFECTIVE-VALUE@1`替代下游effective dependency resolution。
7. 需要模型解释的软件语义不能伪装成Source Interpretation Observation；它只能由下游使用exact Rule Pack/Knowledge Schema Contract，经MODEL_REVIEWED的完整Model Result Eligibility、独立Review、Knowledge Verification与Admission门禁形成Inference。本Profile不复制或弱化Model Gateway字段。

## 7. 失败、Conformance 与兼容边界

| 失败 | 处理 |
|---|---|
| `RESULT_SET_NOT_COMPLETE` | 不签发 Complete Result Set Selection；保留原 Artifact / Coverage |
| `RESULT_SET_ARTIFACT_SHELL_MISMATCH` | 拒绝Selection；Artifact shell Core/Ref、Source Context、Observation Basis、Kind/Schema、Tool/Profile/Identity Strategy、Data Classification或Payload/Coverage Digest任一不可解析或失配均失败关闭 |
| `RESULT_SET_MEMBER_MISMATCH` | 拒绝Selection；Selection Kind/Selector/Member variant/Ordering/cardinality或member bytes任一不一致均失败关闭 |
| `SELF_DIGEST_CYCLE` | 拒绝对象；任一Core包含自身Digest/Envelope、Digest不等于canonical Core bytes，或以opaque摘要替代完整Core时失败关闭 |
| `SOURCE_REGION_NOT_CLOSED` | Observation 为 PARTIAL；不能支持封闭集合或否定 Fact |
| `SOURCE_INTERPRETATION_UNSUPPORTED` | 不输出该 Contract；保留原 Evidence |
| `SOURCE_NATIVE_IDENTITY_AMBIGUOUS` | 不生成 target native key；下游 Entity KEEP_UNRESOLVED |
| `RULE_PACK_REFERENCE_MISMATCH` | 失败关闭；不能选择其他版本 |
| `INTERPRETATION_PROFILE_REFERENCE_MISMATCH` | 失败关闭；Pack/Profile/version/Definition Digest任一不一致都不能输出Observation |
| `INTERPRETATION_OUTPUT_MISMATCH` | 隔离输出；不能用模型文本覆盖 typed bytes |
| `SOURCE_INTERPRETATION_NOT_REPLAYABLE` | 不输出该Contract；任一typed field、Coverage或Digest不能由冻结Artifact与公开确定性步骤完全重建，或依赖隐藏模型输出/不可回放启发式时失败关闭 |

新增 Conformance 至少覆盖：

- 四种 complete result-set selection 各自重算完整Artifact Shell Core/Ref、Selector、tagged Member Set、closed Ordering、cardinality、完整Coverage、Payload/Coverage Digest、Selection Core/Digest/Envelope；另覆盖PARTIAL、cursor、truncation、selector扩张、Kind/Schema/Context/Basis/Tool/Profile/Identity/Data Classification错配、member variant/order/count/digest错配和QUERY_ZERO非空/ABSENT/非零反例。
- 十一种 Source Interpretation Observation各一个合法样例、一个不完整/多义样例，并从typedPayload独立派生、重算并逐字比对EmittedObservationMemberList Core/Digest/Envelope，再逐层重算RegionCoverage Core/Digest/Envelope、ObservationOutput Core/Digest/Envelope和SourceInterpretationObservation Core/Digest/Envelope；只存member digest、列表preimage缺失、内外contractId/list/count错配及State Effect 的 invocation→effect反例必须失败。
- BUILD Observation覆盖九种role及其唯一target NativeKey Kind；九种role-target错配、PROFILE/ACTIVATION/CONFIGURATION无唯一source token/path、跨descriptor effective model、candidate/mediation或用scalar value冒充effective dependency必须失败。
- complete method/descriptor/query region 的零项与非零项；unsupported node 与 selector 相交时不得 COMPLETE。
- Observation 与 Rule Pack 的职责隔离；框架默认、隐式异常、动态调用和 runtime DB 不得出现在直接观察输出。
- 对每种Parser/Hybrid Verifier路径，在移除模型响应、隐藏会话、缓存hint和不可回放状态后从同一冻结Artifact重建逐字相同Observation；Hybrid的每一参与者都必须是确定性公开步骤。隐藏模型输出改变typed field、Coverage或Digest、把模型语义包装为Observation、或必须依赖模型才能重建的反例均失败关闭，并转由下游Rule Pack/Schema路径处理。
- 对 RegionBoundary/Selector/RegionCoverage Core与Envelope、Node/Expression/Access/Query/Constraint 的全部 union 执行非法variant、未知field、任意map/text和Registry Digest反例；逐个Profile验证唯一Tag Registry、member ordinal/digest inclusion，未知/自造/插件Registry必须失败。
- 对本文全部Core/Digest/Envelope逐项执行self-digest、Envelope-in-Core、Digest-in-Core、后置对象-in-Core、只存opaque digest、Core篡改后复用旧Digest和错误Envelope tag反例；任何一个都必须触发`SELF_DIGEST_CYCLE`或codec failure。
- Fixture数据可以固定验证输入；扫描Driver、Contract ID、selector、parser/verifier和实现分支，确认它们不会按scenario ID、claim、问题、repository/class/path专名、commit、第三方组件或黄金值改变语义，也不存在题目或业务专用逻辑。

仅在CAPABILITY_VALIDATION架构Demo使用deterministic Contract Driver：Driver必须在同一Run通过公共Source Tool / Observation Port提交冻结请求，经公共Artifact/Evidence/Fact Verification/Admission/Publication后关闭来源调查上下文，并从新Snapshot正式重读，再进入公共Rule/Candidate、独立Review Proposal、Rule Verification及Knowledge Verification/Admission/Publication；Generation/Review Fixture只能经各自公共Proposal Port且彼此分离，Review Fixture可以提交非权威`REVIEW_ASSERTS_PASS`。任何Fixture都不得直接构造权威Artifact/Evidence/Fact、写Provider或Knowledge Repository、签发`RULE_VERIFICATION_PASS`、Knowledge Obligation PASS或Admission Decision、以模型/Fixture输出充当Source Observation、调用私有parser seam后冒充端到端通过，或向Candidate/Answer注入source payload。PRODUCTION/CAPABILITY_EVALUATION不允许DRIVER/REVIEW_FIXTURE。私有seam测试只记为局部Conformance见证；只有完整公开端口Demo运行才验证该边界内的方案能力，且不证明产品实现或模型可靠性。

## 8. Compatibility 与明确排除

本文相对 `0.1.0` 是新增 Contract 的扩展，不修改既有 Artifact、Codec、Locator、Target 或 Source Context。因此：

- 旧 Schema 仍按 exact `0.1.0` 解释其历史 Dependency，不自动使用本文能力。
- 新消费者必须显式依赖 `0.2.0` 的 exact digest。
- 本文不声明跨 Schema Compatibility，不迁移任何 Snapshot。
- 不增加多页聚合 Artifact、全文 AST Artifact、Diff hunk、Runtime Observation、DB Connector、工作树读取或直接来源回答。
- 不把 Source Interpretation output 提升为 Artifact、Evidence、Fact、Inference 或 Snapshot Member。

<!-- END LOCAL GIT PROFILE CONTRACT -->

## 9. 验证状态

本文状态为`Withdrawn Draft — Not a Current Validation Dependency`。Payload保留供历史追溯，但其Rule Pack依赖已失效；不得注册或作为任何当前Formal Mapping、Conformance、Demo或实施基线输入。
