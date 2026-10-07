---
id: SYS-ADR-005
kind: system-decision
status: accepted
authority: normative
semantic_owner: SYS-ARCH-BASELINE
authority_scope: decision-rationale-only
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

各类 View 可以按受控 Contract 逐步提供 Structure、Behavior、Business、History 和 Operational 等投影，但任何 View 都只是
从 exact Snapshot 重建的只读组织，不因某个 View 尚未实现或尚未启用而删减世界模型的认知维度。后续 View 或索引即使启用，也必须
保持可重建、只读和非权威；具体 Profile 的实现与启用状态记录在项目实现参考中。
