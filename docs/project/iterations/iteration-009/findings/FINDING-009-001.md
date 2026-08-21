---
id: FINDING-009-001
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [ITER-009-SLICE-001, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING]
code: [src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, src/software_world_model/application_services/world_model_answering.py, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_policy.json]
tests: [tests/test_world_model_answer_strategy.py, tests/test_iteration_008_capability_harness.py, tests/test_iteration_008_capability_qualification.py]
iteration: ITER-009
classification: local-implementation
disposition: align-review-prompt-with-existing-typed-limitation-contract
target: src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py
---

# FINDING-009-001：Review 的三层完整性提示错误拒绝如实的 typed Limitation

## Observation

ITER-008 run-012 的第二个方向问题完成两次 Investigation、Draft 和 Review 共四次 Provider 调用。Draft 没有把零候选解释为
实现不存在，而是返回 `LIMITATION`，明确写出业务发现召回未经证实，并携带
`BUSINESS_DISCOVERY_RECALL_UNPROVEN`。Review 仍返回 `REJECT / QUERY_INCOMPLETE`，Answer 因而在交付前失败关闭。

## Evidence and root cause

- request evidence 位于
  `var/iteration-008/slice-001/run-012-live-session/requests/000002-1418b7f70d1d/runs/01/`；terminal 文件 SHA-256 为
  `c4812a82b576ce79cc8b4be871a10cd038b60f2ccc91c7c34b06068c75abb4eb`；
- Gateway 中 Draft output digest 为
  `sha256:f228da6b7cc25cd4a9d29d9a72d55cc75ddece0df4722430c29f9e3e67f3a0de`，disposition 为 `LIMITATION`，正文同时说明零候选与
  recall 未证实，未断言实现不存在；
- Review output digest 为
  `sha256:2c0317e09dc60a1e8f9e9b0ab9827102ac3fc489e880b65b2fb97e8fc2ac7e7c`，decision 为 `REJECT`，唯一 finding 为
  `QUERY_INCOMPLETE`；
- 活动 Review prompt 对 `THREE_LAYER_REVIEW` 无条件规定“三层未全部 COMPLETE 时禁止 APPROVE”。但 typed `LIMITATION`
  正是用缺失的 authority 解释为什么不能形成 supported answer；该规则使一个如实 Limitation 在逻辑上无法通过 Review。

问题不在 Source、查询、网络或浏览器。现有 `SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING` 已要求 Gap/Limitation 作为
一等交付类型，并要求 Review 按 answer type 复核；错误是 prompt 实现把“supported negative 的完整性门槛”误用于 typed
non-supported delivery，因此不改变 System 语义，分类为 `local-implementation`。

## Decision and disposition

Review 继续使用 Application 编译的 `review_completeness_scope`，但按 exact Need outcome 区分：

- `SATISFIED_SUPPORTED_NEGATIVE` 仍必须三层 COMPLETE；
- `KNOWLEDGE_GAP` / `LIMITATION` 只有在保留 exact scope/code、说明缺失 authority 且不升级为 absence、non-existence、total 或
  exhaustive claim 时才可 `APPROVE`；
- 相同零候选证据若被写成“不存在实现”，仍必须 `REJECT / QUERY_INCOMPLETE`。

版本升级为 capability/Strategy `1.5.13`、Prompt `@22` 和 egress policy `@1.4.14`；已归档实验使用过的 `1.5.12`、Prompt
`@21`、policy `@1.4.13` 不复用。输出 vocabulary 保持 `@20`、terminal authority compiler 保持 `@3`，因为 schema 和
Application 投影形状没有变化。冻结能力夹具新增一条 typed Limitation 对照调用，同时保留原越权 negative rejection；总量由
41 变为 42，无 retry、调用预算与产品每题 4–6 次边界均不变。

## Verification after disposition

- 策略、浏览器、能力夹具、qualification、grant、Gateway authorization 与 Slice freeze 离线测试 73/73 PASS；
- 需要本机 AF_UNIX listener 的 Model Egress Gateway 单测在允许该本机能力的执行面 14/14 PASS；
- 允许 AF_UNIX 的完整执行面运行 1042 项，其中 1037 项通过；唯一 4 failure + 1 error 的测试 ID、结果类型与原因精确属于
  `FINDING-008-020` / `FINDING-008-028` 已处置的 ITER-003 historical runtime hold，仍然不得写成 raw full-suite PASS；
- 未读取凭据、未访问 Provider、未启动 Web/live session，不能据此填写 ITER-009 现场体验或 Acceptance verdict。
