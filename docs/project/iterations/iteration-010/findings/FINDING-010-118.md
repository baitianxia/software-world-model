---
id: FINDING-010-118
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [ai, security, operations, quality, project]
depends_on: [FINDING-010-116, FINDING-010-117, SYS-ADR-017, SYS-ADR-018]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: systemic
disposition: preserve-fresh-dual-provider-conformance-for-the-exact-run-038-product
target: ITER-010-VERIFICATION
---

# FINDING-010-118：run-038 exact product 的 fresh 双 Provider Conformance 通过

## Authority and exact identity

用户以 `codex-user-message:sha256:338979f81e29b0d53ddcc86fc5d35cc3a78f6cd671d977a864b5142d62dc352a`
授权 product commit `743942d2593615c5c481110465d7d7faaf41d958` / tree
`748902ce407c434e10f4926cf84b1240a2666424` 按 Ark→DeepSeek 执行 fresh Conformance。每条 route 固定 2 次
HTTP/model request、request retry 0；只有 credential resolution 0 且 HTTP dispatch 0 的 TLS 失败可以 fresh restart，一旦发生 HTTP
dispatch 或 outcome unknown 不得重跑。授权允许解析既定 credential reference，但不允许披露 credential value。

Ark fresh run `ccrun_9f11b0ffe92d409ab6019a432fba9954` 一次完成，没有使用 fresh restart。owner-private Result
`sha256:ef4787881e0cd87a8642088cf1e0165e5a33bb109691965003bb14914b7c4753` 记录 2/2 request、13/13 Case PASS，
requested `glm-5-2-260617`、actual `glm-5.2`，request retry 和 post-dispatch outcome unknown 均为 0；有效期至
`2026-09-25T09:48:37.836520Z`。Result 文件 SHA-256 为
`53176fc2f83d3b2c90b802f8913fd795939ee93dceda25ee90b321e79ecb504c`。

DeepSeek fresh run `ccrun_9bd978e5b6b6474cba4a075ea4f30689` 随后形成 owner-private Result
`sha256:aec00111e27f329fd4291cbec01476c180e0820d1787e7e6877c2fa71e8757d9`：2/2 request、12/12 Case PASS，
requested/actual model 均为 `deepseek-v4-pro`，request retry 和 post-dispatch outcome unknown 均为 0；有效期至
`2026-09-25T09:49:06.407813Z`。Result 文件 SHA-256 为
`cf38957f259197adc282cfc1e812647945d1f0b052649a5fc736439c2e8db815`。

## Disposition

两份 Result 只资格化 exact `743942d…` / `748902c…` 的当时实现、configuration 与
`conversational-engineering-agent@3` model contract，并满足同一用户授权中启动 `run-038-chat-alpha` 的先决条件。它们不证明五轮
Chat 质量，也不能资格化后续 v4 strategy/prompt/input identity。Conformance 没有读取或披露 mall Source/resources，没有启动 Browser；
credential value 未进入 Result，Production Activation 为 `NOT_EXECUTED`。
