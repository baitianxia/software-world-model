---
id: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
kind: system-contract
status: current
authority: normative
owners: [application, source, quality, security]
depends_on: [SYS-ADR-017, SYS-ADR-018, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-CONTRACT-AI-MODEL-GATEWAY]
derived_from: [FINDING-010-097, FINDING-010-098, FINDING-010-099, FINDING-010-100, FINDING-010-101, FINDING-010-102, FINDING-010-103, FINDING-010-104, FINDING-010-105, FINDING-010-106, FINDING-010-109, FINDING-010-113, FINDING-010-116, FINDING-010-117, FINDING-010-120, FINDING-010-121, FINDING-010-125, FINDING-010-128, FINDING-010-132, FINDING-010-133, FINDING-010-136, FINDING-010-138, FINDING-010-139, FINDING-010-154, FINDING-010-156, FINDING-010-159, FINDING-010-160, FINDING-010-169, FINDING-010-170, FINDING-010-172, FINDING-010-176, FINDING-010-177, FINDING-010-183, FINDING-010-191, FINDING-010-192, FINDING-010-193, FINDING-010-194, FINDING-010-195, FINDING-010-196, FINDING-010-197]
code: [src/software_world_model/application_services, src/software_world_model/ai_infrastructure/conversational_engineering_model.py, src/software_world_model/interface]
tests: [tests]
---

# Engineering Conversation

## Purpose and scope

本契约定义 `CONVERSATIONAL_ENGINEERING_AGENT@1`：普通用户默认的工程 Chat。主工程 Agent 在固定工程和 exact revision 上持续理解多轮
对话，使用软件世界模型认知和受控只读来源工具解决用户问题，并以有引用的自然答案或诚实 Limitation 响应。它不是给单轮
`ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3` 页面增加历史消息，也不是开放 shell、仓库写入或任意网络的自治编码 Agent。

本契约只改变 Agent 如何解决问题和维持对话。软件世界模型的正式知识路径、严格 `WORLD_MODEL` Source-off 模式、显式
`DIRECT_INVESTIGATION`、exact revision、Broker/Worker、Evidence Ledger/Package、Citation、Provider 授权、安全隔离、独立审核和
Response Control 放行边界继续由原 Owner 拥有。

## Ownership and state separation

- Conversational Task Control/Application 是 Conversation、Conversation Revision、Turn、User Message、Accepted Correction、Agent Work
  State Revision、Agent Attempt、Tool Authorization/Observation、Evidence Ledger/Package reference 和不可变 Turn Result 的唯一写者。
- Application-owned committed Work State repository 只保存成功 Turn 已密封的 Conversation successor。每个 Provider attempt 的 executor、
  Ledger、Package、Draft 与 Review 是 attempt-local；失败 attempt 不写 committed repository。fresh executor 可从 exact sealed Context 读取
  已提交 predecessor，但 fallback-route executor 不能从 preferred-route executor 私有内存取得输入。
- 软件世界模型由 Knowledge Engine/Snapshot Owner 持有，可跨 Conversation 复用；Conversation Binding 只通过 Application-owned
  Cognition Capability Manifest 引用同一 repository Binding/exact revision 上一个或多个 profile-specific exact Read Authority。对话工作
  状态不准写入 Snapshot 或冒充正式知识，多域投影也不创建 mixed-profile Snapshot/Read Set。
- 主工程 Agent 只提交 Goal/Hypothesis/Plan/Tool/Answer Proposal。它对解决过程具有认知控制，但不拥有业务状态、权限、来源、证据、正式
  知识、Review Decision 或 Delivery Authorization。
- Source Broker/Worker 拥有只读来源 Proposal 的校验、编译和执行；Reviewer 只提交独立 Assessment/Finding；Response Control 独占最终
  Authorization 与 Delivery。

系统必须区分三类输入：

1. **World Model Cognition**：Cognition Capability Manifest 所绑定的 exact profile-specific Snapshot/Read Set 上可跨会话复用的软件认知
   及其 Coverage/Unknown；Manifest 固定 repository/revision、ordered Read Authorities、Schema/Context/Coverage/digest、query/view
   capability+version、已覆盖认知维度与显式 unsupported/partial/unknown；
2. **Conversation Work State**：当前对话目标、已确认实体、用户约束、纠正、开放问题、假设、计划、已观察结果和未完成子任务；
3. **Turn Evidence**：本 Turn 经受控世界模型查询或 Broker/Worker 取得、用于当前答案的 Ledger 与密封 Package。

对话记录、工作状态和先前助手答案都不能自动成为 Turn Evidence。任何沿用结论必须由当前 exact revision 的 admissible evidence 重新支持。

历史 Turn 的 Evidence 只有在 `repository revision + Binding + World Model authority + Source Profile + allowlist + content digest + coverage`
全部 exact match 时才可作为本 Turn 的复用 candidate；Application 仍须按本 Turn 的问题、目标和证据需求重新校验，并把实际使用项重新绑定
到本 Turn Package。旧 Answer Authorization、Review Decision、Limitation、未密封 Tool Result、Provider memory 或隐藏状态一律不可复用。
用户陈述、纠正和偏好可以改变对话目标或待验证假设，但不能成为 Source truth 或支持软件事实。

对于成功且已获 Delivery Authorization 的历史 Turn，Application 可以从其已交付 Citation projection 中选择同 revision 的 full-resource
Source Citation，按 canonical resource 去重并以固定上限形成 current-Turn revalidation candidate。candidate 只携带 prior path、modality、
content digest 和 origin identity，不携带 source content、旧 Observation 或 Claim authority；Source Broker 必须为 current Request/attempt/
Profile/class/path 重新签发 direct opaque locator。只有本 Turn 实际 READ 后由 Worker 返回完整相同 path/coverage/modality/content digest，才
形成新的 current-Turn SUPPORT、Ledger Result、Citation 与 Package closure；任一 identity/content mismatch 失败关闭。search line hit、
World Model Citation、失败/未授权 Turn、不同 revision 或新 Conversation 不得生成该能力。

## Conversation and turn invariants

1. Conversation 在 listener/session 启动前固定产品版本、工程/Binding/exact revision、World Model Cognition Capability Manifest、Source
   Profile/allowlist、工具目录、versioned Conversation input policy、`preferred → fallback` route、两个角色各自的 exact execution-profile ref/digest、
   披露范围、有效期和每 Turn/整会话高安全熔断。产品、主 Agent、Reviewer 和 route branch 只读取通用 route role/profile reference、顺序和受信 availability verdict，
   不得使用 Provider/model 名称选择行为或质量标准。每个 execution profile 的运行配置内部绑定 Provider/model/endpoint、Adapter/plugin、资格、transport 与 admission
   plugin；浏览器不能扩大这些边界。current Artifact Session Configuration `@4` 必须以 zero-based fixed order 列出各 cognition Profile 的
   Profile/Schema/Source Binding、selected Snapshot、ordered/Snapshot Bundle digest 与 exact file digest，并绑定两个 route profile、plugin
   ref+digest、形成通用 dispatch-admission receipt 所需的 closed trusted inputs，以及 `PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY@1` 的明确父
   ref/digest、Source 公开性/upstream/license/exact commit-tree、Provider/account/disclosure/budget/time/loopback 边界；装载时逐项重算后才能
   派生 exact `PUBLIC_SOURCE_MODEL_SESSION_AUTHORITY@1` 与 Application-owned Manifest authority。旧 `@3` admission、`@2` 多 Profile 与
   `@1` 单 Profile 只作为 exact-human-delta 历史兼容读取；current preparation 缺少任一 standing/execution profile/plugin 或必需 admission
   input 必须失败关闭，不能取得新 live Session 资格。
2. 每条 User Message 创建不可变 Turn。Application 从完整历史确定性选择满足本 Turn 所需的相关上下文，密封输入消息、被引用 Turn、有效
   用户约束、当前工作状态和摘要的 identity/digest；不得直接依赖 Provider 会话记忆或无边界拼接全部历史。
3. 主 Agent 必须处理追问、指代、纠正、深入、收窄和总结。若指代在密封上下文内仍不唯一，必须请求澄清或给出明确条件化解释，不能把
   猜测写成事实。对于没有 message、Turn、Work State 或 reviewed conclusion 的新 Conversation，Binding-owned、按语言显式版本化的 input
   policy 必须先识别依赖先行对象的表达，包括所注册语言中的单数、复数和类别性指示；命中时由 Application 在任何 World Model、Source、credential 或 Provider attempt 前要求用户明确
   对象。这个响应只是 input clarification，不含工程事实，不创建 Evidence Package/Review/Delivery，也不能用于非空 Context 或普通显式首问。
   Application 必须从密封 Request 与 Binding 重新计算 policy 命中和澄清文本；Turn executor 或 Provider 自报 clarification quality 不能取得该
   例外。
   用户纠正形成新 Revision 并标记被取代的对话假设，不删除原消息、证据或失败结果。
4. 一次 Turn 失败只密封该 Turn 的失败或 Limitation；Conversation 和 listener 继续可用。后续 Turn 不继承失败 Attempt 的未密封输出、
   Provider 隐藏状态、临时授权或未审核答案。
5. 新对话从空 Conversation Work State 开始，但仍可读取同一 exact World Model；跨对话偏好或长期 Memory 在独立合同接受前不启用。

## Primary engineering Agent loop

每个 Turn 使用一个逻辑主工程 Agent。模型调用可以因上下文窗口、恢复或 Provider attempt 分成多个 fresh invocation，但都必须消费并产生
Application-owned Agent Work State Revision，不得把 Provider session 当作连续性来源。工作状态至少表达：

- 当前用户目标、响应语言、受众与不可丢失约束；
- 已确认对象和指代解析；
- 可证伪假设、当前计划、子任务和优先级；
- 已观察的 World Model/Source 结果、冲突、未知和证据缺口；
- 下一动作理由、完成判断和仍未解决事项。

Agent 循环为 `understand → hypothesize/plan → request tool → observe → replan → answer or limitation`。这描述认知能力而不是固定调用顺序；
简单问题可以直接使用充分的 World Model cognition，复杂问题可以多步调查。Agent 必须根据新观察更新或放弃假设，不能在证据反驳后继续
执行冻结计划，也不能把达到调用上限当作完成证明。

Application 必须在调查前从 original Turn、受信 Conversation Context 和 material Need 形成 `Cognition Eligibility Assessment`：每个 Need
要么绑定 Manifest 中已资格化的认知维度和 query/view capability，要么形成具体 Cognition Gap。开放式工程 Chat 的“完整认知”只允许表示
对预提交问题集合具备资格的多域认知，至少包含结构与实现/行为维度；Maven 模块与依赖的窄结构 Profile 对流程、职责、配置、状态或故障
问题不得标为 eligible/full。认知不足时同一 Engineering Conversation 可以继续使用已授权 Source，但 Source 命中只支持当前 Turn，不得
回填为 World Model 覆盖或贡献。

Primary model 可以读取 previous committed Work State 中延续 Conversation 所需的 goal、constraint、referent、hypothesis、plan 与 open item，
但 previous Turn 的 Observation IDs 不是 current Turn Evidence copy domain，不得向模型披露或授权复用。可信 Application 必须单独投影
`work_state_reference_policy`：exact current-Turn Observation prefix、accepted-correction prefix、superseded-conclusion prefix、sealed current
User Message ID 与允许的 append rule。Provider 必须原序复制 exact prefix；只有 current User Message 明确纠正更早 Context 时才可追加该
sealed Message ID。Application 从原 Request、current observations、previous committed Work State 和 Context 重算并 fail closed。

允许的工具只有受信 Application 提供的 closed catalog：exact World Model query/view，以及由 Source Broker 编译的注册
`search/read/parse` 等 exact-revision 只读操作。Agent 提交的 path、query、class、locator、命令、URL 或完成声明均是不可信 Proposal；
Application/Broker 重新验证 authorization、Profile、allowlist、revision、modality、bytes、进度和剩余熔断。模型没有直接 Repository/
Source Tool/FS/shell/network/credential/write/Knowledge Update 权限。

current `conversational-engineering-agent@8` 对 `WORLD_MODEL_QUERY` 只允许无 argument action，并要求模型把具体事实、关系、状态转换、失败边界
或已知 repository-native symbol 写入 `evidence_need`。Application 必须把该 need 与 exact current User Turn 确定性编译为 bounded semantic
query；模型不能直接取得 query argument domain。相同 need 的 current-Turn 重复、显式 query 或 identity 漂移在 Cognition 执行前失败关闭。
受信旧调用方的 explicit-query 兼容路径不扩大 current 模型权限。每个非空 action 必须显式包含且只包含 `operation/arguments/evidence_need`；
即使 effective catalog 只有一个 operation，也不得省略 `operation` 或由 Application 猜测、补写该字段。

multi-Profile query projection 的 relevance 必须只使用 statement 的语义 value，不得让 JSON field name、schema/discriminator、entity/modality/
disposition/completeness/resolution/revision 等表示层 value 成为 query match。`source_path` 只以 basename 参与相关性，不能让 module/package
公共前缀为整个候选集合增权；这不改变正式 path、locator、Citation 或 Source target identity。英语 function token 与出现在超过候选 cohort
一半 item 中的 exact token 不作 discriminative anchor；若所有 token 都因此被排除，则确定性回退原 query token。exact/prefix 权重分别为
4/1；存在至少两个 exact anchor 时 prefix-only item 不进入结果，并只保留达到本次 strongest score 75% 的尾部，最后按 digest 稳定排序及
既有 item 上限截断。该规则不得按工程、问题、业务词、类、方法或 Provider 分支，也不得把 Profile incomplete 的实现细节伪装为 cognition。

当 immutable original User Message 精确点名 sealed Source allowlist 中一个或多个 top-level Source scope 时，Application 必须在
multi-Profile relevance ranking 前把该 scope 集与每个 Profile 的 formal Coverage root scope 比较。具有 non-repository-wide root 且与
显式 scope 完全不相交的 Profile 不得贡献 affirmative item 或 Profile gap；repository-wide root 仍可贡献相容的 partial cognition，并如实
披露缺失维度。scope selector 只允许对 original question 与 allowlist top-level segment 做 exact boundary match；Provider/model 生成的
relevance query 不能扩大、缩小或改写它。问题未明确点名已知 scope 时不得猜测；异域 Profile mismatch 是 Coverage Boundary，不是 Source
authorization denial。该门控不合并或改写 Snapshot/Read Set，不改变 Capability Manifest、Read Authority、Source Profile、Broker allowlist
或 Citation identity。

Primary input 还必须从 Application-owned loop limit 和 exact current action history 重算并密封
`tool_action_budget = {maximum, used, remaining}`；`remaining` 是最多仍可执行的 action 数，不是消费目标。current maximum 保持 8。
`remaining=0` 时 effective tool catalog 机械变空，普通 successor 的 completion policy 必须要求基于 current SUPPORT/BOUNDARY 的 Draft；
若 Review Finding 要求新 Evidence 而已经没有合法 action，则当前 Turn 失败关闭，不能恢复工具、扩大预算或以 Draft 绕过 Finding。

没有 current observation/action history 且没有 prior exact-source revalidation candidate 的 fresh investigation，只要 effective catalog 含
World Model，第一步必须为 `WORLD_MODEL_QUERY`；decoder 从原 invocation 重算并拒绝先行 Source proposal。这个稳定认知起点用于取得
repository-native target symbol，不要求把全部问题都交给世界模型，也不阻止 current-Turn 重签的 prior full-source candidate 直接重验。
同一 material semantic need 的换句式不是新 need；World Model 已明确给出同一 implementation gap 后，Primary 不得继续询问缺失实现，
必须转向一个命中该 gap 的 Source target 或保留诚实 Boundary。Application 的 exact duplicate/no-progress guard 仍机械执行，但不声称用
字符串规则完整判定语义等价。

Source search 必须优先使用 current cognition/observation 给出的 unread source-native type/member identifier，不得用只存在于已读 caller 的
expression 反复搜索同一调用点；Source read 必须直接对应 current unresolved material target，不能仅因 mapper、DTO、entity、test 或相邻
文件共享词汇就消费 bounded slot。Broker 继续独占 authorization、Profile、allowlist、revision 和 resource backstop；这些调查相关性义务
不让模型取得 path authority，也不让 Broker 从词汇自动推断业务相关性。达到 action/file fuse 仍只失败关闭或从现有证据诚实收敛，不能
通过提高上限冒充 progress。

`ENGINEERING_AGENT_WORLD_MODEL_SUPPORT@4` 还必须把 query-relevant、exact-revision Java entity cognition 中可机械验证的 declaring type
投影为 `ENGINEERING_AGENT_COGNITION_SOURCE_SEARCH_TARGETS@1`：只有 declaring type 末段、`.java` 文件 stem 和 exact `source_path`
一致时才形成候选；每项保留来源 cognition item/revision identity，并明确不授予 Source authority。若该 projection non-empty 且未截断，
并且 current Turn 尚未执行任何 Source action，`ENGINEERING_AGENT_PRIMARY_INPUT@8` 必须把这些 literal 投影为第一次
`SOURCE_SEARCH.query` 的 exhaustive `allowed_exact_values`；Provider 只能精确复制，decoder 从原 World Model SUPPORT Observation 重算并
拒绝宽泛 member word 或其他域外值。该闭域只负责第一次 cognition→Source 导航；执行一次 Source action 后，新 Observation 中出现的
source-native symbol 仍可按既有短字面量 contract 提议。projection 缺失或有界截断时不得伪称 exhaustive，仍由原 proposal/Broker 路径
失败关闭或受控执行；projection locator 不是 read capability，Broker 的 Profile、allowlist、revision 和 fuse 权限不变。

精确 literal 约束还必须保留同一 non-truncated projection 中已经机械校验的 canonical `source_path`，但它只能成为受信 Application 提供给
Broker 的 Search-only scope，不能成为模型 argument、direct READ locator 或 Source authority。当 `SOURCE` 类
`SOURCE_SEARCH.query` 精确等于该 projection 的 literal 时，Broker 可在 `COMPILED_SOURCE_OPERATION@2` 中密封对应
`search_path_scope`；它必须重新验证 path canonical/unique/bounded、`.java` stem 与 query 精确一致、Request allowlist、Source Profile 与
exact revision，并把 `maximum_files` 收紧到 scope 大小。Worker 仍执行 case-sensitive literal content Search，只为实际命中项签发 opaque
locator；Coverage 必须明确是 `TRUSTED_COGNITION_TARGET_PATHS` scope，不能把 scoped complete 冒充整个 Evidence Class complete。scope path
在 exact tree 缺失时必须以 `SOURCE_SEARCH_PATH_SCOPE_INCONSISTENT` 形成 Boundary，不得隐式退化为全类路径扫描。没有可信 scope 的普通
Search 保持原有授权路径和覆盖语义；该机制不提高 action/file/byte fuse，也不改变 Source Broker、Provider route 或 disclosure 权限。

每个 Proposal、Decision、Operation、Observation、Conflict、Unknown、Failure、Coverage 和资源收据按顺序追加到 Turn Evidence Ledger。
主 Agent 可以读取本 Attempt 获准的密封 Ledger prefix 与工具 Observation，但隐藏 rationale 和未密封输出不进入权威状态。

达到连续无进展熔断时，Application 必须终止进一步调查并撤销本 Attempt 的全部可提议工具；不得把同义 query、同资源其他 line locator 或
提高资源上限当作 progress。若 bounded Agent step 仍允许完成，Application 可以给同一主 Agent 一次
`EVIDENCE_ONLY_SYNTHESIS` completion opportunity：只可基于 current sealed SUPPORT/BOUNDARY 提交 Answer 或 Limitation，不能请求工具、
澄清或声称取得新 Evidence。该 Draft 仍须 fresh Review 与 Response Control；Reviewer 要求新 Evidence 时不恢复工具权限，当前 Turn 按
no-progress failure 关闭。

## Evidence, answer and review

1. 主 Agent 准备回答时，Application 从 current Turn、exact Cognition、Work State 和完整 Ledger 密封当前 Question Evidence Package。
   `support/citation` 只含经 modality/Context/Coverage/Support 验证的 admissible entries；`boundary/audit` 强制保留 Gap、Failure、Partial、
   Conflict、Unknown、拒绝和资源收据。seal 只证明身份、完整性、来源与版本，不赋予内容真值。
2. Draft 可以由同一主 Agent 综合多条证据自然回答，不要求把证据记录逐条变成答案句子。每个物质肯定结论必须绑定
   `support/citation`；未知或限制必须绑定相应 `boundary/audit`。答案应延续相关对话目标、响应用户最新纠正，并区分本 Turn 新结论、
   对先前答案的修订和仍未知范围。`draft.claims` 必须覆盖 `draft.content` 正文、summary、table、diagram 或 code comment 中每个 material
   affirmative conclusion；heading、table column、list lead-in、label 或 surrounding sentence 继承给所含 assertion 的 category、scope、
   condition、certainty 与 negation 同样属于结论，Claim statement 必须显式重述物质 qualifier，不能只枚举局部 action/outcome；同一 Draft
   在一处承认 Boundary，不能在另一处把该未知关系写成肯定步骤。Primary model input 必须由可信
   Application 从 exact current-Turn observations 投影两个 closed
   reference domain：affirmative Claim 只能复制 SUPPORT ID，Limitation 只能复制 BOUNDARY ID；cross-disposition 和 unknown ID 禁止。
   Decoder 必须从原 Observation 重算并 fail closed，不能删除错误 Claim、替换引用、提升 Boundary 或自动授权 Draft。current model
   input 还必须由可信 Application 从 current isolated attempt 的 typed action history 与 Source authority-receipt Citations 投影
   `tool_reference_policy`：列出已执行 exact action、已尝试 query/read 和未使用的 `source_read_options`；Provider 只能复制列出的 opaque
   locator，不能重复 exact action、伪造 locator 或把 display path 当 authority。read option 可以来自本 Turn Search receipt，也可以是前述
   current-Turn revalidation candidate；后者在执行 READ 前不是 Evidence，相关 follow-up 应优先用它重验已知 full resource，而不是先以内容
   SEARCH 消耗目录扫描熔断。每个 canonical Source resource 至多暴露一个 read option；
   任一 line reference 被读取后，同一 resource 的全部 reference 都离开 legal domain；没有未使用 option 时 `SOURCE_READ` 不得出现在
   effective tool catalog。Application 还必须从最新受信 Source `RESOURCE_RECEIPT` 投影 exact `used / maximum / remaining / exhausted`
   file budget；没有 receipt 时为 `null`，不得推测。`source_read_options` 只含当前预算与 catalog 下可执行的 opaque locator；
   `exhausted=true` 时 options 与 Source Search/Read catalog 一起关闭，但不能伪造 Broker terminal rejection。受信 Ledger 已出现
   operation/file/byte terminal fuse rejection 时，Source Search/Read 也必须离开 effective
   tool catalog；World Model operation 不被 Source terminal state 连带撤销。
   Decoder 从原 action/Observation/receipt 重算，fallback-route attempt 不继承 preferred-route attempt 的中间 action 或 resource catalog。tool catalog 的
   argument name 与 count 都是 exact closed domain；Provider 不得增加、遗漏或重复参数。Primary input 还必须把每个已用 World
   Model/Source query 就地投影为对应 tool argument 的 `forbidden_exact_values`，把未使用 Source locator 投影为 Source Read argument 的
   exhaustive `allowed_exact_values`；这些 model-facing 值不能取代 Application 从原 action history 与 authority receipt 的重算。
   `completion_policy.allowed_response_kinds` 也是 exhaustive current-Turn domain：没有 SUPPORT 不得列 `ANSWER`，没有 BOUNDARY 不得列
   `LIMITATION`；当前 World Model 已形成 BOUNDARY、但第一次受权 Source follow-up 仍可执行且尚未尝试时，也不得列 `LIMITATION`。若
   Source Search 已返回未读取的 opaque locator，则在第一次 Source Read 前继续禁止该 Limitation；一次实际 Read、一次没有可读 option 的
   Search、terminal Source denial 或 effective Source operation 不存在后，才可按 current BOUNDARY 重新开放。该规则不强制读取全部文件，
   不把 Source availability 提升为证据，也不阻止 current SUPPORT 已完整解决目标时直接提交 Answer。旧 Answer 的总结、改写或收窄仍须
   current-Turn Evidence。Decoder 必须从原 action history、Observation、authority receipt 和 effective catalog 独立重算 response kind 与
   Claim/Boundary copy domain。

   同一 current Turn 内多次 `WORLD_MODEL_QUERY` 的 SUPPORT Observation 是 append-only cognition delta，不是完整快照的重复副本。可信
   evidence-tool adapter 按 exact Cognition item digest 保留首次出现顺序：每次 query 的正式 Context、Ledger 和 authority receipt 仍绑定完整
   current Cognition Context digest、exact revision 与 global coverage，但 model-facing SUPPORT 顶层不得复制 global
   `cognition.coverage/conflicts/unknowns`；这些全局 Gap/Conflict/Unknown 只进入 BOUNDARY。SUPPORT item domain 还必须按 typed
   `CognitionDimension` 机械限制为 `ENTITY/RELATION/BEHAVIOR/CONSTRAINT/STATE`；`COVERAGE/EVIDENCE/UNKNOWN` metadata item 永不取得
   affirmative Claim 资格。SUPPORT 只追加该 Turn 先前尚未投影的 affirmative item 及其自身的 per-item coverage，Citation refs、
   current/novel/already-observed counts 和 cognition-derived Source target 也只按该 domain 计算。重复 item 的首次
   Observation 不得删除、重排或改写；后续 Claim 需要该事实时引用
   首次携带它的 SUPPORT ID。一个 query 没有 novel supported item 时不得制造重复 SUPPORT，而须形成明确 no-new boundary/no-progress；含新
   boundary、conflict 或 unknown 的 Context 仍按其自身 disposition 保留。该压缩不改变正式 Cognition Context、Evidence Ledger、receipt 或
   Citation identity，也不能把未见 item、metadata item、Boundary 或旧 Turn Evidence 提升为支持。metadata-only Context 必须形成明确
   `WORLD_MODEL_HAS_NO_SUPPORTED_ITEMS` BOUNDARY，不能制造空或 metadata-only SUPPORT。

   Ledger/Package 的 audit retention 与 user-visible answer disclosure 必须分离。Boundary 只有在它仍使 current User Message 的 material
   requirement 未解决，或用户明确询问该诊断本身时才进入 Draft；它出现在 `boundary/audit` 不等于必须向用户披露。早期 partial/truncated
   Search、budget、Provider 或其他 acquisition diagnostic 若已由后续 current SUPPORT 闭合同一 material need，只保留在 audit，Primary 还须
   删除或纠正 Work State 中对应的已解决 Hypothesis/Open Item。global inventory count 或 Profile-wide coverage metric 只有在实际限制用户
   要求的具体 conclusion 时才可进入答案，不能代替具体 Evidence boundary。

   成功 Turn 的不可变 Result 还必须只投影 Draft 实际引用的 Observation 所签发的 ordered unique Citation；每项保留 evidence class、exact
   source revision、locator、modality、content digest、Citation ref 与 authority digest。未被 Claim/boundary 引用的 Package Citation 不得顺带
   暴露，identity 不一致必须在浏览器投影前失败关闭。Browser 必须在对应助手消息下提供可展开 Citation，并同时显示本 Turn 的 Evidence
   Package、Answer、fresh Review 与 Delivery Authorization reference；展开只读取已密封 Turn projection，不发起新的 Source operation。
   已执行 live 基线的 model strategy/prompt/Primary input identity 为 `conversational-engineering-agent@6`、
   `conversational-engineering-agent-no-tools-prompt@6` 和 `ENGINEERING_AGENT_PRIMARY_INPUT@6`；产品 Conversation protocol 仍为
   `CONVERSATIONAL_ENGINEERING_AGENT@1`。
3. 每个可交付工程 Draft 至少经过一个 fresh、与主 Agent 隔离的独立 Reviewer。前述 deterministic empty-context input clarification 不是
   工程 Draft，因其不提交事实、Evidence 或 Delivery 而不调用 Reviewer。Reviewer 只读 current User Message、受信相关 Conversation
   Context、当前 Package 与 Draft；无 Repository、World Model/Source Tool、Broker dispatch、shell、网络、credential 或写权限。
4. Reviewer 从用户当前目标独立检查正确性、完整性、相关性、Citation 支持、条件/顺序/副作用、对话一致性、用户纠正和 Unknown 边界。
   `ENGINEERING_AGENT_REVIEW_INPUT@2` 必须投影 exact ordered Claim indices；Reviewer output 必须为每个 Claim 返回一个
   `SUPPORTED/DEFECT` assessment。Application 重算完整 index set，禁止 SUPPORTED Claim 携带 Finding，并要求每个 DEFECT 至少绑定一个
   Finding；`APPROVED` 只允许全 SUPPORTED + empty Findings。global completeness/relevance Finding 可用 `claim_index=null`，但不能把
   “证据已支持/没有 defect”编码为 claim Finding。它只能返回 `APPROVED` 或带具体 Claim/证据缺口的 Finding；流畅、沿用上一轮或其他检查
   通过不能抵消重大错误。Reviewer 必须先比较完整 `draft.content` 与枚举 Claim；未进入 Claim inventory 的 material affirmative
   conclusion 形成 `claim_index=null` 的 global completeness Finding，不能因所有枚举 Claim 都 SUPPORTED 而批准。比较时必须以 heading、
   table column、list lead-in、label 与 surrounding sentence 重建完整 assertion；Claim 漏掉物质继承 qualifier 属 global completeness
   Finding，qualifier 错误、无据或误分类属 concrete defect，窄 Claim 获支持不能批准其容器扩张。路径、package、import、
   symbol name、directory convention 或 caller syntax 不能单独证明类型继承/catch coverage、数据库约束、运行时配置值、
   code-generation/tool provenance 或外部副作用；Primary 必须取得直接声明/执行该关系的 current Evidence，或把结论收窄为不依赖未知关系的结果，Reviewer 对违反
   该规则的 material Claim 必须返回 Finding。current Source 行直接包含 call expression 时，它只直接证明 caller 调用该表达式及源码可见
   的局部顺序，不证明 callee 实现、动态目标、返回语义、类型继承或外部副作用；Draft 只陈述该 invocation/order 并明确把 callee semantics
   留在 evidence boundary 时，Reviewer 不得因后者未知而拒绝前者。Authorization、Evidence Coverage、Tool availability 与 runtime
   outcome 也是彼此独立的状态：只有 current BOUNDARY 明确记录 exact authority/Source Profile denial 时，Draft 才能把事实或来源称为
   未授权或超出授权；Cognition Gap、未读实现、无 locator、预算耗尽或 Provider failure 必须按其真实边界表述。producer-side
   invalidation/publish/refresh/update/commit/remote-write 调用只支持 invocation 与源码局部顺序；若 Draft 声称 invoked implementation、
   成功效果或另一个 request/session/cache consumer/security context/transaction observer/remote system 的可见时点，必须分别取得该
   implementation 和 consumer path 的 current SUPPORT，否则选择仍合法的 targeted action 或报告 exact Evidence boundary。Primary 与
   Reviewer input 必须对称投影这些规则；Reviewer 还必须把无关或已由后续 SUPPORT 闭合的 acquisition diagnostic 判为 relevance Finding，
   并令 `requires_evidence=false`，因为删除它不损失已支持的 requested conclusion。Primary 和 Reviewer 对每个普通 affirmative detail 与
   Boundary 也必须执行 counterfactual relevance test：若删除该细节后 current User Message 的每个 requested conclusion 仍完整回答并诚实
   定界，则必须省略；只有用户明确要求，或该细节改变 requested condition、result、comparison 或 guarantee 时才保留。neighbor declaration、
   alternate helper/overload、package neighbor 或 implementation provenance 不因共享 artifact/vocabulary 自动 material；不能为 Draft 自己引入的
   邻接细节扩大调查。Reviewer 对这种自扩张返回 `requires_evidence=false` 的 relevance Finding。Application 不以题目、技术名词、failure code
   或语言关键词改写 Draft。每个 Finding 的 remediation 还必须互斥：只有 current Package 缺少
   current User Message 真正要求的 material fact，且删除/收窄会让该要求仍未回答时，才可 `requires_evidence=true`；若 current Package 已能
   通过删除、收窄、限定或重组 offending statement 保留全部已支持的 requested conclusions，则必须为 false，不能一边给出这种同包修复一边
   要求新 Evidence。所有 role output 必须是唯一 closed JSON object；JSON 外叙述继续失败关闭，不能抽取
   substring 追认。
5. 现有 Package 足够时，Response Control 把 Finding 绑定到同一主 Agent的新 Work State Revision，形成同包针对性重写。Package 的
   `origin_work_state_digest` 永久表示首次密封该 exact Observation 集合的 Work State；它不是 successor Draft 的 Delivery Work State，
   因而同包重写不得改写 Package origin，也不得要求 current Work State 等于 origin。Response Control 必须重验 immutable Package
   identity/partition，并把当前 successor Work State、Draft、fresh Review、同一 Package 和 Turn 绑定为 exact approved chain；任何新
   Observation 仍形成新 Package。任一 Finding 标记
   `requires_evidence=true` 时，standard successor Primary input 必须把 `tool_action_required` 设为 true，并把 Draft response kind domain 置空；
   主 Agent 只能从 effective tool catalog 提交一个 exact action，不能只重写被拒 Draft。任何新 Observation 都形成新 Ledger/Package
   Revision，旧 Review 不得放行新 Draft。evidence-only completion 不恢复工具；此时 Reviewer 要求新 Evidence 仍按 no-progress failure
   关闭。生成者不能自审，Reviewer 不能自行执行工具或放行。同包重写、补证后重答与每次 fresh Review 都是当前 execution profile 内的新 authorized
   model call，必须有新 call identity、Manifest 和 one-use receipts；它们不是重发同一 Provider request。closed JSON 输出无效时，若已资格化的通用格式修复步骤、
   权威和预算都存在，也只能用同一 execution profile 创建新 authorized call；否则当前 Turn 失败关闭。格式修复输入必须把 trusted local
   validator error code 与 Application-owned bounded diagnostic（以 deterministic trusted-schema traversal 一次收集 parent 与 nested
   object 中最多 32 处可机械定位的 mismatch；每处保留失败路径，并把该路径上 trusted schema 的完整 exact field allowlist、缺失 field
   names、unexpected count 和 additional-fields-forbidden 状态投影给 repair；untrusted unexpected key name 不回显）同原始失败
   call receipt 和 untrusted prior output 一并绑定。repair 必须按 `allowed_exact` 重建该 object；sealed input 的 identity/metadata 字段只有
   同名进入 output allowlist 才能出现在输出。对 parseable `CLOSED_SCHEMA_SHAPE` failure，Application 必须从 untrusted prior output 与
   trusted schema 递归形成 `ENGINEERING_AGENT_OUTPUT_PREFLIGHT@5 / existing_allowed_field_copy_projection`：只保留已存在且当前子树 shape
   可对齐的 allowlisted field/value，排除 unexpected field 并保持 missing field 缺席。若一个 schema-invalid array 的所有 item 都没有任何
   已存在 allowlisted value，则整个 array 子树不形成 copy obligation；repair 只能从 current sealed schema/domain/template 重建它。只要该
   array 仍有一个既存 allowlisted item value，原长度/顺序与所有可对齐值就必须保持，不能用重建吞掉合法 sibling。
   Primary/Reviewer 仍须精确复制 projection；在 Proposal decode 前，Application 还必须以
   `RESTORE_SCHEMA_MATCHING_ALLOWLISTED_VALUES_BEFORE_DECODE@1` 把 repair 对这些既存值的任何原始漂移机械恢复为 prior exact value，再递归重验
   最终值与顺序守恒。该 restoration 不能生成 missing field、保留 unexpected field、重建无 copy obligation 的 invalid 子树、改变 array
   对齐或授予 Tool/事实/Review 权限；不能恢复到完全相等时仍以 structured-output-invalid 失败关闭。raw Provider output、prior output、schema
   与最终 sealed Work State identity 必须保留可重算关系，raw 漂移本身从不获得授权。nullable union、本地 schema reference 或嵌套 object
   不得隐藏可机械定位的字段缺失；parent mismatch 不得提前结束对仍存在的 allowlisted child value 的遍历。该 projection/restoration 只把
   既有守恒义务做成可信机械边界，不赋予事实、语义、Tool、Review 或 Delivery authority，也不得被扩张成任意输出正规化。
   `CLOSED_OUTPUT_CONTRACT` repair 若发现真实缺口只是绑定到错误 Claim，不得为满足一致性
   而删除缺口；针对未枚举正文结论的 Finding 应保留并使用 `claim_index=null`。diagnostic 只定位 shape，不授予
   事实、工具或审核权；除上述显式、版本化、可重算的 existing-value restoration 外，Application 不得据此静默规范化模型输出或改变 Provider adapter
   identity/qualification。两种情况都不允许改换 route role。该诊断性修复沿用 current
   `conversational-engineering-agent-no-tools-prompt@8 / ENGINEERING_AGENT_PRIMARY_INPUT@8 / ENGINEERING_AGENT_REVIEW_INPUT@2` 协议族；每次
   Session authority、role request 和 Provider request 仍必须绑定修复后的 exact prompt/input digest，旧字节不能冒充 current 输入。若
   first non-whitespace character 不是 `{`，bounded diagnostic 必须以 `NON_JSON_OBJECT_PREFIX` 定位 envelope failure 而不回显前缀；final
   preflight 必须明确禁止 JSON object 前后的 analysis/narration。该分类不允许 Application 抽取后部 JSON、增加第二次 repair 或把格式失败
   改判为 Provider unavailable。
6. Reviewer Strategy 可以在资格中采用多个隔离视角或 challenge，但固定角色数量、固定 focus 顺序、固定检查清单 JSON 和一次单独
   Verification Investigation Agent 不是长期架构不变量。任何 Strategy 都不得少于一次 fresh 独立审核，或取消逐结论 evidence closure。

## Generality, evaluation and failure

核心 Agent、Prompt、工具选择、Conversation reducer、Review 和 UI 不得按工程、问题、关键词、语言、框架、符号、类、方法、约定文件名、
fixture 或 Oracle 注入专用答案逻辑。语言和来源差异只能由显式版本化 capability 注册；Conversation input policy 必须进入 Binding identity，
只能决定是否要求澄清，不能生成工程结论或切换 Agent/Provider/Source 路径。

产品资格必须同时验证：多轮指代、追问、用户纠正、目标延续、观察驱动重规划、World Model 与 Source 工具组合、证据引用、Reviewer 缺口
反馈和 Turn 故障隔离。在任何新产品/Web 变更前，同一个四路 Gate 使用直接相关证据到相同 generator、同一主 Agent 仅源码、同一主
Agent question-eligible multi-domain Cognition+源码和 current Codex，同时证明产品替代价值与世界模型认知的独立贡献。第 2/3 路除
认知开关外保持相同；事实来自独立 exact-source ledger，任何一臂都不是 Oracle 或 Reviewer。

授权/identity/revision 漂移、上下文错绑、工具越权、Ledger/Package 缺口、无依据结论、结构化输出无效、Reviewer 未通过、资源耗尽或 raw Provider outcome
unknown 都使当前 provider attempt 或 Turn 失败关闭，除非同一 profile 内存在前述已授权新调用。Provider fallback 只能按 ADR-017 在同一 logical Turn 下从受信 original Turn input、
exact Conversation Context 与 exact Cognition 重启完整 Agent attempt；不得复用失败 Provider 的隐藏状态或未密封中间产物。

Fallback eligibility 不得从 raw error string、owner code、HTTP status 或 outcome 直接推断。model boundary receipt 必须保存原始 owner code 和 trusted failure kind，但它们只是证据。
只有 preferred execution profile 登记的受信 availability owner 能对 exact profile/ref、当前时间与 receipts 密封
`PREFERRED_EXECUTION_PROFILE_UNAVAILABLE` route verdict。`PROVIDER_OUTPUT_INVALID`、`MODEL_REVIEW_REJECTED`、pre-dispatch、Capability/qualification、
Gateway/repository/result identity、Application、Source、authorization/admission 或 Security failure 均保持 non-eligible。每个 attempt authority/receipt 绑定 logical Turn parent、route role、execution profile、
availability owner/verdict、admission plugin/session、execution-profile/disclosure/dispatch-admission/transport/model/terminal receipts 和 same-request retry 0；logical Turn Result 只取最后一个完整 attempt 的 Outcome，
但汇总全部 attempt dispatch。availability owner 若基于 preferred outcome unknown 形成 unavailable verdict，后续 fallback 必须标记 duplicate-cost risk；late preferred-route result 固定
`QUARANTINE_AUDIT_ONLY`，没有覆盖、拼接或追认最终结果的接口。

Browser 的失败视图必须把 logical Turn/Agent/Application 的 execution-stage failure 与已密封 raw Provider evidence 分层显示；存在
`provider_failure_classification/provider_failure_code` 时不能只显示上层 stage code，不存在时也不能推测 Provider 原因。这个显示不取得
availability 或 fallback 权威，不得暴露 Provider 错误正文、credential、secret reference 或未密封模型输出。

## 当前配置实例与历史实现证据

当前 ITER-010 配置把 Ark 映射到 `preferred` execution profile，把 DeepSeek 映射到 `fallback` execution profile；以下具体名称、状态和运行
记录只描述当前配置实例与历史实现证据，不定义本契约的 route 分支、质量、授权或 Agent 语义。

当前独立 Chat Access 已提供 Application-owned Conversation/Turn/Message、不可变 Revision、完整页面消息历史、“新对话”隔离与失败
Turn 后 Conversation 继续，并已通过真实 browser Access Case。Application-owned bounded executor 也已在确定性 fake ports 上密封跨 Turn
Work State revision、工具 Observation、support/boundary Package、Answer、fresh Review 与 Delivery Authorization；协议错绑、缺证后无新
Observation 重写、无进展和资源熔断只关闭当前 Turn。trusted evidence-tool adapter 已复用现有 World Model projector、Source Broker 与
Retrieval Worker；同一动作可分别密封 support/boundary，每条 Observation 携带 exact Turn/Tool/revision、Application 可重算的完整
append-only Ledger entry chain/prefix 与 Citation content digest，Source READ 只接受本 Turn 先前签发的 opaque locator。状态为
`ACCESS_BROWSER_PASS / AGENT_EXECUTOR_LOCAL_CANDIDATE / EVIDENCE_TOOLS_LOCAL_CANDIDATE / MODEL_BOUNDARY_LOCAL_CANDIDATE /
PROVIDER_ROUTE_COMPOSITION_LOCAL_CANDIDATE / PROVIDER_RUNTIME_COMPOSITION_LOCAL_CANDIDATE /
SESSION_RUNTIME_COMPOSITION_LOCAL_CANDIDATE / ARTIFACT_SESSION_V3_ADMISSION_LOCAL_PASS /
ARK_TRANSPORT_SESSION_AUDIT_LOCAL_CANDIDATE / PUBLIC_SOURCE_STANDING_AUTHORITY_DERIVATION_LOCAL_CANDIDATE /
SEVENTH_LIVE_CHAT_THREE_OF_FIVE_LIMITATIONS_OVERALL_FAIL / NEW_CONVERSATION_LEAKAGE_PASS /
V7_UNACCEPTED_SYMPTOM_EXPERIMENT / V8_SEMANTIC_NEED_QUERY_LOCAL_CANDIDATE / RUN043_QUALITY_REWORK /
SESSION_AUTHORITY_REQUIRED / NOT_PRODUCTION`。单 Provider Agent/Reviewer 已使用 separate closed no-tools contracts、逐调用 one-use
Disclosure 和 typed Gateway receipt；pre-dispatch、fresh dispatch、outcome unknown 与 replay 的计数由 Application 重验，Turn/Browser 只保存
receipt digest reference。Application-owned generic preferred→fallback router（当前配置实例映射 Ark→DeepSeek）、committed Work State repository、两 attempt receipt、logical Turn 汇总与
non-starting fixed Browser composition 已通过本地确定性 Gate；预检没有创建 attempt、启动 listener、解析 credential、读取 Source 或 dispatch。
Provider runtime composition 已使用生产 Ark/DeepSeek Adapter 与 credential-lazy transport，但只消费本地构造的 typed qualification identity。
non-starting Session runtime 又把两条 Provider runtime、exact evidence authority、per-attempt fresh Tool/Response Control、共享 committed
   Work State、Conversation 与 Browser 组合成一个对象图；preparation 没有创建 attempt、读取 Source、解析 credential、dispatch 或启动 listener。
artifact Session loader 现可从一个 owner-private closed document 绑定 product/source Git identity、ordered profile-specific published
World Model authorities、Source Profile、Ark→DeepSeek qualification identity、两个 private Gateway repositories 与 Session authority；
current `@4` 在逐 Profile 重验 expected file/Bundle digest、Profile/Schema/Source Binding/selected Snapshot 并形成 Capability Manifest 后，
还要求在 Provider network/credential 前重验公开 upstream、clean HEAD、exact commit/tree、license object、standing scope 和 DeepSeek
admission，再派生 exact Session/Turn/call 摘要链且记录人工重复审批数 0；`@3` admission、`@2` 多 Profile 与 `@1` 单 Profile 配置继续
只读兼容，但不能取得 current standing-authority preparation 状态。唯一 `--session-config` selector 让固定
`127.0.0.1:8765` 命令消费该组合，并在 listener 前/停止后分别密封 launch/terminal receipt；terminal 已验证 Ark/DeepSeek transport audit。
Ark HTTP 前 transport unavailable 也已通过 Gateway owner-typed 为 availability raw evidence，但受信 availability-owner verdict 尚未闭合，不得追认为 fallback eligibility。历史 fresh Ark 与 DeepSeek Conformance 已分别以
exact clean identity、2/2 request 和 strict Session audit PASS，并按各自 exact identity 用于多个 owner-private mall artifact Session。`run-035-chat-alpha` 与
`run-036-chat-alpha` 均真实启动 listener、执行 Browser 五轮 Chat、消费受限 Source/Provider 并优雅停止，但五轮各自 5/5 失败；run-036 的
新 Conversation probe 已以 Application clarification、零 dispatch 和空 Context 通过泄漏负测。run-037 在 fresh 双资格后仍为 0/5；v3
tool copy domain 与 Reviewer assessment 随后形成。`run-038-chat-alpha` 再次取得 fresh 双资格并执行五轮，其中仅 Turn 5 以 reviewed
Limitation 技术成功，整体仍为 1/5 / Quality FAIL；v4 随后关闭 Source resource domain 与 no-progress completion。`run-040-chat-alpha`
在 v4 fresh 双资格后仍只有 Turn 2 的 reviewed Limitation，整体 1/5 / Quality FAIL；v5 随后把 previous Work State Observation IDs 移出
current Turn copy domain，并要求 `requires_evidence` Review successor 只能提交 exact tool action。`run-041-chat-alpha` 已让 Turn 1
Answer 与 Turn 3/4 reviewed Limitation 技术成功，但 Turn 2 重复 exact Source action、Turn 5 在 empty SUPPORT domain 复述 prior
Answer，故整体仍为 3/5 / Quality FAIL。v6 successor 把 response kind 与 tool argument 的 current feasible domain 就地密封；
strategy/prompt/Primary input identity 再次改变，所以 run-041 只保留为执行证据。`run-042-chat-alpha` 已在 v6 对应 route 资格后执行：
Turn 2/3/4 为 reviewed Limitation，Turn 1 review limit、Turn 5 model-call rejection，仍为 3/5 / Quality FAIL；新 Conversation
clarification/隔离/零 dispatch 继续 PASS。后续 v7 的 path-relevance prompt guidance 与 review-scope policy 没有经过逐层因果归因或跨题
验证，只是已停止的本地症状实验，不能成为 current Contract、Conformance 失效原因或下一次 live 重跑入口。run-043 随后把 first
divergence 定位到 semantic `evidence_need` 未进入 Cognition query；current v8 已在 Application 边界本地闭合该绑定，并以两个未参与修复
的异质问题做真实 bundle 诊断。run-043 的答案质量和 DeepSeek 峰时调度 FAIL 均保持；领域 Prompt 变化本身不触发 ADR-017 Provider
Conformance。`run-060/061/062` 又依次暴露同 Turn 重复 Cognition、closed operation repair 诊断和跨 Turn full-source 重验缺口；
`FINDING-010-170/171/172` 已分别形成 `BOUNDED_CONTEXT_REPAIR_LOCAL_CANDIDATE / CLOSED_TOOL_DIAGNOSTIC_LOCAL_CANDIDATE /
CROSS_TURN_SOURCE_REVALIDATION_LOCAL_CANDIDATE`。run-063 已真实证明 revalidation locator 在 Turn 2 生成相同 content digest 的新
current-Turn Citation，但同一答案又包含 indirect type-relation overclaim 且 Reviewer 漏判，Turn 3 的 initial/repair output 连续把
input-only `work_state_ref` 加入 closed output。`FINDING-010-173` 已形成 `EXACT_OUTPUT_ALLOWLIST_REPAIR_LOCAL_CANDIDATE`。run-064 随后
证明 parent mismatch 的 early return 会隐藏同份 output 的 nested missing field；`FINDING-010-174` 已形成
`BOUNDED_COMPLETE_SHAPE_DIAGNOSTIC_LOCAL_CANDIDATE`。run-065 Turn 1 真实成功但 material narrative conclusion 未进入 claims 且 Reviewer
漏判，Turn 2 的 nested diagnostic 正确、shape repair 却改写既有合法值而被机械守恒拒绝；`FINDING-010-175` 已形成
`EXACT_REPAIR_COPY_AND_DRAFT_CLAIM_CLOSURE_LOCAL_CANDIDATE`。run-066 又在 current Controller/Service Source 已足够证明 caller
invocation/order、Draft 已声明 callee semantics 未知时，被 Reviewer 错标为强制补证；Application 正确执行 tool-action-only successor 并
在 Primary 未服从时失败关闭。`FINDING-010-176` 已形成
`CALL_EXPRESSION_EVIDENCE_AND_REVIEW_REMEDIATION_LOCAL_CANDIDATE`。完整三轮仍须新 exact product identity 的 fresh Browser successor 验证，
不能追认这些失败 run 或把局部技术成功称为 MVP。
run-067 随后在 fresh Turn 跳过 World Model，以 broad Source search、已读 caller expression search 和辅助 Mapper read 消耗 Source slots，
再对同一 service implementation gap 连续换句式查询 World Model；第九个 Primary call 提出第九项 Tool action，Application 在执行前以
8-action 上限失败关闭，仍无 Draft/Review/Delivery。`FINDING-010-177` 已形成
`BOUNDED_INVESTIGATION_BUDGET_AND_TARGET_RELEVANCE_LOCAL_CANDIDATE`：Primary input 精确投影 remaining budget，零预算撤销 catalog 并要求
收敛；fresh 无 revalidation 调查机械要求 World Model-first；同义 gap requery 与不命中 unresolved target 的 Source 选择被明确禁止。上限
保持 8，不以扩容掩盖路径漂移；fresh exact Browser successor 仍是唯一产品验证。
旧
`ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3` 继续是兼容协议，不能作为本契约主 Agent 或 Chat 资格证据。
