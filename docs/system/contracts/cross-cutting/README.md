---
id: SYS-CONTRACT-X-INDEX
kind: system-contract-index
status: current
authority: normative
owners: [architecture]
depends_on: [SYS-CONTRACT-INDEX]
code: [src/software_world_model/cross_cutting]
tests: [tests/test_resource_allocation.py, tests/test_telemetry.py]
---

# Cross-cutting Contracts

横切能力提供执行和观察语义，但不能成为业务或知识权威。

- [Capability Execution](capability-execution.md)
- [Telemetry 与成本](telemetry-cost.md)
