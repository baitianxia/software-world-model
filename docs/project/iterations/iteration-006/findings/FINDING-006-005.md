---
id: FINDING-006-005
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-006-SLICE-001, ITER-006-VERIFICATION]
code: [validation/structure_world_model_iteration_006/live_freeze.py, validation/structure_world_model_iteration_006/live_product_probe.py]
tests: []
iteration: ITER-006
classification: verification
disposition: freeze-only-contract-recognized-held-out-language
target: ITER-006-VERIFICATION
---

# FINDING-006-005：held-out 题面必须属于正式产品词汇

## Observation and evidence

首次 zero-provider freeze 的 inventory 题使用“全部方法”；正式解释器的冻结词汇为“哪些方法/所有方法/方法清单”等，因此产品
正确返回 Knowledge Gap，deterministic probe 拒绝 run-001。把题面改为正式支持的“有哪些方法”后，新随机 run 通过。

## Classification and disposition

这不是扩大产品自然语言能力的授权，而是 live suite 必须验证已实现契约、不能因 evaluator 自造同义词制造假失败的 verification
要求。run-001 永久保留；freeze 在任何 external result 前运行正式 deterministic product probe，只有全题通过才允许授权。
