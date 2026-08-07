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

# Candidate：Semantic View

## Trigger

只有真实用户任务需要结构、行为、业务或历史的专门组织方式，且普通正式知识查询无法在可接受成本内支持时，才引入 Semantic View。

## Proposed boundary

- 只读 exact Snapshot 的正式知识，每个视图项保留 exact Support Map。
- Entity 只支持身份，不能把显示结构变成隐藏属性或命题。
- `READY` 只表示视图可读，不等于 Requirement sufficient、Answer reviewed 或 authorized。
- View 和物化缓存不拥有知识，不能隐藏 Conflict、Gap 或 Limitation。

## Unknowns

当前缺少证明专门视图必要性的用户场景、查询成本基线、组织质量评测和失效/缓存数据。旧主题仍为 `In Review`，因此不能作为当前 Contract。

## Entry conditions

用真实任务证明普通 Knowledge Use 的具体不足；冻结 View Purpose、Support 完整性 Oracle 和性能基线；在 Iteration 中验证最小只读 Strategy，并在确有跨模块语义后再接受 System Contract。
