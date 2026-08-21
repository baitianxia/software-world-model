---
id: ITER-008-INDEX
kind: iteration-index
status: rejected
authority: project-decision
owners: [product, project, architecture, engineering, quality]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ROADMAP-M-002, ITER-007-RESULT-SLICE-001-STOP-DECISION, ITER-008-PROPOSAL, ITER-008-READINESS, ITER-008-VERIFICATION, ITER-008-SLICE-001, ITER-008-SLICE-002, FINDING-008-043, ITER-008-RESULT-SLICE-001-STOP-REDIRECT]
code: []
tests: []
iteration: ITER-008
coding_input: false
---

# ITER-008：受限 Agent 驱动的 World Model 调查问答

## Status and authorization

`REJECTED / SLICE-001 BLOCKED / SLICE-002 PROPOSED AND NOT EXECUTED / REDIRECTED WITHOUT ACCEPTANCE`。

本轮不改变“软件世界模型”目标。回答所依据的事实仍必须在提问前进入版本固定、可复用的 World Model；Agent 只负责根据查询结果
决定下一步查什么，不能读取源码、触发更新或转入 Direct 回答。

run-012 formal freeze 已 PASS；同一 frozen candidate 的正式 Web 已正确回答登录流程并给出 4 个 Citation，但下单边界题的正确
Limitation Draft 被 Review 以 `QUERY_INCOMPLETE` 拒绝，未能交付给用户。hidden canary、成熟源码 Agent 对照和差异化价值验证均未
执行。用户以 `codex-user-message:sha256:6ca47f7d…999ed` 决定转入 ITER-009，因此
`ITER-008-RESULT-SLICE-001-STOP-REDIRECT` 将本轮失败保留；不存在 ITER-008 Acceptance 或后续编码授权。

用户报告的 Codex/OpenAI 客户端 prompt admission 阻断按 `FINDING-008-043` 单独归为外部开发工具的环境/配置问题。由于没有本机
产品 receipt，不把它写成产品 Provider、runtime 或架构的已证实根因。

## Required inputs

- `ITER-005/006` Acceptance：Workspace、无问题更新、Snapshot、正式 Web、Citation、Java declaration 与窄范围 `CALLS`；
- `ITER-007-RESULT-SLICE-001-STOP-DECISION`：固定单方法协议的产品失败证据；
- `FINDING-007-008/009`：多候选组合失败和不存在功能的负向判定失败；
- `ROADMAP-M-002` Step 1：Java 结果驱动的 World Model 调查；
- Readiness 前新接受的 bounded investigation 架构与 Contract。

ITER-007 的 Java Source Semantics 实现只能作为待重新验收的技术资产，不能列入已接受能力。

## Iteration content

全轮原计划有两个依次单独授权的纵向 Slice。实际执行到第一个 Slice 后终止：

1. `SLICE-001` 形成 formal freeze 和一条正式 Web 正向成功，但边界交付失败；Reflection 完成并决定 `REDIRECT`，状态为 blocked；
2. `SLICE-002` 从未授权，保持 historical proposal / not-executed，在 rejected ITER-008 中不可再授权。

两段都必须形成独立 `V-REFLECT` Result。Reflection PASS 只表示复盘做完；没有中间 `CONTINUE` 或最终 `ACCEPT`，不能继续开发或
接受本轮。

Agent 仅调用 typed World Model 查询，跨多个候选与方法继续调查。负向结论必须分别证明查询结果完整、知识表示 Coverage 完整和业务
语义发现召回完整；任一层不能证明时只能返回 Limitation。

公开的登录/下单问题只作回归。早期 canary 与最终两个隐藏工程互不复用，且都只能在对应产品代码冻结后披露。

## Exit meaning

本轮没有通过，`ROADMAP-M-002` Step 1 仍未完成。run-012 的代码、测试和正向 Web 证据可由 ITER-009 作为候选技术资产继承并重新
验收；hidden/canary/comparison/Acceptance 与 Production Activation 均不得从本轮推导。
