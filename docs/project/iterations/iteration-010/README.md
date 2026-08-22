---
id: ITER-010-INDEX
kind: iteration-index
status: rejected
authority: project-decision
owners: [product, project, architecture, engineering, quality]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ROADMAP-M-002, ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, ITER-010-PROPOSAL, ITER-010-READINESS, ITER-010-VERIFICATION, ITER-010-SLICE-001, ITER-010-SLICE-002, ITER-010-SLICE-003, FINDING-010-028, ITER-010-RESULT-SLICE-001-STOP-REDIRECT]
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

`REJECTED / SLICE-001 BLOCKED / SLICE-002 AND SLICE-003 PROPOSED BUT NOT AUTHORIZED / REDIRECTED WITHOUT ACCEPTANCE`。

Slice1 已完成 4 条公开方向题和用户现场题。真实 Web、受控调查、Broker/Worker、Ledger/Package、Citation、独立 Review 与失败关闭技术链
能够运行；现场登录答案却仍由 Controller/Service/Filter 方法序列主导，并省略登录日志副作用，Reviewer 无 Finding 批准。

用户以 `codex-user-message:sha256:d746968f58cea4d2b7689b5902c0ff97f42f63c93ffc4cbc40551cfa2c0359e0`
作出 `REDIRECT`。`ITER-010-RESULT-SLICE-001-STOP-REDIRECT` 保留 exact 证据与架构反思；`FINDING-010-028` 将根因定位到自由文本抽象
层级、扁平 Answer Claim 和不可执行的 Review 方向质量 Gate。本轮不再是编码输入；Slice2/3 从未授权，不能在 ITER-010 中继续。

用户消息 `codex-user-message:sha256:d3b60bdaa52d96ced3c653a8dcd54fabff41beb7f23f0bf691e6983ebb9437bc` 于
`2026-08-21T08:23:25Z` 要求按最新讨论重新制定计划并更新文档。它确认：World Model 仍是真正的软件外部认知；提问期由 LLM 主导
自适应调查，Broker/Worker 控制实际读取，调查后 seal，Reviewer 可独立要求补证。

该收据曾只授权重制计划和文档。用户随后以
`codex-user-message:sha256:585f02c4edcf25502b40f880c17a7bdf7f1af71044cd8d1bbe97b055a735ee9e`（`2026-08-21T09:18:34Z`）
接受 Readiness，并只授权 `ITER-010-SLICE-001` 产品代码开发与本地确定性验证。后续 exact grants 已完成本 Slice 所需 Provider/model 与
loopback Web/browser 验证；`SLICE-002/003`、hidden disclosure 和 Production Activation 从未授权。所有 live grants 均已消费或停止，
不得跨新 Iteration 复用。此前 `1b327024… + 5cdb7000…` 仍只绑定被取代的设计。

本轮产品基线固定为 commit `1fb997bab6444523f82ebf1a514a1abbf79656c7`、tree
`1369ce932c778c57a118123e8257ede476229d73`；授权审核的 planning commit/tree 为
`01dcfe2233625dfaa021495850fb18ae1323063b` / `8e364ae854bfaa48580ab080a3e0d9c9c43c3d6f`。ITER-009 的体验代码保留为技术资产，但其代码走读式产品方向已由
`ITER-009-RESULT-SLICE-001-STOP-REDIRECT` 否决，不能被写成 Acceptance。

## Required inputs

- [Proposal](proposal.md)
- [Manifest](manifest.yaml)
- [Verification Matrix](verification-matrix.md)
- [Readiness Review](readiness-review.md)
- [Development Design](development-design/README.md)
- [Findings](findings/README.md)
- [Results](results/README.md)

原计划在 Slice1 的方向 Gate 停止：技术链完成，但答案/审核方向失败。A3 FALSIFIED，A1/A4/A5 UNRESOLVED；Slice2/3、三臂消融、
hidden、正式验收和 Production 均未执行。若继续最终目标，必须从新的 Iteration Proposal/Readiness 和逐 Slice 用户授权重新开始，不能
重新激活本 rejected Iteration。
