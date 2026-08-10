---
id: PROJECT-CURRENT
kind: project-current
status: current
authority: current-development
owners: [project]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ITER-001-INDEX, ITER-002-INDEX, ITER-002-RESULT-ACCEPTANCE, ITER-003-INDEX, ITER-003-SLICE-001]
code: []
tests: []
as_of: 2026-08-10
active_iteration: ITER-003-INDEX
active_slice: ITER-003-SLICE-001
worktree_status: clean-iteration-003-g0-pass-g1-authorized
strategy_relation: iteration-003-g0-pass-deterministic-g1-next
live_model_path: local-evidence-first-accepted-world-model-path-not-active
---

# 当前工作上下文

## 开发授权

**ITER-003 / SLICE-001 已由用户明确授权，G0 已 PASS，当前开放 G1。** 准备提交 P 为 `a4ae307c8ab04979e87e0460f19b6ec81fc915a3`，授权治理提交 Q 为 `42a3f1ababed73cded8aafb046105309a79c170e`，G0 exact 输入 checkpoint 为 `af849fb198179cfe1d1514f272a1a06236684f43`。后续按 G1→G2→G3a→G3b→G4 阻断顺序推进；外部模型披露仍需在首次 CE 或模型分派前单独确认。

## 当前系统与实现状态

| 范围 | 状态 | 证据边界 |
|---|---|---|
| Iteration 001 历史裁决 | Completed / pre-Git attestation | 正式知识单路径和本机体验的历史结果；原运行没有 exact Git identity，Production Activation 未执行 |
| Iteration 002 | **Completed / narrow acceptance** | exact 实现提交 `e5b030c6835a69c70153d90f62803d63b7a4ba75`；只接受 Evidence-first 本机同步问答实验，六题与直接源码基线打平 |
| Iteration 003 | **In progress / G0 PASS** | Structure World Model 纵向闭环已通过冻结输入 Gate；当前只开放 G1 Knowledge Kernel，G1 PASS 前禁止 Structure View/UI |
| Evidence-first Strategy | PASS / exact and time-bound | `evidence-first-software-answer@1.0.0` 的十类能力、两个 Java 工程六题和本机浏览器体验通过；它读取任务级 Evidence Packet，不是 Snapshot 世界模型问答 |
| 软件世界模型产品闭环 | **NOT ACCEPTED** | Structure View、source-disabled Snapshot 问答、独立更新、类型化关系、跨版本稳定身份和 replacement 删除语义未在 ITER-002 验证 |
| `local-browser` | Local Evidence-first experience only | Activation `activation_decision_af90ea83192f441eb7140a011340221c` 只绑定 ITER-002 exact 能力与产品证明，不授权新的世界模型实现 |
| Production Activation | **NOT EXECUTED** | 不得由任何本机 PASS 自动推导 |

精确边界见 [Iteration 002 Acceptance](iterations/iteration-002/results/acceptance.md)。原始 Provider、能力和产品证据保存在本机 `var/`，只通过 Result 中的 ID、Digest 和路径引用，不进入 Git。

## 当前执行顺序

执行类型化 Relation/Literal Fact、Entity/Fact/Coverage Root/State、endpoint closure、显式 `ENRICH`/`REPLACE_COVERAGE` 和 Maven Structure builder 的 G1。必须保存 A→B→A、悬空/歧义/重叠/CAS 反例、旧 Snapshot 只读兼容和逐行 CLI 报告；G1 Result 提交为 PASS 前不得进入 Structure View、浏览器或模型答案。

[生产启用](roadmap/candidates/production-activation.md)、[Schema Evolution](roadmap/candidates/schema-evolution.md) 和超出 Structure 范围的 Semantic View 仍不自动获得授权。

## Agent 读取范围

Agent 必须读取 ITER-003 的 Proposal、Manifest、Readiness、当前 Slice、Verification Matrix 与上一 Gate Result，并只跟随其中引用的 System 文档。当前执行 G1；上一 Gate 的 PASS 不得替代本 Gate 的实现与人工证据。
