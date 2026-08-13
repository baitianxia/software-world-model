---
id: FINDING-006-003
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-006-SLICE-001, ITER-006-VERIFICATION]
code: [validation/structure_world_model_iteration_006/oracle.json]
tests: [tests/test_java_static_call_update.py]
iteration: ITER-006
classification: verification
disposition: freeze-git-object-lineage-and-execute-source-off-cli-in-new-process
target: ITER-006-VERIFICATION
---

# FINDING-006-003：初始集成 harness 未充分证明 exact freeze 与新进程 Source-off

## Observation

Workspace 集成测试最初每次创建真实 R1/R2/R3 Git commits，但沿用当前时间，因此 commit ID 不能跨运行复现；Oracle 也只列
图语义，没有固定 commit/tree identity。同一测试在 DB/repository unmount 后重新调用 CLI `main()`，能证明没有数据回退，
但仍与 Proposal 要求的“新进程 Source-off restart”存在证据差距。

## Evidence

- Git commit identity 包含 author/committer timestamp；未固定时间的同一 source tree 可生成不同 commit ID；
- harness 现在显式使用 SHA-1 object format、固定 author/committer date，并在每次构建时断言 Oracle 中的 commit/tree：
  R1 `db44ddb8…` / `4ee62aea…`，R2 `575ef5a1…` / `2bdd0dbf…`，unsupported R3 `3ba3459d…` /
  `502b1c84…`；同一集成测试连续两次 PASS；
- authority DB 与 repository 改名为不可达后，inventory、direct calls、path 与 ordered diff 均由
  `python -m software_world_model.interface.read_set_catalog_cli` 子进程只挂载 Catalog/Bundle 执行；
- 问答/View 前后的 CURRENT tuple、Workspace/Update Attempt 计数和 Source Operation 计数 exact 相等。

## Impact and classification

产品实现没有因此改变，但原证据不足以满足本轮 exact subject 和 source-off restart Gate，分类为 `verification`。它不授权真实
Provider 调用，也不把 subprocess 测试描述成 V-008 live Product Validation。

## Decision and disposition

把 deterministic Git object lineage、独立图/Evidence Oracle、新进程 Source-off CLI 以及 authority before/after receipt 纳入
V-002—V-007 的执行证据。该 harness 和 Verification Matrix 写回已经处置本 Finding。
