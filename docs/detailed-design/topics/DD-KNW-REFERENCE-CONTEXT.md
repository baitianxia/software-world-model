# KnowledgeContext 与稳定知识引用详细设计

| 元数据 | 值 |
|---|---|
| Document ID | DD-KNW-REFERENCE-CONTEXT |
| Version | 0.1.0 |
| Status | Accepted |
| Document Steward | Knowledge Engine |
| Architecture Baseline | SWM-ARCH@1.2 |
| Depends On | DD-KNW-KNOWLEDGE-SCOPE@0.1.0 |
| Owns Contracts | KNW-CONTEXT-01、KNW-OBSERVED-BASIS-01、KNW-CONTEXT-REF-01、KNW-SCHEMA-REF-01、KNW-SNAPSHOT-REF-01、KNW-FORMAL-REF-01、KNW-REVALIDATION-SIGNAL-01 |
| Supersedes | None |
| Rationale ADR | AD-029、AD-030、AD-079、AD-111、AD-121、AD-122、AD-123、AD-128 |
| Design Validation | None |
| Conformance Cases | None |
| Capability Evaluation | None |

> 概要架构约束直接生效；本文新增的 Context 表达、比较结果和稳定引用外壳在状态进入 `Accepted` 前均为拟议设计。

## 1. 目的与范围

本文拟定所有后续知识主题共同使用的基础语义：

1. KnowledgeContext 如何保留不同来源各自的 Environment、Version、Time 等成立条件，并为后续组合和比较提供稳定表达，而不强行建立全局版本映射。
2. Scope、Knowledge Schema、Snapshot 和正式知识如何使用不可歧义的稳定引用，避免 `latest`、`current`、名称或隐含会话进入持久依赖。
3. 当既有候选或正式知识需要重新验证时，如何用最小诊断信号传递影响，而不提前建设自动传播引擎。

本文只定义基础表达和判断结果，不定义：

- Artifact、Evidence、Fact 或 Inference 的业务字段。
- Context 提取、跨来源关联和兼容性判断的具体算法。
- Snapshot 创建、发布、保留和事务。
- Knowledge Schema 内容、迁移或兼容策略。
- 数据库编码、索引、序列化格式和 API 字段名。

## 2. 核心原则

### 2.1 Context 是成立条件，不是全局标签

KnowledgeContext 不是给所有信息覆盖同一组 `version/environment/time` 标签。它是一个不可变条件表达，必须保留每个条件的主体、维度命名空间、值及其来源依据。

例如：

- Git Artifact 可以具有 `git.commit = A`。
- Log Artifact 可以具有 `environment = production` 和 `eventTime ∈ [t1,t2]`，但不知道对应哪个 Git Commit。
- DB Artifact 可以来自测试实例，也可以来自生产实例，两者各自保留环境和观察时间。

这些信息可以共同参与调查，但不能因为位于同一次 Knowledge Update 中就被改写为同一版本或同一环境。

### 2.2 组合不等于硬关联

跨来源 Context 组合首先保留各自条件，再判断是否存在明确的相容、排斥或未知关系。没有可靠关联时保留 `UNKNOWN`，不能要求预先配置所有平台之间的版本映射，也不能由模型把“看起来相似”提升为确定关系。

### 2.3 稳定引用不包含动态别名

`CURRENT`、`latest`、显示名称和默认 Scope 都是查询选择条件，不是持久化引用。一次读取或构建在开始时把动态选择解析为不可变引用，后续过程只能使用解析结果。

## 3. KnowledgeContext 逻辑模型

### 3.1 Source Context 与 KnowledgeContext 所有权

Source Integration 和 Knowledge Engine 可以共享 Context 的值类型与维度词汇，但不共享 Repository 或写入权：

| 对象 | Owner | 作用 |
|---|---|---|
| Source Context | Source Integration | 表达一次来源操作或 Artifact 直接观察到的环境、版本和时间；随 Artifact 保留不可变 Source Context Reference |
| KnowledgeContext | Knowledge Engine | 在一个 owning KnowledgeScope 和目标 Knowledge Schema 下，保留或组合 Source Context，并约束 Evidence、Fact 与 Inference 的成立条件 |

Knowledge Engine 通过 `NormalizeSourceContext` 消费 Source Context Reference、来源值和定位，按目标 Knowledge Schema 的 Context 词汇验证并创建 KnowledgeContext。规范化必须保留原 Source Context Reference，不能把来源条件覆盖为目标 Scope 的默认值。

同一个 Source Context 被多个 Scope 使用时，各 Scope 分别创建自身的 KnowledgeContext Reference；共享来源表达不表示跨 Scope 共享写入所有权。

### 3.2 Context Term

Context Term 表达一个主体在一个明确维度上的条件：

| 语义 | 约束 |
|---|---|
| Subject | 条件所描述的来源观察、前提或正式知识引用；不能省略后默认作用于整个运行 |
| Dimension | 带命名空间和版本的维度定义 |
| Predicate | 等于、属于集合、范围、之前、之后、包含等由维度允许的谓词 |
| Value | 按维度类型规范化的值；保留来源原始值或其定位 |
| Basis | `OBSERVED` Term 使用 KNW-OBSERVED-BASIS-01；`DERIVED` Term 只能引用 Resolved Formal Knowledge Reference |
| Origin | `OBSERVED` 或 `DERIVED`；不能用模型置信度替代来源性质 |

`OBSERVED` 表示值可由来源元数据或 Evidence 复核；`DERIVED` 表示值已经由正式 Fact 或 Inference 支持。任何自动化或模型原始输出只能形成 Context Term Proposal，不能成为正式 Term 的 Basis。未知值或未知关系保留在 Investigation、Candidate 或后续比较结果中，不能包装成正式 KnowledgeContext Term。模型自报不能把 Term 变为 `OBSERVED` 或 `DERIVED`。

#### KNW-OBSERVED-BASIS-01

Observed Basis 使用稳定、可扩展的判别外壳，避免 Context 基础契约反向依赖某一种 Artifact 或 Evidence 实现：

| Basis Kind | 必须固定 |
|---|---|
| `SOURCE_CONTEXT_TERM` | Source Context Reference、Vocabulary / Canonicalization Version、原始 Term Locator 与值 Digest |
| `OBSERVED_CONTENT_LOCATOR` | Basis Namespace / Contract Version、不可变 Carrier Reference、Carrier Schema Reference、Locator Contract Version、Canonical Locator、Observed Content Digest、Observation Closure Digest、Source Context Reference 和 Provenance Closure Digest |

Basis Namespace 的所有者负责注册确定性 Validator；Knowledge Engine 只接受当前 Knowledge Schema 明确允许、字段完整并能由权威 Repository 重建的 Basis。模型自报、动态 `latest` Contract、缺失 Schema / Locator Version 或只有自由文本说明的 Basis 一律拒绝。

Observed Basis 不是 Evidence、Fact 或正式知识，只证明某个 Context Term 的直接观察位置。完整 Basis 参与 Context Canonicalization 和身份，不得只保存 Hash 后丢弃版本闭包。Evidence 主题可以用 Artifact / Evidence Locator 实例化 `OBSERVED_CONTENT_LOCATOR`，而不改变本基础契约。

其中 `Observed Content Digest` 只覆盖规范化后的精确内容；`Observation Closure Digest` 还覆盖 Carrier、Locator、解释 Schema 等观察闭包。两者不能互换，也不能用同一字段名隐藏不同 canonical input。

### 3.3 标准维度

首批标准维度如下，允许通过版本化 Schema 扩展：

| 维度族 | 必须区分的语义 |
|---|---|
| Environment | 环境命名空间、环境身份或类别；不同系统中都叫 `prod` 不自动表示同一环境 |
| Version | 版本命名空间、种类和值，例如 Git Commit、Branch、Tag、Artifact Version、Image Digest、DB Schema Version |
| Time | Event Time、Valid Time、Observation Time 和处理时间；Instant 与 Interval 不混用 |
| Deployment | 可选的部署实例或发布批次身份；只有来源确实提供时才建立 |

Branch 是一个可变选择名称，Commit 或其他不可变 Revision 才能固定源码内容。仅知道 Branch 时必须保留其观察时间，不能在后续自动解释为 Branch 当前指向。

### 3.4 Context Expression

KnowledgeContext 是由 Context Term 和显式逻辑关系构成的不可变表达：

- `AND`：多个条件同时适用，但不抹平各自 Subject。
- `OR`：来源只能确定若干可能条件之一。

未知关系的多个 Context 可以共同出现在 Investigation 中，但在关系获得正式依据前不能合成一个宣称共同成立的 KnowledgeContext。

Context Expression 必须可规范化、可稳定引用和可完整回放。语义等价的表达可以去重，但不能为了获得同一身份键而丢弃 Subject、Basis 或来源性质。

### 3.5 KNW-CONTEXT-REF-01：创建、身份与解析

KnowledgeContext Reference 至少固定：

- owning KnowledgeScope ID。
- 不可变 Context ID。
- 解释 Context 维度的 Knowledge Schema Reference。
- Canonicalization Version。

`CreateKnowledgeContext` 接收 owning Scope、目标 Schema、Term/Expression 和完整 Basis，执行：

1. 验证维度、值类型、Subject、Basis 和 Origin。
2. 验证嵌套表达引用形成 DAG，不允许直接或间接循环。
3. 按目标 Schema 指定的 Canonicalization Version 形成规范表达和逻辑身份键。
4. 在 owning Scope 内原子执行 get-or-create；并发等价创建返回同一 Context Reference。
5. 持久化规范表达及 Source Context / Formal Knowledge Basis，不只保存哈希。

`ResolveKnowledgeContext` 验证 Scope、Schema、读取权限和对象状态。跨 Scope 使用不能直接复用 Context ID；必须通过确切上游正式知识或 Source Context 重新形成目标 Scope 的 KnowledgeContext。

Canonicalization 变化创建新版本和新 Context Reference，不能原地重算旧身份。语义等价只在相同 Schema 与 Canonicalization Version 内判断。

### 3.6 生命周期与传播

- Artifact 保留 Source Integration 拥有的 Source Context；Evidence 同时保留 Source Context Reference 和 Knowledge Engine 规范化后的 KnowledgeContext Reference，二者都不被目标 Snapshot 改写。
- Entity 身份本身不承载可变业务属性；其存在、别名或状态条件由正式知识主题决定。
- Fact 的 KnowledgeContext 由其 Evidence 条件和命题成立条件形成，不能比支持它的 Evidence 覆盖更宽。
- Inference 的 KnowledgeContext 由全部正式前提及推理规则约束形成，不能静默丢弃不兼容条件。
- Snapshot 可以声明发布和读取范围，但不能把成员知识的 Context 重写成 Snapshot Context。
- Context 一旦被 Candidate、正式知识、Snapshot 或响应依据引用即不可修改；新判断创建新 Context 身份。

## 4. 稳定引用契约

### 4.1 Scope Reference

Scope Reference 只包含稳定 Scope ID。Scope Type 和显示信息是被引用状态，不作为身份的一部分。要求特定 Scope Definition Revision 的管理命令必须另行固定该 Revision。

### 4.2 KNW-SCHEMA-REF-01：Knowledge Schema Reference

`Knowledge Schema Reference = Schema ID + Version Label + Definition Digest`。三项都必须存在；Version Label 便于管理，不能代替 Digest，引用也不能使用 `latest`。

Schema 兼容性是显式判断结果，不从版本号大小推断。Definition、Registration 与 Target Validation 由 DD-KNW-SCHEMA-CORE 定义；Compatibility、Migration 与 Identity Continuation 由 DD-KNW-SCHEMA-EVOLUTION 条件性定义。

### 4.3 KNW-SNAPSHOT-REF-01：Snapshot Reference

Snapshot Reference 至少固定：

- owning KnowledgeScope ID。
- 不可变 Snapshot ID。
- Knowledge Schema Reference。

`CURRENT` 是 `ResolveCurrentSnapshot(scope)` 查询操作。该操作返回一个 Snapshot Reference 或明确的“尚无 CURRENT”；一旦返回，后续 Snapshot Read Session、Build Intent、上游依赖和审核都使用该不可变引用，不随新的发布漂移。

Snapshot 是否存在、是否仍被保留以及能否按目标用途读取，由 Snapshot 主题判断。引用结构本身不赋予读取权限。

#### Upstream Snapshot Binding

Upstream Snapshot Binding 表示一次知识构建或一个已发布 Snapshot 对另一个 Scope 的确切正式知识依赖，其目标必须是完整 Snapshot Reference。

它与 DataSourceBinding 不可互换：前者由 Knowledge Engine 拥有并固定已发布正式知识版本，后者由 Source Integration 拥有并限定外部来源访问范围。Upstream Binding 的创建、过期和保留由 Snapshot 主题定义。

### 4.4 KNW-FORMAL-REF-01：Formal Knowledge Reference

正式知识具有两个不同引用层次：

| 引用 | 组成 | 用途 |
|---|---|---|
| Knowledge Identity Reference | owning Scope ID、Knowledge Kind、稳定 Knowledge ID | 表达跨 Snapshot 延续的命题或实体身份 |
| Resolved Formal Knowledge Reference | Snapshot Reference + Knowledge Identity Reference | 证明某个确切 Snapshot 中存在并可解释的正式知识 |

Knowledge Kind 只允许 `ENTITY`、`FACT` 或 `INFERENCE`。Artifact、Evidence、Candidate、View、Claim 和 Agent 状态不能伪装成 Formal Knowledge Reference。

所有跨 Scope 正式依赖、Semantic View 成员、Sufficiency Assessment 依据和知识型 Answer Claim 必须使用 Resolved Formal Knowledge Reference。只保存稳定 Knowledge ID 不能证明该对象在当前 Snapshot 中存在或具有相同语义。

### 4.5 KNW-REVALIDATION-SIGNAL-01：最小影响诊断

Revalidation Signal 表示：新观察、依赖变化、Context / Schema 变化或权威存储完整性问题，使某个既有候选或正式知识不能未经重验继续进入目标 Snapshot。它只要求后续重新调查或验证，不表示目标命题为假、已经失效，也不支持其反命题。

信号作为产生它的 Authority Attempt、Result 或完整性诊断中的不可变值保存，不建立独立 Repository、状态机、确认队列或后台处理器。其稳定引用由 `producer reference + item digest` 组成；最小内容为：

- owning KnowledgeScope、产生时间和产生原因的版本化类别。
- 正式目标的 Knowledge Identity Reference 或 Resolved Formal Knowledge Reference；构建期目标只能使用产生主题拥有的、带 Kind / Version / Digest 的不透明局部引用。
- 触发判断所使用的确切 Evidence、Premise、Context、Schema、Snapshot、存储诊断或其他稳定 Cause Reference，以及 Read Set / Cause Digest。
- 产生它的 Attempt / Result Reference 和可选的后续调查约束；自由文本说明不能替代上述引用。

Knowledge Update 可以在获得正常命令授权后把信号作为 Build Objective / Investigation 输入，但必须重新解析目标和当前来源，不得把信号本身当作 Evidence、Fact、Inference、冲突结论或自动更新命令。普通 Knowledge Use 不把信号作为答案依据；是否向用户披露“需要重验”由固定 Session 上的 Sufficiency / Limitation 和 Response Review 决定。

该契约只统一当前流程已经产生的诊断值。自动影响传播、订阅、优先级、批量消解或 Evolution Orchestrator 只有出现持续自动重建需求后另行设计。

### 4.6 引用解析不变量

- 引用解析必须验证 Scope 一致、Schema 可解释、Knowledge Kind 一致且对象确实属于目标 Snapshot。
- 一个 Scope 中的 Knowledge ID 不能被另一个 Scope 解释；跨 Scope 使用必须保留原 owning Scope。
- Schema Evolution 只有在稳定身份复用条件通过审核时才延续 Knowledge Identity Reference；语义变化创建新身份。
- 任何持久依赖都不能保存“默认 Scope”“当前会话”“最新版本”或未解析名称。

## 5. 典型上下文融合示例

假设一次调查具有：

```text
Code Artifact:
  subject = source:git-repo-x
  version.git.commit = A

Log Artifact:
  subject = source:log-service-x
  environment = production
  time.event = [2026-07-01T00:00Z, 2026-07-01T01:00Z]
  no observed deployed-code-version term
```

合法结果是保留两个独立 Source/Knowledge Context，并在 Investigation 中记录“部署版本关系未决”。它们可以共同帮助调查，但 Log 不能被标记为 Commit A，也不能直接反驳 Commit A 的代码行为。

如果后续来源提供了可复核的 Image Digest 与 Commit 映射，该对应命题先按 Fact 形成与准入；后续 Context Comparison 能力再依据该正式 Fact 判断兼容关系。原 Context 和原 Artifact 仍保持不变。平台不要求所有环境必须接入发布平台后才能工作，也不把缺少硬映射伪装成确定结论。

## 6. 失败与保守处理

| 类别 | 含义 | 处理 |
|---|---|---|
| CONTEXT_INVALID | Context 表达不满足维度契约 | 拒绝当前 Proposal 或 Candidate |
| DIMENSION_UNKNOWN | 当前 Schema 不认识该维度版本 | 保留原始定位，不能静默丢弃 |
| SCHEMA_REF_NOT_FOUND | Schema Reference 无法解析 | 失败关闭 |
| SNAPSHOT_REF_NOT_FOUND | Snapshot 不存在或已按策略不可读 | 内部明确返回，不回退到 CURRENT |
| REFERENCE_ACCESS_DENIED | 引用存在但当前主体无读取权限 | 失败关闭；外部接口可与 NOT_FOUND 统一映射为不可用以防存在性泄露，审计保留真实原因 |
| REFERENCE_RETIRED | 引用存在但目标已受控退出且当前用途不允许读取 | 按保留与用途策略返回，不替换为其他版本 |
| SCOPE_MISMATCH | 引用的 owning Scope 与对象不一致 | 拒绝并审计 |
| KNOWLEDGE_TYPE_MISMATCH | Knowledge Kind 与实际对象不一致 | 拒绝并审计 |
| OBJECT_NOT_IN_SNAPSHOT | 稳定身份存在，但不属于被引用 Snapshot | 返回不存在于该 Snapshot，不改读其他版本 |

## 7. 可观测性与敏感信息

- Context 创建与解析记录 Correlation Reference、输入 Source Context / KnowledgeContext Reference、Schema、Canonicalization Version 和结果。
- 不在 Telemetry 中复制 Artifact Payload、Evidence Quote 或敏感环境配置。
- 模型使用的 Context 内容必须由调用边界显式授权和裁剪。
- Secret、访问令牌和数据库连接信息永远不是 Context Term。

## 8. 拟议不变量

1. Source Integration 拥有 Source Context，Knowledge Engine 拥有 Scope 内 KnowledgeContext；共享表达格式不等于共享 Repository 或写入权。
2. Environment、Version 和 Time 的相同字符串不自动表示相同语义。
3. Context 组合保留 Subject 和 Basis；未知关系保留为 Investigation 中的独立 Context 与未决关系，不能被强制合成为正式 Context 或全局版本映射。
4. 模型可以提出 Context 关联，但模型结果不能直接成为正式 Context Basis；派生 Term 只能引用已准入正式知识。
5. Context 不同本身不等于事实冲突。
6. `CURRENT` 和 `latest` 只能用于解析，不得进入持久依赖。
7. 跨 Scope 和对外知识依据必须绑定确切 Snapshot。
8. Artifact、Evidence、Candidate、View 和 Claim 不是正式知识引用目标。
9. KnowledgeContext Reference 固定 Scope、Schema 与 Canonicalization Version；等价创建由 Knowledge Engine 原子去重，表达引用必须无环。
10. 被引用的 Context 和稳定引用对象不可原地修改。
11. Revalidation Signal 只能要求重验，不能自行改变正式知识、CURRENT、任务或评测资格；它没有独立生命周期和自动消费者。

## 9. 下游验证义务

以下内容由下游主题冻结：

- Artifact 如何产生 OBSERVED Context Term：DD-SRC-SOURCE-ARTIFACT。
- Evidence、Fact 与 Inference 如何收窄或组合 Context：对应知识主题。
- Context 兼容性比较、Strategy、执行失败和 Assessment 生命周期：DD-KNW-CONTEXT-COMPARISON。
- Snapshot 生命周期、保留和读取可用性：DD-KNW-SNAPSHOT-PUBLICATION。
- Schema 兼容、迁移与身份延续：DD-KNW-SCHEMA-EVOLUTION。

目前无需 Demo 决定基础表达和稳定引用语义。
