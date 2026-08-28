---
id: SYS-ARCH-INVARIANTS
kind: system-invariants
status: current
authority: normative
owners: [architecture]
depends_on: [SYS-PRODUCT-VISION, SYS-ADR-017, SYS-ADR-019]
derived_from: [FINDING-010-029, FINDING-010-139, FINDING-010-140, FINDING-010-156]
code: [src/software_world_model]
tests: [tests]
---

# 架构不变量

这些规则是架构符合性的唯一正文。其他文档引用编号，不复制后改写。

1. **INV-001 — 平台与世界模型分离。** 软件世界模型是软件系统在 exact Scope、Context、Schema 和 Snapshot 上持久、版本化、可验证、可更新的外部认知模型；构建平台不是任何一个世界模型。Knowledge Engine 拥有正式知识记录及生命周期，但平台运行状态不因此成为被建模软件世界的业务命题；手册、地图、摘要、索引或缓存只是投影，不得冒充完整世界模型或第二权威。
2. **INV-002 — Web 与 Agent 经受控应用边界。** Web 自然语言请求只能进入显式的 Engineering Conversation、World Model Query、
   Direct Evidence Answering 或受控 Task Application Service；主 Agent 只能通过 Application Services 使用世界模型和来源能力，不能直接
   访问领域 Core、Store 或 Source Tool。
3. **INV-003 — 来源与知识分离。** Source Integration 止于 Artifact；Knowledge Engine 不访问外部来源。
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
12. **INV-012 — Strategy 资格。** 生产 Strategy 必须具有与当前实现、模型、配置和范围匹配的有效资格；评测输出与生产 Sink 隔离。
13. **INV-013 — 观察和工作状态不掌权。** Telemetry、成本、Agent Work State、Conversation 历史、先前答案和历史运行证据不能成为正式
   知识、当前答案证据或领域决定权威。
14. **INV-014 — 工程与问题中立。** 核心问答流程不得按工程名称、语言、框架、关键词、约定文件名、符号类别、问题题型、fixture 或评测 Oracle 注入专用分支。来源/Schema 专用能力必须作为显式版本化 Profile 在 Source 或 Knowledge 边界注册，不能藏在问答 Prompt 或 UI 中。三种回答模式各自使用统一协议；Evidence Gap、Knowledge Gap 与 Engineering QA Limitation 保持类型边界，任何情况都不得以猜测补齐。
15. **INV-015 — 模式完整与更新独立。** `WORLD_MODEL` 不访问 Source、不触发更新、不静默回退；`DIRECT_INVESTIGATION` 不冒充 Snapshot
   命中；Engineering Conversation 在 Conversation 开始前显式声明 World Model cognition + Source tool 边界，其受控源调查不是运行中
   fallback。Knowledge Update 由独立命令、计划或来源事件触发，即使无人提问也可运行；Chat 后的知识沉淀只能异步提议并重新经过
   Evidence/Candidate/Admission/Publication；任何模式切换都形成新的显式请求与结果。
16. **INV-016 — 主 Agent 工具与审核隔离。** Engineering Conversation 中主 Agent 可根据目标、假设和 Observation 自适应提出 World Model
   query 或来源操作；Application/Broker 重新校验并编译，只有隔离 Retrieval Worker 可对授权 exact revision 执行 allowlisted 只读来源
   操作，全部步骤写入 append-only Evidence Ledger。Source 内容是不可信 data，不能改变权限或工具目录。主 Agent 不得直读 Repository、
   Source Tool、Ledger write port、shell、网络、credential 或未密封内容；Reviewer 不得使用 World Model/Source 工具或继承主 Agent
   上下文，只基于当前 Turn、受信对话 Context、Package 与 Draft 审核。Review 缺口返回主 Agent 新 Work State/Attempt，任何补证仍经同一
   Broker/Worker 边界。预密封 revision/call/operation/bytes/wall-time/no-progress 高安全熔断只允许失败关闭，answerable 超限计失败，
   不得取消证据绑定、Citation 或独立复核。
17. **INV-017 — 工程答案的证据所有权。** 配置 placeholder/injection 只证明 key 与注入点，parameter/import/caller/registration 只证明
   签名或关系，上游 local state/decision 只证明该局部结果；它们分别不能替代具体 runtime value、未挂载 DTO/handler 实现或下游 HTTP/
   API mapping owner。每个工程 Chat Draft 必须由至少一个 fresh 独立 Reviewer 比较用户目标、对话约束、evidence scope 与 Draft scope；
   任何越界、遗漏或错误 Citation 都必须绑定具体 Finding。资格 Strategy 可采用多个 challenge，但固定双 focus 不是架构不变量。最终
   Authorization 只能绑定 current Package 上 finding-free 的独立 Review；预算不足以完成审核时必须失败关闭。
18. **INV-018 — 执行配置路由透明但 attempt 不混合。** Engineering Conversation 在 Turn dispatch 前从有效 standing authority 或其
   exact human delta 冻结有序 `preferred → fallback` route，以及每个角色对应的 exact execution-profile ref/digest。产品、Agent 和 route branch
   只能读取通用 route role、profile ref/digest、顺序与受信 availability verdict。Execution profile 内部绑定 Provider/model/endpoint、
   Adapter/Configuration/plugin、credential reference、资格、披露、预算与 transport；这些具体身份只属于运行配置、资格、Adapter/plugin 和 receipt，
   不得进入产品分支、Agent 决策或质量规则。用户一次提交只形成一个 immutable logical Turn。只有 preferred-route attempt 已密封 terminal、
   没有 authorized answer，且该 preferred profile 登记的受信 availability owner 密封了 exact
   `PREFERRED_EXECUTION_PROFILE_UNAVAILABLE` verdict 时，才可启动最多一个 fallback-route attempt。Raw unavailable/HTTP/outcome 信号本身不授予 fallback；
   结构化输出无效、Reviewer 拒绝、Capability/qualification、Application、Source、authorization/admission 或 Security failure 全部 non-eligible。格式修复、
   答案重写、补证后重答和 fresh Review 若在当前 profile 内继续，每次都必须是新的 authorized call，而不是重发同一 Provider request；无合法新调用时当前 Turn
   失败关闭，不 fallback。每个 fallback attempt 从同一受信 Turn input、Conversation Context 与 exact Cognition 独立运行完整主 Agent—证据—答案—审核链，
   不共享中间态、Provider 会话或结果权威；同 request retry 为 0，迟到的 preferred-route 结果隔离且不得覆盖。每个 route 都必须产生 execution-profile、disclosure、
   dispatch-admission、transport/call 和 attempt-terminal 通用 receipt；profile 声明 admission plugin 时，必须在任何该 Provider 外部网络、credential 和 HTTP 前验证准入，
   并在每个新 request 前重验插件条件或 exact override。拒绝必须证明该 route 分派为 0，不能靠删减答案质量通过。
19. **INV-019 — 语义 Chat 状态分离。** 软件世界模型、Conversation Work State 和 Turn Evidence 是不同权威对象。后续 Turn 可引用、追问、
   纠正、深入或总结，但 Application 必须密封相关历史、有效约束和指代解析；用户纠正形成新 Revision，不改写历史。先前助手答案、摘要、
   Provider hidden state 或模型记忆都不是证据；一次 Turn 失败只结束该 Turn，不能污染后续 Turn、删除会话历史或关闭服务。
20. **INV-020 — 人工边界与逐次机器审计分离。** 对已证明为公开开源、clean exact revision 的来源，以及已批准的
   Provider/model/endpoint/credential account、只读披露范围、预算和 loopback `EVALUATION_ONLY` Sink，一次 standing human authority
   可以覆盖多个 run、Conversation、Turn 和 dispatch。可信系统必须为每个实际 Session/Turn/attempt/call 自动派生不可复用的 exact
   Manifest、disclosure/dispatch receipt 和审计链；它们不是新的人工审批，也不能扩张 standing authority。private/unknown/dirty/local
   data、新 Provider/model/endpoint/credential account、预算扩张、execution profile/admission plugin 或其策略例外变化、外部写入、
   非 loopback 或 Production 才是
   必须重新取得人工决定的 material delta。公开来源仍是不可信 data；exact revision、只读、prompt-injection 防护、Secret/Provider
   隔离、资格、预算、逐调用审计、独立 Reviewer、失败关闭和 profile-specific admission 全部保持。

## 当前配置实例与历史实现证据

当前 ITER-010 配置把 Ark 映射到 `preferred`、DeepSeek 映射到 `fallback`；备用 execution profile 选择的调度插件以
`DEEPSEEK_DISPATCH_ADMISSION@1` 收据和 `V-DEEPSEEK-IDLE-001` 证据验证。该映射、名称与插件实例只是可替换的当前配置和历史实现证据，
不定义 INV-018 的分支、质量、授权或 fallback 语义。

## 架构原则

- **As-is 优先：** 不以未来平台假设扭曲当前可证明语义。
- **冲突不静默消解：** 可并存的观察保持并存，Conflict 不自动选赢家。
- **最小充分设计：** 只有新的权威、事务或安全边界才引入新顶层组件。
