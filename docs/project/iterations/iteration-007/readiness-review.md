---
id: ITER-007-READINESS
kind: iteration-readiness
status: accepted
authority: project-authorization
owners: [project, architecture, quality]
depends_on: [ITER-007-PROPOSAL, ITER-007-VERIFICATION, ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-ACCEPTANCE, SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE]
code: []
tests: []
iteration: ITER-007
authorized_by: user
authorized_at: 2026-08-13T16:01:15+08:00
product_goal_alignment_verdict: accepted
product_goal_alignment_reviewed_by: user
product_goal_alignment_review_ref: codex-user-message:sha256:68df2434a0e31c7996d57ce124d1e3b309f08705cd7e508537c82dbac4de8147
---

# Iteration 007 Readiness Review

## Reviewed exact inputs

已核对 `project/current.md`、ITER-006 Acceptance、提交 `8f305ed396899c8f8e5d175fe7fcecb6ceb48f3f`、当前 System Contract
及实现。结论是：

- ITER-006 已按 exact run-008 窄范围完成用户 Acceptance；
- `JAVA_STATIC_CALL_GRAPH@1` 只有声明和有限静态 `CALLS`，没有方法体实现语义；
- `_analyze_java()` 和 `ProductNeedKind` 只覆盖固定路由；
- 当前手写 parser 不足以覆盖常见 Java；
- Runtime/Gateway 资格按当前每题一次模型调用设计；
- Knowledge Coverage 只有全局 COMPLETE，不能直接假设新 Profile 可发布 PARTIAL；
- 新 Profile 还会影响 Authority、Workspace、Bundle/Catalog、Persistence、CLI/HTTP/Web、Citation 和模型能力资格，不只是新增一个 View。

## Product-goal alignment gate

本 Proposal 的 Outcome 是同一正式 Web 上的 Java 源码实现问答，并要求“不点名类/方法”的功能描述也能从预构建世界模型发现相关
代码。它通过三段式计划把首次真实 Web 提前到最小端到端闭包，随后才做可见语料加固，最后才执行未参与实现工程的隐藏评测。

当前结论为 **READY FOR SLICE-001**。accepted baseline、frontend、normative Contract 与公开 Readiness Oracle 已闭合。用户
明确选择在产品代码冻结后才现场提问；题目由用户持有并在实现期间不向实现方披露。因此外部存储/runner 和预先提交题库不再是
编码前置条件，但用户现场提问与 Result 绑定仍是完成本 Slice、进入下一 Slice 的阻断项。

## Outcome, scope and non-goals

Outcome 是让用户在同一正式 Web 以自由业务描述定位相关 Java 实现，并组合旧静态调用与新条件、状态、返回和异常事实回答。
范围只含受控 Java/Maven 源码；README、配置、运行数据、多语言、动态分派和设计意图均不在本轮。三个 Slice 都服务于这一共同
Outcome，不以 parser、Schema、View 或测试完成作为独立终点。

## System contracts and unresolved decisions

1. **ITER-006 基线（已闭合）：** Acceptance 与 clean implementation/document baseline 为 `8f305ed…`；不得修改实现后继续沿用
   run-008。Acceptance 现场的全局清单误路由、静态示例和 terminal 错误呈现限制保留到本轮重新验证。
2. **Java frontend（本机 exact artifact 已闭合）：** `TREE_SITTER_JAVA_FRONTEND@1` 固定当前 macOS/Python 3.14 环境中的
   `tree-sitter==0.25.2`、`tree-sitter-java==0.23.5`、language ABI 14、MIT 与 runtime fileset digest；禁止继续扩张窄手写
   lexer。exact `javac 21.0.8 --release 17` Oracle 已对带 Unicode 前缀的公开 development corpus 的 12 个目标 node UTF-8 byte
   range/order exact PASS。`pyproject.toml` exact dependency 与跨 Python/OS offline artifact/lock 须在 SLICE-001 内、首次产品
   Gate/capability qualification 前闭合；当前证据不外推为跨平台资格。
3. **Source Semantics / Coverage / no-payload（Contract 与 readiness Oracle 已闭合）：**
   `SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS` 已冻结 condition/branch、state、return、throw/catch、call-site/order、
   disposition、per-method completeness、旧 `CALLS` 不扩张规则与 Bundle allowlist。信息保持 Oracle 以 exact Support
   ref/digest/byte locator 重建 3 条目标 claim；信息越界 Oracle 以 exact schema/type/budget/semantic-closure allowlist 拒绝 direct、
   Base64、gzip+nested-AST、非 canonical Ref、单 Ref hex 与跨合法 Ref 分片 hex 6/6 故意泄露。legacy consistency Oracle 对公开
   语料的 2 条 accepted `CALLS` Relation、3 个 call site 及其 predicate/modality/revision/Support exact PASS；其中成功分支只证明
   issue-session call result 按 source order 被
   return，不把 `NEXT_IN_SOURCE` 扩张为条件 fallthrough/control-flow。exact digest 已入 Manifest。
4. **功能到实现发现（Contract 已闭合）：** `SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY` 正式注册
   `implementation_candidates` 与 `method_implementation`、问题无关 typed index、Support、排序、歧义和失败语义。
5. **模型协议（normative protocol 已冻结，实现在 Slice 内执行）：** `SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING` 已冻结隔离 Plan、
   Draft、Review 三调用、失败策略与操作边界；exact Prompt/role package/Gateway workload 由 SLICE-001 实现后冻结并在 Web 前完成
   capability qualification，旧单调用资格不能继承。
6. **Owner/持久化（Slice 实现清单）：** 新 Schema/Profile 必须逐一覆盖 `structure_authority.py`、`maven_workspace.py`、Bundle/Catalog、SQLite/File
   repositories、runtime/CLI/presenters/HTTP/Web、Citation、egress qualification/policy/workload 和 `pyproject.toml`。
7. **用户持有的现场评测：** 用户明确要求“你开发，我提问”。开发期间不收集题目；`SLICE-001` 产品代码冻结后，用户才提出
   至少一条此前未披露、无符号名且组合旧 `CALLS` 与新实现语义的问题，并补一条真实 boundary。公开 HMAC 协议继续作为可选的
   外部 evaluator 模式并保持 fail-closed，但不是本 Slice 的编码前置。仓库 validator 只能验证用户授权消息、代码冻结和事后
   Result 绑定，不能把开发者自拟题冒充用户现场题。

上述条件已结构化落入 Manifest；`V-PRE-001—006` 已 PASS，Contract、frontend、公开语料、Oracle 与用户持有问题模式已闭合。
题目不得驱动更新，`source_scope.question_or_suite_driven_update_allowed` 保持 `false`；用户问题只在产品代码冻结后进入验收。

## Slice, dependency and risk closure

- **SLICE-001：** 可见开发工程上的最小正式链。只支持 `call + if + return + throw`，但必须立刻由真实产品策略和真实模型在正式
  Web 回答一条不含符号名的跨域问题。随后冻结本 Slice 产品代码并执行独立方持有的 `V-CANARY-001` 小型真实 Java canary。
  HTTP probe、deterministic stub、预制答案或 validation-only 页面均不算 PASS；canary 未 PASS 不得授权 SLICE-002。
- **SLICE-002：** 仅使用可见 development/qualification corpus 加固常见 Java、状态/try-catch、R1→R2、重启和持久化；结束时
  再从正式 Web 人工回答至少 5 条自由问题，其中至少 2 条不含符号名。随后冻结本 Slice 产品代码并执行独立方持有的
  `V-CANARY-002` common-Java canary；未 PASS 不得授权 SLICE-003。
- **SLICE-003：** 产品代码冻结后才暴露 held-out 工程给执行环境。若曝光后修改产品代码，必须保留失败并同时更换工程与问题集；
  不能在同一工程上边看失败边调 parser。

两个 canary 的身份、源码和问题在所属 Slice 产品代码冻结前均须对实现方隐藏；从披露到对应 Slice Result seal 之间的任何产品
改动都会烧毁对应 canary，原结果必须保留，且只能由独立方换全新工程和问题后重试。每个 Slice Result 必须匹配 Manifest 的产品
代码冻结、canary project/suite digest 和披露收据，并证明该零变更窗口内产品变更数为 0。seal 后 capsule 永久 consumed；后续
已授权 Slice 的产品变化不追溯改写已封存 PASS/FAIL。canary 不复用为最终 held-out 工程，也不计入最终 12+4 target。

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

**ACCEPTED / SLICE-001 AUTHORIZED。** `V-PRE-001/002/003/006` 由 frontend/Oracle、System Contract、ITER-006 Acceptance 与
`8f305ed…` 基线闭合；用户消息 `codex-user-message:sha256:68df2434…` 同时确认用户持有现场问题的验收模型并授权开发，关闭
`V-PRE-004/005`。授权只覆盖 `SLICE-001`；用户问题、真实 Web 与 Result 未完成前，`SLICE-002/003` 继续 proposed。
