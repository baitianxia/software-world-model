# Iteration 001 INITIAL Knowledge Schema Definition

| 元数据 | 值 |
|---|---|
| Artifact ID | SWM-ITER-001-KNOWLEDGE-SCHEMA |
| Status | Frozen for Iteration 001 |
| Consumer | SWM-IMP-ITER-001 |
| Design Baseline | [SWM-DBM-ITER-001-REV-002](../../../detailed-design/governance/Design_Baseline_Manifest_Iteration_001_Revision_002.md) |
| Implementation Baseline | [SWM-IBM-ITER-001-REV-002](../Implementation_Baseline_Manifest_Iteration_001_Revision_002.md) |
| Source Contract Dependency | [ITER-001-LOCAL-GIT-PROVIDER@0.1.0](ITER-001-Local-Git-Provider-Profile.md) |
| Shared Error Projection | [ITER-001-SHARED-ERROR-CLASSIFICATION](ITER-001-Shared-Error-Classification.md) |
| Knowledge Schema ID | `swm.local-git.software-knowledge` |
| Version Label | `iter-001.initial.1` |
| Definition Digest | `sha256:1ba1a4090032464b4970bbc13a2a29685bb5b7f5d00fbf35b5da914e266c64fa` |
| Digest Algorithm | SHA-256 |
| Definition Canonicalization | `SWM-SCHEMA-DEFINITION-MARKDOWN-LF@1` |
| Transition Modes | `INITIAL | UNCHANGED` |
| Schema Dependencies | `ITER-001-LOCAL-GIT-PROVIDER@0.1.0` + exact Profile Contract Digest（见 §3.1） |
| Predecessor | None |

> 本文是首个纵向实现切片的 Knowledge Schema Definition，不修改或替代任何 Accepted 详细设计。它只冻结 Iteration 001 实际实现所需的最小语义类别和门禁；数据库、类、API 编码、Prompt、模型选择与 Projection 均不在本文范围。

## 1. 权威依据与优先级

本文采用以下 Accepted Contract，发生歧义时以下文档优先，本文不得放宽其不变量：

- `DD-KNW-SCHEMA-CORE@0.1.0`
- `DD-KNW-REFERENCE-CONTEXT@0.1.0`
- `DD-KNW-CONTEXT-COMPARISON@0.1.0`
- `DD-KNW-EVIDENCE@0.1.0`
- `DD-KNW-ENTITY@0.1.0`
- `DD-KNW-FACT@0.1.0`
- `DD-KNW-INFERENCE-CONFLICT@0.1.0`
- `DD-KNW-ADMISSION@0.1.0`
- `DD-KNW-SNAPSHOT-PUBLICATION@0.1.0`

本文是 SWM-DBM-ITER-001-REV-002 的实施产物，不属于该已冻结 Manifest，也不能反向改变 Manifest 摘要。

## 2. Definition Digest 计算规则

`Definition Digest` 只覆盖下方 `BEGIN SCHEMA DEFINITION PAYLOAD` 与 `END SCHEMA DEFINITION PAYLOAD` 标记之间的内容，不覆盖标记本身、本文元数据、说明或待验证项。规范输入为：

1. 使用 UTF-8、LF 换行和 Unicode NFC；禁止 BOM、CRLF 与行尾空格。
2. 保留 Payload 中的标题、表格行顺序、标点、空行和代码字面值。
3. 输入从 BEGIN 标记后的第一个字节开始，到 END 标记前一行的 LF 为止。
4. 对规范输入计算 SHA-256，小写十六进制并以 `sha256:` 为前缀。

注册实现可以采用其他内部序列化，但必须通过 Conformance Fixture 证明其规范 Definition 与本 Payload 双向无损，并得到本文固定的同一 Definition Digest；不能用 Version Label 或文档文件摘要代替 Definition Digest。

<!-- BEGIN SCHEMA DEFINITION PAYLOAD -->

## 3. Schema 身份与适用边界

### 3.1 不可变身份

| 项 | 定义 |
|---|---|
| Schema ID | `swm.local-git.software-knowledge` |
| Version Label | `iter-001.initial.1` |
| Predecessor | `NONE` |
| Exact Schema Dependency Reference | `ITER-001-LOCAL-GIT-PROVIDER@0.1.0 / sha256:d1eacb1e2c61c160c239b840cc84d660fef9fe282acd465358ae41f07bf76d1f`；提供 Source Context、Artifact / Payload、Typed Observation 与 Source Interpretation Contract |
| Canonicalization Version | `SWM-KNOWLEDGE-CANONICALIZATION@1` |
| Reader Contract | `SWM-FORMAL-KNOWLEDGE-READER@1` |

完整 Knowledge Schema Reference 为 `Schema ID + Version Label + 本文 Definition Digest`。任何运行对象不得保存 `latest`、省略 Digest 或由版本号推断兼容性。

### 3.2 Schema Applicability Boundary

| 维度 | 允许范围 | 越界处理 |
|---|---|---|
| Scope Kind | 单个 `SYSTEM` KnowledgeScope | 失败关闭；不得自动创建 Business Domain 或 Shared Component Scope |
| Source family | Local Git Provider 产生且满足本文 Evidence Representation 的信息载体 | 返回不支持；不得用通用文本猜测其他来源语义 |
| Knowledge Kind | `ENTITY | FACT | INFERENCE` | 其他 Kind 不进入 Candidate / Snapshot |
| Entity Origin | `SOURCE_ANCHORED` | `INFERRED` Entity 不在本 Schema 中注册 |
| Semantic Category | `TECHNICAL` | 稳定 Business Entity 不在本 Schema 中注册 |
| Observation domain | Git Commit、Tree、File Content、Diff 和 Git 内信息载体 | DB、Log、Trace、部署运行观察不适用 |
| Context | 本文第 4 节定义的 exact Git Revision 与 Observation Time | Ref 解析观察只保留在 Target Resolution Provenance；未知维度保留在来源侧，不能静默丢弃或默认填充 |
| Snapshot | 一个 Scope、一个 exact Schema Reference | 不支持跨 Scope 聚合发布或多 Schema 成员 |

“Structure、Behavior、Business、History”是 Knowledge Use 对正式命题的组织维度，不是新的 Knowledge Kind、Snapshot 成员或存储层。本文只提供能够支持这些用途的最小正式类型；不注册 Semantic View。

## 4. KnowledgeContext Vocabulary

### 4.1 Context Dimension

| Dimension ID | 值类型与规范化 | Predicate | 身份语义 |
|---|---|---|---|
| `swm.version.git-commit@1` | `{objectFormat, fullOid}`；`objectFormat` 为 Provider 声明的 Git object format，`fullOid` 为对应长度的小写完整十六进制 | `EQUALS` | 对 Git 内容观察必需；不得使用短 SHA、Branch 名或 Tag 代替 |
| `swm.time.observation@1` | UTC Instant，RFC 3339，规范到纳秒并去除等价表示差异 | `AT` | Target Resolution、Tree 选择和来源操作的观察时间；不表示代码有效时间 |

### 4.2 Context Term 规则

1. 每个 Term 必须保留明确 Subject、Dimension、Predicate、Value、Origin 和 Basis。
2. Local Git 直接观察只产生 `OBSERVED` Term，Basis 必须为 `SOURCE_CONTEXT_TERM` 或满足本文 Evidence Locator 的 `OBSERVED_CONTENT_LOCATOR`。
3. Git 文件、语法声明、Diff 和 Commit 内容 Evidence 必须具有 exact `swm.version.git-commit@1`。Branch、Tag、`HEAD` 与短 SHA 只允许作为 Target Proposal / Resolution Observation，连同解析链和 Observation Time 保留在 Provenance，不进入正式读取 KnowledgeContext。
4. Branch / Tag 后续移动不修改已签发的 Resolution Receipt 或既有 Context；新解析产生新的 Receipt，并以新解析得到的 exact Commit 创建 Source Context / KnowledgeContext。
5. `Repository Identity` 精确为 `LOCAL_GIT_IDENTITY_V1` 给 `(Local Workspace Domain ID, Canonical Source Target)` 分配的永久 DataSource ID，并能回放该规范 Tuple；Workspace Domain ID 单独不能充当 Repository Identity。同一 full commit 在不同 Repository Identity 中不自动等价；该身份保留在 Subject / Source Context / Entity Identity Domain 中。
6. Context 表达只允许 `AND | OR`；不得把 unknown relation 强制组成 AND。
7. Secret、Credential、访问令牌和本地绝对工作区路径不是 Context Term。

### 4.3 Local Git Source Context 映射

本文只接受 exact dependency 中 `LOCAL_GIT_SOURCE_CONTEXT_VOCABULARY@1 / LOCAL_GIT_SOURCE_CONTEXT_CANONICALIZATION@1` 的 Source Context：

| Provider Source Context 值 | KnowledgeContext 投影 |
|---|---|
| Repository Identity | Subject / Entity Identity Domain；不投影为可比较 Dimension |
| Read Revision commit OID | `swm.version.git-commit@1`；Basis 保留 Source Context Reference |
| Comparison base / target OID | 分别按 `BEFORE | AFTER` Role 形成两个 `swm.version.git-commit@1` Term，不合成“同时成立”的 Revision |
| Observation Time | `swm.time.observation@1` |
| tree / blob / path / range | 保留在 Evidence Locator 与 Source Context，不提升为本文 Context Dimension |
| ref proposal / resolution chain | 仅 Target Resolution Provenance；不进入 KnowledgeContext |

Provider Vocabulary、Canonicalization、Repository Identity 或 exact OID 无法按依赖 Contract 重放时不创建 KnowledgeContext；不得读取“最新”Provider 词汇猜测旧值。

### 4.4 Comparison Purpose

| Purpose ID | 最低成功条件 | 非成功结果 |
|---|---|---|
| `ENTITY_IDENTITY_ANCHOR_COMPOSITION` | identity-bearing projection 机械相等，或 exact current VALID Assessment 为 `COMPATIBLE` | `INCOMPATIBLE` 禁止聚合；`UNKNOWN | NOT_COMPARABLE` 保持未解析 |
| `FACT_SUPPORT_COMPOSITION` | 所有 Evidence Context 能在同一 Git Commit 条件下共同成立 | 非 `COMPATIBLE` 不得组合 Support Set |
| `INFERENCE_PREMISE_COMPOSITION` | Type Contract 声明的 Premise Context Role 完整且可共同解释 | 非 `COMPATIBLE` 不得生成普通联合结论 |
| `CHANGE_COMPARISON` | 输入以 `BEFORE | AFTER` 角色分别固定 exact Commit；不要求两个 Context 同时成立 | 无明确角色或 Revision 不可解析时失败 |
| `CONFLICT_COMPARISON` | 目标对齐后，Context 在 Conflict Rule 下可比较 | `UNKNOWN | NOT_COMPARABLE` 不形成 Conflict |

Comparison 失败不是 `UNKNOWN`；只有正常完成的 Assessment 才有四态语义。任何实例级关联若不能由 Context Term 的机械规则证明，必须先成为已发布正式知识，不能藏入 Comparison Proposal。

## 5. Evidence Representation 与 Locator

### 5.1 允许的 Evidence Representation

| Representation ID | exact Local Git Artifact Kind / Payload Schema | 允许的直接观察 |
|---|---|---|
| `swm.evidence.git-commit-record@1` | `LOCAL_GIT_COMMIT_OBSERVATION / 1` + `swm.payload.local-git.commit-observation@1` | full OID、parent OID、author/committer time、message field |
| `swm.evidence.git-tree-entry@1` | `LOCAL_GIT_TREE_LISTING / 1` + `swm.payload.local-git.tree-listing@1` | exact Commit 下的 repository-relative path、entry kind、object OID |
| `swm.evidence.git-file-content@1` | `LOCAL_GIT_BLOB_OBSERVATION / 1` + `swm.payload.local-git.blob-observation@1` | exact Commit 下单个文件的连续文本/字节区域、完整声明、配置或文档陈述 |
| `swm.evidence.git-diff-entry@1` | `LOCAL_GIT_TREE_CHANGESET / 1` + `swm.payload.local-git.tree-changeset@1` | exact base/target Commit comparison 中的单个完整 change entry、before/after path、mode 与 object OID |

Search ranking、Tool 成功状态、未封闭空结果、模型摘要、跨文件聚合和 Investigation Transcript 均不是 Evidence Representation。

### 5.2 Locator Contract

Locator Canonicalization 固定为 `SWM-GIT-LOCATOR-CANONICALIZATION@1`：按表中字段顺序使用 exact dependency 的 `SWM-LOCAL-GIT-TYPED-TUPLE@1`；每个 Locator 首项为 `ID(exact Locator Contract ID)`，Enum / Field ID 使用 `ENUM`，OID、Git path bytes 和 Byte Range 分别按第 12 节规则映射为 `OID | BYTES | UINT64`，缺省可选值使用 typed `ABSENT`，不得靠字段省略表达。该规范 Tuple 是 Locator 等价与 Digest 的唯一输入，不使用 JSON 字段顺序、显示行号或模型文本。

| Locator Contract ID | exact Artifact Kind / Payload Schema | typed Locator Shape | 唯一有界解析与 Coverage |
|---|---|---|---|
| `swm.locator.commit-field@1` | `LOCAL_GIT_COMMIT_OBSERVATION / 1` + `swm.payload.local-git.commit-observation@1` | `(repositoryIdentity, objectFormat, commitOid, fieldId, optionalParentOrdinal)`；`fieldId=COMMIT_OID|TREE_OID|PARENT_OID|AUTHOR_OBSERVATION|COMMITTER_OBSERVATION|MESSAGE_BYTES` | 在冻结 Commit Payload 内按 Field ID 取唯一字段；`PARENT_OID` 必须给出从 0 开始且存在的 ordinal；选择完整 typed field / message bytes，不允许子串或截断 |
| `swm.locator.tree-entry@1` | `LOCAL_GIT_TREE_LISTING / 1` + `swm.payload.local-git.tree-listing@1` | `(repositoryIdentity, objectFormat, commitOid, canonicalPathBytes, entryKind, objectOid)` | 在一个 Coverage 明确的冻结 listing Payload 中按 exact path bytes 唯一选中一项，并重验 entry kind / OID；Locator 只证明已返回的该 entry，不把部分 listing 解释为目录完整性 |
| `swm.locator.content-span@1` | `LOCAL_GIT_BLOB_OBSERVATION / 1` + `swm.payload.local-git.blob-observation@1` | `(repositoryIdentity, objectFormat, commitOid, canonicalPathBytes, blobOid, startByte, endByte)` | Byte Range 为 exact blob 的绝对半开区间 `[startByte,endByte)`，必须完整落在冻结 Artifact 的 returned range 内；重验 Payload 中 exact blob identity、returned range、范围 Content Digest 后唯一返回该连续 bytes。局部 Payload 不要求重算完整 Git blob OID；不允许跨 Range、拼接或行号重解析 |
| `swm.locator.diff-entry@1` | `LOCAL_GIT_TREE_CHANGESET / 1` + `swm.payload.local-git.tree-changeset@1` | `(repositoryIdentity, objectFormat, baseCommitOid, targetCommitOid, changeOrdinal, beforePathOrAbsent, afterPathOrAbsent, beforeModeOrAbsent, afterModeOrAbsent, beforeObjectOidOrAbsent, afterObjectOidOrAbsent)` | 在冻结 changeset Payload 内按 ordinal 与 canonical path 排序位置唯一选中并重验全部 before/after 字段，选择完整 typed change entry；不执行 hunk、rename 或 copy 推断 |

Digest 规则固定如下：

1. `Observed Content Digest = SHA-256(TUPLE(contentEncodingTag, exactSelectedContent))`，Tuple 使用 exact dependency codec。Commit / Tree / Diff 的 tag=`TYPED_OBSERVATION`，content=`BYTES(SWM-LOCAL-GIT-TYPED-OBSERVATION@1 framed bytes)`；Blob / message 的 tag=`RAW_BYTES`，content=`BYTES(exact raw bytes)`，CR 与 LF 原样保留。
2. `Observation Digest = SHA-256(TUPLE(Artifact ID, Artifact Kind / Schema Version, Payload Schema ID, Evidence Representation ID / Version, Locator Contract ID / Version, Source Context Reference, canonical Locator Tuple, Observed Content Digest, actual Coverage Digest))`；ID / Enum / Tuple / Digest 均使用 exact dependency codec，不能拼接裸字符串或使用实现对象序列化。
3. 解析必须产生恰好一个连续有界结果，并重算两个 Digest。`LOCATOR_OUT_OF_BOUNDS | LOCATOR_AMBIGUOUS | LOCATOR_TRUNCATED | LOCATOR_SCHEMA_UNSUPPORTED | LOCATOR_CONTENT_MISMATCH | ARTIFACT_UNAVAILABLE` 任一结果都禁止创建或复用 Evidence，不能降级为局部成功。
4. Iteration 001 不接受 Derived Artifact 进入 Evidence Materialization；因此本 Schema 不注册 Lineage Range Mapping。需要 Derived Artifact 时必须新增版本化 Schema Definition 与完整可逆 Mapping Contract，不能沿用上述 Locator ID。

约束：

1. 一条 Evidence 恰好一个 Artifact、一个 Locator 和一个 Source Context。
2. `content-span` 必须是连续且有界的区域；行号只可展示，不能单独定位。
3. 两个不连续位置形成两条 Evidence，即使属于同一文件；它们仍共享 Source Root，不能按数量冒充独立来源。
4. Evidence Record 必须具有不可变最小精确 Evidence Snapshot；本文采用 `NO_PHYSICAL_CLEANUP`。
5. Evidence 不携带全局极性、Confidence、Entity ID 或 Fact 命题。

## 6. Entity Kind 与 Identity Scheme

全部 Entity 均为 `Semantic Category = TECHNICAL`、`Identity Origin = SOURCE_ANCHORED`。Entity State 中的名称、路径、Kind 和定位元数据只用于身份解析与检索，不能直接支持属性或关系 Claim。

| Entity Kind ID | Identity Key Scheme ID | Identity Domain | Canonical External Entity Key | Identity-bearing Context | 明确不作为稳定键 |
|---|---|---|---|---|---|
| `swm.entity.git-revision@1` | `swm.identity.git-revision@1` | Repository Identity | `{objectFormat, fullOid}` | `EMPTY` | short SHA、Branch、Tag、提交标题 |
| `swm.entity.source-unit@1` | `swm.identity.source-unit@1` | Repository Identity | `{canonicalGitPathBytes}` | `EMPTY` | entry kind、绝对路径、行号、内容相似度 |
| `swm.entity.software-module@1` | `swm.identity.software-module@1` | Repository Identity | `{moduleRootCanonicalGitPathBytes}` | `EMPTY` | GAV、仅显示名、未由受支持 descriptor 固定的聚合目录名 |
| `swm.entity.code-symbol@1` | `swm.identity.code-symbol@1` | Repository Identity + language namespace | `{sourceUnitKey, containingTypeChain, symbolKind, canonicalName, signatureDescriptor}` | `EMPTY` | 仅简单名、模型生成 FQN、缺少签名的重载名 |
| `swm.entity.dependency-component@1` | `swm.identity.dependency-component@1` | `MAVEN` | `{ecosystem=MAVEN, groupId, artifactId, type, classifierOrAbsent}` | `EMPTY` | requested version、下载 URL、显示别名、未解析 property expression |
| `swm.entity.config-item@1` | `swm.identity.config-item@1` | Repository Identity + `UTF8_SIMPLE_PROPERTIES_V1` | `{sourceUnitKey, canonicalConfigKey}` | `EMPTY` | module owner、secret value、环境实际值、文件行号 |

### 6.1 Identity Anchor Contract

Identity Anchor Canonicalizer 固定为 `SWM-LOCAL-GIT-IDENTITY-ANCHOR-CANONICALIZATION@1`。以下是本 Schema 注册的全部 `Artifact Kind × Evidence Representation × Entity Kind` 组合；未列组合一律 `KEEP_UNRESOLVED`，不得由模型、Provider Target Resolution Receipt 或相似名称补齐。

| Anchor Contract ID | exact Artifact / Evidence | Entity Kind | Evidence 内 Source-native Identifier 重建 | Identity Scheme / External Key | Context Projection 与失败边界 |
|---|---|---|---|---|---|
| `swm.anchor.git-revision-from-commit@1` | `LOCAL_GIT_COMMIT_OBSERVATION / 1` + `swm.evidence.git-commit-record@1` | git-revision | 从 commit Payload 与 commit-field Evidence 重验 `{objectFormat, fullCommitOid}` | `swm.identity.git-revision@1 / {objectFormat,fullOid}`；Domain=Repository Identity | `EMPTY`；短/非完整 OID、对象类型非 commit 或 Repository 不明时 unresolved |
| `swm.anchor.source-unit-from-tree@1` | `LOCAL_GIT_TREE_LISTING / 1` + `swm.evidence.git-tree-entry@1` | source-unit | 从唯一 tree entry 重验 canonical Git path bytes 与由 Git mode 机械映射的 `entryKind`；kind 只进入 Entity State | `swm.identity.source-unit@1 / {canonicalGitPathBytes}`；Domain=Repository Identity | `EMPTY`；path/mode/OID 不一致、Selector 越界或 entry 非唯一时 unresolved |
| `swm.anchor.source-unit-from-blob@1` | `LOCAL_GIT_BLOB_OBSERVATION / 1` + `swm.evidence.git-file-content@1` | source-unit | 从 Artifact Target 重验 canonical Git path bytes、blob OID 与 `BLOB|SYMLINK_BLOB` kind；kind 与 Evidence 内容不进入稳定键 | `swm.identity.source-unit@1 / {canonicalGitPathBytes}`；Domain=Repository Identity | `EMPTY`；Artifact 未绑定 path、kind 不支持或 Locator 回放失败时 unresolved |
| `swm.anchor.module-from-build-descriptor@1` | `LOCAL_GIT_BLOB_OBSERVATION / 1` + `swm.evidence.git-file-content@1` | software-module | Evidence 必须覆盖根元素/首个声明，并由 `MAVEN_POM_MODULE_ROOT_V1` 证明 path basename=`pom.xml`；取其 parent path，仓库根用 `ROOT` | `swm.identity.software-module@1 / {moduleRootCanonicalGitPathBytes}`；Domain=Repository Identity | `EMPTY`；非受支持 descriptor、同 path 内容不成合法 Maven project 或 root 无法唯一确定时 unresolved |
| `swm.anchor.java-symbol-from-declaration@1` | `LOCAL_GIT_BLOB_OBSERVATION / 1` + `swm.evidence.git-file-content@1` | code-symbol | 在 Evidence 连续声明范围内按 `JAVA_SYMBOL_V1` 重建 source-unit key、containing type chain、member kind、canonical name、normalized declaration signature 与 declaration digest | `swm.identity.code-symbol@1 / {sourceUnitKey,containingTypeChain,symbolKind,canonicalName,signatureDescriptor}`；Domain=Repository Identity + `java` | `EMPTY`；声明不完整、重载签名缺失、解析多义、模型 FQN 与源码不一致时 unresolved |
| `swm.anchor.maven-component-from-dependency@1` | `LOCAL_GIT_BLOB_OBSERVATION / 1` + `swm.evidence.git-file-content@1` | dependency-component | Evidence 覆盖一个完整 Maven `<dependency>`；`MAVEN_DEPENDENCY_COORDINATE_V1` 直接解析非空字面量 groupId、artifactId、type(default `jar`) 与 classifier(optional) | `swm.identity.dependency-component@1 / {ecosystem=MAVEN,groupId,artifactId,type,classifierOrAbsent}`；Domain=`MAVEN` | `EMPTY`；坐标含未解析 property/expression、继承补值、缺项或 XML 多义时 unresolved |
| `swm.anchor.config-item-from-declaration@1` | `LOCAL_GIT_BLOB_OBSERVATION / 1` + `swm.evidence.git-file-content@1` | config-item | Evidence 覆盖一个完整 `UTF8_SIMPLE_PROPERTIES_V1` 声明，并从同一 Blob Artifact 重建 source-unit key 与 canonical key | `swm.identity.config-item@1 / {sourceUnitKey,canonicalConfigKey}`；Domain=Repository Identity + `UTF8_SIMPLE_PROPERTIES_V1` | `EMPTY`；编码/语法不支持、key 多义、动态/续行/转义输入或 value 为 Secret locator 时 unresolved |

共通 Anchor 规则：

1. Knowledge Engine 必须从权威 Evidence Snapshot 重读并按 exact Anchor Contract 重建 Source-native Identifier、Identity Domain 与 External Key；Provider Receipt 只用于 Source Target 定位和 Provenance，不能直接绑定 Entity。
2. 一项 Anchor Observation 恰好引用一条 Evidence / Mention。多个 Observation 只有 External Key 机械相等且 `ENTITY_IDENTITY_ANCHOR_COMPOSITION` 成功时才可聚合；Evidence 数量不表示身份置信度。
3. 本表全部 `Identity-bearing Context Projection = EMPTY`；未声明的 Commit、Ref、Time、path position 或模型标签不得进入身份键。Source Context 仍完整保留在 Anchor Observation / Entity State。
4. 本版本唯一 Continuity Rule 是同 Domain、Kind、Scheme 与 External Key 的 exact equality。`TREE_CHANGESET_NO_RENAME_V1` 不产生 rename/move/alias Continuity；冲突、缺项、歧义或不能机械重建均返回 `KEEP_UNRESOLVED`。

Identity 规则：

1. owning Scope、Entity Kind、Category、Origin、Identity Domain、Identity Key Scheme ID 和 Canonical External Key 共同进入 Presented Entity Identity Key。
2. Git Commit 不进入除 `git-revision` 外其他 Entity 的稳定身份；它保留在 Entity State / Evidence Context，使同一来源身份可跨 Commit 延续。
3. `source-unit` 的路径移动默认产生新 Presented Key。Iteration 001 Local Git Profile 使用 `TREE_CHANGESET_NO_RENAME_V1`，因此 add + delete 不构成 rename/move Continuity，也不能自动 LINK 既有 Root。
4. 本切片的 `code-symbol` 只支持 `language namespace = java`，并与 Local Git `JAVA_SYMBOL_V1` 对齐。它必须区分 source path、containing type chain、member kind 与重载签名；任一项无法从 Evidence 按 exact Anchor Contract 重建时 `KEEP_UNRESOLVED`，不得仅按名称或 Resolution Receipt 创建。
5. 多 Mention / Anchor 只有 Context 投影机械相等或 `ENTITY_IDENTITY_ANCHOR_COMPOSITION` 为 current VALID `COMPATIBLE` 时才聚合。
6. `CREATE_NEW | LINK_EXISTING | KEEP_UNRESOLVED` 沿用 Accepted Contract。稳定 Entity ID 只在 Snapshot 最终事务分配。
7. 本 Schema 不注册 `BUSINESS`、`INFERRED` 或 `ENTITY_DERIVATION`。遇到需要稳定业务身份或推断型技术身份的任务形成明确 Gap，不创建占位 Entity。

## 7. Fact Type Contract

### 7.1 共通规则

每个 Fact Type 都必须满足：

- Observation Modality 是 Canonical Proposition 的组成部分。
- 至少一个语义目标 Entity Term；名称或未解析文本不能替代 Entity Reference。
- 每个命题路径由 `DIRECT_SUPPORTS` 或合法 `PARTIALLY_SUPPORTS` Composition 完整覆盖。
- FactContext 不宽于 Evidence Context；Git Commit 是 State Applicability Context，默认不进入稳定 Fact Identity Key。
- `Context Limits` 只能收窄；不能靠 Build Intent、Branch 当前值、模型常识或 Snapshot 默认值扩大。
- 同一 Proposition 的重复 Evidence 不投票、不产生 Confidence。
- 正式 Fact State 只有 `ASSERTED`；Partial、Rejected、Conflicted 只存在于 Candidate / Verification。

### 7.2 最小 Fact Type 集合

| Fact Type ID | Canonical Proposition Roles | Observation Modality | 允许 Entity Kind | Direct Support / Composition |
|---|---|---|---|---|
| `swm.fact.element-declaration@1` | `element, declarationKind, canonicalName, optionalSignature` | `CODE_DECLARES` | element=code-symbol | 一条完整 Java 声明 Evidence；不得由 Entity metadata 自证 |
| `swm.fact.structural-relation@1` | `subject, relation, object`；relation=`CONTAINS | DECLARES | EXTENDS | IMPLEMENTS | IMPORTS | REFERENCES` | `CODE_DECLARES` | source-unit / code-symbol 间满足第 7.3 节矩阵的组合 | 一条完整语法关系 Evidence；不根据目录、名称相似或模型常识补写关系 |
| `swm.fact.interface-mapping@1` | `handler, protocol, operation, orderedPathParts, conditions` | `CODE_DECLARES` | handler=code-symbol | 单 Evidence，或 `HTTP_PATH_JOIN@1` 对明确 path fragment 作机械组合；当前 protocol 仅 `HTTP` |
| `swm.fact.execution-step@1` | `owner, stepPath, operation, targetOrValue, condition`；operation=`INVOKE | BRANCH_ON | RETURN | THROW | READ_CONFIG | WRITE_STATE` | `CODE_DECLARES` | owner=code-symbol；target 可为 code-symbol/config-item 或 Typed Literal | 每个 step 一条连续代码 Evidence；stepPath 只表达源码声明顺序，不宣称运行一定发生 |
| `swm.fact.dependency-declaration@1` | `ownerModule, component, requestedVersion, dependencyScope` | `BUILD_DESCRIPTOR_DECLARES` | software-module、dependency-component | 一条完整依赖声明 Evidence；requestedVersion 是命题值，不进入 component 身份 |
| `swm.fact.config-declaration@1` | `configItem, canonicalKey, declaredValueKind, optionalDeclaredValue` | `CONFIG_DECLARES` | config-item | 一条受支持配置声明 Evidence；Secret value 禁止进入命题和 Evidence Snapshot |
| `swm.fact.revision-parent@1` | `revision, parentRevision, parentOrdinal` | `VCS_OBSERVED` | git-revision | exact commit record Evidence；parent 必须为 full OID Entity |
| `swm.fact.revision-change@1` | `targetRevision, baseRevision, changeKind, affectedTarget, beforeObjectOid, afterObjectOid`；changeKind=`ADDED | DELETED | MODIFIED | TYPE_CHANGED` | `VCS_OBSERVED` | target/base=git-revision；affectedTarget=source-unit | 一个 `TREE_CHANGESET_NO_RENAME_V1` diff entry Evidence；若任务要求 parent diff，必须另由 revision-parent Fact 对齐 base |
| `swm.fact.source-statement@1` | `declarer, statementRole, statementText, target`；role=`PURPOSE | RESPONSIBILITY | BUSINESS_RULE | CHANGE_RATIONALE` | `DOCUMENT_DECLARES | VCS_METADATA_DECLARES | CODE_COMMENT_DECLARES` | declarer=source-unit/git-revision；target 为本 Schema Entity 或空 | 直接文本 Evidence；Fact 只表示“来源声明了该语句”，不表示语句内容已成为实现事实 |

### 7.3 命题路径级 Evidence Contract

表中 `!` 为必填路径、`?` 为可选路径；未列路径非法。`Entity<T>` 必须是已解析的本 Schema Entity Reference，`Literal<T>`、Enum 和有序集合按第 12 节规范化。`ONE` 表示一条 Evidence 必须直接覆盖全部已出现路径；`JOIN` 只允许表中点名的组合。

| Fact Type | 命题路径、基数与类型 | exact Evidence Representation / Direct Observation | Coverage / Composition Rule |
|---|---|---|---|
| element-declaration | `element!:Entity<code-symbol>; declarationKind!:Enum<JAVA_SYMBOL_V1 kind>; canonicalName!:Literal<string>; optionalSignature?:Literal<signature>` | `swm.evidence.git-file-content@1`；`JAVA_SYMBOL_V1` 在一个完整连续声明中直接解析全部值 | `JAVA_DECLARATION_ONE@1`：ONE 覆盖所有 present paths；signature 对可重载 member 必填，其他场景 absent；Entity Anchor 可同源但 Entity metadata 不算支持 |
| structural-relation | `subject!:Entity; relation!:Enum; object!:Entity`；只允许 `source-unit-DECLARES-code-symbol`、`code-symbol-DECLARES-code-symbol`、`code-symbol-CONTAINS-code-symbol`、`code-symbol-EXTENDS-code-symbol`、`code-symbol-IMPLEMENTS-code-symbol`、`source-unit-IMPORTS-code-symbol`、`code-symbol-REFERENCES-code-symbol` | `swm.evidence.git-file-content@1`；`JAVA_RELATION_OBSERVATION_V1` 的一个完整 declaration / import / reference node 必须同时出现 subject 语法边界、relation token 与可唯一解析 object source-native identifier | `JAVA_RELATION_ONE@1`：ONE 覆盖三个路径；object 未能按 Anchor Contract 解析为本地 Entity 时不得用字符串代替，也不得跨 Evidence 拼接 |
| interface-mapping | `handler!:Entity<code-symbol>; protocol!:Enum<HTTP>; operation!:Enum<HTTP method>; orderedPathParts!:Ordered<Literal<path fragment>>[1..2]; conditions?:Ordered<Literal<condition>>` | 每项为 `swm.evidence.git-file-content@1`；`JAVA_HTTP_MAPPING_V1` annotation 直接声明 method/path/condition；handler declaration 与 annotation 必须在 Evidence 范围内 | `HTTP_MAPPING_ONE@1` 或 `HTTP_PATH_JOIN@1`：ONE 覆盖全部；JOIN 只允许同 exact Commit、同 handler 的一个 containing-type fragment 加一个 method fragment，按 outer→inner 排序，conditions 原样并列；不得执行配置替换或框架默认推断 |
| execution-step | `owner!:Entity<code-symbol>; stepPath!:Ordered<Literal<unsigned index>>; operation!:Enum<INVOKE|BRANCH_ON|RETURN|THROW|READ_CONFIG|WRITE_STATE>; targetOrValue?:Entity<code-symbol|config-item>|TypedLiteral; condition?:TypedLiteral` | `swm.evidence.git-file-content@1`；`JAVA_EXECUTION_OBSERVATION_V1` 的一个完整 Java statement / expression node 直接声明 operation、source order 与存在的 target/value/condition | `JAVA_EXECUTION_STEP_ONE@1`：ONE；`BRANCH_ON` 必须有 condition，`INVOKE|READ_CONFIG|WRITE_STATE|THROW` 必须有 targetOrValue，RETURN 可 absent；stepPath 仅来自同一 owner declaration 的 lexical order |
| dependency-declaration | `ownerModule!:Entity<software-module>; component!:Entity<dependency-component>; requestedVersion?:Literal<Maven version>; dependencyScope!:Enum<COMPILE|PROVIDED|RUNTIME|TEST|SYSTEM|IMPORT>` | `swm.evidence.git-file-content@1`；`MAVEN_DEPENDENCY_COORDINATE_V1` 从一个完整 `<dependency>` 直接解析所有 present 值，缺 scope 机械取 Maven 默认 `COMPILE` | `MAVEN_DEPENDENCY_ONE@1`：ONE；owner 由同一 pom path 的 module Anchor 重建，component 由同一 dependency Anchor 重建；property/interpolation 未正式解析时 requestedVersion 只能保留原 declared literal，不得改成 effective version |
| config-declaration | `configItem!:Entity<config-item>; canonicalKey!:Literal<config key>; declaredValueKind!:Enum<STRING|NUMBER|BOOLEAN|NULL|SECRET_REFERENCE>; optionalDeclaredValue?:TypedLiteral` | `swm.evidence.git-file-content@1`；`UTF8_SIMPLE_PROPERTIES_V1` 在一个完整单行声明中直接解析 key / value kind / non-secret value | `CONFIG_DECLARATION_ONE@1`：ONE；key 必须等于 Anchor key；Secret 或疑似 credential 只允许 `SECRET_REFERENCE` 且 value absent；不解释环境覆盖、escape、continuation 或结构值 |
| revision-parent | `revision!:Entity<git-revision>; parentRevision!:Entity<git-revision>; parentOrdinal!:Literal<unsigned integer>` | `swm.evidence.git-commit-record@1` + `swm.locator.commit-field@1(fieldId=PARENT_OID, ordinal)`；commit target 与该 ordinal 的 full parent OID 被同一冻结 payload 直接观察 | `GIT_PARENT_ONE@1`：ONE；Locator tuple 同时覆盖 revision、parent 和 ordinal；merge parent 不允许隐式选择 |
| revision-change | `targetRevision!:Entity<git-revision>; baseRevision!:Entity<git-revision>; changeKind!:Enum<ADDED|DELETED|MODIFIED|TYPE_CHANGED>; affectedTarget!:Entity<source-unit>; beforeObjectOid?:Literal<Git OID>; afterObjectOid?:Literal<Git OID>` | `swm.evidence.git-diff-entry@1`；`TREE_CHANGESET_NO_RENAME_V1` 单个 entry 直接观察 base/target、kind、path/mode 与 old/new object OID | `GIT_CHANGE_ONE@1`：ONE；ADDED=`before absent, after required`，DELETED=`before required, after absent`，MODIFIED/TYPE_CHANGED=`both required`；affectedTarget 必须由对应 before/after path 的 source-unit Anchor 解析，不能从 change entry 猜 symbol |
| source-statement | `declarer!:Entity<source-unit|git-revision>; statementRole!:Enum<PURPOSE|RESPONSIBILITY|BUSINESS_RULE|CHANGE_RATIONALE>; statementText!:Literal<string>; target?:Entity` | `SOURCE_STATEMENT_V1`：`swm.evidence.git-file-content@1` 使用完整连续 document/comment statement，或 `swm.evidence.git-commit-record@1` 使用完整 `MESSAGE_BYTES` | `SOURCE_STATEMENT_ONE@1`：ONE；不连续文本不得拼接；role 必须由语句自身明确表达并经独立复核；target 只有在同一 Evidence 中出现且可由 Anchor 唯一解析时允许，否则 absent；文本只证明来源声明 |

所有 ONE Rule 均要求 Evidence Context 不宽于且可推出 FactContext。`HTTP_PATH_JOIN@1` 是本版本唯一多 Evidence Composition：两条 Evidence 必须同 Repository、exact Commit、handler 与 Java declaration nesting，`FACT_SUPPORT_COMPOSITION=COMPATIBLE`，并分别完整覆盖自己的 fragment；其他任何缺失路径都不能由第二条 Evidence、模型常识或 Entity metadata 补齐。

### 7.4 Conflict Target Alignment

只有下表组合可进入 `FACT_CONFLICT_ASSESSMENT@1`；两侧必须同 Scope、同 exact Fact Type、同 listed Observation Modality，先对齐 Key Paths，再比较 Value Paths。Value Paths 均存在且规范值机械不等时才得到 Semantic Incompatibility；未列 Fact Type / Role / Modality、可多值声明或任一值 absent 一律 `NOT_COMPARABLE`，不是 Conflict。

| Fact Type | 双侧 Modality | Target Alignment Key Paths | Compared Value Paths |
|---|---|---|---|
| dependency-declaration | `BUILD_DESCRIPTOR_DECLARES` | `ownerModule, component, dependencyScope` | `requestedVersion` |
| config-declaration | `CONFIG_DECLARES` | `configItem, canonicalKey` | `declaredValueKind, optionalDeclaredValue` |
| revision-parent | `VCS_OBSERVED` | `revision, parentOrdinal` | `parentRevision` |
| revision-change | `VCS_OBSERVED` | `targetRevision, baseRevision, affectedTarget` | `changeKind, beforeObjectOid, afterObjectOid` |

### 7.5 Fact Canonicalization 与身份

1. 本版本的 `Fact Type Identity Scheme ID` 等于表中 exact Fact Type ID；兼容的后续 Definition 必须沿用该 Scheme ID，而不能只因 Contract / Canonicalizer 升级创建新身份命名空间。Fact Identity Key 为 `(FACT, Scope, Fact Type Scheme ID, Canonical Proposition Stable Semantic Key, Fact Identity Context Key)`。
2. 上述类型的 `Fact Identity Context Key = EMPTY`；exact Git Commit 和 Observation Time 完整保留在 Fact State / Support Context，Branch / Tag / HEAD 只保留在 Target Resolution Provenance。
3. Entity Term 以 Effective Entity Identity Key 参与候选期语义 Digest，以稳定 Entity Identity Reference 进入发布后 Proposition。
4. Relation、Operation、Modality、Condition、Typed Literal 类型与值均进入 Proposition；不能把它们降为显示字段。
5. 自然语言 `statementText` 只执行 NFC、LF 和空行保真规范化，不做同义改写；其 Digest 与全文同时属于 Proposition。
6. 否定 Fact 不在本 Schema 注册。空搜索、未发现或未采集不能转成“不存在”。
7. `HTTP_PATH_JOIN@1` 只允许按声明顺序连接 path fragment、规范重复分隔符并保留模板变量；任何配置替换、条件启用或框架隐式规则若未由 Evidence 直接表达，必须进入 Inference 或 Gap。

## 8. Inference Type Contract

### 8.1 共通规则

1. 正式语义前提只允许固定 Snapshot 中 `ASSERTED` Fact，或下表明确允许的已发布 `ASSERTED` Inference。
2. 本轮 Fact / Inference Candidate 永远不能成为另一个 Inference Candidate 的语义前提。
3. 每个 Argument 必须具有非空已发布 Fact Leaf、显式 Premise Role、版本化 Rule、Context 构造、限制与反例检查；不得保存或依赖隐藏 Chain-of-Thought。
4. Output Modality 由 Type Rule 传播，不能从模型 Confidence 推出。
5. Dependency DAG 必须可展平、无环，并服从 Execution Envelope 的有限 Depth / Node / Step / Edge 上限。
6. 正式 Inference State 只有 `ASSERTED`；其 Canonical Conclusion 中仍保留结论自身的 Epistemic / Intent Modality。

### 8.2 最小 Inference Type 集合

本版本的 `Inference Type Identity Scheme ID` 等于表中 exact Inference Type ID；兼容的后续 Definition 必须沿用该 Scheme ID。Type Contract 或 Canonicalizer Version 只进入 Provenance，不自然创建新 Root。

| Inference Type ID | Canonical Conclusion | 允许的直接前提 | 输出 Modality 与边界 |
|---|---|---|---|
| `swm.inference.declared-behavior-flow@1` | `entrySymbol, orderedMajorSteps, branchConditions, declaredOutcome` | execution-step、interface-mapping、structural-relation、config-declaration Fact；可选已发布同类型 Inference | `ASSERTED_RELATION` 只表示代码声明的流程，不表示已部署或每次运行实际发生 |
| `swm.inference.change-impact@1` | `revision, affectedEntity, impactAspect, impactDescription`；aspect=`STRUCTURE | INTERFACE | BEHAVIOR | CONFIGURATION | DEPENDENCY` | revision-parent、revision-change、structural、interface、execution、dependency、config Fact；可选 declared-behavior-flow | 可为 `ASSERTED_RELATION`；每个 affectedEntity/aspect 是独立结论，不能由单条结论宣称影响集合完整 |
| `swm.inference.change-explanation@1` | `revision, explanationKind, explanationText, linkedChanges` | source-statement、revision-change、change-impact | 有明确 CHANGE_RATIONALE statement 时为 `SOURCE_DECLARED_RELATION`；仅从变更相关性归纳时最多 `POSSIBLE_CORRELATION`，不得宣称真实作者意图或因果 |
| `swm.inference.business-interpretation@1` | `technicalSubject, businessConceptLabel, relationshipRole, basisScope` | source-statement、interface-mapping、declared-behavior-flow、structural / execution Fact | 明确 BUSINESS_RULE / PURPOSE statement 支持时为 `SOURCE_DECLARED_RELATION`；仅由技术模式归纳时最多 `POSSIBLE_CORRELATION`；不创建 Business Entity |
| `swm.inference.fact-conflict@1` | `leftFact, rightFact, conflictKind, comparedDimension` | 恰好两个目标 Fact，以及 Conflict Rule 要求的已发布辅助正式前提 | `ASSERTED_RELATION` 表示正式冲突；必须完成 Target Alignment、`CONFLICT_COMPARISON` 和 Semantic Incompatibility；不选择赢家 |

### 8.3 Inference Argument Rule

| Rule ID | 适用类型 | 必须公开的结构化判断 |
|---|---|---|
| `BEHAVIOR_FLOW_COMPOSITION@1` | declared-behavior-flow | entry 对齐、stepPath 顺序、branch 条件、调用边界、遗漏/替代路径和 Context |
| `CHANGE_IMPACT_PROPAGATION@1` | change-impact | exact revision/diff 覆盖、affected Entity 对齐、影响 aspect、传播边和未覆盖范围 |
| `CHANGE_EXPLANATION_LINK@1` | change-explanation | statement 与 revision 对齐、linked change、模态限制和替代解释 |
| `BUSINESS_INTERPRETATION_LINK@1` | business-interpretation | technical premise、source-declared basis 或 pattern basis、Scope、模态和反例 |
| `FACT_CONFLICT_ASSESSMENT@1` | fact-conflict | `TARGET_ALIGNMENT`、`CONTEXT_COMPARABILITY`、`SEMANTIC_INCOMPATIBILITY` 三项独立结果 |

Conflict 最小边界：

- 两个目标 Fact 必须属于相同可比较 Fact Type / Role / Value Dimension，或存在本文明确的机械对齐规则。
- 默认只比较相同 Observation Modality。`DOCUMENT_DECLARES` 与 `CODE_DECLARES` 的差异不自动构成冲突。
- 本版本不注册组织治理、规范优先级或“实现必须符合文档”的通用规则；缺少显式正式前提时不产生规范—实现 Conflict。
- Conflict 不修改、隐藏、降权或删除任一目标 Fact。

### 8.4 INITIAL 前提限制

`INITIAL` 使用 `Expected Current = NO_CURRENT`，因此没有合法本地正式前提。首次 Snapshot 只允许发布 SOURCE_ANCHORED Entity 和直接 Evidence 支持的 Fact；不能在同一 Candidate Bundle 中用这些 Fact Candidate 构造 Inference。

需要 Behavior、Business、History 结论时，Application 必须在首次 Snapshot 成功发布后开启新的 `UNCHANGED` Knowledge Update，以 exact Base Snapshot 中已发布 Fact / Inference 作为前提。该额外更新可以由同一用户任务显式编排，但必须是新的 Application Attempt、Candidate Envelope、Admission 与 Publication；不得伪装成 INITIAL 同事务的“第二阶段”。

## 9. Candidate、关系与 Admission Obligation

### 9.1 Candidate 关系

| 关系 | 类型 | 语义 |
|---|---|---|
| Entity → Fact | `DIRECTED_PUBLICATION_PREREQUISITE` | Fact 引用 Candidate-local Entity 时，Entity Closure 必须同时 INCLUDED / ACCEPT；不合并为一个巨大 Closure |
| Published Entity → Inference Conclusion | `RESOLUTION_BINDING` | 本 Schema 不含 Semantic Entity；Inference Conclusion 只能绑定构建开始时 exact Base Snapshot 中已发布的本地 Entity，并在目标 Snapshot 中完成语义保持 Rebinding |
| Fact / Inference → Inference Premise | `FORMAL_PREMISE_DEPENDENCY` | 只能引用构建开始时固定 Snapshot 中的 Resolved Formal Knowledge Reference；不能引用 Candidate |
| Inference → Conflict target | `FORMAL_PREMISE_DEPENDENCY` | 两个目标 Fact 都必须进入直接 Premise 和依赖闭包 |
| Evidence → Fact | `TRACEABILITY_DEPENDENCY` | Evidence / Link / Support Set 是 Fact State 追溯闭包，不是 Snapshot 正式成员 |
| Context → State | `APPLICABILITY_DEPENDENCY` | Context 限定 Entity / Fact / Inference State，不重写成员语义 |

本 Schema 不存在 INFERRED Entity 与 ENTITY_DERIVATION 的 Hard Atomic Edge。

### 9.2 通用 Admission Obligation

| Obligation ID | 适用对象 | PASS 条件 |
|---|---|---|
| `SCHEMA_AND_TYPE_CLOSED@1` | 全部 | exact Schema、Type、Context、Reference、Canonicalization 和 Digest 可重建，无未知字段或越界 Kind |
| `IDENTITY_UNIQUE_AND_RESOLVED@1` | Entity / 含 Entity Term 的知识 | Effective Identity Key 完整；同名、短 SHA、重载或跨 Scope 歧义失败关闭 |
| `EVIDENCE_REPLAYABLE@1` | SOURCE_ANCHORED Entity / Fact | Evidence Record、Locator、Snapshot、Content / Observation Digest、Context 和 Provenance 可独立重放 |
| `FACT_DIRECT_COVERAGE@1` | Fact | Proposition 每个语义路径被合法 Support Set 直接覆盖，Context 未扩大，无隐藏前提 |
| `FACT_MODALITY_FAITHFUL@1` | Fact | CODE / DOCUMENT / VCS 等 Observation Modality 未被偷换成实现真相或运行真相 |
| `INFERENCE_PREMISE_FORMAL@1` | Inference | 全部前提来自 exact published Snapshot，State=ASSERTED，Type / Modality 允许，Fact Leaf 非空 |
| `INFERENCE_ARGUMENT_COMPLETE@1` | Inference | Conclusion、Argument Step、Dependency、Context、限制和反例完整且有界无环 |
| `CONFLICT_THREE_PART_PROOF@1` | fact-conflict | Target Alignment、Context Comparability、Semantic Incompatibility 全部 PASS，且不选择赢家 |
| `LOCAL_REFERENCE_SUBSTITUTION_SAFE@1` | 含 Candidate-local 引用的 Closure | Substitution Manifest 完整，替换前后 Substitution-Invariant Closure Digest 不变 |
| `DISCLOSURE_AND_COUNTEREXAMPLE_CLOSED@1` | 全部 | Construction Disclosure 与 Verifier 独立发现项全部处置；UNKNOWN / NOT_EVALUATED 不能聚合为 ACCEPT |

Knowledge Verification 必须使用与生成隔离的执行上下文和 Strategy，从权威 Repository 重读 Evidence / Formal Premise。Verifier 不访问 Connector、不修改 Candidate，也不能用 Evidence 中未正式化的内容补写命题或 Argument。

只有全部适用 Obligation 为 PASS 才能 `ACCEPT`。`REVISION_REQUIRED | MORE_INFORMATION_REQUIRED | REJECT` 和 `EXECUTION_FAILED` 沿用 Accepted Admission 语义，不能成为 Snapshot 成员。

## 10. Snapshot Membership 与 Reader Contract

### 10.1 正式成员

Snapshot Member 只允许：

- 本 Schema 下的不可变 Entity State。
- 本 Schema 下的 `ASSERTED` Fact State。
- 本 Schema 下的 `ASSERTED` Inference State。

Artifact、Evidence、KnowledgeContext、Candidate、Admission Decision、Claim、View 和模型输出不是成员。Evidence / Context / Admission / Capability 只作为完整 Provenance Dependency Manifest 被引用。

### 10.2 Snapshot 完整性

1. 每个 Snapshot 恰好绑定本文 exact Knowledge Schema Reference。
2. Member Manifest 是 Scope 的完整目标正式知识集合，不是查询时动态叠加的 Delta。
3. 每个本地 Entity / Premise 在目标 Snapshot 中有 exact State；跨 Scope 引用在本 Schema Applicability Boundary 下禁止。
4. 每个 Entity / Fact / Inference Root 在一个 Snapshot 中至多一个 State。
5. Evidence 必须具有自包含最小快照，并声明 `NOT_REQUIRED_SELF_CONTAINED` 外部保留依赖。
6. Stable ID、Root、State、Link、Manifest、Receipt、Publication Outcome 和 CURRENT 切换在一个 Scope 的最终事务中全部生效或全部不可见。
7. Projection 为 `DISABLED`；Reader 直接从 Authority Store 按 exact Snapshot / Member Manifest 读取。

### 10.3 Reader Contract

`SWM-FORMAL-KNOWLEDGE-READER@1` 只接受：

- exact Snapshot Reference / Snapshot Read Session；不接受动态 CURRENT 作为持续读取引用。
- `ENTITY | FACT | INFERENCE` 和本文注册的 Type ID。
- Resolved Formal Knowledge Reference，并验证对象属于 Member Manifest。
- Context / Entity / Type / Proposition / Conclusion 条件的有界查询。

Reader 返回：

- Entity：只证明身份存在和可引用；名称、位置、Anchor metadata 不能支持属性 Claim。
- Fact：Canonical Proposition、Observation Modality、FactContext、正式引用和允许的 Source Locator；不返回 Evidence Quote。
- Inference：Canonical Conclusion、Conclusion Modality、InferenceContext、Argument / Premise 正式引用和限制；不返回模型隐藏推理。
- Conflict：同时返回全部目标 Fact 与冲突边界；不能只显示一方。

任何用户答案中的属性、关系、行为、业务或历史语义都必须由 Fact Proposition 或 Inference Conclusion 直接支持，不能由 Entity metadata、Evidence 原文或查询摘要补写。

## 11. INITIAL / UNCHANGED 与 Availability 边界

### 11.1 INITIAL

| 条件 | 要求 |
|---|---|
| Expected Current | `NO_CURRENT` |
| Target Schema | 本文 exact Schema Reference，Registry 状态为 `AVAILABLE_FOR_TARGET` |
| Base Snapshot | 不存在 |
| Allowed new knowledge | SOURCE_ANCHORED Entity、直接 Evidence 支持的 Fact |
| Disallowed | 本地 Inference、State Continuation、Migration、Disposition、Identity Lineage、Evolution Plan |
| Publication | exact Manifest 通过 Final Schema Target Validation 后执行单 Scope原子首发 |

### 11.2 UNCHANGED

| 条件 | 要求 |
|---|---|
| Expected Current | `PRESENT(exact Base Snapshot Reference)` |
| Target Schema | 与 Base Snapshot 的 Schema Reference 字节级完全相同 |
| Allowed new knowledge | 新/更新 Entity / Fact；以 Base / 已固定正式前提构建的 Inference；经审核 State Continuation |
| Complete target | Enrichment 从 Base 完整成员出发，或 Replacement 显式覆盖全部 Base disposition |
| Disallowed | Schema Adoption、跨 Schema解释、Migration、Identity Continuation Proof、隐式继承或静默删除 |
| Concurrency | CURRENT、Registry Availability / Revision、Identity unique key 和 Manifest Digest 在提交边界重验 |

### 11.3 Availability

Schema 首次注册必须在同一事务形成 `Availability Revision = 1, AVAILABLE_FOR_TARGET`。本切片不需要主动 Deprecation，但若执行，只允许单调进入 `DEPRECATED_FOR_NEW_TARGET`；历史 Snapshot 仍按 exact Schema Reference 解释。不得原地重新启用旧 Reference。

## 12. Canonicalization 与规范 Digest

`SWM-KNOWLEDGE-CANONICALIZATION@1` 至少固定：

1. Type / Enum / Role ID 使用本文 ASCII 字面值，区分大小写，不接受别名。
2. 已明确解码为文本的自然语言值使用 Unicode NFC、LF；不去除有语义的空白，不做翻译、词干化或同义改写。Artifact / Evidence 的原始 Git blob 与 Content Digest 始终保留 exact bytes，未验证编码的 bytes 不能被模型猜测成文本。
3. Git OID 使用 `{objectFormat}:{lowercaseFullOid}`；短 SHA 永不进入稳定键。
4. Repository-relative path 的稳定值是从 Git tree 逐段验证的原始 segment byte 序列；规范序列化使用长度前缀并保留 segment 顺序，不做 Unicode 归一化或宿主文件系统大小写折叠。`/` 只用于显示，绝对路径与未消解 `.` / `..` 拒绝进入稳定键。
5. Code Symbol Key 必须包含 language namespace、symbol kind、qualified container、canonical name 和 overload signature；缺项即 unresolved。
6. HTTP method 大写；path 保留 segment 顺序和模板变量，除重复分隔符外不猜测框架等价。
7. Typed Literal 必须固定类型、值、单位/精度（适用时）；字符串与数字不互相强转。
8. 无序集合按成员规范 Digest 排序；有序 Role、path part、step 和 parent ordinal 保留顺序。
9. Effective Entity / Fact / Inference Identity Key 分别产生 Semantic Identity Token；Candidate-local 与发布后稳定 ID 使用同一 Token 重算语义 Digest。
10. Definition、Candidate Closure、Admission Decision、Publication Manifest 和 Snapshot 分别使用其 Accepted Contract 的独立 Digest；不得复用一个摘要掩盖不同输入闭包。

<!-- END SCHEMA DEFINITION PAYLOAD -->

## 13. 明确排除项

本 Definition 不注册或暗示以下能力：

- DB、Log、Trace、Deployment、Runtime Observation 和文档空间 Provider。
- Environment / Deployment Context、跨来源版本映射或跨 Scope Context Correlation。
- Business Entity、INFERRED Entity、ENTITY_DERIVATION 或跨系统 Business Domain。
- Schema Adoption、Compatibility、Migration、Disposition、Identity Continuation 或 Evolution 状态机。
- Runtime 行为事实；代码声明的流程不能表述为“生产已发生”。
- 否定 Fact、开放世界完整性、来源投票、全局 Confidence 或 Conflict Winner。
- Semantic View、Projection、向量/图/搜索副本和物理 Cleanup。
- 数据库字段、类层次、API wire format、Prompt、模型阈值或项目专用 Builder。

遇到排除范围时必须返回不支持、Knowledge Gap 或 Application Limitation；不得降级为自由文本 Fact、模型记忆或直接来源答案。

## 14. WP-0 冻结与后续 Conformance 门禁

### 14.1 WP-0 文档冻结条件

本文进入 `Frozen for Iteration 001` 前只要求完成可由设计产物证明的事项：

1. **Definition Digest**：按第 2 节重算并回填，且任何 Payload 字节变化都会改变 Digest。
2. **Dependency Closure**：Local Git exact Profile Contract Digest 可重算，Context、Artifact / Payload、Locator 输入和 Source Interpretation ID 无悬空引用或循环依赖。
3. **Static Schema Closure**：Type / Rule / Obligation ID 唯一，引用可解析，INITIAL / UNCHANGED、Membership 与 Canonicalization 语义无静态矛盾。
4. **Conformance Catalog**：下列实现 Case 的输入、正反例和 Oracle 已定义；没有实现时状态保持 `NOT_EXECUTED`，不能用文档复核冒充 PASS。
5. **Adequacy Trace**：最小类型对 Structure、Behavior、History 与有正式依据时的 Business 用途存在明确表达路径；这只证明可表达性，不证明模型质量或产品任务通过。

### 14.2 首个实现消费者必须执行的 Case

以下 Case Catalog 随 Definition 一并冻结；WP-3 必须在 Schema Registration、Knowledge Admission 和 Publication 能力获得迭代可用资格前执行。涉及 Local Git Provider / Resolver 的前置 Case 由 WP-2 执行并引用 exact Conformance Result：

1. **Schema Registration**：Definition 闭合、Type ID 唯一、无引用环、注册与 Availability Revision 1 原子形成。
2. **Local Git Alignment**：Profile 无损提供第 4、5、6 节要求的 Source Context、Representation、Locator、Repository Identity 与 full OID；不能靠模型自报。
3. **Identity**：短 SHA、同名类、重载方法、路径移动、不同 Repository 同 OID 和不稳定 symbol 都失败关闭或 KEEP_UNRESOLVED。
4. **Fact**：每个 Fact Type 至少一个合法 direct-support 样例和一个隐藏前提 / Context 扩张反例；HTTP path composition 不越过机械规则。
5. **Inference**：INITIAL 中 Candidate Fact 不能成为前提；UNCHANGED 中 exact Base Fact 可以使用；Dependency DAG、modality propagation 与 Conflict 三项判断失败关闭。
6. **Admission**：所有适用 Obligation 双向覆盖；UNKNOWN / NOT_EVALUATED、Evidence 不可读、Digest 不闭合和模型资格失败均不能 ACCEPT。
7. **Snapshot**：INITIAL 并发首发、UNCHANGED exact Schema、完整 Member Manifest、局部引用替换前后语义 Digest、CURRENT CAS 和发布结果未知恢复。
8. **Product Adequacy**：在未见 Local Git 项目上验证至少一个 Structure、Behavior、History，以及有正式依据时的 Business 问题；不足必须创建新 Schema Definition，不能把缺失语义塞入自由字段。

Case Run 必须固定实现 Commit、本文 exact Schema Reference、Local Git Profile Contract Digest、Fixture Digest 和原始结果。任一失败阻止相应能力继续推进，不解冻或原地修改本文。

某个模型达到产品准确率、数据库选型、类设计或 Prompt 完成均不是 Schema 文档冻结条件；它们分别由 Capability Evaluation、实现与后续工作包验证。
