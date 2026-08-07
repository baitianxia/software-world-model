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
| 知识形成 | 把来源观察转成可审核知识 | 构建 Evidence、Entity、Fact、Inference Candidate，并完成准入与发布 |
| 知识使用 | 判断固定 Snapshot 是否足够回答任务 | 固定 Requirement、逐 Need 建立 Support Proof，形成 Gap 或 Sufficiency |
| Agentic 任务 | 从自然语言任务组织受控调用 | 只经 Application Services 分派，保持授权、预算、幂等和恢复 |
| 响应控制 | 交付有依据且不过度推断的答案 | 对 Claim、引用、限制和当前权威重新审核并唯一发送 |
| AI 能力治理 | 选择经过验证的模型 Strategy | 隔离输入，区分符合性、能力评估、产品验收和激活 |
| 管理与观察 | 让操作可恢复、可追溯、可计量 | 保存权威结果，Telemetry 单向观察且不参与业务决定 |

这些能力描述目标和责任，不是版本、排期或实现授权承诺。
