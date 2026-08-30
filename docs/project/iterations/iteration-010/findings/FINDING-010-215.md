---
id: FINDING-010-215
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [FINDING-010-214, ITER-010-PDR-007, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_routing.py, tests/test_conversational_engineering_tools.py, tests/test_engineering_chat_browser.py, tests/test_engineering_chat_candidate.py, tests/test_engineering_chat_alpha_cli.py, tests/test_engineering_chat_provider_launcher.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_qa_browser.py, tests/test_iteration_010_mvp_value_gate.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: bind-boundary-relevance-to-exact-draft-disclosure-fragments
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-215：run-092 暴露未绑定且未披露的 Boundary 仍可制造 audit-only 空操作 Finding

## Observation and execution evidence

`FINDING-010-214` candidate 已提交为 product commit/tree
`4b0f078cc1caaa5b180bc6de91deb47b5a20e9c1 / a2de53c39e3250c3aa12313ac46c45bd5fdab56f`。DeepSeek 官方 pricing 页面在
`2026-08-30T17:27:47.942Z` 由 in-app Browser fresh 可见检查；capture 文件 SHA-256 为
`5ba85a931acd8f04af44f79cba9ae40bb37f1de15efb5a34b947250a255be66e`，可见文本 digest 为
`sha256:9c9dd4d22764599ade403c0ba6cd95abcb947810d5230ee95cb96a56a62d7668`。validated launcher preparation 在
`2026-08-30T17:30:22.417071Z` 返回 `ALLOWED_OFF_PEAK`，但该 receipt 从未激活为 fallback dispatch authority。

唯一 launcher 完成 `run-092-mvp-experience` 的 4 个隔离 Conversation、5 个冻结 Turn。terminal 状态为
`STOPPED_AFTER_DISPATCH`，内部 receipt digest 为
`sha256:e588416e23c0cdf06adf1e2b98e0090f6c6c0cc9f5a0635bee8ec91f994b0d48`。Ark 53 个 call 全部
`COMPLETED`，TLS/credential/HTTP 均为 `53/53/53`，raw failure、outcome unknown、retry 均为 0。Ark 因而从未形成 trusted
pre-dispatch unavailable verdict；DeepSeek dispatch/credential/TLS/HTTP 全部为 0 是 preferred route 持续可用时的正确结果，不是备用
Provider 或人工授权不可用。人工重复审批与 Production Activation 均为 0。

turn-scope/pricing-capture/session/launch/terminal/Ark DB/DeepSeek DB 文件 SHA-256 分别为：

- `bf10535ebf0428de9baa095574e5a55ee7c0b39b81de9d8e07f1a08c2e974a93`
- `5ba85a931acd8f04af44f79cba9ae40bb37f1de15efb5a34b947250a255be66e`
- `be9314b317081249fa18c2b123d0140679331ff09b73a243980fdf01f5251f90`
- `dae85f6114f202dccb23a0038c3d68102d0375a518ffef31e6f7854cf97e21cf`
- `cdc7b6177b46947ba75c90e8de289339c2c4cb2f9bd21e6c2e5a00d0d7d67990`
- `1bda11fabc9165f05be06b3a8506b711b83f21ac1cb34247c201a7a8b6b1aa23`
- `0f539b3df4c6127e4b2a90005b287ed8e49b3701f314994f6d1ce8e79dd6672c`

逐题 dispatch 为 `15/14/9/0/15`。Q3 在同一 Q2 Conversation 形成 `SUCCEEDED / ACCEPTED`、1 个 exact Source Citation 和 fresh
Review/Delivery Authorization；Q4 为零 dispatch `APPLICATION_INPUT_CLARIFICATION`。Q1 以 `AGENT_PRE_DISPATCH_REJECTED`、Q2 以
`AGENT_REVIEW_LIMIT_REACHED`、Q5 以 `REVIEWER_PRE_DISPATCH_REJECTED` 失败。run-092 因而仍为 Quality FAIL，不能称 MVP。

## Exact first divergence

1. Q1 call 10 comprehensive Review 已批准初稿；call 11 focused Review 正确找到两个 caller-only Source Read 被写成 database/cache effect 的
   Claim，call 12 完成收窄。call 13 随后把已经由 full Source Read 闭合的 Search diagnostic 判成 `RESOLVED_AUDIT_ONLY`，尽管正文没有该
   diagnostic。call 14 再次删除/收窄后，call 15 的 Reviewer 输出明确同时陈述 “draft does not disclose this stale acquisition diagnostic” 与
   “boundary reference is not declared”，却仍返回 `RESOLVED_AUDIT_ONLY` 和一个 “no draft prose deletion is required” 的 global Finding。下一
   Primary call 在 15-call authority 前被正确拒绝。最早偏差不是 authority 太小，而是 typed assessment 允许未绑定、未披露、无可执行修复面的
   audit-only Finding。
2. Q2 重现相同闭环。call 23 把未披露的 resolved Search Boundary 选成 `RESOLVED_AUDIT_ONLY` 且没有 Finding code；bounded repair call 24
   为满足旧 typed contract 反而新增“确保以后不要引入”的 no-evidence Finding。replacement Draft 后 call 27 又为同一已解决诊断制造 audit-only
   Finding，最终耗尽 4-Review 上限。Q5 call 41/42 对两个 resolved Search Boundary 发生同样的 `APPROVED + null finding_code → repair
   fabricates two no-op Findings`；后续真实 caller-effect Findings 因而在 15-call 尾部无法完成修订。
3. 现行 `allowed_exact_dispositions` 只由 trusted kind 与 `draft_declared_boundary_reference` 派生。Reviewer 的自由文本
   `boundary_scope/user_requirement` 虽会说“未披露”，Application 却不能把该语义与 disposition 机械关联。Prompt 又要求 audit-only 缺 Finding 时保留
   disposition 并补 Finding，因此 validator 将自相矛盾放大成稳定空操作循环。

## Decision and disposition

这是 `system-contract / systemic` Finding，不按 mall、问题、Provider、语言、类名、Finding code 或 Observation ID 特判。

1. `engineering-agent-independent-review-proposal@7` 为每个 relevance assessment 新增 required
   `draft_disclosed_fragments[]`。每项必须是从当前 `draft.content` 逐字复制的 non-empty、unique substring；Application 在 model decoder、Review
   record 和 Delivery closure 三层重算。Reviewer 自由文本或 Boundary 原文不能代替该闭合证据。
2. `NOT_DISCLOSED_IN_DRAFT` 只允许 `draft_declared_boundary_reference=false` 且 fragments 为空；`MATERIAL_TO_USER_REQUEST` 只允许
   reference=true 且至少一个 exact fragment。kind-specific audit-only 只允许存在 stale structured reference 或至少一个 exact fragment，并继续
   绑定 global/no-evidence Finding。reference=false 且 fragments 为空时 audit-only 是无修复面的 no-op，必须 structured-output-invalid；模型虚构的
   fragment 因不在 Draft 中也必须失败关闭。bound-but-undisclosed stale reference 仍可由 audit-only Finding 要求删除，故没有丢失合法修复面。
3. Review input/prompt/final preflight 同步投影这些规则。协议升级为
   `conversational-engineering-agent@20 / conversational-engineering-agent-no-tools-prompt@20 /
   ENGINEERING_AGENT_PRIMARY_INPUT@20 / ENGINEERING_AGENT_REVIEW_INPUT@12 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@15 /
   engineering-agent-independent-review-proposal@7`。两次 repair、15-call Turn authority、4-Review 上限、Tool/Source fuse、route、retry、fallback
   eligibility、PDR-007 freshness、接收方和 Production 边界均不变。
4. 新增 deterministic regression 覆盖 Q1/Q2/Q5 的 exact no-op closure：未绑定且 fragments 为空的 audit-only、以及不在 Draft 中的虚构
   fragment 均失败；真实 bound reference 或 exact disclosed fragment 仍可形成 audit-only Finding。Agent/Tool/Model 三模块 73 tests 已 PASS；相邻
   Chat/route/startup/safety 组合仍须完成后才能提交，fresh run-093 才能验证真实模型收敛，run-092 不追认为质量或 MVP PASS。

该变化细化既有 Application/Reviewer owner，不改变组件职责，故不需要新 ADR。本 Finding 与同步后的
`SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 是 current system write-back。
