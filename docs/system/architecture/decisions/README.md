---
id: SYS-ADR-INDEX
kind: system-decision-index
status: current
authority: normative
semantic_owner: SYS-ARCH-BASELINE
authority_scope: decision-index-only
owners: [architecture]
depends_on: [SYS-ARCH-BASELINE]
code: []
tests: []
---

# 当前架构决策

ADR 解释为什么选择当前架构；规范正文唯一由 `SYS-ARCH-BASELINE` 拥有，Invariant 和 Contract 只能细化基线，不能独立扩张或收窄顶层语义。旧日志中的 135 条决定已归档，当前有效选择合并如下，并在每份 ADR 的 `derived_from` 中保留旧编号。

接受 ADR 不会自动改变架构。只有把新增、修改或废弃条款同步写入 [架构基线](../architecture-baseline.md)，并修正受影响附录和 Contract 后，决策才成为当前架构的一部分。若 ADR 与基线冲突，以基线为准并立即标记该 ADR 为待收敛状态，不得让开发者自行选择其中一份。

本目录中的 ADR 即使标记为 `authority: normative`，也只是在当前决策集合中保留其理由和迁移关系；每份 ADR 的 `semantic_owner` 均应理解为 `SYS-ARCH-BASELINE`，其具体范围由 `authority_scope` 说明。ADR 不定义默认对话、默认 View、Provider 身份或实现参数。

| ADR | 决定 |
|---|---|
| [ADR-001](ADR-001-platform-and-world-model-separation.md) | 平台与世界模型分离 |
| [ADR-002](ADR-002-ai-native-trusted-control.md) | AI-native 与可信控制并存 |
| [ADR-003](ADR-003-formal-knowledge-model.md) | 正式知识的认识论模型 |
| [ADR-004](ADR-004-scope-context-snapshot-schema.md) | Scope、Context、Snapshot、Schema 一致性边界 |
| [ADR-005](ADR-005-derived-views-are-non-authoritative.md) | 派生视图不拥有知识 |
| [ADR-006](ADR-006-owner-boundaries.md) | Application、Agent、Source、Knowledge 的 Owner 边界 |
| [ADR-007](ADR-007-modular-monolith.md) | 模块化单体与单一逻辑权威 |
| [ADR-008](ADR-008-model-gateway-and-evaluation.md) | 模型入口、Strategy 与受控激活分离 |
| [ADR-009](ADR-009-bounded-update-and-publication.md) | 有界更新与发布/需求判断分离 |
| [ADR-010](ADR-010-independent-verification.md) | 知识审核与答案审核独立 |
| [ADR-011](ADR-011-inference-depth-as-strategy.md) | 推断深度属于受治理 Strategy |
| [ADR-012](ADR-012-telemetry-is-observational.md) | Telemetry 与成本是非权威观察能力 |
| [ADR-013](ADR-013-evidence-first-synchronous-answering.md) | 直接源码调查采用证据优先路径 |
| [ADR-014](ADR-014-snapshot-first-world-model-answering.md) | 软件世界模型回答只读 exact Snapshot，禁止静默源码回退 |
| [ADR-015](ADR-015-bounded-world-model-investigation.md) | Agent 只通过有界 typed 查询调查 exact World Model |
| [ADR-016](ADR-016-engineering-question-answering.md) | 显式 Profile 的世界模型认知与 exact-revision 受控调查边界；默认对话语义由 ADR-018 定义 |
| [ADR-017](ADR-017-transparent-qualified-provider-routing.md) | 以通用 `preferred → fallback` execution-profile route 和受信可用性裁决，对用户透明地处理真实执行配置不可用 |
| [ADR-018](ADR-018-conversational-engineering-agent.md) | 软件世界模型提供持久认知，主工程 Agent 在受控工具和独立审核边界内承担语义多轮工程 Chat |
| [ADR-019](ADR-019-public-source-standing-model-authority.md) | 公开开源 exact revision 与既定 Provider route 采用一次持续人工权威，由系统逐 Turn/调用派生 exact receipt |
| [ADR-020](ADR-020-model-execution-boundary.md) | Provider 候选与容错由 Model Execution Runtime 独占，上层只依赖不透明逻辑执行端口 |
| [ADR-021](ADR-021-cognition-advantage-and-agent-capability.md) | 认知表示与检索成为一等架构关注点；分级准入、只读工具对等、Turn Trace 与知识结晶、Reviewer 有界核验读取、回答路径收敛 |

交付范围、暂停、某次运行实际选择哪个 Provider 和环境激活不改变长期架构选择，因此不进入当前 ADR 集合；Provider 路由协议本身由
ADR-017 拥有。ADR-018 对 ADR-016 作部分修订：保留认知、来源、证据与审核底座，只替换固定多角色 Agent 本体。
ADR-019 进一步区分一次性的人类边界决定与逐次机器控制记录；它不放宽 ADR-017 的 attempt 隔离、备用路线准入或模型调用审计。ADR-020 将 ADR-017
的候选顺序和备用路线从 Application/Session 语义收回 Model Execution Runtime；保留其内部隔离、准入、零重试和失败关闭要求。ADR-021 部分修订 ADR-018：Turn 证据终态后转为非权威 Turn Trace，Reviewer 可做有界只读核验读取；主 Agent、证据分区与跨 Turn 不复用证据的原则不变。
