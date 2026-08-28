---
id: ITER-010-RESULT-V-MVP-EXPERIENCE-001
kind: iteration-result
status: sealed
authority: evidence
owners: [product, project, engineering, quality]
depends_on: [ITER-010-PDR-011, FINDING-010-161, FINDING-010-162, FINDING-010-163, FINDING-010-164, FINDING-010-165, ITER-010-VERIFICATION]
code: [validation/iteration_010_mvp/value_gate/runner.py]
tests: [tests/test_iteration_010_mvp_value_gate.py, tests/test_plan_gate.py, tests/test_docs_gate.py]
iteration: ITER-010
plan_revision_ref: ITER-010-PDR-011
action_ref: ITER-010-ACTION-USER-PLAN-RECOVERY-001
verification_case_id: V-MVP-EXPERIENCE-001
plan_gate_verdict: PASS
evidence_schema: DEVELOPMENT_PLAN_GATE_EVIDENCE@1
evidence_verifier: ITER010_MVP_LIGHT@3
evidence_artifact_path: docs/project/iterations/iteration-010/results/evidence/v-mvp-experience-001.json
evidence_artifact_digest: sha256:10159f091efa5cd6cd32556c16c85b688a023dd0ff8b48fb8a99f1d84d4ce2ad
execution_input_digest: sha256:db3c45d52f7209ba2665a19b45032e84079f29a439a59031ca790a2945b26946
runner_identity_digest: sha256:bb9006ae25b9d24de42c7fdaa14f142dfb9eb8f1a1d80ced08c040479bd55087
runner_receipt_digest: sha256:9947aede77c9d9a0450f5591f331651d79d55489dd46dee8796f230d5eb3b70a
verification_report_digest: sha256:cbc560d4756663e0fa37f4e6c7b27180f45bbae174027b29871c0690d2f9244d
subject_digest: sha256:d1d04ed6ec92dde1bd10f2fc2d082c0389e4ffe5838d76c1bf3a98d929a4fb8a
external_model_call_count: 19
---

# ITER-010 MVP 答案前失败 handoff Result

## Machine verdict and product outcome

`V-MVP-EXPERIENCE-001: PASS / STRUCTURALLY COMPLETE FAILURE HANDOFF`。

这个 machine `PASS` 只证明 PDR-011 的 schema、digest、Git identity 和 runtime reconciliation 闭合；它不表示产品答案质量
PASS。业务结论是严格的 `QUALITY_FAIL_AFTER_ONE_GENERAL_REPAIR`，必须进入用户方向决定。

## Exact identities

- handoff trusted parent：`0be896c1081ae63b4f092d57e6278d31ea0ecf56` / tree
  `e425e602010f27edc5bd719da9cc8efab34c486b`；
- 实际运行的 product candidate：`a5c780f51fa5242ee8209766712ad408ed023f80` / tree
  `4dcf8b0eca2f50b7618d0af1c43eca1613bace94`；
- public Source：`macrozheng/mall` commit `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` / tree
  `047d79d8588b76013c260f3f1a9565707301a60a`。

handoff parent 与 product candidate 在 evidence 中分开绑定，避免把后续治理提交冒充已执行的产品版本。

## Truthful failure record

- run-052 保留为独立 Artifact Session，没有 browser capture，原始登录调用链问题在 initial 与 fresh same-profile repair
  中连续缺少 `action.operation`，在答案生成前失败关闭。
- run-053 保留第二个 Artifact Session 与真实 browser capture。商品入口/职责边界案例的 initial/repair 均把
  `BOUNDARY` observation 用作 Claim support；未登录/权限不足案例的 initial/repair 再次连续缺少
  `action.operation`。两条均在 Delivery 前失败关闭。
- 三条记录覆盖 system purpose/entry、behavior/call-flow/side-effect 与 failure/authorization/unknown；后两条未参与修复。
- 所有内嵌 model output 均是被拒绝的 raw proposal，不是授权 Answer。`answer_emitted=false`、Citation=`0`、
  Review=`false`、current Codex comparison=`false`；没有补造任何缺失产物。

## Runtime reconciliation

- Artifact Session：`2`；
- Ark external call / dispatch / credential / TLS / HTTP：`19 / 19 / 19 / 19 / 19`；
- DeepSeek external call / dispatch / credential / TLS / HTTP：`0 / 0 / 0 / 0 / 0`；
- request retry / human approval request / full regression / Production Activation：`0 / 0 / 0 / NOT_EXECUTED`。

run-052 与 run-053 的 Ark Gateway SQLite raw-byte digest 分别为
`sha256:0d9fbe37fb90a5ba39bb58c061979edea03fead19ae26a24bb4cb804f683f427` 与
`sha256:edf27e17f53268e695d44fc7571489a05181ba79cb6781dac04460c0b1acc9b7`。两个 DeepSeek Gateway SQLite 均为空调用库，
raw-byte digest 均为 `sha256:99598e0e95a9d2ded6a1528018d13bbc38d1779ee341e375e8ca86afd0a14bc2`。

## Trust boundary and consequence

@3 runner 不认证 local capture 真实性，不判定 semantic answer quality，也不把失败 proposal 提升为 Answer。它从 trusted parent
字节独立重放 evidence，并将本 Result 的唯一后续迁移到
`ITER-010-ACTION-USER-DIRECTION-DECISION-001 / V-PREVIEW-002`。

`FINDING-010-165` 的 plan-gate 修正只区分“当前 sealing action 禁止新外调”与“Result 对历史 product run 的调用对账”；它没有把当前
动作改成 external，也没有修改 19/0 runtime 事实。

产品代码、Prompt/Reviewer、Web、Provider dispatch、hardening、full regression、hidden、第二工程和 Production 继续锁定。
用户方向 receipt 只能记录 `CONTINUE / REWORK / REDIRECT / REJECT`；任何后续实现均仍需新 PDR、fresh 明确授权与可信父 cutover。
