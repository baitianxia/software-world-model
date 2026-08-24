---
id: FINDING-010-080
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [engineering, quality, project]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-079]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py, scripts/docs.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py, tests/test_engineering_question_cognition.py, tests/test_engineering_qa_source.py, tests/test_engineering_qa_live.py, tests/test_engineering_qa_preview_cli.py, tests/test_engineering_qa_alpha_cli.py, tests/test_engineering_qa_browser.py, tests/test_docs_gate.py, tests/test_iteration_007_readiness.py, tests]
iteration: ITER-010
classification: verification
scope: systemic
disposition: deterministic-gate-closed-exact-historical-hold-preserved
target: ITER-010-VERIFICATION
---

# FINDING-010-080：material-effect、rewrite coverage 与 exact Claim binding 的确定性 Gate 已闭合

## Observation and evidence

`FINDING-010-079` 增加逐 cited full-content Java entry 的 material-effect scan、第三种
`DRAFT_OMITS_MATERIAL_EFFECT` assessment、Answer early exact observation coverage table，以及所有非 passing assessment 的 exact
challenged-Claim Finding binding。确定性恢复链还证明：full entry 已证明但 sealed Package 缺 atomic observation 时，可由 successor
Verification 复用 predecessor support 补入 typed observation，随后新 Package 的 Answer 和双 Review 才能取得授权；同一 Draft 中另一个
合法 Claim 仍不能冒充被挑战 Claim。

确定性验证得到：

- 三模块 focused 组合 79/79 PASS；全部 Engineering QA 九模块 116/116 PASS；
- focused + docs Gate 149/149 PASS；focused + 历史 ITER-007 readiness oracle 81/81 PASS；
- `python3 scripts/docs.py check` 在本 Finding 与索引最终回写前报告 473 current documents PASS；`compileall` 与
  `git diff --check` PASS；
- 完整 `unittest discover` 共 1182 项。默认 sandbox 为 5 FAIL + 7 ERROR，其中额外 1 FAIL + 6 ERROR 精确来自 AF_UNIX socket
  权限拒绝；允许 AF_UNIX 后 1177 PASS，仅保留 4 FAIL + 1 ERROR。

该五项与此前 Gate 完全相同：四项 ITER-003 V-009 Adapter Conformance 冻结 digest historical hold，以及一项本机 Codex prepared
binary digest historical hold。没有 ITER-010 新失败；raw suite 仍保持 FAIL，本 Finding 不把冻结历史 hold 改写为 PASS。

Manifest exact bindings 为：answer hierarchy
`sha256:bf72d8960dd8f895d9392b85fa4f5ad89b10c74b7800b2bca273b21c23351896`，System fileset
`sha256:15280b0fd44f2d562e6216c126d73a0b8e0f66417fea8335b90198199d6d9f5e`，investigation protocol
`sha256:88f1cae90caac46d5312b438ca9aca63b1c045ca34684ea10d561448ab3c5212`。

## Decision and disposition

- exact observation rewrite table、逐 Java entry effect challenge、`DRAFT_OMITS_MATERIAL_EFFECT`、Package omission successor delta、
  non-passing exact challenged-Claim binding，以及 Strategy/Prompt/Review Schema `@22/@32/@7` 的确定性验证已闭合，可以形成新的 clean
  candidate。
- run-029 永久保持 0/3 PASS，不因本次修复或确定性 PASS 被追认。
- 下一 Gate 必须从该 clean candidate 执行 fresh DeepSeek Conformance、同一持续 Browser 三题、66,000-byte Provider 前负测与 raw
  Answer/Reviewer/challenge-assessment 独立复核；Production Activation 仍不执行。
