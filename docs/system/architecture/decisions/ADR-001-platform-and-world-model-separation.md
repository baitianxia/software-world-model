---
id: SYS-ADR-001
kind: system-decision
status: accepted
authority: normative
owners: [architecture]
depends_on: [SYS-PRODUCT-VISION]
derived_from: [AD-075, AD-083, AD-118]
code: []
tests: []
---

# ADR-001：平台与软件世界模型分离

## Context

同一平台需要构建多个来源、版本和知识范围。若把平台状态与某个世界模型混为一体，权限、生命周期和产品结论会相互污染。

## Decision

平台拥有构建、治理和使用能力，Knowledge Engine 拥有正式知识记录及生命周期；世界模型由 Knowledge Scope、Context、Schema 和 Snapshot 确定。模型输出经平台结晶为正式知识，但平台运行状态本身不成为被建模软件世界的业务命题。

## Alternatives

采用单一全局知识库，或把模型会话当作世界模型，均无法提供精确版本、所有权和可重建性。

## Consequences

每个持久引用必须明确模型边界；多 Scope 不获得隐式全局事务或统一真相。
