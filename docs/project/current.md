---
id: PROJECT-CURRENT
kind: project-current
status: current
authority: current-development
owners: [project]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ITER-001-INDEX, ITER-002-INDEX, ITER-002-RESULT-ACCEPTANCE, ITER-003-INDEX, ITER-003-SLICE-001, ITER-003-RESULT-G3A, ITER-003-RESULT-V009, FINDING-003-020, FINDING-003-021, FINDING-003-022, FINDING-003-023]
code: []
tests: []
as_of: 2026-08-11
active_iteration: ITER-003-INDEX
active_slice: ITER-003-SLICE-001
worktree_status: iteration-003-g3b-authorized-implementation-and-preflight-in-progress
strategy_relation: iteration-003-v009-pass-valid-baselines-sealed-g3b-authorized-product-run-not-started
live_model_path: local-evidence-first-accepted-world-model-path-not-active
---

# 当前工作上下文

## 开发授权

**ITER-003 / SLICE-001 已由用户明确授权；G0、G1、G2、G3a/V-008 与 V-009 已 PASS，G3b 的两批外部披露/调用与 OS audit 又于 2026-08-11 获得独立明确授权且无需重复确认。** V-009 最终在 checkpoint `019f9fced69110c6a7e357a4ea2394ec6742fd2e` 上以 `ITER-003-V009-EXACT-INPUTS@1.0.5` 得到 Adapter Conformance PASS 和 closed CE 7/0/0 PASS/VALID，并在首次 G3b product run 前联合密封 controlled Direct 与 Mature Source Agent 各 55 个 run。Direct 为 15 SUCCESS/40 preserved FAILURE；Mature 为 55 SUCCESS/0 FAILURE，最终 permission preflight 7/7 PASS，联合 seal digest 为 `sha256:7be049fe746a71cb3b9c3941d81e8e51076256d0f8dac61ba5a5c88c873ecbdd`。`FINDING-003-020` 已处置 `/private/tmp` 特殊规则不能证明 sibling denial 的 staging 问题；`FINDING-003-021` 固定 Direct 429/unknown/contract failures 在后续 V-011 中不得择优、插值或静默过滤；`FINDING-003-022` 把 macOS 不支持 exact remote-IP Seatbelt filter 的限制处置为无 credential/payload supervisor 的单一 connected descriptor handoff；`FINDING-003-023` 要求把 executor synthetic external 地址与公网 IP 分列，并仍以 TLS/HTTP exact binding 证明 Provider 身份。

## 当前系统与实现状态

| 范围 | 状态 | 证据边界 |
|---|---|---|
| Iteration 001 历史裁决 | Completed / pre-Git attestation | 正式知识单路径和本机体验的历史结果；原运行没有 exact Git identity，Production Activation 未执行 |
| Iteration 002 | **Completed / narrow acceptance** | exact 实现提交 `e5b030c6835a69c70153d90f62803d63b7a4ba75`；只接受 Evidence-first 本机同步问答实验，六题与直接源码基线打平 |
| Iteration 003 | **In progress / G3b authorized, pre-product implementation** | no-payload Bundle、Source-off View/Citation、十阶段 offline answer authority chain 与最终 external qualification 已通过；110 个 baseline run 已全部密封，G3b 输入/披露已冻结。真实产品调用、G4 与验收尚未执行 |
| Evidence-first Strategy | PASS / exact and time-bound | `evidence-first-software-answer@1.0.0` 的十类能力、两个 Java 工程六题和本机浏览器体验通过；它读取任务级 Evidence Packet，不是 Snapshot 世界模型问答 |
| 软件世界模型产品闭环 | **NOT ACCEPTED** | typed Structure Kernel、Source-off View、offline 回答权威链与 V-009 外部执行资格已通过；真实模型浏览器质量、Product Validation 与 Activation 尚未通过 |
| `local-browser` | Local Evidence-first experience only | Activation `activation_decision_af90ea83192f441eb7140a011340221c` 只绑定 ITER-002 exact 能力与产品证明，不授权新的世界模型实现 |
| Production Activation | **NOT EXECUTED** | 不得由任何本机 PASS 自动推导 |

精确边界见 [Iteration 002 Acceptance](iterations/iteration-002/results/acceptance.md)。原始 Provider、能力和产品证据保存在本机 `var/`，只通过 Result 中的 ID、Digest 和路径引用，不进入 Git。

## 当前执行顺序

前五轮 V-009 证据和两次最终 baseline operator/preflight 失败均永久保存且不可重写。最终 V-009 Result 绑定 checkpoint `019f9fc…`、Conformance、closed CE qualification、全部 110 个 baseline terminal 与联合 seal；旧 freeze 和旧 qualification 仍只作历史证据。Direct 的 40 个失败保持 baseline 事实，Mature 55 个结果只作为质量 comparator，二者尚未与任何 world-model product result 比较。

本次新增确认明确包含 G3b product question/sealed View 模型分派、distinct Model Egress Gateway Provider 调用和 OS denial audit，且无需重复确认；它不包含 Production Activation。首次产品请求前仍必须先提交 clean exact 实现 checkpoint、密封 comparator preflight，并以 distinct Gateway、无 credential/payload 的 connection supervisor 与 OS deny probes 通过 G3b preflight。V-009 direct Adapter transport 只属于 qualification/comparison preflight，不证明 G3b 网络隔离。

[生产启用](roadmap/candidates/production-activation.md)、[Schema Evolution](roadmap/candidates/schema-evolution.md) 和超出 Structure 范围的 Semantic View 仍不自动获得授权。

## Agent 读取范围

Agent 必须读取 ITER-003 的 Proposal、Manifest、Readiness、当前 Slice、Verification Matrix、G3a Result 与 V-009 Result，并只跟随其中引用的 System 文档。不得把 V-009 direct transport、CE qualification、Mature Seatbelt 或 baseline seal 推导为 G3b/G4、Product Validation 或 Activation。G3b 当前只按 `ITER-003-G3B-EXACT-INPUTS@1.0.0` 的独立确认执行；Production Activation 仍未获授权且不得执行或从任何 PASS 推导。
