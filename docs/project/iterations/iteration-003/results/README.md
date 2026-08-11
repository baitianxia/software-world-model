---
id: ITER-003-RESULTS-INDEX
kind: iteration-result-index
status: completed
authority: evidence
owners: [project, quality]
depends_on: [ITER-003-VERIFICATION, ITER-003-RESULT-G0, ITER-003-RESULT-G1, ITER-003-RESULT-G2, ITER-003-RESULT-G3A, ITER-003-RESULT-V009, ITER-003-RESULT-G3B, ITER-003-RESULT-G4, ITER-003-RESULT-ACCEPTANCE]
code: []
tests: []
iteration: ITER-003
---

# Iteration 003 Results

[G0 冻结输入](gate-g0.md) 至 [V-009 External qualification and sealed baselines](v009-qualification.md) 已按各自 exact checkpoint PASS。[G3b Evaluation-only browser model run](gate-g3b.md) 保留初始 58/60 FAIL，并在 root GA 修复后以全新 product checkpoint/batch 取得 60/60 独立 PASS。[G4 Human and Product Acceptance](gate-g4.md) 的真实浏览器内容、Citation、A/B、Knowledge Gap、随机身份/拓扑与独立更新后 Session 稳定核对均 PASS。[Final Acceptance](acceptance.md) 只接受本机 Maven Structure World Model 的 `EVALUATION_ONLY` 纵向闭环，Production Activation 未执行。

预留 ID/文件名固定为：

- `ITER-003-RESULT-G0` / `gate-g0.md` — PASS
- `ITER-003-RESULT-G1` / `gate-g1.md` — PASS
- `ITER-003-RESULT-G2` / `gate-g2.md` — PASS
- `ITER-003-RESULT-G3A` / `gate-g3a.md` — PASS
- `ITER-003-RESULT-V009` / `v009-qualification.md` — PASS
- `ITER-003-RESULT-G3B` / `gate-g3b.md` — PASS（保留初始 FAIL lineage）
- `ITER-003-RESULT-G4` / `gate-g4.md` — PASS
- `ITER-003-RESULT-ACCEPTANCE` / `acceptance.md` — COMPLETED

G0 Result 必须绑定授权治理提交 Q；G1 及以后每个 Result 必须绑定上一 Gate PASS。所有 Result 还必须固定 exact checkpoint commit、Manifest/fixture/suite digest、执行命令、原始证据目录、自动检查和人工核对；上一 Result 未提交为 PASS 时，不得开始下一 Gate 的产品代码。
