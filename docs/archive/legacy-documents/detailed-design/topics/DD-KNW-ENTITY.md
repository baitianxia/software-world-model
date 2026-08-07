# Entity Identity 详细设计

| 元数据 | 值 |
|---|---|
| Document ID | DD-KNW-ENTITY |
| Version | 0.1.0 |
| Status | Accepted |
| Document Steward | Knowledge Engine |
| Architecture Baseline | SWM-ARCH@1.2 |
| Depends On | DD-KNW-REFERENCE-CONTEXT@0.1.0、DD-KNW-SCHEMA-CORE@0.1.0、DD-KNW-CONTEXT-COMPARISON@0.1.0、DD-X-CAPABILITY-EXECUTION@0.1.0、DD-AI-MODEL-GATEWAY@0.1.0、DD-MGT-CAPABILITY-EVALUATION@0.1.0、DD-KNW-EVIDENCE@0.1.0 |
| Owns Contracts | KNW-ENTITY-01、KNW-ENTITY-MENTION-01、KNW-IDENTITY-ANCHOR-01、KNW-ENTITY-RESOLUTION-01、KNW-ENTITY-STATE-01 |
| Design Coverage | 稳定 Entity 公共身份与 Source-anchored Identity；推断型身份由 DD-KNW-INFERENCE-CONFLICT 完成 |
| Supersedes | None |
| Rationale ADR | AD-010、AD-011、AD-012、AD-013、AD-040、AD-041、AD-042、AD-043、AD-078、AD-111、AD-112 |
| Design Validation | None |
| Conformance Cases | None |
| Capability Evaluation | None |

> 概要架构约束直接生效；本文新增的 Mention、Identity Anchor、Resolution 和 Entity State 语义在状态进入 `Accepted` 前均为拟议设计。

## 1. 目的与范围

Entity 表达软件世界中可以被长期、稳定引用的身份。本文首先解决来源锚定身份：如何从 Evidence 识别一个来源对象，判断它应链接已有 Entity、创建新 Entity，还是保持未解析；同时冻结推断型 Entity 必须遵守的公共身份边界。

本文定义：

- Entity、Entity State、Entity Mention 和 Identity Anchor 的区别。
- 来源锚定身份的规范化、解析、风险分级、稳定 ID 和并发约束。
- 重命名、移动、来源变化、跨 Scope 和同名对象的保守处理。
- 模型 Entity Resolution Strategy 与平台身份权威的边界。

本文不定义：

- Entity 的属性、关系、职责、行为、业务含义或显示分类 Claim；它们由 Fact / Inference 表达。
- 推断型 Business Entity / 逻辑子系统如何从正式 Fact 归纳；该路径由 Inference 主题定义并与 Entity 原子准入。
- Fact Candidate 如何引用 Entity、Knowledge Admission 的通用事务或 Snapshot 发布。
- 特定语言符号表、数据库目录、业务目录或日志格式的实现字段。

## 2. Entity 的最小语义

### 2.1 身份容器而非属性容器

正式 Entity 只支持两个权威 Claim：

1. 在确切 Snapshot 中存在这个稳定身份。
2. 其他正式知识可以无歧义地引用它。

名称、路径、限定名、别名、类型标签、状态、职责、归属和关系即使出现在索引或 Entity State 的定位元数据中，也不能单独支持用户可见的软件知识 Claim。需要陈述这些语义时必须有正式 Fact 或 Inference。

### 2.2 两个正交维度

| 维度 | 首批值 | 含义 |
|---|---|---|
| Semantic Category | `TECHNICAL`、`BUSINESS`，可由 Schema 扩展 | 身份在语义模型中的大类，不决定认知来源 |
| Identity Origin | `SOURCE_ANCHORED`、`INFERRED` | 身份直接由来源稳定标识锚定，还是由正式知识语义归纳 |

技术 Entity 通常为 SOURCE_ANCHORED，Business Entity 通常为 INFERRED，但两者不是硬绑定。权威业务目录可以产生 SOURCE_ANCHORED Business Entity；由多个技术 Fact 归纳的逻辑子系统可以是 INFERRED Technical Entity。

`Entity Kind` 是 Knowledge Schema 下用于身份约束和解析的最小判别符，例如 code-symbol、api-endpoint、database-object 或 business-concept。它本身不能替代说明“为什么该对象具有某业务/技术性质”的 Fact 或 Inference。

## 3. 逻辑对象与所有权

| 对象 | Owner | 权威性质 |
|---|---|---|
| Entity Mention | Knowledge Engine Candidate Area | Evidence 中可能指向某个身份的来源锚定观察；不是 Entity |
| Identity Anchor | Knowledge Engine | 由 Evidence 与版本化 Anchor Contract 重建的来源身份坐标；不能自证应链接哪个 Entity |
| Entity Resolution Proposal | Resolution Strategy / Investigation | 不可信的 LINK / CREATE / UNRESOLVED 或上游引用建议 |
| Entity Identity Candidate | Knowledge Engine | 平台重建后等待 Knowledge Admission 的身份决定 |
| Entity | Knowledge Engine | 稳定身份根；只有进入 Snapshot 的正式状态可供正常查询 |
| Entity State | Knowledge Engine | 某 Snapshot 中该身份的成员状态、有效 Anchor 和定位元数据 |
| Semantic Entity Proposal | Inference Candidate Area | 仅供推断型身份；本文只规定不能冒充 Source Anchor |

模型、Agent 和 Source Integration 都不能分配稳定 Entity ID、直接写 Entity Repository 或把名称匹配结果宣布为正式身份。

## 4. KNW-ENTITY-01：稳定 Entity Identity

### 4.1 Entity Root

Entity Root 至少固定：

- owning KnowledgeScope ID。
- 不透明稳定 Entity ID。
- Knowledge Schema Identity / 创建时语义版本。
- Entity Kind 与 Semantic Category。
- Identity Origin。
- 创建时的 `Effective Entity Identity Key`；后续兼容键只能通过已审核的 Identity Continuation 加入持久身份索引。
- 首次 Admission Decision Reference。
- 首次成功发布引用；Root 只有与该 Snapshot 发布原子成功后才存在。

Entity ID 不包含 Snapshot、代码 Revision、环境、时间、名称、文件路径、行号、显示顺序或模型版本。ID 由 Knowledge Engine 在目标 Snapshot 的最终发布事务中分配，不能由模型提供，也不直接用当前路径或名称哈希生成。Knowledge Verification 的准入决定只批准候选闭包，不提前创建 Entity Root。

Entity Root 一旦创建不可改为另一个 Scope、Kind、Category 或 Origin。Schema 演进只有在身份语义兼容并通过迁移审核时才能继续使用同一 ID；实质身份语义变化创建新 Entity。

### 4.2 Effective Entity Identity Key

Entity Identity Scheme 首先构造带 Identity Origin 标签的 `Presented Entity Identity Key`，其结构只能是下列两类互斥元组：

- `SOURCE_ANCHORED = (ENTITY, owning Scope, Entity Kind, Semantic Category, SOURCE_ANCHORED, Identity Domain, Identity Key Scheme ID, Canonical External Entity Key, Identity-bearing Context Key)`。
- `INFERRED = (ENTITY, owning Scope, Entity Kind, Semantic Category, INFERRED, Semantic Identity Scheme ID, Canonical Semantic Definition Stable Key, Semantic Identity Context Key)`。

Identity Key Scheme 负责每个分量的规范化和稳定序列化。Knowledge Schema Version、Anchor / Semantic Identity Contract Version、Canonicalizer Version、Strategy 和显示文本都不进入该键。

权威使用前，Knowledge Engine 必须将 Presented Key 解析到唯一 `Canonical Root Identity Key`：CREATE 时，经相同 Attempt 规范化后的 Presented Key 成为新 Root 的 canonical key；LINK 时，所有兼容别名先经已审核 `IDENTITY_CONTINUATION` Schema Transition Proof 映射到目标 Root 唯一的 canonical key。Proof 必须显式指定 canonical representative，不只声明两键“等价”。`Effective Entity Identity Key` 专指此解析后的 Canonical Root Identity Key。

兼容升级必须继续得到同一 Effective Key，或把新 Presented Key 作为别名映射到原 canonical representative；别名只能在唯一 Alias Index 中指向一个 Root，不得独立生成 Token、Root 或唯一性语义。不兼容变化必须作出 Continuation、Fork 或 Retirement Decision。

Resolution、同 Attempt 聚合、嵌套 Fact / Inference Term、Local Reference Substitution Manifest、Substitution-Invariant Closure Digest、持久身份索引和数据库唯一约束必须共用 Effective Entity Identity Key，不得使用 Presented Alias 或各自重建“相似身份”。`Semantic Identity Token = canonicalDigest(Effective Entity Identity Key)`，因此 Candidate-local Reference、兼容别名与发布后 Entity ID 可以在不改变语义 Digest 的前提下归一到同一 Token。

### 4.3 Identity 与 Snapshot State 分离

稳定 Entity Root 不表示它属于所有 Snapshot。Entity State 表达一个确切 Snapshot 中的成员状态；`Resolved Formal Knowledge Reference` 才能证明 Entity 在目标 Snapshot 中存在。

旧 Snapshot 不因新来源或新解析决定被改写。Entity 在新 Snapshot 中退出、重新出现或改变 Anchor 时仍保留稳定 ID，但必须经过对应候选、影响判断和准入；仅仅“本轮没有观察到”不能自动移除 Entity。

为支持稳定身份重现，成功发布过的 Entity Root 及其有效 Identity Key 必须保留在同 Scope 的内部身份索引中，即使它不属于 Base Snapshot。该索引只证明“该 Root 曾成功发布”，不证明 Entity 在当前 Snapshot 中存在，也不向正常 Knowledge Use 暴露历史 State；物理保留和受控删除由 Persistence / Retention 主题定义。

## 5. KNW-ENTITY-MENTION-01

### 5.1 Mention 的成立

Entity Mention 表达“该 Evidence 的某个子区域呈现了一个可能可引用的来源对象”。它至少固定：

- 仅在 Candidate Bundle 内有效的 Mention Local ID。
- 一个已成功物化的不可变 Evidence Reference，并要求当前 Entity Construction / Verification 用途下可复核。
- Evidence Observed Content 内的相对 Locator 与 Digest。
- 提议的 Entity Kind / Semantic Category。
- 原始名称、来源标识、限定信息及其精确位置。
- Evidence / KnowledgeContext Reference。
- Mention Extraction Capability / Strategy / Execution Reference。

一条 Mention 只能来自一条 Evidence。多个 Evidence 中观察到的同一外部标识形成多个 Mention，再由 Resolution 聚合；不能把多个 Evidence 预先拼成一个 Mention。

### 5.2 Proposal 与平台重建

模型或确定性 Strategy 可以提出 Mention Local ID、Evidence Reference、相对 Locator、Kind 和候选来源键。Knowledge Engine 必须：

1. 从权威 Evidence Snapshot 重读相对区域。
2. 校验 Locator 位于 Evidence 边界内且 Digest 一致。
3. 按目标 Knowledge Schema 校验 Kind / Category。
4. 按 Identity Anchor Contract 重建来源标识、Identity Domain 和 Context。
5. 拒绝模型自报的 Scope、稳定 Entity ID、Canonical External Key 或已有 Entity 存在性。

Mention 可以保留在未解析 Candidate / Investigation 状态中；它不进入 Snapshot，也不能作为 Fact Candidate 的正式 Subject / Object。

Evidence Reference 绑定其创建时 Knowledge Schema。目标 Entity Schema 不同时，只有 Schema Core 的 exact `EVIDENCE_INTERPRETATION` Transition Proof 完整覆盖 Evidence Representation、Locator / Observation、Entity Kind 和 Anchor Contract 解释，才能复用；否则必须重新物化目标 Schema 的 Evidence / Mention，不能用新 Anchor Contract 静默解释旧观察。

## 6. KNW-IDENTITY-ANCHOR-01

### 6.1 Identity Anchor Contract

每种受支持的 Artifact Kind、Evidence Representation 和 Entity Kind 组合必须注册版本化 Identity Anchor Contract，定义：

- Source Identity Domain 的组成和规范化规则。
- 能够从 Evidence 直接复核的 Source-native Identifier。
- 跨兼容版本保持稳定的 `Identity Key Scheme ID`，以及 Canonical External Entity Key 的结构、等价和冲突规则。
- `Identity-bearing Context Projection`：哪些 Context 维度参与身份，如何机械生成 `Identity-bearing Context Key`；未声明的 Context 不得偷偷进入身份键。
- Canonicalizer / Anchor Contract Version；这些版本只记录构造 Provenance，不自然形成新的身份命名空间。
- 哪些字段只是显示名称或可变位置，不能充当稳定键。
- Source Context 对身份等价的约束。
- 可机械识别的重命名、移动、别名或 Continuity Signal。
- 无法证明稳定身份时必须返回的失败/未解析语义。

Provider 可以提供来源词汇和稳定标识，但 Anchor 由 Knowledge Engine 从 Evidence 重建；Provider 或模型不能直接绑定正式 Entity。

### 6.2 Anchor 内容

Identity Anchor 至少固定：

- owning Scope、Knowledge Schema 和 Entity Kind。
- Identity Domain、稳定的 Identity Key Scheme ID、Canonical External Entity Key 和 Identity-bearing Context Key。
- Anchor Contract / Canonicalizer Version；它们属于构造 Provenance，不属于有效唯一键。
- 一个或多个不可拆分的 `Anchor Observation`。每项固定且只固定一条 Evidence Reference、一条 Mention Reference、该观察自己的 Source Context、来源 Revision、规范化显示定位与直接 Continuity Signal。
- Anchor Digest 与构造 Provenance。

Canonical External Entity Key 是解析索引，不是 Entity ID。它可以包含仓库/数据库/业务目录等稳定身份域和来源原生对象键；如果来源只有路径或名称，Contract 必须把其稳定性限制和 Context 保留下来，不能伪装为强身份。

多个 Anchor Observation 共同支持一个 Anchor 时，不得把它们的 Context 或 Revision 覆盖成单值，也不得把不同环境、分支或观察时间隐式拼接成一个事实条件。Anchor 级 Identity-bearing Context Key 只能由 Contract 声明的身份维度机械投影；多个 Observation 只有满足以下任一门禁时才能共同参与同一身份解析：

1. 所有 identity-bearing Context Projection 在同一 Schema、Anchor Contract 与 Canonicalization Version 下机械相等。
2. exact `KNW-CONTEXT-ASSESSMENT-01` 在 `ENTITY_IDENTITY_ANCHOR_COMPOSITION` Purpose 下返回 `COMPATIBLE`，并通过 `ValidateContextAssessmentReuse` 取得当前 exact `VALID` Decision。

采用第二条时，Identity Anchor 与 Entity State Candidate 必须固定 Assessment Reference / Digest、Validity Decision Reference / Revision / Digest、Comparison Purpose、按规范顺序列出的全部输入 KnowledgeContext Reference / Digest、Target Schema 和 supporting Formal Knowledge References。Assessment 只证明这些 identity-bearing 条件可共同用于本次身份解析，不得隐藏新的对象等价、跨 Scope 合并或属性 Claim；其 supporting Formal Knowledge References 必须属于冻结 Base / Upstream Snapshot，并进入 Verification Read Set。

`INCOMPATIBLE` 禁止聚合相应 Observation；`UNKNOWN`、`NOT_COMPARABLE`、执行失败或 Assessment 非 `VALID` 时保持独立 Anchor / Mention，并使需要聚合才能决定的 Resolution 进入 `KEEP_UNRESOLVED`。实现不能以名称相同、模型 Confidence、同一 Investigation 或目标 Snapshot 相同替代上述门禁。

兼容的 Contract / Canonicalizer 升级必须继续产生同一 Identity Key Scheme ID 下的等价 Key，并保存旧键到新键的显式映射。不兼容升级必须经过身份延续、分叉或废弃审核并重验证已有 Anchor；不能通过增加 Schema、Contract 或 Canonicalizer Version 绕开唯一约束，自然创建第二个 Entity Root。

### 6.3 典型 Anchor

| 来源 | 可接受 Anchor 示例 | 不能单独证明同一身份 |
|---|---|---|
| Code | Repository Identity Domain + 语言符号稳定键/签名 + 直接来源位置 | 仅类名、方法名、相似实现文本 |
| DB | 实例身份域 + 数据库原生对象 ID；无原生 ID 时为限定名与观察条件 | 不同实例中的同名表 |
| API Catalog | Catalog 身份域 + 稳定 API ID / Versioned Definition Key | 相同 URL 文本但归属系统未知 |
| Message / Topic | Broker/Registry 身份域 + 原生 Topic ID/限定名 | 不同环境中同名字符串 |
| Business Catalog | Catalog 身份域 + 权威概念 ID | 文档中只出现相同业务名词 |
| Logs / Trace | 可复核的服务实例、Logger、Span Kind 等来源标识 | 模型从消息文本猜出的代码对象 |

日志或 Trace 产生于宿主 System Scope，即使内容提及共享组件，也不能把运行 Evidence 直接变成 Shared Component Scope 的 Entity Anchor。它可以支持宿主 Scope 中的 Fact / Inference 去引用已发布共享组件 Entity。

## 7. KNW-ENTITY-RESOLUTION-01

### 7.1 输入边界

Entity Resolution 固定：

- target KnowledgeScope、Knowledge Schema，以及 `Expected Current Snapshot Binding = PRESENT(Snapshot Reference) | NO_CURRENT`。首次构建显式使用 NO_CURRENT。
- 当前 Candidate Bundle 中的 Mention / Anchor。
- Expected Current 为 PRESENT 时 target Scope 的 Base Snapshot Entity State，以及同 Scope 内曾由成功 Snapshot 发布、当前不属于 Base 的稳定 Entity Root 身份索引；NO_CURRENT 时前者为空。二者是 `LINK_EXISTING` 的合法本地候选集合。
- 只读的确切 Upstream Snapshot Reference；它只用于产生跨 Scope 正式引用结果，不是本地 LINK 候选集合。
- Capability Catalog Snapshot、Execution Envelope、exact Resolution Strategy、`PRODUCTION Activation | EVALUATION_ONLY Grant` 和 Resource Allocation。

Resolution 不按全局名称搜索后直接合并。`LINK_EXISTING` 的目标必须解析为 Expected Current 为 PRESENT 时 Base Snapshot 中的 Resolved Formal Knowledge Reference，或带首次成功发布证明的同 Scope 稳定 Root Identity Target；后者只用于身份延续，不证明 Base 中存在该 Entity。裸 Entity ID、另一 Scope 的同名对象或其他 Attempt 的 Candidate State 都不能成为 LINK 目标。上游 Entity 只能返回只读 Resolved Upstream Entity Reference，并由后续 Fact / Inference 表达它与本 Scope 观察的关系。

### 7.2 本地身份决定与上游引用结果

| 决定 | 条件 | 结果 |
|---|---|---|
| `LINK_EXISTING` | Anchor 与可选 Base Snapshot State 或曾成功发布的同 Scope Root 的有效身份约束一致，且没有未解决碰撞 | 形成向该本地 Entity 添加/确认 Anchor 的 Identity Candidate；历史 Root 只延续身份，目标 State 仍须重新准入和发布 |
| `CREATE_NEW` | Anchor 足以证明独立来源身份，且没有合法现有 Entity 可链接 | 形成使用 Candidate-local Entity Reference 的新身份 Candidate；最终发布事务前不分配稳定 ID |
| `KEEP_UNRESOLVED` | Anchor 不稳定、候选多义、Context 不足、同名碰撞或 Continuity 无法证明 | 保留 Mention、候选集合与原因；不创建占位 Entity |
| `REFERENCE_UPSTREAM` | Mention 可解析为允许的确切 Upstream Snapshot 中的正式 Entity，但该 Entity 不归 target Scope 所有 | 返回只读 Resolved Upstream Entity Reference；不形成本地 Identity Candidate，不创建或修改 Entity State / Anchor |

前三项是本地身份解析决定；`REFERENCE_UPSTREAM` 是跨 Scope 引用解析结果，不是第四种本地 Admission 决定。无法确认时必须 KEEP_UNRESOLVED。为了图结构完整、Fact 构造方便或减少对象数量，不得强制 LINK、CREATE 或跨 Scope 复制身份。

### 7.3 风险分级

Resolution Policy 依据可验证风险而不是固定来源类型分级：

| Resolution Class | 典型依据 | 审核要求 |
|---|---|---|
| Deterministic Anchor | Provider-backed 唯一来源 ID、Scope/Kind/Context 一致、无碰撞 | 独立机械 Verifier；不要求逐条模型调用 |
| Deterministic Continuity | 相同 Anchor，或来源直接提供且 Contract 可验证的 rename/move 映射 | 独立机械校验变更链和 Base State |
| Ambiguous Identity | 名称/路径为主、多个候选、跨来源对应、Context 未决 | Model/Hybrid Proposal + 与生成隔离的 Knowledge Verifier |
| Semantic Identity | 必须依赖多个正式 Fact / Inference 才能证明存在 | 不在本流程创建；进入推断型 Entity Candidate Bundle |

风险等级由版本化 Resolution Policy 计算，模型不能自报“低风险”。错误合并通常比暂时不合并更难恢复，因此在依据不充分时优先 KEEP_UNRESOLVED，而不是以置信度阈值强制选择。

### 7.4 模型 Proposal 与平台 Candidate

模型可以提出候选 Entity、相似性依据、Resolution 决定、上游引用建议和需要补充的 Mention，但输出只是 Entity Resolution Proposal。Knowledge Engine 从冻结输入重新构造：

- `KNW-CANDIDATE-ENVELOPE-01`：Build Intent / Application Attempt References、Scope、Schema、Target Snapshot Local Reference、Expected Current / Upstream Bindings。
- Anchor、Evidence、Context 与 Canonical External Key。
- Expected Current 为 PRESENT 时本地已有 Entity 的 Base Snapshot Resolved Formal Reference、带首次成功发布证明的同 Scope Root Identity Target，或只读 Resolved Upstream Entity Reference；三者不得互换。
- Candidate-local Reference、CREATE / LINK / UNRESOLVED Resolution Intent 和 Provenance；不包含稳定 ID 或预分配请求。

未知字段、越界 Evidence、跨 Scope 裸链接、模型自报 Entity ID、缺少 Anchor 或把 INFERRED 身份伪装为 SOURCE_ANCHORED 时拒绝整个相关 Proposal。修正必须提交完整 replacement Proposal。

只有 `PRODUCTION` Catalog 且 post-call model eligibility 通过时，Resolution 才能形成生产 Identity Candidate。`EVALUATION_ONLY` 只返回隔离 Evaluation Output，不创建 Candidate-local Entity 或进入 Admission Bundle。

## 8. KNW-ENTITY-STATE-01

### 8.1 Entity State Candidate

本节的 Anchor / Evidence 字段适用于 `SOURCE_ANCHORED` Candidate；`INFERRED` Candidate 使用 DD-KNW-INFERENCE-CONFLICT 定义的 Semantic Definition、EntityDerivation 和 INFERRED Entity State Contract，不伪造 Anchor / Evidence。两条路径都复用 4.2 的 Effective Entity Identity Key 和本文的公共发布不变量。

SOURCE_ANCHORED Entity Identity Candidate 通过 Resolution 后仍不是正式 Entity。它至少包含：

- Candidate Envelope Reference / Digest；本地引用不得跨 Envelope。
- `LINK_EXISTING` 或 `CREATE_NEW` 决定与依据。
- Existing Base Resolved Entity Reference、带首次成功发布证明的同 Scope Root Identity Target，或 Candidate-local Entity Reference。
- Entity Kind、Semantic Category、Identity Origin。
- Identity Anchor、Evidence 和 KnowledgeContext Reference。
- 多 Observation 聚合时的 identity-bearing Context 机械相等证明，或 exact Context Assessment / latest VALID Decision 及其输入和 supporting Formal Knowledge Reference 摘要。
- Expected Current Snapshot Binding、Resolution Policy / Strategy 和风险分类。
- 供准入重建的 Effective Entity Identity Key；不包含预分配稳定 Entity ID。SOURCE_ANCHORED Candidate 必须使用本文的 Source 键变体；INFERRED Candidate 使用 DD-KNW-INFERENCE-CONFLICT 的语义定义与 State Contract。

Knowledge Verifier 从权威 Repository 重读 Evidence、Anchor、Expected Current 为 PRESENT 时的 Base Entity State 和唯一性约束，判断 Resolution 是否可准入。多 Observation Anchor 必须重新计算 identity-bearing Projection 的机械相等，或通过公共 `ValidateContextAssessmentReuse` 重验 exact Assessment / latest VALID Decision、全部输入 Context 和 supporting Formal Knowledge References；Assessment 的 Purpose、Scope、Schema、输入或有效性任一失配都不能准入。任何跨 Schema 的 LINK 都必须独立重读并审核 exact `IDENTITY_CONTINUATION` Transition Proof，无论目标来自 Base State 还是历史 Root；若 LINK 指向历史 Root，还必须重读 Root、首次成功发布证明和有效 Identity Key 索引。历史索引命中、Schema 版本相近或模型自报证明都不能替代审核。生成 Strategy 不能审核自身决定。

同一 Attempt 内解析为同一已有 Entity Root，或具有同一待创建 Effective Entity Identity Key 的 CREATE_NEW Candidate，必须先聚合成唯一 `Entity State Candidate`，再由独立 Verifier 审核完整 Anchor Observation、Context、Resolution Target 和依赖闭包。Admission Decision 绑定最终 Substitution-Invariant Closure Digest 与 Local Reference Substitution Manifest；无法合法聚合时拒绝相关 Closure，不能创建竞争 State 或任选一个候选。

Substitution-Invariant Closure Digest 把 Candidate-local Reference 和发布后的稳定 Entity ID 都规范化为 4.2 定义的同一 Semantic Identity Token。Substitution Manifest 固定 Local Reference、完整 Effective Entity Identity Key、Token 和允许的 Entity Kind / Origin；发布事务只补充实际稳定 ID 映射。原始序列化 Digest 可以变化，规范语义 Digest 必须保持一致。

`REFERENCE_UPSTREAM` 不生成 Entity Identity Candidate。它只能作为同一 Candidate Bundle 中 Fact / Inference Candidate 的确切上游引用输入；如果本轮没有合法命题使用该引用，则不产生任何 Snapshot 成员。

### 8.2 最终发布后的 Entity State

Knowledge Verification 通过后，Identity Candidate 仍只使用 Candidate-local Reference。只有目标 Scope Snapshot 的最终发布事务成功时：

- CREATE_NEW 分配稳定 Entity ID、创建 Entity Root 与首个 Snapshot Entity State、替换同一原子 Candidate Closure 内的局部引用，并取得有效身份键的唯一性声明。
- LINK_EXISTING 不创建新 Root，只为可选 Base Snapshot State 或曾成功发布的同 Scope Root 形成目标 Snapshot 的新 State / Anchor 关联；历史 Root 不会让旧 State 自动复活。
- KEEP_UNRESOLVED 不创建 Entity 或 Snapshot State。

稳定 Entity ID、Entity Root、首个 Entity State、Candidate-local 引用替换、有效身份键唯一性声明、历史 Root 发布证明 / Identity Continuation 的再次校验和 `Expected Current = PRESENT(ref) | NO_CURRENT` 的目标 Scope Snapshot Compare-And-Swap 必须在同一个最终发布事务中生效或全部不生效。首次发布只有提交时仍无 CURRENT 才能成功；准入通过、事务准备或发布结果未知均不能使 Entity Root 对正常查询可见。

每个 `(owning Scope, Snapshot ID, Entity ID)` 至多一个不可变 Entity State。发布方只能按 Admission Decision 的 Substitution Manifest 机械替换局部引用，并把发布对象重新规范化后验证 Substitution-Invariant Closure Digest 与审核值一致；不得在审核后追加 Anchor、合并 Context 或改变 Resolution Target。

Entity State 可以保存用于定位和检索的显示名称、限定名、来源位置、Anchor 与成员状态，但这些字段必须能回溯 Evidence，且不能绕过 Fact / Inference 支持用户可见属性 Claim。Projection 可以复制这些字段作为搜索入口，不能成为独立身份权威。

### 8.3 原子唯一性与并发

Knowledge Engine 对完整 Effective Entity Identity Key 维护持久权威索引和有效唯一约束。键组成及排除项只能沿用 4.2，不得在数据库、Resolution 或聚合层另行简化。版本升级只能通过已审核的兼容映射、身份延续或身份分叉 Contract 改变解析结果。

- 两个并发 CREATE_NEW 命中同一有效 Anchor 时，至多一个创建 Root。
- 获胜方只有在 Entity 已进入一个确切成功发布的 Snapshot、并形成带发布证明的稳定 Root 后才可成为失败方下一 Attempt 的 LINK 候选。失败方不能读取、引用或链接获胜方尚未发布的 Candidate State，也不能盲目把 CREATE 改为 LINK。
- 同一个 External Key 出现不兼容 Kind、Context 或多个 Entity 时返回 `IDENTITY_COLLISION`，不能以后写覆盖前写。
- 多个 Anchor 只有在身份连续性完成准入后才能归属于同一 Entity；名称相同不是充分条件。

如果实现需要在最终发布前协调热点身份键，只能创建 Attempt-local、不可查询、可过期清理的 `Identity Reservation`。Reservation 不是 Entity Root、Entity State、Formal Knowledge Reference 或 Snapshot 成员，不得被其他 Attempt 当作 LINK 目标。Candidate Bundle 内的 Entity、Fact 和后续对象使用局部引用，由最终发布事务在同一原子 Candidate Closure 中替换。

## 9. 重命名、移动与身份纠正

### 9.1 Continuity

重命名、文件移动、包迁移或来源位置改变继续使用同一 Entity ID，必须存在：

- 来源直接提供的 rename/move/object-ID 连续性，并由 Anchor Contract 机械验证；或
- 后续经准入的正式知识证明身份连续性。

只有“旧对象消失、新对象相似”时不能强制复用 ID。保守结果是创建新 Entity，并在足够依据形成后用普通 Inference 表达可能的 `EVOLVED_FROM`；该关系不能反向合并两个 ID。

### 9.2 错误链接与重复身份

Snapshot 和稳定引用不可回写：

- 新证据表明旧 Anchor 链接错误时，在新 Candidate Snapshot 中停止该 Anchor 的未来链接并重新解析；旧 Snapshot 保持原样。
- 已发布 Fact / Inference 对错误 Entity 的引用必须进入影响重验证，不能只改搜索索引。
- 已存在两个 Entity 后发现可能同一，不直接删除、复用或重定向任一稳定 ID。当前流程只允许未来 Mention 选择其中一个；正式身份合并/等价需要以后单独的 Admission 与迁移 Contract。

该保守边界避免“修复一次重复”演变成对历史引用的不可审计重写。

## 10. Scope 与跨系统规则

1. 每个 Entity 恰好一个 owning KnowledgeScope；Scope 是身份键的一部分。
2. 不同 System Scope 中的同名 Entity 默认不同，名称和相似代码不能自动合并。
3. Shared Component 的定义 Entity 只属于 Shared Component Scope；宿主系统不复制其身份。
4. 宿主日志、Trace、配置和 DB Evidence 属于宿主 System Scope；它们与共享组件的关系由跨 Scope Fact / Inference 表达。
5. 跨系统 Business Entity 归属于 Business Domain Scope。各系统技术 Entity 仍保留原 Scope，通过正式关系关联，不吸收到 Domain Scope。
6. 创建 Business Domain / Shared Component Entity 所用 Evidence 必须在该 owning Scope 的合法来源边界内；来自另一 Scope 的正式知识只能通过确切 Upstream Snapshot Reference 参与推断型路径。

## 11. 模型能力、Strategy 与评测

### 11.1 AI Native Resolution

模型适合承担：

- 非结构化内容中的 Mention 发现。
- 名称、路径、上下文和历史线索的歧义分析。
- 在有界候选集合中提出 LINK / CREATE / UNRESOLVED。
- 解释为何需要补充 Evidence 或 Continuity 信息。

平台不可让渡：

- Scope、Schema、Evidence、Anchor 与 Expected Current Binding 固定。
- Canonical External Key、唯一约束和 Context 合法性。
- 稳定 ID 分配、Candidate-local 引用替换和原子提交。
- 风险分类、独立准入和历史 Snapshot 不可变性。

随着模型增强，可以减少基于名称相似度的脆弱规则和来源特有消歧代码；稳定 Identity Anchor Contract、未解析状态、唯一性、准入和 Snapshot 边界仍然保留。模型退化时可以切换已评测 Strategy，不改变 Entity Contract。

### 11.2 Capability Evaluation

Entity Mention Extraction 与 Entity Resolution 分别拥有 Capability / Evaluation Contract。评测至少覆盖：

- Mention precision / recall 和关键身份遗漏率。
- False Merge、False Split、错误 CREATE 和不必要 UNRESOLVED。
- 重命名/移动 Continuity、同名跨 Scope、共享组件与宿主运行 Evidence。
- 对未见命名风格、混乱遗留工程和非 DDD 系统的泛化。
- 模型、Prompt、Anchor Strategy 变化后的回归、成本和延迟。

False Merge 与 False Split 必须分别报告，不能用一个平均准确率掩盖；门禁阈值由具体 Contract 和用途定义，不在一般设计中写死。

## 12. 失败、重试与并发

| 类别 | 处理 |
|---|---|
| EVIDENCE_REFERENCE_INVALID | 不构造 Mention 或 Candidate；Materialization 未成功时不存在可用 Evidence Reference |
| EVIDENCE_UNAVAILABLE / RESTRICTED | 当前用途不能独立读取时不构造 Mention 或 Candidate；不使用模型记忆替代 |
| MENTION_LOCATOR_INVALID | 拒绝 Proposal；修正必须完整重提 |
| ANCHOR_CONTRACT_UNSUPPORTED | KEEP_UNRESOLVED 或返回能力缺失；不以名称兜底强绑 |
| ANCHOR_UNSTABLE | KEEP_UNRESOLVED，保留限制 |
| SCOPE_MISMATCH | 拒绝跨 Scope 裸 LINK |
| ENTITY_KIND_MISMATCH | 拒绝；不修改已有 Entity Kind |
| CONTEXT_INCOMPATIBLE | 禁止聚合相应 Anchor Observation；保持独立身份线索，不强制 LINK |
| CONTEXT_UNKNOWN / NOT_COMPARABLE / ASSESSMENT_STALE | 需要聚合时 KEEP_UNRESOLVED；重新比较或补充正式依据，不能以名称或模型判断兜底 |
| ENTITY_NOT_IN_BASE_SNAPSHOT | 只有同 Scope、带成功发布证明且 Identity Key 兼容的历史 Root 才可用于身份延续；否则不回退 CURRENT、名称或任意历史 State |
| IDENTITY_AMBIGUOUS | KEEP_UNRESOLVED，保存候选集合和原因 |
| IDENTITY_COLLISION | 隔离冲突并重新执行 Resolution；不能覆盖 |
| EXPECTED_CURRENT_MISMATCH | 实际 CURRENT 与 PRESENT(ref) 或 NO_CURRENT 期望不一致；当前 Candidate 不发布，基于新观察创建新 Attempt |
| UPSTREAM_ENTITY_NOT_IN_PINNED_SNAPSHOT | 不返回引用，不回退查询 CURRENT 或裸 Entity ID |
| STRATEGY_FAILED / MODEL_UNAVAILABLE | 按激活政策有界重试/回退；不得降低身份门禁 |
| ADMISSION_REJECTED | 不创建 Root/State；保留审计与补证问题 |
| PUBLICATION_OUTCOME_UNKNOWN | 按 Attempt / Idempotency Key 查询权威发布结果；确认失败前不释放 Reservation，确认成功前不暴露 Entity |

- 同一冻结输入和幂等键返回同一 Resolution Result；改变 Evidence、Anchor、Schema、Expected Current Binding 或 Policy 创建新 Attempt。
- 模型重试产生新 Capability Attempt 和完整 replacement Proposal，实际消耗不回滚。
- Candidate 不预留长期稳定 ID；可选 Identity Reservation 只协调唯一键且不可查询，避免失败/取消制造可查询空洞。
- Admission / Publication 使用数据库唯一约束与 Expected Current 条件提交，不依赖应用层先查后写。

## 13. 可观测性与敏感信息

- 传播 Investigation、Mention、Anchor、Resolution、Candidate、Evidence、Expected Current / Upstream Snapshot、Capability、Strategy、Model Call 和 Admission 关联。
- 记录每类 Resolution 决定、UNRESOLVED 原因、碰撞、False Merge/False Split 回归、重试和资源消耗。
- 模型只看到授权 Evidence Snapshot、必要候选 Entity State 和 Context；不能看到越权 Scope 的搜索结果。
- Telemetry 中不复制 Evidence 内容、Source-native Secret 或受保护目录数据。
- Resolution Trace 解释采用了哪些输入和 Strategy，不成为 Evidence、Fact 或 Inference。

## 14. 拟议不变量

1. Entity 只表达稳定身份存在与引用，不承载未经正式命题支持的属性和关系。
2. 每个 Entity 恰好一个 owning KnowledgeScope；跨 Scope 同名不自动合并。
3. Entity ID 不包含 Snapshot、名称、路径、Revision、Context、显示顺序或模型版本。
4. Entity Semantic Category 与 Identity Origin 正交。
5. Source-anchored Entity 必须回溯一个或多个各自独立的 Evidence / Mention 与版本化 Identity Anchor Contract。
6. Canonical External Entity Key 是解析索引，不是 Entity ID；名称或路径单独不足以证明稳定身份。
7. 本地身份 Resolution 只有 LINK_EXISTING、CREATE_NEW 和 KEEP_UNRESOLVED；REFERENCE_UPSTREAM 只返回跨 Scope 只读正式引用，不产生本地 Identity Candidate。
8. CREATE_NEW 在目标 Snapshot 最终发布事务前不分配稳定 Entity ID；Candidate Bundle 使用局部引用。
9. LINK_EXISTING 只引用 Expected Current 为 PRESENT 时 target Scope 的确切 Base Snapshot Entity，或带成功发布证明、仅用于身份延续的同 Scope Root；上游引用不能创建本地 State / Anchor，所有路径都不能使用裸 ID、任意历史 State 或 CURRENT 漂移。
10. 重命名或移动只有在 Continuity 可复核时延续 ID；相似性不足时创建新身份并保留未决演化关系。
11. Entity 名称、位置和 Anchor 的检索元数据不能直接支持用户可见属性 Claim。
12. Provider、模型、Agent、Projection 和数据库索引都不能直接创建或合并正式 Entity。
13. Source-anchored 与推断型 Entity 共用稳定身份和 Snapshot 规则，但推断型身份必须由正式知识依赖闭包证明。
14. Anchor 的每个 Observation 分别保留 Evidence、Mention、Source Context 与 Revision；只有 Contract 声明并机械证明的 Context 投影可以进入身份键。
15. Identity Scheme、Canonical Key 与 identity-bearing Context 构成版本稳定的唯一性语义；Schema / Contract / Canonicalizer Version 不能自然放行重复 Root。
16. Entity Root、首个 State、局部引用替换、唯一键声明和 Snapshot CAS 必须在同一最终发布事务中生效；其他 Attempt 的 Candidate State 永远不是 LINK 目标。
17. 错误链接、重复身份和来源变化只能通过新 Candidate / Snapshot 修正，不能回写历史。
18. 每个 Snapshot 中同一 Entity Root 至多一个 Entity State；等价候选必须先形成最终聚合 Candidate 并完成独立审核。
19. 多 Anchor Observation 只有在 identity-bearing Context Projection 机械相等，或 exact Comparison Purpose 下的 Assessment 具有 current VALID Decision 时才能聚合；Assessment 的输入、依据和有效性必须随 Candidate 固定并在 Admission 重验。
20. `INCOMPATIBLE`、`UNKNOWN`、`NOT_COMPARABLE`、执行失败或失效 Assessment 都不能支持 Observation 聚合或身份强制 LINK。

## 15. 验证义务与下游追溯

当前无需 Design Validation Demo 决定稳定 ID、Scope、Anchor、三种 Resolution 决定和未解析边界；这些约束可由身份语义与一致性推演确定。

具体 Provider / Artifact Kind 的 Identity Anchor 实现必须通过 Contract Conformance，覆盖：

- Identity Domain / External Key 规范化与碰撞。
- 名称、路径和稳定键的区分。
- Context、重命名、移动和来源 Revision。
- 多 Observation identity-bearing Context 的机械相等、COMPATIBLE Assessment、latest VALID 重验，以及 INCOMPATIBLE / UNKNOWN / NOT_COMPARABLE / STALE 的失败关闭。
- 并发 CREATE、LINK 重评、未解析和权限边界。

模型或 Hybrid Mention / Resolution Strategy 必须通过 Capability Evaluation。只有当真实来源无法判断某个 Anchor Contract 能否在重命名、分支或多工程条件下提供稳定身份，并且该选择会改变公共身份契约时，才登记 `DVR-*` 和有界 Demo；Demo 结果不能直接成为全局 Entity 粒度或身份算法。

下游主题必须遵守：

- DD-KNW-FACT：Fact Candidate 只能引用已发布 Entity 或同一原子 Candidate Bundle 中的局部 Entity Reference。
- DD-KNW-INFERENCE-CONFLICT：Semantic Entity Proposal、EntityDerivation Inference 与推断型 Entity 原子准入。
- DD-KNW-ADMISSION：独立重读 Anchor / Evidence，审核 Local Reference Substitution、身份连续性与唯一性 preflight；不分配稳定 ID。
- DD-KNW-SNAPSHOT-PUBLICATION：在最终事务中分配稳定 Entity ID，并负责 Entity State、Base CAS、退出、重现和跨 Scope Snapshot 依赖。
