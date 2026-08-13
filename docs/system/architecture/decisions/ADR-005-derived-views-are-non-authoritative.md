---
id: SYS-ADR-005
kind: system-decision
status: accepted
authority: normative
owners: [architecture]
depends_on: [SYS-ADR-003]
derived_from: [AD-028, AD-035, AD-036, AD-062, AD-114]
code: []
tests: []
---

# ADR-005：派生视图不拥有正式知识

## Context

面向任务组织知识可以改善使用体验，但缓存或视图若成为第二事实源，会使支持链和失效语义分叉。

## Decision

任何 Semantic View 或 Projection 都是从 exact Snapshot 可重建的只读组织，不创造、修改或扩张正式知识，也不单独证明 Sufficiency 或授权回答。

## Alternatives

把物化视图作为新权威读取路径会引入双写和隐藏前提。

## Consequences

Structure View 已作为第一个专门 Semantic View Contract 被接受；ITER-006 进一步接受了只覆盖
`JAVA_STATIC_CALL_GRAPH@1` 的最小 Behavior View。完整 Behavior、Business、History 和其他语言仍未接受；任何后续 View
即使启用也必须保持可重建、只读和非权威。
