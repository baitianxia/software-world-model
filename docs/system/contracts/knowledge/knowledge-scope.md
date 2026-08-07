---
id: SYS-CONTRACT-KNOWLEDGE-SCOPE
kind: system-contract
status: current
authority: normative
owners: [knowledge]
depends_on: [SYS-ARCH-INVARIANTS]
derived_from: [DD-KNW-KNOWLEDGE-SCOPE]
code: [src/software_world_model/knowledge_engine/scope.py, src/software_world_model/infrastructure/sqlite_scope_repository.py]
tests: [tests/test_knowledge_scope.py]
---

# Knowledge Scope

## Purpose and scope

Knowledge Scope 是知识归属、单 Scope 发布、并发控制和逻辑分片的根身份。它不是租户、物理数据库、全局锁或跨 Scope 事务。

## Owner and public contract

Knowledge Engine 是 Scope 的唯一写者。Application 可以请求创建、修订或退休，但不能直接改变生命周期。Source Binding、Context、Schema 和 Snapshot 只能引用已存在的 exact Scope。

## Invariants

1. Scope 稳定身份一经建立不可改变类型或重新绑定其他知识域。
2. `SYSTEM` 归属单个软件系统的本地技术知识，`SHARED_COMPONENT` 归属可独立引用的共享组件定义，`BUSINESS_DOMAIN` 归属跨系统业务身份与语义；跨 Scope 引用不转移所有权。
3. `RETIRED` 不可恢复；退休不改写或删除历史知识、Snapshot 和结果。
4. 每次 Scope Revision 通过 compare-and-set 形成，不允许丢失并发更新。
5. 无跨 Scope 原子发布；跨 Scope 使用者固定一组 exact Snapshot 并独立处理兼容性。
6. Scope Assertion 只证明 exact Revision 的生命周期资格，不授予来源权限，也不证明来源可达、Schema 适用或知识充分；operation dispatch 与 publication commit 必须各自重验当前 Scope 状态。

## Failure and implementation boundary

Revision 冲突、已退休 Scope、类型漂移或重复幂等键输入不一致均拒绝。Command、Attempt、Result 字段和 CAS 机制由代码与测试定义。
