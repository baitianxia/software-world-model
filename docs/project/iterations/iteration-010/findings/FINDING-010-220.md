---
id: FINDING-010-220
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai, quality]
depends_on: [FINDING-010-219, FINDING-010-215, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: close-focused-review-finding-to-challenge-binding-repair
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-220：run-095 暴露 focused Review 的 unbound Finding repair 仍可原样重复

## Observation and execution evidence

本 Finding 使用 `FINDING-010-219` 已密封的同一 `run-095-mvp-experience` identity、Provider
route、artifact digest 与 terminal evidence。Q3 在 DeepSeek route 上完成 6 个 call，连同 Ark sealed
429 共 7 个 dispatch；Primary 已完成 World Model query、bounded SOURCE Search、Answer Draft 与
comprehensive Review，失败发生在 focused Reviewer 闭合，不是 Source authority、Provider availability
或重复授权。

## Exact first divergence

Q3 的 Draft 正确把零匹配与 `56/64` bounded acquisition 诊断保留为 Limitation。focused Reviewer
对两个实际 disclosed Boundary challenge 都返回 `MATERIAL_TO_USER_REQUEST` 且
`finding_code: null`，却又额外返回 Finding `F1`，要求删除或缩窄其中一个诊断。Application 机械拒绝：
`focused Reviewer Findings must equal the exact challenge-bound Finding set`。旧 repair directive 只要求
`REBUILD_FOCUSED_LINKED_FIELDS_AS_ONE_COHERENT_CLOSURE`；repair input 已包含 exact rejected object 和
禁止原样重复的要求，但模型仍逐字返回同一个矛盾对象，最终密封
`FAILED / REVIEWER_MODEL_CALL_REJECTED`。

因此机械 validator 已正确失败关闭；最早缺口是 repair branch 没有把唯一合法二选一投影给模型：
保留 Finding 时必须把它绑定到一个 exact challenge 的允许 audit-only disposition 和同一 code；若所有
Boundary 都 material，则必须删除无绑定 Finding 并 APPROVE。

## Decision and disposition

这是 `system-contract / systemic` Finding，不按 Q3、Finding 文本或具体 Boundary 特判。

1. focused Review prompt 明确禁止“所有 challenge 都是 `MATERIAL_TO_USER_REQUEST` + null code，
   同时又有额外 Finding”的对象。
2. 每个 retained Finding 必须绑定一个 exact disclosed-fragment challenge，复制该 challenge 的允许
   audit-only disposition，并使用相同 unique finding code；如果没有任何 fragment 应从 Draft 删除，
   则删除 unbound Findings 并返回 APPROVED。
3. 对 exact `focused Reviewer Findings ... exact challenge-bound Finding set` diagnostic 使用专用
   closed directive：
   `BIND_EACH_RETAINED_FINDING_TO_ONE_ALLOWED_CHALLENGE_ASSESSMENT_OR_REMOVE_UNBOUND_FINDINGS_AND_APPROVE`。
   其他 linked-field diagnostic 和机械 validator 不放宽。
4. 协议族升级为 `conversational-engineering-agent@22 /
   conversational-engineering-agent-no-tools-prompt@22 / ENGINEERING_AGENT_PRIMARY_INPUT@22 /
   ENGINEERING_AGENT_REVIEW_INPUT@14 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@17`；output schemas、两次
   distinct-category repair 上限、15-call authority、route、budget、retry 与 Production 边界不变。
   targeted regression 已覆盖专用 directive 与 Reviewer prompt，相邻十七模块 `255/255` PASS；fresh
   run-096 才能证明真实模型收敛。

该变化细化既有 Application/Model owner，不改变组件职责或 wire output schema，故不需要新 ADR。
本 Finding 与同步后的 `SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 是 current system write-back。
