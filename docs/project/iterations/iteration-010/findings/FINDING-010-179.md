---
id: FINDING-010-179
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [operations, quality]
depends_on: [FINDING-010-139]
code: [src/software_world_model/application_services/deepseek_dispatch_admission.py]
tests: [tests/test_deepseek_dispatch_admission.py, tests/test_engineering_chat_session_artifact.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: correct-current-deepseek-weekday-weekend-schedule
target: SYS-OPS-CONFIGURATION
---

# FINDING-010-179：DeepSeek 当前闲时规则包含周末全天，旧门禁遗漏星期维度

## Observation

用户指出 `2026-08-29` 是周六，DeepSeek 当天处于全天闲时。随后在 `2026-08-29T07:12:39Z` fresh 获取官方价格页，页面明确把高峰定义为
UTC 周一至周五 `01:00–04:00`、`06:00–10:00`，其余时间均为闲时；等价的北京时间高峰是周一至周五 `09:00–12:00`、
`14:00–18:00`，周六、周日全天闲时。原始页面 SHA-256 为
`cf2c6fb2dd8a32a538f12a8176175b8809a3516326a5cb30dfe52d63c490a968`，用户纠正引用为
`local-user-message-utf8:sha256:d2cc3f9f8d3c152aac647df3446afadd9362d7735eff1b04ad7cfe186dffe1ec`。

当前 PDR-007、`SYS-OPS-CONFIGURATION`、Manifest 和 `DEEPSEEK_OFF_PEAK_WINDOWS` 仍把三个时段无条件应用到每天；
`_off_peak_window` 完全不读取本地星期。因此即使提供 fresh pricing check，旧实现也会把周六 `14:50` 错判为高峰。run-070 的 Session
输入其实已经在摘要中写明 `weekday peak hours`，但调度实现没有表达该事实。

run-070 已密封的实际 decision 仍是 `DENIED_PRICING_CHECK`，直接原因是其 check time
`2026-08-28T05:44:44Z` 到 admission time `2026-08-29T06:50:43Z` 已超过 900 秒 freshness 上限；这次拒绝本身正确，不能追写成
`DENIED_PEAK_WINDOW`。错误在于执行准备没有刷新每 run check，且旧 schedule policy 即使刷新后仍会漏掉周末全天闲时。

## Evidence and first divergence

- 官方 Source：<https://api-docs.deepseek.com/quick_start/pricing/>，fresh raw digest 与检查时间如上；页面当前明确限定高峰只发生在周一至
  周五。
- run-070 `session.json` 的 pricing summary 已写明 `weekday peak hours ... and all other hours are off-peak`，但
  `terminal.json` 的静态 `allowed_windows` 仍只有不含星期的三个每日时段，证明配置证据与执行 policy 不一致。
- 原 `_off_peak_window` 只计算 `hour * 60 + minute`，没有 weekday 输入；这是 fresh check 后的最早实现偏差。
- 定向测试新增周六/周日多个边界、周一高峰、周五晚跨入周末的连续闲时，以及周末下 stale/changed pricing check 仍失败关闭；Artifact
  Session fixture 同步要求 policy `ITER-010-PDR-007@2` 和 `EFFECTIVE` pricing status。

## Classification and disposition

这是 `system-contract / systemic` Finding，主处置到 `SYS-OPS-CONFIGURATION`；不改变 Ark-first、可信 unavailable 才 fallback、逐 request
准入、900 秒 pricing freshness、预算、零 retry、完整质量链或 Production 边界：

1. PDR-007 current policy 修订为 `@2`：工作日保留三个闲时段，周末全天闲时；收据必须显式携带星期限定后的窗口。
2. Application 依据 `Asia/Shanghai` weekday 判定周末，并把相邻的连续闲时保留到下一真实高峰开始；每次 dispatch 仍重验当前确实处于任一
   闲时，不能仅依赖初始 matched label。
3. weekend admission 不绕过 fresh 官方检查；stale、missing 或 changed check 仍在 credential/TLS/HTTP 前失败关闭。
4. `FINDING-010-178` 的 run-068/069/070 原始 Provider/transport 证据保持不变，但“只能等待窗口/外部恢复”的当前结论由本 Finding
   纠正：新的 clean run 可在 fresh pricing check、可信 Ark unavailable 和既有 standing scope 同时成立时直接使用周末 fallback。
5. Manifest 内冻结的三个纯时段值只保留为 trusted-plan compatibility mirror，不再作为当前日历语义来源；其 YAML 注释明确指向
   `SYS-OPS-CONFIGURATION` 和 `ITER-010-PDR-007@2`，避免一次普通缺陷修复伪造新的计划授权。
