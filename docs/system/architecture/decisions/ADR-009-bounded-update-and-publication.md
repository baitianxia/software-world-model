---
id: SYS-ADR-009
kind: system-decision
status: accepted
authority: normative
semantic_owner: SYS-ARCH-BASELINE
authority_scope: decision-rationale-only
owners: [architecture, application, knowledge]
depends_on: [SYS-ADR-004, SYS-ADR-006]
derived_from: [AD-076, AD-081, AD-092, AD-101, AD-102, AD-103, AD-109, AD-110, AD-133]
code: []
tests: []
---

# ADR-009：知识更新必须有界，发布与需求判断分离

## Context

开放式源码调查容易偏离目标，局部 Candidate 成功也不能证明更新完成或产品可用。

## Decision

每次更新从显式 Build Objective 出发；任务驱动更新可以另外绑定 exact Requirement Revision / Gap，首次、手动和计划更新不伪造该绑定。更新固定 Canonical Build Target、授权来源边界、预算、Coverage 和停止条件；Candidate 经知识准入、应用检查和原子发布三道门。发布只证明正式状态成立，不证明调用方的 Requirement 或业务目标已满足。

## Alternatives

让模型自行读取来源并直接写知识，或以发布成功作为任务成功，会产生旁路和假阳性。

## Consequences

流程更长但可回放；Gap 必须在新 Snapshot 上重新全量评估。
