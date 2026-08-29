---
id: FINDING-010-185
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [FINDING-010-181, FINDING-010-184, ITER-010-PDR-012]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: align-source-file-budget-read-options-and-effective-tool-catalog
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-185：Source file budget 已耗尽时仍向模型暴露不可执行 locator

## Observation

fresh Browser `run-075-mvp-experience` 绑定 exact product
`bba64e75d7f6a8bfac17ddcb98c47982cdf24611 / c026679ab11eaa168d4143c81bac7759ba11300c` 与 mall exact Source
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7 / 047d79d8588b76013c260f3f1a9565707301a60a`。run-074 的 Maven/启动链失败题
在 Ark 8 次 dispatch 后形成 `SUCCEEDED / ACCEPTED`，真实证明 `FINDING-010-184` 的 shape-repair 修复已越过旧失败点。随后订单创建题、同
Conversation 库存失败追问和新 Conversation 省略指代隔离 probe 也分别形成成功 Answer 或零 dispatch Clarification。

第五个后台用户角色重分配问题在 8 次 Ark dispatch 后以 `AGENT_MODEL_CALL_REJECTED` 关闭。初始 Primary
`model_call_8b78d5419ee0482aa4869b76a4e73ed9` 的 JSON 在 character 1730 把 `plan` 错写为 `plan[`；唯一 same-profile repair
`model_call_32339502046443aaafe8106edc1a0d1d` 修复了语法，却提出读取
`source_locator_bd87c976f4058811582b9093782325dc`。Application 拒绝该 action 是正确的，因为当前 effective `tool_catalog` 只含
`WORLD_MODEL_QUERY`。

## Evidence and first divergence

- repair 的 sealed input 显示 `tool_action_budget used=5 / remaining=3`、`completion_policy.mode=STANDARD`、
  `tool_action_allowed=true`、`terminal_source_denial_reason=null`；失败不是总 action budget、evidence-only completion 或 Broker terminal
  rejection。
- 同一 input 的最新受信 Source resource receipt 已达 whole-Turn `64/64`，所以 Application 正确从 effective catalog 撤销
  `SOURCE_SEARCH/SOURCE_READ`；但 `tool_reference_policy.source_read_options` 仍列出未使用的 `UmsAdminController.java` opaque locator。
  模型面对“可复制 locator”和“不可执行 operation”两个相反的 closed domain，并选择了 dangling locator。
- initial/repair raw output digest 分别为
  `sha256:05992f0b2600a2c7dd3979fe22ce47df95de7c0d94032432f6d5639e844401a2` 与
  `sha256:6bb3b65f9960d18d3eda0522f9514fd8ff77e7c436196ba509a4613d2a1704ac`。repair action 明确为
  `SOURCE_READ(locator_reference=source_locator_bd87c976f4058811582b9093782325dc)`。
- terminal receipt payload digest 为
  `sha256:eecdabf3a81f9f62be60ef72d506883c7fdb20e6aca2e84cc47030d106068785`，terminal 文件 SHA-256 为
  `1140aaa0a4a1be971fe8bab5a3bd19f60fec0746413eba8241b871ce43996d6a`。它密封 4 Conversation、5 Turn、Ark
  dispatch/TLS/credential/HTTP `31/31/31/31`、retry 0、post-dispatch unknown 0、human approval request 0。DeepSeek 虽获周末
  `ALLOWED_OFF_PEAK`，但 Ark 全部可信可用，故 DeepSeek dispatch/TLS/credential/HTTP 全 0；Production `NOT_EXECUTED`。
- first model defect 是 initial JSON syntax；first systemic interface divergence 是 `_tool_reference_policy` 与
  `_effective_available_operations` 分别投影 read reference domain 和 file-budget executable domain，前者不知道后者已因 `64/64` 关闭。

## Classification and disposition

这是 `system-contract / systemic` Finding；修复所有 Source Profile、工程、语言和问题，不按 mall、controller、locator 或 `64` 特判。

1. Application 从最新受信 `RESOURCE_RECEIPT` 投影 `ENGINEERING_AGENT_SOURCE_FILE_BUDGET@1`，精确给出 `used / maximum / remaining /
   exhausted`；没有 Source resource receipt 时为 `null`，不推测预算状态。
2. `source_read_options` 只列当前预算与 catalog 下可执行的 opaque locator。`exhausted=true` 时清空 options，并同时保持 Source
   Search/Read 离开 effective catalog；模型不得从 observation、prior action、path 或 open item 重建 Source action。
3. 预算耗尽不伪造 Broker decision。只有 Ledger 中真实 terminal rejection 才设置 `terminal_source_denial_reason`；本例继续为 `null`，使
   “已用尽资源”与“操作被 Broker 拒绝”的证据语义保持分离。
4. Decoder 继续从原 receipt、action history 与 current catalog 重算并失败关闭。`63/64` 且有未读 option 时仍保留唯一 READ slot；
   `64/64` 时 option/catalog 同时关闭，dangling READ 被拒；既有 terminal-denial 行为不变。无 AF_UNIX 依赖的受影响组合 `127/127` PASS，
   外部 dispatch 0。扩展 141 项 raw 的 1 FAIL + 5 ERROR 全部是 sandbox 禁止本机 socket，未作为产品 PASS 或代码失败改写。
   fresh Browser successor 仍须验证角色重分配题和未参与修复的异质题；run-075 失败 Turn 不追认。
