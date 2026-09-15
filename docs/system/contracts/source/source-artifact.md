---
id: SYS-CONTRACT-SOURCE-ARTIFACT
kind: system-contract
status: current
authority: normative
owners: [source]
depends_on: [SYS-CONTRACT-SOURCE-DATA-SOURCE, SYS-CONTRACT-X-CAPABILITY-EXECUTION, SYS-ADR-018]
derived_from: [DD-SRC-SOURCE-ARTIFACT, FINDING-010-108, FINDING-010-110, FINDING-010-112, FINDING-010-155, FINDING-010-172, FINDING-010-182, FINDING-010-200, FINDING-010-202, FINDING-010-217, FINDING-010-218, FINDING-010-223, FINDING-010-226]
code: [src/software_world_model/source_integration/operations.py, src/software_world_model/source_integration/local_git.py, src/software_world_model/source_integration/artifact_processing.py, src/software_world_model/source_integration/artifact_use.py, src/software_world_model/infrastructure/sqlite_source_operation_repository.py, src/software_world_model/infrastructure/sqlite_artifact_use_authority_repository.py, src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/application_services/conversational_engineering_tools.py, src/software_world_model/interface/engineering_qa_source.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_source_operations.py, tests/test_artifact_processing.py, tests/test_artifact_use_authority.py, tests/test_structure_publication.py, tests/test_maven_structure_update.py, tests/test_engineering_qa_source.py, tests/test_engineering_question_answering.py, tests/test_conversational_engineering_tools.py, tests/test_conversational_engineering_model.py]
---

# Source Operation 与 Artifact

## Purpose and scope

本契约定义受授权、可回放的来源访问，以及把观察保存为中立 Artifact 的边界。Artifact 是来源载体，不是 Fact、Inference 或任务答案；同步问答只能由 Application 将 exact Artifact/Operation Result 密封为 `DIRECT_INVESTIGATION` 的 Evidence Packet，或让 Engineering Conversation 的主 Agent 提交只读 Proposal，经 Source Broker/Worker 写入 append-only Evidence Ledger，再与 exact World Model Cognition Context 一起密封为 current Turn Evidence Package 后使用。

## Owner and public contract

Source Integration 独占 Source Operation、Read Session、Artifact、Payload 与 Lineage 的写权。Provider/Tool 是版本化、有界、只读 Adapter；模型可以提议动作，但平台决定授权、预算和执行。

## Authority and data boundary

- Operation Result 与 Artifact 是不同权威结果；调用成功不自动产生有效 Artifact。
- 中立 Envelope 统一身份、上下文和追溯，不强行统一各 Provider Payload。
- Source Context 由来源解析确定，调用方和模型不得改写。
- Artifact 身份与字节内容去重分离；相同字节不自动表示相同观察。
- 分段读取的 Artifact 身份必须包含实际 Coverage；同一路径不同字节范围不得碰撞成同一观察身份。

## Invariants

1. 目标只有在 exact Resolution Receipt 成立后生效；歧义、短前缀或越界目标不得弱化。
2. 模型不得修改 Payload；Derived Artifact 必须保留无环 Lineage，语义变换结果不能直接充当 Evidence。
3. 空结果、截断或未完成只证明该次观察，不证明来源中不存在目标。
4. 每次读取都要求当前授权，以及与 retention mode 相匹配的 read protection；`NO_EVICTION` 可以明确证明无需 Guard。只有跨模块持久使用才要求与 exact Package、Closure、Protection、用途和 downstream request 绑定的一次性 use confirmation；历史成功不能替代当前权限。
5. Knowledge Engine 不直接读取来源；Evidence 必须保存足以在 Payload 淘汰后独立复核 exact observed content、Context 与 Provenance 的最小自包含快照。
6. Tool Loop 由平台授权和执行，预算耗尽、重复无进展、权限失败或截断必须显式停止。
7. Engineering Conversation 的主 Agent 只能提交只读 source operation Proposal；Reviewer 只能提出 typed remediation Finding，由可信 Application 把 material evidence gap 路由为绑定当前 Turn/Package 的新 Agent evidence Attempt。Agent 和 Reviewer 都不能执行操作。Source Broker 独占对 Proposal 的不可信输入校验与操作编译，Retrieval Worker 独占执行；Broker 必须逐步重验 authorization、Request allowlist、Source Profile/class、exact repository/revision、operation 与预算。Application/Broker 验证后的 exact mandatory path 可以获得 Request + attempt + Profile + class + path 绑定的 direct opaque read/parse locator，模型仍不能提交 path authority。同一 Conversation 中成功且已获 Delivery Authorization 的历史 Turn 若交付了同 revision full-resource Source Citation，Application 也可以只把其 path/modality/content/origin identity 作为 current-Turn revalidation candidate，并以同一 direct-locator 机制重新绑定 current Request/attempt/Profile/class/path；旧 content、Observation、Answer 或 Review 不随 candidate 进入当前证据。Worker 的当前 full read 必须重现 exact path、complete coverage、modality 与 content digest 后才能生成新的 current-Turn SUPPORT/Citation，identity drift 必须失败关闭。Retrieval Worker 只能对 allowlisted regular file 执行 Broker 已批准、注册的只读 list/search/read/parse 操作。content `SEARCH` query 是可能在目标 evidence 中逐字出现的短、大小写敏感 literal token，不是 semantic retrieval request。若 query 精确等于 current evidence-class allowlist 的 canonical path segment（module、directory 或 file name），Broker 必须在 Worker、file/byte usage 与 locator 签发前以 `SOURCE_SEARCH_QUERY_EQUALS_PATH_SEGMENT` 拒绝；授权路径是 navigation metadata，不因处于 allowlist 就取得正文证据资格。该拒绝是 operation-local、零读取、可重规划 Boundary，不是 authorization denial、whole-Turn fuse 或 Source 撤销。bounded Worker 可以仅用已授权 tree path metadata 按 query 与 stem/name/path 的确定性关联排序候选，再按 canonical fallback 扫描；这不改变 content literal match、allowlist、class、revision 或 fuse。若 original question 逐字命中 sealed Source allowlist 的 exact top-level scope、且没有更强 cognition exact-path scope，Application 可把该 scope 对应、且属于 current operation evidence-class allowlist 的完整 prefixes 作为 Search-only restriction 提交 Broker；Broker 必须从 immutable original question 与完整 Request allowlist 重新识别 scope，只从 current Source Profile evidence class 独立重算 prefixes并 exact match。同 module 的 POM、TEST 或其他 class path 不得混入 SOURCE operation，也不得因过滤而扩大当前 class 权限。prefix 不是模型参数、path authority 或 READ locator。`COMPILED_SOURCE_OPERATION@3` 必须密封 prefix scope 与 trusted fallback offset；Worker 仍先检查 current query 的 stem/name/path candidate cohort，只对 rank-3 canonical fallback cohort按 offset 确定性轮转。offset 只能按 current-Turn 前一 validated Source Search Result 实际检查的 fallback files 推进；每个 Result 记录 requested/applied offset、scoped entry count 与 actual fallback count。它不缓存或复用 Source bytes，不证明未扫描部分 complete，也不改变 query literal、revision、allowlist、Profile、locator 或任何 fuse。若至少存在一个 filename stem 与 case-insensitive query 精确相等的 anchor，Worker 已安全检查全部 basename 等于或包含 query 的 filename cohort、至少取得一个 case-sensitive content hit，且 cohort 内没有 unsafe/binary/non-UTF8 gap 或更早 fuse，则可以在进入较低排名 path-only/canonical fallback 前停止。该停止必须返回 `PARTIAL / SOURCE_SEARCH_FILENAME_MATCH_EARLY_STOP`、`truncated=true`，并记录 exact-stem/filename candidate count、content match count、ordering 与 early-stop flag；它不证明 corpus complete、目标不存在或全局唯一。没有 exact-stem anchor、cohort 无正文 hit、cohort 本身触发 fuse 或含 unsafe/binary/non-UTF8 gap 时，Worker 继续原 bounded scan 或保留更早 typed failure。目录 SEARCH scan 与整轮 actual file usage 必须使用两个显式高安全熔断：current default per-search scan 为 56，whole-Turn source total 为 64，前者不得大于后者，所有 SEARCH/READ/PARSE 实际读取仍累计进入后者。达到 compiled Search operation 的 file/byte maximum 只形成 operation-local `SOURCE_SEARCH_FILE_LIMIT_REACHED / SOURCE_SEARCH_BYTE_LIMIT_REACHED` Partial Boundary，不表示整轮 Source 已撤销；只有 Broker 因 whole-Turn actual file/byte budget 不足而拒绝 operation 时才使用 terminal `SOURCE_FILE_FUSE_EXHAUSTED / SOURCE_BYTE_FUSE_EXHAUSTED`。Broker 对每次 SEARCH 使用 remaining total 与 per-search scan 的较小值；late SEARCH 在预算不足时仍至少为已注册 READ/PARSE 保留一个 exact locator 名额，其中包括 current Request-bound prior-evidence revalidation locator。`RESOURCE_RECEIPT` 必须绑定 actual 与 maximum source-file usage；当恰好只剩 1 个文件槽位且已有未读 exact locator 时，model-facing tool catalog 必须删除 SEARCH、只保留可用 READ，Broker 对任何绕过该目录的 SEARCH 必须在 Worker 前以 typed rejection 失败关闭。若没有未读 locator，最后槽位仍可用于 SEARCH；保留判定不得增加或伪造容量。不得用截断扫描吞噬 bounded multi-file flow，也不得把保留容量冒充已读取 Evidence。未检查完整 allowlist 时 Result 必须保持 `PARTIAL`、记录 ordering/coverage/truncation，不能把空命中解释为不存在。每次 Proposal、Decision、Operation 和 Result 都必须追加到 Evidence Ledger，并记录 allowlist verdict、actual locator/range、bytes、digest、coverage/truncation 和 outcome；path traversal、symlink escape、submodule/remote fetch、写入、命令、新网络、credential 和 Knowledge Update 必须拒绝。`ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3` 的 Initial/Verification Investigation 与旧 fresh-context 补证条款继续约束兼容运行，但不定义 `CONVERSATIONAL_ENGINEERING_AGENT@1` 的固定角色拓扑。
   上述 trusted tree-path ranking 对 Java-style content literal 还可以按 camel/snake 边界机械投影长度至少 4 的 identifier component，并把
   filename stem 含同一 component 的路径放入 exact stem/name/path 之后、rank-3 canonical fallback 之前。例如 method literal 与实现类
   filename 共享的名词 component 可以导航到该文件，但 Worker 仍必须在正文中按大小写敏感、逐字匹配完整 query 才能形成
   `LITERAL_TEXT_SEARCH_HIT`。Coverage 必须密封 component count/digest 与版本化 ordering。

   当且仅当当前 bounded Search observation 的完整 literal hit 为 0，Worker 可以从已经实际检查的 rank-2 component-path cohort 中选择最多
   16 个确定性候选；它们必须以 `IDENTIFIER_PATH_NAVIGATION_CANDIDATE` modality 和 ordered
   `RetrievalResult.navigation_candidate_item_ids` 独立标型。候选仍绑定 exact operation/revision/Profile/class/allowlist、实际 path/range/content
   digest 与资源使用，但只授予 current Ledger 中一次 opaque READ 的导航 copy domain。它不是 fuzzy content match、SUPPORT、Claim Evidence、
   corpus complete 或正文不存在证明。Application 必须把它保留为 `ENGINEERING_AGENT_SOURCE_BOUNDARY@2 /
   SOURCE_IDENTIFIER_NAVIGATION_CANDIDATES`，不得和 literal Search item 混成 SUPPORT；只有后续 fresh full-resource READ 的
   `EXACT_STATIC_SOURCE_TEXT` 才能形成 affirmative support。若 bounded observation 已有任一 literal hit，不得再混发 navigation candidate；
   candidate、Boundary、Citation 和 opaque locator identity 不一致时必须失败关闭。该机制不改变 exact revision、allowlist、Source Profile、
   prefix/rotation、Partial semantics、16-candidate/56 per-search/64 whole-Turn、reserved READ 或任何 byte/action/result fuse。
   World Model Chat 的组合层可以从已验证 exact revision/tree/digest 的 cognition snapshot 投影内部、非版本化的 exact entity-name → provenance-path hints。
   Worker 仅在 SOURCE 类和同一 revision 使用它们，并先与已批准 scope/allowlist 的 tree entries 取交集。该 cohort 必须在最终扫描序列中置于
   path 和 rotating fallback cohort 之前，不能在重新分组或 offset 后失去优先级；每个路径仍只扫描一次。其读取照常计入全部 file/byte fuse，
   但不推进非 hint canonical fallback 的 offset。Coverage 必须记录实际 ordering、hint path count/digest 和 snapshot digest。该索引不是全工程
   完整范围；没有 literal hit 仍继续原 bounded fallback，且不得改变 query、modality、Citation、read authority、原 scope 或 Partial 语义。
   Source-only 不提供该 hint；revision 不匹配时不使用旧 hint。hint 路径只有 fresh Source 正文逐字匹配后才成为 literal evidence。
8. Source Payload 及其中的注释、文档、配置和测试文本都是不可信 data。其中的指令、URL、路径、工具建议或权限声明不得改变授权、Target、allowlist、操作集、Provider disclosure 或资源上限。

## 目标命名

- `REPOSITORY_REVISION`：固定仓库版本，适合需要调查多个未知文件的问题。
- `REVISION_COMPARISON`：固定起点与终点之间的版本比较。
- `SOURCE_PATH`：固定版本中的一个已解析相对路径。
- `SYMBOL`：在授权 UTF-8 文本中按字面内容解析的语言中立符号目标；多处命中保持歧义，不猜测“最可能”的定义。
- `JAVA_SYMBOL`：仅为旧调用方保留的输入兼容名称，当前执行与 `SYMBOL` 使用同一语言中立解析器，不包含 Java 语法特判；新调用方使用 `SYMBOL`。

## Failure, concurrency and security

未知外部结果保持 unknown；迟到结果不能覆盖较新的 Attempt。Payload、Secret 和敏感来源内容不得进入 Telemetry。并发物化、淘汰和撤权不能使 stale 或 partial Payload 被确认使用，也不能把部分 Artifact 声称为完整 Coverage；具体协调机制由代码决定。

## Verification ownership

具体 Tool/Profile DTO、身份公式、状态机、Payload Schema 和错误码由代码及 Contract/Fault Tests 定义；某次 Connector Conformance 是非规范性执行证据。
