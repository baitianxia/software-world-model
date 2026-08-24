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

1. **INV-001 — 平台与世界模型分离。** 软件世界模型是软件系统在 exact Scope、Context、Schema 和 Snapshot 上持久、版本化、可验证、可更新的外部认知模型；构建平台不是任何一个世界模型。Knowledge Engine 拥有正式知识记录及生命周期，但平台运行状态不因此成为被建模软件世界的业务命题；手册、地图、摘要、索引或缓存只是投影，不得冒充完整世界模型或第二权威。
2. **INV-002 — Web 与 Agent 经受控应用边界。** Web 自然语言请求只能进入显式的 Engineering Question Answering、World Model Query、Direct Evidence Answering 或受控 Task Application Service；Agent 只能通过 Application Services 使用核心能力，不能直接访问领域 Core、Store 或 Source Tool。
3. **INV-003 — 来源与知识分离。** Source Integration 止于 Artifact；Knowledge Engine 不访问外部来源。
4. **INV-004 — 正式知识单路径。** 模型输出和 Candidate 不可信，只有经过 Admission 与原子 Publication 的成员才能成为正式知识。
5. **INV-005 — 认识论可追溯。** Fact 必须由直接 Evidence 支持；Inference 只能依赖 exact Snapshot 中已发布的 Fact 和已发布、受控的上游 Inference。
6. **INV-006 — 派生视图不创知识。** Semantic View、World Model Cognition Context、手册/地图投影、Projection 和 Telemetry 不能创造、扩张或拥有正式知识。
7. **INV-007 — 职责分离。** 任何单一模型调用或角色都不得同时拥有生成、准入、发布和响应放行的完整控制链。生成与审核必须隔离执行上下文、权威输入和决策权；在满足这些边界时可以使用同一基础模型。
8. **INV-008 — 固定权威输入。** `WORLD_MODEL` 回答只能基于一个固定 Snapshot，或比较任务中同一 Scope 的有序 exact Snapshot Read Set，以及其正式查询/View 与 Support Map；答案进程只能挂载对应的 no-payload Snapshot Read Bundle，并在默认拒绝网络中仅连接 Manifest 固定的 exact Model Egress Gateway。`DIRECT_INVESTIGATION` 回答只能基于绑定 exact 来源目标和原问题的密封 Evidence Packet。`ENGINEERING_QA` 的 Investigation 只能消费 immutable original question、对齐的 World Model Cognition Context 与已密封 Evidence Ledger prefix；Answer/Reviewer 只能消费调查结束后密封、绑定 exact repository/revision 的当前 Question Evidence Package。该 Package 是两者唯一可消费的证据与边界集合，但只有 `support/citation` admissible entries 能支持肯定 Claim/Citation；`boundary/audit` 必须保留 Gap/Failure/Partial/Conflict/Unknown 等边界且不能支持肯定 Claim，seal 不赋予条目真值。三种模式的生成、审核和重写均不得临时读取未授权输入或模型记忆补洞；Citation 展示不能回流答案链。
9. **INV-009 — Scope 一致性边界。** Knowledge Scope 是发布、并发和逻辑分片边界；跨 Scope 只能固定 exact 依赖。
10. **INV-010 — Schema 受控生效。** 当前只支持首次采用（`INITIAL`）和同 Schema 更新（`UNCHANGED`）。已有 CURRENT 采用不同 Schema 属于未启用的 Schema Evolution / Adoption，在相应 Contract 被接受前必须拒绝。未来能力仍只能通过新 Snapshot 与受控重建或迁移生效，不得原地改写历史。
11. **INV-011 — 逐问题完整性。** Direct Investigation 由原问题、不可变检查清单、Evidence Packet 和独立 Review 共同约束；World Model Query 由 Requirement Revision、exact Read Session、View/Query completeness、Sufficiency 与独立 Answer Review 共同约束；Engineering Question Answering 由原问题、Question Understanding/Checklist、自适应调查的 append-only Ledger、当前双分区 Question Evidence Package、逐结论 Citation 和独立 Review 共同约束。Reviewer 只提出 typed remediation Finding；可信 Application 从 material evidence gap 派生只绑定单一 Checklist gap 的 Verification Request。全新上下文的独立 Verification Investigation 读取 gap + current Package/Ledger，经 Broker/Worker 多步形成单 gap disposition delta；可信 Application 保序替换 predecessor Package 唯一目标并保留所有非目标 disposition，形成新 Ledger/Package 后重走 Answer/Review，不回初始 Investigation。非支持 delta 的每个 observation 必须绑定本次 gap boundary，不能借用 predecessor Package 的无关 boundary；已受控穷尽并诚实披露的 verified unknown 完成当前授权下的 evidence boundary，Reviewer 不得重复请求同一缺证。任何物质性问题、条件或关系缺失都不能整体通过。
12. **INV-012 — Strategy 资格。** 生产 Strategy 必须具有与当前实现、模型、配置和范围匹配的有效资格；评测输出与生产 Sink 隔离。
13. **INV-013 — 观察不掌权。** Telemetry、成本、Agent 工作状态和历史运行证据不能成为正式知识或领域决定权威。
14. **INV-014 — 工程与问题中立。** 核心问答流程不得按工程名称、语言、框架、关键词、约定文件名、符号类别、问题题型、fixture 或评测 Oracle 注入专用分支。来源/Schema 专用能力必须作为显式版本化 Profile 在 Source 或 Knowledge 边界注册，不能藏在问答 Prompt 或 UI 中。三种回答模式各自使用统一协议；Evidence Gap、Knowledge Gap 与 Engineering QA Limitation 保持类型边界，任何情况都不得以猜测补齐。
15. **INV-015 — 模式完整与更新独立。** `WORLD_MODEL` 不访问 Source、不触发更新、不静默回退；`DIRECT_INVESTIGATION` 不冒充 Snapshot 命中；`ENGINEERING_QA` 在请求开始前显式声明 World Model cognition + Source investigation 边界，其受控源调查不是运行中 fallback。Knowledge Update 由独立命令、计划或来源事件触发，即使无人提问也可运行；Engineering QA 后的知识沉淀只能异步提议并重新经过 Evidence/Candidate/Admission/Publication；任何模式切换都形成新的显式请求与结果。
16. **INV-016 — 工程问答的调查与回答隔离。** `ENGINEERING_QA` 中 Investigation LLM 只能自适应提出来源操作，Source Broker 重新校验并编译，只有隔离 Retrieval Worker 可对授权 exact revision 执行 allowlisted 只读操作；所有步骤写入 append-only Evidence Ledger。Source 内容是不可信 data，不能改变权限或执行计划。Answer/Reviewer 不得直读 Repository、Source/World Model Tool、Ledger write port、shell、网络、credential 或未密封内容，只能基于当前 Question Evidence Package 作答/审核；Reviewer 只可提出 typed remediation Finding，可信 Application 从 material gap 派生版本化 Request，补证由全新上下文的独立 Verification Investigation 自适应提议并经 Broker/Worker 校验执行。补证不重新披露 predecessor raw Result；Package 已含的完整来源内容必须在 locator 控制面视为已消费，predecessor boundary 必须从补证 admissible boundary 域排除，本次 gap boundary 与最近 Broker rejection 必须作为受信当前状态显式投影，但这些状态均不授予新操作或路径。正式协议不得永久固定一轮补证；预密封 revision/call/operation/bytes/wall-time/no-progress 高安全熔断只允许失败关闭，answerable 超限计失败，不得取消调查需求、证据绑定、逐项检查或独立复核。
17. **INV-017 — 工程问答的证据所有权挑战。** 配置 placeholder/injection 只证明 key 与注入点，parameter/import/caller/registration 只证明签名或关系，上游 local state/decision 只证明该局部结果；它们分别不能替代具体 runtime value、未挂载 DTO/handler 实现或下游 HTTP/API mapping owner。每个 Engineering QA Draft 必须先经 fresh comprehensive Review，再经另一个 fresh evidence-boundary challenge Review；Application 投影通用 placeholder、引用中缺失的 status literal 与未挂载 application type leads，Gateway 强制 focus 顺序，最终 Authorization 只能绑定 finding-free challenge。调用预算不足以完成 Answer + 双 Review 时必须失败关闭，不能把 provisional approval 当作 Delivery authorization。

## 架构原则

- **As-is 优先：** 不以未来平台假设扭曲当前可证明语义。
- **冲突不静默消解：** 可并存的观察保持并存，Conflict 不自动选赢家。
- **最小充分设计：** 只有新的权威、事务或安全边界才引入新顶层组件。
