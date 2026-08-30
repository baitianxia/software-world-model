---
id: FINDING-010-225
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai, quality]
depends_on: [FINDING-010-223, FINDING-010-220, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: specialize-empty-findings-review-decision-repair-to-approved-only
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-225：run-098 暴露 empty-Findings Review 缺少单义 decision-only repair directive

## Observation and execution evidence

本 Finding 使用 `FINDING-010-223` 密封的同一 `run-098-mvp-experience` identity、Provider route、artifact digests 与 terminal evidence。
Q5 在 Ark sealed 429 后由 DeepSeek 完成 10 个 dispatch，transport 无 unknown、无 retry；失败层为 Reviewer structured output，不是 Provider
不可用或 fallback 阻塞。

## Exact first divergence

Q5 comprehensive Reviewer 返回 APPROVED。fresh focused Reviewer 随后把全部 Claim 判为 SUPPORTED、全部 caller challenge 判为 WITHIN，
唯一 relevance challenge 1 判为 MATERIAL，challenge 2 为合法 unbound + empty `NOT_DISCLOSED_IN_DRAFT`，且 `findings=[]`；它却把冗余
`decision` 写成 FINDINGS。Application 以 `non-approved Review requires Findings` 正确失败关闭。

Reviewer prompt 已逐字要求这一 closed body 只把 decision 改为 APPROVED，但 `_closed_contract_repair_directive` 没有该 diagnostic 的专用分支，
final preflight 因而只得到 generic directive。repair 随后保留 MATERIAL/null finding-code assessments，又制造一个与已 material challenge 重复的
global Finding，第二次被 focused closure 拒绝并形成
`REVIEWER_MODEL_CALL_REJECTED / PROVIDER_OUTPUT_INVALID / STRUCTURED_OUTPUT_INVALID`。这是 format-repair convergence 缺口，不是 Review
semantic authority 缺口；Application 仍不得自行生成或静默升级 approval。

## Decision and disposition

这是 `system-contract / systemic` Finding，不按 Provider、challenge ID、问题或具体 Draft 特判。

1. exact diagnostic 含 `non-approved Review requires Findings` 时，closed-contract repair directive 必须为
   `CHANGE_ONLY_DECISION_TO_APPROVED_KEEP_ALL_CLOSED_ASSESSMENTS_AND_EMPTY_FINDINGS`。
2. Provider 必须保留所有已 closed assessment 与 empty Findings，只改 redundant decision；不得制造 Review-contract Finding、重分类 material
   challenge 或要求 Draft 增加 Claim。Application 仍重新 decode/validate fresh Provider output，不自行批准。
3. 该 directive 只具 local convergence authority，不增加事实、Evidence、Tool、Review 或 Delivery authority；它沿用
   `FINDING-010-224` 的 current `@25/@16/@20` 协议族、原 output schema、route、budget、retry 与 Production 边界。
4. regression 为 exact diagnostic 断言专用 directive；六模块定向测试 `155/155`、相邻 19 模块 `265/265` PASS。fresh run-099 验证真实 repair 收敛；run-098
   保持真实质量 FAIL。

该变化细化既有 Application/model-boundary owner，不改变组件职责，故不需要新 ADR。本 Finding 与同步后的
`SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 是 current system write-back。
