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
