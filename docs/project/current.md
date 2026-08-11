---
id: PROJECT-CURRENT
kind: project-current
status: current
authority: current-development
owners: [project]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ITER-001-INDEX, ITER-002-INDEX, ITER-002-RESULT-ACCEPTANCE, ITER-003-INDEX, ITER-003-RESULT-ACCEPTANCE, ITER-004-INDEX, ITER-004-SLICE-001]
code: []
tests: []
as_of: 2026-08-11
active_iteration: ITER-004-INDEX
active_slice: ITER-004-SLICE-001
worktree_status: iteration-004-interactive-world-model-browser-authorized
strategy_relation: accepted-iteration-003-world-model-awaits-interactive-loopback-entry
live_model_path: local-evidence-first-accepted-world-model-path-not-active
---

# 当前工作上下文

## 开发授权

**ITER-004 / SLICE-001 已由用户明确授权。** 用户实际体验确认 ITER-003 的浏览器工件只能回放冻结 terminal，
正式 Web 自由输入仍走 ITER-002 Evidence-first 路径，因而无法体验最新 Snapshot-first World Model。ITER-004 只补
本机 `EVALUATION_ONLY` 交互入口：复用 accepted ITER-003 package/Bundles/Gateway/Citation 隔离，禁止 Source 回退，
不重写 ITER-003 历史，不执行 Production Activation。

## 当前系统与实现状态

| 范围 | 状态 | 证据边界 |
|---|---|---|
| Iteration 001 历史裁决 | Completed / pre-Git attestation | 正式知识单路径和本机体验的历史结果；原运行没有 exact Git identity，Production Activation 未执行 |
| Iteration 002 | **Completed / narrow acceptance** | exact 实现提交 `e5b030c6835a69c70153d90f62803d63b7a4ba75`；只接受 Evidence-first 本机同步问答实验，六题与直接源码基线打平 |
| Iteration 003 | **Completed / narrow acceptance** | 接受本机 Maven Structure World Model `EVALUATION_ONLY` 纵向闭环；修复后全新 G3b batch/evaluator 60/60 PASS，G4 与 750 项回归 PASS |
| Iteration 004 | **Authorized / interactive remediation** | 把自由问题真正接到 accepted Snapshot-first WORLD_MODEL 隔离链路；范围仅为本机 EVALUATION_ONLY 和既有密封 Maven Read Set |
| Evidence-first Strategy | PASS / exact and time-bound | `evidence-first-software-answer@1.0.0` 的十类能力、两个 Java 工程六题和本机浏览器体验通过；它读取任务级 Evidence Packet，不是 Snapshot 世界模型问答 |
| 软件世界模型产品闭环 | **ACCEPTED / local Maven evaluation-only** | typed Structure Kernel、独立更新、Source-off View/Citation、Snapshot-first 回答、真实模型对照与浏览器产品验收通过；不扩展到其他语言/知识域或 live activation |
| `local-browser` | Local Evidence-first experience only | Activation `activation_decision_af90ea83192f441eb7140a011340221c` 只绑定 ITER-002 exact 能力与产品证明，不授权新的世界模型实现 |
| Production Activation | **NOT EXECUTED** | 不得由任何本机 PASS 自动推导 |

精确边界见 [Iteration 003 Acceptance](iterations/iteration-003/results/acceptance.md)。原始 Provider、能力、
产品和浏览器证据保存在本机 `var/`，只通过 Result 中的 ID、Digest 和路径引用，不进入 Git。

## 当前执行顺序

先实现独立 loopback WORLD_MODEL browser application 与 accepted-artifact runner，再完成无外部调用的机械/隔离测试；
随后按用户已确认的披露边界执行最小 live smoke 和真实浏览器验收。任何 accepted stage/digest/资格漂移、Source/Evidence
可见、Direct fallback 或角色隔离失败都阻断本轮。Production Activation 始终不在执行序列。

[生产启用](roadmap/candidates/production-activation.md)、[Schema Evolution](roadmap/candidates/schema-evolution.md) 和超出 Structure 范围的 Semantic View 仍不自动获得授权。

## Agent 读取范围

Agent 必须读取 ITER-004 Proposal、Manifest、Readiness、当前 Slice 与 Verification Matrix，再跟随其中引用的 System
文档。只可修改本机 EVALUATION_ONLY 交互入口及其验证；不得把旧 `http_api` 的 Direct 结果标成 WORLD_MODEL，不得
扩大知识域或执行 Production Activation。
