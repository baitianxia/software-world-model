---
id: ITER-NNN-PROPOSAL
kind: iteration-proposal
status: proposed
authority: project-proposal
owners: [product, engineering]
depends_on: [SYS-PRODUCT-SUCCESS]
code: []
tests: []
iteration: ITER-NNN
coding_input: false
---

# ITER-NNN Proposal：<Outcome>

## Trigger and evidence

## Product-goal alignment and cumulative delta

- MVP target reference: `SYS-PRODUCT-SUCCESS`
- Capability path reference and current step: <roadmap-milestone-and-step>
- Accepted predecessor evidence: <prior-acceptance-and-failure-evidence>
- Current product gap and real-question evidence: <gap-and-evidence>
- Accepted capabilities reused: <accepted-capability-refs>
- New capabilities integrated into the same answer chain: <new-capability-refs>
- Evaluator/user-owned hidden held-out before/target counts: <measurable-delta-and-isolation>
- Cross-domain questions combining old and new knowledge: <cross-domain-cases>
- Earliest product-owned Web checkpoint and live ad-hoc questions: <slice-and-gate>
- End-of-iteration user-visible Web capability: <exact-capability-if-accepted>
- Next blocking gap after success: <next-earliest-unproved-capability>
- Stop / redirect conditions: <falsifiable-conditions>

## Critical assumptions and falsification plan

列出决定本方案是否成立的少量关键假设。每项必须绑定最早验证 Slice、真实产品证据、反证条件和反证后的动作；第一段优先验证
最高风险假设，并尽早与成熟替代方案对照，不能把架构价值判断留到最终验收。

对照不能只要求“质量不退步”。若方案比成熟替代方案更复杂或更昂贵，必须在编码前冻结至少一项可测的正向差异化价值指标、
阈值、测量周期和基线缓存/复用政策；未达阈值时不得 `CONTINUE` 或 `ACCEPT`。

本节必须恰好使用一张三列表，第一列以 `A1：<完整假设原文>` 格式编号；第二、三列分别写最早反证和反证后的动作，均不得留空。

| 假设 | 最早证据与反证 | 反证后的动作 |
|---|---|---|
| A1：<完整且可证伪的假设原文> | <最早-Slice、真实产品证据与失败判据> | <REDIRECT-REJECT-or-alternative> |

## Outcome and users

## Scope / non-goals

## Adopted system IDs

## Development slices and dependencies

## Risks and unknowns

## Verification and acceptance

## Authorization decision

Proposal 本身不授权编码；结论被接受时把状态改为 `accepted`，但仍需 Manifest、Verification Matrix、Readiness Review、已授权 Slice 与 `project/current.md` 指针共同成立。
