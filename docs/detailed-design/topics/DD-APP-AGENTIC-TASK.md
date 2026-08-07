# Agent 任务编排详细设计

| 元数据 | 值 |
|---|---|
| Document ID | DD-APP-AGENTIC-TASK |
| Version | 0.1.0 |
| Status | Accepted |
| Document Steward | Application Services / Conversational Task Control；各 Agent 维护自己的 Capability Contract |
| Architecture Baseline | SWM-ARCH@1.2 |
| Depends On | DD-APP-KNOWLEDGE-USE@0.1.0、DD-APP-KNOWLEDGE-UPDATE@0.1.0、DD-X-CAPABILITY-EXECUTION@0.1.0、DD-AI-MODEL-GATEWAY@0.1.0、DD-MGT-CAPABILITY-EVALUATION@0.1.0 |
| Conditional Depends On | DD-APP-MANAGEMENT@0.1.0（仅启用自然语言 Management 任务） |
| Owns Contracts | APP-AGENT-CAPABILITY-01、APP-CONVERSATIONAL-TASK-01、APP-AGENT-ORCHESTRATION-01、APP-TASK-EXECUTION-01、APP-REVIEWER-INVOCATION-OUTCOME-01 |
| Design Coverage | Web Chat 任务理解、职责级 Agent 路由、具体任务执行、应用调用授权与结果交接 |
| Supersedes | None |
| Rationale ADR | AD-052、AD-059、AD-064、AD-080、AD-085 至 AD-090、AD-112、AD-114、AD-115、AD-117、AD-127、AD-132、AD-134、AD-135 |
| Design Validation | None |
| Conformance Cases | None |
| Capability Evaluation | Intent / Routing、Task Execution 使用模型时分别适用 |

> 本文定义 Agent 角色、结构化交接和 Conversational Task Control。它是模块化单体 Application Layer 内的逻辑职责，不是新增服务或部署单元；Response Control 由独立主题拥有。

## 1. 目的与范围

本主题保证 Web Chat 的自然语言任务能够在不穿透 Application Services 和知识可信边界的前提下动态执行，并将 Answer Candidate Proposal 交给独立 Response Control 处理。

本文保证：

- Agent Orchestrator 理解“用户要做什么、交给谁”，具体 Agent 决定“如何完成”。
- Agent 动态规划只组合已经存在的 Application Use Case，不复制 Management、Knowledge Update、Knowledge Use 或 Response Control 逻辑。
- Task Execution Agent 只提交结构化 Result 与 Answer Candidate Proposal；Candidate 封存、审核、授权和交付由独立 Response Control 负责。
- 模型和具体 Agent 可以替换或增加，但任务边界、权威输入和结构化交接语义不变。

本文不定义：

- Artifact、Evidence、Candidate、Knowledge Admission、Snapshot Publication 或 Semantic View 内部逻辑。
- 固定 Prompt、具体模型、Agent 框架、类、线程、消息队列或远程部署协议。
- 通用工作流平台、任意 DAG、Agent 间自由协商、长期 Agent Memory 或自动训练。
- CLI / Scheduler 的结构化 Fixed Workflow；它们直接调用 Application Services，默认不生成 Answer Candidate。
- 纯认证、协议和传输错误；Interface Layer 可以直接返回标准错误信封，但不得伪装成业务结论。

## 2. 最小充分实现与扩展边界

最简单合规 Strategy 是：

- 单体进程内静态提供一个通用 Task Execution Agent 和一个 Answer Review Agent。
- Conversational Task Control 依据 Agent Orchestrator 的职责级 Proposal 顺序分派它们；审核反馈需要修正时创建新执行 / 审核 Attempt。
- 不建设动态注册中心、远程发现、持久任务图、并行 Agent 协商或专职 Agent 集群。
- Agent 运行状态使用同一 Application Store；模型统一经 Model Gateway，应用能力统一经 Application Services。

只有出现真实需求时才增加机制：

| 触发条件 | 可增加的 Strategy | 不得改变 |
|---|---|---|
| 不同任务已证明需要显著不同的能力、权限或评测集 | 拆分专职 Task Agent | Agent Task、Application Services 边界和 Answer Review 门禁 |
| 多个职责级任务彼此独立且并行有可测收益 | 有界并行 Agent Invocation | 原始任务边界、资源上限和结果合并审核 |
| Agent 需要跨进程独立部署或热插拔 | 远程 Registry / Discovery Adapter | Agent Capability Contract 与调用授权 |
| 单次任务需要可恢复的复杂依赖图 | 专题任务图设计 | Orchestrator 只拆职责、不执行领域步骤 |

“未来可能增加 Agent”不构成提前实现上述机制的理由。

Answer Review Agent 在本主题中只作为受 Task Control 分派的 Agent Capability；其审核输入、Assessment 和 Decision 语义由 DD-APP-RESPONSE-CONTROL 定义。

## 3. 边界与所有权

| 对象 / 决定 | Owner | 边界 |
|---|---|---|
| Web Chat Request Envelope、Conversation Reference、Adapter Delivery Receipt | Interface Layer | 只做协议、认证上下文输入输出适配；Receipt 不改变应用状态 |
| Conversational Task / Revision、Agent Task / Invocation、Catalog / Root Allocation Binding、Delegated Grant、Dispatch Fence、Action Authorization、Application Call Record、Reviewer Invocation Outcome / Validation Assertion | Application Conversational Task Control | Web 唯一入口和任务状态唯一写者；拥有所有任务、Invocation CAS、副作用 dispatch claim 与 Reviewer 调用完成证明 |
| 意图 / 路由 / 下一职责动作 Proposal | Agent Orchestrator | 只依据冻结输入提出编排建议；不持久化权威任务状态、不执行领域用例 |
| Task Execution Result、Answer Candidate Proposal | Task Execution Agent | 只通过 Application Services 取得权威结果；Proposal 由 Application 封存 |
| Use Case Attempt / Outcome | 对应 Application Use Case Result Owner | Task Control 只保存 exact Result Reference / Digest，不改写领域 Outcome |
| Task Boundary、Requirement、Read Session、Assessment、Gap、Application Use Case Result | Application Services | 由对应详细设计拥有；Agent 只持有引用 |
| Answer Candidate、Review Attempt / Read Set / Decision、Final Response Authorization | Application Response Control | Review Agent 只产生 Assessment Proposal；Response Control 是唯一状态写者 |
| Logical Response Delivery、Send Revision、Dispatch Claim、Delivery Status | Application Response Control | 一个逻辑交付只由该 Owner 线性推进 |

Web Chat 只调用 Conversational Task Control；该 Control 在冻结认证上下文、Catalog、Root Allocation、Task Revision 与 Execution Envelope 后调用 Agent Orchestrator。Agent Orchestrator 可以通过 Model Gateway 执行意图理解和路由，但不得反向调用 Application Services。Task Execution Agent 只能直调用 Delegated Grant 允许的 QUERY / 无副作用 Application Use Case；COMMAND 只提交 Action Proposal，由 Task Control 完成授权和 dispatch claim 后调用目标 Service。Answer Review Agent 只能调用审核所需的只读 Application Services。所有 Agent 都不得直接调用 Source Integration、Knowledge Engine、Semantic View Engine 或底层存储。

## 4. APP-AGENT-CAPABILITY-01

### 4.1 Agent Capability Contract

每个不可变 Contract 至少固定：

- Agent Capability ID / Version / Digest、职责、支持的 Task Kind 和输入 / 输出 Schema。
- Application Access Mode 与允许的 Use Case 集合：Orchestrator 为 `NONE`，Answer Review Agent 为 `READ_ONLY`，Task Execution Agent 为委托授权内的 `QUERY_DIRECT | COMMAND_PROPOSAL`；`NONE` 与 `READ_ONLY` 不得混同，COMMAND_PROPOSAL 不是直连写权限。
- 所需模型 Capability、Platform Proposal Vocabulary / Application Access、Data Classification、资源类别和取消语义；Provider Runtime Tool 权限不得与 Application Access 混用。
- 成功、需要用户输入、可修正失败、不可处理和执行失败的结构化 Result Contract。
- Capability Evaluation Profile 与 Activation Requirement。

Contract 描述职责，不绑定 Agent 名称、实例数量、模型厂商或部署位置。模型自报“我能处理”不是路由依据。

Orchestrator、Task Execution、Answer Drafting 和 Answer Review 的每次模型调用均使用 `NO_EXTERNAL_ACCESS` Provider Runtime。Agent 对 Application Services 的 Query / Command Proposal 发生在模型调用之外，由 Task Control / Application Services 重新授权和执行；不能给 Provider shell、文件、Web、MCP、Connector、Knowledge Repository 或 Agent Runtime 工具来实现 Agent 权限。

### 4.2 Catalog 与选择

Conversational Task Control 维护版本化 `Agent Capability Catalog Snapshot`。最小实现可以由进程内静态配置生成；Catalog Snapshot 仍须具有 Digest，以保证一次任务的路由可回放。真实 Web Task 只接受 `PRODUCTION` Catalog / Activation。

Agent Orchestrator 只能从当前任务冻结的 Catalog Snapshot 中提出选择 Proposal；Conversational Task Control 机械校验 Contract 的激活、权限、Classification 和资源边界后才创建 Invocation。没有匹配能力时形成受审核的 Unsupported Task Result，不把请求交给权限更大的近似 Agent。

Agent / Orchestrator / Answer Review Strategy 的首次或回归评测使用 exact `EVALUATION_ONLY` Grant 和隔离 Evaluation Task Record，复用相同 Contract、Model Gateway 与确定性校验，但不创建生产 Conversational Task、Answer Candidate、Review Decision、Final Authorization 或 Logical Delivery。actual model fingerprint 还须通过 post-call eligibility；评测输出只能进入 Evaluation Run。

生产 Agent Capability 的模型响应同样必须在领域输出封存前消费 `X-MODEL-RESULT-ELIGIBILITY-01`。Conversational Task Control 对 Orchestrator Proposal、Task Execution Result / Candidate Proposal 以及自己拥有的 Reviewer Invocation Outcome 封存门禁负责：它验证 exact Model Call、actual Model / Adapter、Authorized Input Manifest / Provider Request Digest、Isolation Receipt、Catalog / Qualification Proof 和 Capability Attempt。任一项不合格时不封存任何模型语义 Proposal、业务 Result 或 `COMPLETED + ALLOW` Assertion，也不以该内容推进 Task、Review 或响应状态；但 Task Control 必须用平台已经证明的资格失败事实收口自身 Invocation。Reviewer 调用按 7.5 封存 `FAILED + DENY` Outcome Assertion，其他调用封存不携带模型语义内容的执行失败 Result，使下游能够确定性失败关闭，而不是让 Invocation 永久停留在运行中。

## 5. APP-CONVERSATIONAL-TASK-01

### 5.1 输入与原始边界

Web Chat Adapter 向 Conversational Task Control 提交不可变 Request Envelope，至少包含：

- Conversation / Turn / Request ID、Caller、原始用户文本引用 / Digest。
- 经授权的相关用户对话上下文引用；不包含先前 Agent 私有思考或未授权 Tool Trace。
- Locale、Channel Capability、认证 / Classification 和 Request Idempotency Key。

Conversational Task Control 先按 `(Conversation, Turn, Request, Idempotency Key, Request Digest)` 创建或恢复唯一 Task Root / Revision，冻结认证 / Classification、Agent Capability Catalog、Root Allocation 与 Execution Envelope，再把这些不可变输入交给 Agent Orchestrator。Orchestrator 返回 Task Kind、目标、约束、范围、所需响应类型和不确定项 Proposal；Task Control 对照原文机械校验边界并封存 `Conversational Task Revision`。结构化理解不能替代或删减原始请求；没有用户新增授权时不能扩大任务边界。

Orchestrator 使用模型时，Task Control 只有在对应 `X-MODEL-RESULT-ELIGIBILITY-01` 通过后才接受该 Proposal 进入意图 / 路由校验；不合格 Proposal 不能形成 Task Revision、Clarification、Agent Task 或后续动作。确定性 Strategy 不伪造 Model Eligibility，但仍须通过同一 Capability Result Contract。

需要用户决定且不同答案会实质改变任务时，Orchestrator 提出 Clarification Proposal，Task Control 把任务推进为 `WAITING_FOR_USER`，并返回不带业务结论的受控 Clarification Request。只有固定结构、且不包含任何软件知识、操作 Outcome、Gap 或其他业务 Claim 的 Clarification Request 可以不经 Answer Review；一旦包含实质陈述，必须形成 Answer Candidate 并审核。

### 5.2 Agent Task

Orchestrator 只按 Agent 职责提出 Agent Task Proposal；Conversational Task Control 校验后形成不可变 Agent Task：

- Conversational Task / Revision、原始 Request / Context References。
- 分配给该 Agent 的目标、in-scope / out-of-scope、约束和期望 Result Schema。
- Agent Capability Contract / Catalog Snapshot、Orchestration Revision、Deadline / Resource Envelope。
- 前序 Agent 的结构化 Result Reference；不传递其私有 Model Context 或隐藏推理。

Orchestrator 不把 Agent Task 进一步拆成 Query、Connector、Knowledge Update 步骤；这些由具体 Task Execution Agent 在其职责内动态决定。Agent Task / Invocation、Delegated Grant 和子 Allocation 由 Task Control 一次绑定后分派，避免出现已启动 Agent 却没有合法授权的中间状态。

### 5.3 Delegated Application Grant

模型产生的 Task / Route Proposal 不等于应用调用授权。每个 Agent Invocation 必须绑定由 Conversational Task Control 依据认证上下文、原始 Request 与当前权限机械签发的不可变 `Delegated Application Grant`，至少固定：

- Caller、原始 Request / Task Boundary Digest、Purpose、Classification、Authorization Revision / Expiry。
- 允许的 `QUERY_DIRECT | COMMAND_PROPOSAL`、Use Case Contract、目标 Scope / Resource 边界与最大 Effect Class；COMMAND_PROPOSAL 不授予 Agent 直接分派权。
- Agent Capability / Invocation、禁止操作和是否要求逐动作确认。

Grant 只把用户已经授权的能力委托给一次 Invocation，不能由 Agent Capability 的“可调用集合”推导出用户同意。Orchestrator 只能在 Proposal 中引用期望的访问模式，不能签发或绑定 Grant；Reviewer 的 Grant 固定为审核所需只读集合。Grant 变化必须创建新 Invocation，Application Services 在每次调用时校验 exact Grant，而不是信任 Agent 自报。

## 6. APP-AGENT-ORCHESTRATION-01

### 6.1 动态编排

Agent Orchestrator 每次只提出下一个职责级动作，Conversational Task Control 校验并推进权威状态：

- 调用某个 Task Execution Agent。
- 把 exact Answer Candidate 交给 Answer Review Agent。
- 根据 Review Finding 创建 replacement Agent Task。
- 请求用户澄清。
- 在获得 Final Response Authorization 后交付，或以经过审核的 Gap / Failure Candidate 结束。

这不是预先写死的固定流水线。最终业务响应必须审核是固定门禁；Agent 的调用次数和修正循环由任务结果决定。

### 6.2 最小可恢复状态

Conversational Task Control 为每个 Task 持有单调 `Orchestration Revision` 和当前 Phase：

`RECEIVED | ROUTING | AGENT_RUNNING | REVIEWING | WAITING_FOR_USER | CANCEL_REQUESTED | ACTION_OUTCOME_PENDING | RESPONSE_AUTHORIZED | RESPONSE_OUTCOME_PENDING | COMPLETED | FAILED | CANCELED`

Phase 不保存领域步骤。每次 Agent 调用产生由 Task Control 拥有的独立 `Agent Invocation Record`，固定 Task / Orchestration Revision、Capability Contract、Input Digest、Delegated Grant、Resource Envelope、Attempt ID 和结构化 Result Reference。相同 Invocation Key / Input Digest 只恢复原 Attempt；不同输入创建新 Invocation。

任何 Task Phase、Active Invocation、Dispatch Fence 推进都由 Task Control 以 `(Task ID, Orchestration Revision, Current Phase, Active Reference)` 执行 CAS；Candidate、Review、Authorization 与 Delivery 由 Response Control 在自己的状态上 CAS。两者通过不可变 Reference / Revision 交接，不执行跨 Owner 状态更新。CAS 失败的结果只能进入迟到结果处理，不能覆盖当前状态。

迟到 Agent Result 只有在 Task、Orchestration Revision、Invocation 和 Expected Result Contract 仍匹配时才能驱动普通后续流程。用户澄清、任务替换、Answer Candidate 替换或终止都会推进 Revision；旧只读结果只保留历史，不触发后续 Agent 或交付。已经 claim 的副作用调用与已经 claim 的 Response Delivery 是两个终态收口例外：无论后续取消或 Revision 如何变化，都必须按原 Dispatch Claim 解析权威 Outcome；它们不能继续旧任务的普通编排、产生新动作或发送第二份正文，也不能被静默丢弃。

### 6.3 循环与终止

- `REVISION_REQUIRED` 不允许原地修改 Candidate；Task Execution Agent 产生新的 Candidate Revision，再由新的 Review Attempt 审核。
- Review 发现 Requirement 不忠实时，具体 Agent 必须通过 Application Services 形成 replacement Requirement，并重新调查 / Assessment；Orchestrator 不改 Requirement。
- Review 发现知识不足只产生 Finding；是否请求既有 Gap Resolution 由新的 Task Execution Attempt 决定，Answer Review Agent 不发起更新。
- 资源上限、重复 Finding、无可用能力或不可恢复失败时停止循环，形成可审核的 Gap / Failure Candidate；不能为了得到 PASS 无限重试或更换未激活模型。
- Task Control 以 `CANCEL_REQUESTED` 推进 Task Revision / Dispatch Fence，只阻止普通重规划、新业务动作和无关模型调用。取消 CAS 与 Response Control 的发送 Claim 通过同一 Application Store 的当前只读状态线性化：取消先提交时发送重验失败；发送 Claim 先提交时，Task Control 记录原 Delivery / Authorization 并进入 `RESPONSE_OUTCOME_PENDING`。尚未 claim 的 `PREPARED` Call 收口为 `NOT_DISPATCHED`；已 `DISPATCHED | OUTCOME_PENDING` 的副作用使任务进入 `ACTION_OUTCOME_PENDING`。
- 取消后只保留有界 `Outcome Reconciliation Lane`：以原 Dispatch Claim / Idempotency Key 完成或恢复已经 claim 的原调用、查询既有 Call / Use Case Outcome、运行确定性 System Outcome Candidate Formation、只读 Answer Review 和 Delivery Revalidation。固定 Outcome 模板可确定性审核；只有 Review Contract 确实需要语义审核时才允许一个受限、无 Tool / 无副作用的 Review Model Attempt。该 Lane 不得创建新的 Logical Action Occurrence、换 Key 或恢复旧计划。
- 全部权威终态解析并形成经审核的结果披露后，才能最终收口。用户已取消但取消前分派的动作后来成功或失败时，Task 以取消语义进入 `CANCELED`，同时永久记录并如实披露该动作的真实 Outcome；不能把“任务后续编排已取消”表述为“已分派动作被撤销”。未发生取消的普通任务才按业务结果进入 COMPLETED / FAILED。不能在真实 Outcome 未知时告诉用户“操作已取消”。

### 6.4 Task Validation Assertion

Conversational Task Control 提供只读 `ValidateTaskForResponse`。请求固定 Purpose = `REVIEW_AUTHORIZATION | DELIVERY_DISPATCH`、Validation Mode = `NORMAL | OUTCOME_RECONCILIATION`、Task / Orchestration Revision、Candidate / Review / Authorization References、Caller / Request / Classification 和 Expected Task State Revision。返回的不可变 Task Validation Assertion 至少包含：

- exact Task / Revision / Phase / State Revision、当前 Active Invocation / Candidate Binding 与 Dispatch Fence。
- 请求中的 Candidate / Review / Authorization References 及逐项 `ALLOW | DENY`。
- Caller / Request / Classification、Validation Purpose / Time 与 Assertion Digest。

`NORMAL` 模式下，`REVIEW_AUTHORIZATION` 只允许仍处于 exact Candidate 审核阶段的 Task；`DELIVERY_DISPATCH` 只允许已绑定 exact Authorization、未取消且尚未完成其他响应的 Task。

`OUTCOME_RECONCILIATION` 只用于取消后收口取消前已经取得 dispatch claim 的副作用调用。Task Control 必须重建并固定原 Logical Action Occurrence / Application Call / Dispatch Claim / Idempotency Key、取消 Revision、exact 已解析 Use Case Outcome，以及由确定性 System Outcome Candidate Formation Strategy 形成的 Candidate；Review 和 Delivery 都只能绑定这组对象。它不能授权任意旧 Candidate、新动作、新调用、换 Key、恢复旧计划或第二份响应。通过该模式交付后，Task 按 6.3 的取消语义收口，并如实保留已执行动作结果。

Assertion 不推进 Task，也不是 Response Authorization。Response Control 在自己的事务中重读 Expected Task State Revision；并发 Task 变化使当前操作失败，随后只能基于新 Revision 重新评估。

## 7. APP-TASK-EXECUTION-01

### 7.1 执行边界

Task Execution Agent 基于完整 Agent Task 动态选择 Application Use Case：

- 知识任务：登记 Task Boundary / Requirement，打开 Active Knowledge Use Binding，在固定 Session 上调查，取得独立 Sufficiency Assessment；可补充 Gap 只通过正常 Knowledge Update 解决。
- Management / Knowledge Update 任务：调用相应用例，并只依据不可变 Application Use Case Result 描述执行结果。
- 混合任务：每个副作用用例先产生独立结果，知识解释仍走 Knowledge Use；不能用操作成功推断软件世界事实。

Application Services 返回的 `Expected Use Epoch` 失效信号会终止旧调查与答案草稿。新 Snapshot 激活后，Agent 建立新的空 Knowledge Investigation / Answer Drafting ModelExecutionContext；只保留用户原始对话、Task Boundary / Requirement 和新正式结果，不保留 Artifact、Candidate、旧 Tool Trace 或旧答案草稿。

### 7.2 副作用动作授权

Task Execution Agent 对有副作用的 Application Use Case 只能先向 Conversational Task Control 提交结构化 `Action Proposal`。Effect Class 来自 Use Case Contract，不由模型判断。Task Control 仅在下列条件全部满足时签发 exact `Action Authorization`：

- Proposal 位于 Delegated Application Grant 的 Use Case、目标、Purpose、Classification 与有效期内。
- Authorization 固定 canonical Request Digest、Target / Parameters、Effect Class、Grant / Task Revision、稳定 Logical Action Occurrence、唯一 Application Call Record / Idempotency Key 和 Expiry。
- 用户原始请求已经无歧义地授权同一动作和目标，且策略允许直接执行；否则必须取得绑定同一 Digest 的显式用户确认。

`Logical Action Occurrence` 由 Task Control 按 `(Task Root, 用户授权的动作次数, canonical Use Case / Target / Parameters / Effect Digest)` 分配，并跨 Orchestration / Invocation Revision 保持稳定。一个没有明确次数的用户授权默认只产生一个 Occurrence；审核修正、Agent 重试或新 Invocation 仍解析原 Occurrence / Outcome。确实需要再次执行相同动作时，必须由新的明确用户授权 / 确认产生新 Occurrence。

模型可以建议“需要执行什么”，不能确认用户意图或签发 Authorization。同一 Occurrence 最多一个当前 `ISSUED` Action Authorization；未消费 Authorization 到期、Grant / Invocation 替换时，只能由 Task Control CAS 撤销并为同一 Occurrence / Call / Key 签发新 Revision。Action Authorization 只能从 `ISSUED` 在 dispatch claim 中单次消费；一旦消费，不得为该 Occurrence 再签发可执行 Authorization。参数、目标或授权次数任一变化都重新提议并取得新的用户授权 Occurrence。这是动作正确性边界，不引入企业审批流或通用策略平台；最小实现是 Use Case Contract 上的静态 Effect Class、Task 内稳定 Occurrence 和本地确定性规则。

### 7.3 Application Call Record

Task Control 为每个 Logical Action Occurrence 在分派前创建且只创建一个扁平 `Application Call Record`，以 `(Task Root, Logical Action Occurrence)` 唯一标识，并固定提出它的 Invocation / Slot、Use Case、canonical Request / Digest、Application Idempotency Key、Causation 与 Task Revision；`PREPARED` 时可以 CAS 替换尚未消费的 Grant / Action Authorization Revision，进入 `DISPATCHED` 后全部冻结：

`PREPARED → DISPATCHED → OUTCOME_PENDING → TERMINAL`

`PREPARED → NOT_DISPATCHED`

- `PREPARED → DISPATCHED` 由同一个 Task Control 事务同时校验 Task Revision / Phase / Dispatch Fence、Grant / Authorization 有效性、Occurrence / Call / Key 完全匹配，并消费 Action Authorization。该 CAS 是唯一 dispatch claim；Task Control 随后以已经 claim 的 exact Idempotency Key 调用目标 Application Service，Agent 和 Orchestrator都不能自行分派。
- `CANCEL_REQUESTED` 先赢得 Task Dispatch Fence 时，后续 dispatch claim 失败并把未 claim 的 Record 收口为 `NOT_DISPATCHED`；dispatch claim 先赢时，取消必须把它纳入 `ACTION_OUTCOME_PENDING`。
- `DISPATCHED` 后不允许回到未分派；`TERMINAL` 必须引用目标 Result Owner 返回的权威 Use Case Attempt / Outcome。进程在 claim 后、调用前崩溃时仍由 Task Control 只以同一 Key恢复 / 分派。
- 响应丢失、进程恢复、审核修正或取消时只查询 / 重放同一 Application Idempotency Key；不得为同一 Occurrence 创建第二个 Call / Slot / Key。
- `DISPATCHED | OUTCOME_PENDING` 的副作用阻止该 Occurrence 的替代动作，直到原 Outcome 可证明为成功、失败或未执行。
- 只读调用仅在其 Use Case Contract 要求恢复或审计时保存 Call Record；副作用调用必须保存。

该 Record 不表达步骤依赖、DAG 或调度计划；它只消除“调用已提交但 Agent 不知道”的重复副作用窗口。

### 7.4 Task Execution Result

Agent 向 Conversational Task Control 提交结构化 Result Proposal；Task Control 校验 Invocation / Result Contract 后封存，并把 exact Result Reference 提供给 Orchestrator。Result Kind 只允许：

- `ANSWER_CANDIDATE_READY`：包含 exact Candidate Proposal Reference / Digest；正式 Candidate Reference 只有 Response Control 校验并封存后才存在。
- `USER_INPUT_REQUIRED`：包含当前边界内的 Clarification Request。
- `TASK_UNSUPPORTED`：没有匹配能力或请求越界；需要回复用户时同时包含 exact Unsupported Candidate Reference。
- `TASK_BLOCKED`：包含 Knowledge Gap、Application Limitation 或不可恢复 Use Case Result Reference；需要回复用户时同时包含 exact Gap / Failure Candidate Reference。
- `EXECUTION_FAILED`：执行未形成语义结果，包含失败引用；需要回复用户时同时包含 exact Failure Candidate Reference。

Agent Result 不是 Application Use Case Result，不是正式知识，也不能作为 Answer Claim 的最终依据。Task Control 封存的 Orchestration / Invocation / Application Call Outcome 只能证明对应执行状态，不能证明软件世界命题。

Task Execution、Answer Drafting 或其他模型步骤影响 Result / Candidate Proposal 时，Task Control 还必须在封存 Result 前验证每个实质模型输出的 `X-MODEL-RESULT-ELIGIBILITY-01`，并把 exact Eligibility Result / Model Call / Manifest / Isolation Receipt Reference 纳入 Invocation Result Closure。存在不合格、缺失或与输出 Digest 不匹配的模型步骤时，Invocation 进入执行失败，不得封存 `ANSWER_CANDIDATE_READY`、Gap / Failure Candidate 或由该响应派生的其他语义 Result；固定的确定性 System Outcome Candidate 只能依据平台已封存失败状态重新形成，不能复用不合格模型文本。

为避免终止路径断裂，Task Execution Capability 内置一个始终可用的确定性 `System Outcome Candidate Formation Strategy`。它不调用模型，只消费平台封存的 `NO_AGENT_CAPABILITY`、Orchestration / Invocation / Application Call Outcome、Gap 或 Limitation，且只能形成 `UNSUPPORTED | GAP | FAILURE` Candidate；不能添加自由文本业务结论。它是既有 Task Execution Capability 的一种 Strategy，不新增 Agent、服务或模块，产物仍须完整 Answer Review。若连固定结构 Candidate 都无法持久化，只能返回不含业务 Claim 的协议失败。

### 7.5 APP-REVIEWER-INVOCATION-OUTCOME-01

Answer Review Agent 的 Assessment / Finding Proposal 由 DD-APP-RESPONSE-CONTROL 定义，但 Reviewer Agent Task / Invocation、read-only Delegated Grant、分派和运行终态仍由 Conversational Task Control 拥有。Review Agent 不能把自报的 Invocation / Grant ID 直接作为 Response Control 接受 Proposal 的证明。

Task Control 在收到 Reviewer 执行结果时，必须先从自身权威状态重建并原子封存不可变 `Reviewer Invocation Outcome / Validation Assertion`：

- exact Conversational Task / Orchestration Revision、Reviewer Agent Task / Invocation、Dispatch Attempt、read-only Delegated Grant 和 Catalog / Allocation。
- exact Response-Control-owned Review Attempt / Reviewer Dispatch Requirement / READY Review Request Reference 与 Digest；这些只作为绑定输入，不取得其所有权。
- `COMPLETED | FAILED | CANCELED | STALE` Invocation Outcome、Review Assessment Proposal Digest / Output Schema Digest，以及原始 Result Reference；Task Control 不读取、修改或评价 Proposal 语义。
- 使用模型时的 Capability / Strategy / Model Call、actual Model / Adapter、Authorized Input Manifest / Provider Request Digest、Isolation Receipt 和 `X-MODEL-RESULT-ELIGIBILITY-01` Result / Qualification Proof。
- Invocation Result Closure Digest、Task State Revision、Validation Time 和 Assertion Digest。

只有 exact Invocation 已合法分派、Grant / Review Request 未串用、输出形状符合 Agent Capability Contract、Task 对该 Invocation 的收口仍有效，且使用模型时 post-call model eligibility 通过，Task Control 才能封存 `COMPLETED + ALLOW` Assertion，并把 `Proposal Reference / Digest + Assertion` 交给 Response Control。确定性 Review Strategy 明确记录 `Model Eligibility = NOT_APPLICABLE` 及 Strategy Reference，不伪造模型证明。其余情况封存相应终态和 `DENY` Assertion，或记录执行失败；不把不合格 Proposal 交给审核矩阵。Response Control 必须验证该 Assertion 后才能把自己的 Review Attempt 推进为 `ASSESSMENT_RECEIVED`，但 Review Decision、Matrix 和 Authorization 仍完全由 Response Control 拥有。

相同 Reviewer Invocation / Result Digest 只恢复同一 Outcome / Assertion；不同 Digest 冲突。Task Control 在 Proposal 已生成但 Assertion 尚未提交时崩溃，只恢复并封存同一 Invocation Outcome；Response Control 在收到 Assertion 前保持 READY。Response Control 已封存 Assessment 后，Task Control 重放同一 Assertion只取得同一结果，不创建第二个 Invocation 或 Review Attempt。两个 Owner 只交换不可变引用，不互写状态或建立跨 Owner CAS。

## 8. 与 Response Control 的交接边界

Task Execution Agent 返回 `ANSWER_CANDIDATE_READY` 时只携带 Candidate Proposal、Task / Invocation、Application Result / Requirement / Assessment References 和正文 Draft。Conversational Task Control 校验 Invocation 与 Result Contract 后，把 exact Proposal 交给 DD-APP-RESPONSE-CONTROL；它不分配 Candidate ID、不修改 Claim、不审核正文，也不签发交付授权。

Response Control 返回的 Review Result、Final Authorization 和 Delivery Outcome 都是其权威结果。Task Control 只：

- 根据 exact Review Result 选择新的 Agent Invocation、等待用户或请求交付。
- 对交付请求提供当前 Task Validation Assertion。
- 根据 exact Delivery Outcome Assertion 推进自己拥有的 Task Phase。

Review Agent 的执行结果按 7.5 先由 Task Control 封存 Reviewer Invocation Outcome / Validation Assertion，再交给 Response Control。Task Control 只证明调用与输出来源、资格和 Digest，不审核 Finding；Response Control 只消费 Assertion，不推进或复制 Reviewer Invocation 状态。

两个 Owner 不互写状态，不建立跨 Owner CAS。任何响应语义、审核矩阵、发送幂等和正文冻结规则以 DD-APP-RESPONSE-CONTROL 为唯一规范。

## 9. 主流程

```mermaid
sequenceDiagram
    participant W as Web Chat
    participant C as Conversational Task Control
    participant O as Agent Orchestrator
    participant T as Task Execution Agent
    participant A as Application Services
    participant R as Response Control

    W->>C: Request envelope
    C->>C: Freeze task, catalog, authorization and root allocation
    C->>O: Frozen task context
    O-->>C: Intent / route proposal
    C->>C: Validate; create invocation and grant
    C->>T: Immutable Agent Task
    T->>A: Authorized query or side-effect-free use case
    A-->>T: Immutable result references
    opt Side-effect command proposed
        T->>C: Action proposal
        C->>C: Authorize occurrence and claim dispatch
        C->>A: Exact command / stable idempotency key
        A-->>C: Immutable use case result
        C-->>T: Exact outcome reference
    end
    T-->>C: Structured Task Execution Result
    C->>R: Candidate proposal / task references
    R-->>C: Review / authorization / delivery outcome references
    C->>C: Advance only own task state
```

Response Control 内部审核和交付流程不在本图展开。Agent 调用次数由任务动态决定；用户澄清、Requirement 修正、Knowledge Update 后重查和审核 Finding 都创建新的 Task / Invocation Revision，不回写旧对象。

## 10. AI Native 与能力演进

模型适合承担用户意图理解、职责级路由、澄清识别、具体任务规划、Application Use Case 选择和 Candidate Proposal 组织。平台不可让渡：

- 原始 Request / Task Boundary、Agent 权限、Capability Activation 和资源上限。
- Delegated Grant、Action Authorization、Application Dispatch Claim 和 Expected Use Epoch。
- Application Result / Formal Reference 的稳定引用与当前性校验。
- 迟到结果拒绝、幂等、取消、Classification 和 Task 状态推进。

模型增强时可以减少固定 Intent 规则、专用任务 Agent 和人工规划模板；不能让 Provider 直接调用 Application Services / Core Capability，也不能把模型 Proposal 当作授权或 Outcome。模型退化时只切换到已评测激活的 Strategy，不在同一 Attempt 内静默换模型。

## 11. 持久化、幂等、取消与恢复

Conversational Task Control 至少持久化 Conversational Task / Revision、Agent Task、Catalog / Root Allocation Binding、Delegated Application Grant、Agent Invocation / Result、Logical Action Occurrence、Action Authorization 和必需 Application Call Record。

- Request / Invocation / Call Key 唯一绑定输入 Digest；不同输入不得复用。
- 所有状态推进按当前 Task Revision / Phase / Active Reference CAS；迟到结果只保留历史。
- 每个用户授权的 Logical Action Occurrence 只有一个稳定 Application Idempotency Key。恢复只解析原 Use Case Outcome，不能换 Key 重做。
- 取消先阻止新的 dispatch；已经分派的副作用进入 `ACTION_OUTCOME_PENDING`，只允许有界 Outcome Reconciliation。
- 恢复从持久状态继续，不从模型对话、私有 Tool Trace 或内存计划猜测。
- Response Result 只通过 exact Reference / Digest 交接；Task Control 不复制 Response Control 状态。

## 12. 失败语义

| 失败类别 | 处理 |
|---|---|
| `NO_AGENT_CAPABILITY` | 形成受限 Unsupported Proposal 并交给 Response Control；不路由给权限更大的近似 Agent |
| `AGENT_TASK_BOUNDARY_MISMATCH` | 拒绝 Invocation，基于原 Request 重建任务 |
| `AGENT_RESULT_STALE` | 只保留历史，不触发后续动作 |
| `DELEGATED_GRANT_MISMATCH` | 不调用 Use Case；重新授权或请求用户决定 |
| `ACTION_AUTHORIZATION_REQUIRED` | 不执行副作用 |
| `ACTION_OCCURRENCE_ALREADY_CONSUMED` | 返回原 Call / Outcome；再次执行需要新的明确授权 Occurrence |
| `APPLICATION_DISPATCH_FENCED` | 不越过 Cancel Fence 创建调用 |
| `APPLICATION_CALL_OUTCOME_PENDING` | 阻止替代动作，只查询原 Key 的权威 Outcome |
| `APPLICATION_RESULT_UNRESOLVED` | 不生成成功 Proposal，先解析原用例 Outcome |
| `KNOWLEDGE_USE_EPOCH_STALE` | 丢弃旧调查 / Draft，以新 Session 和空模型上下文重做 |
| `MODEL_RESULT_NOT_ELIGIBLE` | actual Model / Adapter、Manifest / Request Digest、Isolation Receipt 或 Qualification 与冻结 Catalog 不匹配；不封存 Orchestrator / Task / Candidate / Reviewer 输出，不推进 Task 或 Review |
| `REVIEWER_INVOCATION_OUTCOME_INVALID` | Reviewer Proposal 缺少 Task-Control-owned Outcome / Validation Assertion，或 Invocation / Grant / Review Attempt /输出 Digest 不一致 | Response Control 不得接收 Proposal；Task Control 只恢复 exact Invocation 或失败关闭 |
| `RESPONSE_RESULT_STALE` | 不推进 Task；按当前 Task Revision 重新取得 Response Control 结果 |

## 13. 可观测性与敏感信息

传播 Conversation / Task / Orchestration Revision、Agent Capability / Invocation、Delegated Grant、Application Call、Requirement / Session / Use Epoch、Candidate Proposal 和 Correlation Reference。

记录路由 Outcome、Agent 调用次数、Use Case 类型、Action Dispatch、修正循环、Token、延迟、成本和 Task Phase。Telemetry 不复制用户正文、Candidate 正文、正式命题、Evidence、Artifact、模型输入或隐藏推理；只保存受控引用、Digest、类型和数量。

Agent ModelExecutionContext 按 Capability / Attempt 隔离。长期 Conversation 只保留获授权的用户消息和最终交付响应，不把 Agent Tool Trace 自动注入后续任务。

## 14. 拟议不变量与验证义务

1. Agent Orchestrator 只提出意图、路由和下一职责动作，不执行领域用例、不生成或审核答案。
2. 具体 Agent 只通过 Application Services 使用系统能力，不直接访问 Core Capability 或存储。
3. Task Control 是 Conversational Task、Agent Invocation、Delegated Grant、Action Authorization 和 Application Dispatch 的唯一写者。
4. Agent / 模型 Proposal 不等于任务状态、应用调用授权、Application Outcome 或 Response Authorization。
5. 每个 Logical Action Occurrence 只绑定一个 Call / Idempotency Key；取消和恢复不得制造重复副作用。
6. Requirement、调查和 Candidate Drafting 使用隔离 ModelExecutionContext；Use Epoch 前进后旧上下文结果不能被当前任务接受。
7. Response Control 的 Candidate、Review、Authorization 和 Delivery 状态不由 Task Control 复制或改写。
8. Agent 扩展依赖 Capability Contract，不要求提前建设远程 Registry、通用 DAG 或多 Agent 协商平台。
9. 所有模型生成的 Orchestration / Task Execution / Candidate / Reviewer 结果必须在生产封存前通过 `X-MODEL-RESULT-ELIGIBILITY-01`；不合格模型输出不能推进 Task、Invocation 或 Response Control。
10. Reviewer Invocation Outcome / Validation Assertion 由 Task Control 独占封存并绑定 exact Invocation / Grant / Review Attempt /输出 Digest /模型资格；Response Control 只有验证该 Assertion 后才能接收 Assessment Proposal，且仍独占 Review Decision。

进入实现前至少验证任务边界保真、Capability / Grant 越权拒绝、Action Dispatch 竞态、同一动作跨 Invocation 去重、取消后 Outcome Reconciliation、旧 Epoch / 迟到结果拒绝、Agent 直连 Core Capability 拒绝、各生产 Agent 输出的 post-call model eligibility，以及 Reviewer Proposal 在缺少/错配 Task-Control-owned Invocation Outcome Assertion 时不能进入 Response Control。还须验证 Proposal 已产生但 Assertion 未提交、Assertion 已提交但 Response Control 未接收、双方重放与取消竞态均只恢复 exact Invocation / Review Attempt。普通模型准确率、专职 Agent 收益和模型升级影响由 Capability Evaluation 验证；只有公共 Agent Contract 无法表达真实任务且会迫使改变契约时才启动 Design Validation Demo。
