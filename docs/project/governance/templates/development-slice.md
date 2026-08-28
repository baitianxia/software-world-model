---
id: ITER-NNN-SLICE-NNN
kind: development-slice
status: proposed
authority: proposed-development
owners: [engineering]
depends_on: [ITER-NNN-PROPOSAL]
code: []
tests: []
iteration: ITER-NNN
coding_input: false
plan_revision_ref: ITER-NNN-PDR-NNN
current_action_ref: ITER-NNN-ACTION-COMPLETE-EXPERIENCE-NNN
current_action_case_id: V-MVP-EXPERIENCE-NNN
product_goal_gate: V-000
product_goal_accepted_capability_refs: []
product_goal_cross_domain_case_ids: []
product_goal_complete_experience_case_id: V-MVP-EXPERIENCE-NNN
product_goal_direction_quality_case_id: V-DIRECTION-QUALITY-NNN
product_goal_direction_preview_case_id: V-PREVIEW-NNN
product_goal_reflection_gate_case_id: V-REFLECT-NNN
product_goal_slice_gate_case_ids: []
---

# SLICE-NNN：<Complete experience outcome>

## Execution card

`first operable browser delivery (no Result) → same-candidate heterogeneous/Codex comparison → final experience Result handoff → user direction decision`

本 Slice 是一个长运行产品动作，可跨多个普通提交。第一次完整浏览器主链可操作后立即交给用户；随后在同一候选上执行至少 3 个异质问题（至少 2 个未参与修复）和 actual current Codex 的严格比较。比较失败阻止方向 `PASS`、hardening 和晋级，但不阻止首次体验交付，也不结束本 Slice。

用户明确 `CONTINUE` 前，不运行 direct evidence / source-only / World Model+source / current Codex 四路因果消融、full regression、hidden、
跨工程或 hardening。`CONTINUE` 后，同一 standing scope 内直接按工作计划继续；只有真实 scope delta 才申请授权。

## User-visible outcome

- Baseline user-visible behavior: <exact-current-browser-evidence>
- Slice-end complete experience: <world-model-agent-source-evidence-citation-review-semantic-chat>
- Repeatable launch and fixed loopback entry: <exact-command-and-address>
- Version and limitations shown to user: <exact-ui-boundary>
- Same-conversation follow-up/correction/summary: <exact-cases>
- New-conversation isolation: <exact-case>
- Failure isolation: <single-turn-failure-service-remains-usable>

## Complete answer chain

本 Slice 必须以真实产品路径闭合以下职责，而不是只完成其中一个组件：

1. 世界模型为大模型提供版本化的软件认知、结构关系、覆盖范围、来源和检索入口；
2. 主工程 Agent 理解用户目标，形成假设和计划，选择源码工具，解释观察，必要时重规划并判断完成；
3. 平台控制精确版本、只读源码访问、外部分派、Evidence/Citation、预算与审计；
4. 独立 Reviewer 面向原问题检查正确性、完整性、引用、未知边界和对话一致性；
5. 浏览器展示自然答案、证据、真实限制和可持续 Conversation 状态。

## Current versus expected behavior

## Interfaces and affected code

## System contracts and invariants

## Security and source boundaries

公开开源、来源/许可证可确认、符合 approved revision policy、clean、allowlisted、只读的测试工程，在 active `PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY@1` 的 route、预算、调度、有效期和 loopback `EVALUATION_ONLY` 范围内，不逐 run、问题、Conversation 或 Turn 申请人工授权。每次外部分派仍须在 Source disclosure、network 和 credential 前生成 exact one-use runtime receipt；receipt 不能扩权，scope mismatch 必须失败关闭。

只有私有/来源未知/dirty 数据、来源或 revision policy 漂移、新外部接收方或 route identity、预算增加、外部写入、非 loopback 或 Production 等真实 scope delta 才直接申请最小授权。批准后自动继续；等待期间继续所有独立安全工作。Provider/model 具体名称只属于 execution profile 和 runtime receipt。

## Failure diagnosis and repair loop

每个不准确、不完整、引用错误或对话错误先记录以下链路的最早偏差：

`Source truth → World Model cognition → conversation/task understanding → Agent work state/plan → tool observation/evidence → answer → independent review → Web`

在形成可证伪 root-cause hypothesis 前不得修改 Prompt、Schema、Contract 或添加规则。每次通用修复先通过本地最小复现和未参与修复的相邻案例，再执行有界 live canary。相同 signature 仍复现时重新检查最早偏差和职责归属；不得堆叠单题特判或无新证据地重跑外部模型，但产品开发继续。

失败保持本动作和 Slice `IN_PROGRESS / coding_input=true`。不为每次失败、测试或 Provider dispatch 新建 action 或 Result。

## Verification order

首次完整体验交付前只运行：

- targeted impact tests；
- startup / fixed-loopback browser smoke；
- source/secret/authorization safety；
- failure truthfulness 和单题故障隔离。

`V-CHAT-EXPERIENCE-NNN` 首次完整主链形成后立即交付；该交付
`requires_result=false`，不密封 Result、不移动游标，也不等待下列比较。随后在同一候选上运行：

- 至少 3 个异质问题，其中至少 2 个未参与修复；
- actual current Codex 的 fresh 隔离答案；
- 基于独立源码证据的密封、独立质量评估；
- 系统绝对质量、逐题无物质落后、总体严格超过和非 locator 世界模型贡献检查。

上述比较不是首次体验前置。用户 `CONTINUE` 后，在同一 standing scope 内直接调整工作计划并进行四路因果消融、full regression、hidden、跨工程和 hardening；只有真实 scope delta 才申请新的最小授权。

## Acceptance scenarios

## User handoff and direction decision

第一次完整浏览器主链形成后只报告 exact version、启动入口、完整链、Chat 行为、质量待验证状态和限制，立即让用户操作；此时不生成 Result、不移动游标。随后同候选完成异质问题和 Codex 比较。只有最终 `V-MVP-EXPERIENCE-NNN` 方向/完成 handoff 或真实项目状态迁移时，才密封一次 Result。

用户基于真实体验和比较结果决定 `CONTINUE / REWORK / REDIRECT / REJECT`。方向 Result/receipt 只记录决定，不能创建或扩大权限；`CONTINUE` 在既有 standing scope 内直接进入夯实，`REWORK` 保持本 Slice 继续开发，只有明确用户转向或核心架构证伪才使用 `REDIRECT`。真实 scope delta 才需要新的最小授权。本地消息 digest 不是平台认证身份或授权。

## Findings

链接本轮 [Findings](../findings/README.md) 并按实现发现回写规则处置。只有 Readiness 已接受、Slice 改为 `status: authorized` / `authority: current-development` / `coding_input: true`，且 `project/current.md` 指向本 Slice，才是编码输入。
