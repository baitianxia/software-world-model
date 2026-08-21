---
id: ITER-010-INDEX
kind: iteration-index
status: proposed
authority: project-plan
owners: [product, project, architecture, engineering, quality]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ROADMAP-M-002, ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, ITER-010-PROPOSAL, ITER-010-READINESS, ITER-010-VERIFICATION, ITER-010-SLICE-001, ITER-010-SLICE-002, ITER-010-SLICE-003]
code: []
tests: []
iteration: ITER-010
coding_input: false
---

# ITER-010：世界模型认知引导的自适应工程问答

## 先看懂这轮要做什么

普通用户在浏览器提问；软件世界模型先提供对当前精确版本的稳定系统认知；调查模型像高级工程师一样根据每次发现决定下一步读什么；
来源代理负责校验权限，隔离读取器只读执行；回答模型只用密封证据组织答案；独立审核模型检查问题是否答全、结论是否有依据，发现具体
证据缺口时再启动一轮全新、独立的补证调查。

| 文档术语 | 中文含义与职责 |
|---|---|
| World Model Cognition Context | 世界模型针对本题投影出的系统认知，不是手册或关键词缓存 |
| Source Broker / Retrieval Worker | 来源代理 / 隔离读取器；前者校验并编译只读操作，后者执行，模型本身没有源码权限 |
| Evidence Ledger | 本题只追加的调查记录，保存每次提议、决定、读取结果、失败和未知 |
| Question Evidence Package | 调查后密封的本题证据包；可支持/引用条目与必须保留但不能支持肯定结论的边界/审计条目严格分区 |
| Verification Investigation | 审核发现具体缺口后启动的全新补证调查，不回到初始调查会话 |

开发顺序是“先出最小 Web 纵切，再确认方向，再夯实”：一条代表问题先跑通真实页面；随后完成 4 条跨维度问题与现场题。只有用户决定
`CONTINUE`，才进入持久恢复、复杂冲突/去重、完整异常矩阵、第二工程和三臂同题认知消融。

## Status and authorization

`REPLANNED / ALL SLICES PROPOSED / NO PRODUCT CODING AUTHORIZED`。

用户消息 `codex-user-message:sha256:d3b60bdaa52d96ced3c653a8dcd54fabff41beb7f23f0bf691e6983ebb9437bc` 于
`2026-08-21T08:23:25Z` 要求按最新讨论重新制定计划并更新文档。它确认：World Model 仍是真正的软件外部认知；提问期由 LLM 主导
自适应调查，Broker/Worker 控制实际读取，调查后 seal，Reviewer 可独立要求补证。

本收据只授权重制计划和文档。此前 `1b327024… + 5cdb7000…` 绑定修正前的一次性检索设计，不能自动扩展为新职责，因此当前没有活动
开发 Slice。产品代码、credential、Provider/model 调用、live Web/browser、隐藏输入、任何 Slice 和 Production Activation 均未获新授权。

本轮产品基线固定为 commit `1fb997bab6444523f82ebf1a514a1abbf79656c7`、tree
`1369ce932c778c57a118123e8257ede476229d73`。ITER-009 的体验代码保留为技术资产，但其代码走读式产品方向已由
`ITER-009-RESULT-SLICE-001-STOP-REDIRECT` 否决，不能被写成 Acceptance。

## Required inputs

- [Proposal](proposal.md)
- [Manifest](manifest.yaml)
- [Verification Matrix](verification-matrix.md)
- [Readiness Review](readiness-review.md)
- [Development Design](development-design/README.md)
- [Findings](findings/README.md)
- [Results](results/README.md)

计划顺序固定为：Slice1 先让一条代表问题跑通最小认知—自适应调查—来源代理/隔离读取—调查记录—证据包—回答/审核真实 Web 纵切，
再用 4 条跨维度问题和现场题确认方向；用户 `CONTINUE` 后才进入跨工程、持久恢复、复杂边界、性能、安全和完整夯实；再次
`CONTINUE` 后才正式验收。三臂消融的新协议、阈值和 digest 尚未获授权，必须在 Slice2 前以新的用户收据冻结。
