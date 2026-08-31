---
id: FINDING-010-244
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai, operations, quality]
depends_on: [FINDING-010-243, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-OPS-CONFIGURATION]
code: [src/software_world_model/ai_infrastructure/__init__.py, src/software_world_model/ai_infrastructure/volcengine_ark_chat_adapter.py, src/software_world_model/ai_infrastructure/ark_chat_conformance.py]
tests: [tests/test_volcengine_ark_chat_adapter.py, tests/test_ark_chat_conformance.py, tests/test_agentic_capability_live_harness.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: bound-glm-reasoning-effort-and-preserve-incomplete-terminal-response-evidence
target: SYS-CONTRACT-AI-MODEL-GATEWAY
---

# FINDING-010-244：run-111 越过旧 SSE 分歧后由隐藏推理耗尽单调用输出预算

## Observation and evidence

run-111 绑定 product commit/tree
`469fe7af12cbfd0722437bc1fdff8a8adeff82fc / 2281610a227c57acdb56651d90d76f7dfbd86944`、Session/Turn-scope file
SHA-256 `a4ac1b9cc0caf1679b6e79d03b3337d57ea5a3a26ec733c7bc512aea57318c4f /
69e81f8e8ee56d996f62f9c16ac20871f5dfb50cbf1b5f88632d06a6774a764a` 与 fresh Ark `@11 / 1.11.0` qualification。Browser 在
fresh Conversation `conversation_7111520fcd3c4f299334d6f154f99fb4` 提交 run-110 的同一 Q4 `mall-search` import/update/delete 链问题。

第一个 Ark call `model_call_97b3bc2e9973465ea4c224c6c2369ab9` 约 `92.616s` completed，actual model `glm-5.3`、input/output
tokens `9931/5259`、Usage 完整。第二个 call `model_call_c5c49ebfcd05431b909bb4a581821190` 约 `147.890s` 后同样完成 SSE/identity/
Usage 重组，input/output tokens `15406/8192`、finish reason `length`；持久化正文为 `1401` characters，并在 JSON string 中途结束。
这直接证明单调用 `8192` 上限由模型生成消耗完，且正文结构化对象未完成。Provider 的 output token 统计包含已由 Adapter 丢弃的
`reasoning_content`，因此 `8192` 与仅 `1401` 个可见正文字符并不矛盾。

Application 正确把第二个 call 记为 `STRUCTURED_OUTPUT_INVALID` 并发起同 profile 的 format repair。第三个 call
`model_call_551c26a5e37e4e5eaf45a0796028a2b3` 约 `138.211s` 后被 Adapter 记为 `PROVIDER_RESPONSE_INVALID`；它没有 terminal output record，
所以不能把其 exact response shape、finish reason 或空正文追认为已观察事实。当前 `_extract_choice` 在调用方检查 non-`stop` finish reason
之前拒绝空 string content，确定会把“合法 terminal identity/Usage + `length` + empty content”误归为协议无效，并丢失 completed-response
evidence；这是独立且可确定复现的分类缺口，但不冒充第三个 response 的已知原始形态。

run-111 terminal audit 为 Ark TLS/credential/HTTP `3/3/3`、post-dispatch unknown 0、retry 0；DeepSeek dispatch/credential/TLS/HTTP 全为 0，
Production `NOT_EXECUTED`。因此本轮不是 Ark 网络不可用，也不满足 fallback 条件。terminal receipt digest 为
`sha256:999d1086ab96bf0f4c5dcccbed9505c6a04d05dfab0b3668cdceea36f9ee373b`；terminal/Ark DB/DeepSeek DB file SHA-256 分别为
`4d008d1a8fc24e3deb3b68f3bfd560edaeb2e0e1facc272716c08334ce3b60cf /
8c1abaecde029e402296bd1dd0d6fc3f0ad04b93186a41cdcfacec26f6d77798 /
e951c232a7d6ed051340cc5c530fac95e52102bd12a024363fad1e8a340af239`。

run-111 的第二个长 response 已在超过 run-110 旧失败时长后被 `@11` 成功重组，说明 successor 把最早分歧推进到输出预算/结构层；raw SSE
仍未持久化，故它不证明 run-110 实际含 comment，`FINDING-010-243` 的该部分继续保持假设而非追认事实。

## Decision and disposition

1. current Ark preferred profile 固定 `reasoning_effort=low`，Adapter 升为 `openai-chat-completions-no-tools@12`。火山引擎官方 Context Chat
   contract 说明 `low` 会减少推理 token 和时间，GLM 官方 contract 也把 `reasoning_effort` 定义为 GLM-5.2+ 的推理强度控制；但 exact
   Coding Plan endpoint/model 是否接受该字段不从文档推导，必须由 fresh live Conformance 决定。
2. `thinking` 继续缺席；request alias、actual fingerprint、endpoint、credential、SSE、schema、tools、`max_tokens=8192` product bound、总预算、
   route、披露、loopback 与非 Production 范围均不变。该改动减少已授权预算内的隐藏推理消耗，不扩大预算或数据披露。
3. 一个已重组 choice 的 `content` 只要是 string 即视为 protocol-shape valid；empty string 随后由 finish/schema 层处理。non-`stop`
   （包括 `length`）统一产生带 terminal AdapterResponse/Usage 的 `STRUCTURED_OUTPUT_INVALID`；`stop` + empty string 也由 closed schema 拒绝。
   missing/non-string content 仍为 `PROVIDER_RESPONSE_INVALID`，tool/refusal/identity/Usage/SSE/[DONE] 约束不放宽。
4. Conformance fixture 升为 `1.12.0`，wire allowlist 与 strict oracle 要求 exact `reasoning_effort=low`。旧 `@11` 资格不能复用；目标测试、
   docs/plan gate、clean trusted-parent commit 和 fresh Ark Conformance PASS 后才可启动 run-112。若 Ark 拒绝该 field，保持失败关闭并撤回候选，
   不把 HTTP 400 当网络重试或 fallback 条件。
5. run-112 复验同一长问题；若仍耗尽预算，优先继续缩减通用 prompt/state 序列化成本或评估已授权单 call bound 内的其他兼容控制，不能针对
   mall/题面/schema 写特判。任何已投递 outcome unknown 仍不得重发。

## Verification

本地新增确定性测试断言 exact wire 包含 `reasoning_effort=low`、配置拒绝其他未冻结值，并证明 empty-content `length` 被保留为带 Usage 的
`ProviderOutputRejected / STRUCTURED_OUTPUT_INVALID`；旧离线 Harness 的 Ark fixture 也同步到 current SSE response contract。Adapter、
Conformance、Gateway、双 Provider route、Session/runtime/launcher/Browser 与相邻 Agent/Conversation 目标回归 `205/205` PASS，文档检查为
`650 current documents`，trusted-base plan snapshot/diff 与 whitespace check PASS。`@12 / 1.12.0` 的 clean commit 与 fresh live Conformance
仍待执行；在这些证据完成前不得把该 candidate 标为 qualified，也不得启动 run-112。

规范依据：

- 火山引擎 Context Chat Completions：<https://api.volcengine.com/api-docs/view?action=ContextChatCompletions&serviceCode=ark&version=2024-01-01>
- 智谱 GLM 深度思考：<https://docs.bigmodel.cn/cn/guide/capabilities/thinking>
