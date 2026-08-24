---
id: FINDING-010-052
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-051]
code: []
tests: [tests/test_engineering_question_strategy.py]
iteration: ITER-010
classification: verification
scope: systemic
disposition: preserve-exact-historical-full-suite-hold-after-answer-role-order-normalization
target: ITER-010-VERIFICATION
---

# FINDING-010-052：Answer role-order 归一化无新增完整回归失败

## Observation and evidence

`FINDING-010-051` 的实现与 System/docs 回写完成后：

- 全部 Engineering QA 组合测试 98/98 PASS，新增回归证明乱序 follow-up claims 按受控 role 稳定排序，同 role 原顺序、Claim 文本和
  identity links 保持不变；既有 Domain 测试继续拒绝直接构造的乱序 Proposal 与其他非法 Answer；
- current docs generate/check 446/446 PASS，System fileset digest 与 exact answer-protocol budget digest 已重新密封；`compileall` 与
  `git diff --check` PASS；
- 默认 workspace sandbox 的 full discovery 共 1164 项，raw 为 5 FAIL + 7 ERROR。精确 test identity 表明其中 1 FAIL + 6 ERROR 全部来自
  AF_UNIX listener/connect 被 sandbox 拒绝；
- 允许本机 AF_UNIX 的同一 full 命令仍为 1164 项，其中 1159 PASS，raw 唯一 4 FAIL + 1 ERROR：3 FAIL + 1 ERROR 为冻结 V-009
  Adapter Conformance implementation drift，另 1 FAIL 为本机 Codex binary digest 与历史 prepared digest 不同。identity、结果类型与
  marker 与此前 historical hold 完全相同，没有 ITER-010 新失败。

## Decision and disposition

raw full suite 继续记录为 FAIL，不能写成全通过；Slice1 只以
`PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD` 继续形成新的 clean candidate。该结果证明本次稳定 role-order canonicalization 没有引入
新确定性回归，不证明 DeepSeek 三题答案、持续体验、Acceptance 或 Production Activation；fresh Conformance 和新 candidate live 仍是
blocking evidence。
