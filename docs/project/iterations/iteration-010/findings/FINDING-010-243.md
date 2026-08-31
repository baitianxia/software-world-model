---
id: FINDING-010-243
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai, operations, quality]
depends_on: [FINDING-010-242, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-OPS-CONFIGURATION]
code: [src/software_world_model/ai_infrastructure/volcengine_ark_chat_adapter.py, src/software_world_model/ai_infrastructure/ark_chat_conformance.py]
tests: [tests/test_volcengine_ark_chat_adapter.py, tests/test_ark_chat_conformance.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: accept-and-discard-sse-comment-keepalives-without-changing-terminal-response-semantics
target: SYS-CONTRACT-AI-MODEL-GATEWAY
---

# FINDING-010-243：长响应已越过旧网络边界，但合法 SSE 控制帧被本地解析器误拒

## Observation and evidence

run-110 绑定 product commit/tree
`2c9197229002156337106f6351715695a429c391 / 1164eee6da4992e19a02fe2aed05d61d812770cb`、Session/Turn-scope file
SHA-256 `fd0f216fc9f94550739b1549d4cf8c5144fcad42e3ea3436aab255de136ce041 /
35dfaa1c34722daf68bec85103bffb19cb5626cf8719f20564cbcabeb5371c30` 和 fresh Ark `@10 / 1.10.0` qualification。Browser 提交此前未因
outcome unknown 而冻结的 Q4 `mall-search` import/update/delete 调用链问题。

第一个 Ark call `model_call_878b5d24a6984b0a8281fae08305a2b3` 从
`2026-08-31T13:13:10.093884Z` dispatch 到 `2026-08-31T13:14:30.426906Z` completed，约 `80.333s`，actual model
`glm-5.3`、input/output tokens `9935/6075`、Usage 完整。它已越过 run-108/109 的约 56 秒 non-streaming 断连边界，直接证明
`FINDING-010-242` 的 SSE response transfer 修复对长响应网络路径有效。

第二个 fresh call `model_call_678999cb2440457099caa211da6c999e` 从
`2026-08-31T13:14:30.442958Z` dispatch 到 `2026-08-31T13:16:13.367703Z` failed，约 `102.925s`，分类为
`PROVIDER_OUTPUT_INVALID / PROVIDER_RESPONSE_INVALID`。run terminal audit 为 Ark TLS/credential/HTTP `2/2/2`、post-dispatch unknown 0、
retry 0；因此这次不是 DNS/TLS/credential/HTTP 断连，也不满足 trusted unavailable，DeepSeek 0 正确。Turn 以
`AGENT_MODEL_CALL_REJECTED` 失败关闭，Conversation 保持 ACTIVE。

当前安全记录有意不持久化 raw Provider response，Gateway failure revision 也只保留 closed failure code，故不能把 run-110 的具体原始
SSE 行型写成已观察事实。代码审查则确定了一个独立、可复现的协议缺口：`@10` parser 要求每个 event 恰好为一行 `data:`，因而必然拒绝任何
以 `:` 开头的 SSE comment keep-alive。火山引擎 Chat Completions 文档明确把该 wire 定义为 SSE；WHATWG SSE 规范定义 comment line 应被
忽略，并明确允许用 comment 保持长连接。run-110 的长时序与 keep-alive 相符，但“该响应实际包含 comment”在 raw response 未保存的前提下
仍是有证据支持、尚待 successor differential 验证的假设，不冒充直接事实。

run-110 terminal receipt digest 为
`sha256:a0fe2c8b7547c2a1f2fbbe4a4b114bdfe40b3ac4e3bb231e0b16f94f56d0108c`；terminal/Ark DB/DeepSeek DB file SHA-256 分别为
`ab9f3263dd7027ed757728bf96ac88262e99f5348184ea770ce7b91f130afca8 /
e4c29a57f92da80f73a36ce8b1e3475b1185c09dc23bb2d20df015aaee1d197e /
e951c232a7d6ed051340cc5c530fac95e52102bd12a024363fad1e8a340af239`。密封状态为 1 Conversation、1 Turn、Ark 2、DeepSeek 0、
human approval 0、Production `NOT_EXECUTED`。

## Decision and disposition

1. Ark Adapter 升级为 `openai-chat-completions-no-tools@11`。SSE framing 层忽略以 `:` 开头的 comment line 和重复空分隔；comment 无论单独
   成帧还是与一个 data field 同帧都不形成 application event，内容不投影、不持久化，也不影响 response digest。
2. Application event 继续要求恰好一个 `data:` field。`event`、`id`、`retry` 或其他非 comment 控制字段仍失败关闭；JSON object、稳定
   response/model identity、单 choice、禁止 tool/function/audio/refusal、finish reason、Usage 顺序和最终 `[DONE]` 全部保持不变。
3. Gateway/Application 仍只观察一个 terminal response；partial content 与 reasoning channel 不外泄。HTTP bytes 已发送后的断连仍为
   outcome unknown；same-request retry 0、trusted-unavailable-only fallback、预算、披露、exact source、loopback 与非 Production 均不变。
4. response parser 与 implementation digest 已改变，旧 `@10 / 1.10.0` live qualification 不得复用。Conformance fixture 升为 `1.11.0`；
   targeted/docs/plan gate 和 clean trusted-parent commit 通过后，必须 fresh Ark Conformance PASS 才能创建 run-111。
5. run-111 先重验 run-110 的已知失败问题，再执行异质冻结问题。若仍出现 `PROVIDER_RESPONSE_INVALID`，不得把本 Finding 的 comment 假设
   追认为根因闭合；继续定位下一最早 parser divergence。任何 output-invalid 都不触发 DeepSeek。

这是 SSE transport framing 的通用兼容修复，不包含工程、题面、关键词、symbol、Schema 内容或模型输出特判。唯一 System Owner 为
`SYS-CONTRACT-AI-MODEL-GATEWAY`；当前配置实例由 `SYS-OPS-CONFIGURATION` 同步更新。

## Verification

新增确定性测试用合法 standalone/mixed/after-DONE comment keep-alive 证明其被丢弃且 terminal output 不变，并证明 `event/id/retry` 仍被拒绝。
Adapter/Conformance、Gateway、双 Provider、Session/runtime/launcher/Browser 和相邻 Agent/Conversation/route 定向测试共 `198/198`
PASS；文档检查为 `649 current documents`，trusted-base plan diff PASS。clean implementation commit/tree 为
`8d7927fabfc068f2df00c7f7ae48ab1ebf04bdb4 / fffe078b22a59c4188880108932f518acb38acda`。

该 exact `@11 / 1.11.0` identity 随后完成 fresh live Conformance
`ccrun_e837a716a9e243c29c4affc4fcd113a0`：13/13 case PASS，actual model `glm-5.3`，input/output tokens `327/199`，Usage 完整，
TLS/credential/HTTP `2/2/2`，retry 与 post-dispatch unknown 均为 0。result digest 为
`sha256:bee27baec52f897d82b028c704a4adf8a61a255232b97013eda10894d0a8e3b2`，artifact file SHA-256 为
`9a64c7a0434989ec8a431d34cc569b421f0063dc345adebd88a7e7cd4e381dd1`，valid until
`2026-09-30T13:57:32.710257Z`。该 PASS 恢复新 Adapter identity 的机器资格；短 canary 未证明实际收到 comment，也不替代 run-111 长产品
differential、答案质量或 MVP 验证。

规范依据：

- 火山引擎 Chat Completions：<https://api.volcengine.com/api-docs/view?action=ChatCompletions&serviceCode=ark&version=2024-01-01>
- WHATWG Server-sent events：<https://html.spec.whatwg.org/dev/server-sent-events.html>
