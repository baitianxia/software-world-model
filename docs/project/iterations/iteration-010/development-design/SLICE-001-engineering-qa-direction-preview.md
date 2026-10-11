---
id: ITER-010-SLICE-001
kind: development-slice
status: authorized
authority: current-development
owners: [engineering, architecture, quality, product]
depends_on: [ITER-010-PROPOSAL, ITER-010-READINESS, ITER-010-VERIFICATION, ITER-010-PDR-010, ITER-006-RESULT-ACCEPTANCE, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, SYS-ADR-017, SYS-ADR-018, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-KNOWLEDGE-STRUCTURE-MODEL, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-QUALITY-ACCEPTANCE, SYS-QUALITY-SECURITY]
code: [src/software_world_model/knowledge_engine, src/software_world_model/application_services, src/software_world_model/ai_infrastructure, src/software_world_model/interface]
tests: [tests, validation/iteration_010_mvp]
iteration: ITER-010
coding_input: true
current_execution_decision_ref: ITER-010-PDR-014
current_execution_plan_ref: ITER-010-EXECUTION-PLAN-CURRENT
current_execution_finding_refs: [FINDING-010-256, FINDING-010-257, FINDING-010-258, FINDING-010-259, FINDING-010-260, FINDING-010-261, FINDING-010-262, FINDING-010-263, FINDING-010-264, FINDING-010-265, FINDING-010-266, FINDING-010-269, FINDING-010-270, FINDING-010-273, FINDING-010-274, FINDING-010-275, FINDING-010-276, FINDING-010-277, FINDING-010-278, FINDING-010-279, FINDING-010-280, FINDING-010-281, FINDING-010-282, FINDING-010-283, FINDING-010-284]
product_goal_gate: V-000
product_goal_accepted_capability_refs: [ITER-006-RESULT-ACCEPTANCE]
product_goal_cross_domain_case_ids: [V-CHAT-XD-001]
product_goal_web_checkpoint_id: V-CHAT-EXPERIENCE-001
direction_preview_web_checkpoint_id: V-CHAT-EXPERIENCE-001
product_goal_direction_preview_checkpoint_id: V-PREVIEW-002
product_goal_reflection_gate_case_id: V-PREVIEW-002
product_goal_slice_gate_case_ids: [V-BROWSER-CHAT-MVP-BUILD-001, V-AGENT-FIRST-CONVERGENCE-001, V-PUBLIC-OSS-AUTHORITY-ADMISSION-001, V-MODEL-TRANSPARENT-ROUTING-001, V-CHAT-EXPERIENCE-001, V-CHAT-001, V-CHAT-XD-001, V-DIRECTION-QUALITY-001, V-PREVIEW-002]
---

# SLICE-001：最小世界模型辅助工程 Chat

## Status and dependencies

本 Slice 是当前唯一活动开发切片。唯一任务顺序、完成标准和失败处理见
[EXECUTION-PLAN-CURRENT.md](EXECUTION-PLAN-CURRENT.md)。历史四阶段、运行记录和旧验收顺序已移至
[iteration-010-slice-001-history.md](../../../implementation-reference/iteration-010-slice-001-history.md)，不再作为编码输入。

活动切片表示保留的产品范围，不表示当前会话已开始执行；是否恢复产品开发以
`docs/project/current.md` 的本轮工作范围和用户最新指令为准。

## Product-goal contribution and cumulative integration

在一个精确版本、只读的公开工程上，交付一个真实浏览器纵向闭环：用户问题和对话上下文进入 Agent；Agent 按需调用世界模型和源码；模型综合本轮证据生成自然答案；复核发现缺口时反馈同一 Agent；浏览器呈现答案和真实 Citation。

网页可打开不算完成。必须能首问、追问、新问题，并在单题失败后继续服务。

## Current vs expected behavior

当前代码中存在旧 Evidence、旧 QA、Legacy Agent 和 Lightweight Agent 并行路径。它们只能作为兼容/历史资产，不能继续作为当前产品主线。

目标行为是一个由 Agent 主导的可往返循环。世界模型和源码是并列证据工具，不规定固定先后；当前轮证据只用于当前答案。

## System contracts and invariants

- 架构基线保持冻结，不通过本 Slice 修改顶层职责或不变量。
- 世界模型提供版本化工程认知，不直接代替源码事实。
- 源码读取必须绑定精确版本并保持只读。
- Agent 负责理解问题、选择工具、根据观察调整计划和组织答案。
- Reviewer 只复核原问题、答案和证据，不重新生成第二份答案。
- 重要结论必须有本轮真实 Citation；无法确认的内容明确标记未知。

## Interfaces and affected code

当前实现可复用已有模型网关、只读 Source Broker/Worker、Conversation、Citation、浏览器和世界模型资产。实现可以自行决定类、字段、Prompt、Tool Schema、算法和存储，但不得重新引入旧协议主路径、题面特判或答案文本语义门禁。

## Compatibility, data and security boundaries

旧入口和旧模块暂不删除，因为仍被兼容测试和内部组件引用；它们必须使用 evaluation/compatibility 命名，不能作为默认产品入口。产品体验仅允许 loopback、精确工程版本、只读源码和现有授权范围，不接触凭据或生产写操作。

## Open questions and implementation risks

- 浏览器主入口仍需完成 Agent、世界模型和源码的真实组合。
- 世界模型当前存在 Java/Structure 两类实现，需要通过一个对外适配边界使用，不在本 Slice 建立第三套知识系统。
- 固定步数、工具熔断和完整知识覆盖前置可能阻碍首次回答，应优先移出主链路，而不是继续增加规则。

## Acceptance scenarios

1. 浏览器首问进入同一 Agent，并实际调用世界模型或源码。
2. Agent 能根据观察继续调查或自然结束，答案包含真实 Citation。
3. Reviewer 能指出具体缺口，并允许同一 Agent 补证或返回诚实限制。
4. 同一 Conversation 支持追问；新 Conversation 不继承旧指代。
5. 单题失败后浏览器服务仍可接受下一题。

## Findings

实现发现影响系统边界、当前计划或质量规则时，写入 ITER-010 findings 并按治理规则处置；不得在本 Slice 中直接修改架构文档。

## Architecture reflection checkpoint

本 Slice 不改变架构。任何实现证据若要求改变顶层职责、权威、不变量或 Agent/世界模型/源码关系，必须停止该项实现并走架构变更流程；普通实现失败不得借机改写架构。
