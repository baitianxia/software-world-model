---
id: ITER-NNN-VERIFICATION
kind: iteration-verification
status: not-run
authority: planned-verification
owners: [quality]
depends_on: [ITER-NNN-PROPOSAL]
code: []
tests: []
iteration: ITER-NNN
product_goal_gate: V-000
product_goal_outcome: user-visible-general-source-qa-delta
product_goal_evaluation: independent-hidden-plus-live-ad-hoc
product_goal_result_id: pending
plan_revision_ref: ITER-NNN-PDR-NNN
current_action_ref: ITER-NNN-ACTION-DIRECTION-FREEZE-NNN
current_action_case_id: V-DIRECTION-FREEZE-NNN
---

# Iteration NNN Verification Matrix

| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |
|---|---|---|---|---|---|---|
| V-000 | 本轮相对 baseline 可测缩短通用源码问答 MVP 差距，并在答案质量上严格超过 current Codex | product / comparison | 未参与实现的真实工程；独立持有的 held-out 和现场问题；exact current Codex identity/protocol；双方密封答案；随机匿名映射；独立盲评量表 | 系统绝对质量 PASS；逐题无物质退步；总体答案质量差值严格为正；全体打平 FAIL；次级效率指标不得补偿；同一正式 Web 可人工验证 | pending | not-run / blocking |
| V-DIRECTION-FREEZE-001 | 在任何产品/Web 变更前冻结可复现四路方向 Gate | product / gate freeze | 三条异质真实工程问题（至少两条 unseen、无 POM-only）；四路 runner；independent exact-source ledger；盲化 rubric；exact model/tool/permission/cache identities；Result Schema | 外部调用 0、产品代码变更 0；四路输入和单变量边界完整；答案密封/匿名/独立裁决可重放；Result exact plan fields 已冻结 | pending | not-run / blocking |
| V-DIRECTION-QUALITY-001 | 世界模型+Agent 在最早价值 Gate 中产生严格正价值 | product / four-arm blind comparison | `V-DIRECTION-FREEZE-001` exact freeze；direct relevant evidence、same-Agent source-only、same-Agent World Model+source、current Codex；独立 source ledger | 世界模型臂绝对质量 PASS、逐题不输任一基线、总体 Codex margin > 0、至少一项非 locator 世界模型贡献；全体打平/物质退步/both-fail/unresolved/invalid/盲化失效均 FAIL；成本/时延/调用/缓存不得补偿 | pending | not-run / blocks product and Web change |
| V-ALPHA-ACCESS-001 | 四路方向 Gate PASS 后交付真实可操作产品入口 | product / first user handoff | `V-DIRECTION-QUALITY-001` PASS Result；固定启动命令、loopback 页面、请求通路、版本/限制、Provider/失败状态；声明 Chat 时包含消息历史和新对话 | 页面真实可操作；Provider 未配置、未资格或失败如实显示；Access PASS 不产生 Chat/Quality/Comparison PASS，也不能替代方向 Gate | pending | not-run / blocking |
| V-TIMEBOX-001 | 首个持续 Web Alpha 遵守微检查点、root-cause-first、授权连续性和轻量 live-attempt 停止规则 | product / delivery | 从 Slice 授权后的第一次产品代码变更计时；exact commit、本轮冻结的用户交付出口、外部 dispatch、failure-signature ledger、earliest-divergence hypothesis、本地复现与相邻案例、standing authority、scope-delta request、等待期间本地工作 | 60 分钟页面、180 分钟持续 Alpha；240 分钟无 Alpha 时停止扩域、hardening、full regression 和无新证据的外部重跑，但继续最小体验恢复；standing authority 内直接执行并生成机器收据，只有 scope delta 在 exact freeze 后申请；只有 delta request 已发出且独立安全工作穷尽才可等待；每点立即交付，计划/测试/文档不算用户可见增量 | pending | not-run / blocking |
| V-PUBLIC-SOURCE-AUTHORITY-001 | 公开开源 exact revision、clean、allowlisted、只读测试在 `PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY@1` 内无需逐 run/逐题人工授权，同时每次动作可精确审计 | security / external authority | human standing authority receipt、scope digest 与 revision selection policy；公开来源/许可证/exact commit-tree/clean 证明；approved Provider/model/endpoint/credential account route；预算/调度/有效期/loopback sink；两个不同问题或 run 的机器 receipt；同 approved upstream/policy 的新 clean commit；private/unknown/local/dirty、different-or-unverified source drift、route change、budget increase、fallback admission override、write、non-loopback、Production 负测 | standing scope 内两次动作及经 Source Authority 复核的同 upstream 新 clean commit 均不请求新用户收据，并在网络/credential 前生成回指同一 authority 的不同 exact Manifest/one-use receipt；receipt 缺失/失配失败关闭；每类真正 scope delta 在外部动作前阻断并要求 exact human delta grant | pending | not-run / blocking |
| V-FALLBACK-ROUTE-ADMISSION-001 | 所有 planned fallback-route dispatch 只在冻结 execution profile 引用的 admission plugin 准入或一次性 exact override 下发生 | operations / dispatch admission | `FALLBACK_ROUTE_DISPATCH_ADMISSION@1`；fallback execution profile 与 plugin identity/configuration digest；plugin 所需 trusted input 边界；无/有 exact override；preferred-route success 与 fallback-ineligible failure；跨准入边界 run；policy source missing/changed；run receipt 和逐 request audit | admission plugin PASS 且最坏质量链可在准入范围内完成才准入；其余情况无 exact override 时在 Provider socket/descriptor/TLS/credential/HTTP 前关闭且相关计数为 0；standing route/canary authority 不能绕过 admission gate；每个 request 重验准入/override 并回指 receipt；准入失效后不创建新 request；质量链不裁剪；等待期间 preferred-route/local 继续 | pending | not-run / blocking |
| V-EXPERIENCE-001 | 首次方向体验是真正可持续操作的版本 | product / browser | <exact-version-single-launch-command-fixed-loopback-address-diverse-visible-cases-and-controlled-failure> | 可重复启动；版本和限制可见；问题真实经过产品链；失败后服务继续接受输入；声明 Chat 时具备消息历史与新对话 | pending | not-run / blocking |
| V-CHAT-001 | 主工程 Agent 在同一 Conversation 完成语义多轮 Chat | product / conversation | 固定工程/revision 的五轮追问、纠正和总结脚本；随后新对话中的无指代问题 | Agent 守恒目标并按观察重规划；追问解析正确；纠正取代旧解释；每轮独立证据/审核；新对话不泄漏旧指代并在歧义时澄清 | pending | not-run / blocking |
| V-PREVIEW-001 | 用户在四路 Gate PASS 后的可持续 Alpha 上实际体验并决定是否进入夯实 | product / directional-preview | <V-DIRECTION-QUALITY-001-and-V-EXPERIENCE-001-results-diverse-visible-cases-and-new-live-input> | 独立四路技术 Gate 和 Web 质量先通过；用户给出 CONTINUE、REWORK、REDIRECT 或 REJECT；非 CONTINUE 时禁止 hardening | pending | not-run / blocks hardening, not acceptance evidence |
| V-XD-001 | `<prior-acceptance-id>` 与 `<current-slice-id>` 在同一问题中组合 | product / integration | <stage-appropriate-exact-cross-domain-case> | <evidence-bound-answer-or-honest-gap> | pending | not-run / blocking |
| V-WEB-001 | `<current-slice-id>` 通过正式 Web 执行 `V-XD-001` | product / browser | <exact-web-subject> | <manual-user-visible-result> | pending | not-run / blocking |
| V-ADHOC-001 | `<current-slice-id>` 通过正式 Web 接受现场临时问题并覆盖 `V-XD-001` | product / browser | <user-owned-live-question-protocol> | <manual-user-visible-result> | pending | not-run / blocking |
| V-REFLECT-001 | `<current-slice-id>` 根据产品证据复盘关键方案假设并作出继续或停止决定 | architecture / reflection | <exact-slice-result-assumptions-findings-and-stage-applicable-baseline-signal-or-comparison> | <complete-review-and-explicit-decision> | pending | not-run / blocking |
| V-001 | <claim> | unit / contract / CC / CE / product / activation | <exact identity> | <result> | pending | not-run / blocking |

`blocking` 只阻止对应 Case 的 PASS 声明、晋级、扩域、hardening 或 exact external action，不自动结束开发目标。活动 Slice 的本地授权仍
覆盖修复时保持 `IN_PROGRESS / coding_input=true`。结束开发回合必须有阶段交付，或已有 actual scope-delta request 且独立安全工作穷尽，或
用户明确停止/转向/拒绝，或不可绕过的安全禁止。

V-000 不能由新增 Profile/View 的封闭题集、测试数量或旧能力回归替代。测试、CC、CE、Product Validation 与 Activation 不得
互相替代。每项 Result 必须绑定 exact subject、运行身份、限制和有效期。完成时每个 Manifest 绑定的 `V-XD`、`V-WEB`、
`V-CANARY`、`V-ADHOC`、`V-REFLECT` 行都必须为 `PASS / blocking`，Evidence 必须精确填写
`<拥有该 Case 的 Slice Result ID>#<case-id>`；最终 Product Result 依赖并聚合全部唯一 Slice Result。只让 V-000 或汇总计数
PASS 不算完成。`V-REFLECT PASS` 只表示复盘完整，不表示方案通过；继续或接受必须由 Result 的独立 decision 字段表达。

`V-DIRECTION-FREEZE` 与 `V-DIRECTION-QUALITY` 是同一 Slice 中任何新产品/Web 变更之前的两个 action，不是新的产品 Slice。只有 freeze
的 exact Result PASS 才能按预注册 transition 执行四路质量 Gate；只有四路 PASS 才能进入 Web。current Codex 与直接证据都不是 Oracle
或裁判；事实来自同一 exact revision 的独立 source ledger。最终 `V-000` 必须在 held-out 套件重跑四路严格比较，不能复用方向 Result。

`V-ALPHA-ACCESS` 只证明真实产品入口和请求通路已经交给用户操作；页面 availability 不依赖答案质量 PASS，`V-TIMEBOX` 因此不能等待
完整质量回归后才开始。Provider 资格状态必须真实显示，但不是页面交付前置。Access 也
不能替代 `V-DIRECTION-QUALITY` 或本 Slice 的 Web 答案质量 Case；只有方向 Gate PASS、Web 质量 PASS 且用户 `CONTINUE` 才可进入
hardening。时间盒和
live-attempt 限制发生在问题之间，已经开始的问题必须保留完整调查、答案、Citation 和独立审核链。
`V-FALLBACK-ROUTE-ADMISSION` 发生在 Provider 外部网络之前，并独立于 Provider 资格和 fallback eligibility；任何
dispatch-without-valid-admission 都使该 Case `FAIL / blocking`，不能通过补写收据追认。失败只阻断 fallback-route 外部动作及其依赖 Gate，不结束本地 Slice 开发。
通用 Matrix 不得在 action/Case ID 或规范性语义中写死 Provider/model 名称；具体名称只能出现在当次 execution profile 配置和执行收据中。

`V-PUBLIC-SOURCE-AUTHORITY` 同时防止两种错误：不得把系统派生 receipt 冒充用户授权，也不得在 active standing scope 内制造逐 run/逐题审批。
standing authority 不免除每次 exact receipt 和 fail-closed 校验；机器 receipt 也不能放行任何 scope delta。

每个 active Matrix 还必须让 Manifest 的唯一 current action Case 恰好解析为一行。动作迁移只接受该 action 指定路径上的 sealed Result
与 digest-bound JSON 收据组合；门禁重算原始字节摘要、受保护 runner identity、case report digest 和
`INVALID > FAIL > PASS` 聚合，手写 frontmatter 不能单独放行。当前树检查之外，候选 diff 必须由 trusted base action 的
allowlist/locks 和预注册 transition 审核；候选 Manifest 不得自行放宽路径或一次推进多步。
