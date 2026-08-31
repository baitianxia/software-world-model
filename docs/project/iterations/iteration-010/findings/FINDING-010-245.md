---
id: FINDING-010-245
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [operations, ai, quality]
depends_on: [FINDING-010-244, ITER-010-PDR-007, ITER-010-PDR-008, ITER-010-VERIFICATION, SYS-CONTRACT-AI-MODEL-GATEWAY]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: individual-case
disposition: retain-low-effort-repair-and-retry-ark-after-bounded-delay-without-retrying-delivered-requests
target: ITER-010-VERIFICATION
---

# FINDING-010-245：run-112 证明 low-effort 链路有效，随后由 Ark 预投递 TLS 与 DeepSeek HTTP 402 关闭

## Observation and evidence

run-112 绑定 product commit/tree
`aef6a353afd4cd9b8cb6d4f00a52e6c5b294f039 / 8f1d74050ea1033acf592457d40a3a0167b34f10`、Session/Turn-scope file SHA-256
`0e89e07c9c1b9ef0dff6e65d552385c7d9bf3c936d57a71fcfb3a02d95fa0ac1 /
3d183082c0294d33903d48ce30249b1d5e7b0828796cea89dc364373e60ba341` 与 fresh `@12 / 1.12.0` qualification。Browser 在 fresh Conversation
`conversation_6d8e5f1bc45248e1b5838a27343b5ba4` 提交相同 Q4。

low-effort wire 已形成直接产品证据：前四个 Ark calls 全部 `stop` completed、actual model `glm-5.3`、Usage 完整，input/output tokens 依次为
`9969/542`、`15463/581`、`41286/934`、`46128/1071`。对应 Agent action 依次为 `WORLD_MODEL_QUERY`、`SOURCE_SEARCH(EsProduct)`、
两次不同 opaque locator 的 `SOURCE_READ`。run-111 的 `8192 / length / JSON truncated` 与笼统 parser rejection 均未复现，证明
`reasoning_effort=low` 已把当前最早分歧越过到后续 Source investigation；它仍未产生 Draft/Review/Delivery，故不构成答案质量或 MVP PASS。

第五个 Ark attempt `model_call_152caed2758d4f5d9910501bf267e04f` 在 credential 和 HTTP 前由 exact transport 以
`TLS_FAILURE / PROVIDER_UNAVAILABLE` 失败。Session audit 为 TLS attempt/success `5/4`、credential `4/4`、HTTP `4`、post-dispatch unknown 0、
retry 0。该 pre-dispatch unavailable 被 trusted route owner 密封后，系统首次依法激活 DeepSeek fallback；这不是重放前四个 completed calls，
也没有重发第五个未投递 HTTP request。

DeepSeek fresh off-peak admission 在 `2026-08-31T15:05:13.824762Z` 通过并授权一次 dispatch。TLS/credential/HTTP 均 `1/1/1`，Provider
明确返回 HTTP `402`，清洗后的 `provider_error_code/type` 为 `invalid_request_error / unknown_error`，没有 provider request ID；call
`model_call_efb7729a90224487b6a4804d932f673c` 以 `PROVIDER_HTTP_ERROR` 失败。raw error body 按安全合同未持久化，故不能把 402 的具体账户、余额、
套餐或账单原因冒充已确认；它是 definite HTTP rejection，不是 network/outcome unknown，不允许同 request retry。

Turn 以 Provider dispatch `6` 失败关闭，Conversation 保持 ACTIVE，Production `NOT_EXECUTED`。terminal receipt digest 为
`sha256:84bd391d8e848e289ef38aa80c9fd6faaa0ecf6a8641bf40cd7a975f9ea06a6c`；terminal/Ark DB/DeepSeek DB file SHA-256 分别为
`fb9848b16a7ff4be72b6e565c9ccd5b68018743cdf7493ea0e4d2f476d63d15b /
ea865619455a50c425eaaad42d2d8812c72da31de1e9772493b99673bc2e2824 /
1644c17b0ddc9c8fd7191f4e1d2dce4da197e162d4034c24f968ad390a804b2e`。

## Decision and disposition

1. `FINDING-010-244` 的 `@12 / reasoning_effort=low` repair 保留；run-112 的四个 completed calls 已证明它解决当前输出预算分歧，不因后续
   环境故障撤回或改写。
2. Ark 第五次失败明确发生在 HTTP 前，且前四次已成功；按用户允许的周期性网络重试与 standing authority，可在 bounded delay 后创建 fresh
   run-113 并重新执行该冻结产品问题。它是新的受审计 Turn，不是 same-request transport retry；所有已完成/已拒绝请求仍保持 retry 0。
3. DeepSeek 402 不改变 off-peak schedule 判断，也不证明 DeepSeek 网络不可用。除非外部账户状态改变，后续 trusted Ark unavailable 仍可能得到
   同一 definite fallback rejection；系统不得绕过 HTTP evidence、伪造 Provider request ID 或把 402 当答案失败后换模型的理由。
4. 本 finding 不改变代码、System contract、budget、route、source、披露、loopback 或 Production；它只更新当前运行证据和下一运行安排。
   run-113 启动前仍需 fresh pricing、exact Session artifact 与 plan snapshot。

## Verification

run-112 Browser 与两个 private Gateway repositories、launch/terminal receipts 交叉一致：Ark completed `4`、pre-dispatch unavailable `1`、
DeepSeek HTTP failure `1`、total provider dispatch `6`、request retry `0`、post-dispatch unknown `0`、human approval request `0`、Production
`NOT_EXECUTED`。该运行验证了 fallback 只在 trusted Ark unavailable 后激活，也揭示了 DeepSeek 当前 definite HTTP 402 阻断；没有 Draft、Review、
Delivery 或 MVP verdict。
