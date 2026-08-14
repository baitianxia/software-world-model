---
id: SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY
kind: system-contract
status: current
authority: normative
owners: [application]
depends_on: [SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS, SYS-ADR-005]
code: [src/software_world_model/application_services, src/software_world_model/interface]
tests: [tests]
---

# Java Implementation Query

## Purpose and scope

本 Contract 为 `JAVA_SOURCE_SEMANTICS@1` 注册两个通用只读操作，使自由功能描述可以先发现正式方法知识，再读取方法实现语义。
操作只读取 exact Snapshot Read Bundle；它们不访问 Source、Artifact/Evidence payload、权威数据库、模型记忆或 Direct
Investigation，也不创建新的 Fact。

## Pregenerated feature index

Knowledge Update 在零问题状态随 Snapshot 形成 `JAVA_IMPLEMENTATION_FEATURE_INDEX@1`。每个 index entry 绑定一个 exact
`JAVA_METHOD` Root/State，只能由下列正式字段机械生成：package/type/method/parameter/return identifier tokens、declared state-slot
identifier tokens、typed branch/operator categories、callee method/type tokens、return category 和 exception type tokens。评论、字符串
literal、源码片段、问题、suite、模型输出、工程专用 synonym 或人工答案均禁止进入 index。

identifier tokenization 固定为 NFC → camel/snake/digit boundary split → Unicode casefold → 去空；保留 canonical token 与来源字段。
Query search term 使用同一 normalization，不做隐藏 stemming、embedding 或工程词典扩展。每个匹配必须返回产生 token 的 Entity/Fact
与 Support ref；index 可以缓存，但必须从 exact Bundle 重建且不能成为第二权威。

## Operations

### `implementation_candidates(search_terms, limit)`

- `search_terms` 是 Planner 从原问题提出、平台验证的 1—12 个非空通用检索词；不得包含 Scope 外部 Ref 或隐藏 operation。
- `limit` 为 1—20；查询必须扫描 exact index，而不是按工程、commit、问题文本或枚举题型分支。
- 结果按 `matched unique normalized term count`、`matched field-class count`、`SEMANTICS_COMPLETE` 优先级降序，再按 canonical
  method signature 与 Root ID 升序稳定排序。排名只能组织候选，不能把高分候选变成已证明的唯一答案。
- 每个 candidate 返回 typed method Ref、matched terms/field classes、disposition/facet completeness、Support Map 与 exact Snapshot/
  Bundle digest。零候选形成明确 Knowledge Gap；多个候选保持集合，调用方必须读取足够候选或披露歧义，不能静默猜选。

用户问题不含 class、method 或 signature 时仍走相同 operation；Planner 可以把业务描述提议为 source-like feature terms，但平台和
Query 不得根据已知题目替换答案。问题措辞改变只允许改变 validated search terms，不得改变 operation 实现或 index 内容。

### `method_implementation(method_ref)`

- `method_ref` 只能是用户提供并在同一 Session 精确解析的 Ref，或该 Session 已密封的 `implementation_candidates` result 中的 Ref；
  名称字符串不能绕过 Ref validation。
- 结果返回 exact method State、disposition/facet completeness、ordered implementation atoms、branch control、call-site target、
  state read/write、return/throw/catch/finally facts、保持原义的 `CALLS` relation 和逐 claim Support Map。
- 返回顺序固定为 source-order ordinal + Atom Root ID；关系方向按各自 Contract 返回。`CALLS` 的 incoming 与 outgoing 必须由显式
  direction 参数或独立通用图操作选择，不能从中文/英文“谁调用谁”猜反。
- 非 `SEMANTICS_COMPLETE` 方法可以返回已支持的正向事实，但必须返回 method Limitation；只有 COMPLETE facet 可形成负向或穷尽
  claim。`FAILED` 不得被展示为空实现。

## Composition and sufficiency

一个功能问题可以先执行一次或多次 candidate search，再对选中的 typed candidates 执行实现查询，并与 method inventory、direct
neighborhood、path 或 ordered diff 组合。每个 Requirement Need 必须保存其 operation inputs/result digest；跨域答案必须在同一
Need/Support chain 中同时引用旧 `CALLS` 与实现事实，不能仅在正文拼接两段互不约束的结果。

Query Result 必须区分 `SUPPORTED`、`KNOWLEDGE_GAP`、`ENTITY_RESOLUTION_LIMITATION`、`METHOD_SEMANTICS_LIMITATION` 与
`EXECUTION_FAILURE`。只有第一项可满足 Need；Gap/Limitations 不计作 supported answer，执行或权限失败不能伪装成 Gap。

## Failure and implementation boundary

未知 operation、term/limit 越界、index/Bundle digest 漂移、unsupported profile、Ref 不属于 Session、分页不完整、Support 越界或
排序不确定均失败关闭。数据结构、缓存和检索实现由代码与测试定义；不得新增题型 enum、工程特判、模型直查 Bundle 或 Source
fallback 来改变以上行为。
