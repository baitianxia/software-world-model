# Model Gateway 详细设计

| 元数据 | 值 |
|---|---|
| Document ID | DD-AI-MODEL-GATEWAY |
| Version | 0.1.0 |
| Status | Accepted |
| Document Steward | AI Infrastructure / Model Gateway |
| Architecture Baseline | SWM-ARCH@1.2 |
| Depends On | DD-X-CAPABILITY-EXECUTION@0.1.0 |
| Owns Contracts | AI-MODEL-CONTEXT-01、AI-AUTHORIZED-INPUT-MANIFEST-01、AI-ISOLATION-RECEIPT-01、AI-MODEL-GATEWAY-01、AI-PROVIDER-ADAPTER-01 |
| Supersedes | `Software_World_Model_MVP_Detailed_Design.md` 中 DD-00B 的模型访问部分 |
| Rationale ADR | AD-019、AD-020、AD-021、AD-059、AD-060、AD-087、AD-088、AD-094、AD-100、AD-101、AD-110、AD-115、AD-117、AD-131、AD-132 |
| Design Validation | None |
| Conformance Cases | None |
| Capability Evaluation | None |

> 概要架构约束直接生效；本文新增的 Provider、隔离、指纹和失败语义在状态进入 `Accepted` 前均为拟议设计。

## 1. 目的与范围

Model Gateway 是平台唯一模型访问边界。它把业务模块构造的受限 ModelExecutionContext 转换为 Provider 调用，执行隔离、输入输出、用量和模型身份控制，并返回不可信的规范化响应。

Gateway 不拥有 Capability Strategy、领域 Prompt 意图、Knowledge Candidate、评测晋升、Snapshot 发布或答案放行。

## 2. AI-MODEL-CONTEXT-01

每次 Model Call 固定：

- Model Call ID、Execution Envelope 和执行阶段，例如 Proposal、Verification、Sufficiency 或 Answer Review。
- Capability Contract、Strategy 和调用它的业务模块。
- `AI-AUTHORIZED-INPUT-MANIFEST-01` Reference / Digest，而不是一段调用方自报的输入摘要。
- Prompt Program / Template Reference、Rendering Contract Version、渲染后消息序列 Digest 和 Adapter Envelope Version。
- Provider Runtime Access Mode，以及可以出现在模型输出中的 Platform Proposal Vocabulary；二者不能用同一个 `tools` 字段表达。
- 输出形状版本、剩余 Allocation、输入和输出体积限制、停止条件及数据分类。
- 请求的 Model Reference、Provider Configuration 和所需可回放性/隔离等级。

Candidate 生成、Knowledge Verification、答案生成和 Answer Review 各自构造独立 Context。它们可以使用同一基础模型，但不能共享生成方的可变工作状态作为审核权威。

### 2.1 AI-AUTHORIZED-INPUT-MANIFEST-01

Authorized Input Manifest 是某次 Model Call 唯一允许发送给 Provider 的应用语义输入清单。它至少固定：

- Manifest ID / Version / Digest、Capability / Strategy、Execution Stage 和调用模块。
- 按渲染顺序排列的 Prompt Instruction、用户或应用消息、结构化字段和内容片段；每项固定内容 Digest、Schema、数据分类、用途和不可变 Authority / Artifact / Application Reference。
- 对内容执行的裁剪、脱敏、Range 选择、Derived 表示和截断规则及其版本；摘要不能代替原始输入清单证明授权范围。
- 明确的空输入、未提供项和已拒绝项，防止 Adapter 用工作区、历史会话或 Provider 默认检索补齐缺失内容。
- Platform Proposal Vocabulary Reference / Digest。它只规定模型可以输出哪些受控提议形状，不授予 Provider 任何外部读取或执行能力。

Gateway 只能从 Manifest 与版本化 Prompt Rendering Contract 构造 Provider Request。Provider Request Digest 必须覆盖 Manifest Digest、Prompt Program / Template、渲染后完整消息序列、Adapter Envelope、结构化输出形状、Runtime Access Mode、Model / Provider / Adapter Configuration Reference / Fingerprint 和资源限制；API Key 等传输 Secret 值既不进入 Digest 也不进入日志。Telemetry 中的输入摘要只用于检索和观测，不能作为“模型只看到这些内容”的证明。

Secret、Connector Credential、未授权 Artifact、调用进程环境变量、工作目录、宿主文件路径和其他非 Manifest 内容不得成为 Provider Request 的隐式组成部分。Provider 自身无法披露的训练数据不属于平台运行时输入证明范围；模型记忆或常识也不能替代正式知识引用、Evidence 或 Capability 的权威输入。

### 2.2 Provider 运行时上下文隔离

每个 ModelExecutionContext 必须解析为一个机械可执行的 Provider Runtime Isolation Policy。它包含两个正交字段，不能把“允许输出 Proposal”误写成“允许 Provider 执行 Tool”：

- Runtime Access Mode = `NO_EXTERNAL_ACCESS`：Provider 调用期间没有 shell、文件系统、Web、MCP、Connector、Agent Runtime、Provider 托管检索、工作区附件或其他外部读取/执行通道。
- Runtime Access Mode = `DECLARED_PROVIDER_TOOL_SET`：只有 Capability 明确需要且 Adapter 能在执行前限制为精确 Provider Tool Set 时才允许；它不能用于需要证明“只依赖冻结输入”的 Requirement、Build / Tool Proposal、Artifact Processing、Candidate、Knowledge Verification、Semantic View、Sufficiency、Answer 或 Answer Review Capability。当前软件知识主路径中的这些认知调用均使用 `NO_EXTERNAL_ACCESS`。
- Platform Proposal Mode = `NONE | DECLARED_PLATFORM_PROPOSAL_ONLY`：后者允许模型输出 Tool / Source Operation Proposal 的结构化数据，但 Provider 不执行该 Proposal；平台在本次调用结束后重新授权和执行。它可以与 `NO_EXTERNAL_ACCESS` 同时成立。

有状态 Provider 必须为每个 ModelExecutionContext 创建新的物理会话，或使用能够证明无历史状态的无会话调用。不同 Context 不得复用 Provider Conversation、Thread、Memory、File Attachment、Retrieval Index 或此前 Tool Trace。Provider 固有安全策略可以存在，但其版本或能力声明必须进入 Adapter Conformance；它不能注入未在 Manifest 中声明的应用数据或来源材料。

## 3. AI-MODEL-GATEWAY-01

Gateway 负责：

1. 只根据显式 Provider Configuration 和 Model Reference 选择 Adapter，不按模型输出动态路由。
2. 在调用前校验 Adapter 的运行时访问隔离、隐藏上下文禁用、数据策略、结构化输出和模型身份能力，并签发 `AI-ISOLATION-RECEIPT-01`。
3. 只从 Authorized Input Manifest 执行输入裁剪、敏感信息门禁、Prompt 渲染、Provider 请求转换和超时控制。
4. 在 `DECLARED_PROVIDER_TOOL_SET` 模式校验 Provider Tool Request 是否位于授权集合；在 `NO_EXTERNAL_ACCESS` 模式只解析 Platform Proposal 输出形状，不把它注册为 Provider Tool，也不直接执行领域 Tool。
5. 记录 Manifest / Prompt / Provider Request Digest、请求模型引用、实际模型指纹、Isolation Receipt、用量、延迟、终止原因、重试和原始响应引用。
6. 将 Provider 响应转换为稳定外壳，并分别报告传输/形状状态。

Gateway 不负责：

- 判断模型输出是否满足领域 Capability Contract。
- 分配 Entity、Fact、Inference、Context 或 Snapshot 身份。
- 直接访问 Data Source、Knowledge Repository 或 Application 状态。
- 扩大 Scope、Tool、数据分类和资源 Allocation。
- 激活、回退或晋升 Strategy。

### 3.1 Model Call Record 与分派边界

每次 Provider 尝试就是一个独立 Model Call Record；重试创建新的 Model Call ID，不再叠加第二套 Attempt 对象。最小状态为：

`PREPARED → DISPATCHED → COMPLETED | FAILED | OUTCOME_UNKNOWN`

`PREPARED → CANCELLED_BEFORE_DISPATCH`

- 每个物理 Provider 尝试先分配稳定 Model Call ID / Dispatch Attempt Key，并按 `X-RESOURCE-ALLOCATION-01` 从父项幂等取得唯一 child Allocation；随后建立本地 `PREPARED` Call Record 并绑定 Allocation，才允许越过 dispatch fence。崩溃恢复复用同一 Key，不得再次扣减或创建第二个物理尝试。失败和迟到尝试的真实消耗同样结算。
- `PREPARED → DISPATCHED` 固定 Authorized Input Manifest、Prompt / Provider Request Digest、Provider / Adapter、Runtime Isolation Policy、Isolation Receipt、actual child Allocation 和可选 Provider Request ID。取消先赢时不发送；分派先赢时不能声称未调用。
- 只有 `COMPLETED` 产生可供 Capability Owner 校验的 Model Response。传输中断且 Provider 是否完成不可证明时进入 `OUTCOME_UNKNOWN`，不得伪造成 FAILED / 未计费。
- Provider 后续能按同一 Request ID 解析时，`OUTCOME_UNKNOWN` 可追加解析为 COMPLETED / FAILED；否则保持未决。迟到 Response 仍绑定原 Call，是否接受由上游 Attempt 当前性和 post-call model eligibility 决定，不能覆盖新 Attempt。
- 每个终态或未决记录都带 `Usage Completeness = COMPLETE | PARTIAL | UNKNOWN`、原始 Usage / Charge Observation Reference 和已知计量；UNKNOWN 不按 0 计费或伪造完整预算结算。

Model Call Record 只解决分派、结果和用量的真实性，不提供业务副作用 exactly-once，也不引入通用队列或远程任务系统。

## 4. AI-PROVIDER-ADAPTER-01

Provider Adapter 必须声明并通过 Conformance Case 证明：

- 能否在执行前机械关闭 shell、文件、Web、MCP、Agent Runtime、Provider 托管检索和全部外部 Tool，或严格限制到明确声明的 Provider Tool Set。
- 能否禁用或物理隔离 Provider Conversation、Memory、File Attachment、Retrieval Index、Workspace 和其他隐藏运行时上下文。
- Platform Proposal Vocabulary 只作为输出形状时，Provider 不会把它解释为可执行 Tool 注册。
- 结构化输出支持程度及失败模式。
- 模型版本是否可固定，以及能否返回每次调用的实际 Model Fingerprint。
- Token、上下文、重试、流式响应和终止原因的计量语义。
- 数据保留、区域和分类限制。

能力声明是版本化事实。Adapter 或 Provider 行为变化后，原 Conformance Result 标记 `Stale`，不能继续证明兼容。

## 5. Tool 隔离与执行

- `AI-ISOLATION-RECEIPT-01` 在分派前形成，固定 Authorized Input Manifest / Provider Request Digest、Provider / Adapter / Configuration、Runtime Isolation Policy、适用 Conformance Result / Revision、Provider Session Policy 和有效性检查结果。它只证明本次请求满足已验证隔离配置，不证明模型输出正确。
- Capability 要求 `NO_EXTERNAL_ACCESS` 而 Adapter 不能在调用前机械保证时，Gateway 返回 `ISOLATION_UNSUPPORTED`，不签发 Receipt、不越过分派边界；不得先执行再从事后日志推断没有越权。
- 空 Provider Tool 清单只有在 Provider 的全部内置访问能力也被关闭时才等价于 `NO_EXTERNAL_ACCESS`；提示词禁止、只读工作目录、临时空目录和事后 Tool Event 检查都不能签发该 Receipt。
- Source Investigation 等有界循环中的“Tool”是模型输出的 Platform Proposal。每一步模型调用仍可以使用 `NO_EXTERNAL_ACCESS`，由 Application Services 在调用结束后授权并经 Source Integration 执行，结果作为下一次调用的新 Authorized Input Manifest 项进入模型。
- `DECLARED_PROVIDER_TOOL_SET` 模式下，模型只返回符合 Provider Tool Contract 的 Tool Request；Gateway 做形状和授权前置检查后返回调用 Strategy。`NO_EXTERNAL_ACCESS` 模式下，Platform Proposal 只是普通结构化响应，由 Capability Owner 完整校验。
- Strategy 只能沿所属模块允许的应用/依赖边界执行 Tool；Gateway 不反向调用 Source Integration、Knowledge Engine 或 Application Services。
- Tool 失败、空结果、分页未完成或截断必须原样反馈，不能解释为“没有相关信息”。
- 副作用 Tool 需要独立 Action Capability、授权和确认边界，不得混入 Source Integration 的读取 Tool。

## 6. 模型身份与滚动别名

每次调用同时记录：

- Requested Model Reference：Strategy 配置请求的名称或版本。
- Resolved Model Fingerprint：Provider 能证明的实际模型 Revision。
- Provider Adapter / Configuration Version。
- Replay Classification：`PINNED`、`OBSERVED_MUTABLE` 或 `UNRESOLVED_MUTABLE`。

规则如下：

1. Gateway 不能把滚动别名记录成固定模型版本。
2. Capability Contract 要求精确可回放而 Adapter 无法在调用前满足时，调用失败关闭。
3. 对 `OBSERVED_MUTABLE`，Gateway 只返回每次实际指纹和与请求引用的关系，不判断该指纹是否被 Evaluation 覆盖，也不改变 Activation 状态。
4. 对 `UNRESOLVED_MUTABLE`，Gateway 按 ModelExecutionContext 的 Required Replay Level 决定拒绝调用或返回明确分类；该分类能否被领域 Strategy 接受由上游已经解析的执行政策决定，Gateway 不读取 Evaluation / Activation Repository。
5. 正式知识准入、Knowledge Verification 和 Answer Review 不因为“使用了更新模型”而降低权威输入重建和独立门禁。

## 7. Provider 输出与领域校验

Gateway 返回的稳定外壳至少区分：

- Provider 请求是否被接受。
- 调用是否完成、超时、取消、限流或被内容/数据策略拒绝。
- 输出是否完整、截断，是否包含 Provider Tool Request 或 Platform Proposal。
- 结构化形状是否可解析。
- 请求与实际模型身份以及 Replay Classification。
- 用量和原始响应审计引用。
- Model Call State、Provider Request ID（可得时）和 Usage Completeness。

即使形状有效，输出仍是不可信 Model Response。调用 Strategy 必须重建受保护字段并执行 Capability Contract 校验，不能信任模型自报 Scope、ID、Evidence Locator、权限、完成度或控制状态。

## 8. 失败与重试

| 类别 | 默认处理 |
|---|---|
| PROVIDER_NOT_CONFIGURED | 不调用；返回配置缺失 |
| PROVIDER_CAPABILITY_MISMATCH | 不调用；Adapter 不满足 Context 要求 |
| AUTHORIZED_INPUT_INVALID | Manifest、Prompt 渲染或 Provider Request Digest 无法闭合；不发送输入 |
| ISOLATION_UNSUPPORTED | 不调用；不允许事后审计替代 |
| ISOLATION_CONFORMANCE_STALE | 不调用；Adapter / Provider 行为变化后原证明不可复用 |
| HIDDEN_CONTEXT_UNCONTROLLED | 无法禁用或隔离 Provider 会话、记忆、附件、检索或工作区；不调用 |
| ISOLATION_BREACH | 分派后发现 Provider 或 Adapter 违反已签发隔离配置；隔离原始响应并使领域调用失败，结果不得进入 Proposal、Candidate、Assessment、Application Result、Answer 或生产缓存 |
| DATA_POLICY_DENIED | 不发送输入；失败关闭 |
| MODEL_REVISION_UNRESOLVED | Required Replay Level 要求实际指纹时拒绝；否则返回明确 Replay Classification，不判断评测覆盖 |
| PROVIDER_UNAVAILABLE / RATE_LIMITED | 仅在 Strategy Policy、剩余 Allocation 和幂等边界内重试 |
| TIMEOUT / CANCELLED | dispatch 前进入 CANCELLED_BEFORE_DISPATCH；dispatch 后只有 Provider Outcome 可证明时记 FAILED，否则进入 OUTCOME_UNKNOWN；始终记录已知用量 |
| PROVIDER_OUTCOME_UNKNOWN | 保留原 Call / Request ID 与 UNKNOWN 用量；迟到结果只解析原 Call，不覆盖新 Attempt |
| OUTPUT_SHAPE_INVALID | 不进入领域校验；可在明确预算内请求修正 |
| TOOL_REQUEST_DENIED | 拒绝请求；不扩大 Tool 集 |

每次重试创建新 Model Call ID 并消耗新的 child Allocation。OUTCOME_UNKNOWN 后是否再尝试由 Strategy 在剩余预算内明确决定；新 Call 不改变原 Call 的结果或用量。Gateway 不在不同模型间自行回退；只有调用方携带新的、已在上游解析完成的 Strategy / ModelExecutionContext 才能发起另一模型调用。

## 9. 可观测性与敏感信息

- 记录关联、Authorized Input Manifest / Prompt / Provider Request Digest、Context / Strategy / Adapter 版本、Isolation Receipt、模型身份、Tool Proposal、原始 Provider Usage / Charge Observation、延迟、重试和结果分类。统一估算成本由横切 Telemetry 按 exact Pricing Revision 形成；Gateway 不建立第二套平台成本真相。
- 原始 Prompt/Response 按数据分类和保留政策存储，Telemetry 默认只保存引用和必要摘要。
- Secret、Connector Credential 和未授权 Artifact 内容不得进入模型输入或日志。
- Model Call 记录不是 Artifact、Evidence 或正式知识。

## 10. 拟议不变量

1. 所有模型调用经过 Model Gateway；Gateway 不拥有领域 Strategy 或正式决定。
2. ModelExecutionContext 的输入、运行时访问、Proposal Vocabulary、数据和资源权限不能在调用中扩大；Provider Request 只能由 Authorized Input Manifest 构造。
3. 要求无外部访问时必须在执行前机械保证，并签发绑定本次请求的 Isolation Receipt；Provider 隐藏会话或检索无法关闭时失败关闭。
4. 请求模型引用和实际模型指纹分别记录；滚动别名不能伪装成固定版本。
5. Provider 结构化形状通过不等于 Capability Contract 通过。
6. Gateway 不执行领域 Tool，不反向调用业务模块。
7. Provider/Adapter 能力变化必须产生版本或能力变化事件；Gateway 只使自身相关 Conformance 依据过期，Evaluation / Activation 所有者据事件独立判断其状态。
8. 生成与审核可以共享基础模型，但必须隔离执行上下文和权威输入。
9. 每次 Provider 分派具有唯一 Model Call / child Allocation；结果未知和用量未知必须显式保留，迟到响应不能覆盖新 Attempt。
10. Isolation Receipt 缺失、过期或与实际请求不匹配时，模型响应不具有任何生产领域输出资格；事后拒绝不能替代执行前隔离。

## 11. 后续验证

每个 Provider Adapter 在可用前建立 `CC-*`，至少验证：未授权文件名 / 路径 / 内容不可经任何运行时通道读取；Provider 会话、记忆、附件和托管检索被关闭或物理隔离；Platform Proposal 不触发 Provider Tool；Authorized Input Manifest 与实际 Provider Request 一致；隔离不成立时不分派；以及数据门禁、形状失败、模型指纹和用量计量。选择模型或 Prompt 的质量比较属于 `CE-*`，不是 Gateway Conformance，也不是设计 Demo。

Conformance 可以放置未进入 Manifest 的诱饵文件 / 路径并检查隔离配置和实际访问通道，但不能仅以“输出是否碰巧包含诱饵内容”作为 Oracle：模型可能猜测或从训练数据知道相同文本。权威判据是调用前访问能力确实关闭、Provider Request 与 Manifest 闭合、运行中不存在外部读取通道；领域输出仍须通过正式引用和 Capability Contract 门禁。

只有当 Provider 的真实行为暴露出会改变 Gateway Contract 的实质不确定性、且 Conformance 无法在现有契约下判定时，才建立 `DVR-*`。
