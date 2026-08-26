---
id: FINDING-010-121
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai, security, quality]
depends_on: [FINDING-010-119, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/application_services/__init__.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: transition-consecutive-no-progress-to-one-evidence-only-reviewed-completion-opportunity
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-121：连续无进展应终止调查，但仍允许一次 evidence-only 受审结论

## Root cause and decision

run-038 Turn 1/2/4 在连续两次无进展后直接以 `AGENT_NO_PROGRESS_LIMIT_REACHED` 关闭。安全目标是阻止继续调查和消耗资源，不是禁止主
Agent 用已经密封的 SUPPORT/BOUNDARY 交付可审核的 Answer 或诚实 Limitation。直接失败绕过了本来可用的 Draft→fresh Review→Response
Control 路径，且不能区分“没有答案”与“现有证据足以说明准确边界”。

Application-owned loop 现引入 typed `EVIDENCE_ONLY_SYNTHESIS` invocation mode：

- 达到既有 consecutive no-progress threshold 后立即冻结调查，`available_operations` 和 model-facing `tool_catalog` 都为空；在未改变的
  maximum Agent-step bound 内提供 completion opportunity，不增加任何 tool、Agent、Provider 或 Source budget；
- Primary input 的 `completion_policy` 要求只提交由 current sealed observations 支持的 `ANSWER`，或绑定 current boundary observations 的
  `LIMITATION`；tool action 与 `CLARIFICATION` 均为协议错误，decoder 和不经模型边界的 direct driver 两层重算；
- Draft 仍必须生成 current Package，进入 fresh independent Reviewer 与 Response Control。Reviewer 若判定需要新 evidence，Application
  不恢复工具权限，按原 no-progress failure fail closed；不需要新证据的 rewrite 仍可在原 Package 上接受审核；
- 该 mode 不把调用上限、Broker rejection 或 Boundary 提升为事实，也不允许声称取得了任何新 evidence。

## Verification and disposition

确定性 Case 先产生两批 boundary/no-progress Observation，随后证明第三次 Primary invocation 收到 response-only mode、提交 Limitation、
经过 fresh Review 并以 `REVIEWED_LIMITATION` 交付；不合规 driver 继续提交 Source action 时以协议错误关闭且 Conversation 保持 ACTIVE。
model boundary Case 证明 v4 input 的 tool catalog 为空、只列 `ANSWER/LIMITATION`，action 与 clarification 输出均被拒绝。联合 Model/Agent
31/31、相邻组合 84/84 与 `py_compile` PASS。

该语义写回 current Engineering Conversation Contract。current strategy/prompt/Primary input identity 为
`conversational-engineering-agent@4`、`conversational-engineering-agent-no-tools-prompt@4`、
`ENGINEERING_AGENT_PRIMARY_INPUT@4`；Review input/output 仍为 v2。v4 只有本地确定性证据，必须先在新 exact product commit/tree 上取得
fresh Ark/DeepSeek Conformance，之后才可申请新的 artifact/五轮 Live；本 Finding 不授权任何外部执行或 Production Activation。
