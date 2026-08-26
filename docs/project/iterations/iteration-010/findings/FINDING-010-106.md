---
id: FINDING-010-106
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [ai, operations, quality, project]
depends_on: [FINDING-010-105, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-OPS-CONFIGURATION]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: systemic
disposition: dual-provider-conformance-pass-session-authority-required-before-artifact
target: ITER-010-VERIFICATION
---

# FINDING-010-106：fresh DeepSeek Conformance 通过，双 Provider qualification 当前可用

## Observation and evidence

用户以 `codex-user-message:sha256:ea4f3ac231cc6c88d412336ddfb9e2cecefcd30b1343f455a3cc2fcf5480c772`
精确授权在 clean commit `653eff385a8da58d29b77b86cf23297f73100e9c`、tree
`d0cab3af62fa24de571015ba6f0c9b431b6171b0` 上执行一次 fresh DeepSeek Conformance：exact `deepseek-v4-pro` endpoint、固定 2 次
HTTP model request、request retry 0、transport lifetime 最多 3 次 credential-free pre-dispatch TLS acquisition；同时禁止 mall
Source/resources、Browser 与 Production Activation。

`2026-08-26T01:22:38.391160Z—01:22:41.700955Z` 实际运行 `CC-DEEPSEEK-CHAT-NO-TOOLS-001 / fixture 1.2.0 /
result @2`，run ID 为 `ccrun_a8e9fd5247f44e559d05e84a3813accf`。12/12 Case PASS；两个 request 返回互异 Provider request ID，
actual model identity 均闭合为 `deepseek-v4-pro`，usage 为 input 418 / output 73。Result digest 为
`sha256:3e43921a5e0ebf00d0805b7c66f609c29b0d29a3fd8b848a8b3e491e641e6a4d`，文件 SHA-256 为
`bd2f598fae196dedc48b9cc4e94d1c4fca7d02240a0cf473f2c0451949f71aa1`，mode 为 `0600`，有效期到
`2026-09-25T01:22:41.700955Z`。owner-private evidence path 为
`var/conformance/CC-DEEPSEEK-CHAT-NO-TOOLS-001-ccrun_a8e9fd5247f44e559d05e84a3813accf.json`。

strict persistent transport Session audit 为 TLS attempts/successes `1/1`、credential resolutions/successes `2/2`、HTTP dispatch `2`、
connection reuse `1`、request retry `0`、post-dispatch outcome unknown `0`；transport 没有消耗第二或第三次 credential-free TLS acquisition。
sealed Result 明确记录 `raw_prompt_persisted=false / raw_response_persisted=false`，current verifier 与 qualification loader 均 PASS。

结合 `FINDING-010-105`，current exact Ark 与 DeepSeek Adapter/Configuration/endpoint/model/transport qualification 现在同时可用。两份
Conformance 只证明 Provider compatibility/identity 与 transport policy，不是 Chat Capability、答案质量、Browser 或 Production PASS。
本次外部活动恰好是授权的两次 DeepSeek call；没有 Ark call、same-request retry、mall Source/resources 读取或披露、listener/browser 或
Production Activation。

## Decision and disposition

- Provider Gate 更新为 `ARK_CONFORMANCE_PASS / DEEPSEEK_CONFORMANCE_PASS / DUAL_PROVIDER_QUALIFICATION_CURRENT`。
- current owner-private artifact 仍不能由本 Conformance grant 生成：artifact 中的 Session authority 将预授权五轮 Turn、Ark→DeepSeek
  disclosure、World Model/Source Profile 和 live bounds，而本次 grant 明确禁止 mall Source/resources 与 Browser。不得把 Conformance grant
  扩张为 Session disclosure/live authority。
- 下一最早 Gate 是取得 current exact five-Turn Session authorization；之后才可读取已发布 World Model projection、生成 artifact、执行零活动
  preparation，并在同一授权边界内启动 fixed listener/browser canary。`src/main/resources`、credential value 与 Production Activation 继续排除。
- `V-CHAT-*`、答案质量、Acceptance 与 Production Activation 全部继续 `NOT-RUN / blocking`。
