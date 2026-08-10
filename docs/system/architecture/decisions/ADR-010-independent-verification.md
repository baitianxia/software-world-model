---
id: SYS-ADR-010
kind: system-decision
status: accepted
authority: normative
owners: [architecture, quality]
depends_on: [SYS-ADR-002, SYS-ADR-009]
derived_from: [AD-053, AD-104, AD-112, AD-115, AD-127]
code: []
tests: []
---

# ADR-010：知识审核与答案审核独立

## Context

候选知识正确不代表答案忠实，答案流畅也不能证明候选知识可准入。

## Decision

Knowledge Verifier 独立复核需要沉淀的 Candidate 与支持闭包。同步 Evidence Answer 的 Answer Review 角色从原问题、密封 Evidence Packet 和用户可见 Draft 独立重建检查清单并提交 Finding Proposal；正式知识回答的 Review 继续重读 Claim、Coverage、限制和绑定。Response Control 独占 Review Decision、Final Authorization 和 Logical Delivery。生成者不能自审，知识审核与答案审核也不能互相替代。

## Alternatives

一次模型自评成本较低，但会共享错误和隐藏输入。

## Consequences

需要隔离上下文和额外调用；任一审核 UNKNOWN 或缺失均失败关闭。
