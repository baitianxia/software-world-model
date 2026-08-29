---
id: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
kind: system-contract
status: current
authority: normative
owners: [application, source, quality, security]
depends_on: [SYS-ADR-017, SYS-ADR-018, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-CONTRACT-AI-MODEL-GATEWAY]
derived_from: [FINDING-010-097, FINDING-010-098, FINDING-010-099, FINDING-010-100, FINDING-010-101, FINDING-010-102, FINDING-010-103, FINDING-010-104, FINDING-010-105, FINDING-010-106, FINDING-010-109, FINDING-010-113, FINDING-010-116, FINDING-010-117, FINDING-010-120, FINDING-010-121, FINDING-010-125, FINDING-010-128, FINDING-010-132, FINDING-010-133, FINDING-010-136, FINDING-010-138, FINDING-010-139, FINDING-010-154, FINDING-010-156, FINDING-010-159, FINDING-010-160, FINDING-010-169, FINDING-010-170]
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
   policy 必须先识别依赖先行对象的表达；命中时由 Application 在任何 World Model、Source、credential 或 Provider attempt 前要求用户明确
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
   对先前答案的修订和仍未知范围。Primary model input 必须由可信 Application 从 exact current-Turn observations 投影两个 closed
   reference domain：affirmative Claim 只能复制 SUPPORT ID，Limitation 只能复制 BOUNDARY ID；cross-disposition 和 unknown ID 禁止。
   Decoder 必须从原 Observation 重算并 fail closed，不能删除错误 Claim、替换引用、提升 Boundary 或自动授权 Draft。current model
   input 还必须由可信 Application 从 current isolated attempt 的 typed action history 与 Source authority-receipt Citations 投影
   `tool_reference_policy`：列出已执行 exact action、已尝试 query/read 和未使用的 `source_read_options`；Provider 只能复制列出的 opaque
   locator，不能重复 exact action、伪造 locator 或把 display path 当 authority。每个 canonical Source resource 至多暴露一个 read option；
   任一 line reference 被读取后，同一 resource 的全部 reference 都离开 legal domain；没有未使用 option 时 `SOURCE_READ` 不得出现在
   effective tool catalog。受信 Ledger 已出现 operation/file/byte terminal fuse rejection 时，Source Search/Read 也必须离开 effective
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
   evidence-tool adapter 按 exact Cognition item digest 保留首次出现顺序：每次 query 仍绑定完整 current Cognition Context digest、exact
   revision、coverage、Ledger 和 authority receipt，但 model-facing SUPPORT content 与 Citation refs 只追加该 Turn 先前 SUPPORT 尚未投影的
   item，并机械记录 current/novel/already-observed counts。重复 item 的首次 Observation 不得删除、重排或改写；后续 Claim 需要该事实时引用
   首次携带它的 SUPPORT ID。一个 query 没有 novel supported item 时不得制造重复 SUPPORT，而须形成明确 no-new boundary/no-progress；含新
   boundary、conflict 或 unknown 的 Context 仍按其自身 disposition 保留。该压缩不改变正式 Cognition Context、Evidence Ledger、receipt 或
   Citation identity，也不能把未见 item、Boundary 或旧 Turn Evidence 提升为支持。

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
   通过不能抵消重大错误。所有 role output 必须是唯一 closed JSON object；JSON 外叙述继续失败关闭，不能抽取 substring 追认。
5. 现有 Package 足够时，Response Control 把 Finding 绑定到同一主 Agent的新 Work State Revision，形成同包针对性重写；任一 Finding 标记
   `requires_evidence=true` 时，standard successor Primary input 必须把 `tool_action_required` 设为 true，并把 Draft response kind domain 置空；
   主 Agent 只能从 effective tool catalog 提交一个 exact action，不能只重写被拒 Draft。任何新 Observation 都形成新 Ledger/Package
   Revision，旧 Review 不得放行新 Draft。evidence-only completion 不恢复工具；此时 Reviewer 要求新 Evidence 仍按 no-progress failure
   关闭。生成者不能自审，Reviewer 不能自行执行工具或放行。同包重写、补证后重答与每次 fresh Review 都是当前 execution profile 内的新 authorized
   model call，必须有新 call identity、Manifest 和 one-use receipts；它们不是重发同一 Provider request。closed JSON 输出无效时，若已资格化的通用格式修复步骤、
   权威和预算都存在，也只能用同一 execution profile 创建新 authorized call；否则当前 Turn 失败关闭。格式修复输入必须把 trusted local
   validator error code 与 Application-owned bounded diagnostic（至少保留失败路径和 trusted schema 中缺失的 closed-object field names；
   untrusted unexpected key 只投影 count）同原始失败 call receipt 和 untrusted prior output 一并绑定；nullable union、本地 schema reference
   或嵌套 object 不得隐藏可机械定位的字段缺失。diagnostic 只定位 shape，不授予事实、工具或审核权，Application 也不得据此静默规范化模型
   输出或改变 Provider adapter identity/qualification。两种情况都不允许改换 route role。该诊断性修复沿用 current
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
Conformance。旧
`ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3` 继续是兼容协议，不能作为本契约主 Agent 或 Chat 资格证据。
