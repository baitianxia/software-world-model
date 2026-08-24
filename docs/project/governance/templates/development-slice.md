---
id: ITER-NNN-SLICE-NNN
kind: development-slice
status: proposed
authority: proposed-development
owners: [engineering]
depends_on: [ITER-NNN-PROPOSAL]
code: []
tests: []
iteration: ITER-NNN
coding_input: false
product_goal_gate: V-000
product_goal_accepted_capability_refs: []
product_goal_cross_domain_case_ids: []
product_goal_web_checkpoint_id: pending
product_goal_direction_preview_checkpoint_id: V-PREVIEW-NNN
product_goal_alpha_agent_comparison_checkpoint_id: V-COMP-ALPHA-NNN
product_goal_live_ad_hoc_checkpoint_id: pending
product_goal_reflection_gate_case_id: V-REFLECT-NNN
product_goal_slice_gate_case_ids: []
---

# SLICE-NNN：<Vertical outcome>

## Status and dependencies

同一 Iteration 有多个累积 Slice 时，本 Slice 必须依赖 accepted Readiness，并直接依赖前一个 Slice。Readiness 只授权第一个 Slice；
后续 Slice 保持 proposed，直到前序人工 Web、该阶段适用的 hidden canary、停止 Gate 和方案复盘完成并形成 exact Slice Result。可体验
Alpha 使用可见真实输入判向，不因 hidden canary 延迟；Alpha `CONTINUE` 后的夯实 Slice 才承担 early hidden。后续授权时再把
该 Result 加入 `depends_on`，并与 Manifest `reflection_prerequisite_result` 一致；不能先授权再补证据。

本 Slice 的失败尝试默认进入 `paused / coding_input=false`，不授权下一 Slice。原 Result 由 Manifest/PDR 保留；用户用新的明确收据
重新授权后，恢复本 Slice 而不是新建 Iteration。只有满足 Proposal 冻结的转向依据才使用 `blocked / REDIRECT`。

## Product-goal contribution and cumulative integration

说明本 Slice 如何缩短 Proposal 冻结的通用源码问答差距、如何连接此前已接受能力，以及本 Slice 结束时用户能在同一个正式
Web 入口人工验证什么。中间机械 Gate 可以先行，但 Slice 不能靠孤立 CLI/View 演示宣称产品增量。

- Product gap shortened: <exact-gap>
- Product capability-path step advanced: <roadmap-step-and-user-visible-delta>
- Existing capabilities combined: <exact-capabilities>
- User-visible Web questions at slice end: <held-out-and-cross-domain-cases>
- Slice stop / redirect signal: <falsifiable-signal>
- Same-Slice rework and no-progress limit: <progress-measure-attempt-limit-and-redirect-bases>
- Critical assumptions tested: <assumption-ids-and-evidence>
- Reflection gate and success decision: <V-REFLECT-NNN-and-CONTINUE-or-ACCEPT>

## Direction preview checkpoint

若本 Slice 是可体验 Alpha，列出真实产品入口、小而多样的代表性任务、仅为运行所必需的门禁、用户可见限制，以及体验后由谁作出
`CONTINUE / REWORK / REDIRECT / REJECT`。不得安排与方向判断无关的全面加固。技术质量必须由独立评测方先行裁决，用户只作产品方向
决定。若本 Slice 属于工程夯实或正式验收，必须引用前一 Alpha 的 `CONTINUE` 结果。

从下一份新产品 Iteration 起，Alpha 还必须在同一出口绑定 `V-COMP-ALPHA-NNN`：一条原失败题加另外至少两条相邻或异质题，后两条中至少
一条是产品冻结后的现场输入；current Codex fresh 独立任务先密封、
系统不可见、两份答案随机匿名、独立评测方依据 exact evidence 裁决。系统绝对质量 PASS、逐题无物质退步且总体答案质量严格为正才允许
`CONTINUE`；全体打平或只具有效率优势时在同一 Slice `REWORK`。该 Case 不是体验前的新阶段。

## Experience version checkpoint

记录精确版本、可重复启动方式、固定本地地址、同一会话连续自由提问、版本/限制显示和单题故障隔离的验证 Case。单题错误必须显示
真实失败或限制，同时服务继续接受下一题；一次性运行器不满足本检查点。

## Current vs expected behavior

## System contracts and invariants

## Interfaces and affected code

## Compatibility, data and security boundaries

## Open questions and implementation risks

## Acceptance scenarios

## Architecture reflection checkpoint

本 Slice 的产品 Gate 后必须形成 exact Result，逐项比较假设与证据、分类问题、复核知识表示/查询编排/Web 产品链/验证设计、
对照成熟方案并处置相关 Finding。`V-REFLECT-NNN PASS` 只表示复盘完成；中间 Slice 只有明确决定 `CONTINUE` 才可申请下一段授权，
最终 Slice 只有明确决定 `ACCEPT` 才可申请 Iteration Acceptance。方案被证伪时使用 `REDIRECT` 或 `REJECT`，不得继续堆叠实现。
实现、答案、审核、配置或局部 Contract 缺陷使用 `REWORK`，只暂停当前 Slice；问题被指出或要求复核不得直接解释为方案被证伪。
Manifest 只绑定本 Slice 已到期的假设；成功决定要求这些假设全部为 `SUPPORTED`。尚未到期的假设只能记录 early signal 与下一风险，
不能伪装成已经证明；最终 Slice 必须覆盖全部关键假设。

产品价值复盘必须把 current Codex 外部强基线与 full cognition/locator-only 因果消融分开；Codex 不得充当 Oracle 或 Reviewer，次级成本、
时延和复用指标不得补偿答案质量平局或退步。

## Findings

链接本轮的 [Findings](../findings/README.md) 与[实现发现回写规则](../../../governance/implementation-feedback-policy.md)。只有 Readiness 已接受、Slice 改为 `status: authorized` / `authority: current-development` / `coding_input: true`，并被 `project/current.md` 指向后，才是编码输入。
