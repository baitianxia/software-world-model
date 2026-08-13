---
id: SYS-CONTRACT-KNOWLEDGE-JAVA-STATIC-CALL-MODEL
kind: system-contract
status: current
authority: normative
owners: [knowledge]
depends_on: [SYS-CONTRACT-KNOWLEDGE-ENTITY, SYS-CONTRACT-KNOWLEDGE-FACT, SYS-CONTRACT-KNOWLEDGE-SNAPSHOT-PUBLICATION, SYS-CONTRACT-SOURCE-ARTIFACT]
code: [src/software_world_model/knowledge_engine/structure.py, src/software_world_model/application_services/java_static_call.py, src/software_world_model/application_services/maven_structure_update.py]
tests: [tests/test_java_static_call.py, tests/test_java_static_call_update.py]
---

# Java Static Call Model

## Purpose and scope

`JAVA_STATIC_CALL_GRAPH@1` 把一个 exact Local Git revision 中、配置 source root 下的受支持 Java 类型、方法声明和可由冻结
Profile 唯一解析的源码级直接调用形成正式知识。它只描述语法和本 Profile 的静态解析结果，不描述 JVM 实际执行、动态分派、
依赖注入、反射、数据流、异常流或业务行为。

该 Profile 使用 exact Schema `JAVA-STATIC-CALL-GRAPH@1.0.0`、Evaluation Context
`JAVA-STATIC-CALL-EVALUATION-CONTEXT@1.0.0` 与 Canonicalization
`JAVA-STATIC-CALL-CANONICALIZATION@1.0.0`。它只可在没有 CURRENT 的新 SYSTEM Scope 初始采用；当前系统仍不支持已有
Scope 的跨 Schema Adoption。

## Formal shape

- `JAVA_TYPE` Root identity 为 owning Scope + `JAVA_TYPE@1` + NFC 规范化 fully-qualified name。State 保存 simple/package
  name、`CLASS` declaration kind、source path、source revision 与 Evidence refs。
- `JAVA_METHOD` Root identity 为 owning Scope + `JAVA_METHOD@1` + declaring type fully-qualified name + method name + ordered
  canonical parameter types。State 保存 return type、visibility、sorted modifiers、source path、source revision 与 Evidence refs。
- `DECLARES_METHOD / JAVA_SOURCE_DECLARATION@1` 的 endpoint 为 `JAVA_TYPE → JAVA_METHOD`；State 保存同一类型内的
  zero-based declaration ordinal。
- `CALLS / JAVA_SOURCE_STATIC_CALL@1` 的 endpoint 为 `JAVA_METHOD → JAVA_METHOD`，方向固定 caller → callee；State 保存
  exact source revision、call-site count 和每个 call-site Evidence ref。它表示 Profile 静态唯一解析，不表示某次运行发生调用。
- 所有 Entity/Fact Root 与 State 继续遵守通用 stable Root / revision-bound State、typed endpoint、Evidence、Coverage 和 atomic
  Snapshot Contract；显示名、path、line/byte locator 与 Git revision 不进入 Root identity。

## Frozen source and resolution profile

完整 Candidate 覆盖配置 source root 下 Git tree 中全部 regular, non-symlink UTF-8 `.java` 文件。当前版本只接受每文件一个与
文件名一致的顶层 `class`，以及具有显式返回类型和 block body 的方法；package 必须与 source-root-relative 目录一致。嵌套、
local 或 anonymous type，constructor、initializer block、inheritance、generic method/type、abstract/native method、lambda、method
reference、static import、varargs，以及 parser 无法闭合的 token/brace 都拒绝本次完整构建。

方法参数类型按 source spelling 的 NFC、去冗余空白规则规范化；重载 Root 可以按完整参数列表区分。调用点只接受：

1. `method(args)` 或 `this.method(args)`，目标为同一 declaring type 中 name + arity 唯一的方法；
2. `TypeName.method(args)` 或 fully-qualified `TypeName.method(args)`，receiver 唯一解析到本 source closure 的类型，且目标
   name + arity 唯一。

参数表达式只用于平衡 delimiter 和计算 arity，不推断类型。`super`、变量/字段/表达式接收者、chained invocation、动态
dispatch、潜在内部目标的 0/N resolution 和其他 invocation form 都使 Candidate 失败；不能将其静默排除为外部调用。明确不
指向 in-scope type 的 constructor 或 language keyword 不是本 Profile 的 `CALLS` 命题，但 parser 必须机械区分，不能靠显示名
猜测。

评论、字符/字符串/text block 内容在保持 byte offset 的 lexer 阶段屏蔽，不能产生 Entity、Fact 或 delimiter。每个声明和调用
Evidence 的 `[byte_start, byte_end)` 必须精确对应原 UTF-8 Artifact；line number 只能由 locator 派生展示，不参与身份。

## Coverage and negative conclusions

Coverage Root 固定 owning Scope、Profile/Schema/Evaluation/Canonicalization exact refs+digests、Source Binding、logical Java
source root，以及 covered `JAVA_TYPE/JAVA_METHOD` 与 `DECLARES_METHOD/CALLS` 集合。Coverage State 固定 exact Git revision、
Context、完整 member manifest、所有 Git tree page Evidence 和 member Evidence。

只有全部 source files、声明、delimiter 和 Profile invocation sites 完成分类，且每个潜在内部调用唯一解析时，才可发布
`COMPLETE` Coverage 并用 `REPLACE_COVERAGE` 更新同一 Root。此时边缺席只支持“本 Profile 的 exact Snapshot 中没有静态
唯一解析的直接调用”；不能扩张为运行时从不调用。任何 unreadable/truncated/symlink source、路径/package 不一致、重复 type
或 method signature、未知语法、歧义调用、Evidence/Manifest 缺失都会拒绝整个 Candidate并保持旧 CURRENT。

## Failure and implementation boundary

实现可以替换 lexer/parser，但必须对同一 source bytes 和 frozen definitions 产生相同 canonical closure。错误码、token DTO、
预算和排序由代码与测试定义；不得通过问题文本、工程名或模型输出来补全解析。
