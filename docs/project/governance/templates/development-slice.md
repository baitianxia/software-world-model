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
product_goal_live_ad_hoc_checkpoint_id: pending
product_goal_slice_gate_case_ids: []
---

# SLICE-NNN：<Vertical outcome>

## Status and dependencies

同一 Iteration 有多个累积 Slice 时，本 Slice 必须依赖 accepted Readiness，并直接依赖前一个 Slice。Readiness 只授权第一个 Slice；
后续 Slice 保持 proposed，直到前序人工 Web、独立隐藏 canary 和停止 Gate 完成并形成 Slice Result，再次获得明确授权。

## Product-goal contribution and cumulative integration

说明本 Slice 如何缩短 Proposal 冻结的通用源码问答差距、如何连接此前已接受能力，以及本 Slice 结束时用户能在同一个正式
Web 入口人工验证什么。中间机械 Gate 可以先行，但 Slice 不能靠孤立 CLI/View 演示宣称产品增量。

- Product gap shortened: <exact-gap>
- Existing capabilities combined: <exact-capabilities>
- User-visible Web questions at slice end: <held-out-and-cross-domain-cases>
- Slice stop / redirect signal: <falsifiable-signal>

## Current vs expected behavior

## System contracts and invariants

## Interfaces and affected code

## Compatibility, data and security boundaries

## Open questions and implementation risks

## Acceptance scenarios

## Findings

链接本轮的 [Findings](../findings/README.md) 与[实现发现回写规则](../../../governance/implementation-feedback-policy.md)。只有 Readiness 已接受、Slice 改为 `status: authorized` / `authority: current-development` / `coding_input: true`，并被 `project/current.md` 指向后，才是编码输入。
