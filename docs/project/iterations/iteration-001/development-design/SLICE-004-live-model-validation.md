---
id: ITER-001-SLICE-004
kind: development-slice
status: completed
authority: historical-development
owners: [ai, quality]
depends_on: [ITER-001-SLICE-003, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
code: [src/software_world_model/ai_infrastructure, validation/agentic_capability_iteration_001, validation/jwt_iteration_001]
tests: [tests/test_ark_chat_conformance.py, tests/test_agentic_capability_evaluation.py, tests/test_strategy_activation.py]
iteration: ITER-001
migration: reconstructed-from-existing-iteration-records
---

# SLICE-004：真实模型符合性与能力资格

## Outcome

在 Secret 不入库、Provider Tool 禁用和输入 Manifest 闭包下，证明 exact Ark Chat Adapter 接口成立，并证明精确模型 Strategy 可以承担本轮六类通用职责。

## Required system semantics

- 所有模型调用经 Gateway，`NO_EXTERNAL_ACCESS` 在分派前机械保证；
- request alias 与 actual model identity 分开；
- CC、CE、Product Validation 和 Activation 独立；
- 生成、审核和比较使用隔离调用与已封存输入；
- 结果绑定实现、配置、模型、Strategy 和有效期，漂移安全关闭。

## Affected implementation

Ark Chat Adapter、direct HTTPS、Provider CLI、Conformance Runner、Capability Evaluation/Activation Repository 和验证 Harness。

## Non-goals

通过 Prompt 声明替代工具隔离、用 Probe 替代 CC、用 CC 替代 CE、自动生产激活。

## 阅读与回写

当前语义见 [Model Gateway](../../../../system/contracts/ai/model-gateway.md)和[Capability Evaluation](../../../../system/contracts/ai/capability-evaluation.md)；实现发现进入本轮 [Findings](../findings/README.md)。

## Acceptance

两次真实 CC 调用与完整 Oracle PASS；六类 Capability 真实执行并由独立来源复核；旧 Adapter/配置/实现结果被加载器拒绝；Outcome Unknown、Usage 和 Secret 安全边界有测试。
