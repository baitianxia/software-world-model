---
id: SYS-ADR-004
kind: system-decision
status: accepted
authority: normative
owners: [architecture, knowledge]
depends_on: [SYS-ADR-003]
derived_from: [AD-011, AD-012, AD-013, AD-029, AD-030, AD-079, AD-099, AD-111, AD-113, AD-121, AD-122, AD-129]
code: []
tests: []
---

# ADR-004：以 Scope、Context、Snapshot、Schema 建立一致性边界

## Context

软件知识只在明确版本和解释条件下成立，且发布必须避免读到部分新状态。

## Decision

Knowledge Scope 是发布、并发和逻辑分片边界；Context 是命题成立条件；Schema 固定可表达语义；Snapshot 是单 Scope 完整不可变状态，CURRENT 只指向一个已原子发布的 Snapshot。Scope 至少区分 System、Shared Component 和 Business Domain：共享组件定义归 Shared Component Scope，宿主运行观察归宿主 System Scope，跨系统 Business Entity 与业务语义归 Business Domain Scope。

## Alternatives

全局 mutable graph、对象逐条上线或长期保存 `latest` 引用都会产生漂移和部分可见性。

## Consequences

跨 Scope 只能 exact 只读引用，且不改变被引用对象的归属。当前 Schema Core 只支持 `INITIAL` 和 `UNCHANGED`；已有 CURRENT 采用不同 Schema 必须在 Schema Evolution / Adoption Contract 被接受前失败关闭。新 Snapshot、受控重建或迁移是未来该能力仍必须遵守的边界，不表示当前已启用。
