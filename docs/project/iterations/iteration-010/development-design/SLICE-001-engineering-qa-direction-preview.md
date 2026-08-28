---
id: ITER-010-SLICE-001
kind: development-slice
status: authorized
authority: current-development
owners: [engineering, architecture, quality, product]
depends_on: [ITER-010-PROPOSAL, ITER-010-READINESS, ITER-010-PDR-010, FINDING-010-153, FINDING-010-093, FINDING-010-094, FINDING-010-095, FINDING-010-100, FINDING-010-101, FINDING-010-102, FINDING-010-103, FINDING-010-104, FINDING-010-105, FINDING-010-106, FINDING-010-107, FINDING-010-108, FINDING-010-109, FINDING-010-110, FINDING-010-111, FINDING-010-112, FINDING-010-113, FINDING-010-114, FINDING-010-115, FINDING-010-116, FINDING-010-117, FINDING-010-118, FINDING-010-119, FINDING-010-120, FINDING-010-121, FINDING-010-122, FINDING-010-123, FINDING-010-124, FINDING-010-125, FINDING-010-126, FINDING-010-127, FINDING-010-128, FINDING-010-129, FINDING-010-130, FINDING-010-131, ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST, ITER-006-RESULT-ACCEPTANCE, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, SYS-ADR-013, SYS-ADR-014, SYS-ADR-015, SYS-ADR-016, SYS-ADR-017, SYS-ADR-018, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-KNOWLEDGE-STRUCTURE-MODEL, SYS-QUALITY-ACCEPTANCE, SYS-QUALITY-SECURITY]
code: [src/software_world_model/application_services, src/software_world_model/ai_infrastructure, src/software_world_model/interface]
tests: [tests]
iteration: ITER-010
coding_input: true
current_execution_decision_ref: ITER-010-PDR-010
current_execution_finding_refs: [FINDING-010-132, FINDING-010-133, FINDING-010-134, FINDING-010-135, FINDING-010-136, FINDING-010-137, FINDING-010-138, FINDING-010-140, FINDING-010-141, FINDING-010-153, FINDING-010-154, FINDING-010-155, FINDING-010-156, FINDING-010-157, FINDING-010-158, FINDING-010-159, FINDING-010-160, FINDING-010-161, FINDING-010-162]
current_scheduling_finding_ref: FINDING-010-139
product_goal_gate: V-000
product_goal_accepted_capability_refs: [ITER-006-RESULT-ACCEPTANCE]
product_goal_cross_domain_case_ids: [V-CHAT-XD-001]
product_goal_web_checkpoint_id: V-CHAT-EXPERIENCE-001
direction_preview_web_checkpoint_id: V-CHAT-EXPERIENCE-001
product_goal_direction_preview_checkpoint_id: V-PREVIEW-002
product_goal_reflection_gate_case_id: V-PREVIEW-002
product_goal_slice_gate_case_ids: [V-MVP-EXPERIENCE-001, V-PUBLIC-OSS-AUTHORITY-ADMISSION-001, V-PUBLIC-OSS-AUTHORITY-001, V-LAYER-ATTRIBUTION-001, V-COGNITION-ELIGIBILITY-001, V-FALLBACK-ROUTE-ADMISSION-001, V-MODEL-TRANSPARENT-ROUTING-001, V-ALPHA-ACCESS-001, V-CHAT-EXPERIENCE-001, V-CHAT-001, V-CHAT-QUALITY-001, V-CHAT-XD-001, V-DIRECTION-QUALITY-001, V-PREVIEW-002]
---

# SLICE-001：完整体验版开发与用户判向

## Status and dependencies

状态：`AUTHORIZED / IN_PROGRESS / coding_input=true / NON-PRODUCTION`。当前计划是 `ITER-010-PDR-010`，Case 是
`V-MVP-EXPERIENCE-001`。机器动作 ID `ITER-010-ACTION-USER-PLAN-RECOVERY-001` 仅为可信父提交连续性保留；它当前表示完整体验版开发，
不表示仍需 recovery、Activation 或 Freeze。

Manifest 当前动作的 path allowlist、forbid list 与 locks 是唯一机械边界。动作可跨多个普通提交持续进行；定向失败、内部候选和普通外调
都不移动游标。`V-CHAT-EXPERIENCE-001` 的第一条完整主链可操作即交付，但 `requires_result=false`、不移动游标。只有同一候选完成三条异质问题、两条 unseen 与 current Codex 比较形成最终 `V-MVP-EXPERIENCE-001` handoff，或一次通用修复后同类重大失败仍存在时，才形成一次 Result/evidence，然后进入 `V-PREVIEW-002`。

current evidence 已到达第二个出口的产品停止条件：run-052 原失败与 run-053 两个异质案例在一次通用修复后仍以 Ark typed-output contract
失败，且结构化输出失败期间 DeepSeek dispatch 始终为 0。产品修复和外调现已停止。冻结 `ITER010_MVP_LIGHT@2` 却只接受已有三份完整
Answer/Citation/Review/Codex comparison 的单 Session 包，不能表达当前答案前失败；当前动作又禁止修改该 runner 与 PDR。因此 Result 尚未
密封、游标尚未移动。唯一合法后续是用户明确授权最小 forward governance revision，先修订失败 handoff contract/runner 并形成新的 trusted
parent，再在后续提交密封唯一 Result。

## Current vs expected behavior

当前可复用资产包括 loopback Chat Access、Conversation/Turn 骨架、主工程 Agent 候选、世界模型 Cognition、受控 Source、Evidence/
Citation、独立 Review、模型路线组合和历史失败 trace。run-045 已把这些组件放入同一真实 Browser 链，并证明 standing authority runtime
与新 Conversation 隔离；但主 Conversation 的第二、三 Turn 失败，尚未共同证明一个可供普通用户持续体验的完整 MVP。

期望行为是同一真实浏览器路径完成：

1. 用户无需认证地创建 Conversation 并提出工程问题；
2. Application 为该 Turn 投影 exact revision 的版本化、多域软件世界模型认知；
3. 主工程 Agent 维护目标、假设和计划，根据每次观察决定继续查询世界模型、受控读取 Source 或结束调查；
4. Broker/Worker 只执行 allowlisted、exact-revision、read-only 操作，模型没有直接源码或系统权限；
5. 调查结束后密封逐 Turn Ledger/Package，主工程 Agent 给出直接答案和结论级 Citation；
6. fresh independent Reviewer 检查问题满足、重大遗漏、证据支持、Citation 和边界；Finding 返回主工程 Agent；
7. 用户可以基于前文追问、纠正、深入或总结；新 Conversation 不继承旧 Context、Evidence 或 Provider memory。

页面、POM/模块图、单轮回答、比较 runner、静态回放或内部测试本身都不算完成。

## Product-goal contribution and cumulative integration

本 Slice 第一次把“软件世界模型认知 + 主工程 Agent + 受控源码 + Evidence/Citation + fresh Review + 语义多轮 Web”作为不可拆分的用户体验。
世界模型不是手册或 locator 缓存；它为 Agent 提供问题前的系统认知。Source 是回答复杂问题的受控补证手段，不取代世界模型，也不回填为
世界模型贡献。

首条完整主链可操作即立即交付用户，明确标记质量状态；随后在同一候选上运行至少三条异质问题，其中至少两条未参与修复，并以 actual
current Codex 独立作答作强外部基线。Codex 不是事实源、Oracle、Reviewer 或裁判。

## System contracts and invariants

- Conversation/Turn/Context 由 Application 拥有；用户陈述、prior Answer/Review 和 Provider hidden memory 不成为 Source truth。
- World Model Cognition 绑定 exact Context/Scope/Schema/Snapshot/Read Authority/Coverage；Maven-only 对行为问题不得冒充完整认知。
- 主工程 Agent 拥有理解、规划、观察解释、重规划、完成判断和答案综合；Control Plane 拥有权限、预算、执行、证据身份和审计。
- Source Broker/Worker 是唯一实际 Source 读取路径；所有模型直接 Repository/FS/Shell/network/credential/write 权限为 0。
- Ledger append-only；Package 只有 support/citation 能支持肯定 Claim，boundary/audit 只约束结论或支持 Limitation；seal 不证明内容为真。
- Reviewer 必须 fresh 且独立，只返回具体 Finding；任何补证或重写都形成新的 Ledger/Package/Answer/Review identity。
- 每个重要结论有 exact Citation；Unknown/Limitation 必须来自可核对 Coverage/Gap，不能把未找到扩张为不存在。
- 不允许工程、题面、关键词、符号、类、方法、fixture 或 Oracle 特判。
- 模型对产品流程透明：动作、分支和质量标准只依赖通用 route role、execution-profile ref/digest 与 availability verdict；产品代码禁止读取
  具体 Provider/model 身份形成分支。具体身份只属于 execution profile 配置和 runtime receipt。
- fallback 的唯一入口是 availability boundary 密封 `PREFERRED_EXECUTION_PROFILE_UNAVAILABLE`。结构化输出无效、Reviewer 拒绝或未经
  availability boundary 分类的原始 HTTP/outcome 均不得回退。格式修复和审核重写留在同一 profile，作为有界的新 call 使用新 request/receipt，
  不属于 transport request retry；安全/no-progress 边界耗尽后如实关闭当前 Turn。

## Interfaces and affected code

实现范围只取 Manifest 当前动作允许的最小子集，主要涉及：

- Application：Conversation/Turn、主 Agent loop、World Model/Source 工具适配、Ledger/Package、Answer/Review/Delivery 绑定；
- AI infrastructure：通用模型边界、透明 route composition、per-dispatch admission/receipt 与失败终态；
- Interface：唯一无认证 loopback Chat 启动入口、消息历史、新 Conversation、答案/Citation/限制与折叠诊断；
- Tests：改动相关的 contract、startup、security、failure-truthfulness 与至少两个非定制相邻/异质案例；其中
  `V-MODEL-TRANSPARENT-ROUTING-001` 必须以可执行 stub/fixture 验证 availability-only fallback、同 profile 新 call 语义和产品分支不读取
  具体 Provider/model；
- 体验证据：只在最终 handoff 时记录 exact candidate、URL、问题、trace/Citation、比较、限制和测试计数。

不得修改 Manifest 禁止路径，不能以候选计划给自身扩权。

## Compatibility, data and security boundaries

strict `WORLD_MODEL` 与显式 `DIRECT_INVESTIGATION` 兼容入口不得静默串线。Source 固定 exact revision、allowlist 和 read-only；仓库内容按不可信
输入处理。Gateway/receipt/Session 私有文件从创建起保持 owner-only，Secret 不进入日志、证据或页面。单 Turn 失败只关闭该 Turn，服务与
Conversation 可继续；late、unknown 或不合格结果不得覆盖已授权 Delivery。

当前公开 mall exact revision、既有披露/预算和配置路线属于 standing scope，不再逐 run/Turn/dispatch 请求用户批准。每次真实 dispatch
仍须由 runtime 自动派生 one-use exact receipt，并在 Source disclosure、credential/network 前检查 revision、route、account、budget、
disclosure、调度与 admission policy。真实 scope delta 必须失败关闭并申请最小增量权限。

## Development loop and immediate handoff

| 顺序 | 开发与验证 | 用户可见出口 |
|---|---|---|
| 1. 完整主链 | 选择一个代表性语义多轮 Conversation，接通全部必需组件；只运行改动相关测试、启动与安全 smoke | 以 `V-CHAT-EXPERIENCE-001` 交付启动命令、URL、exact candidate、质量状态和限制；`requires_result=false`、不移动游标、不等待比较 |
| 2. 异质自测 | 同候选运行至少 3 条异质问题：用途/入口或结构、行为调用链与实质副作用、故障/授权/未知；至少 2 条未参与修复；包含至少 3 Turn 语义链与新 Conversation 负测 | 逐题展示答案、Citation、Review、失败和限制 |
| 3. current Codex 强基线 | 用相同问题和 exact revision，由 actual current Codex 保留真实客户端、model、reasoning、tools 与权限独立作答；独立技术判断 | 如实给出逐题差异、重大错误、物质遗漏和总体结论 |
| 4. 最终 handoff 与用户判向 | 比较完成，或证明一次通用修复后同类重大失败仍存在时，密封一次 `V-MVP-EXPERIENCE-001` Result；进入 `V-PREVIEW-002` | 用户决定 `CONTINUE / REWORK / REDIRECT / REJECT`；receipt 只记录方向且 action 自环 |

严格方向通过要求重大错误为 0、逐题相对 Codex 无物质退步、总体严格超过 Codex，并有至少一项非 locator 世界模型贡献。第一次可操作体验
可以先于该结论交付，但不能被描述为质量 PASS。

最终 Result 的机器验证范围严格限于：候选 Git commit/tree 等于 Result 提交的实际可信父节点、冻结的公开源码与 standing authority、执行配置、
exact session/config/input/disclosure/budget/Secret Reference 的一次性 receipt/计数，以及内嵌原始证据字节
与摘要的结构闭合。机器不认证本地 capture 的真实性，也不判断答案的语义质量；浏览器记录、系统答案、源码事实、世界模型认知、fresh Review、
current Codex 答案和独立比较必须作为内嵌原始记录随 handoff 交给用户，而不能以可能不存在的路径或自报摘要替代。
该 Case 的机器 `PASS` 只代表 handoff 包完整；包内必须另列 `QUALITY_PASS` 或 `QUALITY_FAIL_AFTER_ONE_GENERAL_REPAIR`，两种情况都进入用户判向。

## Failure attribution and repair

普通失败留在当前动作中持续处理：

1. 保存同一 Turn 的 Source truth、World Model construction/projection、Conversation/Work State、Agent observation/plan、Ledger/Package、Answer、Review 和 Web output；
2. 找到最早 material divergence 与本应阻断却未阻断的 guard failure；允许同题同时存在多个下游故障，但修复从最早责任层开始；
3. 提出可证伪根因假设；没有 trace 和假设不得修改 Prompt、Schema、Contract 或工具策略；
4. 做一次最小通用修复，先验证原失败，再验证两个未参与修复的异质案例；
5. 同类故障仍复现时停止无新证据外调，保留最后可运行版本、最早责任层、证据和限制，进入用户判向。

测试失败、preferred execution profile 暂时不可用或授权 scope delta 只阻断对应工作；其他本地、安全且独立的工作继续。不得以同题重跑、规则累积或放宽审核
标准碰正确答案。

`FINDING-010-161` 已完成上述第 4/5 步并停止产品路径。`FINDING-010-162` 记录的是进入用户判向前的计划实现缺口，不授权继续修产品，
也不授权当前候选修改 frozen verifier；该缺口必须通过 forward-only governance revision 解决。

## Open questions and implementation risks

- 现有 Agent loop 是否真的根据上一观察重规划，还是仍是固定多角色流水线；
- 世界模型投影是否覆盖当前问题的行为、职责和失败边界，而不是只给结构 locator；
- Agent 是否会在证据充分前结束，或在无进展时无界探索；
- Reviewer 是否能阻断物质遗漏和错误 Citation，且不会取得工具规划权；
- Conversation 是否真正使用前文语义，同时避免 prior Answer 与新 Conversation 污染；
- runtime standing-authority receipt 已形成 Session/Turn/call 本地派生候选；current actual artifact 中它是否在每个真实 dispatch 前自动、
  one-use 且失败关闭仍须 live receipt 验证；
- 答案是否先解决用户目标，而不是把调查记录和代码走读机械平铺。

这些风险由通用 trace、异质问题和跨层替换实验定位，不通过题目特判消除。

## Acceptance scenarios

| Case | 当前 Slice 判定 |
|---|---|
| `V-CHAT-EXPERIENCE-001` | 第一条完整浏览器主链含世界模型、主 Agent、受控源码、逐 Turn Evidence/Citation/fresh Review、至少 3 Turn 语义链和新 Conversation 隔离；可操作即无 Result 交付，不移动游标、不等待 Codex 比较 |
| `V-MODEL-TRANSPARENT-ROUTING-001` | 可执行定向测试证明产品代码只按 route role/profile ref 与 availability verdict 分支；互换配置身份不改行为；仅首选 profile 不可用结论可回退；结构化输出无效与 Reviewer 拒绝只在同 profile 形成有界新 call，不能触发备用路线；耗尽后准确失败关闭 |
| `V-MVP-EXPERIENCE-001` | 完整浏览器链可运行；至少 3 条异质问题、至少 2 条未参与修复；至少 3 Turn 语义链和新 Conversation 隔离；逐 Turn Evidence/Citation/fresh Review；targeted/startup/safety PASS；full regression=0；记录 current Codex 比较和世界模型非 locator 贡献，或诚实记录最早责任层与失败限制 |
| `V-DIRECTION-QUALITY-001` | 在首次体验之后，以同一候选证明绝对质量、逐题不退步、总体严格超过 current Codex 和非 locator 世界模型贡献；不要求体验前四路 Freeze |
| `V-PREVIEW-002` | 用户能真实追问、纠正、深入或总结并查看证据、比较和限制；方向 receipt 只记录决定。`CONTINUE` 后仍需新 PDR、明确用户授权与可信父 cutover 才能解锁后续夯实 |
| `V-PUBLIC-OSS-AUTHORITY-ADMISSION-001` | standing scope 不重复人工审批；逐 dispatch exact receipt 与 scope-delta fail-close 成立 |

## Architecture reflection checkpoint

Slice1 handoff 按 A1—A6 给出证据化 verdict，但不要求首次体验前完成完整因果消融：A1 世界模型认知、A2 主工程 Agent、A3 Evidence/
Review、A5 current Codex 严格质量、A6 语义多轮必须在当前候选可判；A4 跨工程和 A5 完整四路因果消融在用户 `CONTINUE` 后执行。任何
模型答案都不是真值，独立源码证据和技术判断分别负责事实与质量判读。

## Post-CONTINUE work

只有用户 `CONTINUE`，且后续新 PDR 获得明确用户授权并完成可信父 cutover 后才进入 Slice2：hardening、full regression、跨重启恢复、第二工程、hidden、复杂冲突/去重/性能/安全矩阵，以及
同 Agent、同配置、只改变认知输入的完整四路因果消融。上述工作不得反向阻塞或延迟当前完整体验交付。

用户方向 Result/receipt 不自行扩权；本地消息 digest 只是内容证据引用，不是平台认证身份、签名或授权。

## Findings

当前计划纠偏由 [FINDING-010-153](../findings/FINDING-010-153.md) 和
[PDR-010](../decisions/PDR-010-complete-mvp-vertical-slice.md) 拥有；当前 live authority 与 Source 最后槽位实现发现分别由
[FINDING-010-154](../findings/FINDING-010-154.md)、[FINDING-010-155](../findings/FINDING-010-155.md)、
[FINDING-010-156](../findings/FINDING-010-156.md)、[FINDING-010-161](../findings/FINDING-010-161.md) 和
[FINDING-010-162](../findings/FINDING-010-162.md) 处置。既有实现/运行发现与失败证据继续在
[Findings index](../findings/README.md) 和 [Results index](../results/README.md) 中保留，不在本当前执行卡重复展开。后续发现按
[实现发现回写规则](../../../governance/implementation-feedback-policy.md) 处置。
