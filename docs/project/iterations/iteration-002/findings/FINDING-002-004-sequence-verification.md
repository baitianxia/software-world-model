---
id: FINDING-002-004
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-002-VERIFICATION]
code: [src/software_world_model/ai_infrastructure/agentic_knowledge_strategy.py]
tests: [tests/test_agentic_knowledge_strategy.py, tests/test_product_holdout_world_answer.py]
iteration: ITER-002
classification: verification
disposition: added-complex-sequence-product-gate
target: ITER-002-VERIFICATION
---

# FINDING-002-004：复杂调用链需要独立顺序验收

## Observation

单个事实可以在局部文本上成立，但若把“调用帮助方法”和“使用返回值”合并，插入帮助方法内部行为后会形成不可能同时满足的全局顺序。一般事实审核不会稳定发现这一问题。

## Evidence / reproduction

冻结的 `document-render-two-stage-pipeline` 任务包含调用方、被调渲染器和返回后处理。早期真实模型运行曾把调用与返回后行为合并，或把普通委托关系误判为返回后动作。

## Impact

该缺陷会生成局部正确但整体错误的用户答案，并且可能出现在任何语言或框架的调用链中。

## Classification rationale

平台现有不变量已禁止语义扩张；新事实是长期验收需要显式覆盖调用与返回顺序，因此归类为 verification。

## Decision and disposition

增加语言中立的顺序分析协议和分裂修复，并在 V-006 冻结复杂调用链产品任务。Oracle 由 exact 源码和 Codex 独立判断，不由同一 Provider 自评优劣。

## Verification after disposition

单元测试覆盖严格片段、时序连接词、重复关系和修复；真实产品运行必须在预算内完成且由 Codex 复核最终答案顺序。
