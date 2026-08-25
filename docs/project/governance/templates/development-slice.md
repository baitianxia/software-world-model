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
product_goal_gate: V-000
product_goal_accepted_capability_refs: []
product_goal_cross_domain_case_ids: []
product_goal_web_checkpoint_id: pending
product_goal_direction_preview_checkpoint_id: V-PREVIEW-NNN
product_goal_alpha_access_checkpoint_id: V-ALPHA-ACCESS-NNN
product_goal_experience_timebox_checkpoint_id: V-TIMEBOX-NNN
product_goal_alpha_agent_comparison_checkpoint_id: V-COMP-ALPHA-NNN
product_goal_live_ad_hoc_checkpoint_id: pending
product_goal_reflection_gate_case_id: V-REFLECT-NNN
product_goal_slice_gate_case_ids: []
---

# SLICE-NNN：<Vertical outcome>

## Status and dependencies

同一 Iteration 有多个累积 Slice 时，本 Slice 必须依赖 accepted Readiness，并直接依赖前一个 Slice。Readiness 只授权第一个 Slice；
后续 Slice 保持 proposed，直到前序人工 Web、该阶段适用的 hidden canary、停止 Gate 和方案复盘完成并形成 exact Slice Result。可体验
Alpha 使用可见真实输入判向，不因 hidden canary 延迟；Alpha `CONTINUE` 后的夯实 Slice 才承担 early hidden。后续授权时再把
该 Result 加入 `depends_on`，并与 Manifest `reflection_prerequisite_result` 一致；不能先授权再补证据。

本 Slice 的失败尝试默认进入 `paused / coding_input=false`，不授权下一 Slice。原 Result 由 Manifest/PDR 保留；用户用新的明确收据
重新授权后，恢复本 Slice 而不是新建 Iteration。只有满足 Proposal 冻结的转向依据才使用 `blocked / REDIRECT`。

## Product-goal contribution and cumulative integration

说明本 Slice 如何缩短 Proposal 冻结的通用源码问答差距、如何连接此前已接受能力，以及本 Slice 结束时用户能在同一个正式
Web 入口人工验证什么。中间机械 Gate 可以先行，但 Slice 不能靠孤立 CLI/View 演示宣称产品增量。

- Product gap shortened: <exact-gap>
- Product capability-path step advanced: <roadmap-step-and-user-visible-delta>
- Existing capabilities combined: <exact-capabilities>
- User-visible Web questions at slice end: <held-out-and-cross-domain-cases>
- Slice stop / redirect signal: <falsifiable-signal>
- Same-Slice rework and no-progress limit: <progress-measure-attempt-limit-and-redirect-bases>
- Critical assumptions tested: <assumption-ids-and-evidence>
- Reflection gate and success decision: <V-REFLECT-NNN-and-CONTINUE-or-ACCEPT>

## Direction preview checkpoint

若本 Slice 是可体验 Alpha，列出真实产品入口、小而多样的代表性任务、仅为运行所必需的门禁、用户可见限制，以及体验后由谁作出
`CONTINUE / REWORK / REDIRECT / REJECT`。不得安排与方向判断无关的全面加固。技术质量必须由独立评测方先行裁决，用户只作产品方向
决定。若本 Slice 属于工程夯实或正式验收，必须引用前一 Alpha 的 `CONTINUE` 结果。

方向探索 Slice 必须把本轮最小的有序用户交付点放在本文件最前部的一页执行卡中，至少区分可启动入口、可持续方向体验和最终判向。
每一行都写明累计时限、用户可见出口、允许验证、停止条件和明确延后项。检查点完成后立即交付，不等待后续 Gate；它们不创建或恢复
Slice/Readiness/开发授权，只能在当前授权仍 active 时执行。外部执行仍须 exact grant，且任何用户方向否定都会停止后续检查点。

从下一份新产品 Iteration 起，Alpha 还必须在同一出口绑定 `V-COMP-ALPHA-NNN`：一条原失败题加另外至少两条相邻或异质题，后两条中至少
一条是产品冻结后的现场输入；current Codex fresh 独立任务先密封、
系统不可见、两份答案随机匿名、独立评测方依据 exact evidence 裁决。系统绝对质量 PASS、逐题无物质退步且总体答案质量严格为正才允许
`CONTINUE`；全体打平或只具有效率优势时在同一 Slice `REWORK`。该 Case 不是体验前的新阶段。

## Experience-first timebox and Access/Quality split

首个持续 Alpha Slice 从授权后的第一次产品代码变更开始计时：60 分钟内页面可启动，180 分钟内形成用户可连续操作的持续 Alpha；
到 240 分钟仍未形成时，停止功能扩张、hardening 和外部模型调用，密封已有证据并缩围复盘。首次体验前只允许页面启动、安全边界、
失败真实性、一次 current Provider 资格确认和最多一个 Provider 前本地/Mock Access smoke；不得把全量回归、完整资格、hidden 或对照放在前面。

`V-ALPHA-ACCESS-NNN` 只判断真实产品页面和请求通路是否可操作；Provider 未配置、未资格或失败可以被如实显示，不能阻塞页面交付，也
不能证明答案质量。页面 availability 不等待质量 PASS，但 `V-COMP-ALPHA-NNN` 或本 Slice 冻结的质量 Case 必须 PASS 后才可 hardening。
一次 live attempt 是同一
sealed version 中一个有界用户交互单元只要发生任一外部 dispatch 就计一次，不按单元内部模型/角色调用数放大；Chat 中每个已 dispatch Turn 分别计数；同一 failure signature 最多再试一次，
连续两次没有用户可见增量后停止外部重跑，回到本地根因诊断。已经开始的问题仍执行完整质量链，成本不能删减调查、回答、引用或独立审核。

每次 live failure 先按 `Source truth → World Model cognition → conversation/task understanding → Agent work state/plan → tool observation/evidence → answer → independent review → Web`
记录 earliest divergence 和可证伪 root-cause hypothesis；在此之前禁止改 Prompt/Schema/Contract。修复先通过本地最小复现和至少两个未参与
修复的相邻案例，再执行一个有界 live canary 单元；Chat 使用冻结的最小多轮 Conversation，不得以孤立一题代替。同 signature 修复一次仍复现时，停止增加规则并评审架构职责。Alpha 前只做 targeted impact、
startup、safety 测试；full regression 只能进入 `CONTINUE` 后 hardening 和正式验收前。

记录 Ark-first ordered route 的 current 资格证据，并在 session 开始前预授权双方 disclosure scope。Ark attempt 以 Provider/模型能力原因
终态结束且没有 authorized answer 时，可以对用户透明地启动最多一个 DeepSeek attempt；用户不用新建 session 或重提。fallback 必须从
当前交互的 immutable original input 和 exact World Model cognition 重跑完整链；Chat 还必须携带该 Turn 的 exact relevant Application-sealed Conversation Context。不能复用前次中间产物；迟到 Ark 结果只能隔离审计，不能覆盖已密封
结果。同 Provider retry 为 0；Application、Source 或 Security 失败不得切 Provider 掩盖。DeepSeek 批量工作优先安排在执行时重新核对的
官方非高峰窗口，紧急峰时启动必须有可审计显式 override。

## Experience version checkpoint

记录精确版本、可重复启动方式、固定本地地址、版本/限制显示和单题故障隔离的验证 Case。若产品声明 Chat，还必须记录完整消息历史、
新对话、语义追问、纠正、总结、逐轮证据/审核和新对话隔离；仅在同一 Runtime Session 连续提交独立问题不满足本检查点。

## Current vs expected behavior

## System contracts and invariants

## Interfaces and affected code

## Compatibility, data and security boundaries

## Open questions and implementation risks

## Acceptance scenarios

## Architecture reflection checkpoint

本 Slice 的产品 Gate 后必须形成 exact Result，逐项比较假设与证据、分类问题、复核知识表示/查询编排/Web 产品链/验证设计、
对照成熟方案并处置相关 Finding。`V-REFLECT-NNN PASS` 只表示复盘完成；中间 Slice 只有明确决定 `CONTINUE` 才可申请下一段授权，
最终 Slice 只有明确决定 `ACCEPT` 才可申请 Iteration Acceptance。方案被证伪时使用 `REDIRECT` 或 `REJECT`，不得继续堆叠实现。
实现、答案、审核、配置或局部 Contract 缺陷使用 `REWORK`，只暂停当前 Slice；问题被指出或要求复核不得直接解释为方案被证伪。
Manifest 只绑定本 Slice 已到期的假设；成功决定要求这些假设全部为 `SUPPORTED`。尚未到期的假设只能记录 early signal 与下一风险，
不能伪装成已经证明；最终 Slice 必须覆盖全部关键假设。

产品价值复盘必须把 current Codex 外部强基线与 full cognition/locator-only 因果消融分开；Codex 不得充当 Oracle 或 Reviewer，次级成本、
时延和复用指标不得补偿答案质量平局或退步。

## Findings

链接本轮的 [Findings](../findings/README.md) 与[实现发现回写规则](../../../governance/implementation-feedback-policy.md)。只有 Readiness 已接受、Slice 改为 `status: authorized` / `authority: current-development` / `coding_input: true`，并被 `project/current.md` 指向后，才是编码输入。
