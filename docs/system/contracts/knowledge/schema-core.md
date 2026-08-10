---
id: SYS-CONTRACT-KNOWLEDGE-SCHEMA-CORE
kind: system-contract
status: current
authority: normative
owners: [knowledge]
depends_on: [SYS-CONTRACT-KNOWLEDGE-REFERENCE-CONTEXT]
derived_from: [DD-KNW-SCHEMA-CORE]
code: [src/software_world_model/knowledge_engine/formal.py, src/software_world_model/knowledge_engine/structure_authority.py, src/software_world_model/infrastructure/sqlite_formal_knowledge_repository.py, src/software_world_model/infrastructure/sqlite_structure_knowledge_repository.py]
tests: [tests/test_formal_knowledge.py, tests/test_structure_publication.py]
---

# Schema Core

## Purpose and scope

Schema 定义正式知识可表达的类型和规则。本契约覆盖 Definition 注册、引用和发布时适用性；当前系统不支持从已有 CURRENT 自动采用不同 Schema。

## Owner and public contract

Knowledge Engine 拥有 Schema Registry。调用者通过包含 Digest 的 exact Schema Reference 读取或请求采用；生成者不能自审 Definition。

## Invariants

1. 已注册 Definition 不可变，依赖必须闭合、精确且无环。
2. 注册成功不等于任何 Scope 已采用该 Schema，也不证明模型 Strategy 可生成合规知识。
3. 每次发布都校验实际 Scope、Manifest Target 与 exact Schema；Publisher 在同一事务重新读取 Registry 资格。
4. `INITIAL` 和 `UNCHANGED` 发布不依赖 Evolution Contract；只有从已有 CURRENT 采用不同 Schema 才触发未来 Adoption 能力。
5. 弃用不改写历史 Snapshot，历史解释依赖闭包不得物理清除。
6. Schema Proposal、Review 和 Registration 使用分离身份；模型只能提出候选。
7. Registration 与初始 target-eligible Availability 原子形成；Availability 只能单调弃用，不能原地重新启用旧 exact Schema Reference。
8. Schema selection、final target validation 与 Publisher commit 分别固定或重验当前 Availability；并发弃用使新的 target 失败关闭，但不改写已发布 Snapshot。

## Failure and implementation boundary

Digest 不匹配、依赖缺失、循环、Scope 不适用或发布时资格变化均拒绝。Definition Schema、Registration Attempt、状态和 CAS 由代码与 Contract Tests 定义；具体 Schema 作为版本化实现资产保存。
