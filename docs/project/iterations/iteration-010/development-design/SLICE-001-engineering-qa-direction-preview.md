---
id: ITER-010-SLICE-001
kind: development-slice
status: authorized
authority: current-development
owners: [engineering, architecture, quality, product]
depends_on: [ITER-010-PROPOSAL, ITER-010-READINESS, ITER-010-VERIFICATION, ITER-010-PDR-010, ITER-006-RESULT-ACCEPTANCE, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, SYS-ADR-017, SYS-ADR-018, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-KNOWLEDGE-STRUCTURE-MODEL, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-QUALITY-ACCEPTANCE, SYS-QUALITY-SECURITY]
code: [src/software_world_model]
tests: [tests, validation/iteration_010_mvp]
iteration: ITER-010
coding_input: true
current_execution_decision_ref: ITER-010-PDR-012
current_execution_finding_refs: [FINDING-010-153, FINDING-010-161, FINDING-010-163, FINDING-010-165, FINDING-010-180, FINDING-010-181, FINDING-010-182, FINDING-010-183, FINDING-010-184, FINDING-010-185, FINDING-010-186, FINDING-010-187, FINDING-010-188, FINDING-010-189, FINDING-010-190, FINDING-010-191, FINDING-010-192, FINDING-010-193, FINDING-010-194, FINDING-010-195, FINDING-010-196, FINDING-010-197, FINDING-010-198, FINDING-010-199, FINDING-010-200, FINDING-010-201, FINDING-010-202, FINDING-010-203, FINDING-010-204, FINDING-010-205, FINDING-010-206, FINDING-010-207, FINDING-010-208, FINDING-010-209, FINDING-010-210, FINDING-010-211, FINDING-010-212, FINDING-010-213, FINDING-010-214, FINDING-010-215, FINDING-010-216, FINDING-010-217, FINDING-010-218, FINDING-010-219, FINDING-010-220, FINDING-010-221, FINDING-010-222, FINDING-010-223, FINDING-010-224, FINDING-010-225, FINDING-010-226, FINDING-010-227, FINDING-010-228, FINDING-010-229, FINDING-010-230, FINDING-010-231, FINDING-010-232, FINDING-010-233, FINDING-010-234, FINDING-010-235, FINDING-010-236]
current_scheduling_finding_ref: FINDING-010-179
product_goal_gate: V-000
product_goal_accepted_capability_refs: [ITER-006-RESULT-ACCEPTANCE]
product_goal_cross_domain_case_ids: [V-CHAT-XD-001]
product_goal_web_checkpoint_id: V-CHAT-EXPERIENCE-001
direction_preview_web_checkpoint_id: V-CHAT-EXPERIENCE-001
product_goal_direction_preview_checkpoint_id: V-PREVIEW-002
product_goal_reflection_gate_case_id: V-PREVIEW-002
product_goal_slice_gate_case_ids: [V-BROWSER-CHAT-MVP-BUILD-001, V-PUBLIC-OSS-AUTHORITY-ADMISSION-001, V-MODEL-TRANSPARENT-ROUTING-001, V-CHAT-EXPERIENCE-001, V-CHAT-001, V-CHAT-QUALITY-001, V-CHAT-XD-001, V-DIRECTION-QUALITY-001, V-PREVIEW-002]
---

# SLICE-001：真实浏览器 Chat 纵切

## Status and dependencies

`AUTHORIZED / PDR-012 PRODUCT BUILD ACTIVE / coding_input=true`。依赖 ITER-006 accepted 能力、当前 Proposal/Readiness/Verification、PDR-010
产品方向和现行 System Contracts；PDR-011 只保存历史失败，不再控制当前产品动作。

## 目标

尽快交付普通用户可直接体验的无认证浏览器 Chat，同时验证整体方向：

World Model Cognition → Main Engineering Agent → controlled read-only Source → Evidence/Citation → natural Answer → fresh independent Review → semantic multi-turn Web。

这是一条产品纵切，不是组件清单。世界模型、Agent、Evidence、Review 或 Web 单独完成都不算交付；POM/Maven-only 回答、静态回放、
一次性 CLI 和预制问题页面也不算。

## Current vs expected behavior

- 现有 loopback 页面、Conversation/Turn 骨架、受控 Source、Evidence/Citation 和 Reviewer 资产可复用；
- 历史候选曾在部分问题上形成答案，但长期出现代码走读、Maven-only 认知、遗漏副作用、Reviewer 漏判和 closed structured output 拒绝；
- run-052/053 在 Answer/Citation/Review 前失败，证明产品仍不可体验，不证明总体架构应停止；
- 最大风险是继续针对单题或输出字段碰答案，而没有区分世界模型构建/查询、Agent、Evidence/Answer、Review 与 Web 的最早偏差。

期望行为是用户在同一浏览器 Conversation 中连续提问、追问和纠正，Agent 先使用问题相关认知、再按 Gap 补证，每轮交付自然答案、Citation
和 fresh Review；实际行为仍会在答案形成前失败，因此本 Slice 必须直接修复并贯通该链。

## Product-goal contribution and cumulative integration

- 软件世界模型维护 exact revision 上持久、版本化、可验证、可更新的软件认知，包括结构、行为、关系、职责、影响、失败边界、Coverage、
  Gap、来源和检索入口；它不是文字手册、Maven 快照或 locator 缓存。
- 主工程 Agent 是回答问题的大脑：维护用户目标、指代、约束、假设、计划和观察；先利用问题相关世界模型认知，认知不足时提出受控源码
  操作，根据结果重规划并形成自然答案。
- World Model 的 query-relevant Java entity projection 若已给出 non-empty、non-truncated exact declaring-type target，第一次 Source search 只能
  从该 closed target domain 复制精确字面量；它是 cognition→Source 导航约束，不是 path authority，也不限制首次 Source action 后根据新
  Observation 继续发现其他 source-native symbol。
- exact literal 若命中同一可信 projection 的 canonical `source_path`，Application/Broker 还要把这些路径密封为 Search-only scope，让
  Worker 只在 scope 内验证 case-sensitive literal 并签发 locator；scope 不进入模型 action、不授予 READ authority，Broker 仍重验
  allowlist/Profile/revision/fuse，Coverage 也不能把 scoped complete 冒充全 Evidence Class complete。普通无 scope Search 保持原行为。
- Search operation 自身达到 file/byte maximum 只产生 operation-local Partial Boundary；只有 Broker 因 whole-Turn actual resource 不足
  拒绝 operation 才是 terminal Source fuse。两个层级不得复用同一 failure code，使主 Agent 把仍可用 Source 错当成已撤销。
- Application/Broker/Worker 拥有权限、exact revision、只读执行、证据身份和安全熔断；模型不取得直接文件、Shell、网络、凭据或写入权。
- fresh independent Reviewer 检查原问题是否满足、关键事实是否正确完整、Citation 是否支持、Unknown 是否来自真实 Coverage/Gap；它返回
  具体 Finding，不替主 Agent 规划或执行工具。
- 每个 comprehensive/focused Review 都必须逐字绑定 current User Message，并以 typed requirement-coverage assessment 独立判断 Draft 是否
  回答本轮完整目标；prior Answer/Work State、主题相同或 Claim supported 均不能替代。回答旧问题或遗漏本轮 material distinction/order/Unknown
  时必须形成 global Finding，未 fully addressed 的 Review 不得批准或交付。Primary goal 同样以 current User Message 为当前权威；failure
  follow-up 必须区分 abrupt completion 与 unsuccessful normal return，并把 source-visible local reachability、prior effect、persistence、
  commit/rollback、remote/consumer effect 分别回答。
- ANSWER Claim 除 SUPPORT Observation IDs 外，还必须从每个 citation-bearing selected Observation 选择至少一个直接 supporting ref，且只
  投影最小 exact Citation set。broad Search inventory 不因一个结果 material 而整批进入 Browser；Application 从 authority receipt 重算
  selected-ref identity，ref 漂移失败关闭。
- Reviewer Findings 的 Primary successor 必须同时取得 exact rejected Draft、ordered Findings 和 Review digest；三者缺失或 Turn/Work
  State/digest/reference domain 错配时在 Provider 前失败关闭。无需新 Evidence 的同包 rewrite 以 rejected Draft 为 exact edit base，只按
  Finding 删除、收窄、限定、重排或重述，不增加新的用户可见物质断言；global completeness 只能枚举原正文已有断言。final preflight
  重复 exact SUPPORT/BOUNDARY ID domains 和 active rewrite contract，但不新增 Evidence/Tool/Review/Delivery authority。
- Claim coverage 是 semantic/many-fragment-to-one，不要求每个 phrase、call 或 sentence 单列 Claim；matching exact-revision attribution 是
  sealed provenance context，不能制造 redundant Claim。纯 material evidence boundary 不属于 affirmative Claim；Limitation 保持零 Claim，
  同包 global-completeness rewrite 通过删除/收窄无 SUPPORT 的相邻 diagnostic 收敛，只有既有 assertion 有 current SUPPORT 时才可转 Answer。
  structured Boundary ID 是非正文 binding，不要求显示 opaque ID 或 raw Observation。
- 每个 Draft 先取得 comprehensive Review。Application 从 cited full Java Source 与 Claim 结构投影 exact caller/callee challenge，并为每个
  Package Boundary 投影 ordered relevance challenge；`SOURCE_SEARCH / LITERAL_TEXT_SEARCH_HIT` item 被后续
  `SOURCE_READ / EXACT_STATIC_SOURCE_TEXT / coverage_complete=true` 闭合时使用 `RESOLVED_ACQUISITION`，其余使用
  `BOUNDARY_MATERIALITY`。不同 opaque locator 只能按 authorized exact canonical resource path（去除规范行后缀）关联，不能 basename/fuzzy
  匹配，也不得因 Draft 未声明 Boundary ID 而跳过；存在任一 challenge 时再执行 fresh focused Review。两类投影都只是 review lead：Reviewer 用
  closed semantic scope 区分 caller invocation、local order、callee/return、external-state effect 和 consumer-visible effect，并从每个 challenge
  直接复制由 trusted kind/reference flag 派生的 `allowed_exact_dispositions`，区分 material
  bound Boundary、resolved/non-material audit-only 与 not-disclosed。Response Control 重算 exact ordered assessment set；Observation prefix 由
  Application 直接绑定，不作为 Provider output copy obligation；每 Turn `11 Agent + 4 Review = 15`，不提高 Tool/Source fuse、retry 或 dispatch
  authority。
- Reviewer 必须在一次完整 Draft audit 中报告全部已观察到的独立 material defects；Primary 的同包 replacement 必须解决全部 ordered
  Findings，而不是只改第一个或无关 Boundary。focused Review 的 exact DEFECT Claim indices 必须等于 exceeded caller challenges，exact
  Finding codes 必须等于 exceeded caller 与 audit-only relevance assessments 所引用的集合；focused role 不引入 comprehensive Finding。
  `decision` 只由 Reviewer 按 typed body 修复，Application 不生成 approval。Finding code 仅是 local identity；只有完全未被 focused
  assessment 引用的重复 code 才稳定 disambiguate，且不得改变 message、binding 或顺序；任何被引用的重复 code 仍失败关闭。
- same-Package replacement 若完整 Draft 字段仍等于 exact rejected Draft，decoder 必须拒绝，不能只改 Work State。closed-contract repair
  显式禁止原样复制 prior invalid output，并从 local typed failure 派生不授权事实/Tool 的 convergence directive：repeated Source query 只能换
  sealed legal literal，或在没有新目标且 response domain 允许时用已有 Boundary 收敛；focused DEFECT/exceeded mismatch 必须保留 prior
  Review 的 exact decision/Claim assessments/requirement coverage/Findings semantic anchor，只重建 focused challenge assessment arrays；
  Application 在 decode 前恢复 anchor，且它必须穿过不同 category 的最后一次 bounded repair。challenge-bound Finding set mismatch 使用专用二选一 directive：每个 retained Finding
  绑定一个 exact challenge 的 allowed audit-only disposition 和同一 code；若全部 challenge material，则删除 unbound Findings 并 APPROVE。
- `LIMITATION` 始终零 Claim。Reviewer 不得要求添加 exact-answer detail、interface/search inventory 或 Claim；pure、relevant、正确绑定的
  Limitation 不因 Package 无法产生用户原本要求的 full answer 而成为 completeness defect。已有 opaque Boundary ID 不能误报 missing binding，
  Search hit/interface declaration 不能冒充 implementation、remote effect 或 consumer-visible evidence；相邻 affirmative diagnostic 只能
  删除/收窄为 pure material boundary。
- DeepSeek fallback 的 listener preparation 只密封 non-dispatching decision；真正的 600 秒 active receipt 在 trusted Ark unavailable 后的 first
  DeepSeek preflight 以同一 plan 激活，并重新核验 900 秒 pricing freshness、闲时/override、run authority 和完整质量预算。激活与任何拒绝都
  发生在 credential/TLS/HTTP 前；后续 request 不得重新延长 receipt。
- Engineering Chat DeepSeek runtime ref `DEEPSEEK_PERSISTENT_VERIFIED_TLS_HTTP11_NO_RETRY@3` 在每次 qualified transport call 前检查
  fully consumed socket：non-blocking readiness 为可读/异常，或自最后 HTTP completion 起 idle ≥60 秒时先关闭，再由 exact base
  transport acquisition。轮转仍受 transport lifetime 3 次 TLS 和每 session 20 dispatch 约束，不构成 request retry；base Adapter、
  Conformance identity与HTTP开始后的 outcome-unknown/零 replay语义不变。
- World Model evidence-tool adapter 必须把 model-facing SUPPORT 与 BOUNDARY 按认识论语义分区：SUPPORT 顶层不得复制 global
  coverage/conflict/unknown，只保留 novel affirmative item 及其 per-item coverage；完整 Context、Ledger、receipt 继续绑定 global
  Coverage，且该全局边界只在 BOUNDARY 中呈现。
- SUPPORT 的 typed item domain 只含 `ENTITY/RELATION/BEHAVIOR/CONSTRAINT/STATE`；`COVERAGE/EVIDENCE/UNKNOWN` metadata 不取得
  affirmative Claim 资格，metadata-only Context 形成 `WORLD_MODEL_HAS_NO_SUPPORTED_ITEMS` Boundary。
- World Model query relevance 只使用语义 value：表示层 value 与 path 公共前缀不作特征，cohort-common exact token 不作 anchor；强 exact
  match 存在时关闭 prefix-only 和低于 strongest score 75% 的弱尾部。排序必须确定性且不按工程、题面、业务词、类或方法特判；Profile
  incomplete 的实现细节继续形成 Source gap，不能由 relevance 补造。
- 已选 typed relation 必须在同一 Snapshot/Revision 和剩余 item/byte bound 内紧邻保留 exact subject/object 的直接 Entity state；只作一跳
  graph closure、按 subject→object 与 digest 去重，不恢复词法弱尾部或递归邻居。verified endpoint path 只进入既有 Source navigation，
  Broker/Source authority 不变。
- original User Message 精确点名 sealed Source allowlist 的 top-level scope 时，multi-Profile projection 在 relevance ranking 前排除 formal
  Coverage root 与其完全不相交的非 repository-wide Profile；其 affirmative item 与 Profile gap 都不得进入 Context。selector 只来自原始
  问题的 exact boundary match，模型 query 不能改写；mismatch 是 Coverage Boundary 而非授权拒绝，repository-wide partial Profile 仍可参与。
- Boundary/Audit 的完整保留不要求全部写入用户答案。只有仍限制 current User Message material requirement 或用户明确询问的诊断才可披露；
  已被后续 SUPPORT 闭合的 acquisition diagnostic 和不限制具体结论的 global inventory/coverage metric 通常只留 audit。Application 不自动
  删除 retained Boundary；focused Reviewer 只有在实际披露的每个 fragment 都 material 且 Draft 已绑定 Boundary 时返回
  `MATERIAL_TO_USER_REQUEST`。resolved diagnostic 用 `RESOLVED_AUDIT_ONLY`、其他非物质 Boundary 用 `NON_MATERIAL_AUDIT_ONLY`，均以
  `claim_index=null + requires_evidence=false` 阻断泄漏；未绑定且未披露才可 `NOT_DISCLOSED_IN_DRAFT`，从而保留用户明确询问诊断本身的合法路径。
- 所有普通 affirmative detail 与 Boundary 同样执行反事实相关性测试：删除后仍完整回答并诚实定界的邻接 declaration/helper/provenance
  必须省略，不能为 Draft 自己引入的细节扩大调查；code-generation/tool provenance 不能从 path/package/import/symbol/directory convention
  推断，material claim 必须有 direct current SUPPORT。
- Reviewer 指定现有 Package 足够时，同包 rewrite 必须生成 successor Work State/Draft/fresh Review；Package origin 保留首次封装该证据集的
  Work State，不随 rewrite 改写，也不能被 Response Control 当成当前 Delivery Work State。任何新 Observation 仍形成新 Package。
- closed-shape repair 的 copy obligation 只覆盖 prior output 中已经存在、allowlisted 且可按 schema 对齐的值。完全没有既存 allowlisted item
  value 的 invalid array 子树必须从 sealed schema/domain/template 重建，不继承原长度；其余 array 长度/顺序继续守恒。Application 在 Proposal
  decode 前只把 repair 对可对齐既存值的漂移恢复为 prior exact value，再执行原 closed-schema、tool catalog、Context/Evidence 和 completion
  校验；它不生成缺失字段、不解释 unexpected key、不扩大工具或把 raw drift 追认为授权语义。一个 role step 最多有两次 same-profile repair；
  第二次仅在前一 repair 的 local validator category 严格前进时允许，重复/倒退 category 仍停止，且只能消耗现有 15 次 per-Turn authority 的
  剩余 slot，不构成 Provider retry、fallback eligibility 或预算扩张。
- Source resource receipt 的 file budget 必须进入与 effective catalog 同源的 model-facing policy。`64/64` 等 exhausted 状态同时清空
  Source Search/Read operation 和 read options；`63/64` 且已有 locator 时继续保留唯一 READ slot。预算状态不代替或伪造 Broker terminal
  denial，Decoder 仍从受信 receipt 重算。
- Claim inventory 与 fresh Reviewer 都必须把 heading、table column、list lead-in、label 或 surrounding sentence 继承的 category、scope、
  condition、certainty、negation 视为 contained assertion 的一部分；漏 qualifier 是 global completeness Finding，错误 qualifier 是 concrete
  defect。不得只审核脱离容器的窄 action/outcome Claim。
- 空新 Conversation 的语言 policy 必须在任何 external attempt 前覆盖单数、复数与类别性指示表达；例如没有先行对象的“这些/那些/此类”
  只能形成零 dispatch Clarification。该规则只看 versioned language capability 和可信 Context，不按业务名词、问题或工程分支。
- 失败 Turn 的 Browser projection 与显示必须区分 execution-stage failure 和 raw Provider classification/code。raw evidence 不自动等于
  trusted unavailable verdict；UI 不能隐藏该差异，也不能据此启动 fallback。
- Provider HTTP failure 的安全 status/code/type/request-id 必须由不改变 request/transport 的 Gateway decorator 在 inner terminal 后绑定
  call/request/isolation 密封，并以 status + evidence digest
  贯穿 replay/egress/model receipt/Turn/attempt。当前可信 owner 只接受 typed pre-HTTP unavailable，或密封
  `{402,408,425,429,500,502,503,504}`；auth/config/client status 和没有 digest 的字符串/status 失败关闭。fallback profile 的资格、standing
  authority 派生与 fresh admission 仍逐 route 独立验证；外围 evidence implementation 不改变 exact Provider Conformance identity，也不放宽
  既有 manifest/config/model/fixture/validity 校验。
- Source content Search 不能把 authorized module/directory/file-name path segment 当作正文 literal。Broker 必须在 Worker 与资源消费前 typed reject；该
  Boundary 不等于 Source 撤销，并且在 Source 仍可用时不满足 material follow-up。Primary 必须读取 latest sealed Broker decision、禁止重复
  rejected query，并改用可能在目标正文逐字出现的不同 source-native literal，不能交付假 Limitation。
- Worker 遇到 exact filename-stem anchor 时，必须先检查全部 basename equals/contains query 的安全 cohort；取得 case-sensitive 正文 hit 后可在
  进入低排名 fallback 前以 `SOURCE_SEARCH_FILENAME_MATCH_EARLY_STOP` Partial 停止。结果必须披露 truncation/coverage，实际读取继续计入
  56/64 fuse；无 anchor/hit 或 cohort 有安全、编码、fuse gap 时继续原 bounded scan，不能冒充 corpus complete。

该纵切在 ITER-006 已接受的版本化知识能力之上，第一次把世界模型认知、主工程 Agent、受控源码、逐 Turn Evidence/Review 和语义多轮 Web
组合成普通用户可直接判断方向的产品结果。

## System contracts and invariants

适用 Owner 为 SYS-ADR-018、Engineering Conversation、Agentic Task、Evidence/World Model Answering、Source Artifact、Security 和 Local
Browser contracts。若实现证据改变跨模块语义，先按 Finding policy 写回唯一 System Owner；局部实现由代码和测试决定。

Conversation/Turn/Context 由 Application 拥有；模型不直接访问 Repository、FS、Shell、network、credential 或 write；源码固定 exact
revision 且只读；每个重要结论绑定 Citation；prior Answer/Review 与 Provider hidden memory 不取得事实权威；Reviewer 必须 fresh 且独立。

## Interfaces and affected code

允许修改 `src/software_world_model/` 中的 Application、AI infrastructure 和 Interface 产品路径，以及 `tests/`、
`validation/iteration_010_mvp/` 中与纵切直接相关的定向验证。具体文件由最早偏差证据决定，
不得预先扩大重构范围。

## 唯一工作计划

1. 使用已有 run-052/053 trace 和当前代码建立最小分层证据表，确定最早可证实偏差；不得从最终错误文案猜根因。
2. 只修复该 Owner 的最小通用问题。禁止题面、关键词、工程名、符号、类、方法、fixture、示例答案或 Provider/model identity 分支。
3. 在一个非 POM/Maven 的代表性工程问题上打通首轮：世界模型有可观察的行为/职责/失败边界认知贡献；Gap 触发 Agent 受控读源码；页面
   得到自然 Answer、可打开 Citation 和本轮 fresh Review。
4. 在同一 Conversation 完成上下文追问和纠正/深入/总结；新 Conversation 用模糊指代验证隔离。每轮有独立 Request/Evidence/Review；
   prior Answer 和 hidden memory 不作事实证据。
5. 运行最小 targeted、startup、安全和失败真实性测试。链一旦可操作，立即启动固定 loopback 页面作为“开发体验候选”交给用户，
   requires_result=false；该候选不得称为 MVP、质量 PASS、方向 PASS 或完成。
6. 候选交付后不暂停、不等待新的用户决定，立即在同一候选上运行至少两个未参与修复的异质问题，并让 actual current Codex 在隔离任务中
   回答相同问题。独立 exact-source 证据和技术复核判断双方正确性、完整性、Citation、Unknown 和用户目标满足度。只有系统重大错误为 0、
   逐题无物质退步、总体严格更优且有非 locator 世界模型价值，才能称为 MVP。
7. 质量不足时回到第 1 步继续同一 BUILD。停止同 signature 的无新证据外调，但不停止产品开发，不切备用碰答案，不创建失败 Result/PDR。

## Acceptance scenarios

| Case | 必须可观察的结果 |
|---|---|
| V-BROWSER-CHAT-MVP-BUILD-001 | 兼容技术 ID；持续完成开发体验候选及其质量资格，不能因 ID 含 MVP 就声明完成 |
| V-CHAT-XD-001 | 同一答案链同时使用问题相关世界模型认知和 Gap 驱动的受控源码证据，且二者来源区分正确 |
| V-CHAT-001 | 至少三轮语义连续：首问、追问、纠正/深入/总结；新 Conversation 隔离 |
| V-CHAT-QUALITY-001 | 每轮自然回答、重大错误 0、关键结论有可打开 Citation、fresh Review 无重大漏判 |
| V-MODEL-TRANSPARENT-ROUTING-001 | 产品只使用首选/备用执行角色；只有可信不可用结论触发备用，输出或审核失败不触发 |

首次 Web 交付只证明“候选可操作”，不冒充 MVP、方向、质量、稳定性或 Production PASS。交付后必须立即继续质量资格：系统自身重大错误
为 0；逐题相对 current Codex 无物质退步；总体严格更优；至少一项重要价值来自非 locator 世界模型认知。Codex 不是 Oracle 或裁判。

## Compatibility, data and security boundaries

当前公开 mall exact revision、只读 Source、既有配置路线、披露、预算和 loopback evaluation 属 standing scope；每个真实 dispatch 自动
记录 exact source/product/session/route/disclosure/budget，人工重复授权请求为 0。只有私有/新 Source、新接收方或账户、扩大披露/预算、
外部写入、非 loopback、Production 或破坏性操作才申请权限。

首次体验前不做 full regression、hidden、第二工程、持久化、性能优化、完整四路因果消融或 Production。它们是方向确认后的夯实顺序，
不是当前权限停工点。模型调用次数和成本不能降低单个已开始 Turn 的调查、答案或独立审核质量。

开发只有在用户明确 STOP/REDIRECT/REJECT、真实 scope delta 的 exact 请求已发出且独立安全工作穷尽，或不可绕过的安全禁止时才能停。
普通答案、格式、测试和 Reviewer 失败只关闭对应 Turn 或完成声明。

strict WORLD_MODEL 与显式 DIRECT 兼容入口不得静默串线。Secret 不进入仓库、Prompt、日志、Evidence 或页面；late/unknown/不合格结果不得覆盖
已交付答案。既有 route/disclosure/budget 内的公开源码评估继续使用 standing authority，真实 scope delta 才失败关闭并申请最小权限。

## Architecture reflection checkpoint

首次体验后以真实 Turn 判断 A1/A2/A3/A5/A6，并在后续跨工程阶段判断 A4。current Codex 是强基线，独立源码证据负责事实，独立技术复核负责
质量判断；模型答案不是 Oracle。结论不足时继续 REWORK 当前 Slice，不因一次失败停止产品开发。

## Open questions and implementation risks

- 最早偏差究竟位于世界模型投影、Agent 工作状态、typed evidence/answer contract 还是 Reviewer；
- 世界模型非 locator 认知能否稳定参与不同类型问题，而不是只在示例题出现；
- Agent 是否根据观察重规划并在证据充分时结束，而不是固定流水线或无界探索；
- 三轮 Chat 是否真正使用当前 Context，同时隔离新 Conversation；
- Reviewer 是否能阻断物质遗漏和错误 Citation，而不接管工具规划。

这些问题由 trace、最小复现和未参与修复的异质问题回答，不通过题面特判或重复外调碰答案。

## Findings

当前纠偏由 PDR-012 拥有；FINDING-010-153、161、163、165、191、204、206—235 与既有 Results 保留计划自锁、答案前失败和最新真实/本地质量归因证据。run-103 已在周一 12:13 CST off-peak 完成五问：Ark 4 个 sealed 429、DeepSeek 39/39 completed，shared budget 将逐题合计保持为 `14/10/8/0/11`；Q2 ACCEPTED、Q4 zero-dispatch Clarification，整体仍 FAIL。Q1 的 focused repair 会擦除已识别 DEFECT/Finding，Q3 沿用上一 goal且混淆 abrupt-failure local reachability 与 rollback/effect unknown，Q5 的 duration expiry 仅为 timing-supported inference。current `@29/@19/@24` 以 Application-restored Review semantic anchor 和 current-requirement/failure-condition contract 修复；定向 `137/137` PASS。run-104 随后密封 Q1 的 Ark 1 + DeepSeek 14 exact-budget failure、Q2 的 Ark 429 + DeepSeek sealed HTTP 402 与 Q4 zero-dispatch Clarification；Q3/Q5 按同签名停止边界未发送。Q1 的 first divergence 是 comprehensive redaction 丢失 trusted Boundary presence；current `@30/@20/@24` 以 presence-only Package/Draft counts 修复而不转移 focused ownership；模型协议 `37/37`、相邻定向测试 `137/137` PASS。run-105 按用户明确要求执行 Ark-first recheck，Q1 唯一 Ark dispatch 仍为 sealed 429，DeepSeek 于周一 peak 在网络前拒绝，Q4 zero-dispatch Clarification 通过，Q2/Q3/Q5 未重复同签名外调；它不产生 current candidate 的质量 verdict或代码变化。用户随后明确报告 Ark 流量问题已处理，materially new evidence 已出现；下一项是文档/可信父门禁、提交并立即执行 fresh run-106。新实现发现按
`FINDING-010-235 / run-106` 已完成该 successor：Ark 前 6 个 call completed，第 6 个 malformed Primary JSON 被 current validator 阻断，
第 7 个 fresh same-profile repair 在 HTTP dispatch 后 outcome unknown，按 contract 无 retry、无 fallback；Q4 zero-dispatch Clarification
继续通过。未发现本地 contract 偏差，下一 clean run-107 先执行未重复的 Q2/Q3/Q4/Q5，并在没有重复 stop signature 时补 Q1。

`FINDING-010-236 / run-107` 已执行 Q2/Q3/Q4/Q5：Q2 为 Ark pre-HTTP TLS unavailable 且 DeepSeek peak-window zero-network denial；Q3/Q5
为 Ark HTTP 400 `InvalidParameter / BadRequest`；Q4 为 zero-dispatch Clarification。400 non-eligible 行为正确，但 optional Provider
parameter-name 未进入安全 evidence。current candidate 升级 evidence/SQLite/Egress 与 Ark conformance negative oracle，禁止 message/body
持久化且不改变 route；fresh Ark Conformance 后 run-108 先重放 Q5。

[实现发现回写规则](../../../governance/implementation-feedback-policy.md) 写入 [Findings index](../findings/README.md)，不得用 Finding 创建新的
普通失败停工点。

## 交付

第一条真实三轮链完成后立即提供启动命令、固定 URL、exact product/source revision、可操作页面和已知限制，并明确标记“开发体验候选，
质量未通过，不是 MVP”。该交付无 Result、不移动游标；开发不停，立即继续同候选异质质量检查和 current Codex 同题比较。只有质量资格
通过后才以 MVP 交给用户判向；最终方向与验收事实再在适当的完成记录中密封，不把过程治理放回产品关键路径。
