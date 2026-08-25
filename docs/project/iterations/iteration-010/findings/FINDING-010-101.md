---
id: FINDING-010-101
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai, security, interface, operations, quality, project]
depends_on: [FINDING-010-100, SYS-ADR-017, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, SYS-OPS-CONFIGURATION]
code: [src/software_world_model/interface/engineering_chat_provider_runtime.py, src/software_world_model/interface/engineering_chat_provider_launcher.py, src/software_world_model/interface/__init__.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py, src/software_world_model/ai_infrastructure/volcengine_ark_chat_adapter.py, src/software_world_model/ai_infrastructure/deepseek_chat_adapter.py, src/software_world_model/ai_infrastructure/model_gateway.py]
tests: [tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_provider_launcher.py, tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_routing.py, tests/test_volcengine_ark_chat_adapter.py, tests/test_deepseek_chat_adapter.py, tests/test_model_gateway.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: credential-lazy-qualified-provider-runtime-composition
target: SYS-OPS-CONFIGURATION
---

# FINDING-010-101：真实 Ark/DeepSeek model runtime 形成零 I/O 本地组合候选

## Observation

`FINDING-010-100` 的 fixed Browser composition 接受任意满足 Driver/Reviewer 协议的依赖；其测试使用明确不可调用的 placeholder，因此只证明
route、attempt、Conversation 和 Browser 接线，不能证明现有 Ark/DeepSeek Adapter、transport、Model Gateway、Disclosure Authorizer 与
`CONVERSATIONAL_ENGINEERING_AGENT@1` model boundary 可在同一配置身份下组合。若直接在 fixed command 内零散构造这些对象，容易绕过
Conformance/configuration/session 的 exact equality，或在 listener 前提前解析 credential/建立连接。

## Evidence

- 新 Provider model runtime 只把已验证的 `ArkChatConformanceQualification / DeepSeekChatConformanceQualification` 转换为 exact
  `EngineeringAgentModelConfiguration`。result ref/digest、qualified model identities、adapter version、Provider configuration fingerprint、
  有效期和资源熔断任一漂移均失败关闭；Session Disclosure Authority 还必须绑定同一 Chat Binding 和 configuration。
- Ark runtime 内部构造现有 `UrllibVolcengineArkChatTransport + VolcengineArkChatCompletionsNoToolsAdapter`；DeepSeek runtime 内部构造现有
  `PersistentDeepSeekChatTransport + DeepSeekChatCompletionsNoToolsAdapter`。两者只登记 `env:` secret reference，构造不调用 resolver、不开
  socket、不建立 TLS、不发送 HTTP；同 Provider retry 继续为 0。
- 两条 runtime 分别绑定完整 Model Gateway repository protocol、`LIVE_CURRENT` Adapter capabilities、Session-scoped one-use Disclosure
  Authorizer、Policy-enforcing Gateway 和同一 closed Agent/Reviewer model boundary。公开 preparation receipt 不投影 secret reference，状态固定
  `QUALIFIED_PROVIDER_RUNTIME_BOUND_NOT_DISPATCHED`，preparation-time dispatch/credential/Production 均为 0/false/`NOT_EXECUTED`。
- 两条 runtime 可生成 distinct attempt dependencies，并通过 `EngineeringChatProviderAttemptFactory` 接入 `FINDING-010-100` 的 exact
  Ark→DeepSeek route 与 non-starting Browser launcher。预检结束后两个 model boundary audit、Disclosure request、DeepSeek TLS/credential
  计数、Conversation/Turn 和 Provider dispatch 全部仍为 0。
- 新 3 个 runtime 案例加入上一轮相关组合，命令
  `PYTHONPATH=src:. python3 -m unittest tests.test_engineering_conversation tests.test_conversational_engineering_agent tests.test_conversational_engineering_tools tests.test_conversational_engineering_model tests.test_conversational_engineering_routing tests.test_engineering_chat_candidate tests.test_engineering_chat_provider_launcher tests.test_engineering_chat_provider_runtime tests.test_engineering_chat_browser tests.test_engineering_chat_alpha_cli tests.test_model_gateway`
  重新实际得到 `79/79 PASS`；`compileall`、`git diff --check` 与 current documentation `501/501` 同时通过。本次没有外部网络、
  Provider/model、credential、listener/browser、mall Source/resources 或 Production Activation。

## Decision and disposition

- 实现状态增加 `PROVIDER_RUNTIME_COMPOSITION_LOCAL_CANDIDATE`。这证明生产 Adapter/transport/Gateway/Disclosure/model-boundary 类可由 exact
  typed qualification 和 Session Authority 组合，并且构造期保持零 I/O；不再把“已有两个 Adapter”误写成产品 runtime 已接通。
- 单元测试中的 qualification 是本地构造的 typed identity，不是从当前 sealed Conformance 文件加载的外部执行证据；当前 fixed command 也
  尚未加载双 Conformance、创建两个 private SQLite repositories、构造 Source/World Model runtime 或签发本次五轮 Session。因此仍为
  `CURRENT_QUALIFICATION_NOT_LOADED / FIXED_COMMAND_SESSION_NOT_WIRED / NOT_LIVE`。
- 下一最早缺口是把 published World Model、exact Local Git Source Profile/Worker、两份 current Conformance、两个 private Gateway
  repositories 与双 Session Disclosure 编译为一个固定 Chat Session Configuration；只有该 clean preflight 完成后，才可请求 Provider/browser
  live grant。Production Activation 仍不执行。
