---
id: FINDING-010-007
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, security, quality]
depends_on: [ITER-010-SLICE-001, FINDING-010-004, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING]
code: [src/software_world_model/application_services/engineering_question_answering.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: bind-successor-ledger-gap-and-package-to-one-exact-predecessor
target: src/software_world_model/application_services/engineering_question_answering.py
---

# FINDING-010-007：successor Ledger 必须绑定 prior Package

## Observation

后继 `QuestionEvidencePackage` 已包含 `prior_package_digest`，Reviewer 的 Verification Request 也绑定 current Package；但
`EvidenceLedger.successor()` 原先只记录 parent Ledger seal。主服务把正确对象一起传递，最终 Result chain 也会比较相邻 Package digest，
可是 successor Ledger 的 gap entry 本身没有机械证明“该 gap 与这个 prior Package 属于同一 predecessor”。

## Evidence and root cause

- `VERIFICATION_REQUEST` entry 原 references 只有 parent Ledger seal，details 没有 prior Package digest；
- `QuestionEvidencePackage.seal()` 对 generation > 1 只要求 prior Package digest 非空，没有与 successor Ledger entry 比较；
- `VerificationInvestigationInput` 的 Result suffix 检查能拒绝旧 raw Result，却没有同时验证 Verification Request、current Package、parent
  Ledger seal 和 successor generation 的共同 predecessor；
- `EngineeringQuestionExecutionResult` 会在链尾比较相邻 Package digest，因此正常服务没有观察到错批答案；缺口是身份错误未在最早
  Ledger/role-input/package 边界失败关闭。

根因是 Ledger predecessor identity 和 Package predecessor identity 分别实现后没有建立交叉引用。既有 Contract 已明确旧包/新包、gap
和 Ledger Revision 不得混用，分类为 `local-implementation / systemic`。

## Decision and disposition

- `EvidenceLedger.successor()` 必须接收 exact prior Package digest，并把 parent Ledger seal 与 prior Package digest 同时写入保留
  references；保留 details 不能由 caller 覆盖；
- `VerificationInvestigationInput` 在交给任何角色前验证 Verification Request package digest、gap entry ID/digest、successor
  generation、parent Ledger seal、prior Package digest 和新增 Result suffix；结构化 Input Builder 再执行同一检查；
- successor Package seal 要求其 `prior_package_digest` 与 latest Verification Request entry 的 details/references 完全一致；
- final Result chain 还要逐代验证 `ledger.parent_seal_digest == previous ledger.seal_digest`，形成前移校验后的末端重验。

该处置不改变现有协议语义、一次补证 preview 上限、角色权限或 live 授权，只把既有 identity invariant 机械闭合。

## Verification

完整补证状态机验证 gap entry 同时引用第一代 Ledger seal 与 Package digest，第二代 Package 绑定同一 prior digest；把另一个 digest
替换为 current Package 时，Verification role input 在调用角色前以 authority inconsistency 拒绝。既有旧 raw Result 隔离、后继重答重审
和完整 Result chain 测试继续通过。
