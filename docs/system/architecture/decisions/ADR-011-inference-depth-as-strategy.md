---
id: SYS-ADR-011
kind: system-decision
status: accepted
authority: normative
owners: [architecture, knowledge]
depends_on: [SYS-ADR-003, SYS-ADR-008]
derived_from: [AD-116]
code: []
tests: []
---

# ADR-011：推断深度属于可评测 Strategy

## Context

固定全局深度无法同时满足简单命题和复杂软件影响分析；无限推断又不可控。

## Decision

Contract 只要求有限、无环、可展平并受预算约束。具体深度、搜索和停止策略作为 Capability Strategy 评测和激活，不冻结进领域模型。

## Alternatives

全局常量简单但会成为隐性产品上限；无限递归不可审计。

## Consequences

Strategy 可独立演进，但不能改变正式前提、支持闭包和安全边界。
