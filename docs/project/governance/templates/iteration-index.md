---
id: ITER-NNN-INDEX
kind: iteration-index
status: proposed
authority: project
owners: [project]
depends_on: [ITER-NNN-PROPOSAL, ITER-NNN-READINESS]
code: []
tests: []
iteration: ITER-NNN
coding_input: false
---

# Iteration NNN：<Outcome>

## Status and authorization

## Required inputs

- [Proposal](proposal.md)
- [Manifest](manifest.yaml)
- [Verification Matrix](verification-matrix.md)
- [Readiness Review](readiness-review.md)
- [Development Design](development-design/README.md)
- [Findings](findings/README.md)
- [Results](results/README.md)

只有 Readiness 已接受、Iteration 改为 `status: authorized` / `coding_input: true`，且 `project/current.md` 同时指向本 Iteration 与其中一个已授权 Slice 后，才可编码。

失败尝试进入修复等待时使用 `status: paused` / `coding_input: false`，`project/current.md` 不得指向本 Iteration 或 Slice；收到新的明确
用户授权后恢复同一 Slice。`paused` 不是 `rejected`，也不允许授权后续 Slice。

从未执行的计划被后续项目决定替代时使用 `status: superseded` / `coding_input: false`；它不能包含活动 Slice、执行 Result 或 Acceptance，
也不能用于隐藏执行后的失败。
