---
id: FINDING-010-194
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, knowledge, quality]
depends_on: [FINDING-010-170, FINDING-010-192, FINDING-010-193, ITER-010-PDR-012]
code: [src/software_world_model/application_services/conversational_engineering_tools.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_tools.py, tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: partition-world-model-item-dimensions-before-support-projection
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-194：SUPPORT dimensions 仍夹带 COVERAGE/UNKNOWN/EVIDENCE 元数据 item

## Observation

`FINDING-010-192` 移除了 `ENGINEERING_AGENT_WORLD_MODEL_SUPPORT@3` 顶层的 global `coverage`，但继续检查 run-076 的 exact
`dimensions` 后发现，前两项仍是 capability Profile 的 `dimension=COVERAGE`，第三项是 eligibility assessment 的
`dimension=UNKNOWN/status=COGNITION_GAP`。它们与后续 query-relevant `BEHAVIOR/ENTITY` item 一起获得同一个 SUPPORT Observation ID 和
affirmative Citation domain。

因此只删除顶层字段并未闭合根因。Draft Claim 9/10 同时引用 BOUNDARY 和 SUPPORT，Application 当时因 cross-disposition 正确拒绝；如果
repair 只删除 BOUNDARY ID，仍可用混合 SUPPORT 引用 Gap 与全局清单元数据。

## Evidence and first divergence

- `agent_observation_4b0a41c4c2a24c00969a2378d5f9dd74` 的 `dimensions[0]` 与 `[1]` 是
  `COGNITION_CAPABILITY_MANIFEST_PROFILE/COVERAGE`，statement 内含 `explicit_gaps`；`dimensions[2]` 是
  `COGNITION_QUESTION_ELIGIBILITY/UNKNOWN`，statement 内含 `missing_dimensions=[CONSTRAINT,STATE]` 与 `status=COGNITION_GAP`。
- 领域模型 `CognitionItem.create` 已明确只有 `COVERAGE/UNKNOWN` 可以没有 formal support reference；multi-Profile query projector 也把
  `COVERAGE/EVIDENCE/UNKNOWN` 排除在 query-ranked affirmative relevant items 之外。Application adapter 丢失了这个现成的 typed
  distinction，才是 first divergence。
- 正式 `WorldModelCognitionContext`、Coverage/Unknown、Ledger 与 authority receipt 已保留完整 metadata identity；将这些 item 排除出
  SUPPORT 不会删除审计证据。BOUNDARY 继续携带 global Coverage/Conflict/Unknown。

## Classification and disposition

这是 `system-contract / systemic` Finding，不按具体 Profile、Gap code、工程、问题、数字或语言关键词特判。

1. `ENGINEERING_AGENT_WORLD_MODEL_SUPPORT@4` 只允许 `ENTITY/RELATION/BEHAVIOR/CONSTRAINT/STATE` item；
   `COVERAGE/EVIDENCE/UNKNOWN` 永不取得 affirmative Claim 资格。
2. SUPPORT 的 current/novel/already-observed counts、Citation refs 和 cognition-derived Source target projection 都只按 affirmative item domain
   计算。per-item `coverage` 字段继续保留，用于限定对应 affirmative item，不等同于 `dimension=COVERAGE` metadata item。
3. 完整 Context、global Coverage/Conflict/Unknown、Ledger、authority receipt 及其全部 Citation identity 不变；metadata-only Context 形成
   `WORLD_MODEL_HAS_NO_SUPPORTED_ITEMS` BOUNDARY，不制造空或 metadata-only SUPPORT。
4. Tool/Model 定向组合 `43/43` PASS；含 Agent、Conversation、Browser、Candidate 和 Session 的相邻七模块 `92/92` PASS，覆盖 mixed
   metadata+behavior 只投影一个 BEHAVIOR、receipt 仍保留四个 item identity，以及 metadata-only Context 的 zero SUPPORT / explicit
   BOUNDARY；外部 dispatch 0。fresh Browser successor 仍待验证。
