---
id: SYS-ADR-020
kind: system-decision
status: accepted
authority: normative
semantic_owner: SYS-ARCH-BASELINE
authority_scope: model-execution-boundary
owners: [architecture, application, ai, security, operations, quality]
depends_on: [SYS-ADR-008, SYS-ADR-017, SYS-ADR-018, SYS-ADR-019]
derived_from: [FINDING-010-297]
code: [src/software_world_model/ai_infrastructure, src/software_world_model/application_services, src/software_world_model/interface]
tests: [tests]
---

# ADR-020：模型执行边界由运行时独占

## Context

架构基线已经要求 Model Gateway 隔离 Provider 和调用方式，但旧的应用契约把 `preferred → fallback` route、route role、Provider runtime 和
Provider 失败投影带入了 Conversation、Session artifact、Agent 和 Browser。这样产生了两个问题：上层仍需理解基础设施容错语义；真实入口必须
同时构造备用 Provider，即使首选执行本身已经具备条件。

## Decision

1. 系统增加唯一的 Provider-neutral `ModelExecutionPort`。它接收一次 immutable logical interaction request，返回一个 terminal logical result 和
   opaque execution-audit reference；上层不接收候选、Provider、模型、endpoint、route、attempt 或原始 transport evidence。
2. Model Execution Runtime 是候选配置、顺序、资格、dispatch admission、availability verdict、attempt isolation、调用收据和 Provider audit 的唯一所有者。
   `preferred`、`fallback` 等词只允许存在于运行时内部配置和 audit，不属于 Application、Agent、Session artifact、Conversation、Response Control、Browser 或 UI
   的输入、输出和分支条件。
3. Runtime 在受信 availability owner 密封“当前执行配置不可用”后，可以以原始 logical input 和新的 attempt identity 启动一次完整 Agent chain。该过程对上层表现为
   同一 logical interaction 的一次执行；上层不得拼接两次结果、选择备用配置或因输出无效、Review、Source、权限、应用或安全失败而切换。
4. Provider-specific evidence、模型身份、成本、HTTP/TLS、准入和重复成本风险只写入内部 execution audit。对话和浏览器只能得到通用 execution status、计数和不透明 audit ref。
5. 迁移采用兼容适配器：现有 Provider route/attempt 实现可以暂时留在 infrastructure composition root，但不得作为 Application/Agent 公共导出或新的契约字段。迁移
   完成后删除旧双路 artifact 的应用强制校验。

## Consequences

- Provider 对产品语义和 Agent 规划完全透明，首选成功时不需要构造备用执行。
- fallback 仍保留完整链、零同请求重试和失败关闭语义，但其审计复杂度被封装在运行时。
- 需要新增一个不透明执行端口，并把当前 Conversation/Browser 的 Provider 字段迁移为通用执行状态；旧 receipt 只能作为内部历史兼容读取。
- Provider 资格、授权、预算、准入和 transport 审计不会被删除，只改变所有权和投影位置。

## Rejected alternatives

- 在应用层继续冻结通用 route role：仍然泄漏候选顺序和容错分支。
- 仅隐藏 Provider 名称：上层仍需理解 preferred/fallback，根因未消除。
- 删除 fallback：损失已定义的可信不可用恢复能力，也不能解决应用边界错误。
