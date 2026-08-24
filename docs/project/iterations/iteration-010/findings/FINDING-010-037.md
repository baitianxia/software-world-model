---
id: FINDING-010-037
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [quality, engineering]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-035, FINDING-010-036]
code: [pyproject.toml, scripts/docs.py, src/software_world_model]
tests: [tests]
iteration: ITER-010
classification: verification
scope: individual
disposition: preserve-historical-runtime-hold-after-coverage-limitation-fix
target: ITER-010-VERIFICATION
---

# FINDING-010-037：coverage-only Limitation 修复的完整回归没有新增失败

## Observation and evidence

`FINDING-010-036` 的 domain/schema/prompt 与治理契约修复加入三条直接回归后，最终完整测试总数为 1147：

- Answer/strategy/model-source 定向 49/49 PASS；Engineering QA 全组 86/86 PASS；current docs 430/430 PASS；
- 在允许测试所需本机 AF_UNIX 的执行面运行 `PYTHONPATH=src:. python3 -m unittest discover -s tests -q`：1147 tests，1142 PASS，raw
  `FAILED (failures=4, errors=1)`；
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

继续使用 `PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD`：新增修复和三条回归没有产生 ITER-010 新失败，raw suite 仍不得写成 PASS，也不得修改
frozen ITER-003 asset 或 skip 测试。

该证据只允许形成新的 clean candidate、current DeepSeek Conformance 与持续 Alpha session；不构成 Provider answer quality、三题体验、
Slice Acceptance 或 Production Activation PASS。
