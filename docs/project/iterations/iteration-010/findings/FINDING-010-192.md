---
id: FINDING-010-192
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, knowledge, quality]
depends_on: [FINDING-010-170, FINDING-010-191, ITER-010-PDR-012]
code: [src/software_world_model/application_services/conversational_engineering_tools.py]
tests: [tests/test_conversational_engineering_tools.py, tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: remove-global-boundary-semantics-from-world-model-support-payload
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-192：World Model SUPPORT payload 夹带全局 Gap/Boundary 语义

## Observation

对 `run-076-mvp-experience` 的 exact model-visible Evidence 继续审计后发现，SUPPORT Observation
`agent_observation_4b0a41c4c2a24c00969a2378d5f9dd74` 使用 `ENGINEERING_AGENT_WORLD_MODEL_SUPPORT@3`，但其顶层
`coverage` 同时包含 capability manifest 的 `explicit_gaps`、eligibility assessment 的 `COGNITION_GAP` 和其他全局 Coverage 文本。同一
Coverage/Gap 又完整出现在 BOUNDARY Observation `agent_observation_a9f6c93223cc4945bbc6bb40e7d14815`。

因此 Observation ID 虽按 SUPPORT/BOUNDARY 分区，model-visible SUPPORT 正文却仍携带 Boundary 语义。Primary 可以只引用合法 SUPPORT ID
而把其中的 Gap 写成 affirmative Claim，绕过 Application 的 cross-disposition ID guard；`FINDING-010-191` 记录的 false-authorization
Draft 正是从这份混合输入产生。

## Evidence and first divergence

- run-076 第 9 个 Ark call 的 SUPPORT payload 顶层 keys 为 `schema/query/cognition_context_id/cognition_context_digest/source_revision/
  projection/dimensions/source_search_target_projection/coverage`；其中 `coverage` 明确出现
  `STATE_DIMENSION_UNAVAILABLE`、`UNIVERSAL_CONSTRAINT_DIMENSION_UNAVAILABLE`、`INCOMPLETE_IMPLEMENTATION_METHODS:559`、
  `UNSUPPORTED_EXCLUDED_UNITS:866` 和 `status=COGNITION_GAP`。
- 对应 BOUNDARY payload 的 reason 为 `WORLD_MODEL_UNKNOWN_REPORTED`，并已携带同一 `coverage` 以及 exact `unknowns`。删除 SUPPORT 的
  顶层 global Coverage 不会丢失边界信息，也不改变正式 Cognition Context、Ledger、authority receipt 或 Citation identity。
- Engineering Conversation current Contract 已要求 model-facing SUPPORT content 只追加 current-Turn novel supported items；全局
  Coverage/Conflict/Unknown 属 `boundary/audit`。实现把完整 `cognition.coverage` 复制进 SUPPORT，与该规范冲突。
- first divergence 因而前移到 Application evidence-tool adapter 的 World Model projection，早于 Primary synthesis。`FINDING-010-191`
  的 Primary/Reviewer policy 仍是必要下游 guard，但不再被误记为唯一最早层。

## Classification and disposition

这是 `system-contract / systemic` Finding，不按具体 Gap code、Profile、工程、问题或自然语言特判。

1. `ENGINEERING_AGENT_WORLD_MODEL_SUPPORT@3` 顶层不再投影完整 `cognition.coverage/conflicts/unknowns`；它只保留 exact Context/revision
   provenance、novel supported `dimensions` 和由这些 item 派生的 Source target projection。
2. 每个 affirmative Cognition item 自身的 `dimensions[*].coverage` 继续保留，因为它限定该正向 item；全局 Context Coverage、Conflict、
   Unknown 只进入 `ENGINEERING_AGENT_WORLD_MODEL_BOUNDARY@1`。
3. 完整 Cognition Context digest、正式 Ledger、resource/authority receipt、Citation 和 current-Turn item append-only identity 不变；该修复
   只收窄 model-visible SUPPORT 的认识论分区，不删除审计证据或 Source 导航依据。
4. Tool/Model 定向组合 `42/42` PASS；含 Agent、Conversation、Browser、Candidate 和 Session 的相邻组合 `91/91` PASS，验证 SUPPORT 顶层无
   global Coverage、per-item coverage 仍在、Unknown 只在 BOUNDARY，外部 dispatch 0。fresh Browser successor 仍须验证真实
   Primary/Reviewer，不取得答案质量 PASS 或 MVP 名称。
