---
id: FINDING-010-157
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [operations, interface, application, quality]
depends_on: [FINDING-010-139, FINDING-010-156, ITER-010-PDR-007, ITER-010-PDR-010]
code: [src/software_world_model/interface/engineering_chat_alpha_cli.py]
tests: [tests/test_engineering_chat_alpha_cli.py, tests/test_engineering_chat_provider_runtime.py, tests/test_deepseek_dispatch_admission.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: fallback-admission-is-a-dispatch-gate-not-a-listener-gate
target: SYS-OPS-LOCAL-BROWSER
---

# FINDING-010-157：备用路线准入被错误提升为整个浏览器 Session 的启动条件

## Observation

完成 `FINDING-010-156` 的 availability-only fallback 后，fresh `run-047` 启动准备暴露出一条遗留约束：
`engineering_chat_alpha_cli._run_artifact_session` 在密封零分派 launch receipt 后，要求 DeepSeek admission receipt 的
`allowed=true` 才创建 loopback listener。上海峰时即使首选 Ark route 完整有效、当前没有受信
`PREFERRED_EXECUTION_PROFILE_UNAVAILABLE` verdict、因而不可能合法选择 fallback，CLI 仍会关闭整个 Session。

这把两个不同事实错误耦合：

1. 浏览器 Session 可以启动并使用有资格的 preferred execution profile；
2. fallback execution profile 只有在被真实选择且其 dispatch admission 当前允许时才能解析凭据或发出请求。

`ITER-010-PDR-007` 的硬门禁约束所有实际 DeepSeek dispatch，并明确“不阻断 Ark-only”；`SYS-ADR-017` 与
`FINDING-010-156` 又要求 raw failure 无可信 availability verdict 时 fallback dispatch 为 0。因此遗留 listener check 比当前权威语义更强，
也会让已经修复的模型透明路由继续受具体 fallback 的运营窗口支配。

## Evidence

- 修改前 CLI 直接以 `not admission.receipt.allowed` 拒绝 listener，错误文案把 denied fallback admission 描述成整个 planned
  Artifact Session 不可启动。
- `run-047` 的无监听组合预检在完全相同的 current candidate、Source、standing authority、资格和 cognition artifact 下通过；唯一阻塞来自
  该 CLI listener check，而不是 Ark、Source、authority 或产品候选。
- DeepSeek admission controller 的 `authorize_dispatch` 会在 exact fallback request 创建后再次执行 receipt 时效、窗口、预算和 envelope
  检查；denied receipt 无法取得 authorization，credential、TLS 和 HTTP 均保持 0。

## Disposition

当前运维契约 `SYS-OPS-LOCAL-BROWSER` 明确区分 listener 与 fallback dispatch：

- Artifact Session 在 listener 前仍必须构造 fallback admission controller 并密封真实 receipt；controller 缺失或结构漂移继续失败关闭。
- receipt 为 `DENIED_*` 时允许 preferred-only loopback Session 启动，且状态必须如实展示该决定；启动本身不授予 fallback。
- 只有受信 availability verdict 合法选择 fallback 后，逐请求 `authorize_dispatch` 才能决定当前是否允许 DeepSeek；拒绝必须发生在
  credential、TLS 和 HTTP 前。

实现删除了 `allowed=true` 的 listener 前置条件，只保留 controller 必须存在的不变量。CLI 定向测试使用
`DENIED_PEAK_WINDOW` receipt 证明 listener/launch/terminal 生命周期仍成立；Provider runtime 与 admission 定向测试证明实际 fallback 在
credential/TLS/HTTP 前失败关闭。合计 22 tests PASS，外部 Provider/network dispatch 0，full regression 0。历史
`ITER-010-RESULT-V-DEEPSEEK-IDLE-001` 保留为当时实现证据，但 Result 不拥有或覆盖 current System Contract。
