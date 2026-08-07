# Iteration 001 Local Git Provider-specific Contract Profile

| 元数据 | 值 |
|---|---|
| Profile ID | ITER-001-LOCAL-GIT-PROVIDER |
| Version | 0.1.0 |
| Status | Frozen for Iteration 001 |
| Profile Contract Digest | `sha256:d1eacb1e2c61c160c239b840cc84d660fef9fe282acd465358ae41f07bf76d1f` |
| Contract Canonicalization | `SWM-LOCAL-GIT-PROFILE-MARKDOWN-LF@1` |
| Implementation Plan | [SWM-IMP-ITER-001](../Implementation_Plan_Iteration_001.md) |
| Design Baseline | [SWM-DBM-ITER-001-REV-002](../../../detailed-design/governance/Design_Baseline_Manifest_Iteration_001_Revision_002.md) |
| Implementation Baseline | [SWM-IBM-ITER-001-REV-002](../Implementation_Baseline_Manifest_Iteration_001_Revision_002.md) |
| Knowledge Schema Consumer | [SWM-ITER-001-KNOWLEDGE-SCHEMA](ITER-001-Initial-Knowledge-Schema.md) |
| Shared Error Projection | [ITER-001-SHARED-ERROR-CLASSIFICATION](ITER-001-Shared-Error-Classification.md) |
| Governing Contracts | [DD-SRC-DATA-SOURCE@0.1.0](../../../detailed-design/topics/DD-SRC-DATA-SOURCE.md)、[DD-SRC-SOURCE-ARTIFACT@0.1.0](../../../detailed-design/topics/DD-SRC-SOURCE-ARTIFACT.md)、[DD-APP-KNOWLEDGE-UPDATE@0.1.0](../../../detailed-design/topics/DD-APP-KNOWLEDGE-UPDATE.md) |
| Applies To | WP-2 Local Git Source、WP-4 bounded Source Tool Loop |
| Retention Selection | `NO_EVICTION` |

> 本 Profile 是 Iteration 001 对已接受通用 Contract 的 Provider-specific 收窄，不是新的架构或详细设计主题。它不能放宽通用 Contract，也不进入 Design Baseline Manifest。实现若无法满足本文，应停止 Provider 准入或修订本 Profile；不得反向弱化已接受设计。

`Profile Contract Digest` 只覆盖下方两个标记之间的内容：UTF-8、LF、Unicode NFC，无 BOM、CRLF 或行尾空格；输入从 BEGIN 标记后的首字节开始，到 END 标记前一行的 LF 为止。状态、交叉链接和实施记录不进入规范摘要。

<!-- BEGIN LOCAL GIT PROFILE CONTRACT -->

## 1. 目的与选择边界

本 Profile 冻结首个纵向切片使用的 Local Git 来源语义，使实现和 Contract Conformance 能够对同一组可观察行为进行判断。它只选择：

- 单个本地、非 bare Git 工作树所对应的仓库；来源读取仅访问已提交 Git 对象。
- `list / search / read / compare` 四种只读 Tool。
- Repository Revision、Revision Comparison、Source Object 和 Java Symbol 的 canonical target。
- exact Git revision、路径、范围、覆盖、预算、错误和 `NO_EVICTION` 语义。

本 Profile 不选择：

- 工作树未提交内容、暂存区、stash、reflog、远程 fetch / pull、Git 托管 API 或任何写操作。
- linked worktree、bare repository、submodule 递归读取或 Git LFS 外部对象下载。Gitlink 与 LFS pointer 只能按父仓库已提交的原生条目 / blob 观察。
- `query / read-window`、正则表达式搜索、rename / copy 猜测、跨仓库比较或自动 merge-base 选择。
- Entity、Fact、Endpoint 或业务语义身份。Endpoint 文本只能作为 Target Proposal；若能唯一定位到代码声明，canonical target 仍是 exact Java Symbol。
- Provider 实现类、进程模型、数据库表、Git 库、CLI 命令或 Web 框架。

模型不拥有 Local Git Tool。模型只能提出 Tool Proposal；Application Services 完成授权后，由 Source Integration 构造并执行 Source Operation。

## 2. Provider、DataSource 与 Binding Profile

### 2.1 Provider 身份

| 项 | Iteration 001 选择 |
|---|---|
| Provider Type | `LOCAL_GIT` |
| Provider Contract | `LOCAL_GIT_PROVIDER_V1` |
| Identity Strategy | `LOCAL_GIT_IDENTITY_V1` |
| Artifactization Profile | `LOCAL_GIT_ARTIFACTIZATION_V1` |
| Object Formats | Git repository 声明的 `sha1` 或 `sha256`；不得按摘要长度猜测 |
| Side Effect | 全部 Tool 必须为只读 |

`LOCAL_GIT_IDENTITY_V1` 的 `Repository Identity Domain` 固定为 `(Local Workspace Domain ID, Canonical Source Target)`。规范化和序列化规则如下：

1. Workspace Domain ID 是平台分配的稳定不透明 ID，不使用主机名、用户名或显示标签代替。
2. 注册边界在该 Workspace Domain 内把输入目录绝对化、消解每个既存符号链接、移除 `.` / `..`，并解析 Git directory / worktree 关系得到非 bare 主工作树根；失败或越出 Workspace Domain 时不形成身份。
3. Canonical Source Target 是规范工作树根的原生 path bytes。不得执行 Unicode 归一化、大小写折叠或尾部分隔符保留；受限配置记录保存原值，普通日志和下游知识不披露它。
4. Canonical Tuple 使用下述 `SWM-LOCAL-GIT-TYPED-TUPLE@1`，按固定字段顺序编码 `tupleType=ENUM(REPOSITORY_IDENTITY_DOMAIN)`、`workspaceDomainId=ID`、`canonicalRootPath=BYTES`；禁止省略或 map 重排。
5. Source Integration 对该 Tuple 原子 get-or-create 永久 DataSource ID，并保存 `SHA-256(canonical tuple bytes)`。下游 `Repository Identity` 精确为该永久 DataSource ID；任何使用方都能经授权 Registry Record 回放到同一 Tuple 与 Digest。

Workspace Domain ID 单独不能充当 Repository Identity。远程 URL、仓库目录显示名、当前 branch、HEAD 值和 Git object ID 都不构成 DataSource 身份。

#### `SWM-LOCAL-GIT-TYPED-TUPLE@1` Canonical Byte Codec

每个值统一编码为 `one-byte tag + unsigned 64-bit big-endian payloadLength + payload`。Tag、Payload 和递归规则固定如下；任何非规范表示、未知 Tag、超长值或嵌套深度超过执行预算都失败关闭：

| Tag byte | 类型 | Canonical Payload |
|---|---|---|
| `00` | `ABSENT` | 长度必须为 0 |
| `01` | `ASCII` | 非空 7-bit ASCII bytes |
| `02` | `UTF8_NFC` | 合法 UTF-8 的 Unicode NFC bytes |
| `03` | `BYTES` | 原始 bytes，可为空 |
| `04` | `UINT64` | 长度 8；unsigned big-endian |
| `05` | `BOOL` | 长度 1；false=`00`，true=`01` |
| `06` | `INSTANT` | ASCII `YYYY-MM-DDTHH:MM:SS.nnnnnnnnnZ`；UTC、固定 9 位小数，不接受 offset 等价写法 |
| `07` | `ENUM` | 非空 `[A-Z][A-Z0-9_]*` ASCII bytes，区分大小写 |
| `08` | `ID` | 非空 `[A-Za-z0-9][A-Za-z0-9._:@/-]*` ASCII bytes；显示标签不是 ID |
| `09` | `DIGEST` | 长度 33；首字节 `01` 表示 SHA-256，随后为 32 个摘要原始 bytes |
| `0a` | `OID` | 首字节 `01=sha1 | 02=sha256`，随后分别为 20 或 32 个由完整小写 hex 解码的原始 bytes |
| `0b` | `TUPLE` | unsigned 32-bit big-endian memberCount，随后顺序拼接 memberCount 个完整 framed value |
| `0c` | `ORDERED_LIST` | 与 TUPLE 相同的计数 / framing；列表次序有语义，零成员合法 |

本 Profile 使用以下 exact 类型别名；别名只缩短表格，不引入新的编码：

| Alias | Exact framed shape |
|---|---|
| `ObjectFormat` | `ENUM(SHA1|SHA256)` |
| `GitPath` | `TUPLE(ENUM(ROOT),ABSENT)`，或 `TUPLE(ENUM(PATH),BYTES(non-empty canonical repository-relative path))` |
| `GitMode` | `ENUM(MODE_040000|MODE_100644|MODE_100755|MODE_120000|MODE_160000)` |
| `EntryKind` | `ENUM(TREE|BLOB|SYMLINK_BLOB|GITLINK)`；依次对应上述 tree、regular/executable、symlink 与 gitlink mode |
| `ByteRange` | `TUPLE(UINT64(startInclusive),UINT64(endExclusive))`，且 start ≤ end |
| `RevisionedId` | `TUPLE(ID(identity),UINT64(definitionRevision))` |
| `OptionalCursor` | `BYTES(non-empty opaque cursor)` 或 `ABSENT` |
| `QueryKind` | `ENUM(PATH_LITERAL|CONTENT_LITERAL)` |
| `ChangeKind` | `ENUM(ADDED|DELETED|MODIFIED|TYPE_CHANGED)` |

字段名不进入 bytes；Artifact Payload Schema、Locator Contract 等 exact 外壳已区分的 Tuple 由对应 Contract 固定字段顺序，未被外壳区分的独立身份 Tuple 必须以 `tupleType=ENUM(...)` 开头。Context identity 的摘要输入不是字符串拼接，而是 `TUPLE(ENUM(SOURCE_CONTEXT_IDENTITY), ID(vocabularyId), ID(canonicalizationId), TUPLE(contextExpression))` 的完整 framed bytes。显示用 `sha256:<lowercase hex>` 只在 codec 外表示 `DIGEST`。

Golden Fixture `LOCAL_GIT_CODEC_GOLDEN_001` 固定 `TUPLE(ENUM(REPOSITORY_IDENTITY_DOMAIN), ID(ws-1), BYTES(/repo))`：

- canonical bytes hex：`0b00000000000000420000000307000000000000001a5245504f5349544f52595f4944454e544954595f444f4d41494e08000000000000000477732d310300000000000000052f7265706f`
- SHA-256：`253b2563554f16b18a49be13bbae8db91d942212508c84519f56c80a06a00efc`

Golden Fixture `LOCAL_GIT_CODEC_GOLDEN_002` 固定 `TUPLE(OID(sha1, 20 zero bytes), UINT64(1), ORDERED_LIST(ABSENT, DIGEST(sha256, 32 zero bytes)))`：

- canonical bytes hex：`0b0000000000000073000000030a000000000000001501000000000000000000000000000000000000000004000000000000000800000000000000010c000000000000003700000002000000000000000000090000000000000021010000000000000000000000000000000000000000000000000000000000000000`
- SHA-256：`460500dd1db7238db77fdab6d21d1be8958648144f338c15cd468ee4d5392bc4`

所有 Repository Identity、Source Context、Payload 与 Locator Conformance 实现必须先通过该 Golden Fixture；不能使用语言对象序列化、JSON map 顺序或本地字节序代替此 codec。

Provider 在 DataSource 注册时只执行身份和路径边界所需的本地规范化，不读取提交内容。仓库存在性、布局、对象格式和具体 revision 的可读性由受控 Source Operation 验证。相同 Workspace Domain 与相同规范仓库根必须归并为同一永久 DataSource 逻辑键 / ID；路径移动视为新的 Canonical Source Target，不通过远程 URL 猜测为旧来源。

### 2.2 Provider Configuration

Provider Configuration Revision 至少固定：

- Local Workspace Domain ID 与规范 Repository Root Reference / Digest。
- 允许的仓库布局 `STANDARD_NON_BARE_WORKTREE`。
- 数据分类、允许读取的最大文件 /对象大小等 Provider hard-cap profile reference。
- object format 的验证结果；尚未完成首次受控验证时明确为 `UNVERIFIED`，不能猜测默认值。

配置不保存凭据值。仓库根变化、Workspace Domain 变化或仓库布局变化不能作为同一 Configuration Revision 原地覆盖；它们改变来源身份或兼容性。

### 2.3 Local Git Selector

Iteration 001 Selector 是一个非空的 canonical Git tree prefix 集合：

- prefix 是 repository-relative Git path；仓库根使用显式 `ROOT` 判别值，不用空字符串表达多个含义。
- 规范化结果移除 `.`、拒绝 `..`、绝对路径、NUL 和越过仓库根的表示。
- prefix 按 Git path byte order 排序；父 prefix 已存在时移除其冗余后代。
- 本版不支持 glob、regex、大小写折叠、`.gitignore` 解释或运行时动态 Selector。
- Git path 按提交树中的确切名称比较，不按宿主文件系统大小写、Unicode 或符号链接语义重写。

Git path 的 canonical serialization 必须无损编码原始 path bytes；面向人的 UTF-8 Display Label 不能参与身份、排序或包含判断，也不能把两个不可显示路径归并。

所有 path target、list root、search root、read object 和 compare 输出必须位于有效 prefix 内。Repository Revision / Comparison 可以作为发现根，但其内容覆盖只限 Selector；Provider 不能因目标相关而扩大到 Selector 外。Git tree 中的 symbolic link 作为 mode `120000` 的 blob 读取其链接文本，绝不跟随链接访问宿主文件系统。

## 3. Revision 与 Source Context

### 3.1 Revision 规范

`Canonical Git Revision` 只接受已验证为 `commit` 的完整 object ID：

`Git Object Format + Full Lower-case Object ID`

- branch、tag、`HEAD`、短 SHA 和人类描述只能作为 Target Proposal。
- Resolver 可以观察 ref 或 peel annotated tag，但成功 Receipt 必须记录 proposal、解析链 / observation、object format 和最终 exact commit ID。
- 短 SHA 只有在当前受控解析边界内唯一时才能解析；零个候选为 `NOT_FOUND`，多个候选为 `AMBIGUOUS`。
- 读取阶段永远使用 Receipt 中的 exact commit，不重新解析 branch、tag 或 `HEAD`。
- commit、tree、blob 和 gitlink object ID 不可互换；目标要求 commit 时不能接受 tree 或 blob。

DataSource Definition Revision、Binding Definition Revision、Provider Contract Version、Git commit ID、tree / blob object ID 和 Source Operation Revision 是不同维度，任何实现不得共用一个 `revision` 字段隐藏其含义。

### 3.2 读取基准

`list / search / read` 必须固定一个 exact commit。该 commit 的 root tree 是读取基准；Provider 不从 checkout 文件读取正文，因此工作树变更、当前 branch 切换或 sparse checkout 不改变同一请求的语义。

`compare` 必须固定 exact base commit 与 exact target commit。Provider 不自动选择 merge-base 或 first parent。`parent(target)` 只可作为解析 Proposal：目标恰有一个 parent 时解析为 exact comparison；零 parent 返回 `NOT_FOUND`，多个 parent 返回 `AMBIGUOUS` 并要求显式选择 base。

Source Context Vocabulary 固定为 `LOCAL_GIT_SOURCE_CONTEXT_VOCABULARY@1`，Canonicalization 固定为 `LOCAL_GIT_SOURCE_CONTEXT_CANONICALIZATION@1`。一个 Context 使用 `SWM-LOCAL-GIT-TYPED-TUPLE@1` 按下列顺序编码；可选项必须编码 typed `ABSENT`，不能靠字段省略：

| 字段 | Exact framed value |
|---|---|
| Repository Identity | `ID`；必须是 §2.1 的永久 DataSource ID |
| DataSource Definition Revision | `RevisionedId`；exact DataSource ID + Definition Revision |
| Binding Identity / Definition Revision | `RevisionedId`；exact Binding ID + Definition Revision |
| Provider Contract / Configuration | `TUPLE(ID(providerContractVersion),DIGEST(providerConfigurationFingerprint))` |
| Object Format | `ObjectFormat`；由仓库验证，不按 OID 长度猜测 |
| Read Revision | `OID(exact commit)` 或 `ABSENT`；list/search/read 使用 exact commit |
| Comparison Revision | `TUPLE(OID(base),OID(target),ID(TREE_CHANGESET_NO_RENAME_V1))` 或 `ABSENT` |
| Object Focus | `TUPLE(ENUM(TREE),GitPath,OID)`、`TUPLE(ENUM(BLOB),GitPath,OID,ByteRange)`、`TUPLE(ENUM(GITLINK),GitPath,OID)` 或 `ABSENT` |
| Observation Time | `INSTANT` |
| Observation Basis | `TUPLE(ENUM(OBSERVATION_RESULT),ID(resultReference),DIGEST(resultDigest))`，或 `TUPLE(ENUM(CLOSED_READ_SESSION),ID(sessionReference),DIGEST(sessionDigest),ORDERED_LIST(DIGEST(memberObservationDigest)))` |

单次 Observation 使用其完成观察时间。CLOSED Read Session 若仅作为 Operation / Observation Set Basis，Session close observation time 是外层 Source Context 的 Observation Time，各成员真实观察时间仍保留在有序 Basis 中，不被覆盖或改写。

Context Expression 是按表中十行顺序组成的一个 `TUPLE`。Context identity key 为该 Tuple 按 codec 规则包入 `(SOURCE_CONTEXT_IDENTITY, vocabularyId, canonicalizationId, contextExpression)` 后的 SHA-256；Repository 原子 get-or-create 并保存完整表达与 Basis。Ref 名称、短 SHA、工作树状态和模型标签只能留在 Target Resolution Provenance，不进入正式读取 Source Context。Artifact、Locator 与下游 KnowledgeContext 消费的 Repository Identity、OID、path bytes 必须逐值等于该 Context，不能靠显示字符串关联。

## 4. Canonical Target Profile

### 4.1 支持的 Target Kind

| Target Kind | Canonical Identity 最低闭包 |
|---|---|
| `REPOSITORY_REVISION` | exact DataSource / Binding Definition Revision + object format + full commit ID |
| `REVISION_COMPARISON` | 同一 DataSource / Binding 下 exact base commit + exact target commit + `TREE_CHANGESET_NO_RENAME_V1` |
| `SOURCE_OBJECT` | exact commit + canonical Git path + expected tree entry kind + exact tree / blob / gitlink object ID |
| `JAVA_SYMBOL` | exact commit + canonical source path + `JAVA_SYMBOL_V1` + containing type identity + member kind + normalized declaration signature + declaration range / digest |

Target Identity 同时绑定 Provider / Resolver Contract Version 和 Target Resolution Receipt Digest。Display Label、branch、tag、短 SHA、模块昵称、简单类名、方法名或 URL path 不参与身份。

### 4.2 Path 与对象

Canonical Git path 是从 commit root tree 开始、由实际 tree entry 名称逐段验证得到的 repository-relative path。路径 proposal 不按工作树路径“修复”大小写，也不跟随 symbolic link。不存在、类型不符或 Selector 外的路径不能形成 `EXACT` Receipt。

`SOURCE_OBJECT` 的 expected kind 只区分 `TREE | BLOB | SYMLINK_BLOB | GITLINK`。本版可以列举和比较 GITLINK，但不进入子模块；读取 GITLINK 只返回父仓库记录的 object ID / mode 观察，不读取另一个仓库。

### 4.3 Java Symbol

Java Symbol Resolver 只解析 exact commit 中 exact `.java` Source Object：

- canonical identity 必须包含源路径和 containing type chain，避免跨模块同 FQN 或同名 Controller 合并。
- 方法 /构造器必须包含 member kind、名称和规范化声明参数类型序列；重载不能只用名称区分。
- Receipt 固定 `JAVA_SYMBOL_V1`、解析所用 Source Artifact / content digest、声明 byte range 和 declaration digest。
- 无法唯一解析 import、嵌套类型、重载或生成源码时返回 `AMBIGUOUS | UNSUPPORTED`，不能选择第一个候选。
- Annotation / URL 搜索可以产生候选 Java Symbol；单独 Endpoint 文本不成为新的 Provider target kind。

Java Symbol Resolution 只证明来源定位，不证明该符号是正式 Entity、实现某个 Endpoint 或支持某项业务规则。

### 4.4 Resolution 与发现边界

只有 `SRC-TARGET-RESOLUTION-01` 的 `EXACT` Receipt 能进入 Canonical Build Target。Receipt 必须绑定 exact Source / Binding / Provider Revision、Selector、Canonical Target、解析观察和 Digest。

Iteration 001 的机械后代关系为：

- `REPOSITORY_REVISION` 的后代是同一 commit、Selector 内的 Source Object / Java Symbol。
- `REVISION_COMPARISON` 的后代是该 exact base / target change set 中、Selector 内的 changed Source Object，以及其两侧 exact 对象 /符号。
- `SOURCE_OBJECT` 的后代只能是该对象内的 Java Symbol 或有界 byte / line range。
- Java Symbol 没有可隐式扩大到其他文件的后代。

发现新对象不会修改 Build Intent。超出上述关系、Selector、允许 Target Kind、深度或数量边界时返回 `OUT_OF_SCOPE`，由 Application Services 决定是否建立新的 Build Intent。

## 5. Tool Contract Profile

### 5.1 共同请求与结果

四个 Tool 都必须消费通用 Contract 要求的 exact DataSource / Binding Revision、`SOURCE_EXECUTION` Scope State Assertion、Binding Eligibility Assertion、Capability Catalog / Tool inclusion、Provider Registry Revision、Execution Envelope、parent Resource Allocation 和 Data Classification。

每个 Tool Request 还必须固定：

- 普通调查固定 exact Canonical Target / Resolution Receipt，或能够机械证明位于 frozen descendant discovery boundary 内的目标。
- Target Resolver 自身需要来源观察时，固定 exact Target Resolution Attempt、原始 Proposal Digest、已解析 canonical parent target 和有界候选 /搜索边界；Resolver Step 不要求尚未形成的最终 Receipt，但不能越过 DataSource、Binding、Selector 或 parent target。
- canonical parameters、Selector / Access Boundary Proof、Provider hard-cap revision 和有限预算。
- Owner Idempotency Key 与 canonical Request Digest。

结果必须区分 `COMPLETE | PARTIAL | FAILED | CANCELED | REVOKED_WITH_INFLIGHT | BUDGET_EXHAUSTED`，并报告实际 Coverage、未读范围、Pagination / Cursor、Truncation、Usage、稳定错误类别和 Observation / Artifact Reference。`PARTIAL`、空结果和预算耗尽永远不能解释为完整不存在。

Cursor 必须绑定 Tool Contract、exact revision / comparison、canonical parameters、Selector 和原 Request Digest；Cursor 不能跨 Revision、Binding 或查询复用。

list / search / compare 需要跨页时必须建立符合 `SRC-READ-SESSION-01` 的冻结 Read Session Definition。每页使用独立 Dispatch Attempt / Observation 和 child Allocation；只有 Cursor 链连续、排序稳定、没有缺口且到达终止条件的 Session Result 才能声明 Session 完整 Coverage。Iteration 001 只把单页 Observation 形成页级 Artifact，不把多页 Session 聚合成另一种 Payload；最后一页也不能伪装成全量 Artifact。完整零项 `LOCAL_GIT_QUERY_OBSERVATION / 1` 只允许单次 search 从无 start cursor 扫描至 terminal、无 next cursor 且无截断时形成；分页零项只保留 CLOSED Session Result，不 Artifactize。

### 5.2 `list`

`LOCAL_GIT_LIST_V1` 列举 exact commit 中一个 canonical tree target 的直接子项：

- 输入固定 tree path、`maxEntries`、`maxReturnedBytes` 和可选 continuation cursor。
- 本版每次只列直接子项；递归通过新的、有界 list step 完成，不能使用隐式 unlimited depth。
- 输出按 Git path byte order 稳定排序，逐项返回 canonical path、entry name、mode、kind 和 exact object ID。
- 成功走到 tree 末尾且没有截断时才声明该 tree 的 direct-child Coverage complete。
- tree 为空且完整读取时可以形成信息载体；路径不存在、不是 tree 或越界时不形成空 listing Artifact。

### 5.3 `search`

`LOCAL_GIT_SEARCH_V1` 只支持两种确定性查询：

- `PATH_LITERAL`：在 Selector 与 canonical search root 内，对 canonical Git path bytes 做非空、大小写敏感的 literal 匹配。
- `CONTENT_LITERAL`：对 blob 原始 bytes 做非空 literal 匹配；输入 UTF-8 文本按其确切 bytes 编码，不做 Unicode 归一化、大小写折叠或 regex 扩展。

请求固定 exact commit、search root、query kind / bytes digest、`maxScannedTreeEntries`、`maxScannedObjects`、`maxScannedBytes`、`maxMatches`、`maxReturnedBytes` 和可选 cursor。结果按 canonical path、随后 byte offset 稳定排序；match 至少返回 Source Object identity、byte offset、matched digest 和有界 preview range / digest。preview 仅用于定位，正式读取使用 `read`。

Search Coverage 必须记录实际扫描对象 / bytes、未扫描范围和跳过的非-blob object kind。只有扫描完冻结 search root 内全部适用 blob / path 且无截断时，零匹配才可形成完整 Query Observation Artifact；否则只能表达“已扫描范围内未发现”。

### 5.4 `read`

`LOCAL_GIT_READ_V1` 支持：

- 读取 exact commit metadata：commit ID、tree ID、完整 parent IDs、author / committer observation 和 message bytes。
- 读取 exact blob / symlink blob 的 whole content、canonical byte range 或 line range。
- 读取 GITLINK 的父仓库 entry metadata；不递归读取子模块。

Canonical read target 固定 exact object ID。Whole content 只有在 `maxReturnedBytes` 内才允许；超限返回 `PAYLOAD_TOO_LARGE`，不得静默截断。Byte range 使用半开区间；line range 由 Provider 依据确切 blob 解析为 byte range，并在结果中同时记录原 line range、resolved byte range 和 content digest。换行识别只以 LF 为边界，CR 作为内容保留。

成功 read 必须返回请求范围的全部 bytes；无法完整返回时为 `PARTIAL | FAILED`，并且不能产生冒充完整范围的 Artifact。

### 5.5 `compare`

`LOCAL_GIT_COMPARE_V1` 比较同一 DataSource 中 exact base / target commit 的 tree：

- canonical comparison contract 为 `TREE_CHANGESET_NO_RENAME_V1`；不执行 rename / copy detection。
- 输出只包含 `ADDED | DELETED | MODIFIED | TYPE_CHANGED`，并固定 canonical path、old / new mode、old / new object ID。
- change entries 按 canonical path byte order 稳定排序，并由 Selector 与可选 canonical subtree 过滤。
- 请求固定 `maxScannedTreeEntries`、`maxScannedObjects`、`maxChangedEntries`、`maxReturnedBytes` 和可选 cursor。
- Iteration 001 compare 不返回或 Artifactize textual hunk；需要内容差异时，调查流程对 exact old / new blob 发起有界 `read`。引入 hunk 必须升级 Provider Profile、Payload Schema 与消费它的 Knowledge Schema。

只有 change entry enumeration 到达终点且无缺口时，change-set Coverage 才 complete。分页或扫描预算耗尽不能宣称 revision comparison 已完整调查。merge commit 不触发隐式 parent 选择；base 必须已经 canonicalize。

## 6. Artifactization 与 `NO_EVICTION`

### 6.1 Artifact Kind 与 Payload Schema Registry

成功且承载来源信息的 Observation 只能按 `LOCAL_GIT_ARTIFACTIZATION_V1` 形成下表注册项。`Artifact Kind / Schema Version` 与 `Payload Schema` 是两个独立版本轴；Tool ID 不能充当 Payload Schema。

| Tool / Observation | Artifact Kind / Schema Version | Payload Schema | Media Type | Exact Payload Tuple（固定顺序） |
|---|---|---|---|---|
| list page | `LOCAL_GIT_TREE_LISTING / 1` | `swm.payload.local-git.tree-listing@1` | `application/vnd.swm.local-git.typed-tuple` | `TUPLE(ID(repository),ObjectFormat,OID(commit),GitPath(tree),OID(tree),ORDERED_LIST(TreeEntry),Coverage)` |
| search non-empty result | `LOCAL_GIT_SEARCH_MATCH_SET / 1` | `swm.payload.local-git.search-match-set@1` | 同上 | `TUPLE(ID(repository),ObjectFormat,OID(commit),GitPath(searchRoot),QueryKind,BYTES(non-empty query),ORDERED_LIST(SearchMatch)[1..n],Coverage)` |
| search complete zero result | `LOCAL_GIT_QUERY_OBSERVATION / 1` | `swm.payload.local-git.query-observation@1` | 同上 | `TUPLE(ID(repository),ObjectFormat,OID(commit),GitPath(searchRoot),QueryKind,BYTES(non-empty query),UINT64(0),Coverage(completeness=COMPLETE))` |
| read commit | `LOCAL_GIT_COMMIT_OBSERVATION / 1` | `swm.payload.local-git.commit-observation@1` | 同上 | `TUPLE(ID(repository),ObjectFormat,OID(commit),OID(tree),ORDERED_LIST(OID(parent)),BYTES(authorField),BYTES(committerField),BYTES(message),Coverage)` |
| read blob / range | `LOCAL_GIT_BLOB_OBSERVATION / 1` | `swm.payload.local-git.blob-observation@1` | 同上 | `TUPLE(ID(repository),ObjectFormat,OID(commit),GitPath(path),EntryKind,OID(blob),UINT64(totalLength),UINT64(returnedStart),UINT64(returnedEnd),BYTES(content),Coverage)` |
| compare page | `LOCAL_GIT_TREE_CHANGESET / 1` | `swm.payload.local-git.tree-changeset@1` | 同上 | `TUPLE(ID(repository),ObjectFormat,OID(baseCommit),OID(targetCommit),GitPath(subtree),ORDERED_LIST(ChangeEntry),Coverage)` |

Payload 使用 `SWM-LOCAL-GIT-PAYLOAD-CANONICALIZATION@1`：

1. 采用 §2.1 的 `SWM-LOCAL-GIT-TYPED-TUPLE@1`；字段名和顺序由上表及下列成员结构固定。只有 codec 表注册的 Tag 合法；未知字段或 Tag 失败关闭。
2. `OID` 编码 object format 与从完整小写 hex 解码的原始摘要 bytes；同一 Payload 的每个 OID format 必须等于顶层 `ObjectFormat`。Git path 使用 `GitPath`；原始 blob、commit message 和 author / committer field 不执行文本归一化。Blob 的 `returnedEnd - returnedStart` 必须等于 content bytes 长度，且 `returnedEnd ≤ totalLength`。
3. `TreeEntry = TUPLE(GitPath(path),BYTES(non-empty entryName),GitMode,EntryKind,OID(object))`，按 path 的 raw bytes 排序；mode 与 kind 必须符合 Alias 映射。
4. `SearchMatch = TUPLE(GitPath(path),OID(blob),UINT64(start),UINT64(end),DIGEST(matchedContent),UINT64(previewStart),UINT64(previewEnd),DIGEST(previewContent))`，按 path raw bytes、start 排序；两个 Range 都在 exact blob 内，match Range 位于 preview Range 内。
5. `ChangeEntry = TUPLE(UINT64(ordinal),ChangeKind,GitPath(before)|ABSENT,GitPath(after)|ABSENT,GitMode(before)|ABSENT,GitMode(after)|ABSENT,OID(before)|ABSENT,OID(after)|ABSENT)`。排序键精确为 `after path`（present 时），否则为 `before path`，按 raw bytes 排序后从 0 连续分配 ordinal；ADDED 只允许 after，DELETED 只允许 before，MODIFIED / TYPE_CHANGED 两侧 path 必须相等，本版本不表达 rename。
6. `Coverage = TUPLE(DIGEST(canonicalRequestBoundary),DIGEST(effectiveSelector),OptionalCursor(start),OptionalCursor(next),UINT64(scannedTreeEntries),UINT64(scannedObjects),UINT64(scannedBytes),UINT64(returnedItems),UINT64(returnedBytes),ORDERED_LIST(EntryKind skipped，按 Enum bytes 排序),ENUM(RESULT_LIMIT|BYTE_LIMIT|SCAN_LIMIT|TIME_LIMIT|PROVIDER_HARD_CAP|BUDGET_EXHAUSTED)|ABSENT,BOOL(reachedTerminal),ENUM(COMPLETE|PARTIAL))`。`canonicalRequestBoundary` 是 §5.1 canonical Tool Request 中 target、parameters 与 budget boundary Tuple 的 Digest，不是显示文本。`COMPLETE` 必须同时满足 reachedTerminal=true、next Cursor=ABSENT、truncation reason=ABSENT；否则只能是 `PARTIAL`。returnedItems 必须等于 Payload 成员数量或单对象读取计数。单次 read / commit 与不分页操作的两个 Cursor 均为 typed `ABSENT`。本版本没有 Closed Session Payload 变体。
7. Payload Content Digest 为 `SHA-256(exact canonical payload bytes)`。Artifact shell 还必须固定 Artifact Kind / Schema Version、Payload Schema、Media Type、Source Context Reference、Observation Basis、实际 Coverage Digest、Tool / Profile / Identity Strategy Version 和 Data Classification；这些 shell 字段不因 Payload 内已有同值而省略。
8. Blob range Artifact 的 `blobOid` 来自 Git tree/object 校验，但局部 `contentBytes` 只对 `returnedStart..returnedEnd` 负责；重放时重验 exact blob identity、固化范围和范围 Content Digest，不要求用局部 bytes 重算完整 Git blob OID。Whole-blob Artifact 才能从完整 bytes 重验对象摘要。

Operation 的失败、预算和调度状态留在 Source Operation Result，不单独形成 Artifact。`PARTIAL` Observation 只有在 Payload 与 Coverage 如实有界且仍承载信息时才能形成页级 Artifact；它不能产生完整性或零项语义。模型不能生成或改写 Source Artifact Payload。

本 Profile 只持久化本次有界 Observation 的 Payload，不镜像完整仓库。相同 Git blob bytes 可以物理去重，但不同 Source、commit、path、Context 或 Observation 不能因此合并为一个逻辑 Artifact。

### 6.2 Source Interpretation Contract

下列 ID 是本 Profile 内部、由本 Profile Contract Digest 一并冻结的解释契约，不是外部未解析依赖。它们只固定首切片允许的输入、规范输出与失败边界，不指定实现类或要求所有步骤都由规则代码完成。模型可以提出解释结果，但平台必须保存 exact 输入范围和规范输出，Knowledge Verifier 必须独立重建或复核；任何未覆盖、歧义或不支持输入均失败关闭。

| Contract ID | 允许输入 | 规范输出 | 失败关闭边界 |
|---|---|---|---|
| `SWM-LOCAL-GIT-TYPED-OBSERVATION@1` | §6.1 已注册的冻结 Payload 与单个 field / entry / range | 对 exact selected typed value 使用 `SWM-LOCAL-GIT-TYPED-TUPLE@1`；raw bytes 保真 | Payload Schema、字段、ordinal、range、Digest 或 Coverage 不匹配 |
| `JAVA_SYMBOL_V1` | strict UTF-8、语法完整的 `.java` blob 内一个完整 type / field / method / constructor declaration；identifier / signature 位置含未展开 Unicode escape 时不支持 | `(sourcePathBytes, containingTypeChain, symbolKind, canonicalName, signatureDescriptor, declarationStartByte, declarationEndByte, declarationDigest)`；method / constructor descriptor 为按源码声明顺序的参数类型 token，去除 annotation、modifier、parameter name 与非语义空白，varargs 规范为 array，保留泛型/数组结构 | declaration 不完整；containing chain、kind、名称或 overload descriptor 不唯一；依赖生成源码或猜测 FQN |
| `JAVA_RELATION_OBSERVATION_V1` | `JAVA_SYMBOL_V1` 范围内完整 declaration、import、extends / implements 或 expression node | `(subjectSymbolOrSourceUnit, relation, objectSourceIdentifier, sourceRange)`；只承载源码显式 token | object 无法在同 commit / repository 唯一解析、动态 dispatch 或框架隐式关系 |
| `JAVA_HTTP_MAPPING_V1` | 完整 Java declaration 上可唯一解析的 Spring MVC 或 Jakarta/JAX-RS mapping annotation，method/path/condition 均为源码字面量 | `(handlerSymbol, protocol=HTTP, operation, orderedPathFragment, orderedLiteralConditions, sourceRange)`；type 与 method fragment 分开保留 | annotation type 多义、属性为表达式/常量引用、默认或配置替换才能得值、组合超过 type+method 两段 |
| `JAVA_EXECUTION_OBSERVATION_V1` | 一个方法/构造器内完整 invoke、if/switch condition、return、throw 或直接配置访问 expression/statement node | `(ownerSymbol, lexicalStepPath, operation, targetOrLiteralOrAbsent, conditionOrAbsent, sourceRange)` | 目标多义、跨方法运行顺序、异常传播、反射/框架行为或隐含副作用需要推理 |
| `MAVEN_POM_MODULE_ROOT_V1` | strict UTF-8、禁用 DTD /外部实体、根元素 local-name=`project` 的完整 `pom.xml` | `moduleRootPath = parent(canonical pom path)`，仓库根为 `ROOT` | XML 非法、路径 basename 非 `pom.xml`、根元素不符或来源范围不完整 |
| `MAVEN_DEPENDENCY_COORDINATE_V1` | 上述 POM 中一个完整 `<dependency>`，直接子元素文本为无子 markup 的字面量 | `(groupId,artifactId,typeOrJar,classifierOrAbsent,declaredVersionOrAbsent,scopeOrCompile)`；trim XML character whitespace，不解析 property / inheritance / profile | groupId/artifactId 缺失，`${...}`、实体、继承补值、重复字段或多义 namespace |
| `UTF8_SIMPLE_PROPERTIES_V1` | strict UTF-8 文件中的单行 `key=value` 或 `key:value`；key 仅 `[A-Za-z0-9_.-]+`，不支持 continuation / escape | `(sourcePathBytes,canonicalKey,valueKind,nonSecretTypedValueOrAbsent,sourceRange)`；key 原样，value 仅作 string / number / boolean / null 的无歧义字面量分类 | 动态/重复解析、转义、续行、结构值、编码非法或 Secret /疑似凭据值试图进入输出 |
| `SOURCE_STATEMENT_V1` | commit message field，或 blob 中一个完整连续 document / comment statement | `(declarer,statementRole,exactStatementText,targetOrAbsent,sourceRange)`；role 只允许 PURPOSE / RESPONSIBILITY / BUSINESS_RULE / CHANGE_RATIONALE | 角色仅由上下文猜测、文本被改写/拼接、target 未在同 Evidence 唯一出现；语义复核不通过 |

这些 Interpretation Contract 的 Conformance Fixture 必须覆盖每个允许子集至少一个正例、歧义/不完整/表达式输入反例及规范 Tuple 重算；Fixture 在对应 Resolver、Evidence Materializer 或 Knowledge Verifier 的首个实现消费者退出前执行。新增 Java 语法、框架 annotation、Maven effective model、YAML、跨文件配置 owner 或语言类型时必须创建新 Profile Version，不能扩大 `V1`。

### 6.3 `NO_EVICTION` 选择

Iteration 001 固定：

- Source Integration 只提供 Artifact / Payload 创建与读取，不注册 Archive、Evict 或 Physical Delete 命令。
- 已形成 Artifact 的有界 Observation payload、Artifact 外壳、Digest、Context 和最低审计保持可读；真实存储故障明确返回 `UNAVAILABLE`，不能伪装为淘汰。
- `OpenArtifactRead` 返回 `Read Protection = NOT_REQUIRED_NO_EVICTION`，不创建 Guard Record、Retention Coordination Record、后台清理器或 Store History 状态机。
- Git repository 本身仍是外部来源；`NO_EVICTION` 不承诺尚未观察的 commit 永远不会被外部 GC /替换。exact revision 在 Artifact 形成前消失时失败关闭，不改读 branch 当前值。
- Evidence 仍必须保存自包含最小观察快照；`NO_EVICTION` 不允许正式知识长期依赖 Artifact Payload，也不创建 Snapshot → Artifact Hold。

## 7. 预算、计量与停止语义

### 7.1 冻结的预算维度

任何 Local Git Source Operation 都必须携带有限、正值预算；不存在 unlimited、空值代表默认全仓库或模型申请扩容。Provider 至少计量：

- physical dispatch count、Source Tool Step count 和 compare count。
- scanned object count、scanned uncompressed blob bytes 和 tree entry count。
- returned item / match / changed-entry count 与 returned payload bytes。
- distinct Source Object / Artifact count。
- operation wall time、并发和 Artifactization payload bytes。

Tool-specific limit 按 §5 固定。实际生效预算是 Application parent / child Allocation、Source Operation Request limit 与 Provider hard cap 的逐维最小值；三者的 exact Revision / Digest 都进入 Request / Result。数值阈值由版本化 Resource Policy 与 Provider hard-cap profile 提供，本文件不凭静态设计臆造统一数值。

失败、取消、撤权竞态、重复和 `OUTCOME_UNKNOWN` 已发生的真实扫描 /返回用量均单调结算，不能按零处理。分页和重试取得新的不重叠 child Allocation；模型 Proposal 中的成本声明没有授权效力。

### 7.2 预算耗尽

- list / search / compare 在稳定分页边界耗尽时返回 `PARTIAL | BUDGET_EXHAUSTED`、可信 Cursor、已覆盖与未覆盖范围。
- read 的请求范围若超过可用返回预算，分派前返回 `PAYLOAD_TOO_LARGE`；若 I/O 后异常中断，只报告实际 partial bytes，不生成完整 Artifact。
- Application Services 把预算耗尽写入 Investigation Outcome 和 Target Coverage；不得扩大 Selector、切换 Revision、自动全仓扫描或宣称 REQUIRED Target 完成。
- 同一 Canonical Action Key 在无新 Cursor、Target、权限 Revision 或明确暂态失败依据时重复，按 `SOURCE_TOOL_NO_PROGRESS` 停止。

## 8. 错误与重试分类

Provider 原始诊断必须映射到以下稳定平台语义；实现可以保留附加内部诊断，但不能改变外部分类：

| Local Git 条件 | 平台语义 | 自动处理边界 |
|---|---|---|
| 路径不是受支持仓库、bare / linked-worktree layout | `PROVIDER_NOT_AVAILABLE` | 确定失败；修正 DataSource 或更换 Provider |
| branch / tag / short SHA 无候选 | `SOURCE_TARGET_NOT_FOUND` | 不改读 HEAD 或相近 revision |
| short SHA、多 ref、merge parent 或 Java Symbol 多候选 | `SOURCE_TARGET_AMBIGUOUS` | 返回有界候选与消歧字段；不选第一项 |
| object type、target kind、Java 解析或跨仓库 compare 不支持 | `SOURCE_TARGET_UNSUPPORTED` | 确定失败；不能降级成自由文本目标 |
| path / symbol / discovered target 越过 Selector | `SOURCE_TARGET_OUT_OF_SCOPE`；分派时为 `ACCESS_BOUNDARY_UNPROVEN` | 不读取、不扩大 Selector |
| exact path 不存在或 kind 不符 | `SOURCE_TARGET_NOT_FOUND` | 不做大小写修复或工作树回退 |
| query 为空、非法或使用 regex /不支持语义 | `SOURCE_QUERY_INVALID` | 调用方在原边界内提交新 Proposal |
| exact object 在解析后消失、object ID /内容不一致或仓库损坏 | `SOURCE_REVISION_INCONSISTENT` | 隔离当前 Observation；不替换为最新 revision |
| 本地仓库暂不可读或受控 I/O 暂态失败 | `SOURCE_UNAVAILABLE` | 仅在 exact 输入、剩余预算和 Policy 允许时新建 Dispatch Attempt |
| whole read 或请求范围超过有效上限 | `PAYLOAD_TOO_LARGE` | 缩小显式范围；不静默截断 |
| list / search / compare 未完成 | `SOURCE_PARTIAL / TRUNCATED` | 保留 Coverage / Cursor；不能作为完整否定依据 |
| Scope / Binding /权限 /Fence 失配 | `SCOPE_ASSERTION_INVALID / BINDING_ELIGIBILITY_STALE / EXECUTION_REVOKED` | 不建立新 Grant；不得由 Provider 自行刷新 |
| 预算耗尽或无进展重复 | `RESOURCE_EXHAUSTED / SOURCE_TOOL_NO_PROGRESS` | 受控停止；模型不能扩容 |
| 取消后仍有已分派调用 | `REVOKED_WITH_INFLIGHT / OUTCOME_UNKNOWN` | 先按原 Dispatch / Operation 收口；不创建替代成功 Result |

只有 `SOURCE_UNAVAILABLE` 等明确暂态错误可在相同 canonical Request 语义与剩余预算内重试。目标歧义、不存在、越界、查询非法、对象不一致和预算耗尽不能通过盲重试改变结论。每次真实重试使用新的 Dispatch Attempt 和 child Allocation，同时保留原 Attempt。

## 9. 最低 Conformance 与待验证项

### 9.1 Contract Conformance Case Catalog

WP-0 冻结以下 Case 及机械 Oracle；没有 Provider 实现时不伪造 Run 或 PASS。WP-2 必须在 Local Git Provider / Resolver 获得迭代可用资格前执行全部适用 Case，固定实现 Commit、Profile Contract Digest、Git Adapter 和 Fixture Digest。失败阻止该能力继续推进，并通过新 Profile Version 修订契约；不能原地改写已冻结 `V1`。

1. 相同 Workspace Domain /规范仓库根归并；符号链接别名不能创建第二个 DataSource，Selector 不能越过仓库根。
2. branch / tag 在解析后变化不改变已签发 exact Receipt；短 SHA 唯一、多义和不存在分别得到 `EXACT / AMBIGUOUS / NOT_FOUND`。
3. merge、root commit 和 shallow history 不触发隐式 comparison base；只有 exact base / target 进入 compare。
4. Git path 大小写、Unicode 名称、symlink、gitlink 和同路径名按 commit tree 语义处理，不读取工作树或子模块。
5. list / search / compare 的稳定排序、分页 Cursor、Coverage 和预算耗尽可以回放；空 partial 结果不能成为完整否定观察。
6. read whole / byte range / line range 与 exact blob digest 一致，超限不静默截断。
7. compare 不做 rename 猜测；add + delete、type change、merge base 显式性和 old / new object ID 符合本 Profile。
8. Java 同名类、跨模块同 FQN、重载方法、嵌套类型和多个 Endpoint annotation candidate 不能错误归并。
9. Tool Proposal 缺少 exact Scope Assertion、Binding Eligibility、Allocation、Target Receipt /已授权 Target Resolution Attempt Binding 或 Access Boundary Proof 时不能 dispatch。
10. `NO_EVICTION` 下不存在 Archive / Evict / Physical Delete / Guard 写入口；Artifact Read 使用 `NOT_REQUIRED_NO_EVICTION`，Evidence 仍自包含。
11. 模型运行环境不能直接访问 Local Git、文件系统、shell 或 Provider Tool；每次读取都能回放到 Application Authorization 与 Source Operation。

### 9.2 实现验证后才能确定的参数

以下项目不改变本文 Contract，但必须在对应 CC /负载 Fixture 中取得证据，并在启用的 Resource Policy / Provider hard-cap Revision 中固定：

- 代表性仓库上 `maxScannedObjects / Bytes`、返回 bytes、match / change-entry 数、单文件 range 和 wall-time 的数值阈值。
- sha256-object-format 仓库在所选 Git Adapter 中的真实支持程度；不支持时 Provider Registration 必须明确拒绝，不能按 sha1 运行。
- 大仓库 search 的分页 Cursor 与稳定扫描顺序能否在预算内恢复，而不依赖工作树索引或未声明缓存。
- Java Symbol Resolver 对多模块、嵌套类型、泛型签名和不完整源码的 `EXACT / AMBIGUOUS / UNSUPPORTED` 质量。
- `NO_EVICTION` 下有界 Observation payload 的存储增长、物理去重收益和容量告警；真实压力只能触发后续 Retention 设计，不能在本切片偷偷增加淘汰。

若上述验证发现 Provider 无法保持 exact revision、Selector、Coverage、预算或无旁路读取边界，应阻止 Local Git Provider 进入 WP-2，而不是以 Demo 特例、全仓库预装载或直接 Agent 读取绕过。

## 10. Profile 不变量

1. Local Git DataSource 身份、DataSource Definition Revision、Binding Revision 和 Git Revision 永不混用。
2. 生产读取只针对 exact committed Git object；工作树和动态 ref 不进入 Source Artifact。
3. short SHA、branch、tag、路径片段、简单符号名和 Endpoint 文本都不能直接成为 Canonical Build Target。
4. 四个 Tool 只执行平台授权的有界只读操作；Provider、模型和 Adapter 都不能扩大 Selector 或预算。
5. compare 的 base / target 显式且 exact；本版不推断 merge-base、rename 或跨仓库对应关系。
6. Coverage、Cursor、Truncation、预算和错误是 Result 语义，不被模型文本覆盖。
7. Source Artifact 只承载真实 Observation；Operation 状态不伪装成 Artifact，Artifact 不伪装成 Evidence。
8. `NO_EVICTION` 不创建空 Retention 机制，也不减轻 Evidence 自包含义务。
9. 新 Provider 能力若需要改变 target identity、Tool observable semantics、预算单位或错误分类，必须建立新 Profile Version；不能静默修改 `V1`。

<!-- END LOCAL GIT PROFILE CONTRACT -->
