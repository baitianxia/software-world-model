---
id: SYS-ADR-015
kind: system-decision
status: accepted
authority: normative
owners: [architecture, application, knowledge, ai, quality]
depends_on: [SYS-ADR-005, SYS-ADR-008, SYS-ADR-010, SYS-ADR-014, SYS-PRODUCT-SUCCESS]
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
  → Agent proposes one typed investigation operation
  → Application validates operation, arguments, provenance and remaining budget
  → Knowledge Use executes against the exact no-payload Bundle
  → Application seals the typed result and progress receipt
  → Agent receives only the sealed trace prefix and proposes the next operation or FINISH
  → sealed investigation trace
  → one Draft
  → independent Review
  → deterministic Authorization / Delivery
```

平台而不是 Agent 拥有 operation allowlist、typed Ref、Snapshot fence、查询执行、Support、预算、cycle/progress、trace seal 和终态。
Agent 看不到 Repository、Source file、Artifact/Evidence payload、完整 AST、Knowledge Update、Citation observation、Direct
Investigation、评测 Oracle 或其他角色私有输出。每轮 proposal 只在验证后执行；模型输出本身不是查询结果或授权。

首个受权闭包允许每题 2—4 次调查模型调用，随后恰好 1 次 Draft 和 1 次独立 Review，总调用上限为 6，不重试。每轮只提交一个
typed operation；批量 `method_implementation` 仍是一个查询，最多携带 3 个来自同一已密封 candidate result 的 exact method Ref。
调用、query/result bytes、Support、trace 和 wall time 均由当前 Contract 固定。预算耗尽、无进展、重复 proposal、Ref 越界或结果
未知都失败关闭为具体 Limitation，不取消 Review，也不转入 Source/Direct。

Gateway 可以在 Answer 启动前预建调用上限数量的 exact Provider connection。实际调用数必须落在冻结区间；未消费 descriptor 在
Answer terminal 后由 Gateway 丢弃并单独审计，不能跨题、跨角色或跨 session 复用。每个实际调用仍拥有唯一 workload、manifest、
receipt 和 transport audit。

负向结论必须分别拥有三个独立证明：

1. **Query result completeness**：所有授权页已读，`total/truncated/cursor` 闭合；
2. **Knowledge representation coverage**：授权单元和相关 facet 均有明确 disposition，unsupported/failed 不被当成空事实；
3. **Business discovery recall completeness**：冻结的同义词、不同命名和不同入口反例 Oracle 能证明相关实现不会被发现策略漏掉。

三层同时成立才允许 `BOUNDED_ABSENCE`；任一层未知只能返回指明缺失层的 Limitation。分页结束只证明第一层，不能推导第三层。

## Alternatives

- 直接取最高排名候选：简单，但把排名误当成正确性和完整性证明，已被 ITER-007 产品失败反证。
- 一次展开所有候选与实现：可能覆盖公开题，却没有稳定 query/result/Support/时延上界，并扩大 prompt 注入和泄露面。
- 回答 Agent 读取源码或自动触发更新：可能提高单题命中，但违反 ADR-014，无法证明预构建 World Model 的复用价值。
- 继续固定一次 Plan 并增加更多关键词：仍不能根据结果改变调查路径，也会形成题目/工程补丁。

## Consequences

问答从固定三调用变为有界可变调查，Strategy、Capability Evaluation、Gateway、正式 Web 与审计必须共同版本化；旧
`JAVA_SOURCE_SEMANTICS@1` 三调用资格不能继承。调查 trace 增加实现复杂度和时延，因此产品 Gate 必须与成熟源码 Agent 逐题比较，
并在编码前冻结可重放的正向价值阈值。若最小闭包仍低于成熟 Agent、必须读 Source、或不能在预算内组合多个方法，本方案应停止并
记录为架构反证，而不是继续扩张语法或预算。

## Supersedes / migration

本决定只替代 `JAVA_SOURCE_SEMANTICS@1` 固定单方法、固定三调用的问答编排；ADR-014 的 exact Snapshot、Source-off、Citation
隔离和 no-fallback 继续有效。已接受的 Maven Structure 与 Java Static Call Profile 保持原协议，除非各自取得新的 closed
Qualification。
