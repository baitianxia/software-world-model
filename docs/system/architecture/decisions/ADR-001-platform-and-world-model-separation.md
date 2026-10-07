---
id: SYS-ADR-001
kind: system-decision
status: accepted
authority: normative
semantic_owner: SYS-ARCH-BASELINE
authority_scope: decision-rationale-only
owners: [architecture]
depends_on: [SYS-PRODUCT-VISION]
derived_from: [AD-075, AD-083, AD-118]
code: []
tests: []
---

# ADR-001：平台与软件世界模型分离

## Context

同一平台需要构建多个来源、版本和知识范围。软件世界模型是软件系统持久、版本化、可验证、可更新的外部认知模型；若把平台状态、一次模型会话、工程手册或检索缓存与某个世界模型混为一体，权限、生命周期和产品结论会相互污染。

## Decision

平台拥有构建、治理和使用能力，Knowledge Engine 拥有正式知识记录及生命周期；世界模型由 Knowledge Scope、Context、Schema 和 Snapshot 确定，独立于任何模型会话或隐藏状态，表达被建模软件的实体、关系、行为、约束、状态、来源、Coverage、Conflict 和 Unknown，为 AI 提供持久的系统认知。模型输出经平台结晶为正式知识，但平台运行状态本身不成为被建模软件世界的业务命题。手册、地图、摘要和索引只能作为 exact Snapshot 的派生投影。

## Alternatives

采用单一全局知识库，或把模型会话、文字手册或检索缓存当作世界模型，均无法提供完整认知、精确版本、所有权和可重建性。

## Consequences

每个持久引用必须明确模型边界；多 Scope 不获得隐式全局事务或统一真相。面向人或任务的投影可以独立演进，但不能成为第二认知权威。
