---
id: SYS-CONTRACT-APPLICATION-INDEX
kind: system-contract-index
status: current
authority: normative
owners: [application]
depends_on: [SYS-CONTRACT-INDEX]
code: [src/software_world_model/application_services]
tests: [tests]
---

# Application Contracts

Application Services 拥有用例编排和可恢复结果，但不复制 Source 或 Knowledge Engine 的领域权威。

本目录的 Contract 只定义跨模块稳定语义。它们必须符合 [唯一架构基线](../../architecture/architecture-baseline.md)，不能通过新增角色、模式、字段或协议版本改变顶层架构。默认 Chat 的 Agent 关系、世界模型完整认知范围、Source/Knowledge 权威和 Reviewer 边界以架构基线及其已吸收的 ADR 为准。

详细 Prompt、Provider 配置、局部 Schema、兼容协议和测试夹具属于项目开发设计或代码测试；保留在本目录中的历史兼容细节只约束明确选择该兼容 Profile 的实现，不是默认产品开发入口。

- [Management](management.md)
- [Knowledge Update](knowledge-update.md)
- [Knowledge Use](knowledge-use.md)
- [Structure View](structure-view.md)
- [Java Static Call Behavior View](behavior-view.md)
- [Java Implementation Query](implementation-query.md)
- [World Model Answering](world-model-answering.md)
- [Direct Evidence Answering](evidence-answering.md)
- [Engineering Question Answering](engineering-question-answering.md)
- [Engineering Conversation](engineering-conversation.md)
- [Agentic Task](agentic-task.md)
- [Response Control](response-control.md)
