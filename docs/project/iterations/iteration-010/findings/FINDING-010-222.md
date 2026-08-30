---
id: FINDING-010-222
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai, quality]
depends_on: [FINDING-010-221, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: project-boundary-relevance-disposition-table-by-reference-and-fragment-state
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-222：run-097 暴露 bound-but-undisclosed Boundary 可被 repair 错标为 NOT_DISCLOSED

## Observation and execution evidence

唯一 validated Engineering Chat launcher 在 product commit/tree
`509b58b356c60e3bd2de47e2a9b3d7f6368888b5 / be031b365f1bc0f2f4d823334519b02751aaf691`
上完成 `run-097-mvp-experience` 的 4 个隔离 Conversation、5 个冻结 Turn，并以
`STOPPED_AFTER_DISPATCH` 正常密封。terminal 内部 receipt digest 为
`sha256:6195a17dff79f696b2d1903e34bbac9e0f980972cc45ad96a680559981123c57`。

Ark 在本运行恢复可用：40 个真实 dispatch 中 39 个 `COMPLETED`、1 个
`OUTCOME_UNKNOWN / REMOTE_DISCONNECTED`；transport 为 40 次成功 TLS handshake、40 次 credential
resolution、40 次 HTTP dispatch、0 retry。由于没有任何 pre-dispatch trusted-unavailable verdict，DeepSeek
合法保持 0 dispatch、admission 未激活。人工审批与 Production Activation 均为 0。

逐题 dispatch 为 `10 / 9 / 12 / 0 / 9`：Q1 为 `SUCCEEDED / ACCEPTED`（2 个 exact Source
Citation）；Q2 为 `FAILED / REVIEWER_MODEL_OUTCOME_UNKNOWN / PROVIDER_OUTCOME_UNKNOWN`；Q3 为
`FAILED / REVIEWER_MODEL_CALL_REJECTED / PROVIDER_OUTPUT_INVALID / STRUCTURED_OUTPUT_INVALID`；Q4 为零
dispatch `APPLICATION_INPUT_CLARIFICATION`；Q5 为 `SUCCEEDED / ACCEPTED`（2 个 exact Source
Citation）。run-097 因而仍为 Quality FAIL，不是 MVP。

turn-scope、pricing capture、session、launch、terminal、Ark DB、DeepSeek DB 文件 SHA-256 分别为：

- `32a205f2eefb26b01eaf23ba28b7d7ce085ad5b0fc3f68e4c72da7e1dbeac895`
- `9494975e40311c7fc6f6dbc52d999205544057ea518a172ddcd9af60742a015e`
- `bd2ebf7df8a04dde4f860310ba72aeefefda2b9768ac36f7ec4b4457f35b777c`
- `3b0d461641e864103f096e4584231b4dbf55f65971494d0b98e8b3eeff049b41`
- `a8f74339bf0a6066a4690672c6f2efa11258a35490d9381cdafd4d178a43d3ff`
- `741d119c3e6ef074249b485a36b9737e177b0153eed02f530c829902ba20a6c0`
- `0f539b3df4c6127e4b2a90005b287ed8e49b3701f314994f6d1ce8e79dd6672c`

public Source session authority、session runtime 与 preparation receipt digest 分别为
`sha256:0f9fad8e39ad6a35cc3c50629ec5584d189888f084f60596988ebe5b395ccc74`、
`sha256:7ef281a092b1917a970f384c105edb4493e0f8fd217558e51c0a12042f1b1463` 与
`sha256:739386f89b2d059f4154b82a9f5ea2a88a02bd4dd7e06b52d017f3f5c180ed4c`。

## Exact first divergence

Q2 的第 9 个、也是 focused Reviewer call 在请求已经完整发送后收到 remote disconnect，因此结果不可知；零 retry 与
不切换 Provider 正确避免了对同一逻辑调用的重复执行。这是本次单一 transport unknown，不是可证明的 Ark pre-dispatch
不可用，也不是当前产品修复依据。

Q3 则提供了新的可重复协议偏差。row 28 comprehensive Reviewer 先返回 Claim 3 Finding 与 `SUPPORTED`
assessment 的矛盾对象；row 29 repair 正确收敛为 APPROVED。row 30 fresh focused Reviewer 随后把全部 13 个
caller/callee challenge 都分类为 `CALLER_INVOCATION + SOURCE_VISIBLE_LOCAL_ORDER /
WITHIN_CALLER_EVIDENCE`，证明 `FINDING-010-221` 的 exact-Claim anchor 已生效。

同一 row 30 对 `boundary_challenge_26e3c2035ca8507896157e59b370fa66` 返回 empty
`draft_disclosed_fragments` 与 `NOT_DISCLOSED_IN_DRAFT`。trusted challenge 却明确投影
`draft_declared_boundary_reference=true`、kind `BOUNDARY_MATERIALITY`，所以其 allowed exact disposition 只有
`MATERIAL_TO_USER_REQUEST / NON_MATERIAL_AUDIT_ONLY`。本地 validator 正确拒绝该组合。row 31 收到
closed repair directive、完整 trusted challenge 与 exact diagnostic 后，仍以不同说明文字重复 empty fragments +
`NOT_DISCLOSED_IN_DRAFT`，再次被同一 contract 拒绝并按 Reviewer call 上限失败关闭。

当前输入虽然分别含 reference flag、allowed dispositions 与 fragment 规则，模型仍需跨多个相距较远字段自行合成状态机；final
preflight 只投影 challenge IDs，未逐 challenge 重复 reference/fragment-state 的 closed disposition 表。generic repair 也没有把
trusted reference flag、submitted exact fragment count 与唯一空-fragment选择并置，导致模型用“正文未披露”的自然语言判断覆盖
sealed structured reference。

## Decision and disposition

这是 `system-contract / systemic` Finding，不按 mall、题号、Boundary ID、Provider 或中文表述特判。

1. `ENGINEERING_AGENT_REVIEW_INPUT@16` 为每个 relevance challenge 投影 exhaustive
   `closed_dispositions_by_fragment_state`：bound + empty 只能选择 kind-specific audit-only；bound + non-empty 可在 material 与
   audit-only 中判断；unbound + empty 只能 `NOT_DISCLOSED_IN_DRAFT`；unbound + non-empty 只能 audit-only。
2. `ENGINEERING_AGENT_OUTPUT_PREFLIGHT@19` 从 trusted role input 重算并逐 challenge 重复 exact kind、reference flag、allowed
   dispositions、audit-only disposition 与 fragment-state closure；candidate 字段不能授权自己的合法值。
3. validator diagnostic 增加 trusted `draft_declared_boundary_reference` 与 submitted exact fragment count；repair directive 明确要求
   bound + empty 形成 audit-only + global reference-removal Finding，unbound + empty 才能使用 `NOT_DISCLOSED_IN_DRAFT`。
4. 协议族升级为 `conversational-engineering-agent@24 /
   conversational-engineering-agent-no-tools-prompt@24 / ENGINEERING_AGENT_PRIMARY_INPUT@24 /
   ENGINEERING_AGENT_REVIEW_INPUT@16 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@19`；wire output schemas、语义审核权、
   两次 distinct-category repair、15-call authority、route、budget、retry 与 Production 边界不变。model-boundary targeted
   regression 为 `34/34` PASS，相邻 16 模块 regression 为 `261/261` PASS；documentation check `628`、plan snapshot/diff
   （trusted base `509b58b356c60e3bd2de47e2a9b3d7f6368888b5`）与 current pre-commit hook 均 PASS。提交与 fresh run-098
   仍按当前连续工作计划执行。

该变化细化既有 Application/Reviewer owner，不改变组件职责，故不需要新 ADR。本 Finding 与同步后的
`SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 是 current system write-back。
