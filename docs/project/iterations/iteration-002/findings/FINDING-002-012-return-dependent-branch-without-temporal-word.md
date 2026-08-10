---
id: FINDING-002-012
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-002-SLICE-001, FINDING-002-011]
code: [src/software_world_model/ai_infrastructure/agentic_knowledge_strategy.py]
tests: [tests/test_agentic_knowledge_strategy.py]
iteration: ITER-002
classification: iteration-design
disposition: recognized-return-and-state-dependent-post-call-operations
target: ITER-002-SLICE-001
---

# FINDING-002-012：返回依赖分支不一定含显式时间词

## Observation

Strategy `2.0.193` 已要求每条引用显式分类，并对大型引用集中的每个可能调用方执行两次聚焦审核。产品路径完成 99 次调用并封存，但 Codex 独立复核仍发现 `ElementProcessor.visit` 把 `findPolicy` 调用与基于 `policy` 的返回后分支合在一条事实中，`applyDocxPolicy` 也把 `DelegatePolicy.invoke` 与之后的文档状态检查合在一条事实中。

## Evidence / reproduction

`var/product-generic-v193-suite205-explicit-sequence/document-render-two-stage-pipeline--world_assisted.json` 的答案先展示组合的 `ElementProcessor.visit` 事实，再解释 `RunTemplate.findPolicy` 内部行为；组合事实中的“当 policy 为”依赖 `findPolicy` 已经返回，但没有使用“之后”或“然后”。答案还先展示 `DelegatePolicy.invoke` 内部行为，后展示包含该调用及后续文档变更检查的 `applyDocxPolicy` 事实。逐调用方聚焦输出把这两条都显式判为原子，说明负向证据已可审核，但判定规则本身仍过窄。

## Impact

真实源码经常通过赋值、返回值分支、状态读取或下一条语句表达调用返回顺序，不一定在事实文字中加入显式时间连接词。若只接受“之后/然后”类词，顺序审核即使逐条执行也会系统性漏掉数据依赖和源码语句顺序。

## Classification rationale

变化修订当前切片的通用顺序语义，不引入工程、语言、框架或符号特判，也不改变外部接口 Owner，因此归类为 iteration-design。

## Decision and disposition

组合调用方判定继续要求一个主动调用、一个不同的返回后调用方操作，以及另一条解释 exact 被调内部的事实；但返回后顺序现在可以由显式时间词、被调返回值或绑定值的使用、或者同一正式事实所陈述的后续源码状态分支与语句顺序建立。`temporal_connector_fragment` 在没有显式时间词时只承担精确定位作用，可以是最小分隔或分支引导文本；完整事实必须仍能证明同一路径上的不同后续操作，单独标点、用途说明、平行分支或兄弟重载仍不能构成跨度。

## Verification after disposition

回归测试用“调用帮助方法；若结果有效则返回”的事实验证没有显式时间词的返回值分支仍会被识别，并由两次单调用方聚焦审核触发拆分；平行分派的反例继续通过争议裁决保持原子。相关 159 项测试通过。Strategy 升级为 `2.0.194`，`2.0.193` 的能力资格和产品结果不能继承。
