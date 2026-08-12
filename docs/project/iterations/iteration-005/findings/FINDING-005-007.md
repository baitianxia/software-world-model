---
id: FINDING-005-007
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [quality, engineering]
depends_on: [ITER-005-SLICE-002, ITER-005-VERIFICATION]
code: [validation/structure_world_model_iteration_005/slice2_freeze.py, validation/structure_world_model_iteration_005/slice2_product_probe.py]
tests: [tests/test_world_model_product.py]
iteration: ITER-005
classification: verification
disposition: corrected-and-deterministically-probed-in-run-003
target: ITER-005-VERIFICATION
---

# FINDING-005-007：负向路径题把同名短名误当成唯一 Entity

## Observation

`run-002` 的 held-out suite 把 ``shared-<random>`` 到 ``worker-<random>`` 作为 supported negative path，但随机仓库故意包含
alpha/beta 两个同名 `shared` artifact。按 World Model Contract，路径操作前的 0/N candidate 必须形成 Entity Resolution
Limitation，不能猜选一个 Root，因此该题的 expected outcome 与输入不一致。

## Evidence

- `run-002` 在任何外部结果前密封，记录两个同名完整 GA，但负向路径问题只使用 artifactId；
- 新的 deterministic product probe 用 exact Catalog/Bundle 和 formal proposal stub 执行密封问题时，在 Provider 前稳定返回
  `PRODUCT_PATH_ENDPOINTS_UNRESOLVED`；
- 同一产品已有 ZERO/AMBIGUOUS 回归测试，证明失败来自 suite 选择器设计，不是应放宽产品解析。

## Impact and classification

产品 fail-closed 行为正确；错误位于 held-out verification input。若不修正，外部分派会浪费一次调用且把正确 Limitation 误记为
产品重大错误。该事实改变本轮 V-009 的输入冻结质量门但不改变 System Contract，分类为 `verification`。

## Decision and disposition

- 负向路径题改用唯一的 alpha `shared` 完整 GA 与唯一 `worker` 完整 GA；
- 同名 direct-dependency 题继续保留短名歧义，但 required tokens 同时要求 alpha/beta 两个完整 GA，验证产品没有按名字拼接；
- freeze 在生成任何可授权 grant 前，必须对全部 9 条 exact 问题运行 deterministic product probe，核对正式 assessment outcome、
  required/forbidden tokens、marker、一次 formal proposal 和零外部调用；
- `run-001`（CLI 诊断失败）和 `run-002`（suite 设计错误）均保留但不得成为授权输入。

`run-003` 使用新的随机 seed `9920c2bc8d04474fe253b0ee6c6b5421` 重新生成仓库与 9 条 exact 问题；修正后的
WM-005-004 使用完整 alpha GA。全部问题通过 deterministic product probe，probe digest 为
`sha256:506607f0a6e9dd8bd0b964cecf7cdafa979c977e3ffe32ca8cecc6d6dde1a036`，held-out suite digest 为
`sha256:d1fa4623e171652444fcdb2502b889bdeb37e3372cda8a34bcd17a0642c1f769`。因此本 Finding 已 disposition。

`run-003` 只闭合本 Finding 的题目选择器错误；后续发现的 baseline protocol/调用可观测性问题由
`FINDING-005-008` 单独处理，且会产生新的 candidate freeze。`run-001`、`run-002`、`run-003` 均保留，不被覆盖。
