---
id: PROJECT-CURRENT
kind: project-current
status: current
authority: current-development
owners: [project]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ITER-001-INDEX, ITER-002-INDEX, ITER-002-RESULT-ACCEPTANCE, ITER-003-INDEX, ITER-003-RESULT-ACCEPTANCE, ITER-004-INDEX, ITER-004-RESULT-ACCEPTANCE]
code: []
tests: []
as_of: 2026-08-11
active_iteration: none
active_slice: none
worktree_status: iteration-004-interactive-world-model-browser-completed
strategy_relation: accepted-iteration-003-world-model-has-evaluation-only-interactive-loopback-entry
live_model_path: local-world-model-evaluation-only-interactive-available-not-activated
---

# 当前工作上下文

## 开发授权

当前没有活动开发 Iteration 或 Slice。ITER-004 已按用户授权完成本机 `EVALUATION_ONLY` 交互入口：页面自由输入
现在实际进入 accepted ITER-003 package/Bundles/Gateway/Citation 隔离链路，不再走旧 `/v1/browser/chat`，且禁止
Source/Direct 回退。接受范围和已知限制见 `ITER-004-RESULT-ACCEPTANCE`；Production Activation 未执行。

## 当前系统与实现状态

| 范围 | 状态 | 证据边界 |
|---|---|---|
| Iteration 001 历史裁决 | Completed / pre-Git attestation | 正式知识单路径和本机体验的历史结果；原运行没有 exact Git identity，Production Activation 未执行 |
| Iteration 002 | **Completed / narrow acceptance** | exact 实现提交 `e5b030c6835a69c70153d90f62803d63b7a4ba75`；只接受 Evidence-first 本机同步问答实验，六题与直接源码基线打平 |
| Iteration 003 | **Completed / narrow acceptance** | 接受本机 Maven Structure World Model `EVALUATION_ONLY` 纵向闭环；修复后全新 G3b batch/evaluator 60/60 PASS，G4 与 750 项回归 PASS |
| Iteration 004 | **Completed / narrow acceptance** | implementation `6bacfdfa…`；自由问题已接到 accepted Snapshot-first WORLD_MODEL 隔离链路，真实浏览器、Gap、Citation、失败关闭和 761 项回归 PASS |
| Evidence-first Strategy | PASS / exact and time-bound | `evidence-first-software-answer@1.0.0` 的十类能力、两个 Java 工程六题和本机浏览器体验通过；它读取任务级 Evidence Packet，不是 Snapshot 世界模型问答 |
| 软件世界模型产品闭环 | **ACCEPTED / local Maven evaluation-only** | typed Structure Kernel、独立更新、Source-off View/Citation、Snapshot-first 回答、真实模型对照与浏览器产品验收通过；不扩展到其他语言/知识域或 live activation |
| `local-browser` | Two explicit local evaluation surfaces | 原 `http_api` 仍是 ITER-002 Direct；独立 `55121` 入口是 ITER-003/004 World Model EVALUATION_ONLY，二者不互相兜底 |
| Production Activation | **NOT EXECUTED** | 不得由任何本机 PASS 自动推导 |

精确产品边界见 [Iteration 003 Acceptance](iterations/iteration-003/results/acceptance.md)，交互入口边界见
[Iteration 004 Acceptance](iterations/iteration-004/results/acceptance.md)。原始 Provider、能力、产品和浏览器证据
保存在本机 `var/`，只通过 Result 中的 ID、Digest 和路径引用，不进入 Git。

## 当前执行顺序

本轮执行序列已完成。用户体验时可启动独立 loopback WORLD_MODEL launcher；它会在监听前验证 accepted stage/digest
与 OS isolation preflight。任何漂移、Source/Evidence 可见、Direct fallback 或角色隔离失败都必须阻断。新的产品代码、
知识域、任意仓库建模或 Production Activation 必须建立并授权新 Iteration。

[生产启用](roadmap/candidates/production-activation.md)、[Schema Evolution](roadmap/candidates/schema-evolution.md) 和超出 Structure 范围的 Semantic View 仍不自动获得授权。

## Agent 读取范围

当前没有活动 Slice，ITER-004 目录只作历史证据，不再授权编码。Agent 若只需启动已接受体验，应遵守
`SYS-OPS-LOCAL-BROWSER`；任何修改必须先按治理流程获得新的明确授权。旧 `http_api` 的 Direct 结果仍不得标成
WORLD_MODEL，Production Activation 仍不得由本机 PASS 推导。
