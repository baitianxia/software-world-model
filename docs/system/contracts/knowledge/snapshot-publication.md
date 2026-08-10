---
id: SYS-CONTRACT-KNOWLEDGE-SNAPSHOT-PUBLICATION
kind: system-contract
status: current
authority: normative
owners: [knowledge]
depends_on: [SYS-CONTRACT-KNOWLEDGE-ADMISSION, SYS-CONTRACT-KNOWLEDGE-SCHEMA-CORE]
derived_from: [DD-KNW-SNAPSHOT-PUBLICATION]
code: [src/software_world_model/knowledge_engine/formal.py, src/software_world_model/knowledge_engine/structure_authority.py, src/software_world_model/knowledge_engine/structure_publication.py, src/software_world_model/infrastructure/sqlite_formal_knowledge_repository.py, src/software_world_model/infrastructure/sqlite_structure_knowledge_repository.py]
tests: [tests/test_formal_knowledge.py, tests/test_knowledge_update.py, tests/test_structure_publication.py, tests/test_maven_structure_update.py, tests/test_iteration_003_g1_integration.py]
---

# Snapshot Publication

## Purpose and scope

Snapshot 是单一 Knowledge Scope 下完整、不可变、原子发布的正式知识状态，不是 Delta。发布把已接受的本地 Candidate Reference 固定为正式身份，并按显式 Publication Mode 与 Coverage 形成完整成员集合后移动 CURRENT。

## Owner and public contract

Knowledge Engine 的 Publisher 独占 Snapshot、Manifest、Member State、Publication Attempt 与 CURRENT 写权。Application 提供独立 Acceptance；只有 exact Admission ACCEPT 与 Application PASS 同时成立才可发布。

## Invariants

1. Snapshot 成员仅为 Entity State、ASSERTED Fact State 与 ASSERTED Inference State；Conflict 是受约束的 Inference 类型。Evidence、Artifact、Context、Admission、Schema、Attempt 和 Result 只作 trace dependency。
2. local reference 替换只在整体提交成功后对外可见；失败不能泄露部分正式 ID。
3. Publication Mode 只有显式 `ENRICH` 或 `REPLACE_COVERAGE`。`ENRICH` 继承旧成员且不得静默删除；`REPLACE_COVERAGE` 只继承声明 Coverage 外的旧成员，Coverage 内完全以本次已接受 Manifest 为准，未再次出现的旧成员必须从新 Snapshot 消失。两种模式都不改写旧 Snapshot。
4. 全部权威记录与 CURRENT 在同一 Scope 事务中提交，并显式检查 expected current。
5. cross-scope dependency 固定 exact Snapshot；Read Session 打开后不随 CURRENT 漂移。
6. 当前没有 physical cleanup 或 authoritative projection。Persistence Contract 的 exact Snapshot Read Bundle 是可删除、可重建的 no-payload 读取副本，不拥有成员或 CURRENT，也不构成本条禁止的第二权威。
7. Knowledge Engine 拥有唯一权威发布裁决与并发 fence；可以由串行化、提交时重验证、版本冲突检测或等价机制实现。对同一逻辑请求，cancel 与 publish 竞态只能有一个终态胜出。
8. `OUTCOME_UNKNOWN` 只是调用方尚不能证明结果的视图；同一 request / idempotency key 必须查询或恢复原 Publication Attempt，不得创建第二个竞争发布。
9. Coverage 分为跨 revision 稳定的 Coverage Root 与 revision-bound Coverage State。Root 固定 owning Scope、Profile/schema/evaluation context/canonicalizer 的 exact ref 与 digest、稳定 Source Binding、逻辑目标根和成员类型/谓词，不包含 source revision、Evidence、成员集合或 Context State；State 再固定本次 exact source revision/Context、这些 Definition ref/digest、completeness claim、成员 Manifest、Evidence 与 digest。首次完整发布创建 Coverage Root/State；后续 `REPLACE_COVERAGE` 只能替换同一 Root 的先前 State。Coverage 不完整或无法证明时不得 replacement，也不能误删其他 Coverage Root、Behavior、Business 或 History 知识。
10. Publisher 在提交前重建目标 Snapshot Closure，并验证所有 Relation Fact 端点、Support、exact upstream 与 inherited member 在最终成员集合中仍合法。失败保持旧 CURRENT。
11. 每个 Snapshot 对同一 Root 最多有一个 State。`ENRICH` 首次可创建非重叠 Coverage Root/State，后续 Coverage State Manifest 是先前成员与新增成员的并集；遇到已有知识 Root 时，只允许相同 State 的幂等重放。不同 State 必须拒绝，状态更新只能通过拥有该 Root 的 `REPLACE_COVERAGE` 完成。Publisher 不可自行选择保留或覆盖。
12. 当前系统禁止同一 Scope 内权威 Coverage Root 重叠：一个 Entity/Fact/Inference Root 的 State 在一个 Snapshot 中只能由一个 Coverage State 管理。新 Manifest 若声明的 Root 已由另一 Coverage Root 管理，或两个 replacement 请求对同一 Root 竞争，必须拒绝；Relation 可以引用其他 Coverage 的 exact member，但不会因此取得其管理权。未来若需要共享所有权，必须先接受新的 Publication Contract。
13. Publisher 必须重读 Admission 绑定的 exact Source persistent-use confirmation，并核对 candidate ref/digest；历史 Application Result、未持久化 proof 或另一 Candidate 的 confirmation 都不能推进 CURRENT。

## Failure and implementation boundary

任何 Digest、资格、expected current、Publication Mode、Coverage Root/State、Member Closure 或 CAS 失配都保留旧 CURRENT。Manifest/Receipt 字段、构建顺序、取消和恢复算法由代码及 Contract/Fault Tests 定义。
