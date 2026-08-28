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

只有 Readiness 已接受、Iteration 改为 `status: authorized` / `coding_input: true`，且 `project/current.md` 同时指向本 Iteration、唯一已授权
Slice，并镜像 Manifest 的 `plan_revision_ref`、`current_action.id` 与 `current_action.case_id` 后，才可考虑执行。实际文件、coding 和外部执行
还必须由该唯一 action 的前置、allowlist/denylist 和 locks 精确允许；Slice 广义 `coding_input=true` 不能覆盖动作级限制。

开发前必须运行 plan snapshot；最终 handoff 或合并前必须以 trusted base ref 运行 base-diff gate。首次可操作完整浏览器主链必须立即交付，
但 `requires_result=false`、不移动游标。只有最终方向/完成 handoff 或真实项目状态迁移才需要 Result；普通失败留在当前产品闭环，不移动
游标。候选 Manifest/Result 不能为自身扩权。

用户方向记录只表达 `CONTINUE / REWORK / REDIRECT / REJECT`，不能创建或扩大 standing authority；同一 standing scope 内后续工作直接
调整工作顺序并继续，只有真实 scope delta 才申请新授权。

失败尝试默认在同一 Slice active `REWORK`，只阻止 PASS、晋级和 hardening；现有本地开发授权覆盖修复时继续使用
`status: authorized|in-progress` / `coding_input: true`，`project/current.md` 保持指向。只有 scope/Owner 变化、用户明确暂停或本地开发授权
失效时才使用 `status: paused` / `coding_input: false` 并移除指针。active `PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY@1` 覆盖的公开开源
exact revision、clean、allowlisted、只读测试在已批准 route、预算、调度和 loopback evaluation 边界内不逐 run/逐题申请；系统为每次动作
生成的 exact receipt 不是新授权。只有 scope delta pending 才阻断对应
action，且不导致暂停；开发者必须直接申请最小 delta 并继续独立安全工作。`paused` 不是 `rejected`，也不允许授权后续 Slice。

从未执行的计划被后续项目决定替代时使用 `status: superseded` / `coding_input: false`；它不能包含活动 Slice、执行 Result 或 Acceptance，
也不能用于隐藏执行后的失败。
