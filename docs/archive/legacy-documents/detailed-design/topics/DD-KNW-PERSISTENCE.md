# Knowledge Authority Persistence 详细设计

| 元数据 | 值 |
|---|---|
| Document ID | DD-KNW-PERSISTENCE |
| Version | 0.1.0 |
| Status | Accepted |
| Document Steward | Knowledge Engine；Source Integration 继续拥有 Artifact / Payload 存储 |
| Architecture Baseline | SWM-ARCH@1.2 |
| Depends On | DD-KNW-REFERENCE-CONTEXT@0.1.0、DD-SRC-SOURCE-ARTIFACT@0.1.0、DD-KNW-EVIDENCE@0.1.0、DD-KNW-ADMISSION@0.1.0、DD-KNW-SNAPSHOT-PUBLICATION@0.1.0 |
| Owns Contracts | KNW-AUTHORITY-STORE-01、KNW-REPOSITORY-READ-01、KNW-STORE-RECOVERY-01 |
| Design Coverage | 权威知识持久化、事务与幂等、可靠事件和默认不物理清理策略；Recovery / Cleanup / Projection 仅作为未来兼容边界 |
| Supersedes | None |
| Rationale ADR | AD-016、AD-019、AD-022、AD-024、AD-027、AD-030、AD-033、AD-042、AD-075、AD-079、AD-080、AD-093、AD-096、AD-097、AD-107、AD-112、AD-115、AD-117、AD-128、AD-130、AD-135 |
| Design Validation | None |
| Conformance Cases | None |
| Capability Evaluation | None；未来 Projection 使用模型生成索引 / 摘要时另建 Capability |

> 当前最简单合规 Strategy 是模块化单体内的单一 ACID 权威库、不可变知识内容、append-only 物理保留和权威 Repository 直接查询。物理 Cleanup、历史字节回收、Projection 与非连续存储恢复都未启用；本文只冻结它们未来不得突破的兼容边界。

## 1. 目的与范围

本主题保证正式知识的持久化不会产生第二权威、半发布 Snapshot、幂等请求换义或由缓存补造知识，并明确哪些存储能力当前关闭。

本文保证：

- Evidence、Admission、Entity / Fact / Inference State、Snapshot、CURRENT 与权威 Outcome 具有唯一 Owner 和事务边界。
- 不可变内容与可变控制绑定分离，canonical Digest 不依赖物理表、图或索引布局。
- 正常进程重启只从同一持久库的事务日志和权威 Record 恢复，不从 Telemetry、Projection 或模型猜测。
- 当前不删除已提交的正式知识字节，因此读取不需要为了尚不存在的并发 Cleanup 承担 Lease / Fence 协议。
- 未来启用 Cleanup、Projection 或非连续恢复时，必须先建立专题详细设计，不能把实现细节暗藏在当前 Repository 后面。

本文不定义：

- 数据库、对象存储、图数据库、搜索或向量产品选型。
- 表、索引、分区键、备份拓扑、多副本 HA、PITR 或主从切换过程。
- Source Artifact / Payload 的淘汰；它由 Source Integration 自身策略处理。
- 当前可执行的历史字节清理、Projection 构建或跨恢复点继续运行能力。

## 2. 最小充分实现与启用条件

| 能力 | 当前 Strategy | 何时才允许展开详细设计 |
|---|---|---|
| 权威持久化 | 单一逻辑 ACID Store；模块化单体内 Repository Port | 当前必需 |
| 正式知识保留 | append-only；只做逻辑状态变化，不删除已提交字节 | 出现经过度量的容量 / 合规删除压力，并决定启用物理回收 |
| 查询 | Knowledge Engine 按 exact Snapshot / Schema 直接读取 | 已验证查询的性能、容量或隔离目标无法由权威 Repository 合理满足 |
| Projection | `DISABLED`；不存在 Registry、Instance、Activation 或 Query Lease | 上述查询瓶颈成立并完成有界设计验证 |
| 非连续恢复 | `UNSUPPORTED`；不建立同库自证状态，部署发现回退 / 主写替换或无法确认历史时必须 fail-stop | 明确采用 PITR、主备切换或存在旧 Worker 跨恢复点继续运行 |
| 分片 / 独立服务 | 单体内逻辑 Repository | 单库容量、吞吐或团队自治产生可复现瓶颈 |

“未来可能需要”不能触发条件能力。条件出现前不创建对应表、状态机、Worker、Registry 或空 Adapter。

## 3. 边界与所有权

| 对象 / 决定 | Owner | 边界 |
|---|---|---|
| Knowledge Schema、Context、Evidence、Identity、Fact / Inference State、Admission、Snapshot、CURRENT | Knowledge Engine | 唯一正式知识权威 |
| Authority Repository 与本地事务实现 | Knowledge Engine Persistence | 只执行 Owner Contract，不解释或改变语义 |
| Data Source、Artifact、Payload、Lineage 与 Source Retention | Source Integration | Knowledge Store 只保存稳定引用和 Evidence 自包含快照 |
| Application Task、Requirement、Session、Assessment、Answer | Application Layer | 不写 Knowledge Repository |
| Semantic View Result | Semantic View Engine | 可重建组织结果，不是正式知识或查询权威 |
| Telemetry / Cost Backend | 横切基础设施 | 只引用权威对象，不参与恢复或裁决 Outcome |

逻辑单库允许多个模块共享同一数据库产品，不允许共享写所有权。跨 Owner 修改仍通过公开 Contract；“在同一数据库”不构成直接写其他模块表的授权。Knowledge Engine Persistence 只持久化 Application Reference，不创建 Application Investigation、Evaluation、Activation、Qualification 或 Resource Ledger 的本地镜像和 current binding；这些对象的当前性仍由其 Owner 的公开 Contract 证明。

## 4. KNW-AUTHORITY-STORE-01

### 4.1 逻辑存储域

Knowledge Engine 至少区分以下逻辑域；它们可以共库但不能互相冒充：

- Definition：Knowledge Engine 自己拥有的 Knowledge Schema、Context Vocabulary 和知识对象 Contract 等不可变定义；不包含 Application-owned Capability Evaluation、Strategy Activation 或 Resource Policy 状态。
- Candidate / Knowledge Construction Staging：Knowledge Engine 重建的 Candidate、Candidate Bundle / Closure 和准入前暂存对象；不包含 Application-owned Investigation Working State、Transcript 或 Source Tool Loop 状态。
- Evidence：Evidence Record、Locator、最小精确 Observed Content Snapshot 和 Materialization Outcome。
- Identity / Knowledge State：Entity Root、Identity Index、Fact / Inference Identity 与不可变 State。
- Admission / Publication：Decision、Batch、Manifest、Publication Attempt / Outcome、Snapshot 与 CURRENT Binding。
- Application Reference：只保存必要的 Task / Build / Requirement / Session / Investigation，以及 Capability Evaluation / Activation / Qualification Proof / Resource Policy 的 opaque exact Reference / Digest；不复制、推进或重新解释 Application 状态。
- Staging：尚未通过权威事务引用的内容写入。
- Audit / Idempotency：最低 Receipt、Outcome 和不可复用 Tombstone。

Projection 不是当前逻辑域。未来启用时仍只能保存可重建派生结果，不能与上述权威域共用“正式”标志。

### 4.2 不可变内容与可变绑定

以下对象一旦封存不得原地改写语义：Definition Revision、Evidence、Entity / Fact / Inference State、Admission Decision、Publication Manifest、Snapshot、Publication Outcome、Receipt 和终态 Result。

允许变化的知识控制对象仅保存指向不可变对象的引用与单调 Revision，例如 CURRENT Binding、Schema Availability Current Revision 和执行中 Attempt。部署 readiness / fail-stop 不属于 Knowledge Authority Store 控制对象。控制对象变化不能改变其目标对象的 canonical Digest，也不能创建 Snapshot Schema 之外的平行“Active Schema”。

### 4.3 Canonical Digest 与物理布局

- Digest 来自版本化 canonical serialization，包含所有影响语义、身份、Context、支持、依赖和限制的字段。
- 物理主键、行顺序、时间戳精度、压缩、数据库生成 ID、缓存位置和索引布局不进入语义 Digest。
- 未知 Schema Version、未知枚举或无法 canonicalize 的输入失败关闭，不以忽略字段保持“兼容”。
- 内容寻址可以去重物理字节，但不能合并不同的逻辑 Owner、生命周期、Classification 或可读性决定。

## 5. Repository 与读取契约

### 5.1 Repository Port

Repository Command 至少固定 Owner、Contract / Schema Version、Request / Idempotency Key、canonical Request Digest、Expected Revision / CURRENT（适用时）和 Correlation Reference。

- 同 Key / Digest 返回原 Attempt / Result；同 Key 不同 Digest 返回冲突。
- 可变绑定使用 CAS；不可变对象只 create-if-absent 或读取原对象。
- Repository 不调用模型、不选择 Strategy、不读取 Application 私有状态，也不通过 Telemetry 决定写入。
- 只有拥有模块可以调用写 Port；跨模块只读也必须使用对方公开 Contract。

### 5.2 KNW-REPOSITORY-READ-01

当前读取只接受 exact Snapshot Reference、Knowledge Schema / Reader Contract、Scope、Context / Coverage Boundary、Purpose、权限 / Classification 和 Query Contract。`CURRENT` 必须由调用用例在读取开始时解析一次并冻结为 exact Snapshot；Repository 不在分页或重试中重新解析。

查询结果至少返回 exact Snapshot / Schema、Resolved Formal Knowledge Reference、State / Proposition Digest、Context、Coverage / Pagination 和限制。空、部分、截断或权限裁剪不能被解释成现实不存在。

当前 Strategy 只读权威 Repository。不存在 Projection 命中、缓存正文或“最近可用 Snapshot”回退路径。

## 6. 事务、幂等与受支持恢复

### 6.1 权威事务

至少以下提交保持各自详细设计规定的原子性：

- Evidence Materialization：Evidence、最小精确快照、Materialization Result / Receipt 同一事务可见。
- Admission Closure Seal：单个 Closure 的 Attempt、封存 Read Set、Verification Assessment、Admission Decision（仅 DECIDED 时）和最低 Audit 在一个 Closure-local 权威事务中全有或全无；不同 Closure 可以独立并行封存。
- Admission Batch Seal：只有 Final Candidate Bundle Seal 中每个 Closure 都已有唯一终态 Attempt 后，Admission Coordinator 才在单独事务中以 Batch Idempotency Key / canonical Request Digest 封存一个完整、不可变 Admission Batch Result。该事务只引用已有终态 Attempt / Decision，不创建、修改或重新解释任何 Closure Decision。
- Publication：Snapshot、Member / Dependency Manifest、Identity Index、Publication Outcome / Receipt 与 CURRENT CAS 保持规定的提交边界。
- Publication Attempt：Publisher-owned Record 以唯一 Idempotency Key 线性化；Cancel 的 `PREPARED → NOT_PUBLISHED` 与发布事务的 `PREPARED → PUBLISHED` CAS 只有一方成功，不设置平行 Gate。
- Schema Adoption / Evolution：只有完整目标 Snapshot Publication 成功才改变 CURRENT，不原地迁移已发布 State。

大 Payload 可以先写 Staging，再以 `Durable Content Receipt` 绑定 Authority Attempt、Request Digest、Content Digest / Length 和 Provider Generation。权威事务只引用校验通过的 Receipt；未被任何未解析 Attempt 引用的 Staging 字节可以按 Attempt 终态做本地 orphan cleanup。该 cleanup 不删除已经提交的正式知识，不需要通用 Retention Graph。

Admission Batch 封存前必须机械证明 Final Seal 的 Closure / Attempt 集合与 Batch 条目双向相等，且每个 Closure 恰好一个终态。相同 Batch Key / Digest 返回原 Batch；相同 Key、不同 Digest 冲突。若进程在部分 Closure 已封存、Batch 尚未封存时崩溃，恢复后从同一 Final Seal 和已提交终态 Attempt 幂等重建 Batch；恢复过程不重新运行审核、不改变 Decision，也不暴露部分 Batch。只要仍有 Closure 非终态，就明确返回 Batch 尚不可封存，而不是生成 `INCOMPLETE` 权威 Batch 冒充完成。

### 6.2 可靠事件

影响 Publication、Projection 兼容事件、Telemetry 或其他下游消费者的权威事件，由对象 Owner 通过同事务 local Outbox / Emission Marker 产生。消费者按 Event ID / Authority Revision 幂等；Event 不替代权威 Outcome，也不要求 Telemetry 扫描 Repository。

### 6.3 KNW-STORE-RECOVERY-01

当前只支持同一持久库、没有时间回退和主写身份变化的普通进程重启：

1. 从本地事务日志、Attempt、Receipt、Snapshot 和 Idempotency Tombstone 恢复。
2. Evidence Finalize 与 Publication 都不持久化 `COMMITTING`：事务提交后直接出现 SUCCEEDED / PUBLISHED，回滚后保持可重试前态或已有确定失败终态。调用方超时只查询同一 Attempt。
3. 缓存、Projection、Telemetry、进程日志和模型输出不能补齐权威缺口，也不能创建第二个 Attempt。

当前没有独立于 Knowledge Store 的单调 Store Generation / Recovery Authority，因此不能把 `HEALTHY / QUARANTINED` 等状态写回同一数据库来证明该数据库没有回退。部署只允许把已经配置且由部署运维保证为同一持久历史的数据库交给本版运行；启动或运行中发现权威记录不一致、恢复点回退、主写替换或历史连续性无法确认时，当前实例必须 fail-stop，并使 readiness / Knowledge API 不可用。它不写入新的知识领域状态、不修改 KnowledgeScope，也不从 Projection、Telemetry 或模型补齐缺口。

当前 Contract 不传播 Store Incarnation / Recovery Generation，也不声称支持 PITR、跨主切换、旧 Worker 隔离或 fail-stop 后在原身份上继续运行。恢复同一事务历史可以重启；不能证明同一历史时只能新建明确初始化的部署身份，或先完成包含外部 Generation Authority、旧 Worker Fence、跨 Owner Confirmation 和迁移方案的非连续恢复专题设计。Repository 返回通用 unavailable / integrity failure，不要求上游依赖 Persistence 的隐藏可用性状态。

## 7. 未来 Retention / Cleanup 启用边界

### 7.1 当前关闭策略

当前正式知识采用静态 `NO_PHYSICAL_CLEANUP` Strategy：

- 已提交 Evidence、State、Admission、Snapshot、Outcome、Receipt、Identity Continuation 和最低 Audit / Idempotency 数据不做物理删除。
- 产品 / 权限政策可以在打开新 Session 时拒绝某个 exact Snapshot，但不创建 Snapshot Retention / Retirement State，底层字节仍保留；读取拒绝不授权物理 GC。
- 因为没有并发删除，正式读取不取得 Cleanup Lease、Operation Guard、MVCC Pin、Protection Epoch 或 Integrity Watermark。
- 当前不存在 Cleanup 公共 Contract、Plan / Fence / Sweep Worker；任何删除已提交知识字节的实现都不符合本版设计。

Source Artifact / Payload 仍可由 Source Integration 的本地 Retention 策略淘汰。正式 Evidence 默认保存足以独立复核的最小精确快照，因此 Knowledge Store 不依赖 Source Payload 永久存在。

### 7.2 未来启用边界

只有容量、合规删除或存储成本达到明确阈值并决定删除已提交知识字节时，才建立 Retention / Cleanup 专题设计。该设计至少必须保证：

- CURRENT、可读 Snapshot、正式跨 Scope 依赖、活动读取、未解析 Publication / Recovery、Identity Continuation 和审计保留不会被删除。
- “没有引用”由完整、可验证的权威闭包证明，不能只依赖缓存反向索引或简单引用计数。
- 新保护与删除资格具有同一线性化边界；检查后不能出现未被观察的新引用。
- 共享物理内容只有全部受保护逻辑 Owner 均退出后才可删除。
- Source Payload 清理仍由 Source Integration Owner 决定，Knowledge Engine 不能直接删除。

这些是不变量，不是当前 Protection Graph、Lease 或 Cleanup 状态机的预定义字段。

## 8. 未来 Projection 启用边界

### 8.1 当前关闭策略

当前 `Projection Strategy = DISABLED`：

- 不创建 Projection Definition Registry、Instance、Build Generation、Activation Binding、Query Lease 或专用 Cache。
- Knowledge Use 和 Semantic View 直接读取 exact Snapshot 的权威 Repository。
- 查询超出资源或性能边界时返回明确 `QUERY_LIMIT_EXCEEDED | PROJECTION_NOT_ENABLED`，不能读取旧索引、相近 Snapshot 或未验证缓存补答。

### 8.2 未来兼容边界

只有权威查询在代表性负载下无法满足已批准的性能、容量或隔离目标时，才建立 Projection 专题详细设计。未来实现不得改变以下边界：

- Projection 非权威、可全部删除重建，不进入 Snapshot 或知识依赖。
- 每个结果精确绑定 Projection Contract、Scope、exact Snapshot、Knowledge Schema、Context / Coverage 与权限隔离边界。
- Staging / 未验证结果不可见；失败或陈旧结果不能服务新 Snapshot。
- 返回前必须从 Knowledge Engine 权威回读正式引用并重验 Context / Coverage / Conflict / Classification；Projection 不能扩张语义。
- 无 exact 合格 Projection 时等价回退权威读取，或明确不可用；不回退到“最近实例”。

当前不冻结 Definition 字段、Instance 状态、Provider SPI、激活算法、Query Lease 或 Cache Key；它们由触发后的真实查询约束决定。

## 9. 分片与物理演进

当前单体部署使用逻辑 Owner 与 Repository Port 保持边界，不提前选择全局分片键、跨库事务、复制拓扑或独立服务。

若单库容量 / 吞吐、跨 Scope 自治或团队所有权产生可复现瓶颈，后续设计可以按 KnowledgeScope / Partition 演进，但必须保持：

- Snapshot Publication / CURRENT 在其明确原子边界内成立。
- 跨 Scope 正式引用只绑定 exact 已发布 Snapshot。
- Application、Agent、Semantic View 和 Model Gateway 不因物理拆分获得直接写权。
- 跨分区失败明确暴露，不以最终一致缓存冒充原子发布。

## 10. AI Native 与平台责任

模型可以帮助提出查询计划、物理索引建议和容量解释，但当前权威 Repository 读写不依赖模型。未来 Projection 使用模型时，模型只生成可验证 Proposal；正式引用、Snapshot / Schema 坐标、权限、Coverage 和权威回读仍由平台控制。

模型能力增强不取消 Authority Store、事务、Idempotency 或 Snapshot。模型退化也不触发存储格式变化或从缓存恢复正式知识。

## 11. 失败、重试与恢复语义

| 失败类别 | 处理 |
|---|---|
| IDEMPOTENCY_CONFLICT | 同 Key 不同 Digest；拒绝，不覆盖原 Attempt / Result |
| EXPECTED_REVISION_MISMATCH | CAS 失败；调用方基于当前权威状态重建请求 |
| DURABLE_CONTENT_UNPROVEN | 不提交引用该 Staging Content 的 Evidence / Snapshot |
| AUTHORITY_OUTCOME_UNKNOWN | 保持原 Attempt 未解析并恢复；不猜测失败、不换 Key 重做 |
| ADMISSION_BATCH_NOT_READY | 至少一个 Closure 尚无唯一终态；不封存 Batch，也不把已有 Decision 拼成部分结果 |
| ADMISSION_BATCH_IDEMPOTENCY_CONFLICT | 同 Batch Key 对应不同 Final Seal / Request Digest；拒绝覆盖原 Batch |
| AUTHORITY_RECORD_INCONSISTENT | 当前操作失败并触发实例 fail-stop；不写同库自证状态、不改 Scope，也不从 Projection / Telemetry 补齐 |
| RECOVERY_UNSUPPORTED | 不在原部署身份继续服务；只能证明并恢复同一历史、新建明确初始化的部署，或先完成专题设计 |
| OPTIONAL_CAPABILITY_NOT_DEFINED | Cleanup / Projection 请求不进入本版运行契约；使用权威查询或返回产品能力不可用 |
| QUERY_LIMIT_EXCEEDED | 返回 Coverage / Cursor / 限制；不扩大预算、不读取近似旧结果 |

## 12. 可观测性与敏感信息

传播 Scope、Snapshot、Schema、Repository Operation、Transaction / Attempt、Request Digest、Result / Receipt 和 Correlation Reference。记录事务 Outcome、CAS / Idempotency 冲突、Staging 字节、权威查询覆盖 / 分页、Projection / Cleanup 禁用命中和 Recovery Unsupported。

Telemetry 不复制 Evidence Observed Content、正式命题、Candidate、凭据或数据库 Payload。审计详情只通过 Owner 的受控 Reference 读取。

## 13. 拟议不变量

1. Knowledge Engine 是正式知识唯一写 Owner；共享数据库不产生共享写权。
2. 不可变知识对象不原地改写；可变 Binding 只通过单调 Revision / CAS 指向不可变对象。
3. 同一 Idempotency Key 永久绑定一个 Request Digest 和原 Outcome；调用超时不是失败证明。
4. Snapshot / CURRENT、Evidence Materialization、Admission 和 Publication 保持各自定义的原子边界。
5. 当前正式知识字节 append-only；逻辑退休不授权物理删除，读取不承担未启用 Cleanup 的 Lease / Fence。
6. 当前 Projection 关闭；全部正式查询从 exact Snapshot 的 Authority Repository 返回。
7. Projection 未来仍非权威、精确绑定 Snapshot / Schema 并在返回前权威回读。
8. 当前只支持同一持久历史的事务恢复；非连续恢复失败关闭而不是扩散未经设计的 Generation 协议。
9. Source Integration 继续拥有 Artifact / Payload；Knowledge Engine 不直接删除或恢复 Source 内容。
10. 物理分片、Cleanup、Projection 与 Recovery 扩展不能改变逻辑 Owner、正式引用或 Publication 原子语义。
11. Knowledge Authority Store 不拥有 Application Investigation、Capability Evaluation / Activation 或 Resource Policy；只保存其 opaque exact Reference / Digest。
12. Admission Closure Decision 与完整 Admission Batch 使用两个明确事务边界：Closure 可并行原子封存，Batch 在全部唯一终态后单独幂等封存；任何崩溃恢复都不能产生部分 Batch 或改写既有 Decision。

## 14. 验证义务与下游追溯

进入实现前至少验证：

- 同 Key / 同 Digest 恢复原 Result，同 Key / 不同 Digest 冲突；超时重试不重复 Publication / Materialization。
- Evidence、Admission、Snapshot / CURRENT、Identity Index 与 Receipt 的事务故障注入不产生半可见对象。
- 多 Closure 并行审核、部分 Closure 后崩溃和 Batch 封存响应丢失时，只恢复既有 Closure 终态并幂等生成同一完整 Batch；不重跑 Decision、不暴露部分 Batch、不同 Digest 不覆盖。
- Staging 写成功而权威事务失败、进程崩溃或 Outcome 未解析时，orphan cleanup 只删除已证明无权威引用的暂存字节。
- CURRENT 在 Session / Query 期间变化时，读取仍绑定首次 exact Snapshot。
- 已提交知识不会因逻辑退休、缓存空、反向索引缺失或磁盘压力被物理删除。
- Cleanup / Projection 请求在未启用时明确关闭，不创建隐藏 Registry、Worker 或替代查询路径。
- 检测到持久历史回退 / 不一致时实例 fail-stop，且不通过写入同库 Availability 状态伪造连续性；旧 Outcome、Telemetry 或模型猜测都不能继续发布。
- Repository Port 直接越权写、未知 Schema Version、非 canonical Digest 和 Projection 结果冒充权威均被拒绝。
- Knowledge Store 只保存 Application Investigation / Activation / Evaluation / Resource Policy 的 opaque 引用；任何本地复制 current state、推进 Revision 或跨 Owner 直接写均被拒绝。

当前不需要 Demo 决定 append-only、Projection disabled 和非连续恢复 unsupported；它们是删除条件机制后的简单策略。只有代表性负载证明权威查询不满足目标、正式知识物理删除成为真实需求，或部署明确引入非连续恢复时，才建立对应 `DVR-*` / 专题详细设计。

DD-APP-KNOWLEDGE-USE 只能依赖 Authority Read 与上述禁用 / 回退语义，不能依赖尚未启用的 Projection、Cleanup 或 Recovery 内部状态。
