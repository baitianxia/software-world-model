---
id: SYS-CONTRACT-KNOWLEDGE-INDEX
kind: system-contract-index
status: current
authority: normative
owners: [knowledge]
depends_on: [SYS-CONTRACT-INDEX]
code: [src/software_world_model/knowledge_engine]
tests: [tests/test_formal_knowledge.py, tests/test_knowledge_scope.py]
---

# Knowledge Contracts

Knowledge Engine 是正式知识的唯一写者。其 Contract 按归属与上下文、认识论对象、准入发布和持久化分层：

- [Knowledge Scope](knowledge-scope.md)、[Reference Context](reference-context.md)、[Schema Core](schema-core.md)、[Context Comparison](context-comparison.md)
- [Evidence](evidence.md)、[Entity](entity.md)、[Fact](fact.md)、[Structure Model](structure-model.md)、[Java Static Call Model](java-static-call-model.md)、[Inference & Conflict](inference-conflict.md)
- [Admission](admission.md)、[Snapshot Publication](snapshot-publication.md)、[Persistence](persistence.md)

字段和存储 Schema 由生产代码定义；本目录拥有跨模块语义。
