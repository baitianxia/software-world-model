---
id: FINDING-010-078
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [engineering, quality, project]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-077]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py, scripts/docs.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py, tests/test_engineering_question_cognition.py, tests/test_engineering_qa_source.py, tests/test_engineering_qa_live.py, tests/test_engineering_qa_preview_cli.py, tests/test_engineering_qa_alpha_cli.py, tests/test_engineering_qa_browser.py, tests/test_docs_gate.py, tests/test_iteration_007_readiness.py, tests]
iteration: ITER-010
classification: verification
scope: systemic
disposition: deterministic-gate-closed-exact-historical-hold-preserved
target: ITER-010-VERIFICATION
---

# FINDING-010-078：逐 challenge scope assessment 的确定性 Gate 已闭合

## Observation and evidence

`FINDING-010-077` 为每个 evidence-boundary lead 建立 Application-owned stable `challenge_id`，要求 challenge Review 对 exact ID 集合
逐项返回 evidence scope、Draft scope 与受控 disposition；越界项必须绑定同输出中作用于被挑战 Claim 的 Finding。Application 在
Review accept 与 Authorization 都重新投影并验证集合，Provider 不能通过少报、多报、重复或自造 ID 缩小审计范围。

确定性验证得到：

- 三模块 focused 组合 78/78 PASS；全部 Engineering QA 九模块 115/115 PASS；
- focused + docs Gate 148/148 PASS；focused + 历史 ITER-007 readiness oracle 80/80 PASS；
- `python3 scripts/docs.py check` 在本 Finding 与索引最终回写后报告 472 current documents PASS；`compileall` 与
  `git diff --check` PASS；
- 完整 `unittest discover` 共 1181 项。默认 sandbox 为 5 FAIL + 7 ERROR，其中额外 1 FAIL + 6 ERROR 精确来自 AF_UNIX socket
  权限拒绝；允许 AF_UNIX 后 1176 PASS，仅保留 4 FAIL + 1 ERROR。

该五项与此前 Gate 完全相同：四项 ITER-003 V-009 Adapter Conformance 冻结 digest historical hold，以及一项本机 Codex prepared
binary digest historical hold。没有 ITER-010 新失败；raw suite 仍保持 FAIL，本 Finding 不把冻结历史 hold 改写为 PASS。

Manifest exact bindings 为：answer hierarchy
`sha256:bf72d8960dd8f895d9392b85fa4f5ad89b10c74b7800b2bca273b21c23351896`，System fileset
`sha256:c2a4cffcebb32a8885ecf0e409de83a1b354fcf7e7434347ceab0fd6929f8823`，investigation protocol
`sha256:97189e5e6849f85e68b73251ceb6d62585d33eb84c883141ccd0fc939489d249`。

## Decision and disposition

- stable challenge identity、逐项 assessment、越界 Finding-on-challenged-Claim binding、最终 Authorization 重验，以及
  Strategy/Prompt/Review Schema `@21/@31/@6` 的确定性验证已闭合，可以形成新的 clean candidate。
- run-028 永久保持 Q1/Q3 PASS、Q2 FAIL，不因本次修复或确定性 PASS 被追认。
- 下一 Gate 必须从该 clean candidate 执行 fresh DeepSeek Conformance、同一持续 Browser 三题、66,000-byte Provider 前负测与 raw
  Answer/Reviewer/challenge-assessment 独立复核；Production Activation 仍不执行。
