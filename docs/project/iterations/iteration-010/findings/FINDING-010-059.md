---
id: FINDING-010-059
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-057, FINDING-010-058]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_model_source.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_cognition.py, tests/test_engineering_qa_source.py, tests/test_engineering_qa_live.py, tests/test_engineering_qa_preview_cli.py, tests/test_engineering_qa_alpha_cli.py, tests/test_engineering_qa_browser.py, tests]
iteration: ITER-010
classification: verification
scope: systemic
disposition: preserve-exact-historical-full-suite-hold-after-direct-locator-and-finish-shape
target: ITER-010-VERIFICATION
---

# FINDING-010-059：direct locator 与互斥 FINISH shape 无新增完整回归失败

## Observation and evidence

`FINDING-010-057/058` 的实现与 System/docs 回写完成后：

- 全部 Engineering QA 组合测试 101/101 PASS；其中新增回归分别证明 mandatory path 可直接形成 Broker-authorized READ，且绑定另一个
  Investigation attempt 的 locator 会以 `REQUIRED_PATH_LOCATOR_BINDING_MISMATCH` 失败关闭；
- current docs generate/check 453/453 PASS，`compileall` 与 `git diff --check` PASS；current System Contract
  fileset 改变后，ITER-007 的可复现 fileset 摘要以同一机械算法更新，单项 oracle 1/1 PASS，不改变其历史项目裁决；
- 默认 workspace sandbox 的 full discovery 共 1167 项，raw 为 5 FAIL + 7 ERROR。精确 test identity 表明其中 1 FAIL + 6 ERROR 全部来自
  AF_UNIX listener/connect 被 sandbox 拒绝；
- 允许本机 AF_UNIX 的同一 full 命令仍为 1167 项，其中 1162 PASS，raw 唯一 4 FAIL + 1 ERROR：3 FAIL + 1 ERROR 为冻结 V-009
  Adapter Conformance implementation drift，另 1 FAIL 为本机 Codex binary digest 与历史 prepared digest 不同。identity、结果类型与
  marker 与此前 historical hold 完全相同，没有 ITER-010 新失败。

## Decision and disposition

raw full suite 继续记录为 FAIL，不能写成全通过；Slice1 只以
`PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD` 形成新的 clean candidate。该结果闭合本次 direct locator、FINISH schema 与
Question Understanding modality-minimality 的确定性 Gate，不证明 DeepSeek 已按新 shape 交付三题，也不证明持续体验、Acceptance 或
Production Activation；fresh Conformance、新 candidate live、raw answer/reviewer 独立复核与真正超过 65,536 bytes 的 Provider 前拒绝仍是
blocking evidence。
