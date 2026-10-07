---
id: SYS-ADR-008
kind: system-decision
status: accepted
authority: normative
semantic_owner: SYS-ARCH-BASELINE
authority_scope: decision-rationale-only
owners: [architecture, ai]
depends_on: [SYS-ADR-002, SYS-ADR-006]
derived_from: [AD-021, AD-052, AD-063, AD-088, AD-100, AD-117]
code: []
tests: []
---

# ADR-008：模型入口、Strategy 与受控激活分离

## Context

Provider 接口可用不代表模型适合某项业务能力；请求别名也不等于实际模型身份。

## Decision

所有模型调用经 Model Gateway；业务 Owner 定义 Capability 与 Strategy，Application 管理资格、有效期、激活、撤销和回退。生产 Strategy 与未激活 Strategy 的输入、输出和状态必须隔离；身份漂移、资格失效或边界变化时，生产路径失败关闭。具体业务质量判断不属于本架构决定。

## Alternatives

按 Provider 名称直接启用或把接口测试当能力证明会让身份和能力漂移无从检测。

## Consequences

配置、模型、Prompt、Tool、Adapter 或实现变化可能使资格失效；生产路径默认关闭。
