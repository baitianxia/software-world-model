---
id: FINDING-005-003
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering]
depends_on: [ITER-005-SLICE-002, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING]
code: [src/software_world_model/interface/world_model_product.py]
tests: [tests/test_world_model_product.py]
iteration: ITER-005
classification: local-implementation
disposition: implement-generic-zero-and-ambiguous-candidate-limitations
target: src/software_world_model/interface/world_model_product.py
---

# FINDING-005-003：显式未知模块在 Provider 前失败而非返回 0-candidate Limitation

## Observation

为 SLICE-002 的新仓库冻结 held-out 问题时，静态执行路径表明：同名 artifact 的多个候选可进入
`ENTITY_CANDIDATE_RESOLUTION`，但问题显式引用一个 Catalog 中不存在的 artifact 时，封闭词法 Catalog 不产生 mention，
随后 `PRODUCT_MODEL_RESOLUTION_INPUT_EMPTY` 在 Provider 前失败。它无法满足 SLICE-002 已要求的受控 0/N candidate
Limitation。

## Evidence

- `ProductBundleCatalog.mentioned_modules` 过去只返回已存在于 Bundle 的 alias，无法表达零候选；
- `ProductModelDraftGenerator` 过去拒绝空 `candidate_refs`，尽管已接受 Strategy 明确定义零候选为 `NOT_FOUND`；
- Product Answer reviewer 过去一律拒绝 `WorldModelNeedOutcome.LIMITATION`，因此即使 Query Step 正确阻断也不能安全交付；
- 新增聚焦测试分别以显式反引号 artifact 验证 ZERO 与 AMBIGUOUS：两者各只有一次 qualified model proposal，Query
  Step 因 Entity Resolution 不唯一而阻断，Draft 只投影 `APPLICATION_LIMITATION`，不伪造 Query Result。

## Impact and classification

System Contract 和 Structure View 已拥有 `ENTITY_RESOLUTION_ZERO_CANDIDATES`、`ENTITY_RESOLUTION_AMBIGUOUS` 与
Application Limitation 语义；缺口位于 Product interpreter/planner/reviewer 的局部实现，不改变 Owner、端口或权威模型，分类为
`local-implementation`。它是通用 artifact token 处理，不增加项目名、模块名或拓扑分支。

## Decision and disposition

显式反引号 artifact token 进入与已存在 token 相同的 Entity Candidate 流程：

- 在 chosen exact Snapshot 上解析 0、1 或 N 个 Root；
- 0/N 使用真实 `ENTITY_CANDIDATES` resolution 阻断下游 Query Step，并投影 ZERO/AMBIGUOUS candidate count；
- 独立 reviewer 只在 Claim kind、Limitation codes 和 Assessment 精确一致时允许安全 Limitation；
- 1 candidate 保留既有唯一 Entity 行为；无显式 token 的覆盖外问题仍返回 Knowledge Gap。

代码与聚焦测试已处置该缺口。由于 `world_model_product.py` 属于 Answer package，继承自 ITER-003 的旧 Answer package 资格
按 SLICE-002 不变量失效；Prompt、Strategy 与 Provider subject 未改变，但候选 Answer package 必须重新密封，并在任何监听或
真实分派前完整重做 isolation preflight、Product Validation 和 V-009 对照。

## Verification after disposition

`tests.test_world_model_product` 与 `tests.test_world_model_http` 共 24 项通过；最终 exact candidate package digest、OS preflight
和外部 Product Result 由 V-007/V-009 闭合，不能由本聚焦测试替代。
