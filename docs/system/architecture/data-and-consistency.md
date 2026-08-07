---
id: SYS-ARCH-CONSISTENCY
kind: system-architecture
status: current
authority: normative
owners: [architecture, knowledge]
depends_on: [SYS-ARCH-COMPONENTS, SYS-ARCH-INVARIANTS]
code: [src/software_world_model/infrastructure]
tests: [tests/test_foundation.py, tests/test_formal_knowledge.py, tests/test_management.py]
---

# 数据所有权与一致性

## 原子边界

- 每个 Owner 只在自己的 Repository 和事务中写权威状态。
- Knowledge Scope 是正式知识发布、并发控制和逻辑分片边界；不支持跨 Scope 原子发布。
- Snapshot Publication 在一个事务中写入全部权威成员并移动 CURRENT；Snapshot 是完整状态，不是隐式 Delta。
- 跨 Owner 用稳定命令、结果引用、幂等键和恢复协调，不使用分布式大事务。

## 不可变与恢复

- 已注册 Schema、Artifact、Evidence、正式知识 State、Snapshot 和封存结果不可原地改写。
- 可变关联通过 Revision 与 compare-and-set 更新；同一幂等键永久绑定同一输入摘要和已知结果。
- Timeout 或连接中断只表示结果未知，不能写成失败或零消耗。
- 当前正式知识存储为 append-only，物理清理和 Projection 均不属于当前权威路径。

## 跨边界引用

持久依赖固定 exact Scope、Context、Schema、Snapshot、Artifact 或 Result 身份。`CURRENT`/`latest` 只能在入口解析一次，不能进入长期依赖。跨 Scope 只允许对精确 Snapshot 的只读引用。
