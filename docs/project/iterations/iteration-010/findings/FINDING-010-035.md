---
id: FINDING-010-035
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [quality, engineering]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-032, FINDING-010-033, FINDING-010-034]
code: [pyproject.toml, scripts/docs.py, src/software_world_model]
tests: [tests]
iteration: ITER-010
classification: verification
scope: individual
disposition: preserve-historical-runtime-hold-after-observation-contract-upgrade
target: ITER-010-VERIFICATION
---

# FINDING-010-035：协议 @3 完整回归没有新增失败

## Observation

evidence-grounded material observation contract、Reviewer observation audit 和 private Gateway SQLite 完成后，完整测试总数从 1141 增至
1144。raw suite 仍非 PASS，但所有未通过项继续精确属于已登记的历史 runtime hold，没有 ITER-010 新回归。

## Evidence and root cause

- Engineering QA 全组 83/83 PASS；docs/freeze/browser 聚焦组 86/86 PASS；current docs 427/427 PASS；
- 在允许测试所需本机 AF_UNIX 的执行面运行 `PYTHONPATH=src:. python3 -m unittest discover -s tests -q`：1144 tests，1139 PASS，raw
  `FAILED (failures=4, errors=1)`；
- 唯一 ERROR 仍是 `test_input_freeze_and_evaluator_are_mechanically_closed`，marker 为
  `QUALIFICATION_INVALID: V-009 Adapter Conformance implementation drifted`；
- 三个同源 FAIL 仍是 `test_closed_evaluation_rejects_semantically_tampered_conformance_binding`、
  `test_closed_live_harness_seals_all_seven_cases_and_valid_qualification`、
  `test_conformance_unknown_seals_pre_dispatch_intent_and_stays_blocking`；
- 另一个 FAIL 仍是 `test_agent_baseline_protocols_and_prepared_mature_cli_are_exact`，current Codex digest
  `09db9560f6f9dec139d3324254fb3c8fdbad5ecce1d8c794113dc15294f6aefd` 与 frozen
  `9f6748b4ab10ffc92c28b9ccedae89e61a302bbc011df7d276ee38f55906e481` 不同；
- 默认沙箱的首轮 raw run 另出现 AF_UNIX permission denial；在实际本机执行面重跑后这些额外 1 FAIL + 6 ERROR 全部消失，不能混入产品
  回归结论；
- 已知 SQLite `ResourceWarning` 仍存在，本 Finding 不把它误写为已修复。

## Decision and disposition

继续使用 `PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD`：只允许上述 4 FAIL + 1 ERROR 的 exact identity/type/marker/digest，其他 1139 项必须
通过。不得改 frozen ITER-003 asset、skip 测试或把 raw suite 写成 PASS。

该证据允许准备新的 clean candidate 与 current DeepSeek Conformance；不构成 Provider answer quality、持续三题体验、Slice Acceptance 或
Production Activation PASS。
