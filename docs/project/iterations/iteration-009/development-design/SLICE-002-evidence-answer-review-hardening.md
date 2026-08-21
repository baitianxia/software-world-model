---
id: ITER-009-SLICE-002
kind: development-slice
status: proposed
authority: proposed-development
owners: [engineering, architecture, quality, product]
depends_on: [ITER-009-PROPOSAL, ITER-009-READINESS, ITER-009-SLICE-001, ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-ACCEPTANCE]
code: [src/software_world_model/application_services, src/software_world_model/knowledge_engine, src/software_world_model/ai_infrastructure, src/software_world_model/interface]
tests: [tests, validation]
iteration: ITER-009
coding_input: false
product_goal_gate: V-000
product_goal_accepted_capability_refs: [ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-ACCEPTANCE]
product_goal_cross_domain_case_ids: [V-XD-002]
product_goal_web_checkpoint_id: V-WEB-002
product_goal_reflection_gate_case_id: V-REFLECT-002
product_goal_slice_gate_case_ids: [V-ANSWER-002, V-REWRITE-002, V-HARDEN-002, V-SEC-002, V-XD-002, V-WEB-002, V-CANARY-002, V-NEG-EARLY-002, V-COMP-EARLY-002, V-DIAG-002, V-REGRESSION-002, V-REFLECT-002]
---

# SLICE-002：通用证据问答链夯实

## Status and dependencies

`PROPOSED / NOT AUTHORIZED / NOT EXECUTED`。`SLICE-001` 的 Reflection 决定为 `REDIRECT` 而不是 `CONTINUE`，ITER-009 已拒绝；
因此本 Slice 在本轮中不可再授权。原设计只作为历史方案保留，后续 Iteration 不得把它当成编码输入或自动继承其假设。

## Product-goal contribution and cumulative integration

- Product gap shortened：把方向体验中验证的主线收敛为不依赖具体问题的 Evidence Package → Draft → independent Review → targeted
  Rewrite → Delivery 合同，并在第二个真实工程上证明可复用。
- Product capability-path step advanced：从早期体验进入 `ROADMAP-M-002` Step 1 的通用工程闭合。
- Existing capabilities combined：继续使用 accepted Workspace/Update/Snapshot/Web/Citation/declaration/`CALLS` 和前段封存的体验链。
- User-visible Web questions at slice end：同一 Web 对 answerable、bounded negative、coverage limitation 和第二工程跨域题均能交付可核对结果。
- Slice stop / redirect signal：需要题目/工程特判、Review 弱化、Direct fallback、表示缺口被 Prompt 掩盖、第二工程同类 boundary 仍内部失败，
  或安全/回归/资格任一失败。
- Critical assumptions tested：复核 A1—A3并正式验证 A4；A5 作为安全与最终质量假设继续保留 early signal。
- Reflection gate and success decision：`V-REFLECT-002`；只有用户新的 `CONTINUE` 才可申请正式验收段授权。

## Direction preview checkpoint

本 Slice 不再创建新的方向体验。它必须引用 `SLICE-001` 的 exact `V-PREVIEW-001` 与 `V-REFLECT-001: CONTINUE` Result；没有该结果时
本段保持 proposed。所有夯实继续通过同一个本机 Web 展示，不另建内部演示入口。

## Current vs expected behavior

预期输入是前段已证明有价值但仅覆盖最小任务的产品链。完成后，Application 明确拥有 evidence package、answer type、review
applicability、具体 finding 和单次 targeted rewrite 的状态转换；模型负责自然回答与独立检查，不拥有权限、预算、Ref provenance、
完整性状态或终态的最终解释权。

supported answer、bounded negative 和 insufficient coverage 使用统一协议与不同 typed evidence 状态，不靠问题词、项目名或特定符号分支。

## System contracts and invariants

- Evidence Package 只包含授权、精确版本、typed results、coverage、support 与可引用位置；不是用户答案文本。
- Draft 可以综合多条证据形成自然答案，并为重要结论绑定支持；无法推出的内容必须形成具体 typed Limitation。
- independent Review 按原问题检查实质完整性、越界推断和引用覆盖，并返回具体 finding；不能把适用于负向结论的完整性条件机械套到
  supported answer，也不能因证据不足本身拒绝 typed Limitation。
- targeted rewrite 只能使用同一 sealed evidence package 和具体 review finding，最多一次且计入冻结模型调用预算；无法修复即失败关闭。
- 任何 System Owner、answer protocol、call budget 或 Provider identity 改变必须先形成 Finding，更新 owning Contract/ADR 并重新资格化。
- Source/Update/Direct fallback、问题特判、隐藏 retry、Secret 泄露和公网监听继续禁止。

## Interfaces and affected code

预计影响 World Model answer application service、typed evidence/answer/review contract、model Gateway request/result schema、Web presenter、
Citation delivery、qualification fixtures 和相应测试。实际文件必须由前一 Slice Finding 和 exact code inspection 决定，以最小正确变化为准。

## Compatibility, data and security boundaries

保持 ITER-005/006 accepted 行为与 `SLICE-001` 已封存的用户交互。Knowledge Update 仍在问题前独立发生；聊天路径只读取 no-payload
World Model View。若未来需要异步知识沉淀，只能作为独立能力设计，不得让其阻塞或静默改变当前问答链。

任何 live Conformance、Capability 或 Web 运行都需要与当前代码/configuration identity 匹配的新 freeze 与授权；旧 run-028、run-012
或 Slice1 Result 不授权本段 Provider 请求。

## Open questions and implementation risks

- 单次 targeted rewrite 是否必须增加总调用上限，需要用真实缺口与成本证据决定；不能隐藏为 retry。
- 现有 typed Result 是否足以表达 evidence package，还是需要 Contract 级最小新对象，必须由跨工程证据裁决。
- 第二工程若揭示知识表示缺口，本段应 redirect 到表示层，不通过 Prompt 扩写掩盖。
- 资格调用次数由正确性与独立审核需要决定，不能因配额压低质量。

## Acceptance scenarios

1. `V-ANSWER-002`：answerable、bounded negative、insufficient coverage 三类通用 fixture 均按 typed contract 交付。
2. `V-REWRITE-002`：Reviewer 对实质遗漏返回具体 finding；同一 evidence package 的一次 targeted rewrite 修复且重新通过独立审核，
   不可修复路径失败关闭。
3. `V-HARDEN-002`：预算、pagination/coverage、schema、Ref provenance、terminal 和错误语义机械闭合。
4. `V-SEC-002`：Source-off、Secret、授权、zero hidden retry、Reviewer 隔离与 loopback PASS。
5. `V-XD-002` 与 `V-WEB-002`：第二工程跨域题从同一正式 Web 给出 supported answer 或正确 Limitation/Citation。
6. `V-CANARY-002` 与 `V-NEG-EARLY-002`：Slice2 代码冻结后才首次披露的 1 answerable + 2 boundary early canary PASS；披露后改产品即烧毁。
7. `V-COMP-EARLY-002` 与 `V-DIAG-002`：在正式验收前完成成熟源码 Agent 小规模对照、正向价值测量和 Source 到 Web 的逐层诊断。
8. `V-REGRESSION-002`：accepted 能力、方向体验主线和完整测试集无新增失败。
9. `V-REFLECT-002`：A1—A4 全部有 exact Verdict，A5 有 early signal，用户给出新的继续、转向或拒绝决定。

## Architecture reflection checkpoint

本段 Result 必须对问题分类、首次偏差、Contract 变化、调用成本、第二工程、成熟方案差距与全部 Finding 做独立复盘。
`V-REFLECT-002 PASS` 只表示资料完整；只有 A1—A4 全部 `SUPPORTED` 且用户新决定为 `CONTINUE`，才可申请 `SLICE-003`。

## Findings

链接 [Findings](../findings/README.md) 与[实现发现回写规则](../../../governance/implementation-feedback-policy.md)。本 Slice 当前不是编码输入。
