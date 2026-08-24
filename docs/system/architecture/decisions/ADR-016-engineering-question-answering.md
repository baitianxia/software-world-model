---
id: SYS-ADR-016
kind: system-decision
status: accepted
authority: normative
owners: [architecture, product, application, source, quality, security]
depends_on: [SYS-PRODUCT-SUCCESS, SYS-ADR-013, SYS-ADR-014, SYS-ADR-015]
derived_from: [FINDING-010-001, FINDING-010-002, FINDING-010-005, FINDING-010-011, FINDING-010-028, FINDING-010-029, FINDING-010-031, FINDING-010-057, FINDING-010-058, FINDING-010-060, FINDING-010-062, FINDING-010-064, FINDING-010-070, FINDING-010-071, FINDING-010-073]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/application_services/engineering_question_cognition.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py, src/software_world_model/interface/engineering_qa_source.py, src/software_world_model/interface/engineering_qa_live.py, src/software_world_model/interface/engineering_qa_browser.py, src/software_world_model/interface/engineering_qa_browser_ui.py, src/software_world_model/interface/engineering_qa_alpha_cli.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_cognition.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py, tests/test_engineering_qa_source.py, tests/test_engineering_qa_live.py, tests/test_engineering_qa_browser.py, tests/test_engineering_qa_alpha_cli.py]
---

# ADR-016：世界模型认知驱动的自适应工程调查

## Context

软件世界模型的核心概念从未改变：它是软件系统在精确 Scope、Context、Schema 和 Snapshot 上持久、版本化、可验证、可更新的外部认知模型，独立于任何 LLM 会话或隐藏状态，为 AI 提供稳定的系统认知基础。工程手册、结构地图、摘要、检索提示和面向人的说明都只是这份认知的任务或展示投影，不是世界模型本身，也不能把世界模型降格为文字缓存。

严格 `WORLD_MODEL` 已证明已发布认知可以在 Source-off 环境中跨任务复用；`DIRECT_INVESTIGATION` 则证明独立的直接源码调查可以形成受审核答案。两者都是必要能力，但单独作为普通用户默认问答均有边界：

- 只使用已建模认知会把尚未覆盖的用途、运行、配置、故障和变更影响问题过早关闭为 Knowledge Gap；
- 预先一次性检索并封包，会在调查真正开始前固定证据范围，无法像高级工程师一样根据每次发现继续追踪；
- 让回答模型直接挂载仓库，会把调查、事实选择、表达和自审混在同一上下文，扩大权限和共同盲点；
- 只把方法、分支和调用顺序平铺为答案，会产生代码走读而不是用户请求的工程结论。

本决定不重新定义软件世界模型，而是调整默认工程问答使用世界模型认知和软件来源的方式。

## Decision

默认工程问答采用版本化协议 `ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3`；`@3` 在既有自适应调查边界内增加 evidence-grounded atomic observation closure，不改变三种模式或来源权限。系统保留三种不可混淆的回答模式：

| 模式 | 固定权威输入 | 提问期来源访问 | 产品用途 |
|---|---|---|---|
| `WORLD_MODEL` | exact Snapshot / Read Set 的正式查询、View、Coverage 和 Support Map | 0 | 证明预构建世界模型认知可复用、可隔离和可评测 |
| `DIRECT_INVESTIGATION` | 绑定原问题和 exact Source Target 的 Evidence Packet | 显式授权只读 | 独立直接调查、诊断和产品对照 |
| `ENGINEERING_QA` | 调查结束后密封的 Question Evidence Package | Investigation LLM 提议、Source Broker 授权编译、隔离 Worker 受控执行 | 普通用户的默认通用工程问答 |

模式必须在创建请求之前由显式入口或部署配置决定，并在 Request、Result、Qualification、Audit 和展示中保持同一身份。`ENGINEERING_QA` 的来源调查是该模式事先声明的组成部分，不是 `WORLD_MODEL` 失败后的 `DIRECT_INVESTIGATION` fallback。运行中不得换标签、换权限或使用另一模式的历史资格。

`ENGINEERING_QA` 采用以下固定边界：

1. 原问题不可变。Question Understanding 可由模型提议用户目标、受众、响应语言、必须回答的结论和证据需求，但抽象层级只能使用 `DIRECT / USER_VISIBLE_EXPLANATION / IMPLEMENTATION_DETAIL`；模型必须选择满足原问题的最低细节级别，不能因为证据来自代码就自动选择实现层。流程问题的 material checklist 必须覆盖用户可见阶段、结果和重要状态变化/副作用。required class/path 必须是原问题直接需要的最小集合；不能因为某个 TEST/log/config modality 可用、可作佐证，或用户只要求“可核对依据”就把它提升为 material need。Application 必须校验其保留全部原问题条件、关系和输出约束。模型提议不是事实。
2. Application 从与请求 revision 对齐的 exact Snapshot / Read Set 形成 `World Model Cognition Context`。它向调查模型提供已发布的实体、关系、行为、约束、状态、来源、Coverage、Conflict 和 Unknown，使模型从已有系统认知出发，而不是从空白源码搜索开始。手册、地图和 locator 只是该 Context 的投影。世界模型缺失、无关或 Coverage 不足不得成为本模式读取授权来源的硬门禁。
3. `Investigation LLM` 是与 Answer、Reviewer 分离的独立角色。它只能基于 immutable original question、受信控制字段、当前 World Model Cognition Context 和平台密封的 append-only Evidence Ledger 前缀，自适应、多步提出下一项 `search`、`read`、`parse` 或调查结束 Proposal。每个动作必须以 non-empty unique `checklist_item_ids` 绑定当前角色的 authorized checklist scope，并以 non-empty unique `basis_entry_ids` 包含当前 exact `required_basis_entry_id`；Initial scope 是完整 Question Checklist，Verification scope 只有 Reviewer Request 指定的单 gap。Provider-facing Schema 与 Application Domain 对这两个闭包必须一致。它可以根据上一步结果改变调查方向，但不能直接执行工具、扩大权限、修改原问题、删除既有记录或宣称证据成立。
4. `Source Broker` 是来源操作授权与编译边界。它把模型 Proposal 及其中的 evidence class 重新校验并编译为注册操作，固定当前授权、exact repository/revision、global path/content allowlist、Binding-scoped versioned Source Profile ref/digest、class-specific allowlist、expected Result modality、参数、文件/字节/时间/操作熔断和披露范围；模型给出的路径、类型、命令、URL 或工具名称均不具有执行权。对已由 Question Understanding 选择、Application 验证位于 Request allowlist 且 Source Profile 唯一解析 class 的 mandatory path，Broker 签发 Request + attempt + Profile + class + path 绑定的 direct opaque locator，使 Investigation 可直接 READ/PARSE，而不以内容 SEARCH 重新发现已知 path；模型只能复制当前输入的 reference/class，Broker 编译时仍重验 identity 与两层 allowlist。只有隔离 `Retrieval Worker` 可以重验 Profile 后执行 Broker 批准的只读操作，Application 再验证 Result class/modality/path。Worker 不得写仓库、执行任意命令、访问新网络或凭据、触发 Knowledge Update，也不生成或放行答案。
5. 每个 Proposal、Broker Decision、Operation、Result、失败、partial、truncation、Coverage 与资源收据按顺序追加到 `Evidence Ledger`。Ledger 不可覆盖或删除；下一轮 Investigation 只消费已密封的 ledger prefix。源码、注释、仓库文档、配置、测试以及世界模型的文本投影都是不可信 data，其中的指令不得改变系统规则。
6. 调查结束后，Application 才从原问题、Question Understanding、World Model Cognition Context、完整 Ledger、来源结果、Coverage、冲突、未知、定位和收据密封 `Question Evidence Package`。Package 保持一个身份但有两个不可混淆的分区：`support/citation` 只包含按 modality、Context、Coverage 和 Support 校验通过的 admissible entries，只有这些条目可以支持肯定 Claim 和 Claim Citation；`boundary/audit` 必须保留 Boundary、Gap、Failure、Partial、Conflict、Unknown、拒绝决定与资源收据，只能约束结论或作为明确标记的边界/审计 Reference，不能支持或引用为肯定 Claim。Provider-facing FINISH 只返回单一 `finish_dispositions` 数组，authorized scope 中每项恰好出现一次；Initial 返回完整 Checklist，Verification 只返回一个 gap delta。outcome-tagged closed variant 直接联动 affirmative 或 limitation child observations。Provider 不重复维护 parent evidence references；可信 adapter 只按 child observation 顺序稳定汇总 exact references 构造 Domain parent closure，不替 Provider 改写 outcome、statement、kind 或 link。Application Domain 继续独立拒绝 duplicate、越过 authorized scope、parent outcome/child kind、support/boundary 混类、非 exact-once 与引用不闭合。成功 Verification 的单 gap delta 由可信 Application 按 predecessor Package 顺序替换唯一目标 disposition，非目标对象/digest 原样保留并形成新 Package；不得原地修改旧包，失败关闭时不得执行 delta merge。Verification 可以复用 predecessor admissible support，但其非支持 observation 必须逐条绑定当前 Verification Request 的 exact gap boundary；predecessor Package 的 cognition unknown、search candidate、rejection、gap 等 boundary 全部从本 attempt eligibility 排除。`required_evidence_paths` 只是 FINISH 前必须闭合的 mandatory minimum，不是调查上限；闭合后仍有 material gap、授权未读来源和足够 `SEARCH + READ/PARSE + FINISH` 预算时，Investigation 必须继续按结果调查，不能因同 class 读过别的文件而过早结束。每个 FINISH disposition 还必须从完整引用内容枚举与问题相关的原子 process/outcome/state-change/side-effect/limitation observations 并绑定 admissible references；宽泛 checklist 或代表性事实不能替代其余重要效果。上游 local state、exception 或 deny decision 不能替代拥有最终 HTTP/API status、error category 或 response body 的下游 response/exception mapper 完整证据；custom-handler wiring 只证明选择关系，transport status 与 application/response-body code 必须分别取证。未进入当前包的模型记忆、搜索印象或来源内容不得支持结论。密封只证明集合的身份、完整性、顺序、来源和版本，不使任何条目自动成为真，也不赋予其跨任务正式知识资格。
7. Answer 使用隔离的新上下文，只读原问题、已接受的 Question Understanding 与当前 Package，不挂载 Repository，没有 Source/World Model 查询工具、shell、网络、凭据或 Investigation 私有输出。每个 Claim 必须声明 `DIRECT_ANSWER / USER_VISIBLE_PROCESS / IMPACT_OR_SIDE_EFFECT / IMPLEMENTATION_EVIDENCE / LIMITATION` 之一并绑定 material checklist；表达 Package 实质事实的 Claim 还绑定其文本实际表达的 material observation identities。答案末尾只说明已保留 evidence scope/coverage boundary 的 `LIMITATION` 可使用空 observation-ID 集合并只引用 `boundary/audit`，但不能承载 affirmative fact、错绑 supported observation 或替代 Package observation 覆盖；直接回答 non-supported checklist 的 limitation 仍须绑定对应 limitation observations。恰好一个直接答案必须排首位，它在真实边界下可以是直接、诚实的 limitation。Gateway 保留 raw Answer；可信 adapter 只按受控 role 顺序稳定归一化 follow-up 的展示顺序且不改写任何 Claim 语义或 links，Application 随后拒绝乱序、漏 checklist/observation、observation 不在默认正文、证据分区或角色不一致，以及未引用 observation 所需 Package entries 的 Draft。流程、结果、状态变化和副作用属于用户可见结论。实现证据只在明确请求或支持 material conclusion 所需时产生；`USER_VISIBLE_EXPLANATION` 默认把 observation 已由其他用户可见 Claim 完整覆盖的实现证据留在开发者详情，但 uniquely material 的简洁实现核对依据必须进入默认正文，不能隐藏用户明确要求的 verification basis；`IMPLEMENTATION_DETAIL` 默认展开全部实现证据。每个实质肯定结论只能绑定 `support/citation` 分区中的实际支持，`boundary/audit` 分区只能收窄结论或形成未知/限制说明。若 Package 缺少下游 response/exception mapper 的完整支持，Answer 只能陈述已证明的上游机制并把外部结果保留为 limitation，不能用 framework default 或 wiring 补写最终 status/body。
8. Reviewer 使用另一隔离的新上下文，只读 immutable original question、accepted Question Understanding、当前 Package 与 Draft。它必须先从原问题独立形成 material conclusions，再显式列出 Application checklist 的遗漏；还必须从完整 Package evidence 独立形成带证据的原子 material observations，并分别列出 Package observation 与默认 Draft omission。随后成对比较 direct answer、默认 Claims、Package observations 与独立 observations；同一条件下的互斥 outcome、error category、state、ordering 或 side effect 必须令 `claim_consistency` 为 `FAIL` 并产生 Finding。任何外部 status/error/body 还必须能回到拥有该下游映射的 full-content implementation；上游 empty-context/exception/deny 或 handler registration 不足以支持该结果，缺少 owner 时必须判为 unsupported。若外部结果是 original question/accepted checklist 的 material conclusion，则使用 missing-evidence remediation；若只是 Draft 扩张，则使用现有 Package evidence 删除、收窄或改写，不得由 Reviewer 自创调查范围。同一局部条件同时被赋予 authentication-failure 与 authorization-denial 结果，或 transport status 与 response-body code 被混同，也必须失败。Reviewer 分别给出 direct answer、abstraction fit、material completeness、claim consistency、implementation-detail budget 的 `PASS / FAIL`；只有五项全 PASS、独立 checklist/observation audit 无遗漏、Finding 为空时才能派生 `APPROVED`。Reviewer 不能直接访问文件系统、Repository、shell、网络、凭据或 Source/World Model Tool，也不能执行其提出的请求。
9. Provider-facing Reviewer 不再分别声明顶层 decision、Finding prose 和 Verification Request。每个 Finding 必须选择一个 closed remediation variant：同包可修复项使用 `REWRITE_WITH_EXISTING_EVIDENCE` 并绑定 non-empty current-Package entry IDs；material 缺证项使用 `INVESTIGATE_MISSING_EVIDENCE` 并绑定 Checklist/可选 Claim、受控 evidence class 与不可执行 evidence need；不可恢复项使用 `REJECT_UNRECOVERABLE` 且不携带前两类字段。可信 Adapter/Application 以 reject → missing evidence → rewrite → empty-approved 的固定优先级派生 action；仅当派生 action 为 `MORE_EVIDENCE_REQUIRED` 时，才从首个 evidence-gap Finding 构造版本化 Verification Request，reject 优先时 request 必须为空。任何 rewrite reference 越出 Package、gap need 含路径/URL/命令/operation 或字段组合漂移都失败关闭。合法 Request 启动独立 `Verification Investigation LLM`：它使用全新上下文，只读该 gap、当前 Package 与当前 Ledger prefix，根据每一步新 Result 自适应提出下一项注册操作；predecessor Package 中已完整读取的 exact-source locators 与 gap 后 full reads 共同视为 consumed，相应 locator 不得再次 eligible，旧 raw Result 仍不重新披露。当前 attempt 最近一次 Broker rejection 还必须显式投影，使角色选择真正不同的合法 action 或诚实 FINISH，不得重复已拒绝 intent。Application/Source Broker 逐步重新校验和编译，Worker 执行并追加新的 Ledger Revision，随后由可信 gap-delta merge 密封新 Package、生成新 Answer 并从头独立 Review。Reviewer 取得可信 `verified_gap_outcomes`：只有由 `VERIFICATION_REQUEST` 形成的 typed `VERIFICATION_GAP` 才能取得该资格；已由 bounded Verification 穷尽、以当前 gap boundary 密封且在 Draft 中诚实保留的未知不得再次请求；Draft 自行扩张的非 material 下游结果只能同包删除或收窄。它不得回到初始 Investigation LLM，也不继承 Reviewer 会话；旧 Package 的 Review 不能放行新 Package。
10. 文件、字节、时间、操作、调查 step、Package revision 和模型调用上限必须在请求或 exact run 前作为防止失控执行的高安全熔断密封，同时包含确定性的 no-progress 条件。正式协议不得永久固定为一轮补证；可以在明确标记为非验收的最早方向体验中使用更窄的临时上限，但后续资格/验收必须冻结足以允许多步、结果驱动 Verification Investigation 的 revision/call/operation/bytes/wall-time/no-progress 熔断。达到上限、没有进展或不收敛时失败关闭；answerable 问题因此未获批准必须计失败，不得以 Limitation 取得 supported 结果。不得为了满足调用或成本上限删减原问题、调查需求、证据、Citation、独立审核或交付未通过答案。
11. World Model 的 source revision 必须与请求 exact revision 相等；显式版本比较问题则必须对每个分区分别绑定 exact Snapshot 与 exact Source revision。未对齐的旧 Snapshot 只能作为标记 `UNALIGNED_REVISION` 的导航候选，不能直接支持当前 revision 的结论，所有相关认知必须在请求 revision 上重新核实。
12. 高质量 Package 和已审核结论可以在 Delivery 之后异步提议 Knowledge Update，但必须重新执行 Evidence、Candidate、Admission 和 Publication 的全部正式知识契约。同步回答不等待该过程，其成败不改变已完成答案。
13. 核心流程、Prompt、调查和审核不得包含按问题、项目、语言、框架、关键词、符号、约定文件名、fixture 或评测 Oracle 分支的特判。新来源或语言能力只能通过受控、版本化的 Source/Profile Contract 增加。
14. 持续 loopback Web 可以在 listener 前密封一个有界 `Engineering QA Session Authority`，固定 exact product candidate、工程/Binding/
revision、World Model Read Authority、Source Profile/allowlist、Provider/model/configuration/qualification、角色契约、redaction、有效期和
每题/整会话熔断。它不授权未知问题或直接 dispatch。用户在页面看到该边界后提交问题，提交动作必须密封 exact question digest 与
session authority，System Owner 才能生成 server-owned request/run identity 和该题一次性 run authorization；浏览器不能提供或扩大这些
权威字段。每个动态角色输入仍须按第 6 条形成 exact one-use 子授权。题目失败只关闭该 Request，服务可继续；会话边界漂移、过期或总熔断
耗尽则拒绝后续题。浏览器 POST 还必须在 receipt 前证明 exact same-origin `application/json`，跨站请求不能用 loopback 位置冒充用户确认。
旧单题 prepared launcher 不是持续产品入口。

不同类型的包内证据保留各自 modality：世界模型表达已发布的系统认知及其 Coverage，exact 源码/配置表达该 revision 的静态实现，文档表达记录的用法或意图，测试表达静态预期或已密封的执行观察，模型 Proposal 只表达调查或回答建议。某一来源类型不自动拥有对所有命题的优先级；当相同 Context 中出现不兼容且无受控解析规则时，Package 必须保留 Conflict，答案不得静默选边。

任何把 World Model Cognition Context、Ledger 或 Package 片段发送给外部模型 Provider 的运行，都必须在 dispatch 前另行密封并授权 exact Provider/model/endpoint/configuration、角色、允许片段、redaction、secret reference 和输入 Digest。一个用户 run grant 只可绑定 exact Request/evaluation subject/Provider/Prompt/schema/角色集合与总上限；动态角色输入还须逐次形成 full-input/fragment digest 的一次性子授权，并由 Gateway 独立重验。任一 request 可能 dispatch 后失败或 outcome unknown 均不得 retry、replay 或切换 Provider。开发或文档接受不能推导该外部披露授权。

## Alternatives

- 把世界模型定义为工程手册或检索缓存：会丢失实体、关系、行为、约束、状态、证据、Coverage 与 Unknown 共同组成的软件认知语义，也偏离产品从始至终的核心概念。
- 把 `WORLD_MODEL` 直接改为可回源：会破坏 Source-off 复用证明和既有验收语义。
- 在 Knowledge Gap 后静默调用 `DIRECT_INVESTIGATION`：无法精确表达请求开始时的权限、证据和资格边界。
- 先一次性检索并密封包，再让 Answer 发现缺口：阻断模型根据实际发现自适应追踪，容易形成不完整或机械的代码走读。
- 让 Answer 或 Reviewer 直接挂载仓库并自行调用工具：来源权限、证据形成和响应判断无法独立审计，且共享上下文会放大共同盲点。

## Consequences

默认工程问答以世界模型认知为稳定起点，并允许独立 Investigation LLM 像高级工程师一样根据发现逐步调查；Reviewer 可指出自己的具体证据缺口，另一个全新 Verification Investigation 再独立补证。平台仍独占来源权限，回答和审核仍只使用双分区密封证据。代价是增加 Source Broker、append-only Evidence Ledger、调查状态机、Package Revision 和独立补证闭环，也必须分别证明世界模型认知的因果贡献、调查质量和隔离边界。

## Adoption state

本 ADR 从接受时起是 `ENGINEERING_QA` 的规范目标。`ITER-010 / SLICE-001` 已产生本地确定性的 `ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3` 协议、持久 World Model Cognition Adapter、Source Profile-bound Broker/Worker、mandatory-path direct locator、Ledger/Package、Answer/Review、五角色 closed input/output receipt、逐输入 disclosure/Gateway policy、DeepSeek 组合、Session Authority、逐题 server-owned Request/run 和固定 `8765` 的持续 Alpha launcher。返工还加入受控答案层级、逐 Claim checklist/observation links、默认正文投影、结构互斥 FINISH arrays、Reviewer 独立 checklist + evidence-observation comparison 与五项方向质量 Gate，其中 `claim_consistency` 显式阻断内部矛盾，下游 response ownership rule 阻断由上游局部状态推导最终 status/body。以上只有本地确定性验证；在新 product freeze 和单独授权的真实持续 browser 运行前，不证明真实 Provider、Capability Qualification、Product Validation、Slice Acceptance 或 Activation 已完成。旧 prepared launcher 仅保留历史运行兼容身份，不得标为当前 Alpha 产品。
