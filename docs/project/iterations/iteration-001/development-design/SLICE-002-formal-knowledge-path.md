---
id: ITER-001-SLICE-002
kind: development-slice
status: completed
authority: historical-development
owners: [knowledge, application]
depends_on: [ITER-001-SLICE-001, SYS-CONTRACT-KNOWLEDGE-ADMISSION, SYS-CONTRACT-KNOWLEDGE-SNAPSHOT-PUBLICATION]
code: [src/software_world_model/knowledge_engine, src/software_world_model/application_services/knowledge_update.py]
tests: [tests/test_formal_knowledge.py, tests/test_knowledge_update.py]
iteration: ITER-001
migration: reconstructed-from-existing-iteration-records
---

# SLICE-002：正式知识单路径

## Outcome

来源观察在 INITIAL Schema 下形成 Evidence、Entity、Fact 和有限 Inference Candidate，经独立审核与应用验收后原子发布为单 Scope Snapshot；失败保持旧 CURRENT。

## Required system semantics

- `INV-004`、`INV-005`、`INV-007`、`INV-009` 与 `INV-010`；
- Candidate、Admission ACCEPT、Application PASS 与 PUBLISHED 分离；
- Fact 由直接 Evidence 完整支持，Inference 只依赖已发布前提；
- Snapshot 是完整状态，稳定身份只在整体发布成功时分配；
- INITIAL/UNCHANGED 不依赖 Schema Evolution。

## Affected implementation

Knowledge Scope/Schema/Context、formal knowledge Repository、Admission、Publication 和 Update orchestration。

## Non-goals

跨 Schema Adoption、跨 Scope 原子发布、物理 Cleanup、权威 Projection 和由模型自由字段逃逸 Schema。

## 阅读与回写

当前语义见[架构不变量](../../../../system/architecture/invariants.md)、[Admission](../../../../system/contracts/knowledge/admission.md)和[Snapshot Publication](../../../../system/contracts/knowledge/snapshot-publication.md)；实现发现进入本轮 [Findings](../findings/README.md)。

## Acceptance

身份、Context、Evidence Coverage、非正式前提、Closure、独立审核、expected-current CAS、取消/发布竞态和恢复均有失败关闭测试；同批 Fact 不得作为正式 Inference 前提。
