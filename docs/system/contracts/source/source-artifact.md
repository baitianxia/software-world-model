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
当前 `CONVERSATIONAL_ENGINEERING_AGENT@1` 基线覆盖上述来源安全边界，但不允许历史 Turn 的 Citation、内容或 locator 生成下一 Turn 的 revalidation candidate；只有本 Turn 新形成的 Search/Cognition navigation observation 才可生成本 Turn 的 read option。上一句中关于历史 Citation candidate 的机制仅保留为 `ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3` 兼容实现，不得进入默认 Chat。
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
