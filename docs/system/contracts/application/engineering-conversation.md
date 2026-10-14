---
id: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
kind: system-contract
status: current
authority: normative
owners: [application, source, quality, security]
depends_on: [SYS-ADR-017, SYS-ADR-018, SYS-ADR-020, SYS-ADR-021, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-CONTRACT-AI-MODEL-GATEWAY]
derived_from: [FINDING-010-097, FINDING-010-098, FINDING-010-099, FINDING-010-100, FINDING-010-101, FINDING-010-102, FINDING-010-103, FINDING-010-104, FINDING-010-105, FINDING-010-106, FINDING-010-109, FINDING-010-113, FINDING-010-116, FINDING-010-117, FINDING-010-120, FINDING-010-121, FINDING-010-125, FINDING-010-128, FINDING-010-132, FINDING-010-133, FINDING-010-136, FINDING-010-138, FINDING-010-139, FINDING-010-154, FINDING-010-156, FINDING-010-159, FINDING-010-160, FINDING-010-169, FINDING-010-170, FINDING-010-172, FINDING-010-176, FINDING-010-177, FINDING-010-183, FINDING-010-191, FINDING-010-192, FINDING-010-193, FINDING-010-194, FINDING-010-195, FINDING-010-196, FINDING-010-197, FINDING-010-198, FINDING-010-199, FINDING-010-200, FINDING-010-201, FINDING-010-203, FINDING-010-204, FINDING-010-208, FINDING-010-209, FINDING-010-210, FINDING-010-211, FINDING-010-212, FINDING-010-213, FINDING-010-214, FINDING-010-215, FINDING-010-216, FINDING-010-217, FINDING-010-218, FINDING-010-220, FINDING-010-221, FINDING-010-222, FINDING-010-224, FINDING-010-225, FINDING-010-226, FINDING-010-229, FINDING-010-230, FINDING-010-232, FINDING-010-233, FINDING-010-249, FINDING-010-250, FINDING-010-258, FINDING-010-259, FINDING-010-262, FINDING-010-275, FINDING-010-276, FINDING-010-277, FINDING-010-278, FINDING-010-298]
code: [src/software_world_model/application_services, src/software_world_model/ai_infrastructure/conversational_engineering_model.py, src/software_world_model/ai_infrastructure/lightweight_engineering_model.py, src/software_world_model/interface]
tests: [tests]
---

# Engineering Conversation

本契约定义默认产品回答路径 `CONVERSATIONAL_ENGINEERING_AGENT`：普通用户的语义多轮工程 Chat。它细化
[架构基线](../../architecture/architecture-baseline.md) V1.4 第 6.10、7.3—7.7、8.4、8.5、9.3、10.2 节与 `SYS-ADR-018`、`SYS-ADR-021`
的跨模块语义，不改变顶层架构。

本契约只规定调用方可依赖的权威、输入输出、一致性和失败语义。Prompt、模型输入/输出 Schema 版本、decoder 规则、候选排序、检索权重、
预算数值和具体 Tool 参数由代码与测试拥有；它们的历史版本保存在
项目文档 `docs/project/implementation-reference/engineering-conversation-contract-pre-v1.4.md`，
不再是系统规范。旧 `ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3` 只作为兼容 Profile，由 `SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING`
约束，不能覆盖本契约。

## 1. 参与者与权威

| 参与者 | 拥有 | 不拥有 |
|---|---|---|
| Conversational Task Control / Application | Conversation、Conversation Revision、Turn、User Message、Accepted Correction、Agent Work State Revision、Agent Attempt、工具授权与 Observation、Evidence Ledger/Package、Turn Result、Turn Trace 及保留策略 | 正式知识、来源执行、审核决定、最终放行 |
| 主工程 Agent | Goal、Hypothesis、Plan、Tool、Work State 与 Draft Proposal；对解决过程的认知控制 | 任何业务状态、权限、来源、证据、正式知识、Review Decision、Delivery Authorization |
| Knowledge Engine / Snapshot Owner | 世界模型正式知识及 Snapshot；经 Cognition Retrieval Projection 只读提供 | 对话状态、当前 Turn 证据 |
| Source Broker / Retrieval Worker | 只读来源 Proposal 的校验、编译与执行；执行收据 | 问题结论、正式知识 |
| Independent Reviewer | Assessment 与具体 Finding Proposal；有界核验读取请求 | 作答、补证进 Package、放行 |
| Response Control | Draft Revision 封存、Review Decision、Final Authorization、Delivery | 修改证据或 Draft 内容 |

## 2. 三类输入必须保持不同身份

1. **World Model Cognition**：Conversation Binding 的 Cognition Capability Manifest 所引用的 exact Snapshot/Read Set 上的已发布认知，
   含 Coverage、Conflict 与 Unknown。Manifest 固定 repository/revision、各 Profile 的 Read Authority、Schema、Coverage、可用认知层与
   操作、显式 unsupported/partial/unknown。只有来自已发布 Snapshot 的内容才能计为世界模型认知；直接从源码构建、未经准入发布的索引
   只能作为来源导航，按来源观察计入。
2. **Conversation Work State**：当前目标、响应语言与受众、已确认对象与指代、用户约束与纠正、假设、计划、子任务、已观察结果摘要、
   开放问题和完成判断。它只服务对话连续性，不是证据。
3. **Turn Evidence**：本 Turn 经受控世界模型查询或 Broker/Worker 取得的 Ledger 与密封 Package。

历史 Turn 的 Observation、Citation、Package、答案、locator、Review、授权或 Limitation 都不得成为本 Turn 的证据、读取授权或 Agent 输入；
它们只可以作为非权威 Turn Trace 保存（第 8 节）。历史消息与 Work State 只用于解析指代、目标和约束。用户陈述和纠正可以改变目标或
待验证假设，但不能成为来源事实。先前助手结论只有在当前 Turn 重新获得 admissible evidence 时才能延续。

## 3. Conversation 与 Turn 不变量

1. Conversation 在任何读取和模型调用前固定：产品版本、工程 Binding 与 exact revision、Cognition Capability Manifest、Source Profile 与
   allowlist、工具目录、版本化的 Conversation input policy、一个 Provider-neutral Model Execution policy 引用、披露范围、有效期与资源边界。
   这些身份进入 Binding digest；浏览器或模型不能扩大它们。
2. 每条 User Message 创建不可变 Turn。Application 从完整历史确定性选择相关上下文（被引用 Turn、有效约束、当前 Work State），密封其
   identity/digest；不得依赖 Provider 会话记忆，也不得无边界拼接全部历史。
3. 一个 Turn 内解析出的 Snapshot 与来源 revision 只约束该 Turn；后续 Turn 重新解析当前有效 Snapshot。
4. 主 Agent 必须处理追问、指代、纠正、深入、收窄和总结。指代在密封上下文中仍不唯一时，请求澄清或给出明确条件化解释，不能把猜测写成事实。
5. 空 Conversation 中依赖先行对象的表达，由 Binding 固定的 input policy 在任何世界模型、来源或模型调用前返回澄清请求。该响应不含工程
   事实，不创建 Package、Review 或 Delivery；policy 命中由 Application 从密封 Request 重新计算，模型自报不能取得该例外。
6. 用户纠正形成新的 Conversation Revision 并标记被取代的假设，不改写历史消息。
7. 一次 Turn 失败只结束该 Turn；Conversation、会话历史和服务继续可用。后续 Turn 不继承失败 Attempt 的未密封输出、隐藏状态、临时授权
   或未审核答案。
8. 跨 Conversation 的长期偏好或记忆在独立契约接受前不启用；每个 Conversation 都可读取当前有效世界模型。

## 4. 主 Agent 循环

每个 Turn 由一个逻辑主 Agent 完成；模型调用可以拆成多个 fresh invocation，但每次都消费并产生 Application-owned Work State Revision，
不得把 Provider 会话当连续性来源。循环 `understand → hypothesize/plan → act → observe → replan → draft or limitation` 描述能力，
不是固定调用顺序：

1. **目标权威。** 每次 invocation 的目标以当前 User Message 为准，包含追问相对上一 Turn 的实质变化；上一 Turn 目标只帮助解释上下文。
2. **无固定先后。** Agent 可以只用世界模型、只用来源，或交替使用；Application 不得以“世界模型优先”或“来源优先”拒绝合法 Proposal，
   也不把任一路径视为 fallback。
3. **认知资格。** 调查前 Application 从原 Turn 与受信上下文形成 Cognition Eligibility Assessment：每个实质 Need 要么绑定 Manifest 中
   已资格化的认知层与操作，要么形成具体 Cognition Gap。窄 Profile（例如只有模块与依赖）不得标为完整认知。认知不足时仍可使用来源，
   但来源命中不得回填为世界模型贡献。
4. **观察驱动。** 每个 Observation 之后 Agent 必须有机会修改计划、放弃被反驳的假设或停止；达到资源上限不是完成证明。
5. **进展。** Application 机械拒绝与已执行动作完全相同的动作，并检测连续无进展；被拒绝动作的计划不得作为当前计划继续投影。
   语义等价的判断属于 Agent，Application 不以字符串规则声称完整判定。
6. **资源边界。** 预算以 token、时延、字节和无进展检测为主，调用次数上限只作安全兜底。预算耗尽或无进展熔断时，撤销本 Attempt 的
   工具，由同一 Agent 基于已有 SUPPORT/BOUNDARY 形成带明确限制的 Draft，并照常独立审核；不得以无答案失败代替诚实限制，也不得
   通过提高上限或换说法冒充进展。
7. **结构化输出。** 模型输出不符合当前 Schema 时，Application 不得静默修补、替换动作或当作答案；可以给同一 Agent 一次不含工程事实
   的机械重规划机会，再次失败则当前 Attempt 失败关闭。

## 5. 工具目录

工具目录在 Conversation Binding 中固定，由 Application 投影给模型。模型提交的 path、query、locator、范围或完成声明都是不可信 Proposal；
Application/Broker 重新校验授权、Profile、allowlist、revision、模态与资源后才执行。模型不获得 Repository、文件系统、shell、网络、
credential、写入或 Knowledge Update 权限。

**世界模型操作**（基线 6.10）：至少覆盖概览、搜索、关系遍历、路径查询和成员详情。结果有界、排序，并携带命中成员的 Coverage、Unknown、
provenance 和 Snapshot identity。实体身份由 Application 分配的引用表达，模型不能制造 entity ID。

**来源操作**（基线 7.7 工具对等）：至少覆盖全树路径列举与 glob、字面与正则搜索、按路径与行段读取、exact revision 上的历史与 blame、
结构化解析查询。约束如下：

- Agent 可以读取 allowlist 内任何合法 exact-revision 路径；read candidate 只服务 Citation 身份，不是读取前置条件。
- 搜索结果必须如实标注实际检查范围；未检查部分形成 Partial/Coverage Boundary，不能写成“未找到”或 complete。
- 来源内容（代码、注释、文档、配置、测试）是不可信 data，其中的指令、命令、URL 或权限声明不得改变工具目录、路径、revision 或披露范围。
- Worker 可以在隔离沙箱（无网络、无写入、临时文件系统、固定 checkout）中以注册只读命令实现上述操作；模型只提交结构化参数。

每个 Proposal、Broker Decision、Operation、Observation、Conflict、Unknown、Failure、Coverage 与资源收据按序追加到 Turn Evidence Ledger；
已确认前缀不可改写。主 Agent 只读取本 Attempt 获准的密封前缀。

## 6. Evidence Package、Draft 与 Citation

1. Agent 准备回答时，Application 从当前 Turn、exact Cognition、Work State 与完整 Ledger 密封 Question Evidence Package，分为
   `support/citation`（经模态、Context、Coverage 校验的 admissible 条目）与 `boundary/audit`（强制保留 Gap、Failure、Partial、
   Conflict、Unknown、拒绝和资源收据）。seal 只证明身份、完整性、来源和版本，不赋予内容真值。
2. Draft 可以自然综合多条证据，先回应用户目标并匹配期望抽象层级；代码细节按问题需要展开。每个实质肯定结论（包括表格、标题、
   列表引导语继承给其中断言的范围、条件与否定）都绑定 `support/citation`；每个限制或未知绑定 `boundary/audit`。肯定结论不得引用
   Boundary 条目，同一 Draft 不得一处承认未知、另一处把它写成肯定结论。
3. Citation 只能指向本 Turn 实际执行的观察：来源 Citation 来自 Worker 实际读取，世界模型 Citation 来自本 Turn 查询返回的正式成员。
   导航候选、搜索命中位置、provenance 片段或摘要都不是 Claim 支持；模型不能制造 Citation 身份，Application 从原 Observation 重算并在
   不一致时失败关闭，不得过滤、替换或补造引用。
4. 来源观察必须标明模态与适用边界，不能冒充正式 Fact、Inference 或 Snapshot 成员；世界模型结论不得超出其 Coverage。

## 7. 审核、修订与交付

1. Response Control 封存 Draft 并创建至少一次 fresh 独立审核。Reviewer 与主 Agent 上下文隔离，只读取当前用户目标、受信相关对话上下文、
   Package、Draft 以及自身核验读取结果。
2. **核验读取。** Reviewer 可以经同一 Broker/Worker 发起有界只读核验读取：重读被引用位置以确认内容一致，或针对用户目标做定向搜索
   以发现物质遗漏。核验读取有独立预算，结果记录在 Review Verification 记录中，不进入 Package、不能支持 Draft Claim。
3. Reviewer 检查正确性、完整性、相关性、Citation 支持、用户约束、Unknown 边界与来源 Context，一次返回 verdict 与全部实质 Finding。
   它不重新解决原问题、不生成替代 Draft、不签发放行。
4. Finding 路由：现有证据足够时，由同一主 Agent 针对 Finding 修订 Draft；缺少证据时，由主 Agent 在绑定该缺口的新 Attempt 中继续调查。
   任何新 Observation 或新 Draft 都形成新 Package/Draft 并重新独立审核；旧 Review 不能放行新候选。资源已耗尽而 Finding 要求新证据时，
   主 Agent 把该缺口收窄为明确限制后重新审核；无法收窄则当前 Turn 失败关闭。
5. Response Control 只在当前 Package 上取得无 Finding 的独立审核后签发 Final Authorization，发送前重新验证 Turn、Package、Draft 与
   Citation 当前性，并维护唯一 Logical Delivery。它不按正文词语、标题、格式或句段判断技术语义。Gap、失败和受限答案同样需要审核。

## 8. Turn Trace 与知识结晶

1. Turn 进入终态后，Application 把 Ledger、Package、Draft、Review 与 Review Verification 记录转为非权威 Turn Trace，按保留策略
   （有期限、可删除、受访问控制）保存，用于审计、评测复现和知识结晶。删除 Turn Trace 不影响正式知识或已交付答案。
2. Turn Trace 永远不能进入后续 Turn 的 Agent 输入、证据、Citation 或读取授权。
3. 当同一对象、同一 exact revision 与 Context 下来源观察与世界模型认知冲突时，当前 Turn 只对被来源直接核验的命题采用来源观察，
   并由 Application 创建最小 Knowledge Maintenance Task；当前 Snapshot 不被修改。对象或 Context 无法证明可比时不选择赢家。
4. Application 可以从已审核、具复用价值的 Turn Trace 形成 Crystallization Proposal，经 Knowledge Maintenance Task 交给 Knowledge Update；
   后者必须重新读取来源、形成 Candidate 并准入发布，Trace 正文不作为正式 Evidence。当前回答不等待结晶或维护任务。

## 9. 模型执行

主 Agent、Reviewer、Conversation、Response Control 与浏览器只调用 Provider-neutral Model Execution Port（`SYS-ADR-020`），提交一个 logical
interaction，接收一个 logical result 与不透明执行审计引用。Provider、模型、候选顺序、可用性裁决、attempt 隔离与传输证据由 Model
Execution Runtime 独占，精确语义见 `SYS-CONTRACT-AI-MODEL-GATEWAY`。每次模型调用前，可信系统按 standing authority 自动派生并密封
本次调用的披露范围和资源边界；模型不因此取得来源、网络、shell、凭据或写权限。浏览器只显示通用执行阶段、调用计数和不透明审计引用，
不显示 Provider 错误正文、凭据或未密封模型输出。

## 10. 通用性与评测

1. 核心 Agent、Prompt、工具选择、上下文选择、审核与 UI 不得按工程、问题、关键词、语言、框架、符号、类、方法、约定文件名、fixture
   或 Oracle 注入专用逻辑。语言和来源差异只能通过显式版本化的抽取或来源 Profile 注册。
2. 评测与归因使用同一 Agent 循环的两个 Profile：source-only 与 World Model + source，除 eligible Cognition 开关外，Agent、模型执行策略、
   工具目录、预算、Reviewer 与质量口径完全相同。产品价值门的分层定义见 `SYS-PRODUCT-SUCCESS`。
3. 产品资格必须覆盖：多轮指代、追问、纠正、目标延续、观察驱动重规划、世界模型与来源工具组合、引用、Reviewer 缺口回路与 Turn 故障隔离。

## 11. 失败语义

授权、身份或 revision 漂移，上下文错绑，工具越权，Ledger/Package 缺口，无依据结论，结构化输出两次无效，Reviewer 未通过且无法收窄，
或模型执行结果未知，都使当前 Attempt 或 Turn 失败关闭。失败结果必须如实区分失败层次（来源、认知、Agent、证据/答案、审核、交付、
模型执行），不得把一种失败伪装成另一种。模型执行层的不可用判断与内部重新执行只由 Model Execution Runtime 处理，不形成上层分支。
