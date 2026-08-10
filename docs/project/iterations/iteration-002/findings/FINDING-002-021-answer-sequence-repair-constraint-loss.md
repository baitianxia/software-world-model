---
id: FINDING-002-021
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-002-SLICE-001, FINDING-002-006, FINDING-002-009, FINDING-002-013, FINDING-002-015]
code: [src/software_world_model/ai_infrastructure/agentic_knowledge_strategy.py]
tests: [tests/test_agentic_knowledge_strategy.py]
iteration: ITER-002
classification: iteration-design
disposition: persist-answer-repair-and-require-independent-sequence-confirmation
target: ITER-002-SLICE-001
---

# FINDING-002-021：答案顺序修复约束在内部审核中丢失

## Observation

Strategy `2.0.202` 的产品运行完成 118 次模型调用且全部有完整 Provider 结果，已发布知识快照并通过推理、充分性、答案最小性与完整性阶段。最终答案顺序审核发现选中的正式记录包含无法单点排序的调用返回事实，答案选择随后尝试改用其他正式记录；但同一轮的最小性和完整性审核没有收到该修复约束，又把问题记录选回。三轮外层答案选择因此均以 `answer sequence contains an unsplittable call-return fact` 结束。

## Evidence / reproduction

证据位于 `var/product-generic-v202-suite205-strict-shape-repair/`。三次 `ANSWER_DRAFT_SELECTION` 的修复状态只包含抽象 `last_error` 与允许引用全集，没有包含异常详情中的 `unsplittable_reference_ids`。第二次选择已经移除若干组合记录，但其后两个审核从初始状态重建选择，未继承本轮修复边界。运行的首个答案顺序报告还把 `DefaultRender.render` 的 `RenderDataComputeFactory.newCompute` 调用错误配到 `DelegatePolicy.invoke` 内部事实；平台因 exact 文本片段存在而立即视为正向缺陷，没有等待独立报告确认。

## Impact

问题同时造成两种通用风险：真实缺陷的修复无法跨同轮审核保持，导致可收敛答案被较低固定次数截断；单个模型报告的被调身份判断错误又可能无独立证据地否决正确答案。两者都不依赖具体工程、语言或符号。

## Classification rationale

变化只调整当前切片的答案选择与顺序审计编排，不改变正式记录、对外接口或 System 不变量，归类为 iteration-design。

## Decision and disposition

答案外层修复始终携带完整 `last_error_details`。若其中列出 `unsplittable_reference_ids`，答案选择必须排除这些编号，且同一轮后续最小性与完整性审核继承同一修复状态，不得重新加入。答案外层修复熔断由三次提高到五次。

答案顺序阶段不再用单个全量报告直接形成否决；主分析、独立排序审核和逐引用聚焦审核的正向跨度按同一身份聚合，至少两个独立报告一致才确认。所有包含两个及以上正式记录的答案都逐引用审核两次，不因集合较小或调用成本跳过。契约、exact 片段、Need 范围和最终答案完整性规则均不放宽。

## Verification after disposition

新增测试验证单个正向报告不会独自形成否决，以及经两个独立报告确认后，问题引用编号会进入下一轮最小性审核并持续禁止恢复。相关 187 项测试与完整 433 项测试通过。Strategy 升级为 `2.0.203`；`2.0.202` 的能力资格和失败产品运行不能授权新实现。
