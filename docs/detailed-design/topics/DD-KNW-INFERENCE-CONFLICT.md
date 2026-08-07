# Inference、Conflict 与推断型 Entity 详细设计

| 元数据 | 值 |
|---|---|
| Document ID | DD-KNW-INFERENCE-CONFLICT |
| Version | 0.1.0 |
| Status | Accepted |
| Document Steward | Knowledge Engine |
| Architecture Baseline | SWM-ARCH@1.2 |
| Depends On | DD-KNW-REFERENCE-CONTEXT@0.1.0、DD-KNW-SCHEMA-CORE@0.1.0、DD-KNW-CONTEXT-COMPARISON@0.1.0、DD-KNW-ENTITY@0.1.0、DD-KNW-FACT@0.1.0、DD-X-CAPABILITY-EXECUTION@0.1.0、DD-AI-MODEL-GATEWAY@0.1.0、DD-MGT-CAPABILITY-EVALUATION@0.1.0 |
| Owns Contracts | KNW-INFERENCE-TYPE-01、KNW-INFERENCE-ARGUMENT-01、KNW-INFERENCE-DEPENDENCY-01、KNW-INFERENCE-01、KNW-CONFLICT-INFERENCE-01、KNW-SEMANTIC-ENTITY-01、KNW-INFERENCE-STATE-01 |
| Supersedes | None |
| Rationale ADR | AD-003、AD-006、AD-027 至 AD-036、AD-037 至 AD-043、AD-078、AD-079、AD-087、AD-088、AD-095、AD-108、AD-111、AD-113、AD-115、AD-116、AD-121 至 AD-123、AD-126、AD-128 |
| Design Validation | None |
| Conformance Cases | None |
| Capability Evaluation | None |

> 概要架构约束直接生效；本文新增的 Inference Type、Argument、依赖、Conflict 和 Semantic Entity 语义在状态进入 `Accepted` 前均为拟议设计。

## 1. 目的与范围

Inference 表达基于已发布正式知识形成的语义结论。它承担开放式归纳、跨来源关联、目的与业务解释、因果判断、通用行为还原、上下文关联和冲突判断，同时通过结构化前提、Context、依赖闭包和独立审核限制推理漂移。

本文定义：

- Inference 与 Fact、Evidence、Entity 和 Semantic View 的认知边界。
- Inference Type、Canonical Conclusion、Structured Argument 和正式前提依赖。
- 有界无环推理、稳定 Inference Identity、Snapshot-local State 和重验证。
- Conflict Inference 的可比性、不兼容性和不静默选择规则。
- 推断型 Business / Technical Entity 与 EntityDerivation Inference 的原子闭包。
- 模型推理 Strategy 与平台可信控制、能力评测和模型演进边界。

本文不定义：

- Knowledge Admission 的通用状态机、Snapshot 完整发布协议或物理存储。
- Structure、Behavior、Business、History View 的查询组织方式。
- 特定业务领域的推理规则、Prompt、模型、最大深度数值或风险阈值。
- Target Architecture Recommendation、自动治理动作或人工审批工作流。

## 2. Inference 的认知边界

### 2.1 结论而非来源观察

Inference 是对正式知识作出的语义结论。以下典型内容属于 Inference：

| 输入正式知识 | Inference 示例 |
|---|---|
| 多个代码、配置和测试 Fact | 归纳一个可复用执行流程或状态机 |
| 技术 Entity / Fact 与业务规则 Fact | 判断技术实现承载某个业务能力 |
| Commit、需求和运行影响 Fact | 判断某次变更的可能原因或影响链 |
| Log Context 与部署映射正式知识 | 判断某运行观察对应某代码 Revision |
| 两个可比较但不兼容的 Fact | 形成 Conflict Inference |
| 多个系统的正式知识 | 归纳 Business Domain Entity 或跨系统语义关系 |

Inference 的结论可以是 Structure、Behavior、Business、History 或扩展 View 所需语义，但这些 View 不是新的知识层，也不决定 Fact / Inference 分类。

### 2.2 正式前提边界

Inference 的语义前提只允许：

- 固定 Snapshot 中 `ASSERTED` 的正式 Fact State。
- 版本化 Dependency Policy 允许的、固定 Snapshot 中 `ASSERTED` 的上游 Inference State。

Evidence、Artifact、Entity State、Source Operation Result、Candidate、Hypothesis、Comparison Proposal、Agent Working State、模型摘要和 Telemetry 不能成为正式 Inference 的语义前提。Entity 可以作为结论或前提命题中的稳定 Identity Term，但“Entity 存在”只提供身份引用，不提供属性、关系或业务含义。

Knowledge Verifier 可以沿正式 Fact 追踪 Evidence 复核前提质量；这属于审核输入，不会把 Evidence 提升为 Inference 的直接前提。

### 2.3 结论模态与模型置信度分离

Inference Type 可以定义 `ASSERTED_RELATION`、`POSSIBLE_CORRELATION`、`RECOMMENDATION` 等具有用户可见含义的 Epistemic / Intent Modality。该模态是 Canonical Conclusion 的一部分；“可能 X”和“确定 X”不是同一个命题。

模型 Confidence、采样概率和 Verifier 分数只是 Strategy / Evaluation 元数据，不能自动成为结论模态，也不能用阈值把 POSSIBLE 静默升级为 ASSERTED。`Inference State = ASSERTED` 表示平台正式接受整个带模态命题，例如正式接受“X 可能相关”，不表示把其中的“可能”删除。

## 3. 逻辑对象与所有权

| 对象 | Owner | 权威性质 |
|---|---|---|
| Inference Proposal | Reasoning Strategy / Investigation | 不可信的 Conclusion、Premise、Argument 和 Context 建议 |
| Inference Candidate | Knowledge Engine Candidate Area | 平台重建后等待 Knowledge Verification 的候选 |
| Structured Argument | Knowledge Engine | 可移植、可审核的结论支持结构；不是模型隐藏思维链 |
| Inference Dependency Closure | Knowledge Engine | 直接前提、传递 Inference 和展平 Fact Leaf 的确切闭包 |
| Inference Root | Knowledge Engine | 稳定、不可变的 Canonical Conclusion 身份 |
| Inference State | Knowledge Engine | 某 Snapshot 中该结论的 Context、Argument、依赖和可用性 |
| Conflict Inference | Knowledge Engine | 普通 Inference 的受约束语义类型；没有平行存储或生命周期 |
| Semantic Entity Proposal | Knowledge Engine Candidate Area | 推断型 Entity 的候选身份定义；不能单独成为正式 Entity |
| EntityDerivation Inference Candidate | Knowledge Engine Candidate Area | 证明 Semantic Entity 身份成立的 Inference Candidate |

Application Services 固定 Build Intent、Base / Upstream Snapshot、Capability / Strategy 和资源政策。Knowledge Engine 拥有 Inference Contract、Candidate 重建、依赖闭包、身份、准入接口和正式状态；Model Gateway 只执行模型调用。

## 4. KNW-INFERENCE-TYPE-01

### 4.1 Inference Type Contract

每种 Inference Type 必须由目标 Knowledge Schema 注册版本化 Contract，至少定义：

- 稳定的 `Inference Type Identity Scheme ID` 和语义名称空间。
- Canonical Conclusion 的 Role、Term、Epistemic / Intent Modality、基数、量词、条件和规范化规则。
- 允许的直接 Premise Kind / Type / Role、最小 Fact Leaf 要求和禁止依赖。
- 允许的 Premise Semantic Modality 组合、输出 Modality 传播规则和确定性偏序；包括 Fact Observation Modality 与 Inference Epistemic / Intent Modality 如何进入本类型的语义。
- Structured Argument 必须公开的语义步骤、覆盖义务、替代解释和限制。
- Premise Context 关系、Output Context Construction 和不可接受的 Comparison Result。
- `Identity-bearing Context Projection` 及 Inference Identity Context Key。
- Dependency Policy Class、风险级别和必须执行的 Verifier Profile。
- 等价结论、语义不兼容和 Schema 兼容升级规则。
- 是否属于 `GENERAL`、`CONFLICT` 或 `ENTITY_DERIVATION` 等受约束类别及相应附加义务。

Contract 定义语义与验证义务，不冻结模型的完整推理算法。开放式业务理解可以由模型承担，但不能用自由文本结论绕过类型化 Conclusion、正式前提和 Context。

### 4.2 Canonical Conclusion 不受三元组限制

Canonical Conclusion 可以表达多角色关系、有界逻辑、条件流程、因果方向、比较结果或带模态的语义定义。图三元组、自然语言摘要、标签和向量是可重建 Projection，不能成为结论表达上限或补充正式 Conclusion 未声明的语义。

Conclusion 中的 Entity 或正式知识目标 Term 最终只保存相应 Knowledge Identity Reference；构建和 Inference State 另行固定这些身份在本地目标 Snapshot 或确切 Upstream Snapshot 中的 Resolution Binding。只有 Inference Type 明确允许时 Conclusion 才能引用 Fact / Inference Identity，例如 Conflict 必须标识被比较 Fact；引用本身不能替代它作为 Argument 正式前提。

### 4.3 As-Is、Target 与 Recommendation 分离

描述当前软件语义、推断的可能解释、目标架构和改进建议必须使用不同 Inference Type / Modality。Recommendation 或 Target Model 不能覆盖 As-Is Fact / Inference，也不能因为出现在 Architecture View 中被解释为当前事实。

## 5. KNW-INFERENCE-DEPENDENCY-01

### 5.1 合法直接前提

每个 Premise Reference 必须是 `Resolved Formal Knowledge Reference(kind=FACT|INFERENCE)`：

- Expected Current 为 PRESENT 时，本 Scope 前提来自该 Base Snapshot；NO_CURRENT 时本地正式前提集合为空。
- 跨 Scope 前提来自 Build Intent 允许的确切 Upstream Snapshot。
- Fact State 必须为 `ASSERTED`，满足目标推理用途的可用性政策，且其 Observation Modality 被当前 Inference Type 允许。
- Inference State 必须为 `ASSERTED`，其 Type、Conclusion Modality、Depth 和 Dependency Policy 被当前 Contract 允许。

`ASSERTED` 仅表示该带模态命题已正式准入，不会把 `POSSIBLE(X)` 变成“X 确定成立”。Knowledge Verifier 必须根据 Contract 重建每个 Premise 的有效模态和输出传播。输出确定性不得默认强于必要前提；如果某个形式规则合法地产生不同模态，该映射必须是 Schema 中版本化、可重放的 Type Rule，不得由模型临时声明。

动态 `CURRENT`、裸 Knowledge ID、未解析名称、其他 Attempt 的 Candidate 和已发布但不属于固定 Snapshot 的 Root 都不能作为前提。跨 Scope 前提在目标 Snapshot 中形成显式 Upstream Snapshot Dependency，不复制上游知识。

本地 Base Premise 是生成与审核依据，不是发布后遗留的历史 Snapshot 依赖。Candidate Snapshot 必须为该 Identity 提供一个 `Local Premise Rebinding`：目标 State 继续 ASSERT 同一 Canonical Proposition / Conclusion，Context 覆盖本 Argument 所需范围，且不使用本轮 Candidate 才新增的语义来补足原前提。Verifier 同时保存并比较 Construction Premise Reference 与 Candidate Target Binding；无法证明语义保持时不能发布该 Inference。

Premise 所属 Snapshot Schema 与目标 Inference Schema 不同时，必须具有 Schema Core 的 exact `FORMAL_PREMISE_INTERPRETATION` Transition Proof，固定源 / 目标 Schema、Knowledge Type / Type Contract、允许的语义映射和 Identity Continuation；否则该 Premise 不可使用。Schema 名称、版本大小或模型认为“意思相同”都不能授权跨 Schema 推理。对于本 Scope Schema 重建，通常先发布目标 Schema 下重验证后的 Fact，再在后续 Attempt 构建 Inference。

### 5.2 Candidate 不得成为语义前提

本轮 Fact Candidate 或 Inference Candidate 不能成为另一个 Inference Candidate 的语义前提。Candidate-local Reference 只允许：

- 在 Conclusion 中引用同一原子 Closure 内待创建的 Semantic Entity。
- 在该 Closure 内完成最终稳定 ID 替换。

如果推理需要本轮新建 Fact，必须先将该 Fact 发布到一个 Snapshot，再基于新的 `Expected Current = PRESENT(new Snapshot)` 发起 Inference Construction。该顺序可能增加构建轮次，但防止未经准入的候选通过下游结论间接进入正式知识。

### 5.3 有界、无环与可展平

Dependency Depth 定义为：每个直接 Fact Premise 深度为 0；直接 Inference Premise 深度为其已发布 Depth；`InferenceDepth = 1 + max(全部直接 Premise 深度)`。因此没有直接 Inference Premise、仅依赖 Fact 的首层 Inference 深度为 1；无直接 Premise 的 Candidate 本就因 Fact Leaf 闭包为空而非法。每个 Inference State 必须保存：

- 全部直接 Premise Resolved Reference。
- 全部传递 Inference Dependency Reference。
- 非空的展平 Fact Leaf Reference 集合。
- Dependency DAG、Depth、Node / Edge Count 和 Closure Digest。
- 每个 Structured Argument 的 Step / Edge Count；局部步骤也受执行上限约束，不能把任意深推理塞入一个 Inference 节点绕过 Dependency Depth。
- 计算所用 Dependency Policy / Schema / Canonicalization Version。

每次 Construction 的 Execution Envelope 必须固定有限的 `MaxInferenceDepth`、`MaxDependencyNodes`、`MaxArgumentSteps`、`MaxArgumentStepEdges` 和资源预算，且不超过当前 PRODUCTION Activation 或 EVALUATION_ONLY Grant 明确批准的上限。一般设计不写死两级或某个数字；任何 Strategy 都不能选择“无限”。

以下情况拒绝 Candidate：

- Conclusion Identity 已出现在自己的直接或传递前提中。
- 任一前提闭包不完整、Depth 不可重建或 Closure Digest 不一致。
- 依赖图包含 Candidate、动态 Snapshot 或未经批准的 Inference Type。
- 只有 Inference 前提而无法展平到至少一个正式 Fact Leaf。

跨 Scope 依赖仍只指向已发布 Snapshot，因此发布依赖天然指向既有状态；不同 Scope 之间不建立分布式发布事务。

## 6. KNW-INFERENCE-ARGUMENT-01

### 6.1 Structured Argument

Structured Argument 至少固定：

- Candidate-local Conclusion 或发布后的 Inference Identity。
- 有名 Premise Role 与确切 Resolved Formal Knowledge Reference。
- 版本化 Inference Type / Rule / Argument Schema。
- 面向审核的语义步骤：每步声明输入 Role、产生的中间判断、适用规则和结论路径。
- Output Context Construction、Context Assessment 和未决限制。
- 直接 / 展平依赖闭包、Depth 与循环校验结果。
- 已检查的替代解释、反例范围或明确未覆盖项；具体要求由风险 Profile 定义。
- Capability、Strategy、Model / Tool Execution、Evaluation Activation 和构造 Provenance。

Argument 不保存模型私有 Chain-of-Thought、隐藏会话状态或仅模型可解释的 Token Trace。它保存的是可移植的结构化论证；独立 Verifier 必须能够只依靠正式前提、Contract、必要 Evidence 追溯和该公开结构重新判断结论是否被支持。

Argument 内的 Intermediate Judgment 只服务当前 Conclusion 审核，不是正式知识，也不能被其他 Candidate 引用。若一个中间结论具有独立语义、需要复用、显著增加推理深度或是后续步骤不可省略的高风险前提，必须先作为独立 Inference 发布，再在新 Attempt 中以 Resolved Formal Knowledge Reference 使用；不能通过增加本地 Step 绕过依赖深度和准入。

### 6.2 多个 Argument

同一 Canonical Conclusion 可以由多个分别验证的 Argument 支持，并继续使用一个稳定 Inference Root。Argument 数量不自动提高真值或 Confidence；相互复制、共享同一上游推理链或由同一错误前提派生的 Argument 不构成独立增强。

一个可用 Inference State 至少有一个完整 Argument。缺少必要前提、步骤或 Context 的 Partial Argument 只能保留为 Investigation / Candidate 状态，不能与其他不相关 Argument 按数量拼成正式结论。

## 7. InferenceContext

### 7.1 普通推断

普通 Inference 的 Output Context 由全部正式前提 Context 与推理规则共同形成：

- 需要前提同时成立时，使用版本化 Context Comparison 证明 `COMPATIBLE`，并保留全部 Subject、Term 和 Basis。
- `UNKNOWN`、`NOT_COMPARABLE` 或执行失败不能支持要求共同成立的结论。
- 结论 Context 不能比前提和规则允许的范围更宽。
- DERIVED Context Term 必须直接引用作为本 Argument 正式前提的 Resolved Formal Knowledge Reference，不能引用隐藏 Candidate 或模型判断。

Context Comparison / Compatibility Assessment 只是重放结果，不能隐藏实例语义依据。除纯 Schema 维度规则、形式运算符和无实例输入的机械规则外，必须满足 `assessment.supportingFormalRefs ⊆ inference.directPremises`；这些引用一并进入 Dependency DAG、Depth、Freshness 和失效传播。

### 7.2 比较与跨时间推断

History、环境差异、Context Correlation 和 Conflict 等推断可能有意比较不能同时成立的 Context。此时 Inference Type Contract 必须定义有名 Context Role，例如 `BEFORE / AFTER`、`EXPECTED / OBSERVED` 或 `LEFT / RIGHT`，并在 Conclusion 中保留比较关系；不能把输入 Context 强制合成一个 AND Context。

Context 不同、`INCOMPATIBLE` 或 `UNKNOWN` 本身都不是冲突或相关性的结论。只有正式 Inference 明确声明并通过审核后，Semantic View 和答案才能陈述这种关系。

### 7.3 Context Correlation

版本、部署、环境或时间映射若不是来源直接观察型 Fact，就使用 ContextCorrelation Inference：

- 原 Artifact、Evidence、Fact Context 保持不变。
- Conclusion 明确关联类型、方向、模态和适用范围。
- 依赖保留所有正式 Fact / 上游 Inference 及 Context。
- 后续推理若使用该关联，必须把它列为显式前提并计入 Depth / 失效传播。

模型认为“很可能是同一版本”不能改写 Context，也不能使两个 Evidence 共同形成 Fact。

## 8. Inference Candidate、身份与 Resolution

### 8.1 冻结输入

一次 Inference Construction 至少固定：

- `KNW-CANDIDATE-ENVELOPE-01`：Build Intent / Application Attempt References、target Scope / Schema、Target Snapshot Local Reference、Expected Current 与 Upstream Bindings。首次 Scope 构建显式使用 NO_CURRENT。
- 可读取的 ASSERTED Fact / Inference State 与完整正式引用。
- target / upstream Entity Resolution Binding。
- Capability Catalog Snapshot、Execution Envelope、exact Strategy、`PRODUCTION Activation | EVALUATION_ONLY Grant`、Dependency Policy 和资源分配。

Knowledge Engine 从自己的正式 Repository 读取这些输入，不读取 Source Operation Result、Artifact Payload 或未发布 Candidate。Application Services 不替模型选择前提或解释命题。

平台重建的每个 Inference State Candidate 必须携带 exact Candidate Envelope Reference / Digest；除 ENTITY_DERIVATION 与其 INFERRED Entity 的 Hard Atomic Edge 外，本地 Entity 引用使用 Admission 的 Directed Publication Prerequisite。

只有 `PRODUCTION` Catalog 且 post-call model eligibility 通过时，重建结果才能进入生产 Candidate Envelope / Bundle。`EVALUATION_ONLY` 只返回隔离 Evaluation Output，不创建可准入的 Inference / Semantic Entity Candidate。

### 8.2 Proposal 与平台重建

模型或确定性 Strategy 可以提出：

- Proposal-local Inference Key、Inference Type、Conclusion Modality 和结构化 Term。
- Direct Premise Reference、Role、Argument Step 和 Context Proposal。
- Semantic Entity Proposal / Local Reference（仅 ENTITY_DERIVATION 路径）。
- 替代解释、反例、限制、未决问题和补充正式知识需求。

Knowledge Engine 必须从权威 Repository 重建：

1. Scope、Schema、Expected Current / Upstream Snapshot Binding 和每个 Resolved Premise / Entity Reference。
2. Premise Proposition、State、Context、依赖和 Fact-to-Evidence 追溯引用。
3. Inference Type、Canonical Conclusion、Epistemic / Intent Modality 和 Identity Context Key。
4. Structured Argument、Output Context、Dependency DAG、展平 Fact Leaf、Depth 和 Closure Digest。
5. Semantic Entity Proposal 与 EntityDerivation Closure（若有）。
6. Inference Resolution、Candidate-local Reference 和完整 Capability Provenance。

模型自报的正式 ID、Snapshot、Context、Dependency Depth、Closure、Fact 内容、Entity 已存在性、置信等级或 Admission 状态均不可信。未知字段、重复局部 Key、越界引用、缺失 Premise 和非法 Candidate 依赖拒绝整个相关 Proposal；修正提交完整 replacement Proposal。

### 8.3 Canonical Conclusion 与 Root

Inference Root 至少固定：

- owning KnowledgeScope ID 和不透明稳定 Inference ID。
- Inference Type Identity Scheme ID。
- Canonical Conclusion，包含 Conclusion Modality 和稳定 Entity Identity Term。
- Inference Identity Context Key。
- 创建时 Effective Inference Identity Key。
- 创建时 Knowledge Schema、首次 Admission Decision 和首次成功发布引用。

Inference ID 不包含 Snapshot、Argument、Premise Set、Depth、模型、Strategy、Confidence 或显示文本。同一结论的新 Argument 或重验证形成新 Snapshot State，不复制 Root；Conclusion、Modality 或 identity-bearing Context 实质变化创建新 Inference。

Inference Type Scheme 先构造 `Presented Inference Identity Key = (INFERENCE, owning Scope, Inference Type Identity Scheme ID, Canonical Conclusion Stable Semantic Key, Inference Identity Context Key)`。Canonical Conclusion Stable Semantic Key 包含完整类型化 Term、Operator、Condition 和 Conclusion Modality；其 Entity / Knowledge Term 使用已审核的 canonical Effective Identity Key 规范化。

`Effective Inference Identity Key` 专指 Presented Key 经身份索引和已审核 `IDENTITY_CONTINUATION` Transition Proof 解析后的唯一 Canonical Root Identity Key。CREATE 时，同 Attempt 规范化后的 Presented Key 成为候选 canonical representative；LINK 时，兼容别名必须先映射到目标 Root 的 canonical key。Proof 必须指定唯一 representative，别名只进入唯一 Alias Index，不得独立生成 Token、Root 或嵌套 Term。Schema、Contract、Canonicalizer 和 Strategy Version 不进入唯一键；跨 Schema 复用必须具有该 exact Proof。

Resolution、同 Attempt Candidate 聚合、Local Reference Substitution Manifest、Substitution-Invariant Closure Digest、Root 持久索引和数据库唯一约束必须直接复用 Effective Inference Identity Key。`Inference Semantic Identity Token = canonicalDigest(Effective Inference Identity Key)`；不得为不同阶段另建缺少 Modality、Scope 或 Context 的较弱键。

### 8.4 Resolution

| 决定 | 条件 | 结果 |
|---|---|---|
| `LINK_EQUIVALENT` | 同 Scope、曾成功发布的 Root 具有等价 Canonical Conclusion / Modality / Identity Context | 指向该 Root 并构造目标 Snapshot 的新完整 State |
| `CREATE_NEW` | Conclusion 完整，且不存在合法等价 Root | 使用 Candidate-local Inference Reference；最终发布前不分配稳定 ID |
| `KEEP_UNRESOLVED` | Conclusion、Context Identity、Schema Continuation 或等价性无法证明 | 保留候选和原因；不按文本相似或模型 Confidence 强制归并 |

Expected Current 为 PRESENT 时，LINK 可以使用 Base Snapshot 中的 Inference State；无论是否存在 Base，也可以使用带首次成功发布证明、但不属于 Base 的同 Scope Root 进行身份延续，后者不证明结论在 Base 中成立。跨 Scope Inference、裸 ID、任意历史 State 和其他 Attempt Candidate 不能成为 LINK 目标。

## 9. KNW-CONFLICT-INFERENCE-01

### 9.1 Conflict 是普通 Inference 类型

Conflict Inference 使用普通 Inference Root、State、Argument、Scope、Snapshot、依赖、准入和失效规则。它不创建 Conflict Entity、冲突 Fact、特殊存储或新的知识层，也不修改被引用 Fact。

Conflict Candidate 至少具有两个作为比较目标的 `ASSERTED` Fact Premise；必要时可以使用受控上游 Inference 作为 Context Correlation 或比较依据，但全部目标 Fact 必须直接列出并进入依赖闭包。

Conflict 的 Canonical Conclusion 必须包含全部目标 Fact 的稳定 Fact Identity Reference、Conflict Kind、比较维度和结论模态；Inference State 再把这些身份绑定到本次比较的确切 Resolved Formal Knowledge Reference。目标 Fact 集合按 Contract 规范化，不能只放在 Argument 中而让不同冲突共享同一模糊 Root。

### 9.2 三个独立判断

Conflict Argument 必须分别证明：

1. `TARGET_ALIGNMENT`：Fact Type / Conflict Contract 能把各 Fact 的 Entity、Role、Value Dimension 和 Observation Modality 映射到同一可比较目标。
2. `CONTEXT_COMPARABILITY`：在 `CONFLICT_COMPARISON` Purpose 下，相关 Context 相同或通过显式正式依据证明可比较。
3. `SEMANTIC_INCOMPATIBILITY`：在声明的 Conflict Rule 下，各 Proposition 不能同时满足；只是文本不同、值不同或来源不同不足以证明。

三项缺一不可。Context `UNKNOWN` / `NOT_COMPARABLE`、Fact 目标未对齐、模态没有比较定义或规则只表达“偏好某来源”时，不能生成 Conflict Inference。

Target Alignment 和 Context Comparability 使用的所有实例级 supporting formal reference 必须直接列为该 Conflict Inference 的 Premise，不能只藏在 Comparison Basis / Assessment 中。纯 Schema 内的版本化通用对齐规则不是实例 Premise，但必须由 Conflict Type Contract 精确引用并可重放。

### 9.3 跨模态差异

“需求声明 A”与“代码声明 B”具有不同 Observation Modality，不天然逻辑冲突。若要表达规范—实现偏差，Conflict Type Contract 必须明确：

- 哪两个命题路径应当对齐。
- “实现应符合该规范”的依据。纯通用、无实例参数的版本化 Schema Rule 可由 Conflict Type Contract 引用；针对组织、系统、接口、版本或环境的治理要求必须先发布为 Fact / Inference，并作为当前 Conflict 的显式直接 Premise。
- 允许的版本 / 环境 / 时间关系。
- 输出是 `DIVERGENCE`、`NON_CONFORMANCE`、`INCOMPATIBLE_ASSERTIONS` 或其他确切模态。

缺少应当对齐的依据时，只保留两个 Fact 和未决比较，不能借常识宣布冲突。

### 9.4 不选择赢家

Conflict Inference 必须引用全部被判定不兼容的 Fact、Comparison Basis、Context 和完整依赖，不能覆盖、删除、降权或静默隐藏任一 Fact。选择某一命题作为适用结论需要另一项具有明确政策 / 正式前提的 Inference 或应用决策；Conflict 本身不拥有 Resolution Winner。

Semantic View 和答案在目标 Context 命中已发布 Conflict Inference 时必须披露冲突及各方正式引用，不能只展示排序靠前的一方。

## 10. KNW-SEMANTIC-ENTITY-01

### 10.1 适用范围

Semantic Entity Proposal 只用于无法由 Source-native Identifier 锚定、必须由正式知识归纳其稳定身份的 Entity，例如跨系统 Business Entity 或逻辑子系统。权威业务目录能够直接提供稳定 ID 时继续使用 DD-KNW-ENTITY 的 SOURCE_ANCHORED 路径。

Semantic Category（TECHNICAL / BUSINESS）与 Identity Origin（SOURCE_ANCHORED / INFERRED）正交。本文只创建 `Identity Origin = INFERRED` 的候选，不能把缺失 Source Anchor 的技术对象随意包装为业务概念。

### 10.2 Semantic Identity Contract 与 Proposal

每种推断型 Entity Kind 必须注册版本化 Semantic Identity Contract，定义：

- 稳定 `Semantic Identity Scheme ID`、Canonical Semantic Definition 和 identity-bearing Context Projection。
- 能够形成独立身份的最小定义边界，以及哪些内容只是属性、职责、关系或显示标签。
- 允许的正式 Fact / Inference Premise 类型和必需 Fact Leaf。
- 与已有 SOURCE_ANCHORED / INFERRED Entity 的等价、碰撞、分叉和禁止合并规则。
- Schema 兼容升级、Identity Continuation 和失败语义。

`Canonical Semantic Definition Stable Key` 必须由 Semantic Identity Scheme 对完整 Canonical Semantic Definition 生成，不得用显示名称或模型摘要替代。推断型 Entity 先使用 DD-KNW-ENTITY 定义的键变体构造 Presented Entity Identity Key：

`Presented Entity Identity Key = (ENTITY, owning Scope, Entity Kind, Semantic Category, INFERRED, Semantic Identity Scheme ID, Canonical Semantic Definition Stable Key, Semantic Identity Context Key)`。

Schema、Semantic Identity Contract、Canonicalizer、Strategy 和 Model Version 只记录 Provenance，不自然形成新身份命名空间。该 Presented Key 必须按 DD-KNW-ENTITY 4.2 解析为唯一 Effective Entity Identity Key：兼容升级把别名映射到 Root 的 Canonical Root Identity Key，不兼容变化必须作出 Continuation、Fork 或 Retirement Decision。Effective Key、Entity Root 和首次成功发布证明形成 Knowledge Engine 的持久权威索引。Resolution、聚合、Semantic Identity Token、Substitution Manifest 和数据库唯一约束全部直接复用 Effective Key；Presented Alias 不得单独生成 Token。

Semantic Entity Proposal 至少固定 Candidate-local Entity Reference、owning Scope、Entity Kind / Category、Canonical Semantic Definition、Identity Context、正式 Premise Proposal、生成 Strategy 和 Provenance；不包含稳定 Entity ID。

定义以外的名称、职责、业务规则和技术映射不能塞入 Entity Root，必须由独立 Fact / Inference Conclusion 表达。

### 10.3 EntityDerivation Inference

每个 Semantic Entity Proposal 必须有一个 `ENTITY_DERIVATION` Inference Candidate，其 Canonical Conclusion 明确“该语义定义建立一个可稳定引用的 Entity Identity”，并引用 Candidate-local Entity。

- 展平依赖闭包必须包含至少一个符合 Semantic Identity Contract 的已发布 ASSERTED Fact Leaf；直接 Premise 可以全部是允许的已发布 Inference，但其闭包不能只有模型命名、Embedding Cluster 或无合格 Fact Leaf 的推理链。高风险 Entity Kind 可由 Contract 另行要求最小直接 Fact Premise 数量和类型。
- 至少一个合格 Fact Leaf 必须是独立身份锚点：其 Subject / Identity Resolution 不需要目标 INFERRED Entity，其命题不把该 Entity 作为建立自身身份所必需的 Term，且其依赖血缘不包含该 Entity 的历史 EntityDerivation。旧 Snapshot 中“关于该 Entity 的 Fact”不能反向证明同一 Entity 的身份。
- 前提只能是构建开始时已发布的正式知识；任何本轮 Fact / Inference Candidate 都不能反向证明该 Entity。
- Argument 必须证明定义边界、身份稳定性、Scope 归属、与现有 Entity 的差异及 Context。
- Business Entity 的存在不自动证明它与任何技术实现的关系；IMPLEMENTS / REPRESENTS / PERSISTS 等关系另建 Fact 或 Inference。

### 10.4 Semantic Entity Resolution

| 决定 | 条件 | 结果 |
|---|---|---|
| `LINK_SEMANTIC_ENTITY` | 同 Scope 已成功发布的 INFERRED Entity 具有等价 Effective Entity Identity Key，且 Kind / Category / Origin 兼容 | Derivation Conclusion 引用该现有 Entity；不创建新 Root |
| `CREATE_SEMANTIC_ENTITY` | 定义足以建立独立身份且无合法等价 Root | 保留 Candidate-local Entity；最终原子发布时分配 ID |
| `KEEP_SEMANTIC_ENTITY_UNRESOLVED` | 定义边界、多义性、Scope、Context 或重复判断未闭合 | 不创建占位 Entity 或 Derivation Inference |

跨 Scope 同名或语义相似 Entity 不是 LINK 目标。Business Domain Entity 归属于 Business Domain Scope，并通过确切上游 System Snapshot 的正式知识形成推导；System Scope 的技术 Entity 不复制到 Domain Scope。

语义上相关的 SOURCE_ANCHORED Entity 不是推断型 LINK 目标，因为 Entity Root 的 Identity Origin 不可改变；二者关系由单独 Fact / Inference 表达。Semantic Identity Contract 对每个命中 SOURCE_ANCHORED 索引的等价/碰撞必须得到唯一显式结果：`REJECT_AS_SOURCE_ALIAS`、`KEEP_DISTINCT_WITH_RELATIONSHIP_BASIS` 或 `IDENTITY_MIGRATION_REQUIRED`；禁止默认 LINK、默认合并或无判定地创建重复 Root。只有 Schema Core 可验证的 exact Transition Proof 才能表达既有身份模型的受控迁移。

LINK 可以使用 Expected Current 中的 INFERRED Entity State，或带首次成功发布证明、但不属于 Base 的同 Scope INFERRED Entity Root 进行身份延续。Verifier 必须独立重读 Root、首次成功发布证明、Effective Entity Identity Key 权威索引和跨 Schema IDENTITY_CONTINUATION Transition Proof；历史索引命中不能证明 Entity 在目标 Snapshot 中存在。

### 10.5 INFERRED Entity State Contract

INFERRED Entity 不伪造 Identity Anchor 或直接 Evidence。Candidate 与发布后 State 使用不同引用层级，不得在发布前伪造稳定 ID 或 Resolved Formal Knowledge Reference。

`INFERRED Entity State Candidate` 至少固定：

- Candidate-local Entity Reference、Entity Kind、Semantic Category 和 `Identity Origin = INFERRED`。
- Candidate Envelope Reference / Digest；其中固定 Target Snapshot Local Reference、Expected Current 与 Upstream Bindings，本地引用不得跨 Envelope。
- Semantic Identity Scheme Reference、完整 Presented Entity Identity Key、解析后的 Effective Entity Identity Key、Canonical Semantic Definition 及其 Stable Key、Semantic Identity Context。
- 同一 Closure 中 Candidate-local EntityDerivation Inference State Candidate Reference 及其 Output Context / Premise Closure；该引用不是 Formal Knowledge Reference。
- CREATE / LINK Resolution、历史 Root 目标与首次成功发布证明（LINK 时）、跨 Schema IDENTITY_CONTINUATION Transition Proof（如适用）、Admission Closure / Digest 和 Capability Provenance。

发布后的不可变 `INFERRED Entity State` 至少固定：

- 成功 Snapshot Reference、稳定 Entity Identity Reference、Kind / Category / Origin、完整 Presented Entity Identity Key 和解析后的 Effective Entity Identity Key。
- Semantic Identity Scheme / Definition / Stable Key、Semantic Identity Context 和 Context Verification Result。
- 同一 Snapshot 中一个 `ASSERTED ENTITY_DERIVATION` Inference 的确切 Resolved Formal Knowledge Reference；该 Conclusion 必须指向本稳定 Entity Identity，且其 Premise / Fact Leaf 闭包是当前 State 的权威身份证明。
- CREATE / LINK Resolution、首次成功发布证明（LINK 历史 Root 时）、IDENTITY_CONTINUATION Transition Proof（如适用）、Knowledge Verification / Admission Decision 和 Capability Provenance。

Semantic Identity Context 不能比身份证明更宽。必须满足：

- `PresentedEntityIdentityKey.SemanticIdentityContextKey = SemanticIdentityContract.project(verified EntityDerivation Output Context)`。
- `resolve(Presented Entity Identity Key, IDENTITY_CONTINUATION Transition Proof) = Effective Entity Identity Key`；只有解析后的 Effective Key 进入 Resolution、Token、Manifest、嵌套身份和唯一约束，Presented Key、投影结果与 Proof 必须保留用于复核。
- Entity State 的完整适用 Context 在 `SEMANTIC_IDENTITY` Purpose 下与 Derivation Output Context 等价或更窄，并保留全部 identity-bearing 维度。

Knowledge Verifier 必须从 EntityDerivation Candidate / State 重新计算该投影与 Context Comparison，并把投影结果绑定到 Admission Decision 和 Substitution-Invariant Closure Digest。`UNKNOWN`、投影不一致或 Entity Context 扩大时不得准入。

INFERRED Entity Root 保留创建时 Effective Entity Identity Key、首次成功发布引用和最小持久身份索引；它不单独证明该 Entity 属于任何当前 Snapshot。每个 `(owning Scope, Snapshot ID, Entity ID)` 至多一个 INFERRED Entity State。

新 Snapshot 要继续包含该 Entity，必须在同一 Snapshot 重验并发布合法的 EntityDerivation Inference State；不得只复制旧 Entity State 或只依赖历史 Root。推导前提失效、Context 不再适用或 Derivation 无法重验时，新 Snapshot 不发布该 Entity State，相关依赖进入影响分析；历史 Root / State 保持不变，也不自动宣告反命题。

### 10.6 原子闭包

Semantic Entity Proposal 与 EntityDerivation Inference Candidate 是一个不可拆分的 Admission / Publication Closure：

- 同一 Attempt 中具有同一待创建 Effective Entity Identity Key 的 Proposal 先解析为一个 Candidate-local Entity；等价 Derivation 可以作为该唯一 EntityDerivation Inference State Candidate 的多个 Argument，定义或 Context 无法合法聚合时按 Identity Collision 拒绝，不能并发创建两个 Root。
- Verifier 分别审核身份定义和推导结论，并检查二者引用与 Context 投影一致。Candidate-local Entity 在 EntityDerivation Conclusion 中是 `OUTPUT_BINDING`，不是 Premise Dependency；Entity State 指向该 Derivation 的关系是 `IDENTITY_SUPPORT_PUBLICATION_EDGE`，二者构成一个原子共同定义单元。Depth、展平和语义环检测只遍历 Derivation 的 Formal Premise Dependency DAG，不遍历 Output / Publication Edge；该外部 Premise DAG 必须无环。
- CREATE 时 Entity ID、Entity Root / State、Inference ID、Inference Root / State、Argument、依赖、局部引用替换、唯一键和 Snapshot CAS 同事务生效。
- LINK 时不创建 Entity Root，但目标 Snapshot 必须包含该 Entity State，并原子发布新的 Derivation Inference State。
- 任一部分拒绝、Expected Current 不匹配或发布失败时均不产生正式 Entity / Inference 半成品。

最终发布必须再次验证历史 Root 发布证明、Semantic Identity Continuation、Entity / Inference 唯一键和目标 Entity State 成员关系；发布方不能在 Verification 后改写 Semantic Definition 或 Argument。

同一 Closure 中其他 Fact Candidate 若引用该 INFERRED Entity，必须把 EntityDerivation Inference 一并纳入原子闭包；该证明 Inference 不得依赖这些 Fact Candidate 或该闭包内任何 Fact / Inference Candidate。其他 Inference Candidate 可以共享 Candidate-local Entity 作为 Conclusion Term / Output Binding，但不能互相作为语义前提。

## 11. Inference-specific Knowledge Verification

通用 Admission 流程由 DD-KNW-ADMISSION 定义；它对 Inference 至少必须从权威 Repository 独立检查：

- Inference Type、Conclusion、Modality、Entity / Premise Resolution 和 Schema 合法性。
- 所有直接前提属于固定 Snapshot 且可用，展平 Fact Leaf、Depth、Node / Edge 和 Closure Digest 完整。
- Argument 的每个步骤是否被正式前提支持，是否存在循环、自证、相关性冒充因果、范围扩大或隐藏前提。
- Output Context 是否按 Contract 构造，比较型 Context 是否保留各角色而未静默融合。
- 替代解释、已知反例、限制和生成过程发现的不利知识是否被忽略。
- 等价 Root、Identity Context、Candidate-local Entity 与最终原子闭包是否有效。

Conflict Verifier 额外独立重建 Target Alignment、Context Comparability 和 Semantic Incompatibility；Semantic Entity Verifier 额外审核身份定义、重复风险、Scope 和 EntityDerivation 闭包。

Verifier 可以沿 Premise Fact 读取 Evidence Snapshot 进行核对，但不能以 Evidence 中未正式化的新语义补写 Argument。发现正式前提缺失时返回结构化知识问题，由 Knowledge Construction 触发正常 Fact / Inference 流程；Verifier 不直接访问 Connector、不静默修改 Conclusion，也不发布知识。

独立性由权威输入重建、ModelExecutionContext、权限、判断职责和决策链隔离保证；可以使用同一基础模型，但生成 Strategy 不能审核自身 Proposal。机械校验通过、模型审核完成和最终 Snapshot 发布是三个不同状态。

## 12. KNW-INFERENCE-STATE-01 与生命周期

### 12.1 Inference State

Inference State 至少固定：

- Snapshot Reference 与 Inference Identity Reference。
- Target Knowledge Schema 和 Canonical Conclusion 解释引用。
- 每个 Entity Identity Term 的 Resolution Binding：本地 Entity 属于同一目标 Snapshot，跨 Scope Entity 属于确切 Upstream Snapshot。
- 完整 InferenceContext。
- 一个或多个分别验证的 Structured Argument。
- 直接 / 传递 Dependency Closure、Depth、Fact Leaf 和 Upstream Snapshot Dependency；本地 Premise 保存原 Construction Premise Reference 及经审核的 target Snapshot Rebinding，跨 Scope Premise 保留确切上游 Resolved Formal Knowledge Reference。
- Knowledge Verification / Admission Decision 与 Capability Provenance。

每个 `(owning Scope, Snapshot ID, Inference ID)` 至多一个不可变 State。同一 Attempt 内解析为同一已有 Inference Root，或具有同一待创建 Effective Inference Identity Key 的 CREATE_NEW Candidate，先聚合成唯一 `Inference State Candidate`，再由独立 Verifier 对完整 Conclusion、Context、Argument、Dependency / Entity Binding 闭包重新审核；Admission Decision 绑定最终 Substitution-Invariant Closure Digest 和允许的 Local Reference Substitution Manifest。无法合法聚合时拒绝 Closure，不能创建竞争 State 或后写覆盖。

Substitution-Invariant Closure Digest 对 Inference 使用 8.3 定义的 Inference Semantic Identity Token，对 Semantic Entity 使用 DD-KNW-ENTITY 4.2 定义的 Entity Semantic Identity Token。Manifest 固定每个 Local Reference 的完整 Effective Identity Key、Token 和允许 Kind / Origin；发布只补充实际 ID 映射。原始序列化 Digest 可以变化，规范语义 Digest 必须保持一致。

正常 Knowledge Use、Semantic View 和下游推理只接受 `ASSERTED` State。`PARTIAL`、`UNVERIFIED`、`REJECTED` 和普通 `CONFLICTED` 是 Candidate / Verification 结果，不是正式 State；Conflict 通过 Inference Type 表达，不是通用状态值。

### 12.2 最终发布原子性

Knowledge Verification 通过后 Candidate 仍不是正式知识。最终发布事务同时处理：

- CREATE / LINK 的 Inference Root 与唯一 State。
- Argument、Dependency Closure、Context、Entity Resolution Binding 和 Upstream Snapshot Dependency。
- Semantic Entity Closure（若有）、所有 Candidate-local 引用替换和稳定唯一键。
- 本地前提 / Entity 的目标 Snapshot 成员检查、Local Premise Rebinding 语义保持检查、`Expected Current = PRESENT(ref) | NO_CURRENT` 条件提交和 Snapshot 原子切换。

全部生效或全部不生效。发布方只能按 Admission Decision 的 Substitution Manifest 机械替换局部引用，并把发布对象重新规范化后校验 Substitution-Invariant Closure Digest 与审核值一致；首次发布只有提交时仍无 CURRENT 才能成功。若发布结果未知，按 Attempt / Idempotency Key 查询或幂等重放；确认成功前不暴露新 State，确认失败前不清理仍可能被事务引用的候选闭包。其他 Attempt 只能链接已由成功 Snapshot 发布确立的 Root。

### 12.3 重验证与上游演化

- 新 Snapshot 不原地修改旧 Inference State；要继续 ASSERT 结论，必须对目标 Snapshot 的确切前提和 Context 重建 Argument 或证明可安全继承。
- 任一直接或传递前提在目标 Snapshot 中缺失、不可用、语义变化或 Schema 不兼容时，旧 Argument 不能直接继承。
- 上游 Scope 发布新 CURRENT 不改写下游已发布 State；它仍绑定原上游 Snapshot，同时产生符合 `KNW-REVALIDATION-SIGNAL-01` 的 Dependency Freshness 诊断。
- 下游在完成重验证前继续明确绑定旧上游 Snapshot；若新的本地 Snapshot 已不能证明该结论，则不选择该 State，并在本次构建的非正式影响记录中披露原因。禁止静默重绑新 CURRENT。
- 结论失去支持不等于其反命题成立。目标 Snapshot 无法重验时不发布该 Inference State，只记录 `KNW-REVALIDATION-SIGNAL-01`；不新增 `UNSUPPORTED / UNVERIFIABLE` 正式状态。
- 同一 Conclusion 后续获得新 Argument 时复用稳定 Root，但在新 Snapshot 中形成完整唯一 State。

Inference Root 与稳定 Identity Key 的最小索引在历史 State 退出后仍须保留，以支持身份延续；它不证明结论在 CURRENT 或任意 Snapshot 中成立。

## 13. Scope 与跨系统规则

1. 每个 Inference 和 INFERRED Entity 恰好一个 owning KnowledgeScope。
2. Expected Current 为 PRESENT 时，本 Scope 前提来自该 Base Snapshot；NO_CURRENT 时无本地正式前提。本地前提和 Entity 在发布时都必须重绑目标 Snapshot。
3. 跨 Scope 前提和 Entity 固定确切 Upstream Snapshot，并进入目标 Snapshot 依赖；不复制上游状态。
4. Business Domain Scope 可以依赖多个 System / Shared Component Snapshot，归纳跨系统 Business Entity 和关系；各上游技术身份保持原 Scope。
5. Scope 之间不做全局 Inference 去重、不使用分布式发布事务，也不随上游 CURRENT 静默移动。
6. 一个下游 Inference 的 Context、Modality 和结论范围不能无依据地超过任一必要上游前提。

## 14. AI Native Capability 与评测

### 14.1 模型适合承担

- 开放式归纳、业务语义理解、跨来源关联、因果与替代解释分析。
- 从正式知识中构造复杂 Conclusion 和 Structured Argument。
- 发现反例、遗漏前提、Context 限制、Conflict Candidate 和 Semantic Entity Proposal。
- 在有界候选集合中提出等价 Conclusion / Entity Identity 和补充知识需求。

### 14.2 平台不可让渡

- Scope、Schema、Snapshot、正式引用、Dependency DAG 和 Depth。
- Canonical Conclusion / Identity、Entity Binding、Context 不扩张和候选闭包。
- 正式前提类型、无环有界门禁、独立 Verification 和原子发布。
- Conflict 三项判断的结构完整性、Semantic Entity 原子性和历史不可变性。

模型增强后可以减少固定业务规则、手工关系模板和浅层推理限制；不能取消正式前提、Context、依赖链、独立审核和 Snapshot。确定性逻辑在更准确、可重放且成本更低时继续作为 Tool / Strategy，不因 AI Native 被强制移除。

### 14.3 Capability Evaluation

Inference Construction、Conflict Assessment、Semantic Entity Resolution 和 Inference Verification 分别具有 Capability / Evaluation Contract。评测至少覆盖：

- Conclusion correctness、正式前提忠实性、范围扩大和隐藏前提率。
- 相关性/因果性混淆、Context 组合、未知校准、反例遗漏和不确定模态保真。
- Dependency Depth / Closure 正确性、循环、自证和级联失效。
- Conflict 的 Target Alignment、Context Comparability、False Conflict / Missed Conflict 和赢家偏置。
- Semantic Entity 的 False Merge / Split、无依据身份、Scope 错误和业务—技术映射越权。
- 跨项目、跨任务、跨模型版本的直接 Agent 非回归、成本、延迟和深度收益。

`MaxInferenceDepth`、默认 Strategy 和风险门禁根据 Evaluation Activation 选择，不在一般设计中固定。更深推理只有在真实任务收益超过准确性、成本和失效传播风险时才能晋升。

## 15. 失败、重试与并发

| 类别 | 处理 |
|---|---|
| PREMISE_REFERENCE_INVALID | 不执行推理；不回退 CURRENT、名称或裸 ID |
| PREMISE_NOT_ASSERTED / NOT_USABLE | 不作为正式前提；返回知识缺口或重验证需求 |
| CANDIDATE_AS_PREMISE | 拒绝整个依赖分支；先发布上游知识后开启新 Attempt |
| INFERENCE_TYPE_UNSUPPORTED | 保留 Hypothesis；不降级为自由文本 Inference |
| ARGUMENT_INCOMPLETE / UNSUPPORTED_STEP | 不准入；返回结构化修正或补充正式知识需求 |
| HIDDEN_PREMISE / SELF_SUPPORT | 拒绝并审计 |
| DEPENDENCY_CYCLE | 拒绝整个相关 Closure |
| DEPTH / NODE / BUDGET_LIMIT | 有界停止并返回未完成；不能截断后发布部分 Argument |
| CONTEXT_COMPARISON_UNKNOWN / FAILED | 需要共同成立的推断失败关闭；比较型推断按 Type Contract 保留未决 |
| CONCLUSION_IDENTITY_AMBIGUOUS | KEEP_UNRESOLVED，不按文本相似强并 |
| CONFLICT_TARGET_UNALIGNED | 不产生 Conflict；保留独立 Fact |
| CONFLICT_CONTEXT_NOT_COMPARABLE | 不产生 Conflict；不把 Context 差异当矛盾 |
| CONFLICT_INCOMPATIBILITY_UNPROVEN | 不产生 Conflict；不得选择来源赢家 |
| SEMANTIC_ENTITY_UNSUPPORTED / COLLISION | 不创建 Entity 或 Derivation Inference |
| UPSTREAM_SNAPSHOT_UNAVAILABLE | 不静默重绑新 CURRENT；按依赖政策失败或显式不可用 |
| EXPECTED_CURRENT_MISMATCH | 实际 CURRENT 与 PRESENT(ref) 或 NO_CURRENT 期望不一致；当前 Closure 不发布，基于新观察创建新 Attempt |
| ADMISSION_REJECTED | 不创建 Root / State；保留审计和结构化问题 |
| PUBLICATION_OUTCOME_UNKNOWN | 按 Attempt / Idempotency Key 查询或重放；不暴露半成品 |
| STRATEGY_FAILED / MODEL_UNAVAILABLE | 按激活政策有界重试或回退；不得降低依赖和审核门禁 |

- 相同冻结输入和幂等键返回同一 Construction / Resolution Result；Premise、Schema、Context、Expected Current / Upstream Snapshot、Policy 或 Strategy 变化产生新 Attempt。
- 模型重试产生新 Capability Attempt 和完整 replacement Proposal，资源消耗不回滚。
- Inference / Semantic Entity 唯一性、State 唯一性和 Snapshot CAS 使用 Knowledge Engine 最终事务，不依赖应用层先查后写。
- Hypothesis、Candidate、Partial Argument、`KNW-REVALIDATION-SIGNAL-01` 和 Identity Reservation 不能被正常 Knowledge Use 当作正式知识查询。

## 16. 可观测性、资源与敏感信息

- 传播 Task / Run、Build Intent、Candidate / Attempt、Inference Type、Premise / Fact Leaf、Context、Argument、Dependency、Conflict / Semantic Entity、Verification、Snapshot、Capability / Strategy / Model Call 关联。
- 记录 Proposal、Argument Step、Depth、Node / Edge、Context 比较、反例、Conflict 三项判断、Entity Merge / Split、重试和资源消耗。
- Telemetry 不复制 Evidence Quote、Artifact Payload、受保护 Proposition、Secret 或模型隐藏思维链；保存稳定引用、结果分类、Digest 和审计定位。
- Structured Argument 和 Conclusion 按 Scope、Snapshot、用途和数据分类授权；稳定引用不是读取凭证。
- 模型 Confidence、Evaluation Score、Agent Trace 和 Verifier 解释不是正式前提或 Context Basis。

## 17. 拟议不变量

1. Inference 只以已发布 ASSERTED Fact 和受控上游 Inference 作为语义前提；Evidence、Artifact、Entity 状态和 Candidate 不能成为前提。
2. 每个 Inference 依赖非空 Fact Leaf 闭包，依赖有界、无环、可展平并可随上游变化重验证。
3. Candidate Fact / Inference 不能成为本轮 Inference 前提；局部引用只服务 Semantic Entity 身份替换和原子提交。
4. Inference Conclusion、Modality 和 Context 必须完整表达用户可见语义；Argument、Evidence 和 Projection 不能补写未声明内容。
5. 模型 Confidence 不等于 Epistemic Modality，也不能自动决定准入。
6. Structured Argument 公开可审核前提与语义步骤，不保存或依赖模型私有 Chain-of-Thought。
7. InferenceContext 不得无依据超出前提；比较不同 Context 时保留各自角色，不强制融合。
8. 最大推理深度是每次执行固定、经评测激活的有限策略参数，不是永久两级常量或无限递归。
9. Inference Root 以 Canonical Conclusion 和 identity-bearing Context 稳定去重；Argument、Premise、模型和 Snapshot 不进入稳定 ID。
10. 每个 Snapshot 中同一 Inference Root 至多一个 State；等价 Candidate 只有分别验证并合法聚合后才能共享该 State。
11. Conflict 是普通 Inference 类型，必须分别证明目标对齐、Context 可比和语义不兼容；Fact 共存、来源或 Context 不同本身不构成冲突。
12. Conflict 不选择赢家、不修改 Fact，也不创建特殊 Entity、存储或知识层。
13. 推断型 Entity 与 EntityDerivation Inference 同一无环闭包原子准入；证明必须展平到已发布 Fact，不能依赖本轮任何 Candidate。
14. Business Domain Entity 归属 Domain Scope，上游系统技术身份和正式知识只通过确切 Snapshot 引用参与推导。
15. 本地 Entity / Premise 在发布时属于目标 Snapshot；跨 Scope 引用固定上游 Snapshot，任何路径都不保存动态 CURRENT。
16. Stable Inference / Semantic Entity Identity、State、Argument、依赖、局部替换、唯一键和 Snapshot CAS 在同一最终发布事务中生效。
17. 上游 CURRENT 变化不改写已发布 Inference；通过显式 Freshness、重验证和新 Snapshot 受控收敛。
18. 模型可以主导推理和审核，但不能自报正式引用、依赖闭包、稳定 ID、准入或发布状态。

## 18. 验证义务与下游追溯

当前无需 Design Validation Demo 决定正式前提、Candidate 禁止依赖、有界无环、Conflict 三项判断和 Semantic Entity 原子闭包；这些约束可由概要架构不变量静态推出。

进入具体 Inference Type 实现前必须建立 Contract Conformance：

- Conclusion / Modality / Identity / Context Canonicalization 与 Schema Continuation。
- Direct / transitive Dependency、Fact Leaf 展平、Depth、循环和 Closure Digest。
- 普通、比较、History 和 ContextCorrelation 的 Output Context。
- Conflict Target Alignment、Context Comparability、Semantic Incompatibility 和不选择赢家。
- Semantic Entity Definition、重复身份、Fact Leaf 证明、局部引用和原子发布。
- 等价 Candidate 聚合、上游变化、结果未知和幂等重放。

进入默认 Strategy 激活前必须建立 Capability Evaluation，并使用未见项目与同模型直接来源调查基线比较结论正确性和任务完成度。最大深度、具体 Conflict Rule 或 Semantic Identity Strategy 若存在会改变正式契约且静态分析无法判定的可实现性问题，再按 AD-126 建立有界 `DVR-*` Demo；Demo 结果不自动成为生产算法或阈值。

下游主题必须引用本文而不能重新定义：

- DD-KNW-ADMISSION：独立 Verifier、Candidate Closure、Conflict / EntityDerivation 附加门禁。
- DD-KNW-SNAPSHOT-PUBLICATION：依赖、跨 Scope Binding、Freshness 和原子发布。
- DD-KNW-PERSISTENCE：权威 Conclusion / Argument / Dependency State 与可重建 Projection。
- DD-KNW-SCHEMA-EVOLUTION：Inference / Semantic Entity Identity Continuation 和依赖重验证。
- DD-APP-KNOWLEDGE-USE：只使用固定 Snapshot 的 ASSERTED Conclusion，并完整披露已发布 Conflict。
