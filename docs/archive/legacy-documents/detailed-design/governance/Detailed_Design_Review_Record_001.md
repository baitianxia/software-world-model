# Software World Model 详细设计静态评审记录 001

| 元数据 | 值 |
|---|---|
| Review ID | SWM-DD-REVIEW-001 |
| Review Type | Static Contract Review |
| Review Date | 2026-08-03 |
| Architecture Baseline | SWM-ARCH@1.2 |
| Detailed Design Guide | SWM-DD-GUIDE@0.1.0 |
| Scope | `detailed-design/` 当前全部主题文档 |
| Status | Completed |
| Design Validation Demo | Not Required |

> 本记录证明本轮执行过哪些静态检查、发现了什么以及如何处置，不替代概要架构、主题详细设计、ADR、实现 Conformance 或 Capability Evaluation。

## 1. 评审目标

本轮依次检查：

1. 主题是否按稳定责任、权威所有者、生命周期和公共契约划分。
2. 主题依赖是否存在缺失、循环或反向拥有上游状态。
3. no-tools Model Provider、Canonical Build Target、逐 Need Sufficiency 和有界 Source Tool Loop 是否形成端到端失败关闭链。
4. 每个主题是否说明职责、非职责、对象、状态、失败、并发、模型边界、扩展条件和验证义务。
5. 代表性端到端场景能否只沿正式路径完成，不依赖运行时直接读取来源或答案文本补写知识。

## 2. 主题边界发现与处置

| Finding | 原问题 | 处置 | 架构影响 |
|---|---|---|---|
| BR-001 | `KnowledgeScope 与 Data Source Binding` 同时包含 Knowledge Engine、Source Integration 和 Application Services 三个 Owner | 拆为 `DD-KNW-KNOWLEDGE-SCOPE`、Source Integration 内的 DataSource / Binding Contract，以及 `DD-APP-MANAGEMENT` | 对齐既有所有权；不新增顶层模块 |
| BR-002 | Knowledge Use 文档同时拥有 Semantic View Engine Contract | 新建 `DD-SEM-SEMANTIC-VIEW`；View 使用中立 Read Boundary，不反向读取 Application Session | 对齐 Core Capability 边界 |
| BR-003 | Agentic Task 文档同时拥有 Conversational Task Control 与 Response Control 两套状态 | 新建 `DD-APP-RESPONSE-CONTROL`；两者只交换不可变 Result / Assertion | 对齐 Application Layer 内部权威边界 |
| BR-004 | Persistence 主题 ID 暗示 Projection 已启用 | 改为 `DD-KNW-PERSISTENCE`；Projection / Cleanup / 非连续恢复继续保持条件关闭 | 消除误导，不增加 Projection Module |
| BR-005 | 横切执行主题拥有的通用 Result Delivery Assertion 使用 `APP-*` 名称 | 改为 `X-RESULT-DELIVERY-ASSERTION-01` | Contract 名称与 Steward 一致 |
| BR-006 | 基础 DataSource / Binding 配置被 Source Operation / Artifact Processing 的模型执行依赖阻塞 | 新建 `DD-SRC-DATA-SOURCE`；基础配置可确定性成立，执行主题在其上扩展 Connector / Artifact Contract | 消除适用性耦合，不新增顶层模块 |

Source Integration 中的 Connector Layer 与 Artifact Processing Layer 保留独立内部接口和 Strategy，但仍由同一主题管理：它们共享 Source Integration Owner，且 Operation Observation、Artifact Identity、Lineage、授权读取和 Retention 共同形成下游可复核闭包。当前没有独立所有者或独立发布生命周期，不以代码层次差异为由继续拆分。

## 3. 依赖与所有权检查

静态检查结果：

- 截至本记录完成时，`detailed-design/` 共 24 份主题文档，与总纲 24 条目录记录的 ID、路径、版本和状态逐项一致。
- 截至本记录完成时，123 条基础依赖和 12 条条件依赖均指向存在且版本一致的主题；基础依赖图无循环，条件依赖没有形成反向状态所有权。
- 截至本记录完成时，132 个公共 Contract 均有且仅有一个 Owner；主题文档中出现的 Contract 标识均能解析到该 Owner。
- 对当时的概要架构、详细设计、ADR、静态评审和实施方案共 30 份文档执行结构检查，本地链接、标题层级与代码围栏均有效。
- Knowledge Engine 不直接访问 Data Source；Source Integration 不生成 Evidence / Entity / Fact / Inference；Agent 不直接访问 Core Capability；Semantic View Engine 不读取 Application Repository；Task Control 与 Response Control 不互写状态。
- 模块化单体和单一 ACID Store 只简化物理事务，不改变逻辑写入所有权。

## 4. 四条可信链复核

### 4.1 no-tools Model Provider

链路为：Authorized Input Manifest → Provider Request Digest → 分派前 Isolation Receipt → `NO_EXTERNAL_ACCESS` 调用 → actual Model / Adapter / Receipt post-call eligibility → Capability Owner 领域校验。

隔离不成立、Adapter Conformance 过期、隐藏上下文不可关闭或 post-call 身份失配时，不封存 Proposal、Candidate、Assessment、Application Result、Answer 或生产缓存。事后 Tool Event 检查、提示词禁止、空目录和只读工作区均不能替代分派前隔离。

结论：设计闭环成立；真实 Provider 是否满足该 Contract 属于 Adapter Conformance，不是待决架构方案。

### 4.2 Canonical Build Target

链路为：Build Objective / Requirement Gap → exact Source Target Resolution Receipt → Canonical Build Target / descendant discovery boundary → Build Intent → Target Coverage Map → Source Operation / Artifact → Candidate Disposition → Publication Manifest Member。

短 SHA、Branch、同名或重载方法、同路径 Controller 和模型自报目标都只是 Proposal。歧义、越界、弱化、扩大或使用无关同类型知识填充 Coverage 时失败关闭。

结论：目标没有被“相关知识”替代，更新目标与发布成员之间可重建。

### 4.3 逐 Need 语义充分性

链路为：Task Boundary → 不可变 Requirement Revision → Need / Joint Constraint / Obligation Manifest → exact Snapshot Read Session → Authority Read Set → Need Support Proof → 完整性机械校验 → 集合聚合 → Answer Review 重读。

相关类型、关键词、单条粗粒度 Inference、Entity 身份或流畅 Answer 都不能单独满足 Need。任何 Gap、Conflict、Unknown、Coverage 或 Application Limitation 必须保留。

结论：只有全部 Need 和 Joint Constraint 满足才产生 `SUFFICIENT`，答案无法补写未进入正式证明链的语义。

### 4.4 有界 Source Tool Loop

链路为：Knowledge Construction Strategy 形成 Source Information Need → 模型 /确定性 Planner 提出 Tool Proposal → Application Services 校验 Target、权限、Catalog、预算和重复动作 → Source Integration 执行 → Artifact / Observation → 下一次冻结 Manifest。

停止条件覆盖目标完成、预算 / 时间耗尽、重复无进展、权限 / Provider 失败、取消和模型 Stop Proposal 的平台复核。空 Selector、截断或预算耗尽不能扩大为全仓库读取或完整覆盖。

结论：调查能够渐进取证，模型不获得来源旁路或 Tool 执行权。

## 5. 端到端场景推演

### SC-01：配置系统及 Git 来源

1. Management Application Service 调用 Knowledge Engine 创建 `SYSTEM` Scope。
2. Source Integration 规范化 Git DataSource，并创建绑定 exact Scope Reference 的 DataSourceBinding。
3. 任一步失败时保留已经成功且可观察的上游对象，组合 Result 逐步披露真实 Outcome；不使用跨 Owner 回滚删除。
4. 配置成功不自动宣称知识已初始化或 Snapshot 已发布。

结果：通过。Scope、Source / Binding 和管理用例状态没有混写。

### SC-02：解释 exact Commit 的 JWT 迁移影响

1. Requirement 把 exact Commit、变化范围、JWT 相关性、技术影响区域和未知项表达为可裁决 Need / Joint Constraint。
2. Source Target Resolver 将完整 Commit 与 comparison parent 解析为 exact Receipt；Build Intent 冻结 discovery boundary。
3. no-tools Planner 在有界循环中提出 Read Commit、Read Diff、Search / Read Files 等 Proposal；平台逐步执行并形成 Artifact。
4. Evidence / Candidate / Admission / Snapshot 只接收符合 Target Coverage 的成员。
5. 新 Session 对全部 Need 重新形成 Support Proof；Response Control 只依据同一 Snapshot 的正式知识和 Assessment 审核答案。

结果：通过。无关 History Fact、直接源码回答或 Answer Text 均不能满足任务。

### SC-03：代码与需求文档表达不同规则

1. 两个来源分别形成可独立复核的 Evidence 和 Fact，不因文本冲突而拒绝任一合法直接观察。
2. Context Comparison 先判断目标、维度和 Context 是否可比。
3. 只有可比且互不兼容时才形成 Conflict Inference；否则保留并列 Fact 或未知关系。
4. Semantic View 必须呈现正式 Conflict Inference 及其全部 Fact；Sufficiency 根据 Need 判断冲突是答案还是未决 Gap。

结果：通过。系统既不覆盖冲突，也不把来源不同自动解释为冲突。

### SC-04：A 分支代码、B 版本日志、测试与生产 DB 配置并存

1. 每个来源独立保留 Source Context 和 Observation Basis，不要求硬编码发布平台映射。
2. KnowledgeContext 保留 Branch、Deployment、Environment、Time 与 Data Scope；相同字符串不自动等价。
3. 模型可以提出 Context 关系 Candidate，但正式组合必须具有可复核 Basis 和 Context Comparison Assessment。
4. 无法组合时 Fact 保持各自成立条件，跨 Context Need 返回 Gap / Limitation，不拼成单一全局事实。

结果：通过。AI Native 关联能力得到保留，平台没有放弃 Context 与可信性控制。

### SC-05：模型隔离失效或实际模型发生漂移

Gateway 在调用前无法签发 Receipt 时不分派；分派后发现 breach 或 actual fingerprint 不符合 Qualification 时隔离原始响应，Capability Owner 不产生任何生产领域结果，并向资格 Owner 返回失效信号。

结果：通过。不存在“先污染生产状态、再异步撤销”的窗口。

### SC-06：答案审核期间 Snapshot /权限变化或用户取消

Response Control 在授权和首次发送前重读 Task Validation 与 Result Delivery Assertions。Revision、Use Epoch、权限或 Classification 变化使 Dispatch Claim 失败。若发送 Claim 已先成立，只解析同一 Logical Delivery / Adapter Key 的 Receipt；不发送第二份正文。

结果：通过。Task Control 与 Response Control 各自推进状态，取消和交付 Outcome 不互相伪造。

## 6. Demo 判定

本轮所有发现都可由 SWM-ARCH@1.2 的既有所有权、状态与失败语义静态判定；没有出现两个都合理且必须依靠运行实验才能选择的公共契约方案。因此不启动新 Demo。

以下工作使用其他验证类型：

- Provider 能否机械实现 no-tools：Contract Conformance。
- 模型 Target Resolution、Tool Planning、Candidate、Sufficiency 和 Review 质量：Capability Evaluation。
- 真实实现能否保持幂等、CAS、恢复和交付语义：Conformance / 故障注入。
- 产品是否达到直接来源调查基线：独立产品价值验证。

## 7. 评审结论

本轮没有发现需要修改 SWM-ARCH@1.2 顶层组件或正式知识主干的问题。详细设计已经消除已识别的跨所有者混写，并为四条强制可信链形成可追踪闭环。

所有主题继续保持 `In Review`：本记录是架构自检完成证据，不代表评审委员会已经批准，也不代表实现或产品门禁通过。进入 `Accepted` 前仍需按总纲完成主题级外部评审；进入编码前还需由独立实施方案选择具体纵向切片。

## 8. 后续接受性评审

2026-08-05，首个纵向实现切片依据本记录继续执行独立分组评审与交换回归。该评审发现了静态边界检查没有暴露的 Run / Attempt 生命周期、跨 Owner 资格握手、默认 `NO_EVICTION` 下游兼容和恢复自证等实现阻塞，并在既有主题内完成修订。

正式 Finding、修复、交换回归和主题状态决定见 [SWM-DD-ACCEPT-001](Detailed_Design_Acceptance_Record_001.md)。本记录保留 2026-08-03 的检查事实，不用后续数值覆盖历史结果，也不单独作为当前实施基线。
