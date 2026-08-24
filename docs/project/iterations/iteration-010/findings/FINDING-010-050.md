---
id: FINDING-010-050
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-049]
code: []
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_model_source.py, tests/test_engineering_question_strategy.py]
iteration: ITER-010
classification: verification
scope: systemic
disposition: preserve-exact-historical-full-suite-hold-after-required-path-budget-fix
target: ITER-010-VERIFICATION
---

# FINDING-010-050：required-path budget 修复无新增完整回归失败

## Observation and evidence

`FINDING-010-049` 的实现与 System/docs 回写完成后：

- 全部 Engineering QA 组合测试 97/97 PASS，覆盖 4-path schema/Domain 上限、unread-required locator priority、remaining-fuse 投影、
  premature FINISH path GAP，以及 policy-enforced exact `OUTCOME_UNKNOWN` propagation；
- current docs generate/check 444/444 PASS，System fileset digest 与 exact answer-protocol budget digest 已重新密封；`compileall` 与
  `git diff --check` PASS；
- 默认 workspace sandbox 的 full discovery 共 1163 项，raw 为 5 FAIL + 7 ERROR。精确 test identity 表明其中 1 FAIL + 6 ERROR 全部来自
  AF_UNIX listener/connect 被 sandbox 拒绝；
- 允许本机 AF_UNIX 的同一 full 命令仍为 1163 项，其中 1158 PASS，raw 唯一 4 FAIL + 1 ERROR：3 FAIL + 1 ERROR 为冻结 V-009
  Adapter Conformance implementation drift，另 1 FAIL 为本机 Codex binary digest 与历史 prepared digest 不同。identity、结果类型与 marker
  与此前 historical hold 完全相同，没有 ITER-010 新失败。

## Decision and disposition

raw full suite 继续记录为 FAIL，不能写成全通过；Slice1 只以
`PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD` 继续形成新的 clean candidate。该结果证明本次 required-path/fuse 与 outcome identity 修复没有
引入新确定性回归，不证明 DeepSeek 三题答案、持续体验、Acceptance 或 Production Activation；fresh Conformance 和新 candidate live 仍是
blocking evidence。
