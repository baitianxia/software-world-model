---
id: ITER-001-PDR-002
kind: project-decision
status: accepted
authority: historical-project
owners: [project, architecture]
depends_on: [ITER-001-PDR-001]
code: []
tests: []
iteration: ITER-001
---

# PDR-002：在外部 Provider 关闭下恢复离线开发

## Context

静态契约和机械边界已足以支持不调用外部 Provider 的模块化单体开发，但真实 Adapter、模型能力、产品价值和生产启用仍需独立证据。

## Decision

允许 WP-1 至 WP-7 的离线部分继续，默认禁止真实模型 Strategy 激活。离线 Fixture 只能证明机械行为，不能签发 Live 资格。

## Consequences

工程实现可以与外部配置解耦推进；后续必须依次取得 Live CC、CE 和 Product Validation，并保持 Production Activation 为独立决定。最终这些门禁在本机体验范围完成，但本决定本身没有授权生产。

原始记录：[Implementation Development Reentry 001](../../../../archive/legacy-documents/implementation/iteration-001/Implementation_Development_Reentry_001.md)。
