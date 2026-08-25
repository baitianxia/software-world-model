---
id: SYS-CONTRACT-APPLICATION-AGENTIC-TASK
kind: system-contract
status: current
authority: normative
owners: [application]
depends_on: [SYS-ADR-015, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE, SYS-CONTRACT-X-CAPABILITY-EXECUTION, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
derived_from: [DD-APP-AGENTIC-TASK]
code: [src/software_world_model/application_services/natural_task.py, src/software_world_model/application_services/task_control.py, src/software_world_model/application_services/engineering_conversation.py, src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/application_services/conversational_engineering_tools.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py, src/software_world_model/interface/agentic_runtime.py]
tests: [tests/test_agentic_runtime.py, tests/test_natural_task.py, tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_tools.py, tests/test_conversational_engineering_model.py, tests/test_engineering_conversation.py]
---

# Agentic Task

## Purpose and scope

Agentic Task 把自然语言目标转成有界的 Capability 调用、Engineering Conversation、Evidence Answering、知识更新/使用和响应准备。普通
工程 Chat 由主工程 Agent 在 Application-owned Conversation/Work State 中理解目标、形成假设和计划、使用受控工具、观察后重规划并综合
回答；严格 `WORLD_MODEL` 与 `DIRECT_INVESTIGATION` 保留独立显式入口。需要多能力编排时由 Agent 提议、Task Control 授权和分派。
Agent 不执行业务 Core、不拥有正式知识、最终审核或响应授权。

## Ownership

Task Control 是 Conversation/Task、Turn/Revision、Agent Work State、Invocation、Delegated Grant、Action Authorization 与 Dispatch 的唯一
写者。Agent 只能通过 Application Services 调用能力，不能直接访问 Core、Repository 或 Source Tool；Provider hidden state 不是恢复机制。

## Invariants

1. Proposal、Authorization、Invocation Outcome 和业务 Result 分离；模型计划不能自行执行。
2. 每个 logical action 使用一个稳定幂等键；取消、超时或恢复不得重复外部副作用。
3. Grant 只能收窄当前用户、任务、Capability、资源与时间范围，不能转授更大权限。
4. Model Context、Task Revision 和 Knowledge Use Epoch 相互绑定并隔离，旧上下文不能影响新任务状态。
5. Task Control 与 Response Control 不互写私有状态。Task-owned Outcome Assertion 只绑定 exact Task Revision、Invocation、Delegated Grant、Application Outcome 与自身 Digest；Response Control 以 exact Reference 消费该 Assertion，并在自己的 Review Attempt 中绑定 Reviewer output digest 与 model eligibility。
6. 没有新权威或复杂依赖证据时，不引入通用 DAG、插件注册中心或全局 Workflow Store。
7. Evidence Answering 的 Checklist、Packet、Draft 与 Review 使用稳定 Digest 和执行引用；同包重写不是新的来源动作，补证则形成新的 Packet Revision。Task Control 不得把模型提议当成审核或最终授权。
8. `WORLD_MODEL` bounded investigation 是 Task 内的只读子协议，不是通用自治工作流。Agent 首轮只能用注册 operation/relation
   vocabulary 声明 bounded evidence obligations 和通用 search terms；Application 将其冻结为 Task-owned ledger。以后每轮
   Task Control/Application 按该 ledger、exact trace prefix、立即前序 Result、Snapshot、Ref provenance、progress 和剩余预算计算
   受限 transition allowlist；模型 proposal 不能扩大 allowlist、删除 obligation 或提前 `FINISH`。结果必须先密封才能进入下一轮，
   Agent 不能执行查询、批量展开 Bundle、改变 Need 或把历史模型记忆当输入。强制 candidate discovery 不是可终止 canonical
   obligation；raw candidate evidence alias 由 Application 向上归一为 method evidence，避免非零候选仅凭存在性结束。method Result
   已正式承载的 standalone outgoing `CALLS` obligation 同样收敛到 method；path/incoming/both 不折叠。
9. Investigation、Draft 与 Review 是隔离角色。调查角色不能看到 Source/Repository/raw Evidence/Update/Direct/Citation
   observation；Draft 只消费 sealed trace；Reviewer 从原问题和同一 trace 独立重建检查项。任何角色失败、结果未知或预算耗尽都
   终止本题，不 retry 或降级。
10. Engineering Conversation 是独立的有界组合用例：Task 在 Conversation/Turn 执行前固定 protocol identity、exact revision、World Model
    Read Authority、Source allowlist/tool catalog、Provider disclosure 和资源熔断。Application 密封 current User Turn、相关 Conversation
    Revision 和 Work State；用户纠正形成新 Revision，先前答案和用户陈述不成为 Source truth。
11. 主工程 Agent 的 Work State 至少表达目标、指代、用户约束、可证伪假设、计划/子任务、Observation、缺口和完成判断。它依据 World
    Model/Source Observation 修改计划；Question Understanding、Investigation、Answer 和针对性修订是同一 Agent 的能力，不是固定模型角色。
    Broker 逐步重新校验并编译，只有 Retrieval Worker 可执行 allowlisted exact-revision 只读操作，全部 Proposal/Decision/Result 追加到
    Ledger。模型不得访问 Repository、Source Tool、Ledger write port、shell、网络、credential 或未密封输入。
12. 独立 Reviewer 与主 Agent 使用隔离上下文，只读 current Turn、受信 Conversation Context、当前双分区 Package 和 Draft，并返回具体
    Finding。可信 Application 把 Finding 路由为主 Agent 同包修订或绑定 evidence gap 的新 Agent Attempt；新证据形成新 Package 后重新
    Review。预密封 revision/call/operation/bytes/wall-time/no-progress 高安全熔断只能失败关闭，不得删减 Evidence、Citation 或至少一次
    fresh 独立审核。固定角色数、固定双 Review focus 和独立 Verification Investigation 不是新合同的长期不变量。

## Failure and implementation boundary

授权失效、Conversation/Turn/Work State 错绑、重复动作输入不一致、结果未知、预算耗尽或 Revision 漂移均停止当前 Turn 的后续分派并
如实记录，不关闭整个 Conversation。Agent 调度和上下文压缩算法由代码与测试定义；工具目录、operation allowlist、trace/progress 语义
和失败状态由 owning Contract 固定，不能只在 prompt 中声明。新 Chat Access 已通过真实 browser Case；对话式主 Agent 的 Application-owned
bounded executor、跨 Turn Work State、typed tool/Review/Delivery ports 与 fail-closed 本地状态机已有确定性证据，状态为
`AGENT_EXECUTOR_LOCAL_CANDIDATE`。World Model/Source/Ledger tool adapter 与单 Provider Agent/Reviewer 的 closed role contract、one-use
Disclosure/Gateway receipt 已分别形成 `EVIDENCE_TOOLS_LOCAL_CANDIDATE / MODEL_BOUNDARY_LOCAL_CANDIDATE`。ADR-017 fallback、真实 Provider/
fixed launcher/Citation wiring 仍为 `NOT_INTEGRATED / NOT_QUALIFIED / NOT_LIVE`，不能由本地 fake/offline port 或 Access 状态推导 Agent 已
完成真实执行。
