---
id: PROJECT-CURRENT
kind: project-current
status: current
authority: current-development
owners: [project]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ITER-001-INDEX, ITER-002-INDEX, ITER-002-RESULT-ACCEPTANCE, ITER-003-INDEX, ITER-003-SLICE-001, ITER-003-RESULT-G2]
code: []
tests: []
as_of: 2026-08-10
active_iteration: ITER-003-INDEX
active_slice: ITER-003-SLICE-001
worktree_status: clean-iteration-003-g2-pass-g3a-authorized
strategy_relation: iteration-003-g2-pass-offline-answer-chain-g3a-next
live_model_path: local-evidence-first-accepted-world-model-path-not-active
---

# 当前工作上下文

## 开发授权

**ITER-003 / SLICE-001 已由用户明确授权，G0、G1 与 G2 已 PASS，当前只开放 G3a 无外部分派实现。** 准备提交 P 为 `a4ae307c8ab04979e87e0460f19b6ec81fc915a3`，授权治理提交 Q 为 `42a3f1ababed73cded8aafb046105309a79c170e`，G0 exact 输入 checkpoint 为 `af849fb198179cfe1d1514f272a1a06236684f43`，G1 exact 实现 checkpoint 为 `ddb8f5feba1e0c52d2f788c2bb66c93810f2b469`，G2 exact 实现 checkpoint 为 `82aef7563556c70527b3c92227d0711a28437587`。后续按 G3a→G3b→G4 阻断顺序推进；外部模型披露仍需在首次 CE 或模型分派前单独确认。

## 当前系统与实现状态

| 范围 | 状态 | 证据边界 |
|---|---|---|
| Iteration 001 历史裁决 | Completed / pre-Git attestation | 正式知识单路径和本机体验的历史结果；原运行没有 exact Git identity，Production Activation 未执行 |
| Iteration 002 | **Completed / narrow acceptance** | exact 实现提交 `e5b030c6835a69c70153d90f62803d63b7a4ba75`；只接受 Evidence-first 本机同步问答实验，六题与直接源码基线打平 |
| Iteration 003 | **In progress / G2 PASS** | no-payload Bundle、Source-off Structure View 与独立 Citation Projector 已在 exact checkpoint 上通过 V-007；当前只开放 G3a 无外部分派回答权威链，外部执行仍阻断 |
| Evidence-first Strategy | PASS / exact and time-bound | `evidence-first-software-answer@1.0.0` 的十类能力、两个 Java 工程六题和本机浏览器体验通过；它读取任务级 Evidence Packet，不是 Snapshot 世界模型问答 |
| 软件世界模型产品闭环 | **NOT ACCEPTED** | typed Structure Kernel 与 Source-off View 已在 ITER-003 G1/G2 通过；完整回答权威链、外部执行资格、真实模型浏览器质量、Product Validation 与 Activation 尚未通过 |
| `local-browser` | Local Evidence-first experience only | Activation `activation_decision_af90ea83192f441eb7140a011340221c` 只绑定 ITER-002 exact 能力与产品证明，不授权新的世界模型实现 |
| Production Activation | **NOT EXECUTED** | 不得由任何本机 PASS 自动推导 |

精确边界见 [Iteration 002 Acceptance](iterations/iteration-002/results/acceptance.md)。原始 Provider、能力和产品证据保存在本机 `var/`，只通过 Result 中的 ID、Digest 和路径引用，不进入 Git。

## 当前执行顺序

执行 G3a Offline answer-chain：在不分派任何外部 Provider 且无出站模型 route 的条件下，以 deterministic test strategy 完整走通 `Requirement Revision → Needs/Joint Constraints → candidate resolution → Query Plan → Query Result → Need Assessments → Draft → Review → Authorization → Delivery`，并让 Need 遗漏、0/N/伪造/跨 Session candidate、Result/Read Set 篡改、self-review、Evidence payload/network 与无授权 Delivery 反例全部失败关闭。G3a exact checkpoint 与 PASS Result 提交前不得选择或调用外部模型；首次 CE 或其他外部分派前还必须单独取得披露确认。

[生产启用](roadmap/candidates/production-activation.md)、[Schema Evolution](roadmap/candidates/schema-evolution.md) 和超出 Structure 范围的 Semantic View 仍不自动获得授权。

## Agent 读取范围

Agent 必须读取 ITER-003 的 Proposal、Manifest、Readiness、当前 Slice、Verification Matrix 与上一 Gate Result，并只跟随其中引用的 System 文档。当前执行 G3a 无外部分派实现；G2 PASS 不得替代回答权威链、故障反例、exact checkpoint 与人工 Result，也不授权外部 Provider、CE 或模型分派。
