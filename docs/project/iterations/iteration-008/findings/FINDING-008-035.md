---
id: FINDING-008-035
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai, interface, quality, project]
depends_on: [ITER-008-SLICE-001, FINDING-008-032, FINDING-008-034, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
code: [src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_policy.json, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_qualification.py, src/software_world_model/interface/world_model_runtime_assets/gateway_authorized_workload.py]
tests: [tests/test_world_model_answer_strategy.py, tests/test_iteration_008_capability_harness.py, tests/test_iteration_008_capability_qualification.py]
iteration: ITER-008
classification: system-contract
disposition: current-system-contract
target: SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING
---

# FINDING-008-035：Draft/Review 不应由模型复制 Application authority collection

## Observation

修复 `FINDING-008-034` 后，formal `run-006-freeze` 以 source snapshot commit/tree
`9d5c16132d88df9b728a28227c4eb039bd87f299` / `f55fb1fdccc20d995bee41195250f61071721cc1` 通过 deterministic Gate；freeze
report 与 live grant digest 分别为 `sha256:c047a059c8058340526440c65a26b7b3f74be09cd44ad01dbcc3a08672d04824` /
`sha256:2762b640e88a3e450bc1814105751455497468b2966ef076499d6f9bfea28c32`，startup receipt
`sha256:d6cdcff927562ce7906d92190223b9ef264f41141bf3964cc0477bca1d40f075` PASS。

公开问题 `登录流程是怎样的？` 实际完成 4 次 Provider HTTP request；四次均为 200，一次 verified TLS、三次 connection reuse，credential
resolution 4/4，retry 0。前三个 Investigation Result 全部完成；第四个 Draft request 也已由 DeepSeek 完成，但返回
`termination_reason=length`、`output_tokens=1000`，随后因 JSON 在 `support_digests` 中间截断而以
`STRUCTURED_OUTPUT_INVALID` 失败关闭。terminal document digest 为
`sha256:bff896e44ab3ef05180946ce5b9230ba1133858259b65022b68305d2e98db01c`；浏览器 console 没有 error/warn。

## Evidence and root cause

Draft raw output 在截断前已经给出语义正确的中文登录答案：先校验凭据、失败时记录并抛异常、成功时创建并返回 session。失败不是
DeepSeek、TLS、HTTP、credential、Investigation 或答案语义不可用，而是集成契约要求模型在答案之后逐字复制 4 个
`step_result_id` 和 35 个 `support_digest`。本次 sealed Draft input 为 165857 chars；模型在复制 opaque authority collection 时耗尽
1000-token output budget。

这不能通过小幅提高 `maximum_output_tokens` 系统性修复。当前 Investigation budget 允许最多 512 个 support item；若继续让模型复制
每个 71-char digest，最坏输出会随 authority collection 线性增长到数万 token，而且模型生成的复制品仍不是正式 authority Owner。
Review 同样要求回显 need/result/support check set，存在同一职责倒置。该问题是通用 Owner/Contract 缺陷，不是 LoginService、中文问题
或 Provider 特例。

## Decision and disposition

1. Draft 的答案文本和 Review 的 decision/finding codes 保持模型所有；Draft 的 `step_result_ids` / `support_digests` 与 Review 的三个
   checked collection 改为 Application-owned terminal authority。
2. exact 顶层 authority collection 在调用前从 model-visible sealed input 投影掉；为保持现有 closed wire schema，模型 raw envelope
   必须为这些字段返回空数组。模型自行填入任一 authority 值立即失败关闭。
3. schema validation 后，`java-source-semantics-terminal-authority-compiler@1` 从原 sealed assessment/review authority
   deterministic 注入 exact collection。raw output/digest 不改写，compiler binding digest 进入 normalized Proposal identity；现有 Product
   validators 继续逐项核对 injected collection。
4. active Contract/Strategy 升级为 `1.5.8`，Prompt/Vocabulary 升级为 `@17`，bounded Gateway policy 升级为 `@1.4.8`；Adapter
   保持 `deepseek-chat-completions-no-tools@6`，Investigation compiler 保持 `@7`，1000-token budget、18 Case / 40 calls、no-retry、
   isolation 与三层完整性规则均不放宽。suite/oracle 升级为 `@1.5.8`，terminal Case 用同一个 production compiler 验证 raw-empty /
   normalized-exact closure。
5. `SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING` 明确 terminal authority Owner 和审计边界；
   `SYS-CONTRACT-AI-CAPABILITY-EVALUATION` 同步规定资格必须覆盖 production terminal compiler。该 Finding 以 System Contract 处置闭合。

## Verification and closure

新增测试覆盖 Draft/Review authority 从 model-visible input 移除、normalized exact 注入、缺失 authority 在 Gateway 前拒绝、模型自填
authority 在单次调用后失败关闭，以及 fake 40-call qualification 通过同一 compiler。current bounded Gateway asset 的 self-integrity
pin 同步为新 raw SHA-256 `14a1d869…dbb65`，真实 file/hash 回归继续约束。当前 focused 103/103 与 docs 339/339 PASS；Conformance
与 Capability 仍须在 exact clean candidate 上执行并写回，不能由本地测试替代。完整回归执行 1035 项，1030 PASS；唯一 4 FAIL +
1 ERROR 精确属于 `FINDING-008-020` 的 frozen mature CLI/runtime drift，没有新增失败。

run-006 freeze/grant/session/terminal 永久保留为 completed-provider / failed-local-structure evidence；原 request 不 retry。Contract、Prompt、
policy、suite 与 candidate identity 已变化，因此 run-023 Qualification 和 run-006 formal freeze/grant 都不得复用。下一条外部分派只能来自
全新 clean candidate 的 2-call Conformance freeze；PASS 后再冻结并执行 40-call Capability。hidden canary 未披露，Production
Activation 保持 `NOT_EXECUTED`。
