---
id: FINDING-010-126
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [ai, security, operations, quality, project]
depends_on: [FINDING-010-125, SYS-ADR-017, SYS-ADR-018]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: systemic
disposition: preserve-fresh-dual-provider-conformance-for-the-exact-run-041-product
target: ITER-010-VERIFICATION
---

# FINDING-010-126：run-041 exact product 的 fresh 双 Provider Conformance 通过

## Authority and exact identity

用户授权 product commit `6e97bc1c0c02be858212c39da11ac42e099c365e` / tree
`fd54821e212b3022e318436d9e96b93af11505c6` 按 Ark→DeepSeek 执行 fresh Conformance。每条 route 固定 2 次
HTTP/model request、request retry 0；只有 credential resolution 0 且 HTTP dispatch 0 的 TLS 失败可以 fresh restart，一旦发生 HTTP
dispatch 或 outcome unknown 不得重跑。授权允许解析既定 credential reference，但不允许披露 credential value。本地 artifact 将这条
exact user message 的 UTF-8 内容密封为
`sha256:bed1ccdca788bfaad0c1f8581f538b19d7007da81388a8c8763968f6fdbce8c6`；该 digest 是本地密封值，不冒充平台生成的消息收据。

Ark 前两个 fresh attempt 都在 credential resolution 与 HTTP dispatch 前以 `PROVIDER_UNAVAILABLE / TLS_FAILURE` 关闭，请求数均为 0，
因此分别满足用户定义的 fresh replacement 条件。第三个 fresh run `ccrun_b326cb9b2b414b92b87d4d951d19260e` 形成 owner-private Result
`sha256:b81a9f514bcc4a962732ea873e33fa61ba37a377c11848d6afddfae67a6f4c88`：2/2 request、13/13 Case PASS，requested
`glm-5-2-260617`、actual `glm-5.2`，request retry 和 post-dispatch outcome unknown 均为 0；TLS/credential/HTTP 为 `2/2/2`，
connection reuse 为 0，有效期至 `2026-09-25T12:17:35.869882Z`。Result 文件 SHA-256 为
`62a1540ee5f094e339d6fb259621262514b41c504b74eafb7caba409808166b4`。

DeepSeek fresh run `ccrun_2ac5b6fcdb254b8ea3c75243968fbab0` 随后形成 owner-private Result
`sha256:a6cae82aeff8da0b318c235da918ce7982d1eaec3875a234ed49722e5ae3fedd`：2/2 request、12/12 Case PASS，
requested/actual model 均为 `deepseek-v4-pro`，request retry 和 post-dispatch outcome unknown 均为 0；TLS `1/1`、credential/HTTP
`2/2`、connection reuse 1，有效期至 `2026-09-25T12:17:56.327516Z`。Result 文件 SHA-256 为
`cf6d22dd78c5d7b6c1e1f4fee17c21b8028a47ef246929ec875e7c3c8adf6cee`。

## Disposition

两份 Result 只资格化 exact `6e97bc1…` / `fd54821…` 的当时实现、configuration 与
`conversational-engineering-agent@5` model contract，并满足同一用户授权中启动 `run-041-chat-alpha` 的先决条件。它们不证明五轮
Chat 质量，也不能资格化后续 v6 strategy/prompt/Primary input identity。Conformance 没有读取或披露 mall Source/resources，没有启动
Browser；credential value 未进入 Result，Production Activation 为 `NOT_EXECUTED`。
