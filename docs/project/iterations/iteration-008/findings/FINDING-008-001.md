---
id: FINDING-008-001
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai-infrastructure, quality]
depends_on: [ITER-008-SLICE-001, SYS-CONTRACT-AI-CAPABILITY-EVALUATION, SYS-CONTRACT-AI-MODEL-GATEWAY]
code: [src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, src/software_world_model/ai_infrastructure/java_source_semantics_model_egress_qualification.py, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_qualification.py]
tests: [tests/test_iteration_007_capability_qualification.py, tests/test_iteration_008_capability_qualification.py, tests/test_world_model_answer_strategy.py]
iteration: ITER-008
classification: local-implementation
disposition: keep-fixed-and-bounded-qualification-identities-disjoint
target: src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_qualification.py
---

# FINDING-008-001：活动 Strategy alias 会使历史资格被错误解释为新协议

## Observation

将 Java Source Semantics 的活动 Proposal Contract 从固定 Plan `1.2.2` 升级为有界调查 `1.3.0` 后，ITER-007 的资格装载器、
12 Case Definition 和历史测试若继续引用活动 alias，会在不改变历史 Result bytes 的情况下，尝试按新 Prompt、Schema、operation
set 与调用协议校验旧证明。

## Evidence

- 首轮兼容性测试中，ITER-007 的 exact 12 Case Result 因 `1.3.0` output-contract digest 与历史文件不一致而失败；
- `1.2.2` 只有 `IMPLEMENTATION_QUERY_PLANNING → Draft → Review`，而 `1.3.0` 是
  `IMPLEMENTATION_INVESTIGATION(2—4) → Draft → Review`，两者 capability、Schema、Prompt、operation set 和调用计数均不同；
- 修复后，历史 evaluation/manifest/freeze/CLI/Gateway loader 全部显式绑定
  `JAVA_SOURCE_SEMANTICS_FIXED_WORLD_MODEL_PROPOSAL_CONTRACT`；新 loader 只接受 `1.3.0` 的 18 Case、逐回合
  input/result/trace digest 和新 egress policy；
- ITER-007 24 项相关资格/Strategy 回归与 ITER-008 新资格装载测试分别通过。

## Impact and classification

System Contract 已明确 Strategy 或调用协议变化不得继承旧资格；发现的是 Python 活动 alias 在历史实现资产中的局部使用错误，未改变
Owner、外部接口或冻结规范，因此分类为 `local-implementation`。

## Decision and disposition

保留两个不可互换的 contract identity。历史 ITER-007 模块只使用 fixed `1.2.2`；产品活动链只使用 bounded `1.3.0`。新
Gateway policy 必须取得自己的 closed 18 Case Result，旧 qualification、policy digest、route 或三调用次序不能 fallback。

主处置进入新 bounded qualification loader 与对应测试；无需改写 System 文档，因为现有不继承规则已经完整拥有该语义。

## Verification after disposition

- ITER-007 fixed contract 的 12 Case Definition、output digest、Gateway policy 和 Result loader 保持可重放；
- ITER-008 loader 拒绝 `strategy_version=1.2.2`、缺少逐回合 trace evidence 或 policy drift；
- active/fixed output-contract digest 明确不同。
