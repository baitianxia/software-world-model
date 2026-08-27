---
id: FINDING-010-129
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [ai, security, operations, quality, project]
depends_on: [FINDING-010-128, SYS-ADR-017, SYS-ADR-018]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: systemic
disposition: preserve-fresh-dual-provider-conformance-for-the-exact-run-042-product
target: ITER-010-VERIFICATION
---

# FINDING-010-129：run-042 exact product 的 fresh 双 Provider Conformance 通过

## Authority and exact identity

用户授权 product commit `3b8d09c71796e3c9b91ec6a9ea21697497319bbc` / tree
`6728a5ad63bedf65b1315cb7d7fdf27f111dc0d9` 按 Ark→DeepSeek 执行 fresh Conformance。每条 route 固定 2 次
HTTP/model request、request retry 0；只有 credential resolution 0 且 HTTP dispatch 0 的 TLS 失败可以 fresh restart，一旦发生 HTTP
dispatch 或 outcome unknown 不得重跑。授权允许解析既定 credential reference，但不允许披露 credential value。本地 artifact 将这条
exact user message 的 UTF-8 内容密封为
`sha256:df3cfe58d7a728899e7294a0c26ced0fb9e175f16334a904a1d70ca345d40ee9`；该 digest 是本地密封值，不冒充平台生成的消息收据。

## Fresh qualification results

Ark fresh run `ccrun_ff7b99cf964f43589f5536e5a9fdfd29` 一次形成 owner-private Result
`sha256:10e4b875b933b12b848b8b08dafa7d59bc5770fb18ec0ae19f455a18ce9944e2`：2/2 request、13/13 Case PASS，requested
`glm-5-2-260617`、actual `glm-5.2`，request retry、pre-dispatch TLS failure 与 post-dispatch outcome unknown 均为 0；
TLS/credential/HTTP 为 `2/2/2`，connection reuse 为 0，有效期至 `2026-09-25T14:50:05.091986Z`。Result 文件 SHA-256 为
`3d59fbd5554aa42109e2eef48e491785c8e4103aa23cc6f8a7ddfd76791259ea`，mode 为 `0600`。没有发生 fresh restart。

DeepSeek fresh run `ccrun_4d8cc3ebefb3401a87a6c60165ba70d0` 随后一次形成 owner-private Result
`sha256:85cfe117920bccd403c96578e42f49dc5eca1afcb551b20c707a14eb41e8dd3b`：2/2 request、12/12 Case PASS，
requested/actual model 均为 `deepseek-v4-pro`，request retry、pre-dispatch TLS failure 与 post-dispatch outcome unknown 均为 0；TLS
`1/1`、credential/HTTP `2/2`、connection reuse 1，有效期至 `2026-09-25T14:50:31.180603Z`。Result 文件 SHA-256 为
`dbdb9b89b81a8edf9e9b49ecb6bd845b18e00bce981c662e687e44b90d2374ed`，mode 为 `0600`。没有发生 fresh restart。

## Disposition

两份 Result 只资格化 exact `3b8d09c…` / `6728a5a…` 的当时实现、configuration 与
`conversational-engineering-agent@6` model contract，并满足同一用户授权中启动 `run-042-chat-alpha` 的先决条件。它们不证明五轮
Chat 质量，也不能资格化 `FINDING-010-131` 的 v7 strategy/prompt/Primary/Review input。Conformance 没有读取或披露 mall
Source/resources，没有启动 Browser；credential value 未进入 Result，Production Activation 为 `NOT_EXECUTED`。
