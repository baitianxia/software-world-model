---
id: SYS-CONTRACT-KNOWLEDGE-SNAPSHOT-PUBLICATION
kind: system-contract
status: current
authority: normative
owners: [knowledge]
depends_on: [SYS-CONTRACT-KNOWLEDGE-ADMISSION, SYS-CONTRACT-KNOWLEDGE-SCHEMA-CORE]
derived_from: [DD-KNW-SNAPSHOT-PUBLICATION]
code: [src/software_world_model/knowledge_engine/formal.py, src/software_world_model/infrastructure/sqlite_formal_knowledge_repository.py]
tests: [tests/test_formal_knowledge.py, tests/test_knowledge_update.py]
---

# Snapshot Publication

## Purpose and scope

Snapshot 是单一 Knowledge Scope 下完整、不可变、原子发布的正式知识状态，不是 Delta。发布把已接受的本地 Candidate Reference 固定为正式身份，并移动 CURRENT。

## Owner and public contract

Knowledge Engine 的 Publisher 独占 Snapshot、Manifest、Member State、Publication Attempt 与 CURRENT 写权。Application 提供独立 Acceptance；只有 exact Admission ACCEPT 与 Application PASS 同时成立才可发布。

## Invariants

1. Snapshot 成员仅为 Entity State、ASSERTED Fact State 与 ASSERTED Inference State；Conflict 是受约束的 Inference 类型。Evidence、Artifact、Context、Admission、Schema、Attempt 和 Result 只作 trace dependency。
2. local reference 替换只在整体提交成功后对外可见；失败不能泄露部分正式 ID。
3. replacement 不隐式继承旧成员，enrichment 不静默删除旧知识；旧 State 继续存在也要满足新 Snapshot 的准入闭包。
4. 全部权威记录与 CURRENT 在同一 Scope 事务中提交，并显式检查 expected current。
5. cross-scope dependency 固定 exact Snapshot；Read Session 打开后不随 CURRENT 漂移。
6. 当前没有 physical cleanup 或 authoritative projection。
7. Knowledge Engine 拥有唯一权威发布裁决与并发 fence；可以由串行化、提交时重验证、版本冲突检测或等价机制实现。对同一逻辑请求，cancel 与 publish 竞态只能有一个终态胜出。
8. `OUTCOME_UNKNOWN` 只是调用方尚不能证明结果的视图；同一 request / idempotency key 必须查询或恢复原 Publication Attempt，不得创建第二个竞争发布。

## Failure and implementation boundary

任何 Digest、资格、expected current、Member Closure 或 CAS 失配都保留旧 CURRENT。Manifest/Receipt 字段、构建顺序、取消和恢复算法由代码及 Contract/Fault Tests 定义。
