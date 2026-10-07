---
id: SYS-ADR-018
kind: system-decision
status: accepted
authority: normative
semantic_owner: SYS-ARCH-BASELINE
authority_scope: decision-rationale-only
owners: [architecture, product, application, source, quality, security]
depends_on: [SYS-PRODUCT-SUCCESS, SYS-ADR-006, SYS-ADR-010, SYS-ADR-016]
derived_from: [FINDING-010-093, FINDING-010-109, FINDING-010-132, FINDING-010-133, FINDING-010-136, FINDING-010-169, FINDING-010-170, FINDING-010-172, FINDING-010-176, FINDING-010-177, FINDING-010-191, FINDING-010-192, FINDING-010-193, FINDING-010-194, FINDING-010-195, FINDING-010-196, FINDING-010-197]
code: [src/software_world_model/application_services/engineering_conversation.py, src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/application_services/conversational_engineering_tools.py, src/software_world_model/application_services/engineering_question_cognition.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py, src/software_world_model/interface/engineering_chat_candidate.py, src/software_world_model/interface/engineering_chat_session_artifact.py, src/software_world_model/interface/engineering_chat_browser.py, src/software_world_model/interface/engineering_chat_alpha_cli.py]
tests: [tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_tools.py, tests/test_engineering_question_cognition.py, tests/test_conversational_engineering_model.py, tests/test_engineering_chat_candidate.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_conversation.py, tests/test_engineering_chat_browser.py, tests/test_engineering_chat_alpha_cli.py]
---

# ADR-018：世界模型增强的对话式主工程 Agent

## Context

软件世界模型始终是软件在精确版本和上下文上的持久、版本化、可验证、可更新外部认知。现有
`ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3` 又把一次回答拆成 Question Understanding、Initial Investigation、Answer、
comprehensive Review、evidence-boundary challenge 和 Verification Investigation 等固定模型角色。该设计建立了重要的来源隔离、证据、
引用和审核底座，但也把同一个工程师应连续完成的目标理解、假设形成、计划、观察、重规划和综合回答分散到多个窄上下文中。

真实体验已表明，仅继续增加检查清单、角色 Schema 和阶段间证明不能自然形成优秀的软件工程 Agent，也不能把“同一页面连续提交互不相干
的问题”变成语义上的多轮 Chat。需要调整的是默认产品的 Agent 本体，而不是世界模型定义，也不是放宽来源、安全或证据边界。

## Decision

默认工程体验采用 `CONVERSATIONAL_ENGINEERING_AGENT@1` 和
`SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 定义的对话式主工程 Agent。系统由三个相互制约的部分组成：

1. **软件世界模型**提供跨问题、跨会话复用的版本化软件认知，包括实体、关系、行为、约束、状态、来源、Coverage、Conflict 与 Unknown。
   它不是聊天记录、答案缓存或检索提示集合。工程 Conversation 通过 Application-owned Cognition Binding 引用同一 repository
   Binding/exact revision 上一个或多个 profile-specific exact Read Authority，并以 Capability Manifest 声明各 Profile 的 Schema、
   Coverage、可查询能力、已覆盖认知维度和显式未知。组合只发生在只读投影层，不合并 Snapshot/Read Set，也不绕过跨 Schema Adoption
   边界。
2. **主工程 Agent**是解决用户问题的模型认知控制者。它在同一受控工作循环中理解当前消息和相关对话目标，维护假设、计划、子任务、
   已观察结果和未解决项；按需查询世界模型或提议受控源码读取；根据新观察修改计划；最后综合形成自然答案或诚实限制。Question
   Understanding、Investigation、Answer 和针对性修订是该 Agent 的能力，不再是产品架构强制的独立模型角色流水线。
3. **可信平台与独立 Reviewer**拥有边界而不是思考。Application 保存 Conversation、Turn、Agent Work State、授权、工具结果、Evidence
   Ledger 和 Package 的不可变 Revision；Source Broker/Worker 独占 exact-revision、allowlisted、read-only 来源执行；Response Control
   独占答案授权和发送。至少一个与主 Agent 隔离的新上下文 Reviewer 从当前用户消息、受信对话上下文、当前 Package 和 Draft 独立审核，
   只返回 verdict 与具体 Finding，不重新作答、不生成替代 Draft；生成者不能自审或自行放行。

主 Agent 的隐藏状态、rationale、先前自然语言答案和 Provider 会话记忆都不是权威状态或证据。可恢复工作状态必须由 Application 以
结构化、可密封 Revision 保存；用户纠正形成新 Revision，不改写历史。世界模型、对话工作状态和当前 Turn 证据是三类不同对象：前者可跨
会话复用，第二类只服务当前对话目标，第三类只支持当前候选答案。先前助手答案只有在当前 Turn 重新获得 admissible evidence 支持时才能
作为结论延续。

当前 Turn 的 Source navigation candidate 只能来自本 Turn 的 Search/Cognition observation。历史 Delivery Citation、旧 Evidence、旧 locator 和
旧答案都不得生成本 Turn candidate；后续 Turn 必须重新查询当前有效 World Model 或由 Source Broker/Worker 重新签发并读取 exact-revision
locator，只有本 Turn 新产生的 Observation、Package 与 Citation 才能支持结论。历史对话仍可帮助解释指代和目标，但不携带事实权威。

主 Agent 可以使用的能力只有受控端口：读取 exact World Model Cognition、查询其结构/行为/覆盖，以及向 Source Broker 提交注册的
`search/read/parse` 等只读 Proposal。模型不取得 Repository mount、路径权威、Source Tool、shell、任意网络、credential、写入或正式知识
发布权。所有 Broker Decision、Worker Result、失败、Coverage 和资源收据只在当前 Turn 追加到 Evidence Ledger；每个候选答案形成当前密封
Question Evidence Package，`support/citation` 与 `boundary/audit` 的认识论边界不变。Turn 结束后释放完整 Ledger/Package/Draft/Review 正文，
只保留不含证据正文的最小运行摘要或 Knowledge Maintenance Task 引用。

Reviewer 只检查正确性、完整性、相关性、Citation 支持、用户约束和 Unknown 边界，并返回具体 Finding。它不重新解决原问题、不生成第二份
答案或替代 Draft，也不把自身推断当作证据。现有证据足够时，Finding 进入同一主 Agent 的新工作 Revision 做针对性改写；证据不足时，
主 Agent 在绑定该 gap 的新 Attempt 中继续经 Broker 调查并形成新 Ledger/Package/Draft；新候选必须重新独立审核。架构不再要求单独的
Verification Investigation Agent，也不把 comprehensive 与 challenge 两个固定 focus 或固定角色调用数视为长期产品本体；资格策略可以采用多次
独立审核，但不得减少至少一次 fresh 独立审核或证据边界。

默认 Web 是语义多轮 Chat，而不是单轮接口的历史列表。后续 Turn 可以引用、追问、纠正、收窄、深入或总结此前讨论；Application 必须
密封相关对话上下文与当前工作状态，Agent 必须基于用户最新 Revision 解释指代。一次 Turn 失败只结束该 Turn，不删除会话历史或关闭服务。

新 Conversation 在尚无任何可解析先行对象时，不应为判断一个指代词而调用 Source 或 Provider。Conversation Binding 必须固定显式版本化的
语言 input policy；该可信 policy 只可返回无工程事实的澄清请求，不能回答问题、创建证据、选择 Provider 或替代独立 Reviewer。普通显式首问
和非空 Conversation 仍进入同一主 Agent 路径。

模型和 Provider 对该协议透明。可以使用任何通过同一 Agent 能力、工具、隔离和资格边界的模型 Strategy；外部编码 Agent 不属于
系统运行时依赖、Oracle 或 Reviewer。具体产品质量验证由产品与质量文档定义，不改变本 ADR 的主 Agent、证据、审核和交付边界。
窄 Profile 只能在其 Coverage 内声明能力，不得在未覆盖的问题上被命名为完整认知。

资格按问题而不是按数据量命名：Application 从原 Turn 的 material Need 独立形成 Cognition Eligibility Assessment，并把每个 Need 绑定到
已资格化认知维度/操作或显式 Gap。开放式工程 Chat 的可体验认知至少组合结构与实现/行为维度；缺失时主 Agent仍可按授权使用 Source
完成当前调查，但必须保留 World Model Gap，不能把 Source 命中追认为世界模型贡献。

## Preserved boundaries from ADR-016

本 ADR **amends** 而不整体取代 ADR-016。以下边界继续成立：exact repository/revision、World Model Cognition、Source Profile、Broker/
Worker-only 只读来源执行、append-only Ledger、双分区 Package、逐结论 Citation、来源内容不可信、Provider 披露授权、资源熔断、失败关闭、
独立 Reviewer、Response Control 唯一放行和异步 Knowledge Update。被替代的只有固定多角色 Agent 本体和把连续单轮请求等同 Chat 的解释。

## Alternatives

- **继续为固定流水线增加角色和 Schema。** 能强化局部格式，却不能给同一个问题解决者连续的目标、假设、观察和重规划能力。
- **直接嵌入一个拥有完整 shell/仓库权限的通用编码 Agent。** 能力强，但会绕过 exact revision、只读、Disclosure、证据和独立审核边界。
- **只给现有页面增加历史消息。** 只能形成聊天外观，不能处理指代、纠正、目标延续或基于新证据修订。

## External design evidence

以下外部材料只支持设计原则，不是本系统权威、实现证明或验收证据，也不授权照搬其权限模型：Anthropic 的
[Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) 区分固定 workflow 与由模型动态控制过程的 Agent，
并建议先采用简单可组合模式；[ReAct](https://arxiv.org/abs/2210.03629) 说明 reasoning、action 与 observation 交错的价值；
[SWE-agent](https://proceedings.neurips.cc/paper_files/paper/2024/hash/5a7c947568c1b1328ccc5230172e1e7c-Abstract-Conference.html)
强调 Agent—computer interface 会实质影响软件工程表现；[RepoGraph](https://proceedings.iclr.cc/paper_files/paper/2025/hash/4a4a3c197deac042461c677219efd36c-Abstract-Conference.html)
与 [LocAgent](https://aclanthology.org/2025.acl-long.426/) 展示 repository cognition/navigation 对多跳定位的作用；
[Agentless](https://arxiv.org/abs/2407.01489) 则说明复杂自治并非天然更好，因此本系统保留可组合、可审计的 Agent 边界。上述材料只支持设计取舍，
不构成系统运行时依赖、外部验收协议或质量结论。

## Consequences

系统需要 Conversation/Turn/Agent Work State 合同、Agent 工具协议、上下文选择与压缩策略，以及面向多轮对话的独立质量验证。
实现、产品体验和验证状态不属于本 ADR 的架构结论；它们必须在项目实现参考和验证文档中记录，不能证明或否定本 ADR 的语义。
## 实现与运行记录

原文中的具体配置、局部实现状态和运行记录已原样归位至项目路径 `docs/project/implementation-reference/agent-implementation-history.md`。
这些记录不能覆盖架构基线、证明当前代码已满足本契约，或恢复被用户暂停的开发。
