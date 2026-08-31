---
id: FINDING-010-231
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [operations, application, quality]
depends_on: [FINDING-010-229, FINDING-010-230, FINDING-010-179, ITER-010-PDR-012, SYS-OPS-CONFIGURATION]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: individual
disposition: preserve-peak-window-pre-dispatch-denial-and-retry-fresh-off-peak-or-under-an-exact-peak-override
target: ITER-010-VERIFICATION
---

# FINDING-010-231：run-102 发生在周一高峰，Ark 429 后 DeepSeek 正确保持零 dispatch

## Observation and execution evidence

candidate commit/tree `6f494fbc7c741205be17592ac5ec9e28fea7aab0 / f72742ca0db1677239d1604084e471a8366896e3`
完成 `run-102-mvp-experience` 的 fresh preparation。Browser 在 `2026-08-31T01:41:43Z` 重新读取 DeepSeek 官方 pricing page；visible-text
digest 仍为 `sha256:9c9dd4d22764599ade403c0ba6cd95abcb947810d5230ee95cb96a56a62d7668`。页面明确高峰只发生在 UTC
周一至周五 `01:00–04:00` 与 `06:00–10:00`；机器时间同时证明当前为 `2026-08-31 Monday 09:44 Asia/Shanghai`，即 UTC 周一
`01:44`，属于高峰而不是用户在 `2026-08-29 Saturday` 指出的周末全天闲时。

第一次 launcher preparation 因 Browser timestamp 带毫秒而以 `INVALID_ARGUMENT / official_pricing_checked_at is not canonical UTC` 在
Provider 前拒绝，dispatch 为 0；将同一观测时间规范化为整秒后，唯一 validated launcher 正常启动。launch receipt 同时为 Ark/DeepSeek
runtime 投影相同 logical-Turn budget digest
`sha256:db94a791f1b2920b3cdf4e3becf4bc40e8ec6e2e321a6dafa0fa0790740ee347`，证明 `FINDING-010-230` 的 composition wiring 已生效。

Q1 的 Ark request 通过 verified TLS、credential resolution 与 HTTP，随后形成 sealed
`429 / AccountQuotaExceeded / PROVIDER_HTTP_ERROR` unavailable verdict。fallback preflight 重新密封
`DENIED_PEAK_WINDOW`；DeepSeek credential、TLS、HTTP、authorized dispatch 与 invoked dispatch 全为 0。Browser 如实显示
`FAILED / AGENT_PRE_DISPATCH_REJECTED / Provider dispatch 1`。随后以 fresh Conversation 提交冻结 Q4，得到
`SUCCEEDED / APPLICATION_INPUT_CLARIFICATION / Provider dispatch 0`，没有继承 Q1 指代或失败。

Q2/Q3/Q5 没有继续发送，因为它们在同一时间只能重复已经密封的 Ark quota + DeepSeek peak-denial signature，不能验证 Review candidate，且会
制造无新证据的外调。terminal receipt digest 为
`sha256:9f9c07abe32286d6481b38ab0f8a87fe0f8cea56d73c2f441b0c40f93ad0ad16`，状态为 `STOPPED_AFTER_DISPATCH`，2
Conversation、2 Turn、Ark 1 dispatch、DeepSeek 0 dispatch、retry/人工审批/Production 0。

session、turn scope、pricing capture、launch、terminal、Ark DB 与 DeepSeek DB 的 SHA-256 分别为：

- `b36ebd84d511e2e8811681ed4f368ef64a69d5b46146453e7036ca601f235d09`
- `5751b15786a442bc9f4a8dd12a3ee542911b6f49dc116ce1c3cb4a1802077ffc`
- `94761ec673824558bee772d351be6cc7dd49425ea054ee4f30d45d6aa2dd1483`
- `ffcdda2d71ddcef3def20cb186fe1811bfb34aa4a7ffc6b2b9333054747e7237`
- `587e85d5c4276d0c39d91d638c57ab65176ed632dfb7bd1bcd85bf1c3c223bf9`
- `8eabc4e273ed7a2f3648bb709173d861a9a92572ab341e4f68e20b24ce698c3f`
- `0f539b3df4c6127e4b2a90005b287ed8e49b3701f314994f6d1ce8e79dd6672c`

## Classification and disposition

这是 `verification / individual` 证据，不是 Ark/DeepSeek route 实现失败、Review quality verdict 或 standing authority 撤销：

1. `FINDING-010-179` 的 weekday/weekend schedule 正确工作；周六/周日全天闲时不等于周一高峰可用。
2. current `@28/@18/@23` Review repair 没有取得真实模型执行证据，run-101 Quality FAIL 仍是最近完整质量结果；run-102 不把它升级或降级。
3. fresh successor 可在当前 PDR-007 off-peak window 内直接执行，无需重复第三方处理授权；若要求在当前 peak window 使用 DeepSeek，则是 exact
   pricing/dispatch scope delta，必须先形成 current run-bound peak override，不能从旧周末说明推断。
4. run-102 的 shared-budget wiring、Ark failure truthfulness、DeepSeek zero-dispatch safety 与 new-Conversation zero-dispatch clarification 作为
   正面执行证据保留；没有代码或 System Contract 变更。
