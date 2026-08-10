---
id: FINDING-002-016
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-002-SLICE-001, FINDING-002-015]
code: [src/software_world_model/ai_infrastructure/agentic_knowledge_strategy.py]
tests: [tests/test_agentic_knowledge_strategy.py]
iteration: ITER-002
classification: iteration-design
disposition: complete-conservative-coverage-citation-recovery
target: ITER-002-SLICE-001
---

# FINDING-002-016：覆盖引用的未知文件编号绕过安全恢复

## Observation

Strategy `2.0.197` 取得能力资格后运行产品任务。覆盖复核为事实 `c9` 选择了正确问题、正确源码行和正确锚点，但将其 `artifact_id` 抄错一个字符。平台在 16 次完整模型调用后拒绝发布知识快照；两次修正收到空错误详情并重复同一文件编号。

## Evidence / reproduction

`var/product-generic-v197-suite205-sufficiency-diagnostics/` 的运行数据库显示，授权候选 `c9` 指向 `source_artifact_d055b69c4e560054d7d3f52de8d00d3f:68-72`，三次覆盖输出都使用不存在的 `source_artifact_d055b69c4e560053d7d3f52de8d00d3f:68-72`。候选绑定、行范围、`findPolicy`、`getCustomPolicy`、`tagName`、`getDefaultPolicy`、`sign` 和 `getTemplatePolicy` 源码锚点全部一致。实现已有对“错误但已知文件编号”的唯一映射安全恢复，却在文件编号未知时提前抛错，使同一恢复规则无法执行。

## Impact

模型复制长的不透明编号时可能产生单字符错误。若唯一且已独立审核的事实已经给出精确来源，平台却只返回抽象错误，重复调用不会增加知识；直接接受未知编号会破坏证据闭合，删除覆盖项则会损失答案质量。

## Classification rationale

问题是通用来源身份闭合和契约修正问题，不依赖 Java、文档渲染任务或任何特定文件名，因此归类为当前切片的 iteration-design 修订。

## Decision and disposition

把现有保守恢复扩展到未知文件编号和无效范围，但必须同时满足：只映射一个候选、候选已绑定当前问题、候选来源存在、候选精确范围可读、覆盖项的每个源码锚点都出现在该范围。满足全部条件时，平台采用候选已审核的精确来源身份；任一条件不满足仍失败，并返回 `invalid_fields`、`unknown_artifact_id`、`candidate_evidence` 和可执行修正动作。

这只是确定性修复引用元数据，不补写事实、不改变语义结论、不降低覆盖或来源门槛。

## Verification after disposition

新增回归测试验证未知文件编号只有在唯一候选及全部源码锚点闭合时才能恢复。Strategy 升级为 `2.0.198`；`2.0.197` 能力资格和失败产品运行不能继承。
