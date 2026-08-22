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
- Minimum direction-preview checkpoint, representative tasks and explicit non-goals: <preview-slice-entry-and-cases>
- For high direction risk, a small usable-Alpha checkpoint before hardening: <alpha-slice-diverse-inputs-and-cases>
- Direction decision owner and allowed outcomes before hardening: <owner-and-CONTINUE-REDIRECT-REJECT>
- End-of-iteration user-visible Web capability: <exact-capability-if-accepted>
- Next blocking gap after success: <next-earliest-unproved-capability>
- Stop / redirect conditions: <falsifiable-conditions>

## Critical assumptions and falsification plan

列出决定本方案是否成立的少量关键假设。每项必须绑定最早验证 Slice、真实产品证据、反证条件和反证后的动作；第一段优先验证
最高风险假设。Probe/Alpha 记录相对成熟替代方案的 early signal 与正式比较后置理由；正式对照不晚于首个 hardening Slice。

对照不能只要求“质量不退步”。若方案比成熟替代方案更复杂或更昂贵，必须在拥有该对照的首个 hardening Slice 授权前冻结至少一项可测的
正向差异化价值指标、阈值、测量周期和基线缓存/复用政策；未达阈值时不得从该 Slice `CONTINUE` 或最终 `ACCEPT`。不得用该冻结动作阻塞
方向探针或 Alpha 的首次可见结果。

本节必须恰好使用一张三列表，第一列以 `A1：<完整假设原文>` 格式编号；第二、三列分别写最早反证和反证后的动作，均不得留空。

| 假设 | 最早证据与反证 | 反证后的动作 |
|---|---|---|
| A1：<完整且可证伪的假设原文> | <最早-Slice、真实产品证据与失败判据> | <REDIRECT-REJECT-or-alternative> |

## Outcome and users

## Scope / non-goals

## Adopted system IDs

## Development slices and dependencies

至少明确区分：先形成非验收方向探针；对新答案协议、交互主线或模型职责等高方向风险变化，再形成小而多样的可用 Alpha；只有 Alpha
`CONTINUE` 后才执行工程夯实与正式验收。首次体验前只安排安全运行和判断核心价值所需工作，不把全面加固作为体验前置。

## Risks and unknowns

## Verification and acceptance

## Authorization decision

Proposal 本身不授权编码；结论被接受时把状态改为 `accepted`，但仍需 Manifest、Verification Matrix、Readiness Review、已授权 Slice 与 `project/current.md` 指针共同成立。
