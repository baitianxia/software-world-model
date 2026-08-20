---
id: FINDING-008-037
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai, application, architecture, engineering, quality, project]
depends_on: [ITER-008-SLICE-001, FINDING-008-035, FINDING-008-036, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING]
code: [src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_policy.json, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_qualification.py, src/software_world_model/ai_infrastructure/model_egress_gateway.py, validation/structure_world_model_iteration_008/capability/manifest.py, validation/structure_world_model_iteration_008/capability/suite-1.5.9.json, validation/structure_world_model_iteration_008/capability/oracle-1.5.9.json]
tests: [tests/test_world_model_answer_strategy.py, tests/test_iteration_008_capability_harness.py, tests/test_iteration_008_capability_qualification.py, tests/test_model_egress_gateway.py, tests/test_world_model_evaluation_grant.py]
iteration: ITER-008
classification: system-contract
disposition: scope-business-discovery-recall-to-bounded-negative-review
target: SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING
---

# FINDING-008-037：Business discovery recall 不能阻断有完整正向证据的答案

## Observation

run-025 资格证据写回后的 formal `run-007-freeze` PASS。freeze report/deterministic qualification digest 为
`sha256:515a88b8dd73e3144479c8d3880ce025404d3ccce6008ce5ca8b97b0059492b0` /
`sha256:4995715615e23719ebc1a64a10c7fdefd09bbef601b370f1b86a9033dd81120d`；focused 89/89、candidate package 37/37、
docs PASS，full 1036 项只保留 `FINDING-008-020` 的 exact 4 FAIL + 1 ERROR，freeze 中外部模型调用为 0。authorized grant 与
startup receipt digest 为 `sha256:6c433a11ede56cb37824e23e1eb02423eb3c4f03a39b88edf74560323b609594` /
`sha256:79b38f2c6da4ca7df25155d01361cf72ec25682d46a5b854625944035c6f9564`。

正式浏览器提交公开问题 `登录流程是怎样的？` 后，页面在 32.311 秒按 `ANSWER` stage 失败关闭；terminal digest 为
`sha256:2182903afd811555ed23a81609424684d6b07d8bb3877aa68540fc4554490399`。下单与跨域题未执行，hidden canary 未披露，
Production Activation 为 `NOT_EXECUTED`。

## Evidence and root cause

这不是网络、Provider、Draft authority 或 Snapshot completeness 失败：

1. Gateway 完成 5/5 DeepSeek HTTP 200，TLS attempt/success `1/1`、reuse `4`、credential `5/5`、unknown/retry `0`；Gateway
   summary digest 为 `sha256:7349affd6d87133c46ec9bb941229c7c9190649f11c74ef2c124e1ca64f14e98`；
2. 三个 Investigation call 均完成，trace 为 `FINISHED`。四个相关 Query Result 外层 completeness 全部 `COMPLETE`、
   `truncated=false`、limitations 为空；knowledge representation 为 `COMPLETE`，Need Assessment 为 `SATISFIED`；
3. Draft 以 181 output tokens 完成，raw authority collection 为空，output digest 为
   `sha256:4a099805846195be2f0234c5efa986e1ccbb8b52a29b8394869360ac0ef1fa83`。正文正确覆盖 invalid branch、两次
   `recordFailure()`、throw、`issueSession()` 与 return；
4. Review input 同时包含 `business_discovery_recall=UNKNOWN`、`bounded_absence_allowed=false` 与
   `BUSINESS_DISCOVERY_RECALL_UNPROVEN`。这些字段只表达当前权威不能证明全局无实现；本 Draft 是由 exact positive method facts
   支持的行为说明，没有 absence、non-existence、total inventory 或 exhaustive recall 主张；
5. 旧 Prompt `@17` 只说 business-discovery layer “needed by the Draft” 必须 COMPLETE，没有机械说明正向行为 Draft 不需要该层。
   DeepSeek 因而返回唯一 `QUERY_INCOMPLETE` 并 REJECT，output digest 为
   `sha256:2c0317e09dc60a1e8f9e9b0ab9827102ac3fc489e880b65b2fb97e8fc2ac7e7c`。Application 如实失败关闭，但这是假阴性。

根因是 Review completeness 规则把用于 bounded-negative conclusion 的第三层 Oracle 暧昧地扩张到正向事实答案，不是“模型应自行
适应平台”。该缺口同时存在于 Prompt 和 qualification：旧 `REVIEW-018` 只覆盖 UNKNOWN recall 下的错误 absence REJECT，没有覆盖
UNKNOWN recall 下的 supported positive APPROVE。

## Decision and disposition

1. World Model Answering Contract 明确 Business discovery recall 只约束 absence、non-existence、total inventory、exhaustive
   recall 或其他 bounded-negative claim。正向 `SUPPORTED` 行为答案在 query-result/knowledge completeness 为 `COMPLETE`、Need 为
   `SATISFIED` 时，不因 recall `UNKNOWN`、`bounded_absence_allowed=false` 或缺失第三层 Oracle 而自动 `QUERY_INCOMPLETE`。
2. Prompt/Vocabulary 升级为 `@18`，Capability/Strategy 升级为 `1.5.9`，bounded egress policy 升级为 `@1.4.10`。Adapter `@7`、
   connection/audit `@2/@2`、Investigation/terminal compiler `@7/@1`、4—6 product calls、no-retry 与 1000-token output 不变。
3. suite/oracle 升级为 `@1.5.9`，仍保持 18 Case / 40 calls / 18/18。`REVIEW-018` 增加一个 direct reproduction：同为 UNKNOWN
   recall，错误 absence 必须 REJECT，而完整正向行为必须 APPROVE。为保持冻结调用预算，`DIRECT-NEIGHBORHOOD-006` 移除与专门
   `LEGAL-FINISH-009` 重复的最终 FINISH call；candidate → method evidence 的核心覆盖不变。
4. run-025 Qualification、run-007 freeze/grant/session 均永久保留但不适用于新 identity，不得 retry 或继续提交第二题。新 identity
   必须重新执行 2-call Conformance 与完整 Capability；PASS 后再生成全新 formal freeze/Web。

该改变修正 Reviewer 对三层 completeness 的适用范围，不改变三层 bounded absence 规则或 Reviewer 隔离，不新增 ADR。

## Verification and closure

Reviewer/Capability/Gateway/authorization 定向执行面 62/62 PASS；formal-freeze focused 89/89、candidate-package 37/37 PASS。
fake transport 在其中完整执行 40 calls / 18 Case / 18/18，包含 `REVIEW-018` 的 UNKNOWN recall negative REJECT 与 positive
APPROVE 两次独立调用。current documents 341/341、`compileall`、`git diff --check` 与只输出路径的 credential-shaped secret scan
PASS。

允许 AF_UNIX 的完整执行面共 1036 项，其中 1031 PASS；raw exit 1。唯一 4 FAIL + 1 ERROR 的 exact test identity 与 failure marker
仍全部属于 `FINDING-008-020`：三项 `test_iteration_003_v009` Conformance implementation drift FAIL、一项同源 ERROR，以及一项
prepared Codex binary digest drift FAIL。没有新增 failure/error，该事实不冒充 raw full-suite PASS。

当前确定性 identity 为：

- Prompt program / Strategy implementation / output schema digest：
  `sha256:95f25604855d626c4fc398ddbbe7651de3b3412634ca57942dd23317277aeac8` /
  `sha256:df213c24bbc045d7beaa2d9e680b7bcc3e9c955327b8ebc128fbe081f85c94fc` /
  `sha256:9c2f3505c87d677d416c277ea853649f3bf865ffd7dfcaeaea6bc708e080e775`；
- bounded policy / qualification resource policy digest：
  `sha256:3dc42aa19d5825c6a9dae96f0eaa598660d1670ccb94367755080f16eb05647b` /
  `sha256:d3d6317547bd0f5d83ad3f7e01173eb1778a771d927f2311ad50f797f0d4b348`；
- suite/oracle raw digest：
  `sha256:033c6d210d4c6d148f7db44fa92c89b7240b6826bb84370fac438c07366e746c` /
  `sha256:8be44d13e5f4f712f358c7a4574a0de4f6f8e089abd98d679a411851953445cb`；
- packaged bounded Gateway / authorized wrapper raw SHA-256：
  `35a6f9df90ff8193bb3d1211cd50d3a80914fa2e9c23144f3b1854b44ac37e83` /
  `ecfe6db35f5c26151905b04088facb4f8734c203b37495fbfa152fda5eb5ba76`；
- System fileset digest：ITER-008
  `sha256:b34976449f0a6ba8b920e50b5ed9f34307eb466ecb3cbc2c145c16166ad88374`，共享文档使 ITER-007 同步重算为
  `sha256:97133f00100f523a00f5a914f995056c19a8be38f75473906140971881278c74`。

代码、Contract、Finding 与 deterministic Gate 已闭合；下一步必须从 clean candidate 重新执行 live 2-call Conformance 和完整
40-call Capability。取得新 Qualification 前 V-002、V-003 与 V-WEB-001 继续 blocking。
