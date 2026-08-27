---
id: ITER-010-SLICE-001
kind: development-slice
status: authorized
authority: current-development
owners: [engineering, architecture, quality, product]
depends_on: [ITER-010-PROPOSAL, ITER-010-READINESS, FINDING-010-093, FINDING-010-094, FINDING-010-095, FINDING-010-100, FINDING-010-101, FINDING-010-102, FINDING-010-103, FINDING-010-104, FINDING-010-105, FINDING-010-106, FINDING-010-107, FINDING-010-108, FINDING-010-109, FINDING-010-110, FINDING-010-111, FINDING-010-112, FINDING-010-113, FINDING-010-114, FINDING-010-115, FINDING-010-116, FINDING-010-117, FINDING-010-118, FINDING-010-119, FINDING-010-120, FINDING-010-121, FINDING-010-122, FINDING-010-123, FINDING-010-124, FINDING-010-125, FINDING-010-126, FINDING-010-127, FINDING-010-128, FINDING-010-129, FINDING-010-130, FINDING-010-131, ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST, ITER-006-RESULT-ACCEPTANCE, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, SYS-ADR-013, SYS-ADR-014, SYS-ADR-015, SYS-ADR-016, SYS-ADR-017, SYS-ADR-018, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-KNOWLEDGE-STRUCTURE-MODEL, SYS-QUALITY-ACCEPTANCE, SYS-QUALITY-SECURITY]
code: [src/software_world_model/application_services, src/software_world_model/ai_infrastructure, src/software_world_model/interface]
tests: [tests]
iteration: ITER-010
coding_input: true
current_execution_decision_ref: ITER-010-PDR-006
current_execution_finding_refs: [FINDING-010-132, FINDING-010-133, FINDING-010-134, FINDING-010-135, FINDING-010-136, FINDING-010-137]
product_goal_gate: V-000
product_goal_accepted_capability_refs: [ITER-006-RESULT-ACCEPTANCE]
product_goal_cross_domain_case_ids: [V-CHAT-XD-001]
product_goal_web_checkpoint_id: V-CHAT-EXPERIENCE-001
direction_preview_web_checkpoint_id: V-CHAT-EXPERIENCE-001
product_goal_direction_preview_checkpoint_id: V-PREVIEW-002
product_goal_reflection_gate_case_id: V-PREVIEW-002
product_goal_slice_gate_case_ids: [V-LAYER-ATTRIBUTION-001, V-COGNITION-ELIGIBILITY-001, V-ALPHA-ACCESS-001, V-TIMEBOX-CHAT-001, V-CHAT-EXPERIENCE-001, V-CHAT-001, V-CHAT-QUALITY-001, V-CHAT-XD-001, V-COMP-ALPHA-001, V-PREVIEW-002]
---

# SLICE-001：主工程 Agent 多轮 Chat Alpha 与逐轮质量返工

## Status and dependencies

### PDR-006 持续执行规则与 PDR-005 当前 Gate

新的开发对话不得从 v7、fresh 双 Provider Conformance 或第八次旧五轮重跑开始。先用现有材料归因，再只修改 earliest-divergence Owner；
Maven-only 不具备行为问题的工程认知资格。旧 14 小时/timebox FAIL 和七次 live 失败永久保留，新的检查点是附加 hard stop，不追认或重置
历史。

| 顺序 | 时间边界 | 必须交付给用户/项目的结果 | 允许的工作 | Stop / pass rule |
|---|---:|---|---|---|
| 离线责任层归因 | 产品代码改动前，最多 60 分钟 | `V-LAYER-ATTRIBUTION-001` 逐层表：每个 material fact 的 Source truth、Snapshot、Cognition/Package、Draft、Review、Web；分别标 first divergence、guard failure、display failure | 只读 exact Source、现有 run/Gateway/Ledger/Package/Review、离线 projector；外部调用 0；只允许补可观测性证据 | 不能密封归因就停止产品修改并报告唯一证据缺口；不得猜改 Prompt/Schema/Tool/Review |
| 有资格的认知纵切 | 首个新产品代码改动后 T+180 | 同一 exact revision 的 Cognition Capability Manifest；结构+实现/行为 Read Authorities；三个异质问题逐 Need eligible capability/Gap；不同问题得到相关投影 | 只修改归因命中的知识构建/投影 Owner；定向单测、启动、安全 smoke；复用现有 Web Access | Maven-only、同题硬编码、所有问题返回同一整包或 Source 命中被回填成认知贡献均 FAIL |
| 浏览器方向体验 | T+240 absolute hard stop | 现有 `127.0.0.1:8765` 上一条真正的语义链（初问→省略指代追问或纠正→深入/总结）和两个未参与修复的异质问题；覆盖结构、行为/流程、职责/失败/Unknown；答案/真实失败、Citation、限制和版本可见 | 接入现有页面；每个 Turn 保持完整 Evidence/Answer/fresh Review；最多一个 Ark direction canary session 且须新 exact external grant；DeepSeek 仅 fallback | 到点立即交付最后可运行版并停止新增范围/外部调用；三个独立问答或单题答对不 PASS；重大错误或 Reviewer 漏判为 REWORK |
| 方向比较与决定 | 体验交付之后 | 同 Agent source-only vs eligible-cognition+source 的认知增益；隔离 current Codex 强基线；用户 `CONTINUE/REWORK/REDIRECT/REJECT` | 先绝对质量，再盲化比较；Codex 非 Oracle/Reviewer | eligible cognition 不得弱于 source-only，且至少一项非 locator 相关贡献；只有 CONTINUE 解锁 hardening/full regression |

冻结的体验只冻结类别、exact revision、判定规则和互异性，不把题目/答案/符号写进产品逻辑。其中一组 Turn 必须形成真实语义链，另外
至少两个问题未参与修复；整体覆盖结构、行为/调用、职责/失败边界/Unknown。`V-ALPHA-ACCESS-001` 已 PASS，页面壳不重做。

PDR-004 `f76ba3e8…` 继续授权本 Slice 产品/System 代码与本地确定性验证；本次本地 restart instruction digest
`291f6053…` 不扩大 Provider/model、Source disclosure、live Browser、hidden、Slice2/3 或 Production。新的“开发 ITER-010”对话可以
直接接手，不继承旧对话 Work State，也不需要复现旧开发过程；当前沿用 Slice1 是授权与审计选择，不是对话绑定。

### PDR-004 / v7 历史执行卡（已被 PDR-005 取代）

用户以 `codex-user-message:sha256:27ad0abac79f239eb13793fed79f65b8a5dfd7042e1c828b63e7d8545577d88f`
（`2026-08-25T06:20:03Z`）再次确认：前期工作的目的首先是快速验证方向；方向错误时，内部实现再完整也没有产品价值。下表是当时的
执行顺序，现仅保存 run-035—042 的审计语义；当前唯一顺序见上方 PDR-005 执行卡。

| 检查点 | 累计交付时限 | 用户可见出口 | 只允许的工作与验证 | 到点停止条件 |
|---|---:|---|---|---|
| 可启动 Chat 页面 | 60 分钟 | 固定命令启动 `127.0.0.1:8765`；能发送消息、查看历史并新建对话；未接模型时如实显示未配置/未资格/失败和“质量未验收” | 最小页面、Conversation identity、新对话隔离、loopback/Origin/输入边界、改动模块测试；不得调用模型或跑 full regression | 仍不可操作时，交付最后可运行状态和唯一最早阻塞点，停止架构与范围扩张 |
| 三轮真实方向体验 | 180 分钟交付线；240 分钟绝对停止 | 在 Turn1 前冻结一份五轮 Conversation 脚本，本检查点交付其“初始问题→指代追问→纠正前提”前三轮；每轮显示答案或诚实失败、Citation 和状态 | 每个已开始 Turn 保留完整主 Agent、Evidence、Answer、fresh Review 和失败关闭；外部 dispatch 前另取 exact grant；只跑定向测试和两个相邻非定制案例 | 180 分钟未交即记 timebox FAIL、交付现状并停止新增范围；181—239 分钟的迟到 Alpha 只作 `FAIL / REWORK` 证据；仍是独立问答、纠正不生效、答案像代码走读或需要特判时不继续后两轮、比较或夯实 |
| 五轮 Chat 与新对话隔离 | 360 分钟 | 仅在上一检查点未被停止时，增加“进一步区分/深入→按当前 Context 总结”，并展示新对话不继承旧指代、失败 Turn 后会话可继续 | 同一冻结 Conversation 的后两轮、逐轮 Evidence/Citation/Review、新对话泄漏负测和 Turn 故障隔离；仍不跑 full regression | 上下文泄漏、prior Answer 成为事实、失败关闭会话、重大错误或审核误放行，停止比较和 hardening |
| 小样本三臂比较与方向决定 | 480 分钟 | 展示盲化的 current Codex、同 Agent 仅源码、同 Agent 世界模型认知+源码结果及独立技术判断；用户作出 `CONTINUE / REWORK / REDIRECT / REJECT` | 同一 exact revision、同一代表性 Conversation 与 rubric；系统两臂共享 Agent/model/tool/budget/Reviewer，Codex 保持实际能力 | 完整认知臂有重大错误、弱于源码臂/Codex 或世界模型无可观察贡献时，方向未证明；成本和时延不得抵消质量失败 |

`FINDING-010-095` 已形成第一检查点的本地候选：独立 `swm-engineering-chat` 固定命令、Application-owned Conversation/Turn/Context、完整
消息历史、“新对话”、失败 Turn 隔离和 loopback/Origin/JSON/input 边界通过新 Access 17/17 与旧 QA 相邻兼容 18/18。该证据没有启动
listener/browser，也没有 Provider/model/Source/World Model dispatch，因此当时状态只是 `CHAT_ACCESS_LOCAL_CANDIDATE`。随后 exact
`cf2883bef861e0345afc36415d4216f943d31cf4` 获得仅限本机 Access 的一次性 grant；`ITER-010-RESULT-V-ALPHA-ACCESS-001 /
FINDING-010-096` 已通过真实 fixed-command listener 和 in-app Browser 验证同会话失败 Turn 隔离、完整历史、新 Conversation 隔离与
Provider dispatch 0，`V-ALPHA-ACCESS-001` 现为 `PASS / access-only`。PDR-004 当时的下一动作是同一冻结五轮 Chat canary；PDR-005 已将
当前动作改为离线归因和认知资格。Access PASS 不推导 Agent、Provider、Chat 或 Quality PASS。`FINDING-010-097` 随后把下一纵切的 Application-owned bounded Agent executor、
跨 Turn Work State、Observation/Package、fresh Review Finding 与 Delivery binding 闭合为 48/48 的本地确定性候选；它没有接入真实 World
Model/Source/Provider、完整 Ledger/Citation 或 launcher，也没有执行五轮 canary。`FINDING-010-098` 又以 temp Git 和确定性 model ports
把现有 World Model projector、Source Broker/Worker、逐 Turn append-only Ledger prefix 与 Citation receipt 接成
`EVIDENCE_TOOLS_LOCAL_CANDIDATE`；它没有读取 mall 或执行 live。`FINDING-010-099` 又将单 Provider Agent/Reviewer 的 closed input/output、逐
dispatch Disclosure/Gateway receipt、失败计数与不执行 I/O 的 launcher candidate preflight 接成 `MODEL_BOUNDARY_LOCAL_CANDIDATE`。
`FINDING-010-100` 随后闭合 ADR-017 typed fallback classification、Ark→DeepSeek 隔离 full-chain attempts、committed Work State、logical
Turn 分账与 fixed Browser composition，形成 `PROVIDER_ROUTE_COMPOSITION_LOCAL_CANDIDATE`。`FINDING-010-101` 又将生产 Ark/DeepSeek
Adapter、credential-lazy transport、Model Gateway、Session Disclosure 与 model boundary 接入为
`PROVIDER_RUNTIME_COMPOSITION_LOCAL_CANDIDATE`。`FINDING-010-102` 再把两条 Provider runtime、exact evidence authority、每 attempt fresh
Tool/Response Control、committed Work State、route、Conversation 与 Browser 接成 `SESSION_RUNTIME_COMPOSITION_LOCAL_CANDIDATE`。
`FINDING-010-103` 已实现 canonical owner-private artifact loader、exact ordered Provider routes、fixed bounds/exclusions、两个 private Gateway
repositories、launch/terminal receipt 和唯一 `--session-config` fixed-command lifecycle，形成
`ARTIFACT_SESSION_FIXED_COMMAND_LOCAL_CANDIDATE`。`FINDING-010-104` 又闭合 Ark transport 的 per-request verified TLS Session audit、
TLS-before-credential、typed unavailable fallback 和 fresh-Conformance identity。`FINDING-010-105/106` 已分别在 clean `1e99e9b…` /
`653eff3…` 上取得 fresh Ark 2/2、13/13 与 DeepSeek 2/2、12/12 Conformance PASS，两条 route 的 current qualification 同时可用。
`FINDING-010-107` 随后记录 exact `eb835f5…` / `run-035-chat-alpha`：五轮真实 Chat 全部失败且没有 Answer/Citation/Review/Delivery；新
Conversation 没有旧消息，但省略指代未澄清。最早偏差是 semantic search 提示与 literal Worker 不一致，以及空上下文指代没有可信的
Provider 前所有者。`FINDING-010-108/109` 已完成 bounded literal/path-ranked Search 和 Binding-owned Application clarification 的本地修复。
组合审计又发现截断 Search 会先耗尽 locator Read 的总文件预算；`FINDING-010-110` 在不提高 64 文件总熔断的前提下保留一个 follow-up
read 名额，并用 71 文件、同一固定五轮和新对话 probe 闭合 deterministic successor Gate。`FINDING-010-111` 随后记录 exact
`999616d…` / `run-036-chat-alpha`：五轮再次 5/5 失败、24 logical dispatch、retry 0；新 Conversation clarification/隔离/零 dispatch
首次真实 PASS。第二次失败证明单 READ reservation 是同 signature 的架构缺口，且 Ark Draft 还发生 BOUNDARY→SUPPORT 跨域引用。
`FINDING-010-112/113` 因而把 SEARCH scan 56 与 whole-Turn total 64 显式分开，并由 Application 投影 sealed Draft reference domains；
73 文件相邻案例完成三个不同 READ，累计 59/64。model strategy/prompt/input 已升级到 v2，旧双 Provider Conformance 不再资格化当前
successor。`FINDING-010-114` 随后在 exact `d429be6…` / `400d579…` 上取得 fresh DeepSeek 2/2、12/12 与补充 Ark 2/2、13/13
Conformance PASS；Ark 补充 TLS acquisition 使用 4/10，只有 credential/HTTP 均为 0 的失败 run 被重新启动。条件满足后，
`FINDING-010-115 / run-037-chat-alpha` 执行同一五轮，仍为 0/5，dispatch `10/8/4/4/5`、retry 0；新 Conversation
clarification/隔离/零 dispatch 继续 PASS。最早产品偏差变为 Tool action/locator 没有受信 copy domain，以及 Reviewer 明知 Claim 已支持却
仍编码 FINDINGS。`FINDING-010-116/117` 现以 Primary input v3 的 current-attempt action/locator policy 和 Review input/output v2 的完整
Claim assessments 处置；所有 role output 还显式禁止 JSON 外叙述，closed adapter 不抽取 substring。`FINDING-010-118` 随后在 exact
`743942d…` / `748902c…` 取得 fresh Ark 2/2、13/13 与 DeepSeek 2/2、12/12 Conformance PASS。条件满足后的
`FINDING-010-119 / run-038-chat-alpha` 仍只有 Turn 5 形成 `REVIEWED_LIMITATION`，其余四轮失败，dispatch `8/6/2/8/5`、retry 0；新
Conversation clarification/隔离/零 dispatch 继续 PASS。根因是同一 canonical Source resource 的多个 line locator 仍可分别读取，以及
no-progress threshold 直接失败而不能基于现有边界受审完成。`FINDING-010-120/121` 以 Primary input v4 的 resource-level legal domain、
terminal Source operation removal 和 `EVIDENCE_ONLY_SYNTHESIS` 处置。`FINDING-010-123` 随后在 exact `34d98ae…` / `b9100b1…`
取得 fresh Ark 2/2、13/13 与 DeepSeek 2/2、12/12 Conformance PASS；条件满足后的 `FINDING-010-124 / run-040-chat-alpha` 仍只有
Turn 2 形成 `REVIEWED_LIMITATION`，其余四轮失败，dispatch `11/8/2/5/2`、retry 0，新 Conversation clarification/隔离/零 dispatch 继续
PASS。根因是 previous Work State 暴露 prior-Turn Observation IDs，以及 evidence-required Review successor 仍允许普通 Draft。
`FINDING-010-125` 现以 Primary input v5 的 current-Turn reference policy 与 required tool transition 处置。`FINDING-010-126` 随后在 exact
`6e97bc1…` / `fd54821…` 取得 fresh Ark 2/2、13/13 与 DeepSeek 2/2、12/12 Conformance PASS；条件满足后的
`FINDING-010-127 / run-041-chat-alpha` 让 Turn 1 Answer 与 Turn 3/4 reviewed Limitation 技术成功，提升到 3/5，但 Turn 2/5 仍被
model-output contract 拒绝，dispatch `8/3/8/7/2`、retry/unknown 0，新 Conversation clarification/隔离/零 dispatch 继续 PASS。根因是
exact repeated query 的禁止值没有就地进入对应 tool argument domain，以及 empty current SUPPORT 时 `ANSWER` 仍出现在 allowed response
domain。`FINDING-010-128` 现以 Primary input v6 的 current-evidence response kinds 与 tool-argument forbidden/allowed exact values 处置，
相关 Chat contract 84/84 与 compile PASS。`FINDING-010-129` 随后在 exact `3b8d09c…` / `6728a5a…` 取得 fresh 双资格；条件满足后的
`FINDING-010-130 / run-042-chat-alpha` 仍只有 Turn 2/3/4 reviewed Limitation，Turn 1/5 失败，dispatch `15/9/6/6/7`、retry/unknown 0，
新 Conversation clarification/隔离/零 dispatch 继续 PASS。根因是 Reviewer 把 completeness 扩到 exact request 外，以及 Primary 未看到
bounded Worker 的 path-relevance candidate ordering。`FINDING-010-131` 现以 Primary input v7 source strategy 与 Review input v3
exact-request materiality 形成未接受症状实验。当时计划的 fresh Ark/DeepSeek Conformance 和下一次同五轮已被 PDR-005 取消；任何旧
run 都不能宣称修复已 `LIVE / PASS`，run-035—038、run-040—042 永久保留
各自真实 FAIL/limitation/response 证据。

以上四项是 PDR-004 历史交付/停止点，不创建、恢复或替代 Iteration、Slice、Readiness 或开发授权。当时三轮检查点只是预先冻结的同一五轮 live canary 的中间交付；若在此停止，五轮 canary 记为
`INCOMPLETE / FAIL`，不能取得 Chat/Quality PASS。等待外部授权时立即交付当前可运行版本并停止产品范围扩张；本次计划收据不授权
Provider/model、源码披露或 browser live；run-035—038、run-040—042 的授权均已消费。任何检查点上用户明确认为方向错误，都立即停止后续投入。下文的历史 run、旧协议和最终 Gate
只作证据与边界引用，不能反向成为首个交付的前置任务。

`AUTHORIZED / ACTIVE / REWORK / CODING INPUT`。用户曾以
`codex-user-message:sha256:585f02c4edcf25502b40f880c17a7bdf7f1af71044cd8d1bbe97b055a735ee9e`（`2026-08-21T09:18:34Z`）
接受 Readiness 并只授权本 Slice。`SLICE-002/003` 不随之授权；此前绑定修正前一次性检索/先封包设计的收据不构成本 Slice 的权限来源。

公开题和现场题执行后，旧记录把消息 `d746968f…` 解释为 `REDIRECT`：默认正文仍被类、方法和调用顺序主导，Reviewer 没有识别该质量
失败。[PDR-001](../decisions/PDR-001-resume-as-rework.md) 已确认该消息没有明确拒绝方向，当前决定为同轮 `REWORK`。
`ITER-010-RESULT-SLICE-001-STOP-REDIRECT` 继续保存 exact 执行事实。用户现以
`codex-user-message:sha256:32b298dedd814a93d8dc0a086776090342f14856f032283fddb453061c1efeb5`（`2026-08-24T02:55:16Z`）
明确要求继续开发，恢复同一个 Slice 的产品/System 编码和本地确定性验证。该收据晚于失败 Result 与 PDR-001，不改写历史失败，也不授权
Slice2/3、hidden、Production Activation 或复用旧 live grant。

[PDR-003](../decisions/PDR-003-experience-first-provider-cost-recovery.md) 记录了历史恢复约束：用户报告本轮约 14 小时仍无新体验版本且
DeepSeek token 消耗过多。既有授权不再允许继续无界扩张 Prompt、Schema 或 Contract；PDR-004 恢复只做 Chat Access、Provider route、失败真实性、最多一次 Provider 前本地或 Mock Access smoke 与
五轮 live Conversation 所需的最小工作。该一次 Access smoke 额度已由 `V-ALPHA-ACCESS-001` 的 browser run 消费，不再追加。Ark 为
primary；同一 logical Turn 的 Ark attempt 在密封 terminal 后，仅可按预授权 route 自动启动
一次独立 DeepSeek fallback attempt，用户无需选择模型、重提问题或重启 session。

PDR-004 是仍有效的架构与权限基线，执行顺序现由 PDR-005 覆盖：目标仍是“软件世界模型 + 主工程 Agent”双核心与真正多轮 Chat；默认 Owner 为
ADR-018/Engineering Conversation Contract。文档同步收据 `d8239ea7…` 本身不授权产品代码或 live；用户现以
`codex-user-message:sha256:f76ba3e864f6612b3dcc14c83392ec54db686fdb5653e408fa300785b97ceef5`（`2026-08-25T05:06:07Z`）
接受刷新 Readiness 并授权本 Slice 产品/System 编码与本地确定性验证。下文标明“历史 / non-normative”的段落只保存已发生事实；
该收据不授权 Provider/model、动态源码披露、live browser、hidden、Slice2/3 或 Production；后续 `7256a886…` 补充 exact
`cf2883b…` 的 Access 权限并已消费，`bec7f079…` 又补充 exact `eb835f5…` 五轮 Chat、受限 Source disclosure 与 browser 权限并在失败
run-035 中消费；`096a1bc…` 最后补充 exact `999616d…` 的同一五轮与泄漏负测并在失败 run-036 中消费。v2 model boundary 需要 fresh
Conformance；`8ebd3650…` 又在 exact `d429be6…` 上授权条件式双 Conformance、artifact 和同一 Live，Ark TLS acquisition 补充授权
`e89640fa…` 与上限提升 `21786af7…` 也已按 `FINDING-010-114` 消费，最终失败 run-037 由 `FINDING-010-115` 密封。v3
strategy/prompt/input/output 随后在 `338979f8…` 授权下取得 fresh 双资格并执行 run-038；`FINDING-010-118/119` 已密封 1/5 reviewed
Limitation / overall FAIL 与 leakage PASS。v4 随后由用户授权在 exact `34d98ae…` 上取得 fresh 双资格并执行 run-040；本地密封的
user-message UTF-8 digest 为 `6834f685…`，`FINDING-010-123/124` 再次密封 1/5 reviewed Limitation / overall FAIL 与 leakage PASS。
该授权也已消费；v5 随后在 exact `6e97bc1…` 上取得 fresh 双资格并执行 run-041。本地密封的 exact user-message UTF-8 digest 为
`bed1ccdc…`，`FINDING-010-126/127` 密封 3/5 technical responses / overall FAIL 与 leakage PASS。该授权也已消费；v6
strategy/prompt/Primary input 随后在 exact `3b8d09c…` 上取得 fresh 双资格并执行 run-042。本地密封的 exact user-message UTF-8 digest 为
`df3cfe58…`，`FINDING-010-129/130` 密封 3/5 reviewed Limitation / overall FAIL 与 leakage PASS。该授权也已消费；v7
strategy/prompt/Primary/Review input 已冻结为未接受症状实验，领域 Prompt/Schema 变化本身不使 Provider Conformance 失效。当前没有新的 Provider/Source/browser live 授权，hidden、Slice2/3 与 Production
始终未授权。

恢复后的最小纵切必须同时具备 server-owned Conversation/Turn/Context、完整消息历史、“新对话”、主 Agent 的目标/假设/计划/重规划、
逐轮 Request/Evidence/Answer/Review/Delivery 和新对话隔离。PDR-005 首次方向体验至少含一条真实语义链和两个未参与修复的异质问题；
不能用孤立问题或同 Session 三个独立问答冒充 Chat。每个发生 Provider dispatch 的 Turn 分别计 live attempt。

## PDR-003 / PDR-004 historical recovery record（执行顺序已被 PDR-005 取代）

本节只保存已发生 run 的时间盒、Provider、安全和质量不可裁剪语义；PDR-005 覆盖其中的检查点顺序，不改写已经发生的 run 或安全边界。

1. 从未执行的 `V-ALPHA-ACCESS-001` 按 PDR-004 pre-execution revision 先交一个真实、可重复启动、普通用户可操作且明确标记“质量未验收 / 非生产”的 Chat Web。页面可以如实显示
   Provider 未资格、请求失败、答案或 Limitation；静态回放不算 Access。
2. 新 `V-CHAT-QUALITY-001` 是独立 Quality Gate。Access PASS 不能补成 Quality PASS；Quality FAIL 也不删除可操作页面。已执行 FAIL 的 `V-ANSWER-REWORK-001` 仅保留历史原义。只有 Quality
   PASS 且 `V-PREVIEW-002` 取得用户 `CONTINUE` 才允许进入 hardening。
3. 新 `V-TIMEBOX-CHAT-001` 对 PDR-004 恢复使用四个用户交付检查点：60 分钟页面、180 分钟同一五轮脚本前三轮方向 Alpha 交付线、240 分钟绝对停止、360 分钟五轮方向证据、480 分钟独立比较与用户判向。180 分钟未交即记 timebox FAIL；181—239 分钟形成的迟到 Alpha 只能作为 `FAIL / REWORK` 证据。已执行 FAIL 的 `V-TIMEBOX-001` 仅保留 PDR-003 历史原义。历史 14 小时已经越过 hard stop，因此新授权后立即停止 scope expansion、外部批量调用和
   首次体验前 full regression，收窄为页面启动、安全、失败真实性、最多一次 current Provider qualification 和一个本地或 Mock Access smoke；每到一个检查点立即交付，不等待后续 Gate。
4. 每次失败先按 Source truth、World Model Cognition、Conversation/Task Understanding、Agent Work State/Plan、Tool Observation/Evidence、
   Answer、Independent Review、Web 定位
   最早偏差，并提出可证伪 root-cause hypothesis；没有该假设不得改 Prompt、Schema 或 Contract。修复先通过本地最小复现和两个未参与
   修复的相邻案例，再运行一个五轮 Conversation 作为首次 live Chat canary。
5. 同一 failure signature 只允许修复一次；仍复现即停止规则累积并评审架构职责。五轮 canary 任一 Turn 失败时停止后续方向套件。首次体验前只跑
   targeted impact、startup、safety 和失败真实性；full regression 仅在 Alpha `CONTINUE` 后 hardening 与正式验收前运行。
6. 一个 sealed 版本的 Turn run 到达任何外部 dispatch 即计一次 live attempt。同一 failure signature 最多一个 successor attempt；
   连续两次没有用户可见增量即停止外部重跑、回到本地诊断。内部 Prompt/Schema/Contract 或测试数量变化不算用户可见增量。
7. Ark route 当前未闭合不能被当作 Ark 不可用证据。Session 在问题前预封 Ark→DeepSeek 有序 route 与双 Provider disclosure scope；
   primary attempt 因 Provider unavailable/HTTP/outcome unknown/output invalid 或 Review reject 而密封为无 authorized answer 时，才可对
   同一 Turn 自动启动一次 DeepSeek attempt。Fallback 从 original Turn、该 Turn 密封的 Cognition 和 relevant sealed Conversation Context 重跑完整链，不复用 Ark 中间态；迟到 Ark 结果隔离且不覆盖。
   相同且仍有效的 Conformance 必须复用。
8. DeepSeek 批量运行默认安排在北京时间 `00:00–09:00`、`12:00–14:00`、`18:00–24:00`，并在开始前复核官方价格政策是否已经生效。
   成本只决定是否在 dispatch 前开始，不能裁剪已经开始的问题的调查、Citation 或 Review。

## Rework outcome：先交付持续 Web Alpha

新 Readiness 与授权后的首项交付必须是普通用户实际可持续使用的同一产品 Chat Web，而不是固定 1+1 问题的评测运行器：

1. 服务可通过一条固定、文档化的命令重复启动在 `http://127.0.0.1:8765/`，无需认证；普通体验者不需要拼装逐题 freeze、grant 或内部
   run 参数。页面明确显示产品版本、工程精确版本、Alpha/非生产状态和已知限制。
2. 启动时固定一个本地工程、精确 revision、世界模型认知、Source Profile、Provider/model 与只读范围；服务拥有 Conversation/Turn/Context 和“新对话”，
   用户能在同一 Conversation 追问、纠正、澄清、深入与总结，不得退化为同 Session 中互不相干的独立问题。
3. 每个 Turn 保持独立 Request、Ledger、Package、Answer、Review 和 Citation 身份；Conversation Context 只保留有 provenance 的对话状态，prior Answer/Review 不成为源码事实。
   某 Turn 失败只关闭当前 Turn，Conversation 仍可继续；新 Conversation 不继承旧 referent、Work State、Evidence 或 Provider memory。
4. 主 Agent 使用受控 World Model/Source 工具，基于每次观察重规划并综合答案。fresh independent Reviewer 只返回 Finding；Finding 回主 Agent 补证或重写，
   不启动固定的 Verification Investigation 角色、双 Review 或 `@3` 流水线。不得加入工程/问题/关键词/符号/类/方法/fixture/Oracle 特判。
5. 复用已通过的页面 Access；认知资格接回 Web 后立即交付一条真实语义链和两个未参与修复的异质问题，并执行新对话隔离负测，随后在本 Slice
   内运行三臂方向信号。跨重启恢复、完整五轮套件、第二工程、hidden、复杂异常矩阵和 full regression 延后到用户 `CONTINUE`。

自由提问所需的会话级授权、动态问题披露和 System Owner 语义必须在编码前以最小变更闭合；这项必要安全工作不能扩张为先建设完整答案
Schema 或评测体系。模型调用上限仍只作为安全熔断，不能为了减少调用而省略调查、Citation 或独立审核。

开发 baseline 仍候选绑定 commit `1fb997bab6444523f82ebf1a514a1abbf79656c7` / tree
`1369ce932c778c57a118123e8257ede476229d73`；本次刷新 Readiness 冻结的 planning commit/tree 为
`b66ff9f058b92cebd78d5644ffef042753567b4d` / `30e437eea83e048e3fb59ddd90a8d1b76242d82c`。本开发授权不允许
credential、Provider/model call、live Web/browser、源码片段外发、hidden disclosure 或 Production；live 必须在产品 freeze 后另取 exact grant。

用户随后以 `codex-user-message:sha256:b8b6931f8d76b45a16fa50ae057d7fa6ccd744d58f6041d3fdfc1fd5ca84e7c7` 授权完成本 Slice 所需权限；
该 root authority 已通过 exact product/request/Provider/role/input grants 收窄并消费。Listener 已停止，所有旧 grant 不得复用。Slice2/3、
hidden 与 Production Activation 从未授权。

## Product-goal contribution and cumulative integration

- Product delta：把“固定调查后代码走读”推进为“世界模型认知引导、模型自适应读源码、答案优先”的真实纵切。
- Existing capability：复用 ITER-006 exact Snapshot、declaration/`CALLS`、Citation、只读来源和 loopback Web，不复制 validation-only 入口。
- New chain：World Model Cognition + Conversation Context → 主 Agent 维护目标/计划并选择受控工具 → Source Broker/Worker → append-only Ledger →
  逐轮双分区 Package → 主 Agent 自然综合 → fresh independent Reviewer；Finding 回到主 Agent 补证或重写，再形成后继 Package、答案与 Review。
- Earliest Web micro-checkpoint：最小链一旦完成，立即交付能建立/继续/新建 Conversation 的真实 Web Access；此时可标记“质量未验收”，不用孤立 live question 冒充 Chat。
- Fast checkpoint：一个真实工程上的一条至少三 Turn 语义链，覆盖初始问题、省略指代追问或用户纠正、进一步区分/深入或按 current Context
  总结；另加两个未参与修复的异质问题和新 Conversation 泄漏负测，然后立即形成三臂方向信号。
- Deferred hardening：持久恢复、复杂冲突、跨轮去重、完整异常矩阵、第二工程、全面性能、完整回归和 hidden 留到方向 `CONTINUE` 后；
  小样本三臂方向信号在当前快速体验后完成，完整五轮套件不阻塞当前体验。Slice1 仍须保留实际发生的
  Conflict/Gap/Failure/Partial/Unknown。
- Stop：世界模型被手册化；调查一次性固定；模型直接 Source；任何特判；Ledger/Package/Review 身份错配；答案仍是代码走读；错误、安全
  或审核降级；用户 REDIRECT/REJECT。

## Direction preview checkpoint

历史 `V-WEB-000/V-WEB-001/V-EXPERIENCE-001` 已保存原单轮 Web PASS/FAIL 事实，但不证明 Chat，也不可改写为新 Gate。PDR-004 的五轮
`V-CHAT-EXPERIENCE-001` 设计保留为历史；PDR-005 当前方向体验是在同一页面和固定工程/revision 上完成一条至少三 Turn 的真实语义链，
再回答两个未参与修复的异质问题。新 Conversation 负测必须澄清省略指代，不能继承旧 Context、Evidence 或 Provider memory；任一 Turn
失败只关闭该 Turn，不终止 Conversation。完整五轮套件仅在用户 `CONTINUE` 后执行。

页面只监听 `127.0.0.1`，普通用户无需认证，持续显示“Alpha / 非验收 / 非生产”、产品与工程版本及已知限制。默认展示问题、直接答案或
Limitation、可打开 Citation 和请求级状态；World Model Cognition、Ledger、Broker 操作、Package、调用数、Review Finding 和授权诊断折叠
到开发者详情。只有实际持续体验达到这些条件，才允许用户判断是否进入工程夯实；单题失败本身只进入返工清单。

## Current vs expected behavior

历史 frozen/live 产品能在 World Model 上做有界调查并给出代码行为，但 launcher 只接受启动前精确准备的一道问题；其默认正文会机械
展开方法、分支和调用顺序，Reviewer 可能漏判重要副作用。candidate `b6e13eb…` 的首次持续 Alpha 已真实启动并再次执行现场登录题；完整
Service source 已进入 Package/Reviewer，正文仍遗漏成功登录审计写入且 Review 错误 `APPROVED`，因此该 Result 只作为失败证据，不构成
`V-EXPERIENCE/V-ANSWER-REWORK` PASS。`FINDING-010-033` 把根因定位到宽泛 checklist 可被代表性事实伪闭合，并以协议 `@3` 的原子
evidence observations、Answer observation/evidence closure 与 Reviewer 独立 Package/Draft observation audit 做通用修复；
`FINDING-010-034` 同时修复该会话暴露的 Gateway SQLite `0644` 主文件/WAL/SHM 权限缺口。clean candidate `fc827ce…` 已绑定 current
DeepSeek Conformance 重跑原题；Package/正文覆盖了登录审计副作用且 private DB 成立，但 coverage-only Limitation 被非空 observation-link
规则强迫错绑 supported observations，Draft 因而失败关闭。`FINDING-010-036` 把该通用组合缺口收窄为仅末尾 coverage limitation 可用空
link；该修复尚未成为新的 clean frozen candidate，也没有原题加两道异质题的完整真实执行证据，因此不能把失败行为写成已修复。

随后 clean candidate `e15ec50…` 已绑定 current DeepSeek Conformance 再跑原题；空-link coverage Limitation 已按预期生效，但 Investigation
在只读 README 后过早以全局 Unknown 结束，Answer 又把 limitation observations 错标为 process/impact roles，Domain 因而失败关闭。
`FINDING-010-038` 不放松 Domain，而是显式下发合法 kind/role mapping，并要求 UNKNOWN/CONFLICT/FAILED FINISH 前尝试仍可直接减少
material unknown 的已授权 evidence class。该修复也尚无新的 clean/live 证据。

后续 clean candidate `8575517…` 已使原现场登录题实际读取源码并以 8 次 dispatch 得到完整 `APPROVED`，但同会话两道异质题分别在 13/10
次 dispatch 后失败关闭：Application 把全部 registered class 当作 non-supported FINISH 的必经闭包，挤占了决定性源码调查；Provider-facing
FINISH schema 又允许 `SUPPORTED` disposition 混入 `LIMITATION` observation，直到 Domain 才拒绝。`FINDING-010-047` 现由 Question
Understanding 声明逐题最小 `required_evidence_classes`，Application 只闭合 untried required，且 closed schema 与 Domain 同时强制
supported/affirmative、non-supported/limitation 的一致组合。该修复仍须新 clean candidate、fresh Conformance 和持续三题现场执行。

该处置形成 clean candidate `5ce5ab0…`，run-015 fresh DeepSeek Conformance 2/2 PASS；但原始 SQLite 复核否定了页面的两个
`APPROVED`。原登录题再次漏掉 `insertLoginLog` 持久化审计副作用；混合构建/安全/unknown 题的 Answer 输出两个
`DIRECT_ANSWER` 而失败关闭；401/403 题只读 manager 接线、未读 `DynamicAuthorizationManager` 自身实现，却错误声称动态权限行为已支持。
`FINDING-010-048` 因而新增 exact mandatory-read path closure、结构上唯一的 `direct_answer` 与独立 side-effect checklist/audit；旧会话
3 题、32 dispatch、retry/switch 0、private files 和 Production `NOT_EXECUTED` 只保留为失败诊断。定向 96/96、docs 442/442，允许
AF_UNIX 的 full 1162/1157 且只保留既有 4 FAIL + 1 ERROR；新 clean/fresh live 仍待执行。

该处置形成 clean candidate `00afecd…`，run-016 fresh DeepSeek Conformance 2/2 PASS；但同一持续会话的三题都未形成可交付答案。原题在
第 12 次总 dispatch 遇到一次真实 post-dispatch `PROVIDER_OUTCOME_UNKNOWN`，页面又误报 binding drift；另外两题各用满 12 次
Investigation，分别因 8/6 个 mandatory-read paths 与非必读 locator 消耗而无法 FINISH。terminal receipt `sha256:b3c94c2…` 记录
3 题、38 dispatch、retry/switch 0、private files 和 Production `NOT_EXECUTED`；超长输入仍在 Provider 前拒绝。`FINDING-010-049`
现把 mandatory-read 上限收紧为与 12-call fuse 可达的 4，未闭合时只暴露 required locator 并投影剩余 fuse，同时准确传播 exact-binding
outcome unknown；旧三题仍全部是失败证据。

该处置形成 clean candidate `d12223f…`，run-017 fresh DeepSeek Conformance 2/2 PASS。新的 4-path required closure 已使三题调查全部进入
Answer；构建/安全/resources unknown 题以 14 次 dispatch 获得 `APPROVED`，但原登录题和 401/403 题分别在 9/12 次 dispatch 后因
follow-up role 顺序为“process → impact → process …”而在 Review 前失败关闭。两份 raw Answer 的 checklist、observation、evidence
links 与内容齐全，失败只来自 Provider 后补 process claim 时打破全局 role 顺序。terminal receipt `sha256:e901faf2…` 记录 3 题、35
dispatch、retry/switch 0、private files 和 Production `NOT_EXECUTED`；22,000 字符输入继续在 Provider 前拒绝。`FINDING-010-051`
现保留 Gateway raw output，只在可信 adapter 内按既有受控 role 稳定归一化 follow-up 展示顺序，不改写任何 Claim 语义或 links；旧会话仍是
1 PASS + 2 FAIL 诊断证据。

该处置形成 clean candidate `88e33bd…`，run-018 fresh DeepSeek Conformance 2/2 PASS。原登录题和构建/安全/resources unknown 题分别以
13/15 次 dispatch 获得 `APPROVED`；401/403 题以 8 次 dispatch 进入 Answer，三个检查面、失败区分与 Citation 均已形成，但用户明确要求的
源码核对依据被正确分类为 `IMPLEMENTATION_EVIDENCE` 后无条件移出 `USER_VISIBLE_EXPLANATION` 正文，使其独自承载的 3 个 observations
不可见并在 Review 前失败。terminal receipt `sha256:08d84045…` 记录 3 题、36 dispatch、retry/switch 0、private files 和 Production
`NOT_EXECUTED`；22,000 字符输入继续在 Provider 前拒绝。`FINDING-010-053` 现只隐藏 observations 已由其他可见 Claim 完整覆盖的实现
证据，uniquely material 的简洁核对依据保持可见，部分交叠仍失败；旧会话保持 2 PASS + 1 FAIL。

该处置形成 clean candidate `c65617e…`，run-019 fresh DeepSeek Conformance 2/2 PASS。同一持续会话三题分别以 12/15/12 次 dispatch 获得
模型 `APPROVED`，且第三题 requested implementation evidence 已进入默认正文；但独立技术复核发现其一处把未认证与权限不足都写成 403，
后一处又正确分流为 401/403。raw Review 逐字复述冲突仍全 PASS。terminal receipt `sha256:cfed19a1…` 记录 3 题、39 dispatch、
retry/switch 0、private files、verified transport 与 Production `NOT_EXECUTED`；22,000 字符输入仍在 Provider 前拒绝。见
`FINDING-010-055`；旧会话按 2 个独立可接受答案 + 1 个 independent-quality FAIL 保留。

该处置形成 clean candidate `274e5ea…`，run-020 fresh DeepSeek Conformance 2/2 PASS。原登录题以 10 次 dispatch 获得独立可接受的
`APPROVED`；构建/安全/resources unknown 题虽已声明 4 个 exact mandatory paths，却因 Application 只给 search-issued locator 而没有
direct locator，把 path/filename 当内容搜索词，5 次 dispatch 后以 `NO_PROGRESS_FUSE_EXHAUSTED` 关闭。listener 未重启即接受 401/403
题，证明单题隔离；该题以 11 次 dispatch 完整读取 4 个决定性实现后，在一个 `SUPPORTED` FINISH item 中混入 `LIMITATION` 和
search-only boundary reference，被本地 validator 以 `STRUCTURED_OUTPUT_INVALID` 正确关闭。随后 22,000 ASCII 字符因仅约 22 KB、低于
65,536-byte 服务端上限而合法发生 1 次 dispatch，人工停止会话。terminal receipt `sha256:1408e827…` 记录 4 题、27 dispatch
（10/5/11/1）、retry/switch 0、verified transport 与 Production `NOT_EXECUTED`。`FINDING-010-057/058` 现分别签发 Request + attempt +
Profile-bound mandatory-path direct locator，并把 Provider-facing FINISH 拆为结构互斥的 supported/non-supported arrays；run-020 仍是
1 个独立可接受答案 + 2 个业务题 FAIL + 1 个被人工中断的限界探针。

该处置形成 clean candidate `dfba244…`，run-021 的 Q1/Q3 各以 8 次 dispatch 获得独立可接受的 `APPROVED`，Q2 也已 direct READ
全部 4 个 mandatory paths；但 Q2 把 3 个 UNKNOWN 同时复制进 supported/non-supported arrays，并在尚余 8 个含当前动作 call 时
FINISH，被本地 Schema 正确关闭。66,000-byte 输入在 Provider 前拒绝，Gateway 根保持 22。`FINDING-010-060/061` 已要求 FINISH
partition disjoint + exact-once，并把 mandatory paths 明确为 minimum 而非调查上限；run-021 仍是 2 个独立可接受答案 + 1 个业务题 FAIL。

该处置再形成 clean candidate `be15a0a…`，run-022 的 Conformance 2/2 PASS；首题第一个 Investigation 选择合法 direct locator 与 current
basis，却返回空 `checklist_item_ids`，被 Domain 正确关闭。根因是 Provider Schema 允许 checklist/basis 数组为空或重复，而 Domain 要求
non-empty + unique。会话在 2 次 dispatch 后停止，未提交其余问题；`FINDING-010-062` 现使 Initial/Verification Provider Schema、Prompt 与
Domain 的两个 binding arrays 对齐，不用旧 run 补齐新 candidate 的体验证据。

该处置形成 clean candidate `656b549…` / run-023；fresh Conformance 2/2 PASS，同一持续 Alpha 顺序完成三题 8/8/7 dispatch，
retry/switch 0，66,000-byte UTF-8 输入继续在 Provider 前拒绝且 listener 可用。Q1/Q2 独立可接受；Q3 虽获模型 `APPROVED`，却从
token filter 的 empty-context 与 authorization manager 的 deny decision 无据推出最终 401/403，把同一 unauthenticated 条件分配到互斥
外部结果，Reviewer 仍误判 consistency PASS。`FINDING-010-064` 要求 externally visible status/error/body 由下游 response/exception
mapper 的 full-content implementation 支持；custom-handler wiring 只证明选择，transport status 与 application/response-body code 分开。
Prompt 升为 `@26`；run-023 永久保留为 Q1/Q2 可接受、Q3 独立重大质量 FAIL，不能取得三题 Gate。

后续 clean `740c74a…` / run-024 证明两类重复 Provider 状态仍会破坏闭包：FINISH parent 漏抄 child reference、同一 UNKNOWN item
重复分装，以及 Reviewer 已形成 typed evidence gap 后仍独立维护不一致 action/request。`FINDING-010-066/067` 已把 FINISH 收敛为单一
outcome-tagged list、由 trusted Adapter 派生 parent reference，并让 Application 从 typed remediation 派生 Review action/request；
`FINDING-010-068/069` 闭合 deterministic Gate。

该处置形成 clean `7fb7e7c…` / run-025：fresh Conformance 2/2 PASS，同一持续 Alpha 三题使用 8/13/12 dispatch，retry/switch 0；
66,000-byte UTF-8 输入在 Provider 前拒绝，private files、listener continuity 与 Production `NOT_EXECUTED` 成立。Q1 独立可接受且四个
Citation 已打开核对。Q2 的 Reviewer 正确派生只绑定 `check-3` 的补证 Request，Verification 也正确只返回一个 `check-3` disposition，
但 Application 仍要求重报完整四项 Checklist 而错误关闭。Q3 在所需 handler implementation 不属于本次 exact Source allowlist 时，
重复 intent 被 Broker/no-progress fuse 安全关闭。`FINDING-010-070/071` 因而把补证 FINISH 定义为单 gap delta + trusted merge，并将
predecessor Package full-content paths 与最新 Broker rejection 提升为补证控制状态；run-025 仍是 1 PASS + 2 FAIL，不能取得三题 Gate。

上述处置形成 clean `32a00a3…` / run-026。fresh Conformance 2/2 PASS；持续三题分别使用 8/12/14 dispatch，retry/switch 0，
66,000-byte 输入在 Provider 前拒绝。Q1 `APPROVED`；Q2 的 Verification `UNKNOWN` observations 错借 predecessor Package 中描述
数据库/JWT/端口的 cognition unknown，Answer observation/evidence closure 正确失败；Q3 已诚实保留 handler implementation limitation，
Reviewer 却再次请求同一已穷尽 gap 并触发 preview Verification fuse。`FINDING-010-073` 因而把 predecessor boundary 从补证
admissible 域排除，强制每个非支持 observation 绑定 current gap，并把 terminal verified gap 投影给独立 Reviewer。run-026 仍是 1
PASS + 2 FAIL，不追认三题 Gate。

预期行为是：同一 Conversation 中，主工程 Agent 持续维护用户目标、假设、子任务、计划和完成判断；它组合 exact World Model Cognition、
sealed Conversation Context 与每次受控工具观察，自适应选择下一步或结束。Broker/Worker 仍控制 actual read，Agent 没有直接 Source/FS/Shell/network/credential/write 权限。
Application 每 Turn 密封 Package，主 Agent 综合答案；fresh independent Reviewer 只返回具体 Finding，Finding 回主 Agent 决定补证或重写。任一 Turn 失败不会污染后续 Turn 或关闭 Conversation。

## PDR-004 accepted system baseline as amended by PDR-005

- ADR-018 和 Engineering Conversation Contract 是唯一默认主链 Owner。主 Agent 持续负责目标、假设、计划、工具选择、观察解释、重规划和答案综合；
  Application/Control Plane 负责 exact revision、授权、Broker/Worker、证据身份、安全熔断和审计。
- Application 以 Cognition Capability Manifest 组合同一 revision 上各 Profile 的 exact Read Authority，并按问题 material Need 决定资格和投影；
  Maven-only 只具备结构/locator 资格，不得用于声称行为、调用、职责、配置或故障认知完整，也不得创建 mixed-profile Snapshot/Read Set。
- Application 拥有 Conversation/Turn/Context 与 Agent Work State。Context 只携带确认的目标/约束、指代实体/主题、开放问题、reviewed/superseded conclusion refs 和 exact provenance；
  prior Answer/Review、用户陈述和 Provider hidden memory 不取得 Source truth 权威。
- 主 Agent 只能通过注册的 World Model query 和 Broker/Worker source search/read 工具工作；每次观察、拒绝、资源收据、Gap/Conflict/Unknown 只追加到当前 Turn Ledger。
- 每 Turn 完成后密封双分区 Evidence Package；主 Agent 仅基于当前可授权证据作答并为重要结论绑定 Citation。seal 只证明身份/完整性/来源/版本，不证明内容为真。
- fresh independent Reviewer 审查 original Turn、Context Projection、Package 和 Answer，仅返回绑定 Claim/evidence class/need 的 Finding。Finding 交还主 Agent；任何补证都形成新 Ledger/Package/Answer/Review identity。
- 旧 `ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3`、固定 Investigation/Verification Investigation 角色、双 Review 和 focus challenge 仅是历史/兼容资产，不是 current 主 Agent 拓扑或验收要求。
- Ark→DeepSeek fallback 从 original Turn、relevant sealed Conversation Context 和 exact Cognition 启动完全隔离 attempt；不复用 primary 中间态，同 Provider retry 为 0，late result quarantine。
- 模糊指代在 Source/Provider dispatch 前澄清；新 Conversation 不继承旧 Context/Work State/Evidence/Provider session。所有问题使用同一协议，禁止工程/问题/关键词/符号/类/方法/fixture/Oracle 特判。

## Historical `@3` implementation contract (non-normative)

本节至“Historical interfaces”只保留 PDR-004 前已执行单轮实现的 exact 证据和兼容约束。其中的“必须/不得”、固定角色、`@3`、双 Review 和 Verification Investigation 都只描述历史协议，不得用作 current 开发指令。

### Historical Phase 0：当时的正式边界

开发前必须确认 `FINDING-010-002`、`SYS-ADR-016`、Engineering Question Answering Contract、Product Success、runtime/Agentic/Evidence/
World Model/Response/Source/Security/Browser 文档和治理门禁共同表达 `ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3`。严格 `WORLD_MODEL`
Source-off 和显式 `DIRECT_INVESTIGATION` 继续保留，不得静默 fallback。任一 current Owner 或 Manifest digest 不一致即停止。

### Historical Phase 1：当时的最小真实协议

- Request 固定 immutable original question、exact repository/revision、World Model Context/Scope/Schema/Snapshot、source allowlist、
  Binding-scoped versioned Source Profile ref/digest、Provider disclosure policy 和资源上限；问题或运行状态不能改变这些身份。
- World Model Cognition Context 提供实体、关系、行为、约束、状态、证据、coverage 和 unknown boundary。手册/地图只是投影；Snapshot
  为零或不足不能阻断授权 Source 调查。
- Investigation LLM 是独立角色，只能读取原问题、认知上下文和当前 append-only Ledger；每次只能提出注册的抽象 search/read/parse/
  finish 意图。下一步必须引用 prior Result/progress，不能一次性预写固定列表，也不能按题目/工程/关键词/符号路由。
- Source Broker 把提议的 evidence class 也视为不可信，按 exact Source Profile 验证并编译操作、版本、路径、global/class
  allowlist、bytes、disclosure 和安全上限。Retrieval Worker 重验 Profile 后只执行 Broker 批准的 exact-revision、read-only 操作，
  Application 再验证 Result class/path。已验证 mandatory path 由 Broker 签发 Request + attempt + Profile + class + path 绑定的 direct
  opaque locator；模型只复制当前 eligible reference/class，不能提交 path authority。两者都不生成答案；模型没有直接
  FS/Shell/network/credential/write/source authority 或来源分类权。
- 每次认知查询、提议、Broker decision、操作、Result、locator、digest、bytes、truncation 和 progress 只追加到本题 Evidence Ledger。
  只有合法 `FINISH` 或失败关闭 stop 后才能 seal；不得覆盖历史或在调查完成前密封。
- Question Understanding 必须声明回答 checklist 直接需要的最小受控 evidence-class 集合及 1—4 个 exact mandatory-read paths；多机制/
  检查面选择各决定性实现，flow/lifecycle 把结果、状态变化与持久化/审计/缓存/通知/外部交互副作用拆成独立 checklist。
  startup/call/use/integrate/diagnose 类问题还把 prerequisite/build-start、首个请求与输入、返回值、跨步骤 handoff、结果/失败和 runtime
  unknown 拆成 operational checklist，不能以依赖或组件 inventory 代替。4-path 上限与 12-call initial fuse 保证 4 次 direct
  READ/PARSE + 1 FINISH 后仍有 7 次自适应余量；可选佐证不得占用 mandatory capacity，也不能因
  evidence modality 可用或用户只要求“可核对依据”就引入无关 TEST/log/config need。
  Application 区分 registered/required/investigated/untried/unregistered classes 与 required/unread paths；向 Initial Investigation 投影 exact
  maximum/remaining calls，并在 unread required path 存在时投影 direct locator descriptor 且只暴露这些路径的 eligible locator；角色优先
  直接读取，不通过内容 SEARCH 重新发现已知 path。任何 FINISH 前都必须以无行范围、
  `coverage_complete=true` 的 READ/PARSE 闭合 required paths，SEARCH/截断内容不消费义务；non-supported FINISH 只额外闭合仍可调查的
  required class，不机械遍历无关 registered class，unregistered required 则保留为能力边界。
- 每个 FINISH disposition 必须从完整引用内容列出有界原子 material observations，区分 process、outcome、state change、side effect 与
  limitation，并逐条绑定 admissible evidence；`SUPPORTED` 只能包含 affirmative observation，non-supported outcome 只能包含
  `LIMITATION`。Provider-facing output 只用一个 outcome-tagged `finish_dispositions` 数组且不重复 parent references；可信 adapter 按
  child observation 顺序稳定汇总 exact references。Initial authorized scope 是完整 Question Checklist；Verification scope 只有 Request
  指定的一个 gap，FINISH 只能返回该 gap delta。Application Domain 独立拒绝越权、混类、非 exact-once、错误证据分区或证据不闭合；
  成功补证后由可信 Application 按 predecessor 顺序替换唯一目标 disposition、原样保留所有非目标项并形成 successor Package，失败关闭
  不执行 merge。
  一个代表性事实不能闭合宽泛 checklist。Application 生成稳定 observation identity 并拒绝跨 checklist 或重复。
  caller/configuration/wiring 只证明接线，不能替代被委托组件自身
  的条件、比较、状态变化、结果或失败语义；每个相关 full-content 实现 entry 中的 material side effect 必须单独观察。
- Question Evidence Package 保持一个 seal/identity，但内部严格分区：`support/citation` 只收经 modality、Context、Coverage 和 Support
  校验通过的可采信条目，只有它们能支持肯定 Claim 与 Citation；`boundary/audit` 必须保留 Gap、Failure、Partial、Conflict、Unknown、
  拒绝决定和资源收据，只能约束结论或形成标记清楚的边界说明，不能支持肯定 Claim。seal 不把任何条目或模型推断变成真。
- Answer 在全新上下文中只读当前 sealed Package。closed output 由唯一必填 `direct_answer` 和禁止直答的 follow-up `claims` 组成；混合
  Package 以 affirmative direct summary 回答 supported 部分，non-supported 部分只进末尾 limitation follow-up。Question Understanding
  使用受控 detail level；每个 Claim 声明 role 并绑定 material checklist；表达 material fact 时还绑定文本实际表达的 observation IDs。仅末尾
  coverage-only Limitation 可以使用空 observation link 且只引用 boundary/audit，不能承载 affirmative fact、错绑 supported observation
  或替代 Package observation 覆盖。Application 强制直接答案排首位、全
  checklist/observation 覆盖、每条 observation 默认可见、disposition/证据分区一致且 Claim 引用 observation 所需全部 Package entries；
  真实边界可直接回答 limitation。`USER_VISIBLE_EXPLANATION` 默认正文不展开实现证据，但流程阶段、结果、状态变化和副作用不能被归为可选
  实现详情。
- Answer input 在原问题与大型 Understanding/Package 对象之前提供 exact material-observation coverage table，逐项列出 observation ID、
  statement、kind、checklist 和 required evidence entry。初答与 rewrite 都必须在默认正文恰好覆盖每项；收窄一个越界推断不能删除同一
  Claim 原先承载的其他安全 observation。startup/call/use/integrate/diagnose 类问题还必须按动作顺序连接 material output 与下一步
  input，并分开已知值和 configuration-backed unknown；组件清单不能替代用户可执行 handoff。
- Reviewer 在另一个新上下文中读取原问题、理解记录、当前 Package 和 Draft，无 repo/Source/World Model tool、FS、Shell、network 或
  credential。它从原问题独立重建 material conclusions、列出 Application checklist omission；再检查完整 Package evidence，独立形成带
  evidence entry 的原子 observations，分别列出 Package 与默认 Draft omission，并给 direct answer、abstraction fit、material
  completeness、claim consistency、implementation-detail budget 返回 PASS/FAIL；对 flow/lifecycle 它逐 full-content entry 审核
  持久化/审计/缓存/通知/外部交互，对多机制检查各决定性实现而非 caller/wiring。五项全 PASS、所有 omission 为空且无 Finding 才能
  派生批准。Provider 不单独返回 decision/request：表达缺陷使用绑定 current-Package entries 的
  `REWRITE_WITH_EXISTING_EVIDENCE`，material 证据缺口使用绑定 Checklist/Claim/evidence class/need 的
  `INVESTIGATE_MISSING_EVIDENCE`，不可恢复失败使用 `REJECT_UNRECOVERABLE`；可信 Application 按固定优先级派生 action 与 versioned
  Verification Request。Reviewer 不能提出可执行 path/command/operation，也不能因 Draft 扩张了原问题不要求的细节而扩大调查。
- 上述 finding-free Review 只是 `COMPREHENSIVE` provisional approval。Application 从当前 Package/Draft 投影 cited configuration
  placeholder、Claim 中 cited content 未出现的 HTTP status literal、Draft 提及但实现未挂载的 same-application type，以及每个被默认正文
  Claim 引用的 full-content Java support entry 的独立 material-effect scan，并为每个 scan 投影该 entry 已有的 exact Application
  material observations；entry 归属必须通过 support entry 的 `source_reference` 解析 observation evidence references，不能直接比较
  `support_entry_*` 与 `retrieval_item_*`。此外每个有默认正文和引用 entry 的 Draft 投影一个
  original-question fulfillment scan，检查 direct goal、ordered actions、input/output handoff、known/unknown boundary 与 material
  outcomes，随后使用另一个 fresh context 执行
  `EVIDENCE_BOUNDARY_CHALLENGE`。lead 不自动判错，但 challenge 必须区分 placeholder/key 与 runtime value、caller/getter/import 与 DTO
  fields/wire property/handler output、上游 local state 与下游 status，并逐 entry 检查 persistence/audit write、cache mutation、
  notification 和 external interaction。每项 lead 具有 Application-owned 稳定 `challenge_id`；challenge 必须恰好逐项返回 evidence
  scope、Draft scope 与 `WITHIN_EVIDENCE_BOUNDARY / DRAFT_EXCEEDS_EVIDENCE_BOUNDARY / DRAFT_OMITS_MATERIAL_EFFECT /
  DRAFT_OMITS_MATERIAL_REQUIREMENT`。material-effect omission 还必须返回 exact effect statements 和
  `APPLICATION_PACKAGE / DEFAULT_DRAFT` layer：前者只允许同 evidence class Verification，后者只允许 exact projected observation
  已存在时绑定 challenged entry rewrite。空 observation 投影存在 omission 时只允许前者；两层 omission 同时存在时先只返回
  Application-Package 缺口并形成 successor Verification，后继 Package 再审核 draft-only omission。后两种专用 disposition 必须与对应 challenge kind 匹配；所有非 passing
  assessment 都必须绑定同输出中作用于该 exact challenge Claim 的 Finding，只有 Claim 同时属于每个 challenge 时才允许复用 Finding
  code。Application 重算 exact ID 集合，Gateway 强制 focus 顺序；只有集合完整、全部 `WITHIN_EVIDENCE_BOUNDARY` 且 finding-free 的
  challenge 才可 Authorization。Package 已有 observation 时的 Draft omission 走同包 rewrite；full entry 已证明但 sealed Package 缺少
  observation 时走 successor gap delta，并允许复用 predecessor support。每题为 Answer + 双 Review 预留 3 calls，Review attempt 上限 4，
  hard 24-call fuse 不变。
- 合法 Request 启动独立 `Verification Investigation LLM`。它使用全新上下文，只读具体 gap、当前 Package 与 Ledger prefix，根据每步新
  Result 自适应提出 search/read/parse/finish；predecessor Package 已含的 full-content exact-source locators 与 gap 后 full reads 共同
  标记为 consumed，相应 locator 不再 eligible，旧 raw Result 不重新进入输入。当前 attempt 最近一次 Broker rejection 以受信控制状态
  显式投影，角色必须选择真正不同的合法 action 或诚实 FINISH。每一步仍由 Application/Broker 校验编译、Worker 执行；上述状态都不授予
  新 path/operation。predecessor Package 的 boundary source references 不得进入补证 admissible boundary；角色取得唯一 current gap
  boundary，每个 non-supported observation 必须保留该 reference。它不回初始 Investigation LLM，不继承 Reviewer 会话，也无直接来源
  权限。完成后追加新 Ledger Revision、密封新
  Package、完整生成新 Answer 并重新执行 comprehensive + challenge Review；旧 Review 不得批准新包。
- Package 将 Initial Investigation 的普通 `GAP` 与 `VERIFICATION_REQUEST` 的 typed `VERIFICATION_GAP` 分开密封。Review 输入只将真实
  绑定 `VERIFICATION_GAP` 的 non-supported successor disposition 投影为 terminal `verified_gap_outcome`。Draft 诚实
  保留该 limitation 且不暗示缺失肯定结果时，Reviewer 不得再次请求同一缺证；Draft 自行扩张、删除后仍完整回答 original/checklist 的
  status/body/error detail 必须同包删除或收窄，不能扩大调查。
- 为尽快验证方向，Slice1 每个问题最多冻结一次 Verification Investigation；这是 preview 的临时安全边界，不是永久协议。Slice2/3
  禁止固定一轮上限，改为在各自 exact freeze 前预密封 Package Revision、model call、Broker operation、source bytes、wall time 与
  no-progress 高安全熔断。answerable 因任一熔断耗尽而未回答必须计 `FAIL`，不能用 Limitation 取得 supported 分数。
- 调用、步骤、文件、bytes 和 wall time 是高安全上限。达到上限失败关闭；只有预先分类的真实 boundary 才能交付独立审核认可的准确
  Limitation，answerable 因上限耗尽未回答必须计 FAIL。不能删减调查、checklist、Evidence、Citation 或 Review。
- 交付后的高质量证据/结论可异步提议 Knowledge Update，不能阻塞或追认本题答案。

## System contracts and invariants

current 目标由 `SYS-ADR-018` 和 `SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 拥有，并继续遵守
`SYS-CONTRACT-APPLICATION-AGENTIC-TASK`、Response Control、Source Artifact 与 Security 边界。不可破坏的语义是：世界模型、
Conversation Work State 和 Turn Evidence 三者分离；主 Agent 拥有目标、假设、计划、工具选择、观察解释、重规划和完成判断；
Application/Broker/Worker 拥有 exact revision、授权、只读执行、证据身份和审计；每个 Turn 经 fresh independent Reviewer 后
才能由 Response Control 放行。旧 `ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3` 只是历史兼容协议，不得覆盖这些 current 语义。

## Interfaces and affected code

当前授权下的最小产品变更只能落在 Conversation/Turn/Application-owned Work State、主 Agent 工具循环、逐 Turn
Ledger/Package/Review/Delivery 编排与现有 loopback Web 交互面。它应复用现有 World Model query、Source Broker/Worker、
Citation、Provider Gateway 和 Response Control，不另建旁路。具体类、函数与迁移步骤由实现调查决定；不得把开发授权扩大为 live、
外部披露、hidden、后续 Slice 或 Production 权限。

## Historical interfaces and affected code (non-normative)

当时已消费的历史 Slice 授权曾允许修改 Application orchestration、Investigation/Verification Investigation role、Source Broker port/policy、Retrieval Worker adapter、Evidence Ledger/Package、
Response Control、Answer/Review Strategy、role-specific Gateway input、product-owned HTTP/Web 及对应 tests。优先复用现有 World Model Query、
Evidence Answering、Citation 和 Web 组件，不复制 ITER-009 pipeline。

源码路径不能直接传给模型后依赖 prompt 自律；模型只能提出 Broker 能验证的抽象意图，且其 evidence class 声明不能把一个 Profile
未登记的路径重标为源码、仓库文档、配置或测试。所有自然问题进入同一协议，UI 不按问题维度切换后端。禁止工程、题目、关键词、
符号、类、方法、约定文件名、fixture 或 Oracle 特判；来源类型由显式 versioned Profile capability 决定。

## Compatibility, data and security boundaries

严格 `WORLD_MODEL` no-payload/Source-off、Citation 和历史 accepted 测试继续成立；新协议使用独立 identity。源码、README、注释、配置、
测试均视为不可信输入，其内容或模型声明不能获得 evidence class 权威；拒绝 Source Profile 漂移/类型重标、symlink escape、
submodule/remote 自动获取、binary、oversize、path traversal、写、执行和网络。

历史 original question/Cognition/Ledger/Package/Draft/Review/补证角色 identity 保留原 ID/digest，不作为 current 拓扑。PDR-004 的 Conversation、Turn、Context Projection、Agent Work State、
Ledger Revision、Package、Answer、Review、Finding 和 Delivery 各自保存稳定 identity。Slice1 的 Turn-scoped Ledger 必须只追加且能形成完整 Result；跨进程持久恢复与复杂幂等 replay 明确后移到 Slice2。live
前另行冻结 exact
Provider/model/role、fragment allowlist、redaction、configuration、secret reference 和 audit；计划与开发授权都不允许自动外发。
持续问题 POST 还必须在 receipt/transport/credential 前满足 exact same-origin `application/json`；跨站 simple request 不能仅因目标是
loopback 就取得题目提交权。

## Open questions and implementation risks

- 调查模型可能循环或过早 FINISH；最小版保留基本 progress/no-progress 安全关闭与 Application FINISH 检查，完整循环/异常矩阵后移。
- World Model 和 Source 冲突时必须把两者作为 `boundary/audit` 条目保留，不能默认源码或较新时间自动获胜；复杂冲突裁决留到 Slice2。
- 主 Agent 依据 Reviewer Finding 补证时可能重复已有调查；Slice1 只证明 Work State 可基于 current Package/Ledger 重规划并形成后继 identity，复杂 dedup/recovery 留到 Slice2。
- 一次方向 Conversation 不能证明跨工程泛化；它只判断方向，不能替代 Slice2/3。
- 更多模型调用可能增加成本；首版先证明正确职责和答案质量，随后测量，不因调用数目标删减工作。

## Acceptance scenarios

1. `V-LAYER-ATTRIBUTION-001`：在产品修改前，用现有 immutable run、exact Source、Snapshot/Cognition、Package/Draft/Review/Web 逐 material
   fact 密封 first divergence、downstream guard failure 与 display failure；外部调用 0。未 PASS 前不得改 Prompt/Schema/Tool/Review。
2. `V-COGNITION-ELIGIBILITY-001`：同一 exact revision 上形成 Cognition Capability Manifest，至少包含结构与实现/行为 Read Authority；
   三类问题逐 Need 绑定相关能力或 explicit Gap。Maven-only 对行为题必须 FAIL，Source 命中不得回填为 World Model 贡献。
3. `V-ALPHA-ACCESS-001` 已是 `PASS / access-only`，直接复用固定命令、loopback、无认证、消息历史、“新对话”和版本/限制/失败状态，不重做页面壳。
4. `V-TIMEBOX-CHAT-001`：PDR-005 附加恢复时限是归因 T+60、工程认知接 Web T+180、浏览器方向体验 T+240；Alpha 前 external call
   只允许另行授权的一个 Ark direction canary session，full regression=0。到点交付最后可运行版与准确 Gap并停止扩域。
5. `V-CHAT-EXPERIENCE-001/V-CHAT-001`：同一 Web 至少有一条“初问→省略指代追问或纠正→深入/总结”的真实语义链，并另有两个未参与
   修复的异质问题；三个独立问答不算 Chat。失败只关闭当前 Turn，新 Conversation 泄漏负测要求澄清且零继承。
6. `V-CHAT-QUALITY-001/V-CHAT-XD-001`：每 Turn 重大错误和 Reviewer 重大漏判均为 0，重要结论有 Citation；回答先解决用户目标，代码走读
   只作证据，Unknown 来自 Coverage/Need Gap；至少一项非 locator 结论由 eligible World Model Cognition 贡献并由 Source 核实/补充。
7. `V-COMP-ALPHA-001`：方向体验后先比较同 Agent source-only 与 eligible-cognition+source，再隔离 current Codex 强基线。Codex 保留真实
   客户端/model/reasoning/tools/权限，只作基线而非 Oracle/裁判；两个系统臂共享 Agent/model/tool/budget/cache/Reviewer。
8. `V-PREVIEW-002`：独立技术复核完成 A1—A3/A6 exact Verdict 与 A4/A5 early signal 后，用户结合真实多轮 Chat 和三臂方向信号决定
   `CONTINUE / REWORK / REDIRECT / REJECT`；只有 `CONTINUE` 才解锁完整五轮套件、hardening 和 full regression。

历史 PDR-004 五轮时间线及 `V-ANSWER-001/V-REVIEW-001/V-EXPERIENCE-001/V-TIMEBOX-001/V-ANSWER-REWORK-001/V-XD-001/
V-WEB-000/V-WEB-001/V-PREVIEW-001/V-REFLECT-001` 保留原定义、证据和 PASS/FAIL，不是上述 PDR-005 current Gate，也不能被新 Result 追溯改写。

## Architecture reflection checkpoint

新 Result 必须复核 A1—A3/A6：世界模型概念、主 Agent 的目标/假设/计划/工具观察/重规划、Broker/Worker 权限、逐 Turn Ledger/Package identity、fresh independent Review、持续 Chat Alpha、新对话隔离、安全、
成本/复杂度和全部 Finding。历史失败不删除；新 Result 证明原题与至少两个异质问题的通用修复，并由用户在实际连续体验后决定。
只有适用 Case PASS 且用户决定 `CONTINUE`，才可申请 Slice2；任一单题失败默认进入同 Slice `REWORK`，不会自动拒绝 Iteration。

## Findings

`FINDING-010-001` 保留默认工程问答需要受控回源的根因；`FINDING-010-002` 修正世界模型定义表达和提问期职责；
`FINDING-010-003` 将首轮实现遗漏的五角色结构化输出闭包处置为 exact input/schema receipt binding、可信坐标补入和失败关闭解码。
`FINDING-010-004` 将补证角色输入收紧为 current Package/Ledger 与 current gap 后新增 Result 的精确闭包，禁止旧调查 raw Result 绕过包分区。
`FINDING-010-005` 将 evidence class 从不可信模型声明收回受信 Source Profile：Request/Operation/Worker/Package 绑定 exact Profile，
Broker/Worker/Application 逐层验证 class-specific path capability 和 class + operation Result modality，禁止类型或静态观察模态重标。
`FINDING-010-006` 分离 Result 审计 identity 与 semantic progress identity，使重复相同 observation 触发 deterministic no-progress
熔断，而不是因新 operation digest 被误判为进展。
`FINDING-010-007` 把 parent Ledger seal 与 prior Package digest 一起写入 successor gap，并在 Verification Input、后继 Package seal 和
最终 Result chain 重验，禁止 gap、Ledger Revision 与 Package predecessor 混用。
`FINDING-010-008` 将 wall-time 从“调用前许可”改为每个角色/Projector/Worker 返回后、状态转换前也重验；达到上限的 `FINISH` 或
`APPROVED` 不取得 Package/Authorization 权威。
`FINDING-010-009` 收紧 WSGI ingress 为 unique-key JSON 与 exact `CONTENT_LENGTH` 完整读取，重复 key 或短读在产品路由前失败关闭。
`FINDING-010-010` 用真实持久 Structure Read Bundle 实现 bounded Cognition Projector，固定 Binding/revision/read authority、typed dimension、
Coverage 与显式截断 Unknown，不按问题裁剪或读取 Source。
`FINDING-010-011` 把 exact user run grant 收窄为每个动态 full-input/fragment digest 的一次性 role disclosure authorization，并由
Gateway 独立重验 root Request、Prompt/schema、Provider/configuration/qualification、角色顺序和 Result；DeepSeek 与 prepared Web 组合已
确定性闭合。`FINDING-010-012` 再补齐可信 loopback launcher：运行模块必须来自 clean exact candidate，并在 listener 前绑定 Bundle、
Source Profile、Request/run grant 和 0600 launch receipt，退出时密封逐角色/Gateway/TLS terminal audit；真实 Provider/browser 仍等待
product freeze 后形成执行证据。
`FINDING-010-013` 记录冻结前验证：focused 58/58、docs 389/389、compile/diff PASS；full 1108 中 1103 PASS，唯一 4 FAIL + 1 ERROR
精确属于 `FINDING-008-020` 的历史 runtime drift。raw suite 不写成 PASS，只允许 exact preserved historical hold gate 继续 clean freeze。
`FINDING-010-028` 至 `031` 记录本次返工的答案层级/Reviewer Gate、持续 Session Authority、rework Manifest parser 与 same-origin ingress；
`FINDING-010-032` 记录完整 1141 项只保留既有 4 FAIL + 1 ERROR historical hold。`FINDING-010-033` 记录首次持续 Alpha 仍发生代表性
事实伪闭合并升级为原子 evidence-observation contract；`FINDING-010-034` 记录 Gateway SQLite 主文件及 sidecar 的 private-mode 修复；
`FINDING-010-035` 记录新协议完整 1144 项中 1139 PASS、raw 只保留既有 4 FAIL + 1 ERROR historical hold；`FINDING-010-036` 记录
`fc827ce…` 原题已经覆盖审计副作用却因 coverage-only Limitation link 组合缺口失败关闭，以及对应通用 contract 修复；
`FINDING-010-037` 记录修复后完整 1147 项中 1142 PASS、raw 仍只保留既有 4 FAIL + 1 ERROR historical hold。现有 Alpha 运行只证明
缺陷可复现或部分约束生效；`FINDING-010-038` 记录 `e15ec50…` 的证据类过早结束与 illegal limitation kind/role pairing，并以通用 prompt/
input contract 修复。新修复仍只有确定性证据，真实三题体验 Gate 保持 NOT-RUN。
`FINDING-010-049` 记录 `00afecd…` 三题暴露的 mandatory-read path/fuse 不可达与 outcome-unknown 错误分类，并以 4-path capacity、
required-locator priority、remaining-fuse 投影和 exact terminal propagation 闭合 current System Contract；新 clean/fresh live 前体验 Gate
继续为 FAIL。
`FINDING-010-050` 记录上述修复后的 Engineering QA 97/97、docs 444/444 与允许 AF_UNIX 的 full 1163/1158；raw 唯一
4 FAIL + 1 ERROR 仍为冻结 historical hold，没有 ITER-010 新失败，但也不替代 fresh live。
`FINDING-010-051` 记录 `d12223f…` / run-017 的 4-path 可达性、一个真实 `APPROVED` 与两个同形 Answer role-order FAIL；处置只稳定
归一化 follow-up 展示顺序，Gateway raw 与 Claim 语义保持不变。Engineering QA 98/98 PASS。
`FINDING-010-052` 记录 docs 446/446、compile/diff PASS 与允许 AF_UNIX 的 full 1164/1159；raw 唯一 4 FAIL + 1 ERROR 仍是冻结
historical hold，没有新增失败。确定性 Gate 已闭合，新 clean/fresh live 仍待执行。
`FINDING-010-053` 记录 `88e33bd…` / run-018 的两个真实 `APPROVED` 与一个 uniquely material implementation-evidence visibility FAIL；
处置保留用户明确要求的简洁核对依据，同时继续隐藏完全冗余的实现详情并拒绝部分 observation overlap。Engineering QA 99/99 PASS，
docs 448/448、compile/diff PASS；允许 AF_UNIX 的 full 1165/1160 只保留既有 4 FAIL + 1 ERROR，见 `FINDING-010-054`。确定性 Gate
已闭合，新 clean/fresh live 仍待执行。
`FINDING-010-055` 记录 `c65617e…` / run-019 的三项模型 `APPROVED` 与一个独立发现的跨 Claim 失败语义冲突；处置新增 closed
`claim_consistency` 第五项 Gate，互斥结果必须 FAIL 并 rewrite。Engineering QA 99/99、docs 450/450、compile/diff PASS；允许 AF_UNIX
的 full 1165/1160 只保留既有 4 FAIL + 1 ERROR，见 `FINDING-010-056`。确定性 Gate 已闭合，新 clean/fresh live 待执行。
`FINDING-010-057/058` 记录 `274e5ea…` / run-020 的 Q2 mandatory-path rediscovery/no-progress 与 Q3 conditional FINISH schema 混类；
处置分别新增 Broker direct required-path locator 和结构互斥 FINISH arrays，并把“可核对依据”与无关 TEST/log/config need 分开。Engineering
QA 101/101、docs/compile/diff PASS；允许 AF_UNIX 的 full 1167/1162 只保留既有 4 FAIL + 1 ERROR historical hold，见
`FINDING-010-059`。确定性 Gate 已闭合，new clean/fresh live 仍待执行。
`FINDING-010-060` 记录 clean `dfba244…` / run-021 的 Q1/Q3 独立可接受、Q2 direct mandatory reads 成功后又 duplicate mixed
partition 并在 8 个 remaining-including-current calls 时过早 FINISH，以及真正 66,000-byte Provider 前拒绝。处置不重分区非法输出；
Provider Schema/Prompt 要求 supported/non-supported arrays disjoint 且 union exact-once，Investigation 则把 required paths 视为
mandatory minimum，并在授权未读来源和剩余 fuse 可达时继续缩小 material gap。Strategy/Initial+Verification/Prompt 升为
`@15/@7/@24`；Engineering QA 101/101、docs/compile/diff 与允许 AF_UNIX 的 full 1167/1162 exact historical hold 由
`FINDING-010-061` 闭合。deterministic Gate 已闭合，new clean/fresh live 待执行。
`FINDING-010-062` 记录 clean `be15a0a…` / run-022 首个 Investigation 的空 `checklist_item_ids` 被 Domain 正确关闭；根因是 Provider
Schema 允许空/重复 checklist/basis binding arrays。处置将 Initial/Verification Schema 与 Domain 对齐为 non-empty + unique，并在 Prompt
要求 exact current-input binding；三模块定向 65/65 PASS。
`FINDING-010-063` 记录 Engineering QA 102/102、docs/compile/diff PASS 与允许 AF_UNIX 的 full 1168/1163；raw 唯一 4 FAIL + 1 ERROR
仍是冻结 historical hold，没有 ITER-010 新失败。deterministic Gate 已闭合，new clean/fresh live 待执行。
`FINDING-010-064` 记录 clean `656b549…` / run-023 的 Q1/Q2 独立可接受与 Q3 downstream-response ownership FAIL；处置要求外部
status/error/body 回到 response/exception mapper full-content evidence，拒绝由 empty-context/deny/wiring 假定最终输出，并把 transport
status 与 response-body code 分开。Prompt 升为 `@26`，定向 65/65、Engineering QA 102/102、compile/diff PASS；完整 Gate 与新
clean/fresh live 待闭合。
`FINDING-010-065` 记录上述修复的三模块 65/65、Engineering QA 102/102、docs 459/459、compile/diff PASS 与允许 AF_UNIX 的 full
1168/1163；raw 唯一 4 FAIL + 1 ERROR 仍是冻结 V-009/Codex historical hold，没有 ITER-010 新失败。deterministic Gate 已闭合，
new clean/fresh live 待执行。
`FINDING-010-066/067` 记录 clean `740c74a…` / run-024 的三类 Provider 重复状态失败：FINISH parent 漏抄 child reference、同一
UNKNOWN checklist 重复分装进两个 arrays，以及 Reviewer 明确识别 material evidence gap 后仍另行声明 rewrite/null request。处置将 FINISH
改为单一 outcome-tagged list 并由 trusted Adapter 派生 parent reference closure；Review 只返回 typed Finding remediation，由可信
Application 按 reject → missing evidence → rewrite → empty-approved 派生 action/request。旧 run 不追认。
`FINDING-010-068/069` 校正历史 ITER-007 oracle 用 current System 文档重算冻结摘要的局部测试错误，并闭合新协议 deterministic Gate：
Engineering QA 106/106、current docs 463/463、允许 AF_UNIX 的 full 1172/1167；raw 唯一 4 FAIL + 1 ERROR 仍是冻结 historical hold。
new clean/fresh Conformance、持续 Browser 三题与独立答案复核仍待执行。
`FINDING-010-070/071` 记录 clean `7fb7e7c…` / run-025 的 Q2 Verification scope 契约错配，以及补证重复读取 predecessor Package 内容、
重复已拒绝 intent 的控制面缺口。处置将成功 Verification FINISH 收窄为单 gap delta，由 Application 可信保序合并，并把 Package full reads
与最新 Broker rejection 投影到角色输入；旧 raw Result、Source authority、duplicate/no-progress fuse 均未放宽。新确定性 Gate 与
clean/fresh run 仍须闭合，run-025 不追认为三题 PASS。
`FINDING-010-072` 已以 Engineering QA 109/109、docs 组合 142/142、历史 oracle 组合 74/74、current docs 466/466、compile/diff 与
允许 AF_UNIX 的 full 1175/1170 exact historical hold 闭合 deterministic Gate。下一步只能从新 clean candidate 执行 fresh Conformance、
持续三题与独立复核；旧 run-025 仍不追认。
`FINDING-010-073` 记录 clean `32a00a3…` / run-026 的 gap-boundary 错绑和 terminal verified gap 重复请求。处置排除所有 predecessor
boundary、强制每个 Verification non-supported observation 绑定本次 gap，并向 Review 投影可信 terminal outcome；Strategy/Prompt 升为
`@19/@29`，三模块 76/76 PASS。扩展 deterministic Gate 与下一 clean/fresh live 仍须闭合；run-026 不追认。
`FINDING-010-074` 已以 Engineering QA 113/113、docs 组合 146/146、历史 oracle 组合 78/78、current docs 468/468、
compile/diff 及允许 AF_UNIX 的 full 1179/1174 exact historical hold 闭合 deterministic Gate。下一步只能从新 clean
candidate 执行 fresh Conformance、持续三题、Provider 前负测与独立复核；run-026 仍不追认。
`FINDING-010-075` 记录 clean `b709fad…` / run-027 的 1 PASS + 2 错误放行：placeholder 被扩张为具体 header，caller/import 被扩张为
未挂载 DTO fields/handler output，上游 deny 被扩张为下游 401/403；唯一 Reviewer 复述同一错误并全 PASS。处置要求 comprehensive
provisional Review 后再执行 fresh evidence-boundary challenge，Application 投影三类通用 leads，Gateway 强制 focus 顺序，Authorization
只接受 challenge；Strategy/Prompt 为 `@20/@30`，focused 78/78、Engineering QA 115/115 PASS。扩展 deterministic Gate 与下一
clean/fresh live 仍待闭合；run-027 永久保持 Q1 PASS + Q2/Q3 FAIL。
`FINDING-010-076` 已以 docs 组合 148/148、历史 oracle 组合 80/80、current docs/compile/diff 与允许 AF_UNIX 的 full
1181/1176 exact historical hold 闭合上述 deterministic Gate；raw 唯一 4 FAIL + 1 ERROR 仍为冻结历史 hold，没有 ITER-010 新失败。
下一步只能从新 clean candidate 执行 fresh Conformance、持续三题、Provider 前负测与独立复核；run-027 不追认，Production 不执行。
`FINDING-010-077` 记录 clean `f832ceb…` / run-028 的 2 PASS + 1 错误放行：Q2 fresh challenge 已收到未挂载 type lead，却仍把
caller getter 扩张为 DTO field/wire property 并以空 Findings 批准。处置为每项 lead 密封 Application-owned stable `challenge_id`，
challenge 必须逐项返回 evidence scope、Draft scope 与受控 disposition；Application 重算 exact ID 集合并要求越界项绑定同输出中作用于
被挑战 Claim 的 Finding。Strategy/Prompt/Review Schema 为 `@21/@31/@6`，focused 78/78、Engineering QA 115/115 PASS；扩展
deterministic 与下一 clean/fresh live 待闭合，run-028 永久保持 Q1/Q3 PASS、Q2 FAIL，Production 不执行。
`FINDING-010-078` 已以 docs 组合 148/148、历史 oracle 组合 80/80、current docs/compile/diff 与允许 AF_UNIX 的 full
1181/1176 exact historical hold 闭合上述 deterministic Gate；raw 唯一 4 FAIL + 1 ERROR 仍是冻结历史 hold，没有 ITER-010 新失败。
下一步只能从新 clean candidate 执行 fresh Conformance、持续三题、Provider 前负测与 raw challenge assessment 独立复核；run-028
不追认，Production 不执行。
`FINDING-010-079` 记录 clean `e0ad3c8…` / run-029 的 0/3：Q1 被错误批准但遗漏完整 Service entry 中的登录审计持久化；Q2 的正确
越界 rewrite 又丢掉另一个安全 observation，Application 失败关闭；Q3 的 assessment Finding code 存在但 Claim 不属于每个 exact
challenge，Application 失败关闭。处置为逐 cited full-content Java entry 的 material-effect scan、`DRAFT_OMITS_MATERIAL_EFFECT`、
Answer early exact observation coverage table，以及非 passing assessment 的 exact challenged-Claim binding。Strategy/Prompt/Review Schema
为 `@22/@32/@7`，focused 79/79、Engineering QA 116/116 PASS；扩展 deterministic 与下一 clean/fresh live 待闭合。run-029 不追认，
Production 不执行。
`FINDING-010-080` 已以 docs 组合 149/149、历史 oracle 组合 81/81、current docs/compile/diff 与允许 AF_UNIX 的 full
1182/1177 exact historical hold 闭合上述 deterministic Gate；raw 唯一 4 FAIL + 1 ERROR 仍是冻结历史 hold，没有 ITER-010 新失败。
下一步只能从新 clean candidate 执行 fresh Conformance、持续三题、Provider 前负测与 raw Answer/Reviewer/challenge assessment 独立
复核；run-029 不追认，Production 不执行。
`FINDING-010-081` 记录 clean `9ae982b…` / run-030：fresh Conformance 2/2 PASS，同一持续 Browser 三题共 36 dispatch
（14/14/8），retry/switch/outcome-unknown 0；66,000-byte 输入在 Provider 前拒绝，private files、clean SQLite checkpoint、listener
continuity 与 Production `NOT_EXECUTED` 成立。Q1/Q3 独立 PASS；Q2 虽被页面 `APPROVED`，却没有把登录响应 token/tokenHead 交接为
受保护请求输入，也没有明确 configuration-backed header/prefix unknown，实际为 2 PASS + 1 FAIL。
`FINDING-010-082` 已要求 startup/call/use/integrate/diagnose 的 operational checklist 与 Answer input/output handoff，并为每个可交付
Draft 投影通用 `ORIGINAL_QUESTION_FULFILLMENT_SCAN`；缺 material 用户目标使用 `DRAFT_OMITS_MATERIAL_REQUIREMENT`，专用 disposition
错配 challenge kind 时失败关闭。Strategy/Prompt/Review Schema 为 `@23/@33/@8`，focused 80/80、Engineering QA 117/117 PASS；
`FINDING-010-083` 再以 docs 组合 150/150、历史 oracle 组合 82/82、current docs/compile/diff 与允许 AF_UNIX 的 full 1183/1178
exact historical hold 闭合 deterministic Gate；raw 唯一 4 FAIL + 1 ERROR 仍为冻结历史 hold，没有 ITER-010 新失败。下一步只能从
新 clean candidate 执行 fresh Conformance、持续三题、Provider 前负测与 raw Answer/Reviewer/challenge-assessment 独立复核；
run-030 不追认，Production 不执行。
`FINDING-010-084` 记录 clean `3c45072…` / run-031：fresh Conformance 2/2 PASS；Q1 在同一 Browser 会话使用 12 dispatch，retry/switch/
outcome-unknown 0，但第二次 challenge 发现 cache write 后没有声明 Application observation omission，反而错误请求第二次同包 rewrite，
结果 `SAME_PACKAGE_REWRITE_FUSE_EXHAUSTED` / Q1 FAIL。Q2/Q3 与 66,000-byte 负测因 systemic blocker 未执行，Production 不执行。处置不放宽
rewrite fuse，而是为每个 material-effect omission 增加 exact statements 与 `APPLICATION_PACKAGE / DEFAULT_DRAFT` layer；Application
重算 observation membership、entry/evidence class 与 remediation。`FINDING-010-085` 再以 focused 80/80、Engineering QA 117/117、
docs 组合 150/150、历史 oracle 组合 82/82、current docs/compile/diff 与允许 AF_UNIX 的 full 1183/1178 exact historical hold 闭合
deterministic Gate；没有 ITER-010 新失败。新的 clean/fresh live Gate 待执行。
`FINDING-010-086` 记录 clean `3bd3c04…` / run-032：fresh Conformance 2/2 PASS；持续 Browser 的 Q1 12 dispatch 独立 PASS，Q2
9 dispatch 因 material observation 的 `retrieval_item_*` source reference 被错误拿 `support_entry_*` 比较而形成伪空投影，Reviewer 错选
`DEFAULT_DRAFT` 后由 Application 正确失败关闭；Q3 第 6 次 Answer dispatch 遇到 `REMOTE_DISCONNECTED` 并按零重试封存
OUTCOME_UNKNOWN；66,000-byte 在 Provider 前拒绝且总 dispatch 保持 27。处置为 challenge/Application 复用 exact entry → source-reference
resolver，并加入 application-missing-first layer precedence；Strategy/Prompt 为 `@25/@35`，Review Schema 保持 `@9`。run-032 不追认，
Production 不执行，新的 deterministic 与 clean/fresh live Gate 待闭合。
`FINDING-010-087` 再以 focused 80/80、Engineering QA 117/117、docs 组合 150/150、历史 oracle 组合 82/82、current docs/compile/diff
与允许 AF_UNIX 的 full 1183/1178 exact historical hold 闭合 deterministic Gate；没有 ITER-010 新失败。下一步只能从新 clean candidate
执行 fresh Conformance、持续三题、Provider 前负测与 raw Answer/Reviewer/challenge assessment 独立复核；run-032 不追认，Production 不执行。
`FINDING-010-088` 记录 clean `d70a3e6…` / run-033：fresh Conformance 2/2 PASS；持续 Browser 的 Q1 15 dispatch 已正确进入
`APPLICATION_PACKAGE` Verification，却把未挂载 cache callee 的内部实现当成新证据需求，并用单一 `UNKNOWN` replacement 覆盖 check-6，
静默删除 predecessor 中仍有 support 的登录流程/审计 observations，最终 challenge 又错绑 Claim 而失败关闭。Q2 8 dispatch 因自造
`cognition-unknown-*` 而由 admissible-reference Gate 正确关闭；Q3 第 8 次 Review dispatch 后发生 `NETWORK_FAILURE`，按零重试封存
OUTCOME_UNKNOWN；66,000-byte 仍在 Provider 前拒绝，总 dispatch 31、retry/switch 0、private SQLite/clean stop 与 Production
`NOT_EXECUTED` 成立。run-033 总体 FAIL，不追认。
处置把 Verification target replacement 从任意覆盖收紧为 supported-observation 单调保留：角色输入获得 exact preservation contract，
Application 在 successor seal 前机械拒绝删除、改写或重排旧 observation；non-supported predecessor boundary 仍可被真实新证据替换。
`APPLICATION_PACKAGE` effect gap 只请求 challenged caller full content 已可见 interaction 的 typed observation，不要求未挂载 callee internals。
Strategy/Prompt 升为 `@26/@36`，Review Schema 保持 `@9`；新的 deterministic Gate 与 clean/fresh live 仍须独立闭合。
`FINDING-010-089` 已以 focused 80/80、Engineering QA 117/117、docs 组合 150/150、历史 oracle 组合 82/82、483 current docs、
compile/diff 与允许 AF_UNIX 的 full 1183/1178 exact historical hold 闭合该 deterministic Gate；没有 ITER-010 新失败。下一步只能从
新 clean candidate 执行 fresh Conformance、持续三题、Provider 前负测与 raw Answer/Reviewer/challenge assessment 独立复核。
`FINDING-010-090` 记录新 clean `fe6b6b6…` / run-034：第一条 fresh Conformance request 已完成 credential resolution、verified TLS 与
HTTP dispatch，但 DeepSeek 返回 402；request 1、token 0、retry/switch 0，第二条未发送，无 Qualification、Alpha、Browser 或 Production。
run-034 永久 FAIL；当前 key 所属账户余额实际恢复前保持 configuration-environment hold，之后只能启动新的 fresh Conformance。
`FINDING-010-091` 记录本轮约 14 小时没有新用户体验、却持续进行内部协议修复和 DeepSeek live 的交付反证；PDR-003 现将 Access、Quality
和 hardening 分离，并用 60/180/240、一次资格/一次 smoke、同签名一次 successor 和两次无用户可见增量停止规则收窄恢复。
`FINDING-010-092` 记录当时透明 Ark-primary/DeepSeek-fallback 尚未成为可验证 route，以及 PDR-003 当时的“一题 live canary”计划。该步骤从未执行，已被 PDR-004 修订为“最多一次 Provider 前本地或 Mock Access smoke；
首个 live canary 本身是五轮 Conversation + 新对话隔离负测”。fallback 必须从 original Turn、relevant sealed Conversation Context 和 exact Cognition 完全隔离重跑，用户无需重提，且相同有效 Conformance 必须复用。
`FINDING-010-132/133` 与 PDR-005 停止了 Maven-only 行为认知上的症状修补；`ITER-010-RESULT-V-LAYER-ATTRIBUTION-001 /
FINDING-010-134` 随后以外部调用 0 密封 Knowledge construction/admission 的 first divergence，以及 Agent/Reviewer 的独立下游故障。
`FINDING-010-135` 将普通 Java 的 representable source unit 逐项 disposition，并只发布同 declaring type、唯一 name+arity 的正向
call-site fact；559 个 method implementation incomplete 与 866 个 unsupported unit 继续显式可见。`FINDING-010-136 /
ITER-010-RESULT-V-COGNITION-ELIGIBILITY-001` 又把 original-question Need 的 dimension + query capability、两个独立 Profile authority、
问题相关 projection/Gap 与 artifact Session `@2` 组合闭合为本地 PASS。整个阶段 Provider/model、projection Source read、listener/browser
均为 0；下一步仍须另取 exact external grant 才能执行一个 Ark Web direction canary，不能由本地 Result 追认 live Chat/Quality/XD。
后续发现按 [Findings](../findings/README.md) 与[实现发现回写规则](../../../governance/implementation-feedback-policy.md)处置。
