---
id: SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS
kind: system-contract
status: current
authority: normative
owners: [knowledge]
depends_on: [SYS-CONTRACT-KNOWLEDGE-ENTITY, SYS-CONTRACT-KNOWLEDGE-FACT, SYS-CONTRACT-KNOWLEDGE-SNAPSHOT-PUBLICATION, SYS-CONTRACT-KNOWLEDGE-JAVA-STATIC-CALL-MODEL, SYS-CONTRACT-SOURCE-ARTIFACT]
code: [src/software_world_model/knowledge_engine, src/software_world_model/application_services]
tests: [tests]
---

# Java Source Semantics

## Purpose and scope

`JAVA_SOURCE_SEMANTICS@1` 在 exact Local Git Java revision 上发布声明、保持原义的静态直接调用，以及可由冻结 frontend 和
语义投影机械确认的方法实现事实。它描述源码语义，不描述 JVM 某次执行、动态分派结果、依赖注入、反射目标、并发时序、
数据库真实状态或设计动机。

该 Profile 使用新的 SYSTEM Scope 与初始 Schema `JAVA-SOURCE-SEMANTICS@1.0.0`；当前系统不在已有 Maven 或
`JAVA_STATIC_CALL_GRAPH@1` Scope 上执行跨 Schema Adoption。它必须重建此前接受的 `JAVA_TYPE`、`JAVA_METHOD`、
`DECLARES_METHOD / JAVA_SOURCE_DECLARATION@1` 与 `CALLS / JAVA_SOURCE_STATIC_CALL@1`，但不得改变这些对象的命题含义。

## Frozen frontend boundary

每次 Build Attempt 固定 frontend ref、runtime、language grammar、ABI、license、离线 runtime fileset digest 与
canonical projection version。初始 frontend 为 `TREE_SITTER_JAVA_FRONTEND@1`：`tree-sitter==0.25.2`、
`tree-sitter-java==0.23.5`、Java language ABI `14`，两者均按随 artifact 保存的 MIT license 使用。Attempt 在解析前重算
fileset digest；版本、ABI、artifact 或 grammar 漂移均拒绝 Candidate，不能回退到 ITER-006 的手写 parser。

Frontend 只拥有确定语法树和 byte range，不拥有正式语义。Knowledge Candidate Generator 必须从 exact source bytes 独立形成
canonical projection；独立 Oracle 以另一解析实现或人工冻结的精确期望核对 node identity、range、nesting 与 source order。
存在 parse error、缺失 node range、非 UTF-8、symlink、truncation 或 Source manifest 漂移时，整个 Candidate 失败关闭。

## Formal model

### Stable entities

- `JAVA_TYPE` 与 `JAVA_METHOD` 沿用 Java Static Call Model 的 canonical external key；新 Scope 只改变 owning Scope，不改变
  type/method key 的定义。
- `JAVA_IMPLEMENTATION_ATOM` Root 由 owning Scope、method Root、atom kind 与该方法 canonical syntax projection 中的
  structural ordinal 形成。ordinal 不含 Git revision、path、byte range、显示文本或 Evidence；源码结构变化可以形成新的 Atom
  Root，不能以名称相似猜测 continuity。
- `JAVA_STATE_SLOT` Root 由 owning Scope、declaring method/type Root、slot kind、canonical identifier 与 declaration ordinal
  形成。它只表示源码中的 parameter/local/field slot，不表示运行时对象或值。

`JAVA_IMPLEMENTATION_ATOM` 的 State 只允许以下 atom kind：`BRANCH`、`CALL_SITE`、`RETURN`、`THROW`、`CATCH`、
`FINALLY`、`STATE_READ`、`STATE_WRITE`。State 固定 source revision、source-order ordinal、必要的 typed operator/value category、
referenced Entity Root、method disposition 与 Support refs。任意源码片段、通用 expression 字符串或 parser node payload 不得进入
State。

### Relations and modalities

- `HAS_IMPLEMENTATION_ATOM / JAVA_SOURCE_IMPLEMENTATION_MEMBERSHIP@1`：`JAVA_METHOD → JAVA_IMPLEMENTATION_ATOM`。
- `CONTROLS / JAVA_SOURCE_TRUE_BRANCH_CONTROL@1` 与
  `CONTROLS / JAVA_SOURCE_FALSE_BRANCH_CONTROL@1`：`BRANCH →` 被对应 lexical branch 控制的 Atom；不声称运行时一定执行。
- `NEXT_IN_SOURCE / JAVA_SOURCE_ORDER@1`：同一方法中相邻的 canonical Atom；只表达源码顺序，不表达所有控制流路径或 happens-before。
- `CALL_SITE_TARGETS / JAVA_SOURCE_CALL_SITE_TARGET@1`：`CALL_SITE → JAVA_METHOD`，State 必须记录 frozen resolution class。
  该关系不是 `CALLS`，也不能被聚合或改名为 `CALLS`。
- `READS_STATE / JAVA_SOURCE_STATE_READ@1` 与 `WRITES_STATE / JAVA_SOURCE_STATE_WRITE@1`：对应 Atom → `JAVA_STATE_SLOT`；
  只表达语法可确认的读取或赋值，不表达运行时值。
- `HANDLES_THROW / JAVA_SOURCE_LEXICAL_EXCEPTION_HANDLER@1`：`CATCH → THROW/CALL_SITE` 仅在 source type 与 lexical handler
  可机械关联时形成；它不证明运行时异常一定发生或一定被该 handler 捕获。

每个 `CALL_SITE` 若满足 `JAVA_SOURCE_STATIC_CALL@1` 的旧 exact receiver/name/arity 规则，仍可同时支持 caller method → callee
method 的 `CALLS` Fact；旧关系的 endpoint、方向、call-site count 与 modality 完全不变。variable receiver、inheritance 或其他
新解析结果只能形成 `CALL_SITE_TARGETS` 及其新 modality，不能扩大 `CALLS` Coverage。对旧 Profile 合法的同一 source closure，
新生成器重建的 declaration/`CALLS` canonical closure 必须先显式归一化掉新 owning Scope、Schema/Context 与由此派生的 ID，
再按 canonical type/method external key、predicate/modality、caller→callee 方向、call-site count、source revision 与 Evidence byte
locator/digest 逐项和 accepted Oracle 一致。新 Scope 下的 raw Root/State/Support ID 必然不同，不能把 ID 相等作为一致性条件。

### Typed condition, return and throw values

`BRANCH` condition 只接受冻结 allowlist 中的 semantic form：boolean slot test、null test、typed scalar comparison、logical NOT，
以及由这些 form 组成且有固定预算的 AND/OR。operand 只能是 `JAVA_STATE_SLOT`/Entity Ref 或 typed boolean/null/integer/enum
literal；不得保存原始表达式、任意字符串 literal、token 序列或未知 operator。不能无损投影的条件使相关方法不具备
`SEMANTICS_COMPLETE`。

`RETURN` 只保存 `VOID`、slot/entity ref 或 allowlisted typed boolean/null/integer/enum outcome；`THROW` 只保存可静态确认的
exception type ref、constructor arity 和 rethrow ref。message、任意 constructor argument expression 和 stack/runtime 信息不进入
Bundle。正向事实只能陈述保存的 typed outcome，不得从省略字段推导值。

## Disposition and coverage

每个授权 `.java` 文件、type 和 method 都必须在同一 Coverage State 的 disposition manifest 中恰好出现一次：

- `SEMANTICS_COMPLETE`：该单元在 Profile 支持闭包内全部分类，所有目标 Atom/Relation、source order 与 Support 完整；
- `UNSUPPORTED_EXCLUDED`：source 可解析且已精确识别不支持 construct；可以发布逐项有 Support 的正向事实，但不得从缺边、缺 Atom
  或缺 outcome 作否定结论；
- `FAILED`：exact source 已读取但 canonical semantic projection 失败；除声明和独立成立的旧语义外不发布实现事实，只返回明确
  Limitation。Source/Artifact/manifest/tamper 失败不允许降级为本 disposition，而是拒绝整个 Candidate。

全局 `CoverageCompleteness.COMPLETE` 只表示 source member manifest 与 disposition manifest 对全部授权单元完整、无遗漏或重复，
不表示所有 method 都是 `SEMANTICS_COMPLETE`。方法 State 还必须分别记录 declaration、legacy static-call 与 implementation
semantics facet 的 completeness。只有相应 facet 为 COMPLETE 才能支持“没有分支/调用/return/throw/state access”等闭世界结论；
其他方法只能使用已发布正向事实并同时披露 Limitation。

更新使用 `REPLACE_COVERAGE`。任何 disposition/member/support 丢失、重复、越界，或 publication 前对 Candidate 执行的旧
`CALLS` consistency Oracle 失败，都拒绝新 Snapshot 并保持旧 CURRENT。Snapshot committed 后，Bundle seal 对同一 normalized
closure 再执行 consistency Oracle；此时失败不回滚 Snapshot，而是保持该 Snapshot `READ_BUNDLE_UNAVAILABLE`。两道 Gate 的输入
与 failure 时序不得混用。

## No-payload Bundle boundary

Snapshot Read Bundle 只允许 Entity/Fact Root 与 State、上述 enum/operator/literal allowlist、canonical identifier/token index、
disposition/facet completeness、Support ref/digest、source revision 和 byte locator。它明确禁止：

- raw source、method/class body、comment、Javadoc、string/text-block content；
- lexer token stream、whitespace/punctuation stream、parser node dump、通用 AST/CST 或可逆的完整表达式树；
- Artifact/Evidence observation payload、任意 expression/source snippet 字段；
- 为工程、问题或 held-out suite 添加的别名、答案、关键词或标签。

信息保持 Oracle 必须只从允许字段重建冻结目标 claim，并证明 condition/call/order/return/throw/state 所需事实仍在；信息越界 Oracle
必须先按 exact schema、typed value 和预算 allowlist 拒绝未知字段，再递归扫描 keys/values 与常见可逆编码，证明 Bundle 不能还原
exact source bytes、lexeme/token/punctuation/comment stream、parser node tree 或被省略的任意表达式。Typed atoms 本来就用于重建
语义等价的解释或伪代码 skeleton；这种受 allowlist 和 Support 约束的语义重述不是 raw Source/AST payload，也不能被误报为可逆性
失败。任一 Oracle 未通过时 Bundle 为 `READ_BUNDLE_UNAVAILABLE`，不能由问答请求临时放宽或重新生成。

## Failure and implementation boundary

未知 syntax/semantic form、预算超限、ambiguous resolution、Evidence range 不闭合或 completeness 无法证明时，只能按上述 disposition
或整个 Candidate failure 处理。DTO、enum 数值、预算、canonical digest 和错误码由代码与测试定义，但不得改变本 Contract 的
命题、旧 `CALLS` 边界、per-method negative rule 或 no-payload allowlist。
