---
id: ITER-010-INDEX
kind: iteration-index
status: authorized
authority: current-development
owners: [product, project, architecture, engineering, quality]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, PROJECT-GOVERNANCE-PLAN-EXECUTION, ROADMAP-M-002, ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, ITER-010-PROPOSAL, ITER-010-READINESS, ITER-010-VERIFICATION, ITER-010-SLICE-001, ITER-010-SLICE-002, ITER-010-SLICE-003, FINDING-010-028, FINDING-010-091, FINDING-010-092, FINDING-010-093, FINDING-010-094, FINDING-010-095, FINDING-010-096, FINDING-010-097, FINDING-010-098, FINDING-010-099, FINDING-010-100, FINDING-010-101, FINDING-010-102, FINDING-010-103, FINDING-010-104, FINDING-010-105, FINDING-010-106, FINDING-010-107, FINDING-010-108, FINDING-010-109, FINDING-010-110, FINDING-010-111, FINDING-010-112, FINDING-010-113, FINDING-010-114, FINDING-010-115, FINDING-010-116, FINDING-010-117, FINDING-010-118, FINDING-010-119, FINDING-010-120, FINDING-010-121, FINDING-010-122, FINDING-010-123, FINDING-010-124, FINDING-010-125, FINDING-010-126, FINDING-010-127, FINDING-010-128, FINDING-010-129, FINDING-010-130, FINDING-010-131, FINDING-010-132, FINDING-010-133, FINDING-010-134, FINDING-010-135, FINDING-010-136, FINDING-010-137, FINDING-010-138, FINDING-010-139, FINDING-010-140, FINDING-010-141, FINDING-010-153, FINDING-010-161, FINDING-010-162, FINDING-010-163, FINDING-010-164, FINDING-010-165, ITER-010-RESULT-SLICE-001-STOP-REDIRECT, ITER-010-RESULT-V-ALPHA-ACCESS-001, ITER-010-RESULT-V-LAYER-ATTRIBUTION-001, ITER-010-RESULT-V-COGNITION-ELIGIBILITY-001, ITER-010-RESULT-V-DEEPSEEK-IDLE-001, ITER-010-RESULT-V-PLAN-RECOVERY-001, ITER-010-RESULT-V-MVP-EXPERIENCE-001, ITER-010-RESULT-V-USER-DIRECTION-DECISION-001, ITER-010-DECISIONS, ITER-010-PDR-001, ITER-010-PDR-002, ITER-010-PDR-003, ITER-010-PDR-004, ITER-010-PDR-005, ITER-010-PDR-006, ITER-010-PDR-007, ITER-010-PDR-008, ITER-010-PDR-009, ITER-010-PDR-010, ITER-010-PDR-011, ITER-010-PDR-012, SYS-ADR-018, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: []
tests: []
iteration: ITER-010
coding_input: true
---

# ITER-010：软件世界模型与主工程 Agent 驱动的多轮工程 Chat

## 先看懂这轮要做什么

系统现在冻结两个同等必要、职责不同的核心：软件世界模型持续提供当前精确版本上稳定、可验证、可更新的软件认知；主工程 Agent 在
真正多轮对话中持续理解用户目标、指代与纠正，维护假设和计划，查询世界模型并按需提出受控源码调查，根据观察重规划和组织答案。
平台负责只读执行、证据身份、权限、熔断和审计；独立 Reviewer 在每轮交付前检查事实、完整性、引用、未知边界和对话目标履约。

| 文档术语 | 中文含义与职责 |
|---|---|
| World Model Cognition Context | 世界模型针对本题投影出的系统认知，不是手册或关键词缓存 |
| Cognition Capability Manifest | 同一精确版本上多个窄 Profile 的读取权威、能力、Coverage 与 Unknown 清单；用来判断本题是否有合格的多域认知 |
| Source Broker / Retrieval Worker | 来源代理 / 隔离读取器；前者校验并编译只读操作，后者执行，模型本身没有源码权限 |
| Evidence Ledger | 本题只追加的调查记录，保存每次提议、决定、读取结果、失败和未知 |
| Question Evidence Package | 调查后密封的本题证据包；可支持/引用条目与必须保留但不能支持肯定结论的边界/审计条目严格分区 |
| Legacy Verification Investigation | 旧 `@3` 兼容协议中的独立补证角色；current 目标由主工程 Agent 根据 Reviewer Finding 重写或继续受控调查 |
| Conversation / Turn | 一个对话及其按顺序密封的用户/助手轮次；每轮有自己的 Request、证据包、Answer、Review 与 Citation |
| Conversation Context Revision | 当前目标、指代、用户约束/纠正、未解决问题和 prior Delivery reference 的密封工作状态；不是软件事实 |
| Main Engineering Agent | 持续拥有目标、假设、计划、工具选择、观察解释、重规划、完成判断和答案综合的主工程 Agent |

恢复原则仍是尽快验证方向再夯实。一次性 governance recovery 已中断“先四路 Freeze/Quality、后完整产品纵切”的不可达旧图；
[PDR-010](decisions/PDR-010-complete-mvp-vertical-slice.md) 现将完整 MVP 体验放到严格比较之前。严格质量标准不降低，但必须比较用户已经能
体验的同一候选。三个独立问答不算 Chat，POM 模块/依赖题、Access 页面或单独 Web 外壳也不能充当 MVP。

## Status and authorization

### PDR-012 current status

`AUTHORIZED / REWORK / PRODUCT-FIRST BROWSER CHAT BUILD ACTIVE / STANDING SCOPE ACTIVE / NON-PRODUCTION`。

当前唯一工作计划是 `ITER-010-ACTION-BROWSER-CHAT-MVP-BUILD-001 / V-BROWSER-CHAT-MVP-BUILD-001`：在同一 Slice 完成真实世界模型认知、
主工程 Agent、按 Gap 受控源码、Evidence/Citation、fresh Review 和至少三轮语义 Chat。coding、Prompt/Reviewer、loopback Web 与 standing
scope 内 Provider dispatch 已恢复；首次完整链可操作即无 Result 交付。

[PDR-012](decisions/PDR-012-product-first-continuous-browser-chat-build.md) 是当前执行决定。PDR-011、run-052/053 和 failure Result 只保留
历史失败，不撤销 PDR-008 的公开工程 standing authority。普通失败留在当前 BUILD 做分层归因、通用修复与异质复验；不得生成失败 Result、
新 PDR 或重复授权。只有真实 scope delta、用户明确 STOP/REDIRECT/REJECT 或不可绕过的安全禁止才停止相关工作。

下列 PDR-011 状态说明是历史记录，已被 PDR-012 取代。

## PDR-011 historical status and authorization

`AUTHORIZED / REWORK / PDR-011 CURRENT / PRODUCT AND PROVIDER WORK STOPPED /
FAILURE RESULT SEALED / QUALITY FAIL / AWAITING USER DIRECTION / NO ACTIVATION /
DIRTY V7 AND OLD VALUE RUNNER QUARANTINED / SLICE-002 AND SLICE-003 NOT AUTHORIZED / NO ACCEPTANCE`。

当前唯一动作是 `ITER-010-ACTION-USER-DIRECTION-DECISION-001 / V-PREVIEW-002`：向用户如实呈现已密封的 run-052/053 pre-answer
failure，并记录 `CONTINUE / REWORK / REDIRECT / REJECT`。coding、Prompt、Web 和 Provider dispatch 全部锁定。

[PDR-011](decisions/PDR-011-truthful-pre-answer-failure-handoff.md) 是当前最高优先级执行决定；PDR-010 继续拥有产品设计与停止条件；
[PDR-009](decisions/PDR-009-value-first-four-arm-and-plan-lock.md) 的 Freeze-first 顺序已被取代，仅保留为历史；
[PDR-008](decisions/PDR-008-public-oss-standing-model-execution-authority.md) 继续拥有公开工程持续授权；
[PDR-007](decisions/PDR-007-deepseek-off-peak-hard-admission.md) 继续拥有 DeepSeek 闲时硬门禁；
[PDR-006](decisions/PDR-006-continuous-execution-and-just-in-time-authorization.md) 继续拥有持续执行规则；
[PDR-005](decisions/PDR-005-cognition-eligibility-and-layer-attribution-restart.md) 继续提供已完成的分层归因与认知资格输入。新的开发对话不得
接手产品修复或“fresh Ark+DeepSeek Conformance → 第八次同五轮”待办，只能从当前用户方向动作继续。v7 仅是未接受症状实验，
dirty 代码/测试不构成当前设计或质量证据。

此前分层归因、认知资格、执行配置本地准入和 Web Access 只作为可复用输入，不需要再变成体验前阶段。PDR-010 的执行顺序是：

1. 在同一候选上接通软件世界模型认知、主工程 Agent、按 Gap 受控源码补证、Evidence/Citation、fresh 独立 Review 和语义多轮无认证 Web；
2. 主链完整后以 `V-CHAT-EXPERIENCE-001` 立即交给用户体验，不等待全量回归或四路比较基础设施；该交付 `requires_result=false`、不移动游标；
3. 在同一候选上执行至少三条异质问题和 current Codex 定向对照；若失败，先归因根因，再做一次最小通用修复和定向复验；
4. 比较完成，或证明一次通用修复后同类重大失败仍存在时，才密封 `V-MVP-EXPERIENCE-001` Result 并进入用户方向决定。

current candidate `a5c780f51fa5242ee8209766712ad408ed023f80` 已走到第 4 步的失败出口：run-052 原失败和 run-053 两个异质案例在一次通用修复后
仍发生 Ark typed-output contract failure，DeepSeek 在所有结构化失败路径上保持 0。`FINDING-010-161` 因而停止产品修复与外调。
`FINDING-010-162` 同时证明 frozen `ITER010_MVP_LIGHT@2` 无法表示答案前失败；`FINDING-010-163` 证明普通 gate 因而机械自锁。用户已
明确授权最小治理恢复；`FINDING-010-164` 记录 @3 首次真实回放发现的 Gateway canonical-string digest codec 错配，
`FINDING-010-165` 又分离 sealing action 的新执行权限与历史 runtime 对账。修正后的 trusted-parent runner 已对真实证据重放，
`ITER-010-RESULT-V-MVP-EXPERIENCE-001` 以 machine PASS 密封 truthful failure handoff；该 PASS 不改变产品质量 FAIL，不改产品或历史运行字节。

用户方向 Result/receipt 只记录 `CONTINUE / REWORK / REDIRECT / REJECT`，direction action 保持自环。`CONTINUE` 不自行解锁 hardening、
full regression、第二工程或 hidden；这些工作仍须新 PDR、明确用户授权和可信父 cutover。本地消息 digest 只是内容证据引用，不是平台认证
身份、签名或授权。

当前动作的允许/禁止路径由 Manifest v2 执行。产品代码、Prompt/Reviewer、Web、Provider dispatch、hardening、full regression、第二工程、
hidden 和 Production 均锁定；当前 standing authority 只作为历史运行证据保留，不授权新的 dispatch。

PDR-004 的 `f76ba3e8…` 继续作为 Slice1 正式权限锚点；PDR-008 将它与公开 Apache-2.0 mall exact revision 组合为 current evaluation 的
standing human authority。已冻结的首选配置和符合其准入策略的备用配置无需逐次批准，但 private/different Source、扩大披露或预算、
备用配置策略要求的峰时 override、hidden、Slice2/3 或 Production 仍不在范围内。项目仍沿同一 Slice 记录
REWORK，是为保留失败责任；实际执行可使用全新对话。阶段交付前不得自行停止；只有真正 scope delta 才直接提交最小 exact request，
批准后自动继续。等待闲时不等于停工，standing authority 也不等于峰时 override。

以下 PDR-004 与 run-035—042 内容全部是保留的历史/实现进度，不得覆盖上述当前入口。

[PDR-004](decisions/PDR-004-agent-first-conversational-recovery.md) 已依据 Agent 方向收据 `2f8b92d8…`、Chat 目标收据 `f164d65a…` 和本次
文档同步收据 `d8239ea7…` 曾暂停旧编码权威。用户随后以
`codex-user-message:sha256:f76ba3e864f6612b3dcc14c83392ec54db686fdb5653e408fa300785b97ceef5`（`2026-08-25T05:06:07Z`）
接受刷新后的 Readiness 并授权 Slice1 产品/System 编码与本地确定性验证。新的 Chat Access 已形成
`CHAT_ACCESS_LOCAL_CANDIDATE`。用户随后以
`codex-user-message:sha256:7256a886d863712b27a7012c1c791eaca91c98f7183f732b463ce98543a469b6` 只授权 exact
`cf2883bef861e0345afc36415d4216f943d31cf4` 的本机 listener/browser Case；`ITER-010-RESULT-V-ALPHA-ACCESS-001 / FINDING-010-096`
已把 `V-ALPHA-ACCESS-001` 更新为 `PASS / access-only`。`FINDING-010-097` 随后形成
`AGENT_EXECUTOR_LOCAL_CANDIDATE`：Application-owned loop、跨 Turn Work State、Observation/Package、fresh Review Finding 与 exact
Delivery binding 已通过 48/48 确定性 Gate。`FINDING-010-098/099` 又形成 `EVIDENCE_TOOLS_LOCAL_CANDIDATE /
MODEL_BOUNDARY_LOCAL_CANDIDATE`：World Model/Source/Ledger adapter、单 Provider Agent/Reviewer closed role contract、逐 dispatch
Disclosure/Gateway receipt 和 non-dispatching candidate preflight 已闭合。`FINDING-010-100` 进一步以 trusted failure classification、隔离的
Ark→DeepSeek full-chain attempts、committed Work State 和 logical Turn 分账形成 `PROVIDER_ROUTE_COMPOSITION_LOCAL_CANDIDATE`，最新相关
组合为 76/76。`FINDING-010-101` 又用生产 Ark/DeepSeek Adapter、credential-lazy transport、Model Gateway 与 Session Disclosure 形成
`PROVIDER_RUNTIME_COMPOSITION_LOCAL_CANDIDATE`，最新相关组合 79/79。`FINDING-010-102` 再把 exact evidence authority、每 attempt fresh
Tool/Response Control、两条 Provider runtime、committed Work State、route、Conversation 与 Browser 闭合为
`SESSION_RUNTIME_COMPOSITION_LOCAL_CANDIDATE`，最新相关组合 89/89。`FINDING-010-103` 又以 owner-private closed config、exact ordered
Provider routes、fixed 5×15/75 bounds、mandatory resources exclusion、private Gateway/receipt paths 与唯一 `--session-config` selector 形成
`ARTIFACT_SESSION_FIXED_COMMAND_LOCAL_CANDIDATE`，最新相关组合 117/117。`FINDING-010-104` 又闭合 Ark 每 request verified TLS、TLS 后取
credential、retry 0、typed unavailable fallback 与双 route terminal Session audit，最新相邻组合 141/141。`FINDING-010-105` 随后在
clean `1e99e9b…` 上取得 fresh Ark Conformance 2/2、13/13 PASS；`FINDING-010-106` 又在 clean `653eff3…` 上取得
fresh DeepSeek Conformance 2/2、12/12 PASS，TLS `1/1`、connection reuse 1、retry/outcome unknown 0。两条 route 的 current
qualification 当时同时可用。`FINDING-010-107` 随后记录 exact `eb835f5…` / `run-035-chat-alpha`：首次 owner-private artifact-backed 五轮
Chat 已执行，但五轮 5/5 失败且没有 Answer/Citation/Review/Delivery；新 Conversation transcript 隔离成立，省略指代却没有澄清。
`FINDING-010-108/109/110` 已形成 literal/path-ranked Search、同一 64 文件总熔断内的 follow-up read reserve、Binding-owned 空上下文
澄清和同一固定五轮 deterministic successor canary。`FINDING-010-111` 又记录 exact `999616d…` / `run-036-chat-alpha`：第二次五轮仍
5/5 失败、24 logical dispatch、retry 0，但新 Conversation 的“它呢？”已真实通过 clarification、Context isolation 与零 dispatch。
同 signature 复现后，`FINDING-010-112/113` 已把 per-SEARCH scan 56 与 whole-Turn file total 64 分开，并以
`draft_reference_policy` 密封 SUPPORT/BOUNDARY 两个可复制 ID 域；73 文件相邻案例完成 3 个不同 READ，累计 59/64。model
strategy/prompt/input 已升级到 v2；聚焦 63/63、相邻组合 217/217、docs gate 80/80 和 513-document check 均通过，full discovery
1277 项中 1271 PASS，既有 ITER-003 frozen/Codex binary drift 保持 5 failures + 1 error。旧双 Provider Conformance 因而只保留为历史
证据。`FINDING-010-114` 随后在 exact `d429be6…` / `400d579…` 取得 fresh DeepSeek 2/2、12/12 与 Ark 2/2、13/13 PASS；
`FINDING-010-115 / run-037-chat-alpha` 第三次五轮仍 0/5；v3 Tool copy domain 与 Reviewer assessment 后，`FINDING-010-118` 在 exact
`743942d…` 取得 fresh 双资格。`FINDING-010-119 / run-038-chat-alpha` 仍只有 Turn 5 的 `REVIEWED_LIMITATION`，其余四轮失败，29 logical
dispatch、retry 0，整体 1/5 / Quality FAIL；新 Conversation clarification/Context isolation/零 dispatch 继续 PASS。
`FINDING-010-120/121` 把 canonical-resource Source legal domain、terminal Source operation removal 与 evidence-only completion 写入 v4；
`FINDING-010-123` 随后在 exact `34d98ae…` 上取得 fresh 双资格。`FINDING-010-124 / run-040-chat-alpha` 仍只有 Turn 2 的
`REVIEWED_LIMITATION`，其余四轮失败。`FINDING-010-125` 把 prior-Turn Observation IDs 移出 current Turn copy domain，并要求
evidence-required Review successor 只能提交 exact tool action。`FINDING-010-126` 又在 exact `6e97bc1…` 上取得 fresh 双资格；
`FINDING-010-127 / run-041-chat-alpha` 首次让 Turn 1 Answer 与 Turn 3/4 reviewed Limitation 技术成功，提升到 3/5，但 Turn 2/5 仍失败，
28 logical dispatch、retry/unknown 0，整体 Quality FAIL；新 Conversation clarification/Context isolation/零 dispatch 继续 PASS。
`FINDING-010-128` 现把 current SUPPORT/BOUNDARY 可行的 response kinds 与 tool argument forbidden/allowed exact values 写入 Primary input
v6，相关 Chat contract 84/84 与 compile PASS。`FINDING-010-129` 随后在 exact `3b8d09c…` 上取得 fresh 双资格；
`FINDING-010-130 / run-042-chat-alpha` 的 Turn 2/3/4 为 reviewed Limitation，Turn 1/5 失败，43 logical dispatch、retry/unknown 0，仍为
3/5 / Quality FAIL；新 Conversation clarification/Context isolation/零 dispatch 继续 PASS。`FINDING-010-131` 当时把 bounded Source Worker
path-relevance candidate ordering 与 symbol-first query preference 写入 Primary input v7，并以 exact User request 密封 Review input v3
materiality。`FINDING-010-132/133` 已证明该诊断不完整；v7 和“fresh 双资格后再跑旧五轮”均由 PDR-005 取代。hidden、Slice2/3 与
Production 始终未授权或未执行。

Slice1 已完成 4 条公开方向题和用户现场题。真实 Web、受控调查、Broker/Worker、Ledger/Package、Citation、独立 Review 与失败关闭技术链
能够运行；现场登录答案却仍由 Controller/Service/Filter 方法序列主导，并省略登录日志副作用，Reviewer 无 Finding 批准。

旧记录曾把用户消息 `d746968f…` 解释为 `REDIRECT`。最新接受的 [PDR-001](decisions/PDR-001-resume-as-rework.md) 明确：该消息要求
实现者自行复核并修复已知错误，并没有明确拒绝产品方向；历史 Result 的技术事实与具体 FAIL 保留，但整轮终止结论修订为 `REWORK`。
`FINDING-010-028` 定位的答案和审核根因回到本轮处理。用户随后以
`codex-user-message:sha256:32b298dedd814a93d8dc0a086776090342f14856f032283fddb453061c1efeb5`（`2026-08-24T02:55:16Z`）
明确要求“继续开发”，因此同一个 `ITER-010-SLICE-001` 当时恢复为编码输入。PDR-004 现已暂停这项旧权威；历史失败 Result 和 PDR-001
均保留。该收据不授权 `SLICE-002/003`、hidden 或 Production Activation，也不自动复用任何已消费的 live grant。

用户消息 `codex-user-message:sha256:d3b60bdaa52d96ced3c653a8dcd54fabff41beb7f23f0bf691e6983ebb9437bc` 于
`2026-08-21T08:23:25Z` 要求按最新讨论重新制定计划并更新文档。它确认：World Model 仍是真正的软件外部认知；提问期由 LLM 主导
自适应调查，Broker/Worker 控制实际读取，调查后 seal，Reviewer 可独立要求补证。

该收据曾只授权重制计划和文档。用户随后以
`codex-user-message:sha256:585f02c4edcf25502b40f880c17a7bdf7f1af71044cd8d1bbe97b055a735ee9e`（`2026-08-21T09:18:34Z`）
接受 Readiness，并只授权 `ITER-010-SLICE-001` 产品代码开发与本地确定性验证。用户随后以
`codex-user-message:sha256:815d868ca3df4795276934acbc21d12584fcfd4cb49b31c67696c72d3a5a6b74` 授权本次 mall / DeepSeek
验证的 exact endpoint、问题、Maven World Model 投影、角色 Ledger 和所选 Java/README/POM/Test evidence；调用数不限、retry 0，
`src/main/resources` 与配置凭据排除，Production Activation 不执行。该 root authorization 只允许每个 fresh candidate/session 继续
收窄并密封 exact dispatch，不能跨产品冻结复用旧 dispatch grant。`SLICE-002/003`、hidden disclosure 和 Production Activation 仍未授权。
此前 `1b327024… + 5cdb7000…` 仍只绑定被取代的设计。

clean candidate `274e5ea…` 的 run-020 current DeepSeek Conformance 2/2 PASS；同一持续 Alpha 中，原登录题独立可接受，构建/安全接入题
因 mandatory path 只能经内容 SEARCH 重新发现而触发 no-progress，401/403 题完整读取决定性实现后又因一个 `SUPPORTED` FINISH item
混入 `LIMITATION` observation 被本地 validator 正确失败关闭。`FINDING-010-057/058` 因而增加 Request + attempt + Profile-bound opaque
direct locator，并把 provider-facing FINISH 拆成结构互斥的 supported/non-supported arrays；旧 run-020 只作失败诊断证据，新 clean/fresh
三题与超限输入仍须重跑后才能更新体验 Gate。`FINDING-010-059` 已以 Engineering QA 101/101、current docs/compile/diff 和允许 AF_UNIX
的 full 1167/1162 exact historical hold 闭合确定性 Gate；它不替代 fresh Provider/browser 证据。

随后 clean `dfba244…` / run-021 已让原登录题和 401/403 题各以 8 次 dispatch 获得独立可接受的 `APPROVED`，也证明 66,000-byte
输入在 Provider 前拒绝且调用根不变。Q2 虽已用 direct locator 连续闭合 4 个 mandatory paths，却把 3 个 UNKNOWN 同时复制进
supported/non-supported arrays，并在仍有 8 个含当前动作 call 时结束；本地 validator 正确失败关闭。`FINDING-010-060` 因而要求
partition disjoint + checklist exact-once，并明确 mandatory minimum 不是 investigation maximum；`FINDING-010-061` 已以 Engineering QA
101/101、docs/compile/diff 与 full 1167/1162 historical hold 闭合 deterministic Gate。run-021 仍不能取得三题体验 Gate。

随后 clean `be15a0a…` / run-022 的 current Conformance 2/2 PASS；首题 Understanding 正常，第一个 Investigation 也选择了合法 direct
locator 与 current basis，却返回空 `checklist_item_ids`。Domain 以 structured-output violation 正确关闭，暴露 Provider Schema 允许
checklist/basis 数组为空或重复，而 Domain 一直要求 non-empty + unique。会话在 2 次 dispatch 后停止，没有提交 Q2/Q3 或超限输入，不能
用 run-021 补齐。`FINDING-010-062` 将两个 binding arrays 的 Provider Schema、Prompt 与 Domain 对齐；`FINDING-010-063` 已以
Engineering QA 102/102、docs/compile/diff 与允许 AF_UNIX 的 full 1168/1163 exact historical hold 闭合 deterministic Gate。新
clean/fresh live 仍待执行。

随后 clean `656b549…` / run-023 完成 fresh Conformance 2/2、同会话三题 8/8/7 dispatch 与 66,000-byte Provider 前拒绝；retry/switch
0、private files 和 Production `NOT_EXECUTED` 成立。Q1/Q2 独立可接受，Q3 却仅凭上游 empty authentication context 与 deny decision
推导最终 401/403，并把同一局部条件分配到互斥外部结果；模型 Reviewer 仍误判 `claim_consistency=PASS`。`FINDING-010-064` 现要求
externally visible status/error/body 必须由下游 response/exception mapper full-content evidence 支持，custom-handler wiring 不证明输出，
transport status 与 application/response-body code 分开；Prompt 升为 `@26`。run-023 不能取得三题质量 Gate，新 clean/fresh live 待执行。

`FINDING-010-065` 已以三模块 65/65、Engineering QA 102/102、docs 459/459、compile/diff PASS 与允许 AF_UNIX 的 full 1168/1163
exact historical hold 闭合 deterministic Gate；raw 唯一 4 FAIL + 1 ERROR 仍为冻结 V-009/Codex hold，没有 ITER-010 新失败。新的
clean candidate/fresh live 仍是 blocking evidence。

run-024—run-026 继续以通用机制收敛 Provider 跨字段重复状态、Review remediation 派生、Verification single-gap delta/
stable merge、predecessor full-read consumption、Broker rejection 投影、current-gap boundary 绑定与 terminal verified-gap 复审。
run-026 的 Q1 独立可接受，Q2/Q3 仍作为不相关 predecessor boundary 与重复 terminal-gap 的失败证据保留。
`FINDING-010-073/074` 现已区分普通 `GAP` 与 typed `VERIFICATION_GAP`，并以 Engineering QA 113/113、current docs
468/468 及允许 AF_UNIX 的 full 1179/1174 exact historical hold 闭合 deterministic Gate。下一阻断项是新 clean candidate
的 fresh Conformance、同一持续 Browser 三题、66,000-byte Provider 前负测与独立复核；Production 仍不执行。

随后 clean `b709fad…` / run-027 完成 fresh Conformance 2/2、同一持续 Browser 三题和 Provider 前超限拒绝。Q1 独立复核 PASS；
Q2/Q3 却把配置 placeholder 扩张为具体 header、caller/import 扩张为未挂载 DTO fields/handler output，并把上游局部决定扩张为下游
401/403，唯一 Reviewer 复述这些扩张后错误 `APPROVED`。`FINDING-010-075` 将 comprehensive Review 降为 provisional，随后强制 fresh
evidence-boundary challenge，并由 Gateway 校验 focus 顺序、只以 challenge 授权。focused 78/78、Engineering QA 115/115 已通过；
扩展 deterministic Gate 与新 clean/fresh live 仍是当前阻断项，run-027 永久保留 1 PASS + 2 FAIL，Production 仍不执行。

`FINDING-010-076` 已以 docs 组合 148/148、历史 oracle 组合 80/80、current docs/compile/diff 与允许 AF_UNIX 的 full
1181/1176 exact historical hold 闭合上述 deterministic Gate；raw 唯一 4 FAIL + 1 ERROR 仍精确属于冻结 V-009/Codex hold，没有
ITER-010 新失败。下一步只能从新 clean candidate 执行 fresh Conformance、持续 Browser 三题、Provider 前负测与独立复核；
run-027 不追认，Production 仍不执行。

clean `f832ceb…` / run-028 随后完成 fresh Conformance 2/2、同一 Browser 三题与 66,000-byte Provider 前负测；26 次 dispatch 的
retry/switch 均为 0。Q1/Q3 独立 PASS，Q2 虽保留所有具体配置值为未知，却仍把 Controller 的 getter caller use 写成未挂载
`UmsAdminLoginParam`“包含”字段；fresh challenge 收到精确 type lead 后仍复制该断言并错误 `APPROVED`。`FINDING-010-077` 因此要求
Application-owned stable challenge ID、逐项 evidence/Draft scope assessment、exact 集合重算与越界 Finding-on-challenged-Claim 绑定；
run-028 永久保持 2 PASS + 1 FAIL，新的 deterministic 与 clean/fresh live Gate 待闭合，Production 仍不执行。

`FINDING-010-078` 已以 focused 78/78、Engineering QA 115/115、docs 组合 148/148、历史 oracle 组合 80/80、current
docs/compile/diff 与允许 AF_UNIX 的 full 1181/1176 exact historical hold 闭合上述 deterministic Gate；raw 唯一 4 FAIL + 1 ERROR
仍是冻结历史 hold，没有 ITER-010 新失败。下一步只能从新 clean candidate 执行 fresh Conformance、持续 Browser 三题、Provider 前
负测与 raw challenge assessment 独立复核；run-028 不追认，Production 仍不执行。

后续 run-029—run-032 继续闭合 full-entry effect scan、Answer observation preservation、original-question fulfillment、effect omission layer
与 entry → source-reference resolver；`FINDING-010-079`—`FINDING-010-087` 保留每次 live FAIL/PASS 与对应 deterministic Gate，均不互相
拼接追认。

最新完整 Alpha clean `d70a3e6…` / run-033 的 fresh Conformance 2/2 PASS，但三题仍为 Q1 FAIL、Q2 FAIL、Q3 OUTCOME_UNKNOWN；66,000-byte
Provider-before-call negative PASS，总 dispatch 31、retry/switch 0、Production `NOT_EXECUTED`。`FINDING-010-088` 定位 Q1 的系统根因：
single-gap Verification replacement 可以删除 supported predecessor target observations。当前修复要求 exact/relative-order monotonic
preservation，并把 `APPLICATION_PACKAGE` effect gap 收窄为 caller full content 已可见 interaction；`FINDING-010-089` 已闭合
deterministic Gate，新 clean/fresh live 仍是 blocking evidence，项目决定继续为 `REWORK`。

新 clean `fe6b6b6…` / run-034 已在用户表示充值后启动 fresh DeepSeek Conformance，但第一条 exact
`deepseek-v4-pro` request 仍收到 HTTP 402。credential resolution/TLS/HTTP dispatch 为 1/1，token 0、retry/switch 0，
第二条 canary 未发送，没有 Qualification、Alpha、Browser 或 Production。`FINDING-010-090` 将 run-034 永久封存为
FAIL；当前 key 所属账户恢复 Provider 可用性后，只能启动新的 fresh Conformance。项目决定仍为 `REWORK`。

PDR-003 取代了上述“余额恢复后继续 DeepSeek”的历史下一步，但不改写 run-034。它先冻结质量未验收 Web Access、透明 Ark→DeepSeek
route 和有界 canary；PDR-004 又把孤立 live question 收窄为 Provider 前本地/Mock Access smoke，并把首次方向 live canary 明确为一个
五轮 Conversation 与新对话泄漏负测。Provider 对用户透明，fallback 是同一 logical Turn 下重跑完整链的新 attempt，不共享 Ark 中间态，
用户无需重提或新建 Conversation。该 route 与 Chat 均尚未实现/资格化；首次体验前停止无关 Prompt/Schema/Contract 扩张、外部批量调用和 full regression。

本轮产品基线固定为 commit `1fb997bab6444523f82ebf1a514a1abbf79656c7`、tree
`1369ce932c778c57a118123e8257ede476229d73`；授权审核的 planning commit/tree 为
`01dcfe2233625dfaa021495850fb18ae1323063b` / `8e364ae854bfaa48580ab080a3e0d9c9c43c3d6f`。ITER-009 的体验代码保留为技术资产，但其代码走读式产品方向已由
`ITER-009-RESULT-SLICE-001-STOP-REDIRECT` 否决，不能被写成 Acceptance。

## Required inputs

- [Proposal](proposal.md)
- [Manifest](manifest.yaml)
- [Verification Matrix](verification-matrix.md)
- [Readiness Review](readiness-review.md)
- [Development Design](development-design/README.md)
- [Findings](findings/README.md)
- [Results](results/README.md)
- [Decisions](decisions/README.md)

旧计划在 Slice1 的方向 Gate 失败：技术链能够运行，但答案/审核质量失败，随后又证明重流程、薄 Agent 和无状态连续问答不能实现目标
Chat。Slice2/3、旧三臂、hidden、正式验收和 Production 均未执行。PDR-010 已取代旧 Freeze-first 顺序：当前先完成并无 Result 即时交付
`V-CHAT-EXPERIENCE-001`，再在同一候选上完成异质问题与 current Codex 比较，最终以 `V-MVP-EXPERIENCE-001` Result 进入用户判向。
任何旧 Result、本机 PASS 或方向 receipt 都不自行授权 hidden、Slice2/3、hardening 或 Production。
