---
id: ITER-003-RESULTS-INDEX
kind: iteration-result-index
status: in-progress
authority: evidence
owners: [project, quality]
depends_on: [ITER-003-VERIFICATION, ITER-003-RESULT-G0, ITER-003-RESULT-G1, ITER-003-RESULT-G2, ITER-003-RESULT-G3A, ITER-003-RESULT-V009, ITER-003-RESULT-G3B]
code: []
tests: []
iteration: ITER-003
---

# Iteration 003 Results

[G0 冻结输入](gate-g0.md) 至 [V-009 External qualification and sealed baselines](v009-qualification.md) 已按各自 exact checkpoint PASS。[G3b Evaluation-only browser model run](gate-g3b.md) 的正式 product batch 执行为 60/60 SUCCESS，但独立产品裁决为 58/60，因而 **G3b FAIL**。根 GA 渲染缺口已在后续本地 checkpoint 修正并通过 750 项回归，但新代码尚无全新 60-run 外部 batch；V-011/G4 仍被阻断。

预留 ID/文件名固定为：

- `ITER-003-RESULT-G0` / `gate-g0.md` — PASS
- `ITER-003-RESULT-G1` / `gate-g1.md` — PASS
- `ITER-003-RESULT-G2` / `gate-g2.md` — PASS
- `ITER-003-RESULT-G3A` / `gate-g3a.md` — PASS
- `ITER-003-RESULT-V009` / `v009-qualification.md` — PASS
- `ITER-003-RESULT-G3B` / `gate-g3b.md` — FAIL
- `ITER-003-RESULT-G4` / `gate-g4.md`

G0 Result 必须绑定授权治理提交 Q；G1 及以后每个 Result 必须绑定上一 Gate PASS。所有 Result 还必须固定 exact checkpoint commit、Manifest/fixture/suite digest、执行命令、原始证据目录、自动检查和人工核对；上一 Result 未提交为 PASS 时，不得开始下一 Gate 的产品代码。
