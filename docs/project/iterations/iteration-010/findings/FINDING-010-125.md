---
id: FINDING-010-125
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai, security, quality]
depends_on: [FINDING-010-124, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: seal-current-turn-work-state-reference-domains-and-require-tool-action-after-evidence-finding
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-125：Work State 引用域必须按 current Turn 密封，缺证 Review 必须转入工具动作

## Root cause and decision

run-040 证明 previous Work State 同时承担 Conversation continuity 和 model-facing copy source 时，会把两类不同权威混在一起：目标、约束、
计划和经接受的纠正可以延续，但 previous Turn 的 Observation IDs 不是 current Turn Evidence。把旧 ID 原样投影给模型，使 fallback 能生成
语法正确却无 current Observation authority 的 Work State；decoder 虽正确拒绝，Primary contract 却没有给模型唯一可复制域。

`ENGINEERING_AGENT_PRIMARY_INPUT@5` 现增加可信 Application 生成的 `work_state_reference_policy`：

- `required_current_turn_observation_ids` 是本次 invocation 必须完整、原序复制的唯一 Observation prefix；previous Work State 只披露 prior
  Observation count，不披露 ID，也明确不授权跨 Turn 复用；
- accepted correction 与 superseded conclusion 都以 exact prefix 投影。只有 current User Message 明确纠正较早 Conversation context 时，
  才可把 sealed current User Message ID 追加到 accepted-correction prefix；其他未列 reference 一律禁止；
- Provider 仍提交完整 Work State proposal，Application 从 original Request、current observations、previous committed Work State 与 Context
  重算 reference policy 并 fail closed，不能替模型删除或替换错误 ID。

Reviewer Finding 只要 `requires_evidence=true`，standard successor invocation 的 `completion_policy.tool_action_required` 就必须为 true：合法输出
只能是 effective tool catalog 中一个 exact action，不允许再次提交 Draft。模型必须使用 catalog 列出的 exact 参数名与数量；额外、遗漏、重复
参数继续由 closed schema/decoder 拒绝。evidence-only completion 不恢复工具，所以其 Reviewer 若要求新 Evidence 仍按既有 no-progress
failure 关闭。

## Verification and disposition

测试证明 previous Work State 不再暴露 prior Observation IDs，current policy 只列 current observations；evidence-required Finding 使 response
kind domain 为空，并拒绝没有 tool action 的 Draft；prompt 同时固定 correction/superseded prefix 和 exact action arguments。Model/Agent
31/31、Session/Tool/Route/Browser 相邻组合 84/84 与 `py_compile` PASS。

该变化不放宽 Observation validator、Source/Agent/Review/Provider dispatch、retry、fallback 或 wall-time fuse，也不把历史 Evidence 自动
重绑到 current Turn。它更新 current Engineering Conversation Contract，并把 strategy/prompt/Primary input identity 升级为
`conversational-engineering-agent@5`、`conversational-engineering-agent-no-tools-prompt@5`、
`ENGINEERING_AGENT_PRIMARY_INPUT@5`；Review input/output 仍为 v2。v5 只有本地确定性证据，必须先在新的 exact product commit/tree 上取得
fresh Ark/DeepSeek Conformance，之后才可申请新的 artifact/五轮 Live；本 Finding 不授权任何外部执行或 Production Activation。
