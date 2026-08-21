---
id: SYS-ARCH-INVARIANTS
kind: system-invariants
status: current
authority: normative
owners: [architecture]
depends_on: [SYS-PRODUCT-VISION]
code: [src/software_world_model]
tests: [tests]
---

# 架构不变量

这些规则是架构符合性的唯一正文。其他文档引用编号，不复制后改写。

1. **INV-001 — 平台与世界模型分离。** 构建平台不是任何一个软件世界模型；Knowledge Engine 拥有正式知识记录及生命周期，但平台运行状态不因此成为被建模软件世界的业务命题。
2. **INV-002 — Web 与 Agent 经受控应用边界。** Web 自然语言请求只能进入显式的 Engineering Question Answering、World Model Query、Direct Evidence Answering 或受控 Task Application Service；Agent 只能通过 Application Services 使用核心能力，不能直接访问领域 Core、Store 或 Source Tool。
3. **INV-003 — 来源与知识分离。** Source Integration 止于 Artifact；Knowledge Engine 不访问外部来源。
4. **INV-004 — 正式知识单路径。** 模型输出和 Candidate 不可信，只有经过 Admission 与原子 Publication 的成员才能成为正式知识。
5. **INV-005 — 认识论可追溯。** Fact 必须由直接 Evidence 支持；Inference 只能依赖 exact Snapshot 中已发布的 Fact 和已发布、受控的上游 Inference。
6. **INV-006 — 派生视图不创知识。** Semantic View、Projection 和 Telemetry 不能创造、扩张或拥有正式知识。
7. **INV-007 — 职责分离。** 任何单一模型调用或角色都不得同时拥有生成、准入、发布和响应放行的完整控制链。生成与审核必须隔离执行上下文、权威输入和决策权；在满足这些边界时可以使用同一基础模型。
8. **INV-008 — 固定权威输入。** `WORLD_MODEL` 回答只能基于一个固定 Snapshot，或比较任务中同一 Scope 的有序 exact Snapshot Read Set，以及其正式查询/View 与 Support Map；答案进程只能挂载对应的 no-payload Snapshot Read Bundle，并在默认拒绝网络中仅连接 Manifest 固定的 exact Model Egress Gateway。`DIRECT_INVESTIGATION` 回答只能基于绑定 exact 来源目标和原问题的密封 Evidence Packet。`ENGINEERING_QA` 只能基于绑定原问题、exact repository/revision、World Model Result/Gap 与受控来源读取的密封 Question Evidence Package；只有 Retrieval Worker 挂载 allowlisted 只读来源，Answer/Reviewer 只挂载该包。三种模式的生成、审核和重写均不得临时读取未授权输入或模型记忆补洞；Citation 展示不能回流答案链。
9. **INV-009 — Scope 一致性边界。** Knowledge Scope 是发布、并发和逻辑分片边界；跨 Scope 只能固定 exact 依赖。
10. **INV-010 — Schema 受控生效。** 当前只支持首次采用（`INITIAL`）和同 Schema 更新（`UNCHANGED`）。已有 CURRENT 采用不同 Schema 属于未启用的 Schema Evolution / Adoption，在相应 Contract 被接受前必须拒绝。未来能力仍只能通过新 Snapshot 与受控重建或迁移生效，不得原地改写历史。
11. **INV-011 — 逐问题完整性。** Direct Investigation 由原问题、不可变检查清单、Evidence Packet 和独立 Review 共同约束；World Model Query 由 Requirement Revision、exact Read Session、View/Query completeness、Sufficiency 与独立 Answer Review 共同约束；Engineering Question Answering 由原问题、Question Understanding/Checklist、密封 Question Evidence Package、逐结论 Citation 和独立 Review 共同约束。任何物质性问题、条件或关系缺失都不能整体通过。
12. **INV-012 — Strategy 资格。** 生产 Strategy 必须具有与当前实现、模型、配置和范围匹配的有效资格；评测输出与生产 Sink 隔离。
13. **INV-013 — 观察不掌权。** Telemetry、成本、Agent 工作状态和历史运行证据不能成为正式知识或领域决定权威。
14. **INV-014 — 工程与问题中立。** 核心问答流程不得按工程名称、语言、框架、关键词、约定文件名、符号类别、问题题型、fixture 或评测 Oracle 注入专用分支。来源/Schema 专用能力必须作为显式版本化 Profile 在 Source 或 Knowledge 边界注册，不能藏在问答 Prompt 或 UI 中。三种回答模式各自使用统一协议；Evidence Gap、Knowledge Gap 与 Engineering QA Limitation 保持类型边界，任何情况都不得以猜测补齐。
15. **INV-015 — 模式完整与更新独立。** `WORLD_MODEL` 不访问 Source、不触发更新、不静默回退；`DIRECT_INVESTIGATION` 不冒充 Snapshot 命中；`ENGINEERING_QA` 在请求开始前显式声明 World Model + Source 组合证据边界，其受控源检索不是运行中 fallback。Knowledge Update 由独立命令、计划或来源事件触发，即使无人提问也可运行；Engineering QA 后的知识沉淀只能异步提议并重新经过准入/发布；任何模式切换都形成新的显式请求与结果。
16. **INV-016 — 工程问答的调查与回答隔离。** `ENGINEERING_QA` 中只有隔离 Retrieval Worker 可对授权 exact revision 执行 allowlisted 只读操作；Source 内容是不可信 data，不能改变权限或执行计划。Answer/Reviewer 不得直读 Repository、Source/World Model Tool 或未密封内容，只能基于当前 Question Evidence Package 作答/审核；模型调用数和成本不得用于取消证据绑定、逐项检查或独立复核。

## 架构原则

- **As-is 优先：** 不以未来平台假设扭曲当前可证明语义。
- **冲突不静默消解：** 可并存的观察保持并存，Conflict 不自动选赢家。
- **最小充分设计：** 只有新的权威、事务或安全边界才引入新顶层组件。
