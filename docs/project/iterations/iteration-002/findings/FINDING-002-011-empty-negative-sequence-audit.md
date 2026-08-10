---
id: FINDING-002-011
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-002-SLICE-001, FINDING-002-007, FINDING-002-009]
code: [src/software_world_model/ai_infrastructure/agentic_knowledge_strategy.py]
tests: [tests/test_agentic_knowledge_strategy.py]
iteration: ITER-002
classification: iteration-design
disposition: required-explicit-sequence-classification-and-per-caller-focus
target: ITER-002-SLICE-001
---

# FINDING-002-011：空的顺序负向结论不能证明逐引用检查已执行

## Observation

Strategy `2.0.192` 的产品路径完成并封存，但 Codex 对照冻结源码独立复核时发现，答案先解释 `RunTemplate.findPolicy` 的内部逻辑，随后才展示调用它且同时包含返回后判断的 `ElementProcessor.visit` 事实。三次完整集合顺序分析和两轮八引用聚焦分析都没有把该调用方事实识别为必须拆分的调用返回跨度。

## Evidence / reproduction

`var/product-generic-v192-suite205-quality-first/document-render-two-stage-pipeline--world_assisted.json` 共完成 53 次模型调用并通过内部审核。最终答案的第六条解释 `RunTemplate.findPolicy`，第七条才陈述 `ElementProcessor.visit` 调用 `findPolicy` 后判断策略类型并继续委托；这无法表达真实的“调用方进入、被调内部、返回调用方判断”顺序。运行数据库中的四次聚焦顺序输出均返回空 `call_return_spans` 和空 `atomic_references`。当时实现把 `atomic_references` 视为兼容字段并自动把未报告引用当作原子事实，因此空输出无法区分“已逐项检查后没有跨度”和“没有检查到该引用”。

## Impact

形式正确且已封存的答案仍可能把调用方事实放在被调内部之后。仅增加批次但不要求逐引用留下正向或负向分类证据，不能满足实际调用顺序的质量要求。

## Classification rationale

变化强化当前切片的通用顺序审核与失败关闭语义，不改变正式知识 Owner 或外部产品接口，因此归类为 iteration-design。

## Decision and disposition

完整顺序审核必须把每条引用恰好分类一次：要么作为经精确文本验证的组合调用方，要么在对应 Need 的 `atomic_references` 中显式列出；遗漏、重复、同时属于两类或超出审核范围均触发契约修复。大型引用集继续保留完整集合审核，但聚焦批次由每批最多八个调用方收窄为每次只检查一个可能调用方，并独立执行两轮；每轮仍看到完整 Need 引用集以匹配任意被调内部事实。聚焦输出必须报告有效跨度，或显式把该唯一调用方判为原子，不能返回无法审计的空结论。

## Verification after disposition

新增测试证明遗漏引用、重复原子分类和聚焦范围外分类均失败关闭；另一回归让三次完整审核都漏掉组合事实，再由两次单调用方聚焦审核一致发现并触发事实拆分。相关 166 项测试通过。Strategy 升级为 `2.0.193`，`2.0.192` 的能力资格和封存产品结果不能继承。
