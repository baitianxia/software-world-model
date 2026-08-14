---
id: ROADMAP-CANDIDATE-BOUNDED-WORLD-MODEL-INVESTIGATION
kind: roadmap-candidate
status: candidate
authority: planning-only
owners: [product, architecture, application, quality]
depends_on: [SYS-PRODUCT-SUCCESS, ITER-007-RESULT-SLICE-001-STOP-DECISION, FINDING-007-008]
code: []
tests: []
coding_input: false
---

# Candidate：受限 Agent 驱动的 World Model 调查

## Trigger

ITER-007 已证明相关 Java 方法和实现事实进入 World Model，但固定单方法协议在多个相关候选时拒答，并在不存在功能时返回无关
候选。问题首先发生在查询与编排层，而不是本次 Provider 调用或已观察到的知识缺失。

## Proposed boundary

- Agent 只根据 typed World Model result 决定下一步查询；
- 平台拥有 exact Snapshot、操作白名单、typed Ref、Support、Coverage 和预算；
- 多候选是正常调查输入，不要求先唯一选择；
- 只有查询结果、知识表示 Coverage 与业务语义发现召回三层都可证明完整时，才支持有界负向结论；
- 回答 Agent 禁止访问 Repository、源码、raw Evidence、Update 和 Direct fallback；
- Draft 与独立 Review 使用密封调查 trace，从同一正式 Web 交付答案、Gap 和 Citation。

## Unknowns

现有 Query 的 pagination/total/truncated/coverage 语义是否足以证明穷尽，结果驱动调查的最小调用与时延预算，以及当前 no-payload
语义是否足以覆盖未见多方法问题，都尚未形成证据。任何一项失败都可能把根因重新分类为表示问题，而不是查询问题。

## Entry conditions

先接受 bounded investigation ADR，修订 Answering、Implementation Query、Agentic Task、Runtime、Gateway 和 Security Contract，
冻结 exact baseline、预算、隐藏工程与成熟源码 Agent 对照，再由用户授权唯一纵向 Slice。公开 LoginService 只能作回归，不能作
隐藏泛化证据。

## Active validation

`ITER-008` 已提出用两个依次授权、都可从正式 Web 人工提问的纵向 Slice 验证本 Candidate：第一段尽早执行隐藏 canary，第二段
才做完整加固和最终对照。它仍是 `PROPOSED / NOT READY / NOT AUTHORIZED`；Candidate 与 Proposal 均不构成编码授权。
