---
id: ITER-007-READINESS
kind: iteration-readiness
status: proposed
authority: project-authorization
owners: [project, architecture, quality]
depends_on: [ITER-007-PROPOSAL, ITER-007-VERIFICATION, ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-LIVE-RUN-008]
code: []
tests: []
iteration: ITER-007
authorized_by: pending
authorized_at: pending
product_goal_alignment_verdict: pending
product_goal_alignment_reviewed_by: pending
product_goal_alignment_review_ref: pending
---

# Iteration 007 Readiness Review

## Reviewed exact inputs

已核对 `project/current.md`、ITER-006 的 Proposal/Manifest/active Slice/Verification、当前 System Contract 及实现。结论是：

- ITER-006 技术 Product Validation 已 PASS，但仍无最终用户 Acceptance；
- `JAVA_STATIC_CALL_GRAPH@1` 只有声明和有限静态 `CALLS`，没有方法体实现语义；
- `_analyze_java()` 和 `ProductNeedKind` 只覆盖固定路由；
- 当前手写 parser 不足以覆盖常见 Java；
- Runtime/Gateway 资格按当前每题一次模型调用设计；
- Knowledge Coverage 只有全局 COMPLETE，不能直接假设新 Profile 可发布 PARTIAL；
- 新 Profile 还会影响 Authority、Workspace、Bundle/Catalog、Persistence、CLI/HTTP/Web、Citation 和模型能力资格，不只是新增一个 View。

## Product-goal alignment gate

本 Proposal 的 Outcome 是同一正式 Web 上的 Java 源码实现问答，并要求“不点名类/方法”的功能描述也能从预构建世界模型发现相关
代码。它通过三段式计划把首次真实 Web 提前到最小端到端闭包，随后才做可见语料加固，最后才执行未参与实现工程的隐藏评测。

当前结论仍为 **NOT READY**。以下项目全部是编码授权前的阻断项。

## Outcome, scope and non-goals

Outcome 是让用户在同一正式 Web 以自由业务描述定位相关 Java 实现，并组合旧静态调用与新条件、状态、返回和异常事实回答。
范围只含受控 Java/Maven 源码；README、配置、运行数据、多语言、动态分派和设计意图均不在本轮。三个 Slice 都服务于这一共同
Outcome，不以 parser、Schema、View 或测试完成作为独立终点。

## System contracts and unresolved decisions

1. **ITER-006 基线：** 用户最终 Acceptance 和 accepted commit。不得先改上述三项已知限制再沿用 run-008；推荐在 ITER-006
   Acceptance 中诚实缩窄已证明范围并登记限制，把修复和新资格放入 ITER-007 SLICE-001。若选择在 ITER-006 修复，则必须重新
   freeze、资格和 Product Validation 后再接受。
2. **Java frontend：** 固定成熟 parser/frontend 的名称、版本、license、离线获取、canonicalization、最小支持边界和独立 Oracle；
   禁止继续扩张窄手写 lexer。
3. **Source Semantics Contract：** 冻结 condition/branch、state read/write、return、throw/catch、call-site/order 的 typed
   Entity/Fact/Relation、Root/State、modality、Support 和更新规则。
4. **功能到实现发现：** 正式注册 `implementation_candidates` 和 `method_implementation`。前者必须从问题无关形成的 typed formal
   index 返回候选及 Support；不能依赖类/方法名，也不能用工程、题目、关键词分支伪装通用能力。
5. **Coverage：** 采用“全授权单元 disposition 完整 + 每方法 semantic completeness”的小方案，不新增全局 PARTIAL。
   `SEMANTICS_COMPLETE` 才能支持负向/闭世界结论。
6. **no-payload：** 明确可发布 semantic atom allowlist 和禁止项；用信息保持 Oracle 证明目标事实未丢失，用信息越界 Oracle 证明
   Bundle 不包含原始源码、任意表达式文本、token stream 或可逆完整 AST。
7. **旧调用语义：** 新 frontend 不得扩张 `CALLS / JAVA_SOURCE_STATIC_CALL@1`。variable receiver、inheritance 等新增关系使用新
   predicate/modality，并对旧 `CALLS` exact rebuild 做一致性回归。
8. **模型协议：** 修订并接受 exact 三调用协议：Call 1 只提 Requirement/feature search/Query Plan，平台执行正式查询，Call 2 只
   生成 Draft，Call 3 由独立 Reviewer 从原问题重建检查项并核对完整性与可读性；平台确定性校验 schema、typed refs、Support 和
   Authorization。同步冻结失败策略、Gateway workload、Prompt 和操作词汇；能力资格在 SLICE-001 Web 前执行。若三调用仍不满足
   质量契约，必须停止而不是减少 Review。
9. **Owner/持久化：** 新 Schema/Profile 必须逐一覆盖 `structure_authority.py`、`maven_workspace.py`、Bundle/Catalog、SQLite/File
   repositories、runtime/CLI/presenters/HTTP/Web、Citation、egress qualification/policy/workload 和 `pyproject.toml`。
10. **独立评测：** 独立方先分别冻结 SLICE-001/002 的小型真实 Java canary，再冻结最终两份 held-out 工程的身份/源码、12+4
    suite、当前 baseline、target、mature Agent protocol 和 digests。每个 canary 的工程身份、源码和问题在所属 Slice 产品代码冻结前
    对实现方隐藏，并至少含一条可回答的无符号问题；target 至少为 `min(12, max(baseline + 4, 8))`。

上述条件必须落入 Manifest 的 `readiness_inputs`、`source_scope`、`answer_protocol`、`readiness_blocking_case_ids` 和
`early_hidden_canary_bindings`，不能只写在正文。首个 Slice 授权前，所列 System Contract 必须真实存在且为 current normative，
Readiness 必须直接依赖它们；frontend artifact/version/license、Contract 集、双 Oracle、可见语料、canary 和最终隐藏评测的 digest
必须全部冻结。`source_scope.question_or_suite_driven_update_allowed` 必须保持 `false`，由 `V-002/V-006` 验证知识在零问题状态形成和更新。

## Slice, dependency and risk closure

- **SLICE-001：** 可见开发工程上的最小正式链。只支持 `call + if + return + throw`，但必须立刻由真实产品策略和真实模型在正式
  Web 回答一条不含符号名的跨域问题。随后冻结本 Slice 产品代码并执行独立方持有的 `V-CANARY-001` 小型真实 Java canary。
  HTTP probe、deterministic stub、预制答案或 validation-only 页面均不算 PASS；canary 未 PASS 不得授权 SLICE-002。
- **SLICE-002：** 仅使用可见 development/qualification corpus 加固常见 Java、状态/try-catch、R1→R2、重启和持久化；结束时
  再从正式 Web 人工回答至少 5 条自由问题，其中至少 2 条不含符号名。随后冻结本 Slice 产品代码并执行独立方持有的
  `V-CANARY-002` common-Java canary；未 PASS 不得授权 SLICE-003。
- **SLICE-003：** 产品代码冻结后才暴露 held-out 工程给执行环境。若曝光后修改产品代码，必须保留失败并同时更换工程与问题集；
  不能在同一工程上边看失败边调 parser。

两个 canary 的身份、源码和问题在所属 Slice 产品代码冻结前均须对实现方隐藏；曝光后任何产品改动都会烧毁对应 canary，原失败
必须保留，且只能由独立方换全新工程和问题后重试。每个 Slice Result 必须匹配 Manifest 的产品代码冻结、canary project/suite
digest 和披露收据，并证明曝光后产品变更数为 0。canary 不复用为最终 held-out 工程，也不计入最终 12+4 target。

任一 Slice 的 Web/产品/canary Gate 失败都暂停后续 Slice。失败结果必须保留，不能把 parser、Schema 或 View 的局部完成记为
迭代成功。

## Verification readiness

- supported count 的分母仅为 12 条 answerable；诚实 Gap 不算支持；
- 12 条中至少 6 条不含 class/method/signature，且每个工程至少 2 条；
- 4 条 boundary 单独要求 4/4 正确 Gap；若成熟源码 Agent 仅用同一授权 Java 源能回答，则 World Model Gap 是 FAIL；
- 两个工程和功能定位、条件/状态、返回/异常、跨方法调用四类均须有增量；
- 重大错误为零，旧 accepted baseline 不退步；
- 现场 3 问中至少 2 条不含符号名；
- Production Activation 无条件 `NOT_EXECUTED`。

## Authorization decision

**NOT READY / NOT AUTHORIZED。** 当前文件只固定下一轮候选计划。只有 `V-PRE-006` 已绑定 PASS 证据、ITER-006 被接受并冻结三项限制
及其 disposition、上述 Contract/Oracle/模型资格/hidden freeze 全部落地、Manifest 与三个 Slice 的 accepted refs 同步为真实
`ITER-006-RESULT-ACCEPTANCE`，且用户完成 exact Product-goal review 后，才可接受 Proposal/Readiness 并只授权 SLICE-001，再更新
`project/current.md`。
