---
id: SYS-ADR-003
kind: system-decision
status: accepted
authority: normative
owners: [architecture, knowledge]
depends_on: [SYS-ADR-002]
derived_from: [AD-002, AD-027, AD-041, AD-042, AD-123, AD-128]
code: []
tests: []
---

# ADR-003：采用正式知识的认识论分层

## Context

来源片段、观察、身份、直接命题和推导结论具有不同证明强度，不能统一为无类型文本块。

## Decision

正式路径区分 Artifact、Evidence、Entity、Fact、Inference、Conflict 与 Snapshot。Fact 由直接 Evidence 支持，Inference 只依赖已发布前提；对象身份与 Snapshot 中状态分离且历史不可变。

## Alternatives

统一 Document/Chunk 模型简单但无法证明命题、Context、冲突和更新延续。

## Consequences

准入和 Schema 更严格；局部字段由代码定义，但认识论边界属于稳定 Contract。
