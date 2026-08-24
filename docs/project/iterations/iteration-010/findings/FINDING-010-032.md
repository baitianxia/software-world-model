---
id: FINDING-010-032
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [quality, engineering]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-008-020, FINDING-010-013]
code: [pyproject.toml, scripts/docs.py, src/software_world_model]
tests: [tests]
iteration: ITER-010
classification: verification
scope: individual
disposition: preserve-the-existing-runtime-hold-with-zero-iter010-rework-regressions
target: ITER-010-VERIFICATION
---

# FINDING-010-032：返工完整回归仅保留既有 runtime hold

## Observation

持续 Alpha、Session Authority、答案层级、Reviewer Gate 和同源 ingress 完成后，在允许本机 AF_UNIX 的实际执行面运行完整测试。raw suite
仍非 PASS，但未通过项与 `FINDING-008-020 / FINDING-010-013` 已记录的两类冻结环境漂移完全同源；本次返工没有新增失败。

## Evidence and root cause

- Engineering QA、docs gate 与 ITER-007 fileset 聚焦回归：147/147 PASS；
- current docs gate：424 current documents PASS；
- 完整命令 `env PYTHONPATH=src:. python3 -m unittest discover -s tests -q`：1141 tests，1136 PASS，raw
  `FAILED (failures=4, errors=1)`；
- 唯一 ERROR 为 `test_input_freeze_and_evaluator_are_mechanically_closed`，marker 仍是
  `QUALIFICATION_INVALID: V-009 Adapter Conformance implementation drifted`；
- 三个同源 FAIL 为 `test_closed_evaluation_rejects_semantically_tampered_conformance_binding`、
  `test_closed_live_harness_seals_all_seven_cases_and_valid_qualification`、
  `test_conformance_unknown_seals_pre_dispatch_intent_and_stays_blocking`；
- 另一个 FAIL 为 `test_agent_baseline_protocols_and_prepared_mature_cli_are_exact`：当前 Codex binary digest
  `09db9560f6f9dec139d3324254fb3c8fdbad5ecce1d8c794113dc15294f6aefd` 不等于 frozen
  `9f6748b4ab10ffc92c28b9ccedae89e61a302bbc011df7d276ee38f55906e481`；
- 沙箱内单独跑 Model Egress Gateway 会因 AF_UNIX denial 产生 1 FAIL + 5 ERROR；按其真实本机边界重跑为 14/14 PASS，完整回归也在同一
  允许 AF_UNIX 的执行面完成；
- suite 仍报告既有 SQLite `ResourceWarning`，本 Finding 不把它误写为已修复。

根因仍是被冻结的 ITER-003 Adapter Conformance/Codex binary 与当前执行环境不一致，而不是 ITER-010 Application、Session、Gateway、
Source、Answer/Review、Browser 或文档门禁回归。

## Decision and disposition

raw suite 保持 FAIL，不修改冻结资产、skip 测试或追认当前 runtime。返工的 deterministic regression gate 只允许
`PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD`：未通过项的数量、类型和 marker 必须与上述集合一致，其余 1136 项全部通过。任何新增、缺失、
结果类型或 marker 漂移都阻断 product freeze。

该证据只支持继续准备 clean candidate；它不构成真实 Provider、持续 listener/browser、三题答案质量、用户方向、Slice Acceptance 或
Production Activation PASS。
