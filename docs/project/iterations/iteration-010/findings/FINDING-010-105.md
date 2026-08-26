---
id: FINDING-010-105
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [ai, operations, quality, project]
depends_on: [FINDING-010-104, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-OPS-CONFIGURATION]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: systemic
disposition: ark-conformance-pass-deepseek-requalification-required-before-artifact
target: ITER-010-VERIFICATION
---

# FINDING-010-105：fresh Ark Conformance 通过，artifact Gate 转移到 DeepSeek requalification

## Observation and evidence

用户以 `codex-user-message:sha256:c5e3b3469196bf5fe46118a5bc2d6943e2509adb0bfb6008aa2071fac94f553a`
精确授权在 clean commit `1e99e9bf7a9a2f982efefd6828437b335b05d31b`、tree
`b56a332a87e8da8bf1a25cab034f4842a547641c` 上执行一次 fresh Ark Conformance：固定 2 次调用、同 request retry 0，且不读取或披露
mall Source/resources、不启动 Browser、不执行 Production Activation。

`2026-08-26T01:00:34.355079Z—01:00:39.148494Z` 实际运行 `CC-ARK-CHAT-NO-TOOLS-001 / fixture 1.7.0 /
result @2`，run ID 为 `ccrun_b152115579ca4d9ab192c65471386a19`。13/13 Case PASS；两个 request 返回互异 Provider request ID，
actual model identity 均闭合为 `glm-5.2`，usage 为 input 316 / output 69。Result digest 为
`sha256:d0e9d49f234b770f9c22ad38276622f04168cbb17e1cada3b18586431ba40a15`，文件 SHA-256 为
`b3775bdc0b40dde12b94c0d7b556b014430626bd1b21c67c9faae0f1bce79e74`，mode 为 `0600`，有效期到
`2026-09-25T01:00:39.148494Z`。owner-private evidence path 为
`var/conformance/CC-ARK-CHAT-NO-TOOLS-001-ccrun_b152115579ca4d9ab192c65471386a19.json`。

strict transport Session audit 为 TLS attempts/successes `2/2`、credential resolutions/successes `2/2`、HTTP dispatch `2`、connection
reuse `0`、request retry `0`、post-dispatch outcome unknown `0`；每个 request 使用独立 verified TLS session。sealed Result 明确记录
`raw_prompt_persisted=false / raw_response_persisted=false`，当前 verifier 与 qualification loader 均 PASS。该 Result 只资格化 exact Ark
Adapter/Configuration/endpoint/model/transport identity，不是 Capability、Chat Quality、Browser 或 Production PASS。

artifact Session 同时要求 current Ark 和 DeepSeek qualification。复核发现 DeepSeek Conformance implementation manifest 也包含本次修改的
`model_gateway.py`：current aggregate digest 已为
`sha256:a680b0c8d99ce320dd9abc2096bef90d98420490e441b352e9a2994b741dbb07`，本机所有仍在有效期内的旧 PASS Result 使用
`sha256:1022fdd1044d7b71ce53ad1c61a9fc81f1a89652ae7fc15b5ae365d77b3c3d4b`。current loader 实际以
`QUALIFICATION_INVALID / DeepSeek conformance result is stale for the current implementation or configuration` 拒绝旧 Result；run-034 又是
既有 FAIL，不能提供 qualification。因此 Ark PASS 后仍不能生成 current dual-route artifact。

本次外部活动恰好是授权的两次 Ark call，没有 DeepSeek call、same-request retry、mall Source/resources 读取或披露、listener/browser 或
Production Activation。

## Decision and disposition

- Ark route 状态更新为 `CONFORMANCE_PASS / CURRENT_QUALIFICATION_AVAILABLE`；旧 Ark Result 继续保持 stale，不得替代本 Result。
- current dual-route artifact 的下一最早 Gate 精确改为 fresh DeepSeek Conformance。它必须另有当前 exact endpoint、2-call、zero-retry
  授权；不能把历史 unlimited-call permission、Ark grant 或旧 DeepSeek Result 扩张为新 dispatch 权力。
- fresh DeepSeek PASS 后才生成 current owner-private artifact；artifact preparation 本身必须保持 Source read、credential、Provider dispatch、
  listener/browser 和 Production Activation 全部为 0。五轮 Chat 仍须之后单独取得 exact Session disclosure/browser grant。
- `V-CHAT-*`、答案质量、Acceptance 与 Production Activation 全部继续 `NOT-RUN / blocking`。
