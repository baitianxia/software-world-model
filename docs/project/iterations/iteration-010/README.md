---
id: ITER-010-INDEX
kind: iteration-index
status: authorized
authority: current-development
owners: [product, project, architecture, engineering, quality]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, PROJECT-GOVERNANCE-PLAN-EXECUTION, ROADMAP-M-002, ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, ITER-010-PROPOSAL, ITER-010-READINESS, ITER-010-VERIFICATION, ITER-010-SLICE-001, ITER-010-SLICE-002, ITER-010-SLICE-003, FINDING-010-028, FINDING-010-091, FINDING-010-092, FINDING-010-093, FINDING-010-094, FINDING-010-095, FINDING-010-096, FINDING-010-097, FINDING-010-098, FINDING-010-099, FINDING-010-100, FINDING-010-101, FINDING-010-102, FINDING-010-103, FINDING-010-104, FINDING-010-105, FINDING-010-106, FINDING-010-107, FINDING-010-108, FINDING-010-109, FINDING-010-110, FINDING-010-111, FINDING-010-112, FINDING-010-113, FINDING-010-114, FINDING-010-115, FINDING-010-116, FINDING-010-117, FINDING-010-118, FINDING-010-119, FINDING-010-120, FINDING-010-121, FINDING-010-122, FINDING-010-123, FINDING-010-124, FINDING-010-125, FINDING-010-126, FINDING-010-127, FINDING-010-128, FINDING-010-129, FINDING-010-130, FINDING-010-131, FINDING-010-132, FINDING-010-133, FINDING-010-134, FINDING-010-135, FINDING-010-136, FINDING-010-137, FINDING-010-138, FINDING-010-139, FINDING-010-140, FINDING-010-141, FINDING-010-153, FINDING-010-161, FINDING-010-162, FINDING-010-163, FINDING-010-164, FINDING-010-165, FINDING-010-180, FINDING-010-181, FINDING-010-182, FINDING-010-183, FINDING-010-184, FINDING-010-185, FINDING-010-186, FINDING-010-187, FINDING-010-188, FINDING-010-189, FINDING-010-190, FINDING-010-191, FINDING-010-192, FINDING-010-193, FINDING-010-194, FINDING-010-195, FINDING-010-196, FINDING-010-197, FINDING-010-198, FINDING-010-199, FINDING-010-200, FINDING-010-201, FINDING-010-202, FINDING-010-203, FINDING-010-204, FINDING-010-205, FINDING-010-206, FINDING-010-207, FINDING-010-208, FINDING-010-209, FINDING-010-210, FINDING-010-211, FINDING-010-212, FINDING-010-213, FINDING-010-214, FINDING-010-215, FINDING-010-216, FINDING-010-217, FINDING-010-218, FINDING-010-219, FINDING-010-220, FINDING-010-221, FINDING-010-222, FINDING-010-223, FINDING-010-224, FINDING-010-225, FINDING-010-226, FINDING-010-227, FINDING-010-228, FINDING-010-229, FINDING-010-230, FINDING-010-231, FINDING-010-232, FINDING-010-233, FINDING-010-234, FINDING-010-235, FINDING-010-236, FINDING-010-237, FINDING-010-238, FINDING-010-239, FINDING-010-240, FINDING-010-241, FINDING-010-242, FINDING-010-243, FINDING-010-244, FINDING-010-245, FINDING-010-246, FINDING-010-247, ITER-010-RESULT-SLICE-001-STOP-REDIRECT, ITER-010-RESULT-V-ALPHA-ACCESS-001, ITER-010-RESULT-V-LAYER-ATTRIBUTION-001, ITER-010-RESULT-V-COGNITION-ELIGIBILITY-001, ITER-010-RESULT-V-DEEPSEEK-IDLE-001, ITER-010-RESULT-V-PLAN-RECOVERY-001, ITER-010-RESULT-V-MVP-EXPERIENCE-001, ITER-010-RESULT-V-USER-DIRECTION-DECISION-001, ITER-010-DECISIONS, ITER-010-PDR-001, ITER-010-PDR-002, ITER-010-PDR-003, ITER-010-PDR-004, ITER-010-PDR-005, ITER-010-PDR-006, ITER-010-PDR-007, ITER-010-PDR-008, ITER-010-PDR-009, ITER-010-PDR-010, ITER-010-PDR-011, ITER-010-PDR-012, SYS-ADR-018, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
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
[PDR-010](decisions/PDR-010-complete-mvp-vertical-slice.md) 将完整可运行体验候选放到严格比较之前，但该候选不是 MVP。严格质量标准不降低：
必须比较用户已经能体验的同一候选，并且只有绝对质量和 current Codex 同题比较通过后才取得 MVP 资格。三个独立问答不算 Chat，POM
模块/依赖题、Access 页面或单独 Web 外壳也不能充当候选，更不能充当 MVP。

## Status and authorization

### PDR-012 current status

`AUTHORIZED / REWORK / PRODUCT-FIRST BROWSER CHAT BUILD ACTIVE / STANDING SCOPE ACTIVE / NON-PRODUCTION`。

当前唯一工作计划的技术 ID 仍是 `ITER-010-ACTION-BROWSER-CHAT-MVP-BUILD-001 / V-BROWSER-CHAT-MVP-BUILD-001`：在同一 Slice 完成真实世界模型认知、
主工程 Agent、按 Gap 受控源码、Evidence/Citation、fresh Review 和至少三轮语义 Chat。coding、Prompt/Reviewer、loopback Web 与 standing
scope 内 Provider dispatch 已恢复；首次完整链可操作即以开发体验候选无 Result 交付，随后不停工完成同候选质量资格。技术 ID 含 MVP 不
代表候选已经是 MVP。

[PDR-012](decisions/PDR-012-product-first-continuous-browser-chat-build.md) 是当前执行决定。PDR-011、run-052/053 和 failure Result 只保留
历史失败，不撤销 PDR-008 的公开工程 standing authority。普通失败留在当前 BUILD 做分层归因、通用修复与异质复验；不得生成失败 Result、
新 PDR 或重复授权。只有真实 scope delta、用户明确 STOP/REDIRECT/REJECT 或不可绕过的安全禁止才停止相关工作。

run-075 的证据由 `FINDING-010-185/186` 保存。run-074 的三轮开发体验仍按原 identity 保留并已交付；fresh successor 已让 Maven/启动链
旧失败题以 Ark 8 次形成 Answer/Review/Delivery，证明 `FINDING-010-184` 的 `@5` repair 越过真实失败点。订单创建题、同 Conversation 库存
失败追问和新 Conversation 省略指代 probe 也完成；后者以不同 Conversation identity、EMPTY CONTEXT 和零 Provider dispatch 返回
Clarification，因此 `V-CHAT-001` 已取得显式隔离证据。

质量仍未通过。库存追问把消息发送放在“数据库写入一定尚未发生”的标题下，Claim 只记录调用顺序，fresh Reviewer 对 10 个窄 Claim 全部
`SUPPORTED`；角色重分配题又在 Source receipt `64/64` 时遇到 catalog 已关闭 Source operation、read options 仍暴露 controller locator 的
矛盾，same-profile repair 提出 dangling READ 后被拒。run-075 总计 Ark dispatch/TLS/credential/HTTP `31/31/31/31`，DeepSeek 0、
retry/unknown 0、Production 未执行，故不是 Ark 不可用。current local candidate 以
`ENGINEERING_AGENT_SOURCE_FILE_BUDGET@1` 闭合 budget/options/catalog，并要求 Claim/Reviewer 纳入 heading/table/list 继承 qualifier；
无 AF_UNIX 依赖的受影响组合 `127/127` PASS；扩展 141 项 raw 的 1 FAIL + 5 ERROR 全部来自 sandbox 禁止本机 socket。该阶段仍不能称为
MVP，后继 run-076 的事实如下。

当前最新证据是 `FINDING-010-187/188/189 / run-076`。角色重分配题前 9 个 Ark call 已取得真实 Source Read 和 Answer Draft，并由
Application 正确拒绝 BOUNDARY-as-support Claim，证明旧 Source budget/reference contradiction 已被越过；repair 和后四个冻结 Turn 的
首个 call 随后连续 sealed raw `PROVIDER_HTTP_ERROR`。该 raw evidence 没有受信 unavailable verdict，故已通过周末闲时 admission 的
DeepSeek 保持 0 dispatch 正确。五题均未交付，容器语义和异质答案质量仍未验证。EMPTY CONTEXT 的“这些失败也会回滚吗？”另暴露
plural/class demonstrative marker 缺口，Browser 又只显示 stage code。current candidate 已补齐通用指代 Clarification 和 failure layer
display；Conversation/Browser `20/20` PASS、外调 0。下一步仍是 fresh clean 浏览器 successor 与 actual current Codex 比较，不能称为
MVP。

`FINDING-010-190 / run-077` 已用新的 exact product 真实验证 local repair：首个 Ark call 再次 raw `PROVIDER_HTTP_ERROR`，Browser 已同时
显示 execution-stage 和 raw Provider evidence；第二个 EMPTY CONTEXT Conversation 的“这些失败也会回滚吗？”以零 dispatch
`APPLICATION_INPUT_CLARIFICATION` 成功。因为 run-076/077 已连续出现相同 raw signature 且没有 trusted unavailable verdict，本 run
没有继续提交其余外部质量题；已获周末 `ALLOWED_OFF_PEAK` admission 的 DeepSeek 保持 0 dispatch 正确。terminal 密封 Ark 1、DeepSeek 0、
retry 0、Production 0。该证据验证 `FINDING-010-188/189`，不验证工程答案、Reviewer、Codex 比较或 MVP；下一外调须有 materially new
availability evidence 或新的 product divergence。

`FINDING-010-191` 又从 run-076 未交付 Draft 的 exact Manifest/output 继续本地分层归因：Cognition coverage gap 被误称为授权边界，且
producer-side 缓存失效调用被扩张成 consumer-side 登录态权限刷新结论。current Primary/Reviewer contract 现机械披露并要求区分
authority/coverage/tool/runtime 与 invocation/callee/consumer 三层；模型边界直接 `28/28`、相邻 Application/Conversation/Browser/
Candidate/Session 组合 `77/77` PASS、外调 0。该 local candidate 尚未经过
fresh live Primary/Reviewer，不取得质量 PASS 或 MVP 名称。

`FINDING-010-192` 继续审计同一 exact input，把最早偏差定位到 SUPPORT projection：global Coverage/Gap 同时出现在 SUPPORT 与 BOUNDARY。
current adapter 已从 SUPPORT 顶层移除 global coverage/conflict/unknown，只保留 novel affirmative item 的 per-item coverage；正式 Context、
Ledger、receipt 与 BOUNDARY 不丢失。相邻七模块 `91/91` PASS、外调 0，fresh live 质量证据仍待取得。

`FINDING-010-193` 又发现 Draft 在 full READ 已闭合相同 need 后仍披露早期 Search 截断，并加入没有限制具体 requested conclusion 的全局
559/866 清单数字。current Primary/Reviewer 只把仍未解决的 material Boundary 写入用户答案，已解决或无关 acquisition diagnostic 只留
audit；模型边界直接 `28/28`、相邻七模块 `91/91` PASS、外调 0，fresh live 仍待验证。

`FINDING-010-194` 继续发现 SUPPORT `dimensions` 内仍有 typed `COVERAGE/UNKNOWN` metadata。current `@4` schema 只允许
`ENTITY/RELATION/BEHAVIOR/CONSTRAINT/STATE` affirmative item，并让 counts、Citation 与 Source target 同域；Tool/Model `43/43`、
相邻七模块 `92/92` PASS、外调 0，fresh live 仍待验证。

`FINDING-010-195` 再把 run-076 SUPPORT 的商品/营销/通用 Controller 噪声定位到 cognition relevance：结构 value、公共 path、function
token 和弱正分尾部被错误计分。current query projection 采用 cohort-aware semantic-value ranking；原 artifact/evidence need 零外调 replay
从 32 收敛到 14，已知异域 item 为 0，并保留 `updateRole`、关系 insertion 与 cache 相关认知。Profile incomplete 的旧关系删除继续由
Source 补证；认知 `10/10`、相邻八模块 `102/102` PASS，fresh live 仍待验证。

`FINDING-010-196` 再关闭 Draft 的普通邻接扩张：generation/tool provenance 不能由 path/package/import/symbol/directory convention 推断，
每个 answer detail 和 Boundary 都须通过 counterfactual materiality test；删除后 requested conclusions 仍完整时省略，且不得为 Draft 自己
引入的辅助 declaration/helper/provenance 扩大调查。Model `28/28` PASS、外调 0，fresh live 仍待验证。

`FINDING-010-197` 继续以冻结 `mall-portal` / `mall-search` 题审计 multi-Profile projection，发现仅靠 relevance ranking 仍会把
`mall-admin` Java item 或 559/866 gap 投入异域问题。current formal scope gate 从 original question + sealed allowlist 取得 exact top-level
scope，先排除 Coverage root 完全不相交的非 repository-wide Profile；真实 artifact 零外调复演只保留对应 Maven module item，认知
`11/11` PASS，fresh live 仍待验证。

`FINDING-010-198` 再定位 Ark 失败后 fallback 为 0 的系统原因：Adapter 的安全 HTTP status/details 在 Gateway 持久化边界丢失，可信
availability owner 无法从 exact receipt 作出 unavailable verdict。current Gateway-sealed evidence 贯穿 replay/egress/Turn/attempt，owner
只接受 typed pre-HTTP unavailable 或密封 `{402,408,425,429,500,502,503,504}`；相邻组合 `162/162` PASS，历史 run 不补判，fresh live 待验证。

`FINDING-010-199` 随后修正首版证据实现误触两家 Conformance identity 的问题。run-078 首次启动在外调前正确拒绝 stale qualification；Ark
fresh `2/2` PASS，DeepSeek refresh 在受限开发命令中 HTTP=0。current post-terminal decorator 原样委托 exact qualified Adapter，并在 inner
Gateway 后写 auxiliary evidence；conformance-bound core raw bytes 与两份既有 PASS aggregate 恢复 exact，loader 校验未放宽。

`FINDING-010-200 / run-078` 已形成 materially new live route 与产品证据：Q2/Q3 的 Ark typed pre-HTTP unavailable 均实际启动
DeepSeek，Q1/Q3 的 post-dispatch unknown 则没有 retry 或越权回退；Q4 fresh Conversation 继续零 dispatch Clarification，Q5 以 Ark 7 次和
9 Citation 交付 `SUCCEEDED / ACCEPTED`。Q2 的 DeepSeek 链也完成 Review/Delivery，但 Primary 把 authorized `mall-portal` directory
segment 当成 content literal，空扫 56 文件后过早 Limitation。current Broker 现于 Worker 前以
`SOURCE_SEARCH_QUERY_EQUALS_PATH_SEGMENT` 零读取拒绝，Primary 读取 sealed latest decision 后必须改用不同 source-native literal；两份
完整受影响测试文件 `82/82` PASS。run-078 共 Ark 24、DeepSeek 5，人工审批/retry/Production 0；因两条工程 Turn 失败且 Q2 是假
Limitation，仍不取得质量或 MVP PASS。

`FINDING-010-201 / FINDING-010-202 / run-079` 随后密封 Ark 21、DeepSeek 0；全部 Ark TLS/credential/HTTP 成功，因此没有 trusted
unavailable verdict 且 fallback 0 正确。Q2/Q3/Q5 均 `SUCCEEDED / ACCEPTED`，Q4 继续零 dispatch Clarification；Q1 因一个 raw action 同时
遗漏 `operation` 和使用闭域外 `UmsAdminServiceImpl` 而失败。exact replay 证明更早缺口是 selected `CALL_SITE_TARGETS` relation 的直接
Entity endpoint 被 relevance cutoff 截掉；current one-hop closure 恢复 same-Snapshot verified target，而不放宽 repair。Q5 的 3-Citation
窄答案则来自 exact filename 命中后仍扫描低排名 corpus 并耗尽 `64/64`；current filename-cohort Partial early-stop 保留预算。Cognition
`12/12`、Source/Tool/Question `81/81` PASS，fresh successor 待验证；run-079 仍不取得质量或 MVP PASS。

`FINDING-010-203 / run-080` 继续密封四个 accepted 工程答案和一个零 dispatch Clarification；Ark 32 次 TLS/credential/HTTP 全成功、
DeepSeek 0 正确。Q2 仍把已由 full READ 闭合的 Search diagnostic 写入答案，Q1/Q2/Q5 又把 caller expression 扩张为未读 callee 的
database/Elasticsearch effect，fresh Reviewer 全部漏判；Q5 结束时 Tool `5/8`、Source `5/64` 且仍有 read option。current
`conversational-engineering-agent@9 / ENGINEERING_AGENT_PRIMARY_INPUT@9 / ENGINEERING_AGENT_REVIEW_INPUT@3` 由 Application 投影 exact
caller/callee 与 resolved-acquisition relevance challenge，focused Reviewer 逐项 disposition，Response Control 重算闭合；预算、route、
standing authority 与 Production 边界不变。run-080 仍不取得质量或 MVP PASS。

`FINDING-010-204 / run-081/082` 密封下一轮真实结果：run-081 仅因 pricing check 过期而在外调前停止，不是 Ark unavailable；刷新官方
pricing evidence 后，run-082 获周末 `ALLOWED_OFF_PEAK` admission，而 Ark 41 次 TLS/credential/HTTP 全成功，所以 DeepSeek 0 正确。Q1/Q5
交付、Q4 隔离 Clarification 零 dispatch；Q2 因冗余 Observation ID 抄写漂移失败，Q3 在第三次合法 Finding 后耗尽 Review，Q5 又让未声明
resolved diagnostic 绕过 focused Review，并把 caller invocation 扩成 external effect。current `@10/@4` candidate 由 Application 绑定 exact
Observation prefix、挑战全部 resolved candidate、密封 closed semantic scope，并以 `11 Agent + 4 Review = 15` 保持原 dispatch authority；
132 项定向测试 PASS；后续 run-083 由 `FINDING-010-205` 记录。run-081/082 均不取得质量或 MVP PASS。

`FINDING-010-205 / run-083` 密封新的真实结果：Ark 43 次 TLS/credential/HTTP 全成功，DeepSeek 0 继续符合 preferred-first；Q1/Q3/Q5
accepted、Q4 隔离 Clarification 零 dispatch，Q5 已关闭旧 Search diagnostic 与 caller→effect 缺陷。Q2 在 JSON syntax repair 后才暴露独立
cross-disposition contract failure；Q1 仍泄漏 global `559/866` metric 并绑定 stale Search Boundary。current `@11/@5` candidate 只允许严格后继
validator stage 的第二次 repair，以 exact canonical resource identity 关联 Search/Read，并挑战每个 Package Boundary；其后继结果由
`FINDING-010-206/207` 记录。run-083 仍不取得质量或 MVP PASS。

`FINDING-010-206/207 / run-084` 密封 44 个 Ark call：43 个完成 HTTP，1 个在 HTTP 前 typed TLS unavailable；DeepSeek 因旧 listener-time
600 秒 receipt 已过期而保持 0。Q4 隔离 Clarification 继续零 dispatch，其余工程 Turn 失败。最早产品偏差是 Search/Read matcher 使用错误的
Search modality，Review input 缺 kind-specific closed disposition domain，Prompt/preflight 又未显式禁止 authored string 尾随 whitespace。
current `@12/@6/@7` 按真实 `LITERAL_TEXT_SEARCH_HIT → EXACT_STATIC_SOURCE_TEXT` 关系、authorized Citation 与 exact path 重算；DeepSeek
policy `@3` 在 first real preflight 激活并重验 active receipt。15 次 authority、route/budget/retry 不变，144 项定向测试 PASS，fresh run-085
待验证。run-084 仍不取得质量或 MVP PASS。

`FINDING-010-208 / run-085` 密封 52 个 Ark HTTP dispatch：51 个完成、1 个 post-dispatch outcome unknown；没有可信 HTTP 前 unavailable，
DeepSeek 0 正确。Q4 零 dispatch Clarification 保持，其余工程 Turn 未交付。current `@13/@7/@8` 闭合 nested closed fields、trusted
ACTION/DRAFT/phase branch、Limitation Boundary binding 与正文 disclosure 分离，并保持原 15 次 authority；144 项定向测试 PASS，fresh
run-086 待验证。run-085 仍不取得质量或 MVP PASS。

`FINDING-010-209 / run-086` 密封 49 个 Ark HTTP dispatch：47 个完成、2 个 post-dispatch outcome unknown；没有可信 HTTP 前 unavailable，
DeepSeek 0 正确。Q4 零 dispatch Clarification 保持，其余工程 Turn 未交付。Q2 的 final preflight 没有重复 exact SUPPORT/BOUNDARY ID
domains；Q3 的 Review successor 没有收到 exact rejected Draft，Claim inventory 因重建扩张为 `5 → 10 → 7 → 13`。current
`@14/@7/@9` 联合密封 rejected Draft/Findings/Review digest，限定 same-Package targeted rewrite，并重复 exact reference domains；144 项定向测试
PASS，fresh run-087 待验证。run-086 仍不取得质量或 MVP PASS。

`FINDING-010-210 / run-087` 密封 Ark 4 个 sealed 429 后的合法 DeepSeek fallback；Q4 零 dispatch Clarification 保持，其余工程 Turn
未交付。exact rejected-Draft edit base 已生效；current `@15/@8/@10` 按 semantic Claim coverage、response-kind-aware rewrite 与 hidden
Boundary binding 通用闭合。144 项定向测试 PASS；后继 run-088 由 `FINDING-010-211` 记录，run-087 仍不取得质量或 MVP PASS。

`FINDING-010-211 / run-088` 密封 Ark 4 个 sealed 429 与 DeepSeek 52 个完成 call、1 个 post-dispatch unknown；Q4 零 dispatch
Clarification 保持，其余工程 Turn 未交付。current `@16/@9/@11` 密封一次完整 Draft audit、focused assessment/Claim/Finding exact closure、
Reviewer-authored decision repair、未引用 duplicate local-code disambiguation 与 all-Findings rewrite；15 次 authority 不变，146 项定向测试 PASS，fresh
run-089 待验证。run-088 仍不取得质量或 MVP PASS。

`FINDING-010-212 / run-089` 密封 Ark 4 个 sealed 429 与 DeepSeek 27 个完成 call、1 个 post-dispatch unknown；Q4 零 dispatch
Clarification 保持，其余工程 Turn 未交付。current `@17/@10/@12` 机械拒绝 unchanged same-Package Draft，密封 repeated Source/focused closure
的 typed repair directive 与 actual index diagnostic，并要求 Limitation 保持零 Claim、删除相邻 affirmative diagnostic、承认已有 opaque Boundary
binding及 Search/interface 的实现证据边界；15 次 authority 不变，147 项定向测试 PASS，fresh run-090 待验证。run-089 仍不取得质量或 MVP
PASS。

`FINDING-010-213 / run-090` 密封 Ark 31 个完成 call、1 个 pre-dispatch TLS failure 与 1 个 post-dispatch unknown；Q3 的 fallback 因
pricing evidence 超过 900 秒而在 DeepSeek credential/TLS/HTTP 前关闭，DeepSeek dispatch 0。Q4 零 dispatch Clarification 保持，其余工程
Turn 未交付。current `@18/@11/@13` 允许第二次 repair 处理与前次不同的 validator category，并为 audit-only missing Finding binding 提供
单义 diagnostic、typed directive 与 final preflight；两次 repair、15 次 authority、route、freshness、retry 与 Production 边界不变。模型边界
34 项、相邻十二模块 148 项测试均 PASS，fresh run-091 待验证。run-090 仍不取得质量或 MVP PASS。

`FINDING-010-214 / run-091` 密封 Ark 37 个完成 call 与 1 个 post-dispatch unknown；不存在可信 pre-dispatch Ark unavailable，故 DeepSeek
dispatch/credential/TLS/HTTP 均为 0。Q4 零 dispatch Clarification 保持；Q1 错误交付零 Citation 的 mixed SUPPORT/BOUNDARY Limitation，Q2
补证 action 后丢失全部 correction obligations，Q3 cognition-literal repair 原样重复非法 query，Q5 no-retry unknown。current
`@19/@11/@14` 保留补证后的 rejected Draft/ordered Findings/Review digest，把 Limitation 限于零 SUPPORT，并为 material cognition target 与
resolved-acquisition audit-only final preflight 投影闭合约束；58 项核心测试与相邻十二模块 148 tests 均 PASS，fresh run-092 待验证。run-091
仍不取得质量或 MVP PASS。

`FINDING-010-215 / run-092` 密封 Ark 53 个完成 call，TLS/credential/HTTP 均为 `53/53/53`；无 trusted pre-dispatch unavailable，故
DeepSeek 全链路 0，retry/人工审批/Production 也为 0。Q3 以 1 个 exact Citation 和 fresh Review/Delivery 成功，Q4 零 dispatch
Clarification 保持；Q1/Q2/Q5 因同一 resolved Search diagnostic 被反复制造 audit-only 空操作 Finding 而耗尽 dispatch 或 Review authority。
current `@20/@12/@15` 要求 relevance assessment 返回可逐字核验的 exact Draft fragments，并机械拒绝未绑定、未披露的 no-op audit-only；
Agent/Tool/Model 73 tests 已 PASS，fresh run-093 待验证。run-092 仍不取得质量或 MVP PASS。

`FINDING-010-216/217 / run-093` 密封 Ark 19、DeepSeek 28；3 个 Ark sealed 429 后备用路线自动激活，无重复人工授权。Q1 的 exact
fragment 只因 inline-code backticks 展示差异被拒；Q2/Q5 的 ordinary Source Search 未继承显式 module scope，并从同一 canonical fallback
前缀重复扫描。current `@21/@13/@16` 只忽略 backtick delimiter presentation，`COMPILED_SOURCE_OPERATION@3` 由 Broker 重算 prefix scope
并轮转 rank-3 fallback；`56/64` fuse和 reserved READ 不变，六模块 `154/154`、相邻十五模块 `229/229` PASS，fresh run-094 待验证。run-093 仍不取得质量或 MVP PASS。

`FINDING-010-218 / run-094` 密封 Ark 4、DeepSeek 21；4 个 Ark sealed 429 后备用路线自动激活，DeepSeek 20 completed、1
post-dispatch unknown，retry/人工审批/Production 均为 0。Q1 ACCEPTED 且有 2 个 exact Citation，Q4 零 dispatch Clarification；Q2
按 unknown 失败，Q3 为 REVIEWED_LIMITATION。Q5 的 valid SOURCE Search 暴露 question module scope 把同 module POM/TEST prefix 混入
SOURCE-only operation；current 修复只从 current evidence-class allowlist选择 prefix，wire schema、fuse与 authority 不变。六模块 `154/154`、
相邻十五模块 `229/229` tests PASS，fresh run-095 待验证。run-094 仍不取得质量或 MVP PASS。

`FINDING-010-219/220 / run-095` 密封 Ark 4、DeepSeek 28；4 个 Ark sealed 429 后备用路线自动激活，DeepSeek 27 completed、1
post-dispatch unknown，retry/人工审批/Production 均为 0。Q1/Q5 ACCEPTED，Q4 零 dispatch Clarification，证明 run-094 prefix 修复真实
通过。Q2 暴露 browser idle 后 stale keep-alive 仍被复用；Q3 暴露 challenge assessments 与额外 unbound Finding 的 generic repair 不收敛。
current Engineering Chat runtime ref `@3` 在 qualified transport call 前轮转 stale 或 idle ≥60 秒的 session，base Adapter/Conformance
identity不变；current `@22/@14/@17` 以专用 directive 绑定 retained Finding 或删除它并 APPROVE。相邻十七模块 `255/255` tests PASS，
current Conformance loader PASS，run-096 待验证。run-095 仍不取得质量或 MVP PASS。

`FINDING-010-221 / run-096` 密封 Ark 4、DeepSeek 37；4 个 Ark sealed 429 后备用路线自动激活，DeepSeek 37/37 completed，
retry/unknown/人工审批/Production 均为 0。Q1/Q5 ACCEPTED，Q4 零 dispatch Clarification；Q2 的 focused Reviewer 从 method
name或 prior Finding 向 exact caller-only Claim 重导入 database effect，Primary 随后两次 exact-repeat rejected Draft；Q3 只形成
REVIEWED_LIMITATION。current `@23/@15/@18` 直接密封 exact challenged Claim 并规定 stricter different caller-effect rewrite；targeted
`34/34`、相邻 16 模块 `261/261` PASS，fresh run-097 待验证。run-096 仍不取得质量或 MVP PASS。

`FINDING-010-222 / run-097` 密封 Ark 40、DeepSeek 0；Ark 39 completed、Q2 单一 post-dispatch unknown，Q1/Q5
ACCEPTED、Q4 零 dispatch Clarification。Q3 的 13 个 caller challenge 全部 correctly WITHIN，但 bound + empty Boundary 被 Reviewer/
repair 错标 `NOT_DISCLOSED_IN_DRAFT`。current `@24/@16/@19` 逐 challenge 密封 reference/fragment-state disposition closure；targeted
`34/34`、相邻 16 模块 `261/261` PASS，fresh run-098 待验证。run-097 仍不取得质量或 MVP PASS。

`FINDING-010-223/224/225 / run-098` 密封 Ark 24、DeepSeek 32；Ark 的 pre-dispatch TLS failure 与 2 个 sealed 429 才触发
fallback，DeepSeek 32/32 completed，retry/人工审批/Production 0。Q1 ACCEPTED、Q4 零调用 Clarification，Q2 false acceptance、Q3
review-limit、Q5 structured-invalid 使整体继续 FAIL。current identifier-component path ranking 在不提高 56/64 fuse 下把方法 literal 导航到
共享 component 的 implementation filename；current `@25/@16/@20` 删除 caller-only rewrite 的 authored effect labels，并对 closed body +
empty Findings 只允许 decision→APPROVED。六模块 `155/155`、相邻 19 模块 `265/265` PASS，fresh run-099 待验证；run-098 不取得质量或 MVP PASS。

`FINDING-010-226 / run-099` 密封 Ark 4、DeepSeek 39；Ark 只有 sealed 429 trusted-unavailable 才激活 fallback，DeepSeek 39/39
completed，retry/人工审批/Production 0。Q1/Q5 ACCEPTED、Q4 零调用 Clarification，Q2 Reviewer reject、Q3 reviewed limitation，整体继续
FAIL。run-099 纠正了 run-098 fixture 假设：真实 target 含 `generateOrder`，不含 `createOrder`。current Worker/Application 只把已检查的
identifier-related path 签发为 navigation-only Boundary opaque READ option，Search 绝不产生 SUPPORT，full READ 后才允许 Claim；current
`@26/@16/@21`、六模块 `157/157` PASS，fresh run-100 待验证；run-099 不取得质量或 MVP PASS。

`FINDING-010-227/228 / run-100` 密封 Ark 4、DeepSeek 35；Ark 只有 sealed 429 trusted-unavailable 才激活 fallback，DeepSeek 35/35
completed，retry/人工审批/Production 0。Q2 通过 navigation-only opaque READ 取得目标完整源码，Q1/Q2/Q5 ACCEPTED、Q4 零调用
Clarification；Q3 却重复上一轮普通流程且 Reviewer 错误 APPROVED，Q5 broad Search SUPPORT 又投影 70 个 Citation，整体继续 FAIL。
current `@27/@17/@22` 为每个 Review 密封 exact current-requirement coverage，Primary output `@3` 为每个 Claim 选择最小 direct exact
Citation refs；六模块相邻定向测试 `157/157` 与 documentation check `634` PASS，fresh run-101 待验证，不存在 Provider 或重复授权等待。

`FINDING-010-229/230 / run-101` 密封 Ark 4、DeepSeek 48/48 completed；Q4 保持零 dispatch Clarification，其余四题均失败关闭而未错误
交付。comprehensive Reviewer 把用户题面类别误作必须存在的事实，并与 focused focus 围绕同一 Boundary 产生相反修复；Q3 还实际发出
Ark 1 + DeepSeek 15 = 16，超过 logical Turn 15-call 上限。current `@28/@18/@23` 将一般语义/uncertainty 与 exact Boundary challenge
ownership 分离；两个 Provider authorizer 共享一个 pre-dispatch logical budget，route seal 再重算总和。定向测试 `195/195` PASS；该候选已由
run-102/103 依次验证 peak admission 与完整 off-peak route，不存在 Provider 或重复授权等待。

`FINDING-010-231 / run-102` 发生在周一 weekday peak：Q1 Ark sealed 429 后 DeepSeek 在 credential/TLS/HTTP 前
`DENIED_PEAK_WINDOW`，Q4 new Conversation 零调用澄清通过；同一 shared-budget digest 已绑定两个 runtime。Q2/Q3/Q5 因同签名无新证据
未发送，所以本次不产生 `@28/@18/@23` 质量 verdict；后续 run-103 已在 fresh off-peak evidence 下完成五问。

`FINDING-010-232 / run-103` 密封 Ark 4 个 429 trusted-unavailable 与 DeepSeek `39/39` completed；Q2 ACCEPTED、Q4 零 dispatch，Q1/Q3
分别因 Reviewer/Primary structured-output repair 失败关闭，Q5 在 active receipt 600 秒窗口之后 pre-dispatch reject（仅作时间证据支持的
inference）。shared logical Turn budget 把逐题总调用保持在 15 内。current `@29/@19/@24` 在 focused repair 中机械恢复 Reviewer semantic
anchor，并把本轮 User Message 固定为 current goal，同时区分 abrupt completion、unsuccessful normal return、local reachability 与
persistence/commit/rollback/remote effects；模型协议 `37/37`、相邻定向测试 `137/137` PASS，下一项是提交并执行 fresh run-104。

`FINDING-010-233 / run-104` 在该 committed candidate 上密封 Q1 的 Ark 1 + DeepSeek 14 exact-budget failure、Q2 的 Ark 429 + DeepSeek
sealed HTTP 402，以及 Q4 的 zero-dispatch Clarification；同签名停止边界下 Q3/Q5 未发送，因此不形成完整五问质量 verdict。Q1 暴露
comprehensive redaction 把可信 Boundary presence 一并擦除，Reviewer 据空数组反复要求增删 binding/Claim/SUPPORT。current
`@30/@20/@24` 只投影 trusted Package/Draft Boundary counts，exact values 与 materiality 仍归 focused Review；模型协议 `37/37`、相邻定向测试
`137/137` PASS。
402 不撤销 standing authority，只阻止无新 availability evidence 的同签名 live 重试；本地开发继续且不重复人工授权。

`FINDING-010-234 / run-105` 按用户明确要求在 current candidate 上执行 Ark-first recheck：Q1 唯一 Ark dispatch 仍为 sealed 429，DeepSeek
于周一 16:02 CST peak window 在 credential/TLS/HTTP 前拒绝；Q4 zero-dispatch Clarification 通过，Q2/Q3/Q5 未重复同签名外调。
terminal 为 2 Turn / 2 Conversation / 1 dispatch，retry/人工审批/unknown/Production 为 0。该 run 不产生 `@30/@20/@24` 质量 verdict或
代码变化；新的同签名 Ark 外调等待 materially new availability evidence，standing authority 不变。

用户随后明确报告 Ark 流量问题已处理，新的 availability evidence 已出现；run-105 证据提交恢复 clean identity 后立即执行 run-106 原五问，
不扩大 scope、预算或 Provider route。

`FINDING-010-235 / run-106` 已证明 Ark 流量恢复：Q1 前 6 个 call completed，第 6 个 Primary output 的末尾 JSON closure 缺失被 validator
准确拒绝；第 7 个 same-profile format repair 在 HTTP dispatch 后 `REMOTE_DISCONNECTED / PROVIDER_OUTCOME_UNKNOWN`，故无 retry、无
DeepSeek fallback。Q4 继续 zero-dispatch Clarification；Q2/Q3/Q5 未在同 Session 的 unknown 后继续。现有 contract 没有本地偏差，下一
clean run-107 先跑未重复的 Q2/Q3/Q4/Q5，再按 stop signature 决定是否补 Q1。

`FINDING-010-236 / run-107` 已执行上述顺序：Q2 为 Ark pre-HTTP TLS unavailable + DeepSeek peak-window zero-network denial；Q3/Q5
分别在 Ark HTTP dispatch 后返回 400 `InvalidParameter / BadRequest`；Q4 仍为 zero-dispatch Clarification。400 non-eligible 与零 retry/
fallback 均正确，但 current evidence 丢弃可选 `error.param`，无法安全定位无效 request field。current candidate 将严格清洗的 optional
parameter-name 加入 evidence `@2`、SQLite/Egress 与 Ark negative oracle，历史 `@1` 可回放且不保存 message/body。目标测试已通过；fresh
Ark Conformance 和 clean run-108 Q5 recheck 是下一步，run-107 不取得质量/MVP PASS。

`FINDING-010-237` 的 no-source Conformance differential 进一步证明：移除 `response_format` 仍 400，只移除 `thinking` 即越过 HTTP
parameter validation；最小 request 两次完成，但 actual fingerprint 已是 `glm-5.3`。该 identity 不在 current standing authority/profile/
Conformance 中。所有临时 request variant 已恢复；下一产品 dispatch 等 Ark 恢复 `glm-5.2`，或用户明确批准 `glm-5.3` material delta 后
重新冻结/资格化，不能以旧授权静默升级模型。

`FINDING-010-238` 已记录用户对 actual `glm-5.3` 的 exact delta 授权以及原数据、预算、loopback evaluation、非 Production scope 不变的
限制。current Ark preferred candidate 为 alias `glm-5-2-260617` → actual `glm-5.3`、Adapter `@9`，wire contract 删除 `thinking`；fresh
Conformance `1.9.0` 与 clean exact Session preparation 通过后继续 run-108。

`FINDING-010-240` 的 clean successor 已取得 `glm-5.3/@9` fresh Conformance 2/2 PASS，result digest
`sha256:5cc4d3662573c06dd1ad174121c4c9a9565ae4743805d51b120ea502415a2363`；下一步是 fresh pricing、exact Session 和 Browser run-108。

`FINDING-010-241 / run-108` 已完成 exact preparation，并在 Browser 发送 Q5。Ark request 越过旧 HTTP 400 后于 HTTP dispatch 后
`REMOTE_DISCONNECTED / PROVIDER_OUTCOME_UNKNOWN`；按 no-retry 与 trusted-unavailable-only fallback 保持 DeepSeek 0。Q4 fresh Conversation
继续 zero-dispatch Clarification。run-108 因而是如实密封的 partial execution，不是五问质量/MVP verdict；剩余外部题等待 materially new Ark
network evidence，本地 Slice 工作继续。

用户允许周期性 Ark 网络重试后，fresh `@9` 短 Conformance 2/2 PASS，但 run-109 的新冻结 Q1 在 dispatch 后约 `55.996s` 再次
`REMOTE_DISCONNECTED`，与 run-108 Q5 的 `56.075s` 边界一致。`FINDING-010-242` 因而把 current repair 定为 Ark Provider SSE
response transfer：Adapter `@10 / Conformance 1.10.0` 在内部严格重组一个 terminal result，Gateway stream、no-retry、fallback、预算、披露和
非 Production 均不变。fresh `ccrun_b222fc9abdf641469baae1cec7080f5d` 已在 clean `e95fa929… / 95431f1c…` 上 2/2 PASS；下一步
是 run-110 长产品验证，不重发两条 outcome-unknown request。

run-110 首个 Ark SSE call 已在约 `80.333s` completed，证明旧网络边界消除；第二个约 `102.925s` 后由本地 parser 以
`PROVIDER_RESPONSE_INVALID` 拒绝，transport unknown 0。`FINDING-010-243` 记录 raw frame 未保存，故 comment keep-alive 只是待验证假设；
但 `@10` 确定会误拒 SSE comment。current `@11 / Conformance 1.11.0` 只修该通用 framing 缺口，fresh qualification 后执行 run-111。

该 fresh qualification 已由 `ccrun_e837a716a9e243c29c4affc4fcd113a0` 在 clean `8d7927f… / fffe078…` 上取得 13/13 case PASS；
下一步是 fresh pricing/exact run-111 Session 与长产品复验，仍不把短 canary 当作 comment 或质量证明。

run-111 的前两次 Ark SSE call 已 completed；第二次精确用满 `8192` output token、finish `length`，可见 JSON 中途截断，第三次 repair
仍被 Adapter 归为 `PROVIDER_RESPONSE_INVALID`。transport unknown/retry 0、DeepSeek 0，故当前不是网络等待。`FINDING-010-244` 的
`@12 / 1.12.0` candidate 固定 `reasoning_effort=low`、保留 empty/incomplete terminal 的 Usage 与 structured-output 分类；fresh
qualification PASS 后执行 run-112。

fresh `ccrun_74a415e279f24556a605f6213a26b41e` 已在 clean `2506dec… / f8a9d37…` 上令 `@12 / 1.12.0` 13/13 case PASS；
下一步是 fresh pricing/exact run-112 Session 和同一长问题 differential，不把短 canary 当作产品质量证明。

run-112 前四个 Ark calls 已 completed 并推进到两次 Source read；第五个在 HTTP 前 TLS failure 后依法 fallback，但 DeepSeek definite HTTP 402
关闭 Turn。`FINDING-010-245` 保留 low-effort repair，并按用户允许的周期性重试在 bounded delay、fresh pricing/session 下执行 run-113。

run-113 的周期性 Ark 重试已成功越过网络层：7 个 calls 全部完成 TLS/credential/HTTP，DeepSeek/retry/unknown 0。新的 first divergence
是模型把已正确选择的 Search Citation 长 ID 抄错一个字符，并在两个 bounded repairs 中仍未收敛。`FINDING-010-246` 将 Provider-facing
Primary Claim 改为 1-based Observation/Citation ordinal selection，Application 再解析为 exact refs；目标门禁和 clean commit 后执行
fresh qualification 与 run-114，当前仍没有新的 Draft seal、Review、Delivery 或质量 verdict。

clean `912712c… / e40ba2f…` 的 fresh Ark qualification 已 13/13 PASS。随后 run-114 preparation-only、run-115 Ark pre-dispatch
unavailable → DeepSeek definite HTTP 402，以及 run-116 Ark 9-call `SUCCEEDED / ACCEPTED` 已封存；ordinal protocol 取得 live proof，当前没有
Provider 网络等待。

`FINDING-010-247` 记录 run-116 Delivery 的独立质量审计：模型把 acquisition intent/query echo 的 `SpEL/DTO` 推断提升为事实，跨资源 Claim
又漏选 Repository declaration Citation，两个 Reviewer 均放行。current protocol 升为 `@32 / Primary @31 / Review @21 / preflight @26`，
向 Primary/Reviewer 投影 trusted Citation locator metadata 并禁止 intent echo 作为 Evidence；clean gate 后执行 fresh run-117 与异质冻结题。
run-116 仍不是质量或 MVP PASS。

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
