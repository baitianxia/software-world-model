---
id: ROADMAP-CANDIDATE-SCHEMA-EVOLUTION
kind: roadmap-candidate
status: candidate
authority: planning-only
owners: [knowledge, product]
depends_on: [SYS-CONTRACT-KNOWLEDGE-SCHEMA-CORE, SYS-CONTRACT-KNOWLEDGE-SNAPSHOT-PUBLICATION]
code: []
tests: []
coding_input: false
legacy_source: DD-KNW-SCHEMA-EVOLUTION
---

# Candidate：Schema Evolution

## Trigger

只有 Scope 已有 CURRENT Snapshot，且真实产品需求必须采用不同 exact Schema 时才需要 Evolution。`INITIAL` 和 `UNCHANGED` 发布不依赖本能力。

## Proposed boundary

- 不新增独立顶层 Orchestrator；复用 Knowledge Update、Admission 和 Publisher。
- 固定 exact source Snapshot 与 target Schema，建立双向完整的成员 inventory/disposition。
- Migration 结果仍是普通 Candidate，必须经过独立 Admission 和原子 Publication。
- Stable identity continuation 需要逐对象证明；失败保持旧 CURRENT。

## Unknowns

当前没有证明跨 Schema 迁移相对重建的产品价值、真实数据规模、身份延续规则、兼容读取需求或失败恢复成本。旧详细设计仍为 `In Review`，已归档而非提升为现行 Contract。

## Entry conditions

出现不可由重建解决的真实用户场景；冻结 source/target Schema 和迁移 Oracle；证明最小切片能比较迁移与重建；先在 Iteration 中关闭身份、完整性和回滚设计，再考虑接受 System Contract。
