---
id: FINDING-010-141
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [project, product, engineering, quality]
depends_on: [ITER-010-PDR-002, ITER-010-PDR-005, ITER-010-PDR-008, PROJECT-GOVERNANCE-ITERATION-LIFECYCLE]
code: []
tests: []
iteration: ITER-010
classification: iteration-design
scope: systemic
disposition: move-direction-value-gate-first-and-enforce-one-machine-readable-action
target: ITER-010-PDR-009
---

# FINDING-010-141：计划顺序和粒度允许长期开发而不验证方向

## Observation

ITER-010 已有 Slice 顺序、Readiness、Verification 和大量文档门禁，但活动 Slice 同时授权 Application、AI infrastructure、Web 与完整测试。
现行 next action 只存在于多份自然语言正文，机器校验仍要求“自动收据 → Web canary → 三臂比较”。开发者可以在同一 Slice 内继续调整
Prompt、Reviewer、Provider 和回答规则而不违反 `docs.py check`；也可以把 Manifest 与 Result 一起修改，单树检查无法证明状态迁移来自原
计划。这与“先快速验证方向，再夯实”的用户要求相反。

用户要求“完全纠正”并要求开发严格按计划，随后明确指出文字约束力太差。两条消息的本地 UTF-8 摘要分别为
`sha256:612341017bef3d98db372608d22b0d57744a96883e23dd51a6552c13da183989` 和
`sha256:63962a3f18667dd3727dd76d72c45ae8224e40a06be2d8c12622aca3a4ef0ae5`；它们授权计划与治理纠正，不授权修改产品代码。

## Evidence and root cause

- 现有 Slice 顺序门禁能保证 completed/active/proposed 前后关系，却没有 Slice 内唯一的 machine-readable execution cursor；
- `PROJECT-CURRENT` 的“下一步”是正文描述，Manifest 没有动作级允许路径、外部调用、结果或分支；
- 单树检查看不到 base→target 转换，计划和成功证据可在同一变更中互相授权；仓库此前没有强制运行治理检查的 workflow；
- PDR-002 已确认产品最低标准应超过 current Codex，却把生效时间延后到 ITER-012；ITER-010 仍先投入 canary 和内部完整性，再做弱方向
  信号，导致最重要的替代价值假设长期未检验；
- “直接相关证据、同 Agent 仅源码、同 Agent 世界模型+源码、current Codex”四路尚未同时冻结，无法区分复杂度负担、Agent 负担、世界
  模型贡献和外部强基线差距。

根因是迭代计划以组件/阶段完成度组织，而不是以最早可证伪的产品价值假设组织；治理粒度又停在 Slice，未到实际开发动作。

## Disposition

`ITER-010-PDR-009` 将四路严格价值 Gate 前移，并把当前唯一动作收窄为零外部调用的 Gate freeze。通用执行约束进入
`PROJECT-GOVERNANCE-PLAN-EXECUTION`，由 Manifest v2、Current 镜像、`scripts/docs.py` 单树检查、`scripts/plan_gate.py` 基线差分和 CI
共同执行。当前产品代码与 dirty v7 变更全部锁定、隔离且不得作为比较输入。

本 Finding 不声明四路 Gate 已实现或 PASS；只有动作绑定的 Result 和差分门禁可以推进游标。
