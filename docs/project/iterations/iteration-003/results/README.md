---
id: ITER-003-RESULTS-INDEX
kind: iteration-result-index
status: in-progress
authority: evidence
owners: [project, quality]
depends_on: [ITER-003-VERIFICATION, ITER-003-RESULT-G0, ITER-003-RESULT-G1, ITER-003-RESULT-G2]
code: []
tests: []
iteration: ITER-003
---

# Iteration 003 Results

[G0 冻结输入](gate-g0.md) 已在 exact checkpoint `af849fb198179cfe1d1514f272a1a06236684f43` 上 PASS，绑定授权治理提交 `42a3f1ababed73cded8aafb046105309a79c170e`。[G1 Knowledge Kernel](gate-g1.md) 已在 exact 实现 checkpoint `ddb8f5feba1e0c52d2f788c2bb66c93810f2b469` 上 PASS，绑定已提交的 G0 Result `7286c0108394baac4254a14fc3405029707dd10d`。[G2 Source-off Snapshot/View](gate-g2.md) 已在 exact 实现 checkpoint `82aef7563556c70527b3c92227d0711a28437587` 上 PASS，绑定已提交的 G1 Result `801717d6e75459afeddb7299234a2e32b65aad16`；当前只解除 G3a 无外部分派实现。外部披露、Provider/Model、CC/CE、baseline、G3b/G4 与 Activation 均不能由 G2 推导。

预留 ID/文件名固定为：

- `ITER-003-RESULT-G0` / `gate-g0.md` — PASS
- `ITER-003-RESULT-G1` / `gate-g1.md` — PASS
- `ITER-003-RESULT-G2` / `gate-g2.md` — PASS
- `ITER-003-RESULT-G3A` / `gate-g3a.md`
- `ITER-003-RESULT-G3B` / `gate-g3b.md`
- `ITER-003-RESULT-G4` / `gate-g4.md`

G0 Result 必须绑定授权治理提交 Q；G1 及以后每个 Result 必须绑定上一 Gate PASS。所有 Result 还必须固定 exact checkpoint commit、Manifest/fixture/suite digest、执行命令、原始证据目录、自动检查和人工核对；上一 Result 未提交为 PASS 时，不得开始下一 Gate 的产品代码。
