# Iteration 001 Shared Error Classification

| 元数据 | 值 |
|---|---|
| Baseline ID | ITER-001-SHARED-ERROR-CLASSIFICATION |
| Version | 0.1.0 |
| Status | Frozen for Iteration 001 |
| Implementation Plan | [SWM-IMP-ITER-001](../Implementation_Plan_Iteration_001.md) |
| Design Baseline | [SWM-DBM-ITER-001-REV-002](../../../detailed-design/governance/Design_Baseline_Manifest_Iteration_001_Revision_002.md) |
| Implementation Baseline | [SWM-IBM-ITER-001-REV-002](../Implementation_Baseline_Manifest_Iteration_001_Revision_002.md) |
| Model Adapter | [SWM-ADAPTER-OAI-RESPONSES-001](ITER-001-OpenAI-No-Tools-Adapter-Profile.md) |
| Local Git Profile | [ITER-001-LOCAL-GIT-PROVIDER](ITER-001-Local-Git-Provider-Profile.md) |
| Knowledge Schema | [SWM-ITER-001-KNOWLEDGE-SCHEMA](ITER-001-Initial-Knowledge-Schema.md) |
| Applies To | Iteration 001 模块化单体、Web Chat、CLI 与 Scheduler |
| Authority | 各 Accepted 主题的 Owner Result / Failure Contract 仍是唯一领域权威 |

> 本文是 Iteration 001 的跨主题实现映射，不修改 Accepted Contract，不建立第二套领域错误权威。它统一“如何携带、组合、恢复和披露错误”，不统一“领域上为什么失败”。

## 1. 目的与边界

不同 Owner 已经在各自 Accepted 主题中定义了稳定失败语义，例如 Scope Revision 冲突、Source Outcome Pending、模型隔离失败、Candidate 被拒、Publication 冲突和 Response Delivery Unknown。Iteration 001 需要一个共享外壳，使 Application Services、CLI、Web Response Control 和 Telemetry 在不重解释领域语义的前提下，能够一致回答：

- 错误来自哪个权威 Owner 和哪个 exact Result。
- 当前调用的 Outcome 是否已经确定。
- 是否允许重试，以及必须沿用原身份还是形成新请求。
- 哪些信息可以向用户、管理员或仅向内部审计披露。
- 多个 Owner 失败时如何形成组合 Application Result。

本文不定义：

- Java/Kotlin 异常类、包结构、`throw/catch` 规则或数据库表。
- HTTP、WebSocket、CLI exit code 或 RPC status 的具体映射。
- UI 文案、国际化消息、告警等级或值班策略。
- 全部主题错误码的复制目录。
- Knowledge Gap、正式 Conflict Inference、Evaluation `INCONCLUSIVE`、Telemetry `UNVALUED` 等领域结果的替代语义。

## 2. 基本原则

1. **Owner 语义优先。** `Owner Contract + Owner Error Code + exact Result Reference / Digest` 是错误含义的权威来源；Shared Category 只是实施投影。
2. **分类轴相互独立。** Shared Category、Outcome Certainty、Recovery Directive 和 Exposure Disposition 分别表达原因、确定性、下一动作和披露范围，不能互相推导替代。
3. **未知 Outcome 不是普通暂态失败。** 一旦越过 dispatch 边界而结果未知，只能查询或恢复原 Attempt / Idempotency Key；不得创建“等价重试”猜测旧调用未发生。
4. **失败不能伪装为成功。** Application Services 可以组合多个 Owner Result，但不能把拒绝、未知、部分完成或取消重命名为成功。
5. **正常认知结果不错误化。** Knowledge Gap、Unknown、正式 Conflict、部分正式支持和 `INCONCLUSIVE` 可以是已知且可交付的领域结果；只有执行或契约未能产生该结果时才形成错误。
6. **披露服从最小权限。** Shared Category 不授权披露 Prompt、Payload、Evidence 内容、Secret、路径、SQL、Stack Trace、模型响应或内部 Locator。
7. **不按名称猜测。** 不通过错误码前缀、异常类名或文本消息推断 Category、重试或 Outcome；映射必须绑定 exact Owner Contract Version。

## 3. Shared Error Envelope

跨主题边界传递的非成功结果至少使用以下逻辑字段。它可以嵌入 Owner Result、Application Step Revision 或组合 Application Result，不要求建立独立 Repository。

| 字段 | 约束 |
|---|---|
| Error Occurrence ID | 本次错误观察的稳定身份；重放同一 Owner Result 不生成第二个逻辑错误 |
| Source Owner | 产生权威 Outcome 的逻辑 Owner，不使用进程、类或线程名 |
| Owner Contract / Version | exact Accepted Contract，例如 `SRC-OPERATION-01` |
| Owner Result / Attempt Reference | exact Result、Attempt、Revision 与 Digest；不能只保存文本消息 |
| Owner Error Code | Owner 原始稳定代码或明确的领域 Outcome；不得被 Shared Category 覆盖 |
| Shared Category | §4 的一个稳定类别 |
| Outcome Certainty | §6 的一个值 |
| Recovery Directive | §7 的一个值；同时保留 Owner 给出的前置条件和预算边界 |
| Exposure Disposition | §8 的一个值；实际字段仍受 Caller、Purpose 和 Classification 校验 |
| Affected Target | 适用时固定 Scope、Binding、Artifact、Snapshot、Task、Requirement、Result 或 Delivery 引用 |
| Dispatch / Idempotency Closure | 适用时固定 Dispatch Attempt、Owner Idempotency Key、Request Digest 和 Provider Request ID |
| Partial / Remaining Reference | 适用时引用已完成成员、Cursor、未完成范围或 Limitation；不复制大正文 |
| Diagnostic Reference | 指向 Owner 受控诊断或审计记录；Shared Envelope 不复制敏感详情 |
| Data Classification | 取全部适用输入和诊断的最严格有效分类 |

若同一 Owner Result 已经包含等价字段，Application 层只保存引用，不复制一份可能漂移的值。映射记录必须能够从 exact Owner Result 确定性重建。

## 4. 稳定语义类别

下表是 Iteration 001 的共享类别全集。示例只用于说明映射形状，不是 Owner 错误码目录。

| Shared Category | 适用语义 | 代表性 Owner 语义（非穷举） | 默认恢复方向 | 默认披露 |
|---|---|---|---|---|
| `INVALID_REQUEST` | 输入形状、参数、Purpose、Selector 或命令本身无效，且尚未形成有效执行 | `INPUT_INVALID`、`SELECTOR_INVALID`、`COMMAND_INVALID` | `AFTER_CORRECTION` | `SAFE_ACTIONABLE` |
| `TARGET_OR_REFERENCE_UNRESOLVED` | exact 身份不存在、不唯一、不受支持或无法形成 canonical reference | `SCOPE_NOT_FOUND`、`SOURCE_TARGET_NOT_FOUND`、`SOURCE_TARGET_AMBIGUOUS`、`NO_CURRENT_SNAPSHOT` | `AFTER_CORRECTION` 或 `AFTER_REFRESH` | `SAFE_ACTIONABLE` |
| `ACCESS_OR_POLICY_DENIED` | 权限、Classification、Control State、Scope 状态、Tool Policy 或交付政策不允许 | `DATA_POLICY_DENIED`、`CONTROL_STATE_DENIED`、`TOOL_DENIED`、`RESULT_DELIVERY_DENIED` | `AFTER_AUTHORIZATION` | `SAFE_LIMITATION`；诊断通常更严格 |
| `STALE_OR_CONCURRENT_STATE` | Expected Revision、CURRENT、Cursor、Session、Assertion、Fence 或幂等占用与当前权威状态冲突 | `REVISION_CONFLICT`、`CURRENT_CONFLICT`、`CURSOR_STALE`、`IDEMPOTENCY_MISMATCH` | `AFTER_REFRESH`；同 Key 冲突不得盲重试 | `SAFE_ACTIONABLE` |
| `CAPABILITY_OR_CONFIGURATION_UNAVAILABLE` | exact Provider、Strategy、Adapter、Schema、Tool、Profile 或激活资格不存在或不兼容 | `NO_ACTIVE_STRATEGY`、`PROVIDER_NOT_CONFIGURED`、`ISOLATION_UNSUPPORTED`、`SCHEMA_UNSUPPORTED` | `AFTER_OPERATOR_CHANGE` 或预先批准的 fallback | `ADMIN_ACTION_REQUIRED` |
| `DEPENDENCY_UNAVAILABLE` | 已选择的外部或内部依赖暂时不可访问，但没有证据表明 Contract 本身无效 | `PROVIDER_UNAVAILABLE`、`SOURCE_UNAVAILABLE`、`EXPORT_BACKEND_UNAVAILABLE` | `BOUNDED_SAME_INPUT`；越过 dispatch 后受 Outcome Certainty 覆盖 | `SAFE_LIMITATION` |
| `RESOURCE_LIMIT_REACHED` | Allocation、Token、Tool、时间、大小、并发、速率或存储边界已达到 | `BUDGET_EXHAUSTED`、`RATE_LIMITED`、`PAYLOAD_TOO_LARGE` | `NO_RETRY`，或取得新 Allocation / 更窄请求后形成新调用 | `SAFE_LIMITATION` |
| `CONTRACT_OR_VALIDATION_REJECTED` | 输出形状、领域 Contract、Lineage、Evidence、Candidate、Admission、Sufficiency 或 Review 门禁未通过 | `OUTPUT_CONTRACT_INVALID`、`MODEL_RESULT_NOT_ELIGIBLE`、`LINEAGE_INVALID`、`SUFFICIENCY_PROOF_INCOMPLETE` | `AFTER_CORRECTION`，仅在 Owner 允许的有界修正循环内 | `SAFE_LIMITATION` |
| `CONTEXT_OR_SCHEMA_INCOMPATIBLE` | 各输入本身可读，但 Context、Schema、Scope Binding 或 Snapshot 集合不能合法组合 | `CONTEXT_NOT_COMBINABLE`、`MULTI_SCOPE_INCOMPATIBLE`、Schema / Session incompatibility | `AFTER_CORRECTION` 或 `AFTER_OPERATOR_CHANGE` | `SAFE_LIMITATION` |
| `PARTIAL_OR_INCOMPLETE` | 已知取得部分结果、覆盖、分页或成员，但完整条件未满足 | `SOURCE_PARTIAL / TRUNCATED`、`QUERY_PARTIAL`、`EXPORT_PARTIAL` | `CONTINUE_FROM_OWNER_STATE`；不得重做已完成效果 | `SAFE_LIMITATION` |
| `CANCELED_OR_REVOKED` | Caller、Task Control、Resource Policy 或权威 Owner 阻止后续执行 | `CANCELLED`、`EXECUTION_REVOKED`、读取或权限撤销 | `NO_RETRY`；新授权或新任务形成新调用 | `SAFE_LIMITATION` |
| `INTERNAL_INTEGRITY_FAILURE` | 平台无法证明自身持久化、Digest、稳定引用、映射或原子不变量成立 | 悬空权威引用、不可解释的 Commit/Receipt 缺失、未知 Owner Code、持久历史不连续 | `AFTER_OPERATOR_CHANGE`，默认 fail-stop | `INTERNAL_ONLY` 或 `SECURITY_REDACTED` |

类别不改变 Owner 的细粒度差异。例如 `NOT_FOUND` 可以是 Source Target Resolution 的已知 Receipt，而不是异常；Shared Category 只说明当前用例无法继续解析目标。`MODEL_RESULT_NOT_ELIGIBLE` 也不等于 Provider 调用没有发生，其 Outcome Certainty 必须根据 exact Model Call / Capability Attempt 单独填写。

## 5. 来源 Owner

| Source Owner | 对哪些失败拥有权威 | 不能做什么 |
|---|---|---|
| Application Use Case Owner | Request / Attempt、Build Intent、Requirement、Session、组合步骤、Publication Acceptance、Sufficiency 与应用 Result | 不能把 Source、Knowledge、Model 或 Delivery Owner 的失败重解释为成功 |
| Conversational Task Control | Task、Agent Invocation、Delegated Grant、Application Dispatch 与 Reviewer Invocation Outcome | 不能拥有领域 Use Case Outcome 或 Review Decision |
| Response Control | Candidate、Review Matrix / Decision、Final Authorization、Logical Delivery 与发送收口 | 不能修改 Task、Knowledge、Application Result 或 Adapter Receipt |
| Shared Execution / Resource Owner | Allocation、Dispatch Binding、结算、取消 Fence 和资源状态 | 不能判断领域结果正确性 |
| Model Gateway | Manifest / Provider Request、隔离能力、Model Call、Provider Outcome 与实际模型指纹观察 | 不能判断 Candidate、Assessment 或 Answer 是否可接纳 |
| Capability Owner | 输出 Contract、post-call model eligibility 与领域 Proposal / Assessment 封存资格 | 不能改写 Model Gateway 的真实调用 Outcome |
| Evaluation / Activation Management | Evaluation Run / Result / Validity、Activation Decision 与 Resolution | 不能让未通过或已失效 Strategy 临时进入生产 |
| Source Integration | DataSource / Binding、Target Resolution、Source Operation、Artifact / Lineage、Read Package / Protection 与 Use Confirmation | 不能产生 Evidence、Fact 或知识充分性结论 |
| Knowledge Engine Owner | Scope、Schema、Context、Evidence、Entity、Fact、Inference、Admission、Snapshot、Publication 与权威持久化 | 不能访问 Data Source 或拥有 Application 调查状态 |
| Interface Adapter | 协议接收结果与外部 Delivery Receipt | 不能判断业务响应是否获准，也不能因网络错误生成第二份正文 |
| Telemetry Infrastructure | Event、Usage、Valuation、Exporter Checkpoint 与观测完整性 | 不能覆盖任何业务 Outcome、预算、Activation、Snapshot 或响应放行 |

外部 Provider、数据库驱动或操作系统错误先由直接调用它的 Owner 封装为 Owner Failure Contract，再进入 Shared Mapping。Application 层不能直接把第三方字符串或异常类提升为 Shared Category。

## 6. Outcome Certainty

| 值 | 含义 | 强制处理 |
|---|---|---|
| `NOT_DISPATCHED` | 机械证明没有越过目标 Owner / Provider 的 dispatch 边界 | 可以在修正、刷新或重新授权后形成新调用；旧 Attempt 保留终态 |
| `TERMINAL_KNOWN` | exact Owner 已给出可验证终态；成功、拒绝、失败或无结果的具体语义由 Owner Result 表达 | 不重复执行已完成效果；按 Owner Contract 决定后续 |
| `PARTIAL_KNOWN` | 已完成成员和未完成范围均可枚举，且不存在未知在途调用 | 保留已完成部分，只从 Owner Cursor / Continuation 或新显式 Attempt 处理剩余范围 |
| `OUTCOME_UNKNOWN` | 已越过 dispatch，但原调用真实 Outcome 暂不可证明 | 整体进入 Outcome Pending；只查询、恢复或幂等重放原身份，禁止替代调用 |

`TIMEOUT`、连接断开、进程崩溃和 Cancel Request 都不能单独决定 Outcome Certainty。Certainty 必须来自拥有 dispatch fence、Provider Request ID、Publication Attempt、Finalize Attempt 或 Delivery Adapter Key 的 Owner。Certainty 描述一个 exact Dispatch / Attempt，不自动禁止 Strategy 在其 Accepted Contract 明确允许时创建新的独立 Attempt；新的 Attempt 必须使用新身份和独立资源结算，不能被表述为已经解析、覆盖或取消原 `OUTCOME_UNKNOWN`。

运行时按权威记录映射，不按异常类型映射：

| Owner 可证明的事实 | Outcome Certainty | Recovery 覆盖规则 | 对外最低表达 |
|---|---|---|---|
| dispatch fence 未越过，或 Owner 明确拒绝创建执行 | `NOT_DISPATCHED` | 使用 Category 默认 Directive | 安全的拒绝或修正动作 |
| exact Owner Receipt / Result 已封存且没有未决成员 | `TERMINAL_KNOWN` | 使用 Owner Result 声明的 Directive | 已知失败、拒绝、取消或无结果 |
| completed / remaining 集合均封闭且没有未知 Attempt | `PARTIAL_KNOWN` | 强制保留已完成项，只允许 continuation / 新显式 Attempt | 部分结果与未完成范围同时披露 |
| dispatch 已发生，但 Receipt / Result 暂不可证明 | `OUTCOME_UNKNOWN` | 强制 `SAME_IDENTITY_RECOVERY` | Outcome Pending；不得承诺成功或失败 |

## 7. Recovery Directive

Retryability 不是一个布尔值，而由下表明确区分“自动重试”“原调用收口”“延续剩余工作”和“满足条件后发起新 Attempt”：

| 值 | 允许动作 | 当前 Attempt 可自动推进性 |
|---|---|---|
| `NO_RETRY` | 当前调用终止；只有新的业务目标、授权或管理决定才能形成新请求 | 否 |
| `SAME_IDENTITY_RECOVERY` | 使用原 Attempt / Idempotency Key / Request Digest 查询、解析，或执行 Owner Contract 明确支持的幂等恢复；不得创建替代 Logical Occurrence。若 Owner 需要新的物理恢复尝试，必须使用独立 Dispatch ID / child Allocation 并仍绑定原逻辑身份 | 仅允许有界 Outcome Reconciliation，不等于重新执行业务语义 |
| `BOUNDED_SAME_INPUT` | 在 Owner Policy、剩余 Allocation 和相同冻结输入内执行有界暂态重试；每次物理尝试单独记录 | 是，但必须同时满足全部前置条件 |
| `AFTER_REFRESH` | 重新读取 exact Revision、CURRENT、Assertion、Fence、Cursor 或权限后，由调用方显式决定是否形成新 Attempt | 否；刷新后显式决策 |
| `AFTER_CORRECTION` | 修正请求、目标消歧或提交完整 replacement Proposal；不能原地篡改已封存输入 | 否；修正后形成新 Attempt / Revision |
| `AFTER_AUTHORIZATION` | 获得新的权限、Task Authorization、Delegated Grant 或 Classification Decision 后形成新调用 | 否；授权后显式调用 |
| `AFTER_OPERATOR_CHANGE` | 管理员完成 Provider / Adapter / Strategy Activation / Schema / 部署修复后再执行 | 否 |
| `CONTINUE_FROM_OWNER_STATE` | 使用 Owner 签发的 Cursor、Continuation 或剩余成员闭包继续，不重做已完成成员 | 仅延续，不是重试已完成成员 |

Shared Category 只提供默认方向，最终 Directive 由 Owner Failure Contract 与实际 Outcome Certainty 共同决定。若 `Outcome Certainty = OUTCOME_UNKNOWN`，该 exact Attempt 的 Directive 必须为 `SAME_IDENTITY_RECOVERY`；其他默认值一律被覆盖。Strategy 若获准创建新的独立 Attempt，必须另行分类，不能用它把原 Attempt 改记为已恢复。

## 8. Exposure Disposition

| 值 | 可披露内容 | 典型消费者 |
|---|---|---|
| `SAFE_ACTIONABLE` | 稳定 Shared Category、经授权的 Owner Code、受控目标引用和调用方可执行的修正动作 | Web 用户、CLI 调用方 |
| `SAFE_LIMITATION` | “当前无法完成/仍有未知/仅部分完成”的结构化限制、允许披露的 Coverage 与下一步；不披露内部正文 | Web Response Control、CLI |
| `ADMIN_ACTION_REQUIRED` | 稳定配置/能力缺失类别、受控 Provider / Strategy Reference 和管理动作 | 获授权管理员 |
| `SECURITY_REDACTED` | 仅说明请求被安全或隔离门禁拒绝，并返回受控审计 Reference；不暴露规则、Secret 或探测细节 | 用户看到泛化拒绝，安全管理员按权限深查 |
| `INTERNAL_ONLY` | Error Occurrence、Owner Result、Digest、Correlation 和受控 Diagnostic Reference | 研发、审计、故障处理 |

规则：

- Web 响应只能通过 Response Control 的 Claim / Limitation 和 Delivery Assertion 披露，不直接序列化 Shared Error Envelope。
- 结构化 CLI 可以在当前管理权限和 Classification 允许时返回 Owner Code / Result Reference；这不授权返回 Payload、Prompt、Evidence Quote 或 Secret Reference 细节。
- Telemetry 只记录 Category、Owner、Result Reference / Digest、Certainty、Directive、数量和时延等中立字段，不复制用户输入、Answer、Artifact / Evidence 或 Stack Trace。
- 多个错误组合时采用最严格 Exposure Disposition；更严格的字段不能因另一个错误可公开而降级。

## 9. 映射规则

1. 映射键为 `Owner Contract ID + exact Contract Version + Owner Error Code / Outcome`。允许使用 Owner Result 中已定义的状态字段作判别，不允许解析自由文本。
2. 每个映射固定 Shared Category、默认 Recovery Directive 和默认 Exposure Disposition；Outcome Certainty 在运行时由 Owner 的 dispatch / commit / receipt 记录确定。
3. 同一 Owner Code 在不同 Contract Version 下可以有不同映射；版本变化必须显式评审，不能沿用“最新映射”。
4. 未登记 Owner Code、缺少 exact Result Reference、映射条件重叠或映射结果不唯一时，分类为 `INTERNAL_INTEGRITY_FAILURE` 并失败关闭；不能选择最相近类别。
5. Owner Error Code 仍随 Application Step Result 保留。Shared Category 不参与 Owner 幂等键、状态迁移、知识身份或正式命题判断。
6. 第三方异常先由直接 Owner 规范化。Provider message、SQLState、进程 exit code 或网络异常不能直接穿透到用户响应。

## 10. 组合规则

### 10.1 跨 Owner Application Result

- 组合 Result 保存全部 Step Error Reference；不合并为一段失去来源的错误文本。
- `Primary Blocking Cause` 取冻结工作流中第一个阻止必需后续步骤的 Step；同层并发 Step 按稳定 Step ID 排序。它只用于展示，不删除其他原因。
- 任一已 dispatch 必需 Step 为 `OUTCOME_UNKNOWN` 时，组合 Outcome 必须为 `OUTCOME_PENDING`，Recovery 只能恢复该原 Step。
- 不存在 Unknown，但同时有已完成和未完成/失败步骤时，组合结果按 Owner Contract 为 `PARTIAL` 或对应应用级部分完成；已完成效果不得回滚成“从未执行”。
- 所有失败均为 `NOT_DISPATCHED` 或 `TERMINAL_KNOWN` 时，Application 才能形成稳定失败终态。

### 10.2 重试与取消

- 自动重试需要 Owner Contract、Application Policy、剩余 Allocation 和 Outcome Certainty 全部允许；采用其中最严格限制。
- Revision、CURRENT、Assertion、Cursor 或 Policy 改变后使用 `AFTER_REFRESH`，不能在旧 Attempt 中替换冻结输入。
- Contract / Validation 拒绝只允许提交完整 correction / replacement；相同无变化输入不得循环重试。
- Cancel 只阻止未 dispatch 工作。已 dispatch Outcome 必须按原 Owner 收口；Cancel 不能覆盖已发生或未知的效果。

### 10.3 特殊领域结果

- Knowledge Gap、Unknown、正式 Conflict 和 `PARTIAL_FORMAL_SUPPORT` 是 Knowledge Use / Response Control 可审核的业务结果，不映射为 `INTERNAL_INTEGRITY_FAILURE`。
- Evaluation `FAIL | INCONCLUSIVE` 是已知 Result；只有 Evaluation 执行未能形成可裁决 Result 时才形成执行错误。
- Telemetry `UNVALUED | INCOMPLETE | UNATTRIBUTED` 是观测质量；不能改写业务 Outcome 或把成本填为零。
- Projection 未启用时，若 Accepted Contract 允许权威 Repository 路径，则不是系统失败；只有请求超出当前资源边界时返回明确 Limitation。

## 11. Iteration 001 验证义务

WP-0 必须冻结以下 Conformance Case 定义，但不要求在实现骨架出现前伪造运行结果。各 Case 在其首个实现消费者所在工作包退出前执行；未通过时阻止相应能力继续推进，不反向放宽 Owner Contract：

| Case | 验证目标 |
|---|---|
| `CC-ERR-MAPPING-COVERAGE-001` | 本切片实际使用的每个 Owner 非成功 Code / Outcome 都有唯一版本化映射；未登记代码失败关闭 |
| `CC-ERR-OUTCOME-UNKNOWN-001` | Source、Model、Publication、Evidence Finalize 和 Delivery 响应丢失时只恢复原身份，不产生替代副作用 |
| `CC-ERR-COMPOSITE-001` | 多 Step 成功、失败、取消、部分与 Unknown 的组合结果确定且保留全部 Owner Reference |
| `CC-ERR-RETRY-001` | 只有 Owner + Policy + Allocation + Certainty 同时允许时才重试；冻结输入变化产生新 Attempt |
| `CC-ERR-EXPOSURE-001` | Web、CLI、Telemetry 对同一错误执行不同的受控披露，Secret、Prompt、Payload、Evidence 和 Stack Trace 不泄露 |
| `CC-ERR-TELEMETRY-001` | Telemetry / Export 失败不反向修改业务 Outcome；AUDIT_REQUIRED owner-local Marker 仍遵守原事务 Contract |

## 12. 实现期验证与后续产物

以下事项属于实现 Conformance，不是修改 Accepted 设计的理由：

- 选定 no-tools Model Provider Adapter 后，登记其 Provider 原生错误到 Model Gateway Owner Code 的映射，并验证 timeout / cancel / late response。
- 为 Local Git Provider 定义 Git process、对象不存在、shallow history、权限、仓库损坏和输出截断的 Owner 规范化结果；不得把 stderr 直接提升为 Shared Category。
- 选定单一 ACID Store 和驱动后，验证 CAS、唯一约束、事务 Outcome Unknown 与持久历史 fail-stop 的 Owner 映射。
- 在 Interface 实现阶段另建协议适配表，把 Shared Envelope 映射到 HTTP / WebSocket / CLI；该表不得反向改变本文或 Owner Contract。
- 本文件已经完成 WP-0 复核并冻结；实施方案中的“跨主题错误分类” Gate 可以标记为 Completed。Conformance 运行状态继续独立记录，不能用文档冻结冒充测试通过。
