---
id: FINDING-007-002
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, architecture, security]
depends_on: [ITER-007-SLICE-001, SYS-QUALITY-SECURITY, SYS-ARCH-FLOWS, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING]
code: [src/software_world_model/ai_infrastructure/pinned_ark_https.py, src/software_world_model/interface/world_model_runtime.py, src/software_world_model/interface/world_model_runtime_assets/java_source_semantics_gateway_workload.py]
tests: [tests/test_pinned_ark_https.py, tests/test_world_model_evaluation_grant.py, tests/test_world_model_gateway_authorization.py]
iteration: ITER-007
classification: system-contract
disposition: require-one-preconnected-provider-socket-per-authorized-model-call
target: SYS-QUALITY-SECURITY
---

# FINDING-007-002：三调用协议需要三个独立的预连接 Provider socket

## Observation

ITER-006 的正式运行器按每题一个 Provider 调用设计，只向 Gateway child 交接一个预连接 socket。ITER-007 的
`JAVA_SOURCE_SEMANTICS@1` 固定为 Plan、Draft、Review 三次独立调用；固定 Ark HTTPS transport 在每个请求中发送
`Connection: close`，因此一个 descriptor 不能安全、确定地承载三次调用。

## Evidence

- `pinned_ark_https.py` 的请求头固定为 `Connection: close`，每次调用最终关闭 TLS/raw socket；
- 三 descriptor transport 回归证明三次调用按传入顺序各消费一个 descriptor，第四次调用失败关闭；
- semantic Gateway workload 拒绝少于、超过或重复的 descriptor，并要求 Provider/network count 精确为 3；
- runtime 的授权与 terminal audit 分别记录 supervisor connection provisioning、listener handoff、Provider call 和 network
  operation，三调用 Profile 的各项数量必须精确为 3；
- Answer 仍不持有 credential 或公网 capability，Gateway child 仍被 syscall firewall 禁止创建新 socket。

## Impact and classification

这不是单一 transport 实现细节：它改变正式 Web 启动前必须授予 Gateway 的网络 capability 数量，并影响授权收据、审计和
失败条件，分类为 `system-contract`。影响仅限取得新资格的三调用 Profile；旧单调用 Profile 保持一个 descriptor，不追溯修改
其已接受结果。

## Decision and disposition

每个已授权 Provider 调用对应一个由无 credential supervisor 预建的 exact connected socket。Profile 的 exact call contract
决定 descriptor 数量；`JAVA_SOURCE_SEMANTICS@1` 固定为三个不同 descriptor，按 Plan → Draft → Review 顺序一次性消费，不得
复用、交换、追加或隐藏 retry。少于或多于 exact 数量、handoff/call/network audit 不一致、或 child 尝试新建 socket，均在
交付前失败关闭。

主处置写入 `SYS-QUALITY-SECURITY`；`SYS-ARCH-FLOWS`、`SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING` 与
`SYS-OPS-LOCAL-BROWSER` 同步描述流程和操作证据。

## Verification after disposition

- pinned transport 覆盖三 descriptor 顺序消费和耗尽行为；
- semantic Gateway baseline 与 grant 测试覆盖三调用 qualification binding、dispatch policy 和 audit count；
- 正式现场评测器拒绝任何非三调用、重试、Source/Evidence payload access 或审计数量不一致的结果。
