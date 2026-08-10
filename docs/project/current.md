---
id: PROJECT-CURRENT
kind: project-current
status: current
authority: current-development
owners: [project]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ITER-001-INDEX, ITER-002-INDEX, ITER-002-RESULT-ACCEPTANCE]
code: []
tests: []
as_of: 2026-08-10
active_iteration: none
active_slice: none
worktree_status: clean-governance-closure
strategy_relation: evidence-first-experiment-accepted-world-model-revision-pending
live_model_path: local-evidence-first-accepted-world-model-path-not-active
---

# 当前工作上下文

## 开发授权

**当前没有活动开发迭代或已授权 Development Slice。** Iteration 002 已按本机 Evidence-first 同步问答实验范围接受并关闭；它不再是编码输入，也没有完成软件世界模型目标。用户已经授权继续准备下一轮，但产品代码必须等新 Iteration 的 System 决策、契约、冻结 Oracle 和 Readiness 全部闭合后才能开始。

## 当前系统与实现状态

| 范围 | 状态 | 证据边界 |
|---|---|---|
| Iteration 001 历史裁决 | Completed / pre-Git attestation | 正式知识单路径和本机体验的历史结果；原运行没有 exact Git identity，Production Activation 未执行 |
| Iteration 002 | **Completed / narrow acceptance** | exact 实现提交 `e5b030c6835a69c70153d90f62803d63b7a4ba75`；只接受 Evidence-first 本机同步问答实验，六题与直接源码基线打平 |
| Evidence-first Strategy | PASS / exact and time-bound | `evidence-first-software-answer@1.0.0` 的十类能力、两个 Java 工程六题和本机浏览器体验通过；它读取任务级 Evidence Packet，不是 Snapshot 世界模型问答 |
| 软件世界模型产品闭环 | **NOT ACCEPTED** | Structure View、source-disabled Snapshot 问答、独立更新、类型化关系、跨版本稳定身份和 replacement 删除语义未在 ITER-002 验证 |
| `local-browser` | Local Evidence-first experience only | Activation `activation_decision_af90ea83192f441eb7140a011340221c` 只绑定 ITER-002 exact 能力与产品证明，不授权新的世界模型实现 |
| Production Activation | **NOT EXECUTED** | 不得由任何本机 PASS 自动推导 |

精确边界见 [Iteration 002 Acceptance](iterations/iteration-002/results/acceptance.md)。原始 Provider、能力和产品证据保存在本机 `var/`，只通过 Result 中的 ID、Digest 和路径引用，不进入 Git。

## 下一决策

下一轮必须从 ITER-002 关闭后的干净提交开始，以一个 Maven Structure World Model 纵向切片先验证：类型化实体关系、Root/State 稳定身份、`REPLACE_COVERAGE`、exact Snapshot 查询，以及关闭 Source Provider 后仍能从 Structure View 回答冻结问题。任何一项基础反例未通过，都不能继续浏览器或 Agent 开发。

[生产启用](roadmap/candidates/production-activation.md)、[Schema Evolution](roadmap/candidates/schema-evolution.md) 和超出 Structure 范围的 Semantic View 仍不自动获得授权。

## Agent 读取范围

没有活动 Slice 时，Agent 可以在用户本次明确授权下准备下一轮 Proposal、System 决策、契约、冻结验证和 Readiness；在 `project/current.md` 原子指向已授权的新 Iteration/Slice 前，不得修改产品代码。
