# Platform Telemetry 与 Cost Governance 详细设计

| 元数据 | 值 |
|---|---|
| Document ID | DD-X-TELEMETRY-COST |
| Version | 0.1.0 |
| Status | Accepted |
| Document Steward | Cross-cutting Telemetry Infrastructure；Resource Policy 仍由 Application Layer 拥有 |
| Architecture Baseline | SWM-ARCH@1.2 |
| Depends On | DD-X-CAPABILITY-EXECUTION@0.1.0、DD-AI-MODEL-GATEWAY@0.1.0 |
| Owns Contracts | X-TELEMETRY-CONTEXT-01、X-TELEMETRY-EVENT-01、X-USAGE-REPORT-01、X-COST-VALUATION-01、X-TELEMETRY-EXPORT-01 |
| Design Coverage | 端到端关联、中立运行事件、用量记录、非控制性成本估算、外部观测出口与敏感信息边界 |
| Supersedes | None |
| Rationale ADR | AD-087、AD-088、AD-100、AD-115 至 AD-117、AD-124、AD-125、AD-130 |
| Design Validation | None |
| Conformance Cases | None |
| Capability Evaluation | None；异常检测或成本预测使用模型时另建 Capability |

> Telemetry 只观察和关联平台运行。它不拥有业务状态、预算政策、正式知识、Capability Activation、Snapshot Publication、Sufficiency 或响应放行决定。

## 1. 目的与范围

本文使一次入口请求能够关联到 Agent、Application Use Case、Capability、Model、Tool / Connector、Knowledge Update、Publication 和 Answer Review，并如实记录实际用量与估算成本。

本文保证：

- 各模块使用同一中立关联语义，但仍拥有自己的权威 Result。
- 预算预留 / 结算、真实用量和成本估值是三个不同概念，不互相冒充。
- Telemetry 丢失或延迟不会改写业务 Outcome；关键事件由相应 Authority Owner 的本地 Outbox / Emission State 补发。
- 观测设施不能反向调用业务模块或作出领域决定。
- 事件不复制 Artifact、Evidence、正式命题、模型正文、Credential 或 Agent 私有推理。

本文不定义：

- 日志 / 指标 / Trace 产品选型、仪表盘布局、告警值班制度或企业账单流程。
- Resource Account、Allocation、配额、速率和并发政策；它们由 DD-X-CAPABILITY-EXECUTION 与 Application Layer 拥有。
- Model Call 原始 Prompt / Response 存储；它由 Model Gateway 的数据政策控制。
- 面向目标软件的日志、Trace 或 Metric 接入；那些是 Data Source，经正常 Artifact / Knowledge 路径处理。
- 自动调优、自动停用 Strategy、自动知识修正或自训练。

## 2. 最小充分实现与扩展边界

最简单合规 Strategy 是模块化单体内的：

- 复用 Execution Envelope 传播 Correlation / Causation / Resource References。
- 权威 Result 附带最小 Telemetry Outbox Event，后台幂等导出为结构化日志、指标或 Trace。
- Model Gateway、Tool / Connector 和共享资源结算直接上报已有 Result 中的用量。
- 使用 exact、版本化 Pricing Input Revision 计算估算成本；没有价格或输入不可验证时明确 `UNVALUED`，不填零。

默认最简单合规实现不建设消息总线、独立时序库、数据湖、企业分摊平台、Provider Invoice 对账或 AI 异常检测。它们只在出现下列条件时增加：

| 触发条件 | 可增加 | 稳定边界 |
|---|---|---|
| 单体导出吞吐或可靠性不足 | 外部 Event Bus / Collector | Event ID、Schema、幂等和单向流 |
| 需要财务级实际账单核对 | Invoice Reconciliation Adapter | Usage 与 Valuation 分离、历史不改写 |
| 需要跨团队 / Scope 成本分摊 | Allocation / Tagging Policy 扩展 | Application 拥有 Resource Policy，Telemetry 不决定预算 |
| 数据量需要采样 / 分层保留 | Sampling / Tiering Strategy | 必需审计引用不被普通指标采样替代 |
| 需要异常检测或预测 | 独立只读分析 Capability | 不自动改变业务、知识或 Activation |

## 3. 所有权

| 对象 / 决定 | Owner | Telemetry 的作用 |
|---|---|---|
| 业务 Outcome、Knowledge / Publication / Review Decision | 各业务模块 | 只保存稳定引用、Digest 和事件类型 |
| Execution Envelope、Resource Account / Allocation / Settlement | Application Layer / Shared Execution Contract | 订阅预留、结算和限额事件，不另建预算真相 |
| Model Call / Provider Usage / Provider Charge Observation | Model Gateway | 接收不可变原始观察引用；不把 Gateway 局部估值当作平台成本真相 |
| Tool / Connector Usage | 执行 Tool / Provider 的模块 | 接收规范用量，不解释业务内容 |
| Telemetry Event、规范 Usage Report、非控制性 Cost Valuation、关联索引、Exporter Checkpoint | Telemetry Infrastructure | 自身权威，但不具有业务权威 |
| Pricing Input Revision | 部署配置 / 外部 Cost Policy Owner；当前不是平台权威对象 | Telemetry 校验并按 exact Revision 估值，不注册、修改、抓取或猜测价格 |
| 外部 Observability / Cost Backend | 部署基础设施 | 消费导出，不成为平台业务依赖 |

预算是否允许继续：直接用例由目标 Application Service 决定，Web Task 由 Conversational Task Control 依据 Orchestrator / Agent Proposal、权威结果和 Resource Account 状态决定。Agent Orchestrator 不拥有预算状态或子分配。Telemetry Dashboard、告警、成本估值或 Exporter 不能停止运行、回滚发布、激活 Strategy 或放行答案。

## 4. X-TELEMETRY-CONTEXT-01

Telemetry Context 直接派生自 X-EXECUTION-ENVELOPE-01，至少传播：

- Correlation Reference、Causation / Parent Reference。
- Actor / Initiator、Task / Run / Attempt、入口 Channel。
- 可选 KnowledgeScope、Snapshot / Schema、Application Use Case。
- Capability / Strategy、Model Call、Tool / Connector、Agent Invocation、Review Reference。
- Resource Account / Policy / Allocation Reference。
- Data Classification、Telemetry Policy / Sampling Policy Revision。

生产者不能生成新的业务 Scope、Snapshot 或 Capability 身份来补齐事件；字段不适用时明确缺省。缺失可选维度不阻止业务运行，但记录 Telemetry Completeness Finding。影响授权、预算或领域正确性的字段仍由原业务 Contract 自身验证，不能依赖 Telemetry 补救。

Correlation 表示同一外部目标，Causation 表示直接触发关系。Telemetry 可以构建运行关联图，但该图不是业务依赖图、Artifact Lineage、Inference Argument 或 Snapshot Dependency。

## 5. X-TELEMETRY-EVENT-01

### 5.1 Event Envelope

每个不可变 Event 至少固定：

- Event ID、Event Type / Schema Version、Producer / Producer Version。
- Telemetry Context、Authority Object Reference / Revision / Digest。
- Occurred At、Recorded At、Outcome Category 和 Attempt / Retry 序号。
- 可选 Usage Report / Cost Valuation / Error Classification Reference。
- Data Classification、Payload Field Set / Digest 和 Idempotency Key。

Event Payload 只包含中立枚举、数量、时长、大小、状态引用和受控低敏标签。错误消息先规范化；Stack Trace、SQL、Prompt、Source Locator、用户输入和模型响应不能默认进入 Payload。

### 5.2 Event 类别

| 类别 | 示例 | 可靠性语义 |
|---|---|---|
| Authority Lifecycle | Use Case、Materialization、Admission、Publication、Review 的开始 / 终态引用 | 由权威 Record / Outbox 产生，可对账；Event 不决定 Outcome |
| Execution / Usage | Model、Tool、Connector、Agent、Projection、Query 的执行结果和用量 | 至少一次导出，按 Event ID 幂等 |
| Resource | Allocation 预留、结算、配额 / 速率 / 并发触发 | 只引用 Resource Ledger 决定 |
| Operational Signal | 延迟、队列、缓存、Exporter 健康、聚合指标 | 可以采样或丢失，不作为审计证明 |

普通 Metric 或日志不能替代 Authority Lifecycle Record。反过来，Telemetry Backend 故障也不能把已提交 Publication 或 Review Authorization改判失败。

`AUDIT_REQUIRED` 不是 Producer 自选标签。以下权威终态 / Decision / Result 及其最低用量记录构成不可降级的最小集合：Artifact Materialization / Lineage、Evidence Materialization、Knowledge Admission、Snapshot Publication、Application Side-effect Call、Capability Evaluation / Activation、Answer Review / Final Authorization / Delivery、Model / Tool / Connector leaf execution，以及 Resource Allocation / Settlement。各 Owner 可以在自己的 Contract 中增加类型，不能把该集合降为可采样 Event；删除类型必须先修订概要架构。进行中进度和普通只读查询只有在 Owner Contract 明确要求时才属于 AUDIT_REQUIRED。

### 5.3 产生与恢复

- `AUDIT_REQUIRED` Authority Lifecycle Event 由相应 Authority Owner 在拥有业务状态的同一本地事务写入 owner-local Outbox / Emission Marker；Authority Record 与该 Marker 必须一起提交。
- 若 Owner 的存储 Contract 确实不能共事务，Authority Record 必须自带可枚举、单调的 Telemetry Emission State；只有该 Owner 自己的 Reconciler 可以读取自身 Repository 并补发标准 Event。Telemetry Infrastructure 不扫描任何业务私有 Repository，也不反向调用业务模块。
- Operational Signal 可以 best-effort 产生；它的缺失不使用跨仓库补扫修复，也不能承担审计证明。
- 消费者至少一次投递并按 Event ID 幂等。Event 固定 Authority Object Reference / Revision，不能从进程日志猜测 Outcome。
- Export 成功 / 失败只更新 Telemetry Delivery Record / Checkpoint，不修改生产者业务 Record。
- Producer 重试同一权威状态返回同一 Event ID；新的业务 Revision 或 Attempt 产生新 Event。
- 时钟用于时延分析，不用于判断业务先后；业务顺序依赖 Revision、Attempt 和 Causation。

## 6. X-USAGE-REPORT-01

Usage Report 记录执行边界实际观察到的消耗，不是预算额度。至少固定：

- Usage Report ID / Revision / Supersedes、稳定 Meter Key、Producer Result / Attempt、Provider / Tool / Connector / Model Reference。
- exact Execution Envelope Reference / Digest 与冻结的 Attribution Context，包括适用的 Task / Run、KnowledgeScope、Application Use Case、Capability / Strategy、Model Call、Tool / Connector、Agent Invocation 和 Resource Account / Allocation Reference。
- 规范 Unit Set，例如 input / output / cached token、model call、tool call、byte read / written、compute duration、storage byte-time。
- 每项 Quantity、Unit、Measurement Source 和 Measurement Quality。
- `PROVIDER_REPORTED | PLATFORM_MEASURED | ESTIMATED`，以及 `COMPLETE | INCOMPLETE | UNATTRIBUTED` Attribution Completeness。
- Resource Allocation / Settlement Reference、时间区间、Classification 和 Digest。

规则：

- Meter Key 只由分派前已经稳定的 leaf execution identity（Model Call、Tool Invocation、Connector Operation 或其他 Producer Attempt）、规范 Meter / Unit 和 Producer 预分配的 stable segment 构成。Provider Receipt、Measurement Source 和观察时间区间属于 Usage Revision 的来源 / 去重字段，不得改变 Meter Key；若 Provider Request ID 从首个 Revision 起就是 leaf identity，可以持续作为其中一部分。同一 Meter Key 的后续更可靠观察创建新 Revision 并显式 Supersede 旧 Revision，不创建可同时累计的平行“实际值”。
- 每个 Event Type 的条件必填归因来自其 Contract：Model 用量需要 Capability / Strategy / Model Call，Tool / Connector 用量需要相应调用引用，Agent 用量需要 Agent Invocation；字段不适用时明确缺省，应该存在却缺失时进入 INCOMPLETE / UNATTRIBUTED bucket，不能从 Correlation 文本猜测 Join。
- Provider 未返回用量时可以保存 ESTIMATED，但不能标成实际值。
- 后续取得 Provider Report 或更可靠平台计量时创建同一 Meter Key 的新 Usage Revision；不原地改写原 Report。
- 重试、失败、取消和超时已经消耗的资源照实记录；业务失败不把成本回滚为零。
- Allocation 是允许上限，Usage 是观察量；两者不一致产生 Finding，由 Resource Owner 决定后续动作。
- 不同 Unit 不在没有明确换算 Contract 时相加。

## 7. X-COST-VALUATION-01

### 7.1 Pricing Input Revision

当前最小实现不建立平台内 Pricing Catalog 身份、注册命令、Repository 或 Management 生命周期。部署配置或外部 Cost Policy Owner 向 Valuation 请求提供不可变 `Pricing Input Revision`；它是 `X-COST-VALUATION-01` 的受控输入，不是 Telemetry 拥有的独立权威对象。

每个输入至少固定 Source / Revision / Digest、适用 Provider / Product / Region / Tier、Effective Time Interval、规范 Meter Unit、单价 / Currency / 舍入规则、规则唯一键、审核引用和 Classification。Telemetry 在使用前机械校验完整性、Digest、区间和规则唯一性；重叠、缺失或同一匹配键不唯一时该次估值为 `UNVALUED`，不能把不合格输入注册成平台状态。

Application 或批处理发起 Valuation 时必须显式携带 exact Pricing Input Revision / Valuation As-Of；不解析动态 `latest`。配置变化产生新的外部 Revision，只影响新 Valuation。只有出现平台内价格历史管理、多人审批或自动同步的真实需求后，才为 Cost Policy Owner 建立独立 Management 主题和写契约；Telemetry 继续只读消费 exact Revision。

### 7.2 Cost Valuation

Cost Valuation 把一个或多个 effective Usage Report 按 exact Pricing Input Revision 转换为非控制性的估算成本。每项固定：

- Valuation ID / Revision / Supersedes、Valuation Basis / As-Of、effective Usage Report Set / Digest；同一 Meter Key 在一个 Basis 内恰好选择一个 Revision。
- Provider / Product / Region / Tier / Effective Time 条件和 Pricing Input / Rule Reference。
- Quantity / Unit、单价、单一 Currency、舍入规则。
- `ESTIMATED | UNVALUED`、总额、明细和 Digest。

Pricing 缺失、Digest 无效、时间范围不匹配、Unit 不支持或同一 Pricing Input Revision 中有零个 / 多个匹配 Rule 时为 `UNVALUED`，不能用零成本、最近价格或模型猜测补齐。Pricing Input 更新只影响新 Valuation；历史 Valuation 永久引用原 Revision，需要重算时创建新 Revision并显式 Supersede 旧 Valuation。历史输入由配置 Owner 按其政策保留；引用已不可读取时明确 `PRICING_INPUT_UNAVAILABLE`，不能改绑到新 Revision。同一 Valuation Basis / As-Of 不能同时累计被替代和替代 Revision。

Cost Valuation 只按 Usage Report 中确切存在的 Attribution Context 支持 Task、Scope、Capability、Strategy、Model、Tool / Connector 和 Resource Account 聚合；INCOMPLETE / UNATTRIBUTED 单独统计。不同 Currency 不相加，除非未来启用独立、版本化的换汇 Contract。聚合结果用于观察和管理决策输入，不是 Resource Ledger 余额，也不能覆盖已发生用量。

## 8. Budget 与运行控制边界

预算主干完全复用 DD-X-CAPABILITY-EXECUTION：

1. Application Layer 创建 Resource Account / Policy 和根 Allocation。
2. 直接用例由目标 Application Service 做子分配和继续 / 停止决定；Web Task 由 Conversational Task Control 创建 Agent 子分配并推进任务，Orchestrator 只提出资源需求 Proposal。
3. Shared Execution Infrastructure 原子预留、结算并保留真实 Resource Ledger。
4. 执行模块报告实际 Usage；Telemetry 关联 Usage、Settlement 和 Cost。

若 Allocation 使用货币额度，Application-owned Resource Policy 必须把 exact `Budget Conversion Rule / Revision` 冻结进 Execution Envelope / Allocation；Shared Execution Infrastructure 只按该 Rule 和执行边界实际观察量结算，不同步查询 Telemetry Cost Valuation。Telemetry 的后算估值与 Resource Ledger 结算不同只产生 Finding，不能回写余额或改变已执行决定。

Telemetry 不提供第二个“剩余预算”字段。若 Dashboard 聚合与 Resource Ledger 不一致，平台以 Resource Ledger 控制运行，并暴露 Finding。成本告警只能通知 Policy Owner；自动停止需要由 Application Layer 中显式、版本化 Resource Policy 实现。

## 9. X-TELEMETRY-EXPORT-01

Exporter Adapter 把中立 Event / Usage / Valuation 转换为目标 Backend 协议。Adapter 必须：

- 固定 Backend / Schema Mapping / Redaction / Sampling / Retry Policy Revision。
- 保留 Event ID、Correlation / Causation、Occurred At、单位、Measurement Quality 和 Classification。
- 对目标 Backend 不支持的字段明确丢弃并记录 Mapping Finding，不能改变语义或单位。
- 以 Batch / Checkpoint 幂等；部分成功只推进已确认成员。
- 在发送前执行 Sink Eligibility 与 Data Classification 门禁。

外部 Backend 不可用时本地 Outbox / Checkpoint 按保留政策积压或受控丢弃允许采样的 Operational Signal。必需 Authority Event 不因普通采样丢弃；本地容量耗尽产生明确 Telemetry Degraded 状态，但不伪造业务失败。

## 10. Metrics、Trace 与审计索引

- Trace / Log 可以携带高基数 Correlation / Task / Attempt Reference；聚合 Metrics 的 Label 必须使用受控有限维度，不把用户 ID、Artifact、Knowledge ID、文件路径或 Prompt 作为 Label。
- Audit Index 只把 Authority Object、Event、Usage、Valuation 和 Delivery Record 关联起来；查询结果必须回到拥有模块读取权威详情。
- 每类 `AUDIT_REQUIRED` Authority Contract 必须由 Owner 定义最小 `Audit Receipt / Tombstone`：至少包含 Object ID / Revision / Digest、Outcome、必要依据引用、Classification、Retention Policy 和 Detail Availability。完整对象退出前，Owner 仍须按审计政策保留该 Receipt；Telemetry 只索引其 Reference，不复制正文。
- Receipt 也不可用时，相关 Event / Audit Query 必须标记 `DETAIL_EXPIRED | AUDIT_INCOMPLETE`，不能继续宣称可完整复核。
- 采样 Trace 只能支持性能分析，不能证明某次业务步骤不存在或没有执行。
- Telemetry Completeness 只说明事件链是否完整，不证明知识、答案或操作结果正确。

## 11. 数据、权限与保留

- Event 继承生产者输入和 Result 的最高适用 Classification；无法比较分类时按最严格组合限制。
- Credential、Secret、连接串、Artifact / Evidence 内容、正式命题正文、Answer 正文、Prompt / Response 和 Agent 私有推理默认禁止进入 Telemetry。
- 需要审计原文时只保存拥有模块的受控 Reference；读取仍通过原模块权限和 Retention Contract。
- Telemetry Retention 与业务对象 Retention 分离；删除事件不能删除业务记录，保留事件也不能阻止业务对象按其 Contract 清理。业务 Owner 清理完整对象仍须遵守自身 `AUDIT_REQUIRED` 最小 Receipt / Tombstone Contract。
- 若平台自身 Telemetry 需要进入软件世界模型，必须作为外部 Data Source 重新经过 Connector → Artifact → Evidence → Knowledge Admission；Telemetry Event 不能直接成为 Fact。

## 12. 失败、幂等与恢复

| 失败类别 | 处理 |
|---|---|
| TELEMETRY_SCHEMA_INVALID | 拒绝 Event 并记录 Producer Finding；不修改业务 Outcome |
| CORRELATION_INCOMPLETE | 接受可验证字段并标记不完整；不能杜撰 Task / Scope |
| OUTBOX_WRITE_FAILED | AUDIT_REQUIRED 的 Authority Record 与 owner-local Marker 同事务时一起失败 / 重试；采用可枚举 Emission State 时由该 Owner 自己补发，Telemetry 不扫描业务 Repository |
| EXPORT_BACKEND_UNAVAILABLE | 保留 / 重试允许的 Outbox；不反向停止业务 |
| EXPORT_PARTIAL | 只推进已确认 Event Checkpoint；重复按 Event ID 幂等 |
| USAGE_MISSING | 标记缺失或 ESTIMATED；不填零 |
| USAGE_DUPLICATED | 同 Report Revision 幂等；同 Meter Key 只选择显式 effective Revision，竞争 Revision 进入冲突且不聚合 |
| ATTRIBUTION_INCOMPLETE | 进入 INCOMPLETE / UNATTRIBUTED bucket；不从文本或相邻 Event 猜测维度 |
| PRICING_INPUT_UNAVAILABLE | exact Pricing Input Revision 无法读取；产生 UNVALUED，不改绑新 Revision |
| PRICING_NOT_FOUND_OR_AMBIGUOUS | 产生 UNVALUED；不使用相近、最新或任意一条价格猜测 |
| AUDIT_RECEIPT_UNAVAILABLE | 标记 DETAIL_EXPIRED / AUDIT_INCOMPLETE；不把悬空 Reference 宣称为可完整复核 |
| CLASSIFICATION_DENIED | 不导出受限 Payload；记录受控 Finding，不降级分类 |
| TELEMETRY_RETENTION_EXCEEDED | 优先按 Policy 丢弃可采样 Signal；关键 Event 进入 Degraded / 运维处理 |

恢复只从 Outbox、Event、Usage、Valuation 和 Export Checkpoint 继续。消费者不根据到达顺序重建业务状态；同一 Event 重放不重复累计 Usage / Cost。

## 13. 拟议不变量与验证义务

### 13.1 拟议不变量

1. Telemetry 是单向横切观察能力，不调用业务模块、不决定知识、发布、充分性、激活或响应放行。
2. 每个 Event 引用权威业务对象，不复制或取代其 Outcome。
3. Resource Allocation、Usage Report 和 Cost Valuation 相互分离；Telemetry 不建立第二套预算余额。
4. 同一 Meter Key / Valuation Basis 只有一个 effective Revision 参与聚合；历史 Revision 可查但不重复计量。
5. 失败、取消和重试的真实消耗不会因业务 Outcome 失败而归零。
6. Pricing 缺失或歧义产生 UNVALUED；Cost Revision 不改写历史 Usage 或 Valuation。
7. AUDIT_REQUIRED Event 的补发只由 Authority Owner 的 Outbox / Emission State 发起；Telemetry 不扫描私有业务 Repository。
8. Event / Export 至少一次时按稳定 ID 幂等，重复不重复计量。
9. Operational Signal 可以采样，但不能替代 Authority Record 或被用来证明“未发生”。
10. Telemetry 不包含 Credential、受限内容或隐藏推理；详细内容只保留拥有模块引用。
11. 外部 Observability / Cost Backend 不成为平台正常业务路径的同步依赖。
12. 平台自身 Telemetry 若要成为软件知识，仍走完整 Data Source 与知识准入路径。

### 13.2 Conformance / 故障注入

进入实现前至少验证：

- 入口 → Agent → Application → Capability → Model / Tool → Publication / Review 的 Correlation 与直接 Causation 可追溯，缺失字段不被猜测。
- Authority 事务、owner-local Outbox / Emission Marker、Exporter 崩溃、Event 重复 / 乱序和 Owner-side Reconciler 补发不会形成缺失审计事件、跨 Repository 读取或重复业务 Outcome。
- Model / Tool 失败、重试、取消仍结算真实 Usage；Allocation 上限不被误报为实际成本。
- 同一 Meter Key 从 ESTIMATED 更新为 PROVIDER_REPORTED、竞争 Usage Revision、As-Of 回看和重复 Event 均只选择一个 effective observation。
- 缺失归因字段进入独立 bucket；Task / Scope / Capability / Strategy / Model / Connector 聚合不使用推测 Join。
- Pricing Input 缺失、Digest 无效、不可读取或规则重叠返回 UNVALUED；Input Revision 变化创建新 Valuation，不改写旧 Basis；不同 Currency 不被静默相加。
- Resource Policy 的 Budget Conversion Rule 与 Telemetry 后算 Valuation 不一致时只产生 Finding，运行结算不读取或采用后者。
- Export Partial、Backend 长时间不可用、Checkpoint 回退和进程恢复保持 Event / Usage 幂等。
- 完整 Authority Object 清理后仍可通过 Owner 的最小 Audit Receipt 复核 Outcome；Receipt 已按政策退出时明确 AUDIT_INCOMPLETE。
- Prompt、Artifact / Evidence、正式命题、Answer 正文、Credential 和高敏 Locator 不进入 Event / Metric Label。
- Telemetry Dashboard、告警或异常分析尝试反向调用业务、修改 Activation /预算 / Snapshot 或放行答案时被拒绝。

当前无需 Design Validation Demo 决定中立单向事件、Usage / Cost 分离和非权威边界。具体 Backend Mapping 使用 `CC-*` Conformance；Provider 用量字段和 Pricing Mapping 只有在真实 API 行为会迫使改变公共 Unit / Quality Contract、且静态说明不足时才建立有界 `DVR-*`。
