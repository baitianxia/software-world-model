---
id: ITER-007-RESULT-SLICE-001-PRODUCT-CANDIDATE-FREEZE-RUN-003-FAILURE
kind: iteration-result
status: failed-preserved
authority: execution-evidence
owners: [engineering, quality, security]
depends_on: [ITER-007-RESULT-SLICE-001-LIVE-RUN-002-FAILURE, FINDING-007-007]
code: [src/software_world_model/interface/world_model_runtime.py, validation/structure_world_model_iteration_007/slice1_freeze.py]
tests: [tests/test_world_model_evaluation_grant.py, tests/test_iteration_003_g3b.py, tests/test_model_egress_gateway.py, tests]
iteration: ITER-007
---

# ITER-007 SLICE-001 Product Candidate Freeze run-003 Failure

## Decision

`FINDING-007-007` 修复后的首次冻结尝试 **未形成 product freeze**。focused 与 candidate package 命令先返回成功；full regression
在当前工具 workspace sandbox 中运行 912 项时，6 个依赖本机 AF_UNIX listener 的测试因 `socket.bind()` 返回
`PermissionError: [Errno 1] Operation not permitted`，另一个计数断言随 listener 未启动而失败。freeze helper 因 full suite
return code 1 立即失败，未写 `report.json`、deterministic qualification 或 pending live grant。

这是一条执行环境失败证据，不是产品测试断言在允许 AF_UNIX 的执行面上失败。失败输出根目录
`var/iteration-007/slice-001/run-003-freeze/` 原地保留，不删除、不覆盖，也不得当作候选冻结使用。

## Reproduction and isolation

- 同一 sandbox 中，最小 `socket(AF_UNIX).bind()` probe 直接返回 `EPERM`；
- 失败集合为一个 ITER-003 listener handoff 测试及六个 Model Egress Gateway listener/client 测试；full suite 汇总为
  `Ran 912 tests`、1 failure、6 errors；
- 使用 run-003 producer snapshot，在允许本机 AF_UNIX 的执行面精确重跑这 7 项，结果 **7/7 PASS**；
- 修复新增的 Answer 三连接 audit regression 在 sandbox 内此前已经 PASS；
- 本次冻结没有外部 Provider request、没有模型调用、没有 Production Activation 或仓库 Git 写操作。

## Disposition

run-003 编号永久消费并保留失败。下一次冻结必须使用全新输出路径，并在允许本机 AF_UNIX listener 的执行面运行同一 unmodified
freeze helper；不得删除失败测试或降低 full regression Gate。成功候选仍须重新执行 focused、candidate package、full、docs 和
unauthorized-prelisten 全部 Gate。
