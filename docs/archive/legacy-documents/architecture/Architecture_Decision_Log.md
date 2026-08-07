# Software World Model 架构设计决策清单

本文档记录已经确认的架构决策、后续细化关系和历史演进依据。当前生效的概要架构见 [Software_World_Model_Architecture_Baseline.md](Software_World_Model_Architecture_Baseline.md)；本日志解释“为什么这样设计”，不承担概要架构正文或详细契约职责。

> 本清单保留决策形成时的原始术语和阶段性结论，不回写历史措辞；同一主题以较新的决策及当前基线为准。早期决策中的 `Semantic Model` 组件在当前基线中统一命名为 `Semantic View Engine`。

## 已确认决策

### AD-001：内部系统优先验证功能闭环

- 当前系统面向内部可信用户和受控环境。
- 现阶段优先保证核心功能跑通并可用。
- 安全、性能、可用性、容灾和多租户等非功能能力只保留架构扩展边界，后续按实际需要补充。

### AD-002：Evidence 与 Fact 概念分离

- Evidence 表示原始依据及其定位信息。
- Fact 表示从 Evidence 中确定性提取、标准化后形成的客观陈述。
- Fact 是关于指定数据源的可验证观察，不代表现实世界中的绝对真相。
- MVP 阶段 Evidence 可以内嵌在 Fact 中物理存储。
- Evidence 和 Fact 从第一天采用独立领域类型、稳定 ID 和访问接口，保证后续可以低成本拆分存储。

> **后续细化：** AD-095 保留 Evidence 与 Fact 的认知边界，但不再用“是否由确定性代码生成”判定知识性质。模型可以提出 Fact Candidate；它仍须由平台重建来源锚点并经过同一知识准入，才能成为正式 Fact。

### AD-003：Fact 与 Inference 分层

- Fact 由数据源经过确定性提取和标准化生成，不经过开放式语义推理。
- Inference 是基于一个或多个 Fact 得到的 Behavior、Business 或其他高阶结论。
- Fact Layer 不反向依赖 Inference Layer。
- Inference 必须保留到输入 Fact 的推导关系。
- 不在主领域模型中引入 Claim 作为独立对象；相关职责由 Fact 和 Inference 分别承担。
- KnowledgeRecord 仅作为可能的内部公共接口，出现实际统一处理需求时再引入。

> **后续细化：** AD-087、AD-091 和 AD-095 将本条中“Fact 不经过开放式语义推理”细化为：Fact 与 Inference 按正式命题的认知性质、直接 Evidence 支持和推导关系区分，而不是按 Candidate 的生成者区分。模型可以识别并提出直接观察型 Fact Candidate；超出直接观察的抽象结论仍必须进入 Inference 准入。

### AD-004：语义模型是可物化的组合视图

- Structure、Behavior、Business、Runtime、History 表示知识的语义维度。
- Fact、Inference 表示知识的认知性质。
- Environment、Version、Time 表示知识成立的上下文。
- Evidence、Fact 和 Inference 是需要持久化的标准知识记录。
- Behavior、Business 等 Inference 结果需要持久化并保留推导链。
- 完整语义视图由 Fact、Inference 及其关联关系组装而成。
- 语义视图可以动态生成，也可以物化存储，但物化结果必须可重建，不能成为新的真相源。

### AD-005：Snapshot 当前只保留最新版本

- Snapshot 从第一天进入领域模型和查询接口。
- 当前只维护一个 ACTIVE 模型版本，不提供历史 Snapshot 查询。
- 查询默认使用 CURRENT Snapshot。
- 新版本完成 Fact、Inference 和相关投影构建及验证后，再原子切换为 ACTIVE。
- Snapshot 历史保留采用可配置策略，当前为 LATEST_ONLY，未来可以扩展为 LAST_N、TIME_WINDOW 或 PERMANENT。
- 是否保存旧 Fact 和 Inference 属于存储保留策略，不影响 Snapshot 的领域接口。

### AD-006：Inference 采用受控的两级推理

- 默认 Inference 只能直接依赖 Fact。
- L1 Inference 只允许依赖 Fact。
- 确有必要时，L2 Inference 可以依赖 Fact 和经过验证的 L1 Inference。
- MVP 阶段不允许 L3 及更深层级的推理依赖。
- 作为输入的 L1 Inference 必须是结构化结论，具有明确的验证状态，并能够完整回溯到 Fact。
- L2 Inference 同时保存直接依赖和展平后的底层 Fact 依赖。
- 推理依赖必须无环；上游 Fact 或 Inference 失效时，下游 Inference 必须同步失效。
- 推理准确性不能只依靠置信度阈值控制，还需要结合推理深度、输入类型、验证状态、事实覆盖和失效传播。

> **后续细化：** AD-116 将“两级”从一般架构硬约束下沉为可评测的 Capability Strategy。当前稳定约束是依赖有界、无环、可完整回溯并可随上游失效重新验证；具体最大深度在详细设计和能力评测中确定。

### AD-007：同一客观事实只维护一个 Fact

- Fact 表示去重后的唯一客观陈述，不表示单份数据源记录。
- 同一时间、版本和上下文中的同一客观事实只维护一个 Fact。
- 代码位置、Trace 实例、配置记录和数据库查询结果等作为 Evidence 关联到 Fact。
- 多份 Evidence 用于增强同一 Fact 的可验证性，不重复生成等价 Fact。
- 只有客观陈述本身或其适用上下文不同，才生成不同 Fact。

### AD-008：Fact 归并与验证暂采用代码优先策略

**状态：暂定，需根据实施效果复审。**

- Evidence 先生成 Fact Candidate，再由 Fact Resolver 完成归并和验证。
- Fact Resolver 的确定性归并、上下文比较、状态转换和失效处理由代码实现。
- 模型可以用于非结构化内容理解、实体匹配和候选 Fact 提议，但暂不直接将 Fact 标记为 ACTIVE。
- Fact Resolver 必须通过独立策略接口提供能力，不能将规则固化在 Extractor、存储层或业务流程中。
- 初始实现采用 RuleBasedFactResolver，未来可以替换或扩展为 ModelAssistedFactResolver、HybridFactResolver。
- 每次归并和状态判定需要记录所使用的策略、规则或模型版本以及判定原因，以便后续比较方案效果。
- 在获得真实数据和评测结果后，重新评审模型在 Fact 激活决策中的权限。

### AD-009：Fact 身份稳定，状态随 Snapshot 演化

- 同一客观陈述在多个代码版本或模型版本中持续成立时，只维护一个稳定的 Fact ID。
- Fact ID 不包含代码版本或 Snapshot ID。
- Fact 本体保存 subject、predicate、object/value 等稳定语义。
- FactState 保存指定 Snapshot 下的状态和有效 Evidence。
- 当前只保留最新 Snapshot 时，可以只物理保存最新 FactState，但领域接口需要保留按 Snapshot 查询状态的能力。
- Fact 在后续版本失效或重新出现时继续使用原 Fact ID，通过 FactState 表达 ACTIVE、INVALIDATED 等状态变化。

### AD-010：Entity 身份稳定，名称和位置随 Snapshot 演化

- Entity ID 表示稳定身份，不根据当前名称、文件路径或代码位置直接生成。
- EntityState 保存指定 Snapshot 下的名称、限定名、来源位置和状态。
- 能够通过明确变更信息识别的重命名或文件移动继续使用原 Entity ID。
- 仅观察到旧实体删除和新实体新增、但无法确认身份连续性时，不强行合并。
- 无法确认时创建新 Entity，并通过待验证的 EVOLVED_FROM Inference 表达可能的演化关系。

### AD-011：公共依赖使用独立的共享组件 Scope

- DataSourceBinding 的归属字段从 systemId 泛化为 scopeId。
- KnowledgeScope 当前至少支持 SYSTEM 和 SHARED_COMPONENT 两种类型。
- 公共 Jar、公共 SDK 和公共内部库使用独立的 SHARED_COMPONENT Scope，不归属于某个具体业务系统。
- 公共组件的源码只采集和解析一次，其定义、源码和静态结构知识归属于共享组件 Scope。
- 业务系统通过带版本的依赖关系引用共享组件，不重复绑定或复制公共组件源码。
- 不同业务系统可以引用同一共享组件的不同版本。
- 只有 Jar 或制品信息时，可以使用 Maven 坐标或制品标识建立共享组件；后续获得源码时继续绑定到同一 Scope。

### AD-012：跨系统业务通过语义关联连接多个独立 Scope

- KnowledgeScope 按独立系统或共享组件划分，不按跨系统业务流程合并。
- 一个业务涉及多个系统时，为每个系统建立独立 Scope。
- Business Domain 和 Business Entity 位于多个 Scope 之上，通过跨系统语义关系连接各系统中的技术 Entity。
- 不同 Scope 中的同名 Entity 默认视为不同对象，不根据名称自动合并。
- 多个系统中的不同技术 Entity 表达同一业务概念时，分别保留技术身份，并关联到统一的 Business Entity。
- 确实属于同一个共享技术对象时，只在其拥有者或共享组件 Scope 中创建一次，其他系统通过调用或依赖关系引用。

### AD-013：共享组件归属与宿主系统运行上下文分离

- 公共组件的定义、源码和静态结构归属于 SHARED_COMPONENT Scope。
- 公共组件在业务系统中运行时产生的日志、Trace 和数据库行为归属于宿主 SYSTEM Scope。
- 运行 Evidence 使用 sourceScopeId 表示数据产生的宿主系统上下文。
- 运行 Evidence 后续可以通过代码位置、包名、Logger、Stack Trace、构建依赖等信息关联到共享组件 Entity。
- 运行上下文与 Entity 归属允许不同，由 attributedEntityId 表示运行数据实际反映的 Entity。
- Fact 可以建立共享组件 Entity 与宿主系统 Entity、数据库等对象之间的跨 Scope 关系。

### AD-014：Source Artifact 采用统一引用协议，不强制统一 Payload

**状态：暂定，需通过多类型数据源技术验证。**

- Source Artifact 是来源追踪、版本识别、幂等处理和可重建能力所必需的架构对象，不能省略。
- Source Artifact 统一 artifactId、artifactType、sourceId、scopeId、externalKey、revision、contentHash 和 contentReference 等身份与引用信息。
- 不要求代码、DB、日志、Trace 和文档生成完全相同的 Payload 结构。
- 不同 Artifact 类型由专用 Processor 解析；必要时可以生成具有完整来源关系的 DerivedArtifact。
- 稳定且具有不可变版本的数据源可以默认只保存外部引用。
- DB Schema、动态配置、即将过期的日志或 Trace 等无法可靠重取的数据，必须按类型策略保存必要快照或最小证据内容，不能一律采用引用存储。
- 在最终确定 Artifact Payload 和存储策略前，需要使用代表性代码、DB Schema、结构化与非结构化日志、Markdown/Word/PDF 文档验证解析准确性、原文定位、可重放性和存储放大率。

### AD-015：Source Artifact 粒度按数据源类型实证确定

**状态：暂定，需通过真实项目验证。**

- 不为所有 Data Source 规定统一的 Artifact 粒度。
- Git 文件、DB 表结构、文档版本、Trace、日志批次等当前仅作为候选默认粒度。
- 每种 Artifact 类型通过独立的 ArtifactGranularityPolicy 配置粒度，避免将策略固化在统一协议中。
- 最终粒度需要使用真实项目，根据变更频率、增量重处理成本、Evidence 定位精度、外部内容可重取性和 Artifact 元数据规模确定。
- 无论采用何种粒度，Artifact 都必须具有稳定身份、明确来源、单一版本边界，并支持 Evidence 精确定位。
- Artifact 不得跨越不同 KnowledgeScope 或不可区分的多个源版本。

### AD-016：Artifact 采用按类型和引用状态控制的淘汰机制

- Artifact 保留策略至少支持 TRANSIENT、SOURCE_MANAGED、PIN_WHEN_REFERENCED 和 ARCHIVE。
- 日志、Trace、Metric 等高容量流水 Artifact 默认短期保留，未被知识记录使用时按 TTL 淘汰。
- Artifact 被有效 Evidence 引用时，不要求永久保存整个 Payload；优先固化包含原始片段、定位信息、内容哈希和外部引用的最小 EvidenceSnapshot。
- 只有确需完整重放的重要 Artifact 才归档完整内容。
- Artifact 淘汰不能破坏 Evidence、Fact 和 Inference 之间的引用完整性，淘汰前必须完成引用检查和必要的最小证据固化。
- Artifact 或外部引用过期只表示证据不可访问，不代表事实被推翻。
- 因全部支持证据过期而无法验证的 Fact 标记为 UNVERIFIABLE；只有明确反证或适用版本变化才能标记为 INVALIDATED。

> **后续细化：** AD-128 替代本条最后一项的可变 Fact 状态做法。已发布 Fact / Inference State 保持其确切 Snapshot 内的历史断言；新 Snapshot 无法重验时不选择该 State，并记录最小重验证诊断，不能把证据不可访问解释为命题为假。

### AD-017：Evidence 是中立且可定位的原始内容片段

- Evidence 保存 Source Artifact 或 DerivedArtifact 中可验证的具体内容及其稳定定位，不直接保存知识结论。
- Evidence 本体不声明自己支持或反驳哪项 Fact。
- Evidence 对 Fact Candidate 或 Fact 的 SUPPORTS、CONTRADICTS、PARTIALLY_SUPPORTS 等作用保存在独立关联中。
- 同一 Evidence 可以参与多个知识判断，并对不同判断具有不同关系。
- Evidence 必须包含 artifactId、locator 和 contentHash；原始内容可能过期时按保留策略保存最小 snapshotContent。
- Extractor 或模型不能改写 Evidence 原文，只能解释其语义并建立知识关联。

### AD-018：知识构建采用 Evidence 驱动的候选事实流程

- Extractor 处理 Artifact 时一次输出 Evidence、Fact Candidate 以及二者的关联。
- 不对 Artifact 做无目标的全量 Evidence 切分；提取目标由启用的 Use Case、Knowledge Schema 和 ExtractionProfile 决定。
- Fact Candidate 必须至少具有一份直接 Evidence。
- 尚无 Evidence、仅用于指导证据搜索的判断称为 Hypothesis，不能进入 Fact Layer。
- Fact Candidate 由 Fact Resolver 按 FactValidationPolicy 验证后才能成为正式 Fact。
- Fact 是否成立不能根据 Evidence 数量简单判断。
- 确定性、可复现且覆盖完整的一份权威 Evidence 可以确认 Fact；语义性、启发式或覆盖片面的候选事实需要独立多来源佐证或其他验证。
- 验证结果至少区分 ACTIVE、PARTIAL、CONFLICTED 和 UNVERIFIED。

### AD-019：AI Native 是系统级顶层架构原则

- AI Native 覆盖数据源理解、Artifact Processing、Evidence 调查、Entity Resolution、Fact Construction、语义建模、演化、查询和验证等完整知识生命周期。
- AI Native 的目标是提升系统智能、通用性以及对不同模型和模型迭代的适应能力，不以减少工程工作为目标。
- 系统不得为了使用模型而放弃准确性、来源追踪、版本上下文、可重建性和结果可信性。
- 具有明确语义和稳定算法的操作优先使用确定性工具；AI 负责目标理解、动态规划、工具选择、跨源关联、语义判断和下一步调查。
- AI 生成的知识必须有可定位 Evidence、结构化输出、推导链、验证结果和明确的不确定性；证据不足时必须允许拒绝确认。
- 模型调用必须经过统一的模型抽象、能力路由、版本记录和评测门禁，避免核心知识逻辑绑定单一模型、Prompt 或厂商。
- 模型升级不能直接改变已确认知识；新模型需要通过回放、对比评测和受控重建后才能参与正式知识更新。
- 准确性和可信性优先于自动化程度；AI Native 不等于 LLM Everywhere，也不等于用概率判断替代所有确定性程序。

### AD-020：Data Source Connector 作为 Agent 可发现的确定性工具

- Connector 不由固定全量流水线统一调度，而以自描述 Tool 的形式注册到 Connector Tool Registry。
- Agent 根据目标、上下文和调查进展动态发现、选择和组合 Connector Tool。
- Connector Tool 描述至少包含工具名称、用途、输入 Schema、输出 Artifact 类型、成本提示、数据新鲜度和限制条件。
- Connector 可以提供 search、get、listChanges、aggregate 等面向源系统能力的操作，不局限于统一 collect 接口。
- Agent 负责选择数据源和制定调用计划；Connector 只负责准确执行读取、查询和采集，不进行开放式语义推理。
- Connector Tool 的标准输出为具有稳定来源、版本和引用的 Source Artifact 或 Artifact Reference。
- 后台批量和增量同步仍可存在，但不再是访问 Data Source 的唯一方式；Agent 可以按调查需要动态获取补充 Artifact。

> **后续细化：** AD-059、AD-060 与 AD-110 保留 Connector Tool 的自描述、可发现和动态组合能力，但将调用路径收口到 Application Services。Agent 选择的是应用层公开的来源调查能力，不直接访问 Connector Registry；Application Services 编排，Source Integration 持有凭据并执行 Tool。

### AD-021：Connector 扩展拆分为 Provider SPI 与 Tool SPI

- Connector Provider SPI 表示一种可安装的 Connector 插件，负责插件描述、配置 Schema、Data Source 配置验证、连接或客户端管理以及 Tool 注册。
- 一个 Connector Provider 可以服务多个同类型 Data Source 实例。
- Connector Tool SPI 表示 Provider 暴露的一项可调用能力，负责声明结构化输入输出并执行单一明确操作。
- 一个 Provider 可以注册多个 Tool，例如 Git Provider 注册 searchCode、getFile、getCommit 和 listChanges。
- 平台和插件系统主要使用 Provider；Agent 通过 Tool Registry 发现并调用 Connector Tool。
- Provider 管理的配置、凭证和连接不能由各 Tool 重复实现或直接暴露给 Agent。
- Connector Provider、Connector Tool、输入输出 Schema 和 Artifact Schema 均需要独立版本标识。

> **后续细化：** Provider / Tool 两级 SPI 仍然生效；其中“Agent 发现并调用”表示经 Application Services 暴露的动态能力，不表示 Agent 可以绕过 Source Integration 的配置、授权和 Artifact 边界直接调用 Connector。

### AD-022：只有信息载体才生成 Source Artifact

- 搜索、列表和发现类 Tool 默认返回轻量 SourceObjectRef，不为每条候选结果创建 Source Artifact。
- Agent 确认候选对象相关并调用 get、fetch 等内容读取 Tool 后，才生成 Source Artifact。
- Source Artifact 必须包含或稳定指向能够被独立解释、版本化和作为 Evidence 来源的原始信息内容。
- 纯索引、目录项、分页列表、候选指针和平台生成的摘要不是 Source Artifact。
- Connector Tool 的输出类型至少区分 DISCOVERY_RESULT、ARTIFACT_RESULT 和 STREAM_RESULT。
- 如果搜索结果本身已经包含完整、不可变、可定位的源记录，例如具有唯一 eventId 的完整日志事件，可以直接作为 Artifact，而不要求额外 fetch。

### AD-023：DerivedArtifact 属于 Artifact Processing 层并保留加工链

- Artifact 体系区分直接来自外部数据源的 SourceArtifact 和由平台处理生成的 DerivedArtifact。
- Connector Tool 生成 SourceArtifact；Artifact Processor 使用解析器、工具或模型生成 DerivedArtifact。
- DerivedArtifact 必须是可复用、可独立解释且具有稳定来源链的信息载体，不用于保存单次 Agent 任务的临时推理状态。
- 单次任务的计划、搜索候选、Hypothesis 和临时判断进入 InvestigationRun 或 WorkingMemory，不进入 Artifact 体系。
- Evidence 可以引用 SourceArtifact 或 DerivedArtifact；引用 DerivedArtifact 时必须能够继续回溯到原始 SourceArtifact。
- ArtifactLineage 记录 outputArtifactId、inputArtifactIds、processor、模型和参数版本等加工元数据，用于来源追踪、重建、变更传播和模型版本评测。
- MVP 中单输入 DerivedArtifact 可以内嵌 derivedFromArtifactId 和 processorVersion；出现多输入或多级加工后再拆分为独立 ArtifactLineage 关系。

### AD-024：DerivedArtifact Payload 按重建成本分级存储

- DerivedArtifact 的身份、内容哈希、Processor 版本和 ArtifactLineage 等重建元数据必须保留。
- DerivedArtifact Payload 不要求全部长期保存，按 EPHEMERAL、CACHED、MATERIALIZED 三类策略管理。
- 生成成本高、复用频繁、被有效 Evidence 引用、需要模型版本对比或原始输入可能失效的 DerivedArtifact 优先物化保存。
- 生成成本低、使用频率低且可以从 SourceArtifact 快速重建的 DerivedArtifact 可以仅缓存或临时保存。
- Evidence 引用的 DerivedArtifact 淘汰前必须保存最小 EvidenceSnapshot，或保证 locator 可以稳定映射回 SourceArtifact。
- DerivedArtifact 存储策略变化不能改变其 ID、Lineage 和上层 Evidence 接口。

### AD-025：预留独立 Initialization 模块

**状态：整体暂缓，待核心模型架构确认后单独讨论。**

- 系统需要预留独立的 Initialization 模块或能力。
- Initialization 的作用范围、输入输出、生命周期、Agent 与 Runtime 分工、状态模型和 Snapshot 激活机制均未形成结论。
- “提供系统工程及关联 Git 后初始化到什么程度”属于 Initialization 模块设计，不在当前模型架构讨论中展开。
- 当前模型架构不依赖任何尚未确认的 Initialization 详细流程。
- 依赖方向固定为 Initialization 模块依赖核心模型架构；核心模型架构不能为了适配某个初始化流程而引入初始化专用概念或字段。
- Evidence、Entity、Fact、Inference、Artifact 和 Snapshot 等模型先独立定义其语义与约束，Initialization 后续只通过这些模型提供的标准接口完成首次构建。
- 初始化进度、任务状态、检查点和失败恢复等属于 Initialization 应用模块，不进入核心知识模型。

### AD-026：Evidence 与 Artifact 保持单一来源关系

- 一条 Evidence 只能引用一个 SourceArtifact 或 DerivedArtifact，并在该 Artifact 内使用一个明确 locator 定位内容。
- 一条 Evidence 不得混合多个 Artifact 的内容、版本或时间上下文。
- 多个 Artifact 描述同一客观事实时，分别生成多个 Evidence。
- 多个 Evidence 通过 FactEvidenceLink 共同支持或反驳同一个 Fact Candidate 或 Fact。
- 证据增强发生在 Evidence 与 Fact 的聚合层，不发生在 Evidence 内部。
- DerivedArtifact 即使具有多个输入，也只通过 ArtifactLineage 回溯来源；引用该 DerivedArtifact 的 Evidence 仍保持单 Artifact 关系。

### AD-027：核心知识主干采用 Evidence 驱动的 Entity、Fact、Inference 分层

- Artifact 提供可读取的信息载体，Evidence 是其中可定位、可验证的原始内容片段。
- Evidence 一方面支持 Entity Mention 的识别与身份解析，另一方面提供关系或属性线索。
- Entity 完成身份解析后，才能与关系或属性线索共同形成引用稳定 Entity ID 的 Fact Candidate。
- Fact Candidate 经过验证后成为 Fact；Entity 间关系和 Entity 属性均以 Fact 表达。
- Inference 以一个或多个 Fact 为客观输入，通过 AI 分析和归纳形成 Inference Candidate，经验证后成为正式 Inference。
- Inference 不复制 Evidence 内容，而是通过所依赖的 Fact 回溯 Evidence，保持完整的推导链。
- 未完成身份解析的 Entity Mention 和关系线索不能提前作为正式 Fact Candidate，未经验证的推断也不能进入正式 Inference。

核心主干为：

```text
Artifact
   ↓
Evidence
   ├──→ Entity 识别与身份解析 → Entity ─────────┐
   └──→ 关系 / 属性线索 ─────────────────────────┤
                                                ↓
                                         Fact Candidate
                                                ↓
                                           Fact 验证
                                                ↓
                                              Fact[]
                                                ↓
                                      Inference Candidate
                                                ↓
                                        Inference 验证
                                                ↓
                                            Inference
```

### AD-028：语义模型是 Entity、Fact 与 Inference 的组织和投影视图

- Structure、Behavior、Business 和 History 等语义模型不是位于 Inference 之后的新知识层。
- 语义模型从统一的 Entity、Fact 和 Inference 知识底座中选择并组织内容，为特定领域和用途提供视图。
- 同一个语义模型可以同时包含 Fact 和 Inference；不同模型中二者的比例可以不同。
- 语义模型本身不产生新的事实或结论；分析过程中产生的新客观判断进入 Fact 流程，语义结论进入 Inference 流程。
- 同一 Entity、Fact 或 Inference 可以同时出现在多个语义模型中，不复制其知识身份。
- 语义模型默认可以重建；为性能保存的物化结果是可失效、可重建的投影，不成为新的权威知识来源。

```text
Entity + Fact + Inference
          ↓ 组织 / 投影
Structure | Behavior | Business | History
```

### AD-029：KnowledgeContext 贯穿知识链并支持非破坏性融合

- KnowledgeContext 从 Data Source 和 Artifact 开始，贯穿 Evidence、Fact、Inference 和语义模型，不能到 Fact 阶段才补充。
- KnowledgeContext 至少能够表达 KnowledgeScope、Environment、Version 和 Time 等维度，但允许不同数据源只提供部分维度或使用各自原生标识。
- Artifact 保留采集时已知的源上下文；Evidence 保留该上下文，并可根据其可定位内容进一步缩小或补充适用范围，不能静默覆盖来源信息。
- 上下文融合是保留来源的组合与智能关联，不是把多份上下文覆盖、归一或硬映射为一个标签。
- 来自不同维度且相互兼容的上下文可以组合成更具体的适用范围；同一维度不一致时必须并存，用于关联、比较或冲突分析。
- 跨数据源的版本、部署、环境等关系如果有明确标识，可以作为确定性 Fact；如果只能通过语义和线索判断，则形成可追溯、带不确定性的 ContextCorrelation Inference。
- ContextCorrelation 不能反向修改原始 Artifact 或 Evidence 的上下文，也不能把推测伪装成确定关系。
- Fact 和 Inference 必须保留其上下文依据；输出知识的适用范围不能无依据地超过输入信息能够支持的范围。
- Evidence 不依赖预先建立的全局版本映射才能参与分析；系统围绕构建准确语义模型的目标，动态选择、关联和验证来自不同上下文的信息。

### AD-030：采用统一知识底座和上下文参数化语义模型

- 系统不为每个环境、代码分支、部署版本或时间点复制一套彼此隔离的完整知识模型。
- Entity、Fact、Inference 及其 KnowledgeContext 共同构成统一知识底座，并完整保留各来源和上下文差异。
- 语义模型根据使用目标选择、关联和验证相关上下文中的知识，形成上下文参数化的投影视图。
- “使用所有信息”表示所有信息均可参与目标驱动的调查，不表示把所有上下文中的知识无差别混入同一结果。
- 单上下文视图可用于观察当前生产环境等目标；多上下文视图可用于环境对比、版本差异和代码与线上行为偏差分析。
- 无法确认目标上下文时，必须保留并展示多个可能结果或不确定性，不能静默归并为单一结论。
- 为查询性能保存的上下文 Snapshot 或物化语义模型仍是统一知识底座的可失效、可重建投影，不成为独立权威知识库。

### AD-031：History 是跨时间的演化语义视图，不独占因果解释

- Time 和 Version 属于贯穿知识链的 KnowledgeContext 维度；History 属于利用这些上下文组织知识的语义模型。
- History 的核心职责是描述系统在时间维度发生了什么变化、如何演化至当前状态，并组织能够解释变化原因的知识。
- “是什么、如何、为什么”是查询和推理方式，不是划分各语义模型的唯一标准；Structure、Behavior、Business 和 History 均可以回答其中一个或多个问题。
- 因果解释通常属于 Inference，可以出现在任一语义模型中；故障根因不能因为回答“为什么”就被归入 History。
- Requirement、Decision、Code Change、Deployment、Runtime Impact 等可验证事件和关系以 Fact 表达；需求导致代码变化、代码变化引发运行影响等未被直接确认的因果关系以 Inference 表达。
- History 不复制这些 Fact 和 Inference，而是按时间、版本和演化关系对统一知识底座进行跨上下文投影。

### AD-032：Structure 描述实体组织和不依赖具体执行的结构关系

- Structure Model 描述在给定 KnowledgeContext 中有哪些软件实体，以及它们如何被组织和静态连接。
- Structure 投影 System、Service、Module、Class、API、Table、Topic 等 Entity，以及包含、实现、暴露接口和声明依赖等结构 Fact。
- 根据证据推断出的架构分层、组件边界、职责归属等内容以 Inference 表达，也可以由 Structure Model 展示。
- Structure 与 Behavior、具体执行观察的核心边界是：不依赖某次具体执行及其先后顺序即可成立的关系属于 Structure。
- 代码声明的静态调用或依赖可以进入 Structure；带有执行顺序、条件和状态迁移的调用进入 Behavior；某次请求中实际发生的调用形成带运行上下文的 Fact。
- 文档中的笼统“调用关系”必须进一步表达其语义类型，不能把静态可能性、通用行为和实际运行观察合并为同一种关系。

### AD-033：Behavior 描述可复用的执行规则和模式

- Behavior Model 描述系统在特定条件下可以或应当如何执行，不用于保存某一次已经发生的执行记录。
- Behavior 关注执行步骤和顺序、分支条件、状态迁移、事件触发、前置条件、结果及副作用。
- 由代码、工作流定义或状态机明确定义且可验证的执行规则以 Fact 表达。
- 跨代码、文档和运行信息还原或归纳出的通用流程和状态机以 Inference 表达。
- Trace、Log 等记录的某次具体调用路径形成带运行上下文的 Fact；单次运行记录不能直接提升为通用 Behavior。
- 具体执行观察可以验证、补充或反驳 Behavior；确认通用 Behavior 需要明确规则或足够且适用上下文一致的证据支持。
- Behavior 表达可复用的执行规则或模式；具体执行实例及实际观察保留为带环境、版本和时间上下文的 Fact，并按需进入相关语义视图。

### AD-034：Business 连接跨系统业务语义与技术实现

- Business Model 描述软件承载的业务概念、规则、能力和目的，以及这些业务语义如何由一个或多个系统实现。
- Business Domain 和 Business Entity 位于多个独立 KnowledgeScope 之上，通过语义关系关联各系统中的技术 Entity、Fact 和 Behavior。
- Business 与 Behavior 的核心边界是：Behavior 描述系统如何执行，Business 描述该执行在业务上代表什么以及实现什么目的。
- Business Model 不是纯 Inference 视图；有权威来源并经过验证的业务概念、规则和映射可以形成带上下文的 Fact。
- 根据代码、表结构、接口、文档和运行记录推断出的业务含义、实体归属和技术到业务的映射以 Inference 表达。
- “业务规范声明规则 X”与“系统实际实现规则 X”是两个不同的判断，必须分别建立 Evidence 和 Fact，不能用规范直接证明实现。
- 同一个 Business Model 可以共同投影 Business Entity、业务 Fact、业务 Inference 以及跨 KnowledgeScope 的技术实现关系，不复制底层知识身份。

### AD-035：Runtime 不作为独立核心语义模型

- 静态来源和动态来源的信息遵循同一条 Artifact、Evidence、Fact Candidate、Fact、Inference 知识构建主干，不形成不同知识层级。
- Log、Trace、Metric、运行数据库查询和部署平台等属于动态 Data Source，其内容生成 Artifact 和 Evidence，与代码、文档和数据库结构 Evidence 使用相同验证机制。
- 环境、部署版本和观察时间通过 KnowledgeContext 表达；某次实际调用、指标值、配置值和状态记录形成带该上下文的 Fact。
- 动态 Evidence 可以支持、反驳 Fact 或限制其适用上下文，但不因来源于运行时而进入单独的 Runtime 知识容器。
- 运行相关 Fact 和 Inference 可以被 Structure、Behavior、History 等语义模型按目标使用，不复制知识身份。
- 从核心语义模型集合中移除 Runtime Model；未来存在当前生产状态查看、故障诊断等明确用例时，可以组合实现 Operational View。
- Operational View 属于应用查询和投影视图，不成为新的权威知识层，也不负责保存原始遥测数据。

### AD-036：语义视图内置但可扩展

- Structure、Behavior、Business 和 History 是首批内置标准语义视图，不构成封闭且不可扩展的固定四维模型。
- 核心知识模型只依赖 Entity、Fact、Inference 和 KnowledgeContext，不反向依赖任何具体语义视图。
- 后续可以注册 Data、Security、Operational、Quality 等新视图，而不修改 Artifact、Evidence、Fact 和 Inference 主干。
- 新视图只能选择、组织和呈现统一知识底座中的知识，不得另建彼此不兼容的 Evidence、Fact 或 Inference 体系。
- 每种正式语义视图必须具有结构化定义、输出 Schema、适用上下文和验证约束，不能由模型每次自由生成不可比较的结构。
- AI 可以根据任务动态选择、组合或参数化语义视图；正式输出仍需符合已注册的视图定义。
- 语义视图默认通过 Registry 扩展；内置与扩展视图使用相同接口和知识引用机制。

### AD-037：Agent 产出必须经过确定性校验和独立语义审核

- Reasoning Agent 只能提交 Candidate Package，不能直接写入正式知识或绕过审核发布需要可信保证的最终答案。
- Candidate Package 不保存模型原始自由思考过程，而保存可移植、可审核的 Structured Argument，包括结论、结构化前提和步骤、Fact 或 Inference 引用、KnowledgeContext 及不确定性。
- 审核首先执行确定性校验，检查 Schema、引用存在性、来源链完整性、上下文兼容性、依赖层级和循环依赖。
- 通过确定性校验后，由独立 Verifier 检查依据是否真正支持结论、是否存在推理跳跃、遗漏反证、相关性与因果性混淆以及结论范围扩大。
- Verifier 必须独立读取底层 Fact、Inference 和 Evidence，不能只依据 Reasoning Agent 提供的摘要作出判断。
- Verifier 可以返回反证缺失或需要更多 Evidence 的审核结果，由 Knowledge Engine 和 Application Services 决定是否继续调查；Verifier 不直接调用 Connector 或越过应用层采集数据。
- Verifier 输出至少区分 PASS、REVISE、REJECT 和 NEED_MORE_EVIDENCE，并提供结构化问题，不直接静默修改候选结论。
- Verifier 与 Reasoning Agent 使用独立执行上下文；高风险策略可以进一步要求不同模型、不同提示策略或确定性领域验证器。
- 独立审核不能绝对保证语义正确，但可以在写入权限和来源链硬约束之上，降低模型自我引用、确认偏差和错误推理进入正式知识的风险。

### AD-038：知识审核是 Candidate 生成正式知识的内部准入步骤

- Knowledge Admission Review 不作为 Fact 或 Inference 生成完成后的重复业务流程，也不单独建立一套知识审核生命周期。
- 在审核通过之前，生成结果只能称为 Fact Candidate 或 Inference Candidate；通过后才取得正式 Fact 或 Inference 身份。
- Fact Resolver 在 Fact 构建流程中编排确定性规则校验和独立 Verifier，审核通过后写入正式 Fact。
- Inference Validator 在 Inference 构建流程中编排确定性规则校验和独立 Verifier，审核通过后写入正式 Inference。
- Verifier 的独立性表示审核执行上下文和判断职责独立于生成 Agent，不表示必须在正式知识生成后增加一个重复模块。
- 面向用户的 Answer Review Agent 与上述知识生成门禁相互独立；它审核 Answer Candidate 是否适合当前问题，但不能替代 Fact Resolver 或 Inference Validator。

### AD-039：Agent Investigation 只编排调查，不拥有知识生成逻辑

- Agent Investigation 负责理解目标、制定调查计划、选择和调用 Connector、维护 Hypothesis，并按需触发知识构建能力。
- Entity、Fact 和 Inference 的生成归属于统一的 Knowledge Construction，不归属于 Agent WorkingMemory，也不能由 Agent 直接写入。
- 后台采集、后续 Initialization 和按需 Agent 调查是 Knowledge Construction 的不同触发入口，必须复用同一套 Entity Resolution、Fact Construction 和 Inference Construction 流程。
- Agent Investigation 可以调用知识构建工具并跟踪结果，但只能持有 Candidate ID、知识引用和任务状态，不能维护另一份 Entity、Fact 或 Inference 内容。
- Hypothesis、搜索候选、调查计划和临时跨源关联保存在 InvestigationRun 或 WorkingMemory；正式 Candidate 由 Knowledge Construction 的候选区管理。
- 触发来源不能改变验证标准；无论知识由后台任务还是按需调查发现，都必须经过相同的上下文、来源链和独立审核门禁。

> **后续细化：** AD-092 和 AD-095 允许 Agent Investigation 在一次运行中携带不可变的 Candidate Bundle，作为向 Knowledge Engine 提交的临时边界对象。这不表示 Agent 拥有 Candidate 的稳定身份、准入、持久化或发布权；模型输出先由平台严格反序列化和重建，正式状态仍只能由 Knowledge Engine 产生。

### AD-040：Entity 身份解析采用风险分级准入

- Entity 的准入重点不是审核其全部内容，而是验证 Entity Mention 应创建新身份、链接已有身份还是保持未解析的身份决定。
- 数据源提供稳定唯一标识且上下文兼容时，Entity Resolver 可以通过确定性规则自动创建或复用技术 Entity。
- 同名、跨系统、跨版本演化继承、技术对象到业务概念映射等模糊情况形成 EntityResolutionProposal，并经过独立校验。
- EntityResolutionProposal 的结果至少包括 LINK_EXISTING、CREATE_NEW 和 KEEP_UNRESOLVED。
- 无法确认身份时保留 Entity Mention，不为追求图结构完整而强制合并。
- 确定性身份解析不要求逐条调用模型；独立 Verifier 主要用于错误合并影响较大的高风险决定。
- Entity 的名称、属性、状态和关系不内嵌为未经验证的身份内容，仍通过具有 Evidence 和 KnowledgeContext 的 Fact 表达。

### AD-041：非 DDD 和逻辑混乱系统采用 As-Is 技术事实优先建模

- DDD、清晰领域边界和规范代码结构不是知识构建前提，架构必须支持职责交叉、逻辑分散和命名混乱的遗留系统。
- 首先根据源系统稳定标识和 Evidence 构建 As-Is Technical Model，如实表达系统、服务、模块、API、表、Topic 和实际流程。
- Business Semantic Model 位于技术模型之上，通过可追溯语义关系关联业务概念、能力、规则、流程与技术实现，不覆盖或改写技术现状。
- 技术实现与业务语义必须支持多对多：一个模块可以实现多个业务能力，一个业务能力也可以分散在多个系统和对象中。
- 未被权威来源直接确认的业务归属和技术到业务映射以 Inference 表达，允许不完整、重叠、冲突和不确定状态。
- 系统不得为了产生整洁模型而强制归并领域边界或套用 DDD；无法确认时保留未知和多个候选解释。
- AI 提出的 DDD 重构或目标领域模型属于 Target Model 或架构建议，不能反向覆盖 As-Is Model，也不能作为当前系统 Fact。

### AD-042：Entity 的语义类型与身份来源相互正交

- 不使用“技术身份必然来自 Fact、业务身份必然来自 Inference”的绝对划分，避免把 Entity 的语义类别与认知来源混为一体。
- Entity 的语义类型至少区分 TECHNICAL 和 BUSINESS；身份来源至少区分 SOURCE_ANCHORED 和 INFERRED，两个维度可以自由组合。
- 数据表、代码符号和数据源明确标识的服务等技术 Entity 通常直接由 Evidence 中的稳定标识解析；它们先于引用其身份的 Fact，不由 Fact 反向生成。
- 根据多个技术事实归纳出的逻辑子系统即使属于 TECHNICAL，其身份来源仍为 INFERRED。
- 由权威业务目录或正式业务模型明确声明的 Business Entity 可以具有 SOURCE_ANCHORED 来源。
- 在缺少权威业务定义时，Business Entity 默认由已有 Entity 和 Fact 经过语义归纳、验证后形成，身份来源为 INFERRED。
- Business Entity 的存在不自动证明其与任何技术实现的关系；REPRESENTS、IMPLEMENTS、PERSISTS 等映射仍须独立形成 Fact 或 Inference。
- 默认原则是技术 Entity 优先由 Evidence 锚定、Business Entity 通常由 Fact 归纳，但架构允许反例并保留完整来源。

### AD-043：推断型 Entity 通过候选包审核后原子创建

- 仅对无法从数据源直接锚定、必须由多个 Fact 语义归纳的 Entity 使用 SemanticEntityProposal，例如推断出的 Business Entity 或逻辑子系统。
- SemanticEntityProposal 位于候选区，不是正式 Entity；它使用仅在候选包内有效的 proposalRef、语义类型、定义和 supportingFactIds。
- 审核前的 Inference Candidate 可以在同一候选包内引用 proposalRef，不预先创建可被正式知识查询的占位 Entity。
- Entity Resolver 编排确定性检查和独立 Verifier，验证提议的身份是否被输入 Fact 支持、是否与已有 Entity 重复以及上下文是否合理。
- 审核通过后，系统以一次原子提交分配稳定 EntityId、创建正式 Entity、保存 EntityDerivation Inference，并将候选包内引用替换为正式 ID。
- 审核失败时不创建正式 Entity，提议及问题仅保留在 InvestigationRun 或候选审计记录中。
- Source-anchored Entity 继续使用 Evidence、Entity Mention、Entity Resolution 主流程，不要求经过 SemanticEntityProposal。
- Entity 保持身份容器定位；“为什么认为推断型 Entity 存在”由可追溯、可重新验证的 EntityDerivation Inference 表达。

### AD-044：Evaluation & Learning Engine 构成受控自测和持续改进外循环

**状态：架构预留，MVP 不实现，详细方案后续单独讨论。**

- 整体架构在知识主干之外增加 Evaluation & Learning Engine，持续评测 Data Source、知识构建、语义视图、Agent、Verifier 和最终答案的端到端能力。
- 外循环至少包括 Question Generation、正式系统作答、Independent Verification、Failure Diagnosis、Improvement Proposal、隔离回放、回归评测和 Promotion Gate。
- 失败诊断必须区分知识缺失或错误、Evidence 获取不足、Entity 或 Fact 或 Inference 构建错误、上下文选择错误、Agent 规划和工具选择错误以及基础模型能力不足。
- 知识问题通过 Agent Investigation 触发正常 Knowledge Construction 流程修正，不能绕过 Entity Resolver、Fact Resolver 和 Inference Validator。
- 系统能力问题可以形成 Connector、Processor、Prompt、模型路由、验证策略、Schema 或评测集的改进提议；只有积累经过验证的高质量样本后才考虑微调或训练。
- 系统不得把自身生成的答案直接作为训练真值，也不得依据单次 Reviewer 通过结果自动训练或修改正式策略。
- 所有能力变更必须在隔离环境进行新旧版本回放和回归对比，通过 Promotion Gate 后才能进入正式运行环境。
- Evaluation & Learning Engine 改进的是整个软件世界模型系统，不等同于单一大模型自训练，也不与描述软件自身变化的 History 或 Evolution 语义混淆。
- 禁止为解决某个特定系统、固定问题或已知评测集而把局部模式固化进全局 Prompt、模型权重或核心知识 Schema，避免系统能力过拟合和不可迁移。
- MVP 只保留该模块在总体架构中的位置、输入输出边界和未来接入点，不建设自动提问、自训练、能力晋升及完整评测基础设施。

### AD-045：正式知识采用单一逻辑权威来源和可重建存储投影

- Entity、Fact、Inference、KnowledgeContext 及其来源和依赖关系在逻辑上只能有一个权威记录，不能由关系库、图库和向量库分别维护相互竞争的真值。
- Graph、Vector 和 Search 等存储只承载面向查询的 Storage Projection，不成为正式知识来源。
- Agent 和应用可以读取投影进行检索和遍历，但不能绕过 Knowledge Construction 直接向投影写入正式知识。
- 正式知识通过 Fact Resolver、Inference Validator 和 Entity Resolver 写入权威存储，再由投影构建器异步或同步更新各查询投影。
- 投影必须保存回到权威 Entity、Fact、Inference 的稳定引用；投影内容本身不能作为独立 Evidence。
- 投影丢失、Schema 变化、Embedding 模型升级或图结构调整时，可以从权威知识重新构建，不影响知识身份和来源链。
- 单一逻辑权威不预设必须使用一种物理数据库，也不要求所有类型共享一张通用记录表；物理部署方式在保持唯一权威所有者的前提下可以演化。

### AD-046：MVP 采用模块化单体并按需实现 Projection

- MVP 优先采用单一应用和部署单元，以模块化单体组织 Artifact、Evidence、Entity Resolution、Fact、Inference 和 Projection 等职责。
- 不建立通用 KnowledgeRecord 大表；不同领域对象保持独立 Schema、表和 Repository，通过稳定 ID 与模块接口协作。
- MVP 可以共用一个关系数据库以获得简单事务和较低运维复杂度；大体积 Artifact Payload 根据保留策略放入对象存储、缓存或继续保留在源系统。
- 当前不引入为未来拆分服务的分布式事务、消息总线和多服务部署；未来可以沿既有模块边界拆分而不改变领域身份与接口。
- Projection Module 的准确职责是把正式 Entity、Fact 和 Inference 转换为 Graph、Vector、Search 或其他查询优化结构，不生成新知识。
- Storage Projection 解决知识的物理查询效率，Semantic View 解决面向目标组织和展示哪些知识，两者不能混为一层。
- 当关系数据库已经满足 MVP 查询时，不实现独立 Projection Module；只预留最小 ProjectionBuilder 接口，并在首次引入外部图、向量或搜索索引时实现。
- Projection 可以丢弃并重建，其内容和自然语言摘要不能成为正式 Evidence 或权威知识来源。

### AD-047：MVP 不建设独立 Evolution Engine

- Knowledge Evolution 表示外部软件世界发生变化后，识别受影响知识并触发增量重建的持续同步能力。
- Knowledge Construction 负责如何从当前输入构建知识；Knowledge Evolution 负责变化发生后何时以及针对什么范围重新运行同一套知识构建流程。
- Evolution 不建立另一套 Entity、Fact 或 Inference 生成逻辑，也不能绕过 Entity Resolver、Fact Resolver 和 Inference Validator 直接修改知识。
- MVP 由统一的 Knowledge Construction Orchestrator 处理手动或定时触发的增量更新，不单独建设 Evolution Engine。
- 当前架构只预留变化触发和影响范围输入的扩展边界，不提前实现持续监听、复杂影响传播和自动重建基础设施。
- 当持续同步、多级依赖传播、自动重建和 Snapshot 激活等需求真实出现后，再从统一编排器中拆分独立 Evolution Orchestrator。
- Evolution Orchestrator 描述和更新外部软件世界知识，不与 History Semantic View 或用于改进系统自身能力的 Evaluation & Learning Engine 混淆。

### AD-048：L0 架构将 Knowledge Construction 与 Knowledge Core 合并为 Knowledge Engine

- Knowledge Construction 表示构建动作，Knowledge Core 表示其操作和维护的领域模型；MVP 不将二者设计成两个顶层模块、服务或独立接口边界。
- L0 架构使用统一 Knowledge Engine，负责 Evidence 提取、Entity 解析、Fact 构建与验证、Inference 构建与验证以及正式知识管理。
- Entity、Fact、Inference 和 KnowledgeContext 是 Knowledge Engine 内部的核心领域模型，不作为单独运行模块出现在 L0 架构图中。
- 核心领域对象不依赖具体 Connector、模型或 Prompt，Semantic View 只读取正式知识等依赖原则继续作为 Knowledge Engine 内部架构约束。
- MVP 在同一模块和部署中完成知识构建与管理，避免引入重复接口、对象转换和事务边界。
- 只有出现独立扩缩容、不同团队所有权、多个构建引擎共享知识服务等真实需求后，才评估沿内部边界拆分。
- 简化后的主干为 Data Access、Artifact Processing、Knowledge Engine、Semantic Views、Agent 或 Query 或 Applications。

### AD-049：L0 合并 Source Integration，L1 保持 Connector 与 Artifact Processing 分层

- L0 架构将 Data Access 和 Artifact Processing 归入统一 Source Integration，作为把外部异构数据转换为可被 Knowledge Engine 使用的信息载体的顶层能力。
- L0 合并只表示模块和部署归属，不允许把两类逻辑揉成同一层实现。
- Source Integration 内部在 L1 保持 Connector Layer 与 Artifact Processing Layer 清晰分离。
- Connector Layer 负责连接、查询和准确获取外部数据，输出 Source Artifact，不承担开放式语义理解。
- Artifact Processing Layer 消费 Source Artifact，负责解析、结构化和生成 Derived Artifact，不直接管理外部连接与凭证。
- 两层通过 Artifact 协议衔接并保持单向依赖；MVP 可以同进程、同部署，未来仍可沿内部边界扩展或拆分。
- 当前 L0 主干简化为 Source Integration、Knowledge Engine、Semantic Views、Agent 或 Query 或 Applications。

### AD-050：单体应用提供 Web 与 CLI 双入口，Semantic Model 保持内部逻辑分层

- 系统的部署形态确定为单体应用，同时提供 Web 和 CLI 两种入口，不按当前内部职责划分多个服务。
- Web 与 CLI 属于同一 Interface Layer，共享相同的应用能力，不分别实现知识构建、语义建模或推理逻辑。
- Semantic Views 在单体内部形成 Semantic Model Layer，负责组织 Structure、Behavior、Business 和 History 等可扩展视图。
- Semantic Model Layer 与 Knowledge Engine 保持代码职责和单向依赖边界，但不存在独立服务、网络或部署边界。
- Semantic Model Layer 不拥有另一份权威知识，不生成 Fact 或 Inference，也不因逻辑分层而引入独立存储。
- 当前架构中的“模块”和“层”默认表示单体内部的逻辑组件，除非后续明确出现独立部署需求。

### AD-051：Application Layer 同时支持 Fixed Workflow 与 Agentic Workflow

- 原文 Reasoning Platform 不作为所有请求必须经过的系统总控制层；Task Execution Agent 是单体 Application Layer 内部的一种智能执行能力。
- Web 与 CLI 的请求先进入共享 Application Layer，再根据用例性质进入 Fixed Workflow 或 Agentic Workflow。
- Fixed Workflow 表示执行步骤在开始前已经由应用逻辑明确、不需要 Agent 动态规划的用例；该名称不表示内部算法或模型输出必然确定。
- Agentic Workflow 表示执行步骤需要根据目标和中间结果动态规划的开放式调查或推理用例，由 Task Execution Agent 调用受控应用能力完成。
- Fixed Workflow 内部仍可以调用模型；是否使用模型不是区分两类 Workflow 的依据。
- Task Execution Agent 负责目标理解、动态规划、Application Use Case 选择和 Answer Candidate 组织，只通过 Application Services 间接使用系统能力。
- Task Execution Agent 不拥有 Connector、Artifact Processing、知识构建、语义视图定义或正式知识存储逻辑，也不能直接操作底层存储。
- “确定性”一词仅用于描述输入输出和算法行为可复现的工具或操作，不再用于指代执行路径固定的应用用例。

### AD-052：统一 Model Gateway，Task Execution Agent 与模型访问职责分离

- 不再使用容易混淆的 Agent Runtime 和 Model Runtime 作为两个平级层次的名称。
- Task Execution Agent 位于 Application Layer，负责开放式目标理解、动态规划和应用能力编排，解决“下一步做什么”。
- Model Gateway 位于 Shared Infrastructure，负责统一访问不同模型和模型提供方，解决“如何调用模型”。
- Artifact Processor、Knowledge Engine、Agent Orchestrator、Task Execution Agent 和各类审核组件等需要模型能力的组件统一依赖 Model Gateway，不直接绑定具体模型厂商或调用方式。
- Model Gateway 不定义业务任务、不制定调查计划、不生成知识准入规则，也不作出审核决定。
- Source Connector 不调用模型；需要语义解析的内容由 Artifact Processing 通过 Model Gateway 处理。
- MVP 在单体内部实现最小 Model Gateway，不建设独立模型平台或独立部署服务。

### AD-053：Knowledge Verifier 与 Answer Review Agent 是两个独立组件

- 不建立统一 Verification Layer，也不使用一个通用 Verifier 同时承担知识准入和答案审核职责。
- Knowledge Verifier 位于 Knowledge Engine 的知识构建链路，审核 Entity、Fact 和 Inference Candidate，决定其能否成为长期共享的正式知识。
- Knowledge Verifier 不负责判断答案是否回应当前问题，也不处理面向用户的表达质量。
- Answer Review Agent 位于 Application Layer，独立审核当前 Answer Candidate 是否回应问题、忠实引用已有知识以及是否存在过度推断。
- Answer Review Agent 可以使用模型自主规划审核步骤，但不决定知识准入，不能创建、修改或删除正式 Entity、Fact 和 Inference。
- 两个组件可以共同依赖 Model Gateway 和受控知识查询能力，但不共享审核职责、策略和生命周期。
- 二者在代码职责和执行上下文上独立，当前仍运行在同一个单体应用中，不形成独立部署服务。
- 原文统一 Knowledge Governance 层从 MVP 主数据流中移除；企业级 Governance 只保留为后续扩展能力。

### AD-054：Use Case 与调用方式分离，Web Chat 和 CLI 复用同一应用能力

- Management、Knowledge Update 和 Knowledge Use 表示系统功能类别；Fixed Workflow 和 Agentic Workflow 表示用例的调用与编排方式；Application Services 和 Agent 组件表示静态组件，三者不能画成同一层级。
- Application Use Case 不固有地属于 Fixed 或 Agentic；同一 Use Case 可以由不同入口以不同方式调用。
- CLI 以结构化命令和参数直接调用 Application Use Case，形成 Fixed Workflow。
- Web 当前定位为 Chat 入口，自然语言请求先进入 Agent Orchestrator，由其调度 Task Execution Agent；具体 Agent 再调用一个或多个 Application Use Case，形成 Agentic Workflow。
- Scheduler 等系统触发器可以直接调用相应 Application Use Case，不要求经过 Agent。
- Task Execution Agent 负责意图理解、参数补全和动态编排，不重复实现 Data Source 管理、知识更新或知识查询逻辑。
- Web Chat、CLI 和未来其他入口共享 Application Use Case 和 Core Capabilities，但不要求共享完全相同的调用流程。
- 架构文档分别提供静态组件视图和动态流程视图；组件表示职责与依赖，流程表示一次调用如何经过组件。

### AD-055：功能分类与调用流程采用正交视图

- Application Use Cases 按系统功能划分为 Management、Knowledge Update 和 Knowledge Use 三类，不使用 Fixed 或 Agentic 对功能本身分类。
- Management 包含 Data Source、KnowledgeScope、构建任务和系统配置等管理用例；Knowledge Update 负责触发知识构建或更新；Knowledge Use 负责查询、调查和使用知识。
- 动态调用流程按 Direct Invocation Flow 和 Conversational Agent Flow 描述，与三类功能保持正交。
- Direct Invocation Flow 由 CLI、Scheduler 等结构化入口直接调用 Application Use Case，再访问相应 Core Capability。
- Conversational Agent Flow 由 Web Chat 进入 Agent Orchestrator，再由其依次调度 Task Execution Agent 和 Answer Review Agent；具体任务由 Agent 执行，Agent Orchestrator 只控制流程。
- 任一功能类别均可由不同调用流程使用；例如 Data Source 配置既可由 CLI 直接执行，也可由 Web Chat 经 Task Execution Agent 执行。
- Knowledge Update 或 Knowledge Use 不与 Agent 组件平级展示：前者是功能类别，后者是 Application Layer 中的静态组件。

### AD-056：MVP 为四种 Semantic Model 的最小可用纵向闭环

- MVP 以完整用户旅程和端到端可用结果定义，不以完成所有规划模块或所有数据源接入作为完成标准。
- MVP 支持一个 KnowledgeScope、本地工程及其关联 Git，输入覆盖源代码、配置、测试、仓库内文档和 Commit History。
- MVP 跑通 Management、Knowledge Update 和 Knowledge Use 三类 Application Use Case，以及 CLI Direct Invocation 和 Web Conversational Agent 两种调用流程。
- 对空 KnowledgeScope 的首次构建复用 Knowledge Update，不在 MVP 中引入独立 Initialization 模块；代码变化后支持手动再次触发更新。
- MVP 同时提供 Structure、Behavior、Business 和 History 四种 Semantic Model，但每种只实现一条最小可用纵向能力，不追求完整覆盖。
- Structure 最小能力是识别系统组成、代码实体和静态依赖；Behavior 是从代码、测试和配置还原主要执行流程。
- Business 最小能力是结合仓库内文档与技术事实识别主要业务概念及其技术映射，证据不足时保持为 Inference。
- History 最小能力是基于 Git 历史展示主要代码变化和演化关系，不要求维护完整历史 Snapshot。
- 四种视图共同复用 Evidence、Entity、Fact、Inference 和 KnowledgeContext，并可以由 Web Chat 查询和用于生成可审核答案。
- MVP 不包含生产 Log、Trace、Metric、跨系统 Business Model、独立 Evolution Engine、Evaluation & Learning Engine、企业级 Governance 和完整历史 Snapshot。

### AD-057：Application Layer 的 L0 组件图待职责确认后重绘

- 先前仅表达 Application Services 与单一 Agent Orchestrator 的 L0 图不再作为当前架构依据。
- Management、Knowledge Update 和 Knowledge Use 仍属于功能分类，不与静态组件画成同一层级。
- Application Services 仍是入口无关的用例协调器；CLI 和 Scheduler 可以直接调用它们。
- Web Chat 流程已经明确包含 Task Execution Agent、Answer Review Agent 以及二者之上的 Agent Orchestrator，不能再简化为 Web Chat 直接调用单一 Agent。
- Agent Orchestrator 的职责已经确认，但在其他模块职责全部确认前仍不固定新的 Application Layer 组件图。

### AD-058：Application Services 是入口无关的用例协调器集合

- Application Services 不是单个大型服务，而是一组与 Web、CLI、Scheduler 等具体入口无关的应用用例协调器。
- Application Services 对外提供 Management、Knowledge Update 和 Knowledge Use 三类 Application Use Cases，并协调一次用例涉及的内部能力。
- CLI、Scheduler 和 Task Execution Agent 复用同一套 Application Services，不分别实现数据源管理、知识更新或知识使用逻辑。
- Application Services 将入口请求转化为对 Source Integration、Knowledge Engine 和 Semantic Model 的用例级协调，并返回结构化执行结果。
- Application Services 不理解自然语言、不动态制定 Agent 计划、不实现外部数据访问和 Artifact 解析，也不生成或审核 Entity、Fact、Inference。
- Application Services 不定义 Semantic Model，不直接绑定或调用具体模型提供方。
- Application Services 可以依赖 Source Integration、Knowledge Engine 和 Semantic Model；这些核心能力不反向依赖 Application Services。

### AD-059：Task Execution Agent 只通过 Application Services 动态执行任务

- Task Execution Agent 位于 Application Layer，将 Agent Orchestrator 交付的 Agent Task 转换为一组动态 Application Use Case 调用。
- Task Execution Agent 负责理解具体任务及其上下文、动态制定执行计划、选择 Application Use Case、根据中间结果调整步骤以及形成 Answer Candidate。
- MVP 中 Task Execution Agent 服务于 Web Chat 的对话任务；CLI 和 Scheduler 不经过该 Agent。
- Task Execution Agent 依赖 Application Services 取得可调用的应用能力，并依赖 Model Gateway 使用模型能力。
- Task Execution Agent 不实现任何 Application Use Case，不直接调用 Source Integration、Knowledge Engine 或 Semantic Model，也不直接访问底层存储。
- Task Execution Agent 不创建或写入正式 Entity、Fact 和 Inference，不决定知识准入，也不负责最终答案审核和发布。
- Task Execution Agent 不封装具体模型厂商调用；所有模型访问统一经过 Model Gateway。

### AD-060：Source Integration 以 Artifact 为职责边界

- Source Integration 负责连接外部 Data Source，并将外部信息转换为具有明确来源和 KnowledgeContext 的 Artifact。
- Source Integration 内部在 L1 保持 Connector Layer 与 Artifact Processing Layer 分离：前者访问和读取外部数据，后者解析和加工已获取的 Artifact。
- Source Integration 负责 Data Source 连接与访问能力、源系统搜索和读取、Source Artifact 生成、Derived Artifact 加工以及来源和加工链保留。
- Source Integration 为不同 Data Source 和 Artifact 类型提供扩展边界，但不把具体 Connector 和 Processor 实现暴露为上层业务逻辑。
- Source Integration 的职责终点是 Artifact；Evidence、Entity、Fact 和 Inference 不在该模块中生成或确认。
- Source Integration 不执行跨数据源业务语义关联、不编排 Application Use Case，也不直接回答用户问题。
- Application Services 是 Source Integration 的上层调用者；Task Execution Agent 不直接调用该模块。
- Connector Layer 不使用模型；Artifact Processing Layer 需要语义解析时通过 Model Gateway 使用模型能力。
- Source Integration 不直接依赖或触发 Knowledge Engine；Knowledge Update Use Case 由 Application Services 协调 Artifact 获取和后续知识构建。

> **后续细化：** AD-109 和 AD-110 中的 Source Operation Result 只向 Application Services 报告来源调用、覆盖、失败、截断、预算与 Artifact 引用。Artifact 仍是 Source Integration 唯一面向 Knowledge Engine 的信息载体；操作结果不形成 Evidence 或正式知识，因此不改变本条职责边界。

### AD-061：Knowledge Engine 以 Artifact 输入和正式知识输出为职责边界

- Knowledge Engine 负责将 Artifact 转化为经过验证、可追溯且带有 KnowledgeContext 的正式知识，并管理这些知识。
- Knowledge Engine 从 Source Artifact 或 Derived Artifact 中提取 Evidence，执行 Entity 身份解析，构建 Fact Candidate 和 Inference Candidate，并调用 Knowledge Verifier 完成准入。
- Knowledge Engine 管理正式 Entity、Fact、Inference 及其来源和依赖关系，并处理已有知识的更新和重新验证。
- Knowledge Engine 向 Semantic Model 提供正式知识查询能力；Semantic Model 不反向参与知识生成。
- Application Services 调用 Knowledge Engine 触发知识构建、更新和基础知识操作；Task Execution Agent 和外部入口不直接调用 Knowledge Engine。
- Knowledge Engine 依赖 Knowledge Verifier，并在需要模型提取、身份解析和推理时依赖 Model Gateway。
- Knowledge Engine 不连接外部 Data Source、不解析或加工 Artifact、不编排 Application Use Case，也不定义语义视图和生成最终用户答案。
- Knowledge Engine 不依赖 Source Integration、Semantic Model、Task Execution Agent、Web、CLI 或 Scheduler。
- 权威知识存储属于 Knowledge Engine 的内部实现，具体存储设计不在当前架构讨论中展开。

### AD-062：Semantic Model 可以使用模型组织视图，但不能创造正式知识

- Semantic Model 是从正式知识生成 Semantic View 的组件；Semantic View 是面向目标和 KnowledgeContext 的结构化视图结果。
- Semantic Model 定义 Structure、Behavior、Business 和 History 四种内置视图，并支持后续注册新的视图类型。
- Semantic Model 读取 Knowledge Engine 中的正式 Entity、Fact 和 Inference，根据目标 Scope、Environment、Version 和 Time 组织结果。
- Application Services 调用 Semantic Model；Semantic Model 不依赖具体入口和 Task Execution Agent。
- Semantic Model 可以按需依赖 Model Gateway，用模型完成已有知识的选择、分组、排序、摘要和向视图 Schema 的组织。
- 模型组织出的每项视图内容必须引用底层正式 Entity、Fact 或 Inference；模型生成的摘要不是 Fact 或 Evidence。
- Semantic Model 不能在视图中创建新的正式关系或结论；发现新的语义关系时只能报告知识缺口或候选需求，由 Knowledge Engine 走正式构建和验证流程。
- Semantic Model 不读取 Artifact、不提取 Evidence、不修改正式知识，也不制定 Agent 调查计划或审核最终答案。

### AD-063：Model Gateway 统一模型访问但不拥有领域判断

- Model Gateway 是单体应用内部统一访问模型能力的 Shared Infrastructure，用于隔离内部组件与具体模型、厂商和调用方式。
- Model Gateway 接收内部组件提出的模型能力请求，根据所需能力选择模型、适配 Model Provider、执行调用并返回结构化结果。
- Model Gateway 记录实际模型和版本，使模型参与的 Artifact 加工、知识生成、语义组织、Agent 编排和审核结果可追溯。
- Artifact Processing、Knowledge Engine、Semantic Model、Agent Orchestrator、Task Execution Agent、Knowledge Verifier 和 Answer Review Agent 可以依赖 Model Gateway。
- 调用方负责定义任务语义和期望结果；Model Gateway 只负责模型选择与调用，不理解 Application Use Case 或制定 Agent 计划。
- Model Gateway 不定义 Artifact、Entity、Fact、Inference 或 Semantic View，不判断模型输出正确性，也不决定知识准入和答案发布。
- 模型调用结果不能因为经过 Model Gateway 就自动成为 Evidence、Fact、Inference 或最终答案。
- Model Gateway 不负责训练或自动优化模型；Evaluation & Learning 的后续能力与模型调用基础设施保持分离。

### AD-064：Answer Candidate 是 Task Execution Agent 与 Answer Review Agent 之间的临时输出

- Answer Candidate 不是模块、正式知识、Evidence、Semantic View 或 Final Response，而是 Conversational Agent 流程中的临时输出契约。
- Task Execution Agent 在调用一个或多个 Application Services 后，基于结构化用例结果、Semantic View 和知识引用，通过 Model Gateway 组织 Answer Candidate。
- Answer Candidate 表达待返回回答、底层 Entity 或 Fact 或 Inference 引用、适用 KnowledgeContext、可审核依据说明以及不确定性和限制。
- Answer Candidate 必须经过 Answer Review Agent 后才能成为返回 Web Chat 的 Final Response。
- Answer Candidate 不能进入 Knowledge Engine，也不能作为后续 Fact 或 Inference 的 Evidence。
- CLI 直接执行 Fixed Workflow 时默认返回结构化 Use Case Result，不生成 Answer Candidate；未来请求自然语言回答时才复用同一审核流程。
- 当前不增加独立 Answer Generator 顶层模块；答案组织是 Task Execution Agent 的职责，Answer Candidate 是其明确输出。

### AD-065：Interface Layer 只负责入口适配

- Interface Layer 将外部交互转换为内部组件请求，并把内部结果转换为对应入口的响应，不承载 Application Use Case 或领域逻辑。
- Web Chat Adapter 接收自然语言对话请求并交给 Agent Orchestrator，最终只返回经过审核的 Final Response。
- CLI Adapter 接收结构化命令和参数，直接调用对应 Application Services 并返回结构化 Use Case Result；MVP 中不经过 Agent。
- Scheduler Adapter 根据预先配置的计划产生系统触发请求并调用指定 Application Services，主要用于定时 Knowledge Update。
- Interface Layer 不访问 Data Source、不处理 Artifact、不构建知识、不生成 Semantic View、不执行 Agent 规划、不调用模型，也不承担知识和答案审核。
- Web Chat Adapter 依赖 Agent Orchestrator；CLI Adapter 和 Scheduler Adapter 依赖 Application Services。
- Application Services、Agent 组件和内部核心组件不反向依赖具体 Web、CLI 或 Scheduler 入口。

### AD-066：Knowledge Verifier 是 Knowledge Engine 内部独立的知识准入组件

- Knowledge Verifier 独立于 Entity、Fact 和 Inference Candidate 生成过程，负责判断 Candidate 能否成为正式知识。
- Knowledge Verifier 审核 Entity 身份解析提议、Fact Candidate 的 Evidence 支持、Inference Candidate 的正式知识依据和推导链，并检查 KnowledgeContext 兼容性。
- Knowledge Verifier 识别依据不足、明显冲突和结论范围扩大，向 Knowledge Engine 返回准入决定和结构化审核问题。
- Knowledge Verifier 不生成或修改 Candidate，不写入正式知识，不生成 Semantic View，也不审核用户答案。
- Knowledge Engine 是 Knowledge Verifier 的唯一调用者；Knowledge Verifier 依赖 Knowledge Engine 提供的 Candidate、Evidence 和正式知识读取能力，并可通过 Model Gateway 使用模型审核能力。
- Knowledge Verifier 不直接调用 Source Integration 或编排调查；需要更多 Evidence 时返回审核结果，由 Knowledge Engine 和 Application Services 决定后续动作。
- Knowledge Verifier 的独立性表示职责、审核上下文和判断过程与 Candidate 生成器分离；它仍是 Knowledge Engine 内部组件，不是独立服务或 L0 顶层模块。

### AD-067：两个 Agent 采用暂定的职责型命名

- 原先集中在单一 Agent Orchestrator 中的职责被拆分：领域任务理解、规划执行和 Answer Candidate 生成由 Task Execution Agent 承担；Agent Orchestrator 名称保留给上层意图理解、Agent 路由和流程编排组件。
- 原 Response Verifier 或 Answer Verifier 暂定更名为 Answer Review Agent，强调其需要模型和 Agentic Review 能力对 Answer Candidate 进行独立审核，而不是执行简单规则校验。
- Task Execution Agent 与 Answer Review Agent 职责独立：前者生成 Answer Candidate，后者形成 Answer Review Result，二者不直接调用或控制对方。
- 二者之间的调用顺序、重试和最终返回由上层 Agent Orchestrator 控制。
- 以上命名属于架构阶段的暂定名称；MVP 验证如发现职责或理解偏差，可以调整名称，但不能在无明确决策时混用旧称。

### AD-068：Agent Orchestrator 只编排 Agent，不执行具体任务

- Agent Orchestrator 位于 Application Layer，是 Task Execution Agent、Answer Review Agent 以及未来其他专职 Agent 之上的流程编排组件。
- Agent Orchestrator 接收 Web Chat 的对话请求，理解用户自然语言和对话上下文，识别任务意图并选择对应 Agent；同时根据任务目标和中间结果动态决定 Agent 的调用顺序、结果传递、重试、终止和最终返回。
- Agent Orchestrator 负责理解“用户要做什么、交给谁”；具体 Agent 负责理解所分配任务“如何完成”，并执行领域任务。
- 领域任务规划、Application Use Case 调用、Answer Candidate 生成和答案审核均由相应的具体 Agent 执行，不属于 Agent Orchestrator 的职责。
- Agent Orchestrator 不直接调用 Application Services、Source Integration、Knowledge Engine 或 Semantic Model，不直接访问存储，也不创建或审核正式知识。
- Agent Orchestrator 可以依赖 Model Gateway 完成自然语言理解和 Agent 路由，是具有模型能力的编排组件，但不是领域任务执行 Agent。
- 对下游流程，Agent Orchestrator 依据具体 Agent 返回的结构化结果控制状态，不自行解释或重新执行领域任务。
- 该名称复用后具有新的严格定义：Agent Orchestrator 只保留顶层意图理解、Agent 路由和流程控制；领域任务理解、动态执行规划和答案生成由 Task Execution Agent 承担。

### AD-069：Answer Review 属于 Knowledge Use，但用途是答案审核

- 从功能分类看，Answer Review 属于 Knowledge Use：它读取并使用已有正式知识、Evidence、Semantic View 和 KnowledgeContext，不构建或修改知识。
- 从静态组件看，Answer Review Agent 是执行该 Knowledge Use 场景的 Agent，不能与 Knowledge Use 功能类别画成同一层级。
- Answer Review Agent 可以通过 Application Services 调用只读的 Knowledge Use 能力，独立核对 Answer Candidate 的引用、上下文适用性、遗漏、冲突和过度推断。
- Answer Review Agent 使用知识的目的不是再次生成答案，而是形成 Answer Review Result，供 Agent Orchestrator 决定放行、退回修正或终止。
- Answer Review Agent 不调用 Management 或 Knowledge Update，不直接访问 Source Integration、Knowledge Engine、Semantic Model 或底层存储，也不修改正式知识。
- 当审核发现现有知识不足时，Answer Review Agent 只报告知识缺口或补充调查需求；是否发起后续任务由 Agent Orchestrator 决定，并交给相应的具体 Agent 执行。

> **后续细化：** AD-112 将 Answer Review 扩展为所有 Web Chat 响应的 Application Layer 放行门禁。只有软件知识响应的审核属于 Knowledge Use；平台操作响应只读 Application Services 产生的不可变 Application Use Case Result，不取得 Management 或 Knowledge Update 权限，也不虚构 Requirement / Assessment。

### AD-070：MVP 使用通用 Task Execution Agent，并预留专职 Agent 扩展边界

- Task Execution Agent 在架构上表示任务执行角色，不被限定为永远只有一个具体 Agent 实现。
- MVP 只实现一个通用 Task Execution Agent，由它处理 Web Chat 中涉及 Management、Knowledge Update 和 Knowledge Use 的不同任务，避免为尚未验证的任务类型提前拆分多个 Agent。
- Agent Orchestrator 依赖稳定的 Agent 角色边界和结构化执行结果，不与通用 Task Execution Agent 的具体实现绑定，也不假设系统永远只有该 Agent。
- 未来可以根据真实任务差异增加或拆分专职 Agent，并由 Agent Orchestrator 统一控制调用顺序、结果传递和生命周期；Web Chat、Application Services 和 Core Capabilities 的职责边界不因此改变。
- 用户请求的顶层意图理解和 Agent 路由由 Agent Orchestrator 完成；分配后的领域任务理解、执行计划和中间调整由具体 Agent 完成。
- MVP 只保留上述逻辑扩展边界，不提前建设动态 Agent 注册平台、复杂协作协议或多 Agent 调度算法；具体拆分和路由方式由后续验证结果决定。

### AD-071：Agent Orchestrator 对上理解自然语言，对下传递完整 Agent Task

- Agent Orchestrator 是 Web Chat 与具体 Agent 之间的语义编排边界，不能只转发未经理解的文本。
- Agent Orchestrator 结合用户原始请求和相关对话上下文识别目标、约束和任务类型，并将其传递给匹配的具体 Agent。
- 为避免自然语言解释造成信息损失，Agent Task 同时保留用户原始表达、必要对话上下文和 Agent Orchestrator 形成的结构化任务理解；结构化理解不能替代原始输入。
- Agent Orchestrator 对任务传递的完整性负责，但不对领域执行结论负责；具体 Agent 必须基于完整 Agent Task 自主制定执行计划。
- Agent Orchestrator 可以通过 Model Gateway 使用模型完成意图理解和路由，但不能因此直接调用 Application Services、执行 Knowledge Use 或生成 Answer Candidate。

### AD-072：Agent Orchestrator 只按 Agent 职责拆分任务

- 当一个用户请求涉及多个不同 Agent 职责时，Agent Orchestrator 可以将其拆分为一个或多个 Agent Task，并控制这些任务之间的调用关系。
- Agent Orchestrator 的拆分边界止于“哪部分任务交给哪个 Agent”，不继续拆解具体 Agent 内部需要执行的领域步骤。
- 每个具体 Agent 根据收到的完整 Agent Task 自主制定执行计划、选择 Application Use Case，并根据中间结果调整执行过程。
- MVP 只提供通用 Task Execution Agent 和 Answer Review Agent 两种最小 Agent 角色，但二者的调用次数、反馈和重新执行由 Agent Orchestrator 根据当前任务动态决定；Answer Candidate 返回前必须经过审核是固定门禁，而不是固定编排流程。
- MVP 不提前建设通用任务图、复杂并行调度或多 Agent 协商平台；动态编排由 Agent Orchestrator 基于当前可用 Agent 能力完成。
- 未来增加专职 Agent 时，可以扩展 Agent Orchestrator 的职责级任务拆分和调用关系，而不改变具体 Agent 与 Application Services 的既有边界。

### AD-073：Web Chat 的 Agent 编排由用户任务动态决定

- Conversational Agent Flow 不是预先写死的 Agent 调用链；Agent Orchestrator 根据用户请求、对话上下文、可用 Agent 能力和中间执行结果动态形成当前任务的编排。
- 动态编排可以决定选择哪些 Agent、调用次序、是否再次调用以及何时结束，但具体 Agent 内部的领域执行计划仍由该 Agent 自己负责。
- 固定的是架构约束而不是执行路径：Agent Orchestrator 不执行领域任务，具体 Agent 不越过 Application Services 访问核心模块，最终 Answer Candidate 必须经过 Answer Review Agent。
- MVP 即使只有一个通用 Task Execution Agent，也不能把 Web Chat 实现为固定流水线；Agent Orchestrator 仍需根据任务和审核反馈动态决定调用过程。
- 动态编排不等于当前必须建设通用工作流引擎、动态 Agent 注册中心或复杂多 Agent 协商系统；这些实现能力只在后续真实需求出现时引入。

### AD-074：Agent Capability Contract 是动态编排的稳定扩展边界

- 每个可被编排的具体 Agent 对外提供 Agent Capability Contract，用于表达该 Agent 的职责范围、能够接受的任务以及能够产生的结果。
- Agent Orchestrator 依据用户任务、对话上下文和可用的 Agent Capability Contract 动态选择具体 Agent，不在编排逻辑中写死 Agent 名称或固定调用链。
- Agent Capability Contract 是架构级能力契约，不包含具体 Agent 的领域执行步骤；如何完成任务仍由具体 Agent 自主规划。
- MVP 在单体应用内部静态提供通用 Task Execution Agent 和 Answer Review Agent 的能力定义，不建设动态注册中心、独立 Agent 平台或远程发现机制。
- 未来增加或拆分专职 Agent 时，只需提供新的 Agent Capability Contract 并接入 Agent Orchestrator，Application Services 和 Core Capabilities 的既有职责边界保持稳定。

### AD-075：软件世界模型与构建它的平台采用独立定义

- 软件世界模型是对一个或多个软件系统在特定上下文中的结构、行为、业务语义和演化过程的统一语义表示。
- 软件世界模型由 Entity、Fact 和 Inference 构成，并能够回溯到相应 Evidence。
- Software World Model 平台是构建和使用该模型的 AI Native 系统，从软件的可观察信息中获取依据，负责知识的构建、验证、更新和使用。
- 软件世界模型是平台构建和维护的核心语义表示；平台是围绕该表示提供完整知识生命周期能力的软件系统，二者不能混为同一概念。
- Semantic View、Agent、Web Chat 和 CLI 是平台组织或使用模型的方式，不属于软件世界模型本体定义。

### AD-076：构建意图与执行策略分离

- 每次 Knowledge Update 都必须具有显式构建意图，用于表达目标 KnowledgeScope、必需来源范围、期望知识范围和最低发布结果。
- 构建意图既可以覆盖完整 KnowledgeScope，也可以限定到某类知识或来源；“有构建目标”不等同于“必须窄范围按需构建”。
- 全量、目标驱动和增量是实现同一 Knowledge Update 语义的不同执行策略，不能隐藏在 Connector、方法名或具体解析器中。
- 单个代表性工程中的全量构建和回放存储观察，只能证明需要度量构建与保留成本，不能单独决定 MVP 的默认更新策略。
- MVP 可以优先使用简单、完整的全量构建；只有代表性工程的规模、更新频率、成本或时延超过验收阈值时，才引入目标驱动或增量优化。

> **后续细化：** AD-096 不否定完整 Scope 的全量重建，但要求目标限定更新不能用局部构建结果替换当前完整知识。相同 Revision 下的局部任务更新采用基于当前 Snapshot 的 enrichment；完整 Scope 更新或 Revision 变化仍可采用 replacement。该区分首先解决正式状态正确性，不以性能优化为前提。

### AD-077：Artifact 使用中立边界契约

- Artifact 是 Source Integration 与 Knowledge Engine 之间的数据边界，但不造成两个核心模块之间的实现依赖。
- Source Integration 负责产生 Artifact，并拥有其来源身份、获取状态、Lineage 和生命周期；Application Services 只负责编排和传递；Knowledge Engine 只消费 Artifact 契约。
- Source Integration 与 Knowledge Engine 在代码上共同依赖中立 Artifact 契约，不能导入对方的 Connector、Processor、Builder、Repository 或内部存储类型。
- 中立契约是代码依赖边界，不是新的运行模块、顶层架构层或数据所有者。

### AD-078：稳定身份不能承载顺序语义

- Entity ID 和 Fact ID 用于稳定引用同一身份或同一客观陈述，不表达声明顺序、执行顺序、时间顺序或重要性。
- Behavior 步骤、调用先后和 History 时序必须由来源位置、显式顺序属性或 `PRECEDES` 等正式关系表达。
- 查询、Semantic View 和 Agent 不能通过稳定 ID、数据库插入顺序或偶然遍历顺序恢复业务时序。

### AD-079：来源上下文与 Snapshot 发布上下文分离

- Artifact 与 Evidence 必须保留各自 Data Source 的 Revision、Environment 和 Time，不因进入某次 Snapshot 而被改写。
- Fact 和 Inference 记录结论成立或适用所需的 KnowledgeContext；Snapshot 记录平台一次发布的正式知识集合，三者相关但不强制相等。
- 一个 Snapshot 可以组合不同来源版本和环境的知识，但组合关系必须显式保留并通过验证；不确定的对应关系仍以 Inference 表达。
- Knowledge Verifier 校验 Evidence 时以其 Artifact 来源上下文为准，不能要求 Evidence Revision 等于当前 Snapshot 的代码 Revision。

### AD-080：Answer Candidate 使用结构化 Answer Claim 作为审核单元

- Answer Claim 表达候选答案准备向当前用户陈述的一项判断，用于把自然语言答案拆成可以独立核对的审核单元。
- Answer Claim 不是 Evidence、Fact、Inference 或新的正式知识；它可以引用一个或多个正式知识，也可以明确表示不确定性、知识缺口或应用操作结果。
- Task Execution Agent 必须同时输出自然语言答案、重要 Answer Claim 及其知识引用，不能只给审核器一段无法稳定对照的自由文本。
- Answer Review Agent 分别检查 Claim 是否被引用知识支持、答案文本是否忠实覆盖 Claim，以及整份答案是否回应用户问题。
- Answer 文本与结构化 Claim 不一致时不得发布，即使 Claim 引用本身合法。

### AD-081：Snapshot 发布门禁与 Semantic View 产品验收分离

- Snapshot 发布门禁属于 Knowledge Engine，只判断必需来源完成、正式知识准入、引用与推理一致性，以及本次请求声明的最低正式知识结果。
- Structure、Behavior、Business 和 History 的固定问题集属于 MVP 产品验收，由 Application Services 在 Snapshot 发布后调用 Semantic View Engine 执行。
- Knowledge Engine 不定义或判断 Semantic View 的产品质量；Semantic View Engine 也不能因此获得 Snapshot 发布、回滚或正式知识修改权。
- 完整 Scope 的首次 Knowledge Update 必须具有足以阻止空模型或严重残缺模型被报告为成功的最低正式知识条件，但这不等同于把所有产品验收规则写入发布事务。
- Semantic View 验收失败时，上层记录知识缺口并可发起新的 Knowledge Update，已经发布且内部一致的 Snapshot 不被视图组件直接改写。

### AD-082：软件世界模型不以替代单次代码 Agent 调查为价值目标

- 对单个 Git 工程的一次性问答，直接代码 Agent 通常具有更低启动成本，软件世界模型不预设自身更快或更准确。
- 平台的差异化目标是把一次调查中具有复用价值的认知转化为可共享、可验证、带 KnowledgeContext 且可受控更新的长期知识。
- 项目是否值得建设，取决于该知识在重复任务、多用户、多来源和版本变化中的复用收益，是否显著高于知识构建、验证、存储和更新成本。
- 一般架构能够跑通只证明可行性，不证明产品价值；进入 MVP 详细设计前必须增加与直接代码 Agent 的对照验证。
- 如果对照验证无法形成明显复用收益，应缩小或停止软件世界模型范围，不能以既有投入作为继续建设的理由。

### AD-083：正式知识按复用价值逐步结晶

- 软件世界模型不是对所有源内容和模型结论的预计算副本，不以使用前完整理解整个软件世界为目标。
- 低成本、稳定、广泛复用的 Structure 基础知识可以初始化或全量构建；高成本 Behavior、Business、History 归纳及跨来源关联优先由真实任务触发。
- 任务调查结果只有在具有复用价值、能够回溯 Evidence 并通过知识准入时，才进入长期正式知识；一次性回答、搜索线索和 Agent Working State 不进入模型。
- 该原则决定“构建哪些知识”，但不预设底层必须使用全量、目标驱动或增量执行策略；执行策略仍由 AD-076 约束。
- 随模型能力增强，可以减少高成本语义能力的预编码和预物化，但 Artifact、Evidence、Context、准入、Snapshot 和审计边界继续保留。

### AD-084：价值验证比较执行路径而非模型品牌

- 对照基线是能够直接读取工程和使用正常开发工具的“直接仓库调查 Agent”，不绑定特定产品或模型品牌。
- 优先使用同一个基础模型分别运行直接调查路径和 Software World Model 路径，避免把模型能力差异误认为平台架构收益。
- 两条路径使用相同问题、工程 Revision、来源边界、工具权限和结果评价标准；差异只在于是否构建或复用正式软件世界模型。
- 实验可以由同一执行者完成，但输入、过程和结果评分必须可回放，不能依靠执行者对自身方案的主观判断。

### AD-085：直接仓库调查能力是平台能力下限

- 在相同基础模型、Data Source 和工具权限下，通用 Agent 直接读取来源能够完成的任务，是 Software World Model 平台的功能能力下限。
- 平台允许因为 Evidence 构建、独立审核和知识准入而更慢，但不能因为固定 Semantic View、已物化知识范围或 Schema 缺失而降低任务完成率、正确性和关键证据覆盖。
- 正式知识是生产 Knowledge Use 和答案的唯一知识依据；现有知识不足或不能证明答案完整时，Task Execution Agent 必须通过 Application Services 发起 Knowledge Update，新信息完成知识准入并发布后才能用于回答。
- Semantic View 返回 `READY` 只说明其查询契约完成，不代表当前用户问题已经完整回答；答案完整性由 Task Execution Agent 和 Answer Review 针对当前任务判断。
- 模型、Prompt、工具、知识构建策略或 Semantic View 变化后，必须在固定任务集上与直接仓库 Agent 重新进行能力非回归验证。
- 对所有随机任务逐题作绝对正确性保证并不现实，但产品验收必须将完成率、正确性和关键证据覆盖不低于直接路径设为 P0 门禁。

### AD-086：生产回答采用单一世界模型路径

- 生产环境不同时运行 Software World Model 回答和直接仓库 Agent 回答，不使用后者补充、纠正或兜底前者。
- 运行时双路径会掩盖知识构建、表达、查询和完整性判断的缺陷，无法证明软件世界模型自身产生价值，因此不进入产品架构。
- 当正式知识不足时，系统可以暂停当前回答并执行任务驱动的 Knowledge Update；Source Integration 取得的新 Artifact 必须经过 Evidence、Candidate、Knowledge Verifier 和 Snapshot 发布主干，之后才能由 Knowledge Use 使用。
- Task Execution Agent 不能把 Knowledge Update 中的临时来源片段或未经准入的 Candidate 直接写入 Answer Candidate。
- 直接仓库 Agent 仅在系统外部的隔离测试中使用，作为黄金答案辅助、能力非回归基线和缺陷发现手段；其输出不传给被测世界模型路径。
- 如果世界模型在固定任务集上无法达到直接 Agent 的完成率、正确性和关键证据覆盖，应修正或缩小系统能力范围，而不是增加运行时直接调查兜底。

> **后续细化：** AD-112 将“答案的唯一知识依据”限定为软件世界知识性 Claim。Management、Knowledge Update 等平台操作性 Claim 使用 Application Services 产生的不可变 Application Use Case Result，不要求把操作结果伪装为软件世界正式知识；这不构成直接来源回答的第二路径。

### AD-087：模型主导开放式认知，系统拥有可信控制

- 自然语言目标理解、Knowledge Requirement 形成、调查规划、跨来源关联、反例搜索、Candidate 提议、动态 Semantic View 和答案审核属于模型主导的开放式认知能力。
- 确定性解析器、索引、规则和固定查询可以作为可靠工具、候选生成器或经过验证的优化 Strategy，但不能成为开放式任务的能力上限。
- Data Source 权限与副作用、Artifact Lineage、Evidence 定位与哈希、KnowledgeContext、稳定身份约束、知识准入流程、Snapshot 原子发布、审计和回放由平台负责，模型不能绕过。
- AI Native 的目标不是最大化模型调用次数，而是让模型充分承担其更擅长且持续增强的认知工作，同时用系统机制保持准确性、可信性和正式状态一致性。
- 验证实现中的固定语义路径、固定构建目标和模型替身不得直接冻结为产品的认知实现。

### AD-088：Capability Contract 支持执行 Strategy 演进

- 每项可演进能力通过稳定 Capability Contract 定义输入、输出、工具权限、知识影响、失败语义和验收指标。
- 同一能力可以具有 Deterministic、Model-Primary 和 Hybrid Strategy；Strategy 由能力所属业务模块管理，Model Gateway 只负责模型访问。
- 新模型、Prompt、工具或 Strategy 必须通过固定样例回放、直接 Agent 非回归对照和必要的影子验证后才能晋升为默认实现；发生退化时可以回退。
- 模型能力增强后，可以减少原有语义硬编码和预物化；已经更准确、低成本且可复现的确定性工具不因模型可用而被强制替换。
- 独立 Evaluation & Learning Engine 可以后置，但 MVP 必须具备最小的能力级版本记录、回放、比较和准入机制，否则无法安全利用模型演进。

### AD-089：任务知识完整性采用 Knowledge Requirement 与 Sufficiency Assessment 表达

- Knowledge Requirement 由 Task Execution Agent 基于用户原始请求和 KnowledgeContext 通过模型形成，表达当前任务必须回答的 Knowledge Need 及其充分条件。
- Requirement 形成必须忠实于用户原始请求：Need 既不能遗漏、弱化或改写用户明确要求，也不能把未请求的模块清单、全部异常分支、回滚补偿或实现深度扩张为强制条件；每项充分条件必须必要且与原问题相称。
- Requirement 在任务内不可变，属于 Application Layer 的 Agent Working State，不是正式知识、Semantic View、Build Intent 或产品验收规则。
- Requirement 不绑定单个 Snapshot；Knowledge Sufficiency Assessment 绑定一次明确的已发布 Snapshot，并逐项以正式知识引用判断每个 Need 为满足或 Gap。
- 整体完成状态只能由“全部 Need 均满足”机械推导；语义上的满足判断由独立于调查和答案撰写的模型能力完成，平台负责引用存在性、上下文一致性和逐项完整映射。
- Gap 触发 Knowledge Update 后，在新 Snapshot 上重新评估同一 Requirement，不能通过弱化 Requirement 获得完成。
- Answer Review Agent 必须反向检查 Requirement 是否完整覆盖用户问题，防止遗漏 Need 形成虚假的完整性。
- 平台能够机械保证 Requirement 冻结、Need 唯一性和逐项映射，但“没有遗漏也没有扩张”的语义忠实性仍须由独立模型能力或评测审核，不能以 Schema 校验冒充。

> **后续细化：** AD-107 将“Requirement 在任务内不可变”精确化为“任务边界不可扩张或弱化、每个 Requirement Revision 不可原地修改”。忠实性审核发现遗漏、重复或错误时，可以在同一任务边界内生成可追溯的新 Revision，不能因首版分解错误造成任务死锁。

### AD-090：通用正式知识调查采用固定读取上下文和模型编排

- MVP 提供打开正式知识上下文、搜索 Entity / Inference、读取一跳 Fact 邻域、批量解释 Fact / Inference 的正式命题、依赖和来源定位四类通用只读能力；它们是 Knowledge Use 应用能力，不是新的架构模块。正常答案调查面不读取 Evidence 原文。
- 工具负责上下文固定、参数校验、有界且可继续的机械查询、稳定引用和追溯；模型负责调查规划、工具组合、反例搜索、语义解释和知识充分性判断。
- 每轮调查只使用一个固定 Snapshot 上下文；Snapshot 更新后旧上下文失效，必须重新打开并重新评估。
- Knowledge Update 的来源调查上下文与生产答案上下文严格隔离，Artifact、未准入 Candidate 和未发布结果不能直接支持答案。
- 空查询和未声明覆盖只表示当前正式知识中没有匹配结果，不表示现实对象不存在；否定结论需要适用的正式知识或经过确认的完备覆盖边界。

> **后续细化：** AD-094 和 AD-097 将“固定读取上下文和模型编排”落实为阶段隔离的 Model Execution Context 与平台约束的有界 Tool Loop。Explain 在正常答案读取面只提供正式命题、依赖和来源定位，不向 Answer 上下文暴露 Evidence quote 或 Artifact payload；需要读取原文的知识构建或审核能力使用各自隔离的执行上下文。

### AD-091：Evidence 不能扩大正式命题的语义范围

- Evidence 证明它所支持的正式命题，不表示 Evidence 原文中的全部信息自动成为正式知识。
- Answer Claim 必须被所引用 Fact 或 Inference 的正式命题直接支持；仅在关联 Evidence quote 中出现参数、公式、分支或结果，不能弥补正式命题没有表达这些语义。
- 模型从 Evidence 中发现的新语义必须先形成 Fact 或 Inference Candidate，经过 Knowledge Verifier 并发布到新 Snapshot，之后才能支持生产答案。
- Knowledge Update、Knowledge Verifier 和 Answer Review 可以在各自隔离上下文中读取 Evidence 原文；答案生成默认只读取正式命题、正式引用和来源定位，不能借 Evidence quote 形成隐性源码回答路径。
- Fact 的三元组或检索投影不能被误认为知识表达上限；无论采用何种表示，正式命题本身必须足以表达并审核准备对用户陈述的语义范围。

> **后续细化：** AD-112 允许正式 Entity 及其 Snapshot 成员状态只支持身份存在和引用 Claim；属性、关系、行为与业务含义等实质陈述仍必须由 Fact 或 Inference 正式命题直接支持。本条禁止 Evidence 扩张命题的原则不变。

### AD-092：模型主导的任务驱动 Knowledge Update 是下一阶段 P0

- 当前正式知识不足时，从 Knowledge Requirement 的 Gap 派生独立 Build Intent；Build Intent 在新增来源调查前冻结，不得因看到结果而弱化 Requirement 或最低发布条件。
- 模型在隔离的 Investigation Run 中通过 Application Services 使用 Connector Tool、Artifact 与已有正式知识，提出带 Evidence、KnowledgeContext 和依赖的 Entity、Fact 与 Inference Candidate。
- Investigation Run 与 Candidate Bundle 属于临时执行状态，不是新的知识层或顶层模块；Knowledge Update 的唯一正式产物是经过准入并原子发布的新 Snapshot，以及拒绝项和仍存在的 Gap。
- Artifact 内容、调查对话、Hypothesis、未准入 Candidate 和答案式 Update 摘要不得进入 Answer Candidate 上下文。发布后必须使用新的模型调用和固定正式知识 Context，对原 Requirement 全量重评。
- Git 等 Connector 必须支持按任务发现和读取任意 Revision、父 Revision 与 Diff，不能由固定验证配置决定平台能够理解哪些 Commit。
- 最小验收是：关闭来源访问并清空调查上下文后，新 Snapshot 仍能让系统只依靠正式知识完成同一个 Requirement；否则该流程只是把直接源码回答包装成 Knowledge Update。

> **后续细化：** AD-109 和 AD-110 明确了当前所有权：模型先提出 Build Target Proposal 或 Candidate Proposal；Application Services 拥有 InvestigationRun 并协调来源调用，Knowledge Engine 拥有 Source Information Need 的语义判断、Candidate 构造与准入。模型和 Task Execution Agent 都不直接拥有 Candidate，也不绕过 Application Services 调用 Connector。

### AD-093：PV-HOLDOUT-001 未通过，继续冻结广泛 MVP 详细设计

- 首轮产品留出测试未达到直接来源调查的能力下限；完整评分和失败分类只在 [Product_Value_Validation_Log.md](../validation/product-value/Product_Value_Validation_Log.md) 维护。
- 失败性质是正式知识覆盖与任务完成度不足，不能以可追溯性、稳定身份或未来复用价值抵消。
- 保留通用正式知识调查能力，但禁止增加题目专用 View、Extractor 或运行时直接来源兜底来掩盖缺口。
- 已见问题只能用于诊断回归；纠偏后必须冻结新的未见任务集，以同模型和同来源边界重新执行能力非回归。
- 新的 P0 门禁通过前，暂停广泛 MVP 详细设计；若模型主导 Knowledge Update 仍不能达到直接调查能力下限，应缩小或停止项目范围，而不是继续堆叠架构层次。

### AD-094：模型执行上下文按认知阶段隔离

- 平台将模型参与的任务过程显式划分为 `ROUTING`、`REQUIREMENT`、`KNOWLEDGE_USE`、`INVESTIGATION`、`ASSESSMENT`、`ANSWER` 和 `REVIEW` 等执行阶段；每次模型调用必须绑定一个具有独立身份的 Model Execution Context。
- 所有在 Model Gateway 注册的 Capability 只能在其声明的阶段上下文中调用；缺失上下文、阶段不匹配或上下文已经关闭时必须在 Provider 调用前失败。未注册 Capability 不能进入生产 Agent 路径，需先补充阶段契约。
- Requirement 形成、正式知识调查、来源调查与 Candidate 提议、充分性评估、答案生成和答案审核分别使用独立上下文。Knowledge Update 发布后，旧的 Knowledge Use Context 和模型上下文同时失效，必须从空 Tool Trace 重新调查并评估同一 Requirement。
- Answer 上下文只接收 Knowledge Requirement、最新 Assessment、正式命题、正式引用和必要的来源定位；Artifact 内容、Evidence quote、Investigation Run、Hypothesis、Candidate Bundle 和答案式更新摘要不得进入该上下文。
- Model Gateway 负责 Capability 与阶段匹配、上下文生命周期和调用审计；使用有状态 Model Provider 时，Provider 适配器还必须保证不同 context 不共享隐藏会话记忆，不能只记录一个逻辑标签。
- Model Execution Context 是认知隔离和审计边界，不是权限凭证或企业安全沙箱；数据源访问权限仍由 Application Services 和 Source Integration 控制。

### AD-095：模型 Candidate 是不可信语义提议，正式对象由平台重建

- 模型可以在 Investigation Context 中提出 Entity、Evidence locator、Fact 和 Inference 的语义内容，但模型响应本身不是 Candidate Bundle，更不是正式知识。
- 平台对模型输出执行严格 Schema 反序列化：拒绝未知字段、重复局部 Key、越界引用、Scope 不一致、非法 Evidence locator、Gap Need 遗漏或重叠，以及不受支持的依赖关系。
- 模型只声明候选内局部引用、语义字段和来源定位；Evidence quote、content hash、Revision、Scope、稳定 Entity / Fact / Inference ID 和 model-call provenance 必须根据冻结的 Build Intent 与 SourceCollection 由平台生成或核对，不能信任模型自报值。
- Fact 与 Inference 的分类取决于正式命题的认知性质和支持关系，而不取决于 Candidate 由代码还是模型提出。直接观察型 Fact 必须具有直接 Evidence；对观察作出的归纳、目的解释或语义抽象必须形成具有显式支持链的 Inference。
- 对直接 Fact 使用的保守准入 Strategy 只能作为可替换的验证策略，不能外推为所有数据源和 Fact 类型的通用语义算法；后续 Strategy 仍须通过能力评测晋升。
- Agent 可以在 Investigation Run 内携带平台构造的不可变 Candidate Bundle 作为提交对象，但不拥有稳定身份分配、语义准入、持久化和 Snapshot 发布权。Knowledge Engine 仍是 Candidate 成为正式知识的唯一入口。

### AD-096：同 Revision 的目标限定更新采用 Snapshot Enrichment 与 Base CAS

- 任务驱动的目标限定更新通常只采集当前 Requirement Gap 所需的局部 Artifact 和 Candidate；该局部结果不能作为完整 replacement 覆盖当前 Snapshot，否则会丢失与本次任务无关但仍有效的正式知识。
- 当目标 KnowledgeScope 和 Revision 与当前 Snapshot 相同，Knowledge Update 必须绑定 Assessment 所依据的 Base Snapshot，继承其全部正式 Entity、Evidence、Fact、Inference、依赖和 Artifact 引用，再合并本次已经准入的 delta，形成新的完整 Snapshot。
- Enrichment 只允许合并稳定 ID 下语义兼容的对象，并可以为同一 Fact 增加新的 Evidence；同一稳定 ID 出现不兼容语义时必须拒绝发布，不能静默覆盖 Base 内容。
- 发布采用 Base Snapshot Compare-And-Set：只有 Base 在提交时仍为该 Scope 的 CURRENT Snapshot，才能原子激活新 Snapshot；如果其他更新已经替换 Base，本次调查以 `STALE_BASE_SNAPSHOT` 失败，不能覆盖并发结果。
- 未发布构建、Candidate 被拒绝、Base 过期或合并冲突时，原 CURRENT Snapshot 保持可查询。成功后旧读取 token 失效，调用方重新打开正式知识上下文。
- 完整 Scope 构建或 Revision 变化可以继续采用 replacement；enrichment 不等于已经实现通用增量影响分析、删除传播、历史 Snapshot 查询或独立 Evolution Engine。

> **后续细化：** AD-113 将稳定决策推广到 replacement 与 enrichment：任何更新都不得用陈旧或不兼容的发布基线覆盖 CURRENT。Compare-And-Set 和 `STALE_BASE_SNAPSHOT` 是当前可选实现 Strategy，不是一般架构固定的锁机制或错误码；也可以通过串行化、提交时重验证或等价版本冲突检测实现。

### AD-097：正式知识调查采用模型规划、平台约束的有界 Tool Loop

- Task Execution Agent 不再根据 `use_case` 直接选择固定 Semantic View 作为开放式问题的唯一调查路径，而是让模型围绕不可变 Knowledge Requirement 动态组合通用正式知识工具。
- MVP 的最小 Tool Loop 包括：搜索 Entity / Inference、从 Entity 读取一跳 Fact Neighborhood、批量解释 Fact / Inference，以及显式停止。工具返回正式命题、稳定引用、依赖、来源定位和固定上下文，不向答案调查暴露 Evidence quote 或 Artifact payload。
- Scope、Snapshot Token 和 KnowledgeContext 由 Task Execution Agent 根据已打开的正式知识上下文注入每次 Application Service 调用，不能由模型参数选择或覆盖；每个工具结果必须返回并通过相同上下文校验。
- 模型负责下一步工具、查询条件、分页和何时停止；平台负责严格 Action Schema、参数上限、总步数预算、重复动作检测、结果类型校验和 stale-context 终止。空结果形成 Gap，不自动生成否定性 Claim。
- Snapshot 更新后必须销毁旧 Tool Trace，在新的 `KNOWLEDGE_USE` 模型上下文中从零执行同一 Requirement；更新前后发现的正式命题不能混入同一 Assessment。
- 机制回放只证明 Tool Loop 的边界、上下文和终止机制可运行，不证明模型已经具备充分的调查规划、反例搜索和错误恢复能力；具体证据见 [Architecture_Validation_Log.md](../validation/architecture/Architecture_Validation_Log.md)。

### AD-098：纠偏机制验证通过但产品 P0 判定不变

- 任务完整性、阶段隔离、动态来源获取、Candidate 准入、Snapshot enrichment 和正式知识调查等纠偏机制已经形成可回放正反例，说明架构闭环可以成立。
- 机制通过不等于模型认知质量通过，也不能把不同替代 Strategy 的独立成功合并表述为复杂知识生成已经完成。
- 产品 P0 判定保持未通过；机制修正不能替代新的未见产品留出测试。完整实验依据见 [Architecture_Validation_Log.md](../validation/architecture/Architecture_Validation_Log.md) 与 [Product_Value_Validation_Log.md](../validation/product-value/Product_Value_Validation_Log.md)。
- 达到直接调查能力下限前继续暂停广泛 MVP 详细设计，生产路径仍禁止直接来源调查兜底。

### AD-099：Snapshot Knowledge Schema 版本参与读取与合并门禁

- Snapshot 必须记录正式知识 Schema 版本；Knowledge Use 只能打开读取方明确支持的版本，不能把旧表存在或字段默认值误认为当前知识契约。
- 相同 Revision 的 enrichment 只能继承兼容 Schema 的 Base Snapshot；旧 Schema 内容不能未经重验证混入新 Schema Snapshot。
- Schema 升级通过完整 replacement 或显式迁移、重验证和原子发布完成。失败时旧 CURRENT Snapshot 保持不变，但不兼容读取必须明确返回重建或迁移要求。
- Schema 版本描述正式 Entity、Fact、Inference、Evidence 及其不变量，不等同于数据库 DDL 版本、模型版本或 Provider 输出 Schema。

### AD-100：Provider 结构化输出与平台 Capability Contract 分离

- Model Provider 只负责传输模型调用并尽可能约束其支持的可移植 JSON 形状；Provider 不支持或被降级移除的长度、数量、唯一性、跨字段关系、引用、Scope、Revision 和业务前置条件仍由能力所属模块完整校验。
- Provider 返回“符合输出 Schema”不代表 Capability 成功。平台必须对每个模型响应执行完整契约解析、上下文绑定和失败关闭处理，将可预期错误转换为稳定的能力失败，不能让原始解析异常逃逸或发布 Snapshot。
- 模型只能访问当前 Capability 显式授予的输入和工具；该边界必须在执行前和执行中机械保证，提示约束和事后事件检查只能作为纵深审计。
- 当前把 no-tools 作为前置条件是为了保证被测 Agent 不能绕过 Source Integration 和正式知识路径，不代表企业级安全、租户隔离或合规能力被提前纳入功能 P0。

### AD-101：开放式 Source Investigation 采用能力目录和有界 Tool Loop

- Application Services 向 Investigation 暴露由 Source Integration 与 Knowledge Engine 实际注册能力组合形成、带版本的能力目录；模型只能规划目录中存在的发现、搜索、按范围读取、Revision 比较、Candidate 提议和校验反馈能力，不能在 Prompt 中发明 Builder 内部目标。
- 复杂任务的默认路径是有界、渐进的 Source Investigation Tool Loop：先发现和搜索，再按预算读取最小来源，提出 Candidate，接收结构化校验结果，然后修正、补充来源或停止。
- 一次性装入来源并单次生成 Candidate 只可作为已通过评测的窄任务 Strategy，不能成为开放式问题的通用架构；读取和模型输入必须受预算约束，预算耗尽必须显式返回而不得静默截断。
- 模型可见内容必须保留可复核的来源身份、上下文和定位；调查切片与工具结果属于 Investigation Working State，不因此自动生成新的 Artifact 或 Evidence。
- 空选择不能隐式扩大为全量读取；“全部”必须由 Application 授权的显式、有界选择表达。

### AD-102：Build Target 由平台规范化并绑定冻结目标

- 模型可以根据 Gap 和能力目录提出来源范围及语义构建目标，但模型输出只是 Build Target Proposal；Application Services 必须结合冻结 Knowledge Requirement、DataSource 的 Canonical Source Target、Source Integration 解析出的 Canonical Operation Target / Resolution Receipt 和当前能力目录重建最终 Build Intent。
- 平台派生不可删除的最低目标与结果门禁。模型可以在授权预算内补充调查目标，不能用空目标集合、通配符、短前缀或无关同类型知识关闭或替代当前 Need 的最低目标。
- 任务驱动更新的目标覆盖必须绑定 `(Requirement Revision / Gap / Need, canonical target, knowledge kind/type)`；首次、手动、定时或 Schema 更新则绑定自身 Build Objective，不伪造 Need。发布门禁不能只检查 Snapshot 中“存在某种 Inference type”；Commit、Revision 和方法身份必须经过 Connector 或语言工具规范化后精确匹配。
- 验证实现中的目标选择表示属于可替换 Strategy，不是稳定的公开 Target Contract；正式契约必须区分规范身份与人类可读描述，并处理歧义和范围。

> **后续细化：** AD-109 将本条验证期的“最低结果门禁”统一为 Publication Acceptance Criteria，并把 Build Objective、可选 Requirement Binding、Data Source 或上游 Snapshot Binding、版本化 Capability Catalog 纳入 Build Intent 规范化。Need 的任务充分性只在新 Snapshot 发布后由 Knowledge Sufficiency Assessment 判断，不能与发布条件混为同一决定。

### AD-103：Candidate 契约错误允许在同一调查内有界修正

- 模型 Candidate 提议仍是不可信输入。局部 Key、Entity/Evidence 引用、locator、Need 分区或其他可安全说明的契约错误，可以在同一隔离 Investigation Context 中以结构化 `REJECTED` 结果回送模型。
- 每次修正必须提交完整 replacement proposal；平台从冻结 Build Intent 和 SourceCollection 重新构造正式身份、Evidence quote/hash、Revision、Scope 和 model-call provenance，不能在旧对象上原地补丁或信任模型自报字段。
- 修正次数和输入预算必须有界；重复错误或预算耗尽返回稳定失败状态，且不得创建 CURRENT Snapshot。Scope、Snapshot token、权限等平台控制字段的越权尝试继续立即失败。
- 有界修正只是 Source Investigation Tool Loop 的局部闭环，不等于动态补充来源、复杂 Candidate 语义准入或产品 P0 已完成；具体预算由能力评测和详细设计决定。

### AD-104：知识充分性按 Need 语义蕴含审核，答案不能自证

- Knowledge Build 的“required type 已存在”只是一致性下限，不能证明该知识满足某个用户 Need；Knowledge Sufficiency 必须逐项检查正式 Entity 身份状态或正式命题是否在各自权威范围内支持冻结的 question 与 sufficiency criterion。
- 同一条粗粒度 Inference 只有在确实覆盖每项充分条件时才能被多个 Need 引用；存在正确类型、合法 ID 或来源 Evidence 都不能替代语义覆盖审核。
- Answer Review 的权威依据必须由绑定 Snapshot 中的正式命题和 Claim 引用重新构造，不能直接复制 Answer Candidate 的文本让候选答案证明自己；模型结论与其发现的 unsupported claim 冲突时平台必须拒绝。
- Requirement 形成、Sufficiency Assessment、Answer drafting 与 Answer Review 使用隔离上下文；MVP 可以复用同一基础模型，但能力版本、输入和结论必须分别审计，产品正确性仍由外部留出集而非内部 `PASS` 决定。
- 每个 SATISFIED Need 必须形成绑定同一 Snapshot / Session 的可重建 Support Proof，双向覆盖 Criterion Obligation、正式引用、Context、Coverage、Conflict、未知项与反例检查；自然语言解释、同类型知识或 Answer Text 不能填补 Proof 缺口。

### AD-105：真实模型诊断不能替代产品门禁

- 真实模型诊断能够为 Requirement、来源调查、Candidate 准入、正式知识使用和答案审核提供架构正反例，但单实例成功或受控拒绝都不是未见产品门禁。
- 诊断暴露的契约错误应提升为通用架构约束，例如有界完整修正、空选择不扩大范围、审核依据不得由答案自证，以及模型能力不能旁路正式知识路径。
- 在调用边界不能保证模型只访问显式授予能力时，不得把该轨迹作为正式路径隔离的证明；事后审计不能替代执行边界。
- 产品 P0 仍未通过。下一次质量判断必须在新的未见任务集上进行外部评分；具体诊断和门禁结果分别见 [Architecture_Validation_Log.md](../validation/architecture/Architecture_Validation_Log.md) 与 [Product_Value_Validation_Log.md](../validation/product-value/Product_Value_Validation_Log.md)。

### AD-106：一般架构完成度与产品验收门禁分离

- 架构闭环门禁判断知识构建、准入、发布、使用和审核能否按稳定职责与依赖运行。
- 产品 P0 能力门禁判断平台在代表性未见任务上的正确性、完成率和关键证据覆盖是否不低于直接来源调查 Agent。
- MVP 价值门禁在 P0 通过后，进一步判断重复任务、多使用者、版本变化或多来源场景中的知识复用收益是否覆盖平台成本。
- 一般架构文档是否完成取决于职责、依赖、核心语义和演进边界是否自洽，不由某次产品分数决定；产品 P0 未通过则不得宣称 MVP 已验收。

### AD-107：任务边界固定，Knowledge Requirement 采用不可变 Revision

- 原始用户意图、任务范围、约束和目标 KnowledgeContext 构成任务内不可扩张或弱化的边界。
- 首次 Knowledge Requirement 是对该边界的知识需求分解，不具备绝对正确性；每个 Revision 自身不可原地修改。
- 独立忠实性审核发现 Need 遗漏、重复或错误时，可以在同一任务边界内产生带原因和前后关系的新 Revision，并从正式知识调查重新执行。
- 任务驱动的 Build Intent 和所有 Knowledge Sufficiency Assessment 必须绑定明确 Requirement Revision，不能通过静默改写 Requirement 获得完成；首次、手动和定时更新不伪造 Requirement Binding。

### AD-108：Derived Artifact 的 Lineage 不自动产生事实可信性

- Lineage 只证明 Derived Artifact 来自哪些上游 Artifact，不证明加工保持了来源语义。
- 只有可回放、可复核到来源观察且语义保持的 Derived Artifact，才能成为 Fact Evidence 的直接锚点。
- 模型摘要、解释和其他语义变换 Derived Artifact 只能辅助定位并提出 Fact 或 Inference Candidate，不作为 Fact 的直接 Evidence，也不能成为正式 Inference 的前提；正式 Inference 的前提仍只能是正式 Fact 和受控上游 Inference。
- 该约束不要求现在冻结 Artifact 分类字段；具体可信等级与验证 Strategy 在 Artifact 和 Evidence 详细设计中定义。

### AD-109：Build Target Proposal 与最终 Build Intent 分离

- 每次 Knowledge Update 都由显式 Build Objective 触发；首次、手动和定时更新使用 Scope Policy，任务驱动更新可以引用某个 Requirement Revision 的 Gap。
- 模型输出只是可选 Build Target Proposal。Application Services 结合 Build Objective、Requirement Binding（若存在）、Data Source 的 canonical source target 或显式上游 Snapshot Binding、版本化 Capability Catalog 和 Publication Acceptance Criteria，生成并冻结最终 Build Intent。
- Publication Acceptance Criteria 判断更新能否发布：Application Services 根据不可变 Investigation Result 判定来源执行与覆盖条件，Knowledge Engine 判定知识、Schema 与并发条件并拥有最终发布决定。发布后的 Knowledge Sufficiency Assessment 判断原 Requirement 是否满足。更新成功、任务解决和 MVP 验收是三个不同结论。
- 全量、目标限定和未来增量仍是执行 Strategy，不改变 Build Intent 的应用语义。

### AD-110：Knowledge Construction Strategy 拥有调查判断，Application Services 拥有调查循环

- Knowledge Engine 内部的 Knowledge Construction Strategy 根据 Build Intent 与已有 Artifact 判断还需要哪些来源信息，并返回结构化 Source Information Need。
- Application Services 拥有 InvestigationRun 生命周期，固定允许的 Capability、Scope 和预算，由 Source Integration 执行来源授权与调用，再把新增 Artifact 交回 Knowledge Engine；它只编排，不理解知识语义。
- Source Integration 只执行来源操作并产生 Source Operation Result 与其中引用的 Artifact，不判断知识充分性；Application Services 将操作状态累积为 Investigation Result，只把 Artifact 交给 Knowledge Engine，Knowledge Engine 不直接访问 Data Source。
- 模型或确定性生成器首先产生 Candidate Proposal；Knowledge Engine 完成契约解析、来源和上下文绑定后才构造成 Candidate Bundle。Candidate 是 Knowledge Engine 的准入前状态，不属于 Application Layer。
- Knowledge Verifier 的结构化补证问题返回 Knowledge Construction Strategy；后者可以形成新的 Source Information Need 并进入同一有界调查循环。循环结束时 Application Services 冻结 Investigation Result，供分区判定 Publication Acceptance Criteria。

### AD-111：Business Domain Scope 是跨系统 Business Entity 的身份边界

- KnowledgeScope 包含 System Scope、Shared Component Scope 和 Business Domain Scope 三类身份边界。
- 跨系统 Business Entity 归属于 Business Domain Scope，并通过跨 Scope Fact 或 Inference 关联多个独立 System Scope；Business Domain Scope 不吸收或复制系统技术知识。
- 系统本地 Entity 与共享组件 Entity 分别保留原 Scope，跨 Scope 关系不改变任何一方的稳定身份。
- 推断型新 Business Entity 与证明其身份的 Inference 作为同一依赖闭包原子准入；推导前提只能引用已有正式知识。
- 每个 Fact 和 Inference 也只有一个 owning KnowledgeScope；跨系统 Business Fact / Inference 归属于 Business Domain Scope，所引用的上游 System Snapshot 必须作为显式依赖保留。

### AD-112：知识性 Claim 与操作性 Claim 使用不同权威依据

- 正式 Entity 及其 Snapshot 成员状态只能支持身份存在和引用 Claim；属性、关系、行为与业务含义等软件知识性 Claim 只能由固定 Snapshot 中的正式 Fact 或 Inference 支持。
- 数据源配置、更新执行等操作性 Claim 只能由 Application Services 产生、可由审核方独立重读的不可变 Application Use Case Result 支持；不同权威范围不能互相替代。
- 知识任务中的 Gap 或无法建立结论 Claim 必须由当前 Requirement Revision、SnapshotReadSession、Knowledge Sufficiency Assessment 及其覆盖或限制状态共同支持，并由 Answer Review 重新核验；它只证明当前任务知识不足，不证明对象不存在。
- 实质知识答案要求当前 Requirement Revision 的全部 Need 满足；无法建立结论时可以形成只陈述 Gap 或失败边界的受控响应，但不得夹带不受支持的实质断言。
- 所有 Web Chat 响应仍经过 Answer Review；纯协议或传输错误作为 Interface Error Result 处理，不伪装成 Answer Candidate。

### AD-113：Snapshot 按 KnowledgeScope 发布，事务由 Knowledge Engine 独占

- KnowledgeScope 在首次成功发布前没有 CURRENT Snapshot；发布后恰有且只暴露一个 CURRENT。多 Scope 视图或任务绑定一组明确且与上游依赖兼容的 Snapshot，不能隐式读取各 Scope 不同时间的最新状态。
- Snapshot 选择正式 Entity、Fact 和 Inference 的可一致读取状态；Artifact 与 Evidence 是追溯依赖，不因此成为正式知识成员。
- Data Source 访问、Artifact 获取和模型调用不进入 Snapshot 发布事务。Application Services 不拥有跨模块大事务，Knowledge Engine 独占一致性检查和原子发布。
- 模块可以共用物理数据库，但只能通过逻辑所有者写入，不能跨模块直接操作 Repository 或表。
- replacement 与 enrichment 都必须在提交时检测发布基线冲突，具体并发控制机制不由一般架构固定。跨 Scope Snapshot 必须保留确切上游 Snapshot 依赖，上游 CURRENT 变化不能静默重绑定。

### AD-114：Semantic View 不能通过组织或摘要扩张正式知识

- Semantic View 是正式 Entity、Fact 和 Inference 的任务化组织结果，不是新的权威知识层。
- View 中的身份存在与引用项必须由正式 Entity 及其 Snapshot 成员状态支持；属性、关系、行为与业务含义等陈述必须被正式 Fact 或 Inference 命题直接蕴含。仅存在引用关系不足以证明摘要语义合法。
- 模型可以选择、组合、排序和摘要，但发现的新语义只能形成知识缺口或 Candidate 需求，不能直接进入 View 后被答案使用。

### AD-115：独立审核是职责与决策链独立，不是模型错误统计独立

- Knowledge Verifier 与 Answer Review Agent 的独立性由职责、权威输入重建、ModelExecutionContext、权限和决策链隔离保证。
- 生成方没有准入、发布或最终放行权；机械校验失败关闭，审核过程必须可追溯。
- 两类审核可以使用同一基础模型；不同模型或 Strategy 只是增强手段，不是架构硬要求，也不能据此宣称语义正确性已经得到保证。
- 审核质量仍须通过跨项目、跨任务和跨模型版本评测证明。

### AD-116：Inference 依赖深度属于可评测 Strategy

- 一般架构只要求 Inference 依赖有界、无环、保留完整依赖链，并能在上游知识失效时重新验证。
- 固定两级可以作为 MVP 的保守初始 Strategy，但不是 Software World Model 的永久语义上限，也不能阻止真实任务形成必要的更深推导。
- 最大深度、展平方式、成本预算和风险门禁在 Inference 详细设计中定义，并通过跨项目、跨任务和跨模型版本评测选择。
- Strategy 变化不能削弱正式前提引用、上下文兼容、独立审核和失效传播约束。

### AD-117：最小 Capability Evaluation 由应用级用例承接

- 提供 Capability 的业务模块拥有稳定 Contract、可选 Strategy、默认项、回退项和评测契约。
- MVP 不建设独立 Evaluation & Learning Engine；由 Management 类 Capability Evaluation 应用用例或调用同一用例的工程评测 Harness 执行固定回放，并产生不可变 Capability Evaluation Result。
- Application Layer 拥有 Evaluation Result 和 Strategy Activation Record；Management 只能激活已经通过门禁的 Strategy 版本，发生退化时按记录回退。执行时由 Application Service 解析激活记录并通过公开接口传入 Strategy 版本，能力模块不能反向读取 Application Layer 存储。
- Model Gateway 只保存模型调用与回放信息，不判断 Strategy 晋升或降级。评测与直接 Agent 基线比较；只有存在有效确定性基线时才要求同时比较确定性 Strategy。

> **后续细化：** AD-131 补充生产执行与候选评测的输出隔离，以及模型调用完成后对实际模型身份的最终资格校验。

### AD-118：Software World Model 定位为企业软件认知基础设施

- Software World Model 面向一个或多个软件系统及其业务范围，提供可共享、可追溯、可更新的统一语义认知，不以单仓一次性问答定义产品边界。
- 平台把代码、配置、数据、文档、版本历史和运行记录中的可观察信息，转化为带 KnowledgeContext 的正式 Entity、Fact 和 Inference，供人员、Agent 和自动化任务共同使用。
- 直接来源调查 Agent 是任务级认知能力和产品非回归基线，不是平台的价值定义，也不作为生产回答旁路。
- 平台的差异化价值在共享认知、跨来源与跨系统语义、证据与上下文、受控演化和跨任务复用场景中验证；MVP 的有限范围不能反向缩小一般系统定位。

### AD-119：概要架构、ADR、详细设计与验证证据分层维护

- 概要架构只定义稳定的系统定位、范围、领域概念、模块职责、依赖、关键流程和跨实现约束。
- Architecture Decision Log 记录决策原因、替代方案、历史术语和被后续决策细化或替代的结论。
- 详细设计记录应用执行对象、接口语义、状态、失败、并发和实现契约；验证文档记录项目、模型、参数、样例、分数和运行轨迹。
- 验证可以修正概要架构，但验证过程、具体实现和讨论记录不直接进入概要架构正文。

### AD-120：概要架构采用阶段无关的总体设计视角

- 概要架构只描述在不同交付阶段都成立的系统定位、结构、职责、关系、一致性和演进约束。
- MVP、P0、交付范围、实施顺序、暂缓项、项目门禁和实验状态不进入概要架构正文，由详细设计、实施方案和验证文档分别维护。
- 模块化单体、正式知识单路径、Snapshot、Capability Evaluation 等内容只有在作为总体架构选择时才保留，不能再以阶段性简化为理由定义。
- 可选职责使用“条件能力及启用边界”表达；条件能力仍必须遵守同一正式知识权威和核心领域语义。

### AD-121：Knowledge Schema 通过新 Snapshot 受控演进

- Knowledge Schema 是 Knowledge Engine 管理的版本化语义契约，每个 Snapshot 固定绑定一个 Schema 版本。
- Schema 变化复用正常 Knowledge Update，只能生成新的候选 Snapshot，不原地修改 CURRENT，也不能只重建 Projection 来代替正式知识演进。
- 语义保持型变化可以使用可回放的迁移 Strategy 提出迁移 Candidate；不能证明等价的变化必须按知识性质基于 Evidence、外部来源或重验证后的正式前提重建。迁移和重建 Candidate 都由 Knowledge Verifier 独立审核，Strategy 不能自证。
- 无法安全迁移或重建的对象不得进入新 Snapshot；弃用表示也必须由目标 Schema 定义并作为新 Candidate 完成准入。稳定身份只有在命题语义未变化且身份复用条件通过审核时才能继承；语义变化必须分配新身份。
- Schema、依赖、上游 Snapshot、并发基线和发布条件全部通过后才能切换 CURRENT；失败保留原状态。Projection 必须绑定 Snapshot 与 Schema 并从新权威状态重建。

### AD-122：KnowledgeScope 是发布、并发和逻辑分片边界

- 单个 KnowledgeScope 是 Snapshot 原子发布单位，不同 Scope 拥有独立 CURRENT，可以并发构建和发布，不存在全局 CURRENT 或覆盖全部 Scope 的发布锁。
- Scope 之间不建立分布式发布事务。跨 Scope 正式知识固定引用确切上游 Snapshot，并通过依赖变化检测、显式或计划更新和重验证受控最终一致。
- 上游 CURRENT 变化后，下游在重验证或重建前继续绑定原上游 Snapshot，或明确暴露依赖过期状态，不能静默重绑定。
- KnowledgeScope 的逻辑分片不等于物理数据库分片、服务拆分、租户或安全边界；物理路由和部署不能改变 Scope 身份与 Snapshot 一致性语义。

### AD-123：来源冲突通过 Fact 与 Conflict Inference 表达

- 不同来源提供互不兼容的直接观察时，各自按照 Evidence、来源语义和 KnowledgeContext 形成独立 Fact，不强制合并、覆盖或选择一个全局真相。
- 来源或上下文不同本身不等于冲突；只有正式 Fact 在经过验证可比较的目标、维度和上下文中互不兼容时，才能形成 Conflict Inference。
- Conflict Inference 是普通 Inference 的语义类型，必须引用被判断为互不兼容的正式 Fact、比较依据和 KnowledgeContext，并遵守普通 Inference 的 Scope、准入、Snapshot 和失效规则。独立 Fact 的共存本身不构成正式冲突结论。
- 冲突不创建特殊 Entity、平行存储或新的知识层，也不覆盖或删除原始 Fact。Semantic View 和响应不能静默隐藏已确认冲突。

### AD-124：平台遥测与成本治理是横切能力

- Platform Telemetry & Cost Governance 贯穿入口、任务、Agent、Capability、模型、Tool、Connector、Knowledge Update、Snapshot 发布和审核，但不构成业务模块或正式知识权威。
- 平台传播统一关联与资源政策上下文，并记录延迟、结果、重试、模型和工具用量、估算成本、预算分配与消耗，以及配额、速率和并发限制触发情况，支持按任务、KnowledgeScope、Capability、Strategy、模型和 Connector 聚合。
- Application Services 拥有预算、配额、速率和并发政策及应用用例内部循环决定；Agent Orchestrator 拥有 Agent 级编排决定；各执行边界只执行资源检查并报告真实消耗。观测设施使用中立单向事件，不能反向调用业务模块或作出知识、发布、充分性和响应决定。
- Model Gateway 和各执行边界拥有原始 Usage / Provider Charge Observation；Telemetry 拥有规范用量索引和按 exact Pricing Revision 形成的非控制性估值；Resource Ledger 只按 Application-owned、随 Allocation 冻结的 Budget Conversion Rule 控制运行。三者不相互覆盖或同步依赖。
- `AUDIT_REQUIRED` 事件由 Authority Owner 的本地 Outbox / Emission State 产生，Telemetry 不跨越模块扫描私有 Repository。默认能力只要求可归因用量、估算成本和明确 UNVALUED；财务账单对账、税费折扣、分摊和换汇只在真实需求出现后扩展。
- Telemetry、成本台账和审计索引不是 Artifact、Evidence 或正式知识。若对平台自身建模，仍须重新经过 Data Source、Connector、Artifact 和正式知识路径。

> **后续细化：** AD-127 将 Agent 级权威推进、授权和分派决定归属 Conversational Task Control；Agent Orchestrator 只形成编排 Proposal。AD-124 中关于资源政策、执行记录与 Telemetry 单向性的结论保持有效。

### AD-125：详细设计按稳定责任主题持续演进

- 详细设计采用“总纲 + 独立主题文档”的阶段无关体系；主题 ID 表达设计域和责任，不表达开发阶段、MVP 或实施顺序。
- 主题文档独立版本化并管理 Draft、In Review、Accepted、Superseded、Retired 和 Withdrawn 状态；设计状态与实现进度、验证结果分离。
- KnowledgeContext 与稳定引用作为知识基础前置契约；Capability Execution、Model Gateway、Capability Evaluation / Strategy Activation 按各自所有权分别设计，并共同为模型能力提供执行、访问和演进边界。Knowledge Update 可以先保留概要语义骨架，但只有 Artifact、知识形成、准入和 Snapshot 发布依赖完成后才能最终定稿。
- 每次迭代由独立实施方案选择已经 Accepted 的详细设计版本；后续能力在编码前先完成相应主题设计，因此无需为 MVP 或版本复制一套详细设计。
- 新对象、状态和协调协议只有在保护当前能力的不变量、删除后会产生可复现错误且不能由现有对象或局部事务表达时才进入详细设计；扩展性优先由稳定 Contract / SPI 保证，不预建空模块、占位状态机或未来服务。
- 第一个生产实施方案建立时再创建 Design Baseline Manifest 固定采用的概要架构和主题文档精确版本，不预先建立没有消费者的空基线。

### AD-126：Demo 只用于关闭明确的设计不确定性

- Demo 只有在存在会实质影响正式契约、技术边界或可实现性的设计不确定性、静态分析无法可靠关闭且问题可被有界实验判定时才启动；不要求预先存在两个完整方案。
- Demo 开始前必须建立设计验证记录，固定问题、方案、假设、环境、数据、模型、工具、Oracle、判定标准和停止条件；运行结果与设计状态分离。
- Demo 是可丢弃的证据生成资产，不是生产实现、设计权威或验收旁路；其中的类型、表、流程、算法和阈值不自动进入正式设计。
- 验证结论只有经复核并吸收到主题详细设计后才能约束实现；若改变概要边界，还必须同步更新 ADR 和概要架构。
- 单项目或单模型成功只能证明限定条件下可行，不能自动证明跨项目、跨来源或跨模型泛化。

### AD-127：Task Control 与 Response Control 拥有 Web 任务的权威控制

- Web Chat Adapter 把自然语言请求交给 Conversational Task Control。Task Control 拥有任务 Revision、Agent 任务与调用、委托授权、资源分配、动作授权和 Application 调用分派决定。
- Agent Orchestrator 只基于任务上下文提出意图、职责路由和下一动作 Proposal；它不拥有权威任务状态，不签发授权，也不直接调用 Application Services。
- 具体 Agent 执行获授任务。只读用例可以在确切授权内调用；会改变状态的动作必须返回 Action Proposal，由 Task Control 校验、授权并取得唯一分派权后调用 Application Services。
- Answer Review Agent 只提出审核 Assessment；Response Control 独立重建审核结果，拥有最终响应授权和交付决定。Agent 或模型不能自证、自批或自行发送响应。
- 本条替代 AD-065、AD-067 至 AD-074 中关于 Web 首接方、流程决定、重试放行、调用授权和最终返回权的旧归属，也细化 AD-124 的 Agent 级资源决定。旧条目中的职责型 Agent 名称与可扩展 Capability Contract 仅在不与本条冲突时继续适用。

### AD-128：正式知识状态不因后续可验证性变化而原地改写

- 已发布 Entity、Fact 和 Inference State 是确切 Snapshot 中的不可变历史断言；后续 Evidence 不可访问、依赖变化或新观察不会原地改变该 State，也不能据此推出反命题。
- 构建新 Snapshot 时，只有经过目标 Context、Schema、Evidence 或正式前提重验的 State 才能继续入选。无法重验的 State 不进入新 Snapshot，并在本次权威结果中保存最小 Revalidation Signal。
- Revalidation Signal 只表达“需要重验”及其确切目标和原因，不是 Evidence、Fact、Inference、冲突结论或自动更新命令；当前不为它建设独立 Repository、队列、状态机或传播引擎。
- 本条替代 AD-016 中 `UNVERIFIABLE / INVALIDATED` 作为已发布 Fact 可变状态的做法，并统一 Fact、Inference、Admission 和 Snapshot 的处理语义。

### AD-129：Schema Core 与跨 Schema Evolution 分离

- Schema Definition、Registration 和目标 Snapshot 的 Schema Validation 是所有正式知识构建都需要的 Knowledge Engine 基础能力。
- 跨 Schema Compatibility、Migration、Identity Continuation 和 Adoption 只在已有 Scope 确实迁移到另一 Schema 时启用，不成为普通构建、查询或首次初始化的前置依赖。
- Evolution 仍复用普通 Candidate、Knowledge Verifier、Knowledge Update 和 Snapshot Publication 主干，不原地迁移历史正式知识，也不建立独立 Evolution Orchestrator。
- 只有出现持续影响传播或自动重建需求后，才为自动 Evolution 编排建立专题设计；基础 Schema Contract 不预留空服务或占位状态机。

### AD-130：当前权威持久化采用最小单库策略

- 模块化单体使用一个逻辑 ACID 权威库承载正式知识和发布事务；逻辑所有权仍由各模块控制，不能跨所有者直接写表。
- 正式知识和 Snapshot 当前 append-only 保留，Knowledge Use 直接读取权威 Repository。系统不预建 Projection、物理 Cleanup、分布式保留协议或非连续历史恢复机制。
- KnowledgeScope 仍是独立 CURRENT、并发和逻辑分片边界，但不等于物理分库或独立服务。不同 Scope 的发布不需要全局锁。
- 当数据量、查询模式或保留成本形成可测量触发条件时，再设计 Projection、Cleanup 或物理分片；扩展不得改变稳定引用、Snapshot 原子性和权威数据所有权。

### AD-131：生产能力与候选评测共享执行路径但隔离资格和输出

- Capability Contract 保持稳定，确定性、模型主导和混合 Strategy 可以随模型能力演进；生产执行只接受已通过当前门禁的精确资格，候选评测只能写隔离评测结果。
- 请求时选择的模型名称或滚动别名不足以证明资格。模型调用完成后，Capability Owner 必须在封存领域结果前校验实际模型、Adapter 和回放分类仍在本次冻结的允许范围内。
- 校验失败时本次领域输出失败关闭，并使相关评测依据进入重新评估；不能先写入 Artifact、Candidate、Application Result 或响应，再依赖异步修正。
- 资格、权限、稳定身份、Lineage、Admission、Publication 和响应放行继续由平台控制；随着模型增强，可以减少具体解析和语义启发式规则，但不能把这些权威责任让渡给模型。

### AD-132：模型生产调用使用冻结输入与执行前无外部访问隔离

- 每次模型调用必须具有唯一 Authorized Input Manifest，固定 Prompt 渲染、输入内容、数据分类、来源引用、输出 Proposal Vocabulary 和完整 Request Digest；Telemetry 摘要不能代替该清单。
- 需要证明结果只依赖授权输入的 Capability 使用 `NO_EXTERNAL_ACCESS` Provider Runtime：shell、文件、Web、MCP、Agent Runtime、Provider 托管检索、附件和隐藏会话记忆在分派前机械禁用或物理隔离。提示词禁止、空目录、只读工作区和事后 Tool Event 检查都不能替代。
- 模型可以输出 Platform Tool / Source Operation Proposal，但 Provider 不执行它。Application Services 在模型调用结束后重新授权，业务模块执行，再把受控 Observation 作为下一次调用的新 Manifest 输入。
- Gateway 在分派前签发绑定 exact Request 和有效 Adapter Conformance 的 Isolation Receipt；Receipt 缺失、过期、失配或发生隔离违约时，模型结果不得进入 Proposal、Candidate、Assessment、Application Result、Answer 或生产缓存。
- 该决策保护软件世界模型的知识可信链，不把企业级租户安全、合规、网络治理或全部非功能能力提前纳入核心功能范围。

### AD-133：Canonical Build Target 使用解析凭证、发现边界与覆盖映射

- 人类描述、短 Revision、路径片段、同名/重载对象和模型自报 ID 只能作为 Target Proposal；Source Integration 或相应身份 Owner 必须返回 exact canonical identity 和不可变 Resolution Receipt，歧义、越界和不存在均失败关闭。
- Build Intent 冻结 exact Target，或冻结 exact canonical root 与可机械判断的 descendant discovery boundary。调查可以在边界内发现子目标，不能以语义“相关”为由扩大到其他 Scope、DataSource、Revision、模块或全仓库。
- Build Objective 通过版本化 Target Shape Contract 规定最低目标关系；例如 change-impact 必须解析 exact revision 与适用 comparison parent / base，changed objects 可以在该 comparison boundary 内发现并进入 Coverage Map，不能以任意同类型 History 知识替代。
- Application Services 维护从 Required Target 到 Source Information Need、Tool Step、Artifact、Candidate Disposition 和 Publication Manifest Member 的 Coverage Map；无关同类型知识不能满足该映射。
- Target Coverage 证明本次更新没有跑偏，Publication Acceptance 判断承诺的更新能否发布；发布后 Knowledge Sufficiency 才判断原 Requirement / Need 是否得到满足。三者不能合并。

### AD-134：逐 Need 充分性使用可重建的正式知识支持证明

- Requirement Need 必须对应一个可独立裁决的实质问题、断言或具有明确 Coverage 语义的枚举目标；可以分别失败的断言拆分为 Need，共同成立条件表达为 Joint Knowledge Constraint。
- 每个 Need Assessment 从固定 Snapshot Read Session 的权威正式知识重建 Support / Counterexample Reference、Canonical Proposition / Conclusion、Context、Coverage、Conflict 和未知边界，并形成不可变 Support Proof。
- 语义蕴含可以由经过评测的模型 Strategy 判断，但模型不能创建正式引用、改变 Criterion、删除未满足项或执行最终集合聚合；平台机械检查完整性并仅在全部 Need / Joint Constraint SATISFIED 时产生 SUFFICIENT。
- Gap、未知、冲突、引用越界和 Coverage 不足必须显式保留。Answer drafting 与 Review 只能消费 Assessment 和正式知识，不能用流畅答案补写未进入 Support Proof 的语义。

### AD-135：详细设计主题按权威所有者和独立生命周期划分

- 详细设计主题是可独立评审的稳定责任边界，不是运行时模块、功能菜单、调用流程或文档篇幅分段。不同权威状态、生命周期、一致性语义或独立变化原因必须拆分；同一所有者内紧密协作的对象可以保留在同一主题。
- KnowledgeScope 的身份和状态归 Knowledge Engine；DataSource、DataSourceBinding、Selector、来源操作和 Artifact 归 Source Integration；跨所有者组合管理命令和结果归 Management Application Services。原 `DD-MGT-SCOPE-BINDING` 的混合所有权主题据此拆分，不改变概要架构组件或部署形态。
- Semantic View Definition / Execution 归 Semantic View Engine，Knowledge Requirement、Snapshot Read Session、Sufficiency 和 Gap 归 Knowledge Use。View 接收中立的 exact Read Boundary，不读取或推进 Application Session，避免 Core Capability 反向拥有 Application 状态。
- Conversational Task Control 拥有任务、Agent Invocation、委托授权和 Application Dispatch；Response Control 独立拥有 Answer Candidate、Review Decision、Final Authorization 和 Logical Delivery。二者只交换不可变 Reference、Result 和只读 Assertion，不互写状态。
- 权威持久化主题只拥有 Knowledge Authority Store / Repository Contract；Projection、Cleanup 和非连续恢复仍是条件关闭能力，因此不把 `Projection` 写入当前主题身份。通用 Result Delivery Assertion 属于横切执行契约，使用 `X-*` 身份，不伪装成某个应用结果所有者。
- 这些调整是对 SWM-ARCH@1.2 已有逻辑所有权的详细设计校正，不新增顶层业务模块、服务或数据库，也不构成交付范围。后续新增主题仍须证明唯一 Owner、公共契约、生命周期和适用条件，不能为了目录对称或未来可能性拆分。

## 当前生效关系索引

本日志保留历史措辞；以下索引用于定位当前主题的生效决策，最终定义以当前概要架构基线为准。

| 主题 | 当前生效决策 |
|---|---|
| Fact / Inference 认知性质、依赖、冲突与模型 Candidate | AD-087、AD-091、AD-095、AD-108、AD-116、AD-123、AD-128 |
| Semantic View 与 Runtime 边界 | AD-035、AD-036、AD-062、AD-114 |
| Agent、Application Services 与审核职责 | AD-112、AD-115、AD-127 |
| Requirement、Sufficiency 与答案完整性 | AD-089、AD-104、AD-107、AD-112、AD-134 |
| Knowledge Update、Build Intent 与 Source Investigation | AD-076、AD-092、AD-096、AD-101 至 AD-103、AD-109、AD-110、AD-133 |
| Derived Artifact、Evidence 与可信根 | AD-017、AD-023、AD-026、AD-091、AD-108 |
| Scope、跨系统业务与上下文 | AD-011 至 AD-013、AD-029、AD-030、AD-079、AD-111 |
| Snapshot、Schema、Scope 分片与并发发布 | AD-005、AD-009、AD-096、AD-099、AD-113、AD-121、AD-122、AD-128 至 AD-130 |
| AI Native、Capability Strategy 与 Provider | AD-019 至 AD-021、AD-059、AD-060、AD-087、AD-088、AD-094、AD-100、AD-101、AD-110、AD-117、AD-131、AD-132 |
| 权威持久化与条件 Projection / Cleanup | AD-113、AD-122、AD-125、AD-130 |
| 平台运行观测、预算与成本治理 | AD-124 |
| 产品定位、价值、直接调查基线与门禁 | AD-082 至 AD-086、AD-093、AD-098、AD-105、AD-106、AD-118 |
| 概要架构视角、文档分层与权威关系 | AD-119、AD-120、AD-125、AD-126、AD-129、AD-130、AD-135 |
