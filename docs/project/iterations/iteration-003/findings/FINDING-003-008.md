---
id: FINDING-003-008
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-003-SLICE-001, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-CONTRACT-KNOWLEDGE-EVIDENCE, SYS-CONTRACT-KNOWLEDGE-ADMISSION, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE]
code: [src/software_world_model/source_integration/operations.py, src/software_world_model/source_integration/artifact_use.py, src/software_world_model/infrastructure/sqlite_source_operation_repository.py, src/software_world_model/infrastructure/sqlite_artifact_use_authority_repository.py, src/software_world_model/knowledge_engine/structure_authority.py, src/software_world_model/knowledge_engine/structure_publication.py, src/software_world_model/application_services/maven_structure_update.py]
tests: [tests/test_source_operations.py, tests/test_artifact_use_authority.py, tests/test_structure_publication.py, tests/test_maven_structure_update.py]
iteration: ITER-003
classification: local-implementation
disposition: enforce-current-artifact-read-and-owner-verified-persistent-use
target: src/software_world_model/source_integration/artifact_use.py
---

# FINDING-003-008：跨模块 Artifact 读取与持久使用初版没有闭合当前授权

## Observation

G1 初版 Maven 更新从已完成的 Source Operation 直接重放 Artifact，并只在 Application
Result 中记录一次 use confirmation。历史 Operation 成功不能证明当前 Scope、Source 与
Binding 仍允许读取；独立 verifier 和 `OUTCOME_PENDING` recovery 也可绕过 exact Read
Package/Closure/Protection 取得 payload。更严重的是，confirmation 发生在 Admission 之后，
Knowledge Admission 与 Publisher 无法证明将要保存的 Candidate 就是 Source owner 已确认的
exact downstream persistent use。

## Evidence

- 暂停 Binding 或退役 Scope 后，旧 replay port 仍能返回 terminal Operation payload。
- verifier 与 recovery 初版持有全局 replay port，而不是 Package-bounded replay capability。
- `StructureAdmissionDecision` 与 Publisher 输入没有 confirmation ID/digest；公共 Admission/
  Publication 调用方可完全不创建 Source confirmation。
- 只在 Maven Application Result 保存 confirmation 不能让 Knowledge owner 在 ACCEPT/CURRENT
  写入边界重读并拒绝伪造或漂移。

## Impact and classification

Source Artifact、Evidence、Admission 与 Knowledge Update 契约已经要求当前授权、exact
Package/Closure/Protection、一次性 persistent-use confirmation 和 owner-side proof
consumption。本发现没有改变这些系统语义，而是暴露实现未闭合跨模块 authority closure，
因此属于 local implementation。

## Decision and disposition

Source Operation 为无 payload 的 authority coordinates 保存独立摘要；Artifact replay 在读取
payload 前必须消费 Application 提供的新鲜 `SOURCE_EXECUTION` Scope assertion，并重验当前
Source/Binding revision 与 lifecycle。Artifact owner 只为 exact Package/Closure/Protection
签发 bounded replay capability，verifier 与 recovery 不再持有全局 replay。

Candidate 在独立 Assessment 之前取得一次性 confirmation；confirmation ID/digest 随 Candidate、
Verifier Assessment 与 Admission canonical digest 持久化。Knowledge Admission 与 Publisher
通过中立 proof-verifier port 从 Source owner 重读 exact confirmation，并核对 candidate
ref/digest；缺失、伪造、漂移、撤权或 Package/Protection 不匹配都在 ACCEPT/CURRENT 前失败。
测试覆盖 suspended Binding、retired Scope、越界 package replay、direct public bypass、
confirmation tamper 及 pending recovery。
