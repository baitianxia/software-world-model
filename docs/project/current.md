---
id: PROJECT-CURRENT
kind: project-current
status: current
authority: current-development
owners: [project]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ITER-001-INDEX, ITER-002-INDEX, ITER-002-RESULT-ACCEPTANCE, ITER-003-INDEX, ITER-003-SLICE-001, ITER-003-RESULT-G3A, FINDING-003-014, FINDING-003-015, FINDING-003-016, FINDING-003-017, FINDING-003-018, FINDING-003-019]
code: []
tests: []
as_of: 2026-08-10
active_iteration: ITER-003-INDEX
active_slice: ITER-003-SLICE-001
worktree_status: iteration-003-v009-v1-0-3-requalification-checkpoint-preparation
strategy_relation: iteration-003-v009-attempt-3-pass-baseline-input-corrected-full-rerun-pending
live_model_path: local-evidence-first-accepted-world-model-path-not-active
---

# 当前工作上下文

## 开发授权

**ITER-003 / SLICE-001 已由用户明确授权，G0、G1、G2 与 G3a/V-008 已 PASS；用户又以独立消息确认了 V-009 Conformance、closed CE 与其要求的两条 baseline 外部披露。** 准备提交 P 为 `a4ae307c8ab04979e87e0460f19b6ec81fc915a3`，授权治理提交 Q 为 `42a3f1ababed73cded8aafb046105309a79c170e`，G0 exact 输入 checkpoint 为 `af849fb198179cfe1d1514f272a1a06236684f43`，G1 exact 实现 checkpoint 为 `ddb8f5feba1e0c52d2f788c2bb66c93810f2b469`，G2 exact 实现 checkpoint 为 `82aef7563556c70527b3c92227d0711a28437587`，G3a exact 实现 checkpoint 为 `f2269ecca5c1e85e69fafd93fe599c841227f3c7`。前两轮 V-009 分别因 owner 与 PARTIAL status Prompt 歧义得到 6/1/0；第三轮由 `FINDING-003-017` 修复 Direct per-revision closure，第四轮由 `FINDING-003-018` 修复 Mature legacy sandbox。第五轮在 checkpoint `3d09ed1c8f9fe1a0199619e924189f0453822937` 上又取得 Conformance PASS 与 closed CE 7/0/0 PASS/VALID；baseline 调用前运行器审计发现 Mature model-generated command 尚可能继承 operator 的 `ARK_API_KEY` 等环境变量，仍没有发出 baseline 请求。`FINDING-003-019` 已固定 inherit-none/no-login/non-secret shell environment 并冻结 `ITER-003-V009-EXACT-INPUTS@1.0.5`，按 drift rule 等待新 clean checkpoint 全量重跑。

## 当前系统与实现状态

| 范围 | 状态 | 证据边界 |
|---|---|---|
| Iteration 001 历史裁决 | Completed / pre-Git attestation | 正式知识单路径和本机体验的历史结果；原运行没有 exact Git identity，Production Activation 未执行 |
| Iteration 002 | **Completed / narrow acceptance** | exact 实现提交 `e5b030c6835a69c70153d90f62803d63b7a4ba75`；只接受 Evidence-first 本机同步问答实验，六题与直接源码基线打平 |
| Iteration 003 | **In progress / G3a PASS / V-009 requalification pending** | no-payload Bundle、Source-off View/Citation 与十阶段 offline answer authority chain 已通过 V-007/V-008；第五轮 V-009 CE 已 7/7 PASS，但 baseline preflight 暴露并修复 Mature operator 环境继承缺口，按 exact-input drift 须重新资格化；两条 baseline、G3b/G4 尚未完成 |
| Evidence-first Strategy | PASS / exact and time-bound | `evidence-first-software-answer@1.0.0` 的十类能力、两个 Java 工程六题和本机浏览器体验通过；它读取任务级 Evidence Packet，不是 Snapshot 世界模型问答 |
| 软件世界模型产品闭环 | **NOT ACCEPTED** | typed Structure Kernel、Source-off View 与 offline 回答权威链已在 ITER-003 G1/G2/G3a 通过；外部执行资格、真实模型浏览器质量、Product Validation 与 Activation 尚未通过 |
| `local-browser` | Local Evidence-first experience only | Activation `activation_decision_af90ea83192f441eb7140a011340221c` 只绑定 ITER-002 exact 能力与产品证明，不授权新的世界模型实现 |
| Production Activation | **NOT EXECUTED** | 不得由任何本机 PASS 自动推导 |

精确边界见 [Iteration 002 Acceptance](iterations/iteration-002/results/acceptance.md)。原始 Provider、能力和产品证据保存在本机 `var/`，只通过 Result 中的 ID、Digest 和路径引用，不进入 Git。

## 当前执行顺序

前五轮 V-009 的 Conformance/CE 证据永久保存在各自 checkpoint 目录且不可重写；第三至五轮 7/7 PASS 均因随后发现的 baseline exact input 漂移而不能继承。当前必须先让 `ITER-003-V009-EXACT-INPUTS@1.0.5`、Direct protocol `1.0.1` / Strategy `@5`、Mature protocol `1.0.3`、world-model Strategy `1.0.2` / Prompt `@3` 与测试形成新的 enclosing clean Git checkpoint；旧 Conformance 均不可复用。随后按冻结参数重新运行两调用 Adapter Conformance，再一次性执行全部七个 required closed CE Case；任何 Provider outcome unknown、Case FAIL、unknown、Result 非 PASS 或 Validity 非 VALID 都阻断且不得选择性重跑。只有 closed CE PASS/VALID 后，才可在首次 G3b product run 前完整密封同模型 controlled Direct 与 exact Codex CLI/model mature Source Agent 两条 baseline。

本次确认范围不包含 G3b product dispatch；即使 V-009 与 baseline 全部通过，开始 G3b 真实产品请求前仍需单独确认，并实现 distinct Model Egress Gateway process 与 OS denial audit。V-009 direct Adapter transport 只属于 qualification/comparison preflight，不证明 G3b 网络隔离。

[生产启用](roadmap/candidates/production-activation.md)、[Schema Evolution](roadmap/candidates/schema-evolution.md) 和超出 Structure 范围的 Semantic View 仍不自动获得授权。

## Agent 读取范围

Agent 必须读取 ITER-003 的 Proposal、Manifest、Readiness、当前 Slice、Verification Matrix 与 G3a Result，并只跟随其中引用的 System 文档。V-009 必须严格使用当前 `ITER-003-V009-EXACT-INPUTS@1.0.5` 和新的 enclosing clean checkpoint；旧 freeze、两轮 FAIL 与第三至五轮 PASS Result 都只作不可变历史证据，不得复用或改写。不得把 V-009 direct transport、CE qualification 或 baseline 推导为 G3b/G4、Product Validation 或 Activation。G3b product dispatch 尚未包含在当前披露确认中。
