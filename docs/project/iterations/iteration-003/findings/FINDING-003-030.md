---
id: FINDING-003-030
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-003-SLICE-001, ITER-003-VERIFICATION, FINDING-003-028]
code: [validation/structure_world_model_iteration_003/g3b/evaluate_results.py]
tests: [tests/test_iteration_003_g3b.py]
iteration: ITER-003
classification: local-implementation
disposition: count-all-preserved-non-success-baseline-terminals
target: validation/structure_world_model_iteration_003/g3b/evaluate_results.py
---

# FINDING-003-030：Direct population 报告没有计入保留的非成功终态

## Observation

`product-evaluation-v2.json` 已正确保留 55 个 Direct terminal，performance 也正确报告 40 个
Provider/non-success terminal；但顶层 `direct_population.failure_count` 却为 0。

## Evidence

- V-009 联合 seal 固定 Direct 为 15 `SUCCESS` 与 40 `FAILURE_KEPT_NO_RETRY`；
- evaluator 的 Gate 判定使用 `status != "SUCCESS"` 计数，因而正确得到 40；
- Result 渲染却使用 `statuses.count("FAILURE")`，与真实的保留终态名不相等；
- 该错误只影响报告字段，没有改变 58/60 质量裁决、性能总体、任一 product terminal 或模型调用。

## Impact and classification

不一致字段会让读者误以为 40 个 Direct 失败被删除，与 `FINDING-003-021` 的“全部失败保留”规则冲突。
修复不改评分或对外契约，分类为 `local-implementation`。

## Decision and disposition

对 Direct 和 Mature population 统一使用“所有不等于 exact `SUCCESS` 的已保留 terminal”计数，
并在 baseline population Gate 与 Result 渲染中共用同一值。不把 `FAILURE_KEPT_NO_RETRY`、429、outcome
unknown 或 structured-output failure 等非成功终态重命名为一个虚构的 `FAILURE`。

为保持 product/evaluator lineage 分离，修复从纯 evaluator checkpoint `4d75aaf…` 的 detached
worktree 提交为 `bff20651c7b2b9b84f2bd9c845091ccc631ca096`，然后以 merge parent 纳入 main；该 commit 不含
任何产品代码。

## Verification after disposition

G3b 模块 14/14 PASS。在 `bff2065…` 上密封的 `product-evaluation-v3.json` 正确报告
Direct 55 terminal = 15 SUCCESS + 40 failure，Mature 55 = 55 + 0，同时保持产品裁决 58/60 FAIL。
移植回 main 后的 G3b/V-009 聚焦回归 46/46、全量回归 750/750 PASS。没有 Provider 调用，
Production Activation 为 `NOT_EXECUTED`。
