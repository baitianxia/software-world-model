---
id: FINDING-002-009
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-002-SLICE-001, FINDING-002-007]
code: [src/software_world_model/ai_infrastructure/agentic_knowledge_strategy.py]
tests: [tests/test_agentic_knowledge_strategy.py]
iteration: ITER-002
classification: iteration-design
disposition: added-batched-independent-call-return-audits
target: ITER-002-SLICE-001
---

# FINDING-002-009：大型顺序引用集会漏掉真实调用返回边界

## Observation

Strategy `2.0.190` 的事实阶段同时向顺序模型提供 19 条引用并要求排序与调用返回检查。一次主审和两次独立复审都未识别 `applyDocxPolicy` 事实把 `DelegatePolicy.invoke` 与调用后的文档刷新合并；最终答案阶段重复识别该真实边界，因正式事实已发布而无法修复。

## Evidence / reproduction

`var/product-generic-v190-suite205-quality-first/` 中事实引用 `c15` 同时陈述策略调用及之后的 `current != template.getXWPFDocument()` 处理，`c7` 单独解释 `DelegatePolicy.invoke` 内部行为。事实顺序输出把大量预算用于排序边并漏掉该跨度；答案引用 `r12` 与 `r13` 对应同一事实和被调内部行为，多次答案顺序检查重新发现该跨度，最终以 `answer draft exhausted bounded contract retries` 失败。

## Impact

当一个问题包含较多阶段、分支和异常事实时，单个完整输出同时承担排序与穷举跨度检查，可能因注意力和输出容量漏掉后部引用中的真实边界。答案阶段只能拒绝，不能修复已经发布的正式事实。

## Classification rationale

变化增强本轮通用顺序审核策略，不改变正式知识或外部接口 Owner，因此归类为 iteration-design。

## Decision and disposition

保留现有完整集合主审和两次独立复审；当一个 Need 的引用数超过 12 时，再按最多 8 条可能调用方分批，每批执行两次互不可见的聚焦审核。聚焦审核仍接收完整引用集以匹配被调内部事实，但只能把本批引用标为组合调用方，不生成排序边。所有结果继续进入既有的一致性确认、争议裁决和事实拆分流程。触发条件只依赖引用数量，不包含工程、语言、框架或符号定制。

## Verification after disposition

单元测试固定 19 条引用被分为 8、8、3 三批，12 条及以下不增加聚焦调用。Strategy 升级为 `2.0.191`；旧资格和产品结果均不可继承，必须重新完成六角色资格与 Suite `2.0.5` 产品运行。
