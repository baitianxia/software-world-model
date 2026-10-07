---
id: SYS-ARCH-INVARIANTS
kind: system-invariants
status: current
authority: normative
semantic_owner: SYS-ARCH-BASELINE
authority_scope: controlled-architecture-appendix
owners: [architecture]
depends_on: [SYS-PRODUCT-VISION, SYS-ADR-017, SYS-ADR-019]
derived_from: [FINDING-010-029, FINDING-010-139, FINDING-010-140, FINDING-010-156, FINDING-010-198, FINDING-010-199, FINDING-010-236]
code: [src/software_world_model]
tests: [tests]
---

# 架构不变量

这些规则是架构不变量的唯一详细正文；顶层架构语义仍由 `SYS-ARCH-BASELINE` 拥有。INV-018/020 中出现的 Provider、HTTP、receipt、准入和持续授权字段只用于表达不变量的边界，精确状态映射和字段契约由相应 Contract/Operations 定义。其他文档引用编号，不复制后改写，也不能借不变量正文另立架构入口。

1. **INV-001 — 平台与世界模型分离。** 软件世界模型是软件系统在 exact Scope、Context、Schema 和 Snapshot 上持久、版本化、可验证、可更新的外部认知模型；构建平台不是任何一个世界模型。Knowledge Engine 拥有正式知识记录及生命周期，但平台运行状态不因此成为被建模软件世界的业务命题；手册、地图、摘要、索引或缓存只是投影，不得冒充完整世界模型或第二权威。
2. **INV-002 — Web 与 Agent 经受控应用边界。** Web 自然语言请求只能进入显式的 Engineering Conversation、World Model Query、
   Direct Evidence Answering 或受控 Task Application Service；主 Agent 只能通过 Application Services 使用世界模型和来源能力，不能直接
   访问领域 Core、Store 或 Source Tool。
3. **INV-003 — 来源与知识分离。** 在 Knowledge Update 路径中，Source Integration 向 Application 提供 Artifact 后止于 Artifact；默认 Engineering Chat 的当前 Turn 来源观察由 Source Broker/Worker 在 Application 边界内执行和记录，不是 Knowledge Engine 的正式 Evidence。Knowledge Engine 不访问外部来源。
4. **INV-004 — 正式知识单路径。** 模型输出和 Candidate 不可信，只有经过 Admission 与原子 Publication 的成员才能成为正式知识。
5. **INV-005 — 认识论可追溯。** Fact 必须由直接 Evidence 支持；Inference 只能依赖 exact Snapshot 中已发布的 Fact 和已发布、受控的上游 Inference。
6. **INV-006 — 派生视图不创知识。** Semantic View、World Model Cognition Context、手册/地图投影、Projection 和 Telemetry 不能创造、扩张或拥有正式知识。
7. **INV-007 — 职责分离。** 任何单一模型调用或角色都不得同时拥有生成、准入、发布和响应放行的完整控制链。生成与审核必须隔离执行上下文、权威输入和决策权；在满足这些边界时可以使用同一基础模型。
8. **INV-008 — 固定权威输入。** `WORLD_MODEL` 回答只能基于一个固定 Snapshot，或比较任务中同一 Scope 的有序 exact Snapshot Read Set，
   以及其正式查询/View 与 Support Map；答案进程只能挂载对应的 no-payload Snapshot Read Bundle，并在默认拒绝网络中仅连接 Manifest
   固定的 exact Model Egress Gateway。`DIRECT_INVESTIGATION` 回答只能基于绑定 exact 来源目标和原问题的密封 Evidence Packet。
   Engineering Conversation 的主 Agent 只能消费 immutable current Turn、受信相关 Conversation/Work State Revision、对齐的 World Model
   Cognition Context 与已密封 Evidence Ledger prefix，并只能经 Application/Broker 使用工具；Reviewer 只能消费当前 Turn、受信对话
   Context、绑定 exact repository/revision 的 Question Evidence Package 与 Draft。只有 Package 的 `support/citation` admissible entries
   能支持肯定 Claim/Citation；`boundary/audit` 必须保留 Gap/Failure/Partial/Conflict/Unknown 等边界且不能支持肯定 Claim，seal 不赋予
   条目真值。生成、审核和重写均不得用未授权输入、Provider 记忆或先前答案补洞；Citation 展示不能回流答案链。
9. **INV-009 — Scope 一致性边界。** Knowledge Scope 是发布、并发和逻辑分片边界；跨 Scope 只能固定 exact 依赖。
10. **INV-010 — Schema 受控生效。** 当前只支持首次采用（`INITIAL`）和同 Schema 更新（`UNCHANGED`）。已有 CURRENT 采用不同 Schema 属于未启用的 Schema Evolution / Adoption，在相应 Contract 被接受前必须拒绝。未来能力仍只能通过新 Snapshot 与受控重建或迁移生效，不得原地改写历史。
11. **INV-011 — 逐 Turn 完整性。** Direct Investigation 由原问题、不可变检查清单、Evidence Packet 和独立 Review 共同约束；World Model
   Query 由 Requirement Revision、exact Read Session、View/Query completeness、Sufficiency 与独立 Answer Review 共同约束；Engineering
   Conversation 由 current User Turn、受信相关对话目标/纠正、Agent Work State、append-only Ledger、当前双分区 Question Evidence
   Package、逐结论 Citation 和 fresh 独立 Review 共同约束。Reviewer 只提出具体 remediation Finding；可信 Application 把现有证据问题
   路由为同包主 Agent 修订，把 material evidence gap 路由为绑定该 gap 的新 Agent Attempt。任何新观察都形成新 Ledger/Package/Draft 并
   重新审核；旧 Review 不得放行。已受控穷尽并诚实披露的 verified unknown 完成当前授权下的 evidence boundary，但任何物质性用户条件、
   纠正、关系或结果缺失都不能整体通过。
12. **INV-012 — Strategy 资格。** 生产 Strategy 必须具有与当前实现、模型、配置和范围匹配的有效资格；未激活或资格失效的输出与生产 Sink 隔离。
13. **INV-013 — 观察和工作状态不掌权。** Telemetry、成本、Agent Work State、Conversation 历史、先前答案和历史运行证据不能成为正式
   知识、当前答案证据或领域决定权威。
14. **INV-014 — 工程与问题中立。** 核心问答流程不得按工程名称、语言、框架、关键词、约定文件名、符号类别、问题题型、fixture 或评测 Oracle 注入专用分支。来源/Schema 专用能力必须作为显式版本化 Profile 在 Source 或 Knowledge 边界注册，不能藏在问答 Prompt 或 UI 中。严格 `WORLD_MODEL`、严格 `DIRECT_INVESTIGATION` 与默认 Engineering Conversation 共享统一证据协议，但只有前两者是 Source-off/Source-only 的显式能力 profile；默认对话可以在同一循环组合两类观察。Evidence Gap、Knowledge Gap 与 Engineering QA Limitation 保持类型边界，任何情况都不得以猜测补齐。
15. **INV-015 — 模式完整与更新独立。** 严格 `WORLD_MODEL` 不访问 Source、不触发更新；严格 `DIRECT_INVESTIGATION` 不冒充 Snapshot 命中。默认 Engineering Conversation 在请求开始时声明 World Model cognition + Source tool 的组合边界，主 Agent 可以在同一 Turn 内自适应提出任一或两类受控操作，这不是运行中 fallback 或模式切换。Knowledge Update 由独立命令、计划或来源事件触发，即使无人提问也可运行；Chat 后的知识沉淀只能异步提议并重新经过 Evidence/Candidate/Admission/Publication，冲突只创建最小 Knowledge Maintenance Task，不原地修改当前 Snapshot。只有显式 profile 或权限边界变化才形成新的请求与结果。
16. **INV-016 — 主 Agent 工具与审核隔离。** Engineering Conversation 中主 Agent 可根据目标、假设和 Observation 自适应提出 World Model
   query 或来源操作；Application/Broker 重新校验并编译，只有隔离 Retrieval Worker 可对授权 exact revision 执行 allowlisted 只读来源
   操作，全部步骤写入 append-only Evidence Ledger。Source 内容是不可信 data，不能改变权限或工具目录。主 Agent 不得直读 Repository、
   Source Tool、Ledger write port、shell、网络、credential 或未密封内容；Reviewer 不得使用 World Model/Source 工具或继承主 Agent
   上下文，只基于当前 Turn、受信对话 Context、Package 与 Draft 审核；Reviewer 只返回 verdict/Finding，不重新解决原问题或生成替代答案。
   Review 缺口返回主 Agent 新 Work State/Attempt，任何补证仍经同一
   Broker/Worker 边界。预密封 revision/call/operation/bytes/wall-time/no-progress 高安全熔断只允许失败关闭，answerable 超限计失败，
   不得取消证据绑定、Citation 或独立复核。
17. **INV-017 — 工程答案的证据所有权。** 配置 placeholder/injection 只证明 key 与注入点，parameter/import/caller/registration 只证明
   签名或关系，上游 local state/decision 只证明该局部结果；它们分别不能替代具体 runtime value、未挂载 DTO/handler 实现或下游 HTTP/
   API mapping owner。每个工程 Chat Draft 必须由至少一个 fresh 独立 Reviewer 比较用户目标、对话约束、evidence scope 与 Draft scope；
   任何越界、遗漏或错误 Citation 都必须绑定具体 Finding。资格 Strategy 可采用多个 challenge，但固定双 focus 不是架构不变量。最终
   Authorization 只能绑定 current Package 上 finding-free 的独立 Review；预算不足以完成审核时必须失败关闭。
18. **INV-018 — 执行配置路由透明但 Attempt 不混合。** Engineering Conversation 只依赖通用 route role 和受信可用性裁决，
   不把 Provider、模型或实现身份暴露给产品分支、Agent 决策或质量规则。一次 Turn 的 preferred 与 fallback 是相互隔离的 Attempt；
   只有首选 Attempt 已终止、没有授权答案且受信所有者证明执行配置真实不可用时，才允许最多一次 fallback。格式无效、审核拒绝、能力/
   资格、应用、来源、授权/准入或安全失败不得伪装为不可用；同一外部请求不得重试，迟到结果不得覆盖已密封结果。每个 Attempt 都必须
   独立完成证据、答案、审核和审计链，具体状态映射、字段、收据与准入规则由 Model Gateway/Provider Routing Contract 定义。
19. **INV-019 — 语义 Chat 状态分离。** 软件世界模型、Conversation Work State 和 Turn Evidence 是不同权威对象。后续 Turn 可引用、追问、
   纠正、深入或总结，但 Application 必须密封相关历史、有效约束和指代解析；用户纠正形成新 Revision，不改写历史。每个 Turn 的完整
   Evidence Ledger/Package 只在该 Turn 内有效并在结束后释放；后续 Turn 必须重新查询当前 exact revision 的 World Model 或重新读取 Source。
   先前助手答案、摘要、Provider hidden state 或模型记忆都不是证据；一次 Turn 失败只结束该 Turn，不能污染后续 Turn、删除会话历史或关闭服务。
20. **INV-020 — 人工边界与逐次机器审计分离。** 一次 standing human authority 可以覆盖其明确声明的公开来源、只读披露、
   执行配置、预算和环境边界；可信系统必须为每个实际 Session、Turn、Attempt 和 call 自动派生不可复用的控制记录。机器派生只执行
   已批准边界，不能扩大授权，也不能成为新的人工审批步骤。来源敏感级别、执行身份、预算、副作用、环境或准入策略发生 material delta
   时必须重新取得人工决定；无法验证边界时失败关闭。Secret 隔离、来源不可信、独立 Reviewer、逐调用审计和失败关闭始终有效，具体
   standing-authority 字段与 receipt 由相应 Contract/Operations 定义。

## 实现与运行记录

原文中的具体配置、局部实现状态和运行记录已原样归位至项目路径 `docs/project/implementation-reference/routing-instance-history.md`。
这些记录不能覆盖架构基线、证明当前代码已满足本契约，或恢复被用户暂停的开发。

## 架构原则

- **As-is 优先：** 不以未来平台假设扭曲当前可证明语义。
- **冲突不静默消解：** 可并存的观察保持并存，Conflict 不自动选赢家。
- **最小充分设计：** 只有新的权威、事务或安全边界才引入新顶层组件。
