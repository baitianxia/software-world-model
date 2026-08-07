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
2. **INV-002 — Web 与 Agent 经受控应用边界。** Web 自然语言请求只能先进入 Conversational Task Control；Agent 只能通过 Application Services 使用核心能力，不能直接访问领域 Core、Store 或 Source Tool。
3. **INV-003 — 来源与知识分离。** Source Integration 止于 Artifact；Knowledge Engine 不访问外部来源。
4. **INV-004 — 正式知识单路径。** 模型输出和 Candidate 不可信，只有经过 Admission 与原子 Publication 的成员才能成为正式知识。
5. **INV-005 — 认识论可追溯。** Fact 必须由直接 Evidence 支持；Inference 只能依赖 exact Snapshot 中已发布的 Fact 和已发布、受控的上游 Inference。
6. **INV-006 — 派生视图不创知识。** Semantic View、Projection 和 Telemetry 不能创造、扩张或拥有正式知识。
7. **INV-007 — 职责分离。** 任何单一模型调用或角色都不得同时拥有生成、准入、发布和响应放行的完整控制链。生成与审核必须隔离执行上下文、权威输入和决策权；在满足这些边界时可以使用同一基础模型。
8. **INV-008 — 固定正式输入。** 生产软件知识响应只能基于固定 Snapshot 的正式知识；不得读取来源或模型记忆补洞。
9. **INV-009 — Scope 一致性边界。** Knowledge Scope 是发布、并发和逻辑分片边界；跨 Scope 只能固定 exact 依赖。
10. **INV-010 — Schema 受控生效。** 当前只支持首次采用（`INITIAL`）和同 Schema 更新（`UNCHANGED`）。已有 CURRENT 采用不同 Schema 属于未启用的 Schema Evolution / Adoption，在相应 Contract 被接受前必须拒绝。未来能力仍只能通过新 Snapshot 与受控重建或迁移生效，不得原地改写历史。
11. **INV-011 — 逐 Need 完整性。** Requirement Revision、Read Session 和 Sufficiency Assessment 必须共同约束任务语义；任何 Need 缺失都不能整体通过。
12. **INV-012 — Strategy 资格。** 生产 Strategy 必须具有与当前实现、模型、配置和范围匹配的有效资格；评测输出与生产 Sink 隔离。
13. **INV-013 — 观察不掌权。** Telemetry、成本、Agent 工作状态和历史运行证据不能成为正式知识或领域决定权威。
14. **INV-014 — 工程与问题中立。** 核心问答流程不得按工程名称、语言、框架、约定文件名、符号类别或问题题型注入专用分支；所有请求统一经过需求保持、信息增益驱动的来源调查、正式知识复核和回答复核。来源访问或执行失败必须保留为失败、限制或 Unknown；只有有效 Read Session 内的语义不足才形成 Gap，任何情况都不得以猜测补齐。

## 架构原则

- **As-is 优先：** 不以未来平台假设扭曲当前可证明语义。
- **冲突不静默消解：** 可并存的观察保持并存，Conflict 不自动选赢家。
- **最小充分设计：** 只有新的权威、事务或安全边界才引入新顶层组件。
