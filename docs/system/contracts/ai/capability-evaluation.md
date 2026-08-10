---
id: SYS-CONTRACT-AI-CAPABILITY-EVALUATION
kind: system-contract
status: current
authority: normative
owners: [application]
depends_on: [SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-X-CAPABILITY-EXECUTION]
derived_from: [DD-MGT-CAPABILITY-EVALUATION]
code: [src/software_world_model/application_services/evaluation.py, src/software_world_model/application_services/activation.py, src/software_world_model/ai_infrastructure/agentic_capability_evaluation.py, src/software_world_model/ai_infrastructure/world_model_capability_evaluation.py]
tests: [tests/test_capability_evaluation.py, tests/test_strategy_activation.py, tests/test_evaluation_runner.py]
---

# Capability Evaluation 与 Activation

## Purpose and scope

本契约定义一个精确模型 Strategy 如何获得、失去和使用业务能力资格。它不规定具体数据集、阈值、模型或某次运行结果。

## Ownership

业务模块拥有 Evaluation Contract 与 Oracle 语义；Application 拥有 Definition、Run、Result、Validity 和 Activation。Model Gateway 和领域 Core 不读写 Activation。

## Invariants

1. 只有 closed、PASS 且当前 `VALID` 的 Result 才可能支持 Activation；Conformance PASS 不能替代 Capability PASS。
2. 实现、模型、Prompt、Tool、Strategy、Adapter 或任何影响行为与资格的实质配置变化不得继承旧身份；滚动 alias 必须显式处理漂移。
3. Validity 只能从有效单调进入 stale/revoked；不能通过修改旧记录恢复。
4. Activation 绑定 Capability 声明的 normalized Activation Scope、单调 revision 和当前有效资格；environment、expiration 等维度只在该 Capability Contract 声明时生效。评测通过不会自动激活。
5. evaluation-only Sink 与生产 Sink 隔离，历史评测输出不得进入正式知识或生产答案。
6. 回退不能降低权限、隔离、输入闭包或产品边界。

## Failure and evidence boundary

运行结果未知保持 unknown；失败和过期结果永久保留但不能授权新 Activation。具体数据集、阈值、运行和产品对照是非规范性验证证据，必须绑定可重放的 exact implementation identity 与外部输入身份。

## Verification ownership

Definition/Run/Case/Result/Activation 的字段、状态机和恢复由代码及测试定义。
