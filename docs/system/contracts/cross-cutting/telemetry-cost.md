---
id: SYS-CONTRACT-X-TELEMETRY-COST
kind: system-contract
status: current
authority: normative
owners: [telemetry]
depends_on: [SYS-CONTRACT-X-CAPABILITY-EXECUTION, SYS-CONTRACT-AI-MODEL-GATEWAY]
derived_from: [DD-X-TELEMETRY-COST]
code: [src/software_world_model/cross_cutting/telemetry.py, src/software_world_model/infrastructure/sqlite_telemetry_repository.py]
tests: [tests/test_telemetry.py]
---

# Telemetry 与成本治理

## Purpose and scope

Telemetry 对已发生的权威流程做单向观察，用于诊断、Usage 和成本分析。它不参与知识准入、发布、充分性、响应授权或 Strategy 激活。

## Owner and public contract

每个业务 Owner 发布引用自身权威 Result 的稳定事件；`AUDIT_REQUIRED` 事件必须由 Owner-local reliable emission / Outbox 保证可恢复，普通 Operational Signal 可以采样或异步发送。Telemetry 不扫描 Owner 私有 Store，也不复制完整领域正文。

## Invariants

1. Allocation、实际 Usage 与价格 Valuation 分离；Telemetry 不建立第二预算系统。
2. 失败和未知结果仍记录已知的真实消耗；价格缺失或歧义是 `UNVALUED`，不是零成本。
3. 交付采用 at-least-once，按稳定 Event ID 幂等；丢失 Signal 不能证明业务未发生。
4. 外部 Backend 不得成为同步业务依赖。
5. Secret、源码正文、模型内容、未公开错误正文和 Chain of Thought 不进入事件。
6. Telemetry 推导、Dashboard 或告警不能改变领域状态。
7. 同一 Meter Key / Valuation Basis 只有一个 effective Usage revision 参与聚合；重复事件或后续 Provider Observation 不得重复计量。
8. 新 Usage observation 或 Pricing revision 形成新的不可变 Usage / Valuation revision，不回写历史记录；不同 Currency 不静默合并。

## Failure and operations boundary

导出失败通过可恢复的幂等进度继续，不回滚已完成业务。Checkpoint 形态、事件 taxonomy、价格配置、保留期、Dashboard 和告警属于代码或运维配置；某次运行指标是非规范性执行证据。
