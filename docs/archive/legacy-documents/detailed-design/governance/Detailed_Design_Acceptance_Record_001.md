# Software World Model 详细设计主题接受记录 001

| 元数据 | 值 |
|---|---|
| Record ID | SWM-DD-ACCEPT-001 |
| Decision Date | 2026-08-05 |
| Architecture Baseline | [SWM-ARCH@1.2](../../architecture/Software_World_Model_Architecture_Baseline.md) |
| Detailed Design Guide | [SWM-DD-GUIDE@0.1.0](../Software_World_Model_Detailed_Design.md) |
| Implementation Consumer | [SWM-IMP-ITER-001](../../implementation/iteration-001/Implementation_Plan_Iteration_001.md) |
| Preceding Static Review | [SWM-DD-REVIEW-001](Detailed_Design_Review_Record_001.md) |
| Review Method | 独立分组评审 + 交换回归 + 全局机械一致性检查 |
| Decision | SWM-DD-GUIDE@0.1.0 与 22 个采用主题 `Accepted`；2 个条件主题保持 `In Review` |
| Design Validation Demo | Not Required |
| Status | Completed |

> 本记录批准详细设计成为可实施契约，不表示实现、Provider Conformance、Capability Evaluation 或产品验收已经通过。评审者只提出 Finding；Architecture Steward 按主题所有权和依赖顺序作出状态决定。

## 1. 接受范围

本轮接受 SWM-DD-GUIDE@0.1.0 的主题划分、依赖、状态、验证和变更治理规则，并接受首个纵向实现切片实际采用的主题：

- 共享执行、模型隔离、能力评测与运行观测。
- KnowledgeScope、DataSource / Binding、Source Operation / Artifact。
- Context、Schema Core、Evidence、Entity、Fact、Inference / Conflict、Admission、Snapshot / Publication 与权威持久化。
- Management、Knowledge Update、Knowledge Use、Agentic Task 与 Response Control。

以下条件主题不属于本次实现消费者，继续保持 `In Review`：

- `DD-KNW-SCHEMA-EVOLUTION@0.1.0`：只有跨 Schema Adoption 时启用。
- `DD-SEM-SEMANTIC-VIEW@0.1.0`：首个切片直接使用正式知识 Query / Sufficiency，不以 View 为前置条件。

## 2. 评审组织与独立性

首轮分别按责任边界只读评审：

| Reviewer Focus | 评审范围 | 初次结果 |
|---|---|---|
| Infrastructure / Source | X、AI、Evaluation、Scope、DataSource、Source Artifact、Management、Telemetry | 7 项阻塞 |
| Knowledge Core | Context、Schema、Evidence、Entity、Fact、Inference、Admission、Snapshot、Persistence | 4 项阻塞 |
| Application Trust Chain | Knowledge Update / Use、Agentic Task、Response Control | 3 项阻塞 |

完成修订后交换评审，避免原评审者只复核自己的修复：

- Infrastructure / Source Reviewer 复核 Knowledge Core 修复。
- Knowledge Core Reviewer 复核 Application Trust Chain 修复。
- Application Trust Chain Reviewer 复核 Infrastructure / Source 修复及其跨主题调用闭环。

交换评审又发现恢复状态、下游接口和资格传递中的残留问题；全部修复后，三个 Reviewer Focus 的最终结果均为 `PASS`。

## 3. 阻塞 Finding 与关闭结果

| ID | 阻塞问题 | 关闭方式 |
|---|---|---|
| AC-001 | Evaluation 只有 Result，没有可恢复 Run / Case Attempt | 新增 `MGT-EVALUATION-RUN-01`，定义隔离 Sink、Case Attempt、取消、未知 Outcome、幂等和恢复 |
| AC-002 | Activation 缺少 Scope 级停用、替换、回退和 CAS | 使用不可变 `ACTIVATE / REPLACE / DEACTIVATE` Decision 与单调 Activation Revision |
| AC-003 | Source Dispatch 被表述为跨 Owner 原子操作 | 拆为 Source 资格准备、Allocation / PREPARED 握手和 Source 本地 dispatch fence |
| AC-004 | Binding Eligibility 使用悬空 Scope Assertion | 新增 `KNW-SCOPE-STATE-ASSERTION-01`，DataSource 明确消费 exact Purpose / Revision / Digest |
| AC-005 | Target Resolution 缺少 Attempt、幂等和未知 Outcome 恢复 | 增加 Target Resolution Attempt、唯一 Receipt、Resolution Revision 与失败关闭 |
| AC-006 | 首个切片被未来淘汰协调状态机阻塞 | `NO_EVICTION` 使用 `NOT_REQUIRED_NO_EVICTION` Read Protection；只有 `MANAGED_EVICTION` 创建 Guard |
| AC-007 | Management Pending / Unknown / Cancelled 状态不闭合 | 统一 `OUTCOME_PENDING`，使用 Step Root + append-only Revision、Attempt / Result 原子有效指针和真实取消映射 |
| AC-008 | Management 重复拥有 Evaluation / Activation 语义 | Management 主题只管理自身组合命令；Evaluation / Activation 由专属主题拥有 |
| AC-009 | Pricing Catalog Contract 与实例权威 Owner 冲突 | Telemetry 不再拥有平台内 Pricing Catalog，只消费 external exact Pricing Input Revision |
| AC-010 | Schema Availability 有状态但无生命周期 | 新增 `KNW-SCHEMA-AVAILABILITY-01`，定义初始状态、CAS、幂等和单调弃用；重新启用使用新 Schema Reference |
| AC-011 | Entity 聚合使用未声明的 Context 兼容能力 | 增加 Context Comparison 依赖；只接受机械相等或 exact current VALID Assessment |
| AC-012 | Persistence 的逻辑域越过 Application Owner | Investigation、Evaluation、Activation、Resource Policy 只保存 opaque exact Reference / Digest |
| AC-013 | Persistence 把 Closure Decision 与完整 Batch 错写为同一事务 | 拆为 Closure 原子 Seal 与全部终态后的独立幂等 Batch Seal |
| AC-014 | Reviewer Proposal 缺少 Task-Control-owned Invocation Outcome | 新增 `APP-REVIEWER-INVOCATION-OUTCOME-01`；Response Control 验证 Assertion 后才接收 Assessment |
| AC-015 | 应用模型结果资格没有落到生产封存点 | Update、Use、Task、Response 分别在领域封存前消费 `X-MODEL-RESULT-ELIGIBILITY-01` |
| AC-016 | 未满足枚举 Need 无法披露已经证明的部分 | 增加 `PARTIAL_FORMAL_SUPPORT`，同时强制保留 Gap、未知范围和未满足 Obligation |
| AC-017 | Evaluation 取消后可能永久停在 OUTCOME_PENDING | 原 Case 解析后允许 Run 收敛到 CANCELED；不形成 Evaluation Result |
| AC-018 | Management Binding 流程没有取得 BIND_CONFIGURATION Assertion | 在 Binding dispatch 前读取并传递 exact Scope State Assertion |
| AC-019 | Reviewer 模型资格失败时既不能 ALLOW 又无法收口 | Task Control 以平台资格失败事实封存 `FAILED + DENY`，不保存模型语义 Proposal |
| AC-020 | Review Assessment 结构失败没有终态 | 允许 `ASSESSMENT_RECEIVED → FAILED | CANCELED`，并区分结构失败与完整矩阵的 UNKNOWN |
| AC-021 | 同库 Store Availability 状态机无法证明数据库没有回退 | 删除同库自证状态；当前只支持同一历史重启，非连续历史由部署 fail-stop，未来需外部 Generation Authority |
| AC-022 | `NO_EVICTION` 修订未贯穿 Evidence / Update | Source、Evidence 与 Update 统一使用判别式 Read Protection；Guard 仅适用于 `MANAGED_EVICTION` |
| AC-023 | Evaluation Case 的 OUTCOME_UNKNOWN 没有解析迁移 | 通过原 Provider Request 追加 Resolution Revision，使同一 Attempt 收敛为 SUCCEEDED / FAILED |
| AC-024 | Source Operation 缺少 SOURCE_EXECUTION 资格闭环 | Update 每个 Source Step 取得 Scope Assertion 和 Binding Eligibility；Intent、Request、Grant 和 dispatch 重验全部绑定 |

以上修订都发生在既有主题和 Owner 内，没有新增顶层模块、服务、数据库、运行旁路或双路径，也没有引入需要 Demo 裁决的新公共契约分叉。

## 4. Accepted 条件检查

| 总纲条件 | 结果 | 依据 |
|---|---|---|
| 上游依赖已生效或可按依赖顺序生效 | PASS | 124 条基础依赖无缺失、版本失配或环；本记录按拓扑层级作出决定 |
| 职责、输入输出、状态、失败、并发和一致性无未标注空白 | PASS | 初评与交换回归的 24 项阻塞全部关闭 |
| 改变契约选择的不确定性已关闭 | PASS | 所有 Finding 可由静态契约推演关闭；无需 DVR Demo |
| 不依赖 Demo、样例工程、模型或供应商偶然行为 | PASS | Provider 行为由后续 CC 验证，模型质量由 CE 验证 |
| 与架构、ADR 及其他主题完成追溯 | PASS | 主题元数据、唯一 Contract Owner、依赖图和本地引用机械检查通过 |
| no-tools 冻结输入闭环 | PASS | Gateway / X Execution /领域生产 Sink 全部失败关闭 |
| Canonical Build Target 与有界 Source Tool Loop | PASS | Target Receipt、Coverage、Scope / Binding Assertions 和平台执行链闭合 |
| 逐 Need Sufficiency 与 Answer Review | PASS | Support Proof、Partial Formal Support、Reviewer Outcome 和交付重验闭合 |

## 5. 依赖顺序与主题决定

| Layer | Accepted Documents |
|---|---|
| L0 | DD-KNW-KNOWLEDGE-SCOPE@0.1.0；DD-X-CAPABILITY-EXECUTION@0.1.0 |
| L1 | DD-AI-MODEL-GATEWAY@0.1.0；DD-KNW-REFERENCE-CONTEXT@0.1.0；DD-SRC-DATA-SOURCE@0.1.0 |
| L2 | DD-APP-MANAGEMENT@0.1.0；DD-MGT-CAPABILITY-EVALUATION@0.1.0；DD-SRC-SOURCE-ARTIFACT@0.1.0；DD-X-TELEMETRY-COST@0.1.0 |
| L3 | DD-KNW-SCHEMA-CORE@0.1.0 |
| L4 | DD-KNW-CONTEXT-COMPARISON@0.1.0；DD-KNW-EVIDENCE@0.1.0 |
| L5 | DD-KNW-ENTITY@0.1.0 |
| L6 | DD-KNW-FACT@0.1.0 |
| L7 | DD-KNW-INFERENCE-CONFLICT@0.1.0 |
| L8 | DD-KNW-ADMISSION@0.1.0 |
| L9 | DD-KNW-SNAPSHOT-PUBLICATION@0.1.0 |
| L10 | DD-APP-KNOWLEDGE-UPDATE@0.1.0；DD-KNW-PERSISTENCE@0.1.0 |
| L11 | DD-APP-KNOWLEDGE-USE@0.1.0 |
| L12 | DD-APP-AGENTIC-TASK@0.1.0 |
| L13 | DD-APP-RESPONSE-CONTROL@0.1.0 |

L0 到 L13 依次生效。同一 Layer 的主题没有相互基础依赖，可以同时决定。条件依赖只在声明的 Applicability 启用时生效；本轮未启用 Schema Adoption 和 Semantic View。

## 6. 决定边界

自本记录生效起：

1. `SWM-DD-GUIDE@0.1.0` 与上述 22 个 `@0.1.0` 主题状态为 `Accepted`；主题可以被实施方案精确采用。
2. `DD-KNW-SCHEMA-EVOLUTION@0.1.0` 与 `DD-SEM-SEMANTIC-VIEW@0.1.0` 仍为 `In Review`，不能被本轮实现隐式使用。
3. `Accepted` 不证明真实 Model Provider 已满足 no-tools、不证明 Connector / Repository 已符合 Contract，也不证明模型质量或产品价值；这些分别由 CC、故障注入、CE 和 Product Holdout 决定。
4. 任何 Accepted 文档的规范性内容变化必须按总纲升级版本、评估下游并建立新的 Design Baseline Manifest；不能直接修改当前实施基线。
5. 精确基线已由 [SWM-DBM-ITER-001-REV-002](Design_Baseline_Manifest_Iteration_001_Revision_002.md) 建立；当前进入 WP-0 的 Provider Adapter、INITIAL Schema、Local Git Contract 和错误分类冻结。
