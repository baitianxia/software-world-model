---
id: FINDING-006-001
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-006-SLICE-001, ITER-006-VERIFICATION]
code: [src/software_world_model/knowledge_engine/structure.py]
tests: [tests/test_structure_knowledge.py, tests/test_java_static_call.py]
iteration: ITER-006
classification: local-implementation
disposition: freeze-profile-specific-coverage-members-explicitly
target: src/software_world_model/knowledge_engine/structure.py
---

# FINDING-006-001：通用 enum 扩展会隐式改变旧 Maven Coverage

## Observation

加入 `JAVA_TYPE/JAVA_METHOD` 与 `DECLARES_METHOD/CALLS` 后，`CoverageRoot.create` 的 Maven 默认 Coverage 仍由
`tuple(EntityType)` 和 `tuple(RelationPredicate)` 形成。这个默认值在旧 enum 只有 Maven 成员时看似正确，但扩展后的进程会把
Java 成员自动写入旧 Maven Coverage Root，并改变 Root identity；Maven Admission 随后也会把扩展后的 enum 全集误当成旧
Profile 的完整集合。

## Evidence

- baseline 的同一默认参数在 enum 扩展前只含 `SOFTWARE_SYSTEM/MAVEN_MODULE` 与 `CONTAINS_MODULE/DEPENDS_ON`；加入 Java
  成员后，未修正实现会把四个新成员一并纳入；
- 既有 Maven knowledge/publication/read/view 回归在完整套件中暴露 Profile/Coverage 不一致，而 Java-only 测试不能证明旧
  Profile identity 未漂移；
- `tests.test_structure_knowledge.StructureKnowledgeTests.test_default_maven_coverage_is_not_derived_from_generic_enum_members`
  直接固定 Maven 默认集合，并明确断言 `JAVA_TYPE` 与 `CALLS` 不得出现；
- 修正后的 Java/knowledge/product 聚焦集合 25/25 PASS，最终完整套件 812/812 PASS。

## Impact and classification

现有 Snapshot/Coverage Contract 和本轮 Slice 已要求每个 Profile 固定自己的 explicit member set，旧 Maven digest 与语义不得
因通用 enum 扩展改变。问题没有改变 Owner、接口或 System 语义，而是通用 DTO 的默认值没有完整实现既有不变量，因此分类为
`local-implementation`。

## Decision and disposition

`CoverageRoot.create` 的兼容默认值和 Maven Admission expected set 都改为显式的两类 Maven Entity 与两个 Maven Predicate；
Java builder 必须显式传入自己的两类 Entity 与两个 Predicate。以后新增通用 enum 成员不会自动扩大任何已冻结 Profile。

该实现、直接回归和完整套件已经处置本 Finding；System 文档无需另行改变，因为当前契约已经要求 Profile-specific Coverage
以及旧 Maven Result 不受 enum 扩展影响。
