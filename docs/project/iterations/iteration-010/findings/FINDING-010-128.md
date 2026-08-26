---
id: FINDING-010-128
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai, security, quality]
depends_on: [FINDING-010-127, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: project-current-turn-response-and-tool-argument-feasible-domains
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-128：Primary input 必须投影 current-Turn 响应与工具参数的真实可行域

## Root cause and decision

run-041 的两个失败都发生在可信执行边界之前：Provider 收到的信息足以让 decoder 判错，却没有在它做 Proposal 的局部位置形成同样的
closed domain。`ANSWER`/`LIMITATION` 是否可行由 current-Turn SUPPORT/BOUNDARY 决定；tool argument 是否可行又由本 Attempt 已执行
action 和未使用 locator 决定。把这些事实只放在旁路 reference policy，而在 `allowed_response_kinds` 或当前 tool entry 中继续展示更宽域，
会诱导模型产生必然被可信层拒绝的输出。

`ENGINEERING_AGENT_PRIMARY_INPUT@6` 现由可信 Application 重算并投影：

- `completion_policy.allowed_response_kinds` 是 exhaustive domain：只有存在 current-Turn SUPPORT 时才列 `ANSWER`，只有存在
  current-Turn BOUNDARY 时才列 `LIMITATION`；standard invocation 仍可在指代确实不明时列 `CLARIFICATION`。对旧 Answer 的总结、改写
  或收窄仍必须重新取得 current-Turn Evidence，不能用 Conversation 文本取得 Claim authority；
- decoder 对所有 mode 都重新检查 Draft response kind 属于上述 current domain。既有 Claim SUPPORT、Limitation BOUNDARY、Observation
  prefix 和 Work State reference 校验继续独立执行，不能由模型自报 policy 绕过；
- 每个 model-facing tool entry 在其参数 `value_constraints` 旁直接列出已用 World Model/Source query 的
  `forbidden_exact_values`，Source Read 则列出唯一可复制的 `allowed_exact_values`。独立 `tool_reference_policy` 与可信 action-history
  decoder 仍是 authority；就地投影只让 Proposal domain 与最终校验一致，不扩大工具或来源权限。

## Verification and disposition

回归覆盖 run-041 的两个最小 signature：无 current observations 的 successor 只把 `CLARIFICATION` 列为 response kind，不能把 prior
Answer 复述成软件事实；已有 `SOURCE_SEARCH(SOURCE, login)` 时，同一个 query 直接出现在对应 tool entry 的 forbidden exact domain，未用
Source locator 则作为 Source Read allowed exact domain。相邻 SUPPORT-only、BOUNDARY-only、evidence-only、unused locator、same-resource
read、forged locator、exact repeated action、terminal Source fuse 与 evidence-required Review case 保持 fail-closed。完整相关 Chat
contract 组合 84/84、`py_compile` 与 `git diff --check` PASS。

该变化不实现或冒充历史 Evidence rebind，也不放宽 Source/Agent/Review/Provider dispatch、retry、fallback、resource 或 wall-time fuse。
它更新 current Engineering Conversation Contract，并把 strategy/prompt/Primary input identity 升级为
`conversational-engineering-agent@6`、`conversational-engineering-agent-no-tools-prompt@6`、
`ENGINEERING_AGENT_PRIMARY_INPUT@6`；Review input/output 仍为 v2。v6 只有本地确定性证据，必须先在新的 exact product commit/tree 上取得
fresh Ark/DeepSeek Conformance，之后才可申请新的 artifact/五轮 Live；本 Finding 不授权任何外部执行或 Production Activation。
