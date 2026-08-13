---
id: ITER-006-INDEX
kind: iteration-index
status: completed
authority: historical-project
owners: [project]
depends_on: [ITER-006-PROPOSAL, ITER-006-READINESS, ITER-006-RESULT-ACCEPTANCE]
code: [src/software_world_model]
tests: [tests]
iteration: ITER-006
coding_input: false
---

# Iteration 006：Java 静态调用行为世界模型

## Status and authorization

用户于 `2026-08-12T09:18:11+08:00` 明确要求“开发 ITER-006”。本轮把该授权限定为一个新 SYSTEM Scope 上的
`JAVA_STATIC_CALL_GRAPH@1` 最小纵向闭环：独立构建 exact Local Git revision 的 Java 声明与可静态唯一解析的直接调用知识，
发布 no-payload Read Bundle，并从既有 `WORLD_MODEL / EVALUATION_ONLY` 本机 Web 入口完成 Source-off 问答。

当前只授权 [SLICE-001](development-design/SLICE-001-java-static-call-world-model.md)。它不授权 Production Activation、已有
Scope 的 Schema 迁移，或把静态源码关系解释成运行时行为。用户后来对 exact run-003、Ark、OpenAI Codex 与三路 payload
边界作出明确授权；该授权不包含提交、推送或 Production Activation。

当前 [Implementation Verification Result](results/implementation-verification.md) 已闭合 V-001—V-007；
[Live run-003 Result](results/live-run-003.md) 永久保留两套 baseline 各 6/6、World Model 4/6 的失败事实。根因修复先形成
[Java Capability Candidate Freeze](results/java-capability-candidate-freeze.md)，随后用户对 exact freeze/suite 的单次 Ark 授权由
[Capability run-002](results/java-capability-run-002.md) 执行并取得 8/8 `PASS_VALID`。

在该资格上，[Product Candidate Freeze run-007](results/product-candidate-freeze-run-007.md) 重新冻结六题 suite 并通过本地 Gate；
随后用户 exact 授权的 [Live run-007](results/live-run-007.md) 仍为 FAIL：Direct/Codex 各 6/6，World Model 六题都完成一次 Ark
call，但授权 wrapper 将 Java baseline 的 `document_digest` 与外层同名字段冲突，六题均被 exact postcondition 拒绝。失败与授权
消费事实永久保留。

`FINDING-006-012` 的最小本地修复仅排除被包装 baseline 的同名 digest，并新增 Java baseline 回归。新的
[Product Candidate Freeze run-008](results/product-candidate-freeze-run-008.md) 已完成 56/56 focused、18/18 Answer package、
836/836 full regression、docs 与未授权安全门。用户随后精确授权 [Live run-008](results/live-run-008.md)：Direct、Codex 与
World Model 各 6/6 SUCCESS，comparison `sha256:857085c4…` PASS、blocker 0、无 retry/filter/interpolation；V-008/V-009 已
闭合。用户于 `2026-08-13T11:45:33+08:00` 接受 exact run-008 的窄范围结果；最终裁决见
[Final Acceptance](results/acceptance.md)。本轮已经完成并转为历史证据，不再提供编码授权。

该 Acceptance 明确不把当前评测页面称为正式最终 Web Chat，也不扩张到系统用途、架构意图、总体介绍或通用源码问答。
最终交互会话暴露的全局类型/方法清单路由、动态示例和底层错误呈现限制均保留，不由本次裁决隐式修复。

## Required inputs

- [Proposal](proposal.md)
- [Manifest](manifest.yaml)
- [Verification Matrix](verification-matrix.md)
- [Readiness Review](readiness-review.md)
- [Development Design](development-design/README.md)
- [Findings](findings/README.md)
- [Results](results/README.md)

本轮代码、确定性产品链和 Source-off Web 入口达到 Gate 后才进入真实模型 Product Validation；最终 run-008 已由用户接受。
Production Activation、提交与推送仍未执行。
