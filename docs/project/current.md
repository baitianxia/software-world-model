---
id: PROJECT-CURRENT
kind: project-current
status: current
authority: current-development
owners: [project]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ITER-001-INDEX, ITER-002-INDEX, ITER-002-RESULT-ACCEPTANCE, ITER-003-INDEX, ITER-003-SLICE-001, ITER-003-RESULT-G3A]
code: []
tests: []
as_of: 2026-08-10
active_iteration: ITER-003-INDEX
active_slice: ITER-003-SLICE-001
worktree_status: clean-iteration-003-g3a-pass-external-disclosure-confirmation-required
strategy_relation: iteration-003-g3a-pass-external-disclosure-confirmation-required-before-v009
live_model_path: local-evidence-first-accepted-world-model-path-not-active
---

# 当前工作上下文

## 开发授权

**ITER-003 / SLICE-001 已由用户明确授权，G0、G1、G2 与 G3a/V-008 已 PASS；当前执行必须停止在 V-009 之前。** 准备提交 P 为 `a4ae307c8ab04979e87e0460f19b6ec81fc915a3`，授权治理提交 Q 为 `42a3f1ababed73cded8aafb046105309a79c170e`，G0 exact 输入 checkpoint 为 `af849fb198179cfe1d1514f272a1a06236684f43`，G1 exact 实现 checkpoint 为 `ddb8f5feba1e0c52d2f788c2bb66c93810f2b469`，G2 exact 实现 checkpoint 为 `82aef7563556c70527b3c92227d0711a28437587`，G3a exact 实现 checkpoint 为 `f2269ecca5c1e85e69fafd93fe599c841227f3c7`。现有开发授权不构成任何内容向外部 Provider 的披露确认；只有用户在后续独立消息中明确确认本轮披露，且 exact Provider/Adapter/Model、endpoint、credential reference、default-deny egress policy 与 Conformance 输入全部冻结后，才可开始 V-009。

## 当前系统与实现状态

| 范围 | 状态 | 证据边界 |
|---|---|---|
| Iteration 001 历史裁决 | Completed / pre-Git attestation | 正式知识单路径和本机体验的历史结果；原运行没有 exact Git identity，Production Activation 未执行 |
| Iteration 002 | **Completed / narrow acceptance** | exact 实现提交 `e5b030c6835a69c70153d90f62803d63b7a4ba75`；只接受 Evidence-first 本机同步问答实验，六题与直接源码基线打平 |
| Iteration 003 | **In progress / G3a PASS** | no-payload Bundle、Source-off View/Citation 与十阶段 offline answer authority chain 已在 exact checkpoints 上通过 V-007/V-008；外部披露、V-009、G3b/G4 仍阻断 |
| Evidence-first Strategy | PASS / exact and time-bound | `evidence-first-software-answer@1.0.0` 的十类能力、两个 Java 工程六题和本机浏览器体验通过；它读取任务级 Evidence Packet，不是 Snapshot 世界模型问答 |
| 软件世界模型产品闭环 | **NOT ACCEPTED** | typed Structure Kernel、Source-off View 与 offline 回答权威链已在 ITER-003 G1/G2/G3a 通过；外部执行资格、真实模型浏览器质量、Product Validation 与 Activation 尚未通过 |
| `local-browser` | Local Evidence-first experience only | Activation `activation_decision_af90ea83192f441eb7140a011340221c` 只绑定 ITER-002 exact 能力与产品证明，不授权新的世界模型实现 |
| Production Activation | **NOT EXECUTED** | 不得由任何本机 PASS 自动推导 |

精确边界见 [Iteration 002 Acceptance](iterations/iteration-002/results/acceptance.md)。原始 Provider、能力和产品证据保存在本机 `var/`，只通过 Result 中的 ID、Digest 和路径引用，不进入 Git。

## 当前执行顺序

当前没有获授权的下一执行步骤。`ITER-003-RESULT-G3A` 已只裁决 V-008；必须停止在 V-009 之前，不得选择或调用外部 Provider/Adapter/Model，不得运行 CC/CE 或两条 baseline，也不得披露源码、Bundle、结构结果、问题文本或其他内容。只有用户在后续独立消息中明确确认本轮外部披露，并完成 V-009 所需 exact Provider/Adapter/Model、scheme/host/port/path、credential reference、default-deny Model Egress Gateway policy 与 Conformance 输入冻结后，才能继续。

[生产启用](roadmap/candidates/production-activation.md)、[Schema Evolution](roadmap/candidates/schema-evolution.md) 和超出 Structure 范围的 Semantic View 仍不自动获得授权。

## Agent 读取范围

Agent 必须读取 ITER-003 的 Proposal、Manifest、Readiness、当前 Slice、Verification Matrix 与 G3a Result，并只跟随其中引用的 System 文档。G3a/V-008 PASS 不授权 V-009、外部披露、Provider/Adapter/Model 选择或调用、CC/CE、baseline、G3b/G4、Product Validation 或 Activation；没有用户后续独立披露确认时必须停止。
