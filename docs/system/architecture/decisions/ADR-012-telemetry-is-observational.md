---
id: SYS-ADR-012
kind: system-decision
status: accepted
authority: normative
owners: [architecture, operations]
depends_on: [SYS-ADR-006]
derived_from: [AD-124]
code: []
tests: []
---

# ADR-012：Telemetry 与成本治理只做观察

## Context

跨模块需要统一观测和成本分析，但集中采集不能成为第二业务 Store 或同步依赖。

## Decision

Telemetry 单向消费 Owner 已封存的 Result 引用；Usage 与 Valuation 分离，未知价格不是零。采集、导出和后端失败不改变领域结果，也不能放行知识、回答或激活。

## Alternatives

让 Telemetry 扫描私有 Store 或参与预算决定会复制权威并放大故障。

## Consequences

采用 at-least-once、稳定事件 ID 和 Owner outbox；内容、Secret 与思维链不进入事件。
