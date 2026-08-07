---
id: SYS-CONTRACT-KNOWLEDGE-PERSISTENCE
kind: system-contract
status: current
authority: normative
owners: [knowledge]
depends_on: [SYS-CONTRACT-KNOWLEDGE-SNAPSHOT-PUBLICATION]
derived_from: [DD-KNW-PERSISTENCE]
code: [src/software_world_model/infrastructure/sqlite_formal_knowledge_repository.py, src/software_world_model/infrastructure/sqlite_database.py]
tests: [tests/test_formal_knowledge.py, tests/test_foundation.py]
---

# Formal Knowledge Persistence

## Purpose and scope

本契约保护正式知识在持久化、幂等恢复和物理演进中的逻辑语义。具体 SQLite 表、索引和 Repository 方法属于实现。

## Owner and public contract

Knowledge Engine 是正式知识唯一写者；Infrastructure 实现其 Repository Port，但不能重解释身份、引用、Admission 或 Publication。Source Integration 继续拥有 Artifact 存储。

## Invariants

1. 不可变内容不原地修改；Knowledge-owned 的 CURRENT、Availability 等可变指针或生命周期状态使用 Revision 和 compare-and-set。
2. 同一幂等键永久绑定同一输入 Digest 与已知 Outcome；Timeout 不证明失败，不能用新键重复副作用。
3. Scope、Schema Registry、Admission、Publication 与其他 Owner 的原子边界保持分离，物理共库不能合并语义事务。
4. 当前正式知识 append-only，`NO_PHYSICAL_CLEANUP`；Projection 关闭，未来即使启用也非权威。
5. 只支持从同一连续持久历史恢复；无法证明连续性、Digest 或 CAS 时 fail-stop。
6. 数据库迁移、备份和物理布局不得改变逻辑 Owner、Reference 或 Snapshot Publication 语义。

## Failure and evolution boundary

损坏、历史缺口、重复键冲突或不可证明恢复均拒绝继续写入。Repository Port、canonical encoding、Outbox 和 Recovery Algorithm 由代码与测试定义；Cleanup、Projection 和非连续恢复在新的 System Contract 被接受前保持不支持。
