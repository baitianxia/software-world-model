---
id: ITER-008-INDEX
kind: iteration-index
status: authorized
authority: current-development
owners: [product, project, architecture, engineering, quality]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ROADMAP-M-002, ITER-007-RESULT-SLICE-001-STOP-DECISION, ITER-008-PROPOSAL, ITER-008-READINESS, ITER-008-VERIFICATION, ITER-008-SLICE-001, ITER-008-SLICE-002]
code: []
tests: []
iteration: ITER-008
coding_input: true
---

# ITER-008：受限 Agent 驱动的 World Model 调查问答

## Status and authorization

`AUTHORIZED / SLICE-001 IN PROGRESS / SLICE-002 NOT AUTHORIZED`。

本轮不改变“软件世界模型”目标。回答所依据的事实仍必须在提问前进入版本固定、可复用的 World Model；Agent 只负责根据查询结果
决定下一步查什么，不能读取源码、触发更新或转入 Direct 回答。

`SYS-ADR-015`、System Contract fileset、baseline `38ebed2…`、调查预算、Agent/rubric、正向价值阈值与用户持有的隐藏披露协议已
冻结。用户以 `codex-user-message:sha256:eb381cfd…7221` 接受 Readiness 并单独授权 `SLICE-001`。本授权不包含 `SLICE-002`、
任何 live Provider 问题披露、Production Activation、提交后的隐藏题修补或 Direct fallback。

## Required inputs

- `ITER-005/006` Acceptance：Workspace、无问题更新、Snapshot、正式 Web、Citation、Java declaration 与窄范围 `CALLS`；
- `ITER-007-RESULT-SLICE-001-STOP-DECISION`：固定单方法协议的产品失败证据；
- `FINDING-007-008/009`：多候选组合失败和不存在功能的负向判定失败；
- `ROADMAP-M-002` Step 1：Java 结果驱动的 World Model 调查；
- Readiness 前新接受的 bounded investigation 架构与 Contract。

ITER-007 的 Java Source Semantics 实现只能作为待重新验收的技术资产，不能列入已接受能力。

## Iteration content

全轮有两个依次单独授权的纵向 Slice。每个 Slice 都固定执行“实现 → 同一正式 Web/隐藏输入体验 → 成熟基线对照 → 方案复盘 →
继续/接受/转向/拒绝”：

1. `SLICE-001` 先完成最小结果驱动调查闭环，并用公开回归、一组代码冻结后才披露的早期 canary 和成熟源码 Agent 同题对照尽快
   证伪架构；只有复盘决定 `CONTINUE` 才可申请下一段授权；
2. `SLICE-002` 只在前一段 PASS 后加固分页、三层完整性、安全和预算，再执行两个最终隐藏工程与成熟源码 Agent 逐题比较。

两段都必须形成独立 `V-REFLECT` Result。Reflection PASS 只表示复盘做完；没有中间 `CONTINUE` 或最终 `ACCEPT`，不能继续开发或
接受本轮。

Agent 仅调用 typed World Model 查询，跨多个候选与方法继续调查。负向结论必须分别证明查询结果完整、知识表示 Coverage 完整和业务
语义发现召回完整；任一层不能证明时只能返回 Limitation。

公开的登录/下单问题只作回归。早期 canary 与最终两个隐藏工程互不复用，且都只能在对应产品代码冻结后披露。

## Exit meaning

若本轮通过，`ROADMAP-M-002` Step 1 才完成：系统证明“预构建 World Model 可以支持结果驱动的通用 Java 调查”，下一步才是
真实 Java 工程与语法广度。若失败，保留 Result 并继续停留在 Step 1，不得跳去 README、配置、多语言或生产启用。
