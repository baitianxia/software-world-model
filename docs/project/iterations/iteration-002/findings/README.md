---
id: ITER-002-FINDINGS
kind: iteration-findings-index
status: open
authority: development-evidence
owners: [engineering, architecture]
depends_on: [PROJECT-GOVERNANCE-IMPLEMENTATION-FEEDBACK, ITER-002-PROPOSAL]
code: []
tests: []
iteration: ITER-002
---

# Iteration 002 Findings

- [FINDING-002-001：浏览器输出暴露内部诊断并扩张问题](FINDING-002-001-browser-answer-projection.md) — dispositioned to Slice design
- [FINDING-002-002：已满足问题仍可能存在应用限制](FINDING-002-002-application-limitation.md) — dispositioned to Response Control contract
- [FINDING-002-003：事实覆盖复核需要保留 Need 绑定](FINDING-002-003-reviewed-need-binding.md) — dispositioned to Fact contract
- [FINDING-002-004：复杂调用链需要独立顺序验收](FINDING-002-004-sequence-verification.md) — dispositioned to Verification Matrix
- [FINDING-002-005：产品验收需要单独的源码外发授权](FINDING-002-005-source-disclosure-authorization.md) — dispositioned to Slice security boundary
- [FINDING-002-006：资源上限不应成为答案质量目标](FINDING-002-006-quality-before-call-budget.md) — dispositioned to Verification Matrix
- [FINDING-002-007：空顺序结果缺少穷举证明](FINDING-002-007-exhaustive-sequence-audit.md) — dispositioned to Slice design
- [FINDING-002-008：全局调用熔断再次截断正常收敛的质量链](FINDING-002-008-global-budget-truncated-convergent-quality-chain.md) — dispositioned to Verification Matrix
- [FINDING-002-009：大型顺序引用集会漏掉真实调用返回边界](FINDING-002-009-large-sequence-set-missed-boundary.md) — dispositioned to Slice design
- [FINDING-002-010：局部重试熔断截断可收敛的语言修复](FINDING-002-010-language-repair-truncated-by-local-fuse.md) — dispositioned to Slice design
- [FINDING-002-011：空的顺序负向结论不能证明逐引用检查已执行](FINDING-002-011-empty-negative-sequence-audit.md) — dispositioned to Slice design
- [FINDING-002-012：返回依赖分支不一定含显式时间词](FINDING-002-012-return-dependent-branch-without-temporal-word.md) — dispositioned to Slice design
- [FINDING-002-013：整体顺序审核仍会因注意力稀释漏掉组合事实](FINDING-002-013-aggregate-sequence-audit-attention-dilution.md) — dispositioned to Slice design
- [FINDING-002-014：事实复核重试缺少精确的候选键差异](FINDING-002-014-fact-review-repair-missing-key-diagnostics.md) — dispositioned to Slice design
- [FINDING-002-015：充分性修正缺少精确的引用和限制差异](FINDING-002-015-sufficiency-repair-reference-diagnostics.md) — dispositioned to Slice design
- [FINDING-002-016：覆盖引用的未知文件编号绕过安全恢复](FINDING-002-016-coverage-unknown-artifact-recovery.md) — dispositioned to Slice design
- [FINDING-002-017：顺序正向证据被负向标签和平台派生边覆盖](FINDING-002-017-sequence-positive-evidence-dominated-by-negative-label.md) — dispositioned to Slice design
- [FINDING-002-018：顺序片段的最小词边界重叠会丢失正向证据](FINDING-002-018-sequence-fragment-lexical-overlap.md) — dispositioned to Slice design
- [FINDING-002-019：受限裁决中的额外负向标签覆盖正向跨度](FINDING-002-019-restricted-positive-span-extra-negative-labels.md) — dispositioned to Slice design
- [FINDING-002-020：单数字段格式错误耗尽顺序审核修复次数](FINDING-002-020-sequence-atomic-shape-repair.md) — dispositioned to Slice design
- [FINDING-002-021：答案顺序修复约束在内部审核中丢失](FINDING-002-021-answer-sequence-repair-constraint-loss.md) — dispositioned to Slice design
- [FINDING-002-022：下游再次精简会删除已证明的必要答案内容](FINDING-002-022-downstream-support-deletion.md) — dispositioned to Slice design
- [FINDING-002-023：充分性证明集合不等于应逐条展示的答案集合](FINDING-002-023-proof-support-is-not-visible-answer.md) — dispositioned to Slice design
- [FINDING-002-024：正式知识生产与同步答案耦合扩大失败面](FINDING-002-024-formal-knowledge-critical-path-coupling.md) — dispositioned to ADR-013 and Evidence Answering contract
- [FINDING-002-025：同一路径的分段读取会发生 Artifact 身份碰撞](FINDING-002-025-partial-artifact-identity-collision.md) — dispositioned to Source Artifact contract
- [FINDING-002-026：审核模型可能错误批准响应语言不一致](FINDING-002-026-review-language-false-approval.md) — dispositioned to Evidence Answering contract and generic writing-system guard
- [FINDING-002-027：聚合审核漏过顺序颠倒和未证实意图](FINDING-002-027-review-order-and-intent-gaps.md) — dispositioned to Verification Matrix and capability counterexamples
- [FINDING-002-028：生成结果满足 JSON Schema 但违反答案段语义约束](FINDING-002-028-draft-semantic-contract-recovery.md) — dispositioned to Evidence Answering contract and bounded draft repair
- [FINDING-002-029：来源正确不等于回答相关且可读](FINDING-002-029-review-relevance-readability-gap.md) — dispositioned to Evidence Answering contract and independent relevance/readability review
- [FINDING-002-030：完整模型响应仍可能因截断或语义缺项违反角色契约](FINDING-002-030-model-role-contract-repair.md) — dispositioned to Evidence Answering contract and bounded role repair
