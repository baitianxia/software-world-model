# Source Integration 与 Artifact 详细设计

| 元数据 | 值 |
|---|---|
| Document ID | DD-SRC-SOURCE-ARTIFACT |
| Version | 0.1.0 |
| Status | Accepted |
| Document Steward | Source Integration |
| Architecture Baseline | SWM-ARCH@1.2 |
| Depends On | DD-SRC-DATA-SOURCE@0.1.0、DD-KNW-REFERENCE-CONTEXT@0.1.0、DD-X-CAPABILITY-EXECUTION@0.1.0 |
| Owns Contracts | SRC-PROVIDER-01、SRC-TOOL-01、SRC-TARGET-RESOLUTION-01、SRC-OPERATION-01、SRC-READ-SESSION-01、SRC-CONTEXT-01、SRC-ARTIFACT-01、SRC-ARTIFACT-ACCESS-01、SRC-DERIVED-ARTIFACT-01、SRC-PROCESSING-01、SRC-LINEAGE-01、SRC-ARTIFACTIZATION-PROFILE-01、SRC-RETENTION-01 |
| Conditional Depends On | DD-AI-MODEL-GATEWAY@0.1.0、DD-MGT-CAPABILITY-EVALUATION@0.1.0（仅模型辅助 Target Resolution 或 Artifact Processing） |
| Rationale ADR | AD-014、AD-015、AD-017、AD-018、AD-021、AD-022、AD-023、AD-025、AD-026、AD-091、AD-101、AD-102、AD-108、AD-109、AD-110、AD-133、AD-135 |
| Design Validation | None |
| Conformance Cases | None |
| Capability Evaluation | Target Resolution 或 Artifact Processing 使用模型时分别适用 |

> 概要架构约束直接生效；本文新增的 SPI、Artifact 外壳、Lineage、粒度和保留语义在状态进入 `Accepted` 前均为拟议设计。

## 1. 目的与范围

Source Integration 将 Git、Code、Config、Test、DB、Docs、Logs、Trace、Deployment 等异构外部来源转换为中立 Artifact，使 Knowledge Engine 不依赖任何 Connector 实现或来源协议。

本文定义：

- Connector Provider 与 Connector Tool 的扩展契约。
- 来源原生目标的规范化、消歧和解析凭证。
- Source Operation Request / Result 和执行资格边界。
- Source Context、Source Artifact、Derived Artifact 和 Artifact Lineage。
- Provider 自有、版本化 Artifactization Profile。
- Artifact 身份、Payload、生命周期、保留和淘汰语义。
- 确定性解析与模型辅助加工的边界。

本文不定义：

- Evidence、Entity、Fact、Inference 或 KnowledgeContext 的构造。
- Knowledge Engine 还需要哪些信息，或来源范围是否足以满足用户任务。
- Build Intent、调查循环和发布决定。
- 具体 Git / DB / Log Provider 的配置字段、查询语言和生产保留阈值。
- 外部系统写入、变更代码或生产操作等 Action Capability。

## 2. 模块内部责任

Source Integration 内部保留两个逻辑层次，但在模块化单体中不要求拆成独立服务：

| 层次 | 责任 | 输出终点 |
|---|---|---|
| Connector Layer | 消费 DataSource / Binding / Provider 配置，管理连接、凭据使用、能力发现、来源搜索/读取与 Source Context | Source Operation Result、Source Artifact |
| Artifact Processing Layer | 解析、分段、格式转换、规范化和模型辅助加工 | Derived Artifact、Artifact Lineage |

两层都不能生成 Evidence、Entity、Fact 或 Inference。解析器可以识别语法结构和来源位置，但“该结构代表哪个正式 Entity 或 Fact”由 Knowledge Engine 判断。

DD-SRC-DATA-SOURCE 拥有 DataSource、Binding 与 Selector；本主题拥有 Source Context、Source Operation Result、Artifact 和 Lineage。中立 Artifact Contract 可以位于共享契约包中供 Knowledge Engine 编译依赖，但共享包不取得数据所有权，Knowledge Engine 也不能绕过 Source Integration 写入 Artifact Repository。

Connector Operation 与 Artifact Processing 保留独立内部接口、Strategy 和测试边界，但当前不拆成两个详细设计主题：二者由同一 Source Integration 执行 Owner 管理，Source Operation 的 Observation / Context、Artifact 身份和 Lineage / Retention 共同决定下游可复核读取闭包。只有出现独立所有者、独立发布契约或无法共同演进的生命周期后，才按总纲 4.1 拆分主题；代码包或处理步骤不同本身不是拆分依据。

## 3. Connector 扩展 SPI

### 3.1 SRC-PROVIDER-01：Connector Provider

Connector Provider 面向一种 DataSource 类型，实现并扩展 `SRC-DATA-SOURCE-PROVIDER-01`。基础配置、Identity 与 Selector 语义由上游 Contract 唯一定义；本主题增加可执行连接和 Artifact 能力：

- exact DataSource Provider Contract Reference / Digest 与兼容范围。
- 连接 Adapter、凭据使用、连接生命周期和运行时隔离要求。
- Connector Tool 清单、能力发现和各 Tool 的版本。
- Source Context 词汇、来源原生 Revision / Cursor 语义。
- Artifact Kind、Payload Schema 与 Artifactization Profile 清单。
- 连接健康和 Provider 能力事实。

Provider 不负责：

- 把 Source ID、路径、表名或日志字段解释成 Entity ID。
- 跨 DataSource 建立版本、部署或业务语义映射。
- 根据用户问题改变权限或返回未声明 Tool。
- 声明 Artifact 内容已经构成 Evidence 或正式知识。

Binding Proposal 只按上游 `SRC-BINDING-PROPOSAL-01` 形成和接受；Connector Provider 可以提供来源元数据 Observation，但不能在本 SPI 中重新定义 Selector、暗中调用模型或写入 Binding。

### 3.2 SRC-TOOL-01：Connector Tool

Connector Tool 表达一个有界、可授权、可计量的来源读取动作。一个 Provider 可以暴露多个 Tool，例如：

- `list`：列举受 Selector 限定的来源对象。
- `search`：按来源原生查询能力返回定位结果。
- `read`：读取确切对象、Revision、Range 或 Cursor。
- `compare`：比较两个确切来源 Revision。
- `query`：执行 Provider 允许的只读结构化查询。
- `read-window`：读取明确时间窗和分页 Cursor 的日志/Trace 片段。

每个 Tool Contract 至少定义：

| 语义 | 约束 |
|---|---|
| Tool ID / Version | 在 Provider Contract 内稳定且可回放 |
| Input Schema | 只允许声明的参数、Revision、时间窗、Range、分页和排序 |
| Outcome Schema | Provider 原生 Tool Outcome / Observation；不能自行填写平台 Result、Grant、Context ID 或 Artifact ID |
| Capability Flags | 是否支持 Snapshot Read、分页、稳定排序、比较、内容哈希等 |
| Cost Model | 调用、扫描、返回体积和 Provider 配额的估算维度 |
| Data Classification | 允许读取和返回的数据等级 |
| Side Effect | Source Integration Tool 必须为只读；无法证明只读则不得在此 SPI 注册 |

Provider 负责连接生命周期和能力发现；Tool 负责一次具体有界操作。两者不能合并成“Connector 自由执行任意命令”的接口。

Tool Outcome 只报告来源原生响应、Cursor、边界、错误和 Provider 能声明的覆盖/完整性事实。Source Integration 必须依据真实分派记录和冻结 Contract 重建平台 Source Operation Result、Source Context、Artifact 身份、Grant 关系及覆盖分类；自定义 Provider 不能自报这些平台权威字段。Provider 的完整性声明只有在相应 Capability 和 Conformance 仍有效时才能被平台采纳。

### 3.3 SPI 兼容与注册

- Provider、Tool、配置、Identity Strategy、Selector、Source Context Vocabulary、Artifact Kind 和 Profile 分别版本化。
- 新 Provider 只能注册自身命名空间内的 Payload / Context Schema，不能修改中立 Artifact 外壳。
- Provider 升级不能静默改变已有 Binding 或 Artifact 的解释；不兼容变化创建新 Contract Version，并通过 Binding Revision 或新 DataSource 生效。
- Provider 实现必须通过 Contract Conformance，覆盖 Identity、Selector、权限、分页、截断、Context、Artifact 身份、撤权和失败语义。

### 3.4 SRC-TARGET-RESOLUTION-01：来源目标解析

Source Target Resolution 把用户或模型提出的人类可读目标解析成 Source Integration 能够机械比较和执行的 Canonical Operation Target。它只解析来源身份与定位，不把代码符号、Endpoint、表或文档解释为正式 Entity / Fact，也不判断该目标是否足以满足用户 Need。DataSource 定义中的 `Canonical Source Target` 仍专指仓库、数据库实例、日志服务或文档空间等来源根身份，不能与本契约的操作目标混用。

`Source Target Resolution Request` 至少固定：

- Request ID / Idempotency Key、原始 Target Proposal Digest 和 Target Kind。
- DataSource / Binding Definition Revision、Provider Registry Snapshot 和允许的 Resolver / Tool Contract Version。
- 可选已解析父目标，例如 exact Repository、Revision、Module 或 Document Space。
- 允许的 Scope / Selector / Context Constraint、候选数量和解析资源上限。

每个 Request 创建或恢复唯一 `Target Resolution Attempt`。其稳定键由 Caller Control Boundary、Owner Idempotency Key 和规范 Request Digest 组成，状态为：

`PREPARED → RESOLVING → RESOLVED | FAILED | CANCELED | OUTCOME_PENDING`

`OUTCOME_PENDING → RESOLVING | RESOLVED | FAILED`

- 相同 Owner Idempotency Key 与 Request Digest 返回同一 Attempt、唯一终态 Receipt，或取消终态；不同 Digest 复用 Key 返回 `IDEMPOTENCY_MISMATCH`。
- Attempt 追加记录实际 Resolver Step、Source Operation / Observation Result 和候选集合 Revision。恢复只消费已经封存的 Step Result；已 dispatch 且 Outcome 未知的来源调用必须先按原 Dispatch Attempt 解析，不能以新 ID 假设旧调用未发生。
- 取消只阻止新的 Resolver Step。存在未决外部调用时进入 `OUTCOME_PENDING`，不封存 `NOT_FOUND`、`AMBIGUOUS` 或 `EXECUTION_FAILED` Receipt 来掩盖未知结果。
- 终态 Receipt 与 Attempt 在 Source Integration 本地事务中一次封存。封存后迟到结果只进入原 Dispatch 审计，不修改 Receipt；确需纳入时创建新的 Resolution Request / Attempt。

Provider 可以注册版本化 Target Resolver，或复用 `list / search / read / compare` Tool 组合完成解析。所有外部读取仍走 §4 的 Source Operation 分派、权限、预算和审计边界；Resolver 不能拥有任意查询旁路。

Attempt 以 `RESOLVED` 或 `FAILED` 达到可裁决终态时，Source Integration 形成唯一不可变 `Source Target Resolution Receipt`；`CANCELED` 只形成不含 Canonical Target 的取消终态，不伪造 Receipt：

- Receipt ID / Version / Digest、Attempt / Request / Proposal Digest。
- exact DataSource / Binding / Provider / Resolver Contract Revision。
- Target Kind、Canonical Operation Target Identity、规范序列化和人类可读 Display Label；Display Label 不参与身份和门禁。
- 解析所依赖的父目标、外部 Revision、Observation / Source Operation Result，以及访问边界证明。
- `EXACT | NOT_FOUND | AMBIGUOUS | OUT_OF_SCOPE | UNSUPPORTED | EXECUTION_FAILED` Outcome。
- AMBIGUOUS 时的有界 Candidate Identity / Disambiguation Field 集合；它只用于重新提出目标，不能被调用方任选第一项。

只有 `EXACT` Receipt 可以进入上游 Canonical Build Target。典型身份要求如下：

| Target Kind | Canonical Identity 最低闭包 |
|---|---|
| Repository Revision | DataSource / Binding + repository native identity + 完整不可变 revision；短 SHA、branch 或 tag 只能作为解析输入 |
| Revision Comparison | 同一可比较来源中的 exact base revision + exact target revision + comparison contract |
| Source Object | exact parent revision / observation + source-native object identity，例如规范路径、文档 ID、表限定名或日志流身份 |
| Code Symbol / Method | exact revision + module / source object + language identity domain + fully qualified symbol + signature / overload discriminator |
| Endpoint / Config / Schema Element | exact owning source object / revision + Provider 或 Parser 定义的规范定位键；单独路径、名称或自由文本不构成身份 |
| Bounded Range / Window | exact source object / revision + canonical range、cursor 或 time window + ordering / watermark contract |

同名对象、重载方法、跨模块同名 Controller、多个短 Revision 前缀或无法证明唯一的动态对象都返回 `AMBIGUOUS` 或 `UNSUPPORTED`。Resolver 不通过扩大到整个 DataSource 来消除歧义；需要更大搜索范围时由上游在原授权边界内发起新的有界 Resolution Request，超出边界则重新授权。

## 4. SRC-OPERATION-01

### 4.1 Source Operation Intent 与 Request

Application Services 是 Source Integration 公开操作入口，并提交自包含的 `Source Operation Intent`，只表达：

- Intent ID、幂等键和可选的不透明 Causation Reference。
- DataSource ID / DataSource Definition Revision。
- Binding ID / Binding Definition Revision。
- Knowledge Engine 签发且 Purpose = `SOURCE_EXECUTION` 的 exact `KNW-SCOPE-STATE-ASSERTION-01`，以及 Source Integration 按 `SRC-BINDING-ELIGIBILITY-01` 返回的 exact Binding Eligibility Assertion / Digest；二者必须绑定同一 Scope、DataSource、Binding 和 Definition Revision。
- Capability Catalog Snapshot Reference，以及其中允许的 Source Operation Capability / Tool Contract Reference 集合。
- 所需来源操作语义、目标 Revision / Cursor / Time Window 和有界查询约束。
- 所需 Source Artifact Kind / 内容性质；任何 Derived 表示都通过独立 Artifact Processing Intent 请求。
- Execution Envelope、Data Classification 和本 Logical Operation 的 parent Resource Allocation。

Causation Reference 只用于关联，Source Integration 不解析其指向的用户任务、调查或更新语义。Intent 不指定可绕过 Provider 注册信息的实现类、自由工具名或任意查询。Source Integration 只能在冻结 Catalog 允许集合、冻结 DataSource 定义和自身 Provider Registry Snapshot 的交集中解析实际 Provider / Tool；不存在满足条件的确切版本时返回能力缺失，不能改读动态最新版本、扩大范围或让调用方临时发明 Tool。

解析成功后，Source Integration 构造不可变 `Source Operation Request`。每次 Request 固定：

- Source Operation ID、规范化 Intent Digest 和 Causation Reference。
- DataSource ID / DataSource Definition Revision。
- Binding ID / Binding Definition Revision。
- exact Scope State Assertion / Digest 与 Binding Eligibility Assertion / Digest；Request 只冻结调用方已经取得的资格闭包，不把它们升级为长期租约。
- Capability Catalog Snapshot、Tool Contract Inclusion / Activation Reference 和 Provider Registry Snapshot / Registration Revision。
- 不含 Secret 值的 Effective Provider Configuration Revision / Fingerprint。
- 实际 Provider / Tool Contract Version、解析依据和 Artifactization Profile Version。
- Artifact Identity Strategy Version。
- Provider 规范化参数、目标外部 Revision / Cursor / Time Window。
- 规范化 Binding Selector / 可执行 Context Constraint 和 Access Boundary Proof。
- Execution Envelope、Data Classification 和 parent Resource Allocation；具体外部调用只能使用按 §4.2 取得的 child Allocation。

任何外部或模型提议都必须先由调用方还原为上述受控 Intent，再由 Source Integration 从自身权威定义构造 Request。提议中的 Source、Scope、Provider、Tool、Revision、权限和预算都不具有执行效力。

### 4.2 分派资格、跨 Owner 握手与撤权

每次外部调用按三个可恢复边界执行，不存在覆盖 Application-owned Resource Ledger、外部 Secret / Permission Facility、Source Integration Repository 和外部 Provider 的共同事务：

1. **Source 资格准备。** Source Integration 验证 exact Scope State Assertion 的 Scope / Definition Revision / `SOURCE_EXECUTION` Purpose / Digest / `ELIGIBLE`，并按 `SRC-BINDING-ELIGIBILITY-01` 重读确切 DataSource / Binding Definition Revision、当前控制状态、Secret / Permission Reference、Effective Provider Configuration 和 Control Fence；输入 Binding Eligibility Assertion 必须与重读结果及 Scope Assertion exact 匹配。随后按冻结 Provider Contract重新规范化 Tool Target、Query、Range 与 Cursor，并机械证明其为 Binding Selector / Context Constraint 的子集，再生成稳定 Dispatch Attempt Key、Grant Request Digest 和预期 Control Fence；该阶段不越过外部分派边界。
2. **Allocation / PREPARED 握手。** Source Integration 按 `X-RESOURCE-ALLOCATION-01` 使用同一 Dispatch Attempt Key 从 Request 的 parent Allocation 幂等取得唯一 child Allocation。预留成功后，在 Source Integration 本地事务中建立或恢复唯一 `PREPARED` Dispatch Record，固定 Grant Request Digest、Definition / Provider / Tool / Configuration / Access Boundary / Fence 和 child Allocation，再调用 `BindDispatch` 绑定 Allocation。任一步崩溃都按同一 Key 查询和补做；没有本地 Record 且已经证明尚未分派时才可释放未绑定预留。不同 Digest 复用 Key 失败关闭。
3. **Source 本地 dispatch fence。** 在真正 I/O 前，Source Integration 本地 CAS 再次校验 DataSource / Binding Revision、Binding Eligibility Assertion、Scope Assertion 绑定、Control Fence、短期 Secret / Permission 资格和 PREPARED Record，签发不可复用 Execution Grant；Grant 固定两个 Assertion / Digest，并在同一 Source 本地事务把 Attempt 标记为 `DISPATCHED`。只有该事务成功后才执行外部 I/O；Attempt 结束后独立报告并结算真实消耗，失败、撤权竞态和迟到响应的消耗也不回滚。

资格准备后任何 Definition、权限或 Fence 漂移都使第三阶段失败，不得复用旧 Grant。Allocation 已预留但 Source 本地 dispatch fence 未越过时按握手恢复或受控释放；Source 已持久标记 `DISPATCHED` 后不能因 Application 超时或响应丢失猜测“未调用”。

撤权或取消后尚未分派的操作不得开始。已越过边界的在途 I/O 可以结束，但 Observation Result 必须同时记录 Grant Fence 和完成时观察到的最新 Fence；调用方依据显式状态决定能否继续使用。不存在覆盖调用方状态与 Source Integration 的分布式锁。

### 4.3 Dispatch、Observation 与终态 Result

三个层次不能混用：

| 对象 | 身份与可变性 | 含义 |
|---|---|---|
| Dispatch Attempt Record | 每个物理外部调用一个唯一 ID；越过分派边界后不可重用 | 固定 Execution Grant、Call ID、开始/结束状态和实际用量 |
| Observation Result | 每次已经发生的来源观察一条不可变记录 | 固定 Tool Outcome、Source Context、Artifact 和该次真实覆盖 |
| Source Operation Result | Logical Source Operation 终止时形成一个不可变聚合结果 | 引用全部 Dispatch / Observation，给出最终完成、部分、失败或取消状态 |

Logical Operation 在结束前只有内部 Operation State，不向外伪装为不可变终态 Result。终态 Source Operation Result 至少区分：

| 语义 | 作用 |
|---|---|
| Execution Status | 完成、部分完成、失败、取消、撤权竞态或预算耗尽 |
| Coverage | 实际扫描/读取范围、未读范围和 Provider 能证明的边界 |
| Pagination | 当前 Cursor、是否还有数据、排序稳定性和终止原因 |
| Truncation | 是否截断、截断位置和原始体积 |
| Definition Closure | DataSource / Binding Definition Revision、Catalog / Tool Inclusion、Provider Registry Revision、Provider Configuration Fingerprint、Provider / Tool / Profile Version |
| Dispatch / Observation | 全部物理调用、Execution Grant 与不可变 Observation Result 引用 |
| Source Context | 每次观察各自的 Revision、Environment、Time 等 Source Context Reference；不强制合并 |
| Artifact References | Artifact Reference 与确切 Source Observation Basis Reference；既包括 Observation-level，也包括满足 §4.4 的 Session-closure-level Source Artifact |
| Usage | 调用、扫描量、传输量、延迟和 Provider 配额 |
| Failure | 稳定失败类别和 Provider 原始诊断引用 |
| Execution Grant | 分派 Fence、完成 Fence 和撤权关系 |

Source Operation Result 是应用执行信息，不是 Artifact、Evidence 或正式知识。它可以支持 Application Services 判断执行与覆盖条件，但不能证明来源中的业务命题。每个 Source Artifact 必须引用判别联合 `SourceObservationBasisRef = SINGLE_OBSERVATION | CLOSED_READ_SESSION`；Observation Result 只列自身直接产生的 Artifact，Session 终止后形成的聚合 Artifact 由终态 Operation Result 关联，不能伪挂到单页 Observation。

### 4.3.1 取消、撤权与在途分派封口

取消和撤权只在 Source Integration 的权威 Operation Record 上推进 Dispatch Fence，不伪造已经发出的 I/O 被撤回：

1. `CancelSourceOperation` 或撤权处理原子禁止新 Dispatch，并冻结 `Dispatched-at-Fence Set`：所有已经持久记录“越过分派边界”的 Dispatch Attempt ID。
2. Set 外调用不得开始；Set 内每个 Attempt 必须先达到 `COMPLETED | FAILED | CANCELLED_BEFORE_IO | OUTCOME_UNKNOWN` 之一，Operation 才能封存终态 Result。
3. 有界等待结束仍无法确认外部结果时，Attempt 以显式 `OUTCOME_UNKNOWN` 进入 Result；不能把未知写成取消或失败。
4. Result 只纳入封存前已经完成且通过内容 / Fence 校验的 Observation 与 Artifact。Execution Status 明确区分 `CANCELED`、`REVOKED_WITH_INFLIGHT` 和 `PARTIAL`。
5. Result 封存后到达的响应写入绑定原 Dispatch Attempt 的不可变 `Late Dispatch Resolution Audit Record`；它不修改 Operation Result，不进入已冻结 Investigation，也不产生可由该 Operation 返回或用于 Evidence 的 Artifact。

重复取消返回同一 Fence / Result。调用方超时只查询 Operation State，不能在 Source Integration 尚未封口时自行构造 `CANCELED` Result。若业务确实要使用迟到响应，必须在当前权限下创建新的 Source Operation；不能把审计记录重新激活为旧 Operation 的 Observation。

### 4.4 SRC-READ-SESSION-01：分页、增量与持续来源

需要跨页、分批或读取持续来源时，Source Operation 建立不可变 Read Session Definition，至少固定：

- DataSource / Binding Definition Revision、Provider / Tool / Profile Version 和规范查询。
- 目标外部 Revision 或 Provider Snapshot Token；没有时明确记录读取一致性等级。
- 初始 Cursor、稳定排序键、每页边界和终止条件。
- 有界时间窗；日志/Trace 还要固定 Provider Watermark 语义、允许的迟到数据边界和回补策略版本。
- Provider 声明并通过 Conformance 的覆盖、Snapshot Read、分页和完整性能力。

每一页或批次使用独立 Dispatch Attempt 和 Observation Result。Session 终止时形成不可变 `Read Session Result / Observation Set`，固定：

- Read Session ID、Definition Digest 和终态状态。
- 按读取顺序排列的 Observation Result Reference，以及每项对应的 Artifact Reference。
- 实际输入/输出 Cursor 链、稳定排序校验、重复/缺口、截断和终止原因。
- 实际 Provider Snapshot Token / 一致性等级；持续来源还包括终态 Watermark、迟到边界和回补状态。
- 实际 Coverage、未读范围，以及基于冻结 Provider Capability / Conformance 得出的完整性结论。

Observation Set 具有自身稳定 ID，但仍是来源执行结果而非 Artifact 或正式知识。只有 Cursor 链连续、排序与截断条件满足、终止条件达到，并且 Provider 的一致读取/完整性能力足以支持目标语义时，终态 Session Result 才能声明相应范围完成。

如果 Provider 不支持 Snapshot Token 或等价一致读取，多页结果保留各页 Context，只能表达“在这些观察时刻看到了这些内容”，不能伪装成单一时点的完整快照。持续流必须切成有界窗口；`complete` 只相对于冻结的窗口、Watermark 和迟到数据政策成立。新的迟到事件或回补读取形成新的 Observation 和 Artifact，不改写旧记录。

零项 Query Observation Artifact 只能由已达到终态、具有封闭查询范围且满足上述完整性条件的 Observation Set 形成；其 Source Provenance 必须引用该确切 Read Session Result / Observation Set，并只能在稳定 Snapshot Token 或等价一致性条件下形成一个不扩大各观察条件的 Source Context。分页未完成、Cursor 断裂、一致性未知或无法形成该 Context 时禁止生成。

### 4.5 幂等与重试

- 同一调用方、幂等键和等价 Intent 解析为同一 Logical Operation；重复提交返回 Operation State 或唯一终态 Result。不同 Intent 复用同一键必须失败。
- 每次实际物理调用都创建新的 Dispatch Attempt ID。一个 Attempt 最多越过分派边界一次；结果不确定时先查询该 Attempt 的权威状态，禁止用同一 ID 再次调用外部来源。
- 暂态失败允许在同一 Logical Operation 内创建新 Dispatch Attempt，但不抹去先前 Attempt。若先前调用已经产生来源响应，则每次响应各自形成 Observation Result。
- 每个新 Dispatch Attempt（包括分页、回补和重试）必须从 parent Allocation 取得不重叠的 child Allocation 并独立结算；不得复用 Request 或上一 Attempt 的 Allocation。
- 固定不可变外部 Revision 可以按 Contract 复用等价 Artifact；日志、数据库当前值等可变来源的每次真实观察仍形成独立 Source Context 和 Observation Result，即使 Payload 最终去重。
- 改变 DataSource / Binding Revision、规范查询、目标外部 Revision、时间窗、Profile 或所需 Artifact Kind 会改变 Request 语义，必须创建新的 Logical Operation；分页 Cursor 推进只在同一冻结 Read Session 内进行。

## 5. SRC-CONTEXT-01：Source Context

Source Context 是 Source Integration 对一次来源观察条件的不可变表达，至少固定：

- DataSource ID / DataSource Definition Revision、Provider Context Vocabulary Version 和 Canonicalization Version。
- 来源原生 Subject / Locator。
- 可观察 Environment、Version、Time、Deployment 等 Term。
- Event Time、Observation Time 和处理时间的明确区分。
- Term 的原始值、规范值和来源定位。
- 确切 Source Observation Basis；外部内容 Revision 与 DataSource / Binding Definition Revision 分开保存。

Source Context 不建立跨来源关系，不把 Branch 当前值解释为过去值，也不由目标 Scope 或 Snapshot 改写。无法观察的维度不制造 `UNKNOWN` 正式 Term，只在 Result 中记录未观察到的维度。

`Source Context Reference` 固定：

- DataSource ID。
- 不可变 Source Context ID。
- Provider Context Vocabulary Version。
- Canonicalization Version。

`Source Observation Basis` 是判别联合：

- `SINGLE_OBSERVATION`：引用一个确切 Observation Result。
- `CLOSED_READ_SESSION`：引用一个满足 §4.4 完整性要求的终态 Read Session Result / Observation Set，并保留其有序成员 Observation 及各自 Source Context Reference。

Session 型 Context 只有在冻结 Snapshot Token 或等价一致性契约下，才能把成员 Context 规范化为不扩大条件的组合表达；无法证明组合合法时不得生成单一 Session Context 或基于它的聚合 Source Artifact，只保留各 Observation / Artifact。

Source Integration 从 Tool Outcome 与平台分派记录重建 Context，验证 Provider 词汇，规范化 Term，并以 DataSource、Definition Revision、Subject、规范表达、Vocabulary / Canonicalization Version、Basis 类型和确切 Observation / Observation Set Reference 形成身份键，原子 get-or-create。Repository 必须持久化完整表达、Basis 和 Session 成员引用，不能只保存摘要或哈希。

`ResolveSourceContext` 验证引用完整、版本可解释和当前数据访问权限；不会把 `latest` Provider 词汇套用到旧 Context。只要 Artifact 或 Lineage 仍引用该 Context，其身份、完整表达和最小来源依据就不能删除。下游消费者可以据此在目标 Knowledge Schema 下创建自身 KnowledgeContext；共享值格式不表示共享 Repository、写入权或跨来源语义关系。

## 6. SRC-ARTIFACT-01：中立 Artifact 外壳

### 6.1 Artifact 的成立条件

只有能够承载后续知识构建信息的有界结果才形成 Artifact。以下结果不单独成为 Artifact：

- 连接成功、权限校验、心跳、分页状态和错误码。
- 没有固定查询条件、读取一致性和覆盖边界的普通空结果；它只能说明此次操作未返回内容，不能证明对象不存在。
- Tool 调用计划、模型思考过程和 Investigation 控制状态。
- 只用于运行计费、延迟和覆盖的统计。

若 Provider 能把来源返回的“零项观察”固化为不可变 `Query Observation Artifact`，它可以成为 Source Artifact。该 Payload 必须至少包含确切查询/过滤表达式、目标对象与 Revision 或隔离级别、封闭范围、排序与分页终止状态、返回数量、观察时间，以及 Provider 可以证明的完整性条件。它承载的是“在这些明确条件下来源返回零项”这一直接观察，不自动证明某个跨范围对象绝对不存在。

仅存在 Operation 成功状态、客户端计数器或不完整分页时不得生成该 Artifact。Source Integration 只负责固化来源观察和证明条件；它能否形成否定 Evidence、支持何种命题及命题范围，仍由 Evidence 与 Fact 主题决定。

### 6.2 稳定外壳

所有 Artifact 使用同一个带 `Artifact Class` 判别字段的逻辑外壳，但 Payload 和 Provenance 分支保留差异。公共字段为：

| 语义 | 约束 |
|---|---|
| Artifact ID | 平台稳定、不透明身份；Artifact 创建后不可修改 |
| Artifact Class | `SOURCE` 或 `DERIVED` |
| Artifact Kind / Schema Version | Provider 或 Processor 命名空间内的内容类型和解释版本 |
| Payload Reference | 内联内容、对象存储、外部不可变引用或最小快照；不要求统一物理位置 |
| Payload Schema / Media Type | 解释 Payload 的版本化契约 |
| Content Digest | 对实际 Payload 或受控内容快照计算；算法版本显式 |
| Data Classification | 按版本化分类政策计算的有效等级；控制持久化、模型可见性和返回范围 |
| Retention State | Payload 可用性、保留原因和期限；不改变 Artifact 身份 |

Class-specific Provenance 不能互相伪造：

| Artifact Class | 必须 Provenance | 禁止的伪装 |
|---|---|---|
| SOURCE | 恰好一个 DataSource ID / Definition Revision、Binding ID / Definition Revision、Provider Configuration Fingerprint、Source-Native Identity、Source Context Reference，以及确切 Source Observation Basis、Provider / Tool / Profile / Identity Strategy Version；Basis 是一个 Observation Result，或满足 §4.4 的终态 Read Session Result / Observation Set | 不能用 Processor Execution、非终态 Session 或模型结果冒充外部观察 |
| DERIVED | 规范化 Parent Artifact Reference、每个父的 Range / Context 映射、Artifact Lineage 和 Processing Execution / Transformation Reference | 不得杜撰单一 DataSource、Source-Native Identity、Source Context 或 Source Operation Acquisition |

多父 Derived Artifact 通过每条 Lineage Edge 保留父 Context；外壳不生成声称父 Context 彼此相容的合并 Context。中立外壳统一身份、Payload 引用和追溯方式，不统一内容结构或把多来源压成单一来源。下游消费者根据 Artifact Kind / Schema 选择已注册解析能力，不能把任意 Provider Payload 当作通用 JSON 猜测。

Source Artifact 的有效 Data Classification 是 Execution Intent、DataSource / Binding、Tool、来源原生标记与当前分类政策的最严格合并结果。Derived Artifact 默认至少继承全部父输入的最严格合并结果；存在不可比较等级时保留组合限制并失败关闭模型发送与外部返回。只有独立、显式激活且可审核的 Sanitization / Declassification Contract 能提出降级结果，并须记录原分类、变换、审核和政策版本；Provider、Processor 或模型自报不能降低等级。

### 6.3 Artifact 身份与去重

Source Artifact 与 Derived Artifact 使用不同身份闭包：

- Source Artifact Identity 由 Provider 的版本化 Identity Strategy 产生，至少包含 DataSource ID / Definition Revision、Source-Native Identity、Source Context / 外部 Revision、Artifact Kind / Payload Schema、Provider / Tool / Artifactization Profile / Identity Strategy Version。
- Derived Artifact Derivation Key 由 Processor 按 Transformation Contract 规范化，至少包含父 Artifact 引用及输入 Range、父顺序语义、Transformation Contract、Capability / Strategy / Parser / Model / Configuration Version，以及输出 Kind / Schema。Source Roots 与 Context 只能从 Lineage 推导。
- 通过 Conformance 证明为确定性的 Transformation，可以按 Derivation Key 与 Content Digest 原子复用；同一 Key 返回不同 Digest 时隔离为 `PROCESSING_NONDETERMINISTIC_CONTRACT_VIOLATION`。
- 未声明确定性或使用随机模型的 Transformation，每次成功 Processing Attempt 产生包含 Attempt ID 与 Content Digest 的新 Artifact 身份；不能仅凭相同输入和模型名假定输出可复用。

不同 Source、Revision、时间窗、Profile、Transformation 实质版本或语义 Kind 不得只因 Content Digest 相同而合并成一个 Artifact。

同一完整逻辑身份与 Content Digest 的并发创建执行原子 get-or-create。相同 Source Artifact 逻辑身份出现不同 Digest 时不得覆盖：

- 如果来源是可变对象且 Context / Revision 不完整，当前操作失败并要求补齐观察条件。
- 如果 Provider 声明同一不可变 Revision，却返回不同内容，记录 `SOURCE_REVISION_INCONSISTENT` 并隔离结果。

Content-addressed 存储可以复用相同字节，但 Artifact 身份和来源关系仍分别保留。逻辑 Artifact 淘汰与物理 Content GC 是两个不同决定：Artifact 进入 `EVICTED` 只移除该 Artifact 对完整 Payload 的可用性，不授权删除共享字节。

每个物理 Content Node 必须具有由 Artifact、Range、Lineage Replay Closure、Staging / Recovery 和保留策略组成的可重建完整 Owner / Reachability Set。物理删除只能在统一 Source Retention Fence 内，依据覆盖全部 Owner Namespace 的完整性水位证明所有逻辑 Owner 均已退出且没有 Lease、Hold、Reservation、恢复或审计保护后执行。缓存引用计数、单个 Artifact 的 Owner 数量、某条 Lineage 退出或一次扫描未命中都不是删除证明；无法证明集合完整时保留字节或将该 Content Node 隔离为待对账状态。

## 7. Source Artifact

Source Artifact 直接承载 Connector 从外部 DataSource 观察到的内容，生成过程不使用模型改写内容。模型可以规划读取范围，但不能生成 Source Artifact Payload。

典型表示不是强制全局粒度：

| 来源 | 可用 Source Artifact 示例 | 必须保留 |
|---|---|---|
| Git / Code | 某 Commit 的文件、Commit 元数据、两个 Revision 的 Diff | 仓库、不可变 Revision、路径、字节/文本哈希 |
| DB | Schema 观察、带确切查询与读取一致性信息的结果批次或零项 Query Observation | 实例身份域、观察时间、Schema/事务标记、查询范围与分页 |
| Docs | 页面或文档 Revision、附件、版本化内容块 | 空间、文档身份、Revision、定位和原文 |
| Logs | 查询与时间窗限定的不可变事件批次、零项 Query Observation 或原生日志段 | 日志源、查询范围、Event/Observation Time、Cursor 和覆盖 |
| Trace | 一个 Trace 或受界 Span 批次 | Trace/Span Identity、采样信息、时间和服务 Context |
| Deployment | Manifest、Image Metadata、发布记录 | 集群/环境命名空间、观察时间、原生 Revision |

DataSource 本身、数据库连接、持续日志流句柄和“整个系统”不是 Artifact。对于持续来源，每个 Artifact 必须是可复核的有界观察；新的内容形成新 Artifact，不原地追加到旧 Artifact。

## 8. SRC-DERIVED-ARTIFACT-01

Derived Artifact 是 Artifact Processing 对一个或多个 Artifact 的显式加工结果，可以作为解析缓存、检索结构、模型输入切片或 Candidate 发现材料。它不是 Agent 私有思考过程。

### 8.1 Transformation Class

| Class | 示例 | Source Integration 可声明的机械性质 |
|---|---|---|
| LOSSLESS | 编码规范化、解压、无损格式转换 | 字节/值语义保持、可回放、输入输出映射完整 |
| LOCATOR_PRESERVING | 文件分段、语法树、结构索引，能够精确映射回单一 Source Artifact | Locator 可逆、Source Root 数量和可回放范围 |
| SEMANTIC_TRANSFORMING | 模型摘要、解释、分类、实体/关系提议、自然语言重写 | 只声明输入来源与变换版本，不声明语义保持 |
| AGGREGATING | 多文件、多来源拼接、统计、搜索索引、联合摘要 | 父集合、聚合函数和 Source Root Cardinality |

Source Integration 只记录 Transformation Fidelity、Locator Reversibility、Source Root Cardinality、Replayability 和相应 Conformance / Evaluation Reference，不声明下游 Evidence Eligibility。根据概要架构，语义变换与多源聚合结果不能直接证明 Fact；是否接受其他 Derived Artifact 由下游 Evidence Contract 基于上述可机械复核性质判断。

### 8.2 SRC-PROCESSING-01：加工执行

Application Services 通过与 Source Operation 分离的 `Artifact Processing Intent` 请求加工。Intent 固定不透明 Causation Reference、Parent Artifact / Range、目标 Artifact Kind / Payload Schema、Transformation Contract、Capability Catalog Snapshot 与其中 exact Capability / Strategy、Execution Envelope、Data Classification 和 Resource Allocation。Catalog Mode 必须明确为 `PRODUCTION`（exact Activation Decision）或 `EVALUATION_ONLY`（exact Evaluation Run / Qualification Proof）；Source Integration 不根据目标 Kind 或 Profile 隐式选择 Strategy。

Source Integration 验证父 Artifact、分类、Catalog / Activation 与 Strategy Contract 后，为每个加工步骤构造不可变 `Artifact Processing Request`，至少固定：

- Processing Execution ID / Attempt ID 和可选不透明 Causation Reference。
- 规范化 Parent Artifact Reference、每个输入 Range 和父顺序语义。
- 目标 Artifact Kind / Payload Schema 与 Transformation Contract Version。
- Capability Catalog Snapshot 中的确切 Capability / Strategy Reference，以及 `PRODUCTION Activation Decision | EVALUATION_ONLY Qualification Proof`。
- Parser、Prompt、Model Selection Policy、配置和实质参数引用。
- Execution Envelope、Model Execution Context、Data Classification 和 Resource Allocation。

Artifactization Profile 只能声明兼容的 Transformation Contract / Capability Contract 和默认粒度，不能选择、激活或静默替换 Strategy。Source Integration 在执行前校验 Strategy 确实实现目标 Contract；配置、父输入、输出 Kind 或实质版本变化都创建新 Request / Attempt。

`Artifact Processing Result` 与 Derived Artifact 分离，记录 Catalog Mode、执行状态、真实模型/Parser 指纹、post-call eligibility、用量、失败、Proposal 和实际 Artifact Reference。确定性 Processor 可以直接产生受控 Payload；模型或其他不可信 Strategy 只产生 Derived Artifact Proposal，Source Integration 按冻结 Request 重建身份、父引用、Lineage、Context 映射、Digest 和平台字段。

只有 `PRODUCTION` 且 post-call eligibility 通过的执行可以创建 / 注册 Derived Artifact、Lineage 和可供下游读取的 Artifact Reference。`EVALUATION_ONLY` 复用同一 Processor / Gateway 路径，但输出只写 Evaluation Run 隔离区并返回 Evaluation Output Reference；不得注册生产 Artifact、进入 Artifact Read Handshake、Evidence Materialization 或生产缓存。这样首次评测无需伪造 Activation，也不会污染生产对象。

Processing Result 只返回 Application Services；成功时可以包含一个或多个 Derived Artifact Reference，失败不能回退为由 Source Integration 自选其他 Strategy。Source Operation Result 不混入 Processing Result；Application Services 可以对新取得或既有 Artifact 独立发起加工。

Artifact Processing 是 Source Integration 所有权边界内的受控读写：冻结 Processing Request、Capability / Strategy、Parent Range、Data Classification、Execution Grant 和本地提交事务共同构成其授权闭包，不通过面向跨模块消费者的 Artifact Read Package / ConfirmArtifactUse。只有 Derived Artifact Payload 后续跨模块交付并形成外部持久依赖时，才必须进入 §11 的 Read / Use Handshake。Processor 仍不得绕过 Model Gateway、分类政策或 Lineage。

### 8.3 模型辅助加工

- 对日志、文档等非结构化内容，可以使用 Model-Primary / Hybrid Artifact Processing Strategy。
- 原始有界内容必须先形成 Source Artifact；模型输出只能形成 Derived Artifact Proposal。
- Source Integration 从冻结 Processing Request 重建父 Artifact、Lineage、Context 映射、实际模型指纹、Content Digest 和平台控制字段。
- 模型摘要、解释和语义结构化结果默认属于 SEMANTIC_TRANSFORMING，不能直接成为 Fact Evidence 或 Inference 前提。
- 模型不可用或输出 Contract 无效时，Source Artifact 仍有效；只返回加工失败，不能伪造 Derived Artifact。

确定性解析器适合语法、格式和位置可机械复核的来源；模型适合非结构化语义理解。是否选择模型由版本化 Capability Strategy 和 Evaluation 决定，不按文件扩展名永久硬编码。

## 9. SRC-LINEAGE-01：Artifact Lineage

每条 Lineage Edge 固定：

- Child Artifact Reference。
- 一个或多个 Parent Artifact Reference。
- Transformation Class、Capability Contract、Strategy / Parser / Model Fingerprint 和配置版本。
- 输入 Range 与输出 Range 的定位映射。
- Execution / Model Call Reference 和 Content Digest。
- Transformation Fidelity、Locator Reversibility、Source Root Cardinality、Replayability，以及支持这些机械性质的 Conformance / Evaluation Reference。

Lineage 形成不可变 DAG，禁止循环。Derived Artifact 不拥有一个覆盖父条件的新 Source Context；多父输入通过各 Edge 保留每个父的独立 Context，不能由 Processing 自动合并未知关系或声明更宽条件。

Lineage 只证明“由哪些输入通过哪个加工产生”以及哪些机械性质已被验证，不证明加工结果的业务语义正确，也不作出下游知识准入决定。

## 10. SRC-ARTIFACTIZATION-PROFILE-01：粒度策略

平台不规定所有 DataSource 生成同一内容结构或同一粒度。每个 Provider 通过版本化 Artifactization Profile 定义：

- Source-Native Identity 与不可变观察边界。
- 一个 Artifact 的最大/目标 Payload、分页和分段规则。
- Source Artifact 与 Derived Chunk / Index 的关系。
- 内容变化如何产生新身份、复用或失效加工缓存。
- Source Context 和完整性/覆盖能力。
- 默认 Payload Retention Class 与数据分类。
- 兼容的解析 / Transformation Capability Contract 及可机械验证的 Fidelity / Locator 性质。

Profile 必须满足：

1. Artifact 是有界信息载体，可定位、可哈希、可独立引用。
2. Source Context 足以区分会改变内容含义的 Revision、Environment 或 Time。
3. 大内容可以通过 Payload Reference 和 Derived 分段按需读取，不要求一次送入模型。
4. 来源变化尽可能局部生成新 Artifact，但不能为减少处理量而牺牲观察完整性。
5. 同一 Profile 在相同来源观察上产生稳定身份和 Lineage。

Git 文件、DB 查询批次、日志时间段、Trace 和文档 Revision 可以采用不同 Profile，却仍产生统一 Artifact 外壳。

### 10.1 全范围与按需调查

Artifact Contract 同时支持调用方的三种访问模式：

- Exhaustive：在显式 Binding Selector 与有界终止条件内枚举并处理目标范围。
- Targeted：按调用方给出的有界操作意图逐步搜索、读取和比较。
- Incremental Reuse：按确切外部 Revision、Identity Strategy 和 Processing Closure 复用明确未变化的 Artifact 或加工结果。

三者不改变 Source Integration 的契约、Artifact 身份或可信边界；Source Integration 不解释调用方为何选择某种模式。空 Selector、空 Include 条件或预算耗尽不能隐式解释为“读取整个来源”或“覆盖完整”。

是否为某个 Provider 选择文件、方法、页面、事件或批次粒度，只有在真实项目规模、变化频率、定位精度、模型预算和存储放大之间存在会影响 Profile 契约的实质不确定性时，才启动 `DVR-*`；不能把某次 Demo 的方便结构直接定为平台全局粒度。

## 11. SRC-ARTIFACT-ACCESS-01：授权读取与局部保护

Artifact Reference 只是定位引用，不是凭证。Source Integration 必须通过显式 Contract 执行授权读取，并把读取时观察到的确切内容与上下文固定下来。

### 11.1 请求与握手身份

`OpenArtifactRead` 至少固定：

- 目标 Artifact Reference、目标 Range / Locator Requirement 和所需 Lineage Closure 深度。
- 下游 Materialization Reference、Request Digest、Artifact Read Requirement ID 和 Purpose。
- 调用方 Execution Envelope、身份、租户 / Scope、能力声明和数据分类上限。
- 是否允许从归档恢复；恢复的成本和等待上限。
- 请求所需的最小字段、原始字节范围或结构化观察，不允许用“尽可能多”作为读取边界。

稳定的 `Logical Artifact Read Key` 由下游 Materialization Reference、Request Digest、Artifact Read Requirement ID、Artifact Reference、Range 与 Purpose 共同决定。每次实际打开还必须携带 `Artifact Read Attempt ID / Idempotency Key`：同一 Attempt 与相同 Digest 返回原 Package 或终态；同一 Attempt 被不同 Digest 占用时返回 `IDEMPOTENCY_CONFLICT`。`MANAGED_EVICTION` 中 Guard 过期会终止原 Materialization；新的 Materialization 产生新的 Logical Read Key / Attempt，不能迁移旧 Package、Read Protection 或 Staged Manifest。`NO_EVICTION` 不产生 Guard，但也不能跨 Materialization 复用旧 Package。

### 11.2 Artifact Read Package

Source Integration 先完成确定性授权、Artifact 状态与分类检查，再展开实际 Lineage Closure，并返回不可变 `Artifact Read Package`。Package 至少包含：

| 字段 | 语义 |
|---|---|
| Package ID / Logical Read Key / Read Attempt | 本次逻辑读取与实际打开的稳定身份 |
| Artifact / Range | 被读取的确切 Artifact 与边界 |
| Closure Manifest / Digest | 实际依赖的 Artifact 闭包 |
| Content / Structured Observation Digest | 返回内容或结构化观察的规范摘要 |
| Context Snapshot | SourceContext 及有效 Context 观察 |
| Classification / Grant Reference | 生效的数据分类和授权依据 |
| Read Protection | 判别值 `NOT_REQUIRED_NO_EVICTION`，或仅由 Source Integration 管理的有界 `MANAGED_EVICTION` Guard / Revision |
| Package Outcome | `OPENED | ARCHIVE_RESTORE_REQUIRED | EVICTED | UNAVAILABLE | DENIED` |

Source Integration 可以返回受控内容流、最小 Payload 或规范化结构化观察，但必须保证 Content Digest 覆盖 Evidence 将要固定的全部观察。模型只能在授权 Package 内解释内容，不能把不可访问的源内容写入输出。

### 11.3 局部读取保护

读取保护由当前 `SRC-RETENTION-01` Strategy 决定：

- `NO_EVICTION`：平台没有 Payload Archive / Evict / Physical Cleanup 写入口，读取期间不存在平台内并发淘汰。Source Integration 在本地读取事务中验证 Closure 全部 `AVAILABLE` 后，在 Package 的 Read Protection 字段返回判别值 `NOT_REQUIRED_NO_EVICTION`；它保持下游握手形状稳定，但不创建 Guard Record、后台清理器或 Store History 状态机。首个 Local Git / 单库切片使用该最简单 Strategy。
- `MANAGED_EVICTION`：仅当平台确实启用可与读取并发的 Archive / Evict 时使用。Source Integration 在返回 Package 前，必须在自身的 Source Retention Coordination Record 上取得覆盖实际 Closure 的有界 `Local Read Guard`。

`MANAGED_EVICTION` 的 Guard 只解决“正在读取时内容被删除”的本地竞态：

1. Source Integration 在本地事务或 CAS 中验证目标仍可读并登记 Guard。
2. Payload 淘汰必须在同一权威记录上证明不存在有效 Guard，才能提交状态变化。
3. Evidence Materialization 在 Guard 有效期内完成确切内容读取和最小快照持久化。
4. Materialization 完成、失败或超时后释放 Guard；Guard 不转化为跨模块长期 Hold。
5. 调用方在 Guard 过期后仍未完成使用确认时，必须关闭当前 Materialization，并从新的 Read Requirement / Logical Read Key 重新开始，不能沿用旧内容假设。

当前不引入 Source Store Incarnation、跨 Owner Retention Epoch、Recovery Attestation、Store History 状态机或长期 Hold 所有权协议。若未来实际部署允许持久历史被不连续替换且现有 ACID / 对象存储一致性契约无法判定连续性，必须先建立专题详细设计和 Conformance，再启用 Store 级隔离；本主题不预建 `SRC-STORE-AVAILABILITY` 对象、表或空状态。

### 11.4 使用确认

读取完成后，下游通过 `ConfirmArtifactUse` 提交 Artifact Use Requirement ID、原 Artifact Read Requirement ID、Logical Read Key、确切 Read Attempt / Package、Read Protection（`NOT_REQUIRED_NO_EVICTION` 或 Guard Revision）、实际 Closure Digest、使用的 Range / Locator、Staged Materialization Manifest Digest、Purpose、Classification 与 Content Digest。Source Integration 只做来源侧的一致性校验，并签发不可变 `Artifact Use Confirmation`。

Use Confirmation 证明“下游使用的是哪个被授权 Package”，不证明正式 Evidence 已提交，也不提供长期 Payload 可用性。`MANAGED_EVICTION` 下 Knowledge Engine 必须在结束 Local Read Guard 前，把正式复核所需的最小确切观察保存到 Evidence Snapshot；`NO_EVICTION` 下仍须在本轮 Materialization 提交前保存同样的自包含快照，不能把“当前不淘汰”解释为允许正式 Evidence 长期依赖 Source Payload。无法在政策允许范围内保存足够内容时，本轮 Materialization 失败关闭。

## 12. SRC-RETENTION-01：持久化与淘汰

### 12.1 持久化边界

Retention Strategy 是 Source Integration 部署配置的精确版本化选择：当前最小 Strategy 为 `NO_EVICTION`，只允许创建和读取 Payload，不注册 Archive / Evict / Physical Delete 命令；`MANAGED_EVICTION` 只有在保留成本形成真实需求并完成对应 Conformance 后启用。选择 Strategy 不改变 Artifact 身份、Evidence 自包含要求或 Source Integration 所有权。

必须落地：

- Artifact 元数据、Content Digest、SourceContext、版本 / 时间观察、分类和 Artifactization Profile。
- ArtifactLineage 与必要 DerivedArtifact 的确定性输入 / 输出摘要。
- Access / Use Confirmation 的最小审计记录和幂等终态。
- Payload Location、Payload State；仅 `MANAGED_EVICTION` 额外持久化 Source Retention Coordination Record。

Payload 是否本地长期保存由 Connector 类型、来源可重放性、法规与成本策略决定，不要求统一复制全部原始内容。

### 12.2 Payload 状态

Contract 可以表达以下状态，但 `NO_EVICTION` 实现只产生 `AVAILABLE`，以及真实存储故障时的 `UNAVAILABLE`；`ARCHIVED / EVICTED` 只由启用的 `MANAGED_EVICTION` Strategy 产生：

- `AVAILABLE`：可直接读取。
- `ARCHIVED`：需显式恢复。
- `EVICTED`：内容已按策略淘汰，仅保留元数据与 Digest。
- `UNAVAILABLE`：来源暂不可访问且未确认已淘汰。
这些状态只描述单个 Payload 的内容可用性，都不改变已经自包含落地的 Evidence，也不能被模型改写。当前不另建 Source Store 整体状态；真实存储不可用由 Repository / Payload 读取失败明确返回。

### 12.3 本地淘汰规则

Source Integration 独占 Payload 状态和淘汰决定。以下规则仅在 `MANAGED_EVICTION` 启用时适用；`NO_EVICTION` 不实现淘汰入口或协调记录：

- 存在有效 Local Read Guard 的 Closure 不得淘汰。
- DerivedArtifact 尚未完成且重放仍依赖父 Artifact 内容时，不得淘汰其必要父内容。
- 法规、审计或 Connector Policy 要求保留时，不得提前淘汰。
- 淘汰通过同一 Source Retention Coordination Record 的 CAS / 事务完成；检查与状态变化不能分离。
- 淘汰后保留 Artifact 外壳、Digest、Lineage、Context、Policy Decision 与不可复用幂等 Tombstone。
- `ARCHIVED` 的恢复是显式操作；恢复失败不能静默回退为猜测内容。

按来源类型可采用不同策略：

- Git：优先保留 Commit / Blob 引用与必要缓存，仓库可重放时不复制全部文件正文。
- DB：保留受控查询结果或快照位置；不能重放的结果按政策保存最小必要字节。
- 日志 / Trace：采用窗口、分层存储与聚合；Evidence 形成后不依赖原日志继续在线。
- 文档：保留版本、对象引用、Digest 与必要文本快照。
- DerivedArtifact：保留派生定义、父引用、参数、模型 / 工具版本与结果摘要；正文按重放成本决定。

### 12.4 当前不启用的跨存储长期保留

当前 `External Artifact Retention Dependency Strategy = DISABLED`：

- 正式 Evidence 必须保存可独立复核的最小快照，并声明 `NOT_REQUIRED_SELF_CONTAINED`。
- Snapshot Publication 不取得 Artifact Hold、Publication Reservation 或跨存储 Release Confirmation。
- Source Payload 后续淘汰不使已发布 Fact / Inference 失效；其复核依据是 Evidence Snapshot 与 Source Provenance。
- Source Integration 不维护 Evidence / Snapshot Owner Set，也不读取 Knowledge Engine 的清理状态。

只有真实数据政策明确禁止保存足够 Evidence Snapshot，且正式知识必须长期依赖外部 Payload 时，才启动专题设计。届时需要先验证容量、法规、恢复和所有权需求，再定义最小的跨 Owner 保留 Contract；本文件不预建相关对象、表、状态机或后台服务。

## 13. 失败语义

| 类别 | 处理 |
|---|---|
| PROVIDER_NOT_AVAILABLE | 不选择替代 Provider 猜测；返回能力缺失 |
| TARGET_RESOLUTION_IDEMPOTENCY_MISMATCH | 同一 Owner Key 对应不同 Resolution Request；拒绝且不执行新 Resolver Step |
| TARGET_RESOLUTION_OUTCOME_PENDING | 已 dispatch Resolver Step 的 Outcome 暂不可证明；不封存 Target Receipt，按原 Attempt 恢复 |
| SOURCE_TARGET_NOT_FOUND | 返回不可变 NOT_FOUND Receipt；不降级为相近目标 |
| SOURCE_TARGET_AMBIGUOUS | 返回有界候选和所需消歧字段；不自动选择第一项或扩大范围 |
| SOURCE_TARGET_OUT_OF_SCOPE | 不解析、不读取；调用方不能把解析失败改写为授权 |
| SOURCE_TARGET_UNSUPPORTED / RESOLUTION_FAILED | 返回明确 Receipt 与诊断引用；不降级为自由文本目标 |
| SCOPE_ASSERTION_INVALID / BINDING_ELIGIBILITY_STALE | `SOURCE_EXECUTION` Purpose、Scope / Binding Revision、Digest、Eligibility 或当前 Source 资格失配；不建立 Dispatch Grant |
| BINDING_INVALID / REVISION_CONFLICT | 不执行来源调用；调用方使用新定义重建 Intent |
| ACCESS_BOUNDARY_UNPROVEN | Tool 参数无法证明位于 Binding Selector / Constraint 内；失败关闭 |
| EXECUTION_REVOKED | 不分派新调用；标记在途结果的 Fence 关系 |
| ACCESS_DENIED / SECRET_UNAVAILABLE | 失败关闭，不记录 Secret 值 |
| SOURCE_QUERY_INVALID | 不自动扩大查询范围 |
| SOURCE_UNAVAILABLE / RATE_LIMITED | 仅按 Tool Policy 和 Allocation 有界重试 |
| SOURCE_PARTIAL / TRUNCATED | Result 明确未完成范围；不能宣称覆盖 |
| SOURCE_REVISION_INCONSISTENT | 隔离 Artifact，不覆盖已有不可变记录 |
| PAYLOAD_TOO_LARGE | 保留 Source Artifact 引用，按 Profile 分段或请求更窄范围；不静默截断 |
| ARTIFACT_SCHEMA_UNSUPPORTED | Artifact 可以保留，Knowledge Engine 不得猜测解析 |
| PROCESSING_FAILED | Source Artifact 保持有效；不产生伪 Derived Artifact |
| LINEAGE_INVALID / CYCLIC | 拒绝 Derived Artifact |
| PAYLOAD_UNAVAILABLE | 明确返回追溯限制，不伪装内容为空 |
| ARTIFACT_READ_REVOKED | 不签发新 Read Grant；标记已经打开的有界读取 Fence 关系 |
| LINEAGE_READ_CLOSURE_INCOMPLETE | 不返回部分闭包；调用方不能继续下游回放 |
| ARTIFACT_USE_UNCONFIRMED | 不允许形成正式 Evidence；重新取得 Package 或失败 |
| LOCAL_READ_GUARD_EXPIRED | 仅 `MANAGED_EVICTION`：停止使用未完成内容，关闭当前 Materialization 并以新 Attempt 从 Prepare 开始 |
| SOURCE_OPERATION_DRAINING | 已禁止新 Dispatch；等待冻结集合封口或记录明确 OUTCOME_UNKNOWN |
| SOURCE_RETENTION_CONFLICT | 仅 `MANAGED_EVICTION`：读取保护或淘汰只有一个本地 CAS 成功；失败方按当前状态重试 |
| EVIDENCE_SNAPSHOT_INSUFFICIENT | 不形成正式 Evidence；缩小范围、补充允许保存的观察或终止调查 |

## 14. 可观测性与敏感信息

- 传播 Operation、Provider、Tool、Binding、Artifact、Capability、Model Call、Execution Grant 和资源关联。
- 记录真实覆盖、分页、截断、扫描量、传输量、延迟、重试以及原始 Usage / Charge / Meter Reference；Source Integration 不计算也不回写横切 Telemetry 的 Cost Valuation，查询展示时可由 Telemetry 自身索引关联。
- Credential 只以 Secret Reference 进入连接边界，绝不进入 Artifact、模型输入、Lineage 或 Telemetry。
- DB Row、Log、Trace 和文档 Payload 按 Data Classification 裁剪、加密和保留；模型加工必须通过 Model Gateway 数据门禁。
- Telemetry 与 Source Operation Result 不成为 Artifact 或正式知识。

## 15. 拟议不变量

1. Source Integration 的知识边界终点是 Artifact；不得生成 Evidence、Entity、Fact 或 Inference。
2. Connector Provider 管理一种来源类型和能力；Connector Tool 只执行一个有界、只读来源操作。
3. 所有来源统一 Artifact 外壳，不统一 Payload 结构和全局粒度。
4. 只有信息载体形成 Artifact；执行、覆盖和失败状态留在 Source Operation Result。
5. Source Artifact 直接来自外部观察，模型不能生成或改写其 Payload。
6. Derived Artifact 必须保留无环 Lineage；Lineage 证明加工来源，不证明语义正确。
7. 模型摘要、解释、多源聚合和其他语义变换不能直接成为 Fact Evidence 或 Inference 前提。
8. 一个可直接作为 Evidence 锚点的 Derived Artifact 必须单一 Source Root、定位可回放且 Transformation Contract 已验证。
9. Source Artifact 保留自身 Source Context；Derived Artifact 通过每条 Lineage Edge 保留父 Context，不被任何调用方状态改写或伪合并。
10. 可变日志/DB 等来源的每次真实观察形成新的 Observation Result / Context / Artifact，不原地改写旧记录。
11. 普通空结果、截断、分页未完成和预算耗尽不能证明来源中对象不存在；只有固化了确切封闭范围与完整性条件的 Query Observation Artifact 才能进入否定 Evidence 判断。
12. Artifact Payload 可以淘汰；Artifact 外壳、Digest 与 Lineage 保留，正式 Evidence 的最低可复核内容由其自身 Snapshot 承担。
13. Artifact Identity 与字节去重分离；相同 Digest 不能抹去来源、Revision 或 Context 差异。
14. Provider 扩展不得创建新的正式知识权威或绕过 Model Gateway、Application Services 和下游知识准入边界。
15. Source Artifact 和 Derived Artifact 使用不同且版本闭合的身份规则；多父 Derived Artifact 不伪造单一来源 Provenance。
16. Artifact 读取必须经过当前授权与明确 Read Protection；`NO_EVICTION` 不创建 Guard，只有启用 `MANAGED_EVICTION` 时才使用有界 Local Read Guard。Core Capability 之间不直接调用。
17. Artifact Data Classification 按全部适用输入取最严格有效结果；任何降级都必须经过独立、版本化且可审核的专门 Contract。
18. 所有基于 Artifact Read Package 的跨模块持久使用都必须具有与确切 Package、Closure、用途和下游 Request 绑定的一次性 Artifact Use Confirmation；Source Integration 内部 Processing 由冻结 Processing Request / Grant / Lineage 事务授权，不构成旁路。
19. `MANAGED_EVICTION` 下 Source 的 Local Read Guard 与淘汰在同一权威协调记录上串行化；`NO_EVICTION` 不实现淘汰入口或空协调状态。
20. 正式 Evidence 必须在本轮 Materialization 内保存自包含的最小观察快照；`MANAGED_EVICTION` 时还必须在 Guard 结束前完成。当前发布路径不依赖外部 Payload 长期在线。
21. 当前不声称支持 Source Store 非连续历史恢复；出现真实替换需求前先完成专题设计，不预建 Store History 状态机。
22. 共享 Content 的逻辑 Artifact 淘汰不自动授权删除仍被本地 Guard、Derived 重放或法规策略保护的物理字节。
23. 取消 / 撤权先冻结已分派集合，再封存唯一终态 Result；封存后的迟到响应只进审计，不能形成旧 Operation 可用 Artifact。
24. 人类可读 Target、短 Revision、同名对象和模型自报身份不能直接进入来源操作；只有绑定确切定义与解析依据的 `EXACT` Source Target Resolution Receipt 具有 Canonical Operation Target 效力。
25. 每次 Source Operation 的 Intent、Request 和 Execution Grant 都绑定 exact `SOURCE_EXECUTION` Scope State Assertion 与 Binding Eligibility Assertion；任何失配只失败关闭，不由 Source Integration 猜测 Scope 状态或扩大 Binding。

## 16. 验证义务与开放项

当前不需要 Design Validation Demo 来决定中立 Artifact 外壳或 Target Resolution 边界，因为两者都可由 Provider Contract、确定性解析和失败关闭表达。进入具体 Provider 实现前必须建立 `CC-*` 验证 Identity、Selector、Target Resolution、权限、分页、Context、Artifact、Lineage、撤权和保留。

以下情况才建立 `DVR-*`：

- 某类来源无法在有界 Artifact 与稳定 Source Context 下表示。
- 候选粒度方案会实质改变定位正确性、变更隔离或跨模块 Contract，且静态分析不足。
- 模型辅助解析是否能被限制为可验证 LOCATOR_PRESERVING 转换无法由现有 Contract 判断。

Contract Conformance 还必须覆盖：

- 短 Revision 唯一 / 多义、同名及重载符号、跨模块同名对象、目标不存在和越过 Binding Selector 时分别得到 exact Receipt 或明确失败，不能落到相近目标或全量扫描。
- `NO_EVICTION` 下不存在 Archive / Evict / Physical Delete 写入口，也不产生 Guard Record；`MANAGED_EVICTION` Conformance 才覆盖淘汰与新 Local Read Guard 的全部竞态，且只有一方成功。
- `MANAGED_EVICTION` 的 Guard 过期、读取中断或 Package 内容不完整时，不形成部分 Evidence；`NO_EVICTION` 仍验证 Package / Closure 与自包含 Evidence Snapshot。
- Evidence Materialization 成功后即使源 Payload 淘汰，仍能只凭 Evidence Snapshot 与 Provenance 完成复核。
- 取消与 Dispatch 竞争时冻结集合无漏项；在途 Attempt 全部有终态或明确 Unknown 后才封存，迟到响应不进入 Investigation / Evidence。

具体模型解析 Strategy 的质量使用 `CE-*`。存储容量测试、吞吐压测和某个项目的 Artifact 数量是实现/非功能证据，不单独改变一般 Contract。
