---
id: PROJECT-CURRENT
kind: project-current
status: current
authority: current-development
owners: [project]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ITER-001-INDEX, ITER-002-INDEX, ITER-002-RESULT-ACCEPTANCE, ITER-003-INDEX, ITER-003-RESULT-ACCEPTANCE, ITER-004-INDEX, ITER-004-RESULT-ACCEPTANCE, ITER-005-INDEX, ITER-005-RESULT-ACCEPTANCE]
code: []
tests: []
as_of: 2026-08-12
active_iteration: none
active_slice: none
worktree_status: iteration-005-accepted-no-active-development
strategy_relation: accepted-user-selected-maven-workspace-with-product-web-qa
live_model_path: local-maven-structure-world-model-evaluation-only-not-production-activated
---

# 当前工作上下文

## 开发授权

当前没有活动开发 Iteration 或 Slice。用户于 `2026-08-12T08:44:55+08:00` 接受 ITER-005：用户指定的本机 Maven
Workspace 可在零问题状态构建或显式更新 exact Snapshot，生成动态 no-payload Read Set，并通过产品自有 Web 入口完成
Source-off Structure 问答、Gap 与 Citation。接受对象为 implementation commit `956f31d6…`；Production Activation 从未执行。

## 当前系统与实现状态

| 范围 | 状态 | 证据边界 |
|---|---|---|
| Iteration 001 历史裁决 | Completed / pre-Git attestation | 正式知识单路径和本机体验的历史结果；原运行没有 exact Git identity，Production Activation 未执行 |
| Iteration 002 | **Completed / narrow acceptance** | exact 实现提交 `e5b030c6835a69c70153d90f62803d63b7a4ba75`；只接受 Evidence-first 本机同步问答实验，六题与直接源码基线打平 |
| Iteration 003 | **Completed / narrow acceptance** | 接受本机 Maven Structure World Model `EVALUATION_ONLY` 纵向闭环；修复后全新 G3b batch/evaluator 60/60 PASS，G4 与 750 项回归 PASS |
| Iteration 004 | **Completed / narrow acceptance** | implementation `6bacfdfa…`；自由问题已接到 accepted Snapshot-first WORLD_MODEL 隔离链路，真实浏览器、Gap、Citation、失败关闭和 761 项回归 PASS |
| Iteration 005 | **Completed / narrow acceptance** | implementation `956f31d6…`；用户指定 Maven Workspace、零问题显式更新、动态 Read Set 与正式 Web 问答完成；`run-006` 失败保留，`run-007` 三路各 9/9、comparison 与真实浏览器 PASS |
| Evidence-first Strategy | PASS / exact and time-bound | `evidence-first-software-answer@1.0.0` 的十类能力、两个 Java 工程六题和本机浏览器体验通过；它读取任务级 Evidence Packet，不是 Snapshot 世界模型问答 |
| 软件世界模型产品闭环 | **ACCEPTED / local Maven evaluation-only** | typed Structure Kernel、独立更新、Source-off View/Citation、Snapshot-first 回答、真实模型对照与浏览器产品验收通过；不扩展到其他语言/知识域或 live activation |
| `local-browser` | Two explicit local evaluation surfaces | 原 `http_api` 仍是 ITER-002 Direct；独立产品入口是 ITER-003—005 World Model EVALUATION_ONLY，支持动态 Maven Read Set，二者不互相兜底 |
| Production Activation | **NOT EXECUTED** | 不得由任何本机 PASS 自动推导 |

精确产品边界见 [Iteration 005 Acceptance](iterations/iteration-005/results/acceptance.md)。原始 Provider、能力、产品和浏览器证据
保存在本机 `var/`，只通过 Result 中的 ID、Digest 和路径引用，不进入 Git。

## 当前执行顺序

ITER-005 已完成，没有剩余执行步骤。下一轮若扩展代码语义、Behavior、Business、History、其他语言或自动刷新，必须建立
新的 Proposal、Readiness 和人工可体验 Slice；不得把 ITER-005 的 Maven Structure Acceptance 扩张解释为这些能力。

[生产启用](roadmap/candidates/production-activation.md)、[Schema Evolution](roadmap/candidates/schema-evolution.md) 和超出 Structure 范围的 Semantic View 仍不自动获得授权。

## Agent 读取范围

当前没有活动 Slice；ITER-005 目录只作历史证据，不再授权编码。Agent 若只需启动已接受体验，应遵守
`SYS-OPS-LOCAL-BROWSER`。任何新知识域或产品修改必须先建立并授权新 Iteration；不得改变旧 `http_api` Direct 行为，
也不得执行 Production Activation。
