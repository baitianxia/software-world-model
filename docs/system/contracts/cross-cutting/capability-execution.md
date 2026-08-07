---
id: SYS-CONTRACT-X-CAPABILITY-EXECUTION
kind: system-contract
status: current
authority: normative
owners: [application]
depends_on: [SYS-ARCH-INVARIANTS]
derived_from: [DD-X-CAPABILITY-EXECUTION]
code: [src/software_world_model/application_services/resources.py, src/software_world_model/application_services/evaluation.py]
tests: [tests/test_resource_allocation.py, tests/test_capability_evaluation.py]
---

# Capability Execution

## Purpose and scope

本契约定义业务 Capability 如何选择 Strategy、获得执行资格和受控资源。它不统一各业务领域的输入输出，也不把模型或 Provider 形状提升为领域契约。

## Owner and public contract

业务模块拥有 Capability Contract 与可接受 Strategy 语义；Application 在进入领域 Core 前冻结 production Activation 或 exact evaluation grant。Model Gateway 是唯一模型入口，但不是 Capability 的业务权威。

## Invariants

1. Strategy 可替换，但 Capability 的权限、知识语义、外部结果和失败边界不得漂移。
2. Provider Envelope 符合不等于领域结果符合；领域 Owner 在封存结果前复核实际 Model Fingerprint、输入 Manifest、Request Digest 和资格。
3. 资源子分配只能收窄父授权，不能超分配；相同逻辑键恢复原结果，不产生第二次副作用。
4. evaluation-only 输出和 Sink 与生产状态隔离。
5. 资格缺失、过期、撤销、配置漂移或 post-call eligibility 失败时，不封存生产领域结果。
6. Capability Catalog / Registry 只解析调用方已声明的 Capability 与 Strategy，不能成为绕过模块静态依赖的 service locator。

## Failure and recovery

分派后结果未知不得推测失败或零 Usage；预留、绑定和结算如实表达部分状态。回退 Strategy 不得降低权限、隔离或知识边界。

## Verification ownership

Capability/Strategy/Allocation 的字段、状态、结算算法和通用错误由代码与测试拥有；具体模型阈值与运行结果是非规范性验证证据。
