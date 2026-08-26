---
id: FINDING-010-114
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [ai, security, operations, quality, project]
depends_on: [FINDING-010-112, FINDING-010-113, SYS-ADR-017, SYS-ADR-018]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: systemic
disposition: preserve-fresh-dual-provider-conformance-for-the-exact-run-037-product
target: ITER-010-VERIFICATION
---

# FINDING-010-114：run-037 exact product 的 fresh 双 Provider Conformance 通过

## Authority and exact identity

用户以 `codex-user-message:sha256:8ebd3650ea8c82ad43dc5015f633cd4e9b0dd3a39a81a6ddfb1566dc6c80d13a`
授权 clean product commit `d429be6c7e5e43342bf427e394ca5babcc55bcdb` / tree
`400d5791e4c443c201765da5f488519093136738` 的 fresh Ark→DeepSeek Conformance，并把后续 artifact/Live 明确条件化为两条 route
均 PASS。该授权固定每条 route 2 次 HTTP/model request、request retry 0，排除 mall Source/resources、Browser 和 Production Activation。

DeepSeek fresh run `ccrun_51602243de5c42779a2529c25f241923` 形成 owner-private Result
`sha256:5fe0a06f253a3865325738a63c00f9fd659cd96c25aa764c76a3ec2914646b6c`：2/2 request、12/12 Case PASS，
requested/actual model 均为 `deepseek-v4-pro`，TLS 1/1、credential 2/2、HTTP 2、connection reuse 1、request retry 0、
post-dispatch outcome unknown 0；有效期至 `2026-09-25T08:18:50.616197Z`。Result 文件 SHA-256 为
`63bf5582867855ea9279619c5eabcef23ef387f590c897b9c03cc722ce1ede4c`，raw prompt/response 均未持久化。

首次 Ark run 在 credential resolution 和 HTTP dispatch 前发生独立 TLS acquisition failure，没有生成资格 Result。用户随后以
`codex-user-message:sha256:e89640faf226ce069216ba40c71448dac0d8e09faf898aacbe74577067d540b3` 授权仅在 credential 0、
HTTP dispatch 0 时重新启动 fresh run；又以
`codex-user-message:sha256:21786af7d671472735a0cf7f064a26a7e19030b8ca6291c14f83ca1c1bfdfae1` 将该补充授权的
credential-free pre-dispatch TLS acquisition 总上限从 3 提高到 10，当时已使用 2、剩余 8。补充授权最终共使用 4/10 次 acquisition：
前 2 次各在 credential/HTTP 之前失败，后 2 次属于同一个成功 fresh run；没有在 HTTP dispatch 或 outcome unknown 后重跑。

Ark fresh run `ccrun_afd4fee16aab430e9332b7ab0cc633fd` 形成 owner-private Result
`sha256:bbaf5611a46d68400d0ee4da4f5994deeb8bffecbeead07b7db26b40cbe4b114`：2/2 request、13/13 Case PASS，
requested `glm-5-2-260617`、actual `glm-5.2`，TLS/credential/HTTP 均 2/2、connection reuse 0、request retry 0、
post-dispatch outcome unknown 0；有效期至 `2026-09-25T08:55:23.155945Z`。Result 文件 SHA-256 为
`30f76ca78c45a94ccc71fec0284580921ed280ce48fccb1094c8324c7f66b326`，raw prompt/response 均未持久化。

## Disposition

两份 Result 只资格化 exact `d429be6…` / `400d579…` 当时的 Adapter、configuration、strategy/prompt/input identity，允许条件式
`run-037-chat-alpha` 启动。它们不证明五轮答案质量，也不授权任何 successor code、重复 Conformance 或 Production Activation。
本次 Conformance 没有读取 mall Source/resources，没有启动 Browser，credential value 未进入 Result，Production Activation 为
`NOT_EXECUTED`。
