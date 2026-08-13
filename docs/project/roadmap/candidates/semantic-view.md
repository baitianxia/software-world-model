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

从 ITER-007 起，View 只能作为缩短 `SYS-PRODUCT-SUCCESS` 通用源码问答差距的实现手段，不能再以“新增一个 View 可读”作为
独立产品 Iteration Outcome。候选必须在同一正式 Web 的自由问题中组合此前已接受能力，并通过产品目标对齐门禁。

## Active validation

`ITER-006` 已完成其中最窄 Java 静态调用 Behavior 子集的 deterministic 与 run-008 live Product Validation；Direct/Codex/
World Model 各 6/6、comparison PASS，但尚无最终用户 Acceptance。该结果不接受完整 Behavior View，也不改变 Business、History、
其他语言或运行时调用的 Candidate 状态。`ITER-007` 当前只提出 Java 源码实现语义与通用源码问答的累积产品切片，不把
Business View 或其他单一 View 提升为开发授权。
