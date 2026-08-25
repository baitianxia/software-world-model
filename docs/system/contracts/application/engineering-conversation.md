---
id: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
kind: system-contract
status: current
authority: normative
owners: [application, source, quality, security]
depends_on: [SYS-ADR-017, SYS-ADR-018, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-CONTRACT-AI-MODEL-GATEWAY]
code: [src/software_world_model/application_services/engineering_conversation.py, src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/application_services/conversational_engineering_routing.py, src/software_world_model/application_services/conversational_engineering_tools.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py, src/software_world_model/interface/engineering_chat_candidate.py, src/software_world_model/interface/engineering_chat_provider_launcher.py, src/software_world_model/interface/engineering_chat_provider_runtime.py, src/software_world_model/interface/engineering_chat_session_runtime.py, src/software_world_model/interface/engineering_chat_session_artifact.py, src/software_world_model/interface/engineering_chat_browser.py, src/software_world_model/interface/engineering_chat_browser_ui.py, src/software_world_model/interface/engineering_chat_alpha_cli.py]
tests: [tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_tools.py, tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_routing.py, tests/test_engineering_chat_candidate.py, tests/test_engineering_chat_provider_launcher.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_conversation.py, tests/test_engineering_chat_browser.py, tests/test_engineering_chat_alpha_cli.py]
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
  已提交 predecessor，但不能从 primary executor 私有内存取得 fallback 输入。
- 软件世界模型由 Knowledge Engine/Snapshot Owner 持有，可跨 Conversation 复用；对话工作状态不准写入 Snapshot 或冒充正式知识。
- 主工程 Agent 只提交 Goal/Hypothesis/Plan/Tool/Answer Proposal。它对解决过程具有认知控制，但不拥有业务状态、权限、来源、证据、正式
  知识、Review Decision 或 Delivery Authorization。
- Source Broker/Worker 拥有只读来源 Proposal 的校验、编译和执行；Reviewer 只提交独立 Assessment/Finding；Response Control 独占最终
  Authorization 与 Delivery。

系统必须区分三类输入：

1. **World Model Cognition**：exact Snapshot/Read Set 上可跨会话复用的软件认知及其 Coverage/Unknown；
2. **Conversation Work State**：当前对话目标、已确认实体、用户约束、纠正、开放问题、假设、计划、已观察结果和未完成子任务；
3. **Turn Evidence**：本 Turn 经受控世界模型查询或 Broker/Worker 取得、用于当前答案的 Ledger 与密封 Package。

对话记录、工作状态和先前助手答案都不能自动成为 Turn Evidence。任何沿用结论必须由当前 exact revision 的 admissible evidence 重新支持。

历史 Turn 的 Evidence 只有在 `repository revision + Binding + World Model authority + Source Profile + allowlist + content digest + coverage`
全部 exact match 时才可作为本 Turn 的复用 candidate；Application 仍须按本 Turn 的问题、目标和证据需求重新校验，并把实际使用项重新绑定
到本 Turn Package。旧 Answer Authorization、Review Decision、Limitation、未密封 Tool Result、Provider memory 或隐藏状态一律不可复用。
用户陈述、纠正和偏好可以改变对话目标或待验证假设，但不能成为 Source truth 或支持软件事实。

## Conversation and turn invariants

1. Conversation 在 listener/session 启动前固定产品版本、工程/Binding/exact revision、World Model Read Authority、Source Profile/allowlist、
   工具目录、Provider route、披露范围、有效期和每 Turn/整会话高安全熔断。浏览器不能扩大这些边界。
2. 每条 User Message 创建不可变 Turn。Application 从完整历史确定性选择满足本 Turn 所需的相关上下文，密封输入消息、被引用 Turn、有效
   用户约束、当前工作状态和摘要的 identity/digest；不得直接依赖 Provider 会话记忆或无边界拼接全部历史。
3. 主 Agent 必须处理追问、指代、纠正、深入、收窄和总结。若指代在密封上下文内仍不唯一，必须请求澄清或给出明确条件化解释，不能把
   猜测写成事实。用户纠正形成新 Revision 并标记被取代的对话假设，不删除原消息、证据或失败结果。
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

允许的工具只有受信 Application 提供的 closed catalog：exact World Model query/view，以及由 Source Broker 编译的注册
`search/read/parse` 等 exact-revision 只读操作。Agent 提交的 path、query、class、locator、命令、URL 或完成声明均是不可信 Proposal；
Application/Broker 重新验证 authorization、Profile、allowlist、revision、modality、bytes、进度和剩余熔断。模型没有直接 Repository/
Source Tool/FS/shell/network/credential/write/Knowledge Update 权限。

每个 Proposal、Decision、Operation、Observation、Conflict、Unknown、Failure、Coverage 和资源收据按顺序追加到 Turn Evidence Ledger。
主 Agent 可以读取本 Attempt 获准的密封 Ledger prefix 与工具 Observation，但隐藏 rationale 和未密封输出不进入权威状态。

## Evidence, answer and review

1. 主 Agent 准备回答时，Application 从 current Turn、exact Cognition、Work State 和完整 Ledger 密封当前 Question Evidence Package。
   `support/citation` 只含经 modality/Context/Coverage/Support 验证的 admissible entries；`boundary/audit` 强制保留 Gap、Failure、Partial、
   Conflict、Unknown、拒绝和资源收据。seal 只证明身份、完整性、来源与版本，不赋予内容真值。
2. Draft 可以由同一主 Agent 综合多条证据自然回答，不要求把证据记录逐条变成答案句子。每个物质肯定结论必须绑定
   `support/citation`；未知或限制必须绑定相应 `boundary/audit`。答案应延续相关对话目标、响应用户最新纠正，并区分本 Turn 新结论、
   对先前答案的修订和仍未知范围。
3. 每个可交付 Draft 至少经过一个 fresh、与主 Agent 隔离的独立 Reviewer。Reviewer 只读 current User Message、受信相关 Conversation
   Context、当前 Package 与 Draft；无 Repository、World Model/Source Tool、Broker dispatch、shell、网络、credential 或写权限。
4. Reviewer 从用户当前目标独立检查正确性、完整性、相关性、Citation 支持、条件/顺序/副作用、对话一致性、用户纠正和 Unknown 边界。
   它只能返回 `APPROVED` 或带具体 Claim/证据缺口的 Finding；流畅、沿用上一轮或其他检查通过不能抵消重大错误。
5. 现有 Package 足够时，Response Control 把 Finding 绑定到同一主 Agent 的新 Work State Revision，形成同包针对性重写；证据不足时，
   Application 形成绑定具体缺口的新 Agent Attempt，主 Agent 继续经 World Model/Broker 工具调查。任何新 Observation 都形成新 Ledger/
   Package Revision，旧 Review 不得放行新 Draft。生成者不能自审，Reviewer 不能自行执行工具或放行。
6. Reviewer Strategy 可以在资格中采用多个隔离视角或 challenge，但固定角色数量、固定 focus 顺序、固定检查清单 JSON 和一次单独
   Verification Investigation Agent 不是长期架构不变量。任何 Strategy 都不得少于一次 fresh 独立审核，或取消逐结论 evidence closure。

## Generality, evaluation and failure

核心 Agent、Prompt、工具选择、Conversation reducer、Review 和 UI 不得按工程、问题、关键词、语言、框架、符号、类、方法、约定文件名、
fixture 或 Oracle 注入专用答案逻辑。语言和来源差异只能由显式版本化 Source/Knowledge capability 注册。

产品资格必须同时验证：多轮指代、追问、用户纠正、目标延续、观察驱动重规划、World Model 与 Source 工具组合、证据引用、Reviewer 缺口
反馈和 Turn 故障隔离。系统与 current Codex 的比较用于证明产品替代价值；同一主 Agent 的 full Cognition 与 locator-only/empty 对照用于
证明世界模型认知的独立贡献，二者不得混为 Oracle。

授权/identity/revision 漂移、上下文错绑、工具越权、Ledger/Package 缺口、无依据结论、Reviewer 未通过、资源耗尽或 Provider outcome
unknown 都使当前 provider attempt 或 Turn 失败关闭。Provider fallback 只能按 ADR-017 在同一 logical Turn 下从受信 original Turn input、
exact Conversation Context 与 exact Cognition 重启完整 Agent attempt；不得复用失败 Provider 的隐藏状态或未密封中间产物。

Fallback eligibility 不得从 raw error string 推断。model boundary receipt 必须同时保存原始 owner code 和 trusted failure kind；Application
只能把 `PROVIDER_UNAVAILABLE / PROVIDER_HTTP_ERROR / PROVIDER_OUTCOME_UNKNOWN / PROVIDER_OUTPUT_INVALID / MODEL_REVIEW_REJECTED`
五类投影为 route classification。pre-dispatch、qualification、Gateway/repository/result identity、Application、Source、authorization 或
Security failure 均保持 non-eligible。每个 attempt authority/receipt 绑定 logical Turn parent、route/configuration/session、dispatch/model
receipts 和 retry 0；logical Turn Result 只取最后一个完整 attempt 的 Outcome，但汇总全部 attempt dispatch。outcome unknown 后启动 fallback
必须标记 duplicate-cost risk；late primary 固定 `QUARANTINE_AUDIT_ONLY`，没有覆盖、拼接或追认最终结果的接口。

当前独立 Chat Access 已提供 Application-owned Conversation/Turn/Message、不可变 Revision、完整页面消息历史、“新对话”隔离与失败
Turn 后 Conversation 继续，并已通过真实 browser Access Case。Application-owned bounded executor 也已在确定性 fake ports 上密封跨 Turn
Work State revision、工具 Observation、support/boundary Package、Answer、fresh Review 与 Delivery Authorization；协议错绑、缺证后无新
Observation 重写、无进展和资源熔断只关闭当前 Turn。trusted evidence-tool adapter 已复用现有 World Model projector、Source Broker 与
Retrieval Worker；同一动作可分别密封 support/boundary，每条 Observation 携带 exact Turn/Tool/revision、Application 可重算的完整
append-only Ledger entry chain/prefix 与 Citation content digest，Source READ 只接受本 Turn 先前签发的 opaque locator。状态为
`ACCESS_BROWSER_PASS / AGENT_EXECUTOR_LOCAL_CANDIDATE / EVIDENCE_TOOLS_LOCAL_CANDIDATE / MODEL_BOUNDARY_LOCAL_CANDIDATE /
PROVIDER_ROUTE_COMPOSITION_LOCAL_CANDIDATE / PROVIDER_RUNTIME_COMPOSITION_LOCAL_CANDIDATE /
SESSION_RUNTIME_COMPOSITION_LOCAL_CANDIDATE / ARTIFACT_SESSION_FIXED_COMMAND_LOCAL_CANDIDATE /
NOT_QUALIFIED / NOT_LIVE`。单 Provider Agent/Reviewer 已使用 separate closed no-tools contracts、逐调用 one-use
Disclosure 和 typed Gateway receipt；pre-dispatch、fresh dispatch、outcome unknown 与 replay 的计数由 Application 重验，Turn/Browser 只保存
receipt digest reference。Application-owned Ark→DeepSeek router、committed Work State repository、两 attempt receipt、logical Turn 汇总与
non-starting fixed Browser composition 已通过本地确定性 Gate；预检没有创建 attempt、启动 listener、解析 credential、读取 Source 或 dispatch。
Provider runtime composition 已使用生产 Ark/DeepSeek Adapter 与 credential-lazy transport，但只消费本地构造的 typed qualification identity。
non-starting Session runtime 又把两条 Provider runtime、exact evidence authority、per-attempt fresh Tool/Response Control、共享 committed
Work State、Conversation 与 Browser 组合成一个对象图；preparation 没有创建 attempt、读取 Source、解析 credential、dispatch 或启动 listener。
artifact Session loader 现可从一个 owner-private closed document 绑定 product/source Git identity、published World Model、Source Profile、
Ark→DeepSeek qualification identity、两个 private Gateway repositories 与 Session authority；唯一 `--session-config` selector 让固定
`127.0.0.1:8765` 命令消费该组合，并在 listener 前/停止后分别密封 launch/terminal receipt；terminal 已验证 DeepSeek transport audit。
该生命周期只在 fake listener 与本地构造或 patched typed artifacts 上验证；current actual artifact、Ark transport-level Session audit、Citation 内容与五轮 Browser Chat 尚未闭合，
也没有真实 Provider/model、Source payload 或 listener 执行。旧
`ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3` 继续是兼容协议，不能作为本契约主 Agent 或 Chat 资格证据。
