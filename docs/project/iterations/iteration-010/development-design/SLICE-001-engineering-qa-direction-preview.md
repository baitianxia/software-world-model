---
id: ITER-010-SLICE-001
kind: development-slice
status: authorized
authority: current-development
owners: [engineering, architecture, quality, product]
depends_on: [ITER-010-PROPOSAL, ITER-010-READINESS, ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST, ITER-006-RESULT-ACCEPTANCE, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, SYS-ADR-013, SYS-ADR-014, SYS-ADR-015, SYS-ADR-016, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-QUALITY-SECURITY]
code: [src/software_world_model/application_services, src/software_world_model/ai_infrastructure, src/software_world_model/interface]
tests: [tests]
iteration: ITER-010
coding_input: true
product_goal_gate: V-000
product_goal_accepted_capability_refs: [ITER-006-RESULT-ACCEPTANCE]
product_goal_cross_domain_case_ids: [V-XD-001]
product_goal_web_checkpoint_id: V-WEB-000
direction_preview_web_checkpoint_id: V-EXPERIENCE-001
product_goal_direction_preview_checkpoint_id: V-PREVIEW-002
product_goal_reflection_gate_case_id: V-REFLECT-001
product_goal_slice_gate_case_ids: [V-BASELINE-001, V-ARCH-001, V-COGNITION-001, V-QINTENT-001, V-INVESTIGATE-001, V-BROKER-001, V-LEDGER-001, V-ISOLATION-001, V-ANSWER-001, V-REVIEW-001, V-LIMIT-001, V-SEC-001, V-XD-001, V-WEB-000, V-WEB-001, V-PREVIEW-001, V-REFLECT-001, V-EXPERIENCE-001, V-ANSWER-REWORK-001, V-PREVIEW-002]
---

# SLICE-001：持续 Web Alpha 与答案质量返工

## Status and dependencies

`AUTHORIZED / REWORK / CURRENT DEVELOPMENT / CODING INPUT`。用户曾以
`codex-user-message:sha256:585f02c4edcf25502b40f880c17a7bdf7f1af71044cd8d1bbe97b055a735ee9e`（`2026-08-21T09:18:34Z`）
接受 Readiness 并只授权本 Slice。`SLICE-002/003` 不随之授权；此前绑定修正前一次性检索/先封包设计的收据不构成本 Slice 的权限来源。

公开题和现场题执行后，旧记录把消息 `d746968f…` 解释为 `REDIRECT`：默认正文仍被类、方法和调用顺序主导，Reviewer 没有识别该质量
失败。[PDR-001](../decisions/PDR-001-resume-as-rework.md) 已确认该消息没有明确拒绝方向，当前决定为同轮 `REWORK`。
`ITER-010-RESULT-SLICE-001-STOP-REDIRECT` 继续保存 exact 执行事实。用户现以
`codex-user-message:sha256:32b298dedd814a93d8dc0a086776090342f14856f032283fddb453061c1efeb5`（`2026-08-24T02:55:16Z`）
明确要求继续开发，恢复同一个 Slice 的产品/System 编码和本地确定性验证。该收据晚于失败 Result 与 PDR-001，不改写历史失败，也不授权
Slice2/3、hidden、Production Activation 或复用旧 live grant。

## Rework outcome：先交付持续 Web Alpha

恢复开发后的首项交付必须是普通用户实际可持续使用的同一产品 Web，而不是固定 1+1 问题的评测运行器：

1. 服务可通过一条固定、文档化的命令重复启动在 `http://127.0.0.1:8765/`，无需认证；普通体验者不需要拼装逐题 freeze、grant 或内部
   run 参数。页面明确显示产品版本、工程精确版本、Alpha/非生产状态和已知限制。
2. 启动时固定一个本地工程、精确 revision、世界模型认知、Source Profile、Provider/model 与只读范围；同一运行会话允许用户连续提出
   任意自然语言工程问题，不得要求每题重启服务或重新走一次项目计划授权。
3. 每个问题保持独立 Request、Ledger、Package、Answer、Review 和 Citation 身份。某题调查失败、审核拒绝或达到安全熔断时只关闭该题，
   页面展示真实失败或 Limitation，服务仍可接受下一题；错误答案不得被标成已审核成功。
4. 在同一 Slice 内对答案层级和 Reviewer 漏判做最小、通用修复，并以原现场登录题加至少两个相邻或异质问题回归。至少一个问题不是实现
   走读题；不得加入工程名、问题文本、关键词、符号、类、方法、fixture 或 Oracle 特判。
5. 用户可持续体验和独立技术复核完成前，不启动第二工程、持久恢复、完整异常矩阵、全面性能安全、hidden、三臂或 full regression。

自由提问所需的会话级授权、动态问题披露和 System Owner 语义必须在编码前以最小变更闭合；这项必要安全工作不能扩张为先建设完整答案
Schema 或评测体系。模型调用上限仍只作为安全熔断，不能为了减少调用而省略调查、Citation 或独立审核。

开发 baseline 仍候选绑定 commit `1fb997bab6444523f82ebf1a514a1abbf79656c7` / tree
`1369ce932c778c57a118123e8257ede476229d73`；冻结的 planning commit/tree 为
`01dcfe2233625dfaa021495850fb18ae1323063b` / `8e364ae854bfaa48580ab080a3e0d9c9c43c3d6f`。本开发授权不允许
credential、Provider/model call、live Web/browser、源码片段外发、hidden disclosure 或 Production；live 必须在产品 freeze 后另取 exact grant。

用户随后以 `codex-user-message:sha256:b8b6931f8d76b45a16fa50ae057d7fa6ccd744d58f6041d3fdfc1fd5ca84e7c7` 授权完成本 Slice 所需权限；
该 root authority 已通过 exact product/request/Provider/role/input grants 收窄并消费。Listener 已停止，所有旧 grant 不得复用。Slice2/3、
hidden 与 Production Activation 从未授权。

## Product-goal contribution and cumulative integration

- Product delta：把“固定调查后代码走读”推进为“世界模型认知引导、模型自适应读源码、答案优先”的真实纵切。
- Existing capability：复用 ITER-006 exact Snapshot、declaration/`CALLS`、Citation、只读来源和 loopback Web，不复制 validation-only 入口。
- New chain：World Model Cognition Context → Investigation LLM → Source Broker → Retrieval Worker → append-only Ledger → 双分区 Package →
  Answer → Reviewer；审核给出具体 gap 后，新的 Verification Investigation 在新上下文中自适应补证，再形成后继 Package、重答、重审。
- Earliest Web micro-checkpoint：最小链一旦完成，立即用一条需要 World Model 认知与 query-time Source 共同支持的代表问题跑真实 Web；
  exact revision、只读、不可信来源、support/citation 分区、Citation 和独立 Review 在该检查点不可延后。
- Fast checkpoint：一个真实工程 4 条不同维度自然问题，加至少一条现场题；至少 3 supported、至少 2 个非实现维度。
- Deferred hardening：持久恢复、复杂冲突、跨轮去重、完整异常矩阵、第二工程、全面性能、完整回归、hidden 和三臂对照留到方向
  `CONTINUE` 后。Slice1 仍须保留实际发生的 Conflict/Gap/Failure/Partial/Unknown，不得静默消解。
- Stop：世界模型被手册化；调查一次性固定；模型直接 Source；任何特判；Ledger/Package/Review 身份错配；答案仍是代码走读；错误、安全
  或审核降级；用户 REDIRECT/REJECT。

## Direction preview checkpoint

历史 `V-WEB-000/V-WEB-001` 已证明同一 product-owned 页面和完整最小后端链可以运行，但它们依赖启动前精确准备的一题，不能再被称为
持续可体验版本。返工检查点 `V-EXPERIENCE-001` 必须从同一页面完成：一次启动、一次固定工程/revision、同一会话连续提交原失败题及至少
两个相邻或异质问题，期间不重启服务、不更换产品路径，也不因其中一题失败停止后续提问。

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

预期行为是：固定工程会话持续接受自由问题；每题由 World Model 提供 exact 系统认知，Investigation LLM 保留原问题全部约束，根据每一步
Ledger Result 自适应决定下一项抽象读操作或结束，Broker/Worker 控制 actual read。调查结束后才密封 Package，Answer 在新上下文中只读
包、先回答目标；Reviewer 在独立新上下文中检查并可指出具体证据缺口，但不能自己读源码或执行工具。任一题失败不会污染后续题或关闭
Web 服务。

## System contracts and invariants

### Phase 0：复核正式边界

开发前必须确认 `FINDING-010-002`、`SYS-ADR-016`、Engineering Question Answering Contract、Product Success、runtime/Agentic/Evidence/
World Model/Response/Source/Security/Browser 文档和治理门禁共同表达 `ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3`。严格 `WORLD_MODEL`
Source-off 和显式 `DIRECT_INVESTIGATION` 继续保留，不得静默 fallback。任一 current Owner 或 Manifest digest 不一致即停止。

### Phase 1：最小真实协议

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
  检查面选择各决定性实现，flow/lifecycle 把结果、状态变化与持久化/审计/缓存/通知/外部交互副作用拆成独立 checklist。4-path 上限与
  12-call initial fuse 保证 4 次 direct READ/PARSE + 1 FINISH 后仍有 7 次自适应余量；可选佐证不得占用 mandatory capacity，也不能因
  evidence modality 可用或用户只要求“可核对依据”就引入无关 TEST/log/config need。
  Application 区分 registered/required/investigated/untried/unregistered classes 与 required/unread paths；向 Initial Investigation 投影 exact
  maximum/remaining calls，并在 unread required path 存在时投影 direct locator descriptor 且只暴露这些路径的 eligible locator；角色优先
  直接读取，不通过内容 SEARCH 重新发现已知 path。任何 FINISH 前都必须以无行范围、
  `coverage_complete=true` 的 READ/PARSE 闭合 required paths，SEARCH/截断内容不消费义务；non-supported FINISH 只额外闭合仍可调查的
  required class，不机械遍历无关 registered class，unregistered required 则保留为能力边界。
- 每个 FINISH disposition 必须从完整引用内容列出有界原子 material observations，区分 process、outcome、state change、side effect 与
  limitation，并逐条绑定 admissible evidence；`SUPPORTED` 只能包含 affirmative observation，non-supported outcome 只能包含
  `LIMITATION`。Provider-facing output 用结构互斥的 `supported_finish_dispositions / non_supported_finish_dispositions` 两数组，可信
  adapter 只合并已验证数组；Application Domain 再独立拒绝混类。一个代表性事实不能闭合宽泛 checklist。Application 生成稳定
  observation identity 并拒绝跨 checklist、重复、错误分区或证据不闭合。caller/configuration/wiring 只证明接线，不能替代被委托组件自身
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
- Reviewer 在另一个新上下文中读取原问题、理解记录、当前 Package 和 Draft，无 repo/Source/World Model tool、FS、Shell、network 或
  credential。它从原问题独立重建 material conclusions、列出 Application checklist omission；再检查完整 Package evidence，独立形成带
  evidence entry 的原子 observations，分别列出 Package 与默认 Draft omission，并给 direct answer、abstraction fit、material
  completeness、implementation-detail budget 返回 PASS/FAIL；对 flow/lifecycle 它逐 full-content entry 审核持久化/审计/缓存/通知/外部
  交互，对多机制检查各决定性实现而非 caller/wiring。四项全 PASS、所有 omission 为空且无 Finding 才能批准。表达缺陷可请求同包
  针对性重写；证据缺口只能输出绑定 Checklist/Claim/evidence class/need 的 versioned Verification Request，不能提出可执行
  path/command/operation。
- 合法 Request 启动独立 `Verification Investigation LLM`。它使用全新上下文，只读具体 gap、当前 Package 与 Ledger prefix，根据每步新
  Result 自适应提出 search/read/parse/finish；每一步仍由 Application/Broker 校验编译、Worker 执行。它不回初始 Investigation LLM，
  不继承 Reviewer 会话，也无直接来源权限。完成后追加新 Ledger Revision、密封新 Package、完整生成新 Answer 并独立 Review；旧 Review
  不得批准新包。
- 为尽快验证方向，Slice1 每个问题最多冻结一次 Verification Investigation；这是 preview 的临时安全边界，不是永久协议。Slice2/3
  禁止固定一轮上限，改为在各自 exact freeze 前预密封 Package Revision、model call、Broker operation、source bytes、wall time 与
  no-progress 高安全熔断。answerable 因任一熔断耗尽而未回答必须计 `FAIL`，不能用 Limitation 取得 supported 分数。
- 调用、步骤、文件、bytes 和 wall time 是高安全上限。达到上限失败关闭；只有预先分类的真实 boundary 才能交付独立审核认可的准确
  Limitation，answerable 因上限耗尽未回答必须计 FAIL。不能删减调查、checklist、Evidence、Citation 或 Review。
- 交付后的高质量证据/结论可异步提议 Knowledge Update，不能阻塞或追认本题答案。

## Interfaces and affected code

本 Slice 授权允许修改 Application orchestration、Investigation/Verification Investigation role、Source Broker port/policy、Retrieval Worker adapter、Evidence Ledger/Package、
Response Control、Answer/Review Strategy、role-specific Gateway input、product-owned HTTP/Web 及对应 tests。优先复用现有 World Model Query、
Evidence Answering、Citation 和 Web 组件，不复制 ITER-009 pipeline。

源码路径不能直接传给模型后依赖 prompt 自律；模型只能提出 Broker 能验证的抽象意图，且其 evidence class 声明不能把一个 Profile
未登记的路径重标为源码、仓库文档、配置或测试。所有自然问题进入同一协议，UI 不按问题维度切换后端。禁止工程、题目、关键词、
符号、类、方法、约定文件名、fixture 或 Oracle 特判；来源类型由显式 versioned Profile capability 决定。

## Compatibility, data and security boundaries

严格 `WORLD_MODEL` no-payload/Source-off、Citation 和历史 accepted 测试继续成立；新协议使用独立 identity。源码、README、注释、配置、
测试均视为不可信输入，其内容或模型声明不能获得 evidence class 权威；拒绝 Source Profile 漂移/类型重标、symlink escape、
submodule/remote 自动获取、binary、oversize、path traversal、写、执行和网络。

每个 original question、Cognition Context、Ledger Revision、Package、Draft、Review、补证请求和独立 Verification Investigation 保存稳定
ID/digest。Slice1 的 request-scoped Ledger 必须只追加且能形成完整 Result；跨进程持久恢复与复杂幂等 replay 明确后移到 Slice2。live
前另行冻结 exact
Provider/model/role、fragment allowlist、redaction、configuration、secret reference 和 audit；计划与开发授权都不允许自动外发。
持续问题 POST 还必须在 receipt/transport/credential 前满足 exact same-origin `application/json`；跨站 simple request 不能仅因目标是
loopback 就取得题目提交权。

## Open questions and implementation risks

- 调查模型可能循环或过早 FINISH；最小版保留基本 progress/no-progress 安全关闭与 Application FINISH 检查，完整循环/异常矩阵后移。
- World Model 和 Source 冲突时必须把两者作为 `boundary/audit` 条目保留，不能默认源码或较新时间自动获胜；复杂冲突裁决留到 Slice2。
- 独立补证可能重复初始调查；Slice1 只证明一轮全新上下文、结果驱动和后继 identity，复杂多轮、dedup/recovery 留到 Slice2。
- 公开 4 题不能证明跨工程泛化；它只判断方向，不能替代 Slice2/3。
- 更多模型调用可能增加成本；首版先证明正确职责和答案质量，随后测量，不因调用数目标删减工作。

## Acceptance scenarios

1. `V-BASELINE-001`：exact baseline/tree 与 ITER-009 rejected 结论一致。
2. `V-ARCH-001`：Finding、ADR/Contract、Manifest、docs gate 一致；严格 WORLD_MODEL/DIRECT 回归边界不变。
3. `V-COGNITION-001`：World Model 以 exact、持久、版本化外部认知供模型使用，不退化为手册/缓存/keyword hints。
4. `V-QINTENT-001`：原问题目标、受众、层级、结论、语言和约束不丢失；无特判路由。
5. `V-INVESTIGATE-001`：至少两步由 prior Result 驱动；partial/zero cognition 不阻断必要 Source；FINISH 有证据与 progress 支持。
6. `V-BROKER-001`：Broker 以 exact Source Profile 编译并审计抽象提议与 evidence class，Worker 仅执行 global/class allowlisted
   read-only exact-revision 操作，Application 重验 Result class/path；模型直接权限和分类权均为 0。
7. `V-LEDGER-001`：Ledger append-only，调查后 seal；Package 的 support/citation 仅 admissible，boundary/audit 必须保留且不能支持肯定 Claim，
   seal 不等于真值，revision 身份不可混用。
8. `V-ANSWER-001`：历史 4+1 题结果继续保留，其中现场题答案层级与完整性 FAIL，不因 PDR 改写为 PASS。
9. `V-REVIEW-001`：历史 Reviewer 漏判继续为 FAIL；返工版 Reviewer 只给具体 gap，独立 Verification Investigation 在新上下文中多步自适应补证，经 Broker/Worker 形成新
   Ledger/Package/Answer/Review；不回初始 Investigation 且无直接 Source。
10. `V-LIMIT-001`：证据或安全上限不足时准确 Limitation 或失败关闭，不伪造 absence/coverage；answerable 因上限耗尽计 FAIL。
11. `V-XD-001`、`V-WEB-000`：历史最小纵切技术 PASS 保留，不冒充持续体验或返工 PASS。
12. `V-EXPERIENCE-001`：同一 Web 由一条固定命令重复启动，在固定工程/revision 的同一会话连续自由提问；受控坏题只失败该 Request，
    服务继续接受下一题，状态不串扰；页面展示版本和限制，并证明答案来自真实世界模型—调查—证据链而非预制回放。
13. `V-ANSWER-REWORK-001`：原失败题加至少两个相邻或异质问题完成通用修复回归；重大错误为 0、重要结论有 Citation、至少一题非实现走读，且无任何特判。
14. `V-PREVIEW-002`：独立技术复核后，用户在持续 Web Alpha 上实际自由提问并决定 `CONTINUE / REWORK / REDIRECT / REJECT`。
15. `V-SEC-001`：Source injection、path/write/exec/network/secret/disclosure、budget、no retry、loopback 全部符合边界。
16. `V-REFLECT-001`：历史反思事实保留；返工 Result 重新给出 A1—A3 证据、A4/A5 early signal、全部 Finding 和用户新决定。

## Architecture reflection checkpoint

返工 Result 必须复核世界模型概念、调查自适应性、Broker/Worker 权限、Ledger/Package identity、补证独立性、持续 Web Alpha、安全、
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
后续发现按 [Findings](../findings/README.md) 与[实现发现回写规则](../../../governance/implementation-feedback-policy.md)处置。
