---
id: FINDING-010-136
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, knowledge, interface, quality, project]
depends_on: [FINDING-010-132, FINDING-010-134, FINDING-010-135]
code: [src/software_world_model/application_services/engineering_question_cognition.py, src/software_world_model/application_services/conversational_engineering_tools.py, src/software_world_model/interface/engineering_chat_session_artifact.py]
tests: [tests/test_engineering_question_cognition.py, tests/test_conversational_engineering_tools.py, tests/test_engineering_chat_session_artifact.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: bind-question-needs-to-versioned-profile-capabilities
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-136：认知资格必须同时匹配维度、查询能力和独立 Read Authority

## Observation

把两个 Snapshot 的记录放进同一 Context 不能证明工程认知资格。`DECLARES_METHOD` 只证明声明关系，不能单独取得 Behavior；泛化的
`ENTITY/RELATION` 标签也会让 Java declaration Profile 与 Maven dependency Profile 同时命中结构题。另一方面，旧 artifact Session
Configuration `@1` 只绑定一组 ordered/Snapshot 文件路径，没有表达 ordered multi-Profile identity 或 expected file/Bundle digest。

因此 Question Eligibility 需要从原问题先导出 material dimensions 和 versioned query capability，再逐 Need 对照 Profile；query-time
相关性可以使用 Agent 的 semantic query，但不能借此改写原问题 Need。Session loader 还必须逐 Profile 固定 exact artifact identity，再由
Application 形成 composite authority，而不能合并 Snapshot/Read Set。

## Evidence

- exact `mall@0504e86b…` 的 Manifest `sha256:bf8a416f6866bce7015946aac6ee2e19073d897ca33a76ffc76316f4eb643792`
  以固定顺序绑定 Maven 与 Java 两个不同 Snapshot/Read Authority，revision 唯一，Application Binding 唯一；
- 结构题只由 `MAVEN_REACTOR_STRUCTURE@1 + direct_dependency@1` 取得资格；行为题只由
  `JAVA_SOURCE_SEMANTICS@1 + method_implementations@1` 取得资格；Maven-only 行为题同时报告缺少 Behavior 和 method implementation
  capability；
- 行为投影产生非 locator 关系 `login → loadUserByUsername`、`login → insertLoginLog`、
  `insertLoginLog → getAdminByUsername`；职责/失败边界题保留 `CONSTRAINT/STATE` Cognition Gap，未把正向 call fact 扩张成完整失败语义；
- 三类问题得到不同 Context digest 和 23/32/32 个正式 support item；最多 32 个 query-ranked item，JSON field name 不参与相关性匹配；
- artifact Session Configuration `@2` 逐 Profile 固定 ordinal、Profile/Schema/Source Binding、selected Snapshot、ordered/Snapshot Bundle
  digest 与 file digest；全组合测试证明 preparation 为零 cognition call、零 Source read、零 credential resolve、零 Provider dispatch、零
  listener。旧 `@1` 单 Profile配置仍可加载，但不取得 multi-Profile 资格。

## Decision and disposition

该发现处置到 `SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION`：

- Capability Manifest 保留每个 Profile 的 Schema、Coverage binding、Snapshot/Read Session/Read Set/ordered Bundle、query capability、
  cognition dimension、gap 和 exact digest；Application composite digest 是 Chat 的 World Model authority；
- Eligibility 从 original question 形成 Need，逐 dimension 和 query capability 给出 Profile bindings、eligible Profile 或 explicit Gap；
- query-relevant projection只读取各自已验证 Bundle，Profile Snapshot/Read Set identity不合并；Source 不能进入 projector，也不能回填为
  World Model contribution；
- `WORLD_MODEL_QUERY` 可以用 Agent semantic query 重新投影相关正式项，但每次新 Context 都绑定同一 Turn Request/Manifest authority 并
  追加 Ledger receipt；
- `@2` 是 multi-Profile artifact binding；`@1` 仅保持历史单 Profile Session 可读兼容。
