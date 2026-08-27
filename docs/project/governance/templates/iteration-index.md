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

失败尝试默认在同一 Slice active `REWORK`，只阻止 PASS、晋级和 hardening；现有本地开发授权覆盖修复时继续使用
`status: authorized|in-progress` / `coding_input: true`，`project/current.md` 保持指向。只有 scope/Owner 变化、用户明确暂停或本地开发授权
失效时才使用 `status: paused` / `coding_input: false` 并移除指针。external exact grant pending 只阻断对应 action，不导致暂停；开发者必须
直接申请最小权限并继续独立安全工作。`paused` 不是 `rejected`，也不允许授权后续 Slice。

从未执行的计划被后续项目决定替代时使用 `status: superseded` / `coding_input: false`；它不能包含活动 Slice、执行 Result 或 Acceptance，
也不能用于隐藏执行后的失败。
