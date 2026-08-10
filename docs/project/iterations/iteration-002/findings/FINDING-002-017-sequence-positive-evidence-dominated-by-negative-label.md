---
id: FINDING-002-017
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-002-SLICE-001, FINDING-002-013]
code: [src/software_world_model/ai_infrastructure/agentic_knowledge_strategy.py]
tests: [tests/test_agentic_knowledge_strategy.py]
iteration: ITER-002
classification: iteration-design
disposition: preserve-validated-sequence-defects-and-separate-derived-edges
target: ITER-002-SLICE-001
---

# FINDING-002-017：顺序正向证据被负向标签和平台派生边覆盖

## Observation

Strategy `2.0.198` 的产品运行完成 127 次模型调用后在答案修正阶段失败。聚焦审核每次都按要求返回空 `edges`，但平台解析器自动加入“推理前提先于推理记录”的必要排序边，随后又把这些平台派生边误判为聚焦审核越界。另一方面，整体顺序审核曾返回一个经文本片段校验成立的调用返回跨度，却同时把该引用留在原子列表；平台把整个输出作为重复分类拒绝，修正后模型删除了真实跨度。

## Evidence / reproduction

`var/product-generic-v198-suite205-coverage-citation-recovery/` 的三轮答案选择都在第一个聚焦引用处耗尽三次局部重试。模型原始输出的 `edges` 均为空，错误详情却分别报告 5、2、7 条边；这些数量来自所选 INFERENCE 的平台前提边。第三轮整体审核还正确识别 `renderInclude` 引用把 `template.reload(generate())` 调用与返回后的 `applyDocxPolicy` 合并，并给出精确调用、时间连接、返回后行为和 `reload` 被调内部引用，但因同一引用也出现在 `atomic_references` 中而被全部丢弃。

同轮事实顺序审核也曾输出经证据校验成立的组合跨度，同时保留原子标签；因此该问题不仅浪费答案重试，还会让上游事实修复漏掉已经发现的真实拆分缺陷。

## Impact

聚焦审核的模型输出与平台派生排序边属于不同权限层。混淆两者会使任何包含推理记录的大答案必然在第一个聚焦引用处失败。正向调用返回跨度已经通过精确片段、被调身份、顺序和 Need 范围校验；让一个重复的负向“原子”标签覆盖它，会把已经发现的质量问题重新隐藏。

## Classification rationale

问题属于通用顺序证据合并与权限边界，不依赖特定工程、语言、调用名或自然语言，因此归类为当前切片的 iteration-design 修订。

## Decision and disposition

聚焦审核的无边约束只检查模型原始 `edges` 字段；平台在校验后补充的推理前提边继续用于最终排序，但不能用于指控模型越界。一个调用返回跨度只有在精确调用方片段、时间或返回依赖、返回后行为、被调主题和 Need 范围全部通过后才进入有效集合；若同一引用还被标为原子，平台确定性删除该负向原子标签并保留正向跨度。未知、缺失或范围外分类仍失败关闭。

该规则让已验证的缺陷触发事实拆分，不接受组合事实，也不删除推理的必要排序边。

## Verification after disposition

新增测试验证有效跨度优先于同一输出中的重复原子标签，以及包含平台派生推理边的答案仍可完成逐引用聚焦审核。Strategy 升级为 `2.0.199`；`2.0.198` 能力资格和失败产品运行不能继承。
