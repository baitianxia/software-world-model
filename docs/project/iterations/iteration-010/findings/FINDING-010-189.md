---
id: FINDING-010-189
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, interface, quality]
depends_on: [FINDING-010-187, SYS-ADR-017, SYS-OPS-LOCAL-BROWSER]
code: [src/software_world_model/interface/engineering_chat_browser_ui.py]
tests: [tests/test_engineering_chat_browser.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: distinguish-execution-failure-from-raw-provider-evidence-in-browser
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-189：Browser 只显示执行阶段码，隐藏已保留的 raw Provider failure

## Observation and root cause

run-076 的后五个 Ark call 都在 Gateway/Agent/route/Turn projection 中保留
`provider_failure_classification=PROVIDER_HTTP_ERROR` 与 `provider_failure_code=PROVIDER_HTTP_ERROR`，上层 Turn stage code 为
`AGENT_MODEL_CALL_REJECTED`。Browser 的主消息和提交 notice 却只读取 `turn.failure.code`，所以页面只显示
`AGENT_MODEL_CALL_REJECTED`。这是显示层遗漏，不是 Gateway、Application、route receipt 或 terminal audit 丢失 raw evidence，也没有改变
DeepSeek fallback 判定。

## Decision and disposition

这是 `system-contract / systemic` Finding。Browser failure view 现在明确分层显示：

- `Execution <failure.code>` 表示当前 Agent/Application 执行阶段；
- raw Provider evidence 存在时，另显示 `<provider_failure_classification> / <provider_failure_code>`；不存在时不伪造 Provider 原因；
- Provider dispatch count 继续单独显示，Conversation 保持 ACTIVE；页面不暴露错误响应正文、凭据、secret reference 或未密封模型输出；
- route eligibility 完全不从 UI 文案推导，仍只消费 availability owner 的受信 verdict。

Browser tests 以 deterministic failed executor 验证 projection 同时保留 stage 与 raw Provider 两层字段，并检查同一个
`turnFailureSummary` 同时驱动消息与 notice。该变更不修改 receipt、fallback、Provider adapter 或网络行为；无需新 ADR。
