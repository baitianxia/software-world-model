---
id: FINDING-010-236
kind: implementation-finding
status: open
authority: execution-evidence
owners: [ai, architecture, operations, quality, project]
depends_on: [FINDING-010-235, ITER-010-PDR-007, ITER-010-PDR-012, ITER-010-VERIFICATION, SYS-ADR-017, SYS-CONTRACT-AI-MODEL-GATEWAY]
code: [src/software_world_model/ai_infrastructure/provider_http_failure_evidence.py, src/software_world_model/ai_infrastructure/model_egress_gateway.py, src/software_world_model/ai_infrastructure/volcengine_ark_chat_adapter.py, src/software_world_model/infrastructure/sqlite_model_gateway_repository.py, src/software_world_model/interface/provider_cli.py]
tests: [tests/test_model_gateway.py, tests/test_model_egress_gateway.py, tests/test_volcengine_ark_chat_adapter.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: add-sanitized-optional-provider-error-parameter-evidence-with-v1-replay-compatibility-and-no-routing-effect
target: SYS-CONTRACT-AI-MODEL-GATEWAY
---

# FINDING-010-236：run-107 的 Ark 400 缺少可安全定位的参数名

## Observation and execution evidence

`run-107-mvp-experience` 在 current product commit/tree
`0e66247159422d8da4f1a001bb14b11c5d8dff20 / af167050807543b371d596cef2388ab5b521e5fc` 上按冻结顺序执行 Q2、同
Conversation 的 Q3、fresh Conversation 的 Q4 和 fresh Conversation 的 Q5：

- Q2 的 Ark call 在 HTTP 前发生 typed `TLS_FAILURE / PROVIDER_UNAVAILABLE`；DeepSeek 在周一 `17:03 CST` 的 first preflight 由
  `DENIED_PEAK_WINDOW` 阻断，credential/TLS/HTTP 均为 0；
- Q3 与 Q5 的 Ark request 均完成 verified TLS、credential resolution 和 HTTP dispatch，随后分别以 HTTP 400
  `InvalidParameter / BadRequest` 失败。对应 Provider request ID 为
  `021788167089402a92b4afba7ed5745e150097919eafbc67185b5` 与
  `021788167170138b19f2272b96096885d7095f98214c210a6bdf1`；
- Q4 继续形成 `SUCCEEDED / APPLICATION_INPUT_CLARIFICATION / Provider dispatch 0`；重复 400 后没有发送 Q1。

terminal 为 `STOPPED_AFTER_DISPATCH`，4 Turn / 3 Conversation / 3 preferred model call；Ark transport 为 3 次 TLS attempt、2 次 TLS
success、2 次 credential resolution、2 次 HTTP dispatch，DeepSeek dispatch 0，request retry、人工审批和 Production 均为 0。terminal、
preparation、session runtime、public-source session authority、Ark runtime、DeepSeek runtime 与 shared logical-Turn budget digest 分别为：

- `sha256:df77c07833ec4ab7d62ae4faa557b62f2ae474a348b5d864d49644eee9a0ac61`
- `sha256:26cb4a2ce66a5cc2c52d4888aec2dfbe6757f4470469d35826c3d3ca88259e50`
- `sha256:763082c7d060ba3c60b3deee572fdc8f1e3e11b87d20622f848a4107cc62395c`
- `sha256:80c43d3fa5b59c40b0e773085c6bc4b3d36ee8c619d091f2140843b517b33848`
- `sha256:a8398e1b7cf0c3b6358f51327b8b8973f66490c21a16307d8943affcfa87d47c`
- `sha256:be1d3dafa37eb958461931e1348160ac042a867017892b64f90f2b180b71d51f`
- `sha256:8cca0ff549285e45e30c09ed1177a3eb5847cb026fcac42dd9ff588a6a1813bd`

session、turn scope、pricing capture、launch、terminal、Ark DB 与 DeepSeek DB file SHA-256 分别为
`b742120ba262bca56e7d024346db87a1c7b635b4f49e991ac6e80987a8be5664`、
`bf0eaa9195231cad534d0a300e37b821bde69e0adb201f844e5283dc73ac9c81`、
`2edf32d76492ee6d8cb00998033c67757837f42db9c45194c7ed34e54f63ebe0`、
`c74461282443fa3ee544cace38b6f29245f1b6164ddb1ec416969f8d49d7ce43`、
`2b416be6482ec21a2a2139705539360480e6ad00a2bb3fb6e1c2aa35a31989be`、
`a9fd3c1cc56bc24a45144f76b2d50f09968eb53090cd9fe0543f765e1fa6cd66` 与
`0f539b3df4c6127e4b2a90005b287ed8e49b3701f314994f6d1ce8e79dd6672c`。

## Root cause classification

HTTP 400 本身是 Provider 对 current request 的 client/config rejection，不是可信 availability verdict；current route 正确地没有 retry 或
fallback。系统也正确持久化了 status、code、type 与 request ID，但 Ark OpenAI-compatible error parser 未读取可选 `error.param`，Gateway
安全证据 schema 也没有对应字段。因此本地只能知道“某个参数无效”，不能在不持久化敏感 error message/response body 的前提下判断应修复哪个
request field。这是通用 HTTP failure observability contract 的系统性缺口；它尚不能证明 run-107 response 确实携带了非空 `error.param`，该事实必须由
fresh successor 证据确认。

## Decision and disposition

1. Gateway-sealed HTTP failure evidence 增加 optional `provider_error_parameter`。它只接受长度不超过 128 的 ASCII token/path 字符集，任何
   空值、错误正文、response body/header、credential 或其他字段仍全部丢弃。
2. 该字段只用于故障定位，不进入 availability owner 判据，不改变 400 的 non-eligible 结论，不增加 retry/fallback，也不改变 Provider request
   bytes、transport 或模型输出解析。
3. 新 evidence 使用 `MODEL_PROVIDER_HTTP_FAILURE_EVIDENCE@2`，SQLite 以 nullable column 原位迁移；历史 `@1` row 保持可回放并按原 digest
   规则验证。Model Egress closed response 同步升级并继续 exact-key/digest 校验。
4. Ark Adapter/CLI 和 Conformance negative oracle 验证只投影安全 parameter token、拒绝 message 与非安全 parameter；DeepSeek Adapter 不在本次
   变化中，避免把 Ark 诊断修复扩张成未获 fresh DeepSeek qualification 的 Provider identity 变化。
5. 代码、目标测试、System 文档与 fresh Ark Conformance 通过后，使用新的 clean run-108 先重放 Q5。若 Ark 返回安全 parameter name，则只对该
   通用 request field 做最小修复；若仍为空，则保留 evidence，继续用不披露正文的受控差分定位。run-107 不取得 Delivery/Review、质量或 MVP PASS。
