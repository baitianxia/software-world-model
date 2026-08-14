---
id: ITER-NNN-READINESS
kind: iteration-readiness
status: proposed
authority: project-authorization
owners: [project, architecture, quality]
depends_on: [ITER-NNN-PROPOSAL, ITER-NNN-VERIFICATION]
code: []
tests: []
iteration: ITER-NNN
authorized_by: pending
authorized_at: pending
product_goal_alignment_verdict: pending
product_goal_alignment_reviewed_by: pending
product_goal_alignment_review_ref: pending
critical_assumption_catalog_digest: pending
---

# Iteration NNN Readiness Review

## Reviewed exact inputs

## Product-goal alignment gate

核对 Proposal/Manifest 已冻结通用源码问答 MVP 的 baseline gap、已有能力累积路径、独立持有且对实现隐藏的 held-out 自由
问题增量、至少一个跨域问题、最早正式 Web 体验点、现场临时问题和停止条件。任一项缺失，或 Outcome 只是孤立
Profile/View/组件，Readiness 必须保持 `proposed`。

- Reviewed evidence and baseline gap: <exact-reference-and-verdict>
- Capability-path step, predecessor evidence, end capability and next gap: <exact-reference-and-verdict>
- Accepted/new capability integration and cross-domain path: <exact-reference-and-verdict>
- Hidden held-out ownership, before/target counts and live Web questions: <exact-reference-and-verdict>
- Stop / redirect decision: <exact-reference-and-verdict>

## Architecture reflection gate readiness

核对 Proposal 已冻结关键假设、最早反证、成熟替代方案对照和反证后的动作；Manifest 为每个 Slice 恰好绑定一个
`V-REFLECT-NNN`。第一段必须优先验证最高风险架构假设，每个 Slice Result 必须形成独立复盘结论；没有 `CONTINUE` 决定和用户
再次授权时，后续 Slice 不得进入开发。
每段 Reflection 必须绑定 exact 用户决策消息收据；后续 Slice 的授权必须引用同一条前序 Reflection 决策消息，且不能复用更早
授权。成熟替代方案 protocol/rubric/cache policy 和正向价值 metric/unit/direction/threshold/replay protocol、独立裁决 Owner
也必须在编码前冻结；调查步数与模型调用上限至少为 2，并结构化冻结 query/result 单步与总字节、总时长、Support、trace 和超限语义。

## Outcome, scope and non-goals

## System contracts and unresolved decisions

## Slice, dependency and risk closure

## Verification readiness

## Authorization decision

只有明确授权后才把 `status` 改为 `accepted`，填写非 `pending` 的 `authorized_by` / `authorized_at`，再更新 Iteration、Slice 与 `project/current.md`。本记录不能自行推定用户授权。
