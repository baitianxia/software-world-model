# Semantic View 详细设计

| 元数据 | 值 |
|---|---|
| Document ID | DD-SEM-SEMANTIC-VIEW |
| Version | 0.1.0 |
| Status | In Review |
| Document Steward | Semantic View Engine |
| Architecture Baseline | SWM-ARCH@1.2 |
| Depends On | DD-KNW-REFERENCE-CONTEXT@0.1.0、DD-KNW-SCHEMA-CORE@0.1.0、DD-KNW-CONTEXT-COMPARISON@0.1.0、DD-KNW-SNAPSHOT-PUBLICATION@0.1.0、DD-KNW-PERSISTENCE@0.1.0、DD-X-CAPABILITY-EXECUTION@0.1.0、DD-AI-MODEL-GATEWAY@0.1.0、DD-MGT-CAPABILITY-EVALUATION@0.1.0 |
| Owns Contracts | SEM-VIEW-READ-BOUNDARY-01、SEM-VIEW-DEFINITION-01、SEM-VIEW-EXECUTION-01 |
| Supersedes | `DD-APP-KNOWLEDGE-USE@0.1.0` 中 Semantic View Definition 与 Execution 语义 |
| Rationale ADR | AD-028、AD-031 至 AD-036、AD-062、AD-114、AD-115、AD-125、AD-135 |
| Design Validation | None |
| Conformance Cases | None |
| Capability Evaluation | Semantic View Organization / Conformance 使用模型时适用 |

> Semantic View Engine 只组织已发布正式知识，不拥有 Knowledge Requirement、Snapshot Read Session、Sufficiency、正式知识或用户答案。

## 1. 目的与范围

本文定义 Structure、Behavior、Business、History 及可注册扩展视图的版本化契约和执行语义，使不同调用方可以按任务组织正式知识，同时保持每个输出项对原始 Entity、Fact 或 Inference 的可追溯性。

本文不定义 Application Session、Knowledge Sufficiency、用户答案、Artifact / Evidence 读取、正式知识写入、UI 布局或物化存储实现。当前采用按需可重建执行；只有重复查询和性能证据触发时才另行启用物化 Projection。

## 2. 边界与所有权

| 对象或决定 | Owner |
|---|---|
| View Definition、View Read Boundary Contract、Execution / Conformance Result | Semantic View Engine |
| Snapshot、Schema、正式 Entity / Fact / Inference 与 Member Manifest | Knowledge Engine |
| Task、Requirement、Read Session、Use Epoch、Sufficiency 与 Gap | Application Services |
| View Organization Strategy | Semantic View Engine；模型只生成不可信 Draft |
| View Materialization | 当前未启用；未来仍为可重建 Projection |

Semantic View Engine 是只读 Knowledge Engine 的 Core Capability。它不访问 Source Integration、Artifact、Evidence Quote、Candidate 或 Application Repository，也不把 View Finding 写入正式知识。调用方只能通过 Application Services 使用该能力。

## 3. SEM-VIEW-DEFINITION-01

### 3.1 View Definition

每个不可变 Semantic View Definition 至少固定：

- View ID / Version / Digest、View Kind、用途和 Output Schema / Query Contract。
- 支持的 Knowledge Schema / Type / Context / Scope 组合与 Compatibility Requirement。
- 正式知识选择、组织、排序、分组和字段映射规则。
- 每种 Output Item / Field 所需 `Support Kind` 与语义蕴含边界。
- Coverage / Pagination / Partial 语义、Conflict / Limitation 展示规则。
- Deterministic / Model-Primary / Hybrid Organization Strategy 与独立 Conformance Profile。

View Definition 由 Semantic View Engine 注册。Definition 注册成功只表示 Contract 合法，不表示任何 Snapshot 已具有 READY View，也不表示用户任务充分。

当前每次按 Session 执行 View，不创建 View Materialization Instance。未来只有实际重复查询和性能证据触发 Projection / Materialization 设计；届时仍不得改变 Definition、Support Map、权限隔离和权威回读语义。

### 3.2 内置 View 语义

| View | 组织目标 | 必须保持的边界 |
|---|---|---|
| Structure | Entity 组成、包含、接口、静态依赖和结构推断 | 不把某次执行顺序或运行观察泛化为静态结构 |
| Behavior | 条件、步骤、分支、状态迁移、事件、结果和副作用 | 区分可复用 / 预期 Behavior 与单次运行 Fact |
| Business | Business Entity、规则、能力、目的与跨系统实现映射 | 技术身份保留在各自 Scope，业务语义由正式 Fact / Inference 支持 |
| History | 按 Time / Version / Change Context 组织变化、原因和影响 | 不等同于平台历史 Snapshot；原因 / 影响必须由正式 Inference 支持 |

Operational View 可以注册为扩展 View，用日志 / Trace / Metric 形成的正式知识组织运行语义；Runtime 仍不是独立核心知识层。

### 3.3 View Support Map

每个 View Item 及其具有语义的字段 / 边必须绑定：

- 身份存在 / 引用：目标 Snapshot 中正式 Entity State。
- 属性、关系、行为、业务含义、变化、原因或影响：一个或多个其正式命题直接蕴含该表达的 Fact / Inference。
- “存在冲突”：正式 Conflict Inference 及其引用的全部 Fact。
- 限制 / 未知：Read Boundary Coverage、View Coverage 与明确 Gap / Unavailable 状态。

View 可以重命名显示标签、排序和摘要，但不能把多个较弱命题拼成更强陈述、删除 Context 条件、选择冲突赢家或用 Source Locator 中的文本补足正式命题。View 发现的新解释只能形成非权威 View Finding / Gap Proposal；只有 DD-APP-KNOWLEDGE-USE 对 exact Requirement 的独立 Sufficiency Assessment 才能产生正式应用态 Knowledge Gap。

## 4. SEM-VIEW-EXECUTION-01

### 4.1 输入与执行

Semantic View Request 固定中立 `SEM-VIEW-READ-BOUNDARY-01`、View Definition、Context / Scope subset、Output Boundary、Capability Catalog、Execution Envelope 和 Idempotency Key。Read Boundary 由调用方根据已经验证的读取上下文构造，至少固定 exact Snapshot Set / Member Manifest、Schema Set、KnowledgeContext、Coverage、Purpose、权限 / Classification、Snapshot Selection Validation Receipt 和 Digest；可携带 opaque Application Session / Task / Expected Use Epoch Reference 作为关联字段，但 Semantic View Engine 不读取或推进应用状态。

执行步骤：

1. 校验 Definition 支持 Read Boundary 的 exact Snapshot Schema Set、Context、Scope 与 Purpose；跨 Schema 组织必须绑定 Read Boundary 中方向匹配、Purpose = SNAPSHOT_READ、Outcome = EQUIVALENT 的 Compatibility Decision。
2. 通过只读 Knowledge Engine API 查询同一 Read Boundary 的正式知识；不访问 Source、Evidence Quote、Candidate、Projection 或缓存正文。
3. 按 Definition 组织 View Draft；模型输出经过严格 Output Schema 解析，未知字段 / 引用和越界项拒绝。
4. 机械验证每个 View Item / Field 的 Support Map、Member Reference、Context、Conflict 和 Coverage。一个 Item / Field 跨 Schema 使用 Support 时先验证上述 SNAPSHOT_READ Decision；跨 KnowledgeContext 组合时再携带当前 Catalog / Activation、latest Evaluation Validity 与依赖 Revision 调用 `ValidateContextAssessmentReuse`。Schema 与 Context 两个门禁必须分别通过，不能由模型隐藏映射。
5. 对模型生成的非平凡摘要 / 归类执行与 Organization Strategy 隔离的 View Semantic Conformance Assessment，从权威正式命题重建语义范围。
6. 封存 View Result / Conformance / Coverage；历史 Result 不成为后续 Session 的缓存输入。

View Result 固定 Read Boundary / Digest、Definition、Support Map、Coverage、权限 / Classification Assertion 和 Result Digest。Semantic View Engine 在封存前重验全部正式引用属于该 Read Boundary；调用方在接受或交付 Result 前负责重验自己的 Session / Use Epoch。缓存文本、摘要或先前 Conformance Result 不能绕过任一门禁；引用悬空、越权或不再满足 Read Boundary 时不得交付旧正文，只能形成新的 PARTIAL / 失败 Result，历史 Result 保持不可变。

Organization Strategy 不能审核自己。完全由版本化 Mapping 机械确定的 View 可以使用 Deterministic Conformance；模型审核失败或未执行不能被当作 READY。

### 4.2 View Result 状态

| 状态 | 含义 |
|---|---|
| READY | Definition 要求的 Support / Coverage / Conformance 全部满足 |
| PARTIAL | 合法输出了一部分，但 Coverage / 权限 /资源 / Schema 限制明确存在 |
| INCOMPATIBLE | Read Boundary 的 Schema / Context / Scope 不受 Definition 支持 |
| EXECUTION_FAILED | Tool / Model / Provider / Conformance 执行失败，没有 READY 结果 |

READY 只表示 View Query Contract 完成，不证明当前 Requirement 或答案完整。PARTIAL 可以返回安全的已支持 Item 与限制，但调用方不能删除限制后当作 READY。

已确认 Conflict Inference 必须连同全部被引用 Fact 和 Context 以 Definition 规定方式呈现；排序、分页或摘要不得让某一方静默消失。仅存在两个不同 Fact 而没有 Conflict Inference 时，View 可以并列观察，但不能标注“冲突”。来自 `UNKNOWN | NOT_COMPARABLE | INCOMPATIBLE` Context 的 Item 必须分组或带限制呈现，不能拼成一个联合语义。

## 5. 模型 Strategy 与能力演进

Deterministic、Model-Primary 和 Hybrid Strategy 均实现同一个 View Definition Contract。模型只承担选择、组织、归类和受控摘要；平台负责正式引用、Schema / Context 门禁、Support Map、Coverage、Conflict 展示和结果封存。

Strategy、Prompt、模型、Adapter 或 Conformance 规则发生实质变化时使用新版本并重新评测。模型增强可以减少专用组织规则，但不能删除 Support Map、读取边界、冲突披露或正式知识权威回读。

## 6. 失败与恢复

至少区分：

| 类别 | 语义 |
|---|---|
| `READ_BOUNDARY_INVALID` | Snapshot、Schema、Context、权限或 Receipt 不完整 / 失配 |
| `VIEW_DEFINITION_INCOMPATIBLE` | Definition 不支持当前 Read Boundary |
| `FORMAL_REFERENCE_INVALID` | Item 引用不属于 exact Snapshot Member Manifest |
| `SUPPORT_NOT_ENTAILING` | 正式命题不能直接支持 View 表达 |
| `CONFLICT_DISCLOSURE_INCOMPLETE` | 已确认冲突未完整呈现 |
| `MODEL_EXECUTION_INELIGIBLE` | 模型隔离、实际指纹或 Strategy 资格不成立 |
| `EXECUTION_FAILED` | 执行未形成合法 Result |

重试只能复用相同 Definition、Read Boundary、Catalog 和 Idempotency Key；任一输入变化创建新 Execution。失败结果不能作为历史 READY View 缓存的授权。

## 7. 拟议不变量与验证义务

1. View 只组织正式知识，不创建或扩张正式语义。
2. 每个有语义的 Item / Field 都具有 exact Support Map。
3. Entity 只能支持身份存在；属性、关系、行为、业务含义、原因和影响必须由正式 Fact / Inference 支持。
4. View Read Boundary 不允许 Semantic View Engine 读取或推进 Application Session。
5. Conflict、Context、Schema、Coverage 和权限限制不能被排序、分页或摘要静默隐藏。
6. View READY 不等于 Requirement SUFFICIENT，也不等于 Answer 获准交付。
7. View 物化结果始终可重建，不能成为平行知识权威。

这些语义通过固定正式知识 Fixture、Support Map 反例、跨 Context / Schema Case 和 Strategy Conformance Evaluation 验证；当前无需设计 Demo。

进入实现前至少覆盖：Entity-only 越权支持属性、模型摘要增加限定词 / 因果 / 唯一性、跨 Snapshot 引用、Context 或 Schema 不可组合、已确认 Conflict 任一方被分页或摘要隐藏、没有 Conflict Inference 却标注冲突、PARTIAL 限制被删除、权限隔离键变化、Read Boundary 失效、Conformance 漏项，以及当前未启用 Materialization 时出现隐藏缓存正文。上述任一 Case 都不能产生或维持 READY Result。
