---
id: SYS-ADR-002
kind: system-decision
status: accepted
authority: normative
semantic_owner: SYS-ARCH-BASELINE
authority_scope: decision-rationale-only
owners: [architecture, ai]
depends_on: [SYS-ADR-001]
derived_from: [AD-019, AD-086, AD-087, AD-095, AD-115, AD-131, AD-132]
code: []
tests: []
---

# ADR-002：AI-native 与可信控制并存

## Context

软件理解需要生成式推理，但模型不能可靠承担身份、权限、一致性和最终事实判断。

## Decision

模型负责 Proposal、解释和独立 Review；平台负责授权、冻结输入、确定性约束、身份、准入、发布和放行。模型能力通过可替换 Strategy 接入，不能绕过正式知识路径。

## Alternatives

纯确定性解析覆盖不足；让自治 Agent 直接操作 Store 或来源会破坏审计和权限边界。

## Consequences

模型结果始终是不可信输入；平台必须付出额外的 Manifest、Receipt、Review 和失败关闭成本。
