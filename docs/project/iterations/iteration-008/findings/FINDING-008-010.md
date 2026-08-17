---
id: FINDING-008-010
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai, architecture, quality, security]
depends_on: [ITER-008-SLICE-001, FINDING-008-005, FINDING-008-009, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-AI-CAPABILITY-EVALUATION, SYS-QUALITY-SECURITY]
code: [src/software_world_model/ai_infrastructure/deepseek_chat_adapter.py, src/software_world_model/ai_infrastructure/deepseek_chat_conformance.py, src/software_world_model/interface/deepseek_provider_cli.py, validation/structure_world_model_iteration_008/capability]
tests: [tests/test_deepseek_chat_adapter.py, tests/test_deepseek_chat_conformance.py, tests/test_iteration_008_capability_harness.py, tests/test_iteration_008_capability_qualification.py]
iteration: ITER-008
classification: iteration-design
disposition: prepare-deepseek-provider-and-hold-live-gates-until-key-and-exact-authorization
target: ITER-008-SLICE-001
---

# FINDING-008-010：DeepSeek 独立 Provider 契约已离线闭合，live 资格按 Gate 推进

## Observation

用户选择新增 DeepSeek 模型 Provider，随后把 API Key 配置到受控执行环境。一次无网络状态检查只确认 secret reference 可解析，
没有输出或持久化 Key，也没有建立 Provider transport。DeepSeek 当前提供 OpenAI-format Chat Completions 接口，但
“OpenAI-compatible”只描述协议表面，不能继承 Ark 的 Provider identity、wire allowlist、模型 identity、secret、网络边界或任何既有
Conformance / Capability Result。

截至 `2026-08-17` 查阅的 DeepSeek 官方 API 文档，选定的 exact endpoint 为
`https://api.deepseek.com/chat/completions`，当前模型 identity 为 `deepseek-v4-pro` 与 `deepseek-v4-flash`；
`deepseek-chat` / `deepseek-reasoner` 已被官方标记为弃用。当前 Slice 以 `deepseek-v4-pro` 作为默认且期望相同 response model
identity，`deepseek-v4-flash` 只作为显式可选项，不接受旧 alias 的静默回退。

## Evidence

- 新增独立 Provider type `DEEPSEEK`、Adapter `deepseek-chat-completions-no-tools@1` 与 secret reference
  `env:DEEPSEEK_API_KEY`；configuration fingerprint 只包含非 secret 设置；
- wire contract 只允许 `model`、`messages`、`stream: false`、`max_tokens`、`thinking: {type: disabled}` 与
  `response_format: {type: json_object}`，不发送 tool、store、session 或 retry 字段；响应端再次验证 closed JSON Schema、结束原因、
  tool/reasoning/refusal 禁止项、usage 与 exact response model identity；
- transport 只接受 exact HTTPS host/path/port，启用证书验证并显式忽略 ambient proxy；网络结果未知保持
  `ProviderOutcomeUnknown`，Provider error 只投影安全的 code/type/request-id，不持久化原始错误正文；
- 独立 `CC-DEEPSEEK-CHAT-NO-TOOLS-001` Conformance 固定恰好两次 synthetic call、12 项判定、无 retry、0600 独占结果文件、
  30 天有效期，并把 DeepSeek Adapter、Conformance、direct HTTPS、Gateway、Schema validator 与独立 CLI 的实现 digest 纳入资格；
- ITER-008 preflight / authorization / capability runner 已改为绑定该 DeepSeek configuration 和资格，不接受 Ark Result 或已消费的
  Ark authorization；fake transport 验证了 2-call Conformance 与 18-case / 39-call Capability 的 exact count 和失败密封；
- 最小 model diagnostic 具有独立 zero-network freeze、单次 authorization 与 write-before-dispatch runner；它固定一个静态 strict-JSON
  probe、恰好 1 次调用、无 retry，并在 PASS、已知 FAIL 或 outcome unknown 时密封 sanitized result/failure 与 terminal；
- 官方依据：[Create Chat Completion](https://api-docs.deepseek.com/api/create-chat-completion)、
  [JSON Output](https://api-docs.deepseek.com/guides/json_mode/) 与
  [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing?article_id=article_1779470751466_8)。

## Impact and classification

该变更替换 ITER-008 尚未执行的 Provider-dependent Gate，但不改 Model Gateway、Capability Evaluation 或 Security 的既有系统不变量：
每个 Provider 仍有独立版本化 Adapter、exact configuration fingerprint、live Conformance 与 Capability Gate，secret 仍只在授权后的
dispatch 前解析。因此分类为 `iteration-design`，主处置写回 `ITER-008-SLICE-001`。

正式 bounded Web runtime、已冻结的 product egress policy 与历史 ITER-003—007 Ark 证据本次保持不变。DeepSeek 最小 live 调用随后
已按独立授权 PASS，后续 2-call Conformance run-001 也按另一份 exact 授权 PASS；两者仍不能解释为业务 Capability、产品结果或生产可用。

## Subsequent live evidence

clean candidate `8cbb3ab69871603d4cc77826eee1082e4e566f55`（tree `fa39f3e575104806499898cf396ac1c1681f3564`）
生成 DeepSeek model diagnostic run-001 freeze
`sha256:1c17dbe86ae42cd7f9d0d8d210ad90cf971c5d9d2d41772b2cfe3a081622c6d9`。用户 exact authorization ref 为
`codex-user-message:sha256:9f4eca3367b2f5f09774af175a0e8aef5c1bcb5c250fc7f1ccf98868b48008a4`，authorization digest 为
`sha256:00a1bbc625070cb6e555a95b171c68ecb47c6d4c4bbde6b1b3b13fc0fac33810`。

runner 恰好执行 1 次请求并返回 `MODEL_DIAGNOSTIC_PASS`：请求和响应 identity 均为 `deepseek-v4-pro`，strict JSON probe 合格，
input/output tokens 为 115/5，Provider request id 为 `e267523d-7756-4e37-9952-157428cdcda9`。result/terminal digest 分别为
`sha256:42d1cacddf878d367b7eea89029563b503fbcf049f244f32e8409b9e629d27b6` 和
`sha256:6202f52af2656f6b101003cc60f4b2904a1df13cf73db910444c077319c261c5`。invocation/result/terminal 均为 0600，
digest 复核 PASS；credential、raw prompt 与 raw response 未持久化，授权已消费且不可重试。

写回后的 clean candidate `45fe1523b286f944cdc1ea781f49fe2bc5461da2`（tree
`31fead7b483c59337b8b29acfbd13cd425e69557`）生成 Conformance run-001 preflight
`sha256:243d154eb3d89072d947a9bd678fd52786ff847cee309cbc38e9ccdef452b3a6`。用户 exact authorization ref 为
`codex-user-message:sha256:82df7218972365cd9c251a3d2600d9e35f0f5fca3be9cf8ac6c21d5d527e4082`，authorization digest 为
`sha256:4391deea9b0e5de7f4c42bbc92fc5612fc72a602c70bac6ca6e200d17e606a01`。

runner 恰好执行 2 次 synthetic request 并返回 `CONFORMANCE_PASS`：12/12 case PASS，请求模型和唯一响应 identity 均为
`deepseek-v4-pro`，input/output tokens 为 378/87，usage 完整；Provider request ids 为
`eabb5d83-a620-40e6-aab0-4c957058f8ca`、`e28b9c86-5c25-4472-a373-12e05c1d7630`。result/terminal digest 分别为
`sha256:390378f02094d70fff4b404acc48f1ce18050761aa027d9a64d43d91f151d37e` 与
`sha256:4e81b6507cc6546ca1bc54bf682a0d2fda8ad68fa03a4c17160c56ced5154261`，资格有效至
`2026-09-16T11:52:36.748495Z`。六份证据均为 0600，digest 和当前 DeepSeek implementation/configuration binding 复核 PASS；credential、
raw prompt 与 raw response 未持久化，授权已消费且不可重试。

## Decision and disposition

保留 DeepSeek 为独立新 Provider，默认模型固定为 `deepseek-v4-pro`。model availability 与本候选 Conformance 已分别按独立授权 PASS；
下一步仍须先闭合 `FINDING-008-011` 的 Capability verifier 缺陷并对修复后的 exact candidate 重新完成同候选 Conformance，再决定是否申请
39-call Capability，仍不提前切换正式 runtime/policy。API Key 只置于
`DEEPSEEK_API_KEY` 环境引用中；不得写入仓库、命令参数、freeze、日志或 Result。

任何 live 步骤仍须先生成绑定当时 clean exact candidate、endpoint、model、Adapter、call count、payload boundary 与 result directory
的 freeze，再取得用户对该 digest 的一次性明确授权。最小 model diagnostic、2-call Conformance、39-call Capability 是三个不同 Gate，
授权不得继承；前一 Gate PASS 前不执行后一 Gate，也不执行正式 Web、hidden canary、SLICE-002 或 Production Activation。

## Verification after disposition

- DeepSeek Adapter、model diagnostic、Conformance、CLI、ITER-008 fake transport、现有 Gateway/Ark 回归与历史 Ark
  implementation-manifest 检查共 85 项通过；测试没有读取真实 credential 或建立公网连接；
- 原 Ark Adapter / Conformance 实现未修改，其历史 implementation manifest identity 保持可验证；
- ITER-008 既有 bounded product egress qualification 测试仍以 Ark 正式 runtime policy 通过，证明本次没有提前切换产品 egress；
- full discovery 实际运行 954 项，但因当前 worktree 缺少历史 validation repository Git metadata / `var/` 密封资产以及 sandbox
  禁止 AF_UNIX listener，以 5 failures、30 errors、1 skipped 结束；因此不把全量 suite 记为 PASS。上述 85 项受影响范围回归独立 PASS；
- `python3 scripts/docs.py check` 对 315 份 current documents PASS，`git diff --check` 与相关 Python compile check PASS；
- live DeepSeek model diagnostic 恰好执行 1 次并 PASS，独立 Conformance 恰好执行 2 次且 12/12 PASS；Capability、正式 Web、hidden
  canary、SLICE-002 与 Production Activation 均未执行。
