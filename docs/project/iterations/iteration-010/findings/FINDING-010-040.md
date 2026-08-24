---
id: FINDING-010-040
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [quality, engineering]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-039]
code: [src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests]
iteration: ITER-010
classification: verification
scope: individual
disposition: preserve-historical-runtime-hold-after-provider-failure-audit-fix
target: ITER-010-VERIFICATION
---

# FINDING-010-040：Provider 失败审计修复的完整回归没有新增失败

## Observation and evidence

`FINDING-010-039` 的 exact terminal failure propagation 与 policy rejection audit 修复加入直接回归后：

- model-source 定向 11/11、Engineering QA 全组 87/87 PASS；修改 current docs 后最终文档门禁 433/433 PASS；
- 默认沙箱执行完整 1148 项时，除历史 hold 外额外出现 6 ERROR + 1 FAIL；它们精确来自 AF_UNIX listener
  `Operation not permitted`、socket 未创建及其派生审计断言，不是产品回归；
- 在允许测试专用本机 AF_UNIX 的执行面重跑相同命令 `PYTHONPATH=src:. python3 -m unittest discover -s tests -q`：1148 tests，
  1143 PASS，raw `FAILED (failures=4, errors=1)`；
- 唯一 ERROR 仍是 `test_input_freeze_and_evaluator_are_mechanically_closed`，marker 为
  `QUALIFICATION_INVALID: V-009 Adapter Conformance implementation drifted`；
- 三个同源 FAIL 仍是 `test_closed_evaluation_rejects_semantically_tampered_conformance_binding`、
  `test_closed_live_harness_seals_all_seven_cases_and_valid_qualification`、
  `test_conformance_unknown_seals_pre_dispatch_intent_and_stays_blocking`；
- 另一个 FAIL 仍是 `test_agent_baseline_protocols_and_prepared_mature_cli_are_exact`，current/frozen Codex digests 仍分别为
  `09db9560f6f9dec139d3324254fb3c8fdbad5ecce1d8c794113dc15294f6aefd` 与
  `9f6748b4ab10ffc92c28b9ccedae89e61a302bbc011df7d276ee38f55906e481`；
- 已知 SQLite `ResourceWarning` 仍存在，没有被本 Finding 写成已修复。

## Decision and disposition

继续使用 `PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD`：新增 Provider 失败分类/审计修复及其回归没有产生 ITER-010 新失败；raw suite 仍不得
写成 PASS，也不得修改冻结的 ITER-003 asset、跳过测试或把沙箱权限噪声混入产品失败集合。

该证据只允许形成新的 clean candidate、current DeepSeek Conformance 与持续 Alpha session；不构成两道后续问题的答案质量、三题体验、
Slice Acceptance 或 Production Activation PASS。
