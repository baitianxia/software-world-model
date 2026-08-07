# Software World Model Implementation Baseline Manifest — Iteration 001 / Revision 002

| 元数据 | 值 |
|---|---|
| Manifest ID | SWM-IBM-ITER-001-REV-002 |
| Status | Frozen |
| Created At | 2026-08-05 |
| Supersedes | `SWM-IBM-ITER-001`（仅文档目录与导航包装） |
| Migration Record | [SWM-DOC-MIG-001](../../history/Documentation_Structure_Migration_Record_001.md) |
| Implementation Plan | [SWM-IMP-ITER-001](Implementation_Plan_Iteration_001.md) |
| Design Acceptance | [SWM-DD-ACCEPT-001](../../detailed-design/governance/Detailed_Design_Acceptance_Record_001.md) |
| Design Baseline | [SWM-DBM-ITER-001-REV-002](../../detailed-design/governance/Design_Baseline_Manifest_Iteration_001_Revision_002.md) |
| Current Gate | WP-0 Complete / WP-1 Ready |
| Hash Algorithm | SHA-256 |
| Workspace VCS | None；以本文的完整文件摘要和内层规范摘要固定基线 |

> 本 Manifest 固定首个纵向实现切片在编码前必须共同遵守的实施契约。Revision 002 只重新固定迁移后的 canonical 路径和完整文件摘要，不改变内层规范 Payload 或实施选择。它不表示 Adapter、Provider、Schema Registry、模型能力或产品质量已经通过运行验证；没有实现时定义 Conformance Fixture，不伪造执行结果。

## 1. 冻结决定

WP-0 的文档准入条件已经满足：

1. 采用的 22 个详细设计主题已经 Accepted，并由 SWM-DBM-ITER-001-REV-002 固定；两个条件主题未被本切片隐式使用。
2. OpenAI Responses no-tools Adapter 方式已经选定，执行前输入闭包和禁止旁路具有机械配置方案；真实 Conformance 尚未执行。
3. Iteration 001 INITIAL Knowledge Schema、Local Git Provider-specific Contract 和 Shared Error Classification 已冻结且互相一致。
4. Schema 对 Local Git Profile 使用 exact 单向依赖；Profile 不依赖 Schema Definition Digest，不存在规范摘要循环。
5. WP-1 可以建立单体骨架与权威存储，但任何模型 Strategy、Local Git Provider 或正式知识发布能力仍须在其工作包内通过相应 Conformance / Capability Gate。

## 2. 固定实施产物

| Document | ID / Version / Status | 内层规范摘要 | 完整文件 SHA-256 |
|---|---|---|---|
| [OpenAI no-tools Adapter Profile](contracts/ITER-001-OpenAI-No-Tools-Adapter-Profile.md) | `SWM-ADAPTER-OAI-RESPONSES-001@0.1.0` / Selected — Conformance Required | 不适用 | `f222ea0b86db6994db2f09baa2f9ad44cd4dd8b7746b88ef09573410db8add60` |
| [CC-MODEL-NO-TOOLS-001](conformance/CC-MODEL-NO-TOOLS-001.md) | `CC-MODEL-NO-TOOLS-001@0.1.0` / Defined — Not Executed | 不适用 | `ee4bc94ef8f56c987c204145a38ff6e22b5a9b48a1b989b0c46111d957a989c0` |
| [INITIAL Knowledge Schema](contracts/ITER-001-Initial-Knowledge-Schema.md) | `swm.local-git.software-knowledge / iter-001.initial.1` / Frozen for Iteration 001 | Definition `sha256:1ba1a4090032464b4970bbc13a2a29685bb5b7f5d00fbf35b5da914e266c64fa` | `7dfb27cfc8d9652f97c64d466a01662521870c08cc868e97fc4d0a442342a494` |
| [Local Git Provider Profile](contracts/ITER-001-Local-Git-Provider-Profile.md) | `ITER-001-LOCAL-GIT-PROVIDER@0.1.0` / Frozen for Iteration 001 | Profile `sha256:d1eacb1e2c61c160c239b840cc84d660fef9fe282acd465358ae41f07bf76d1f` | `24cd748572ef69dd2bddd2b4a0f157288b6ce55aa32becba694fa160b8e0d855` |
| [Shared Error Classification](contracts/ITER-001-Shared-Error-Classification.md) | `ITER-001-SHARED-ERROR-CLASSIFICATION@0.1.0` / Frozen for Iteration 001 | 不适用 | `e2a40c880f4c214067d4fb3810a47bcd2ab42f596674402db6dd6d96be33ee7d` |

内层规范摘要只覆盖各文档明确标记的规范 Payload，用于运行对象精确引用；完整文件摘要还覆盖状态、导航链接和说明，用于证明实现采用了本 Manifest 审核过的完整文档。两者不能互相替代。

## 3. 本轮实施选择

| 维度 | 冻结选择 |
|---|---|
| Runtime Knowledge Path | `Formal Knowledge Single Path`；不存在运行时直接来源回答旁路 |
| Model Adapter | OpenAI `POST /v1/responses` direct HTTPS；无会话、无 Provider Tool、无附件、仅 Manifest 内联文本 |
| Model State | 不在本基线选择具体生产模型；exact Model、Prompt 与 Strategy 由后续 CC、CE 和 Activation 决定 |
| Source Provider | 单个本地非 bare Git 工作树；只读 committed object；`list / search / read / compare` |
| Source Artifact | 版本化 Artifact Kind / Payload Schema；首版只 Artifactize 单页或单次 Observation，不聚合多页 Payload，不生成 hunk |
| Source Retention | `NO_EVICTION`；不实现 Archive、Evict、Physical Delete 或 Guard 状态机 |
| Knowledge Schema | 单 Scope、单 exact Schema Reference；只使用 `INITIAL | UNCHANGED`，不启用 Adoption |
| Knowledge Membership | `ENTITY | FACT | INFERENCE`；Artifact、Evidence、Context、Candidate 和模型输出不是 Snapshot Member |
| Projection / Semantic View | `DISABLED` / 不作为本切片依赖 |
| Error Handling | Owner Result 保持领域权威；Shared Error 只投影 Category、Outcome Certainty、Recovery 和 Exposure |

## 4. 最小语义可表达性

本表只证明 Schema 存在正式表达路径，不证明模型可以在真实项目上正确构建这些知识。

| 用途 | 本切片正式表达路径 | 明确限制 |
|---|---|---|
| Structure | source-unit / module / code-symbol / dependency / config Entity；element-declaration、structural-relation、interface-mapping、dependency/config Fact | 只接受 Profile 注册的保守输入子集；歧义保持 unresolved |
| Behavior | execution-step、interface-mapping 等直接 Fact；首次 Snapshot 发布后，以 exact Base Snapshot 在 `UNCHANGED` 更新中形成 declared-behavior-flow Inference | 不把静态代码声明表述为已部署运行事实 |
| History | revision-parent、revision-change Fact；后续 change-impact / change-explanation Inference | 不推断 merge-base、rename、真实作者意图或完整影响集合 |
| Business | source-statement Fact；后续 business-interpretation Inference | 不创建 Business Entity；没有明确来源或充分前提时返回 Gap |
| Conflict | 只对 Schema 明确注册的 Fact 类型、目标键、Context 和值维度形成 fact-conflict Inference | 未注册组合、未知或不可比较返回 `NOT_COMPARABLE` / Gap，不制造冲突或选择赢家 |

`INITIAL` 只发布 SOURCE_ANCHORED Entity 和直接 Evidence 支持的 Fact。Behavior、Business、History 等需要推理的结论必须在 INITIAL 成功后开启新的 `UNCHANGED` Application Attempt，引用已发布正式前提；不能在同一 Candidate Bundle 中把 Candidate Fact 当作 Inference 前提。

## 5. 尚未执行的门禁

| Gate | 当前状态 | 最迟执行边界 |
|---|---|---|
| OpenAI no-tools Adapter CC | Defined — Not Executed | WP-2；通过前不得签发生产 Eligibility 或激活模型 Strategy |
| Local Git Provider / Resolver Conformance | Case Catalog Frozen — Not Executed | WP-2；通过前 Provider / Resolver 不获得迭代可用资格 |
| Schema / Identity / Fact / Inference / Admission / Snapshot Conformance | Case Catalog Frozen — Not Executed | WP-3；通过前不得把相应能力声明为可用 |
| Shared Error Mapping / Recovery / Exposure Conformance | Case Catalog Frozen — Not Executed | 各首个实现消费者所在工作包退出前 |
| Capability Evaluation / Strategy Activation | Not Selected / Not Executed | 相应模型 Capability 进入生产前 |
| Product Holdout | Not Executed | WP-7；决定本纵向切片能否最终验收 |

因此，`WP-0 Complete` 只表示编码前契约已闭合；不等于 Provider 合规、模型可用、正式知识路径可运行或产品目标通过。

## 6. 复核结论

冻结前完成两条独立只读复核：

- Knowledge Core 复核：Schema、Context、Evidence、Entity、Fact、INITIAL / UNCHANGED 和 Local Git exact dependency 均为 `PASS`。
- Infrastructure / Source 复核：Repository Identity、Source Context Vocabulary、Artifact / Payload、typed codec、分页 /零项、no-hunk、Conformance 分阶段边界和摘要依赖均为 `PASS`。

机械复核确认：

- Local Git Profile Contract Digest、Schema Definition Digest和两个 codec Golden Vector 均可独立重算。
- Schema 只依赖 exact Local Git Profile Digest；导航用 Consumer 链接位于规范摘要之外，不构成循环。
- 本轮修订没有新增顶层模块、服务、数据库、运行双路径或项目专用 Builder。

## 7. 完整性与变更规则

1. WP-1 及后续实现、测试、CC、CE 和产品验证必须记录 `SWM-DBM-ITER-001-REV-002 + SWM-IBM-ITER-001-REV-002`。
2. 使用前必须同时重算本文第 2 节的完整文件摘要和文档内层规范摘要；任一不一致均不得声称符合本基线。
3. 冻结产物的规范语义变化必须创建新版本和新的 Implementation Baseline Manifest；不能原地修改 Digest 或继续沿用 `V1`。
4. Adapter / Fixture 状态保持独立演进。真实 Run 通过后应封存单独 Conformance Result，不把本文状态改写成测试结果。
5. 实现发现 Contract 无法满足时，应停止对应能力、记录失败并修订实施契约；不能通过直接来源回答、模型隐藏 Tool、自由字段或 Demo 特例绕过。
