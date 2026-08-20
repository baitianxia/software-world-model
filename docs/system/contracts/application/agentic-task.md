---
id: SYS-CONTRACT-APPLICATION-AGENTIC-TASK
kind: system-contract
status: current
authority: normative
owners: [application]
depends_on: [SYS-ADR-015, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE, SYS-CONTRACT-X-CAPABILITY-EXECUTION, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
derived_from: [DD-APP-AGENTIC-TASK]
code: [src/software_world_model/application_services/natural_task.py, src/software_world_model/application_services/task_control.py, src/software_world_model/interface/agentic_runtime.py]
tests: [tests/test_agentic_runtime.py, tests/test_natural_task.py]
---

# Agentic Task

## Purpose and scope

Agentic Task 把自然语言请求转成有界的 Capability 调用、Evidence Answering、知识更新/使用和响应准备。同步聊天可以直接进入受控 Evidence Answering 用例；需要多能力编排时由 Orchestrator 提议和路由。Orchestrator 不执行业务 Core、不拥有最终答案或授权。

## Ownership

Task Control 是 Task、Revision、Invocation、Delegated Grant、Action Authorization 与 Dispatch 的唯一写者。Agent 只能通过 Application Services 调用能力，不能直接访问 Core、Repository 或 Source Tool。

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
   Agent 不能执行查询、批量展开 Bundle、改变 Need 或把历史模型记忆当输入。
9. Investigation、Draft 与 Review 是隔离角色。调查角色不能看到 Source/Repository/raw Evidence/Update/Direct/Citation
   observation；Draft 只消费 sealed trace；Reviewer 从原问题和同一 trace 独立重建检查项。任何角色失败、结果未知或预算耗尽都
   终止本题，不 retry 或降级。

## Failure and implementation boundary

授权失效、重复动作输入不一致、结果未知、预算耗尽或 Task Revision 漂移均停止后续分派并如实记录。通用 Agent 类型和调度算法由
代码与测试定义；`JAVA_SOURCE_SEMANTICS@1` 的调查上限、operation allowlist、trace/progress 语义和失败状态由 World Model
Answering 与 Implementation Query Contract 固定，不能只在 prompt 中声明。
