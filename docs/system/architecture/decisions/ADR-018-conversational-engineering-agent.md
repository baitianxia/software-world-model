---
id: SYS-ADR-018
kind: system-decision
status: accepted
authority: normative
owners: [architecture, product, application, source, quality, security]
depends_on: [SYS-PRODUCT-SUCCESS, SYS-ADR-006, SYS-ADR-010, SYS-ADR-016]
derived_from: [FINDING-010-093]
code: [src/software_world_model/application_services/engineering_conversation.py, src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/interface/engineering_chat_browser.py, src/software_world_model/interface/engineering_chat_alpha_cli.py]
tests: [tests/test_conversational_engineering_agent.py, tests/test_engineering_conversation.py, tests/test_engineering_chat_browser.py, tests/test_engineering_chat_alpha_cli.py]
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
   它不是聊天记录、答案缓存或检索提示集合。
2. **主工程 Agent**是解决用户问题的模型认知控制者。它在同一受控工作循环中理解当前消息和相关对话目标，维护假设、计划、子任务、
   已观察结果和未解决项；按需查询世界模型或提议受控源码读取；根据新观察修改计划；最后综合形成自然答案或诚实限制。Question
   Understanding、Investigation、Answer 和针对性修订是该 Agent 的能力，不再是产品架构强制的独立模型角色流水线。
3. **可信平台与独立 Reviewer**拥有边界而不是思考。Application 保存 Conversation、Turn、Agent Work State、授权、工具结果、Evidence
   Ledger 和 Package 的不可变 Revision；Source Broker/Worker 独占 exact-revision、allowlisted、read-only 来源执行；Response Control
   独占答案授权和发送。至少一个与主 Agent 隔离的新上下文 Reviewer 从当前用户消息、受信对话上下文、当前 Package 和 Draft 独立审核，
   生成者不能自审或自行放行。

主 Agent 的隐藏状态、rationale、先前自然语言答案和 Provider 会话记忆都不是权威状态或证据。可恢复工作状态必须由 Application 以
结构化、可密封 Revision 保存；用户纠正形成新 Revision，不改写历史。世界模型、对话工作状态和当前 Turn 证据是三类不同对象：前者可跨
会话复用，第二类只服务当前对话目标，第三类只支持当前候选答案。先前助手答案只有在当前 Turn 重新获得 admissible evidence 支持时才能
作为结论延续。

主 Agent 可以使用的能力只有受控端口：读取 exact World Model Cognition、查询其结构/行为/覆盖，以及向 Source Broker 提交注册的
`search/read/parse` 等只读 Proposal。模型不取得 Repository mount、路径权威、Source Tool、shell、任意网络、credential、写入或正式知识
发布权。所有 Broker Decision、Worker Result、失败、Coverage 和资源收据继续追加到 Evidence Ledger；每个候选答案形成当前密封
Question Evidence Package，`support/citation` 与 `boundary/audit` 的认识论边界不变。

Reviewer 只检查正确性、完整性、相关性、Citation 支持、用户约束和 Unknown 边界，并返回具体 Finding。现有证据足够时，Finding 进入
同一主 Agent 的新工作 Revision 做针对性改写；证据不足时，主 Agent 在绑定该 gap 的新 Attempt 中继续经 Broker 调查并形成新 Ledger/
Package/Draft；新候选必须重新独立审核。架构不再要求单独的 Verification Investigation Agent，也不把 comprehensive 与 challenge 两个
固定 focus 或固定角色调用数视为长期产品本体；资格策略可以采用多次独立审核，但不得减少至少一次 fresh 独立审核或证据边界。

默认 Web 是语义多轮 Chat，而不是单轮接口的历史列表。后续 Turn 可以引用、追问、纠正、收窄、深入或总结此前讨论；Application 必须
密封相关对话上下文与当前工作状态，Agent 必须基于用户最新 Revision 解释指代。一次 Turn 失败只结束该 Turn，不删除会话历史或关闭服务。

模型和 Provider 对该协议透明。可以使用任何通过同一 Agent 能力、工具、隔离和质量资格的模型 Strategy；current Codex 是强外部产品
基线，不是系统运行时依赖、Oracle 或 Reviewer。系统还必须以同一主 Agent 的完整世界模型认知与 locator-only/empty 控制做因果消融，
分别证明 Agent 本体质量和世界模型认知价值。

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
[Agentless](https://arxiv.org/abs/2407.01489) 则说明复杂自治并非天然更好，因此本系统保留简单基线和因果对照。所有架构结论仍须由本项目
exact 代码、运行、对照与用户体验证据验证。

## Consequences

系统需要新的 Conversation/Turn/Agent Work State 合同、Agent 工具协议、上下文选择与压缩策略，以及面向多轮对话的资格和产品验证。旧
`ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3` 的代码和运行证据继续作为可复用安全/证据资产和历史基线，但不能证明本 ADR 已实现。
当前 Access scaffold 已通过真实浏览器验证。Application-owned 主工程 Agent bounded loop、跨 Turn Work State revision、closed-catalog
工具 Proposal/Observation、双分区 Package、fresh Review Finding 回路和 exact Delivery binding 已形成
`AGENT_EXECUTOR_LOCAL_CANDIDATE`；其证据仅来自确定性 fake ports。真实 World Model/Source Broker/Worker、完整 Ledger/Citation、
Provider driver/Reviewer、Disclosure/fallback、产品 launcher wiring 与五轮 Chat 仍为 `NOT_INTEGRATED / NOT_QUALIFIED / NOT_LIVE`。
