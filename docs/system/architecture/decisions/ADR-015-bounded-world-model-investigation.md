---
id: SYS-ADR-015
kind: system-decision
status: accepted
authority: normative
owners: [architecture, application, knowledge, ai, quality]
depends_on: [SYS-ADR-005, SYS-ADR-008, SYS-ADR-010, SYS-ADR-014, SYS-PRODUCT-SUCCESS]
derived_from: [FINDING-008-024]
code: [src/software_world_model/application_services, src/software_world_model/ai_infrastructure, src/software_world_model/interface]
tests: [tests]
---

# ADR-015：Agent 只通过有界 typed 查询调查 exact World Model

## Context

`JAVA_SOURCE_SEMANTICS@1` 已能在提问前把 Java declaration、静态 `CALLS` 与受支持的实现语义发布到 no-payload Snapshot Read
Bundle。ITER-007 的固定 `Plan → 单方法选择 → Draft → Review` 却把多个相关方法当成歧义：登录问题所需的
`authenticate`、`recordFailure` 和 `issueSession` 都已进入正式知识，系统仍因不能唯一选择一个方法而拒答；零候选或无关候选也
不足以证明业务功能不存在。

问题不应通过取排名第一的方法、一次性展开全部 Bundle 或允许回答角色回读源码来修补。第一种会制造漏答，第二种失去资源上界，
第三种会把 `WORLD_MODEL` 静默变回 Direct Investigation。

## Decision

`WORLD_MODEL` 的知识权威、更新时点和 Source-off 边界保持不变；新增的 Agent 只拥有调查控制权：

```text
immutable Question / Needs / exact Read Authority
  → Agent proposes generic search terms and a bounded evidence-obligation set
  → Application normalizes and freezes the obligation ledger
  → Application derives the legal transition set from the ledger and sealed Result prefix
  → Agent proposes within that constrained set
  → Application compiles exact authority arguments and validates provenance/budget/terminal eligibility
  → Knowledge Use executes against the exact no-payload Bundle
  → Application seals the typed result and progress receipt
  → repeat only while a frozen obligation has a legal evidence-reducing transition
  → sealed investigation trace
  → one Draft
  → independent Review
  → deterministic Authorization / Delivery
```

Agent 只拥有原问题的语义解释、通用 search terms、由注册 operation/relation vocabulary 表达的 evidence request，以及当前受限
transition 内的 proposal hint。evidence request 是需要哪类正式证据，不是题型 enum、查询参数或执行授权；首轮经 Application
做 operation-discriminated normalization、去重、依赖收敛和预算可达性校验后即成为不可变 ledger，后续模型输出不能删改。
candidate discovery 是所有功能调查的强制首 transition，不是一个可单独关闭非空候选调查的 canonical evidence obligation；模型输出
`implementation_candidates` evidence alias 时，Application 必须无条件向上归一为 `method_implementations`，再执行既有 graph/inventory
依赖收敛。该规则不读取问题关键词或未来 Result，并保证非零候选不能只凭排名或存在性提前结束；零候选和截断候选仍按 typed
completeness 形成 Gap/Limitation，不执行伪 method query。
`method_implementation` 的正式 Result 已密封该方法的 exact supported outgoing `CALLS` 与方向/Coverage，因此 standalone raw
`direct_neighborhood(OUTGOING_CALLS)` evidence alias 也由 Application 收敛为 `method_implementations`，避免对同一关系重复查询。
该 subsumption 只读注册 operation/relation；与 path obligation 组合时 direct 保持独立，`INCOMING_CALLS`、`BOTH_CALLS` 也不折叠。
平台而不是 Agent 拥有逐状态 operation allowlist、typed Ref、Result binding、Snapshot fence、direction/predicate expansion、graph bounds、
查询执行、Support、预算、cycle/progress、trace seal、evidence fulfillment、FINISH reason 和终态；Application 必须从冻结 ledger 与 sealed input
deterministic 编译这些 authority 参数，不能要求模型复制、重建或猜测 opaque identifier，也不能让一次模型 `FINISH` 缩小未完成义务。
Agent 看不到 Repository、Source file、Artifact/Evidence payload、完整 AST、Knowledge Update、Citation observation、Direct
Investigation、评测 Oracle 或其他角色私有输出。每轮 proposal 只在验证后执行；模型输出本身不是查询结果或授权。

首个受权闭包允许每题 2—4 次调查模型调用，随后恰好 1 次 Draft 和 1 次独立 Review，总调用上限为 6，不重试。首轮始终编译为
candidate discovery 并冻结向上归一后的 evidence ledger；以后每轮只披露由 ledger、立即前序 Result 和剩余预算推导的受限 operation 子集。
只有全部 evidence obligation 已由 sealed Result 覆盖，或 typed Result 证明没有合法 evidence-reducing transition 时，Application 才
允许显式 `FINISH`。`FINISH` 自身计作一次调用，因此 candidate Result 已关闭全部义务时，1 query + FINISH 仍是合法 2-call
investigation；尚无任何 Result 时的 FINISH 仍失败关闭。每轮 Application 只编译一个 typed operation；批量 `method_implementation` 仍是一个查询，
最多携带 3 个来自同一已密封 candidate result 的 exact method Ref。
调用、query/result bytes、Support、trace 和 wall time 均由当前 Contract 固定。预算耗尽、无进展、重复 proposal、Ref 越界或结果
未知都失败关闭为具体 Limitation，不取消 Review，也不转入 Source/Direct。
`remaining_budget=1` 时 Application 仍可授权 ledger 中最后一个有证据增益的 query；执行并密封 Result 后立即以
`INVESTIGATION_BUDGET_EXHAUSTED` 终止 Session，不需要超出上限的额外 `FINISH`。无进展/cycle 依据是同一 Session 中已执行的
exact query 和 Result progress token，而不是脱离 sealed state 单独比较 operation 名称。

Gateway 可以在 Answer 启动前按已资格 connection policy 预建有界 exact Provider descriptor set；descriptor 数不能从调用上限自动
推导。默认 policy 保持一请求一连接。Provider endpoint 明确支持且已由 Conformance 与 Capability Result 证明时，版本化 persistent
verified TLS policy 可以在同一授权 Gateway run 内复用一个 TLS session；这只是 transport 复用，不是 Provider session memory，也不
合并逻辑调用身份。只有 credential 尚未解析、Authorization/HTTP bytes 尚未发送时，才能消费下一个 descriptor 重新取得 TLS；任何
request bytes 可能已发送后的连接失败立即 outcome unknown，禁止 request retry。实际调用数仍必须落在冻结区间；未消费 descriptor 在
Answer terminal 后由 Gateway 丢弃并单独审计，不能跨题或跨 session 复用。每个实际调用仍拥有唯一 workload、manifest、receipt、
request ID、body/result digest 和 transport audit；TLS attempt/success/reuse 与 Provider call count 分开闭合。

历史单 Provider Profile 继续在 product freeze 前选择一个 exact route，并保持同 Provider request 零重试。默认 `ENGINEERING_QA` 的
多 Provider 高可用语义已由 ADR-017 收窄为 Session 预授权的 Ark→DeepSeek 有序 attempt：用户的一次 logical question 可在 primary
attempt 密封 terminal 后透明启动一个完全隔离、从原问题与 exact Cognition 重跑全链的 fallback attempt。它不是同一外部 request 的
retry，也不得复用 primary 中间态。本 ADR 不再拥有 Engineering QA 的跨 Provider 路由规则。

progress receipt 可以投影下列三层平台 verdict，但不得暴露 Oracle identity、评测期望或隐藏输入。负向结论必须分别拥有三个独立证明：

1. **Query result completeness**：所有授权页已读，`total/truncated/cursor` 闭合；
2. **Knowledge representation coverage**：授权单元和相关 facet 均有明确 disposition，unsupported/failed 不被当成空事实；
3. **Business discovery recall completeness**：冻结的同义词、不同命名和不同入口反例 Oracle 能证明相关实现不会被发现策略漏掉。

三层同时成立才允许 `BOUNDED_ABSENCE`；任一层未知只能返回指明缺失层的 Limitation。分页结束只证明第一层，不能推导第三层。

## Alternatives

- 直接取最高排名候选：简单，但把排名误当成正确性和完整性证明，已被 ITER-007 产品失败反证。
- 一次展开所有候选与实现：可能覆盖公开题，却没有稳定 query/result/Support/时延上界，并扩大 prompt 注入和泄露面。
- 让严格 `WORLD_MODEL` 的回答 Agent 读取源码或自动触发更新：可能提高单题命中，但违反 ADR-014，无法证明预构建 World Model 的复用价值。默认 `ENGINEERING_QA` 的自适应源码调查由 ADR-016 作为独立模式定义，不属于本替代项。
- 继续固定一次 Plan 并增加更多关键词：仍不能根据结果改变调查路径，也会形成题目/工程补丁。

## Consequences

问答从固定三调用变为有界可变调查，Strategy、Capability Evaluation、Gateway、connection policy、正式 Web 与审计必须共同版本化；旧
`JAVA_SOURCE_SEMANTICS@1` 三调用资格不能继承。调查 trace 增加实现复杂度和时延，因此产品 Gate 必须与成熟源码 Agent 逐题比较，
并在编码前冻结可重放的正向价值阈值。若最小闭包仍低于成熟 Agent、必须读 Source、或不能在预算内组合多个方法，本方案应停止并
记录为架构反证，而不是继续扩张语法或预算。

Provider Conformance、Capability、Product 与 Activation 证据始终不能跨 Provider 继承。采用 ADR-017 的 Engineering QA Session 必须
分别冻结并审计两条 route；其他尚未采用该 ADR 的 Profile 仍是单 Provider。

## Supersedes / migration

本决定只替代 `JAVA_SOURCE_SEMANTICS@1` 固定单方法、固定三调用的问答编排；ADR-014 的 exact Snapshot、Source-off、Citation
隔离和 no-fallback 继续有效。已接受的 Maven Structure 与 Java Static Call Profile 保持原协议，除非各自取得新的 closed
Qualification。
