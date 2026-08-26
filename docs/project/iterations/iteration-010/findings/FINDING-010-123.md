---
id: FINDING-010-123
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [ai, security, operations, quality, project]
depends_on: [FINDING-010-120, FINDING-010-121, SYS-ADR-017, SYS-ADR-018]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: systemic
disposition: preserve-fresh-dual-provider-conformance-for-the-exact-run-040-product
target: ITER-010-VERIFICATION
---

# FINDING-010-123：run-040 exact product 的 fresh 双 Provider Conformance 通过

## Authority and exact identity

用户授权 product commit `34d98ae12fe7429afb3cbe391d273c59a71c4758` / tree
`b9100b15a2db30da811157549fc1f2d9affff288` 按 Ark→DeepSeek 执行 fresh Conformance。每条 route 固定 2 次
HTTP/model request、request retry 0；只有 credential resolution 0 且 HTTP dispatch 0 的 TLS 失败可以 fresh restart，一旦发生 HTTP
dispatch 或 outcome unknown 不得重跑。授权允许解析既定 credential reference，但不允许披露 credential value。本地 artifact 将这条
exact user message 的 UTF-8 内容密封为
`sha256:6834f6854008a41355d5dacff7c7aaad6edb56c9e915f9097ad14c82f5447ce4`；该 digest 是本地密封值，不冒充平台生成的消息收据。

Ark 首次 fresh attempt 在 credential resolution 与 HTTP dispatch 前以 `PROVIDER_UNAVAILABLE / TLS_FAILURE` 关闭，request count 为 0，
因此按授权启动一次 fresh replacement。成功 run `ccrun_91d98e319cb0426da0ab8dd5080e76eb` 的 owner-private Result
`sha256:8c179dd2e7d00fb4a8177557b3716c254ccfab7911e8ed46e78df6ebd8f728cd` 记录 2/2 request、13/13 Case PASS，
requested `glm-5-2-260617`、actual `glm-5.2`，request retry 和 post-dispatch outcome unknown 均为 0；TLS/credential/HTTP 为
`2/2/2`，connection reuse 为 0，有效期至 `2026-09-25T10:43:47.159999Z`。Result 文件 SHA-256 为
`79e34bd48f749be3e576f9f53c58bdde6303706490bae88f2b2d5d0cbe4b81fa`。

DeepSeek fresh run `ccrun_b7f51506fb5b4f9d8d9a8cdaaa532dd8` 随后形成 owner-private Result
`sha256:a61f7eafa4d6caa42b33d54fd41386d065abb14dd0302b16f665dfb725a54e92`：2/2 request、12/12 Case PASS，
requested/actual model 均为 `deepseek-v4-pro`，request retry 和 post-dispatch outcome unknown 均为 0；TLS `1/1`、credential/HTTP
`2/2`、connection reuse 1，有效期至 `2026-09-25T10:44:16.953081Z`。Result 文件 SHA-256 为
`9f6eae0dc70121f62e67e55c037fc1d427172d9a0e2b2c9b0562e850ddff7a64`。

## Disposition

两份 Result 只资格化 exact `34d98ae…` / `b9100b1…` 的当时实现、configuration 与
`conversational-engineering-agent@4` model contract，并满足同一用户授权中启动 `run-040-chat-alpha` 的先决条件。它们不证明五轮
Chat 质量，也不能资格化后续 v5 strategy/prompt/Primary input identity。Conformance 没有读取或披露 mall Source/resources，没有启动
Browser；credential value 未进入 Result，Production Activation 为 `NOT_EXECUTED`。
