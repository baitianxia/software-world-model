---
id: SYS-CONTRACT-APPLICATION-BEHAVIOR-VIEW
kind: system-contract
status: current
authority: normative
owners: [application]
depends_on: [SYS-ADR-005, SYS-ADR-014, SYS-CONTRACT-KNOWLEDGE-JAVA-STATIC-CALL-MODEL, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE]
code: [src/software_world_model/application_services/structure_view.py, src/software_world_model/application_services/citation_projection.py, src/software_world_model/interface/structure_view_cli.py, src/software_world_model/interface/world_model_product.py]
tests: [tests/test_behavior_view.py, tests/test_world_model_product.py, tests/test_citation_projector.py]
---

# Java Static Call Behavior View

## Purpose and scope

Behavior View 是 exact `JAVA_STATIC_CALL_GRAPH@1` Snapshot 的可重建只读组织。它提供 type/method candidate resolution、类型的
方法 inventory、方法直接调用邻域、静态调用路径和有序 Snapshot diff；不拥有知识、不读取 Source、不重新解析 Java，也不
决定任意 Requirement 是否充分。

“Behavior” 在本契约中仅是源码静态调用子集的产品组织名，不表示完整程序行为。运行时 dispatch、反射、framework wiring、
调用次数/顺序、条件可达性、数据流、异常和业务意图仍在 Coverage 外。

## Input and output contract

View 只接受已验证的 exact no-payload Snapshot Bundle / ordered Read Set。除通用 `entity_candidates`、`direct_neighborhood`、
`all_simple_paths` 和 `ordered_snapshot_diff` 外，增加 `declared_method_inventory`：输入同一 Read Session 的 typed
`JAVA_TYPE` argument，只沿 `DECLARES_METHOD / JAVA_SOURCE_DECLARATION@1` 返回全部 `JAVA_METHOD`，按 canonical signature
排序。

调用邻域和路径必须显式选择 `CALLS`，输出同时携带 `JAVA_SOURCE_STATIC_CALL@1`。每个 Result 固定 operation inputs、exact
Snapshot/Bundle/Profile/Coverage、typed Root/State、completeness、truncation、Support Map、Evidence allowlist 与 digest。
方法公开显示引用为 `fully.qualified.Type#method(parameterTypes)`；显示引用不替代 typed Root。

Entity candidate lookup 只匹配 Snapshot State 的公开 identity/display 字段：type fully-qualified/simple name，method full
signature、declaring type、method name。只有 exact Ref 或同一 Session 中密封的唯一 candidate 可进入后续 operation；仅方法名
命中多个 overload 必须返回 Resolution Limitation。

## Invariants

1. View 不能访问 Repository、Source、SQLite、Evidence payload、模型会话或更新 Port；Citation 仍由密封 Result 后的独立
   Broker/Projector 路径提供，正文不回流 Answer worker。
2. View 只能遍历已发布 typed Relation Fact，不按名称、arity、文件顺序或问题文本补边。
3. 零邻居/零路径只有在 exact Coverage COMPLETE、query 未截断且 predicate/modality 被覆盖时才支持本 Profile 范围内的否定。
4. `READY` 只表示投影可读；Coverage 外需求由 Knowledge Use 判为 Gap，访问/Schema/Bundle 失败是 Limitation/Failure。
5. Maven Structure 与 Java Behavior Profile 使用相同通用 View kernel 时仍必须保留各自允许的 entity/predicate/modalities；不支持
   混合 Profile Read Set，也不能让 enum 扩展改变旧 Maven Result。
6. ordered diff 只比较相邻、Context-compatible、同 Scope、同 exact Schema/Profile 的 caller-declared base→target Pair，并
   区分 Root added/removed 与 State changed。

## Failure and implementation boundary

Profile/Schema 不匹配、typed endpoint 不闭合、0/N candidate 被用作 argument、Support 不完整、预算耗尽或 Bundle/Catalog
tamper 均失败关闭。排序、DTO、lexer-independent display formatting 和路径算法由代码测试定义，但不能改变正式静态语义。
