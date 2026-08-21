---
id: SYS-PRODUCT-CAPABILITIES
kind: system-product
status: current
authority: normative
owners: [product]
depends_on: [SYS-PRODUCT-VISION]
code: [src/software_world_model]
tests: [tests]
---

# 能力地图

| 能力域 | 用户结果 | 系统责任 |
|---|---|---|
| 来源管理 | 连接并固定可授权的软件来源 | 管理 Data Source、Binding、精确 Revision 与只读操作 |
| 世界模型构建 | 为人和 AI 建立持久的软件系统认知 | 把来源观察构建为有版本、证据、Coverage 与 Unknown 的 Entity、Fact、Inference，并完成准入和原子发布 |
| 世界模型使用 | 在固定版本上读取和投影系统认知 | 从 exact Snapshot 形成可验证的查询、结构、行为、约束、Support 和面向人/任务的手册或地图投影 |
| 工程问答 | 用自然问题获得层级匹配、有引用的工程结论 | Investigation LLM 基于世界模型认知自适应提议调查，Broker/Worker 受控取证，Ledger 结束后封包并由独立 Answer/Reviewer 处理 |
| Agentic 任务 | 从自然语言任务组织受控调用 | 只经 Application Services 分派，保持授权、预算、幂等和恢复 |
| 响应控制 | 交付有依据且不过度推断的答案 | 对 Claim、引用、限制和当前权威重新审核并唯一发送 |
| AI 能力治理 | 选择经过验证的模型 Strategy | 隔离输入，区分符合性、能力评估、产品验收和激活 |
| 管理与观察 | 让操作可恢复、可追溯、可计量 | 保存权威结果，Telemetry 单向观察且不参与业务决定 |

这些能力描述目标和责任，不是版本、排期、已实现或环境激活承诺。
