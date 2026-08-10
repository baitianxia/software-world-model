---
id: SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL
kind: system-contract
status: current
authority: normative
owners: [application]
depends_on: [SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-STRUCTURE-VIEW, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-CONTRACT-X-CAPABILITY-EXECUTION, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
derived_from: [DD-APP-RESPONSE-CONTROL]
code: [src/software_world_model/application_services/response_control.py, src/software_world_model/application_services/evidence_answer.py, src/software_world_model/infrastructure/sqlite_response_control_repository.py]
tests: [tests/test_response_control.py, tests/test_evidence_answer.py, tests/test_agentic_runtime.py]
---

# Response Control

## Purpose and scope

Response Control 审核、授权并唯一交付用户可见响应。它同时处理成功、部分、Gap 和业务失败，不能让流畅文本掩盖知识不足或未知状态。

## Ownership

Response Control 是 Answer Candidate、固定输入上的 Draft Revision、Claim Binding、Review、Authorization、Dispatch 与 Delivery 的唯一写者。Reviewer 只能提交 Proposal；Task Control、Direct Evidence Answering、World Model Query 与 Delivery Adapter 不能自行放行候选正文。

## Invariants

1. Direct Evidence Answer 的每个实质 Section 绑定密封 Packet 中的实际 Evidence 或明确 UNKNOWN；World Model Answer 的 Claim 绑定同一 exact Read Session 的正式知识、Structure View/Query Result、Knowledge Gap 或 Limitation。Answer Text 不能成为自身证据。
2. 完整/部分/Gap 结论绑定 exact Requirement Revision、Session、Use Epoch 和全部 Need Assessment。
3. Reviewer Assessment Proposal 只有在其 exact Task-owned Outcome Assertion、Invocation 与 Grant 匹配，且 Response-owned Review Attempt 绑定的 reviewer output digest 与 model eligibility 都有效时才可接收；Task Control 不拥有 Review Attempt 或 Review Decision。
4. Review 使用当前权威重新读取 Claim、引用、Context 和 Coverage；UNKNOWN、遗漏或语义扩张均失败关闭。
5. `PARTIAL_FORMAL_SUPPORT` 只可披露未满足枚举 Need 的 Support Proof 已证明部分，必须同时交付该 Need 的 Gap、未知范围和未满足 obligations；它不能改变 Need Outcome 或整体 Sufficiency。
6. 只有 exact approved Candidate 可授权；正文、引用、限制或权威绑定变化立即使授权失效。
7. 发送前重新验证 Task / Use / Qualification / Authorization Revision、当前 permission / classification，以及正式知识和 Application Result 的有效性，并唯一 claim dispatch。
8. 同一 logical delivery 使用稳定 Adapter Key；结果 pending 时不得生成或发送第二份正文。
9. 业务失败、Gap 和 Limitation 同样接受审核，不能通过错误路径绕过安全和内容规则。
10. 已满足 Need 仍可携带必须披露的 Application Limitation；该 Claim 绑定同一 Sufficiency Proof，但不是正式知识或 Knowledge Gap，不得获得 Formal Reference，也不得把 Need 改写为未满足。投影可以改善可读性，但不能改变这三类权威来源。
11. Evidence Answer 重写必须绑定同一 Checklist、Packet Digest、prior Draft 和 exact Review Findings；Review 要求补证时必须返回 Application 形成新 Packet，Response Control 不能访问 Source Tool 或自行扩充证据。
12. World Model Answer 的生成、审核和重写固定同一 Snapshot、View/Query Result、Coverage 与 Support Map；Response Control 不得访问 Source、启动 Knowledge Update 或切换 Direct Investigation。输入变化必须形成新的 Candidate，而不是改写旧授权。

## Failure and implementation boundary

Adapter Outcome Unknown 保持 pending；迟到 Receipt 只能解析原 Dispatch。Candidate/Review Matrix/Auth/Delivery DTO、详细状态和重试算法由代码与 Contract/Fault Tests 定义。
