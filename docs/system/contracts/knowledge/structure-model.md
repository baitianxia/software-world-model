---
id: SYS-CONTRACT-KNOWLEDGE-STRUCTURE-MODEL
kind: system-contract
status: current
authority: normative
owners: [knowledge]
depends_on: [SYS-CONTRACT-KNOWLEDGE-ENTITY, SYS-CONTRACT-KNOWLEDGE-FACT, SYS-CONTRACT-KNOWLEDGE-SNAPSHOT-PUBLICATION, SYS-CONTRACT-SOURCE-ARTIFACT]
code: [src/software_world_model/knowledge_engine, src/software_world_model/application_services/knowledge_update.py, src/software_world_model/application_services/maven_structure.py, src/software_world_model/application_services/maven_structure_update.py]
tests: [tests/test_formal_knowledge.py, tests/test_knowledge_update.py, tests/test_structure_knowledge.py, tests/test_maven_structure.py, tests/test_maven_structure_update.py, tests/test_maven_structure_cli.py, tests/test_iteration_003_g1_integration.py]
---

# Structure Model

## Purpose and scope

Structure Model 是正式知识中的可遍历结构关系，不是按显示名称拼接的 UI 图。当前最小产品 Profile 是 `MAVEN_REACTOR_STRUCTURE@1`，采用 `MAVEN-REACTOR-STRUCTURE@1.0.0`，只描述一个 exact Local Git revision 中的 Maven 根项目、递归子项目及其直接内部依赖。每次采用还必须固定 exact Maven Evaluation Context；Git revision 本身不足以决定 effective model。

## Formal shape

- Entity 类型至少包括 `SOFTWARE_SYSTEM` 与 `MAVEN_MODULE`。
- Relation Fact 使用 `subject EntityRef + predicate + object EntityRef`；当前谓词与 observation modality 固定为 `CONTAINS_MODULE / RECURSIVE_REACTOR_MEMBERSHIP@1` 和 `DEPENDS_ON / POM_LOCAL_DECLARED_INTERNAL_DEPENDENCY@1`。
- EntityRef 必须解析到目标 Snapshot 的成员，或其 Manifest 固定的 exact upstream Snapshot。悬空、歧义或按 label/path 猜测的端点必须拒绝。
- View、查询和持久化结果必须保留两个 typed endpoint、Fact Root/State、Context 与 Support Map，不能退化成一段关系文本。

## Maven reactor profile

1. `SOFTWARE_SYSTEM@1` 同时表示本 Profile 的逻辑软件系统和 reactor root `<project>`。Root identity 为 owning System Scope、identity scheme version 与 Scope 创建时固定的 canonical system key。root project 的 effective GAV、Source Binding、仓库路径、label、Git revision、Anchor 和 Evidence 属于 State/Support；同一 Scope 的 A/B revision 必须复用同一 system Root。
2. `MAVEN_MODULE@1` 只表示从 root `<modules>` 递归可达的子项目，不包含 root aggregator 本身。Root identity 为 owning Scope、identity scheme version、规范化 effective `groupId` 与 `artifactId`。`version`、POM 路径、目录、label、Git revision、Anchor 和 Evidence 属于 State 或 Fact，不进入 Root ID。本文和产品输出中的“reactor child modules”均使用这个排除 root 的定义；不得把 root 有时也参与 Maven reactor build 的术语差异带入计数。
3. root `<modules>` 递归闭包中的每个有效子项目形成一条 `SOFTWARE_SYSTEM CONTAINS_MODULE MAVEN_MODULE`；这是扁平的软件系统成员关系，不保留 nested aggregator/parent 层级。路径只用于解析 POM 和 Evidence，不作为模块身份。
4. root project 和每个 child module 自身 POM 的 `<dependencies>` 都必须进入完整性检查。本 Profile 的“直接依赖”固定为该 POM 本地声明，不把 parent `<dependencies>` 继承后重复归到 child；current POM、再到 nearest reactor parent chain 只参与坐标、property 和 dependencyManagement 求值。每项声明先解析 canonical GA：若 GA 不在 reactor child 集合，在不可变 Build/Admission 报告中记录带原因的 profile exclusion，version 不必解析；root project GA 也明确归为不支持的 target exclusion，因为本版 `DEPENDS_ON` object 只允许 `MAVEN_MODULE`。若 GA 命中唯一 child Root，则必须解析 exact version，且规范化 `groupId:artifactId:version` 与目标 State 的 effective GAV 精确相等时才形成内部 `DEPENDS_ON`。方向为 consumer → dependency，consumer 可以是 `SOFTWARE_SYSTEM` 或 `MAVEN_MODULE`。模块 Root 仍按 GA 稳定；version mismatch 表示该依赖不指向当前 reactor child module，并同样进入构建报告。
5. dependency version 可以由 direct declaration、property、parent 或 `dependencyManagement` 解析，但 `dependencyManagement` 条目本身、Maven parent、plugin 和外部/版本不匹配依赖不形成内部 `DEPENDS_ON`。无法得到 exact effective version 时不得按 GA 猜测。
6. 同一 reactor child module 集合出现重复或不可唯一解析的 effective GA/GAV，或同一 POM 重复声明相同 canonical dependency GA 时，本次完整构建失败并保持旧 CURRENT；不能按 artifactId、目录、声明顺序或显示名选择赢家。scope 与 optional 保留在 Fact State；本版只支持缺省/`jar` type 且 classifier 为空，命中 reactor GA 的其他 type/classifier 使完整 Coverage 失败。
7. `MAVEN_MODULE@1` 只有 canonical effective GA 改变才形成新 Entity Root；version、path、label、revision 或 Evidence 改变只形成新 State。模块移动不改变身份；GA 已改变时本版没有 continuity 机制，不能根据旧名称或路径猜测仍是同一 Entity。`SOFTWARE_SYSTEM@1` 仍只由 Scope 中固定的 canonical system key 决定 Root。

## Maven evaluation context

`MAVEN-EVALUATION-CONTEXT@1.0.0` 与 `MAVEN-REACTOR-CANONICALIZATION@1.0.0` 冻结以下确定性子集：不激活 Profile，不读取用户、系统、环境或 Settings properties，不联网解析 external parent/BOM，只沿 current POM 和 reactor parent 文件中的 properties/dependencyManagement 求值。任一 covered POM 的 `<profiles>` 会影响 modules、coordinates、dependencies、dependencyManagement 或被结构求值引用的 property 时，必须拒绝 complete Coverage；version range、命中 reactor GA 却只能靠外部内容解析的 version、必需 GA/坐标未解析、property cycle、重复声明或不支持 type/classifier 同样失败关闭。GA 已证明不属于 reactor 的本地声明可以在 version 未解析时明确排除，不能因此制造内部边或阻止本 Profile 完整。

每个 Coverage Root/State 必须记录 Schema、Evaluation Context 与 Canonicalization 的 exact ref/digest。实现可以使用 Maven library 或自有 parser，但同一 frozen POM bytes 和三个 Definition 必须得到相同 effective structure；不得读取本机 `~/.m2`、环境变量或隐含 active profile 补全结果。

## Coverage and limitations

Profile Coverage Root 由 owning Scope、`MAVEN_REACTOR_STRUCTURE@1`、exact Schema/Evaluation Context/Canonicalization、稳定 Source Binding、逻辑 reactor root locator 和所覆盖类型/谓词形成；A/B revision 共享该 Root，各自形成 exact Coverage State。完整构建覆盖 root project State、全部递归 child module Entity State、root/child `<dependencies>` 的完整扫描、`CONTAINS_MODULE` 和内部 `DEPENDS_ON`。因此只有 Coverage `COMPLETE` 时，内部边的缺席才能支持“没有 POM 本地声明的直接内部依赖”；若 root POM 未扫描，相关问题必须是 Gap，不能回答否。Build/Admission exclusion 报告不是 Snapshot 成员，能审计构建但不能在 Source-off 回答中证明某条声明被排除的具体原因；若产品需要回答该原因，必须先接受新的正式 Schema，而不能读取报告或 Evidence 补洞。未解析 POM、缺失 module、effective GAV/属性解析不完整或权限过滤使完整 State 失败，不能执行 `REPLACE_COVERAGE` 或发布伪完整图。当前 Profile 不表达 aggregator/parent 层级、外部依赖图、effective/传递/compile/runtime 依赖、运行时调用、Behavior、Business 或 History。
