---
id: FINDING-010-116
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, source, ai, security, quality]
depends_on: [FINDING-010-112, FINDING-010-115, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_agent.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: project-trusted-current-turn-tool-copy-domains-and-reject-repeat-or-forged-actions
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-116：Tool 合法参数不能由模型从长 Observation 中自行重建

## Root cause and decision

run-037 Turn 2/4 证明 Broker 的正确拒绝与 no-progress fuse 不能替代 model-facing proposal contract。Application 已持有 exact current-Turn
action history；Source Search 的 authority receipt 也已持有合法 opaque locator、display locator、evidence class 和 modality。旧 input 却只
给出自然语言“使用 earlier locator / 不要重复”，要求 Provider 从长 Observation content 自行重建 action→argument 集合，导致 exact Search
重复和从未签发的 locator 被提交。

`EngineeringAgentInvocation` 现在携带只属于当前隔离 attempt 的 typed `action_history`。Application 在
`ENGINEERING_AGENT_PRIMARY_INPUT@3` 中确定性投影 `tool_reference_policy`：

- `prior_actions` 密封每个已执行 operation、exact arguments 和 proposal digest；
- 分别列出已尝试的 Source Search query、World Model query 和 Source Read locator；
- `source_read_options` 只从 current-Turn `SOURCE_SEARCH / SUPPORT` Observation 的受信 authority-receipt Citation 投影未使用的
  `locator_reference`、display locator、evidence class、modality 和来源 Observation ID；不解析或相信 Source content 中的权限声明；
- exact action 重复和未列出的 Source Read reference 显式禁止。

closed decoder 从原 typed action history、Observation disposition、Citation receipt 与 operation catalog 重算该策略：参数名必须精确匹配；
Search class 必须属于 sealed catalog；exact action 不得重复；Source Read 必须复制当前未使用的 option。Application 不替模型挑选文件、
不生成 query、不把 path 变为 authority，也不修改 Draft。Provider fallback 是 fresh attempt，因此不会继承失败 primary 的中间 action 或
locator catalog。

## Verification and disposition

聚焦测试证明合法 locator 可复制；伪造 locator、重复 Search、参数漂移和跨 disposition 引用均 fail closed；既有 Agent no-progress、Tool
authority、Provider route、artifact Session、Conversation 与 Browser 相邻行为保持不变。首轮 Model/Agent 组合 27/27 PASS，随后 Tool、
Routing、Launcher、Provider Runtime、Artifact、Browser 和 Conversation 相邻组合 43/43 PASS，`py_compile` PASS。

该变化不增加 Source file/byte/operation、model call、Provider dispatch、retry 或 wall-time fuse，也不执行任何 Source/Provider/Browser/
Production 活动。它更新 current Engineering Conversation system truth，但仍只是 local successor candidate；strategy/input identity 改变后
必须 fresh 双 Provider Conformance，才能申请新的 artifact/Live authority。
