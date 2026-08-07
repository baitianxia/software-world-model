---
id: SYS-ADR-007
kind: system-decision
status: accepted
authority: normative
owners: [architecture]
depends_on: [SYS-ADR-006]
derived_from: [AD-045, AD-046, AD-050, AD-130]
code: []
tests: []
---

# ADR-007：采用模块化单体和 Owner-local 持久化

## Context

当前规模需要可靠事务和快速演进，没有证据支持分布式部署成本。

## Decision

生产实现采用模块化单体；逻辑模块通过 Port 协作，每个 Owner 保持自己的事务与 Repository。Projection 默认关闭且永不成为权威。

## Alternatives

微服务会提前引入分布式一致性；单层应用则无法保护 Owner 边界。

## Consequences

同进程调用不能绕过公开 Port。未来拆分部署必须保持现有权威和幂等语义。
