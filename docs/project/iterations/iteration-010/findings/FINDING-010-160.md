---
id: FINDING-010-160
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [FINDING-010-159, ITER-010-PDR-010]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_routing.py, tests/test_engineering_chat_provider_launcher.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_chat_alpha_cli.py, tests/test_openai_responses_adapter.py, tests/test_volcengine_ark_chat_adapter.py, tests/test_deepseek_chat_adapter.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: keep-format-repair-diagnostic-in-agent-application-boundary-and-preserve-provider-conformance
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-160：格式修复诊断曾错误改变 Provider adapter 身份

## Observation

`FINDING-010-159` 的首个候选 `c0d53498f1d1db26d1d3ad20296d8313df452dca` / tree
`1889463c1df0691726ba5b67e897dc79dd514aa1` 把 nullable/closed-object 字段诊断写进了
`openai_responses_adapter.py`。fresh `run-050-mvp-experience` 因此在 listener、credential、TLS 和 Provider network 前以
`QUALIFICATION_INVALID: Ark conformance result is stale for the current implementation or configuration` 失败；这不是 Ark availability，也没有
触发 DeepSeek 或等待其窗口。

两个新 Gateway repository 只完成 schema 初始化，roots/manifests/outputs 均为 `0/0/0`；没有 launch/terminal receipt，外部模型调用为 0。
既有 Ark Conformance 密封的 adapter file digest 为
`sha256:4a584ef2fbf92338e897ccd5f9ea71b971f4baac3460bb8e31b900fcb6695830`，首个候选改变了该字节，导致 aggregate implementation digest
不再等于资格 Result。格式修复属于 Agent/Application work-state boundary，不应为获得字段提示而改变已经独立资格化的 Provider wire adapter。

## Decision and disposition

- 恢复 `openai_responses_adapter.py` 与其测试的 exact qualified bytes；current Ark/DeepSeek implementation aggregate digest 分别重新等于既有
  Conformance 的 `sha256:6053c96dd8ab32b3582b84109cc45359f8f13cc8e282d94e418b3f461d81878f` 和
  `sha256:a680b0c8d99ce320dd9abc2096bef90d98420490e441b352e9a2994b741dbb07`，不重跑 Provider Conformance。
- 字段级诊断由 `conversational_engineering_model.py` 在同一 exact output schema 上生成，只用于 Agent/Application-owned fresh repair input。
  它穿透 nullable `anyOf`、本地 `$ref` 与嵌套 closed object，报告 trusted schema 中缺失的字段名；untrusted unexpected key 只报告有界 count，
  不把其文本提升为 trusted instruction。
- Provider adapter 仍负责原有 closed-output acceptance；Application 既不改变 wire/adapter identity，也不修补模型输出。诊断失败时保留 adapter
  原始 failure message；第二次 shape 仍无效时继续关闭 Turn，fallback 仍为 0。

受影响 Adapter/Agent/routing/launcher/runtime/artifact/CLI 组合 123/123 tests PASS；adapter exact file digest 与双 Provider aggregate digest
分别同既有资格 Result 对账 PASS。外部 Provider/network dispatch 0，full regression 0。fresh Browser successor 待执行。
