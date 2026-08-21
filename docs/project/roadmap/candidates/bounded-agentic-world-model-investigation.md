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

`ITER-008` 已执行第一段并以 `REDIRECT` 结束。run-012 的正式冻结 PASS，正向登录流程已经从真实 Web 给出自然答案和 Citation；边界问题的
Draft 已形成 Limitation，但在 Review 交付处失败关闭。用户另报告 Codex/OpenAI 客户端的提示词准入阻断，本地尚无对应产品运行
receipt，不能把它归因于产品 Provider 或本 Candidate 架构。`ITER-009-SLICE-001` 已按
`ROADMAP-CANDIDATE-LOCAL-WEB-DIRECTION-PREVIEW-RECOVERY` 完成最小 Web 方向体验。结果证明 Snapshot-only 技术链能够交付答案和
Limitation，却也证明固定 `implementation-answer`、逐代码事件 Draft/Review 与实验台 UI 会把自由问题变成代码走读。ITER-009 因而
`REDIRECT`，后续由 `ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST` 继续同一产品目标；本 Candidate 不再构成活动编码授权。
