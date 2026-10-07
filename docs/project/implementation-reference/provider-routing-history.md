---
id: PROJECT-REFERENCE-PROVIDER-ROUTING-HISTORY
kind: implementation-reference
status: historical
authority: historical-evidence
owners: [engineering, operations, project]
depends_on: [SYS-ADR-017, SYS-ARCH-BASELINE]
code: []
tests: []
coding_input: false
source_path: docs/system/architecture/decisions/ADR-017-transparent-qualified-provider-routing.md
as_of: 2026-10-02
---

# provider routing implementation history

以下内容从 ADR-017 的 Consequences 迁出，保留当前迭代实例和本地候选证据。它们不定义 preferred/fallback 的架构语义。

曾有 ITER-010 配置把 Ark 映射到 `preferred`、DeepSeek 映射到 `fallback`，并由 `V-DEEPSEEK-IDLE-001` 验证备用配置的调度插件。
`FINDING-010-100` 和 `FINDING-010-101` 曾形成 Application-owned typed classification、两个独立 attempt authority/runtime/receipt、
committed Work State 隔离、logical Turn 分账和 non-starting Browser/provider composition；这些证据没有执行真实 Adapter、transport、
credential、Provider 或 Browser，因此只能标为本地候选，不能宣称透明 fallback 已可用或已取得 live/qualified 状态。
