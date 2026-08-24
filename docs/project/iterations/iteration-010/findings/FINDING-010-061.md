---
id: FINDING-010-061
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-060]
code: [src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_model_source.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_cognition.py, tests/test_engineering_qa_source.py, tests/test_engineering_qa_live.py, tests/test_engineering_qa_preview_cli.py, tests/test_engineering_qa_alpha_cli.py, tests/test_engineering_qa_browser.py, tests]
iteration: ITER-010
classification: verification
scope: systemic
disposition: preserve-exact-historical-full-suite-hold-after-finish-partition-and-gap-exhaustion
target: ITER-010-VERIFICATION
---

# FINDING-010-061：exact-once FINISH 与 material-gap exhaustion 无新增完整回归失败

## Observation and evidence

`FINDING-010-060` 的实现与 System/docs 回写完成后：

- 全部 Engineering QA 组合测试 101/101 PASS；Provider Schema description、Initial/Verification Prompt 与 exact run-021 reproducer 均覆盖
  supported/non-supported disjoint + checklist exact-once，Question Understanding/Initial Prompt 同时固定 mandatory minimum 与剩余预算内的
  material-gap exhaustion；
- current docs generate/check 455/455 PASS，`compileall` 与 `git diff --check` PASS；
- 默认 workspace sandbox 的 full discovery 共 1167 项，raw 为 5 FAIL + 7 ERROR，其中 1 FAIL + 6 ERROR 精确来自 AF_UNIX
  listener/connect 被 sandbox 拒绝；
- 允许本机 AF_UNIX 的同一 full 命令仍为 1167 项，其中 1162 PASS，raw 唯一 4 FAIL + 1 ERROR：3 FAIL + 1 ERROR 为冻结 V-009
  Adapter Conformance implementation drift，另 1 FAIL 为本机 Codex binary digest 与历史 prepared digest 不同。identity、结果类型与
  marker 与此前 historical hold 完全相同，没有 ITER-010 新失败。

## Decision and disposition

raw full suite 继续记录为 FAIL，不能写成全通过；Slice1 只以
`PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD` 形成新的 clean candidate。该结果闭合 run-021 后的 deterministic Gate，不证明当前
DeepSeek 已按 exact-once partition 交付 Q2，也不证明三题、持续体验、Acceptance 或 Production Activation；fresh Conformance、新
candidate live 与 raw answer/reviewer 独立复核仍是 blocking evidence。
