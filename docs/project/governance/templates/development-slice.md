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
current_action_ref: ITER-NNN-ACTION-DIRECTION-FREEZE-NNN
current_action_case_id: V-DIRECTION-FREEZE-NNN
product_goal_gate: V-000
product_goal_accepted_capability_refs: []
product_goal_cross_domain_case_ids: []
product_goal_web_checkpoint_id: pending
product_goal_direction_preview_checkpoint_id: V-PREVIEW-NNN
product_goal_alpha_access_checkpoint_id: V-ALPHA-ACCESS-NNN
product_goal_experience_timebox_checkpoint_id: V-TIMEBOX-NNN
product_goal_alpha_agent_comparison_checkpoint_id: V-DIRECTION-QUALITY-NNN
product_goal_direction_freeze_checkpoint_id: V-DIRECTION-FREEZE-NNN
product_goal_direction_quality_checkpoint_id: V-DIRECTION-QUALITY-NNN
product_goal_live_ad_hoc_checkpoint_id: pending
product_goal_reflection_gate_case_id: V-REFLECT-NNN
product_goal_slice_gate_case_ids: []
---

# SLICE-NNN：<Vertical outcome>

## Status and dependencies

本 Slice 的广义 `coding_input` 不拥有执行顺序。实际工作必须先匹配 Manifest 唯一 `current_action` 的 Case、coding/external flags、前置、
allowed/forbidden paths 和 locks；不在 action allowlist 中的产品代码、Prompt/Reviewer、Provider、Web、hardening 或测试一律未授权。
`project/current.md` 必须镜像 plan revision、action ID 和 Case ID。开发前运行 plan snapshot；交付前以 trusted base 运行 base-diff gate。

同一 Iteration 有多个累积 Slice 时，本 Slice 必须依赖 accepted Readiness，并直接依赖前一个 Slice。Readiness 只授权第一个 Slice；
后续 Slice 保持 proposed，直到前序人工 Web、该阶段适用的 hidden canary、停止 Gate 和方案复盘完成并形成 exact Slice Result。可体验
Alpha 使用可见真实输入判向，不因 hidden canary 延迟；Alpha `CONTINUE` 后的夯实 Slice 才承担 early hidden。后续授权时再把
该 Result 加入 `depends_on`，并与 Manifest `reflection_prerequisite_result` 一致；不能先授权再补证据。

本 Slice 的失败尝试默认保留为同一 Slice 的 `REWORK`，只阻止 PASS、晋级、扩域和 hardening。若现有本地开发授权仍覆盖通用修复，
保持 `authorized / in-progress / coding_input=true`；只有 scope/Owner 变化、用户明确暂停或本地开发授权失效时才进入
`paused / coding_input=false`。原 Result 由 Manifest/PDR 保留；恢复时继续本 Slice而不是新建 Iteration。只有满足 Proposal 冻结的转向
依据才使用 `blocked / REDIRECT`。

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

本 Slice 的第一页执行卡必须先列出 `direction-gate-freeze → four-arm-direction-quality-gate → minimum Web Chat → user direction
decision`。freeze action 只冻结三条异质问题、四路 runner、独立 source-truth ledger、盲化 rubric、exact identities 和 Result Schema，
外部调用与产品代码均为 0；其 PASS 后才可运行四路 Gate，四路 PASS 后才解锁 Web action。

若后续 action 是可体验 Alpha，列出真实产品入口、小而多样的代表性任务、仅为运行所必需的门禁、用户可见限制，以及体验后由谁作出
`CONTINUE / REWORK / REDIRECT / REJECT`。不得安排与方向判断无关的全面加固。技术质量必须由独立评测方先行裁决，用户只作产品方向
决定。若本 Slice 属于工程夯实或正式验收，必须引用前一 Alpha 的 `CONTINUE` 结果。

方向探索 Slice 必须把本轮最小的有序用户交付点放在本文件最前部的一页执行卡中，至少区分可启动入口、可持续方向体验和最终判向。
每一行都写明累计时限、用户可见出口、允许验证、停止条件和明确延后项。检查点完成后立即交付，不等待后续 Gate；只要当前阶段仍有
未完成工作且授权覆盖，交付后继续执行。检查点不创建或恢复 Slice/Readiness/开发授权，也不是开发目标或开发回合的自动停止点。外部
执行须落在 standing external authority 内并生成 exact machine receipt，只有 scope delta 才需新的人类授权；用户明确方向否定会停止后续
检查点。

四路 Gate 对当前及未来计划立即强制：直接相关证据、同 Agent 仅源码、同 Agent 世界模型认知+源码、current Codex。事实由独立 exact
source ledger 持有；答案先密封、随机匿名，独立评测方不参与生成。世界模型臂须绝对质量 PASS、逐题不输任一基线、总体严格超过
Codex，并证明至少一项非 locator 世界模型贡献；全体打平、任一物质退步、both-fail、unresolved/invalid 或盲化失效均 `FAIL`，效率
不得补偿。该 Gate 明确发生在体验前，但仍属于同一 Slice，不创建额外产品 Slice。

## Authorization continuity and development-turn exit

分别冻结 Slice 本地开发授权、人类 `PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY@1`、系统派生 exact Authorized Input Manifest/one-use
disclosure/dispatch receipt 和一次性 scope-delta grant。standing authority 必须明确 canonical public source、许可记录、revision selection policy、每次运行的 exact commit/tree、
clean 状态、allowlist/只读披露、Provider/model/endpoint/credential account route、调用/重试/token/时长预算、调度、有效期/撤销条件、结果
保存、loopback `EVALUATION_ONLY` Sink 和 exclusions。source identity 保持在该范围内的新 run、Conversation、Turn 或问题不构成 delta，
不得逐次请求用户授权。

每次外部动作仍须在 Source disclosure、Provider socket 或 credential 前冻结 exact command/action、product/source revision、artifact/
session/turn、Provider/model/
endpoint/credential account、input/disclosure/redaction、预算、时间和 fallback，并生成回指 standing authority 的 exact machine receipt；
receipt 不能创建权限，缺失、失效或 scope mismatch 必须失败关闭。只有私有/来源或许可证未知/仅本机存在/dirty 数据、超出 approved
upstream/revision selection policy/allowlist、新外部接收方或 route identity、预算增加、超出 fallback admission policy 的调度范围或需要一次性 override、
外部写入、非 loopback 暴露、Production Activation 或
standing authority 的其他 exclusions 才直接提交最小 exact approval request。不得先问“是否申请”，也不只报告“需要授权”后退出；
批准后自动继续。等待期间继续所有不依赖该 delta 的安全工作。

开发回合只能在以下任一条件成立时结束：阶段用户可见交付已交给用户；scope-delta exact request 已实际发出且所有独立安全工作已
穷尽；用户明确
`STOP / REDIRECT / REJECT`；或存在不可通过申请或安全替代绕开的禁止。等待状态写成 `WAITING_EXACT_GRANT / IN_PROGRESS`，不得写成
开发完成、失败或停止。

## Experience-first timebox and Access/Quality split

本节只在四路方向 Gate PASS 并由预注册 Web action 解锁后适用。首个持续 Alpha Slice 从 Web action 获授权后的第一次产品代码变更开始
计时：60 分钟内页面可启动，180 分钟内形成用户可连续操作的持续 Alpha；
到 240 分钟仍未形成时，停止功能扩张、hardening、full regression 和无新证据的外部模型重跑，密封已有证据并缩围复盘，同时继续本地
根因归因与最小体验纵切。该 hard stop 结束失控路径，不结束整个开发目标。首次体验前只允许页面启动、安全边界、
失败真实性、一次 current Provider 资格确认和最多一个 Provider 前本地/Mock Access smoke；不得把全量回归、完整资格、hidden 或对照放在前面。

`V-ALPHA-ACCESS-NNN` 只判断真实产品页面和请求通路是否可操作；Provider 未配置、未资格或失败可以被如实显示，不能阻塞页面交付，也
不能证明答案质量。页面 availability 不等待 Web 质量 PASS，但 `V-DIRECTION-QUALITY-NNN` 必须先 PASS 才能解锁 Web，本 Slice 冻结的
Web 质量 Case 也必须 PASS 后才可 hardening。
一次 live attempt 是同一
sealed version 中一个有界用户交互单元只要发生任一外部 dispatch 就计一次，不按单元内部模型/角色调用数放大；Chat 中每个已 dispatch Turn 分别计数；同一 failure signature 最多再试一次，
连续两次没有用户可见增量后停止外部重跑，回到本地根因诊断。已经开始的问题仍执行完整质量链，成本不能删减调查、回答、引用或独立审核。

每次 live failure 先按 `Source truth → World Model cognition → conversation/task understanding → Agent work state/plan → tool observation/evidence → answer → independent review → Web`
记录 earliest divergence 和可证伪 root-cause hypothesis；在此之前禁止改 Prompt/Schema/Contract。修复先通过本地最小复现和至少两个未参与
修复的相邻案例，再执行一个有界 live canary 单元；Chat 使用冻结的最小多轮 Conversation，不得以孤立一题代替。同 signature 修复一次仍复现时，停止增加规则并评审架构职责。Alpha 前只做 targeted impact、
startup、safety 测试；full regression 只能进入 `CONTINUE` 后 hardening 和正式验收前。

记录 preferred-first ordered route 的 current 资格证据，并由 standing external authority 预授权两个角色的 execution profile、disclosure scope、预算与
admission policy；范围内 session/Turn 只需生成 exact machine receipt。preferred-route attempt 以 Provider/模型能力原因终态结束且没有 authorized answer
时，可以对用户透明地启动最多一个 fallback-route attempt；用户不用新建 session 或重提。fallback 必须从
当前交互的 immutable original input 和 exact World Model cognition 重跑完整链；Chat 还必须携带该 Turn 的 exact relevant Application-sealed Conversation Context。不能复用前次中间产物；迟到 preferred-route 结果只能隔离审计，不能覆盖已密封
结果。同 Provider retry 为 0；Application、Source 或 Security 失败不得切 Provider 掩盖。所有 planned fallback-route 调用均须通过该 execution profile
引用的 admission plugin；fallback eligibility 或 standing route authority 不构成调度准入。run receipt 与每个新 request 的准入条件/一次性 exact
override 重验必须早于 Provider socket/connected descriptor、TLS、credential 和 HTTP；缺失时相应计数为 0。完整最坏质量链必须能在
当前准入范围结束前完成；准入失效后不创建新 request，无法完成独立审核时失败关闭。等待准入时继续 preferred-route-only 和本地开发。具体 Provider/model
名称只属于 execution profile 配置和执行收据，不得写入通用 action/Case 语义。

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
实现、答案、审核、配置或局部 Contract 缺陷使用 `REWORK`，只阻止 PASS、晋级与 hardening；现有授权覆盖修复时保持当前 Slice active。
问题被指出或要求复核不得直接解释为方案被证伪。
Manifest 只绑定本 Slice 已到期的假设；成功决定要求这些假设全部为 `SUPPORTED`。尚未到期的假设只能记录 early signal 与下一风险，
不能伪装成已经证明；最终 Slice 必须覆盖全部关键假设。

产品价值复盘必须在同一四路 Gate 内分别报告直接证据、仅源码、世界模型认知+源码和 current Codex；Codex 与直接证据都不得充当
Oracle 或 Reviewer。第 2/3 路的单变量差异用于世界模型因果归因，次级成本、时延和复用指标不得补偿答案质量平局或退步。

## Findings

链接本轮的 [Findings](../findings/README.md) 与[实现发现回写规则](../../../governance/implementation-feedback-policy.md)。只有 Readiness 已接受、Slice 改为 `status: authorized` / `authority: current-development` / `coding_input: true`，并被 `project/current.md` 指向后，才是编码输入。
