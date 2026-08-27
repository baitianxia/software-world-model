---
id: ITER-NNN-RESULTS-INDEX
kind: iteration-result-index
status: draft
authority: evidence
owners: [project, quality]
depends_on: [ITER-NNN-VERIFICATION]
code: []
tests: []
iteration: ITER-NNN
---

# Iteration NNN Results

结果只记录 exact subject 上实际发生的运行、证据、失败和限制，不拥有 System 规范。每个 Slice Result 还必须记录关键假设与实际
证据的方案复盘和明确的 `CONTINUE / ACCEPT / REWORK / REDIRECT / REJECT`；为每类独立 Gate 创建 Result，并最终链接 Acceptance。
失败尝试必须保留为 `failed-preserved`；`REWORK` 留在同一 Slice，不能被改写为方向转向。

每个 machine action 只能由 Manifest 指定的唯一 Result ID/path 驱动迁移。该 transition Result 必须精确填写 `plan_revision_ref`、
`action_ref`、`verification_case_id` 和 `plan_gate_verdict`；最后一项只能是 `PASS / FAIL / INVALID`，不得使用别名。Result 记录事实，不能
修改 allowlist、预注册 contract 或为同一 candidate diff 创建权限。
