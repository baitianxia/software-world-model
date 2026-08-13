---
id: FINDING-006-009
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-006-SLICE-001, ITER-006-VERIFICATION]
code: [validation/structure_world_model_iteration_006/live_evaluator.py]
tests: [tests/test_iteration_006_live_evaluator.py]
iteration: ITER-006
classification: local-implementation
disposition: preserve-failed-terminal-and-return-fail-report
target: validation/structure_world_model_iteration_006/live_evaluator.py
---

# FINDING-006-009：独立 evaluator 未处理失败 terminal 的空 completeness

## Observation and evidence

`run-003` 的 World Model population 原样保留两个失败 terminal 后，冻结 evaluator
`sha256:2f186c9d…` 已先登记 `World Model terminal failed` blocker，但随后仍对该 terminal 的
`completeness_ppm=null` 执行 `int()`，以 `TypeError` 退出，未写出 comparison report。失败 terminal 是 suite 明确允许且必须
保留的输入，因此 evaluator 崩溃属于本地实现缺陷，不改变两题已失败的事实。

## Classification and disposition

Evaluator 现在只在 World Model terminal eligible 且 completeness 为非布尔整数时比较较强 baseline；失败 terminal 直接保留
既有 task/call/terminal blockers，不插值、不产生虚假 completeness regression。新增回归直接覆盖 World Model failure + 两个
eligible baseline 的组合，确认返回 `status=FAIL` 而不抛异常。

最初只修复 null terminal 后的 evaluator 文件 digest 为
`sha256:a014efee28c52b9f17cd1c4a425486453ec8a5a33ec9cd22c8a0b424125e4833`；后续 Java qualification binding 又使当前候选变为
`sha256:bb972939badfbebf8f0f3365e86a0ffc841bf70b38466f247f3aad383bbb7e03`。二者都不能追溯替换 run-003 已冻结的 evaluator；
下一 product run 必须在新 qualification 后以当时 exact digest 重新冻结 suite。该 Finding 不改变 System 语义，故只处置到代码
与测试。
