---
id: FINDING-010-263
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [knowledge, application, ai, quality, web]
depends_on: [ITER-010-PDR-014, FINDING-010-261, FINDING-010-262, ITER-010-VERIFICATION]
code: [src/software_world_model/knowledge_engine/capability_cognition.py, src/software_world_model/application_services/lightweight_engineering_agent.py, src/software_world_model/ai_infrastructure/lightweight_engineering_model.py, src/software_world_model/interface/engineering_chat_browser.py]
tests: [tests/test_capability_cognition.py, tests/test_lightweight_engineering_agent.py, tests/test_lightweight_engineering_model.py, tests/test_engineering_chat_browser.py]
iteration: ITER-010
classification: verification
scope: systemic
disposition: record-live-alpha-rework
target: ITER-010-VERIFICATION
---

# FINDING-010-263：首个世界模型 Browser Alpha 贯通，但声明链漏检造成重大事务错误且 Reviewer 错误批准

## Observation

`run-001` 在 exact product `e8557d3…`、mall `0504e86…` 和同一 Phase B cognition artifact
`sha256:eda4d8…` 上完成三个 Conversation、四个真实 Turn。注册首问、购物车状态行为和 Elasticsearch 导入边界均交付；注册追问却断言
`UmsAdminServiceImpl#updateRole` 没有事务保证、先删除的角色关系会在后续插入失败时残留。exact Source 的
`UmsAdminService#updateRole` 在 `L65-L66` 明确带 `@Transactional`，所以该结论是重大错误，不是可接受的 Unknown 表述。

fresh Reviewer 在只有实现文件 Citation 的情况下仍返回 `APPROVED`。Browser 忠实显示了已授权结果，因此页面不是 first divergence；
Phase C 首次贯通只能证明 Alpha 可操作，不能取得质量、消融增益或 MVP 状态。

## Evidence

- terminal receipt `sha256:5c1a99d42fc2e3bebed496d13f8f9dcde8d4a55d4abaf76bf0be4303ca9500c7`：
  `3 conversations / 4 turns / 31 Ark dispatch / retry 0 / DeepSeek 0 / human approval 0 / Production NOT_EXECUTED`；
- 失败 Turn trajectory 为 `SEARCH_COGNITION(total=1330) → READ_SOURCE(UmsAdminServiceImpl) → FINISH → APPROVED`；Agent 没有取得或读取
  interface declaration；
- 同一 frozen cognition 已包含 `UmsAdminServiceImpl INHERITS UmsAdminService`、接口 `updateRole` method entity 及
  `modifiers=@Transactional`，故 construction 为 PASS，最早偏差是 cognition retrieval/ranking；
- downstream synthesis 把单文件未见注解扩成 repository-level absence，Reviewer 又未挑战该负向保证，因此二者是独立后续故障；
- 购物车 Turn 实际使用两次 `RETRIEVE_COGNITION_DETAIL`，并在第一次 Review `MORE_EVIDENCE` 后补读完整 Source 才通过，证明同一 Agent
  loop 与 fresh Review 在其他问题上能够观察后重规划。

## Disposition

`V-INTEGRATED-ALPHA-001` 记录为 `REWORK`：真实纵链已贯通，但重大错误和 Reviewer 漏判阻止 PASS。按 Slice failure attribution，下一动作先
修 cognition retrieval 并用原失败加两个异质问题复验；不得增加题面分支、答案词法协议或把三项成功掩盖这一项失败。
