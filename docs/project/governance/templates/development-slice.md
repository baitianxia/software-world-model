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
product_goal_live_ad_hoc_checkpoint_id: pending
product_goal_reflection_gate_case_id: V-REFLECT-NNN
product_goal_slice_gate_case_ids: []
---

# SLICE-NNN：<Vertical outcome>

## Status and dependencies

同一 Iteration 有多个累积 Slice 时，本 Slice 必须依赖 accepted Readiness，并直接依赖前一个 Slice。Readiness 只授权第一个 Slice；
后续 Slice 保持 proposed，直到前序人工 Web、该阶段适用的 hidden canary、停止 Gate 和方案复盘完成并形成 exact Slice Result。方向探针
与可用 Alpha 使用可见真实输入判向，不因 hidden canary 延迟；Alpha `CONTINUE` 后的夯实 Slice 才承担 early hidden。后续授权时再把
该 Result 加入 `depends_on`，并与 Manifest `reflection_prerequisite_result` 一致；不能先授权再补证据。

## Product-goal contribution and cumulative integration

说明本 Slice 如何缩短 Proposal 冻结的通用源码问答差距、如何连接此前已接受能力，以及本 Slice 结束时用户能在同一个正式
Web 入口人工验证什么。中间机械 Gate 可以先行，但 Slice 不能靠孤立 CLI/View 演示宣称产品增量。

- Product gap shortened: <exact-gap>
- Product capability-path step advanced: <roadmap-step-and-user-visible-delta>
- Existing capabilities combined: <exact-capabilities>
- User-visible Web questions at slice end: <held-out-and-cross-domain-cases>
- Slice stop / redirect signal: <falsifiable-signal>
- Critical assumptions tested: <assumption-ids-and-evidence>
- Reflection gate and success decision: <V-REFLECT-NNN-and-CONTINUE-or-ACCEPT>

## Direction preview checkpoint

若本 Slice 是方向探针或可用 Alpha，列出真实产品入口、最少代表性任务、仅为运行所必需的门禁、用户可见限制，以及体验后由谁作出
`CONTINUE / REDIRECT / REJECT`。探针使用极少量输入；Alpha 使用小而多样的输入并只做探针证据要求的最小通用修正。两者都不得安排
与方向判断无关的全面加固。技术质量必须由独立评测方先行裁决，用户只作产品方向决定。若本 Slice 属于工程夯实或正式验收，必须引用
前一 Alpha 或方向体验的 `CONTINUE` 结果。

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
Manifest 只绑定本 Slice 已到期的假设；成功决定要求这些假设全部为 `SUPPORTED`。尚未到期的假设只能记录 early signal 与下一风险，
不能伪装成已经证明；最终 Slice 必须覆盖全部关键假设。

## Findings

链接本轮的 [Findings](../findings/README.md) 与[实现发现回写规则](../../../governance/implementation-feedback-policy.md)。只有 Readiness 已接受、Slice 改为 `status: authorized` / `authority: current-development` / `coding_input: true`，并被 `project/current.md` 指向后，才是编码输入。
