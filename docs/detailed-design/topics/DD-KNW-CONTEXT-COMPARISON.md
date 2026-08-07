# KnowledgeContext Comparison 详细设计

| 元数据 | 值 |
|---|---|
| Document ID | DD-KNW-CONTEXT-COMPARISON |
| Version | 0.1.0 |
| Status | Accepted |
| Document Steward | Knowledge Engine |
| Architecture Baseline | SWM-ARCH@1.2 |
| Depends On | DD-KNW-REFERENCE-CONTEXT@0.1.0、DD-KNW-SCHEMA-CORE@0.1.0、DD-X-CAPABILITY-EXECUTION@0.1.0、DD-AI-MODEL-GATEWAY@0.1.0、DD-MGT-CAPABILITY-EVALUATION@0.1.0 |
| Owns Contracts | KNW-CONTEXT-COMPARE-01、KNW-CONTEXT-ASSESSMENT-01、KNW-CONTEXT-ASSESSMENT-VALIDITY-01 |
| Supersedes | None |
| Rationale ADR | AD-029、AD-030、AD-079、AD-087、AD-111、AD-115、AD-123 |
| Design Validation | None |
| Conformance Cases | None |
| Capability Evaluation | None |

> 概要架构约束直接生效；本文新增的比较结果、执行、复用和失效语义在状态进入 `Accepted` 前均为拟议设计。

## 1. 目的与范围

本文定义 Knowledge Engine 如何在一个明确判断目的下比较多个 KnowledgeContext，并将确定性或模型 Strategy 的执行结果转换为可审计 Compatibility Assessment。

本文不定义 Context 的身份、表达、Schema 和引用，也不允许 Compatibility Assessment 充当未准入的跨来源语义前提。

## 2. Capability 所有权

Knowledge Engine 拥有 Context Comparison Capability Contract、领域输入输出、Assessment 和组合门禁。Application Services 在进入 Knowledge Engine 前冻结 Capability Catalog 和 Execution Envelope：生产调用解析 exact Activation，首次 / 回归评测解析 exact EVALUATION_ONLY Grant。Knowledge Engine 在自身模块内执行 Deterministic / Model-Primary / Hybrid Strategy，并按需直接调用 Model Gateway。

Knowledge Engine 不反向读取 Application 的 Activation 状态。模型输出只形成 Comparison Proposal，不能直接形成 Assessment。

## 3. KNW-CONTEXT-COMPARE-01

一次请求至少固定：

- Comparison Purpose：例如 Fact Context 合并、Inference 前提兼容、跨 Scope 读取或 Conflict 可比性。
- 两个或多个 KnowledgeContext Reference。
- Target Knowledge Schema 与维度定义。
- 允许使用的 Resolved Formal Knowledge Reference。
- Capability Catalog Snapshot、Execution Envelope、`PRODUCTION Activation / Evaluation Result / latest Validity | exact EVALUATION_ONLY Grant`、Strategy、模型/Tool 边界和资源 Allocation。
- 调用方需要证明的最低结果；不能把 `UNKNOWN` 当作成功。

只有成功解析全部 Context、Schema、权限和正式依据后才执行比较。

## 4. KNW-CONTEXT-ASSESSMENT-01

执行成功后产生不可变 Compatibility Assessment：

| 结果 | 含义 |
|---|---|
| COMPATIBLE | 正式依据证明输入 Context 可以在当前 Purpose 下同时成立 |
| INCOMPATIBLE | 正式依据证明至少一个必要条件互相排斥 |
| UNKNOWN | 比较已正常完成，但正式依据不足，既不能证明相容也不能证明排斥 |
| NOT_COMPARABLE | 输入目标、维度或命名空间使当前 Purpose 下的比较没有定义 |

Assessment 同时固定：

- Comparison Purpose、输入 Context 和 Target Schema。
- Capability Contract、Strategy、Model Fingerprint / Replay Classification 和 Tool 版本。
- 支持结果的正式依据、维度判定和未决项。
- 执行状态、资源消耗和审计引用。
- 支持 Strategy 激活的 Evaluation Result Reference。

只有 `PRODUCTION` Catalog 且 post-call model eligibility 通过时，Knowledge Engine 才封存 Assessment，并在同一事务创建 `Assessment Validity Revision = 1, VALID`，固定当时 Capability Catalog、Activation、Evaluation Validity、Model Fingerprint、Tool、Schema / Dimension 和正式依据 Revision；新 Assessment 不存在“尚无 Validity”的中间状态。`EVALUATION_ONLY` 只返回隔离的 Evaluation Output Reference，不创建 Assessment / Validity，也不能被 Candidate、View 或 Knowledge Use 引用。

执行状态与语义结果正交。只有 `COMPLETED` 才有上述四种结果；`NO_ACTIVE_STRATEGY`、`FAILED`、`CANCELLED`、`BUDGET_EXHAUSTED`、Provider/Tool 不可用或输出 Contract 无效都表示没有 Assessment，不能映射为 `UNKNOWN`。

## 5. 正式依据与隐藏前提禁令

- 确切值相等、集合/区间关系和同一命名空间内的确定性判断，可以直接依据 Context Term 和版本化维度规则完成。
- 模型可以根据别名、描述或间接线索提出跨来源 Relation Proposal。
- 如果比较结论依赖一个没有被输入 Context 或正式知识表达的对应关系，该关系必须先形成 Fact 或 Inference Candidate、完成准入并发布；Comparison 随后引用其 Resolved Formal Knowledge Reference。
- Model Response、Comparison Proposal、Artifact、Evidence 或 Candidate 不能成为 Assessment 的隐藏语义前提。
- Assessment 只证明特定 Purpose 下的 Context 兼容性，不自动形成“两个来源属于同一部署”等对外知识 Claim。

## 6. 组合规则

1. `COMPATIBLE` 允许创建保留全部 Subject、Term 和 Basis 的新 KnowledgeContext。
2. `INCOMPATIBLE` 禁止构造宣称全部条件同时成立的 Context；原 Context 继续独立存在。
3. `UNKNOWN` 保留多个独立 Context 和未决调查关系，不能证明跨来源命题成立。
4. `NOT_COMPARABLE` 的知识可以同时存在，但不能被当作相互增强或冲突。
5. Context 不同或 Assessment 为 INCOMPATIBLE 都不自动形成对外冲突 Claim；只有已发布 Conflict Inference 可以声明正式冲突。

组合后的 KnowledgeContext 仍通过 KNW-CONTEXT-REF-01 创建，Assessment Reference 作为机械门禁依据保存；所有正式语义 Basis 仍必须是 Source Context / Evidence 或 Resolved Formal Knowledge Reference。

## 7. Strategy、评测与复用

- 每个 Strategy 实现同一 Context Comparison Capability Contract，并声明支持的 Purpose、维度和 Schema。
- 模型 Strategy 必须使用独立 ModelExecutionContext，平台重建 Context 与正式依据，禁止模型改写观察值。
- Strategy 上线前通过 `CE-*` 比较准确性、UNKNOWN/NOT_COMPARABLE 校准、错误相容率、成本和延迟。
- Assessment 只有在输入 Context、Purpose、Schema/维度、Capability、Strategy、Model Fingerprint、Tool 和支持其激活的 Evaluation Result 全部相同时才允许复用。
- Knowledge Engine 提供公共 `ValidateContextAssessmentReuse`。调用方提交 Assessment Reference、当前 Capability Catalog / Activation、Application Services 解析出的 latest Evaluation Validity Decision、全部依赖 Revision Proof 和 Expected Assessment Validity Revision。Knowledge Engine 不反向读取 Application Repository，而是验证这些权威引用与 Assessment 冻结依赖。
- 依赖完全一致且当前 Assessment Validity 为 VALID 时返回原 VALID Decision；任一依赖改变、Activation 失效或 Evaluation Validity 为 `STALE | REVOKED` 时，以 Expected Revision CAS 追加不可变 `STALE | REVOKED` Decision。状态只允许 `VALID → STALE | REVOKED` 和 `STALE → REVOKED`，不能回到 VALID；需要恢复资格必须重新比较并形成新 Assessment。
- Fact / Inference Construction、Admission、Semantic View 和 Knowledge Use 在组合 Context 前都必须调用该公共 Contract，并固定返回的 latest VALID Decision。历史准入仍保留当时 Assessment / Validity 引用；失效不回写旧 Assessment 的四态结果。

不存在依据时返回 `UNKNOWN` 是正确结果，不得为了生成完整模型而猜测 `COMPATIBLE`。

## 8. 失败与保守处理

| 类别 | 处理 |
|---|---|
| CONTEXT_REFERENCE_INVALID | 不执行比较；返回引用错误 |
| PURPOSE_UNSUPPORTED | 不用相近 Purpose 猜测；返回不可用 |
| NO_ACTIVE_STRATEGY | 不执行；Application 可选择已批准回退后发起新 Attempt |
| COMPARISON_EXECUTION_FAILED | 不产生 Assessment，不映射 UNKNOWN |
| OUTPUT_CONTRACT_INVALID | 拒绝 Comparison Proposal |
| FORMAL_BASIS_MISSING | 返回 UNKNOWN 或补充信息需求，不允许模型补写依据 |
| CONTEXT_INCOMPATIBLE | 需要 COMPATIBLE 的调用失败，但不删除输入 Context/知识 |
| ASSESSMENT_STALE | 重新执行比较，不静默复用 |

## 9. 可观测性与数据边界

- 记录 Comparison ID、Purpose、Context/Schema、Capability/Strategy/Model、正式依据、结果、失败和资源消耗引用。
- 不在 Telemetry 复制 Artifact Payload、Evidence Quote 或敏感 Context 值。
- Assessment、Proposal 和运行轨迹不是 Artifact、Evidence、Fact 或 Inference。

## 10. 拟议不变量

1. Context Comparison 是 Knowledge Engine 拥有的 Capability，不反向调用 Application Services。
2. 只有执行完成才具有语义结果；运行失败不能伪装为 UNKNOWN。
3. Strategy Result 先是 Proposal，Assessment 由 Knowledge Engine 重建并校验。
4. 影响正式语义的跨来源关系必须先进入正常 Fact / Inference 准入与发布路径。
5. Compatibility Assessment 不能成为 Fact / Inference 的隐藏前提或对外知识 Claim。
6. Context 不同、INCOMPATIBLE 和正式 Conflict Inference 是三个不同概念。
7. Assessment 复用绑定精确输入、执行和 Evaluation 版本，失效后不能支持新 Candidate。
8. 模型升级只通过新 Strategy/Evaluation 激活，不改变 Context 语义和保守结果边界。
9. Assessment 与 initial VALID 同事务封存；Validity 只能单调失效，所有复用都通过公开 Validate Contract 可达。

## 11. 验证义务

当前基础 Contract 不需要 Design Validation Demo。每个具体 Strategy 必须建立 `CE-*`；实现必须以 `CC-*` 验证运行失败与 UNKNOWN 分离、隐藏前提拒绝和 Stale Assessment 不可复用。只有真实来源类型暴露出会改变四态语义或正式依据边界的不确定性时，才建立 `DVR-*`。
