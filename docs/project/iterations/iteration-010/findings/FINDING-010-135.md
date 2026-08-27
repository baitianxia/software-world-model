---
id: FINDING-010-135
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [knowledge, application, source, quality, project]
depends_on: [FINDING-010-014, FINDING-010-134]
code: [src/software_world_model/application_services/java_source_semantics.py]
tests: [tests/test_java_source_semantics.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: preserve-positive-facts-with-complete-unit-dispositions
target: SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS
---

# FINDING-010-135：通用 Java 正向事实不能因窄 legacy closure 失败而整包丢失

## Observation

已接受的 `JAVA_SOURCE_SEMANTICS@1` evaluator 先要求整个 source closure 落入 ITER-006 的窄 class/method-body 子集。exact
`mall-admin@0504e86b…` 的普通 annotation、field、framework method body 等 construct 在第一个不支持成员处终止，尽管 current System
Contract 已要求 parseable unsupported unit 使用 `UNSUPPORTED_EXCLUDED`，并允许逐项发布有 Support 的正向事实。

同一 source root 有 153 个 `.java` 文件、154 个具备 canonical external key 的 named top-level/member type 和 559 个 member method；
冻结 frontend 全部 parse clean。语法树还包含 constructor、4 个 annotation element 和 anonymous class 中的一个 nested method body，现有
`JAVA_TYPE/JAVA_METHOD` external key 不能无损表示这些单元。把 nested executable 中的调用归到外层 method 会形成错误正向事实，伪造匿名
type/method identity也会改变正式模型。

## Evidence

- exact revision 的通用 disposition path 形成 153 file、154 type、559 method 的完整 representable-unit manifest，全部明确为
  `UNSUPPORTED_EXCLUDED`；发布 48 个 `CALL_SITE`、48 个 `CALL_SITE_TARGETS` 和 26 个 `NEXT_IN_SOURCE`，不发布新的 `CALLS`；
- sealed Snapshot `structure_snapshot_30c29cee2db34077b5f2123c82fa7323` / Bundle
  `sha256:dd3d7e97d64fe158fe0596bf9784ae73abfdf6f65194b5ac83643bd59ca14744` 为 `QUERYABLE`，含 914 Entity、681 Relation、0 Literal；
- `login → loadUserByUsername`、`login → insertLoginLog`、`insertLoginLog → getAdminByUsername` 等关系由 exact method/atom identity 与
  no-payload Evidence metadata 支持；空边或缺 Atom 仍不能形成否定结论；
- 定向测试覆盖 annotation/field、nested enum member、anonymous executable boundary、wildcard-import type namespace、parse failure、
  legacy fixture exact closure 与 no-payload Bundle；直接的 legacy filename mismatch、parse、tamper、manifest/authority failure 不进入
  disposition fallback，未解析 wildcard/type-variable simple name 也不会伪造 declaring-package qualification。

## Decision and disposition

该发现处置到 `SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS`：

- legacy-complete closure 继续是唯一可以重建旧 `CALLS` 的路径，其既有外部语义不变；
- parseable 但超出 closure 的 source 使用完整 file/type/method disposition manifest，只发布 `this`/unqualified、同 declaring type、
  name+arity 唯一解析的正向 call-site fact；所有相关 method 的 legacy/implementation facet 保持 `INCOMPLETE`；
- nested anonymous/local/lambda executable boundary 不被遍历为外层 method 事实；constructor、annotation element 与没有 canonical external
  key 的 nested executable 不生成合成 Root，而使最近可表示单元保持 `UNSUPPORTED_EXCLUDED`；
- global Coverage `COMPLETE` 只证明 866 个可表示 source unit 的分类 manifest 完整，不把 559 个 method 追认为语义完整，也不支持负向推断。
