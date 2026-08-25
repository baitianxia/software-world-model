---
id: ITER-010-READINESS
kind: iteration-readiness
status: accepted
authority: project-authorization
owners: [project, architecture, quality, product]
depends_on: [ITER-010-PROPOSAL, ITER-010-VERIFICATION, ROADMAP-M-002, ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST, ITER-006-RESULT-ACCEPTANCE, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, FINDING-010-002, FINDING-010-093, FINDING-010-094, SYS-ADR-013, SYS-ADR-014, SYS-ADR-015, SYS-ADR-016, SYS-ADR-017, SYS-ADR-018, SYS-CONTRACT-AI-CAPABILITY-EVALUATION, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS, SYS-CONTRACT-SOURCE-ARTIFACT]
code: []
tests: []
iteration: ITER-010
authorized_by: user
authorized_at: 2026-08-25T05:06:07Z
product_goal_alignment_verdict: accepted
product_goal_alignment_reviewed_by: user
product_goal_alignment_review_ref: codex-user-message:sha256:f76ba3e864f6612b3dcc14c83392ec54db686fdb5653e408fa300785b97ceef5
historical_product_goal_alignment_review_ref: codex-user-message:sha256:585f02c4edcf25502b40f880c17a7bdf7f1af71044cd8d1bbe97b055a735ee9e
historical_authorized_at: 2026-08-21T09:18:34Z
critical_assumption_catalog_digest: sha256:2e53074115b08841a527fb7ba49e739eb2afd0473d20cacaa1a926338f8a8260
coding_input: false
---

# ITER-010 Readiness Review

## Reviewed exact inputs

产品 baseline 固定为 commit `1fb997bab6444523f82ebf1a514a1abbf79656c7`、tree
`1369ce932c778c57a118123e8257ede476229d73`；本次授权复核的 planning commit 为
`b66ff9f058b92cebd78d5644ffef042753567b4d`、tree `30e437eea83e048e3fb59ddd90a8d1b76242d82c`。ITER-009 技术资产保留，
但产品方向仍为 rejected/redirect。已复核重制后的 Candidate、Proposal、Manifest、Verification Matrix、三个 Slice 和
`FINDING-010-002/093/094`、ADR-018 和 Engineering Conversation Contract，并把 World Model、主 Agent、Conversation/Turn、平台与 Reviewer
职责明确分开。

用户收据 `d3b60bda…`（`2026-08-21T08:23:25Z`）确认重新制定计划并更新文档；新收据
`codex-user-message:sha256:585f02c4edcf25502b40f880c17a7bdf7f1af71044cd8d1bbe97b055a735ee9e`（`2026-08-21T09:18:34Z`）
接受本 Readiness，并只授权 `ITER-010-SLICE-001` 开发。修正前设计的旧授权不会被当作本设计的授权。

上述 `585f02c4…` 是历史 Readiness 收据。用户现以
`codex-user-message:sha256:f76ba3e864f6612b3dcc14c83392ec54db686fdb5653e408fa300785b97ceef5`（`2026-08-25T05:06:07Z`）
接受本文件的 PDR-004 refresh，并明确授权 `ITER-010-SLICE-001` 产品/System 编码与本地确定性验证。该收据不授权 Provider/model call、
credential、动态源码披露、live browser、hidden、Slice2/3 或 Production Activation。

该历史开发授权及其派生 live grant 均已执行、消费或停止。最新 [PDR-001](decisions/PDR-001-resume-as-rework.md) 只把错误的整轮
`REDIRECT` 解释纠正为 `REWORK`，没有自动恢复旧授权。用户随后以
`codex-user-message:sha256:32b298dedd814a93d8dc0a086776090342f14856f032283fddb453061c1efeb5`（`2026-08-24T02:55:16Z`）
明确要求继续开发，恢复同一个 Slice1 的产品/System 编码与本地确定性验证。Provider 调用、动态问题/源码披露和 live browser 不从该
开发收据推导，仍须在新 product freeze 后按 exact Session Authority 单独授权。

## Historical PDR-001—003 authorization delta (non-normative)

本节只解释 PDR-004 前已发生的授权和实现事实，不是 current 开发指令，也不恢复旧固定角色流程。`FINDING-010-029` 已完成当时恢复前的最小 System Owner 差异复核：旧 prepared Request/run 只保留历史单题兼容身份；持续 Alpha 在 listener
前固定 exact product、工程/revision、World Model、Source Profile/allowlist、Provider/configuration/qualification、角色契约、有效期和
每题/整会话熔断。用户提交动作密封 exact question receipt，System Owner 生成 server-owned per-question Request/run，动态角色输入仍
逐次形成 one-use disclosure authorization。该变化不放宽 Source、Provider、zero-retry、loopback 或非生产边界，已同步 ADR-016、
Engineering QA Contract、Security 和 Local Browser Operations。

## PDR-003 recovery delta

用户收据 `codex-user-message:sha256:47a3421d48fe3f36000e45696ea9c41b49b7e362332bc724306c10ca42fe119c`
记录约 14 小时没有新体验版本和 DeepSeek token 消耗过多。`FINDING-010-091/092` 与 PDR-003 现把当前 Slice 收窄为 experience-first
recovery：60 分钟页面可启动、180 分钟持续可操作、240 分钟 hard stop；本轮已超过 hard stop，停止 scope expansion、外部批量调用和
首次体验前 full regression，只允许启动安全、失败真实性、一次必要 qualification 和一个本地或 Mock 单轮 Access smoke。

Access 与 Quality 分开：从未执行的 `V-ALPHA-ACCESS-001` 以 PDR-004 pre-execution revision 验证真实 Chat Web 可操作；它不能通过
`V-CHAT-QUALITY-001`。已执行且 FAIL 的 `V-ANSWER-REWORK-001` 只保留旧单轮返工事实。PDR-004 以后不得再用孤立 live question 充当 Chat canary；首个方向 live canary 本身就是一个有界五轮
Conversation，每个到达 Provider dispatch 的 Turn 分别计 live attempt。同 failure signature 最多一个 successor live attempt，连续两次
没有用户可见增量即停止外部重跑。

本轮不再追逐答案表象：每次失败先沿 Source truth 到 Web 定位最早偏差并形成可证伪 root-cause hypothesis；没有假设和本地最小复现不得
修改 Prompt、Schema 或 Contract。修复先通过最小复现与两个未参与修复的相邻案例，再进入 PDR-004 五轮 live Chat canary；同 signature
修一次仍复现则停止规则累积并评审架构职责。首次体验前测试仅限 targeted impact/startup/safety 和失败真实性；full regression 只在 Alpha
`CONTINUE` 后 hardening 与正式验收前运行。

ADR-017 将 Provider 路由改为 Session 预授权的 Ark→DeepSeek：用户一次提交同一 logical question；primary attempt 只有在密封 terminal、
没有 authorized answer 且属于受控 Provider/model reason 后，才透明启动一个完全隔离的 fallback attempt。Fallback 从 original Turn、
该 Turn 密封的 exact Cognition 与 relevant sealed Conversation Context 重跑完整链，不共享中间态；同 Provider retry 0、late primary quarantine。当前代码尚未证明该语义，Readiness 只接受
它作为恢复开发输入，不把它写成 live PASS；外部调用继续需要 exact freeze/grant。

## PDR-004 readiness refresh and current acceptance

本文件头部 `status: accepted`、`product_goal_alignment_review_ref: f76ba3e8…` 与当前 A1—A6 digest 保存 PDR-004 刷新后的当前
Readiness 权威；`585f02c4…` 对旧单轮 Engineering QA 计划的历史 Readiness 仅由 `historical_*` 字段保存。
`FINDING-010-093/094` 和 PDR-004 已把目标修订为“软件世界模型 + 主工程 Agent”双核心及真正语义多轮 Chat。新默认 System Owner 是
`SYS-ADR-018 / SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION`，旧 ADR-016/Engineering Question Answering 只保留历史与兼容边界。

文档同步收据 `codex-user-message:sha256:d8239ea7da3d767caa5d0a091726849d1a644e45d44f631d36f3028787093a90` 只允许更新
文档。此后 current System docs、Proposal、Manifest、Slice 和 Verification 已一致冻结下列内容，并由 `f76ba3e8…` 接受。当前 Readiness
verdict 是 `ACCEPTED`，Iteration/Slice1 为 `authorized / coding_input=true`。此后 `FINDING-010-095` 已形成
`CHAT_ACCESS_LOCAL_CANDIDATE`；再后一次仅限 exact Access 的 grant 形成 `ITER-010-RESULT-V-ALPHA-ACCESS-001 / FINDING-010-096`，真实
listener/browser 使 `V-ALPHA-ACCESS-001` 成为 `PASS / access-only`。主 Agent、逐轮证据/审核、Provider route、资格和 live Chat 状态仍是
`NOT_IMPLEMENTED / NOT_QUALIFIED / NOT_LIVE`。此后 `FINDING-010-097` 已形成
`AGENT_EXECUTOR_LOCAL_CANDIDATE`：Application-owned loop、跨 Turn Work State、Observation/Package、fresh Review Finding 与 exact
Delivery binding 有 48/48 本地确定性证据。`FINDING-010-098` 随后形成 `EVIDENCE_TOOLS_LOCAL_CANDIDATE`：现有 World Model projector 与
Source Broker/Worker 经 trusted adapter 接入，support/boundary 可由同一动作分别密封，逐 Turn Ledger prefix 和 Citation receipt 可由
Application 重算；包含 temp Git exact search→opaque locator→read 的定向组合为 61/61。`FINDING-010-099` 随后形成
`MODEL_BOUNDARY_LOCAL_CANDIDATE`：单 Provider 主 Agent/Reviewer 的 closed no-tools input/output、逐 dispatch Disclosure/Gateway receipt、
失败计数与 non-dispatching candidate preflight 已有本地证据。`FINDING-010-100` 随后形成
`PROVIDER_ROUTE_COMPOSITION_LOCAL_CANDIDATE`：五类 typed fallback classification、Ark→DeepSeek 隔离 full-chain attempt、Application-owned
committed Work State、logical Turn 分账/duplicate-cost risk/late quarantine 和 fixed Browser composition 的最新相关组合为 76/76。真实
`FINDING-010-101` 又以生产 Ark/DeepSeek Adapter、credential-lazy transport、Model Gateway、Session Disclosure 与 model boundary 形成
`PROVIDER_RUNTIME_COMPOSITION_LOCAL_CANDIDATE`，最新相关组合为 79/79。current sealed Conformance、Source/World Model runtime、固定命令
Session 接线、资格和 live Chat 仍为 `NOT_LOADED / NOT_QUALIFIED / NOT_LIVE`：

- 主 Agent 拥有目标、假设、子任务、计划修订、context/tool 选择、观察解释、重规划、完成判断和答案综合；Control Plane 继续拥有权限、
  exact version、只读工具执行、证据身份、预算和审计，独立 Reviewer 必须保留。
- server-owned Conversation/Turn/Context，Context 至少包含确认目标/约束、指代实体/主题、开放问题、已审核结论、争议/被取代结论和
  exact provenance；Application 密封每轮 Context Projection，Provider hidden memory 不掌权。
- 模糊指代在 Source/Provider dispatch 前澄清；用户陈述和 prior Answer/Review 不成为 Source truth。旧 evidence 只有 exact revision、Binding、
  World Model authority、Source Profile/allowlist、content digest 和 Coverage 全部匹配，并重新绑定当前 Turn Package 后才可复用。
- 每轮独立 Request/Evidence/Answer/Review/Delivery；新 Conversation 不继承旧 Context；失败 Turn 不关闭 Conversation。
- 首个方向 canary 为一段五轮 Conversation 和一个新对话泄漏 probe；随后的比较分开两个问题：current Codex external baseline
  保留其真实客户端/model/reasoning/tools/权限，只作强基线而不是 Oracle/裁判；World Model 因果消融的 source-only 与
  full-cognition + source 两臂才共享同一主 Agent/model/tool/budget/cache/Reviewer。

PDR-003 的体验时间盒、Access/Quality、root-cause-first、首次体验前 full regression=0、Ark→DeepSeek transparent fallback、Conformance
reuse、DeepSeek 调度和成本不降质仍是恢复后的必要约束，不因本次架构更新重置或放宽。

## Product-goal alignment gate

- Baseline gap：真实 Web 能运行但回答像代码走读；固定多角色流水线没有主工程 Agent，同一 Runtime Session 的独立问题也不具备 Chat 语义。
- Product concept：World Model 始终是持久、版本化、可验证、可更新的软件外部认知，不是手册、缓存或关键词索引。
- Capability path：继续 `ROADMAP-M-002` 最早未证明的 Step 1；提问期 Source 调查核实、补充或纠正认知，不取代问题前建模。
- Cumulative integration：一个主工程 Agent 在 Conversation 中组合 exact World Model Cognition、受控 source/doc/config/test Evidence 和
  prior reviewed Delivery references，但 prior Answer 不取得事实权威。
- Fast checkpoint：历史单题与 4+1 题只证明受控 Web 技术链。返工首交付是固定工程/revision、消息历史、“新对话”和真实 Turn 提交的
  Access；Chat 专项 canary 是一个有界五轮 Conversation，每个到达 Provider dispatch 的 Turn 分别计 live attempt并保持完整证据/审核。
  新对话泄漏 probe 必须同行执行；失败回到本地根因诊断，不启动独立三题套件。
- Direction signal：Slice1 在用户先取得可操作 Chat、五轮 canary 与泄漏负测后，立即以同一 exact revision/Conversation 脚本/可比较输出/rubric
  运行 current Codex 强外部基线与系统两臂消融；Codex 保留实际能力，系统两臂才固定同 Agent/model/budget/cache。它是方向信号，不阻塞页面交付，也不把 Codex 当 Oracle/裁判。
- Later proof：Slice2 在第二工程复验多轮 Chat、持久恢复和三臂，Slice3 在最终隐藏工程和现场 Conversation 复验。PDR-002 的“严格超过
  current Codex”正式强制仍从 ITER-012 起；ITER-010 的 direction signal 不能冒充该正式 Gate。
- Stop：任何手册化/缓存化概念漂移、一次性固定调查、模型直接 Source 权限、特判、旧包批准、错误 Citation、审核/安全降级均阻断。

结论：Outcome 直接服务多轮工程 Chat MVP。历史 Readiness 已失去当前编码效力；PDR-004 refresh 已由 `f76ba3e8…` 接受并恢复
Iteration/Slice1 编码。Agent/Conversation 与透明 route 都尚未实现或验证；本文件只授权 Slice1 产品/System 编码与本地确定性验证，
不追认旧结果，也不授权外部调用、live 或后续 Slice。

## Architecture reflection gate readiness

Proposal 重新冻结 A1—A6：A1 检查世界模型认知概念、提问期调查与认知消融贡献；A2 检查主 Agent 自适应决策和 Broker/Worker
权限；A3 检查每轮密封 Evidence Package、主 Agent 自然综合、fresh independent Reviewer，以及 Finding 返回主 Agent 后的补证或重写；
A4 检查跨工程泛化；A5 检查三臂质量、完整
Cognition 的预提交增益、建模成本与复用周期；A6 检查语义追问、指代、纠正、总结、逐轮证据和新对话隔离。

Slice1 到期 A1—A3/A6，Slice2 累积到 A4/A6，Slice3 覆盖 A1—A6。每个阶段仍以用户新 `CONTINUE/ACCEPT` 作为下一段条件；安全上限只触发
失败关闭，不能裁剪调查、Evidence、Citation 或 Review。

## Outcome, scope and non-goals

计划 Outcome 是本机多轮工程 Chat：主工程 Agent 使用 Application 密封的 Conversation Context、exact World Model Cognition 和受控工具
观察持续维护用户目标、假设、计划与完成判断；Broker/Worker 只执行 exact-revision、allowlisted、read-only、audited 操作。每个 Turn
独立形成 append-only Ledger、双分区 Package、Answer、Citation、Review 和 Delivery；prior Answer/Review 不是事实证据，旧 evidence 只有
exact identity 全匹配并重新绑定当前 Package 后才可复用。新 Conversation 不继承旧工作状态或逐轮证据。

范围限 loopback、无认证、本地 Git exact revision、Java、World Model 与仓库源码/文档/配置/测试。非目标包括公网、Production、写仓库、
任意 shell、第二语言、跨仓库、跨重启长期 Memory、多 Agent/技能市场和同步知识发布。会话内工作状态不可延后；严格 `WORLD_MODEL` 与
显式 `DIRECT_INVESTIGATION` 保留且不可静默 fallback。

## System contracts and unresolved decisions

新的默认 System Owner 是 `SYS-ADR-018` 与 `SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION`。`SYS-ADR-016` 与 Engineering
Question Answering Contract 仅作为历史/兼容实现边界。原 planning commit 与授权时 Manifest 冻结的是
`ENGINEERING_QA_ADAPTIVE_INVESTIGATION@2`；同一已授权 Slice 的 `FINDING-010-033` 曾把当时历史单轮 Contract/Manifest 升级为
`@3` 的 evidence-grounded atomic observation closure，`FINDING-010-036` 再闭合其 coverage-only Limitation 缺口。这些只是已执行 PDR-004 前实现的兼容与
证据记录，不得被解读为恢复 `@3`、双 Review 或固定 Verification Investigation 拓扑的 current 命令。原 readiness receipt 也不证明新 candidate 或 live PASS。

DTO、Broker port、抽象 read operation、Ledger storage 和 UI 折叠是实现细节；以下不是实现选择：World Model 不得缩窄为手册；主 Agent 的工具选择与重规划必须
由先前观察驱动；模型无直接 FS/Shell/network/credential/source authority；Ledger append-only；调查后才 seal；Package seal 不等于真值；
Reviewer 必须在 fresh context 审查逐轮包与答案，其 Finding 只能返回主 Agent，由主 Agent 决定在 Control Plane 约束下补证或重写，再形成
新的 Package/Answer/Review identity；旧 `Verification Investigation` 固定角色只保留兼容资产，不是目标 Agent 本体。Slice1 的一次补证
上限不得成为 Slice2/3 永久协议；禁止任何题目/
工程/关键词/符号/类/方法/fixture/Oracle 特判。

## Slice, dependency and risk closure

Slice1 的历史失败尝试已执行完毕；当前为 `authorized / active / rework / coding_input=true`。最短顺序是：
闭合主 Agent 与 Conversation/Turn/Context 最小纵切 → 可重复启动且标记质量未验收的消息历史/新对话 Access → 最多一次本地或 Mock 单轮
Access smoke → 冻结最小候选与 Ark→DeepSeek route → 一个有界五轮 Conversation 作为首次方向 live canary，并执行新对话泄漏 probe。
不得用孤立 live question 代替 Chat canary；每个到达 Provider dispatch 的 Turn 分别计 live attempt并完成完整证据/审核。不得在此之前
建设跨重启持久化、第二工程、hidden、多 Agent、三臂或 full regression；但五轮 canary 与泄漏负测通过后，Slice1 必须运行不阻塞页面
交付的小样本三臂方向比较，再交给用户决定。Slice2/3 继续需要 Chat Alpha `CONTINUE` 和新授权。

首版必须保留 exact revision、allowlist、只读、Source untrusted、Ledger append-only、seal、证据分区、role isolation、Citation、独立
Review、Secret 和失败真实性；持久恢复、复杂冲突/去重、跨工程、全面性能、完整异常矩阵、hidden/三臂 comparison 和正式验收可延后。
Provider/model/source fragment
disclosure 必须在 live 前另行冻结和授权。

## Verification readiness

已执行的 `V-ANSWER-001/V-REVIEW-001/V-EXPERIENCE-001/V-TIMEBOX-001/V-ANSWER-REWORK-001/V-WEB-000/V-WEB-001/
V-PREVIEW-001/V-REFLECT-001` 保留原定义与 PASS/FAIL 证据，只是 historical，不是 PDR-004 的 current Gate。从未执行的
`V-ALPHA-ACCESS-001/V-PREVIEW-002` 以明确的 PDR-004 pre-execution revision 复用；没有旧执行证据可被追认。

current Slice1 Gate 是 `V-ALPHA-ACCESS-001/V-TIMEBOX-CHAT-001/V-CHAT-EXPERIENCE-001/V-CHAT-001/V-CHAT-QUALITY-001/V-CHAT-XD-001/V-COMP-ALPHA-001/V-PREVIEW-002`：先交可操作 Chat，
再运行一个五轮 Conversation 及新对话泄漏负测；每轮保留完整证据、Citation 和 fresh independent Review，Finding 回主 Agent 补证或重写。
随后的 `V-COMP-ALPHA-001` 不增加产品交付前阶段：Codex 保留实际能力并只作强外部基线；系统两臂才共享同一 Agent/model/budget/cache。所有新 live Case
仍须在当前开发授权、后续代码冻结和独立 live grant 下执行；计划、Mock 或旧单轮结果不能冒充真实 Chat。

## Authorization decision

**CURRENT READINESS ACCEPTED / ITERATION AND SLICE1 AUTHORIZED / CODING INPUT TRUE。** 原 Readiness 和 Slice1 开发曾由收据
`585f02c4…` 接受并执行；该授权及派生 grant 已消费或停止。PDR-001 接受的是计划纠正，后续 `32b298de…` 收据恢复当前 Slice1 的
产品/System 代码与确定性测试；PDR-004 已以 docs-only 收据 `d8239ea7…` 暂停该旧权威，`PROJECT-CURRENT` 不再指向任何 active Slice。
Agent/Conversation System Owner、Manifest 与五轮 Gate 现已一致，用户以 `f76ba3e8…` 明确接受并授权 Slice1 产品/System 代码与本地
确定性验证。该收据不授权 credential、Provider/model call、动态源码披露、live browser、hidden、Production Activation 或 Slice2/3；
后续 `7256a886…` 仅补充 exact `cf2883b…` 的 `V-ALPHA-ACCESS-001` 本机 listener/browser 权限并已消费。Provider-dispatched Chat、
源码披露、hidden、Production Activation 和 Slice2/3 仍未授权。
