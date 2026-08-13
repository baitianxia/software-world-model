---
id: ITER-007-INDEX
kind: iteration-index
status: proposed
authority: project-governance
owners: [product, project, engineering, quality]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ITER-007-PROPOSAL, ITER-007-READINESS, ITER-007-VERIFICATION, ITER-007-SLICE-001, ITER-007-SLICE-002, ITER-007-SLICE-003]
code: []
tests: []
iteration: ITER-007
coding_input: false
---

# ITER-007：Java 源码实现语义与通用源码问答首个累积切片

## Status and authorization

`PROPOSED / NOT READY / NOT AUTHORIZED`。

本目录只固定下一轮候选计划，不授权产品代码开发，也不改变 `project/current.md`。进入 Readiness 前至少要：

1. 用户接受 ITER-006，并明确登记 method inventory 排序、调用方向和“异常路径”路由三项限制；代码修复属于 SLICE-001 的退出
   Gate。若 ITER-006 被拒绝，必须重做本 Proposal，不能沿用跨域依赖继续；
2. 冻结 accepted baseline、Java frontend、Source Semantics/no-payload/功能发现/三调用模型 Contract；
3. 由独立方冻结 SLICE-001/002 各自的小型隐藏 canary，并冻结两份最终 held-out 工程的身份/源码、12+4 问题、baseline/target 和
   成熟源码 Agent 对照协议；
4. 用户对 exact Product-goal alignment 作语义评审并明确授权。

## Required inputs

- [Proposal](proposal.md)
- [Manifest](manifest.yaml)
- [Readiness Review](readiness-review.md)
- [Development Design](development-design/README.md)
- [Verification Matrix](verification-matrix.md)
- [Findings](findings/README.md)
- [Results](results/README.md)

## 开发顺序

1. 最小方法体语义和功能到代码发现，立即走真实模型与正式 Web；冻结本段代码后通过第一个独立隐藏 canary 才能继续；
2. 只在可见开发语料上加固 Java frontend、语义、更新和持久化，再次人工 Web 验证；冻结本段代码后通过第二个独立隐藏 canary；
3. 产品代码冻结后才运行此前完全未参与实现的两份工程、隐藏题和现场题。

本轮不把 README、配置、运行数据或多语言混进同一 Slice。它先回答一个更根本的问题：预先构建的软件世界模型能否在不读源码的
问答阶段，仅凭正式 Java 实现语义，定位业务功能并解释代码实现和调用逻辑。
