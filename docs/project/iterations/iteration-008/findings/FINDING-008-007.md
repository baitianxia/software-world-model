---
id: FINDING-008-007
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai, quality, security]
depends_on: [ITER-008-SLICE-001, FINDING-008-005, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-QUALITY-SECURITY]
code: [validation/structure_world_model_iteration_008/capability/cli.py]
tests: [tests/test_iteration_008_capability_harness.py]
iteration: ITER-008
classification: local-implementation
disposition: seal-provider-outcome-unknown-before-returning-control
target: validation/structure_world_model_iteration_008/capability/cli.py
---

# FINDING-008-007：未知 Provider 结果必须形成不可重试的 terminal evidence

## Observation

用户对 run-001 preflight 的一次性 2-call Conformance 授权被实际执行后，CLI 返回
`PROVIDER_OUTCOME_UNKNOWN`，但旧 runner 只在首次分派前写入 `invocation.json`。异常到达顶层时没有写入 `failure.json` 或
`terminal.json`，也没有保留 transport 的失败原因和已尝试请求数。因此 run-001 只能证明授权已经消费且执行过 1—2 次调用，不能从密封
证据恢复究竟是第 1 次还是第 2 次调用结果未知，也不能恢复网络原因码。

## Evidence

- exact candidate commit 为 `872d1e9ec6bd185dd05aa2974a33faf2ef509d5b`，tree 为
  `c1b2f39feb7b72bd1b979076ec051b3756932041`；preflight digest 为
  `sha256:ce95cf496e0a0a2d22281640564bef8014992111bacfec715dd05ac4fa396f26`；
- 用户授权只绑定上述 freeze、恰好 2 次 synthetic Conformance call、零 retry；authorization digest 为
  `sha256:2300df70f71f767c9ea9ba28add2e2fb310c81a4403c35f03d73cf50f1c7ebe4`；
- 实际 CLI 以 exit code 2 返回 `PROVIDER_OUTCOME_UNKNOWN`，未执行 hidden canary、产品题、Source/Evidence 读取或 Production
  Activation；
- run-001 结果目录只包含 digest 为
  `sha256:1994085d47252b26cc76b956b4d71d934552addee55e210dfeb37bab4384d6f0` 的 `invocation.json`；不存在
  terminal、failure 或 Conformance Result；
- credential status 只证明当前 `@8` 配置已配置 credential，不能证明网络失败原因，也不能补造缺失的调用计数；
- Conformance runner 顺序执行两次调用并在未知结果时退出，所以现有证据只支持闭区间 1—2 次。任何更精确数字或原因都是推测。

## Impact and classification

未知 Provider 结果不可自动重试、授权必须单次消费、credential 和原始 payload 不得进入证据，这些规则已由现有 System Contract 和
Security 质量规则拥有。缺陷只在 ITER-008 validation runner 没有把 transport 层事实写入失败闭包；没有改变生产 Owner、Provider
协议或调用方语义，因此分类为 `local-implementation`。

run-001 授权已经消费，禁止用修复后的代码重放。由于它没有 PASS Conformance Result，39-call Capability Gate 继续关闭。

## Decision and disposition

Conformance 与 Capability runner 都在首次分派前安装只记录非秘密 wire body 的 dispatch audit。遇到未知结果时，先一次性写入：

- attempted Provider request count；
- 每个请求体的 SHA-256 digest，不写原始 prompt/response 或 credential；
- transport 保留的精确原因码；
- `authorization_consumed: true` 与 `retry_permitted_with_same_authorization: false`；
- 显式 `PROVIDER_OUTCOME_UNKNOWN` terminal。

Capability 的 Model Gateway 会把 transport 异常归一化成拒绝资格的 Domain Error；runner 在该边界保留原始原因后再恢复成顶层
`ProviderOutcomeUnknown`，避免把网络未知误报成普通 capability failure。成功闭包同时以 dispatch audit 验证 exact 39-call count；output
计数与实际分派不一致时不得密封 qualification proof。

旧 run-001 证据保持原样。下一次尝试必须先提交修复，生成绑定新 exact candidate 的零调用 preflight，并取得新的显式 2-call 授权。

## Verification after disposition

- Conformance unknown fixture：恰好尝试 1 次，密封 reason、request digest、failure 和 terminal，原授权不可重试；
- Capability unknown fixture：异常即使经 Model Gateway 归一化，仍以原始原因和 exact attempt count 失败闭合；
- 合法 fake chain 仍恰好完成 2 次 Conformance 和 39 次 Capability call；
- failure evidence 不包含 fixture credential、原始 prompt 或原始 response。
