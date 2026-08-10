---
id: FINDING-002-019
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-002-SLICE-001, FINDING-002-017, FINDING-002-018]
code: [src/software_world_model/ai_infrastructure/agentic_knowledge_strategy.py]
tests: [tests/test_agentic_knowledge_strategy.py]
iteration: ITER-002
classification: iteration-design
disposition: restrict-extra-negative-labels-after-positive-proof
target: ITER-002-SLICE-001
---

# FINDING-002-019：受限裁决中的额外负向标签覆盖正向跨度

## Observation

Strategy `2.0.200` 的产品运行完成 81 次模型调用和 6 次源码动作，没有 Provider 结果未知。事实顺序审核按 `FINDING-002-018` 保留了 `renderInclude` 的调用返回跨度，并把它送入独立争议裁决。裁决前两次只返回全部引用的原子标签，因超出只裁决一个调用方的范围而被正确要求修正；第三次返回了精确、成立的正向跨度，但仍附带全部引用的原子标签。平台因这些范围外负向标签拒绝整份输出，最终没有发布知识快照。

## Evidence / reproduction

证据位于 `var/product-generic-v200-suite205-lexical-overlap-preservation/`。`model_call_6cb07b957d1d4942adae0802302ae5c4` 的跨度以 `c13` 为组合调用方、`c14` 为 `reload` 内部行为，调用、连接和后续 `applyDocxPolicy` 片段都通过 exact 文本与顺序校验。同一输出把 `c1` 至 `c16` 全部列为原子；平台已按 `FINDING-002-017` 删除 `c13` 的重复原子标签，却继续把其余 15 个不在本次裁决范围内的负向标签视为致命越界。

## Impact

受限审核的范围用于限制模型能够提出的正向缺陷和负向结论。一个已验证的范围内正向跨度不会因其他已知引用被顺带标为原子而变得不成立；让无排序证据的额外负向标签覆盖它，会再次丢失质量缺陷。另一方面，若输出只有越界原子标签而没有任何正向跨度，放宽范围会让模型用未执行的聚焦检查形成虚假否定结论。

## Classification rationale

问题属于通用的正负顺序证据合并和受限审核权限边界，不依赖工程、语言或具体符号，归类为当前切片的 iteration-design 修订。

## Decision and disposition

完整集合审核继续要求每条引用精确分类。聚焦或争议裁决使用受限分类范围时，默认仍严格拒绝范围外原子标签；只有同一 Need 的同一输出已经包含至少一个通过 exact 片段、被调身份、顺序和范围校验的正向跨度时，平台才把原子集合收缩到本次必需分类范围。范围外原子标签只是冗余负向意见，不进入顺序证据，也不能删除正向跨度。

纯负向越界输出继续失败并触发契约修正；未知引用、范围外正向跨度、越界边、缺失必需调用方和无效片段继续失败关闭。

## Verification after disposition

新增测试同时验证“正向跨度存在时忽略额外原子标签”和既有“纯负向虚假并行跨度由裁决拒绝”。用失败运行第三次裁决输出重放后，`c13 → c14 → 后续 applyDocxPolicy` 跨度被保留。Strategy 升级为 `2.0.201`；`2.0.200` 的能力资格和失败产品运行不能继承。
