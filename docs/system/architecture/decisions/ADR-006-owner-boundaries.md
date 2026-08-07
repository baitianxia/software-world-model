---
id: SYS-ADR-006
kind: system-decision
status: accepted
authority: normative
owners: [architecture]
depends_on: [SYS-ADR-002, SYS-ADR-003]
derived_from: [AD-048, AD-049, AD-051, AD-054, AD-058, AD-059, AD-060, AD-061, AD-074, AD-077, AD-109, AD-110, AD-112, AD-127, AD-135]
code: []
tests: []
---

# ADR-006：按权威状态划分 Owner

## Context

Agentic 流程跨来源、知识、模型和交付；若由 Orchestrator 拥有全部状态，会形成大事务和越权入口。

## Decision

Source Integration 拥有来源与 Artifact；Knowledge Engine 拥有正式知识；Model Gateway 拥有模型调用边界。Application Layer 内部继续按权威状态拆分：Use-case Services 拥有各用例 Attempt / Result，Conversational Task Control 拥有 Task、Grant、Invocation、Authorization 与 Dispatch，Response Control 拥有 Answer Candidate、Review Decision、Final Authorization 与 Logical Delivery。它们只交换不可变 Reference、Result 和只读 Assertion，不互写私有状态。Agent 只产生 Proposal / Assessment，并通过受控 Application Services 使用能力。

## Alternatives

中心 Workflow/Agent Store 统一掌权会复制领域状态并模糊失败恢复。

## Consequences

跨 Owner 通过命令、不可变结果和幂等恢复协作，部分成功必须显式呈现。
