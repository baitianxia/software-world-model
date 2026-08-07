---
id: SYS-CONTRACT-KNOWLEDGE-ADMISSION
kind: system-contract
status: current
authority: normative
owners: [knowledge]
depends_on: [SYS-CONTRACT-KNOWLEDGE-EVIDENCE, SYS-CONTRACT-KNOWLEDGE-ENTITY, SYS-CONTRACT-KNOWLEDGE-FACT, SYS-CONTRACT-KNOWLEDGE-INFERENCE-CONFLICT, SYS-CONTRACT-KNOWLEDGE-SCHEMA-CORE]
derived_from: [DD-KNW-ADMISSION]
code: [src/software_world_model/knowledge_engine/formal.py, src/software_world_model/infrastructure/sqlite_formal_knowledge_repository.py]
tests: [tests/test_formal_knowledge.py, tests/test_knowledge_update.py]
---

# Knowledge Admission

## Purpose and scope

Admission 判断一个完整 Candidate Closure 是否满足正式知识契约。Proposal、Candidate、Admission ACCEPT 和 Published 是不同状态；ACCEPT 只授权进入发布前置检查。

## Owner and public contract

Knowledge Engine 拥有 Candidate Identity、Read Set、Verifier Assessment 与 Admission Decision。Verifier 独立重读 exact Closure，不能访问 Connector、修改 Candidate 或自行发布。

## Invariants

1. 先按 authoritative identity 聚合，再审核 final Candidate；不能通过拆分重复对象绕过检查。
2. 机械闭包检查与语义审核分阶段，二者都绑定 exact Candidate Digest、Schema、Context、upstream 和 provenance。
3. 生成与审核上下文隔离；审核 UNKNOWN、缺失或资格失效均失败关闭。
4. 每个 Admission Decision 绑定一个 exact Closure Revision、该 Closure 的完整 Read Set、Schema、Context、expected current、upstream 与 provenance；它不绑定之后才形成的整批结果或 Publication Manifest。
5. Publisher 只允许把已审核 local reference 替换为最终稳定 ID，且替换前后语义 Digest 不变。
6. Admission Preflight 不替代 Publication CAS；Admission、Application Acceptance 和 Publication 是三道独立门。
7. Candidate 不得被 Knowledge Use、Response Control 或生产缓存读取。
8. 只有共同定义关系形成 Hard Atomic Closure；普通 Entity→Fact 等依赖使用有向 Publication Prerequisite，最终 Manifest 必须 predecessor-closed。
9. 独立 Closure 可以并行审核；Admission Batch Result 绑定唯一 Final Bundle Seal，并完整覆盖每个 Closure、未解析项和对应终态，不能静默丢项或把局部 ACCEPT 聚合成整体 ACCEPT。

## Failure, concurrency and recovery

Closure 缺失、身份冲突、Verifier 读取漂移、Schema 失效或并发重复均保持旧正式状态。Envelope、Decision、Attempt、Batch 字段和并行算法由代码与 Fault/Contract Tests 定义。
