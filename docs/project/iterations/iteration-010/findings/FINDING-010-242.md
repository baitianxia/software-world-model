---
id: FINDING-010-242
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai, operations, quality]
depends_on: [FINDING-010-240, FINDING-010-241, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-OPS-CONFIGURATION]
code: [src/software_world_model/ai_infrastructure/volcengine_ark_chat_adapter.py, src/software_world_model/ai_infrastructure/ark_chat_conformance.py]
tests: [tests/test_volcengine_ark_chat_adapter.py, tests/test_ark_chat_conformance.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: use-qualified-provider-sse-wire-and-reconstruct-one-terminal-adapter-response
target: SYS-CONTRACT-AI-MODEL-GATEWAY
---

# FINDING-010-242：短 Ark canary 成功掩盖约 56 秒长响应断连

## Observation and evidence

用户允许定时重试 Ark 网络后，fresh no-source Conformance
`ccrun_59669547ea8c4e7598ef91bf020c44c6` 在 current `glm-5.3/@9` identity 上两个 canary 均 completed，result digest 为
`sha256:7821d7525cb82d8aefe1512310f1d762b7ea74f277c0c5b80a153f41b15910e0`，总 input/output tokens 为 `330/215`。这证明当时的
DNS、TLS、credential、HTTP 和短响应路径可用，因此触发同 standing scope 的 clean run-109，而不是继续空等。

run-109 绑定 product commit/tree
`aa647b4da289ec4ecbeb50cd6c0868b4f0fa18e2 / 2122c6da9a4371ca791816deeb702a9211184435`、Session/Turn-scope file SHA-256
`61f567eb95383d95e23dc568571c273303377f0f81d804ae14eab03c77ccff03 / b84c48f6102023e5b6712e485b785f6b23d7ecce36d0f960eb96c55935c44ced`
和上述 fresh qualification。Browser 使用此前未执行的冻结 Q1，不重复 run-108 Q5 的 outcome-unknown request。model call
`model_call_34169eabafb742fd8e10cb18c256db6b` 在
`2026-08-31T12:15:02.753309Z` 进入 `DISPATCHED`，于 `2026-08-31T12:15:58.748933Z` 进入
`OUTCOME_UNKNOWN / PROVIDER_OUTCOME_UNKNOWN`，精确间隔约 `55.996` 秒；transport 再次记录
`REMOTE_DISCONNECTED`，TLS/credential/HTTP `1/1/1`、retry 0、DeepSeek 0。

run-108 的异质 Q5 则从 `2026-08-31T11:24:21.791655Z` dispatch 到
`2026-08-31T11:25:17.866402Z` outcome unknown，间隔约 `56.075` 秒。两个不同长产品输入在近乎相同边界断开，而同一网络上的短
Conformance canary 数秒完成；因此“Ark 整体不可用”不是有证据的根因，周期性短探针也会产生可用性假阳性。当前最早偏差是 Ark
non-streaming wire 必须等待完整生成后才产生响应内容，无法在该长响应连接边界前提供持续流量。`56` 秒边界来自两次本地执行的归纳，不声称是
Provider 公布的固定超时。

run-109 terminal receipt
`sha256:e4373ff9bafc4b752dbe09a7e599efa24af058ed64ff1f7e0a1828022bbf9266` 密封 1 Conversation、1 Turn、Ark 1、DeepSeek 0、retry 0、
human approval 0 和 Production `NOT_EXECUTED`。terminal/Ark DB file SHA-256 分别为
`c9de2d8e6298e8d4ca038d0ea2e4ed68cac68ec8290283c02b1eac84eff753c9 / 378c0e599fc4b684ea53055d4ad4ffaa0f955a2c45b105dd00637907428abb7b`。

火山引擎 official Chat Completions API 文档定义 `stream:true` 时以 SSE 返回增量块并以 `data: [DONE]` 终止，且
`stream_options.include_usage:true` 请求最终 Usage 块：
<https://api.volcengine.com/api-docs/view?action=ChatCompletions&serviceCode=ark&version=2024-01-01>。该已发布协议提供了保持同
Provider/model/endpoint/account、同一次 request 和同预算的通用 wire repair；它不是重发历史 unknown request，也不扩大 disclosure。

## Decision and disposition

1. Gateway/Application 的 `ProviderRequest.stream` 继续固定为 `false`：调用方只收到一个已完成、已校验的 terminal `AdapterResponse`，不观察
   partial token，不改变 Turn、review、retry、fallback 或交付语义。
2. Ark Adapter 升级为 `openai-chat-completions-no-tools@10`。其 Provider wire 固定
   `stream:true + stream_options:{include_usage:true}`，HTTP `Accept: text/event-stream`；Adapter 在内存中完整消费 SSE 后才构造一个终态
   response。Provider-only `reasoning_content` 只允许 string/null 并丢弃，不进入产品输出或持久化。
3. SSE parser 失败关闭：要求 `text/event-stream`、UTF-8、单一 data event framing、稳定且非空的 response/model identity、恰好一个 choice、
   assistant delta、禁止 tool/function/audio/refusal output、唯一 finish reason、合法顺序和最终 `[DONE]`。Content 只按顺序拼接；Usage 仍按
   `prompt + completion = total` 判断完整性。中途断连仍由 transport 记为 outcome unknown，绝不重发或据此 fallback。
4. `DIRECT_VERIFIED_TLS_HTTP11_ONE_REQUEST_PER_SESSION@1`、每 request 一次 TLS/HTTP、`Connection: close`、credential timing、调用/token/
   时长预算、Ark preferred route、DeepSeek trusted-unavailable-only fallback 与非 Production 边界全部不变。
5. request bytes、response parser 和 Adapter identity 已改变，旧 `@9 / Conformance 1.9.0` 资格不得复用。Conformance fixture 升为
   `1.10.0`，live oracle 必须证明 exact SSE request、terminal reconstruction、actual `glm-5.3`、Usage、request ID 和原 transport audit；只有
   fresh PASS 后才创建 run-110。

这是 Provider wire/response parsing 的 current system contract repair，不是问题、工程或输出特判。Model Gateway current configuration 和
Operations configuration 在同一变更中更新；目标测试通过只能证明 local candidate，不能替代 fresh live Conformance 或产品质量 verdict。
