---
id: FINDING-003-007
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-003-SLICE-001, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-KNOWLEDGE-CONTEXT-COMPARISON, SYS-CONTRACT-KNOWLEDGE-PERSISTENCE, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE]
code: [src/software_world_model/knowledge_engine/context_comparison.py, src/software_world_model/application_services/structure_read_session.py, src/software_world_model/infrastructure/sqlite_structure_read_session_repository.py, src/software_world_model/interface/runtime.py, src/software_world_model/interface/cli.py, src/software_world_model/interface/presenters.py]
tests: [tests/test_context_comparison.py, tests/test_structure_read_session.py, tests/test_iteration_003_g1_integration.py]
iteration: ITER-003
classification: local-implementation
disposition: persist-exact-structure-read-session
target: src/software_world_model/application_services/structure_read_session.py
---

# FINDING-003-007：通用旧 Read Session 不能证明 Structure ordered Read Set 不漂移

## Observation

G1 的 A1→B→A2 初版集成只检查旧 Formal Knowledge 的
`app_snapshot_read_sessions` 计数为零，并把 Admission 的 Source Artifact read-set digest
误当作 Snapshot Read Set。两者都没有固定 Structure Snapshot manifest、Coverage State 和
Profile/Schema/Evaluation Context/Canonicalization 比较基础，因此不能证明 B 后已解析的旧
Session 与 caller-declared A1→B ordered Read Set 在 A2 发布后保持不变。继续核对还发现，
比较 Assessment 若由 Application 自行创建，会违反 Context Comparison 的 Knowledge Engine
所有权；只固定 Snapshot ID 也不足以证明读取时 Scope 与 Task 授权仍有效。

## Evidence

- Admission read set 描述候选生成所读取的 Source Operation/Artifact，不拥有 Knowledge Use
  的 Snapshot selection。
- 旧 `SnapshotReadSession` 读取 Formal Knowledge Snapshot，无法解析新
  `StructureSnapshot` 与 typed Coverage record。
- 初版 mall integration 从未创建 Structure Session，A2 后也没有按 Session ID 重启复读；
  仅断言一个不同表的记录数始终为零。
- 初版比较逻辑把 Assessment/Outcome 定义并创建在 Application service，不能证明
  Knowledge Engine 从 exact Context inputs 独立重建 Validity。
- 仅保存 Snapshot selection 没有绑定 Scope revision、Task Boundary、caller 与
  `KNOWLEDGE_USE@1` Scope assertion，历史可读性可能绕过当前控制状态。

## Impact and classification

System Contract 和 V-006 已要求 CURRENT 单次解析、exact Snapshot 与 ordered Read Set 固定；
发现没有改变 View、Bundle 或查询语义，只暴露 G1 实现缺少对应持久 authority。因此属于
local implementation，且必须在 G2 开始前闭合。

## Decision and disposition

新增最小 `StructureReadSessionService` 和 SQLite authority，只保存 exact Snapshot/Coverage
refs、定义摘要、member manifest 与 canonical digest，不保存 Evidence/Source payload，也不
提前实现 View、Bundle 或 query。每次打开绑定 exact Scope revision、Task Boundary、caller
和 Knowledge-owned Scope state assertion；重放和读取会重验当前 Scope 控制状态。

`CURRENT` 只在首次打开时解析一次；幂等重放和按 Session ID 读取只重验已固定 Snapshot。
ordered 模式保留 caller 声明顺序，不按 Snapshot revision 猜测 base/target；相邻 pair 必须
同 Scope、相同 Schema 与 Coverage comparison basis。Application 把 no-payload exact
Snapshot/Knowledge Context/basis 输入交给 Knowledge Engine 的确定性
`StructureContextComparisonService`，Session Repository 只保存和反序列化其不可变
Assessment，随后由 Knowledge Engine 从 exact inputs 重建校验 Outcome/Validity。mall 集成
在 B 后打开 CURRENT B 与 A1→B ordered Session，另有 B→A reverse-order 反例；发布 A2 后
重启复读并逐字段相等，同时证明更新本身没有创建 Question、Task 或 Session。
