---
id: SYS-CONTRACT-SOURCE-ARTIFACT
kind: system-contract
status: current
authority: normative
owners: [source]
depends_on: [SYS-CONTRACT-SOURCE-DATA-SOURCE, SYS-CONTRACT-X-CAPABILITY-EXECUTION]
derived_from: [DD-SRC-SOURCE-ARTIFACT]
code: [src/software_world_model/source_integration/operations.py, src/software_world_model/source_integration/local_git.py, src/software_world_model/source_integration/artifact_processing.py, src/software_world_model/source_integration/artifact_use.py, src/software_world_model/infrastructure/sqlite_source_operation_repository.py, src/software_world_model/infrastructure/sqlite_artifact_use_authority_repository.py]
tests: [tests/test_source_operations.py, tests/test_artifact_processing.py, tests/test_artifact_use_authority.py, tests/test_structure_publication.py, tests/test_maven_structure_update.py]
---

# Source Operation 与 Artifact

## Purpose and scope

本契约定义受授权、可回放的来源访问，以及把观察保存为中立 Artifact 的边界。Artifact 是来源载体，不是 Fact、Inference 或任务答案；同步问答只能由 Application 将 exact Artifact 内容和来源操作引用密封为任务级 Evidence Packet 后使用。

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
