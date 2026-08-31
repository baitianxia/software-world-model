---
id: FINDING-010-230
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai, interface, security, quality]
depends_on: [FINDING-010-229, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py, src/software_world_model/application_services/conversational_engineering_routing.py, src/software_world_model/interface/engineering_chat_provider_runtime.py, src/software_world_model/interface/engineering_chat_session_artifact.py, src/software_world_model/interface/engineering_chat_session_runtime.py]
tests: [tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_routing.py, tests/test_engineering_chat_session_artifact.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: enforce-one-pre-dispatch-logical-turn-budget-across-preferred-and-fallback-providers
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-230：run-101 的 Provider 独立 authorizer 让同一 Turn 实际发出 16 次 dispatch

## Observation and execution evidence

`run-101-mvp-experience` Q3 的 route receipt 与两个 Gateway DB 共同证明该 logical Turn 发出 `1` 次 Ark 和 `15` 次 DeepSeek dispatch，合计
`16`。Ark dispatch 形成可信 pre-dispatch-unavailable verdict 后，DeepSeek fallback 15/15 completed；没有 retry 或未授权 fallback，但合计值
违反 current `11 Agent + 4 Review = 15` per-Turn hard upper bound。其余 run/artifact identity 由 `FINDING-010-229` 记录。

这是安全预算实现偏差，不能因所有调用都处于 standing disclosure scope、Ark 返回 429 或 DeepSeek 全天闲时可用而保留。run-101 永久保存
该超限事实；修复不会追认第 16 次调用，也不扩大任何 Provider、披露、Source、retry 或 Production 权限。

## Exact first divergence

Ark 与 DeepSeek 各自拥有一个 `SealedEngineeringAgentRoleDisclosureAuthorizer`，两者都独立执行 `maximum_dispatches_per_turn=15`。旧 route
只把 preferred/fallback 绑定为同一个 logical Turn request，但没有一个在两个 Provider authorizer 之前共享的 reservation state；因此 Ark 的
第 1 个 unavailable call 没有减少 DeepSeek 的本 Turn allowance。route receipt 直到两个 attempt 完成后才汇总 dispatch，且旧 seal 没有重算
combined upper bound。

## Decision and disposition

1. fixed Artifact Session 为 Ark/DeepSeek 两个 authorizer 注入同一个
   `SWM-ENGINEERING-AGENT-LOGICAL-TURN-DISPATCH-BUDGET@1` 对象，绑定 exact Chat、共同 standing authorization message、5 Turn、每 Turn 15
   与 session 75。每个 role disclosure authorization 在 Provider boundary 前先 reservation；preferred unavailable call 同样消耗 slot。
2. shared budget 验证 Turn request/ID、Provider binding、Provider session authority 与共同授权 digest，重复 request、Turn rebind、第 16 次
   per-Turn 或第 76 次 session reservation 都在 dispatch 前以 `BUDGET_EXHAUSTED` 失败关闭。
3. `EngineeringProviderRouteReceipt.seal` 独立重算所有 attempt dispatch sum，不允许其超过 route plan 的最小 per-Turn bound，作为事后
   defense-in-depth；它不代替 pre-dispatch shared budget。
4. Provider runtime/session runtime identity 分别升级为 `SWM-ENGINEERING-CHAT-PROVIDER-MODEL-RUNTIME@2` 与
   `SWM-ENGINEERING-CHAT-SESSION-RUNTIME@3`，receipt/public status 披露 shared budget digest；fixed command composition 要求两个 routes
   持有同一个非空对象。
5. tests 覆盖跨 Provider reservation、第 16 次拒绝、route-combined 16 次失败关闭、Artifact 两 route 对象 identity 与 preparation 零
   reservation。各 Provider 原 session authority 仍保留完整 worst-case funding identity，但不能叠加成第二份 logical allowance。

这项变化写回 `SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 与 active Slice，不改变 route ownership，故不需要新 ADR。fresh
run-102 必须证明任何 Turn 的 Ark+DeepSeek 合计不超过 15。
