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

当前唯一活动设计是 [SLICE-001：世界模型与主工程 Agent 能力恢复](SLICE-001-engineering-qa-direction-preview.md)。PDR-014 已完全替换
PDR-013 的执行路线：知识构建、Agent harness、二者集成增益和最终产品质量分别验证，并在累计八个开发小时内优先交付真实浏览器 Alpha。

旧 Answer/Review/preflight 协议、run-127 以前的逐题修复和未提交 `@40` candidate 只保留为历史证据。开发不得继续增长旧协议；普通失败
按最早责任层切换实现并继续，不创建新的失败动作或授权等待。

后续设计只有在用户确认 Alpha 与质量方向后才可进入：

- [SLICE-002：跨工程夯实](SLICE-002-cross-project-hardening.md)
- [SLICE-003：正式产品验收](SLICE-003-formal-product-acceptance.md)

两者当前均不得前置到活动 Slice。
