---
id: ITER-010-SLICE-001
kind: development-slice
status: authorized
authority: current-development
owners: [engineering, architecture, quality, product]
depends_on: [ITER-010-PROPOSAL, ITER-010-READINESS, ITER-010-VERIFICATION, ITER-010-PDR-010, ITER-006-RESULT-ACCEPTANCE, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, SYS-ADR-017, SYS-ADR-018, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-KNOWLEDGE-STRUCTURE-MODEL, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-QUALITY-ACCEPTANCE, SYS-QUALITY-SECURITY]
code: [src/software_world_model]
tests: [tests, validation/iteration_010_mvp]
iteration: ITER-010
coding_input: true
current_execution_decision_ref: ITER-010-PDR-012
current_execution_finding_refs: [FINDING-010-153, FINDING-010-161, FINDING-010-163, FINDING-010-165]
current_scheduling_finding_ref: FINDING-010-179
product_goal_gate: V-000
product_goal_accepted_capability_refs: [ITER-006-RESULT-ACCEPTANCE]
product_goal_cross_domain_case_ids: [V-CHAT-XD-001]
product_goal_web_checkpoint_id: V-CHAT-EXPERIENCE-001
direction_preview_web_checkpoint_id: V-CHAT-EXPERIENCE-001
product_goal_direction_preview_checkpoint_id: V-PREVIEW-002
product_goal_reflection_gate_case_id: V-PREVIEW-002
product_goal_slice_gate_case_ids: [V-BROWSER-CHAT-MVP-BUILD-001, V-PUBLIC-OSS-AUTHORITY-ADMISSION-001, V-MODEL-TRANSPARENT-ROUTING-001, V-CHAT-EXPERIENCE-001, V-CHAT-001, V-CHAT-QUALITY-001, V-CHAT-XD-001, V-DIRECTION-QUALITY-001, V-PREVIEW-002]
---

# SLICE-001：真实浏览器 Chat 纵切

## Status and dependencies

`AUTHORIZED / PDR-012 PRODUCT BUILD ACTIVE / coding_input=true`。依赖 ITER-006 accepted 能力、当前 Proposal/Readiness/Verification、PDR-010
产品方向和现行 System Contracts；PDR-011 只保存历史失败，不再控制当前产品动作。

## 目标

尽快交付普通用户可直接体验的无认证浏览器 Chat，同时验证整体方向：

World Model Cognition → Main Engineering Agent → controlled read-only Source → Evidence/Citation → natural Answer → fresh independent Review → semantic multi-turn Web。

这是一条产品纵切，不是组件清单。世界模型、Agent、Evidence、Review 或 Web 单独完成都不算交付；POM/Maven-only 回答、静态回放、
一次性 CLI 和预制问题页面也不算。

## Current vs expected behavior

- 现有 loopback 页面、Conversation/Turn 骨架、受控 Source、Evidence/Citation 和 Reviewer 资产可复用；
- 历史候选曾在部分问题上形成答案，但长期出现代码走读、Maven-only 认知、遗漏副作用、Reviewer 漏判和 closed structured output 拒绝；
- run-052/053 在 Answer/Citation/Review 前失败，证明产品仍不可体验，不证明总体架构应停止；
- 最大风险是继续针对单题或输出字段碰答案，而没有区分世界模型构建/查询、Agent、Evidence/Answer、Review 与 Web 的最早偏差。

期望行为是用户在同一浏览器 Conversation 中连续提问、追问和纠正，Agent 先使用问题相关认知、再按 Gap 补证，每轮交付自然答案、Citation
和 fresh Review；实际行为仍会在答案形成前失败，因此本 Slice 必须直接修复并贯通该链。

## Product-goal contribution and cumulative integration

- 软件世界模型维护 exact revision 上持久、版本化、可验证、可更新的软件认知，包括结构、行为、关系、职责、影响、失败边界、Coverage、
  Gap、来源和检索入口；它不是文字手册、Maven 快照或 locator 缓存。
- 主工程 Agent 是回答问题的大脑：维护用户目标、指代、约束、假设、计划和观察；先利用问题相关世界模型认知，认知不足时提出受控源码
  操作，根据结果重规划并形成自然答案。
- Application/Broker/Worker 拥有权限、exact revision、只读执行、证据身份和安全熔断；模型不取得直接文件、Shell、网络、凭据或写入权。
- fresh independent Reviewer 检查原问题是否满足、关键事实是否正确完整、Citation 是否支持、Unknown 是否来自真实 Coverage/Gap；它返回
  具体 Finding，不替主 Agent 规划或执行工具。

该纵切在 ITER-006 已接受的版本化知识能力之上，第一次把世界模型认知、主工程 Agent、受控源码、逐 Turn Evidence/Review 和语义多轮 Web
组合成普通用户可直接判断方向的产品结果。

## System contracts and invariants

适用 Owner 为 SYS-ADR-018、Engineering Conversation、Agentic Task、Evidence/World Model Answering、Source Artifact、Security 和 Local
Browser contracts。若实现证据改变跨模块语义，先按 Finding policy 写回唯一 System Owner；局部实现由代码和测试决定。

Conversation/Turn/Context 由 Application 拥有；模型不直接访问 Repository、FS、Shell、network、credential 或 write；源码固定 exact
revision 且只读；每个重要结论绑定 Citation；prior Answer/Review 与 Provider hidden memory 不取得事实权威；Reviewer 必须 fresh 且独立。

## Interfaces and affected code

允许修改 `src/software_world_model/` 中的 Application、AI infrastructure 和 Interface 产品路径，以及 `tests/`、
`validation/iteration_010_mvp/` 中与纵切直接相关的定向验证。具体文件由最早偏差证据决定，
不得预先扩大重构范围。

## 唯一工作计划

1. 使用已有 run-052/053 trace 和当前代码建立最小分层证据表，确定最早可证实偏差；不得从最终错误文案猜根因。
2. 只修复该 Owner 的最小通用问题。禁止题面、关键词、工程名、符号、类、方法、fixture、示例答案或 Provider/model identity 分支。
3. 在一个非 POM/Maven 的代表性工程问题上打通首轮：世界模型有可观察的行为/职责/失败边界认知贡献；Gap 触发 Agent 受控读源码；页面
   得到自然 Answer、可打开 Citation 和本轮 fresh Review。
4. 在同一 Conversation 完成上下文追问和纠正/深入/总结；新 Conversation 用模糊指代验证隔离。每轮有独立 Request/Evidence/Review；
   prior Answer 和 hidden memory 不作事实证据。
5. 运行最小 targeted、startup、安全和失败真实性测试。链一旦可操作，立即启动固定 loopback 页面作为“开发体验候选”交给用户，
   requires_result=false；该候选不得称为 MVP、质量 PASS、方向 PASS 或完成。
6. 候选交付后不暂停、不等待新的用户决定，立即在同一候选上运行至少两个未参与修复的异质问题，并让 actual current Codex 在隔离任务中
   回答相同问题。独立 exact-source 证据和技术复核判断双方正确性、完整性、Citation、Unknown 和用户目标满足度。只有系统重大错误为 0、
   逐题无物质退步、总体严格更优且有非 locator 世界模型价值，才能称为 MVP。
7. 质量不足时回到第 1 步继续同一 BUILD。停止同 signature 的无新证据外调，但不停止产品开发，不切备用碰答案，不创建失败 Result/PDR。

## Acceptance scenarios

| Case | 必须可观察的结果 |
|---|---|
| V-BROWSER-CHAT-MVP-BUILD-001 | 兼容技术 ID；持续完成开发体验候选及其质量资格，不能因 ID 含 MVP 就声明完成 |
| V-CHAT-XD-001 | 同一答案链同时使用问题相关世界模型认知和 Gap 驱动的受控源码证据，且二者来源区分正确 |
| V-CHAT-001 | 至少三轮语义连续：首问、追问、纠正/深入/总结；新 Conversation 隔离 |
| V-CHAT-QUALITY-001 | 每轮自然回答、重大错误 0、关键结论有可打开 Citation、fresh Review 无重大漏判 |
| V-MODEL-TRANSPARENT-ROUTING-001 | 产品只使用首选/备用执行角色；只有可信不可用结论触发备用，输出或审核失败不触发 |

首次 Web 交付只证明“候选可操作”，不冒充 MVP、方向、质量、稳定性或 Production PASS。交付后必须立即继续质量资格：系统自身重大错误
为 0；逐题相对 current Codex 无物质退步；总体严格更优；至少一项重要价值来自非 locator 世界模型认知。Codex 不是 Oracle 或裁判。

## Compatibility, data and security boundaries

当前公开 mall exact revision、只读 Source、既有配置路线、披露、预算和 loopback evaluation 属 standing scope；每个真实 dispatch 自动
记录 exact source/product/session/route/disclosure/budget，人工重复授权请求为 0。只有私有/新 Source、新接收方或账户、扩大披露/预算、
外部写入、非 loopback、Production 或破坏性操作才申请权限。

首次体验前不做 full regression、hidden、第二工程、持久化、性能优化、完整四路因果消融或 Production。它们是方向确认后的夯实顺序，
不是当前权限停工点。模型调用次数和成本不能降低单个已开始 Turn 的调查、答案或独立审核质量。

开发只有在用户明确 STOP/REDIRECT/REJECT、真实 scope delta 的 exact 请求已发出且独立安全工作穷尽，或不可绕过的安全禁止时才能停。
普通答案、格式、测试和 Reviewer 失败只关闭对应 Turn 或完成声明。

strict WORLD_MODEL 与显式 DIRECT 兼容入口不得静默串线。Secret 不进入仓库、Prompt、日志、Evidence 或页面；late/unknown/不合格结果不得覆盖
已交付答案。既有 route/disclosure/budget 内的公开源码评估继续使用 standing authority，真实 scope delta 才失败关闭并申请最小权限。

## Architecture reflection checkpoint

首次体验后以真实 Turn 判断 A1/A2/A3/A5/A6，并在后续跨工程阶段判断 A4。current Codex 是强基线，独立源码证据负责事实，独立技术复核负责
质量判断；模型答案不是 Oracle。结论不足时继续 REWORK 当前 Slice，不因一次失败停止产品开发。

## Open questions and implementation risks

- 最早偏差究竟位于世界模型投影、Agent 工作状态、typed evidence/answer contract 还是 Reviewer；
- 世界模型非 locator 认知能否稳定参与不同类型问题，而不是只在示例题出现；
- Agent 是否根据观察重规划并在证据充分时结束，而不是固定流水线或无界探索；
- 三轮 Chat 是否真正使用当前 Context，同时隔离新 Conversation；
- Reviewer 是否能阻断物质遗漏和错误 Citation，而不接管工具规划。

这些问题由 trace、最小复现和未参与修复的异质问题回答，不通过题面特判或重复外调碰答案。

## Findings

当前纠偏由 PDR-012 拥有；FINDING-010-153、161、163、165 与既有 Results 保留计划自锁和答案前失败证据。新实现发现按
[实现发现回写规则](../../../governance/implementation-feedback-policy.md) 写入 [Findings index](../findings/README.md)，不得用 Finding 创建新的
普通失败停工点。

## 交付

第一条真实三轮链完成后立即提供启动命令、固定 URL、exact product/source revision、可操作页面和已知限制，并明确标记“开发体验候选，
质量未通过，不是 MVP”。该交付无 Result、不移动游标；开发不停，立即继续同候选异质质量检查和 current Codex 同题比较。只有质量资格
通过后才以 MVP 交给用户判向；最终方向与验收事实再在适当的完成记录中密封，不把过程治理放回产品关键路径。
