# Fact 详细设计

| 元数据 | 值 |
|---|---|
| Document ID | DD-KNW-FACT |
| Version | 0.1.0 |
| Status | Accepted |
| Document Steward | Knowledge Engine |
| Architecture Baseline | SWM-ARCH@1.2 |
| Depends On | DD-KNW-REFERENCE-CONTEXT@0.1.0、DD-KNW-SCHEMA-CORE@0.1.0、DD-KNW-CONTEXT-COMPARISON@0.1.0、DD-KNW-EVIDENCE@0.1.0、DD-KNW-ENTITY@0.1.0、DD-X-CAPABILITY-EXECUTION@0.1.0、DD-AI-MODEL-GATEWAY@0.1.0、DD-MGT-CAPABILITY-EVALUATION@0.1.0 |
| Owns Contracts | KNW-FACT-TYPE-01、KNW-FACT-01、KNW-FACT-EVIDENCE-LINK-01、KNW-FACT-RESOLUTION-01、KNW-FACT-STATE-01 |
| Supersedes | None |
| Rationale ADR | AD-002、AD-003、AD-007 至 AD-009、AD-017、AD-018、AD-026、AD-027、AD-029、AD-030、AD-087、AD-088、AD-091、AD-095、AD-096、AD-108、AD-111、AD-113、AD-115、AD-121、AD-123、AD-126、AD-128 |
| Design Validation | None |
| Conformance Cases | None |
| Capability Evaluation | None |

> 概要架构约束直接生效；本文新增的 Fact Type、Proposition、Evidence Link、Resolution 和 Fact State 语义在状态进入 `Accepted` 前均为拟议设计。

## 1. 目的与范围

Fact 表达平台在明确 KnowledgeContext 下接受的、能够由直接 Evidence 独立复核的客观命题。本文解决同一来源观察如何形成完整命题、多个 Evidence 如何支持同一 Fact、等价命题如何复用稳定身份，以及互不兼容的来源观察如何在不选择“全局真相”的前提下分别保留。

本文定义：

- Fact 与 Evidence、Entity、Inference 的认知边界。
- Fact Type Contract、规范命题、来源观察模态和直接支持规则。
- Fact Candidate、FactEvidenceLink、Support Set、Fact Resolution 和稳定身份。
- FactContext 的形成、跨 Scope 引用、Snapshot-local Fact State 和最终发布边界。
- 模型 Fact Construction / Resolution Strategy 与平台可信控制的分工。

本文不定义：

- Inference 推导、Conflict Inference 或推断型 Entity 身份。
- Knowledge Verifier 的通用准入工作流和 Snapshot 的完整发布协议。
- Schema 迁移、历史 Snapshot 保留和物理 Projection。
- 特定语言、数据库、日志或文档的 Fact Type 字段、抽取 Prompt、置信阈值或存储表结构。

## 2. Fact 的认知边界

### 2.1 客观命题不等于绝对真相

Fact 的“客观”表示：在固定来源语义、Context 和版本化 Fact Type Contract 下，独立审核者能够从直接 Evidence 重放并核对整个命题；它不表示平台发现了跨来源、跨环境和跨时间的唯一现实真相。

因此必须保留来源观察模态：

| Evidence 呈现 | 合法 Fact 语义 | 不能直接扩张为 |
|---|---|---|
| 代码声明了路由 | 某代码对象在该 Revision 声明路由 `/x` | `/x` 已部署并可用 |
| Trace 观察到一次调用 | 在该运行观察条件内出现 A 到 B 的调用 | A 在所有版本中必然调用 B |
| 需求文档规定某规则 | 该文档版本声明了该规则 | 当前实现符合该规则 |
| DB 元数据记录一项约束 | 该数据库观察条件下记录了该约束 | 所有环境都具有该约束 |
| 封闭查询返回零项 | 该确切范围和一致性条件下返回零项 | 对象在任何地方都不存在 |

来源权威性、实现是否符合文档、行为目的、业务含义、跨来源等价和因果解释都不是上述直接观察的隐含部分；它们需要独立 Fact 或 Inference。

### 2.2 Fact / Inference 判定

一个命题只有同时满足以下条件才具有 Fact 资格：

1. 命题的每个语义元素都被一个或多个直接 Evidence 的确切内容明示蕴含。
2. Locator、Quote / Typed Value、Digest、Context、引用和规范化由平台机械重建；Evidence 是否明示蕴含某个语义元素可以由受评测的 Model-Primary / Hybrid Strategy 提议，并由隔离的 Knowledge Verifier 重读原文审核。
3. 命题不依赖未明示的目的、意图、因果、业务归纳、跨来源等价、开放世界完整性或其他正式命题作为语义前提。
4. FactContext 不比支持它的 Evidence Context 更宽，所有 Context 组合都能仅凭输入 OBSERVED Term 与版本化机械规则复核；需要其他正式知识作为 Context Basis 时结果进入 Inference。

模型可以生成满足这些条件的 Fact Proposal；确定性程序也可能生成超出这些条件的语义结论。Fact / Inference 分类只取决于认知性质和支持关系，不取决于生成者。

“直接”不是“只能由确定性代码抽取”。模型可以理解需求文本、日志语句或代码语义，但只能识别 Evidence 已经表达的内容；一旦补充了归纳、目的、因果、跨来源对应或其他外部前提，结果就不再是 Fact。

### 2.3 Entity 只提供身份

Fact 的 Entity Reference 只证明命题中的对象身份可稳定引用。Entity 名称、Kind、Anchor 或 State 定位元数据不能替代 Evidence 去证明属性、关系、行为或业务含义。Fact Candidate 对这些实质语义仍必须具有直接 Evidence。

## 3. 逻辑对象与所有权

| 对象 | Owner | 权威性质 |
|---|---|---|
| Fact Construction Proposal | Construction Strategy / Investigation | 不可信的命题、Context 与 Evidence 映射建议 |
| Fact Candidate | Knowledge Engine Candidate Area | 平台重建、仍待独立 Knowledge Verification 的完整候选 |
| FactEvidenceLink Candidate | Knowledge Engine Candidate Area | Evidence 对某候选命题的作用和覆盖建议；尚未正式接受 |
| Fact Resolution Result | Knowledge Engine | 对规范命题身份的 LINK / CREATE / UNRESOLVED 判断；不是准入结果 |
| Fact Root | Knowledge Engine | 稳定、不可变的规范命题身份；只有进入确切 Snapshot 的 State 才能支持使用 |
| Fact State | Knowledge Engine | 某 Snapshot 中 Fact 的完整 Context、Support Set、Context Constraint Set 和可用性 |
| FactEvidenceLink | Knowledge Engine | Evidence 相对于确切 Fact 命题/State 的经验证作用；不是 Evidence 的属性 |
| Support Set | Knowledge Engine | 在一个明确 Context 下完整覆盖 Fact 命题的最小 Evidence Link 集合 |

模型、Agent、Evidence Extractor、Projection 和 Source Integration 都不能分配稳定 Fact ID、改变 Fact Root、接受 Evidence Link 或发布 Fact State。

## 4. KNW-FACT-TYPE-01：Fact Type Contract

### 4.1 语义 Schema

每种 Fact Type 必须由目标 Knowledge Schema 注册版本化 Contract，至少定义：

- 稳定的 `Fact Type Identity Scheme ID` 和语义名称空间。
- Observation Modality，即命题声明的是代码定义、运行观察、文档陈述、配置观察、封闭查询结果或其他来源限定语义。
- 命题 Role、Term 类型、基数、必填条件、顺序语义和允许的逻辑结构。
- Entity Kind / Scope 约束、Typed Literal 的单位、枚举、精度和规范化规则。
- Canonical Proposition、等价、不可兼容和非法命题的机械判定边界。
- `Identity-bearing Context Projection` 及其 `Fact Identity Context Key` 生成规则。
- 不改变 Fact 身份但必须保留在 Fact State 的 Applicability Context 维度。
- 每个命题路径可接受的 Evidence Representation、Direct Observation Rule 和 Coverage Rule。
- 允许多 Evidence 组成完整直接支持时的可重放 Composition Rule。
- 供后续 Conflict 主题使用的可比较目标、维度和值域；它不直接宣布两个 Fact 冲突。
- Schema / Contract / Canonicalizer 的兼容升级、显式迁移和失败语义。

Fact Type Contract 不能把自由文本解释、模型置信度或“通常如此”注册为机械规则。需要开放式语义判断时，模型可以提出 Proposal，但正式结论仍按 Fact 直接性或 Inference 依赖规则分类。

### 4.2 命题不受三元组限制

Canonical Proposition 是受 Schema 约束的类型化命题，可以是一元属性、二元关系、多角色关系、带条件的记录或有界逻辑结构。例如条件分支、调用参数绑定和数据库复合约束不必被拆成会丢失语义的若干三元组。

图三元组、搜索字段、自然语言摘要和显示标签都只是 Projection。它们可以从 Canonical Proposition 重建，但不能增加、删减或替代正式命题语义。

### 4.3 来源模态是命题组成部分

Observation Modality 参与 Canonical Proposition 的语义身份。`DOCUMENT_DECLARES(rule)`、`CODE_DECLARES(rule)` 和 `RUNTIME_OBSERVED(rule)` 即使文本相同也不是等价 Fact。只有 Fact Type Contract 明确证明两个表示属于同一模态和等价规则时才能归并。

## 5. KNW-FACT-01：Fact Proposition 与稳定身份

### 5.1 Canonical Proposition

Canonical Proposition 至少固定：

- Fact Type Identity Scheme ID 和 Observation Modality。
- 有名 Role 及其规范 Term；不能依赖字段顺序猜测角色。
- 至少一个语义目标 Entity Term。Candidate 构建时它使用已发布 Entity 的 Resolved Formal Knowledge Reference，或同一原子 Candidate Closure 内的 Candidate-local Entity Reference；最终 Canonical Proposition 只保存稳定 Entity Identity Reference。
- 影响命题含义的条件、量词、比较符、单位、值域和否定边界。
- Fact Identity Context Key。
- Canonical Proposition Digest 和构造 Contract / Canonicalizer Version。

Term 可以是 Entity Identity Reference、Typed Literal、Schema-defined Value Object 或有界结构。未解析名称、Source Path、模型生成显示名和自然语言代词不能充当正式 Entity Term；它们只能留在 Proposal 或 Investigation 中。

Resolved Formal Knowledge Reference 中的 Snapshot 只证明构建时 Entity 在确切本地或上游 Snapshot 中存在，不进入 Fact Root 的 Proposition 身份。Fact State 必须保存每个 Entity Identity Term 对应的确切 Resolution Binding；因此上游发布新 Snapshot 不会仅因 Snapshot ID 变化创建新 Fact Root，但使用新上游 Snapshot 前仍必须重验证 Entity 存在、语义兼容和整个 Fact State。

否定命题只有在 Evidence 对目标范围具有经过验证的完备观察能力时才有 Fact 资格。普通空搜索、缺少命中或本轮未采集不能形成否定 Fact。

### 5.2 Fact Root

Fact Root 至少固定：

- owning KnowledgeScope ID。
- 不透明稳定 Fact ID。
- Fact Type Identity Scheme ID 和 Canonical Proposition。
- Fact Identity Context Key。
- 创建时 Knowledge Schema Reference 与首次 Admission Decision Reference。
- 首次成功发布的 Snapshot / Publication Receipt Reference；Root 只有与该首个 Fact State 和 Snapshot 发布原子成功后才存在。

Fact ID 不包含 Snapshot、Evidence 数量、Source Revision、模型、Prompt、Strategy、显示文本或当前状态。ID 由 Knowledge Engine 在目标 Snapshot 最终发布事务中分配，不能由模型提供，也不直接使用 Proposition Digest 作为公共 ID。

Fact Root 不保存“当前为真”、Confidence、冲突状态或当前 Evidence；这些都不能成为跨 Snapshot 稳定身份的一部分。Root 一旦创建不可改写 Proposition。语义变化创建新 Fact；语义兼容的再次观察复用同一 Root 并形成新 Fact State。

为支持身份延续，成功发布过的 Fact Root、Canonical / Alias Effective Fact Identity Key 索引和首次成功发布证明在历史 State 退出后仍保留最小权威记录。它只证明该 Root 曾被某个成功 Snapshot 创建，不证明 Fact 在 CURRENT 或任意目标 Snapshot 中为 ASSERTED。

### 5.3 稳定唯一键

Fact Type Scheme 先以下列完整元组构造 `Presented Fact Identity Key`：

- `(FACT, owning Scope, Fact Type Identity Scheme ID, Canonical Proposition Stable Semantic Key, Fact Identity Context Key)`。

`Canonical Proposition Stable Semantic Key` 必须由 Fact Type Contract 对完整类型化命题生成，包含经规范化的 Role / Term、Operator、Condition、Quantifier 和 Observation Modality；不得用显示文本、Argument 或某一个 Entity ID 的偶然序列化替代。Entity Term 以已审核的 Effective Entity Identity Key 进入规范语义键，使 Candidate-local Reference 和发布后 ID 表示同一命题。

`Effective Fact Identity Key` 专指 Presented Key 经身份索引和已审核 Continuation Decision 解析后的唯一 Canonical Root Identity Key。CREATE Candidate 没有现有 Root 时，同 Attempt 内规范化后的 Presented Key 成为候选 canonical representative；LINK 时，所有兼容别名先映射到目标 Root 的 canonical key。Continuation Decision 必须指定唯一 representative，别名只进入唯一 Alias Index，不得独立生成 Token、Root 或嵌套 Term。

Knowledge Schema、Fact Type Contract、Canonicalizer Version 和发现 Strategy 不进入唯一键。兼容升级必须继续得到同一 Effective Key，或通过 exact IDENTITY_CONTINUATION Transition Proof 映射到原 canonical representative；不兼容升级必须重建、分叉或停止延续，不能仅靠版本变化自然创建重复 Fact Root。

Resolution、同 Attempt Candidate 聚合、Local Reference Substitution Manifest、Substitution-Invariant Closure Digest、Fact Root 索引和数据库唯一约束必须直接复用 Effective Fact Identity Key，不得各自派生较弱键。`Fact Semantic Identity Token = canonicalDigest(Effective Fact Identity Key)`。

## 6. Fact Candidate 构建

### 6.1 冻结输入

一次 Fact Construction 至少固定：

- `KNW-CANDIDATE-ENVELOPE-01`：Build Intent / Application Attempt References、target Scope / Schema、Target Snapshot Local Reference、Expected Current 与 Upstream Bindings。首次构建必须显式使用 `NO_CURRENT`。
- 已成功物化的不可变 Evidence Reference、当前 Construction 用途下的可复核性结果，以及其 KnowledgeContext、Source Root、Observation 和 Provenance Closure。
- 当 Expected Current 为 PRESENT 时，该 Base Snapshot 中的 Resolved Entity Reference；NO_CURRENT 时本地已有正式 Entity 集合为空。
- 同一 Candidate Closure 中已重建的 Candidate-local Entity Reference。SOURCE_ANCHORED Entity 携带完整 Identity Candidate；INFERRED Entity 还必须携带同一闭包中的 EntityDerivation Inference Candidate。
- 允许的确切 Upstream Snapshot Binding 与 Resolved Upstream Entity Reference。
- Capability Catalog Snapshot、Execution Envelope、exact Construction Strategy、`PRODUCTION Activation | EVALUATION_ONLY Grant` 和资源分配。

Fact Construction 不读取 Source Operation Result、Artifact Payload、Agent 对话或模型记忆。需要新增来源内容时回到标准 Evidence Materialization；Knowledge Engine 不建立直接来源旁路。

平台重建的每个 Fact State Candidate 必须携带 exact Candidate Envelope Reference / Digest；Candidate-local Entity 只可来自同一 Envelope，并通过 Admission 的 Directed Publication Prerequisite 进入 Manifest。

只有 `PRODUCTION` Catalog 且 post-call model eligibility 通过时，重建结果才能进入生产 Candidate Envelope / Bundle。`EVALUATION_ONLY` 只返回隔离 Evaluation Output，不创建可准入的 Fact State Candidate。

Evidence Reference 自身绑定创建它的 Knowledge Schema。它与目标 Fact Schema 不同时，只有 Schema Core 的 exact `EVIDENCE_INTERPRETATION` Transition Proof 完整绑定源 / 目标 Schema、Evidence Representation、Locator / Observation Contract 和允许的重解释范围，才能复用；否则必须从仍可用 Artifact / Source 重新物化目标 Schema 的 Evidence。Fact Construction 不能用新 Fact Type Contract 静默解释旧 Evidence。

### 6.2 Proposal 与平台重建

模型或确定性 Strategy 可以提出：

- Proposal-local Fact Key、Fact Type 和 Observation Modality。
- 命题 Role / Term 及 Candidate-local / Resolved Entity Reference。
- Evidence Reference、覆盖路径、关系类型和 FactContext Proposal。
- 可能的等价 Fact、替代命题、未决项和补证需求。

Knowledge Engine 必须从权威 Repository 重新构造：

1. Scope、Schema、Expected Current / Upstream Snapshot Binding 和所有 Entity Reference。
2. Evidence 内容、Locator、Observed Content / Observation Digest、Context 和 Provenance Closure。
3. Fact Type Contract、Canonical Term、Proposition 和稳定语义键。
4. 每条 Evidence Link 的关系、Coverage Map 和支持 Context。
5. 完整 Support Set、FactContext 和身份 Context Key。
6. Fact Resolution Result、Candidate-local Fact Reference 和完整 Provenance。

模型自报的 Quote、Digest、Scope、Context、稳定 Fact ID、Evidence 独立性、直接支持完整性、等价关系或 Admission 状态均不可信。未知字段、重复局部 Key、越界引用和不支持的 Fact Type 拒绝相关完整 Proposal；修正使用 replacement Proposal，不原地修改旧输出。

### 6.3 Hypothesis 与 Candidate 的边界

只有满足以下最低条件时平台才构造 Fact Candidate：

- Proposition 按 Fact Type Contract 完整且可规范化。
- 所有 Entity Term 已解析为合法正式引用或同一原子 Closure 内的局部引用。
- 至少存在一个直接 Evidence Link，且存在能够覆盖整个命题的合法 Support Set。
- FactContext 可构造，且没有被 Evidence Context 无依据地扩大。
- Candidate-local INFERRED Entity 的证明 Inference 已进入同一原子候选闭包；其全部语义 Premise Dependency DAG 必须无环，且只能引用 Expected Current（若存在）或确切 Upstream Snapshot 中的 Resolved Formal Knowledge Reference。Candidate-local Entity 在 Derivation Conclusion 中只是 Output Binding，不是语义前提；Derivation 不能依赖任何本轮 Fact / Inference Candidate。

缺少 Evidence、身份未解析、命题语义不完整或仍需开放式前提的结果是 Investigation Hypothesis / Fact Clue，不是“部分正式 Fact”。它可以驱动补充调查，但不能进入 Knowledge Admission、Snapshot 或正常 Knowledge Use。

## 7. KNW-FACT-EVIDENCE-LINK-01

### 7.1 Link 关系

Evidence 本身中立；作用只存在于“该 Evidence 相对于该确切 Proposition”的 Link 中：

| Relation | 语义 | 对 Fact 成立的作用 |
|---|---|---|
| `DIRECT_SUPPORTS` | Evidence 在自身 Context 下直接呈现 Link 指定的命题语义 | 可以进入 Support Set |
| `PARTIALLY_SUPPORTS` | Evidence 只直接覆盖命题的明确子路径 | 只有与合法 Composition Rule 下的其他 Link 完整覆盖时才可进入 Support Set |
| `CONTEXT_LIMITS` | Evidence 直接证明命题只能在更窄条件下复核 | 收窄 Support Context；不能单独证明命题 |
| `CONTRADICTS` | Evidence 直接支持一个与目标 Proposition 不兼容的替代观察 | 触发替代 Fact Candidate 与目标 Fact 重验证；不自动形成正式冲突 |

`CONTRADICTS` 是 Evidence Link 的直接观察判断，不是“两个正式 Fact 存在冲突”的用户可见 Claim。后者只能由完成准入的 Conflict Inference 表达。

### 7.2 Link 内容

FactEvidenceLink 至少固定：

- 目标 Candidate-local Proposition，或已发布后的 `Resolved Formal Knowledge Reference(kind=FACT)`；后者等价于 Snapshot Reference 与 Fact Identity Reference 的组合，不另创第三种公开引用层级。仅用于触发重验证、但尚未进入新 Snapshot State 的评估可以指向稳定 Fact Identity Reference，并按 `KNW-REVALIDATION-SIGNAL-01` 形成诊断；它不是可供正式知识使用的 FactEvidenceLink。
- 一个 Evidence Reference；Link 不拼接 Evidence 内容。
- Relation 和逐命题路径的 Coverage Map。
- Evidence Context、Link Support Context 与必要 Context Assessment Reference。
- Observation Modality、Direct Observation / Composition Contract Reference。
- Evidence Source Root、Observation、Lineage 和 Acquisition Closure 摘要引用。
- Link Verification、Capability / Strategy / Execution 和构造 Provenance。

Link 不保存全局 Evidence 置信度、来源排名或“真值概率”。同一 Evidence 对不同 Proposition 可以具有不同 Link；一个 Link 只能针对一个确切 Proposition 解释。

正式 Link 按作用具有不同归属：

- `DIRECT_SUPPORTS` / `PARTIALLY_SUPPORTS` 属于确切 Fact State 的 Support Set。
- `CONTEXT_LIMITS` 属于该 State 的 Context Constraint Set；它只收窄相应 Support Set，不能脱离被约束 Link 存在。
- `CONTRADICTS` 属于当前 Attempt 的 Revalidation Record，并优先指向它正向支持的替代 Candidate。它不进入原 Fact State 的支持闭包；若替代 Fact 发布，正式冲突仍由后续 Conflict Inference 表达。

Support Set、Context Constraint Set 和它们引用的 Link 都随确切 Fact State 不可变，不能在新 Evidence 到来时追加到旧 Snapshot。Revalidation Record 是可审计构建状态，不是 Snapshot 正式知识成员或答案依据。

### 7.3 Support Set 与完整覆盖

每个可用 Fact State 至少具有一个经验证的 Support Set。一个 Support Set：

- 固定一个 Fact Proposition 和一个明确 Support Context。
- 包含一条或多条 `DIRECT_SUPPORTS` / `PARTIALLY_SUPPORTS` Link，并引用适用于它的 Context Constraint Set。
- 对 Fact Type Contract 要求的每个语义路径恰当地提供直接覆盖。
- 不依赖 Link 之间未声明的语义补全或开放式推理。
- 保留所用 Composition Rule 和逐路径覆盖证明。
- 对 Coverage 而言是最小集合：移除任一 Link 都会失去必要语义路径或合法 Context 约束。独立的完整佐证形成另一个 Support Set，不能把无必要 Link 填入同一集合制造“证据更多”的外观。

一条完整、可复现的 Evidence 可以单独形成 Support Set。多个 Evidence 只有在 Fact Type Contract 声明了版本化、可回放的 Composition Contract、Context 可合法共同成立且全部语义路径被覆盖时，才能共同形成一个 Support Set。每个 Evidence 到命题路径的明示蕴含可以由模型识别并独立语义审核；平台仍机械验证引用、范围、覆盖拓扑和 Context。需要模型补写跨来源对象等价、因果、目的或其他未由 Evidence 明示的关系时，结果必须进入 Inference，不得以“多证据”名义包装成 Fact。

### 7.4 多 Evidence 不等于投票

等价 Proposition 可以具有多个 Support Set 或在同一 Support Set 中使用多个 Evidence，但：

- Evidence 数量不产生真值、Confidence 或多数票。
- 同一 Artifact、Source Root、Observation、复制内容或 Derived 分片默认不构成独立佐证。
- 只有具体 Fact Validation Policy 要求交叉佐证时，才计算本次 Candidate 的 Provenance / Observation Independence；平台不维护脱离用途的全局“独立性分数”。
- 交叉佐证改善可复核性或满足风险政策，不扩大 Proposition 或 FactContext。

这使简单 Fact 不必为了“设计完整”强制收集多个来源，同时避免把重复 Evidence 当作增强。

### 7.5 替代观察

当 Evidence 直接支持与已有 Fact 不兼容的替代 Proposition 时，Knowledge Construction 应为替代 Proposition 构造独立正向 Fact Candidate，并可同时记录对原 Fact 的 `CONTRADICTS` Link。以下规则同时成立：

- 替代 Candidate 按自己的 Evidence、Context、Fact Type 和 Support Set 接受审核。
- 原 Fact 不被覆盖、改写或自动标记为错误。
- 两个可分别复核的替代 Fact 可以共同进入 Snapshot。
- 只有后续 Conflict Inference 能声明它们在可比较目标和 Context 中正式冲突。

若替代命题尚不完整，只保留符合 `KNW-REVALIDATION-SIGNAL-01` 的诊断和 Investigation 问题；不能制造占位 Fact 或形式上的 Conflict。

Revalidation Record 至少固定目标 `Resolved Formal Knowledge Reference(kind=FACT)`、`CONTRADICTS` Link 的 Evidence / Coverage / Context、替代 Candidate Reference（若完整）、Verification Decision、Attempt、处理结果和完整 Provenance。它随 Attempt Result 不可变提交；即使替代 Candidate 被拒绝或 Snapshot 发布失败，也不能丢失已发现的反驳依据和后续处理结果。

## 8. FactContext

### 8.1 从 Evidence 形成

FactContext 必须保留支持 Evidence 的 Source / KnowledgeContext 条件，并满足：

1. 单 Evidence Support Set 的 FactContext 不得宽于该 Evidence Context。
2. 多 Evidence 共同覆盖一个命题时，必须通过 `FACT_SUPPORT_COMPOSITION` Purpose 的 Context Comparison 证明所需条件可以共同成立；该比较只能依据输入 Evidence 的 OBSERVED Context Term 和同一 Context Vocabulary 的机械规则，`UNKNOWN`、`NOT_COMPARABLE` 或执行失败均不能被当作兼容。
3. 不同 Support Set 在不同 Context 下分别支持同一 Proposition 时，各自保留 Support Context；只有 Fact Type Contract 声明且机械证明每个分支均被覆盖时，才能形成更宽的显式组合表达。
4. Snapshot、Build Intent、默认环境、模型推测或同一次 Investigation 不能覆盖 Evidence Context。

Context Comparison Assessment 只提供组合门禁。若 Context 关系必须依赖部署映射、跨来源身份对应、其他正式 Fact / Inference 或模型语义判断才能成立，则组合后的软件结论是 Inference Candidate，而不是增加 DERIVED Term 后继续称为 Fact。该关系不能藏在 Assessment、FactContext 或 Prompt 中，从而形成 Fact 对 Inference 的反向语义依赖。

### 8.2 Identity-bearing 与 State Applicability Context

Fact Type Contract 必须把 Context 维度分为：

- `Identity-bearing`：改变命题指称或含义的条件，参与 Fact Identity Context Key。不同值通常形成不同 Fact，例如环境特定配置值的环境身份。
- `State Applicability`：同一 Proposition 在不同观察版本或时间中的成立记录，不直接改变稳定 Root，例如同一代码声明在连续 Commit 中仍存在。
- `Unsupported / Unknown`：Contract 无法安全分类的条件；不得为了归并而丢弃，Fact Resolution 保持未解析或形成保守的不同身份。

该划分由 Fact Type 语义决定，不是全局按 `Environment / Version / Time` 固定分类。即使 Revision 不进入稳定 Fact ID，它仍完整保留在 Fact State 和 Support Context 中。

### 8.3 Context 不能注入命题或反向依赖

FactContext 的成立条件只使用直接 Evidence 保留或合法收窄的 `OBSERVED` Term；它不能以另一个正式 Fact / Inference 的 `DERIVED` Term 扩充自身成立范围。`DERIVED` Context Term 仍可用于 Inference Context、Context-aware View 或查询选择，但不能把依赖正式知识才能成立的跨来源组合重新包装为 Fact。

例如，“这段生产日志对应 Commit A”若不是来源直接提供的同一观察闭包，就必须先作为正式关联知识参与 Inference；由此得到的“Commit A 在生产发生了该调用”也是 Inference，而不是给原运行 Fact 悄悄增加 `git.commit=A`。原运行 Fact 始终保留日志自身的 Environment、Deployment 和 Time 条件。

## 9. KNW-FACT-RESOLUTION-01

### 9.1 Resolution 只判断身份

Fact Resolution 在 owning Scope 内比较 Candidate 的稳定语义键，返回：

| 决定 | 条件 | 结果 |
|---|---|---|
| `LINK_EQUIVALENT` | 已成功发布过的同 Scope Fact Root 在当前 Schema 下具有经审核映射后相同的稳定 Fact Type Scheme、Proposition Semantic Key 和 Identity Context Key | Candidate 指向该 Root；在目标 Snapshot 中形成新的完整 Fact State |
| `CREATE_NEW` | Candidate 命题完整且不存在合法等价 Root | 使用 Candidate-local Fact Reference；最终发布前不分配稳定 ID |
| `KEEP_UNRESOLVED` | Canonicalization、Entity、Context Identity、Schema 兼容或等价性无法证明 | 保留候选与原因；不按文本相似或模型 Confidence 强制归并 |

`LINK_EQUIVALENT` 可以解析 Expected Current 为 PRESENT 时 Base Snapshot 中的 Fact State，也可以解析一个由既往成功 Snapshot 首次发布、但不属于 Base Snapshot 的稳定 Fact Root；后者只用于身份延续，不证明该 Fact 在 Base 中成立。跨 Knowledge Schema 延续还必须具有 exact `IDENTITY_CONTINUATION` Transition Proof；Resolver 比较的是 Proof 映射后的稳定语义身份，不要求不同版本 Canonical Proposition 表示对象按字节相同，也不能只凭 Fact Type Scheme ID 或 Canonicalizer 名称复用 Root。裸 Fact ID、其他 Attempt 的 Candidate 或跨 Scope Fact 不能成为 LINK 目标。

Resolution 不判断 Fact 是否证据充分、不选择互不兼容命题、不产生 Conflict Inference，也不拥有 Admission。相似自然语言、相同谓词或相同 Evidence 不是等价命题的充分条件。

### 9.2 Resolution Proposal 与平台决定

模型可以提出语义等价或差异说明；平台只在 Fact Type Contract、Canonical Proposition、Identity Context 和稳定 Root 索引能够重建时形成 Resolution Result。模型自报的等价 Fact ID、历史存在性和 Schema 兼容性一律忽略。

Fact Resolution Capability 可以采用 Deterministic、Model-Primary 或 Hybrid Strategy，但开放式 Proposal 不能绕过独立 Knowledge Verification。错误 Fact Merge 通常比暂时 KEEP_UNRESOLVED 更难恢复，依据不足时优先保守分离。

### 9.3 Fact-specific Knowledge Verification 义务

通用 Admission 流程由 DD-KNW-ADMISSION 定义；它对 Fact 至少必须从权威 Repository 独立重建并检查：

- Fact Type、Canonical Proposition、Entity Resolution Binding、Evidence / Context 和 Expected Current / Upstream Snapshot 引用完整性。
- 每个 Proposition Path 的直接覆盖、Composition Rule、Support Set 和否定观察闭包。
- Context 未扩大、Identity-bearing Context 归类、等价 Root 和唯一键合法性。
- 是否存在隐藏语义前提、Fact / Inference 误分类、来源模态偷换或 Evidence 原文中的未声明语义。
- 生成过程已发现的替代观察、Context 限制和 `KNW-REVALIDATION-SIGNAL-01` 是否被静默忽略。
- Candidate-local Entity、Fact，以及 INFERRED Entity 必需的 EntityDerivation Inference 原子闭包能否完整替换且无跨 Attempt 引用；无环检查只针对证明 Inference 的 Formal Premise Dependency DAG，不把 Entity Conclusion Output Binding / Identity Support Publication Edge 当作语义自证环。证明 Inference 的全部前提必须是固定 Snapshot 中的 Resolved Formal Knowledge Reference，不得依赖同一闭包内任何 Candidate。

Verifier 可以在隔离的 Verification Execution Context 中读取 Evidence Snapshot，并追踪 Entity Anchor 来核对命题；这些读取不会把 Entity 元数据、模型摘要或未声明内容变成 Fact 支持。Verifier 不直接调用 Connector，也不能静默修改 Proposition 或代替生成方补写缺失 Link；需要修正或补证时返回结构化问题，由 Knowledge Construction 形成新 Proposal / Attempt。

独立性由输入重建、执行上下文、判断职责和决策权隔离保证，不要求永久使用不同基础模型。机械校验通过不等于语义准入通过，Verifier 调用完成也不等于 Snapshot 已发布。

## 10. KNW-FACT-STATE-01 与最终发布

### 10.1 Fact State

Fact State 是 Fact Root 在一个确切 Snapshot 中的完整状态，至少固定：

- Snapshot Reference 与 Fact Identity Reference。
- 目标 Knowledge Schema 和 Canonical Proposition 解释引用。
- Canonical Proposition 中每个 Entity Identity Term 的确切 Resolution Binding：本地 Entity 必须绑定同一个目标 Snapshot 中的 Entity State；只有跨 Scope Entity 才绑定确切 Upstream Snapshot。
- 完整 FactContext Reference。
- 一个或多个经验证 Support Set、对应 Context Constraint Set 及其 FactEvidenceLink。
- 发布时按 Verification 用途取得的 Evidence Validation Result（Evidence、用途、检查时间、`READABLE` 结果与 Policy）、Knowledge Verification / Admission Decision 和依赖闭包。
- Candidate、Resolution、Capability / Strategy / Model Execution Provenance。

每个正式 Fact State 的状态恒为 `ASSERTED`；正常 Knowledge Use 和 Inference 前提只接受目标 Snapshot 中的该状态。State 保存发布时不可变的 Evidence Validation Result，不建立递归、实时的 `Fact Use Eligibility`。发布后 Evidence 的访问限制只影响 Evidence 原文追溯，不改写已经发布的 Fact；完整性故障必须隔离受影响存储并产生 `KNW-REVALIDATION-SIGNAL-01`，不能静默把旧 State 解释为仍已复核或其反命题。

目标 Snapshot 若无法按当时政策重验该命题，就不发布该 Fact State，并记录未延续原因；不创建 `UNVERIFIABLE` 等无生产消费者的正式状态。`PARTIAL`、`UNVERIFIED`、`REJECTED` 和 `CONFLICTED` 仍只是 Candidate / Verification 结果。多个替代 Fact 共存也不会把任一 Fact State 改名为 CONFLICTED。

每个 `(owning Scope, Snapshot ID, Fact ID)` 至多存在一个不可变 Fact State。一个 Attempt 内解析为同一已有 Fact Root，或具有同一待创建 Effective Fact Identity Key 的 CREATE_NEW Candidate，必须先聚合为一个最终 `Fact State Candidate`：只合入分别完成初步验证的 Support Set、Context Constraint Set 和 Context 分支。聚合对象随后由独立 Knowledge Verifier 对完整 Proposition、FactContext、Support / Constraint Set、Entity Binding 和依赖闭包重新审核；Admission Decision 必须绑定最终 Substitution-Invariant Closure Digest 和允许的 Local Reference Substitution Manifest。无法证明这些分支能够形成一个合法完整 State 时，拒绝相关 Candidate Closure 或重新 Resolution；禁止创建竞争 State、后写覆盖或任意丢弃其中一个候选。

Substitution-Invariant Closure Digest 在规范化时，对 Fact 使用 5.3 定义的 Fact Semantic Identity Token，对其 Entity Term 使用 DD-KNW-ENTITY 定义的 Entity Semantic Identity Token。Substitution Manifest 固定每个 Local Reference 的完整 Effective Identity Key、Token 和允许创建的 Knowledge Kind；发布事务只补充实际稳定 ID 映射。原始序列化 Digest 可以因 ID 分配变化而不同，但规范语义 Digest 必须保持一致，从而无需在准入前预分配 ID。

### 10.2 最终发布原子性

Knowledge Verification 通过后，Fact Candidate 仍不是正式知识。只有目标 Scope Snapshot 最终发布事务成功时：

- CREATE_NEW 分配稳定 Fact ID、创建 Fact Root 与首个 Fact State。
- LINK_EQUIVALENT 为已成功发布的 Root 创建目标 Snapshot 的完整新 State，不修改旧 State。
- 同一 Candidate Closure 内的 Entity / Fact / 必需 EntityDerivation Inference 局部引用被替换为稳定 Identity Reference。本地 Entity 全部重绑到正在发布的目标 Snapshot 成员；跨 Scope Entity 固定到允许的确切 Upstream Snapshot。
- FactEvidenceLink、Support Set、Context Constraint Set、Context / upstream 依赖、唯一键声明和 Snapshot Compare-And-Swap 一并生效。发布方只能按 Admission Decision 绑定的 Substitution Manifest 机械替换局部引用，并把发布对象重新规范化后校验 Substitution-Invariant Closure Digest 与审核值一致；不得在审核后聚合、增删或改写 Context / Support Closure。

稳定 Fact ID、Root、唯一 Fact State、首次成功发布证明、Support / Context Constraint Link、局部引用替换、INFERRED Entity 证明闭包、Canonical / Alias 有效唯一键、本地 Entity 目标成员检查和 `Expected Current = PRESENT(ref) | NO_CURRENT` 的目标 Snapshot CAS 必须在同一最终发布事务中全部生效或全部不生效。首次发布只有提交时仍不存在 CURRENT 才能成功。若需要发布前协调热点唯一键，只能使用 Attempt-local、不可查询、可过期的 Fact Identity Reservation；它不是 Fact 或 Formal Knowledge Reference。

发布结果未知时按 Attempt / Idempotency Key 查询或幂等重放；确认成功前不暴露新 State，确认失败前不清理仍可能被成功事务引用的候选闭包。其他 Attempt 只能链接由某次成功 Snapshot 发布确立的 Root，不能依赖未发布 Candidate。

### 10.3 Enrichment 与重验证

同 Revision 的目标限定更新可以为等价 Fact 增加 Evidence，但必须创建新的完整 Fact State：

- Base State 的 Support Set 只有在 Evidence、Context、Schema 和依赖仍满足当前政策时才可继承。
- 新 Link 不能原地追加到已发布 State，也不能静默扩大 FactContext。
- 新 Evidence 只是重复来源时可以保留审计关联，但不能冒充新的独立佐证。
- 新 Evidence 支持替代命题时构造独立 Candidate，并对原 Fact 触发影响重验证。
- 本轮未观察到 Fact 不等于反证；目标 Snapshot 中不延续或继续 ASSERT 由 Build Mode、覆盖边界和 Publication 主题决定。

## 11. Scope 与跨 Scope 规则

1. 每个 Fact 恰好一个 owning KnowledgeScope；所有直接 Evidence 必须属于该 Scope。
2. Expected Current 为 PRESENT 时，本 Scope Entity 在构建时使用该 Base Snapshot 的 Resolved Formal Knowledge Reference或同一原子 Closure 内的 Candidate-local 引用；NO_CURRENT 时只能使用局部候选。Base 引用只作为构建依据，发布后 Proposition 保存稳定 Entity Identity Reference，Fact State 必须重绑目标 Snapshot 中已继承或同事务新建的 Entity State。
3. 跨 Scope Entity Term 在构建时必须使用允许的确切 Upstream Snapshot 中的 Resolved Formal Knowledge Reference，并形成 Snapshot Upstream Dependency；发布后的 Proposition 同样只保存稳定 Entity Identity Reference，不能把 Snapshot 动态别名或 ID 混入稳定命题身份。
4. 本地或跨 Scope Fact / Inference 都不能作为 Fact Proposition 或 FactContext 的语义前提；若命题或跨来源 Context 关联依赖它们得出结论，该对象属于 Inference。
5. Shared Component 的宿主运行 Evidence 属于宿主 System Scope；它可以支持宿主 Fact 引用共享组件的上游 Entity，但不能把 Evidence 或 Fact 迁移到 Shared Component Scope。
6. Business Domain Scope 只有在自己的合法来源 Evidence 能直接支持命题时创建 Fact；综合多个系统正式知识形成的业务结论属于 Inference。

不同 Scope 不做 Fact 全局去重。跨 Scope 文本相同、Proposition 相似或引用相同 Entity 都不改变各自发布归属。

## 12. AI Native Capability 与评测

### 12.1 模型适合承担

- 从非结构化 Evidence 中提出完整的类型化命题。
- 识别复杂条件、参数绑定和多角色关系，并映射到 Evidence 区域。
- 发现替代命题、缺失语义元素、可能的 Fact / Inference 误分类和补证需求。
- 在有界候选集合中提出命题等价、Context Identity 和归并建议。

### 12.2 平台不可让渡

- Scope、Schema、Fact Type、Evidence / Entity / Snapshot 引用解析。
- Quote / Digest 重读、Canonical Proposition、Coverage Map 和 Context 不扩张。
- Direct Support / Composition Contract、稳定唯一键和最终 ID。
- 独立 Knowledge Verification、Snapshot 原子发布和历史不可变性。

更强模型可以替代脆弱的来源特定 Extractor、命题模板和相似性规则；不能取消 Fact / Inference 边界、直接 Evidence、Context、稳定引用、独立审核或发布门禁。确定性解析在更准确、低成本且可重放时继续作为 Tool 或 Strategy，而不是模型能力上限。

### 12.3 Capability Evaluation

Fact Construction 与 Fact Resolution 分别具有 Capability / Evaluation Contract。评测至少覆盖：

- Proposition semantic accuracy、必要语义元素召回和无依据语义增加率。
- Evidence faithfulness、逐路径 Coverage、Context 扩张和隐藏前提率。
- Fact / Inference 误分类，尤其是目的、因果、业务归纳和跨来源拼接。
- False Merge / False Split、稳定 ID 延续和 Schema / Canonicalizer 升级。
- 替代命题发现、重复 Evidence 误计独立佐证、负面观察范围扩张。
- 未见项目、非 DDD/混乱工程、不同来源与不同模型上的直接调查非回归、成本和延迟。

模型、Prompt、Tool 或 Strategy 只有经过固定样例回放、直接来源 Agent 对照和必要影子验证后才能晋升。门禁阈值由具体 Capability Contract 决定，不在一般 Fact 设计中写死。

## 13. 失败、重试与并发

| 类别 | 处理 |
|---|---|
| EVIDENCE_REFERENCE_INVALID | 不构造 Fact Candidate；Materialization 未成功时不存在可用 Evidence Reference |
| EVIDENCE_UNAVAILABLE / RESTRICTED | 当前用途不能独立读取时不构造新的可用 Fact Candidate；不使用模型记忆或摘要替代 |
| FACT_TYPE_UNSUPPORTED | 保留线索并返回能力缺失；不降级为自由文本 Fact |
| PROPOSITION_INVALID / INCOMPLETE | 拒绝 Proposal 或保留 Hypothesis；不创建部分 Fact |
| ENTITY_UNRESOLVED | 返回身份补充需求；不把名称写入 Entity Term |
| EVIDENCE_COVERAGE_INCOMPLETE | 不进入 Admission；可以形成结构化补证问题 |
| HIDDEN_SEMANTIC_PREMISE | 重新分类为 Inference Proposal 或补充直接 Evidence；不得伪装为 Fact |
| CONTEXT_EXPANSION_UNPROVEN | 保持更窄 Context、拆分 Candidate 或失败关闭 |
| CONTEXT_INCOMPATIBLE / UNKNOWN | 不组合 Support Set；保留各 Evidence 与未决关系 |
| NEGATIVE_OBSERVATION_NOT_CLOSED | 拒绝否定 Fact；空结果不兜底 |
| FACT_IDENTITY_AMBIGUOUS | KEEP_UNRESOLVED，不按相似度强制归并 |
| FACT_IDENTITY_COLLISION | 隔离并重新 Resolution；不能覆盖已有 Root |
| UPSTREAM_REFERENCE_INVALID | 不回退 CURRENT、名称或裸 ID |
| EXPECTED_CURRENT_MISMATCH | 实际 CURRENT 与 PRESENT(ref) 或 NO_CURRENT 期望不一致；当前候选不发布，基于新观察创建新 Attempt |
| ADMISSION_REJECTED | 不创建 Root / State / Link；保留审计和补证问题 |
| PUBLICATION_OUTCOME_UNKNOWN | 按 Attempt / Idempotency Key 查询或幂等重放；不暴露半成品 |
| STRATEGY_FAILED / MODEL_UNAVAILABLE | 按激活政策有界重试或回退；不得降低直接支持门禁 |

- 相同冻结输入和幂等键返回同一 Construction / Resolution Result；改变 Evidence、Entity、Context、Schema、Expected Current Binding、Contract 或 Strategy 产生新 Attempt。
- 模型重试产生新的 Capability Attempt 和完整 replacement Proposal；实际资源消耗不回滚。
- Fact Root 唯一性和 Snapshot CAS 由 Knowledge Engine 的发布事务保证，不依赖应用层“先查后写”。
- Candidate、Hypothesis、`KNW-REVALIDATION-SIGNAL-01` 和 Fact Identity Reservation 都不能被正常 Knowledge Use 当作正式知识查询。

## 14. 可观测性、资源与敏感信息

- 传播 Task / Run、Build Intent、Candidate / Attempt、Fact Type、Evidence / Entity、Context、Resolution、Verification、Snapshot、Capability / Strategy / Model Call 关联。
- 记录 Proposal 数、直接性拒绝、Coverage 缺口、Fact / Inference 重分类、Merge / Split、Context 扩张拒绝、替代命题、重试和资源消耗。
- Fact Telemetry 不复制 Evidence Quote、Artifact Payload、Secret 或模型隐藏推理；只保存稳定引用、结果分类、Digest 和审计定位。
- Fact Proposition 可以包含受保护的软件语义，读取仍按 Scope、Snapshot、用途和数据分类授权；稳定引用不是读取凭证。
- 评测分数、模型 Confidence、Agent Trace 和审核解释不是 Evidence、Fact 或 FactContext Basis。

## 15. 拟议不变量

1. Fact 是明确 Context 下可由直接 Evidence 完整复核的客观命题，不是跨来源绝对真相。
2. Fact / Inference 按认知性质与支持关系区分，不按模型或代码生成区分。
3. Observation Modality 是命题语义的一部分；文档陈述、代码声明和运行观察不能静默归并。
4. 正式命题必须表达全部用户可见语义；Evidence 原文和 Projection 不能补写 Fact 未声明的内容。
5. Fact Proposition 不受三元组限制，但必须受版本化 Fact Type Contract 约束并可规范化。
6. Fact 的每个语义路径都必须由合法 Support Set 直接覆盖；隐藏语义前提使其成为 Inference 或未决 Hypothesis。
7. Evidence 本身没有支持极性；Relation、Coverage、Context 和 Verification 属于 FactEvidenceLink。
8. Evidence 数量不表示真值或 Confidence；只有具体政策需要时才判断来源/观察独立性。
9. 多 Evidence 只能通过已声明、可重放的 Composition Rule 共同支持 Fact，不能用模型猜测填补语义间隙。
10. 互不兼容的直接观察形成独立 Fact Candidate；Fact 共存不等于正式冲突，Conflict 只能由 Inference 表达。
11. FactContext 不得宽于支持 Evidence Context，也不得使用正式 Fact / Inference 的 DERIVED Term 建立反向语义依赖；未知或不兼容 Context 不能被静默融合。
12. Context 是否参与稳定身份由 Fact Type 声明；Schema / Contract / Canonicalizer Version 不能自然放行重复 Root。
13. Fact ID 不包含 Snapshot、Evidence、Revision、模型或显示文本；Root Proposition 不可原地改写。
14. 所有直接 Evidence 与 Fact 属于同一 owning Scope；跨 Scope 只使用确切上游 Entity Reference 和 Snapshot Dependency。
15. Fact Candidate 只能引用已发布 Entity 或同一原子 Candidate Closure 内的 Entity Local Reference；INFERRED Entity 必须同时闭合不依赖本轮 Fact Candidate 的 EntityDerivation Inference。Root 命题保存稳定 Entity Identity，本地 State 重绑目标 Snapshot，跨 Scope State 绑定确切上游 Snapshot。
16. 只有目标 Snapshot 中的 ASSERTED Fact State 能支持正常 Knowledge Use 和新 Inference；Candidate / Verification 结果不能支持生产 Claim。
17. Stable Fact ID、Root、State、Evidence Link、Support Set、局部引用替换、唯一键和 Snapshot CAS 在同一最终发布事务中生效。
18. 模型可以主导 Fact 发现和命题提议，但不能自报 Scope、稳定 ID、Evidence 内容、直接支持完整性、准入或发布结果。
19. 每个 Snapshot 中同一 Fact Root 至多一个 Fact State；等价 Candidate 只能在分别验证并合法聚合后形成该唯一 State。

## 16. 验证义务与下游追溯

当前无需 Design Validation Demo 决定 Fact 的直接 Evidence、来源模态、完整命题、Context 不扩张和正式冲突边界；这些约束可由认知责任和概要不变量静态推出。

进入具体 Fact Type 实现前必须建立 Contract Conformance：

- Canonical Proposition、等价、稳定身份键和兼容升级映射。
- 每个命题路径的 Direct Observation / Coverage / Composition Rule。
- 单 Evidence、多 Evidence、重复 Provenance 和部分覆盖。
- FactContext 收窄、Context Comparison 四态和 identity-bearing Context。
- 替代命题、否定观察边界和 Fact / Inference 分类。
- CREATE / LINK 并发、局部 Entity 引用替换、发布结果未知和幂等重放。

进入默认 Strategy 激活前必须建立 Capability Evaluation，至少使用未见项目同时比较模型主导、确定性和 Hybrid Strategy；真实来源暴露出会改变 Fact / Inference 边界、Context Identity 或多 Evidence 组合契约且静态分析无法判定时，才按 AD-126 建立有界 `DVR-*` Demo。

下游主题必须引用本文而不能重新定义：

- DD-KNW-INFERENCE-CONFLICT：只消费已发布 ASSERTED Fact 作为语义前提，并定义 Conflict Inference。
- DD-KNW-ADMISSION：实现独立 Knowledge Verifier、替代 Fact 共存和候选依赖闭包门禁。
- DD-KNW-SNAPSHOT-PUBLICATION：实现 Fact State、跨 Scope 依赖、唯一性和最终发布原子性。
- DD-KNW-PERSISTENCE：保存权威 Proposition / Link / State，并使图、搜索和向量 Projection 可重建。
- DD-APP-KNOWLEDGE-USE：只从固定 Snapshot 读取正式 Proposition，不借 Evidence Quote 扩张答案。
