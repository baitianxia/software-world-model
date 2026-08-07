---
id: ROADMAP-INDEX
kind: roadmap-index
status: current
authority: planning-only
owners: [product, project]
depends_on: [SYS-PRODUCT-SUCCESS, PROJECT-GOVERNANCE-ITERATION-LIFECYCLE]
code: []
tests: []
coding_input: false
---

# Roadmap

Roadmap 按产品或系统结果组织方向，不按组件列任务。它用于比较价值、风险、依赖和学习目标，不直接授权编码、排期或生产启用。

## Milestones

- [M-001：正式知识单路径的本机体验基线](milestones/M-001-formal-knowledge-single-path.md) — achieved。

## Candidates

- [显式限定范围的生产启用](candidates/production-activation.md)
- [Schema Evolution](candidates/schema-evolution.md)
- [Semantic View](candidates/semantic-view.md)

Candidate 的存在不表示它会成为下一轮。只有进入条件有证据、Outcome 相对其他候选更优且 Proposal 获得明确授权后，才能建立 Iteration。

## 选择规则

优先选择能够验证最大产品/架构风险的最小纵向结果。排序至少比较：用户价值或风险降低、当前证据强度、依赖是否就绪、失败能学到什么、是否可逆、验证和运行成本。没有证据时保持 Candidate，不用伪精确分数制造优先级。
