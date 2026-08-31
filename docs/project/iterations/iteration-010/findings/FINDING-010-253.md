---
id: FINDING-010-253
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai, quality, operations]
depends_on: [FINDING-010-252, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: aggregate-anchor-diagnostics-nonassertive-closure-and-progress-sensitive-layered-repair
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-253：run-124 的 Reviewer 只修一项锚点并借 NON_ASSERTIVE 绕过其余事实

## Observation and execution evidence

clean product commit/tree
`8130a128c76478fde43bb9210fc5d02bd9f61f00 / da62753f7c4dcc6c66274b8ae357a2d7c53b7b26` 上，fresh Ark qualification
`ccrun_5f745da6cc624cb9872c5c252e74f213` 以 actual `glm-5.3`、13/13 cases、TLS/credential/HTTP `2/2/2`、retry/unknown 0
通过；result digest 为 `sha256:178e92e69ade36886c1be0d37f8437cf50aaa2a8465214eaee952dcf1a6cd99c`，文件 SHA-256 为
`d21e96a1b5b6119d422416c5b31f26b4f740c09024999649bf8b0c1c60442ed2`。

run-124 的新 Session config 初始文件模式为 `0644`，owner-private gate 在 listener、credential、Gateway 与 dispatch 前以
`CONTROL_STATE_DENIED` 拒绝；将该新文件及关联证据收紧为 `0600` 后，同一尚未消费的 preparation 正常启动。页面冻结 Q4 最终形成
`TURN 1 FAILED / REVIEWER_MODEL_CALL_REJECTED / PROVIDER_OUTPUT_INVALID / STRUCTURED_OUTPUT_INVALID`，Evidence Package
`agent_evidence_package_9befb662c2b74d5b9e9eb585589b473a` 与 Draft `agent_answer_3cebbe574b9c4b7981ac0fc9a42b82e9` 已形成，但
fresh Review 与 Delivery 均不存在。Ark 8 个 calls 全部 `COMPLETED`，TLS/credential/HTTP `8/8/8`；DeepSeek dispatch、request retry、
pre-dispatch failure 与 post-dispatch unknown 均为 0，Production 未执行。terminal digest 为
`sha256:5af183554e72be7adf2def2d7a1017d2311e1290cd4a03c6a356b0b96b2abbe8`，terminal file SHA-256 为
`e81415b60406f63ae77266639e77a32e3d931ab1d22bf70bfebb74531814c858`。

第 7 个 Ark call 的 comprehensive Review 把 6 个 Draft units 判为 `APPROVED`。Application 的 `FINDING-010-252` gate 正确拒绝了它，但旧
decoder 遇到第一个 unmatched anchor 即只返回通用错误。独立重算显示至少三个 `COVERED` 锚点未命中 mapped Claim：unit 1 的
``EsProductService``、unit 2 的 ``EsProductDao.getAllEsProductList(...)``、unit 3 的 ``delete(id)``。更严重的是 unit 5 仍断言
``EsProductDao`` 的 SQL/mapper “位于 ``src/main/resources``”，却被标为 `NON_ASSERTIVE`；该 unit 还有 ``saveAll``、``save``、
``deleteById``、``deleteAll`` 等技术锚点，因此完全绕开了只检查 `COVERED` 的 exact-anchor gate。

第 8 个 Ark call 是第一次 bounded format repair。它只把 unit 2 改为 `DEFECT`，仍保留 unit 1、unit 3 的 unmatched anchors 与 unit 5 的
`NON_ASSERTIVE` 逃逸；同时 `DEFECT` 仍携带 Claim refs，违反 typed disposition shape。初始失败与修复失败都被粗分为
`CLOSED_OUTPUT_CONTRACT`，`_can_followup_format_repair` 因 category 未变化而拒绝使用尚获准的第二个也是最后一个 repair slot。这里没有 Ark
网络故障、fallback 条件或 retry；失败来自 Application diagnostic/repair convergence contract。

## Exact first divergence

最早系统偏差有三部分，均为通用 Review closure 缺口：

1. decode 在第一项 anchor mismatch 立即抛错，没有把同一 Review 的全部 unit/anchor 违规投影给 bounded repair；Provider 只能猜测其他错误。
2. `NON_ASSERTIVE` 的自然语言约束没有机械下界，含 technical anchors 的事实段可借该 disposition 绕过 Claim/Boundary/Finding closure。
3. 第二层 repair 只比较四种粗粒度 validator category；同属 `CLOSED_OUTPUT_CONTRACT` 但 exact diagnostic 已变化的真实收敛进度被当作无进展。

这不是 mall、Elasticsearch、Dao 或某一 Provider 特判。任何多违规 Review 都可能只修第一项；任何含路径/symbol/method/literal 的事实段都可能被
错误标为 `NON_ASSERTIVE`；任何 semantic repair 后暴露新的 typed closure 都可能落在同一粗类别。

## Decision and disposition

1. 除整个 fragment 是 pure Markdown heading 或 standalone bold label 外，`NON_ASSERTIVE` unit 不得含任何 Markdown inline-code anchor；
   ``**标签**：事实正文`` 不是 standalone label。其他带技术锚点正文必须使用 `COVERED`、合法 defer 或 bound `DEFECT`。
2. Review decode 必须一次扫描 exact ordered unit set，聚合全部 `COVERED` unmatched anchors 与 nonstructural `NON_ASSERTIVE` anchors，形成最多
   32 项的 bounded Application-derived diagnostic，包含 exact unit index、violation kind 与 bounded anchor。它只是机械修复坐标，不是 Evidence
   或 semantic truth；seal 与 Delivery 仍分别重算。
3. 一个 role step 仍最多两次 fresh same-profile format repair。第二次只在 proposal bytes 已变化，且 validator category 改变，或两次都为
   `CLOSED_OUTPUT_CONTRACT` 但 exact diagnostic message 已变化时允许；同 output、同 diagnostic 与 `CLOSED_SCHEMA_SHAPE` 守恒失败仍立即停止。
   这不会增加 Provider retry、fallback eligibility 或 15-call logical Turn budget。
4. anchor repair directive 必须要求一次修复每个列出的 unit/anchor；把 unit 改为 `DEFECT/NON_ASSERTIVE` 时必须清空 Claim/Boundary refs，
   `DEFECT` 还必须绑定现有 Finding。Application 不静默修改 Reviewer 的 semantic choice。
5. 协议族升级为 `conversational-engineering-agent@38 / prompt@38 / ENGINEERING_AGENT_PRIMARY_INPUT@34 /
   ENGINEERING_AGENT_REVIEW_INPUT@27 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@32`。Review output `@10` 与 sealed Review `@5` shape 不变；route、
   Provider adapter、资格、披露、Source/Tool/dispatch budget、no-retry 与非 Production 边界均不改变。

## Verification

新增负向 fixture 要求非结构 `NON_ASSERTIVE` 技术锚点失败，并确认 pure heading 的 revision anchor 不被误判；run-123-like fixture 现在返回 exact
anchor diagnostic。分层 repair fixture 证明不同 exact `CLOSED_OUTPUT_CONTRACT` diagnostic 可使用第二个 slot，而既有 closed-shape drift 仍停止。
Agent/Model/Tool 定向集合 `86/86` PASS，相邻 Slice1 集合 `186/186` PASS，659 份 current documents check PASS；计划门禁、clean commit、
fresh Ark qualification 与 run-125 同题 live successor 仍须依次完成。run-124 不取得 Quality 或 MVP PASS。
