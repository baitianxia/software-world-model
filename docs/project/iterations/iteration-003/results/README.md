---
id: ITER-003-RESULTS-INDEX
kind: iteration-result-index
status: not-run
authority: planned-evidence
owners: [project, quality]
depends_on: [ITER-003-VERIFICATION]
code: []
tests: []
iteration: ITER-003
---

# Iteration 003 Results

尚未运行。每个 Gate 只在实际产生 exact subject、原始证据、完整失败和人工结论后新增对应 Result；本目录和 Proposal 不能预先声明 PASS。

预留 ID/文件名固定为：

- `ITER-003-RESULT-G0` / `gate-g0.md`
- `ITER-003-RESULT-G1` / `gate-g1.md`
- `ITER-003-RESULT-G2` / `gate-g2.md`
- `ITER-003-RESULT-G3A` / `gate-g3a.md`
- `ITER-003-RESULT-G3B` / `gate-g3b.md`
- `ITER-003-RESULT-G4` / `gate-g4.md`

G0 Result 必须绑定授权治理提交 Q；G1 及以后每个 Result 必须绑定上一 Gate PASS。所有 Result 还必须固定 exact checkpoint commit、Manifest/fixture/suite digest、执行命令、原始证据目录、自动检查和人工核对；上一 Result 未提交为 PASS 时，不得开始下一 Gate 的产品代码。
