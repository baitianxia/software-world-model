---
id: PROJECT-CURRENT
kind: project-current
status: current
authority: current-development
owners: [project]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ITER-001-INDEX, ITER-002-INDEX, ITER-002-RESULT-ACCEPTANCE, ITER-003-INDEX, ITER-003-RESULT-ACCEPTANCE, ITER-004-INDEX, ITER-004-RESULT-ACCEPTANCE, ITER-005-INDEX, ITER-005-SLICE-001, ITER-005-SLICE-002, ITER-005-RESULT-SLICE-001, ITER-005-RESULT-SLICE-002-RUN-006, ITER-005-RESULT-SLICE-002-CANDIDATE-FREEZE, ITER-005-RESULT-SLICE-002-RUN-007]
code: []
tests: []
as_of: 2026-08-12
active_iteration: ITER-005-INDEX
active_slice: ITER-005-SLICE-002
worktree_status: iteration-005-slice-002-run-007-live-pass-awaiting-user-acceptance
strategy_relation: accepted-iteration-004-fixed-read-sets-to-user-selected-maven-workspace
live_model_path: run-006-fail-preserved-run-007-evaluation-pass-production-activation-not-executed
---

# 当前工作上下文

## 开发授权

`ITER-005-SLICE-001` 已实现并通过 V-002—V-005；用户于 `2026-08-11T19:32:39+08:00` 接受该 Result 并授权进入
`ITER-005-SLICE-002`。正式动态 Web 入口、candidate Answer/Gateway wrapper、动态 Catalog binding、comparison controller
与独立 comparator 已实现。`run-006` 的真实浏览器 PASS、comparison FAIL 原样保留；`FINDING-005-009/010` 后的新
`run-007` suite 已获得绑定三条 disclosure 的当前用户授权，并按 baseline-first 顺序完成真实比较与浏览器验收。三条
population 均 9/9，independent evaluator 与真实浏览器均 PASS。SLICE-002 与 ITER-005 现等待用户接受 Result；Production
Activation 从未执行。

## 当前系统与实现状态

| 范围 | 状态 | 证据边界 |
|---|---|---|
| Iteration 001 历史裁决 | Completed / pre-Git attestation | 正式知识单路径和本机体验的历史结果；原运行没有 exact Git identity，Production Activation 未执行 |
| Iteration 002 | **Completed / narrow acceptance** | exact 实现提交 `e5b030c6835a69c70153d90f62803d63b7a4ba75`；只接受 Evidence-first 本机同步问答实验，六题与直接源码基线打平 |
| Iteration 003 | **Completed / narrow acceptance** | 接受本机 Maven Structure World Model `EVALUATION_ONLY` 纵向闭环；修复后全新 G3b batch/evaluator 60/60 PASS，G4 与 750 项回归 PASS |
| Iteration 004 | **Completed / narrow acceptance** | implementation `6bacfdfa…`；自由问题已接到 accepted Snapshot-first WORLD_MODEL 隔离链路，真实浏览器、Gap、Citation、失败关闭和 761 项回归 PASS |
| Iteration 005 | **Active / verification complete, awaiting user acceptance** | G0 与 V-002—V-005 PASS；SLICE-001 已接受；`run-006` 失败保留；`run-007` 在 exact 授权下 Direct/Mature/World 各 9/9，comparison 与真实浏览器 PASS，51 focused、13 staged Answer、801 full regression 和 docs gate PASS |
| Evidence-first Strategy | PASS / exact and time-bound | `evidence-first-software-answer@1.0.0` 的十类能力、两个 Java 工程六题和本机浏览器体验通过；它读取任务级 Evidence Packet，不是 Snapshot 世界模型问答 |
| 软件世界模型产品闭环 | **ACCEPTED / local Maven evaluation-only** | typed Structure Kernel、独立更新、Source-off View/Citation、Snapshot-first 回答、真实模型对照与浏览器产品验收通过；不扩展到其他语言/知识域或 live activation |
| `local-browser` | Two explicit local evaluation surfaces | 原 `http_api` 仍是 ITER-002 Direct；独立 `55121` 入口是 ITER-003/004 World Model EVALUATION_ONLY，二者不互相兜底 |
| Production Activation | **NOT EXECUTED** | 不得由任何本机 PASS 自动推导 |

精确产品边界见 [Iteration 003 Acceptance](iterations/iteration-003/results/acceptance.md)，交互入口边界见
[Iteration 004 Acceptance](iterations/iteration-004/results/acceptance.md)。原始 Provider、能力、产品和浏览器证据
保存在本机 `var/`，只通过 Result 中的 ID、Digest 和路径引用，不进入 Git。

## 当前执行顺序

当前 `ITER-005-SLICE-002` 的实现与验证已经完成，活动状态只为等待用户裁决。exact live subject 绑定 producer commit
`0c2b155d…`、stage `sha256:7cf5e832…`、held-out suite `sha256:04f50cae…`、authorization
`sha256:a33d6537…`、independent evaluator `sha256:020287ba…` 与 comparison runner `sha256:e3da9685…`。baseline seal
`sha256:cd193c00…` 证明 Direct/Mature 各 9 条在 World Model 为 0 条时先行密封；comparison
`sha256:e7d16fa4…` 为 PASS。真实浏览器 supported/Gap/Citation/长 identity 布局与 console 均通过，服务已停止。
下一步由用户明确接受、拒绝或决定后续；在此之前不得把 Result 改写为 accepted/completed。

[生产启用](roadmap/candidates/production-activation.md)、[Schema Evolution](roadmap/candidates/schema-evolution.md) 和超出 Structure 范围的 Semantic View 仍不自动获得授权。

## Agent 读取范围

Agent 先读取 ITER-005 的 Proposal、Manifest、Readiness、`SLICE-002-dynamic-world-model-browser`、SLICE-001 Result、
[Run-007 Live Result](iterations/iteration-005/results/slice-002-run-007-live.md) 与 Verification Matrix，再按其引用读取 System
Contract。当前 live gate 已闭合但用户 Acceptance 尚未发生；不得重跑或改写三条 population，不得改变旧 `http_api`
Direct 行为，也不得执行 Production Activation。
