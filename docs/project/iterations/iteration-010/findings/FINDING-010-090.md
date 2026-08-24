---
id: FINDING-010-090
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [quality, project]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-089]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: individual
disposition: deepseek-account-balance-hold-after-fresh-run-034
target: ITER-010-VERIFICATION
---

# FINDING-010-090：run-034 fresh Conformance 仍收到 DeepSeek HTTP 402

## Observation and evidence

`FINDING-010-089` 后的 clean candidate commit 为 `fe6b6b6e99251624e2fb9042714b04cb2b85af28`、tree
`fa0b4299d8d9fab3d5e0e450bd94b99a0971fc70`，归档 SHA-256 为
`097332c700238a2691945e5884e1c60561eaa041eabc4b468e8acad73abdda78`。product 与 exact mall
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` 两份 detached checkout 均 clean。

用户明确表示已充值后，run-034 从该新候选执行 fresh DeepSeek Conformance。第一条 exact `deepseek-v4-pro` request 已完成
credential resolution 1/1、verified TLS handshake 1/1、HTTP dispatch 1；Provider 返回 HTTP `402`，sanitized failure 为
`PROVIDER_HTTP_ERROR / invalid_request_error / unknown_error`。没有 actual model fingerprint、provider request ID 或 token usage。
transport audit 记录 retry 0、connection reuse 0、post-dispatch outcome unknown 0。

Conformance run ID 为 `ccrun_0d6e38d297b94e2d95cacd40ad38ce94`，result digest 为
`sha256:f13d2e0afe3ea3dc41b1b2cf25a11f34d038c14a1e2891dfac283daba26e6215`。Result 以 `FAIL` 密封；第二个 canary request 未发送，
没有 Qualification。由于用户仍冻结 request retry 0，不能再次发送同一请求、切换 Provider 或把另一 run 伪装成该 dispatch 的 retry。

run-034 没有生成 Alpha Session Authority、没有启动 listener、没有 Browser submission、没有发送任何 mall/World Model/角色输入，
Production Activation 为 `NOT_EXECUTED`。这不是 `FINDING-010-088` 代码修复的回归，也没有证据表明充值已对当前
`env:DEEPSEEK_API_KEY` 所属账户生效。

## Decision and disposition

- run-034 永久保持 fresh Conformance FAIL；不得复用 run-033 Conformance 或启动未资格化 Alpha。
- clean candidate `fe6b6b6…` 与 deterministic Gate 仍有效，但 live Gate 保持 blocking。
- 当前外部 hold 只能由当前 `DEEPSEEK_API_KEY` 所属账户恢复可用余额来解除。确认后必须启动新的 fresh Conformance run；零重试、
  Provider switch 0、resources/credential exclusion 和 Production `NOT_EXECUTED` 均不变。
