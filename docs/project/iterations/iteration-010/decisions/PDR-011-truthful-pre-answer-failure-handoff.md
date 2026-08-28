---
id: ITER-010-PDR-011
kind: project-decision
status: accepted
authority: project-decision
owners: [product, project, architecture, engineering, quality, ai]
depends_on: [FINDING-010-161, FINDING-010-162, FINDING-010-163, ITER-010-PDR-010, PROJECT-GOVERNANCE-PLAN-EXECUTION]
code: [scripts/docs.py, scripts/plan_gate.py, validation/iteration_010_mvp/value_gate/runner.py]
tests: [tests/test_docs_gate.py, tests/test_plan_gate.py, tests/test_iteration_010_mvp_value_gate.py]
iteration: ITER-010
decision: REWORK
rework_strategy: TRUTHFUL_PRE_ANSWER_FAILURE_HANDOFF
decision_ref: local-user-message-utf8:sha256:382638cd16fdbc85c08a4202a94e630fe4c973ce03bb0d8a1671cbe4ee151aa7
effective_scope: ITER-010-SLICE-001
coding_input: false
---

# PDR-011：如实密封答案前失败并进入用户判向

## Context

PDR-010 的一次通用修复停止条件已经满足。冻结 product candidate
`a5c780f51fa5242ee8209766712ad408ed023f80` 上，run-052 原问题与 run-053 两个异质复验均在 Answer、Citation、Package 和 fresh Review
之前关闭；19 次 Ark dispatch 均完成 TLS/credential/HTTP，DeepSeek dispatch/credential/TLS/HTTP 均为零。继续碰答案不再授权。

`ITER010_MVP_LIGHT@2` 却只接受已有三份完整系统答案和单一 Session 的成功形状。填写这些字段会伪造产品输出。与此同时普通 plan revision
要求先进入 governance action 并有 PASS Result，形成 `FINDING-010-163` 所述机械自锁。用户现已明确授权最小治理修订。

## Decision

### 1. 一次性恢复边界

从 exact base `120a8903462caf04fbf7bda0c1afa07e3133d448` / tree
`883bdde37eec62856139e7fc00ee38691d311b73` 执行一次 trust-root recovery。本治理提交不冒充 PDR-010 transition gate PASS；它只安装
PDR-011、Manifest、`ITER010_MVP_LIGHT@3`、对应测试和必要文档。产品代码、Prompt、route、Provider 调用、浏览器复验、full regression、
hardening、hidden、第二工程和 Production 均不在范围内，也不得在该提交生成 Result。

### 2. 当前动作只完成失败 handoff

机器 action ID 与 Result path 保持不变，以避免改写历史身份；其当前语义收窄为“密封已经发生的 pre-answer failure handoff”。coding 和 external
execution 关闭，所有执行锁关闭。唯一允许的后续变更是内嵌既有 evidence、生成唯一 `V-MVP-EXPERIENCE-001` Result、更新当前文档并按预注册
transition 进入 `V-PREVIEW-002`。

### 3. @3 verifier 的 truthful failure contract

`ITER010_MVP_LIGHT@3` 只接受当前已观察到的 `QUALITY_FAIL_AFTER_ONE_GENERAL_REPAIR` failure handoff，并要求：

- exact product candidate commit/tree/raw commit 与 handoff governance parent commit/tree/raw commit 分开绑定；runtime 仍回指实际运行的 product
  candidate，plan gate 则把 handoff parent 绑定到 Result 提交的真实父节点；
- 内嵌 run-052/053 的 exact turn-scope、terminal 与可用 browser JSON 原始 bytes/digest；run-052 无 browser capture 必须如实为 null，不能补造；
- 允许多个 exact Artifact Session；保留一个原失败和两个 unseen 异质复验，覆盖 purpose/entry、behavior/call-flow/side-effect 与
  failure/authorization/unknown 三类；
- 每条失败记录绑定 initial 与 fresh same-profile repair 的 exact Gateway call/output bytes，但明确这些 raw model proposals 不是授权 Answer；
  `answer_emitted=false`、Citation=0、Review=false、current Codex comparison=false；
- terminal/Gateway 摘要逐 Session 对账 Ark dispatch/credential/TLS/HTTP、DeepSeek 零调用、retry=0、human approval=0、full regression=0；
- machine `PASS` 只表示 schema、digest、Git identity 和 runtime reconciliation 闭合。local capture authenticity 与 semantic quality 继续为 false，
  包内业务结论仍是严格 `QUALITY_FAIL_AFTER_ONE_GENERAL_REPAIR`。

### 4. Runner 与 Result 分离

本 PDR、Manifest、runner 和测试必须先提交，形成新的 trusted parent。只有后续提交才能用该 trusted parent runner 重放 exact evidence bytes、密封
Result 并移动动作。不得在同一候选中修改 verifier 又让它验证自己的 Result。

### 5. 用户方向不自动解锁开发

失败 Result 完成后进入现有 governance action `ITER-010-ACTION-USER-DIRECTION-DECISION-001 / V-PREVIEW-002`。用户可以决定
`CONTINUE / REWORK / REDIRECT / REJECT`。方向 receipt 仍只记录决定；即使 `CONTINUE`，任何后续产品工作也需要新的 PDR、fresh 明确授权和
可信父 cutover。

## Consequences

- 产品修复和外部运行保持停止，不再等待或调用 DeepSeek。
- 不生成不存在的系统 Answer、Citation、Review 或 Codex comparison；失败本身作为方向证据交给用户。
- PDR-010 继续拥有产品设计和停止条件；PDR-011 只修正 failure-handoff/治理表达能力，不降低产品质量标准。
- 本地用户消息 digest 不是平台认证身份或不可抵赖签名；一次性 recovery 的边界与不合规声明必须在 commit 和 Manifest 中可见。
