---
id: FINDING-008-022
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [architecture, application, ai, engineering, quality, project]
depends_on: [ITER-008-SLICE-001, FINDING-008-021, SYS-ADR-015, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING]
code: [src/software_world_model/application_services/bounded_world_model_investigation.py, src/software_world_model/application_services/structure_view.py, src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, src/software_world_model/ai_infrastructure/model_egress_gateway.py, validation/structure_world_model_iteration_008/capability]
tests: [tests/test_bounded_world_model_investigation.py, tests/test_java_source_semantics.py, tests/test_world_model_answer_strategy.py, tests/test_iteration_008_capability_harness.py, tests/test_iteration_008_capability_qualification.py, tests/test_model_egress_gateway.py]
iteration: ITER-008
classification: system-contract
disposition: outgoing-call-evidence-is-fulfilled-by-method-result
target: SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY
---

# FINDING-008-022：method result 已承载的 outgoing CALLS 不应要求模型再选择重复图查询

## Observation

clean candidate `5ef09d4f29f538fc40985613c963d9c29bd2ee15`（tree
`f912744582d4864c26697295668a9560a07f21d1`）的 run-012 Conformance preflight
`sha256:51d892770d777073e3337e074122b22acc6954610a1d5e357e73894a9442ecec` 经后置单次授权
`sha256:15dca55301643f148755998f609ea3a66427d74f04eb4712338754c320edbbca` 后恰好执行 2 requests，12/12 PASS；Result
digest 为 `sha256:f50ea41a6ec5502df6a7cc90e840d52e3474b5f78b3c593e0f58672f8b69715c`。唯一 actual identity 为
`deepseek-v4-pro`，temperature 0、thinking disabled、usage 完整，input/output tokens 为 376/86，无 retry。

同候选 Capability freeze `sha256:4964298813d036ee59e2ffec7fd9013a88e4d16ac557c1703c4ca4ec5bd61d93` 经后置单次授权
`sha256:4f7758ff216cec47be4bfdd7d1f0eecfe36c000bef26f4938718d9a35e573ed8` 启动。前 9 Case / 21 accepted calls
全部 independent PASS，material error/omission 为 0。第 22 次 Provider request 在
`WM-JSS-I8-MAX-FOUR-010:call-1` 完成后，本地 frozen-ledger 校验以
`QUALIFICATION_INVALID: bounded capability call did not preserve the frozen evidence obligations` 失败关闭；没有 retry、Qualification、
正式 Web、canary 或 Activation。failure/terminal document digest 为
`sha256:58c1a33c3fb458db0dd592c1871072dac6a6ec815f7aaba5ca57350ed8d9382a` /
`sha256:fabb08a4731f4d2d6d5b8f1890f203e887048229c57e9edec29f149dd7b03f4c`。

失败问题是 “Trace authentication through failure recording and successful session issuance.”。DeepSeek 返回合法 candidate operation、
覆盖 authentication/failure/recording/session/issuance/trace/through/return/throw/order/audit 的 terms，并选择
`method_implementations` evidence；suite 选择 `direct_neighborhood(OUTGOING_CALLS)`。实际 closed structured output digest 为
`sha256:72e0522a6c5f3d775286bd628620b4ea0278aaa53ec7d2326b3fb194787f851b`，actual model、usage、shape 与 transport 均正常。

## Evidence and root cause

`SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY` 已要求 `method_implementation` 返回 ordered implementation atoms、call-site target、
保持原义且带 Support 的 `CALLS` relations；产品 payload 还明确密封 `legacy_calls_direction: OUTGOING` 与 `legacy_calls`。当前测试证明
该结果对完整方法返回 exact outgoing calls，并由 CALLS Coverage 共同决定 completeness。

因此，在没有 path obligation 时，先执行 method batch、再对同一 batch 的方法执行 `direct_neighborhood(OUTGOING, CALLS)` 会重复读取
已在前一 Result 中密封的正式关系。run-012 的模型选择不是证据缩减：它选择了同时包含实现语义和 outgoing calls 的较小充分计划；
suite 则选择了重复的额外 operation。让模型在这两个表示别名之间保持 exact label 不增加产品知识，只增加 provider/评测脆弱性。

## Decision and disposition

Application 在冻结 ledger 前执行通用 capability subsumption：独立的 raw `direct_neighborhood(OUTGOING_CALLS)` evidence request 归一为
`method_implementations`；若同一 ledger 还含 `path_exists` 或 `all_simple_paths`，direct obligation 保持独立，因为 path 结果不等于完整
neighborhood。`INCOMING_CALLS`、`BOTH_CALLS`、inventory、path bounds、typed Ref、Coverage、Support 与预算语义均不改变。

该规则只读取注册 operation/relation vocabulary，不读取问题文本、search terms、工程、Case ID、Oracle 或未来 Result。它使 raw method
与 raw outgoing-direct 两种模型表达收敛到同一产品 transition，同时仍由 method Result 的 CALLS Coverage 失败关闭不完整证据。

活动 capability/Strategy 升级为 `1.5.2`，prompt/vocabulary 为 `@11`，compiler 为 `@6`，Gateway policy 为 `@1.2.2`，suite/oracle 为
`@1.5.2`，closed evaluation protocol 为 `@1.0.2`。18 Case、18/18 threshold、temperature 0、no-retry 不变；由于
`MAX-FOUR-010` 的重复 direct call 被删除，planned provider calls 从 41 降为 40。`BUDGET-EXHAUSTION-011` 仍以 BOTH + all-paths
执行完整四回合，最大预算、graph capability 与失败关闭未被削弱。旧 run-012 已消费且不可重试。

## Verification and closure

- raw candidate 和 standalone outgoing-direct evidence 都必须归一为 method；incoming/both 保持 direct；outgoing-direct 与 path 组合不得
  被错误折叠；
- method result 必须继续密封 exact outgoing CALLS、direction、Coverage 与 Support；非完整 CALLS Coverage 不能伪装成充分证据；
- production compiler、Gateway dynamic allowlist、18-case / 40-call fake transport 与 independent evaluator 必须 18/18 PASS；
- targeted、Gateway AF_UNIX、docs、compile/diff/secret scan 与完整回归重新执行。新的 live qualification 未达到 18/18 前，正式 Web、
  hidden canary、SLICE-002 和 Production Activation 继续 blocking。

处置证据满足上述边界：raw candidate、standalone outgoing direct、incoming/both 及 outgoing+path 的定向反例全部 PASS；覆盖
DeepSeek Adapter/Conformance、compiler、Gateway AF_UNIX、runtime 与 product chain 的相关回归 169/169 PASS；fake transport 恰好
40 calls / 18 Case，并由独立 evaluator 18/18 PASS。current documents 326/326、compileall、diff check 与路径级 secret scan PASS。

完整回归执行 985 项，其中 980 项通过；唯一 4 failure + 1 error 与 `FINDING-008-020` 已密封的 ITER-003 Codex CLI exact-binary drift
完全一致，无活动代码新增失败。写回后的 `ITER-008-SYSTEM-CONTRACT-SET@1` digest 为
`sha256:1542f20e7b946ee9a5a597ad4f5a2206f8e59ad58ac60ccdb2b2803b913d6987`；共享当前文档对应的
`ITER-007-SYSTEM-CONTRACT-SET@1` digest 为
`sha256:6f470e7cfc7c0812474219a3530e8ad23817fcfddb192647bafedb4fde72d349`。Finding 因此处置到
`SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY`、相邻 System Contract、活动设计、代码与测试；run-012 仍保留为失败证据。
新的 run-013 live qualification 未达到 18/18 前，正式 Web、hidden canary、SLICE-002 与 Production Activation 继续 blocking。

处置后 clean candidate `a93666ce51f24149a487581a3c12283691cbd14b` / tree
`e3ffdb9d72aa1202a6029a5202db20af3178ad8b` 完成 run-013。Conformance 以 preflight/result
`sha256:38a95bcddae1bbb03de98c419d8577cd98903560ecbca681524b2379f9ce467e` /
`sha256:8505983e13d9e2ab4ec9fbeec6b92b2cc9369fb89f921582457fd8703146c2c1` 完成 2 requests / 12/12 PASS；Capability 以
freeze/result/qualification
`sha256:11524d4c219c13c8593cbdfb499e2b23c809b3cfdcf56eb4e06d3adddf9b469b` /
`sha256:b05583d6edf669008253618c0bd3cd2c872da037da33a8dacae3c46f2ee1ca25` /
`sha256:61f18bd62d217ad68ac778a5aa4e8537eff180f4009067a75c8e2c011102a0c1` 恰好完成 40 requests / 18 Case、18/18
independent PASS，failure/unknown 为 0。唯一模型 identity 为 `deepseek-v4-pro`，usage 完整、零重试；该 live 证据确认本 Finding 的
Contract redirect 可由当前 Provider 遵循。V-002 已 PASS；正式 Web、hidden canary、SLICE-002 与 Production Activation 仍由各自
Gate 独立阻断。
