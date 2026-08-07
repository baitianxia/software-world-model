# Capability Execution Contract 详细设计

| 元数据 | 值 |
|---|---|
| Document ID | DD-X-CAPABILITY-EXECUTION |
| Version | 0.1.0 |
| Status | Accepted |
| Document Steward | Application Layer / Shared Execution Contract |
| Architecture Baseline | SWM-ARCH@1.2 |
| Depends On | None |
| Owns Contracts | X-CAPABILITY-META-01、X-STRATEGY-META-01、X-EXECUTION-ENVELOPE-01、X-RESOURCE-ALLOCATION-01、X-CAPABILITY-RESULT-01、X-MODEL-RESULT-ELIGIBILITY-01、X-RESULT-DELIVERY-ASSERTION-01 |
| Supersedes | `Software_World_Model_MVP_Detailed_Design.md` 中 DD-00B 的执行框架部分 |
| Rationale ADR | AD-019、AD-020、AD-021、AD-059、AD-060、AD-087、AD-088、AD-094、AD-100、AD-110、AD-115、AD-116、AD-117、AD-131、AD-132、AD-135 |
| Design Validation | None |
| Conformance Cases | None |
| Capability Evaluation | None |

> 概要架构约束直接生效；本文新增的元契约、执行信封和资源结算语义在状态进入 `Accepted` 前均为拟议设计。

## 1. 目的与范围

本文定义 Deterministic、Model-Primary 和 Hybrid 能力共同遵守的执行元契约，使业务能力可以随模型变化替换 Strategy，而不改变模块职责和正式状态边界。

本文不创建集中式 AI 业务引擎，也不拥有任何具体 Evidence、Entity、Fact、Inference、Semantic View、Sufficiency 或 Review 逻辑。共享执行支持是模块化单体内的横切实现责任，不新增顶层业务模块。

本文不定义 Model Provider 调用、Strategy 评测与激活、具体 Capability 字段、Prompt 或阈值；它们分别由 Model Gateway、Management 以及各能力所有者定义。

## 2. 所有权

| 对象或决定 | Contract / Data Owner |
|---|---|
| 某项 Capability Contract、领域输入输出和验收语义 | 提供该能力的业务模块 |
| 该 Capability 的 Strategy 实现与确定性校验 | 提供该能力的业务模块 |
| 用例可用的 Capability Catalog Snapshot、激活 Strategy 解析 | Application Services |
| Agent 内的任务级能力选择 | Agent Orchestrator / 具体 Agent提出 Proposal；Conversational Task Control 校验并签发确切 Grant 与子 Allocation |
| 预算/资源政策、Resource Account、Allocation 及其运行状态 | Application Layer；目标 Application Service 拥有直接用例状态，Conversational Task Control 拥有 Web Task 根项与 Agent 子分配；Agent Orchestrator 只提资源需求 Proposal |
| Execution Envelope 值类型、Allocation 原子预留/结算机制和通用结果外壳 | Shared Execution Infrastructure（只执行所有者命令，不是逻辑数据 Owner 或业务模块） |
| Provider 模型调用 | Model Gateway |
| Production / Evaluation-only Execution Qualification 的签发与失效 | Application Layer 的资格判定 Owner；本 Contract 只验证调用方传入的 opaque Proof 与冻结 Policy |

Document Steward 只维护共享元契约，不取得各业务 Capability 的领域所有权。

## 3. X-CAPABILITY-META-01

每个 Capability Contract 至少定义：

| 语义 | 约束 |
|---|---|
| Capability ID | 稳定身份，不使用类名、Prompt 名或模型名 |
| Contract Version | 独立语义版本；不兼容输入、输出或不变量变化增加主版本 |
| Purpose | 单一领域问题和适用边界 |
| Input Contract | 输入、稳定引用、前置条件、信任级别和数据分类 |
| Output Contract | 结构化结果、后置条件、确定性校验和权威性质 |
| Tool Contract | 可以申请的 Tool、参数边界、读取/副作用级别和结果预算 |
| Authority Boundary | 输出是 Proposal、Assessment、Application Result 或正式状态请求；谁拥有最终决定 |
| Failure Contract | 失败分类、部分结果、重试、取消和受控回退语义 |
| Evaluation Contract | 样例族、Oracle、指标、比较基线和门禁所有者 |

Provider 可接受的 JSON 或 Structured Output 形状不是 Capability Contract。形状通过只证明可以解析，能力所有者仍须执行完整领域校验。

## 4. X-STRATEGY-META-01

Strategy 是实现一个确切 Capability Contract Version 的不可变方案：

| 类型 | 语义 |
|---|---|
| Deterministic | 主要由确定性代码或规则完成 |
| Model-Primary | 模型承担主要认知工作，平台执行边界控制和领域校验 |
| Hybrid | 确定性步骤与模型步骤按显式执行图组合 |

Strategy Version 固定：

- 所实现的 Capability Contract Version。
- Strategy Owner 和执行入口。
- 执行阶段、确定性校验器和输出转换器版本。
- 所需 Model Gateway 能力、Tool Contract 和隔离要求。
- Prompt/Instruction、模型选择政策和实质参数引用。
- 默认重试、候选修正和资源政策引用。

改变上述任一项且可能影响领域结果时创建新 Strategy Version，不能在原版本下静默替换。

模型只承担语义理解、规划、消歧和 Proposal/Assessment 生成。权限、稳定身份、Lineage、Context、准入、发布和放行仍由相应平台契约控制。

## 5. Capability Catalog Snapshot

Application Services 在进入 Core Capability 前，将允许使用的 Capability Contract、Strategy、Tool Contract 和资源政策解析为不可变 Catalog Snapshot。Catalog Mode 只能是：

- `PRODUCTION`：每个 Strategy 都由 Application 资格判定 Owner 签发的当前 Production Qualification Proof 支持。
- `EVALUATION_ONLY`：每个候选由 exact Evaluation Execution Qualification Proof 支持，只能执行评测。

两种 Mode 不能混合；生产 Catalog 只允许已激活 Strategy。

Catalog Snapshot 必须：

- 固定确切 Contract 和 Strategy Version，不使用 `latest`。
- 只包含当前用例、Scope、阶段和数据分类允许的能力。
- Catalog 记录 opaque Qualification Proof Reference / Digest、签发 Owner / Authority Revision，以及执行时可机械验证的 exact Strategy、Model / Adapter Identity Policy、Tool、数据和资源边界；公共 Contract 不解析下游评测对象的内部状态。
- 在一次运行中保持不变；新的激活只影响后续运行。

首次评测候选 Strategy 时，Application 资格判定 Owner 可以按本元契约签发不可变 `EVALUATION_ONLY` Qualification Proof。它只授权 exact candidate、Case / Fixture、Model / Tool、数据和资源边界，不要求生产资格；Catalog 带 Purpose = EVALUATION。Runtime、业务模块和 Model Gateway 复用正常执行路径，但输出只能写入签发方指定的隔离 Evaluation Sink，严禁进入生产知识、Application Result、答案或生产缓存。具体评测 Definition、Validity 和 Activation 由下游资格判定主题拥有，不是本元契约的输入结构。

业务模块校验传入 Strategy 确实实现所请求的 Capability，并校验 Catalog 是有效生产 Activation 或 exact EVALUATION_ONLY Grant，随后在模块内部执行自身 Strategy。业务模块不得反向调用 Application Services 获取或改变激活状态。

### 5.1 X-MODEL-RESULT-ELIGIBILITY-01

任何 Strategy 使用模型时，业务 Capability Owner 必须在封存 Proposal / Assessment / Candidate / Application Result 等领域输出前，机械验证 Model Gateway 返回的 actual Model Fingerprint、Adapter Version、Replay Classification、Authorized Input Manifest / Provider Request Digest 和 Isolation Receipt：

- `PRODUCTION` Catalog：actual identity 必须落在 Catalog 冻结并由 Qualification Proof 覆盖的 Allowed Model / Adapter Identity Policy 内。
- `EVALUATION_ONLY` Catalog：actual identity 必须符合 Qualification Proof 冻结的候选模型与 Replay Policy；输出只能写入 Proof 指定的隔离 Evaluation Sink，不得写入生产领域 Repository。
- Model Call 的 Manifest、Prompt / Provider Request Digest、Runtime Isolation Policy 和 Isolation Receipt 必须与 Capability Attempt 冻结输入一致，Receipt 所依据的 Adapter Conformance 仍有效，且不存在 `ISOLATION_BREACH` / 隐藏上下文未受控状态。

模型身份不满足时返回 `MODEL_FINGERPRINT_NOT_EVALUATED`；输入或隔离闭包不满足时返回 `MODEL_EXECUTION_NOT_ELIGIBLE`。两者都不产生领域结果，并把固定 actual identity、Manifest / Receipt、Catalog 和 Qualification Proof 的失效信号返回签发 Owner。Capability Owner 和 Gateway 都不反向写资格判定 Repository；签发 Owner 如何使评测或激活失效由其下游 Contract 决定。异步失效事件不能代替本次 post-call 门禁。

## 6. X-EXECUTION-ENVELOPE-01

每个 Agent、Capability、模型、Tool、Connector、Knowledge Update 和审核执行都传播不可变 Execution Control Envelope：

| 语义 | 作用 |
|---|---|
| Correlation Reference | 关联同一外部请求或计划触发 |
| Causation / Parent Reference | 表达直接触发关系 |
| Actor / Initiator Reference | 记录用户、Agent、Scheduler 或策略来源 |
| Task / Run Reference | 固定任务、Investigation、Evaluation 或 Review 身份 |
| Scope Reference | 存在知识边界时固定 owning/target Scope |
| Snapshot / Schema Reference | 涉及正式知识时固定确切版本 |
| Capability / Strategy Reference | 固定当前 Contract 与实现版本 |
| Resource Account / Policy Reference | 指向预算账户和不可变配额、速率、并发政策 |
| Allocation Reference | 当前执行已被原子预留的资源上限 |
| Budget Conversion Rule Reference | Allocation 使用货币额度时固定 Application-owned 用量换算规则；不引用后算 Telemetry Valuation |
| Data Classification | 限制内容可发送的 Provider 和 Tool |

模型输出和 Core Capability 都不能修改 Envelope 或自行增配资源。需要扩权时返回上层控制者重新决策。

本公共元契约把 Scope / Snapshot / Schema 等业务引用视为由领域 Owner 定义的 opaque stable reference，不复制其结构，因此不反向依赖 Knowledge Reference Contract。

### 6.1 并行预算与结算

- Application Layer 拥有 Resource Policy、Account 和 Allocation 的逻辑状态。CLI / Scheduler 直接用例由目标 Application Service 按已解析政策创建根 Allocation；Web Chat 由 Conversational Task Control 在调用 Agent Orchestrator 前创建 Agent Root Allocation 并显式传入，Web Chat Adapter 不选择政策，Agent Orchestrator 也不反向调用 Application Services。
- Agent Orchestrator 只能在获授的 Agent Root Allocation 边界内提出下一职责动作及资源需求 Proposal；Conversational Task Control 机械校验后，从 Root Allocation 预留子项并与 Agent Invocation / Delegated Grant 一次绑定。Task Execution Agent 调用 Application Services 时随 Execution Envelope 传入该 Allocation；Application Service 不另建一份不受父账户约束的预算，Orchestrator 和 Agent 都不能自行创建权威子分配。
- 创建子任务前，共享执行基础设施按 Application Layer 所有者命令，从父 Allocation 原子预留时间、调用、Token、结果体积和成本额度。并行子任务获得互不重叠的 Allocation，不能各自看到完整父余额。
- 使用货币成本额度时，Resource Policy 必须在 Allocation / Execution Envelope 中冻结 exact Budget Conversion Rule / Revision；Shared Execution Infrastructure 只按该规则结算实际观察量，不同步查询 Telemetry Cost Valuation。后算估值差异只形成 Finding，不能改写 Resource Ledger。
- 执行边界报告实际消耗；结算后未使用额度原子返还父 Allocation。取消只释放尚未消费的额度。
- 每次重试创建新的 Attempt 和子 Allocation，并计入同一父账户；失败尝试的实际消耗不能回滚。
- Provider 超出估算额度时记录真实消耗并阻止后续分配；不能通过账本截断掩盖真实成本。
- 共享执行基础设施只执行预留和结算，不拥有 Resource Account，也不决定业务循环是否继续。直接用例由目标 Application Service 决定继续、停止或降级；Web Task 由 Conversational Task Control 依据 Orchestrator / Agent Proposal、权威结果和资源状态推进；具体能力所有者只决定自身 Attempt，Orchestrator 不推进权威 Task 状态。

### 6.2 X-RESOURCE-ALLOCATION-01

Resource Allocation 是 Application Layer 拥有的最小可恢复预算预留记录，不是独立预算服务。共享执行基础设施只提供以下幂等状态变换：

| 字段 | 约束 |
|---|---|
| Allocation ID / Revision | 稳定身份与乐观并发版本 |
| Parent Allocation ID | 根 Allocation 为空；子 Allocation 必须固定直接父项 |
| Allocation Key | 由 Owner Control Boundary、Owner Attempt、Dispatch Kind 和 Dispatch Attempt Key 组成；在父项内唯一 |
| Request Digest | 固定本次预留的规范请求；同 Key 不同 Digest 必须拒绝 |
| Reserved Limits | 调用、Token、时间、结果体积和成本等确切上限 |
| Policy / Conversion Rule Revisions | 冻结预算与换算规则，不引用后算 Telemetry Valuation |
| Dispatch Binding | 可空；绑定调用方权威 `PREPARED` Dispatch / Call Record 的稳定引用与 Digest |
| Usage Reports / Completeness | 追加已观察用量，并显式区分 `COMPLETE | PARTIAL | UNKNOWN` |
| State | `RESERVED → SETTLED | RELEASED`；终态不可逆 |

`ReserveChild` 必须在一个 Application-owned 事务中扣减父项可用额度并建立子项。重复提交相同 Parent / Allocation Key / Request Digest 返回同一 Allocation；Digest 不同返回 `ALLOCATION_KEY_CONFLICT`，不能再次扣减。

外部调用 Owner 先用稳定 Dispatch Attempt Key 预留，再在自己的 Repository 建立 `PREPARED` Record，并以 `BindDispatch` 把该 Record 绑定到 Allocation。两步之间崩溃时，恢复流程按同一 Allocation Key 查询：存在 `PREPARED` Record 就补做幂等绑定并继续；不存在则创建同一个 Record，或在确认尚未分派后释放未绑定预留。已经绑定的预留只有在 Dispatch Owner 提供确切 `CANCELLED_BEFORE_DISPATCH` 终态时才可释放；不能因超时或查不到响应而猜测未调用。

`ReportUsage` 只追加观察，`Settle` 以 Expected Revision 原子结算并返还可证明未使用的额度。Provider 结果或用量仍未知时，按 Allocation 创建时冻结的政策保持 `RESERVED`，或按完整预留上限结算；不得按零消费释放。新的物理重试使用新的 Dispatch Attempt Key 和 child Allocation；进程恢复同一次物理尝试则复用原 Key。

该契约只关闭“预留成功但本地 Dispatch 记录尚未提交”的恢复歧义，不引入跨模块事务、分布式锁、预算预测、财务对账或自动清理器。

## 7. X-CAPABILITY-RESULT-01

通用 Capability Execution Result 至少区分：

- 请求是否满足 Capability Contract 并实际开始。
- Strategy 是否完成、失败、取消、超时或预算耗尽。
- Provider 形状校验与领域 Contract 校验是否分别通过。
- 是否产生 Proposal、Assessment 或领域结果；其权威性质是什么。
- 实际 Contract、Strategy、Model Call、Tool 和资源政策引用。
- 用量、延迟、重试、截断和未完成范围。

“执行成功”不等于“Proposal 正确”“Candidate 准入”“Snapshot 发布”或“答案放行”。具体能力必须在领域结果中进一步区分。

### 7.1 X-RESULT-DELIVERY-ASSERTION-01

每个可能进入 Web 响应 Claim 的 Application Result Owner 必须提供只读 `ValidateResultDelivery`。它不是统一结果服务，也不取得领域 Result 所有权；该公共 Contract 只统一 Response Control 所需的最小交接形状。

请求固定 exact Result Reference / Revision / Digest、请求中的 Content Manifest（字段路径、正式引用、Gap 或 Limitation）、Caller / Request / Purpose / Classification、Task Revision（适用时）和 Expected Owner Revision。Result Owner 从自己的权威状态重建后返回不可变 Assertion：

- Assertion ID / Revision / Digest、Result Owner 与 exact Result Reference / Digest。
- 请求的 Content Manifest 及其逐项 `ALLOW | DENY`，以及拒绝原因；未列入 Manifest 的内容不获授权。
- 结果当前性所依赖的 Owner State / Permission / Session / Schema 等 exact Revision 与权威 Read Set。
- Caller / Request / Purpose / Classification、Validation Time 和 Contract Version。

Assertion 不改变 Result、不重新执行副作用，也不把 Application Outcome 变成软件世界 Fact。Response Control 只能把新取得的 Assertion 用于当前 Authorization / Dispatch；在同一 Application Store 事务中重读其中声明的 current revisions，任一 Revision 漂移即拒绝。历史 Assertion、缓存正文或同一幂等键不能绕过新一轮校验。

各 Result Owner 只实现自己的语义：Knowledge Use 还必须重读 exact Formal References、Session / Use Epoch、Gap 和 Limitation；Knowledge Update 必须解析最新权威 Publication Outcome；Management 必须排除 Secret 并绑定对象 Definition / Control Revision。公共 Contract 不规定这些领域算法。

## 8. 正确执行方向

```mermaid
sequenceDiagram
    participant A as Application Services
    participant O as Core Capability Owner
    participant S as Owner Strategy Executor
    participant G as Model Gateway

    A->>A: Resolve PRODUCTION activation or EVALUATION_ONLY grant; freeze Catalog/Envelope
    A->>O: Domain request + Strategy Ref + Envelope
    O->>O: Validate Capability Contract and authority
    O->>S: Execute owned Strategy
    opt Strategy needs a model
        S->>G: Restricted ModelExecutionContext
        G-->>S: Normalized untrusted result
    end
    S-->>O: Proposal/Assessment/domain result
    O->>O: Deterministic contract and post-call model eligibility validation
    O-->>A: Capability Execution Result
```

如果 Core Capability 需要新的外部来源信息，它返回 Source Information Need；Application Services 决定是否协调 Source Integration 后再次调用。Core 不反向调用 Application Services，也不让 Model Gateway 直接访问其他业务模块。

Core 内部一个能力调用另一个能力时，只能沿概要架构允许的依赖方向，并使用上层已经冻结的 Catalog/Envelope；不能借 Capability Registry 绕过静态模块依赖。

## 9. 通用失败语义

| 类别 | 处理 |
|---|---|
| CONTRACT_MISMATCH | 不执行；Strategy 与 Contract 不兼容 |
| STRATEGY_NOT_ALLOWED | 不执行；传入 Strategy 不在冻结 Catalog 中 |
| INPUT_INVALID | 不执行模型或 Tool；返回领域输入错误 |
| RESOURCE_RESERVATION_FAILED | 不开始子执行；由控制者决定停止或缩小范围 |
| ALLOCATION_KEY_CONFLICT | 同一 Allocation Key 对应不同请求；失败关闭，不重复扣减 |
| ALLOCATION_STATE_CONFLICT | Expected Revision 或状态不匹配；重读原 Allocation 后恢复 |
| BUDGET_EXHAUSTED | 受控停止并暴露未完成范围 |
| TOOL_DENIED | 拒绝 Tool Request；只能按 Capability Policy 做有界修正 |
| OUTPUT_SHAPE_INVALID | 不进入领域处理 |
| OUTPUT_CONTRACT_INVALID | 拒绝 Proposal/Assessment；生成方不能自证 |
| MODEL_FINGERPRINT_NOT_EVALUATED | 不封存领域结果；返回绑定 Qualification Proof 的失效信号，由签发 Owner 按其 Contract 处理资格失效 |
| MODEL_EXECUTION_NOT_ELIGIBLE | Authorized Input Manifest、Provider Request 或 Isolation Receipt 缺失、失配、过期或发生隔离违约；不封存 Proposal、Candidate、Assessment、Application Result、Answer 或生产缓存 |
| CANCELLED | 停止新子调用并结算已消费资源 |

重试由具体 Failure Contract 规定。随机模型的重新采样创建新 Attempt，不能覆盖前次执行或伪装成幂等返回。

## 10. 可观测性与数据边界

- 每个执行记录 Envelope、Contract/Strategy、Attempt、资源预留/结算和结果分类。
- 事件引用业务对象，不复制 Artifact Payload、Evidence Quote、凭据或完整模型上下文。
- Telemetry 和资源账本不是 Artifact、Evidence 或正式知识。
- 共享 Runtime 不读取业务模块私有 Repository，也不根据遥测反向改变正式知识或 Strategy 激活。

## 11. 拟议不变量

1. Capability 领域契约和 Strategy 归能力提供模块所有，通用 Runtime 不集中业务逻辑。
2. Application Services 在进入 Core 前解析 PRODUCTION Activation 或 exact EVALUATION_ONLY Grant 并冻结 Catalog/Envelope；Core 不反向读取 Application 状态。
3. Strategy 可替换，Capability Contract、权限和正式知识语义不能随模型漂移。
4. Provider 输出形状通过不等于领域 Contract 通过。
5. Resource Policy、Account 和 Allocation 由 Application Layer 逻辑拥有；共享基础设施只执行原子预留和结算。Allocation Key 幂等、Dispatch Binding 可恢复，子执行权限和资源只能是父执行的子集。
6. Model Gateway 是唯一模型访问入口，但不是 Strategy、知识或审核权威。
7. Capability Registry 不能成为绕过模块静态依赖的服务定位器。
8. 回退只能选择已通过相同 Capability Contract 门禁的 Strategy，并沿同一业务路径执行。
9. 每个模型调用的 actual identity、Authorized Input Manifest / Provider Request Digest 和 Isolation Receipt 必须在领域结果封存前通过冻结 Catalog 的 post-call Eligibility；未经评测的滚动版本或隔离闭包不成立的调用不能产出生产对象。

## 12. 后续依赖与验证

- ModelExecutionContext、Provider 隔离和模型指纹：DD-AI-MODEL-GATEWAY。
- Evaluation Result、Strategy Activation 与模型升级/退化：DD-MGT-CAPABILITY-EVALUATION。
- 各领域输入输出、重试、指标和门禁：所属主题详细设计。

当前无需 Design Validation Demo。Runtime 实现需要 `CC-*` Conformance Case 验证资源原子预留、父子权限单调收窄、Model Call 输入/隔离 Eligibility 失败时所有生产 Sink 均拒绝，以及 Core 不反向依赖 Application；具体 Strategy 使用 `CE-*` Capability Evaluation，不与 Demo 混用。
