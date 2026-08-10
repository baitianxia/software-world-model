---
id: SYS-CONTRACT-KNOWLEDGE-ENTITY
kind: system-contract
status: current
authority: normative
owners: [knowledge]
depends_on: [SYS-CONTRACT-KNOWLEDGE-EVIDENCE, SYS-CONTRACT-KNOWLEDGE-CONTEXT-COMPARISON]
derived_from: [DD-KNW-ENTITY]
code: [src/software_world_model/knowledge_engine/formal.py]
tests: [tests/test_formal_knowledge.py]
---

# Entity

## Purpose and scope

Entity 为软件世界中的对象提供稳定身份和引用锚点。Entity 不承载可变化的属性或关系；这些语义由 Fact 或 Inference 表达。

## Owner and public contract

Knowledge Engine 拥有 Entity Root、Snapshot State 与 Resolution。模型和 Provider 可以提出 Mention/Candidate，但不能创建、合并或重绑正式身份。

## Invariants

1. 每个 Entity 属于一个 Knowledge Scope。Root ID 只由 owning Scope、Entity type/category、identity scheme version 与 canonical external key 形成；不包含 Snapshot、显示名、路径、Revision、State Context、Anchor、Evidence 或模型身份。
2. Category 与 Origin 正交；来源发现不自动决定领域分类。
3. Source-backed 身份必须有 Evidence、Mention 和 Anchor；无法安全解析时保持 unresolved。
4. Resolution 只有 link、create 或 unresolved。link 只能指向 exact published base Snapshot 中的 Entity，或同 Scope、带成功 Publication Proof 的 continuity Root；不能链接任意历史 State、Candidate 或动态 `CURRENT`。跨 Scope 只允许 exact read-only Reference，且不创建本地 State / Anchor。
5. 新稳定 ID 只在最终发布成功时分配；失败 Candidate 不消耗正式身份。
6. 重命名或移动必须有 continuity 证明，名称相同不证明同一对象。
7. Root 与 Snapshot State 分离。同一 Snapshot 至多包含一个 Entity State；State 承载该 Snapshot 下的 label、path、version、revision-bound Context、Anchor 和 Evidence。外部 key 未变时这些 State 变化不得生成新 Root。
8. 跨 Context 聚合只有在机械相等或有效 Comparison Assessment 支持时成立。
9. 唯一性语义固定 owning Scope、identity scheme、canonical external key、稳定命名空间 Context 与 canonicalizer / contract version；所谓 identity-bearing Context 只能包含跨 Snapshot 稳定的命名空间，不能把 Git revision 或 Evidence 身份带入 Root。实现升级不能自然放行重复 Root。

## Failure and implementation boundary

高风险歧义、Anchor 冲突、Context 不可比或跨 Scope 写入均拒绝。Mention/Anchor/Candidate/State 字段、解析算法、风险阈值和错误码由代码、Schema 与测试定义。
