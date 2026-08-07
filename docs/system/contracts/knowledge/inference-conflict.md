---
id: SYS-CONTRACT-KNOWLEDGE-INFERENCE-CONFLICT
kind: system-contract
status: current
authority: normative
owners: [knowledge]
depends_on: [SYS-CONTRACT-KNOWLEDGE-FACT, SYS-CONTRACT-KNOWLEDGE-REFERENCE-CONTEXT]
derived_from: [DD-KNW-INFERENCE-CONFLICT]
code: [src/software_world_model/knowledge_engine/formal.py]
tests: [tests/test_formal_knowledge.py]
---

# Inference 与 Conflict

## Purpose and scope

Inference 从正式前提形成有界结论；Conflict 证明目标对齐、Context 可比且语义不兼容。它们保存结构化论证，不保存模型 Chain of Thought。

## Owner and public contract

Knowledge Engine 拥有 Inference、Argument、Dependency 与 Conflict State。模型可以提出候选论证，Verifier 与平台重建前提闭包和结论。

## Invariants

1. 前提非空、有限、无环，只能是 exact upstream Snapshot 中已发布的 ASSERTED Fact，或已发布 ASSERTED、受控的上游 Inference；同批 Candidate 不作正式前提。
2. 任一 Inference 可展平到 exact Fact-leaf closure，并固定 Context、modality 和全部 upstream Snapshot。
3. Conclusion 的实质语义必须完整表达；confidence 不能代替 modality 或支持证明。
4. Conflict 分别证明目标对齐、Context 可比和语义不兼容，不自动选择赢家或改写前提。
5. 推断型 Entity 与其 derivation Inference 必须形成同一原子发布闭包。
6. 跨 Scope 前提只能引用 exact Snapshot；上游 CURRENT 变化不改写历史 Inference。
7. 深度和搜索属于经评测 Strategy，但永远受有限、无环和预算边界约束。

## Failure and implementation boundary

循环、非正式前提、闭包缺失、Context 不可比、结论扩张或深度超预算均拒绝。Type Catalog、Argument Schema、canonicalization 与状态机由代码、Schema 和测试定义。
