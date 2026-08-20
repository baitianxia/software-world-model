---
id: SYS-CONTRACT-AI-MODEL-GATEWAY
kind: system-contract
status: current
authority: normative
owners: [ai]
depends_on: [SYS-ADR-015, SYS-CONTRACT-X-CAPABILITY-EXECUTION, SYS-QUALITY-SECURITY]
derived_from: [DD-AI-MODEL-GATEWAY]
code: [src/software_world_model/ai_infrastructure/model_gateway.py, src/software_world_model/ai_infrastructure/openai_responses_adapter.py, src/software_world_model/ai_infrastructure/volcengine_ark_chat_adapter.py, src/software_world_model/ai_infrastructure/deepseek_chat_adapter.py, src/software_world_model/ai_infrastructure/model_egress_gateway.py, src/software_world_model/ai_infrastructure/pinned_ark_https.py, src/software_world_model/ai_infrastructure/pinned_deepseek_https.py, src/software_world_model/interface/world_model_runtime.py, src/software_world_model/interface/world_model_runtime_assets/gateway_authorized_workload.py]
tests: [tests/test_model_gateway.py, tests/test_openai_responses_adapter.py, tests/test_volcengine_ark_chat_adapter.py, tests/test_deepseek_chat_adapter.py, tests/test_model_egress_gateway.py, tests/test_pinned_ark_https.py, tests/test_pinned_deepseek_https.py, tests/test_world_model_gateway_authorization.py, tests/test_world_model_evaluation_grant.py]
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
7. 每个新的外部披露评测必须绑定当前用户授权；历史 Conformance、Capability Qualification、Product Result 或 package
   freeze 只能证明能力与实现身份，不能授权新问题。trusted launcher 从 exact evaluation grant 派生当前 session receipt；
   active Gateway entrypoint 必须在读取 credential 或进入已资格 baseline 前验证 grant digest、disclosure digest、用户、授权时间、
   authorization ref、payload boundary 与 `Production Activation=NOT_EXECUTED`。历史 permission 字段只能标为 baseline-only。
8. 有界可变调用协议必须同时冻结最小/最大调用数、合法角色序列和 terminal 条件。每个实际调用拥有唯一 Authorized Input
   Manifest、workload/role/step identity、model call ID、receipt 和 transport audit；不能用一个 Plan receipt 代表多个调查回合。
   supervisor 可以提供上限数量的 exact connected descriptor，但 Gateway 只能顺序消费，不能创建、交换或复用连接。Answer terminal
   后未消费 descriptor 必须关闭并记录 `UNUSED_CLOSED`，且 `provisioned = consumed + unused_closed`；少于最小、超过最大、缺 receipt、
   跨题/跨 session 使用或计数未知均失败关闭。
9. 若 Capability 使用 Application-owned constrained transition，Gateway 输入必须同时绑定完整版本化 operation universe 与当前 sealed
   state 的非空受限子集。子集只能由 Application 从冻结 evidence ledger、前序 Result 和预算派生，并按 contract canonical order
   表达；Gateway 拒绝 universe 外 operation、空子集、乱序/重复项或调用方自行扩张。模型 response 中越出子集的 operation 仍作为
   untrusted raw output 记录，但不能由 Gateway 或 Adapter 获得查询/FINISH 权力。
10. 多 Provider 偏好只能在 product freeze 与任何 request dispatch 之前，从分别持有 current Adapter Conformance、同一活动
    Strategy/Configuration Capability Qualification、exact endpoint、secret reference 和隔离 transport 的 route 中选择。选择结果必须
    作为单一 exact Provider subject 密封到 policy、grant、session、socket/TLS 与调用审计；未选择或资格不完整的 route 不能获得
    credential、socket 或试探性调用。一旦任何 request 已分派或 outcome unknown，不得换 Provider 重试；新的 route 选择需要新的
    product freeze 和外部披露授权。

## Security and compatibility

Secret 只在分派前由 Reference 解析，不进入 Request Manifest、日志或持久正文。每个 Provider / Configuration 必须具有明确、版本化且经过 Conformance 的 Adapter compatibility；共享 Adapter 只有在分别证明 Envelope、隔离和身份语义时才可复用，不能凭“OpenAI-compatible”等名称推定兼容。Provider preference 是资格 route 的确定性选择输入，不是 request-level failover 或绕过资格的可用性探测。

## Verification ownership

Execution Context、Manifest、Call Record、Provider DTO、重试状态和错误投影由代码与 Adapter Contract Tests 定义。Live Conformance 与具体运行身份是非规范性执行证据。
