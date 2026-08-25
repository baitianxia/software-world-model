---
id: ITER-010-PROPOSAL
kind: iteration-proposal
status: accepted
authority: project-proposal
owners: [product, project, architecture, engineering, quality]
depends_on: [SYS-PRODUCT-SUCCESS, ROADMAP-M-002, ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST, ITER-006-RESULT-ACCEPTANCE, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, SYS-ADR-013, SYS-ADR-014, SYS-ADR-015, SYS-ADR-016, SYS-CONTRACT-AI-CAPABILITY-EVALUATION, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-QUALITY-SECURITY, SYS-OPS-LOCAL-BROWSER]
code: []
tests: []
iteration: ITER-010
coding_input: false
---

# ITER-010 Proposal：世界模型认知引导的自适应工程问答

## Trigger and evidence

`ITER-009-RESULT-SLICE-001-STOP-REDIRECT` 证明真实本机 Web、精确版本、独立审核、Limitation 和 Citation 已能运行，也证明默认答案仍被
方法、分支、调用顺序和内部诊断主导，整体像代码走读。初版 ITER-010 因此引入提问期受控回源，但进一步讨论指出两处架构偏差：

- 把 World Model 简化为“工程手册、地图、检索提示”缩窄了它从项目开始就稳定存在的概念；
- 在回答前一次性生成检索计划和 Evidence Package，不能让大模型根据刚读到的结果继续像高级工程师一样调查。

软件世界模型的定义不变：它是软件在 exact Context、Scope、Schema、Snapshot 上持久、版本化、可验证、可更新的外部认知模型，表达
实体、关系、行为、约束、状态、证据、覆盖和未知边界，为大模型提供稳定系统认知。手册、地图和检索入口只是这种认知面向人或任务的
投影。需要重构的是默认工程问答主链：Investigation LLM 主导自适应调查，Source Broker 和隔离 Retrieval Worker 控制实际只读访问，
调查结束后才密封 Question Evidence Package；Answer 只读包生成答案，Reviewer 可独立指出具体证据缺口并通过 Application/Broker
触发后继 Ledger、Package、Answer 和 Review。

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
因此再次收窄 Slice1 执行顺序：Access 与答案 Quality 分开，先交明确标记“质量未验收”的可操作 Web；一题 canary 未通过时不运行三题集，
首次体验前停止 Answer/Review Prompt、Schema、Contract 扩张和 full regression。

Experience policy 使用 60/180/240 分钟检查点。历史经过已经越过 hard stop，当前恢复只允许页面启动、安全、失败真实性、一次必要资格和
一次 live smoke。一个 sealed 版本的 question run 到达任一外部 dispatch 就计一次 live attempt；同 failure signature 最多一个 successor，
连续两次没有用户可见增量即停止外部重跑。

失败处理从 `answer-chasing` 改为 root-cause-first：按 Source truth 到 Web 的固定责任链定位最早偏差，先提出可证伪假设；没有假设和本地
最小复现不得改 Prompt、Schema 或 Contract。修复需先通过最小复现与两个未参与修复的相邻案例，随后只跑一题 live canary；同 signature
修一次仍复现即停止规则累积并做架构职责评审。首次体验前只跑 targeted impact/startup/safety，full regression 仅在 Alpha `CONTINUE`
后的 hardening 与正式验收前执行。

模型 route 按 ADR-017 对用户透明：Session 预授权 `VOLCENGINE_ARK → DEEPSEEK`。用户只提交一次 logical question；Ark attempt 仅在密封
terminal、无 authorized answer 且属于允许的 Provider/model reason 时，才自动启动一次独立 DeepSeek attempt。Fallback 从原问题与 exact
Cognition 重跑完整链，不复用 Ark 中间态；同 Provider retry 为 0，late Ark 结果 quarantine。当前实现尚未证明该 route，必须先以最小
产品变化闭合，不能把文档目标写成运行 PASS。

## Product-goal alignment and cumulative delta

- MVP target：`SYS-PRODUCT-SUCCESS`。目标仍是基于预构建软件世界模型的通用工程问答，不另立源码 Agent 产品。
- Capability path：`ROADMAP-M-002 / step-1-java-result-driven-world-model-investigation`。World Model 负责持久外部认知；提问期 Source 调查
  用于核实、补充或纠正本题认知，不取代问题前建模和跨问题复用。
- Accepted predecessor：`ITER-006-RESULT-ACCEPTANCE` 提供 exact Snapshot、声明/静态 `CALLS`、Citation 和本机 Web 窄基线；ITER-009
  提供方向反证而非 Acceptance。
- Current gap：系统能展示代码行为，但不能按用户目标自适应调查并组织工程答案；一次性证据准备也可能过早限制 Answer 和 Review。
- Cumulative integration：同一问题链使用 exact World Model Cognition Context 与本题 source/doc/config/test 调查证据，不建立平行答案。
- Earliest Web checkpoint：历史单题和 4+1 题检查点已执行，但只证明受控运行，不是持续体验。返工后的首个交付是在固定 loopback、工程和
  exact revision 下可重复启动并连续自由提问的 Web Alpha；一次请求失败不关闭服务。原失败题加至少两个相邻或异质问题用于通用回归，
  exact revision、只读、不可信来源、逐结论 Citation 和独立 Review 不可延后。
- Later proof：只有持续 Alpha 经实际体验 `CONTINUE` 后，Slice2 才做持久恢复、复杂冲突/去重/异常矩阵、第二工程、性能、安全、完整回归、early hidden
  和三臂同题认知消融；Slice3 执行最终两个未见工程 10 answerable + 2 boundary、两条现场题和最终消融。
- End capability：普通用户无需认证即可在本机 Web 询问用途、架构、运行、业务流程、配置、故障、影响和实现细节，获得直接、层级匹配、
  可核对 Citation 的答案或诚实 Limitation。
- Next gap：第二语言、跨仓库、大型工程性能、持续后台认知更新和非本机部署。
- Request fail：答案重大错误、物质遗漏、错误 Citation、审核漏判或资源熔断只使当前问题失败并进入同轮返工，不得冒充成功。
- Stop/redirect：世界模型被降级为手册/缓存；调查不是先前结果驱动；模型取得直接 Source 权限；任何题目/工程/关键词/符号/类/方法/
  fixture/Oracle 特判；Ledger/Package/Review 身份错配或安全边界失效；多个异质问题证明核心路径无法有界修复；用户在持续体验后明确转向或拒绝。

## Critical assumptions and falsification plan

| 假设 | 最早证据与反证 | 反证后的动作 |
|---|---|---|
| A1：保持软件世界模型作为持久、版本化外部认知而非手册或缓存，同时可让提问期 Source 调查核实、补充或纠正本题认知，并能证明完整认知不只是 locator 装饰 | Slice1 的 V-ARCH-001、V-COGNITION-001、V-XD-001 先验证职责；Slice2/3 的三臂同题 V-COMP-EARLY-002/V-COMP-001 比较完整认知、locator-only/empty 同链和成熟源码 Agent。若实现把 World Model 只当检索提示、把命中当回源门禁、用直接源码 Agent 取代问题前认知，或完整认知无预提交质量/非 locator 调查成本增益，则反证 | REDIRECT 认知与问答边界；停止编码，不用命名掩盖概念漂移 |
| A2：独立 Investigation LLM 可以依据不可变原问题、exact World Model Cognition Context 和先前 Ledger 结果自适应提出下一步，而 Source Broker/Worker 能在不授予模型直接权限的情况下执行 | Slice1 的 V-QINTENT-001、V-INVESTIGATE-001、V-BROKER-001；若调查仍是一次性固定计划、需要题目/工程特判，或模型必须直接访问文件系统/Shell/网络才能工作，则反证 | REDIRECT 调查协议或 Broker 抽象；拒绝特判和越权方案 |
| A3：调查后密封、包内 Answer 和 Reviewer 独立补证可以同时保证直接答案、正确 Citation、失败关闭与真实首版体验 | Slice1 的 V-LEDGER-001、V-ANSWER-001、V-REVIEW-001、V-LIMIT-001、V-PREVIEW-001；若先封包限制调查、seal 被当作真值、旧 Review 批准新包、补证不能形成完整新链或答案仍是代码走读，则反证 | 停止体验；修正 Ledger/Package/Answer/Review 首个系统性偏差，不减少检查换取交付 |
| A4：相同认知—调查—Broker—Ledger—Package 协议能跨第二工程、来源组合和复杂失败模式泛化，不依赖问题、项目、关键词、符号、类、方法、fixture 或 Oracle 路由 | Slice2 的 V-GENERAL-002、V-RERETRIEVE-002、V-CANARY-002、V-XD-002；新工程或新表达必须新增特殊分支，或复杂补证不收敛即反证 | REDIRECT 通用表示、Broker policy、调查或审核合同；烧毁已披露输入并保留 Result |
| A5：在不因调用次数裁剪调查或审核质量的前提下，完整认知与成熟源码 Agent 先通过零重大错误、boundary 正确且完整认知逐结论不退步的质量门；再以 locator-only/empty 同链为消融 control，证明完整认知有预提交质量或非 locator 调查成本增益，并计入建模成本与复用周期 | Slice2 的 V-COMP-EARLY-002 提前验证，Slice3 的 V-COMP-001、V-HIDDEN-003 和现场题最终裁决；三臂固定相同 revision/model/questions/budget/cache/rubric。locator control 的质量失败可成为质量增益证据，但不能降低完整认知自身验收门；质量退步、成本遗漏或增益未达即反证 | REDIRECT 或 REJECT；不取消独立审核、不压缩证据清单、不把安全上限改成质量配额，也不隐藏 World Model 建模成本 |

Slice1 验证 A1—A3，并以 V-XD-001/V-SEC-001 提前暴露 A4/A5；Slice2 累积验证 A1—A4 并提前验证 A5；Slice3 最终覆盖 A1—A5。
资源、调用、文件、bytes 和 wall time 都是预先密封的安全上限，不是期望调用数或质量配额；达到上限失败关闭，不删除调查、证据、
Citation 或独立 Review。

## Outcome and users

首要用户是理解或维护陌生工程的开发者。他只提出自然问题，不选择模式、题型或内部代号。系统向独立 Investigation LLM 提供原问题和
exact World Model Cognition Context；模型根据 append-only Ledger 中的每一步结果提出下一项抽象 search/read/parse/finish。Source
Broker 校验并编译提议，Retrieval Worker 只执行 exact-revision、allowlisted、read-only、audited 操作。

调查结束后 Application 密封 Question Evidence Package。Package 只有两个明确分区：`support/citation` 仅包含按 modality、Context、
Coverage 与 Support 校验通过的可采信条目，只有它们能支持肯定 Claim 和 Citation；`boundary/audit` 必须保留 Gap、Failure、Partial、
Conflict、Unknown、拒绝决定和资源收据，只能约束结论或支持 Limitation 的边界说明，不能支持肯定 Claim。seal 证明身份、完整性、来源和
版本，不证明内容为真。

Answer 在新上下文中只读包，先给结论再给必要解释。Reviewer 在另一个新上下文中独立检查；需要补证时只能输出绑定 Checklist/Claim/
evidence class/need 的具体 Verification Request。合法请求启动新的 `Verification Investigation`：独立调查模型在全新上下文读取具体 gap、当前
Package 和 Ledger prefix，根据每步新 Result 自适应提出下一步，再经 Application/Broker/Worker 执行。它不回到初始 Investigation
LLM，也不继承 Reviewer 会话；补证后形成后继 Ledger Revision、Package、Answer 和 Review。页面以答案为主，内部 Ledger、操作、调用
和 Finding 折叠到开发者详情。

## Scope / non-goals

本轮范围是 loopback、普通用户无认证、一个可重复启动并在同一会话连续自由提问的统一 `ENGINEERING_QA` Web、授权本地 Git exact revision、Java 工程、预构建 World Model，
以及源码、仓库文档、构建/运行配置和测试的受控只读调查。Slice1 只做可体验的最小真实纵切；Slice2 做跨工程和工程化夯实；Slice3
正式验收。Slice1 的 Alpha 必须显示产品/工程版本、已知限制与请求级失败；一题失败不得终止服务或整轮。

不包括公网、Production Activation、团队权限、多用户隔离、远程仓库写入、任意 shell、工程修改、第二语言、跨仓库知识、长期 Memory
或同步知识发布。严格 `WORLD_MODEL` Source-off 模式和显式 `DIRECT_INVESTIGATION` 保留，但不能成为 ENGINEERING_QA 的静默 fallback。

## Adopted system IDs

设计继续采用 `SYS-ADR-016`、`SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING`、Agentic/Evidence/World Model Answering、
Knowledge Update/Use、Response Control、Model Gateway、Capability Evaluation、Source Artifact、Security 和 Local Browser 等 Owner。
`FINDING-010-002` 细化 World Model 定义、Investigation LLM、Source Broker、Retrieval Worker、Evidence Ledger、调查后密封和 Reviewer
独立补证。实现前 `V-ARCH-001` 必须复核 current System docs、Manifest schema 和治理门禁一致。

## Development slices and dependencies

1. `SLICE-001`：持续 Web Alpha 与答案质量返工。复用已实现的认知上下文、自适应调查、Broker/Worker、Ledger/Package、Answer/Review、
   Citation 与页面；首先按 PDR-003 闭合可启动 Access 和透明 Ark→DeepSeek route，只跑一题 canary。canary 通过后才在同一冻结版本回归
   原失败题和至少两个相邻或异质问题；否则回到本地诊断。持久恢复、第二工程、完整矩阵和 full regression 不阻塞首个持续体验。
2. `SLICE-002`：跨工程和工程化夯实。持续 Alpha 方向 `CONTINUE` 且重新授权后，完成持久恢复、第二工程、来源冲突、复杂多步补证、去重、性能、
   安全、资格、完整异常/回归、early hidden、三臂同题消融、World Model 建模成本/复用周期计量和异步知识沉淀。固定一轮补证不是长期
   协议；以预密封 revision/call/operation/bytes/wall-time/no-progress 高安全熔断控制。
3. `SLICE-003`：正式验收。再次 `CONTINUE` 和重新授权后冻结产品，执行最终 10+2、现场题、三臂消融、价值、安全和 Reflection。

每段都使用同一个 product-owned Web；首段方向体验早于大规模加固，不能由 validation-only 入口替代。

## Risks and unknowns

- Investigation LLM 可能无界探索或过早结束；Broker policy、Ledger progress 和安全上限必须机械控制，超限失败关闭。
- World Model 与 Source 可能冲突；包必须保留各自 Context/revision/provenance/coverage，不能静默选取。
- README、注释、测试和源码都是不可信输入；内容不能改变 system instruction、权限、路径、Provider 或 disclosure。
- Reviewer 的补证请求可能夹带可执行路径或命令；versioned Request 只能绑定 Checklist/Claim/evidence class/need，不能规划或执行操作。
  独立 Verification Investigation 在新上下文中多步提议，仍须由 Application/Broker 逐步校验编译，不能回到初始 Investigation LLM。
- 自然答案可能掩盖错误；Citation 必须逐结论支持，未知不能扩张为不存在或完整性结论。
- 架构比直接源码 Agent 更复杂；最终必须用完整认知、locator-only/empty 同链和成熟源码 Agent 三臂同题消融证明复杂度合理。新增消融的
  protocol、阈值和 digest 当前只是 proposed，不能复用旧 `6ca47f7d…` 收据，Slice2 前必须取得新的用户冻结收据。
- Provider route 必须保持 logical question 与 provider attempt 双层身份；透明 fallback 若复用 primary Ledger/Package、允许 late response
  覆盖，或把 Application/Source/Security failure 误分类成模型失败，将破坏证据与安全边界。当前实现缺口必须在一题 smoke 前闭合。

## Verification and acceptance

Slice1 的历史 deterministic/Web 证据保留；返工先以 `V-ALPHA-ACCESS-001/V-TIMEBOX-001` 证明持续启动、会话自由提问、请求隔离、
版本/限制展示和 recovery 纪律。Access 不要求答案 Quality PASS，也不能替代它。一题 canary 通过后，原失败题与至少两个相邻或异质
问题才进入 `V-ANSWER-REWORK-001`：重大错误为 0，重要结论有 Citation，失败只能显示准确 Limitation 或请求级 fail-close。用户在实际
持续体验后裁决方向。

Slice2 运行第二工程 5+2 early canary、三臂同题消融、建模成本/复用周期、性能、安全和完整回归。三个 Arm 固定相同 revision、model、
questions、模型与来源资源 budget、cache policy/state、rubric 和 evaluator；完整认知与成熟源码 Agent 的质量 Gate 先 PASS，完整认知
随后必须相对 locator-only/empty 同链达到新收据预提交的质量或非 locator 调查成本增益。locator control 失败可以证明质量增益，但不得
降低完整认知门槛；Slice3 在最终两个隐藏工程 10+2 与两条现场题
复验。最终要求 answerable 10/10、boundary 2/2、重大错误 0、逐结论不退步、消融/value Gate PASS、每项 Source 操作与 Ledger 对账，
Investigation/Verification Investigation/Answer/Reviewer 直接 Source/FS/Shell/network/write 权限为 0，Production Activation=`NOT_EXECUTED`。

## Authorization decision

**ACCEPTED PROPOSAL / CURRENT REWORK AUTHORIZED / SLICE1 CODING INPUT。** 收据 `d3b60bda…` 只记录重制计划和文档；用户随后以
`codex-user-message:sha256:585f02c4edcf25502b40f880c17a7bdf7f1af71044cd8d1bbe97b055a735ee9e`（`2026-08-21T09:18:34Z`）
接受本 Proposal 与 Readiness，并曾授权 `ITER-010-SLICE-001` 成为产品编码输入。该历史授权基于已冻结的 planning commit
`01dcfe2233625dfaa021495850fb18ae1323063b` / tree `8e364ae854bfaa48580ab080a3e0d9c9c43c3d6f`。

该历史授权及后续派生 grant 已消费或停止。PDR-001 只授权项目决定纠正；用户随后以
`codex-user-message:sha256:32b298dedd814a93d8dc0a086776090342f14856f032283fddb453061c1efeb5`（`2026-08-24T02:55:16Z`）
明确要求继续开发，恢复同一个 Slice1 的产品/System 编码与本地确定性测试。它不复用 credential、Provider/model、动态源码披露或 live
Web/browser grant；这些仍须在新 product freeze 后按 exact Session Authority 另行授权。hidden、`SLICE-002/003` 与 Production
Activation 继续未授权。此前 `1b327024… + 5cdb7000…` 仍只绑定被取代的一次性检索/先封包设计。
新三臂消融的 exact protocol、阈值和 digest 仍须在 Slice2 前由新的用户收据冻结。
