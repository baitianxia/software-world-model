---
id: FINDING-010-013
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [quality, engineering]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-008-020, FINDING-010-012]
code: [src/software_world_model]
tests: [tests]
iteration: ITER-010
classification: verification
scope: individual
disposition: preserve-the-exact-historical-runtime-hold-while-requiring-zero-new-failures-for-the-slice1-product-freeze
target: ITER-010-VERIFICATION
---

# FINDING-010-013：Slice1 冻结前回归只有既有五项历史 runtime hold

## Observation

ITER-010 新实现和 launcher 完成后，沙箱内 full discovery 会因 AF_UNIX 被拒绝产生额外 socket 伪失败，不能作为冻结结论。在允许本机
Unix socket 的执行面重跑后，suite 原始退出仍为 1，但全部未通过项精确等于 `FINDING-008-020` 已密封的 ITER-003 Codex CLI/runtime
drift；没有 ITER-010 或其他新增失败。

## Evidence and root cause

- ITER-010 聚焦测试：58/58 PASS；覆盖 Application 状态机、五角色 schema/receipt、逐输入 disclosure/Gateway、持久 Structure
  Cognition、Local Git Broker/Worker、prepared Web、DeepSeek fake transport 和 trusted launcher；
- 文档检查：389 current documents PASS；`py_compile` 与 `git diff --check` PASS；
- 允许 AF_UNIX 的 full discovery：1108 tests，1103 PASS，原始状态 `FAILED (failures=4, errors=1)`；
- 唯一 ERROR：`test_input_freeze_and_evaluator_are_mechanically_closed`，marker 为
  `QUALIFICATION_INVALID: V-009 Adapter Conformance implementation drifted`；
- 三项同源 FAIL：`test_closed_evaluation_rejects_semantically_tampered_conformance_binding`、
  `test_closed_live_harness_seals_all_seven_cases_and_valid_qualification`、
  `test_conformance_unknown_seals_pre_dispatch_intent_and_stays_blocking`；
- 唯一其他 FAIL：`test_agent_baseline_protocols_and_prepared_mature_cli_are_exact`，当前 Codex binary digest
  `7645c3ca…21e7` 不等于 frozen `9f6748b4…e481`；
- SQLite connection `ResourceWarning` 仍可见，但未改变测试 verdict；它不是本 Slice 新失败，也不能被写成已解决。

根因仍是已记录的历史 exact-runtime/environment drift，而不是当前 Application、Gateway、Source、Web 或 launcher regression。沙箱内
socket denial 属执行环境限制；系统级重跑已消除这些额外项。

## Decision and disposition

本 Slice 的 deterministic regression gate 采用既有 `PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD` 语义：保留 raw full suite
`pass=false`、4 FAIL + 1 ERROR 的 exact identity/reason，并要求其余 1103 项全部通过。不能把 raw suite 写成 PASS，不能修改 ITER-003
freeze 追认当前 binary，也不能通过 skip/改名/删除断言消除 hold。任何新增、缺失、结果类型或 marker 漂移都阻断 product freeze。

该处置只允许继续 Slice1 的 `EVALUATION_ONLY` exact product freeze/live preview；它不形成 V-WEB、Slice Result、hidden、Acceptance 或
Production Activation verdict。

## Verification

系统级命令为 `env PYTHONPATH=src:. python3 -m unittest discover -s tests -q`，执行 1108 项并精确得到上述 4 FAIL + 1 ERROR；聚焦
58/58、docs 389/389、compile/diff 均通过。正式 freeze 仍须在 clean commit 上重新绑定 candidate commit/tree 与该 gate，不能复用当前
dirty worktree 的测试身份。
