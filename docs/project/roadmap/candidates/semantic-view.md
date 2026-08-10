---
id: ROADMAP-CANDIDATE-SEMANTIC-VIEW
kind: roadmap-candidate
status: candidate
authority: planning-only
owners: [application, product]
depends_on: [SYS-ADR-005, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE]
code: []
tests: []
coding_input: false
legacy_source: DD-SEM-SEMANTIC-VIEW
---

# Candidate：后续 Semantic Views

## Trigger

Structure View 已因真实 Maven 结构任务进入 current System Contract。本 Candidate 只保留 Behavior、Business、History 和其他后续 View；只有真实任务证明普通正式知识查询无法在可接受成本内支持时，才继续引入。

## Proposed boundary

- 只读 exact Snapshot 的正式知识，每个视图项保留 exact Support Map。
- Entity 只支持身份，不能把显示结构变成隐藏属性或命题。
- `READY` 只表示视图可读，不等于 Requirement sufficient、Answer reviewed 或 authorized。
- View 和物化缓存不拥有知识，不能隐藏 Conflict、Gap 或 Limitation。

## Unknowns

Structure 范围已有冻结场景和契约；其实现与产品结果拟由 `ITER-003` 验证。其他 View 仍缺少用户场景、查询成本基线、组织质量评测和失效/缓存数据，不能从 Structure View 自动推导。

## Entry conditions

每个后续 View 分别用真实任务证明具体不足，冻结 View Purpose、Support 完整性 Oracle 和性能基线，并在独立 Iteration 中验证最小只读 Strategy。不得把 Structure View 的接受当作其他 View 的授权。
