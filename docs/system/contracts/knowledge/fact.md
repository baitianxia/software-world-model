---
id: SYS-CONTRACT-KNOWLEDGE-FACT
kind: system-contract
status: current
authority: normative
owners: [knowledge]
depends_on: [SYS-CONTRACT-KNOWLEDGE-EVIDENCE, SYS-CONTRACT-KNOWLEDGE-ENTITY, SYS-CONTRACT-KNOWLEDGE-CONTEXT-COMPARISON]
derived_from: [DD-KNW-FACT]
code: [src/software_world_model/knowledge_engine/formal.py]
tests: [tests/test_formal_knowledge.py]
---

# Fact

## Purpose and scope

Fact 是在明确 Context 下由直接 Evidence 完整复核的命题，不是脱离版本和观察方式的绝对真相。Fact 与 Inference 按支持关系区分，而不是按生成者或模型是否参与区分。

## Owner and public contract

Knowledge Engine 拥有 Fact Root、Candidate、Support 与 Snapshot State。Fact 分为 Literal Fact 和 Relation Fact；调用方只能使用已发布 ASSERTED Fact，Candidate 不得进入生产读取。

## Invariants

1. Observation modality 是 Proposition 的组成部分；所有用户可见语义必须显式进入命题，不能藏在标签或 Evidence 摘要中。
2. 命题的每条实质语义路径必须由合法 Support Set 覆盖；相关 Evidence 不等于蕴含。
3. Evidence Link 明确 relation 与 coverage；多 Evidence 只按声明的 composition 共同支持。
4. Context 不得由 Evidence 或答案扩张；跨 Context 使用需要有效 Assessment。
5. 互斥观察可以同时存在；是否构成 Conflict 由受控 Inference 单独证明。
6. Root/State 分离。Relation Fact Root 由 owning Scope、Fact type/schema、subject Root、predicate、object Root 与稳定 modality 构成；Literal Fact Root 由同类稳定字段和规范化 literal proposition 构成。Context revision、Evidence、locator、review 与 Snapshot membership 属于 State/Support，不进入 Root ID。历史 Snapshot 不因新观察改写。
7. Candidate、Verifier Proposal 和未发布 State 都不是正式知识。
8. 直接 Evidence 与 Fact 属于同一 owning Scope；跨 Scope 只能使用 exact upstream Entity / formal references，并登记对应 Snapshot dependency。
9. Candidate 只能引用已发布 Entity，或同一原子 Closure 内等待最终替换的 Entity local reference；裸 ID、任意 Candidate 和动态 `CURRENT` 不构成合法引用。
10. 当独立审核确认一个 Fact Candidate 对特定 Requirement Need 的适用性时，该 Need 绑定是审核结果的一部分，必须随正式记录保存并可重建；后续读取方不得用词汇相似度猜测、扩大或跨 Need 借用该绑定。旧记录没有可证明绑定时保持空绑定。
11. Literal Fact 必须有 typed literal object；Relation Fact 必须有 typed subject EntityRef 和 object EntityRef，二者不可混用。关系两个端点必须属于目标 Snapshot Closure 或 Manifest 固定的 exact upstream Snapshot。
12. 公共查询和持久化往返必须保留 Fact kind、两个 EntityRef、predicate、Root/State ID、Context 与 Support；把关系降成 `object_value`、显示文本或名称匹配不符合契约。

## Failure and implementation boundary

Support 不完整、Evidence 越界、modality 缺失、Context 漂移、悬空/歧义 EntityRef 或 Candidate 重复/冲突均保持非正式。Fact Type、Literal Schema、Relation Schema、canonical key、composition 与状态由代码和测试定义。
