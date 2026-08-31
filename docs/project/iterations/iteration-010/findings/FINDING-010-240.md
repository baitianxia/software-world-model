---
id: FINDING-010-240
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [ai, operations, quality]
depends_on: [FINDING-010-238, FINDING-010-239, ITER-010-VERIFICATION]
code: [src/software_world_model/interface/provider_cli.py]
tests: [tests/test_ark_chat_conformance.py]
iteration: ITER-010
classification: local-implementation
scope: general
disposition: raise-default-ark-conformance-canary-output-bound-to-fit-glm-5-3-within-existing-standing-budget
target: src/software_world_model/interface/provider_cli.py
---

# FINDING-010-240：glm-5.3 Conformance canary 的 96-token 默认上限导致截断

## Observation and evidence

`FINDING-010-239` 的 safe evidence successor `ccrun_c0769582b200432c96bb06e742f0c111` 在 verified TLS、credential 和 HTTP 全部成功后，
准确密封 actual model `glm-5.3`、output tokens `96` 与 `INCOMPLETE_TERMINATION`。输出计数精确触及 `provider_cli conformance` 的默认
`--max-output-tokens=96`，证明本次 failure 是资格 canary 的本地资源上限，而不是 model identity、JSON/schema、request parameter、route 或
Provider availability failure。

一次显式 `--max-output-tokens 512` 的 fresh attempt 随后在 HTTP 前发生 typed `TLS_FAILURE`，HTTP dispatch 0；它既没有验证也没有否定新
bound，但证明 transport failure 与上述 completed-response truncation 是独立层。

## Decision and disposition

1. `provider_cli conformance` 默认输出上限从 `96` 提到 `512`；它仍远低于 standing scope 的单 call `8192` 与总 output budget
   `614400`，不扩大用户已批准的预算、数据、route、loopback 或非 Production 边界。
2. Adapter/product runtime 的 per-call bound、wire fields、no-retry、schema 与模型身份均不变；只有固定无源码 Conformance canary 的 CLI
   默认资源参数改变。
3. CLI 单元测试直接断言未显式传参时两个 canary request 都使用 `max_tokens=512`。由于 `provider_cli.py` 属于 Ark Conformance
   implementation aggregate，旧结果自动失效；clean successor 必须重新取得 2/2 PASS。
