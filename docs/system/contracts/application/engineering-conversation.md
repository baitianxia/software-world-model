---
id: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
kind: system-contract
status: current
authority: normative
owners: [application, source, quality, security]
depends_on: [SYS-ADR-017, SYS-ADR-018, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-CONTRACT-AI-MODEL-GATEWAY]
derived_from: [FINDING-010-097, FINDING-010-098, FINDING-010-099, FINDING-010-100, FINDING-010-101, FINDING-010-102, FINDING-010-103, FINDING-010-104, FINDING-010-105, FINDING-010-106, FINDING-010-109, FINDING-010-113, FINDING-010-116, FINDING-010-117, FINDING-010-120, FINDING-010-121, FINDING-010-125, FINDING-010-128, FINDING-010-132, FINDING-010-133, FINDING-010-136, FINDING-010-138, FINDING-010-139, FINDING-010-154, FINDING-010-156, FINDING-010-159, FINDING-010-160, FINDING-010-169, FINDING-010-170, FINDING-010-172, FINDING-010-176, FINDING-010-177, FINDING-010-183, FINDING-010-191, FINDING-010-192, FINDING-010-193, FINDING-010-194, FINDING-010-195, FINDING-010-196, FINDING-010-197, FINDING-010-198, FINDING-010-199, FINDING-010-200, FINDING-010-201, FINDING-010-203, FINDING-010-204, FINDING-010-208, FINDING-010-209, FINDING-010-210, FINDING-010-211, FINDING-010-212, FINDING-010-213, FINDING-010-214, FINDING-010-215, FINDING-010-216, FINDING-010-217, FINDING-010-218, FINDING-010-220]
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
User Message ID 与允许的 append rule。Observation prefix 完全由 Application 持有，`engineering-agent-work-state-proposal@2` 不再把
`observation_ids` 作为 Provider output field；Application 必须从 current invocation 直接绑定完整有序 prefix，Provider 若输出、遗漏或尝试改写该
field 均不能改变 Work State identity。accepted-correction 与 superseded-conclusion 仍由 Provider 原序复制；只有 current User Message 明确纠正
更早 Context 时才可追加 sealed Message ID。Application 从原 Request、current observations、previous committed Work State 和 Context 重算并
fail closed；这种 Application-owned identity binding 不授予事实、Tool、Review 或 Delivery authority。

允许的工具只有受信 Application 提供的 closed catalog：exact World Model query/view，以及由 Source Broker 编译的注册
`search/read/parse` 等 exact-revision 只读操作。Agent 提交的 path、query、class、locator、命令、URL 或完成声明均是不可信 Proposal；
Application/Broker 重新验证 authorization、Profile、allowlist、revision、modality、bytes、进度和剩余熔断。模型没有直接 Repository/
Source Tool/FS/shell/network/credential/write/Knowledge Update 权限。

current `conversational-engineering-agent@13` 对 `WORLD_MODEL_QUERY` 只允许无 argument action，并要求模型把具体事实、关系、状态转换、失败边界
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

relevance 已选中的 typed relation 必须在同一 Snapshot、same revision 和既有 item/byte bound 内保留可由 relation exact
`subject_entity_root_id / object_entity_root_id` 解析的直接 Entity endpoint state，并按 subject→object 顺序、item digest 去重后紧邻
relation 投影。该 direct graph closure 只使用 Snapshot 已有 evidence；缺失或超出 bound 时保持 Unknown/截断，不递归邻居、不以名称或弱
词法尾部猜 Entity。endpoint 的 verified declaring type/source path 可以进入既有 cognition→Source navigation projection，但不改变
Snapshot、Read Authority、Coverage、Citation、Broker 重验或 Source authority。

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

module、directory 或 file-name path segment 只承担 Source scope/navigation 语义，不能仅因出现在 authorized allowlist 中就作为 content
`SOURCE_SEARCH.query`。Broker 对 `SOURCE_SEARCH_QUERY_EQUALS_PATH_SEGMENT` 的 sealed rejection 必须发生在 Worker 前，因而该 action
没有取得 Evidence、locator 或 file/byte usage，也不满足 completion policy 要求的 Source follow-up。Primary input 必须投影 latest sealed
Broker decision；只要 Source action 仍合法且 material requirement 未解决，模型必须选择不同的、可能在目标正文逐字出现的 source-native
literal。被拒 query 继续进入 exact action repetition denylist；Application 不把该拒绝改写成 authorization denial、whole-Turn fuse、
Provider unavailable 或允许过早 Limitation 的依据。

`ENGINEERING_AGENT_WORLD_MODEL_SUPPORT@4` 还必须把 query-relevant、exact-revision Java entity cognition 中可机械验证的 declaring type
投影为 `ENGINEERING_AGENT_COGNITION_SOURCE_SEARCH_TARGETS@1`：只有 declaring type 末段、`.java` 文件 stem 和 exact `source_path`
一致时才形成候选；每项保留来源 cognition item/revision identity，并明确不授予 Source authority。若该 projection non-empty 且未截断，
并且 current Turn 尚未执行任何 Source action，`ENGINEERING_AGENT_PRIMARY_INPUT@24` 必须把这些 literal 投影为第一次
`SOURCE_SEARCH.query` 的 exhaustive `allowed_exact_values`；Provider 只能精确复制，decoder 从原 World Model SUPPORT Observation 重算并
拒绝宽泛 member word 或其他域外值。该闭域只负责第一次 cognition→Source 导航；执行一次 Source action 后，新 Observation 中出现的
source-native symbol 仍可按既有短字面量 contract 提议。projection 缺失或有界截断时不得伪称 exhaustive，仍由原 proposal/Broker 路径
失败关闭或受控执行；projection locator 不是 read capability，Broker 的 Profile、allowlist、revision 和 fuse 权限不变。

精确 literal 约束还必须保留同一 non-truncated projection 中已经机械校验的 canonical `source_path`，但它只能成为受信 Application 提供给
Broker 的 Search-only scope，不能成为模型 argument、direct READ locator 或 Source authority。当 `SOURCE` 类
`SOURCE_SEARCH.query` 精确等于该 projection 的 literal 时，Broker 可在 `COMPILED_SOURCE_OPERATION@3` 中密封对应
`search_path_scope`；它必须重新验证 path canonical/unique/bounded、`.java` stem 与 query 精确一致、Request allowlist、Source Profile 与
exact revision，并把 `maximum_files` 收紧到 scope 大小。Worker 仍执行 case-sensitive literal content Search，只为实际命中项签发 opaque
locator；Coverage 必须明确是 `TRUSTED_COGNITION_TARGET_PATHS` scope，不能把 scoped complete 冒充整个 Evidence Class complete。scope path
在 exact tree 缺失时必须以 `SOURCE_SEARCH_PATH_SCOPE_INCONSISTENT` 形成 Boundary，不得隐式退化为全类路径扫描。没有可信 scope 的普通
Search 保持原有授权路径和覆盖语义；该机制不提高 action/file/byte fuse，也不改变 Source Broker、Provider route 或 disclosure 权限。

当不存在上述更强 exact-path scope、original User Message 又逐字命中 sealed Source allowlist 的 top-level scope 时，Application 必须把该
scope 对应、且属于 current operation evidence-class allowlist 的完整 prefixes 作为 Search-only restriction 交给 Broker。Broker 必须从
immutable original question 与完整 Request allowlist 重新识别 scope，再只从 current Source Profile evidence class 独立重算 prefixes 并
exact match；同 module 的 POM、TEST 或其他 class path 不得混入 SOURCE operation。模型不能提交或扩展 prefix，prefix 也不签发 READ locator。Worker 先检查每个
query 的 stem/name/path candidate cohort，再只对其 rank-3 canonical fallback cohort 使用 current-Turn trusted offset 做确定性环形轮转。
offset 只能由前一 validated SOURCE Search Result 的 actual `fallback_examined_file_count` 推进；Result 必须记录 requested/applied offset、
scoped entry count 与 actual fallback count。query 改变导致 candidate cohort 改变时仍先执行新 candidate，不把 offset解释为全局完整游标。
该机制不得缓存或复用旧 source bytes，不得跳过 exact revision/allowlist/content match，也不得提高 per-search 56、whole-Turn 64 或最后一个
exact READ 槽位；未检查部分仍形成明确 Partial/Coverage，而不是“未找到”或 complete。

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
   `completion_policy.allowed_response_kinds` 也是 exhaustive current-Turn domain：没有 SUPPORT 不得列 `ANSWER`；`LIMITATION` 只在
   current SUPPORT 为零且至少有一个 BOUNDARY 时可列。只要已有 current SUPPORT，混合已知事实与未决边界必须使用 `ANSWER`，以 Claim/Citation
   表达所有 affirmative conclusion、以 Boundary 表达仍 material 的未知部分，不能用零 Claim Limitation 绕过 Citation。当前 World Model 已形成
   BOUNDARY、但第一次受权 Source follow-up 仍可执行且尚未尝试时，也不得列 `LIMITATION`。若
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
   Search、budget、Provider 或其他 acquisition diagnostic 若已由后续 current SUPPORT 闭合同一 material need，通常只保留在 audit，Primary
   还须删除或纠正 Work State 中对应的已解决 Hypothesis/Open Item。global inventory count 或 Profile-wide coverage metric 只有在实际限制用户
   要求的具体 conclusion 时才可进入答案，不能代替具体 Evidence boundary。

   Application 不得机械删除这种 Boundary，因为用户可能明确询问 acquisition diagnostic 本身。每个 Package Boundary 都必须按 Package 顺序投影
   exact relevance challenge，不能再只投影 resolved Search 或只与 Draft 声明的 Boundary ID 求交。普通 retained Boundary 使用
   `BOUNDARY_MATERIALITY` kind 且 resolver 为空；同一 Source Search 的 SUPPORT item 被后续 current-Turn full exact Source Read 闭合时，该
   Search Boundary 使用 `RESOLVED_ACQUISITION` kind，并绑定 non-empty resolving Source Read Observation IDs。resolved 判断先允许 exact opaque
   `locator_reference` 相等；不同 operation 生成不同 reference 时，只能比较 Application-sealed retrieval item 的 exact canonical resource locator：
   Search item 必须来自 `SOURCE_SEARCH`、绑定 authorized Citation 且 modality 为 `LITERAL_TEXT_SEARCH_HIT`；其 locator 只去除格式化
   `:Lstart[-end]` 后缀。Read item 必须来自后续 `SOURCE_READ`、绑定 authorized Citation、modality 为
   `EXACT_STATIC_SOURCE_TEXT` 且 `coverage_complete=true`。basename、前后缀、相似 path、错误 operation/modality 或其他模糊匹配不得闭合。

   每个 challenge 还必须绑定 Boundary 与 `draft_declared_boundary_reference`，使直接写入正文但不声明 ID 的诊断、普通 global metric 和 stale
   reference 都必须经过 focused Review。focused Reviewer 必须检查完整 Draft，并独立比较 original User requirement、完整 Boundary scope 与可选
   resolving SUPPORT。`draft.boundary_observation_ids` 是 Evidence binding，不自动把 Boundary 的 raw observation metadata、inventory、audit 或
   provenance fragment 披露给用户；是否披露只能按 `draft.content` 实际出现的正文判断。`engineering-agent-independent-review-proposal@8`
   必须为每个 relevance assessment 返回 ordered presentation-unique `draft_disclosed_fragments[]`；每项是从 current `draft.content` 逐字复制的
   non-empty substring。唯一允许的 presentation normalization 是在 fragment 与 Draft 两侧删除 U+0060 Markdown inline-code backtick
   delimiter bytes；其余文字、字符、标点和顺序必须 verbatim。normalized-empty 或 normalized duplicate 非法，语义改写或虚构内容仍失败关闭。
   Application 在 model decode、Review record 与 Delivery closure 三层使用同一 normalization 逐项重算。自由文本 `boundary_scope/user_requirement`
   或 Boundary 原文不能替代该闭合证据。只有正文实际披露的每个 fragment 都由用户明确要求或仍限制 material requested conclusion、且 Draft
   已绑定对应 Boundary、fragments non-empty 时返回 `MATERIAL_TO_USER_REQUEST`；Draft 既未绑定也未披露时返回
   `NOT_DISCLOSED_IN_DRAFT`，此时 fragments 必须为空。Application 必须为每个 challenge
   投影由 trusted kind 与 `draft_declared_boundary_reference` 共同派生的两个 `allowed_exact_dispositions`，Reviewer 只能复制其中一项，decoder
   逐 challenge 重算并在错误时返回 exact index/ID/domain，不能要求模型从 Boundary prose 反推 trusted kind。current input 与 final
   preflight 还必须逐 challenge 投影 exhaustive `closed_dispositions_by_fragment_state`：bound + empty fragments 只能选择 kind-specific
   audit-only 并绑定 global reference-removal Finding；bound + non-empty fragments 可由 Reviewer 在 material 与 audit-only 中判断；unbound +
   empty fragments 只能 `NOT_DISCLOSED_IN_DRAFT`；unbound + non-empty fragments 只能 kind-specific audit-only。User requirement、自由文本
   `boundary_scope` 或“正文未披露”的模型判断都不能覆盖 sealed reference flag；final preflight 必须从 trusted role input 重算该表，不能复制
   candidate 自报值。其他
   `RESOLVED_ACQUISITION` 只有在 stale structured reference 或至少一个 exact disclosed fragment 仍存在时才能返回
   `RESOLVED_AUDIT_ONLY`；`BOUNDARY_MATERIALITY` 同理才能返回 `NON_MATERIAL_AUDIT_ONLY`。两种 audit-only disposition 都必须绑定
   `claim_index=null / requires_evidence=false` 的 Finding，且 remedy 必须删除至少一个真实 reference 或 exact fragment。未绑定且 fragments 为空的
   audit-only 是无修复面的 no-op，必须 structured-output-invalid；不在 Draft 中的虚构 fragment 同样失败关闭。bound-but-undisclosed stale
   reference 仍可由 audit-only Finding 删除。audit-only assessment 缺少 `finding_code` 与 non-audit-only assessment 非法携带
   `finding_code` 必须形成单义 typed diagnostic；bounded diagnostic 必须并置 trusted reference flag 与 submitted exact fragment count。
   repair 必须先重算 exact fragments/reference：unbound + empty 才能使用 `NOT_DISCLOSED_IN_DRAFT` 并清除 no-op Finding；bound + empty 必须
   使用 kind-specific audit-only、绑定 unique global no-evidence reference-removal Finding 并返回 FINDINGS；其他组合按逐 challenge closed 表选择。一个 material
   gap 不得让同 Observation 内的 unrelated global inventory/coverage metric 自动
   material。`LIMITATION` 必须始终绑定至少一个与用户请求相关的 reportable Boundary，并且 current SUPPORT 必须为零；其正文只能表达
   material unresolved boundary，不能附带源码调用、结构、顺序或其他 affirmative diagnostic。删除 audit-only prose 时必须保留或替换该
   material binding，不能把“结构化 binding 不等于全文披露”误作零 Boundary Limitation 的许可。opaque Boundary ID 或 raw Observation 不需要出现在正文；Draft 已陈述 material unresolved requirement 并绑定对应
   Boundary 时，Reviewer 不得仅因正文没有命名该 ID 或复述 raw metadata 而返回 Finding。Application 不按 failure code、问题词或语言关键词
   自动重写 Provider Draft。

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
   `ENGINEERING_AGENT_REVIEW_INPUT@16` 必须投影 exact ordered Claim indices；`engineering-agent-independent-review-proposal@8` 必须为每个 Claim 返回一个
   `SUPPORTED/DEFECT` assessment。Application 重算完整 index set，禁止 SUPPORTED Claim 携带 Finding，并要求每个 DEFECT 至少绑定一个
   Finding；`APPROVED` 只允许全 SUPPORTED + empty Findings。global completeness/relevance Finding 可用 `claim_index=null`，但不能把
   “证据已支持/没有 defect”编码为 claim Finding。它只能返回 `APPROVED` 或带具体 Claim/证据缺口的 Finding；流畅、沿用上一轮或其他检查
   通过不能抵消重大错误。Reviewer 必须先审核完整 Draft 并在同一个 Review 中返回全部已经观察到的独立 material defects，不能故意只报
   第一个再把其他已见缺陷推迟到 fresh Review。每个独立 Finding 使用唯一 local code；code 只作本 Review 内引用 identity，不承载审核
   语义。只有完全未被任何 focused assessment 的 `finding_code` 引用的重复 code，model-boundary adapter 才可以只添加稳定后缀
   disambiguate identity；Finding message、requires-evidence、Claim binding 和全部顺序不得改变。任何被 assessment 引用的重复 code 都保留
   原值并按 structured-output-invalid 失败关闭，不能按数组位置猜测引用关系。`decision` 是 typed body 的冗余摘要：findings non-empty 才能为 FINDINGS；全部 Claim 与
   focused assessment closed 且 findings empty 时必须由 Reviewer 返回 APPROVED。bounded same-profile repair 可以在 exact diagnostic 下只修
   该 decision，不能制造 Review-contract Finding；Application 不得生成或静默升级 Reviewer approval。Reviewer 必须先比较完整
   `draft.content` 与枚举 Claim；未进入 Claim inventory 的 material affirmative
   conclusion 形成 `claim_index=null` 的 global completeness Finding，不能因所有枚举 Claim 都 SUPPORTED 而批准。比较时必须以 heading、
   table column、list lead-in、label 与 surrounding sentence 重建完整 assertion；Claim 漏掉物质继承 qualifier 属 global completeness
   Finding，qualifier 错误、无据或误分类属 concrete defect，窄 Claim 获支持不能批准其容器扩张。Claim coverage 是
   semantic/many-fragment-to-one，不是每个 phrase、call 或 sentence 单独一个
   Claim：一个 grouped Claim 若完整保留 category、scope、condition、certainty、negation 与 local ordering qualifiers，且其 current SUPPORT
   覆盖这些内容，就可覆盖多个正文 fragment。Reviewer 返回 global-completeness Finding 前必须检查全部 ordered Claims，不得把语义已覆盖的
   assertion 再拆成 redundant Claim。只把已枚举结论归属于 `turn.binding.repository_revision` exact revision 的 heading/footer 是受信 provenance
   context，不要求 standalone Claim；不同或虚构 revision 仍是 concrete defect。纯粹表述 current Evidence 未确认/未建立 requested relation、
   order、effect 或 guarantee 的 material Boundary 不是 affirmative Claim；file/search/tool/model 内容的 affirmative diagnostic 仍须
   SUPPORT-bound，否则必须从 Limitation 删除或收窄。路径、package、import、
   symbol name、directory convention 或 caller syntax 不能单独证明类型继承/catch coverage、数据库约束、运行时配置值、
   code-generation/tool provenance 或外部副作用；Primary 必须取得直接声明/执行该关系的 current Evidence，或把结论收窄为不依赖未知关系的结果，Reviewer 对违反
   该规则的 material Claim 必须返回 Finding。current Source 行直接包含 call expression 时，它只直接证明 caller 调用该表达式及源码可见
   的局部顺序，不证明 callee 实现、动态目标、返回语义、类型继承或外部副作用；Draft 只陈述该 invocation/order 并明确把 callee semantics
   留在 evidence boundary 时，Reviewer 不得因后者未知而拒绝前者。对于 Claim 引用 full exact Java Source 且复现其中 receiver method call
   expression 的情况，Application 必须投影 exact caller/callee challenge，绑定 Claim index、Source Observation/locator、call expression、
   declared receiver type、exact current challenged Claim statement，以及 Package/cited callee implementation Observation IDs。focused Reviewer
   只能从该 exact ordered Claim statement 分类语义 scope；User requirement、邻接 `draft.content`、先前 Review/Finding 与 method/call-expression
   name 都不能为 Claim 增加 effect semantics。identifier 即使惯常表示 insert/save/delete/update/publish/remote write，也不能单独证明 effect。
   该结构投影只是 review lead，不是自动 defect：focused
   Reviewer 必须逐项返回 non-empty closed `draft_semantic_scopes` 与 `WITHIN_CALLER_EVIDENCE` 或
   `CLAIM_EXCEEDS_CALLER_EVIDENCE`。scope vocabulary 为 `CALLER_INVOCATION / SOURCE_VISIBLE_LOCAL_ORDER /
   CALLEE_IMPLEMENTATION_OR_RETURN / DATABASE_OR_EXTERNAL_STATE_EFFECT / CONSUMER_VISIBLE_RUNTIME_EFFECT`；没有 cited implementation 时，任何
   后三类 scope 与 `WITHIN_CALLER_EVIDENCE` 的组合必须由 Adapter/Application/Response Control 失败关闭。exceeded 状态必须绑定 challenged Claim 的
   concrete Finding；focused Review 还必须双向闭合：exact `DEFECT` Claim index set 等于
   `CLAIM_EXCEEDS_CALLER_EVIDENCE` challenges 投影的 Claim index set，exact Finding code set 等于 exceeded caller assessments 与
   audit-only Boundary relevance assessments 引用的 code set。`WITHIN_CALLER_EVIDENCE` 不能与该 Claim 的 unbound caller-effect Finding
   并存，focused Review 不能引入 comprehensive/global-completeness Finding。Decoder 在 model boundary 重算 Claim/body closure，Application
   seal 在 typed Reviewer port boundary 重算其可见的 exact Finding/reference closure。未被该 Claim 引用的 same-Package callee Evidence 只允许 successor rewrite，不能追认当前 Claim。语义 scope 仍由 fresh
   Reviewer 分类，Application 不做自然语言关键词判错。Authorization、Evidence Coverage、Tool availability 与 runtime
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
   Observation 仍形成新 Package。Reviewer 返回 Findings 后，下一次 Primary invocation 必须把 exact rejected Draft 与 ordered Findings、
   Review digest 一起密封；三者共同存在或共同缺席。Application 必须在 Provider 前重验 rejected Draft 的 Turn、origin Work State、
   canonical digest 及当前 SUPPORT/BOUNDARY reference domains。无需新 Evidence 的同包 successor 只能把该 Draft 作为 exact edit base，
   按 Findings 删除、收窄、限定、重排或重述；不得从 Work State 重建全文、增加新的用户可见物质断言或相邻细节。只有 global
   completeness Finding 明确指出 rejected Draft 正文已有但 Claim inventory 未枚举的断言时，才能增加对应 Claim entry；rejected Draft
   仍是 untrusted model-authored data，不取得 Evidence authority。该 exception 只直接适用于 `ANSWER`；`LIMITATION` 的 Claim inventory
   必须保持为空，并通过删除/收窄相邻 affirmative diagnostic 收敛为纯 material Boundary。只有原正文已有 assertion、current SUPPORT
   可绑定且不增加新物质结论时，才可转换为 ANSWER 并枚举它。同一个 replacement 必须解决全部 ordered Findings，不能只修第一个、只改
   unrelated Boundary reference，或保留 Finding 已指名的同一 semantic defect。caller-effect Finding 必须同时收窄 challenged Claim 与
   matching content fragment 到 observed invocation/local order；unsupported diagnostic 必须删除或收窄为纯 material Boundary，不能把该
   Boundary 提升为新 affirmative Claim。若 replacement 的 response kind、content、ordered Claims/bindings 与 Boundary IDs 全部等于
   exact rejected Draft，Application 必须以 structured-output-invalid 拒绝；只改 Work State 不是 rewrite。LIMITATION 的 global Finding
   优先通过删除相邻 file/interface/tool/model/search affirmative diagnostic 并只保留 material unresolved boundary 收敛，不能用另一份
   inventory/diagnostic 替换争议内容。任一 Finding 标记
   `requires_evidence=true` 时，standard successor Primary input 必须把 `tool_action_required` 设为 true，并把 Draft response kind domain 置空；
   主 Agent 只能从 effective tool catalog 提交一个 exact action，不能只重写被拒 Draft。该 action 完成后，Application 必须保留 exact rejected
   Draft、全部 ordered Findings 与 Review digest 作为下一 invocation 的 correction baseline；新 Evidence 扩展 Package，但不消除任何 Finding，
   尤其不消除 `requires_evidence=false` 的删除、收窄或限定义务。补证后的 Primary 可以继续选择仍合法的 targeted action，或提交一个同时解决全部
   Findings 的 replacement Draft；只有 replacement Draft 被接受为 Proposal 后才清除 review-correction state。任何新 Observation 都形成新
   Ledger/Package Revision，旧 Review 不得放行新 Draft。evidence-only completion 不恢复工具；此时 Reviewer 要求新 Evidence 仍按 no-progress failure
   关闭。生成者不能自审，Reviewer 不能自行执行工具或放行。同包重写、补证后重答与每次 fresh Review 都是当前 execution profile 内的新 authorized
   model call，必须有新 call identity、Manifest 和 one-use receipts；它们不是重发同一 Provider request。closed JSON 输出无效时，若已资格化的通用格式修复步骤、
   权威和预算都存在，也只能用同一 execution profile 创建新 authorized call；否则当前 Turn 失败关闭。格式修复输入必须把 trusted local
   validator error code 与 Application-owned bounded diagnostic（以 deterministic trusted-schema traversal 一次收集 parent 与 nested
   object 中最多 32 处可机械定位的 mismatch；每处保留失败路径，并把该路径上 trusted schema 的完整 exact field allowlist、缺失 field
   names、unexpected count 和 additional-fields-forbidden 状态投影给 repair；untrusted unexpected key name 不回显）同原始失败
   call receipt 和 untrusted prior output 一并绑定。repair 必须按 `allowed_exact` 重建该 object；sealed input 的 identity/metadata 字段只有
   同名进入 output allowlist 才能出现在输出。对 parseable `CLOSED_SCHEMA_SHAPE` failure，Application 必须从 untrusted prior output 与
   trusted schema 递归形成 `ENGINEERING_AGENT_OUTPUT_PREFLIGHT@19 / existing_allowed_field_copy_projection`：只保留已存在且当前子树 shape
   可对齐的 allowlisted field/value，排除 unexpected field 并保持 missing field 缺席。若一个 schema-invalid array 的所有 item 都没有任何
   已存在 allowlisted value，则整个 array 子树不形成 copy obligation；repair 只能从 current sealed schema/domain/template 重建它。只要该
   array 仍有一个既存 allowlisted item value，原长度/顺序与所有可对齐值就必须保持，不能用重建吞掉合法 sibling。final preflight 还必须
   递归列出 nested object/array item 的 exact required fields 并明确 additional fields forbidden：Primary action argument item 只能是
   `{name,value}`，Reviewer Boundary assessment 只能使用 `challenge_id`。Primary preflight 必须从 trusted completion policy 投影唯一有效
   branch：action 只允许 nonterminal phase 且 draft 为 null；Draft 只允许 `RESPONSE_READY` 且 action 为 null；`ANSWER` 至少一个 Claim，
   `CLARIFICATION` 无 Claim/Boundary，`LIMITATION` 无 Claim、current SUPPORT 必须为零且至少一个 reportable Boundary。Provider output 不能自行改变该 branch。
   Primary final preflight 还必须再次列出当前 ANSWER Claim SUPPORT 与 Draft Boundary 的两个 exact allowed Observation ID domains，明确
   cross-disposition 和 unknown references 均 forbidden，并重复 active same-Package rewrite contract。final preflight 列出的
   resolved-acquisition candidate Observation IDs 只是 audit-only-by-default 的 review lead，不是完整 Package inventory；只有 current User Message
   明确询问该 acquisition diagnostic 时才能按 focused materiality contract 进入正文。这些值只冗余 sealed Primary input 的约束，不新增
   Evidence、Tool、Review 或 Delivery authority。
   Primary/Reviewer 仍须精确复制 projection；在 Proposal decode 前，Application 还必须以
   `RESTORE_SCHEMA_MATCHING_ALLOWLISTED_VALUES_BEFORE_DECODE@1` 把 repair 对这些既存值的任何原始漂移机械恢复为 prior exact value，再递归重验
   最终值与顺序守恒。该 restoration 不能生成 missing field、保留 unexpected field、重建无 copy obligation 的 invalid 子树、改变 array
   对齐或授予 Tool/事实/Review 权限；不能恢复到完全相等时仍以 structured-output-invalid 失败关闭。raw Provider output、prior output、schema
   与最终 sealed Work State identity 必须保留可重算关系，raw 漂移本身从不获得授权。nullable union、本地 schema reference 或嵌套 object
   不得隐藏可机械定位的字段缺失；parent mismatch 不得提前结束对仍存在的 allowlisted child value 的遍历。该 projection/restoration 只把
   既有守恒义务做成可信机械边界，不赋予事实、语义、Tool、Review 或 Delivery authority，也不得被扩张成任意输出正规化。repair 必须先保持
   projection 中全部既有合法 exact value，再补 missing field，不能借 shape repair 协调 decision、Finding 或其他语义。model-authored object
   进入 typed domain constructor 后产生的 `INVALID_ARGUMENT` 必须归一化为 `STRUCTURED_OUTPUT_INVALID`；Application 自身 authority/invariant 的
   非该类 DomainError 必须原样传播，不能被这条 untrusted-output 边界掩盖。
   `engineering-agent-work-state-proposal@2` 由 Application 从 invocation 直接绑定 Observation prefix，不属于 repair 或 Provider output
   正规化：该字段不在 output schema 中，Provider 若输出它必须按 unexpected field 拒绝，Application 不能从 raw output 猜测或模糊纠正 ID。
   `CLOSED_OUTPUT_CONTRACT` repair 若发现真实缺口只是绑定到错误 Claim，不得为满足一致性
   而删除缺口；针对未枚举正文结论的 Finding 应保留并使用 `claim_index=null`。diagnostic 只定位 exact closed output violation，不授予
   事实、工具或审核权。repair input 必须显式投影 prior exact output 不得原样返回，并为 closed-contract failure 给出从 local typed
   violation 派生的 convergence directive：重复 Source query 只能换当前 sealed legal action，或在没有新 source-native literal 且当前
   response domain 允许时用现有 reportable Boundary 收敛；focused closure mismatch 必须重建 verdict、disposition、finding code 与 Finding
   的整组闭合。若 exact diagnostic 表明 Findings 不等于 challenge-bound Finding set，则每个 retained Finding 必须绑定一个 exact challenge、
   复制其允许的 audit-only disposition 并使用同一 unique finding code；若所有 challenge 都是 material，则必须删除 unbound Findings 并
   APPROVE，不能重复 `MATERIAL_TO_USER_REQUEST + null finding_code + extra Finding`。audit-only 缺少 Finding binding 时必须保留该 disposition、增加 matching global no-evidence Finding 并改为 FINDINGS。
   第一次 Source Search 未复制 cognition-derived target literal 时，repair 必须选择 sealed domain 中与当前用户目标 material 的 allowed literal；
   若不存在，则改用合法且不同的 `WORLD_MODEL_QUERY`，不得原样重复非法 literal，也不得为满足字面 allowlist 选择无关 target。
   same-Package 或 post-evidence correction 若逐字返回 exact rejected Draft，repair 必须对每个 Finding 指定的 fragment 做更严格且不同的
   edit；caller-effect Finding 在 baseline 已是 invocation/local-order wording 时，必须在正文与 Claim 中显式区分 observed invocation/order
   与未确认的 callee/database/remote/consumer effect，或删除非必要 challenged assertion，不能让 method name 重新授予 effect semantics。
   focused diagnostic 可以投影实际 DEFECT/EXCEEDS index set，但不得把 untrusted Finding message 提升成 trusted instruction。final preflight
   必须冗余投影该 closed-contract directive，但不从中取得新事实或审核权。这些 directive 不新增 Tool、Evidence、Review 或 Delivery
   authority。除上述显式、版本化、可重算的 existing-value restoration 外，Application
   不得据此静默规范化模型输出或改变 Provider adapter
   identity/qualification。所有 Provider-authored string 必须是 non-empty、且首尾都不是 whitespace；特别是 `draft.content` 的 Markdown
   最后一个字符不能是空格或换行。Prompt 与 final preflight 必须显式投影该 closed constraint，Application 仍按原值失败关闭，不能 trim 或
   静默规范化。两种情况都不允许改换 route role。该诊断性修复沿用 current
   `conversational-engineering-agent@24 / conversational-engineering-agent-no-tools-prompt@24 /
   ENGINEERING_AGENT_PRIMARY_INPUT@24 / ENGINEERING_AGENT_REVIEW_INPUT@16 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@19` 协议族；每次
   Session authority、role request 和 Provider request 仍必须绑定修复后的 exact prompt/input digest，旧字节不能冒充 current 输入。若
   first non-whitespace character 不是 `{`，bounded diagnostic 必须以 `NON_JSON_OBJECT_PREFIX` 定位 envelope failure 而不回显前缀；final
   preflight 必须明确禁止 JSON object 前后的 analysis/narration。一个 logical role step 最多允许两次 repair；第二次只允许前一个 repair 产生
   fresh `PROVIDER_OUTPUT_INVALID`，且 local validator category 必须与前一失败不同。semantic contract repair 若已经纠正 named closure、但新输出
   回退为 envelope/JSON/shape failure，可使用最后一个 slot 修复该不同 category；相同 category 不再调用，closed-shape existing-value
   restoration 自身的守恒拒绝仍属于同一 category。每个 repair 都必须是
   same execution profile 下的新 request/Manifest/one-use receipt，不是 Provider retry，不取得 fallback eligibility，也只能消耗 existing
   per-Turn 15 dispatch authority 的剩余 slot；Authorizer 在 authority 耗尽时必须在 Provider boundary 前拒绝。该分类不允许 Application 抽取后部
   JSON、提高 dispatch/Tool/Source/Session budget 或把格式失败改判为 Provider unavailable。
6. Reviewer Strategy 可以在资格中采用多个隔离视角或 challenge，但固定角色数量、固定 focus 顺序、固定检查清单 JSON 和一次单独
   Verification Investigation Agent 不是长期架构不变量。current `@24` Strategy 对每个 Draft 先执行 comprehensive Review；若 Application
   投影出 caller/callee challenge 或 Package 含任何 Boundary，再执行一个 fresh focused Review。focused Finding 的 successor Draft 可按
   仍存在的 challenge focus 直接复审。为容纳一次 comprehensive rewrite 和一次 focused rewrite，
   Reviewer call 上限现为 4，同时 Agent step 上限从 12 收紧为 11，最坏组合仍为原有 15 per-Turn dispatch authority。Response Control 必须重算
   exact ordered challenge/assessment set，只有 caller challenge 全部 `WITHIN_CALLER_EVIDENCE`、每项 closed semantic scope 与 challenge 一致、
   relevance challenge 全部为已绑定的 `MATERIAL_TO_USER_REQUEST` 或未披露的 `NOT_DISCLOSED_IN_DRAFT`，且 empty Findings 时才放行。
   comprehensive Reviewer 对 `LIMITATION` 不得要求增加 Claim、exact-answer detail、interface/search inventory；pure、relevant、正确绑定的
   Limitation 不因当前 Package 无法满足用户原始 Answer/full-chain/exact-Source 要求而产生虚构 completeness Finding。Adjacent affirmative
   diagnostic 的无补证修复只能删除/收窄为 pure material boundary；已有 exact opaque Boundary ID 时不得声称未绑定，Search hit 或 interface
   declaration 也不能冒充 implementation、remote effect 或 consumer-visible evidence。
   该 Strategy 不提高 15 per-Turn dispatch authority、Tool/File fuse 或 Provider retry。任何 Strategy 都不得少于一次 fresh
   独立审核，或取消逐结论 evidence closure。

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

Fallback eligibility 不得从 raw error string、owner code、HTTP status 或 outcome 直接推断。model boundary receipt 必须保存原始 owner code 和 trusted failure kind；若 Gateway 密封了 HTTP failure evidence，还必须成对保存受限 status 与 evidence digest，并把两者经 Turn outcome、attempt receipt 和 availability verdict 绑定传递，但它们仍只是证据。
只有 preferred execution profile 登记的受信 availability owner 能对 exact profile/ref、当前时间与 receipts 密封
`PREFERRED_EXECUTION_PROFILE_UNAVAILABLE` route verdict。当前 owner 只接受 typed pre-HTTP unavailable，或拥有 exact dispatch/call receipt 与
Gateway evidence digest 的 `{402,408,425,429,500,502,503,504}`；`400/401/403/404/409/422`、未密封 status 和字符串相似性都 fail closed。
`PROVIDER_OUTPUT_INVALID`、`MODEL_REVIEW_REJECTED`、pre-dispatch、Capability/qualification、
Gateway/repository/result identity、Application、Source、authorization/admission 或 Security failure 均保持 non-eligible。每个 attempt authority/receipt 绑定 logical Turn parent、route role、execution profile、
availability owner/verdict、admission plugin/session、execution-profile/disclosure/dispatch-admission/transport/model/terminal receipts 和 same-request retry 0；logical Turn Result 只取最后一个完整 attempt 的 Outcome，
但汇总全部 attempt dispatch。availability owner 若基于 preferred outcome unknown 形成 unavailable verdict，后续 fallback 必须标记 duplicate-cost risk；late preferred-route result 固定
`QUARANTINE_AUDIT_ONLY`，没有覆盖、拼接或追认最终结果的接口。

Browser 的失败视图必须把 logical Turn/Agent/Application 的 execution-stage failure 与已密封 raw Provider evidence 分层显示；存在
`provider_failure_classification/provider_failure_code` 时不能只显示上层 stage code，存在 Gateway-sealed HTTP evidence 时还要显示受限
status 并保留 evidence digest identity，不存在时也不能推测 Provider 原因。这个显示不取得
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
run-085 随后完成 52 次 Ark HTTP dispatch，其中 51 次完成、1 次在发出后成为 `PROVIDER_OUTCOME_UNKNOWN`；没有 HTTP 前 trusted
unavailable，故 DeepSeek 0 正确。Q4 fresh Conversation 零 dispatch Clarification 继续通过，其余工程 Turn 未交付。Q1 暴露 Reviewer nested
`challenge_id` 与 existing-value repair 缺口；Q3 暴露 Boundary evidence binding 被误作 raw metadata 全文披露，并继发空 Boundary
`LIMITATION` 与 action/phase 冲突；Q5 的 action argument shape 和 required-action branch 漂移耗尽既有 15 次 authority。
`FINDING-010-208` 已形成 current `@13/@7/@8` nested closed-shape、trusted branch、binding/disclosure 和 untrusted typed-error candidate；
144 项定向测试 PASS，fresh run-086 仍须证明真实 Answer/Review，run-085 保持质量 FAIL。
run-086 随后完成 49 次 Ark HTTP dispatch，其中 47 次完成、2 次在发出后成为 `PROVIDER_OUTCOME_UNKNOWN`；没有 HTTP 前 trusted
unavailable，故 DeepSeek 0 正确。Q4 fresh Conversation 零 dispatch Clarification 继续通过，其余工程 Turn 未交付。Q2 暴露 final
preflight 未重复 exact SUPPORT/BOUNDARY ID domains；Q3 暴露 Review successor 只收到 Findings/digest、没有收到 exact rejected Draft，
使同包重写的 Claim inventory 从 `5 → 10 → 7 → 13` 扩张并产生新缺陷。`FINDING-010-209` 已形成 current `@14/@7/@9` exact rejected-Draft
edit base、targeted rewrite 与 redundant reference-domain preflight candidate；144 项定向测试 PASS，fresh run-087 仍须证明真实 Answer/Review，
run-086 保持质量 FAIL。
run-087 随后由 Ark 10 个完成 call 与 4 个 sealed `429 / AccountQuotaExceeded` call 触发合法 DeepSeek fallback；DeepSeek 42 个完成 call、
1 个 post-dispatch `REMOTE_DISCONNECTED / PROVIDER_OUTCOME_UNKNOWN`，retry/人工审批/Production 仍为 0。Q4 fresh Conversation 零 dispatch
Clarification 继续通过；Q1/Q2/Q5 均以 Review limit 失败，Q3 按 unknown no-retry 失败。Q1 的 exact rejected Draft Claim inventory 保持
`4 → 5 → 6 → 6 → 6`，证明 `FINDING-010-209` edit base 已真实生效；新的 first divergence 是 Reviewer 把 exact-revision provenance、grouped
Claim 与已明确 local order 按 phrase 重复拆分。Q2/Q5 又证明 generic global-completeness Claim exception 与 `LIMITATION` 零 Claim branch
互相冲突，且 opaque Boundary binding 被误作必须在正文披露。`FINDING-010-210` 已形成 current `@15/@8/@10` semantic Claim coverage、
response-kind-aware rewrite 与 hidden Boundary binding candidate；144 项定向测试 PASS，fresh run-088 仍须证明真实 Answer/Review，run-087
保持质量 FAIL。
run-088 随后由 Ark 4 个 sealed `429 / AccountQuotaExceeded` call 触发合法 DeepSeek fallback；DeepSeek 52 个完成 call、1 个
post-dispatch `REMOTE_DISCONNECTED / PROVIDER_OUTCOME_UNKNOWN`，retry/人工审批/Production 仍为 0。Q4 fresh Conversation 零 dispatch
Clarification 继续通过；Q1/Q5 在下一 Reviewer 前耗尽 authority，Q2 达到 Review limit，Q3 按 unknown no-retry 失败。新的 first
divergence 是 comprehensive Reviewer 逐轮只报一个 defect并重复 Finding identity，focused Reviewer 让 closed assessment body 与
decision/Finding 自相矛盾，Primary 又未在一个 replacement 中解决全部 ordered Findings。`FINDING-010-211` 已形成 current
`@16/@9/@11` complete-Draft audit、focused exact closure、Reviewer-authored decision repair、未引用 duplicate local-code disambiguation 与
all-Findings rewrite candidate；146 项定向测试 PASS，fresh run-089 仍须证明真实 Answer/Review，run-088 保持质量 FAIL。
run-089 由 Ark 4 个 sealed `429 / AccountQuotaExceeded` call 再次触发合法 DeepSeek fallback；DeepSeek 27 个完成 call、1 个
post-dispatch `REMOTE_DISCONNECTED / PROVIDER_OUTCOME_UNKNOWN`，retry/人工审批/Production 仍为 0。Q4 fresh Conversation 零 dispatch
Clarification 继续通过；Q1 的 focused closure guard 正确拒绝 Reviewer 矛盾 body，但同-profile repair 原样复制；Q3 在 World Model 与 Source
Search Boundary 已允许 Limitation 时仍连续复制 forbidden exact query；Q5 的 Primary 两次返回 exact rejected Draft，comprehensive Reviewer 又在
Limitation 上要求 Claim、误报已有 Boundary binding 并把 Search/interface 当实现证据。`FINDING-010-212` 已形成 current
`@17/@10/@12` changed-replacement guard、typed closed-contract convergence directive、actual focused index diagnostic 与 response-kind-aware
Limitation review candidate；147 项定向测试 PASS，fresh run-090 仍须证明真实 Answer/Review，run-089 保持质量 FAIL。
run-090 的 Ark 33 个 call 中 31 个完成、1 个 pre-dispatch TLS failure、1 个 post-dispatch unknown；Q3 fallback 因 pricing evidence 超过
900 秒在 DeepSeek credential/TLS/HTTP 前关闭，DeepSeek dispatch 0，retry/人工审批/Production 仍为 0。Q4 fresh Conversation 零
dispatch Clarification 继续通过；Q1 的 coherent closed-contract repair 回退到 non-JSON prefix 后旧单向 category gate 未使用第二个 repair
slot，Q2 的 audit-only relevance assessment 缺 Finding code且 generic repair 原样返回。`FINDING-010-213` 已形成 current
`@18/@11/@13` distinct-category final repair、单义 audit-only diagnostic/typed closure 与 final-preflight directive candidate；模型边界 34
项测试 PASS，相邻定向集与 fresh run-091 仍须证明真实 Answer/Review，run-090 保持质量 FAIL。
run-091 的 Ark 38 个 call 中 37 个完成、1 个 post-dispatch `REMOTE_DISCONNECTED / PROVIDER_OUTCOME_UNKNOWN`，不存在可信 pre-dispatch
unavailable verdict，故 DeepSeek dispatch/credential/TLS/HTTP 全为 0；retry、人工审批和 Production 仍为 0。Q4 fresh Conversation 零 dispatch
Clarification 继续通过；Q1 以零 Citation 的混合事实/边界 Limitation 被错误交付，Q2 补证 action 后丢失完整 Review correction baseline 并在下一
focused Review 前耗尽 authority，Q3 的 cognition-literal repair 原样重复非法 query，Q5 按 post-dispatch unknown no-retry 失败。
`FINDING-010-214` 已形成 current `@19/@11/@14` 补证后全 Findings 保留、Limitation 零 SUPPORT、material cognition-literal replan 与
resolved-candidate final-preflight 冗余 candidate；fresh run-092 仍须证明真实 Answer/Review，run-091 保持质量 FAIL。
run-092 的 Ark 53 个 call 全部完成，TLS/credential/HTTP 均为 `53/53/53`；不存在 raw failure 或 trusted pre-dispatch unavailable verdict，
故 DeepSeek 全链路 0 是 preferred route 持续可用时的正确结果。Q3 以 1 个 exact Source Citation 和 fresh Review/Delivery 成功，Q4 fresh
Conversation 零 dispatch Clarification 继续通过；Q1/Q2/Q5 分别耗尽 dispatch 或 Review authority。三题共同 first divergence 是
Reviewer 在明确“Draft 未披露、也未绑定 resolved Search diagnostic”时仍可返回 audit-only disposition 并制造无可删除对象的 global Finding；
replacement Draft 后同一 Finding 重现。`FINDING-010-215` 已形成 current `@20/@12/@15` exact
`draft_disclosed_fragments[]`、reference/fragment/disposition 三向闭合与 no-op audit-only rejection candidate；73 项 Agent/Tool/Model 测试
PASS，相邻定向集与 fresh run-093 仍须证明真实 Answer/Review，run-092 保持质量 FAIL。
run-093 随后以 Ark 3 个 sealed 429 合法自动激活 DeepSeek 并完成 28 个 fallback dispatch，证明备用路线与 standing authority 正常；Q1
暴露 exact fragment 的 inline-code backtick presentation mismatch，Q2/Q5 暴露 original-question module scope 未进入 Source Search且多个
query 重扫 canonical fallback 前缀。`FINDING-010-216/217` 已形成 current `@21/@13/@16` backtick-only normalization 与
`COMPILED_SOURCE_OPERATION@3` Broker-recomputed prefix/rotating fallback contract；六模块 154 项、相邻十五模块 229 项定向测试 PASS，fresh run-094 仍须证明真实
Answer/Review，run-093 保持质量 FAIL。
run-094 随后以 Ark 4 个 sealed 429 合法自动激活 DeepSeek；DeepSeek 20 个 call 完成、1 个 post-dispatch unknown，retry、人工审批与
Production 均为 0。Q1 以 2 个 exact Citation 取得 ACCEPTED，证明 backtick fragment closure 真实通过；Q4 零 dispatch Clarification 继续
通过。Q5 的合法 `SOURCE_SEARCH(SOURCE, ElasticsearchRepository)` 暴露 question module prefix 初版把同 module POM/TEST paths 混入
SOURCE restriction，Broker 按 class 正确失败关闭。`FINDING-010-218` 已把 scope 识别保留在完整 Request allowlist，同时只从 current
evidence-class allowlist 选择 prefix；wire schema、route、rotation 与全部 fuse 不变。六模块 154 项、相邻十五模块 229 项定向测试 PASS，fresh run-095 待验证；
Q2 的 post-dispatch unknown 与 Q3 limitation 不被追认为 product quality PASS。
run-095 随后再次以 Ark 4 个 sealed 429 合法自动激活 DeepSeek；DeepSeek 27 个 call 完成、1 个 post-dispatch unknown，Q1/Q5
ACCEPTED、Q4 零 dispatch Clarification，证明 evidence-class-only prefix closure 已真实通过。Q2 在 Q1 后闲置约 141 秒时复用已失效的
DeepSeek keep-alive 并按 no-retry 失败；Q3 的 focused Reviewer 把全部 disclosed Boundary 判为 material/null code，却又返回额外
Finding，generic repair 原样重复后失败。`FINDING-010-219/220` 分别形成 credential/HTTP 前的 stale-or-60-second-idle session rotation，
以及 retained Finding 绑定 exact challenge 或删除 unbound Finding 并 APPROVE 的专用 repair closure。相邻十七模块 255 项定向测试 PASS；
DeepSeek Adapter exact bytes 已恢复并由 current Conformance loader 重新核验通过；Engineering Chat runtime transport ref `@3` 与 run-096
仍须证明真实 stale/idle rotation、Answer/Review，run-095 保持质量 FAIL。
旧
`ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3` 继续是兼容协议，不能作为本契约主 Agent 或 Chat 资格证据。
