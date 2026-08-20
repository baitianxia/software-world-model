---
id: FINDING-008-028
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality, operations]
depends_on: [ITER-008-SLICE-001, FINDING-008-020, FINDING-008-027, SYS-OPS-LOCAL-BROWSER]
code: [src/software_world_model/interface/world_model_runtime.py, validation/structure_world_model_iteration_008/slice1_freeze.py, validation/structure_world_model_iteration_008/slice1_live_authorize.py]
tests: [tests/test_iteration_008_slice1_freeze.py, tests/test_iteration_008_slice1_live_authorize.py, tests/test_world_model_evaluation_grant.py]
iteration: ITER-008
classification: system-contract
disposition: versioned-exact-preserved-historical-hold-gate
target: SYS-OPS-LOCAL-BROWSER
---

# FINDING-008-028：正式产品 freeze 必须区分 raw regression 结果与精确保留的历史环境 hold

## Observation

run-019 已关闭当前 Strategy 的 Conformance/Capability 阻断后，正式 SLICE-001 freeze 的现有实现仍调用完整 `unittest` 并只接受 exit
code 0，随后把 `full_regression_pass` 固定写成 `true`。`FINDING-008-020` 同时要求 ITER-003 的五项 exact-runtime 测试保持原样、在
当前桌面 Codex binary 漂移时继续 4 failure + 1 error，并禁止把 1013/1018 写成 full-suite PASS。两个条件都正确，却使产品 freeze
形成永久死锁：修复历史测试会破坏已接受证据，不修复则永远不能产生确定性候选资格。

这不是 ITER-008 产品 regression，也不是取消回归门禁的理由。缺失的是一个版本化、可机械复核的 gate outcome，用于表达“raw suite
仍 FAIL，但失败集合精确等于已处置的外部历史 hold，所有其他当前测试 PASS”。原 `@1` qualification 只有单一 full-PASS 语义，不能
在不说谎的情况下承载该状态。

## Evidence and root cause

允许 AF_UNIX 的执行面已证明当前完整 suite 中只有以下既有结果：

- `ERROR`：`test_iteration_003_v009.Iteration003V009Tests.test_input_freeze_and_evaluator_are_mechanically_closed`；
- `FAIL`：同模块的 `test_closed_evaluation_rejects_semantically_tampered_conformance_binding`、
  `test_closed_live_harness_seals_all_seven_cases_and_valid_qualification` 与
  `test_conformance_unknown_seals_pre_dispatch_intent_and_stays_blocking`；
- `FAIL`：`test_iteration_003_validation_assets.Iteration003FrozenAssetTests.test_agent_baseline_protocols_and_prepared_mature_cli_are_exact`。

前三类输出绑定 `V-009 Adapter Conformance implementation drifted`，最后一项绑定 frozen prepared digest
`9f6748b4ab10ffc92c28b9ccedae89e61a302bbc011df7d276ee38f55906e481`；未知状态 Case 仍精确表现为 code 2 对 frozen code 3 的断言。
直接重放 9 项历史测试再次得到 4 PASS / 4 FAIL / 1 ERROR。产品 freeze 的旧 `_test_result()` 在 return code 1 时直接抛错，无法表达或
复核这个已知集合；runtime 则只接受 `SWM-WORLD-MODEL-DETERMINISTIC-QUALIFICATION@1` 和
`full_regression_pass: true`。根因因此是 verification contract 的表达缺口，而不是历史测试或产品实现错误。

## Decision and disposition

新增 `SWM-WORLD-MODEL-DETERMINISTIC-QUALIFICATION@2`，但只允许 ITER-008 bounded Java source-semantics Gateway route 使用。freeze
以 verbose discovery 运行完整 suite，并要求五个历史测试各出现一次。raw exit 0 形成普通 `PASS`；raw exit 1 只有同时满足 exact
4 failure + 1 error、上述五个 ID/结果类型、每项原因 marker、无额外 header、其余测试全通过时，才形成
`PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD`。输出只密封命令、raw/gate boolean、总数/通过数、failure/error count、完整 held identity、
Finding ref 与 stdout/stderr digest，不持久化完整日志。

runtime 对 `@1` 保持原要求不变；对 `@2` 重验 bounded route、exact command、全部计数、held list、reason-validated freeze 结果结构及
top-level/raw 一致性。live authorization helper 同步升级 freeze report identity，并在授权文件生成前拒绝任何不一致 gate status。
任何新增、缺失、改名、skip、原因漂移或不同 return code 都失败关闭。历史 ITER-003 freeze、Manifest、测试和 expected digest 均未修改。

System Owner 处置写入 `SYS-OPS-LOCAL-BROWSER`。该 gate 只解除当前 `EVALUATION_ONLY` public Web freeze 的机械死锁，不把 raw suite
写成 PASS，也不能授权 hidden canary、Slice Acceptance、SLICE-002、Direct/Production Activation。定向资格/runtime/authorize 测试
22/22 PASS。System 写回后的 ITER-008/ITER-007 fileset digest 分别为
`sha256:80b5393bd767cbc7be60f67ca0bbefbd308e1c7e84b8a522aab8bb016c26b311` /
`sha256:3f25570e48caa265feb3a3d95cf0441628f36890744c9902a35b1ecac3844819`。最终完整执行面为 1021/1026；raw exit 1，唯一
4 FAIL + 1 ERROR 的 ID、类型和原因精确匹配 preserved hold，结构化 gate PASS，stdout/stderr digest 为
`sha256:f9b8e96414287cbcdf698497bc5342bfb2bc8a37ba21def4b0db8e17559573e0` /
`sha256:76a79e6dd2302d369ee4b3c9e7b0d717c93da989cb79b6ac28adc59f37615e27`。正式产品 freeze 仍须从 clean exact candidate
单独生成。
