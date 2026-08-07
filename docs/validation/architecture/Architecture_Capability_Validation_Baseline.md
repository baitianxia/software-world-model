# Software World Model 架构能力验证基线

| 元数据 | 值 |
|---|---|
| Document ID | `SWM-ARCH-CAPABILITY-VALIDATION-BASELINE-001` |
| Validation Case ID | `DVR-FORMAL-PATH-CAPABILITY-001` |
| Status | `Defined — Not Executed` |
| Validation Type | Design Validation / Architecture Capability |
| Architecture Baseline | `SWM-ARCH@1.2` |
| Design Baseline | `SWM-DBM-ITER-001-REV-002` |
| Implementation Slice | `SWM-IMP-ITER-001` |
| Runtime Knowledge Path | Formal Knowledge Single Path |

> 本文定义一个可证伪的架构能力实验，不修改或替代架构、详细设计、Knowledge Schema 或实施方案。验证结果可以触发设计修订，但只有后续正式修订才能改变规范性基线。

## 1. 验证问题

本验证回答的唯一主问题是：

> 在 Iteration 001 声明的 Local Git、Java、Maven 和 exact Revision 任务边界内，直接源码调查能够由授权来源证明的实质信息与结论，是否能够在不弱化语义、Context、Modality、Coverage 和未知边界的情况下，完整经过 `Artifact → Evidence → Entity / Fact / Inference → Admission → Snapshot → Sufficiency → Answer Review`，并在来源关闭后只依赖正式知识恢复；同时，方案是否产生认知复用、受控 Context 融合和可信审核等直接单次源码调查不原生提供的能力。

本验证通过一次完整、受控且可回放的公共端口 Demo Run，检验架构方案是否能够实际承载、约束、发布并恢复上述能力。公共契约存在相应类型和字段只是运行前的静态容量条件，不能单独证明方案具备能力。本 Case 不检验某个基础模型、Prompt 或 Candidate Strategy 当前能否可靠提出正确认知；这部分由 Capability Evaluation 负责。但是，Demo 中承担平台职责的 Source、Application、Knowledge、Publication、Sufficiency 和 Review 机制必须真实执行，不能由 Fixture 代替。

一个有限 Demo 不能证明对任意程序、任意问题和任意推理普遍无损。因此本文只允许在预先冻结的任务和来源边界内作出结论；不得将通过结果外推为“所有源码问题均可无损正式化”。

### 1.1 “方案具备能力”的判定边界

本 Demo 的被测对象是架构方案，不是 Demo 产品，也不是模型质量。只有同时满足以下条件，才能在本 Case 的冻结边界内判定“方案具备该能力”：

1. 预先冻结的正确 Proposal 能通过公开 Application Port 和正式组件责任，完整到达权威状态与最终交付；不得由 Fixture、测试代码或私有 Helper 直接写入权威 Repository 或跳过 Gate。
2. 对应的错误、越权、歧义和信息不足 Proposal 会被平台机械拒绝；正确性不能只依赖模型自觉、Prompt 要求或事后文本检查。
3. 完成任务所需语义均有通用、版本化、可替换的公共 Contract 承载，不依赖题目、仓库、类名、Commit 或黄金答案专用实现。
4. 来源关闭后仍能从正式状态重建结果，并能回放 Context、Support、Admission、Snapshot、Sufficiency 和 Review 决策。
5. 同一能力在随机身份和冻结反例下可重复执行；一次偶然输出正确不能证明方案能力。

确定性 Capability Fixture 只扮演“不可信认知生产者”，用来排除基础模型概率波动这个无关变量。它可以提交 Proposal，但不能代替平台形成权威决定。因此：

- 正确 Fixture Proposal 都无法通过公共契约完成，说明方案或其现行规范存在能力缺口。
- Fixture 可以通过，但真实模型不能稳定形成正确 Proposal，说明现行 Capability Strategy 尚不合格；不能据此放宽正式知识路径。
- 只有私有测试缝隙或手工跨阶段编排能够跑通，只能登记为局部机制见证，不能判定本 Case 或总体方案通过。
- 完整 ACV 通过只证明冻结任务边界内的方案能力；真实模型可靠性、未见项目泛化和产品优势仍分别由 Capability Evaluation 与 Product Holdout 验证。

### 1.2 证据层级

| 证据 | 能够证明 | 不能证明 |
|---|---|---|
| Formal Mapping 静态审计 | 目标语义具有 exact Contract 承载空间，完整 Demo 获得执行资格 | 方案已经运行完成任务、任何 ACV Gate 已通过 |
| 局部机制见证 | 某个公开或受控 seam 上的局部状态机制可执行 | 完整公共方案具备端到端能力 |
| 完整公共端口 ACV Demo Run | 在冻结任务、来源和反例边界内，架构方案能够通过 Formal Knowledge Single Path 完成任务并产生所声明的架构增益 | 真实模型可靠性、未见项目泛化或产品可用性 |
| Capability Evaluation | exact 模型、Prompt、Tool 与 Strategy 能否在冻结能力契约下可靠提出合格 Proposal | 未见产品任务上的端到端优势 |
| Product Holdout | 真实系统在未见工程和任务上是否达到或超过同条件直接调查 Agent | 对任意软件问题的普遍保证 |

因此，本文中的“Demo 验证方案能力”始终指第三行的完整运行证据，不是 Demo 工程质量、测试数量、静态映射结果或 Fixture 所携带答案本身。

## 2. 能力守恒与架构增益

### 2.1 任务语义守恒

正式知识单路径不要求把全部源码字节、调查 Transcript 或模型思考暴露给答案阶段。它要求保存完成冻结任务所需的语义：

- 每个来源支持的实质 Claim 都有同一成立条件下的正式 Fact Proposition 或 Inference Conclusion 支持。
- Formal Support 的语义必须蕴含目标 Claim，并保留同一目标身份、Revision、Context、Observation / Conclusion Modality、限制和 Coverage。
- 多来源观察、复合结论和否定或完整性结论所依赖的组合、反例与 Coverage 义务必须显式保留，不能藏入自由文本、Evidence Quote 或 Agent 记忆。
- 一个有来源依据的 Direct Claim 若在正式路径中只能变成 `Gap | Unknown | Application Limitation`，即发生能力损失；诚实披露不能抵消该损失。
- Direct Claim Oracle 中不存在来源依据的内容不得为了达到覆盖率而进入正式知识或答案。

设冻结的实质 Direct Claim 集为 `D`，已发布正式命题集为 `K`。能力守恒要求对每个 `d ∈ D`，存在一个可重建的正式支持闭包 `K_d ⊆ K`，使 `K_d` 在相同 Context 和 Modality 下蕴含 `d`。任何实质 Claim 缺少该映射即失败，不按总分平均掩盖。

### 2.2 架构增益

只有能力守恒全部通过后，才评价以下额外能力：

1. **认知复用**：一次正式化后，不同问题、全新 Session 和不同 Agent 可以在不重新读取来源、不重新构建知识的情况下复用同一正式命题。
2. **Context 融合**：兼容 Context 中的多个正式命题可以显式组合；Revision、比较角色或 Context 不兼容时必须阻止错误拼接。
3. **可信审核**：每个 Answer Claim 可以回放到 exact Snapshot、Admission、Fact / Inference、Evidence、Artifact 和 Revision；篡改或陈旧状态不能获得放行。
4. **受控演化**：来源 Revision 变化后，受影响知识不会静默继承，旧 Session 和旧 Authorization 不能与新 Snapshot 混用。

上述属性必须由状态和可回放记录证明，不能用“理论上可以”“Agent 记住了”或自然语言说明代替。

## 3. Direct Claim Oracle

### 3.1 定义

`Direct Claim Oracle` 是本验证的来源支持下限，不是某次模型回答正文。每个 Oracle Item 至少固定：

- `Claim ID`、对应问题和 Knowledge Need。
- 规范化 Claim 语义及 Claim Kind。
- exact Repository、Revision / Comparison、目标身份和适用 Context。
- `DIRECT_OBSERVATION | SOURCE_DECLARED | DERIVED | UNKNOWN_BOUNDARY` Modality。
- 必需 Source Observation / Evidence Locator 集及内容 Digest。
- 派生 Claim 的正式前提、组合规则、限制、反例和 Coverage Obligation。
- 是否为实质 Claim，以及它与其他 Claim 的联合约束。
- 独立核对结果；不能只引用直接 Agent 的自报结论。

自然语言措辞差异不构成损失；目标身份、条件、关系、公式、枚举项、因果或相关性 Modality、未知边界发生变化则构成语义差异。

### 3.2 冻结来源

首轮 Oracle 采用以下两类输入：

1. [PV-HOLDOUT-001 冻结题目与黄金量表](../product-value/Product_Value_Holdout_Baseline.md) 中 H-01 至 H-05 的全部实质评分点和关键 Evidence。直接 Git 调查路径已经在固定 Revision 上取得 `50 / 50`，因此这些内容构成已观察到的直接源码能力下限。
2. 为复用、Context 正反例、篡改和 Revision 更新建立的最小有界 Fixture。Fixture 只引入验证某个架构性质所需的信息，不作为新的产品题目。

H-01 至 H-05 已参与过开发诊断，只能作为本架构能力实验的回归 Oracle，不能再次充当未见产品 Holdout。

在编写或修改本次 Demo 实现前，执行记录必须冻结 Oracle Manifest、项目 Revision、所有 Item 和 Evidence Digest。失败后不得删除 Claim、降低实质性、改写 Context 或把不易表达的 Claim 重新分类为非目标；如基线本身存在客观错误，只能用独立 Errata 保留原记录并说明影响。

## 4. 模型隔离与验证方法

### 4.1 不以模型质量作为自变量

本验证使用版本化、可回放的确定性 Capability Fixture 产生 Requirement、Source Tool Proposal、Candidate Proposal、Sufficiency Proposal、Answer Claim 和 Review Proposal。Fixture 只能通过对应的不可信 Proposal Port 输入数据，不能直接写 Repository、Admission Decision、Snapshot、Assessment Decision、Authorization 或答案正文。

模型相关要求为：

- 不要求调用真实模型或特定 Provider。
- 如果经过 Model Gateway，使用确定性 Test Double，并固定输入输出 Digest。
- Fixture 中的正确 Proposal 和反例 Proposal 均预先冻结；运行后不得根据系统行为即时改写。
- Knowledge Verifier、Application Owner、Snapshot Publisher、Sufficiency 聚合和 Response Control 仍执行真实契约与失败关闭逻辑。
- 整个 Run 预先绑定 exact `CAPABILITY_VALIDATION / VALIDATION_ONLY` Authority Store 与 CURRENT 命名空间。验证中的 Admission、Publication、Snapshot 和 Reader 必须真实执行，但所有 Reference 都只能在该 Run 的验证边界内解析；不得读取、覆盖、别名或切换生产 CURRENT，也不得成为生产 Premise、Coverage Basis、Continuation 或 Root / State 复用来源。

因此，通过只证明公共边界能够承载正确认知并拒绝已知违规；不证明真实模型形成 Requirement、规划调查、生成复杂 Candidate、判断充分性或审核答案的正确率。

### 4.2 两个验证角色与输入域（不是运行双路径）

| 验证角色 | 作用 | 允许输入 | 禁止作用 |
|---|---|---|---|
| Direct Oracle Role | 建立来源支持下限 | exact Git 来源与独立核对 | 不写 Software World Model，不参与被测答案 |
| SWM Evaluation Role | 验证正式知识单路径所代表的架构方案 | 同一来源边界、确定性 Proposal Fixture 和正式 Application Port | 不读取 Direct Answer 正文，不在答案阶段访问 Source / Artifact Payload |

两个角色只通过预先冻结的 Oracle Item 建立验收关系。它们不是 Software World Model 的两条运行或回答路径：Direct Oracle 仅产生独立对照标准，被测系统始终只走 Formal Knowledge Single Path。Direct Agent 输出不得成为 Evidence、Candidate、Fact、Inference、Assessment 或 Answer Claim。

## 5. 禁止捷径

出现以下任一行为，本次验证直接失败：

1. Answer、Sufficiency 或 Review 阶段读取源码、Source Artifact Payload、Evidence Quote、Investigation Transcript、Candidate Working State 或来源调查模型记忆。
2. 运行时直接来源 Agent 兜底、双路径择优，或把 Direct Answer 复制到正式路径。
3. 使用题目 ID、项目类名、黄金答案或固定输出模板建立专用 Builder、View、Predicate、查询分支或答案分支。
4. 用无类型自由文本 Fact、`source-statement`、Evidence Quote 或宽泛 Inference 包装当前 Schema 无法表达的语义。
5. 通过省略 Need、弱化 Sufficiency Criterion、改变 Revision、缩小 Coverage 或把实质 Claim 改成非目标获得完成。
6. 用相关但不蕴含、同类型但目标不同、另一个 Snapshot 或 Context 不可组合的正式知识填充 Support Proof。
7. 用总分、平均分、文风或附加价值抵消任一实质 Direct Claim 的丢失或错误。
8. 在能力守恒未通过前评价复用、Context、审计、时延或成本优势。
9. 复用场景中发生任何 Source Operation、Knowledge Update、Candidate Admission 或新 Snapshot 发布后仍宣称“零调查复用”。
10. 通过 Telemetry、测试断言或 Oracle 文件直接补造权威业务状态。
11. 把 `CAPABILITY_VALIDATION` Fixture 经真实 Gate 形成的验证状态暴露给生产 Reader，或将其作为生产知识前提、CURRENT、Continuation、Root / State 复用来源。

## 6. 验证场景

| ID | 场景 | 核心观察 |
|---|---|---|
| ACV-S01 | 来源观察可达 | Oracle 所需 Commit、Diff、文件范围、声明和反例范围均能由授权 `list / search / read / compare` 取得，且 Locator / Digest 可重放 |
| ACV-S02 | Structure 守恒 | Maven 依赖、模块关系、图覆盖及无环 / 拓扑等实质结论能够正式表达和恢复 |
| ACV-S03 | Behavior 与一致性边界守恒 | 控制流、终止结果、状态写入、事务声明、重复 / 并发保证及未知边界不被弱化 |
| ACV-S04 | 复杂规则守恒 | 分组、分支、档位、金额 /库存 /积分字段、输出次序和缺资料行为逐项正式化 |
| ACV-S05 | History 守恒 | 任意 exact Commit 与父 Revision 的依赖、生成、解析、校验、刷新和未知边界能够覆盖，而非只返回同类型 History 知识 |
| ACV-S06 | Business 规则与边界反例守恒 | 金额、时间、范围、分类、未知值和注释 /代码语义边界完整表达 |
| ACV-S07 | 来源关闭后的单路径恢复 | 发布后关闭 Connector、Artifact Payload 和 Investigation Context，重新打开 Knowledge Use Session 并恢复全部 Oracle Claim |
| ACV-S08 | 跨任务与跨 Agent 复用 | 至少两个不同但共享知识的问题，由至少三个全新 Session / Agent 复用同一 Snapshot 回答 |
| ACV-S09 | Context 融合正反例 | 同 exact Commit 多文件命题可组合；before / after 只按比较角色组合；不兼容 Revision 或未知 Context 不得拼接 |
| ACV-S10 | 审核与追溯篡改 | 分别篡改 Locator / Digest、Evidence Link、Inference Premise、Snapshot Member、Support Proof、Answer Claim / Body 和 Snapshot / Task Revision |
| ACV-S11 | Revision 演化 | 新 Revision 中未变知识可受控延续，受影响知识需重验证；旧 Session、旧 Assessment 和旧 Authorization 不得进入新交付 |

当前实施切片只声明 Local Git 和单个 SYSTEM Scope。ACV-S09 只验证同来源多 Artifact、同 Revision 组合和明确 Git Revision Comparison；DB、Log、Trace、Deployment、多 Scope 和真实跨来源融合不在本次通过结论内。

## 7. 硬门禁

| Gate | 判定 | 必须结果 |
|---|---|---|
| ACV-G00 基线完整性 | 输入可回放 | Oracle Manifest、Fixture、实现 Commit、Schema、Provider Contract 和全部 Digest 在运行前冻结；结果可独立重跑 |
| ACV-G01 来源可达 | Observation Closure | `100%` 实质 Oracle Claim 的必需来源观察能够在同授权边界取得；截断、空选择和未闭合分页不得算完整 |
| ACV-G02 语义可表达 | Formal Mapping | 每个实质 Oracle Claim 都有同 Context / Modality 的正式支持闭包；Claim Preservation 为 `100%`，不得以 Gap 替代 |
| ACV-G03 准入与发布闭环 | Formalization | 全部正确 Closure 能在 exact `VALIDATION_ONLY` 状态边界内经过独立 Verification、Admission、原子 Publication 与 Reader 重放；任何正确 Claim 因 Contract 无法承载而丢失，或验证 State 触及生产 CURRENT，均失败 |
| ACV-G04 逐 Need 充分性 | Support Proof | 每个 Need / Joint Constraint 双向覆盖，全部引用来自同一 exact Session；遗漏、重复或相关但不蕴含时不能 SUFFICIENT |
| ACV-G05 来源关闭恢复 | Single Path | 来源、Artifact Payload 与 Investigation 全部设为 fail-fast 后，Oracle Claim 恢复率仍为 `100%`，Source Operation 为 `0` |
| ACV-G06 无过度推断 | Safety | Unsupported Claim、Context 扩张、Modality 偷换、错误否定、目标弱化和 validation→production 状态泄漏的正式化或放行数均为 `0` |
| ACV-G07 认知复用 | Reuse Gain | 至少三个全新消费者、两个不同问题复用同一正式知识；新增 Source Operation、Update、Admission 和 Publication 均为 `0` |
| ACV-G08 Context 融合 | Context Gain | 全部正例能够按显式规则组合；全部不兼容 /未知 /错 Revision 反例均拒绝，错误融合数为 `0` |
| ACV-G09 可信审核 | Audit Gain | `100%` Answer Claim 具有完整权威追溯闭包；每类篡改均被发现并阻止 Authorization / Delivery |
| ACV-G10 受控演化 | Evolution Gain | 受影响知识不静默继承，陈旧 Session / Assessment / Authorization 放行数为 `0`，CURRENT 不被过期发布覆盖 |

只有 ACV-G00 至 ACV-G10 全部通过，`DVR-FORMAL-PATH-CAPABILITY-001` 才能记为 `Pass`。任一 Gate 为 `Fail | Inconclusive | Not Run` 时，整体不得记为通过。

该门禁故意采用逐 Claim 的 `100%` 下限，因为它验证是否存在架构信息瓶颈，而不是评价可容忍的模型统计误差。时延、Token、调用次数、存储和成本必须记录，但本轮只用于发现可行性风险，不作为架构能力通过条件。

## 8. 失败解释与处置

| 失败位置 | 首要解释 | 处置边界 |
|---|---|---|
| ACV-G01 | Source Provider / Artifact / Locator Contract 无法提供直接路径所需观察 | 修订来源契约或缩小经需求批准的产品范围；不能让答案阶段直接读源码 |
| ACV-G02 | Knowledge Schema、Fact / Inference 类型或 Context / Coverage 表达不足 | 创建新的 Schema Definition 或修订相关详细设计与基线；不能塞入自由字段 |
| ACV-G03 | Candidate、Admission、两阶段 Inference 或 Publication Contract 存在承载断点 | 修订相应知识形成契约；不能跳过准入或直接写 Snapshot |
| ACV-G04–G06 | Query、Requirement、Sufficiency、Response Control 或单路径隔离不足 | 修订 Knowledge Use / Response 边界；Gap 诚实性不能抵消已有依据 Claim 的丢失 |
| ACV-G07–G10 | 核心答案可守恒，但尚未产生所声明的架构增益 | 不得宣称方案能力超过直接单次源码调查；明确缺失增益后再决定修订或缩小目标 |
| 全部 ACV 通过但真实模型失败 | 方案可承载，当前 Capability Strategy 质量不足 | 进入 Capability Evaluation、Strategy 改进或更换模型；不能据此直接否定或放宽架构门禁 |
| 全部 ACV 通过但产品 Holdout 失败 | 架构容量存在，但真实端到端完成度、泛化、成本或体验未达标 | 保持产品未验收；不得用本次 DVR 覆盖 Holdout 结果 |

如果某个 Oracle Claim 在运行后才被声明为“超出 Iteration 001”，结果仍为失败或基线无效，不能自动豁免。只有在 Demo 实现前已经由用户旅程和规范性范围明确排除的内容，才可不进入 Oracle。

## 9. 与既有验证和产品 Holdout 的边界

| 验证 | 回答的问题 | 参与者 | 能否证明产品可用 |
|---|---|---|---|
| 既有 Architecture Validation | 模块职责、依赖方向和关键控制机制能否运行 | 确定性实现、部分真实模型诊断 | 否 |
| 本 Architecture Capability Validation | 公共方案是否能够无语义损失地承载直接源码能力下限，并产生架构增益 | Direct Claim Oracle + 确定性 Capability Fixture | 否 |
| Capability Evaluation | 某个 exact 模型 / Prompt / Tool / Strategy 是否在固定能力契约下达到质量门槛 | 候选与基准 Strategy | 否；只支持 Strategy 激活 |
| Product Holdout | 真实系统在未见工程和任务上是否达到或超过同条件直接调查 Agent | 测试 Harness 内同模型、同来源、同授权预算的两组隔离执行；Direct Agent 不进入 SWM 运行时 | 是，需满足独立产品门禁 |

[PV-HOLDOUT-001](../product-value/Product_Value_Holdout_Run_001.md) 的 `33.75 / 50` 失败结论保持不变。本验证不得回算该分数，也不得把机制、可表达性、复用或审计优势用于抵消正确性与任务完成率差距。

本验证通过后，仍须按实施方案在至少两个未参与开发调试的 Git 工程和未见任务集上执行新的 Product Holdout。只有 Product Holdout 通过，才能宣称首个纵向切片达到直接调查能力下限；只有在此基础上观察到复用、Context、审核、成本或稳定性增益，才能形成产品层面的“超过”结论。

## 10. 运行记录要求

每次 Run 必须在 [Architecture_Validation_Log.md](Architecture_Validation_Log.md) 中记录：

- Run ID、日期、执行者、实现 Commit 和工作树状态。
- exact Architecture / Design / Schema / Provider Contract Reference 与 Digest。
- Direct Claim Oracle Manifest / Fixture Digest、Claim / Need / Evidence 数量。
- 每个 Claim 的 Formal Mapping、Admission、Snapshot Member、Support Proof 和 Answer Claim Reference。
- Source Operation、Knowledge Update、Admission、Publication、Query、Review 和 Delivery 计数。
- 来源关闭方式、fail-fast 触发记录和 Context 隔离证据。
- exact Validation Run / Authority Store / CURRENT Namespace Reference，以及与生产 Reader、CURRENT、Premise 和 Root / State 解析隔离的机械证据。
- ACV-G00 至 ACV-G10 的逐项结果、失败反例和权威输出 Digest。
- 是否发现题目专用逻辑、自由文本逃逸或其他禁止捷径。
- 失败属于实现缺陷、Contract 缺口、Schema 不充分、架构增益缺失，还是实验自身无效。

在完整 Run 产生前，本 Case 状态保持 `Defined — Not Executed`；文档评审、静态推演和旧 Demo 测试不能替代执行结果。
