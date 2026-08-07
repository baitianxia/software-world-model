---
id: SYS-CONTRACT-APPLICATION-AGENTIC-TASK
kind: system-contract
status: current
authority: normative
owners: [application]
depends_on: [SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE, SYS-CONTRACT-X-CAPABILITY-EXECUTION, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
derived_from: [DD-APP-AGENTIC-TASK]
code: [src/software_world_model/application_services/natural_task.py, src/software_world_model/application_services/task_control.py, src/software_world_model/interface/agentic_runtime.py]
tests: [tests/test_agentic_runtime.py, tests/test_natural_task.py]
---

# Agentic Task

## Purpose and scope

Agentic Task 把自然语言请求转成有界的 Capability 调用、知识更新/使用和响应准备。Orchestrator 负责提议和路由，不执行业务 Core、不拥有最终答案或授权。

## Ownership

Task Control 是 Task、Revision、Invocation、Delegated Grant、Action Authorization 与 Dispatch 的唯一写者。Agent 只能通过 Application Services 调用能力，不能直接访问 Core、Repository 或 Source Tool。

## Invariants

1. Proposal、Authorization、Invocation Outcome 和业务 Result 分离；模型计划不能自行执行。
2. 每个 logical action 使用一个稳定幂等键；取消、超时或恢复不得重复外部副作用。
3. Grant 只能收窄当前用户、任务、Capability、资源与时间范围，不能转授更大权限。
4. Model Context、Task Revision 和 Knowledge Use Epoch 相互绑定并隔离，旧上下文不能影响新任务状态。
5. Task Control 与 Response Control 不互写私有状态。Task-owned Outcome Assertion 只绑定 exact Task Revision、Invocation、Delegated Grant、Application Outcome 与自身 Digest；Response Control 以 exact Reference 消费该 Assertion，并在自己的 Review Attempt 中绑定 Reviewer output digest 与 model eligibility。
6. 没有新权威或复杂依赖证据时，不引入通用 DAG、插件注册中心或全局 Workflow Store。

## Failure and implementation boundary

授权失效、重复动作输入不一致、结果未知、预算耗尽或 Task Revision 漂移均停止后续分派并如实记录。Agent 类型、Task DTO、循环上限和调度算法由代码与测试定义。
