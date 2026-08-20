---
id: FINDING-008-025
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai, architecture, engineering, quality, project]
depends_on: [ITER-008-SLICE-001, FINDING-008-024, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY]
code: [src/software_world_model/ai_infrastructure/deepseek_chat_adapter.py, src/software_world_model/ai_infrastructure/deepseek_chat_conformance.py, src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, src/software_world_model/ai_infrastructure/model_egress_gateway.py, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_policy.json, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_qualification.py, validation/structure_world_model_iteration_008/capability]
tests: [tests/test_deepseek_chat_adapter.py, tests/test_deepseek_chat_conformance.py, tests/test_world_model_answer_strategy.py, tests/test_iteration_008_capability_harness.py, tests/test_iteration_008_capability_qualification.py, tests/test_model_egress_gateway.py]
iteration: ITER-008
classification: system-contract
disposition: one-leading-system-authority-for-deepseek-json-mode
target: SYS-CONTRACT-AI-MODEL-GATEWAY
---

# FINDING-008-025：DeepSeek JSON 适配必须把 schema 与任务语义合并为单一 system authority

## Observation

clean candidate `139e61c94f218a6076022f1863cf871b2d3104f2`（tree
`efb2cd48b6fb02365ab2a2544f3a5e9adec890cf`）的 run-016 Conformance 以 preflight/result
`sha256:6af24a38abc6292787f7abc2f714669827877b2c6ddf85150d0a1480fbaba63a` /
`sha256:9e035d75899140ecb02f5513666b16ff09f72f5490ff8c259201353aa8c1d83b` 完成 2 requests / 12/12 PASS。
唯一模型 identity 为 `deepseek-v4-pro`，temperature 0、thinking disabled、usage 完整；persistent transport 只完成 1 次 verified TLS
handshake，复用 1 次，2 次 HTTP dispatch/credential resolution，post-dispatch unknown 与 retry 均为 0。

同候选 Capability freeze `sha256:63151e87fc13d241b1586429276dfd8269af8c9f59f10f9b09e67e263c13f43d` 在前 6 Case /
12 requests 全部 PASS 后，第 13 次已完成 request 于 `WM-JSS-I8-PATH-EXISTS-007:call-1` 被本地 frozen-ledger exactness 校验拒绝。
失败/terminal digest 为 `sha256:b698c9820a8f4770d7b49b158038e01378ca263afc83ac660732c9977ad95f64` /
`sha256:e85fb34aca3ee21cedc3486d78c270c749fa4923c355026de017f74b98761d42`；授权已消费、没有 retry、Qualification、Web、canary 或
Activation。

该 synthetic 问题是 “Can authentication reach session issuance through static calls?”，冻结 evidence obligation 是
`path_exists`。模型输出 digest `sha256:9da19fb83c88c4c71afe0114e321e9719680cde70d2f30038039bce6f39577de`，虽生成
`authentication/session/issuance/static/calls/reach/path`，却选择 `method_implementations(OUTGOING_CALLS)`，并把只存在于 prompt
示例中的 `direct/all/method/implementation/candidate` 追加为 search terms。

## Evidence and root cause

网络、身份、JSON shape、Usage 与 persistent TLS session 在失败 request 上均正常。Application 的 exact ledger 比较也按设计拒绝了错误
语义，不能通过放宽 evaluator、把 reach/path 关键词映射写入 Application，或读取 Case/Oracle 来“修复”。同一 `1.5.2/@11` Contract
曾在 run-013 通过该 Case，说明问题不是注册 operation 或 compiler 缺失，而是当前模型线协议对任务语义的稳定传递不足。

活动 wire 先由 DeepSeek Adapter 插入一个仅含 closed JSON Schema 的 system message，再把 Gateway 的完整语义 prompt 作为第二个
system message发送。DeepSeek 的[官方 JSON Output 指南](https://api-docs.deepseek.com/guides/json_mode/)给出的标准形态是在同一个
system prompt 中同时说明任务与 JSON 输出格式；Chat Completion 文档也要求 JSON mode 的 system/user instruction 明确要求 JSON。
官方文档没有声明多个 system message 一定失效，因此“只读取第一个 system”不是事实；结合 run-016 输出，可以确认的系统缺口是：
当前 split-system wire 从未对 Capability 级语义遵循取得资格，且把格式 authority 放在任务 authority 之前增加了 Provider 解释歧义。

## Decision and disposition

DeepSeek Adapter 升级为 `deepseek-chat-completions-no-tools@4`：若 Gateway Request 已有 leading system instruction，Adapter 将任务语义与
closed schema 合并为恰好一个 leading system message；其余消息顺序不变。Conformance fixture 升级为 `1.2.0`，live wire Case 必须证明
只有一个 system message，且该消息同时包含任务语义与 closed schema。Ark Adapter 不继承这项 DeepSeek-specific 资格结论。

Provider-independent 语义合同升级为 capability/Strategy `1.5.3`、prompt/vocabulary `@12`。它明确每次只应用 sealed capability 对应的
instruction section；提示中的示例词只有原问题实际包含/请求该概念时才进入 search terms；evidence 按问题要求的答案分类，而不是按孤立
词分类。显式 reachability 必须选择 `path_exists`，即使问题同时提到 static calls/calls/trace；只有不含 reachability/path obligation 的
局部实现、行为或 outgoing trace 才使用 `method_implementations`。Application normalization、compiler `@6`、18 Case、40-call Oracle、
18/18 threshold、temperature 0、persistent TLS 与 no-retry 均不放宽。

bounded egress policy 升级为 `@1.4.1`，suite/oracle 升级为 `@1.5.3`。run-016 及之前所有 Adapter/Prompt qualification 均失效且不得用
原授权重试；必须在新 clean candidate 上重新完成 2-call Conformance 和完整 18-case Capability。两者未通过前，正式 product freeze、
Web、early canary、Agent 对照、Reflection、SLICE-002 与 Production Activation 继续 blocking。

## Verification and closure

- Adapter contract test 必须证明 semantic prompt 与 schema 只形成一个 leading system message，且 user message 原序保留；user-only
  request 仍由 Adapter 添加 schema system authority；
- Conformance fake/live evaluator 必须拒绝多个 system message，并继续验证 no-tools、stateless、strict JSON、identity、Usage、secret
  absence 与 persistent TLS session；
- active prompt test 必须绑定 capability section isolation、example-only terms 和 reachability precedence；
- suite/oracle、policy、qualification/resource policy、runtime workload、授权 freeze 与 exact digest 全链拒绝旧身份；
- targeted、AF_UNIX Gateway、fake 40-call Capability、完整回归、docs、compile/diff/secret scan 重新执行。新 live qualification 的实际
  结果只在完成后追加，不能由本 Finding 预先声明 PASS。

处置后的 active identities 为 Adapter `deepseek-chat-completions-no-tools@4`、configuration
`sha256:cf85faed9ef5c314abc6967e86ecbc0d9362cfbe4b4a0ead4303cd8f279a586d`、Conformance fixture `1.2.0` /
`sha256:98267b7d84dc9224750b39c18d64ccba3a006ce77dae6ed6548e9aca61ba6d49`、Result `@2`、policy raw digest
`sha256:58d3879008fcca9b290e2f522cdd6e91cb26394f027d15f4129257c0460f485d`、resource policy
`sha256:d7b895f30d5c91d1a82d017f41f69374777d37f77763ffb032a278ed80b9b4c9`、suite/oracle raw digest
`sha256:3cf0e75407e5a3f565756367537b5b574e8e7cda953447f24cebbbbbea0aa7ca` /
`sha256:39dfdad5f193a1e65694eb49891ba26d996f14c54e89a149b3da2fea998bf783`。product workload digest 为
`ff992e8b5699a5f7fe5da0ffa55f4d8047bba3587d2d4315a9d2591326fd7273`，authorized wrapper exact allowlist 已同步。

DeepSeek/ITER-008/Gateway/runtime/product 相关回归 128/128 PASS，fake transport 仍恰好执行 40 calls / 18 Case 并由 independent
evaluator 18/18 PASS。完整执行面 1016 项中 1011 项通过；唯一 4 failure + 1 error 仍是 `FINDING-008-020` 已密封的 ITER-003
Codex CLI/runtime exact-binary drift，错误名称和原因均未变化，未冒充 full-suite PASS。current documents 329/329、compileall、diff
check 与路径级 secret pattern scan PASS；`ITER-008-SYSTEM-CONTRACT-SET@1` digest 为
`sha256:c9992a431726a48274355d1075187311471c40bea6efbb51de1c7b3ff9e14968`。Finding 因而处置到
`SYS-CONTRACT-AI-MODEL-GATEWAY`、活动设计、代码和测试；全新 live Conformance/Capability 仍是独立 blocking Gate。
