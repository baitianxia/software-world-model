# Software World Model 首个纵向实现切片方案

| 元数据 | 值 |
|---|---|
| Plan ID | SWM-IMP-ITER-001 |
| Status | Product Validation PASS — Local Browser Experience Ready / Production Pending |
| Architecture Baseline | SWM-ARCH@1.2 |
| Detailed Design Guide | SWM-DD-GUIDE@0.1.0 |
| Static Review | SWM-DD-REVIEW-001 |
| Design Acceptance | [SWM-DD-ACCEPT-001](../../detailed-design/governance/Detailed_Design_Acceptance_Record_001.md) |
| Design Baseline | [SWM-DBM-ITER-001-REV-002](../../detailed-design/governance/Design_Baseline_Manifest_Iteration_001_Revision_002.md) |
| Implementation Baseline | [SWM-IBM-ITER-001-REV-002](Implementation_Baseline_Manifest_Iteration_001_Revision_002.md) |
| Current Work Package | WP-7 — 产品验收与本机浏览器体验完成 / 生产启用待决定 |
| Active Readiness Record | [SWM-IMP-DEV-REENTRY-001](Implementation_Development_Reentry_001.md) |
| Delivery Form | 模块化单体；Web Chat + CLI；单一逻辑 ACID Store |
| Runtime Knowledge Path | Formal Knowledge Single Path |

> 本文选择首个交付切片，不改变一般架构和详细设计。所采用的 22 个主题已经接受并由 SWM-DBM-ITER-001-REV-002 固定；两个未采用的条件主题继续保持 `In Review`。旧的 WP-0 实施基线和暂停记录继续作为历史证据。WP-1 至 WP-6 的实现、WP-7离线回归、当前模型接口符合性、六类通用能力评估和两个陌生工程六题产品验收均已完成并通过。模型方案只为本机浏览器体验范围启用，生产发布仍保持关闭。

## 1. 实现目标

实现一个可运行的纵向系统：用户配置一个本地 Git 工程后，可以通过 Web Chat 提出未预编码的软件问题。系统把问题形成 Knowledge Requirement，在 exact Git Revision / Commit / Code Target 边界内通过有界 Tool Loop 调查来源，形成 Artifact、Evidence、Entity、Fact / Inference，经独立知识准入和 Snapshot 发布后，只依赖新 Snapshot 完成逐 Need 充分性判断、Answer Candidate、独立审核和响应交付。

首个切片允许慢，但必须满足：

- 不使用运行时直接源码回答旁路。
- 不用相关但不充分的知识伪造任务完成。
- 不因模型具有隐藏 Tool 或工作区访问能力而获得不可证明的正确答案。
- 对无法证明的内容显式返回 Gap、Conflict、Unknown 或 Application Limitation。
- 在冻结未见任务集上，正确性和任务完成率不得低于同模型、同来源、同授权 Tool 预算的直接来源调查 Agent。

## 2. 用户旅程

### 2.1 配置来源

平台管理员通过 CLI：

1. 创建一个 `SYSTEM` KnowledgeScope。
2. 注册 Local Git DataSource。
3. 使用明确仓库范围 Selector 创建 DataSourceBinding。
4. 查看组合 Management Result；配置成功不自动等同于知识已构建。

### 2.2 Web Chat 知识任务

用户通过 Web Chat 提问，例如：

- “这个 Endpoint 在什么条件下执行哪些主要步骤？”
- “Commit `<exact SHA>` 的 JWT 迁移影响了哪些技术区域？”
- “某项业务规则由哪些代码路径实现，当前有哪些未知或冲突？”

系统动态执行：

`Task Boundary → Requirement → 当前 Snapshot 调查 → Gap → Knowledge Update → 新 Snapshot → 全 Need 重评 → Answer Review → Delivery`

问题没有预编码专用 Builder、固定答案模板或题目专用 View。模型在通用 Contract 内规划与理解，平台控制身份、授权、Lineage、Context、准入、发布、充分性和放行。

### 2.3 CLI 固定用例

CLI 同时提供结构化 Management、Knowledge Update 和 Knowledge Use 命令，用于运维、调试和 Conformance。CLI 不经过 Agent Orchestrator，也不能形成与 Web 不同的知识构建路径。

## 3. 选取的设计切片

每个主题只实现本迭代用户旅程需要的 Contract 子集；未选择的能力继续由详细设计保留，不建立空模块或占位状态机。

| 主题组 | 采用主题 | 本切片范围 |
|---|---|---|
| 共享执行与模型 | DD-X-CAPABILITY-EXECUTION、DD-AI-MODEL-GATEWAY、DD-MGT-CAPABILITY-EVALUATION | Capability / Strategy、资源分配、Authorized Input Manifest、no-tools Adapter、Isolation Receipt、实际模型资格、最小评测与激活 |
| Scope 与来源配置 | DD-KNW-KNOWLEDGE-SCOPE、DD-SRC-DATA-SOURCE、DD-APP-MANAGEMENT | Create / Get Scope、Register / Get Local Git Source、Bind / Get Binding、组合 Result 与幂等 |
| 来源执行 | DD-SRC-SOURCE-ARTIFACT | Local Git `list/search/read/compare`、Commit / Revision / Code Target Resolution、Source Operation、Source / Derived Artifact、Lineage、授权局部读取与最小保留策略 |
| 知识基础 | DD-KNW-REFERENCE-CONTEXT、DD-KNW-SCHEMA-CORE、DD-KNW-CONTEXT-COMPARISON | 单 Schema INITIAL / UNCHANGED、exact Git Revision / Observation Time Context、Branch / Tag Resolution Provenance、确定性同 Context 与受控比较 |
| 知识形成 | DD-KNW-EVIDENCE、DD-KNW-ENTITY、DD-KNW-FACT、DD-KNW-INFERENCE-CONFLICT、DD-KNW-ADMISSION | 自包含 Evidence、技术 Entity、Fact、受控 Inference / Conflict、Candidate 平台重建、独立 Verification 与 Admission |
| 发布与持久化 | DD-KNW-SNAPSHOT-PUBLICATION、DD-KNW-PERSISTENCE | 单 Scope Snapshot、CURRENT、append-only 权威存储、原子发布、exact Snapshot 读取 |
| 更新与使用 | DD-APP-KNOWLEDGE-UPDATE、DD-APP-KNOWLEDGE-USE | Canonical Build Target、Target Coverage、有界 Tool Loop、Publication Acceptance、Requirement / Session / Query、逐 Need Support Proof、Gap 和发布后重评 |
| Web Agent 与响应 | DD-APP-AGENTIC-TASK、DD-APP-RESPONSE-CONTROL | Task Control、动态 Agent 路由、Task Execution、Candidate、独立 Review、Final Authorization 与幂等交付 |
| 运行观测 | DD-X-TELEMETRY-COST | 结构化运行事件、模型 / Tool 用量、估算成本、Correlation 与最小审计索引 |

本切片不采用 DD-KNW-SCHEMA-EVOLUTION；所有 Snapshot 使用同一 Knowledge Schema。DD-SEM-SEMANTIC-VIEW 不作为知识任务前置条件；Agent 使用通用正式知识 Query 和 Sufficiency 完成问题。后续需要稳定的人类 /自动化 View 时再选择该主题。

## 4. 明确不在本切片的能力

- DB、Log、Trace、部署平台和文档空间 Provider。
- 跨 KnowledgeScope Business Domain 聚合。
- Schema Adoption、身份拆分 / 合并和自动 Evolution。
- Projection、物理 Cleanup、向量 / 图 /搜索副本和非连续恢复。
- 独立 Initialization、Evaluation & Learning、Governance 或 Workflow 服务。
- 多租户、SSO、企业级权限治理、HA、灾备和财务级账单核对。
- Provider 托管 Tool、shell、文件、Web、MCP 或 Agent Runtime 访问。
- 运行时直接来源 Agent 兜底、双路径择优或“答不出时直接读源码”。

上述排除项不得用空接口、预留表或假状态机进入代码。稳定 SPI、Reference 和条件启用边界按详细设计保留。

## 5. 实现工作包与顺序

本节采用以下编号规则；通用术语见[文档中心术语和标识约定](../../README.md#2-术语和标识约定)。

| 标识 | 含义 |
|---|---|
| `WP-N` | 第 `N` 个 Work Package。数字表示本计划中的依赖顺序，不表示优先级、进度百分比或必须由不同团队承担。 |
| `WP-0` | 原编码前准备工作包；其冻结结果保留为历史闭包。 |
| `WP-0R` | WP-0 之后的能力契约修订与实施再准入工作包。`R`在本计划中表示 Revision / Re-admission，不是新的生产功能包。 |
| `0R-A…0R-E` | WP-0R 内部阶段。`0R-A`是离线开发准入门禁；`0R-B…0R-E`是后续真实集成、能力验证和生产激活门禁。 |
| `WP-1 Held` | 2026-08-05暂停记录中的历史状态；2026-08-06已仅对离线开发解除。 |
| `WP-NX` | Work Package内部阶段，例如`WP-1A`；数字指所属工作包，字母只表示该包内的迭代顺序。 |
| `WP-1…WP-6` | 在外部调用默认关闭的条件下依次推进的生产代码工作包；前一包退出不自动证明后一包完成。 |
| `WP-7` | 端到端质量与产品门禁；其中真实Provider与产品验收部分必须等待`0R-B…0R-E`。 |
| `SWM` | Software World Model，本系统及其文档标识前缀。 |
| `JWT` | JSON Web Token。本计划用它标识 H-04 的 Commit 影响分析验证题目，不是 Work Package 或代码模块缩写。 |
| `ITER-001` | Iteration 001，首个纵向实现迭代。 |
| `DD` | Detailed Design，详细设计产物前缀。 |
| `IMP` | Implementation，实施计划、基线或实施状态产物前缀。 |
| `ACV` | Architecture Capability Validation，架构能力验证。 |
| `CC` | Conformance Case / Contract Conformance，契约符合性用例。 |
| `CC-ARK-NN` | 方舟Chat Adapter专用Conformance Case编号；与OpenAI Responses的`CC-NT-NN`及JWT Need编号互不替代。 |
| `CE` | Capability Evaluation，模型 / Prompt / Strategy的业务能力评测；CC只证明Adapter契约，两者不共用PASS。 |
| `Validity` | 已封存Evaluation Result当前是否仍能用于新激活的单调状态；`STALE/REVOKED`不能恢复为`VALID`。 |
| `G-01…G-12` | 本计划的强制 Gate（门禁）场景编号。编号表示可追溯身份，不表示执行顺序。 |
| `H-04` | 架构验证问题目录中的第 4 个假设 /题目；本迭代以 JWT Commit 影响分析作为该题目的窄切片。 |
| `DVR` | Design Variance Record，发现公共契约无法表达或约束时登记的设计分叉记录。 |

代码包命名与架构边界对应：`application_services`负责用例编排，`knowledge_engine`负责知识权威状态，`source_integration`负责来源配置与读取，`ai_infrastructure`负责模型隔离调用，`infrastructure`保存SQLite适配器，`interface`保存CLI等入口，`cross_cutting`保存跨模块基础类型。名称描述职责，不授予跨Owner直接写入权限。

工作包状态与其内部测试状态彼此独立。`0R-A Completed`只授权离线开发，不能推导`WP-0R Completed`、Live Conformance PASS、模型Strategy可激活或产品可发布。

### WP-0R：能力契约修订与实施再准入

WP-0 的原始设计基线和 Adapter 选择作为冻结历史保留；当前工作包不是重新讨论一般架构。真实模型能力验证仍通过最小纵向切片完成，但不再阻塞与外部Provider无关的实现工作。

- 保留 22 个 Accepted 详细设计主题和既有 Design Baseline，不用实施 Schema 缺口重开一般架构。
- 先只闭合H-04 JWT Commit影响分析的六个Need，不把H-01、H-02、H-03、H-05或完整语言 /框架语义库放入本次门禁。
- 通过真实no-tools模型、有界Source Tool Loop、Formal Knowledge Single Path和同题Direct Agent对照执行JWT Capability Run；Fixture只能验证机械门禁。
- 如果架构切片通过，再选择首个production纵向切片，并只冻结该切片实际实现的类型、摘要和Conformance；后续切片在各自编码前迭代冻结。
- 历史33项映射继续作为需求风险目录，不作为开始首个纵向实现的整包前置条件。

离线开发准入条件：JWT切片Formal Contract静态闭合；Revision 002 的13个Mechanical Conformance Case和no-tools Adapter离线机械Oracle通过；外部调用默认关闭，Fixture不能签发Live资格。该条件已经满足，允许进入WP-1离线开发。

真实集成与生产激活条件：no-tools Adapter真实边界通过；完整JWT Capability Run证明六个Need在来源关闭后不低于同题Direct Agent；失败没有使用源码直答、双路径或Fixture掩盖；随后形成新的Implementation Baseline。上述条件继续阻止真实模型Strategy激活和生产发布，但不追溯否定已完成的离线开发。

当前进度：

| WP-0R Gate | 状态 | 权威依据 / 待形成产物 |
|---|---|---|
| 采用主题接受 | Completed | [SWM-DD-ACCEPT-001](../../detailed-design/governance/Detailed_Design_Acceptance_Record_001.md) |
| 精确设计基线 | Completed | [SWM-DBM-ITER-001-REV-002](../../detailed-design/governance/Design_Baseline_Manifest_Iteration_001_Revision_002.md) |
| no-tools Model Provider Adapter 选择与 Conformance Fixture | OpenAI历史Fixture保留；Ark Coding Plan @7 Profile、12 Case运行器、安全Result封存与资格加载已实现；Live CC 12 / 12 PASS | [OpenAI no-tools Adapter Profile](contracts/ITER-001-OpenAI-No-Tools-Adapter-Profile.md)、[Ark Chat Adapter Profile](contracts/ITER-001-Volcengine-Ark-No-Tools-Adapter-Profile.md)、[CC-ARK-CHAT-NO-TOOLS-001](conformance/CC-ARK-CHAT-NO-TOOLS-001.md) |
| 历史 INITIAL Knowledge Schema | Completed — Frozen Historical | [Iteration 001 INITIAL Knowledge Schema](contracts/ITER-001-Initial-Knowledge-Schema.md)；`iter-001.initial.1` 不满足当前能力目标 |
| 历史 Local Git Provider Contract | Completed — Frozen Historical | [Iteration 001 Local Git Provider Profile](contracts/ITER-001-Local-Git-Provider-Profile.md) |
| 宽范围 Provider / Rule Pack / Schema 候选 | Withdrawn Draft；历史`33 / 33`已撤回 | [Provider Profile Revision 002](contracts/ITER-001-Local-Git-Provider-Profile-Revision-002.md)、[Foundational Semantics Rule Pack](contracts/ITER-001-Foundational-Software-Semantics-Rule-Pack.md)、[Schema Revision 002](contracts/ITER-001-Initial-Knowledge-Schema-Revision-002.md)、[Formal Mapping Audit 002](../../validation/architecture/Architecture_Capability_Formal_Mapping_Audit_002.md) |
| JWT validation-only Formal Contract | Revision 002 candidate；13 / 13 Mechanical Conformance Passed | [JWT Formal Contract Revision 002](contracts/ITER-001-JWT-Validation-Formal-Contract-Revision-002.md)、[JWT Capability Slice 002](../../validation/architecture/Architecture_Capability_Validation_Slice_JWT_002.md) |
| JWT Capability Run | @7 Direct Oracle已密封；七角色World、跨模型Comparison与CE均PASS；激活未执行 | [JWT Capability Run Harness 001](JWT_Capability_Run_Harness_001.md)、[JWT Capability Run Result 001](JWT_Capability_Run_Result_001.md) |
| 跨主题错误分类 | Completed — Frozen | [Iteration 001 Shared Error Classification](contracts/ITER-001-Shared-Error-Classification.md) |

WP-0 曾按`SWM-IBM-ITER-001-REV-002`关闭文档门禁；后续真实验证证明现有路径不能保持Direct Agent能力，因此生产激活被暂停。历史Formal Mapping Audit 002已经失效。随后`SWM-IMP-DEV-REENTRY-001`解除离线编码限制，现已完成WP-1至WP-6实现及WP-7离线回归。Revision 002的13个机械符合性用例、真实模型接口12项验证、历史专项运行、当前六类通用能力评估和两个陌生工程六题产品验收均已通过。各层验证仍不能互相替代，生产启用继续由独立的显式决定控制。

#### WP-0R 内部分阶段迭代

| 阶段 | 交付物 | 验收条件 | 当前状态 |
|---|---|---|---|
| 0R-A 机械闭包 | Revision 002 Formal Harness；no-tools Adapter、Envelope校验、Recording Transport与离线反例 | JWT `13 / 13`；Adapter离线CC覆盖全部12类机械Oracle；全量回归通过；不产生Live PASS | Completed |
| 0R-B Live Adapter Conformance | exact Model / Prompt / Output Schema /网络捕获配置；不可变CC Result | `CC-ARK-01…12`全部PASS，Secret不入结果，Result摘要和失效依赖完整 | Completed — @7 Live CC 12 / 12 PASS |
| 0R-C Oracle与Run冻结 | 独立Direct Agent结果、逐Claim Oracle、七角色Authorized Input Matrix和Run Manifest | 在任何SWM Source Operation前完成冻结；Oracle与Runtime物理、逻辑隔离 | Completed — Oracle Sealed / Run Configuration Frozen |
| 0R-D 完整JWT Capability Run | 七角色真实模型轨迹、三阶段Snapshot、逐Obligation充分性、来源关闭回答、独立跨模型Review与CE | obligation missing / extra / duplicate均为0，无实质错误，全部隔离、Delivery、Comparison与CE Gate PASS | Completed — World / Comparison / CE PASS；历史两轮FAIL保留 |
| 0R-E 生产激活再准入 | 真实集成Hold解除记录；只授权首个production切片的新Implementation Baseline | 0R-B至0R-D全部PASS；G-12产品Holdout通过；失败证据不被Fixture、总分或旁路掩盖 | Product Holdout PASS / Explicit activation decision pending |

### WP-1：单体骨架与权威存储

当前只执行离线范围。模型Capability / Strategy状态可以实现，但真实Strategy必须保持未配置且不可激活；测试只使用不能签发Live资格的test double。

离线实现栈采用Python 3.11及以上版本和标准库SQLite。SQLite作为Iteration 001单进程模块化单体的单一逻辑ACID Store；Owner仍通过各自Repository Port独占写入。当前不引入Web框架、ORM、Projection、分布式事务或独立服务；若后续实测约束要求更换数据库产品，必须保持Repository契约、事务语义和迁移证据。

- 建立模块化单体内的 Interface、Application Services、Source Integration、Knowledge Engine、AI Infrastructure 与 Cross-cutting 包边界；本切片不创建 Semantic View 空模块，也不拆服务。
- 建立单一 ACID Store 与各 Owner Repository Port。
- 实现 Scope、DataSource、Binding、Capability / Strategy Activation 和 Resource Allocation 的最低状态。
- 实现稳定 ID、Revision、Digest、Idempotency Key、Correlation 和 local Outbox 基础类型。

退出条件：不同 Owner 不能绕过公开 Port 写入；幂等、Revision 冲突和基本恢复测试通过。

#### WP-1 内部分阶段

| 阶段 | 交付物 | 验收条件 | 当前状态 |
|---|---|---|---|
| WP-1A Foundation / Scope | canonical Digest、稳定ID、Revision、Idempotency、Correlation；SQLite事务；KnowledgeScope Repository、State Assertion和owner-local Outbox | Scope创建/修订/退休、幂等冲突、Revision冲突、回滚及Outbox原子性测试通过 | Completed — 11 / 11 tests |
| WP-1B Source Configuration | DataSource、Binding、Provider配置Port及Source Integration Repository | 永久唯一键、Selector等价、Scope Assertion、状态迁移和退休Tombstone测试通过 | Completed — 7 / 7 tests |
| WP-1C Capability / Resource | Capability与Strategy注册、默认禁止真实模型激活、Resource Allocation预留/绑定/结算 | 未配置模型不能激活；父子预算不超分配；同Key恢复且不同Digest冲突 | Completed — 10 / 10 tests |
| WP-1D Management / Recovery | 组合Management Attempt / Result、Owner调用恢复和基础CLI入口 | 部分成功、Outcome Pending、取消、重试和同一逻辑Result恢复测试通过；WP-1全量回归通过 | Completed — 10 / 10 tests |

WP-1离线实现状态：`Completed — 38 / 38 focused tests`。

### WP-2：Model Gateway 与 Local Git Source

- 实现 Authorized Input Manifest、Prompt Rendering、Provider Request Digest、Isolation Receipt、Model Call Record 和 post-call eligibility。
- 实现 Local Git DataSource Provider、Connector Provider 与 `list/search/read/compare` Tool。
- 实现 exact Commit / Comparison / Path / Java Symbol Target Resolver；短 SHA、重载和跨模块同名失败关闭。
- 实现 Source Operation、Artifact / Lineage、局部读取、预算、分页 /截断和 Observation。

退出条件：模型无法访问 Manifest 之外的文件、工作区、Web 或 Tool；所有来源读取均由平台授权、执行和记录。

离线实现状态：`Completed — 35 / 35 focused tests`。除OpenAI Responses no-tools Adapter外，已按配置新增火山方舟OpenAI-compatible Chat Completions Adapter、安全Secret Reference、Provider状态/探测CLI、closed Structured Output复验、直连HTTPS代理隔离、系统CA回退、安全Provider错误投影和模型身份/Usage Eligibility；两类Adapter默认仍为`OFFLINE_FIXTURE`，不能签发真实Provider生产资格。

### WP-3：正式知识构建与发布

- 实现 INITIAL Knowledge Schema 与 Context canonicalization。
- 实现 Artifact → Evidence → Entity / Fact Candidate；Inference 只引用已发布正式前提。
- 实现 Candidate Contract 校验、Knowledge Verification、Admission Batch、Snapshot Manifest 与单 Scope 原子发布。
- 实现 append-only Authority Store 和 exact Snapshot Read。

退出条件：Evidence 越界、Entity / Fact 悬空引用、Inference 非正式前提、审核失败和发布并发均不能污染 CURRENT。

离线实现状态：`Completed — 6 / 6 focused tests`。

### WP-4：任务驱动 Knowledge Update

- 实现 Build Objective、Canonical Build Target、Resolution Receipt、Build Intent 和 Target Coverage Map。
- 实现 Source Information Need、no-tools Tool Proposal、Application Authorization、Tool Step、Observation 和有界停止。
- 实现 Candidate / Admission / Publication Coverage 闭包和 Publication Acceptance。
- 实现 Update Result 与 Delivery Assertion。

退出条件：给定未预编码 Commit 或 Endpoint，系统可以渐进找到材料并发布相关正式知识；无关同类型知识、空选择、越界和预算耗尽不能假通过。

离线实现状态：`Completed — 4 / 4 focused tests`。当前离线执行使用通用确定性调查策略和字面Evidence Builder；真实模型Tool Proposal与Candidate质量属于待执行的Capability Evaluation，不由此状态替代。

### WP-5：Knowledge Use 与逐 Need Sufficiency

- 实现 Task Boundary、Requirement Revision / Fidelity、Need / Joint Constraint / Obligation Manifest。
- 实现 exact Snapshot Read Session、正式知识 Query、Read Set 和 Cursor。
- 实现独立 Sufficiency Attempt、Need Support Proof、Counterexample / Conflict / Unknown / Limitation 和机械聚合。
- 实现 Gap Resolution 后 exact Snapshot 重绑定和全部 Need 重评。

退出条件：每个 SATISFIED Need 都有同一 Snapshot 可重建 Proof；任一缺口都不能被 Answer Draft 补写。

离线实现状态：`Completed — 3 / 3 focused tests`。

### WP-6：Web Task、Answer Review 与交付

- 实现 Conversational Task Control、Agent Capability Catalog、Orchestrator Proposal、Delegated Grant 和 Application Call Record。
- 实现 Task Execution Agent 的通用 Knowledge Use / Update 规划。
- 实现 Answer Candidate / Claim / Coverage Manifest、独立 Reviewer、Review Matrix、Final Authorization 和 Logical Delivery。
- 实现取消、副作用 Outcome Pending、发送 Claim 和 Adapter Receipt 收口。

退出条件：Agent 无法直连 Core；Reviewer 从权威 Owner 重读依据；未审核或陈旧 Candidate 不能发送；同一请求不产生第二份正文。

离线实现状态：`Completed — generic task path implemented / activation held`。除loopback JSON/HTTP的Knowledge Update、Knowledge Query和Web来源Task Query入口外，现已实现可注入的自然语言Requirement规划与隔离保真复核、受控Source Proposal、source-grounded Fact Proposal/Review、语义Need Sufficiency、source-closed Answer Draft和语义Answer Review。自然语言任务可从精确Snapshot开始；初次评估存在Gap且调用方已提供精确调查授权时，系统执行一次受控Knowledge Update，在新Snapshot上重新评估全部Need后才形成Candidate。模型调用、Assessment、Candidate、Review和Authorization均支持原逻辑恢复；同一任务不能在重试时更换Snapshot、Requirement或正文。六个模型职责以共同Implementation Digest和同一当前Qualification Proof绑定，Generation与Review使用不同职责标识和独立调用。`/v1/tasks/prepare-answer`只暴露已审核和授权但尚未声明外部Delivery的结果。平台会重验精确Target、Read Set、Support Proof和Formal Reference；模型不能直接执行来源工具或自由写入最终Claim。当前六类职责通用能力评估和新产品验收均已通过；默认组合根仍不自动激活，只有显式生产决定才能启用。实现边界见[通用模型任务运行链路实施记录 001](General_Model_Task_Runtime_001.md)。

### WP-7：端到端质量与产品门禁

- 建立 Contract Conformance、故障注入和 Capability Evaluation 套件。
- 冻结至少两个未参与开发调试的 Git 工程和未见任务集，覆盖 Structure、Behavior、History 以及能够从正式依据成立的 Business 语义。
- 使用同一基础模型、同一来源、同一总 Tool / Token 预算运行 SWM 与直接来源调查 Agent 对照；对照 Agent 只在测试 Harness 中存在。
- 记录正确性、任务完成率、关键证据覆盖、Gap 诚实性、延迟和成本。

退出条件：全部强制 Conformance 通过；SWM 正确性和任务完成率不低于直接来源调查基线。若未达到，保持迭代未验收并回到 Capability / Contract 诊断，不把直接 Agent 接入生产路径作弊。

当前质量状态：`production 288 / 288；historical demo 121 / 121；当前六类通用能力真实执行与Codex独立复核PASS；两个陌生工程六题产品验收PASS；本机浏览器体验READY；生产启用NOT RUN`。命令行、本地浏览器、本地接口、运行记录、模型适配器、完整任务验证和能力评估权威状态机具备功能验收证据；通用模型职责、可恢复任务链、经独立复核的解释性正式知识、候选召回、分职责有限修正、重复正文去重、无预设判断的复核表、完整能力资格登记、逐任务产品对照、只写一次的结果材料和双证明启动门禁均已有边界测试。产品验收记录见[新一轮未见项目验收输入 002](Product_Holdout_Suite_002.md)，浏览器体验见[本机浏览器聊天体验说明 001](Browser_Chat_Experience_001.md)。本轮工程实现和产品门禁已经完成；两类证明都有时效，生产启用是独立的部署决定，当前未执行。

## 6. 强制验收场景

| Gate | 场景 | 必须结果 |
|---|---|---|
| G-01 no-tools | Manifest 外放置已知文件名、路径和秘密片段 | Provider 调用期间无读取通道；输出无法包含运行时偷读内容；平台保存可核验 Receipt |
| G-02 模型漂移 | 请求模型与 actual fingerprint / Adapter 不在 Qualification 范围 | Capability Owner 不封存任何生产领域结果 |
| G-03 canonical target | 短 SHA 多解、同名重载、同路径 Controller | 明确歧义或失败；不扩大为全仓库 |
| G-04 target coverage | exact Commit 问题只存在无关 `HISTORY_IMPACT` | Update / Sufficiency 均不能把它当作目标覆盖 |
| G-05 bounded loop | Planner 重复动作、无新 Observation、预算耗尽 | 受控停止并披露未完成范围，不生成完整 Coverage |
| G-06 knowledge admission | Fact 超出 Evidence、Inference 使用 Candidate / Artifact 前提 | Candidate 被拒绝，旧 CURRENT 不变 |
| G-07 per-Need sufficiency | Commit 已知但 JWT 影响区域只覆盖一部分 | 未覆盖 Need /枚举 Coverage 形成 Gap，整体不是 SUFFICIENT |
| G-08 conflict/context | 代码与文档规则不同或 Branch / Deployment Context 不可组合 | 保留独立 Fact；只有正式 Conflict 才标注冲突；不可组合时不拼接 |
| G-09 answer review | Candidate 增加正式命题未蕴含的因果、唯一性或确定性 | Review 不 APPROVED |
| G-10 stale delivery | Review 后 Snapshot Session、Task Revision 或权限变化 | 当前重验拒绝发送旧正文 |
| G-11 idempotency | 来源调用、Publication、Application Command 或发送在响应丢失后重试 | 只恢复原 Attempt / Key，不产生重复副作用或第二响应 |
| G-12 product baseline | 冻结未见任务集对照直接来源调查 Agent | SWM 正确性与任务完成率达到或超过基线，否则不验收 |

## 7. 测试分层

| 测试类型 | 验证内容 |
|---|---|
| Unit / Property | Canonicalization、Digest、状态迁移、集合双向覆盖、Context 与身份不变量 |
| Contract Conformance | Provider / Adapter / Repository / Tool 是否符合已 Accepted Contract |
| Fault Injection | dispatch、取消、CAS、崩溃恢复、Outcome Unknown、Publication 与 Delivery 竞态 |
| Capability Evaluation | Requirement、Tool Planning、Artifact Processing、Candidate、Sufficiency、Drafting、Review 的模型质量与退化 |
| End-to-End | 单路径从配置来源到审核后回答，以及 Gap /Conflict /失败路径 |
| Product Holdout | 与同条件直接来源调查 Agent 比较正确性和完成率 |

Demo 是非生产的架构能力验证 Harness：它回答“当前方案在给定 Contract 下是否具备所需承载、约束和失败关闭能力”。为隔离变量，Demo 可以使用确定性 Capability Fixture / Contract Driver 生成 Candidate；这不证明真实模型能在陌生工程中生成同等 Candidate，也不能计入 Capability Evaluation。

真实模型的 Requirement 理解、Tool Planning、Candidate 生成、审核质量和模型变化退化由 Capability Evaluation 独立验证。模型质量不足不会自动变成架构问题；只有 Demo 或 CE 暴露公共契约无法表达、平台无法约束、或正式单路径无法恢复已有语义时，才登记新的 `DVR-*` 设计分叉。Demo Harness 不进入生产路径，也不得成为答案阶段直接读取来源的旁路。

## 8. 完成定义

当前离线实现、模型接口符合性、六类通用能力评估、两个陌生项目六题产品验收和本机浏览器聊天体验均已完成并通过。历史失败结果继续保留用于追溯，不再适用于当前实现。`local-browser`只授权同机人工体验，不等于生产发布；当前证明过期或实现、模型、接口配置变化后必须重新评估并创建新的限定范围启用记录。

本迭代只有同时满足以下条件才完成：

1. Design Baseline Manifest 中全部主题版本在编码前已经 `Accepted`。
2. G-01 至 G-11 全部通过，无生产直接来源回答旁路。
3. 端到端任务的每个 Answer Claim 都能回放到同一 Snapshot 的正式知识或不可变 Application Result。
4. 所有 Gap、Conflict、Unknown、权限和执行限制如实披露。
5. Adapter / Connector Conformance 和模型 Capability Evaluation 结果可按 exact 版本追溯。
6. G-12 产品基线通过；否则保留失败结果并继续迭代，不能宣称该切片可用。
7. 实际实现没有引入未记录的跨 Owner 写入、新顶层模块、Projection、双路径或题目专用逻辑。

后续迭代在选择新的 Provider、Semantic View、跨 Scope、Schema Adoption 或平台自我提升能力前，先完成对应详细设计评审和新的独立实施方案。
