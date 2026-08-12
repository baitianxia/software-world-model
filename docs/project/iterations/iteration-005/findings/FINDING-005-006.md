---
id: FINDING-005-006
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-005-SLICE-002, FINDING-005-005]
code: [src/software_world_model/interface/world_model_runtime.py, validation/structure_world_model_iteration_005/slice2_freeze.py]
tests: [tests/test_world_model_evaluation_grant.py, tests/test_world_model_product.py]
iteration: ITER-005
classification: local-implementation
disposition: verify-schema-bound-candidate-documents-and-exact-staged-answer
target: src/software_world_model/interface/world_model_runtime.py
---

# FINDING-005-006：未授权短路掩盖候选资格摘要不兼容

## Observation

为 `SWM-WORLD-MODEL-EVALUATION-GRANT@2` 增加完整正向解析测试时，候选 deterministic qualification 与 held-out suite
使用各自 schema 绑定的 `digest([schema, core])`，但 runtime 的通用 document reference verifier 使用
`digest(core)`。真实授权 grant 会在任何 Provider 操作前因摘要算法不一致而拒绝。原有测试只有未授权 grant，先在
disclosure gate 短路，因此没有执行 subject/qualification 验证，也没有暴露该问题。

同一审计还确认：只在当前 `src/` 上运行 `world_model_product` 测试，不能证明最终 staged Answer package 使用 inherited
dependency bytes 时也成立。

## Evidence

- 新增的完整 synthetic authorized grant 只调用 `_load_evaluation_grant`、不创建 executor、不打开 socket、不分派模型；修复前
  在 `_verified_document` 稳定失败；
- qualification、suite、grant、disclosure 和 independent evaluator 各自有显式 schema/digest 约定，只有前两者经过错误的
  generic verifier；
- 篡改 qualification raw bytes 的测试继续在 digest gate 失败；
- freeze harness 现在用 candidate stage 的 `packages/answer` 作为首个 `PYTHONPATH` 重跑产品测试，并在测试后重新计算整个
  protected stage manifest，禁止测试过程改变候选 bytes。

## Impact and classification

System 已要求 exact provenance、pre-listen verification 和 fail-closed；问题没有改变调用方或 System 语义，是 grant loader 与
deterministic qualification harness 的局部实现缺口，分类为 `local-implementation`。synthetic test 中的
`AUTHORIZED` 只属于不执行网络的单元 fixture，不是用户对真实候选问题的披露授权。

## Decision and disposition

`_verified_document` 对 qualification/suite 按 document 自带的非空 schema 重算 `digest([schema, core])`，同时继续验证 canonical
JSON、raw SHA-256 和 grant 中的 exact document digest。新增完整正向 grant 与 raw tamper 回归测试；真实 freeze 额外要求
exact staged Answer package tests PASS，并把结果写入 deterministic qualification，runtime 在授权启动时机械要求该字段。

该修复与测试已处置本 Finding；外部 Product Validation、OS preflight 和人工浏览器验证仍等待单独披露授权，不能由正向
parser 单元测试替代。
