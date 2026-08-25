---
id: SYS-ADR-INDEX
kind: system-decision-index
status: current
authority: normative
owners: [architecture]
depends_on: [SYS-ARCH-OVERVIEW]
code: []
tests: []
---

# 当前架构决策

ADR 解释为什么选择当前架构；规范正文仍由 Architecture、Invariant 或 Contract 拥有。旧日志中的 135 条决定已归档，当前有效选择合并如下，并在每份 ADR 的 `derived_from` 中保留旧编号。

| ADR | 决定 |
|---|---|
| [ADR-001](ADR-001-platform-and-world-model-separation.md) | 平台与世界模型分离 |
| [ADR-002](ADR-002-ai-native-trusted-control.md) | AI-native 与可信控制并存 |
| [ADR-003](ADR-003-formal-knowledge-model.md) | 正式知识的认识论模型 |
| [ADR-004](ADR-004-scope-context-snapshot-schema.md) | Scope、Context、Snapshot、Schema 一致性边界 |
| [ADR-005](ADR-005-derived-views-are-non-authoritative.md) | 派生视图不拥有知识 |
| [ADR-006](ADR-006-owner-boundaries.md) | Application、Agent、Source、Knowledge 的 Owner 边界 |
| [ADR-007](ADR-007-modular-monolith.md) | 模块化单体与单一逻辑权威 |
| [ADR-008](ADR-008-model-gateway-and-evaluation.md) | 模型入口、Strategy 与 Evaluation 分离 |
| [ADR-009](ADR-009-bounded-update-and-publication.md) | 有界更新与发布/验收分离 |
| [ADR-010](ADR-010-independent-verification.md) | 知识审核与答案审核独立 |
| [ADR-011](ADR-011-inference-depth-as-strategy.md) | 推断深度属于可评测 Strategy |
| [ADR-012](ADR-012-telemetry-is-observational.md) | Telemetry 与成本是非权威观察能力 |
| [ADR-013](ADR-013-evidence-first-synchronous-answering.md) | 直接源码调查采用证据优先路径 |
| [ADR-014](ADR-014-snapshot-first-world-model-answering.md) | 软件世界模型回答只读 exact Snapshot，禁止静默源码回退 |
| [ADR-015](ADR-015-bounded-world-model-investigation.md) | Agent 只通过有界 typed 查询调查 exact World Model |
| [ADR-016](ADR-016-engineering-question-answering.md) | 默认工程问答由世界模型认知驱动自适应、受控的 exact-revision 调查 |
| [ADR-017](ADR-017-transparent-qualified-provider-routing.md) | Ark 优先、DeepSeek 备用，以隔离的完整 Provider attempt 对用户透明地处理同一 logical question |

交付范围、暂停、某次运行实际选择哪个 Provider 和环境激活不改变长期架构选择，因此不进入当前 ADR 集合；Provider 路由协议本身由
ADR-017 拥有。
