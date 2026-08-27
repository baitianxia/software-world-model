---
id: ITER-010-PROPOSAL
kind: iteration-proposal
status: accepted
authority: project-proposal
owners: [product, project, architecture, engineering, quality]
depends_on: [SYS-PRODUCT-SUCCESS, ROADMAP-M-002, ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST, ITER-006-RESULT-ACCEPTANCE, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, FINDING-010-107, FINDING-010-108, FINDING-010-109, SYS-ADR-013, SYS-ADR-014, SYS-ADR-015, SYS-ADR-016, SYS-ADR-017, SYS-ADR-018, SYS-CONTRACT-AI-CAPABILITY-EVALUATION, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS, SYS-CONTRACT-KNOWLEDGE-STRUCTURE-MODEL, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-QUALITY-ACCEPTANCE, SYS-QUALITY-SECURITY, SYS-OPS-LOCAL-BROWSER]
code: []
tests: []
iteration: ITER-010
coding_input: false
current_execution_decision_ref: ITER-010-PDR-009
current_execution_finding_refs: [FINDING-010-132, FINDING-010-133, FINDING-010-134, FINDING-010-135, FINDING-010-136, FINDING-010-137, FINDING-010-138, FINDING-010-140, FINDING-010-141]
current_scheduling_finding_ref: FINDING-010-139
---

# ITER-010 Proposal：软件世界模型与主工程 Agent 驱动的多轮工程 Chat

## PDR-009 current amendment：价值 Gate 前移并机械锁定计划

本轮继续采用“软件世界模型 + 主工程 Agent”的双核心架构，但不再先完善内部链和 Web，再事后比较。最早产品动作改为四路价值 Gate：
直接相关证据、同 Agent 仅源码、同 Agent 世界模型认知+源码、current Codex。前三路共享同一首选 execution profile 与 output 约束；两个 Agent 路除世界模型
认知开关外完全相同。事实来自独立 exact-source ledger，答案隔离密封并盲评；current Codex 和直接证据路都不是 Oracle 或裁判。

目标系统必须先满足零重大错误、物质遗漏、无据结论、错误 Citation、假 Unknown 和 Reviewer 漏判，再逐题不输三个基线、总体严格超过
current Codex，并证明至少一项非 locator 世界模型贡献。全体打平即 FAIL，成本或调用数不能补偿。失败只解锁最早责任层的一个通用修复，
不能继续按单题碰答案。

Manifest v2 已预注册 Freeze、PreferredQuality、FallbackRefreeze、FallbackQuality、FreezeRework、DirectionRework、MinimumWeb、
WebFailureAttribution、UserDirectionDecision、ResponsibilityPlan 十个动作，当前只授权 `ITER-010-ACTION-DIRECTION-FREEZE-001`：零外部调用、零产品代码地冻结 runner、三条异质问题、source-truth
ledger、盲化 rubric、exact identity 和 Result Schema。允许路径、禁止路径、唯一 Result 与后继动作由单树和 base→target 差分门禁执行。
Freeze PASS 后先运行 PreferredQuality。PreferredQuality `PASS` 进入 MinimumWeb，`FAIL` 进入 DirectionRework，`INVALID` 进入零外部调用、零人工授权请求、
零 Provider dispatch 的 FallbackRefreeze；Refreeze 从可信父树绑定首选配置 INVALID Result seal、provider-neutral root input set、备用执行
配置与其准入策略插件，只有首选终态为 `TERMINAL_UNAVAILABLE` 时才 `PASS` 并进入 FallbackQuality；其他 INVALID 返回 PreferredQuality。
FallbackQuality `PASS` 进入 MinimumWeb、`FAIL` 进入 DirectionRework、`INVALID` 自环失败关闭。首选/备用两个 Quality Result 都能生产
`V-DIRECTION-QUALITY-001`，但最多一个 PASS。dirty v7 是
`QUARANTINED / NOT_INPUT`。

## PDR-008 amendment：公开开源评测持续授权

固定测试输入 `https://github.com/macrozheng/mall.git` 是 Apache-2.0 公开工程，当前 clean revision 为
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` / tree `047d79d8588b76013c260f3f1a9565707301a60a`。PDR-008 将现有 Slice/root
授权解释为当前公开工程评测的持续 human authority；每个 run、Turn 和 dispatch 的 exact authority/disclosure/admission 由 runtime 自动
派生为 one-use machine receipt，不再逐次向用户申请。

首选 execution profile 在 current route/budget 内可以直接执行；备用 profile 仅在其 admission plugin 允许、合法 fallback 和完整质量链内
直接执行。备用准入策略例外、private/unknown/different-upstream Source、Provider/model/endpoint/account drift、扩大披露或预算、hidden、
后续 Slice 与 Production 是真正 scope delta，仍须 exact user authorization。未验证 source revision drift 失败关闭；同 approved upstream/revision policy 内的新 clean commit 经 Source Authority 复核
后无需人工批准。PDR-009 后机器收据仍是外部调用的安全前置，但不再作为独立产品阶段；当前 freeze 外部调用为 0，真实四路运行时再
验证和生成 exact receipt。完整 `V-PUBLIC-OSS-AUTHORITY-001` 当前为 `NOT-RUN / blocking`、不是独立入口；PDR-009 已修订其执行顺序，
当前唯一入口仍是 Freeze。FallbackRefreeze 也属于 standing scope 的机器动作，不得重复向用户请求授权。

## Trigger and evidence

`ITER-009-RESULT-SLICE-001-STOP-REDIRECT` 证明真实本机 Web、精确版本、独立审核、Limitation 和 Citation 已能运行，也证明默认答案仍被
方法、分支、调用顺序和内部诊断主导，整体像代码走读。初版 ITER-010 因此引入提问期受控回源，但进一步讨论指出两处架构偏差：

- 把 World Model 简化为“工程手册、地图、检索提示”缩窄了它从项目开始就稳定存在的概念；
- 在回答前一次性生成检索计划和 Evidence Package，不能让大模型根据刚读到的结果继续像高级工程师一样调查。

软件世界模型的定义不变：它是软件在 exact Context、Scope、Schema、Snapshot 上持久、版本化、可验证、可更新的外部认知模型，表达
实体、关系、行为、约束、状态、证据、覆盖和未知边界，为大模型提供稳定系统认知。手册、地图和检索入口只是这种认知面向人或任务的
投影。需要重构的是默认工程问答主链：主工程 Agent 持续维护目标、假设和计划，依据每次工具观察自适应重规划；
Source Broker 和隔离 Retrieval Worker 仍控制实际只读访问。Application 在每个 Turn 完成调查后密封 Evidence Package，主 Agent 综合答案；
fresh independent Reviewer 只返回具体 Finding，Finding 交还主 Agent 决定基于现有证据重写，或在 Control Plane 内启动新的受控补证。

本次重制由 `FINDING-010-002` 保存。用户消息
`codex-user-message:sha256:d3b60bdaa52d96ced3c653a8dcd54fabff41beb7f23f0bf691e6983ebb9437bc`（`2026-08-21T08:23:25Z`）
只要求重新制定计划并更新文档，不构成新设计的产品编码授权。

## PDR-001 amendment：从整轮拒绝改为同轮返工

Slice1 后续真实运行证明调查、证据、Citation 与 Web 链能够工作，也暴露答案代码走读和 Reviewer 漏判。旧 Result 把用户要求“实现者自行
复核已知错误”的消息推断为整轮 `REDIRECT`；[PDR-001](decisions/PDR-001-resume-as-rework.md) 已依据最新用户收据
`codex-user-message:sha256:3112da2512628a1beddf15117a8bd78ed484ad5c6ceece3feac7877e1d7ecf4e` 将当前决定修订为 `REWORK`。

该 PDR 当时把顺序修订为先恢复 Web Alpha、再按真实问题返工；这条历史顺序已由 PDR-009 取代。当前必须先冻结并通过四路方向质量 Gate，
不得先改产品、Prompt、Reviewer 或 Web。单题失败仍只判该 Request 失败；只有通用修复和异质问题复验共同证明核心架构无法有界修复，
或用户实际体验后明确拒绝，才触发架构转向。

该 PDR 只修订项目方向；其接受时 Slice1 为 `paused / coding_input=false`，旧授权与所有 live grant 已消费。后续 `32b298de…` 收据已恢复
编码，外部调用仍须在新 product freeze 后另行授权。

## PDR-003 amendment：体验优先恢复与透明模型路由

用户以 `codex-user-message:sha256:47a3421d48fe3f36000e45696ea9c41b49b7e362332bc724306c10ca42fe119c`
指出 ITER-010 约 14 小时仍没有新的可体验结果，并消耗了大量 DeepSeek token。[PDR-003](decisions/PDR-003-experience-first-provider-cost-recovery.md)
因此曾把 Slice1 收窄为先交明确标记“质量未验收”的可操作 Web。该历史 Access 已经通过并可复用，但 PDR-009 已把新的最早产品判断改成
四路方向质量 Gate；在该 Gate PASS 前停止产品、Answer/Review Prompt、Schema、Contract 与 Web 变更，也不运行 full regression。

Experience policy 使用 60/180/240 分钟检查点。历史经过已经越过 hard stop，当前恢复只允许页面启动、安全、失败真实性、一次必要资格和
最多一次 Provider 前本地或 Mock Access smoke。首个发生 Provider dispatch 的方向 canary 必须是五轮 Conversation；每个 sealed Turn 到达任一外部 dispatch 就计一次 live attempt；同 failure signature 最多一个 successor，
连续两次没有用户可见增量即停止外部重跑。

失败处理从 `answer-chasing` 改为 root-cause-first：按 Source truth 到 Web 的固定责任链定位最早偏差，先提出可证伪假设；没有假设和本地
最小复现不得改 Prompt、Schema 或 Contract。修复需先通过最小复现与两个未参与修复的相邻案例，随后运行一个有界五轮 Conversation 作为
首次方向 live canary；每个到达 Provider dispatch 的 Turn 分别计 live attempt。同 signature
修一次仍复现即停止规则累积并做架构职责评审。首次体验前只跑 targeted impact/startup/safety，full regression 仅在 Alpha `CONTINUE`
后的 hardening 与正式验收前执行。

模型 route 按 ADR-017 对用户透明：Session 只预授权 `preferred → fallback` 两个路线角色，具体身份由 execution profile 配置。用户只提交一次
logical question；preferred attempt 仅在密封 terminal、无 authorized answer 且属于允许的 Provider/model reason 时，才自动启动一次独立
fallback attempt。Fallback 从原 Turn、该 Turn 密封的 exact Cognition 以及与当前 Turn 有关的 sealed Conversation Context 重跑完整链，不复用
preferred 中间态；同 Provider retry 为 0，late preferred 结果
quarantine。PDR-003 作出决定时尚未证明该 route，因此当时只能作为开发目标；后续实现与 live 事实由 PDR-004 段及 Findings 更新。

PDR-007 又把当前 fallback execution profile 的配置专属调度规则收紧为所有 planned development/evaluation dispatch 的调用前硬准入。
当前插件要求最坏完整质量链整体落入其配置窗口；窗口外没有 exact user override 时，在 Provider socket/connected descriptor、TLS、credential
和 HTTP 前关闭且相关计数为 `0`。每个新 request 重验插件 verdict 或 override。等待准入时 preferred route 与本地开发继续，不能把持续开发
解释成绕过备用路线的配置策略立即调用。具体窗口和 Provider/model 身份只属于当前配置插件及其执行收据，不定义本 Proposal 的动作图。

## PDR-004 amendment：主工程 Agent 与真正多轮 Chat

`FINDING-010-093/094` 证明“固定多角色内容流水线 + 同一 Runtime Session 连续独立提问”不是目标产品。PDR-004 因此在不废弃既有
World Model、Broker/Worker、Evidence、Citation、Review、Web 和 Provider 资产的前提下，冻结两个核心：软件世界模型提供持久、版本化、
可验证的软件认知；主工程 Agent 持续拥有用户目标、假设、子任务、计划修订、上下文选择、工具选择、观察解释、重规划、完成判断和答案综合。

默认交互改为 server-owned Conversation/Turn/Context 的语义多轮 Chat。每轮 Request、Evidence、Answer、Review 和 Delivery 保持独立；
Conversation Context 只承载确认目标/约束、指代实体、开放问题、已审核结论 reference、争议或被取代结论及 exact provenance，不把用户陈述、
上一轮答案或 Provider 隐藏记忆变成源码事实。模糊指代必须在 Source/Provider dispatch 前澄清；新 Conversation 不继承旧 working state 或
逐轮证据。

首个 Chat canary 是一段五轮连续对话，而不是三道互不相关问题；另加“新对话后省略指代必须澄清”的泄漏负测。PDR-004 当时使用
same-agent source-only、same-agent full World Model cognition + source、current Codex 三路；PDR-009 已以四路 Gate 取代该协议，并增加
直接相关证据 control。旧编码权威曾由 PDR-004 暂停，`d8239ea7…`
只授权文档同步；用户现以 `f76ba3e8…` 接受刷新 Readiness 并授权 Slice1 产品/System 代码和本地确定性验证。`FINDING-010-095` 已形成
`CHAT_ACCESS_LOCAL_CANDIDATE`；其后一次 exact、零 Provider 的本机 listener/browser grant 已形成
`ITER-010-RESULT-V-ALPHA-ACCESS-001 / FINDING-010-096`，`V-ALPHA-ACCESS-001` 为 `PASS / access-only`。主 Agent、逐轮证据/审核和 Provider
route 当时保持 `NOT_IMPLEMENTED / NOT_QUALIFIED / NOT_LIVE`。`FINDING-010-097` 现已把 Application-owned bounded loop、跨 Turn Work
State、Observation/Package、fresh Review Finding 与 Delivery binding 实现为 `AGENT_EXECUTOR_LOCAL_CANDIDATE`；`FINDING-010-098` 又将
现有 World Model projector、Source Broker/Worker 与可重算的逐 Turn Ledger/Citation receipt 接成 `EVIDENCE_TOOLS_LOCAL_CANDIDATE`。
`FINDING-010-099` 现又把单 Provider 主 Agent/Reviewer 的 closed no-tools input/output、逐 dispatch Disclosure/Gateway receipt、失败计数与
non-dispatching candidate preflight 实现为 `MODEL_BOUNDARY_LOCAL_CANDIDATE`。`FINDING-010-100` 再将 ADR-017 的五类 trusted fallback
classification、两个隔离 full-chain attempt、committed Work State、logical Turn 分账和 fixed Browser composition 实现为
`PROVIDER_ROUTE_COMPOSITION_LOCAL_CANDIDATE`。`FINDING-010-101` 又将生产 Ark/DeepSeek Adapter、credential-lazy transport、Model Gateway、
Session Disclosure 与 model boundary 接入为 `PROVIDER_RUNTIME_COMPOSITION_LOCAL_CANDIDATE`。`FINDING-010-102` 再将两条 Provider runtime、
exact evidence authority、per-attempt fresh Tool/Response Control、committed Work State、Conversation 与 Browser 接成
`SESSION_RUNTIME_COMPOSITION_LOCAL_CANDIDATE`。`FINDING-010-103` 又实现 owner-private artifact Session loader 与唯一
`--session-config` 固定命令分支，形成 `ARTIFACT_SESSION_FIXED_COMMAND_LOCAL_CANDIDATE`。`FINDING-010-104` 又闭合 Ark TLS-before-credential、
per-request Session audit、typed unavailable fallback 与新 Conformance identity。`FINDING-010-105/106` 已分别在 clean `1e99e9b…` /
`653eff3…` 上取得 fresh Ark 2/2、13/13 与 DeepSeek 2/2、12/12 Conformance PASS，两条 route 的 current qualification 同时可用。
`FINDING-010-107` 随后记录 exact `eb835f5…` / `run-035-chat-alpha` 的首次 artifact-backed 五轮 Chat：五轮全部失败，没有
Answer/Citation/Review/Delivery；新 Conversation 没有旧消息，却把省略指代作为通用 pre-dispatch failure，而不是澄清。
`FINDING-010-108/109` 已分别将 Source Search 的 model/Worker contract 对齐为 bounded literal semantics，并将空新 Conversation 的指代
澄清归属到 Binding-owned Application policy。修复状态只是 `LOCAL_CANDIDATE`，后续 Provider/source disclosure 与 live Chat 必须绑定新的
exact product freeze、artifact 和 Session Authority；不能追认首次失败 run。PDR-003 的时间盒、根因、测试后置、Provider 和成本规则全部
继续有效。

## PDR-005 amendment：先证明认知资格和故障层，再恢复体验

run-035—042 证明 PDR-004 的 Agent/Chat 方向尚未被否定，但执行方式已经偏离：唯一 World Model input 始终是 Maven 模块与依赖，
每次失败后又修改下游 Prompt/Schema/Tool/Reviewer，再重复双 Provider Conformance 和同一五轮。用户已停止该执行链，并要求新的开发
对话在文档纠偏后重启。

本 Proposal 的最早差距因此前移：先用 `V-LAYER-ATTRIBUTION-001` 在零外部调用下区分知识构建、Cognition 投影/查询、Agent 调查、
Evidence、答案、Reviewer 与 Web；再以 `V-COGNITION-ELIGIBILITY-001` 建立同一 exact revision 上按问题有资格的多域 Cognition
Capability Manifest。Maven-only 仍是正确的窄结构 Profile，但在行为、流程、职责、配置和故障问题上无 full/engineering cognition
资格。Source 可以补全当前 Turn，不得冒充 World Model 贡献。

v7 的 query/review 提示冻结为未接受症状实验。恢复后不再先重跑首选与备用 profile 的 Conformance：ADR-017 已规定领域 Prompt 或答案 Schema
变化不使同一 Adapter/Configuration/endpoint/model/transport Conformance 失效；fallback 只有在 preferred terminal 已密封且满足通用
fallback reason 时才透明启动。现有 Web Access PASS 复用；PDR-005 当时把方向出口安排为离线归因、多域认知、现有 Web 和语义链，PDR-009
当前改为先用既有 clean candidate 完成四路价值验证，通过后才允许最小 Web Chat。三个互不相关的独立问答不算 Chat；方向确认前不跑
full regression。

项目仍为 `REWORK`，因为世界模型、主工程 Agent、证据与独立审核的总体架构未被证伪。新的“开发 ITER-010”对话可以接手，不能继承旧
对话的 v7 推断或执行待办。当前项目入口继续使用已授权 Slice1，以保留此前失败/timebox 责任；这不绑定开发对话，也不禁止未来在确有
交付边界变化时按治理流程另建 Slice。

## PDR-006 amendment：阶段交付前持续执行，授权按需直接申请

PDR-006 不改变 PDR-005 的 Gate、产品架构或安全边界，只修正执行连续性。检查点、timebox FAIL、局部 Gate FAIL 或外部权限缺口只阻止
对应的 PASS/晋级、扩域、hardening、full regression 或无新证据的外部重跑，不自动结束当前开发目标。只要 Slice1 本地授权仍有效，状态
保持 `AUTHORIZED / IN_PROGRESS / coding_input=true`，开发者继续最小体验纵切与本地根因修复。

到达外部执行边界时，先完成 credential-free preflight 和 exact product/source/artifact/session/disclosure freeze；已有 active grant 且
覆盖该 identity 时必须复用，不能重复询问。只有 scope 或 identity 不受覆盖时，才直接提交最小 exact delta request，不先问“是否申请”；
批准后自动继续，等待期间继续所有独立安全工作。只有阶段交付已交给用户、exact request 已实际发出且替代工作穷尽、用户明确
`STOP/REDIRECT/REJECT`，或存在不可绕过的安全禁止时，开发回合才可结束。

## 当前配置插件证据：PDR-007 备用路线闲时硬准入

`run-043` 在北京时间 `11:19–11:27` 的高峰窗口执行 DeepSeek `18` 次，且没有 fresh official check、window verdict 或 peak override
receipt。该 run 只保留为真实成本、答案、失败和责任层归因证据，不能作为合规方向体验。PDR-007 要求的
`V-DEEPSEEK-IDLE-001` 已由 clean `03520eb…` 本地 PASS：planned development/evaluation run 只能在 `[00:00,09:00)`、`[12:00,14:00)`、
`[18:00,24:00)` 内容纳最坏完整质量链；窗口外没有一次性 exact user override 时在 Provider socket/connected descriptor、TLS、
credential 和 HTTP 前失败关闭。clean `3a6089f…` successor 也已冻结；准入未通过时继续 preferred route 和本地工作。PDR-008 后当前不缺 human grant，
只缺自动机器收据 runtime Gate 与合规 live receipt。该配置插件收据只证明备用路线可被准入，不定义、推进或替代下一动作；当前执行入口仍是
`V-DIRECTION-FREEZE-001`。

## Product-goal alignment and cumulative delta

- MVP target：`SYS-PRODUCT-SUCCESS`。目标是“准确的软件世界模型 + 优秀的主工程 Agent”共同支撑多轮工程 Chat，不另立绕过世界模型的
  源码 Agent 产品，也不建设通用自治 Agent 平台。
- Capability path：`ROADMAP-M-002 / step-1-java-result-driven-world-model-investigation`。World Model 负责持久外部认知；提问期 Source 调查
  用于核实、补充或纠正本题认知，不取代问题前建模和跨问题复用。
- Accepted predecessor：`ITER-006-RESULT-ACCEPTANCE` 提供 exact Snapshot、声明/静态 `CALLS`、Citation 和本机 Web 窄基线；ITER-009
  提供方向反证而非 Acceptance。
- Current gap：已有 Web 与问答链能够运行，但尚未证明“世界模型认知 + 主工程 Agent”在准确性、完整性和可用性上比直接证据、仅源码
  Agent 与 current Codex 更有价值；继续完善 Chat 或代码只会放大尚未验证的方向风险。
- Cumulative integration：同一问题链使用 exact World Model Cognition Context 与本题 source/doc/config/test 调查证据，不建立平行答案。
- Earliest direction checkpoint：当前先以零外部调用冻结三条异质问题、四路 runner、独立源码事实账本、盲评量表和 exact identities；冻结
  PASS 后，在任何新产品、Prompt、Reviewer 或 Web 变更前先运行首选配置四路 Gate；首选配置 INVALID 只能按预注册 FallbackRefreeze→Fallback Quality
  分支处理。题目至少覆盖用途/入口/结构、行为调用链与实质副作用、故障/
  授权/未知三类，至少两题未参与开发，禁止只用 POM/Maven 问题。
- Direction quality gate：直接相关证据、同 Agent 仅源码、同 Agent 世界模型认知+源码、current Codex 四路相互隔离；目标系统绝对质量
  必须 PASS，逐题不得输给任何基线，总体必须严格优于 current Codex，并证明非 locator 的世界模型贡献。Codex 不是 Oracle 或裁判；平局
  和次要效率优势都不能通过。
- Earliest Web checkpoint：只有四路 Gate PASS 才允许在固定 loopback、工程和 exact revision 上交付最小真实语义多轮 Chat。逐轮只读、
  Citation、独立 Review、失败真实性和新对话隔离不可延后；完整五轮套件不反向阻塞最小体验。
- Later proof：只有最小 Chat 经实际体验 `CONTINUE` 后，Slice2 才做持久恢复、复杂冲突/去重/异常矩阵、第二工程、性能、安全、完整回归与
  early hidden；Slice3 执行最终两个未见工程 10 answerable + 2 boundary、两条现场题和正式复验。严格超过 current Codex 已从 PDR-009
  起成为 ITER-010 当前方向门，不再延后到 ITER-012。
- End capability：普通用户无需认证即可在本机 Web 围绕用途、架构、运行、流程、配置、故障、影响和实现细节持续 Chat，能够追问、纠正、
  澄清、深入和总结，并逐轮获得直接、层级匹配、可核对 Citation 的答案或诚实 Limitation。
- Next gap：第二语言、跨仓库、大型工程性能、持续后台认知更新和非本机部署。
- Request fail：答案重大错误、物质遗漏、错误 Citation、审核漏判或资源熔断只使当前问题失败并进入同轮返工，不得冒充成功。
- Stop/redirect：世界模型被降级为手册/缓存；调查不是先前结果驱动；模型取得直接 Source 权限；任何题目/工程/关键词/符号/类/方法/
  fixture/Oracle 特判；Ledger/Package/Review 身份错配或安全边界失效；多个异质问题证明核心路径无法有界修复；用户在持续体验后明确转向或拒绝。

## Critical assumptions and falsification plan

| 假设 | 最早证据与反证 | 反证后的动作 |
|---|---|---|
| A1：软件世界模型保持为持久、版本化、可验证、可更新的软件外部认知，提问期 Source 调查只核实、补充或纠正本 Turn 认知 | Slice1 先以 `V-DIRECTION-QUALITY-001` 检查非 locator 认知贡献，再以 current System Owner 和 `V-CHAT-QUALITY-001` 检查 Chat；Slice2/3 复验。把 World Model 降级为手册、缓存、locator 集或 Source recall 门禁，或完整 Cognition 无可验证贡献，即反证 | REDIRECT 认知与问答边界；不用命名掩盖概念漂移 |
| A2：主工程 Agent 能持续维护目标、假设、子任务和计划，依据每次观察选择 World Model/Source 受控工具并重规划，不取得直接权限 | Slice1 的 `V-CHAT-001/V-CHAT-QUALITY-001`；若仍是预先固定的角色/操作清单、需要特判，或 Agent 必须直接访问 repository/FS/Shell/network/credential/write 才能工作，即反证 | REDIRECT Agent/tool 合同；保留 Application/Broker/Worker 的 exact-version、allowlist、只读、证据身份、预算和审计责任 |
| A3：每个 Turn 的 Evidence Package、自然答案与 fresh independent Review 同时保证直接答案、Citation、失败关闭和可返工性，Reviewer Finding 只回到主 Agent | Slice1 的 `V-CHAT-QUALITY-001`。若 seal 被当作真值、prior Answer/Review 取得证据权威、Reviewer 直接规划/执行工具，或 Finding 绕过主 Agent 进入固定补证角色，即反证 | 修正 Agent—Evidence—Review 首个系统性偏差；不减少证据或独立审核换取交付 |
| A4：相同 Conversation—主 Agent—受控工具—逐 Turn Evidence/Review 协议能跨第二工程、来源组合和复杂失败泛化 | Slice2 的 `V-GENERAL-002/V-RERETRIEVE-002/V-CANARY-002/V-XD-002`；新工程或新表达必须新增项目/问题/关键词/符号/类/方法/fixture/Oracle 分支，或主 Agent 的补证与重规划不收敛，即反证 | REDIRECT 通用 Context、Agent/tool、Broker 或 Review 合同；烧毁已披露输入并保留 Result |
| A5：产品外部比较与 World Model 因果消融在同一四路 Gate 中独立判读；current Codex 保留真实客户端、model、reasoning、tools 和权限，前三路固定相同 Provider/model/config，两个 Agent 路除认知开关外完全相同 | Slice1 的 `V-DIRECTION-QUALITY-001` 是阻塞方向门：目标系统绝对质量 PASS、逐题不输直接证据/仅源码/current Codex、总体严格超过 Codex，且有非 locator 认知贡献。把任一模型答案当真值或裁判、削弱 Codex、混用 Provider、让系统两 Agent 路存在其他变量差异、以平局或效率补偿质量，即反证 | FAIL 后只解锁最早责任层的通用修复；两轮通用架构修复仍失败则作架构责任决策 |
| A6：产品具有真正语义多轮 Conversation，而不是同 Session 的独立问答 | Slice1 的 `V-CHAT-EXPERIENCE-001/V-CHAT-001/V-CHAT-QUALITY-001`。五轮必须验证追问指代、用户纠正、进一步区分/深入、基于 current Context 总结、逐 Turn 证据与新 Conversation 隔离；任一缺失即反证 | REWORK Conversation/Work State 而不将单 Turn 失败自动升级为整轮 REDIRECT |

Slice1 先以 `V-DIRECTION-FREEZE-001/V-DIRECTION-QUALITY-001` 验证 A1/A5 和整体方向，通过后再以最小 Chat 验证 A2/A3/A6；Slice2 累积
验证 A1—A4/A6，Slice3 最终覆盖 A1—A6。
资源、调用、文件、bytes 和 wall time 都是预先密封的安全上限，不是期望调用数或质量配额；达到上限失败关闭，不删除调查、证据、
Citation 或独立 Review。

## Outcome and users

首要用户是理解或维护陌生工程的开发者。他在一个 Conversation 中自然追问、纠正、澄清、深入和总结，不选择模式、题型或内部代号。
主工程 Agent 使用 Application 密封的 Conversation Context 和 exact World Model Cognition，维护目标、假设与计划，并通过受控工具族提出
世界模型查询或源码 search/read；Source Broker 校验并编译提议，Retrieval Worker 只执行 exact-revision、allowlisted、read-only、audited
操作。

调查结束后 Application 密封 Question Evidence Package。Package 只有两个明确分区：`support/citation` 仅包含按 modality、Context、
Coverage 与 Support 校验通过的可采信条目，只有它们能支持肯定 Claim 和 Citation；`boundary/audit` 必须保留 Gap、Failure、Partial、
Conflict、Unknown、拒绝决定和资源收据，只能约束结论或支持 Limitation 的边界说明，不能支持肯定 Claim。seal 证明身份、完整性、来源和
版本，不证明内容为真。

主 Agent 在受控新上下文中只读当前 Turn 的密封 Package，自然综合为先结论、后必要解释的答案。fresh independent Reviewer 检查问题、
Context、Package 与答案，只返回绑定 Checklist/Claim/evidence class/need 的具体 Finding；Finding 回到主 Agent，由它决定在 Control Plane
约束下使用世界模型或源码工具补证，或基于原包重写。任何补证都形成新的 Ledger Revision、Package、Answer 和 Review identity，旧 Review
不能批准新包。旧 `Verification Investigation` 独立固定角色保留为兼容实现资产，不是目标 Agent 本体。页面以答案为主，内部 Ledger、操作、
调用和 Finding 折叠到开发者详情。

## Scope / non-goals

本轮范围是 loopback、普通用户无认证、一个可重复启动并支持 server-owned Conversation/Turn/Context、完整消息历史、“新对话”和语义
多轮追问/纠正/总结的统一工程 Chat Web、授权本地 Git exact revision、Java 工程、预构建 World Model，
以及源码、仓库文档、构建/运行配置和测试的受控只读调查。Slice1 只做可体验的最小真实纵切；Slice2 做跨工程和工程化夯实；Slice3
正式验收。Slice1 的 Alpha 必须显示产品/工程版本、已知限制与请求级失败；一题失败不得终止服务或整轮。

不包括公网、Production Activation、团队权限、多用户隔离、远程仓库写入、任意 shell、工程修改、第二语言、跨仓库知识、跨重启长期
Memory、多 Agent/技能市场或同步知识发布。会话内工作状态是首版必需能力，不属于被延后的长期 Memory。严格 `WORLD_MODEL` Source-off
模式和显式 `DIRECT_INVESTIGATION` 保留，但不能成为默认 Chat 的静默 fallback。

## Adopted system IDs

新默认 Owner 是 `SYS-ADR-018` 与 `SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION`；它们组合 World Model、Conversation、主 Agent、
逐轮证据与独立 Review。`SYS-ADR-016` 和旧 Engineering Question Answering Contract 保留为历史/兼容边界。设计继续采用 Agentic/Evidence/World Model Answering、
Knowledge Update/Use、Response Control、Model Gateway、Capability Evaluation、Source Artifact、Security 和 Local Browser 等 Owner。
`FINDING-010-002` 保留旧单轮 Investigation/Broker/Ledger 设计的历史来源；PDR-004 之后的 current 语义只由 ADR-018、
Engineering Conversation Contract 和本 Proposal 的 A1—A6 组合定义。旧固定角色、`@3` 和双审只是兼容资产，不是待恢复的 current 流程。

## Development slices and dependencies

1. `SLICE-001`：价值方向 Gate 与最小主工程 Agent 多轮 Chat。现有分层归因、认知资格、通用备用路线准入和 Web Access 证据直接复用；当前
   唯一动作只冻结三条异质题、四路 runner、独立源码事实账本、盲评量表和 exact identities，外部调用与产品代码变更均为 0。冻结 PASS 后
   先运行 首选配置四路方向质量 Gate；首选配置 PASS 直接进最小 Web，首选配置 FAIL 进归因，只有 首选配置 INVALID 才能在零外部、零人工请求、零 dispatch
   Refreeze PASS 后运行统一 备用配置四路 Gate。实际 Quality Route PASS 后才允许把既有 clean candidate 接成一条最小语义链。持久恢复、
   多 Agent 和 full regression 不阻塞。
2. `SLICE-002`：跨工程和工程化夯实。Chat Alpha `CONTINUE` 且重新授权后，完成跨重启 Conversation 恢复、第二工程、冲突/去重/性能/
   安全/完整回归、early hidden、四路复验、World Model 成本/复用周期和异步知识沉淀。
3. `SLICE-003`：正式验收。再次 `CONTINUE` 和重新授权后冻结产品，执行最终隐藏多轮对话、现场 Conversation、四路价值、安全和 Reflection。

每段都使用同一个 product-owned Web；首段方向体验早于大规模加固，不能由 validation-only 入口替代。

## Risks and unknowns

- 主工程 Agent 可能无界探索或过早结束；Application/Broker policy、Work State/Ledger progress 和安全上限必须机械控制，超限失败关闭。
- World Model 与 Source 可能冲突；包必须保留各自 Context/revision/provenance/coverage，不能静默选取。
- README、注释、测试和源码都是不可信输入；内容不能改变 system instruction、权限、路径、Provider 或 disclosure。
- Reviewer 的 Finding 可能夹带可执行路径或命令；它只能绑定 Checklist/Claim/evidence class/need，不能规划或执行操作。补证规划由主 Agent
  在独立审核之后重新完成，仍须由 Application/Broker 逐步校验编译；Reviewer 不取得工具权威。
- 自然答案可能掩盖错误；Citation 必须逐结论支持，未知不能扩张为不存在或完整性结论。
- 架构比直接提交相关证据或仅源码 Agent 更复杂；必须从 Slice1 的四路 Gate 起证明目标系统严格质量和非 locator 的世界模型贡献。当前
  freeze 动作必须生成新 protocol、rubric 和 identity digest；不得复用旧 `6ca47f7d…` 三路收据或把旧结果升级为 PASS。
- Provider route 必须保持 logical question 与 provider attempt 双层身份；透明 fallback 若复用 primary Ledger/Package、允许 late response
  覆盖，或把 Application/Source/Security failure 误分类成模型失败，将破坏证据与安全边界。当前实现缺口必须在一题 smoke 前闭合。
- Conversation Context 若把 prior Answer、用户陈述或 Provider hidden memory 当成事实，会污染逐轮证据；新对话若继承旧 referent、Ledger、
  Package 或 Provider 会话会造成跨对话泄漏。Application 必须密封 context projection，模糊指代 dispatch 前澄清。
- 主 Agent 若被重新压回固定多角色内容流水线，或为了“更 Agentic”取得直接 Repository/Shell/network/write 权限，均违反双核心边界。

## Verification and acceptance

Slice1 的历史 deterministic/Web 证据保留但不证明方向或 Chat。PDR-005 的 `V-LAYER-ATTRIBUTION-001` 和
`V-COGNITION-ELIGIBILITY-001` 已分别由 `ITER-010-RESULT-V-LAYER-ATTRIBUTION-001` 与
`ITER-010-RESULT-V-COGNITION-ELIGIBILITY-001` 以外部调用 0 PASS；通用 `V-FALLBACK-ROUTE-ADMISSION-001`（由当前配置插件的密封收据支持）与 `V-ALPHA-ACCESS-001` 也直接复用。当前先运行
`V-DIRECTION-FREEZE-001`，它只允许建立四路 runner、三题清单、独立源码事实账本、盲评量表、execution-profile refs、Agent/Codex identities 与结果 Schema，
外部调用和产品代码改动为 0。冻结 PASS 后才使用 preferred execution profile 运行 `V-DIRECTION-QUALITY-001`；任何模型答案都不是真值，事实只来自独立
exact-source ledger。目标系统必须满足绝对质量门、逐题不输三条基线、总体严格超过 current Codex，并有至少一项非 locator 世界模型
贡献；平局即 FAIL。Preferred Quality INVALID 只进入 FallbackRefreeze；其 PASS 收据必须证明外部调用、人工授权请求和 Provider dispatch 均为
0，并从可信父树绑定首选配置 INVALID Result seal、Freeze root input set、备用执行配置与准入策略插件。随后 Fallback Quality 复用同一 Case；
两条路线 Quality Result 最多一个 PASS，备用路线 INVALID 自环失败关闭。

只有该方向 Gate PASS，才运行 `V-TIMEBOX-CHAT-001/V-CHAT-EXPERIENCE-001/V-CHAT-001`，验证一条至少三 Turn 的真实语义链、两个未参与修复的
异质问题和新对话负测；每轮进入 `V-CHAT-QUALITY-001`，要求重大错误与 Reviewer 重大漏判均为 0、重要结论有 Citation、纠正真实更新
Context、prior Answer 不作事实且新对话不泄漏。完整五轮套件、full regression 和 hardening 只有用户在该体验后决定 `CONTINUE` 才解锁。

Slice2 运行第二工程 5+2 early canary、四路同题复验、建模成本/复用周期、性能、安全和完整回归。比较分为两类：对 current Codex 的
外部产品比较保留其实际客户端、model、reasoning、tools 和权限，只固定 exact revision、Conversation 脚本、可比较输出和 rubric；Codex 不是 Oracle 或裁判。World Model
因果消融只比较 same-agent source-only 与 same-agent full-cognition + source，两臂固定同一主 Agent/model/tool/budget/cache/Reviewer。完整认知随后必须相对 source-only 同链达到新收据预提交的质量或非 locator 调查成本增益。source-only control 失败可以证明质量增益，但不得
降低完整认知门槛；Slice3 在最终两个隐藏工程 10+2 与两条现场题
复验。最终要求 answerable 10/10、boundary 2/2、重大错误 0、逐结论不退步、消融/value Gate PASS、每项 Source 操作与 Ledger 对账，
主 Agent 与 Reviewer 直接 Source/FS/Shell/network/write 权限为 0，Production Activation=`NOT_EXECUTED`。

## Authorization decision

**ACCEPTED PROPOSAL / PDR-009 CURRENT PLAN LOCK / ITERATION AUTHORIZED / SLICE1 ACTION-LEVEL CODING INPUT。** PDR-008/007/006 继续提供
公开工程 authority、当前备用 profile 的配置插件准入和持续执行边界，但不能改变 PDR-009 的唯一下一动作。收据 `d3b60bda…` 只记录重制计划和文档；用户随后以
`codex-user-message:sha256:585f02c4edcf25502b40f880c17a7bdf7f1af71044cd8d1bbe97b055a735ee9e`（`2026-08-21T09:18:34Z`）
接受本 Proposal 与 Readiness，并曾授权 `ITER-010-SLICE-001` 成为产品编码输入。该历史授权基于已冻结的 planning commit
`01dcfe2233625dfaa021495850fb18ae1323063b` / tree `8e364ae854bfaa48580ab080a3e0d9c9c43c3d6f`。

该历史授权及后续派生 grant 已消费或停止。PDR-001 只授权项目决定纠正；用户随后以
`codex-user-message:sha256:32b298dedd814a93d8dc0a086776090342f14856f032283fddb453061c1efeb5`（`2026-08-24T02:55:16Z`）
明确要求继续开发，恢复同一个 Slice1 的产品/System 编码与本地确定性测试。它不复用 credential、Provider/model、动态源码披露或 live
Web/browser grant；这些仍须在新 product freeze 后按 exact Session Authority 另行授权。hidden、`SLICE-002/003` 与 Production
Activation 继续未授权。此前 `1b327024… + 5cdb7000…` 仍只绑定被取代的一次性检索/先封包设计。旧三路方向信号及“ITER-012 才严格超过
Codex”的例外均已被 PDR-009 取代，不能作为 current 开发输入。

上述授权是历史事实。PDR-004 的文档同步收据
`codex-user-message:sha256:d8239ea7da3d767caa5d0a091726849d1a644e45d44f631d36f3028787093a90` 不授权代码，已暂停旧
Slice1 编码权威。用户现以
`codex-user-message:sha256:f76ba3e864f6612b3dcc14c83392ec54db686fdb5653e408fa300785b97ceef5`（`2026-08-25T05:06:07Z`）
接受基于 planning commit `b66ff9f058b92cebd78d5644ffef042753567b4d` / tree
`30e437eea83e048e3fb59ddd90a8d1b76242d82c` 的刷新 Readiness，并授权 `ITER-010-SLICE-001` 产品/System 编码与本地确定性验证。
该收据不授权 Provider/model、动态源码披露、live browser、hidden、Slice2/3 或 Production；后续 `7256a886…` 仅补充 exact
`cf2883b…` 的 `V-ALPHA-ACCESS-001` 本机 listener/browser 权限并已消费。再后的
`local-user-message-utf8:sha256:15a8f8100f8cb6ac333edf85166cf572bb67a5e69d5a731a75c574d36fa5a4e4` 已授权一次受限
direction canary，当前等待 clean-candidate exact freeze 和覆盖校验；它不扩大为其他外部执行权限。

以上逐 run grant 是 PDR-008 前的历史事实，不能驱动 current successor 再次申请。PDR-005/006/007 分别保留方向、连续执行和当前备用
profile 的配置插件准入规则；PDR-008 以 `PUBLIC_OSS_EVALUATION_STANDING_AUTHORITY@1` 覆盖 current mall 评测，只有真正 scope delta 才申请最小 delta。
开发可在全新的“开发 ITER-010”对话中直接接手；换对话、clean product successor、run/Turn/dispatch identity 更新不要求重新授权。

用户又以 `local-user-message-utf8:sha256:612341017bef3d98db372608d22b0d57744a96883e23dd51a6552c13da183989` 要求完全纠正并严格遵循
计划，并以 `local-user-message-utf8:sha256:63962a3f18667dd3727dd76d72c45ae8224e40a06be2d8c12622aca3a4ef0ae5` 拒绝仅靠文字约束。
因此 current coding authority 被收窄到 Manifest `plan_execution_control.current_action`：`ITER-010-ACTION-DIRECTION-FREEZE-001`。
本动作只能改白名单 runner/test/Result/Finding 和迁移游标文件，外部调用为 0；dirty v7、产品代码、Prompt/Reviewer、Web、hardening、
full regression 与 Provider dispatch 均锁定。只有绑定 Result 的 PASS/FAIL/INVALID 能按预声明 transition 改变下一动作；目标分支不得通过
同时修改计划来扩大 base-tree 权限。
