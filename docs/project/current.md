---
id: PROJECT-CURRENT
kind: project-current
status: current
authority: current-development
owners: [project]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ITER-001-INDEX, ITER-002-INDEX, ITER-002-RESULT-ACCEPTANCE, ITER-003-INDEX, ITER-003-RESULT-ACCEPTANCE]
code: []
tests: []
as_of: 2026-08-11
active_iteration: none
active_slice: none
worktree_status: clean-governance-closure
strategy_relation: local-maven-structure-world-model-evaluation-only-accepted-not-active
live_model_path: local-evidence-first-accepted-world-model-path-not-active
---

# 当前工作上下文

## 开发授权

**当前没有活动开发迭代或已授权 Development Slice。** Iteration 003 已按本机 Maven Structure World Model
`EVALUATION_ONLY` 纵向闭环接受并关闭；Iteration 与 Slice 均不再是编码输入。接受对象是 product checkpoint
`b9b329a9b341b01fc41486ef9b0c809ac8665332`，由独立 evaluator checkpoint `9977269…` 裁决为 60/60
PASS，并通过真实浏览器 G4 与 750 项完整回归。初始 G3b 58/60 FAIL 与全部失败尝试仍永久保留。

## 当前系统与实现状态

| 范围 | 状态 | 证据边界 |
|---|---|---|
| Iteration 001 历史裁决 | Completed / pre-Git attestation | 正式知识单路径和本机体验的历史结果；原运行没有 exact Git identity，Production Activation 未执行 |
| Iteration 002 | **Completed / narrow acceptance** | exact 实现提交 `e5b030c6835a69c70153d90f62803d63b7a4ba75`；只接受 Evidence-first 本机同步问答实验，六题与直接源码基线打平 |
| Iteration 003 | **Completed / narrow acceptance** | 接受本机 Maven Structure World Model `EVALUATION_ONLY` 纵向闭环；修复后全新 G3b batch/evaluator 60/60 PASS，G4 与 750 项回归 PASS |
| Evidence-first Strategy | PASS / exact and time-bound | `evidence-first-software-answer@1.0.0` 的十类能力、两个 Java 工程六题和本机浏览器体验通过；它读取任务级 Evidence Packet，不是 Snapshot 世界模型问答 |
| 软件世界模型产品闭环 | **ACCEPTED / local Maven evaluation-only** | typed Structure Kernel、独立更新、Source-off View/Citation、Snapshot-first 回答、真实模型对照与浏览器产品验收通过；不扩展到其他语言/知识域或 live activation |
| `local-browser` | Local Evidence-first experience only | Activation `activation_decision_af90ea83192f441eb7140a011340221c` 只绑定 ITER-002 exact 能力与产品证明，不授权新的世界模型实现 |
| Production Activation | **NOT EXECUTED** | 不得由任何本机 PASS 自动推导 |

精确边界见 [Iteration 003 Acceptance](iterations/iteration-003/results/acceptance.md)。原始 Provider、能力、
产品和浏览器证据保存在本机 `var/`，只通过 Result 中的 ID、Digest 和路径引用，不进入 Git。

## 下一决策

后续若要扩大到自动 Scheduler、多源/跨 Scope、旧 Scope Schema Migration、其他构建系统/知识域，必须建立新
Iteration 并冻结相应 Contract、Oracle 和失败条件。若要把已接受的评测路径切换为本机默认或生产路径，必须单独完成
Activation 决策、运行权限和运维验收，不能从 ITER-003 PASS 自动推导。

[生产启用](roadmap/candidates/production-activation.md)、[Schema Evolution](roadmap/candidates/schema-evolution.md) 和超出 Structure 范围的 Semantic View 仍不自动获得授权。

## Agent 读取范围

没有活动 Slice 时，Agent 可以在用户新的明确请求下准备 Proposal、System 决策、契约、冻结验证和 Readiness；在
`project/current.md` 原子指向已授权的新 Iteration/Slice 前不得修改产品代码。ITER-003 只作历史证据，不授权继续调用
Provider、扩大范围或执行 Production Activation。
