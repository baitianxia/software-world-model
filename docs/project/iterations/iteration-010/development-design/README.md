---
id: ITER-010-DEVELOPMENT-DESIGN
kind: development-design-index
status: current
authority: project-plan
owners: [engineering, architecture, product, quality]
depends_on: [ITER-010-PROPOSAL, ITER-010-READINESS, ITER-010-VERIFICATION, ITER-010-SLICE-001, ITER-010-PDR-012, ITER-010-PDR-014, FINDING-010-256, FINDING-010-257, PROJECT-GOVERNANCE-PLAN-EXECUTION]
code: []
tests: []
iteration: ITER-010
coding_input: true
---

# ITER-010 Development Design

当前唯一活动设计是 [SLICE-001：世界模型与主工程 Agent 能力恢复](SLICE-001-engineering-qa-direction-preview.md)，其当前任务顺序唯一见
[ITER-010 当前任务拆分计划](EXECUTION-PLAN-CURRENT.md)。PDR-014 的能力目标保留，但不再把知识构建、Agent harness、集成和浏览器拆成
相互阻塞的内部阶段；它们必须在最小用户价值纵切中一起验证。

旧 Answer/Review/preflight 协议、run-127 以前的逐题修复和未提交 candidate 只保留为历史证据。开发不得继续增长旧协议；普通失败
按最早责任层切换实现并继续，不创建新的失败动作或授权等待。当前计划修订必须通过 `plan_shape` 检查，不能增加第二套阶段编号或过期版本绑定。

后续设计只有在用户确认 Alpha 与质量方向后才可进入：

- [SLICE-002：跨工程夯实](SLICE-002-cross-project-hardening.md)
- [SLICE-003：正式产品验收](SLICE-003-formal-product-acceptance.md)

两者当前均不得前置到活动 Slice。
