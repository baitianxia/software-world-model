---
id: SYS-CONTRACT-KNOWLEDGE-PERSISTENCE
kind: system-contract
status: current
authority: normative
owners: [knowledge]
depends_on: [SYS-CONTRACT-KNOWLEDGE-SNAPSHOT-PUBLICATION]
derived_from: [DD-KNW-PERSISTENCE]
code: [src/software_world_model/infrastructure/sqlite_formal_knowledge_repository.py, src/software_world_model/infrastructure/sqlite_structure_knowledge_repository.py, src/software_world_model/infrastructure/sqlite_structure_read_session_repository.py, src/software_world_model/infrastructure/sqlite_maven_structure_update_repository.py, src/software_world_model/infrastructure/sqlite_legacy_formal_reader.py, src/software_world_model/infrastructure/sqlite_database.py]
tests: [tests/test_formal_knowledge.py, tests/test_foundation.py, tests/test_structure_publication.py, tests/test_structure_read_session.py, tests/test_maven_structure_update_authority.py, tests/test_legacy_formal_reader.py]
---

# Formal Knowledge Persistence

## Purpose and scope

本契约保护正式知识在持久化、幂等恢复、隔离读取和物理演进中的逻辑语义。具体 SQLite 表、索引和 Repository 方法属于实现。

## Owner and public contract

Knowledge Engine 是正式知识唯一写者；Infrastructure 实现其 Repository Port，但不能重解释身份、引用、Admission 或 Publication。Source Integration 继续拥有 Artifact 存储。

## Invariants

1. 不可变内容不原地修改；Knowledge-owned 的 CURRENT、Availability 等可变指针或生命周期状态使用 Revision 和 compare-and-set。
2. 同一幂等键永久绑定同一输入 Digest 与已知 Outcome；Timeout 不证明失败，不能用新键重复副作用。
3. Scope、Schema Registry、Admission、Publication 与其他 Owner 的原子边界保持分离，物理共库不能合并语义事务。
4. 当前正式知识 append-only，`NO_PHYSICAL_CLEANUP`；Projection 关闭，未来即使启用也非权威。
5. 只支持从同一连续持久历史恢复；无法证明连续性、Digest 或 CAS 时 fail-stop。
6. 数据库迁移、备份和物理布局不得改变逻辑 Owner、Reference 或 Snapshot Publication 语义。
7. Repository 必须分别持久化 Root 与 Snapshot State，并无损保存 Relation Fact 的 typed subject/object EntityRef、Publication Mode、Coverage Root/State 和 Support Map；读取层不得从 label、path 或文本反向拼接关系。
8. exact Snapshot 查询、重启恢复和 Snapshot diff 都只能使用已提交的 Snapshot Manifest 与成员，不得借当前 Source 状态补齐或重新解释历史。
9. `Snapshot Read Bundle` 是 committed exact Snapshot/ordered Read Set 的不可变、可删除、可重建读取副本，不是第二权威或语义 Projection。它必须绑定 Scope、Snapshot IDs 与顺序、Schema/Context/Profile、Coverage、完整成员 Manifest 及每条 Root/State/Support metadata digest；消费者先机械验证这些绑定，任一缺失或不匹配即拒绝读取。
10. Read Bundle 只能包含查询所需的 typed Entity/Fact Root/State、Coverage、Support ref/locator/digest 与公开定义；禁止包含 Evidence observation/excerpt、Artifact/Source bytes、Provider 输入或其他可被答案链当作源码旁路的 payload。Bundle 只能在对应 Snapshot 已提交后生成，生成失败不改写 Snapshot，但该 Snapshot 不得标记为可隔离回答。
11. `WORLD_MODEL` 隔离回答进程只挂载产品 package 与 exact Read Bundle，不能挂载包含 Evidence payload 的权威数据库或 Evidence Store。旧版合库可通过兼容性端口读取，但不得进入该进程。Query Result 密封后，独立 Citation Projector 才可在另一进程读取 Evidence Store 中 Result allowlist 指定的 observation；Projector 不得拥有模型、Query、Update 或回传答案链的端口。

## Failure and evolution boundary

损坏、历史缺口、重复键冲突或不可证明恢复均拒绝继续写入。Repository Port、canonical encoding、Outbox 和 Recovery Algorithm 由代码与测试定义；Cleanup、Projection 和非连续恢复在新的 System Contract 被接受前保持不支持。
