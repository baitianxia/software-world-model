---
id: FINDING-010-207
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai-infrastructure, operations, quality]
depends_on: [FINDING-010-179, FINDING-010-206, ITER-010-PDR-012, SYS-ADR-017]
code: [src/software_world_model/application_services/deepseek_dispatch_admission.py, src/software_world_model/interface/engineering_chat_provider_runtime.py, src/software_world_model/interface/engineering_chat_alpha_cli.py]
tests: [tests/test_deepseek_dispatch_admission.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_chat_alpha_cli.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: activate-deepseek-run-receipt-at-first-real-fallback-preflight
target: SYS-OPS-CONFIGURATION
---

# FINDING-010-207：run-084 的 DeepSeek receipt 在真实 fallback 前已提前过期

## Observation and first divergence

run-084 的 listener preparation 在 `2026-08-30T10:46:42Z` 以周末全天闲时形成 `ALLOWED_OFF_PEAK` DeepSeek receipt，固定
`maximum_duration_seconds=600`，因此 `valid_until=2026-08-30T10:56:42.355199Z`。run 内 44 个 Ark call 有 43 个完成；其中 DB row 33
（`model_call_b3d65124ed104eff94cab207cf228168`）在
`2026-08-30T10:57:46.623110Z` 首次产生 HTTP 前 typed `TLS_FAILURE`，受信 availability owner 因而可以选择 fallback。

此时官方 pricing check 年龄约 848 秒，仍小于 900 秒 freshness 上限，周六也仍处于连续闲时；run authority、预算和 route scope 均有效。
DeepSeek 却在 credential、TLS、HTTP 之前因 preparation receipt 的 600 秒 duration 已过期而失败关闭，实际 dispatch/TLS/credential/HTTP
保持 `0/0/0/0`。旧实现从 listener 启动而非第一次真实 DeepSeek preflight 开始计时，是该 eligible fallback 未执行的 exact first divergence。
这不是 Ark 没有可信 unavailable、用户未授权、DeepSeek 周末不可用或 runtime 等待；在旧 `@2` 规则下拒绝本身是正确的过期执行，错误是
admission 生命周期定义过早。

## Decision and disposition

这是 `system-contract / systemic` Finding，主处置到 `SYS-OPS-CONFIGURATION`，并将 PDR-007 current policy 修订为
`ITER-010-PDR-007@3`：

1. controller 在 listener preparation 仍从 exact immutable plan 密封 preparation decision，以便在任何 Source/credential/TLS/HTTP 前验证输入并
   如实展示当时 verdict；该 decision 不授权 DeepSeek dispatch，也不启动 active duration。
2. 第一次真正的 DeepSeek request preflight 在同一 lock 内从同一 plan 与注入的 current aware UTC clock 重新密封 active receipt；必须重新
   检查 run authority、pricing age/status、`Asia/Shanghai` 闲时/override 和完整最坏时长。任一条件失效都在 credential/TLS/HTTP 前以 0
   dispatch 失败关闭；不能沿用 preparation allowed verdict。
3. 后续 exact execution envelope 继续绑定同一个 active receipt，重验当前窗口/expiry 与 calls/tokens；不按 request 重新延长 duration，不增加
   retry、fallback attempt、budget、接收方或 authority。
4. immutable runtime preparation digest 显式绑定 preparation receipt；terminal public audit 同时保存 preparation 与 active receipt、activation
   mode、是否已激活、逐 call authorization 和 invocation 集合，避免把两种 receipt 混为一谈。
5. 定向测试覆盖 listener 后 11 分钟才发生周末 fallback：因 pricing age 仍小于 900 秒，active 600 秒从 first preflight 开始；另覆盖 16 分钟后
   check 已 stale，首次 fallback 以 0 authorization 失败关闭。已有窗口边界、预算、replay 和 no-network deny 测试继续适用；与相邻
   Chat/route/launcher/Browser 组合共 144 项定向测试 PASS、外调 0。

该修正不创建新的授权或 route。它只确保 existing standing scope 下真正选择 fallback 时才消耗既有 600 秒质量链，并继续服从 900 秒官方检查
freshness、Ark-first、trusted-unavailability-only、零 retry、完整 Review 和 Production `NOT_EXECUTED` 边界。run-084 的原始 DeepSeek 0 与失败
证据永久保留，不能按新 policy 追写为已执行。
