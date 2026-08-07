---
id: SYS-CONTRACT-AI-MODEL-GATEWAY
kind: system-contract
status: current
authority: normative
owners: [ai]
depends_on: [SYS-CONTRACT-X-CAPABILITY-EXECUTION, SYS-QUALITY-SECURITY]
derived_from: [DD-AI-MODEL-GATEWAY]
code: [src/software_world_model/ai_infrastructure/model_gateway.py, src/software_world_model/ai_infrastructure/openai_responses_adapter.py, src/software_world_model/ai_infrastructure/volcengine_ark_chat_adapter.py]
tests: [tests/test_model_gateway.py, tests/test_openai_responses_adapter.py, tests/test_volcengine_ark_chat_adapter.py]
---

# Model Gateway

## Purpose and scope

Model Gateway 是所有外部模型调用的唯一入口，负责精确请求身份、授权输入闭包、执行隔离、Adapter 约束和调用结果记录。它不拥有领域 Strategy、业务 Decision、来源 Tool 或知识准入。

## Public contract

调用方提供经过授权的 Capability、Strategy、精确模型资格和 Authorized Input Manifest。Gateway 只能从 Manifest 构造 Provider Request，并返回不可信的模型结果及可验证执行元数据；领域 Owner 决定结果能否封存。

## Invariants

1. `NO_EXTERNAL_ACCESS` 必须在分派前机械保证，并由绑定 Request Digest 的 Isolation Receipt 证明；提示词禁止工具不是隔离。
2. Gateway 不执行领域 Tool。若任务需要来源调查，模型只产生 Proposal，由 Application 授权 Source Integration 执行。
3. Request model alias 与实际响应 fingerprint 分开记录；资格必须检查 actual identity。
4. 生成、语义审核和答案审核使用隔离上下文；不得依赖 Provider 会话记忆。
5. 响应、Usage、结束原因和 Provider 元数据均不可信，必须经过 closed Schema 和领域语义校验。
6. 迟到或结果未知的调用不能覆盖更新的 Attempt，也不能被写成明确 FAIL、PASS 或零 Usage。

## Security and compatibility

Secret 只在分派前由 Reference 解析，不进入 Request Manifest、日志或持久正文。每个 Provider / Configuration 必须具有明确、版本化且经过 Conformance 的 Adapter compatibility；共享 Adapter 只有在分别证明 Envelope、隔离和身份语义时才可复用，不能凭“OpenAI-compatible”等名称推定兼容。

## Verification ownership

Execution Context、Manifest、Call Record、Provider DTO、重试状态和错误投影由代码与 Adapter Contract Tests 定义。Live Conformance 与具体运行身份是非规范性执行证据。
