---
id: SYS-CONTRACT-AI-INDEX
kind: system-contract-index
status: current
authority: normative
owners: [ai, application]
depends_on: [SYS-CONTRACT-INDEX]
code: [src/software_world_model/ai_infrastructure]
tests: [tests/test_model_gateway.py, tests/test_capability_evaluation.py]
---

# AI Contracts

- [Model Gateway](model-gateway.md) 定义唯一模型调用和输入隔离边界。
- [Capability Evaluation](capability-evaluation.md) 定义资格、有效期与激活边界。

Provider 配置和某次 PASS 是运行配置或非规范性证据，不构成 System Contract。
