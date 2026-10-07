---
id: SYS-ADR-015
kind: system-decision
status: accepted
authority: normative
semantic_owner: SYS-ARCH-BASELINE
authority_scope: decision-rationale-only
owners: [architecture, application, knowledge, ai, quality]
depends_on: [SYS-ADR-005, SYS-ADR-008, SYS-ADR-010, SYS-ADR-014, SYS-PRODUCT-SUCCESS]
derived_from: [FINDING-008-024]
code: [src/software_world_model/application_services, src/software_world_model/ai_infrastructure, src/software_world_model/interface]
tests: [tests]
---

# ADR-015：Agent 只通过有界 typed 查询调查 exact World Model

## Context

`JAVA_SOURCE_SEMANTICS@1` 已能在提问前把 Java declaration、静态 `CALLS` 与受支持的实现语义发布到 no-payload Snapshot Read
Bundle。固定的单方法选择策略可能把多个相关方法当成歧义，使问题无法覆盖完整业务路径；零候选或无关候选也不足以证明业务功能不存在。

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
transition 内的 proposal hint。evidence request 是需要哪类正式证据，不是查询参数或执行授权；Application 负责归一、去重、依赖收敛、
预算可达性校验并冻结不可变 ledger，后续模型输出不能删改。候选发现、方法实现和调用关系的具体 vocabulary、别名归一、结果数量
和路径组合属于详细 Profile Contract，不在本 ADR 固定。平台而不是 Agent 拥有逐状态 operation allowlist、typed Ref、Result binding、
Snapshot fence、查询执行、Support、进度、trace seal、evidence fulfillment、终态和资源边界；模型输出本身不是查询结果或授权。
Agent 看不到 Repository、Source file、Artifact/Evidence payload、完整 AST、Knowledge Update、Citation observation、Direct
Investigation 或其他角色私有输出。每轮 proposal 只在验证后执行；模型输出本身不是查询结果或授权。

调查必须有界、可进展、零重试，并在每次 proposal、typed Result、Draft 和独立 Review 上保留精确身份与资源收据。具体调用上限、
FINISH 计数、结果数量、bytes/wall-time、连接复用和 descriptor/TLS 策略由 Profile Contract、资格和运行实现定义，不在本 ADR 中
重复规定。无进展、越界、预算耗尽或结果未知必须失败关闭为具体 Limitation，不取消 Review，也不转入 Source/Direct。

历史单 Provider Profile 继续在 product freeze 前选择一个 exact route，并保持同 Provider request 零重试。默认 `ENGINEERING_QA` 的
多 Provider 高可用语义已由 ADR-017 收窄为 Session 预授权的 `preferred → fallback` 有序 attempt；具体 Provider/model 只由 execution profile
配置解析。用户的一次 logical question 可在 preferred
attempt 密封 terminal 后透明启动一个完全隔离、从原问题与 exact Cognition 重跑全链的 fallback attempt。它不是同一外部 request 的
retry，也不得复用 preferred 中间态。本 ADR 不再拥有 Engineering QA 的跨 Provider 路由规则。

Profile Contract 可以要求分别证明查询结果、知识表示和问题相关发现范围的完整性；否定性结论只有在所有适用完整性条件均已密封时
才能成立。任一条件未知只能返回指明缺失边界的 Limitation，不能从分页结束、候选数量或单一查询结果推出业务不存在。

## Alternatives

- 直接取最高排名候选：简单，但会把排名误当成正确性和完整性证明。
- 一次展开所有候选与实现：可能覆盖公开题，却没有稳定 query/result/Support/时延上界，并扩大 prompt 注入和泄露面。
- 让严格 `WORLD_MODEL` 的回答 Agent 读取源码或自动触发更新：可能提高单题命中，但违反 ADR-014，无法证明预构建 World Model 的复用价值。默认 `ENGINEERING_QA` 的自适应源码调查由 ADR-016 作为独立模式定义，不属于本替代项。
- 继续固定一次 Plan 并增加更多关键词：仍不能根据结果改变调查路径，也会形成题目/工程补丁。

## Consequences

问答从固定选择变为有界可变调查，Strategy 治理、资格、Gateway、connection policy 和审计必须共同版本化；具体产品资格、
体验和比较方法由产品与质量文档定义。若调查不能在其受控边界内形成可审核证据，应失败关闭并保留 Limitation，而不是扩大权限或静默
改用另一模式。

Provider Conformance、Capability、Product 与 Activation 证据始终不能跨 Provider 继承。采用 ADR-017 的 Engineering QA Session 必须
分别冻结并审计两条 route；其他尚未采用该 ADR 的 Profile 仍是单 Provider。

## Supersedes / migration

本决定只替代 `JAVA_SOURCE_SEMANTICS@1` 固定单方法、固定三调用的问答编排；ADR-014 的 exact Snapshot、Source-off、Citation
隔离和 no-fallback 继续有效。既有 Structure 与 Static Call Profile 保持各自受控契约，除非取得新的 closed Qualification；具体语言、构建工具和实现实例不属于本架构决策。
