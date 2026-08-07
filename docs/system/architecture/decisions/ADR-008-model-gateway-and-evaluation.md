---
id: SYS-ADR-008
kind: system-decision
status: accepted
authority: normative
owners: [architecture, ai]
depends_on: [SYS-ADR-002, SYS-ADR-006]
derived_from: [AD-021, AD-052, AD-063, AD-088, AD-100, AD-117]
code: []
tests: []
---

# ADR-008：模型入口、Strategy 与 Evaluation 分离

## Context

Provider 接口可用不代表模型适合某项业务能力；请求别名也不等于实际模型身份。

## Decision

所有模型调用经 Model Gateway；业务 Owner 定义 Capability 与 Strategy，Application 管理评测、有效期和激活。Contract Conformance、Capability Evaluation、Product Validation 与 Activation 分别形成证据。

## Alternatives

按 Provider 名称直接启用或把接口测试当能力证明会让漂移无从检测。

## Consequences

配置、模型、Prompt、Tool、Adapter 或实现变化可能使资格失效；生产路径默认关闭。
