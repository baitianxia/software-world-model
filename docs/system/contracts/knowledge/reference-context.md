---
id: SYS-CONTRACT-KNOWLEDGE-REFERENCE-CONTEXT
kind: system-contract
status: current
authority: normative
owners: [knowledge]
depends_on: [SYS-CONTRACT-KNOWLEDGE-SCOPE, SYS-CONTRACT-SOURCE-ARTIFACT]
derived_from: [DD-KNW-REFERENCE-CONTEXT]
code: [src/software_world_model/knowledge_engine/formal.py, src/software_world_model/infrastructure/sqlite_formal_knowledge_repository.py]
tests: [tests/test_formal_knowledge.py, tests/test_knowledge_use.py]
---

# Reference Context

## Purpose and scope

Context 表达命题成立和引用可解释的条件。Source Context 由 Source Integration 拥有；Knowledge Engine 只能消费其 exact 中立表示来形成 Knowledge Context，不能反向改写 Source Context。Knowledge Context 与正式 Reference 由 Knowledge Engine 拥有。

## Public contract

调用方可以请求解析或比较 Context，但正式对象必须保存 canonical、exact 且不可变的 Context Reference。`CURRENT`/`latest` 仅允许在入口解析一次，持久依赖固定精确结果。

## Invariants

1. Context 是成立条件，不是任意全局标签；未知关系不能强行融合为 compatible。
2. 模型 Comparison Proposal 不是正式 basis，平台必须重建 exact 输入与结论。
3. Reference 必须保持类型边界：Formal Reference family 只指向 exact Scope、Schema、Snapshot 及 Snapshot 中的 Entity、Fact 或 Inference，并为每类对象使用各自的 typed Reference。Source identity 使用 Source Contract 的非正式知识引用；Artifact、Evidence、Candidate、View、Claim、模型文本和可变别名都不能成为 Formal Reference。
4. Context Reference 固定 Scope、Schema 与 canonicalizer，且依赖闭合无环。
5. Context 扩张必须显式证明；来源更广、版本更晚或名字相同都不自动兼容。
6. Revalidation Signal 只触发重新验证，不能直接修改既有结论或 CURRENT。

## Failure and implementation boundary

解析失败、循环、Schema 不匹配和关系未知必须显式返回；不得回退到字符串相等。表达式字段、canonical encoding、Signal Payload 和错误枚举由代码与测试定义。
