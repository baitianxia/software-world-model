---
id: ITER-010-PROPOSAL
kind: iteration-proposal
status: accepted
authority: project-proposal
owners: [product, project, architecture, engineering, quality]
depends_on: [SYS-PRODUCT-SUCCESS, ROADMAP-M-002, ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST, ITER-006-RESULT-ACCEPTANCE, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, SYS-ADR-013, SYS-ADR-014, SYS-ADR-015, SYS-ADR-016, SYS-ADR-017, SYS-ADR-018, SYS-CONTRACT-AI-CAPABILITY-EVALUATION, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-QUALITY-SECURITY, SYS-OPS-LOCAL-BROWSER]
code: []
tests: []
iteration: ITER-010
coding_input: false
---

# ITER-010 Proposal：软件世界模型与主工程 Agent 驱动的多轮工程 Chat

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

本 Proposal 的目标与核心认知—调查—证据架构不变，但执行顺序修订如下：不再另起 ITER-011，也不把另一组冻结 1+1 问题当作可体验版本；
Slice1 首先把现有链恢复为可重复启动、同会话连续自由提问的 Web Alpha，然后在同轮按真实问题修复答案与审核的通用根因。单题失败只
判该 Request 失败；只有多类问题共同证明核心架构无法有界修复，或用户实际体验后明确拒绝，才触发架构转向。

该 PDR 只修订项目方向；其接受时 Slice1 为 `paused / coding_input=false`，旧授权与所有 live grant 已消费。后续 `32b298de…` 收据已恢复
编码，外部调用仍须在新 product freeze 后另行授权。

## PDR-003 amendment：体验优先恢复与透明模型路由

用户以 `codex-user-message:sha256:47a3421d48fe3f36000e45696ea9c41b49b7e362332bc724306c10ca42fe119c`
指出 ITER-010 约 14 小时仍没有新的可体验结果，并消耗了大量 DeepSeek token。[PDR-003](decisions/PDR-003-experience-first-provider-cost-recovery.md)
因此再次收窄 Slice1 执行顺序：Access 与答案 Quality 分开，先交明确标记“质量未验收”的可操作 Web；PDR-003 原有单题 smoke 只保留为
Provider 前本地或 Mock Access 检查，不能充当 PDR-004 的 Chat canary。首次体验前停止 Answer/Review Prompt、Schema、Contract 扩张和
full regression。

Experience policy 使用 60/180/240 分钟检查点。历史经过已经越过 hard stop，当前恢复只允许页面启动、安全、失败真实性、一次必要资格和
最多一次 Provider 前本地或 Mock Access smoke。首个发生 Provider dispatch 的方向 canary 必须是五轮 Conversation；每个 sealed Turn 到达任一外部 dispatch 就计一次 live attempt；同 failure signature 最多一个 successor，
连续两次没有用户可见增量即停止外部重跑。

失败处理从 `answer-chasing` 改为 root-cause-first：按 Source truth 到 Web 的固定责任链定位最早偏差，先提出可证伪假设；没有假设和本地
最小复现不得改 Prompt、Schema 或 Contract。修复需先通过最小复现与两个未参与修复的相邻案例，随后运行一个有界五轮 Conversation 作为
首次方向 live canary；每个到达 Provider dispatch 的 Turn 分别计 live attempt。同 signature
修一次仍复现即停止规则累积并做架构职责评审。首次体验前只跑 targeted impact/startup/safety，full regression 仅在 Alpha `CONTINUE`
后的 hardening 与正式验收前执行。

模型 route 按 ADR-017 对用户透明：Session 预授权 `VOLCENGINE_ARK → DEEPSEEK`。用户只提交一次 logical question；Ark attempt 仅在密封
terminal、无 authorized answer 且属于允许的 Provider/model reason 时，才自动启动一次独立 DeepSeek attempt。Fallback 从原 Turn、该 Turn 密封的 exact
Cognition 以及与当前 Turn 有关的 sealed Conversation Context 重跑完整链，不复用 Ark 中间态；同 Provider retry 为 0，late Ark 结果 quarantine。当前实现尚未证明该 route，必须先以最小
产品变化闭合，不能把文档目标写成运行 PASS。

## PDR-004 amendment：主工程 Agent 与真正多轮 Chat

`FINDING-010-093/094` 证明“固定多角色内容流水线 + 同一 Runtime Session 连续独立提问”不是目标产品。PDR-004 因此在不废弃既有
World Model、Broker/Worker、Evidence、Citation、Review、Web 和 Provider 资产的前提下，冻结两个核心：软件世界模型提供持久、版本化、
可验证的软件认知；主工程 Agent 持续拥有用户目标、假设、子任务、计划修订、上下文选择、工具选择、观察解释、重规划、完成判断和答案综合。

默认交互改为 server-owned Conversation/Turn/Context 的语义多轮 Chat。每轮 Request、Evidence、Answer、Review 和 Delivery 保持独立；
Conversation Context 只承载确认目标/约束、指代实体、开放问题、已审核结论 reference、争议或被取代结论及 exact provenance，不把用户陈述、
上一轮答案或 Provider 隐藏记忆变成源码事实。模糊指代必须在 Source/Provider dispatch 前澄清；新 Conversation 不继承旧 working state 或
逐轮证据。

首个 Chat canary 是一段五轮连续对话，而不是三道互不相关问题；另加“新对话后省略指代必须澄清”的泄漏负测。三臂更新为 same-agent
source-only、same-agent full World Model cognition + source、current Codex external baseline。旧编码权威曾由 PDR-004 暂停，`d8239ea7…`
只授权文档同步；用户现以 `f76ba3e8…` 接受刷新 Readiness 并授权 Slice1 产品/System 代码和本地确定性验证。新架构仍保持
`NOT_IMPLEMENTED / NOT_QUALIFIED / NOT_LIVE`，外部调用与 live 仍须另行冻结和授权。PDR-003 的时间盒、根因、测试后置、Provider 和成本
规则全部继续有效。

## Product-goal alignment and cumulative delta

- MVP target：`SYS-PRODUCT-SUCCESS`。目标是“准确的软件世界模型 + 优秀的主工程 Agent”共同支撑多轮工程 Chat，不另立绕过世界模型的
  源码 Agent 产品，也不建设通用自治 Agent 平台。
- Capability path：`ROADMAP-M-002 / step-1-java-result-driven-world-model-investigation`。World Model 负责持久外部认知；提问期 Source 调查
  用于核实、补充或纠正本题认知，不取代问题前建模和跨问题复用。
- Accepted predecessor：`ITER-006-RESULT-ACCEPTANCE` 提供 exact Snapshot、声明/静态 `CALLS`、Citation 和本机 Web 窄基线；ITER-009
  提供方向反证而非 Acceptance。
- Current gap：系统能执行单轮自适应调查，却没有持续拥有对话目标和计划的主工程 Agent；同一 Session 的独立问题没有追问、指代、纠正、
  总结或新对话隔离语义。
- Cumulative integration：同一问题链使用 exact World Model Cognition Context 与本题 source/doc/config/test 调查证据，不建立平行答案。
- Earliest Web checkpoint：历史单题和 4+1 题只证明受控单轮运行。新首交付在固定 loopback、工程和 exact revision 下显示完整消息历史与
  “新对话”，由主 Agent 完成五轮追问/纠正/深入/总结；一轮失败不关闭 Conversation。逐轮 exact revision、只读、不可信来源、Citation、
  独立 Review 和新对话隔离不可延后。
- Direction signal：用户先取得可操作 Chat，五轮 canary 与新对话泄漏负测通过后，Slice1 立即以小样本运行 same-agent source-only、
  same-agent full-cognition + source、current Codex 三臂，作为不阻塞页面交付的方向信号；Codex 不是 Oracle。
- Later proof：只有持续 Alpha 经实际体验 `CONTINUE` 后，Slice2 才做持久恢复、复杂冲突/去重/异常矩阵、第二工程、性能、安全、完整回归、early hidden
  和三臂复验；Slice3 执行最终两个未见工程 10 answerable + 2 boundary、两条现场题和最终复验。PDR-002 的严格超过 Codex 强制仍从 ITER-012 起。
- End capability：普通用户无需认证即可在本机 Web 围绕用途、架构、运行、流程、配置、故障、影响和实现细节持续 Chat，能够追问、纠正、
  澄清、深入和总结，并逐轮获得直接、层级匹配、可核对 Citation 的答案或诚实 Limitation。
- Next gap：第二语言、跨仓库、大型工程性能、持续后台认知更新和非本机部署。
- Request fail：答案重大错误、物质遗漏、错误 Citation、审核漏判或资源熔断只使当前问题失败并进入同轮返工，不得冒充成功。
- Stop/redirect：世界模型被降级为手册/缓存；调查不是先前结果驱动；模型取得直接 Source 权限；任何题目/工程/关键词/符号/类/方法/
  fixture/Oracle 特判；Ledger/Package/Review 身份错配或安全边界失效；多个异质问题证明核心路径无法有界修复；用户在持续体验后明确转向或拒绝。

## Critical assumptions and falsification plan

| 假设 | 最早证据与反证 | 反证后的动作 |
|---|---|---|
| A1：软件世界模型保持为持久、版本化、可验证、可更新的软件外部认知，提问期 Source 调查只核实、补充或纠正本 Turn 认知 | Slice1 以 current System Owner、`V-CHAT-QUALITY-001` 和 `V-COMP-ALPHA-001` 先检查；Slice2/3 以 `V-COMP-EARLY-002/V-COMP-001` 复验。把 World Model 降级为手册、缓存、locator 集或 Source recall 门禁，或完整 Cognition 无可验证贡献，即反证 | REDIRECT 认知与问答边界；不用命名掩盖概念漂移 |
| A2：主工程 Agent 能持续维护目标、假设、子任务和计划，依据每次观察选择 World Model/Source 受控工具并重规划，不取得直接权限 | Slice1 的 `V-CHAT-001/V-CHAT-QUALITY-001`；若仍是预先固定的角色/操作清单、需要特判，或 Agent 必须直接访问 repository/FS/Shell/network/credential/write 才能工作，即反证 | REDIRECT Agent/tool 合同；保留 Application/Broker/Worker 的 exact-version、allowlist、只读、证据身份、预算和审计责任 |
| A3：每个 Turn 的 Evidence Package、自然答案与 fresh independent Review 同时保证直接答案、Citation、失败关闭和可返工性，Reviewer Finding 只回到主 Agent | Slice1 的 `V-CHAT-QUALITY-001`。若 seal 被当作真值、prior Answer/Review 取得证据权威、Reviewer 直接规划/执行工具，或 Finding 绕过主 Agent 进入固定补证角色，即反证 | 修正 Agent—Evidence—Review 首个系统性偏差；不减少证据或独立审核换取交付 |
| A4：相同 Conversation—主 Agent—受控工具—逐 Turn Evidence/Review 协议能跨第二工程、来源组合和复杂失败泛化 | Slice2 的 `V-GENERAL-002/V-RERETRIEVE-002/V-CANARY-002/V-XD-002`；新工程或新表达必须新增项目/问题/关键词/符号/类/方法/fixture/Oracle 分支，或主 Agent 的补证与重规划不收敛，即反证 | REDIRECT 通用 Context、Agent/tool、Broker 或 Review 合同；烧毁已披露输入并保留 Result |
| A5：产品外部比较与 World Model 因果消融必须分开；current Codex 保留其真实客户端、model、reasoning、tools 和权限，只有系统的 source-only 与 full-cognition 两臂使用同一主 Agent/model/tool/budget/cache/Reviewer | Slice1 的 `V-COMP-ALPHA-001` 只产出方向信号；Slice2/3 的 `V-COMP-EARLY-002/V-COMP-001` 分别报告外部产品对比和系统两臂消融。把 Codex 当 Oracle/裁判，为取得表面“同配置”而削弱其实际能力，或两个系统臂不同 Agent/model/budget/cache，即反证 | REDIRECT 比较协议；完整披露能力差异，不用效率抵消质量失败 |
| A6：产品具有真正语义多轮 Conversation，而不是同 Session 的独立问答 | Slice1 的 `V-CHAT-EXPERIENCE-001/V-CHAT-001/V-CHAT-QUALITY-001`。五轮必须验证追问指代、用户纠正、进一步区分/深入、基于 current Context 总结、逐 Turn 证据与新 Conversation 隔离；任一缺失即反证 | REWORK Conversation/Work State 而不将单 Turn 失败自动升级为整轮 REDIRECT |

Slice1 验证 A1—A3/A6，并以 `V-COMP-ALPHA-001` 提前暴露 A4/A5；Slice2 累积验证 A1—A4/A6 并提前复验 A5；Slice3 最终覆盖 A1—A6。
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

1. `SLICE-001`：主工程 Agent 多轮 Chat Alpha。复用认知、Broker/Worker、逐轮 Ledger/Package、Answer/Review、Citation、Web 和 PDR-003
   Provider route；先形成消息历史/新对话 Access，再以一个五轮 Conversation 作为首次 live canary并执行泄漏负测；随后运行不阻塞页面交付的
   小样本三臂方向比较。持久恢复、多 Agent 和 full regression 不阻塞。
2. `SLICE-002`：跨工程和工程化夯实。Chat Alpha `CONTINUE` 且重新授权后，完成跨重启 Conversation 恢复、第二工程、冲突/去重/性能/
   安全/完整回归、early hidden、Codex/source-only/full-cognition 三臂复验、World Model 成本/复用周期和异步知识沉淀。
3. `SLICE-003`：正式验收。再次 `CONTINUE` 和重新授权后冻结产品，执行最终隐藏多轮对话、现场 Conversation、三臂、价值、安全和 Reflection。

每段都使用同一个 product-owned Web；首段方向体验早于大规模加固，不能由 validation-only 入口替代。

## Risks and unknowns

- 主工程 Agent 可能无界探索或过早结束；Application/Broker policy、Work State/Ledger progress 和安全上限必须机械控制，超限失败关闭。
- World Model 与 Source 可能冲突；包必须保留各自 Context/revision/provenance/coverage，不能静默选取。
- README、注释、测试和源码都是不可信输入；内容不能改变 system instruction、权限、路径、Provider 或 disclosure。
- Reviewer 的 Finding 可能夹带可执行路径或命令；它只能绑定 Checklist/Claim/evidence class/need，不能规划或执行操作。补证规划由主 Agent
  在独立审核之后重新完成，仍须由 Application/Broker 逐步校验编译；Reviewer 不取得工具权威。
- 自然答案可能掩盖错误；Citation 必须逐结论支持，未知不能扩张为不存在或完整性结论。
- 架构比直接源码 Agent 更复杂；最终必须用完整认知、locator-only/empty 同链和成熟源码 Agent 三臂同题消融证明复杂度合理。新增消融的
  protocol、阈值和 digest 当前只是 proposed，不能复用旧 `6ca47f7d…` 收据，Slice2 前必须取得新的用户冻结收据。
- Provider route 必须保持 logical question 与 provider attempt 双层身份；透明 fallback 若复用 primary Ledger/Package、允许 late response
  覆盖，或把 Application/Source/Security failure 误分类成模型失败，将破坏证据与安全边界。当前实现缺口必须在一题 smoke 前闭合。
- Conversation Context 若把 prior Answer、用户陈述或 Provider hidden memory 当成事实，会污染逐轮证据；新对话若继承旧 referent、Ledger、
  Package 或 Provider 会话会造成跨对话泄漏。Application 必须密封 context projection，模糊指代 dispatch 前澄清。
- 主 Agent 若被重新压回固定多角色内容流水线，或为了“更 Agentic”取得直接 Repository/Shell/network/write 权限，均违反双核心边界。

## Verification and acceptance

Slice1 的历史 deterministic/Web 证据保留但不证明 Chat。PDR-004 返工以从未执行的 `V-ALPHA-ACCESS-001` PDR-004 修订版与新
`V-TIMEBOX-CHAT-001/V-CHAT-EXPERIENCE-001` 证明启动、消息历史、新对话、Turn 故障隔离和 recovery 纪律；Access 不能替代质量。首次方向 live canary 本身就是
`V-CHAT-001` 的五轮脚本和新对话负测，同时每轮进入 `V-CHAT-QUALITY-001`：重大错误为 0、重要结论有 Citation、纠正真实更新 context、prior Answer 不作事实、新对话不泄漏。用户在真实
Chat 后先取得可操作体验，再运行 `V-COMP-ALPHA-001` 小样本三臂方向比较并裁决方向。

Slice2 运行第二工程 5+2 early canary、三臂同题复验、建模成本/复用周期、性能、安全和完整回归。比较分为两类：对 current Codex 的
外部产品比较保留其实际客户端、model、reasoning、tools 和权限，只固定 exact revision、Conversation 脚本、可比较输出和 rubric；Codex 不是 Oracle 或裁判。World Model
因果消融只比较 same-agent source-only 与 same-agent full-cognition + source，两臂固定同一主 Agent/model/tool/budget/cache/Reviewer。完整认知随后必须相对 source-only 同链达到新收据预提交的质量或非 locator 调查成本增益。source-only control 失败可以证明质量增益，但不得
降低完整认知门槛；Slice3 在最终两个隐藏工程 10+2 与两条现场题
复验。最终要求 answerable 10/10、boundary 2/2、重大错误 0、逐结论不退步、消融/value Gate PASS、每项 Source 操作与 Ledger 对账，
主 Agent 与 Reviewer 直接 Source/FS/Shell/network/write 权限为 0，Production Activation=`NOT_EXECUTED`。

## Authorization decision

**ACCEPTED PROPOSAL / PDR-004 REVISION / ITERATION AUTHORIZED / SLICE1 CODING INPUT。** 收据 `d3b60bda…` 只记录重制计划和文档；用户随后以
`codex-user-message:sha256:585f02c4edcf25502b40f880c17a7bdf7f1af71044cd8d1bbe97b055a735ee9e`（`2026-08-21T09:18:34Z`）
接受本 Proposal 与 Readiness，并曾授权 `ITER-010-SLICE-001` 成为产品编码输入。该历史授权基于已冻结的 planning commit
`01dcfe2233625dfaa021495850fb18ae1323063b` / tree `8e364ae854bfaa48580ab080a3e0d9c9c43c3d6f`。

该历史授权及后续派生 grant 已消费或停止。PDR-001 只授权项目决定纠正；用户随后以
`codex-user-message:sha256:32b298dedd814a93d8dc0a086776090342f14856f032283fddb453061c1efeb5`（`2026-08-24T02:55:16Z`）
明确要求继续开发，恢复同一个 Slice1 的产品/System 编码与本地确定性测试。它不复用 credential、Provider/model、动态源码披露或 live
Web/browser grant；这些仍须在新 product freeze 后按 exact Session Authority 另行授权。hidden、`SLICE-002/003` 与 Production
Activation 继续未授权。此前 `1b327024… + 5cdb7000…` 仍只绑定被取代的一次性检索/先封包设计。
Slice1 小样本三臂只需在新 Readiness 中冻结可比输入、三条 Arm 和方向性判读，不作为正式优越性 Gate；Slice2/3 严格消融的 exact protocol、
阈值和 digest 仍须在 Slice2 前由新的用户收据冻结。

上述授权是历史事实。PDR-004 的文档同步收据
`codex-user-message:sha256:d8239ea7da3d767caa5d0a091726849d1a644e45d44f631d36f3028787093a90` 不授权代码，已暂停旧
Slice1 编码权威。用户现以
`codex-user-message:sha256:f76ba3e864f6612b3dcc14c83392ec54db686fdb5653e408fa300785b97ceef5`（`2026-08-25T05:06:07Z`）
接受基于 planning commit `b66ff9f058b92cebd78d5644ffef042753567b4d` / tree
`30e437eea83e048e3fb59ddd90a8d1b76242d82c` 的刷新 Readiness，并授权 `ITER-010-SLICE-001` 产品/System 编码与本地确定性验证。
Provider/model、动态源码披露、live browser、hidden、Slice2/3 与 Production 仍未授权。
