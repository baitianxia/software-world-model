---
id: ITER-010-PROPOSAL
kind: iteration-proposal
status: accepted
authority: project-proposal
owners: [product, project, architecture, engineering, quality]
depends_on: [SYS-PRODUCT-SUCCESS, ROADMAP-M-002, ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST, ITER-006-RESULT-ACCEPTANCE, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, ITER-010-PDR-010, FINDING-010-107, FINDING-010-108, FINDING-010-109, FINDING-010-153, SYS-ADR-013, SYS-ADR-014, SYS-ADR-015, SYS-ADR-016, SYS-ADR-017, SYS-ADR-018, SYS-CONTRACT-AI-CAPABILITY-EVALUATION, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS, SYS-CONTRACT-KNOWLEDGE-STRUCTURE-MODEL, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-QUALITY-ACCEPTANCE, SYS-QUALITY-SECURITY, SYS-OPS-LOCAL-BROWSER]
code: []
tests: []
iteration: ITER-010
coding_input: false
current_execution_decision_ref: ITER-010-PDR-012
current_execution_finding_refs: [FINDING-010-132, FINDING-010-133, FINDING-010-134, FINDING-010-135, FINDING-010-136, FINDING-010-137, FINDING-010-138, FINDING-010-140, FINDING-010-141, FINDING-010-153, FINDING-010-161, FINDING-010-162, FINDING-010-163, FINDING-010-164, FINDING-010-165, FINDING-010-180, FINDING-010-204, FINDING-010-205, FINDING-010-206, FINDING-010-207, FINDING-010-208, FINDING-010-209, FINDING-010-210, FINDING-010-211, FINDING-010-212, FINDING-010-213, FINDING-010-214, FINDING-010-215, FINDING-010-216, FINDING-010-217, FINDING-010-218, FINDING-010-219, FINDING-010-220, FINDING-010-221, FINDING-010-222, FINDING-010-223, FINDING-010-224, FINDING-010-225, FINDING-010-226, FINDING-010-227, FINDING-010-228, FINDING-010-229, FINDING-010-230, FINDING-010-231, FINDING-010-232, FINDING-010-233, FINDING-010-234, FINDING-010-235, FINDING-010-236, FINDING-010-237, FINDING-010-238, FINDING-010-239, FINDING-010-240, FINDING-010-241, FINDING-010-242, FINDING-010-243, FINDING-010-244, FINDING-010-245, FINDING-010-246, FINDING-010-247, FINDING-010-248, FINDING-010-249, FINDING-010-250, FINDING-010-251, FINDING-010-252, FINDING-010-253]
current_scheduling_finding_ref: FINDING-010-179
---

# ITER-010 Proposal：软件世界模型与主工程 Agent 驱动的多轮工程 Chat

## PDR-012 current amendment：持续完成真实浏览器 Chat

PDR-011 已如实保存 run-052/053 的答案前失败，但把工作计划误作授权来源并停止了仍在 standing scope 内的产品开发。PDR-012 保留全部
失败证据，恢复同一 Slice 的持续产品开发；普通失败不再迁移游标或产生新的治理任务。当前唯一目标是尽快交付答案质量合格的真实浏览器
Chat MVP；首条可运行纵切只是开发体验候选，不是 MVP 完成。

ITER-010 保持“双核心”产品架构：软件世界模型维护 exact revision 上持久、版本化、可验证、可更新的软件认知；主工程 Agent 以该认知为
起点，持续维护用户目标、假设、计划和对话上下文，并按证据缺口通过受控工具读取源码、文档、配置或测试。Application 密封逐 Turn
Evidence Package，主工程 Agent 形成自然答案，fresh independent Reviewer 检查问题满足度、证据支持和 Citation。

历史 `ITER-010-RESULT-V-MVP-EXPERIENCE-001` 的 machine PASS 只证明 failure handoff 完整，产品质量仍 FAIL；它不代表用户获得过完整
体验，也不撤销活动 Slice 和公开工程 standing authority。当前工作计划不再设置 Activation、Freeze-first、分钟硬停、逐候选授权或
“一次修复即停止”的产品出口。

`FINDING-010-204 / run-081/082` 进一步证明当前没有 Provider 等待点：run-081 是 stale pricing evidence 导致的外调前失败；fresh pricing
admission 后，run-082 的 Ark 41 次 dispatch 全部成功，故 DeepSeek 0 符合 preferred-first 合同。该 run 暴露的是 Application-owned
Observation ID 抄写、未声明 diagnostic 绕过、caller effect scope 自相矛盾和三次 Review 容量不足。current `@10/@4` candidate 在不改变
15 次 per-Turn dispatch authority 的前提下作通用闭合；其下一项真实证据当时为 fresh run-083。

`FINDING-010-205 / run-083` 已证明该 candidate 关闭了 Q5 的两个目标缺陷，且 Ark 43 次 dispatch 全部成功；当前不是 Provider 等待或
fallback 问题。新的最早偏差是 Q2 的 syntax→closed-contract 分层输出失败，以及 Q1 对 global metric/stale Boundary 的 materiality 漏审。
`FINDING-010-206/207 / run-084` 又证明真实 Search modality 与首版 matcher fixture 不一致，导致 resolved acquisition 被误分类；同时 Ark
首次 typed TLS unavailable 发生时，旧 DeepSeek receipt 已从 listener preparation 提前耗尽 600 秒。current `@12/@6/@7` candidate 分开验证
Search `LITERAL_TEXT_SEARCH_HIT` 与 full Read `EXACT_STATIC_SOURCE_TEXT`，逐 challenge 投影 closed disposition domain 并禁止 authored string
首尾 whitespace；DeepSeek `@3` 只在 first real fallback preflight 激活并重验 active receipt。15 次 Turn authority、route、budget、retry 与
Production 边界不变，144 tests PASS；fresh run-085 是下一项真实证据。

`FINDING-010-208 / run-085` 又证明 Ark preferred route 并未不可用：52 次 HTTP dispatch 中 51 次完成、1 次 post-dispatch outcome unknown，
因此 DeepSeek 0 正确。Q4 零 dispatch Clarification 保持，其余四题仍未形成完整交付。current `@13/@7/@8` candidate 闭合 nested object exact
fields、trusted ACTION/DRAFT/phase branch、Limitation 的最小 Boundary binding，并区分结构化 binding 与正文实际 disclosure；同时保持既有值
repair 守恒和 untrusted typed-output error 边界。15 次 Turn authority、route、fallback、预算、retry 与 Production 边界不变，144 tests
PASS；fresh run-086 是下一项真实证据。

`FINDING-010-209 / run-086` 又证明 Ark preferred route 仍未出现 HTTP 前 unavailable：49 次 HTTP dispatch 中 47 次完成、2 次
post-dispatch outcome unknown，故 DeepSeek 0 正确且不重发。Q4 零 dispatch Clarification 保持，其余四题仍未形成完整交付。新的最早通用
偏差是 final preflight 未重复 exact SUPPORT/BOUNDARY ID domains，以及 Review successor 丢失 exact rejected Draft 后重建并扩张 Claims。
current `@14/@7/@9` candidate 把 rejected Draft 作为 same-Package targeted edit base，并在 final preflight 重复 exact reference domains；
15 次 Turn authority、route、fallback、预算、retry 与 Production 边界不变，144 tests PASS；fresh run-087 是下一项真实证据。

`FINDING-010-210 / run-087` 已证明上述 exact edit base 生效：Q1 的 rejected Draft Claim 数保持 `4 → 5 → 6 → 6 → 6`。Ark 4 个 sealed
429 后按现行策略合法切换 DeepSeek；DeepSeek 42 个 call 完成、1 个 post-dispatch unknown，retry/人工审批/Production 仍为 0。Q4 零
dispatch Clarification 保持；Q1/Q2/Q5 的 Review limit 又暴露 semantic Claim coverage 被按 phrase 重复拆分、generic global-completeness
Claim exception 与 `LIMITATION` 零 Claim branch 冲突，以及 opaque Boundary binding 被误作正文披露。current `@15/@8/@10` candidate 现按
semantic coverage、response kind 与 hidden binding 收窄合同；15 次 Turn authority、route、fallback、预算、retry 与 Production 边界不变，
144 tests PASS；fresh run-088 是下一项真实证据。

`FINDING-010-211 / run-088` 又证明 Ark 的 4 个 sealed 429 可合法启动 DeepSeek 周末 fallback；DeepSeek 52 个 call 完成、1 个
post-dispatch unknown，retry/人工审批/Production 仍为 0。Q4 零 dispatch Clarification 保持，其余四题仍未交付。新的最早通用偏差是
Reviewer 未在一次完整 Draft audit 中报告全部已见 defects、重复 local Finding code 消耗 repair、focused assessment/Claim verdict/Finding
body 不双向闭合，以及 Primary 没有在一个 replacement 中解决全部 ordered Findings。current `@16/@9/@11` candidate 密封 full-audit、
exact focused closure、Reviewer-authored empty-Finding decision repair、未引用 duplicate local-code disambiguation 与 all-Findings rewrite；15 次 Turn
authority、route、fallback、预算、retry 与 Production 边界不变，146 tests PASS；fresh run-089 是下一项真实证据。

`FINDING-010-212 / run-089` 再次由 Ark 4 个 sealed 429 合法进入 DeepSeek；DeepSeek 27 个 call 完成、1 个 post-dispatch unknown，
retry/人工审批/Production 仍为 0。Q4 零 dispatch Clarification 保持；Q1 的 focused guard 拒绝矛盾 Review 后，repair 原样复制 invalid
object；Q3 在两个 reportable Boundary 已允许 Limitation 时仍复制 forbidden Source query；Q5 的 Primary 两次原样返回 rejected Draft，Reviewer
又在 Limitation 上要求 Claim、误报已有 Boundary binding并把 Search/interface 当实现证据。current `@17/@10/@12` candidate 密封
changed-replacement guard、typed contract-repair directive、actual focused index diagnostic 与 pure-boundary Limitation review；15 次 Turn
authority、route、fallback、预算、retry 与 Production 边界不变，147 tests PASS；fresh run-090 是下一项真实证据。

`FINDING-010-213 / run-090` 的 Ark 31 completed / 1 pre-dispatch TLS failure / 1 post-dispatch unknown 如实密封；Q3 fallback 因 pricing
evidence 超过 900 秒在 DeepSeek credential/TLS/HTTP 前拒绝，DeepSeek dispatch 0。Q4 零 dispatch Clarification 保持；Q1 coherent semantic
repair 回退为 non-JSON prefix 后旧单向 category gate 未使用第二个 slot，Q2 audit-only assessment 缺 Finding code且 repair 原样返回。current
`@18/@11/@13` candidate 允许第二次 repair 处理任意不同 validator category，并对 audit-only missing binding 给出单义 diagnostic 与 typed
closure directive；两次上限、15 次 Turn authority、route、fallback、freshness、retry 与 Production 边界不变。模型边界 34 tests、相邻
十二模块 148 tests 均 PASS；提交后以 launcher 前最后时刻 fresh pricing capture 执行 run-091。

`FINDING-010-214 / run-091` 的 Ark 37 completed / 1 post-dispatch unknown 如实密封；没有可信 pre-dispatch unavailable，故 DeepSeek
dispatch/credential/TLS/HTTP 均为 0。Q4 零 dispatch Clarification 保持；Q1 交付了含 affirmative source facts 却零 Citation 的 Limitation，
Q2 补证后丢失完整 Findings，Q3 cognition literal repair 原样重复非法 query，Q5 按 unknown no-retry 失败。current `@19/@11/@14`
candidate 保留 evidence action 后的 rejected Draft/Findings/Review baseline，把 Limitation 限于零 SUPPORT，并闭合 material literal replan 与
resolved-candidate audit-only final preflight；authority、route、fallback、freshness、retry 和 Production 边界不变。fresh run-092 是下一真实证据。

`FINDING-010-215 / run-092` 密封 Ark 53/53 completed、DeepSeek 0、retry/人工审批/Production 0。Q3/Q4 成功，Q1/Q2/Q5 共同暴露
unbound + undisclosed resolved Search Boundary 仍可被 Reviewer 判为 audit-only，并生成没有真实 rewrite surface 的 Finding。current
`@20/@12/@15` candidate 用 exact Draft substring 数组闭合 disclosure、reference 与 disposition；no-op audit-only 和虚构 fragment 失败关闭，
而 bound stale reference 或真实 disclosed fragment 仍可形成合法无补证修复。authority、route、fallback、freshness、retry 和 Production 边界
不变；fresh run-093 是下一真实证据。

`FINDING-010-216/217 / run-093` 密封 Ark 19、DeepSeek 28，且 fallback 只在 3 个 sealed Ark 429 后自动发生；人工审批、retry、
Production 仍为 0。Q1 暴露 inline-code backticks 造成 exact fragment 假阴性，Q2/Q5 暴露显式 module scope 没有进入 Source Broker 与
bounded fallback 重扫。current `@21/@13/@16` 与 `COMPILED_SOURCE_OPERATION@3` 分别做 presentation-normalized verbatim closure 和
Broker-recomputed prefix/rotating fallback closure；所有预算与 authority 不变，fresh run-094 是下一真实证据。

`FINDING-010-218 / run-094` 密封 Ark 4 个 sealed 429、DeepSeek 20 completed + 1 post-dispatch unknown；Q1 ACCEPTED/Q4 零调用
Clarification 通过，Q2 unknown、Q3 limitation、Q5 protocol violation 使整体仍 FAIL。Q5 的最早偏差是 original-question module helper 把
同 module 的 POM/TEST path 混入 SOURCE prefix，Broker 按 class 正确拒绝。current closure 保留完整 Request scope recognition，并只从
current operation evidence-class allowlist 选择 prefix；`COMPILED_SOURCE_OPERATION@3`、route、budget、retry 和 Production 边界不变，
fresh run-095 是下一真实证据。

`FINDING-010-219/220 / run-095` 密封 Ark 4 个 sealed 429、DeepSeek 27 completed + 1 post-dispatch unknown；Q1/Q5 ACCEPTED、
Q4 零调用 Clarification 通过，Q2 unknown、Q3 Reviewer reject 使整体仍 FAIL。最早偏差分别是 interactive idle 后复用 stale DeepSeek
keep-alive，以及 focused Review 的 material/null-code assessments 与 unbound Finding 同时存在且 generic repair 原样重复。current closure
以 Engineering Chat runtime ref `@3` 在 qualified transport call 前轮转 stale 或 idle ≥60 秒的 session，并为 challenge-bound Finding
mismatch 提供 exact 二选一 repair；base Adapter/Conformance identity、`PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@2` 的 3/20 bounds、
零 retry、route、budget 与 Production 边界不变，run-096 是下一真实证据。

`FINDING-010-221 / run-096` 密封 Ark 4 个 sealed 429、DeepSeek 37/37 completed，stale/idle rotation 已真实通过；Q1/Q5
ACCEPTED、Q4 零调用 Clarification，Q2 structured-invalid、Q3 reviewed limitation 使整体仍 FAIL。Q2 first divergence 是 focused
Reviewer 从 method vocabulary或 prior Finding 向 exact caller-only Claim 重导入 database effect，随后 Primary 两次 exact-repeat rejected
Draft。current `@23/@15/@18` 把 exact challenged Claim 独立投影给 Reviewer，并要求 repeat repair 显式区分 invocation/order 与未确认 effect
或删除 assertion；wire output schema、authority、route、budget、retry 与 Production 边界不变，fresh run-097 是下一真实证据。

`FINDING-010-222 / run-097` 密封 Ark 40 dispatch（39 completed、1 post-dispatch unknown），DeepSeek 0；Q1/Q5 ACCEPTED、Q4
零调用 Clarification。Q3 的 13 个 caller challenge 全部 WITHIN，随后 bound + empty Boundary 被 Reviewer/repair 错选
`NOT_DISCLOSED_IN_DRAFT`。current `@24/@16/@19` 逐 challenge 投影 sealed reference flag 与 fragment-state closed disposition 表；
targeted `34/34`、相邻 16 模块 `261/261` PASS，wire output schema、authority、route、budget、retry 与 Production 边界不变，fresh
run-098 是下一真实证据。

`FINDING-010-223/224/225 / run-098` 密封 Ark 24 dispatch（21 completed、1 pre-dispatch TLS failure、2 sealed 429）与 DeepSeek
32/32 completed；fallback 仍只由 trusted Ark unavailable 自动触发，retry、人工审批与 Production 均为 0。Q1 ACCEPTED、Q4 零调用
Clarification；Q2 错误 ACCEPTED 一份仅含 12 个无关 Controller Citation 的不完整答案，Q3 review-limit failure，Q5 structured-invalid，
整体仍 FAIL。current Worker 以 Java identifier components 导航 authorized tree path 而不提高 56/64 fuse；current `@25/@16/@20` 删除
caller-only rewrite 的 authored effect labels，并把 closed body + empty Findings 的 repair 收敛为 decision-only APPROVED。wire output schema、
authority、route、budget、retry 与 Production 边界不变，fresh run-099 是下一真实证据。

`FINDING-010-226 / run-099` 密封 Ark 4 个 sealed 429 与 DeepSeek 39/39 completed；Q1/Q5 ACCEPTED、Q4 zero-dispatch Clarification，
Q2 Reviewer reject、Q3 reviewed limitation 使整体仍 FAIL。真实 exact source 使用 `generateOrder` 而不是 `createOrder`，所以 run-098 的
identifier ranking 已把目标带入 56-file observation，却不能合法生成 literal hit。current successor 把最多 16 个零-hit identifier-path item
标为 navigation-only Boundary opaque READ options，禁止 Search SUPPORT，fresh full READ 后才允许 Claim；current protocol
`@26/@16/@21`、六模块 `157/157` PASS。authority、route、fallback、budget、retry 与 Production 边界不变，fresh run-100 是下一真实证据。

`FINDING-010-227/228 / run-100` 密封 Ark 4 个 sealed 429 与 DeepSeek 35/35 completed；Q2 首次通过 navigation-only opaque
READ 取得目标 full source，Q1/Q2/Q5 ACCEPTED、Q4 zero-dispatch Clarification。Q3 却重复上一轮普通流程且 Reviewer 错误
APPROVED，Q5 又投影 70 个 Citation，整体仍 FAIL。current `@27/@17/@22` 为每个 Review 强制 exact current-requirement coverage
assessment，Primary output `@3` 为每个 Claim 选择最小 exact Citation refs。authority、route、fallback、budget、retry 与 Production
边界不变；六模块相邻定向测试 `157/157` 与 documentation check `634` PASS，fresh run-101 是下一真实证据。

PDR-009 的四路前置 Gate 和多动作状态机已被 [PDR-010](decisions/PDR-010-complete-mvp-vertical-slice.md) 取代。其历史原因与结果仍由
[decisions](decisions/README.md)、[findings](findings/README.md) 和 [results](results/README.md) 保存，不是当前开发输入。

## Trigger and evidence

既有真实 Web 证明页面、精确版本、Citation 和审核链可以运行，也证明产品长期停留在代码走读、Maven/POM 窄认知和逐题修补，十轮后仍没有
满足目标的 MVP。根因属于计划与架构执行问题：把内部证明和比较工具放在完整体验之前；答案失败没有先区分世界模型构建、Agent、Evidence/
Review 与 Chat/Web 的最早偏差；过多动作、收据和时间门禁把普通开发失败变成停工。

PDR-010 因此把最早可验证产物改为完整开发体验候选，同时保留准确性、安全、独立审核和严格强基线标准。质量判断在候选可运行后立即执行，
并且是 MVP 命名、完成和用户判向的必经条件。

## Product-goal alignment and cumulative delta

- 目标用户可以在无需认证的 loopback 浏览器中围绕陌生工程持续追问、纠正、深入和总结，而不是进行互不相关的一问一答。
- 世界模型贡献必须包含非 locator 的系统认知；Maven 模块、目录或入口提示只能是窄投影，不能代表完整认知。
- 主工程 Agent 是回答和调查的大脑，但不取得 Repository、FS、Shell、network、credential 或 write 权限；实际 Source 操作仍由受控 Broker/Worker 执行。
- 每个重要结论绑定可核对 Citation；证据不足时给出具体 Unknown/Limitation，不能把未找到扩张为不存在。
- 模型路线对产品透明：产品代码只使用 `preferred/fallback` route role 和 execution-profile ref/digest，不读取具体 Provider/model 身份形成分支。
  只有独立 availability boundary 密封首选 execution profile 不可用，才可进入备用路线。
- 结构化输出无效与 Reviewer 拒绝不是“模型不可用”。前者在同一 profile 内有界格式修复，后者由同一 profile 重写并 fresh review；两者都是
  新 call、新 request identity 和新 receipt，不是 transport request retry，耗尽通用安全/no-progress 边界后如实关闭当前 Turn，不能切换路线碰答案。
- 第一次完整链只形成可供早期反馈的开发体验候选；它不证明方向或 MVP 合格。系统自身无重大错误、逐题不输 actual current Codex、总体
  严格超过 Codex和具有非 locator 世界模型贡献，共同决定是否取得 MVP 资格并进入用户判向。

## Outcome and users

首要用户是理解或维护陌生工程的开发者。目标体验是一条真正语义多轮的工程 Chat：用户自然提问，主工程 Agent 使用版本化世界模型认知
建立系统理解，根据新观察受控补证，给出直接且层级匹配的答案，并允许用户基于前文追问或纠正。页面以答案为主，内部轨迹折叠展示。

## Scope / non-goals

当前范围是一个公开 Java 工程的 exact revision、预构建世界模型认知、受控只读 Source、逐 Turn Evidence/Citation/fresh Review、
server-owned Conversation/Turn/Context、新 Conversation 隔离和无认证 loopback Web。

首次用户判向前不做 hardening、full regression、第二工程、hidden、跨重启长期 Memory、第二语言、跨仓库、公网、Production、团队权限、
任意 Shell 或源码写入。知识沉淀不阻塞当前回答，可在后续作为独立能力。

## Adopted system IDs

当前默认 Owner 是 `SYS-ADR-018` 与 `SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION`，并组合 Agentic Task、Evidence Answering、
World Model Answering、Knowledge Update/Use、Response Control、Model Gateway、Source Artifact、Security 与 Local Browser 等现行
合同。旧单轮 Engineering QA 和固定多角色调查只保留兼容或历史边界。

## Development slices and dependencies

1. `SLICE-001`：当前 active Slice。持续完成真实浏览器 Chat；首次完整三轮链可操作即作为开发体验候选交付，开发不停，随后立即用异质问题
   与 current Codex 完成 MVP 质量资格判断。
2. `SLICE-002`：用户确认方向后完成持久恢复、第二工程、复杂冲突/去重/性能/安全、完整四路因果消融与 full regression；同一 standing
   scope 内不重复申请授权。
3. `SLICE-003`：再次授权后执行最终隐藏工程、现场问题、安全与正式 Acceptance。

普通失败留在 Slice1 的同一动作：保存 trace、定位最早责任层、提出可证伪根因并做最小通用修复，再验证原失败和两个未参与修复的异质
案例。同类故障复现时停止无新证据外调并回到本地归因，但不停止整个产品开发。

## Critical assumptions and falsification plan

| 假设 | 最早证据与反证 | 反证后的动作 |
|---|---|---|
| A1：软件世界模型保持为持久、版本化、可验证、可更新的软件外部认知，提问期 Source 调查只核实、补充或纠正本 Turn 认知 | Slice1 先以 `V-MVP-EXPERIENCE-001/V-CHAT-QUALITY-001` 检查真实 Chat 中的认知使用，再在首次体验后以 `V-DIRECTION-QUALITY-001` 检查非 locator 认知贡献；Slice2/3 复验。把 World Model 降级为手册、缓存、locator 集或 Source recall 门禁，或完整 Cognition 无可验证贡献，即反证 | REDIRECT 认知与问答边界；不用命名掩盖概念漂移 |
| A2：主工程 Agent 能持续维护目标、假设、子任务和计划，依据每次观察选择 World Model/Source 受控工具并重规划，不取得直接权限 | Slice1 的 `V-CHAT-001/V-CHAT-QUALITY-001`；若仍是预先固定的角色/操作清单、需要特判，或 Agent 必须直接访问 repository/FS/Shell/network/credential/write 才能工作，即反证 | REDIRECT Agent/tool 合同；保留 Application/Broker/Worker 的 exact-version、allowlist、只读、证据身份、预算和审计责任 |
| A3：每个 Turn 的 Evidence Package、自然答案与 fresh independent Review 同时保证直接答案、Citation、失败关闭和可返工性，Reviewer Finding 只回到主 Agent | Slice1 的 `V-CHAT-QUALITY-001`。若 seal 被当作真值、prior Answer/Review 取得证据权威、Reviewer 直接规划/执行工具，或 Finding 绕过主 Agent 进入固定补证角色，即反证 | 修正 Agent—Evidence—Review 首个系统性偏差；不减少证据或独立审核换取交付 |
| A4：相同 Conversation—主 Agent—受控工具—逐 Turn Evidence/Review 协议能跨第二工程、来源组合和复杂失败泛化 | Slice2 的 `V-GENERAL-002/V-RERETRIEVE-002/V-CANARY-002/V-XD-002`；新工程或新表达必须新增项目/问题/关键词/符号/类/方法/fixture/Oracle 分支，或主 Agent 的补证与重规划不收敛，即反证 | REDIRECT 通用 Context、Agent/tool、Broker 或 Review 合同；烧毁已披露输入并保留 Result |
| A5：完整体验候选先与保留真实客户端、model、reasoning、tools 和权限的 current Codex 做严格外部比较；用户 CONTINUE 后再用同 Agent、同 Provider/model/config 且只改变认知输入的受控对照做 World Model 因果消融 | Slice1 在完整体验可交付后运行 `V-DIRECTION-QUALITY-001`：目标系统绝对质量 PASS、逐题不输 current Codex、总体严格超过 Codex，且有非 locator 认知贡献。把任一模型答案当真值或裁判、削弱 Codex、以平局或效率补偿质量，即反证；完整因果消融在用户 CONTINUE 后执行 | FAIL 后回到最早责任层，形成可证伪根因并通用修复；不得靠同题重跑碰答案，也不得停止仍有证据路径的产品开发 |
| A6：产品具有真正语义多轮 Conversation，而不是同 Session 的独立问答 | Slice1 的 `V-CHAT-EXPERIENCE-001/V-CHAT-001/V-CHAT-QUALITY-001` 至少用三 Turn 验证追问指代或用户纠正、进一步深入或总结、逐 Turn 证据与新 Conversation 隔离；完整扩展场景在用户 `CONTINUE` 后验证；任一当前必需项缺失即反证 | REWORK Conversation/Work State 而不将单 Turn 失败自动升级为整轮 REDIRECT |

Slice1 先以 `V-MVP-EXPERIENCE-001` 验证 A1/A2/A3/A5/A6 的真实组合。首次主链可操作即交付；随后用异质问题和 current Codex 检查严格方向质量。
用户确认方向后，Slice2 执行完整四路因果消融、跨工程 A4、hardening 和 full regression；只有发生真实 scope delta 才申请新授权。
Slice3 完成最终 A1—A6 验收。

## Risks and unknowns

- Agent 可能无界探索或过早结束；Application/Broker 以操作、bytes、wall time 和 no-progress 高安全上限失败关闭，但调用次数不能成为裁剪调查或审核质量的理由。
- World Model 与 Source 可能冲突；必须保留各自 revision、provenance、coverage 和 conflict，不得静默选取。
- Reviewer 可能漏判或越权规划工具；它只能返回具体 Finding，补证和重写仍由主工程 Agent 在 Control Plane 内决定。
- 路由实现可能把已返回但格式无效或审核未通过误判为首选路线不可用；必须以独立 availability verdict 作为唯一 fallback 条件，并由可执行
  `V-MODEL-TRANSPARENT-ROUTING-001` 阻断具体身份分支和非法回退。
- Conversation Context 可能把用户陈述、prior Answer 或 Provider hidden memory 误作事实；新 Conversation 泄漏和模糊指代必须在 dispatch 前阻断。
- 针对工程、题面、关键词、符号、类、方法、fixture 或 Oracle 的特判会产生虚假正确答案，属于方向失败。

## Verification and acceptance

当前验证顺序固定为：完整浏览器主链 → 以“开发体验候选”无 Result 立即用户可体验且开发不停 → 同候选异质问题与 actual current Codex
严格比较 → 质量通过后命名为 MVP → 用户 `CONTINUE / REWORK / REDIRECT / REJECT`。第一条体验交付不移动游标、不冒充 MVP 或质量 PASS；
普通失败继续同一开发动作。

严格方向通过要求：重大错误为 0；逐题相对 Codex 无物质退步；总体质量严格超过 Codex；至少一项重要价值来自非 locator 的世界模型认知。
Codex 是强基线，不是真值、Oracle、Reviewer 或裁判。完整四路因果消融、第二工程、hidden、hardening 与 full regression 只在用户
`CONTINUE` 后执行。

当前公开工程的 exact revision、既有披露/预算和配置路线属于 standing scope。runtime 为每个真实 dispatch 自动派生 one-use exact receipt；
真实 scope delta 才需要新授权。具体 Provider/model 仅是 execution profile 和收据中的配置值，不定义产品动作或质量标准；备用路线只接受
`PREFERRED_EXECUTION_PROFILE_UNAVAILABLE`，不能由原始 HTTP/outcome、结构化输出失败或 Reviewer 拒绝直接触发。

## Authorization decision

**ACCEPTED PROPOSAL / PDR-012 PRODUCT-FIRST BUILD ACTIVE。**

当前 Manifest 工作计划是 `V-BROWSER-CHAT-MVP-BUILD-001`，授权产品开发、loopback Web 和 standing scope 内的 Provider dispatch。
只有真实 scope delta、用户明确停止/改向或不可绕过的安全禁止才停止相关工作；Production 始终未授权。

run-101 的 Ark→DeepSeek fallback 正常完成，最新质量偏差由 `FINDING-010-229/230` 定位为 Review focus/uncertainty 收敛与跨 route logical
Turn budget，而不是 Provider 或授权等待。current candidate 在同一 PDR-012 工作计划内修复并以 fresh run-102 继续验证。

run-102 发生在 weekday peak，Ark sealed 429 后 DeepSeek 按 PDR-007 在外调前拒绝；该部分 run 只验证 shared-budget wiring 和 Q4
Conversation isolation，不产生 Review quality verdict。下一完整 run 仍在 standing scope 内使用 fresh off-peak evidence；peak override 另属 exact scope delta。

run-103 已在 fresh off-peak window 完成同一五问：Ark 4 个 sealed 429、DeepSeek 39/39 completed、每题合计均不超过 15；Q2 ACCEPTED、Q4
zero-dispatch Clarification，整体仍 Quality FAIL。最早通用偏差是 focused repair 可抹掉 Reviewer 已选择的 DEFECT/Finding，以及 failure
follow-up 沿用 previous goal并把 caller local reachability 与 transaction/rollback/remote effect unknown 混为一体。current
`@29/@19/@24` 保留 Review semantic anchor并让当前 requirement/failure condition 成为 Primary 与 Reviewer 的显式 rewrite contract；fresh
committed run-104 是下一证据，不需要新人工授权。

run-104 已在该 committed candidate 上执行：Q1 的 Ark 1 + DeepSeek 14 命中 exact 15-call fuse，Q2 的 Ark 429 后 DeepSeek 首个 dispatch
返回 sealed HTTP 402，Q4 仍为零 dispatch Clarification；同签名停止边界下 Q3/Q5 未发送，本次不形成完整五问质量 verdict。Q1 证明
comprehensive redaction 丢失可信 Boundary presence 并诱发 add/delete Review 振荡。current `@30/@20/@24` 只新增 trusted Package/Draft
Boundary counts 作为 presence-only metadata，exact binding/materiality 与 reference add/remove 仍由 focused Review 独占。402 不改变产品
契约或 standing authority；模型协议 `37/37`、相邻定向测试 `137/137` PASS。本地开发继续，下一 live run 只等待 materially new Provider
availability evidence，不重复请求人工授权。

run-105 按用户明确要求执行 Ark-first recheck：Q1 的唯一 Ark dispatch 仍返回 sealed 429，DeepSeek 在周一 16:02 CST peak window 于
credential/TLS/HTTP 前 `DENIED_PEAK_WINDOW`；Q4 为 zero-dispatch Clarification，Q2/Q3/Q5 按同签名停止边界未发送。该 run 只验证当前
Provider availability 与 route/admission 行为，不产生 `@30/@20/@24` 质量 verdict或代码变化。新的同签名 Ark 外调等待 materially new
availability evidence；standing authority 继续有效且不重复请求人工授权。

用户随后明确报告 Ark 流量问题已经处理，因而 run-106 具备新的 availability trigger；完成 run-105 证据提交并恢复 clean product identity 后
直接执行原五问，无需新授权且不改变任何 scope/budget/route contract。

run-106 已完成该 trigger：Ark 连续 6 个 call completed，第 6 个 Primary output 的顶层 JSON closure 缺失被准确分类为
`STRUCTURED_OUTPUT_INVALID / JSON_SYNTAX_ERROR`；第 7 个 fresh same-profile repair 在 HTTP dispatch 后密封
`REMOTE_DISCONNECTED / PROVIDER_OUTCOME_UNKNOWN`，按 current contract 无 retry、无 DeepSeek fallback。Q4 fresh Conversation
继续 zero-dispatch Clarification，Q2/Q3/Q5 未在同 Session 的 unknown 后发送。该证据不要求修改现有 schema/repair/route；下一 clean
run-107 先执行未重复的 Q2/Q3/Q4/Q5，并在没有重复 stop signature 时补 Q1。

run-107 已取得新的 client-rejection evidence：Q2 为 Ark pre-HTTP TLS unavailable，Q3/Q5 均为 Ark HTTP 400
`InvalidParameter / BadRequest`，Q4 zero-dispatch Clarification；DeepSeek 在周一 peak first preflight 保持零网络。400 不授权 fallback，
但现有安全证据未保留 Provider 可选 parameter-name。`FINDING-010-236` 的 bounded system-contract repair 仅扩展清洗/持久化/回放与 Ark
Conformance oracle，不改变 request bytes、error message 丢弃、availability 或 route。fresh Conformance 后以 run-108 Q5 验证。

fresh Conformance/differential 已由 `FINDING-010-237` 定位：current `thinking` field 被 resolved model 拒绝，而最小 request 的 actual
fingerprint 是 `glm-5.3`，不是冻结的 `glm-5.2`。临时 variant 全部恢复；该 material model delta 超出 current standing profile，故 run-108
不创建。只有 Provider 恢复 exact `glm-5.2` 或用户批准 `glm-5.3` 并完成新的 request contract/Conformance/Capability qualification，才恢复
产品外调。

用户随后以
`local-user-message-utf8:sha256:d27184be5bb47c2526e275232aac3c2b2091e3405310b4d4239b98af2edf1cfd`
明确批准 Ark preferred actual model 更新为 `glm-5.3`，同时重申原数据、预算、loopback evaluation 与非 Production 边界。按
`FINDING-010-238`，requested alias 保持 `glm-5-2-260617`，Adapter `@9` 只删除不兼容的 `thinking` field，并把 Conformance fixture
升级到 `1.9.0`。该 delta 已解除人工授权阻塞；run-108 仍须等待新 exact implementation 的目标测试、门禁和 fresh Ark Conformance PASS，
不能复用 `glm-5.2/@8` 资格。

`FINDING-010-240` 的 clean successor 已用默认 512-token canary 取得 Ark `glm-5.3/@9` Conformance 2/2 PASS，result digest
`sha256:5cc4d3662573c06dd1ad174121c4c9a9565ae4743805d51b120ea502415a2363`，valid until
`2026-09-30T11:10:37.983023Z`。run-108 的 Provider qualification 前置条件现已满足；下一步是 fresh pricing/session preparation 与 Browser Q5。

`FINDING-010-241 / run-108` 随后以 exact product/session 执行 Q5。Ark `@9` request 已完成 TLS、credential 和 HTTP dispatch，证明旧
`thinking` HTTP 400 不再是最早偏差；远端在 response 完成前断开，model call 密封为 `OUTCOME_UNKNOWN / PROVIDER_OUTCOME_UNKNOWN`。
unknown 不满足 trusted unavailable，故没有 retry，也没有激活已准备为 off-peak allowed 的 DeepSeek。Q4 fresh Conversation 的省略指代
以零 dispatch Clarification 正确关闭。该 partial run 不替代五问质量 verdict；剩余外部题等待 materially new Ark network evidence，Slice
本地开发与证据闭合继续。

用户允许周期性重试后，fresh `@9` Conformance canary 2/2 成功，但 run-109 的新冻结 Q1 仍在 Ark dispatch 后约 `55.996s`
`REMOTE_DISCONNECTED`；run-108 的异质 Q5 是 `56.075s`。`FINDING-010-242` 因而把短探针成功识别为长响应可用性的假阳性，并在相同
Provider/model/endpoint/account、数据、预算和非 Production scope 内采用官方 SSE wire。current Adapter `@10` 只在内部消费
`stream:true + include_usage:true` 后严格重组一个 terminal response，Gateway/Turn 仍为 non-streaming，no-retry/fallback 边界不变。旧 `@9`
资格失效。clean `e95fa929… / 95431f1c…` 已通过目标/文档/计划门禁；fresh `ccrun_b222fc9abdf641469baae1cec7080f5d`
Conformance `1.10.0` 又以 actual `glm-5.3`、Usage 完整、retry/unknown 0 取得 2/2 PASS。下一动作是 fresh pricing/exact Session 和
run-110 长产品验证。

`FINDING-010-243 / run-110` 进一步证明 SSE 网络修复有效但 parser profile 仍过窄：第一个 Ark call 在约 `80.333s` completed，第二个在约
`102.925s` 后被本地 `PROVIDER_RESPONSE_INVALID` 拒绝；transport TLS/credential/HTTP `2/2/2`、unknown 0，故不是网络不可用且不触发
DeepSeek。raw SSE 未持久化，具体 frame 保持未知；代码却确定会拒绝 SSE 标准允许的 comment keep-alive。current `@11 / 1.11.0`
candidate 只丢弃 comment/重复空分隔，其他控制字段与既有 terminal validation 继续失败关闭。fresh qualification 与 run-111 differential
通过前，不把 comment 假设写成已确认根因，也不产生质量/MVP verdict。

clean `8d7927f… / fffe078…` 的 fresh `ccrun_e837a716a9e243c29c4affc4fcd113a0` 已令 `@11 / 1.11.0` 取得 13/13 case
PASS：actual `glm-5.3`、Usage 完整、TLS/credential/HTTP `2/2/2`、retry/unknown 0。机器资格现已恢复；下一动作是 fresh pricing/exact
run-111 Session 和长产品 differential，仍不提前确认 comment 假设或质量/MVP。

run-111 已在同一长问题上将 parser 分歧推进到生成预算层：前两次 Ark call 均完成 SSE 重组，第二次精确触及 `8192` output token、
finish `length`，正文 JSON 中途截断；第三次 format repair 被笼统归为 `PROVIDER_RESPONSE_INVALID`。transport `3/3/3`、unknown/retry 0，
DeepSeek 0，因此不是网络重试或 fallback 条件。`FINDING-010-244` 的 `@12 / 1.12.0` candidate 固定 `reasoning_effort=low`，并让合法 terminal
的 empty/截断 string content 形成带 Usage 的 structured-output rejection。它不扩大现有预算；fresh live Conformance PASS 前不得进入 run-112。

clean `2506dec… / f8a9d37…` 的 fresh `ccrun_74a415e279f24556a605f6213a26b41e` 已令 `@12 / 1.12.0` 取得 13/13 case PASS：
actual `glm-5.3`、input/output `323/71`、TLS/credential/HTTP `2/2/2`、retry/unknown 0。exact Coding Plan endpoint 已接受 low-effort field；
下一动作是 fresh pricing/exact run-112 长产品 differential，仍不提前产生质量/MVP verdict。

run-112 已令前四个 Ark calls 以 low-effort 正常完成并推进到两次 Source read；第五个在 HTTP 前 `TLS_FAILURE`，随后 trusted fallback 的
DeepSeek call 明确得到 HTTP 402。unknown/retry 均 0，故 `FINDING-010-245` 保留 `@12` repair，并允许在 bounded delay 后以 fresh run-113
重试 Ark；402 只作为 definite fallback rejection 记录，不改变 schedule 或 route contract。

run-113 的 Ark 7 个 attempts 已全部完成 TLS、credential 和 HTTP，证明周期性网络重试取得 materially new availability evidence；DeepSeek
与 retry 均为 0。第一份可用 Draft 的语义选择正确，但 Provider 抄写一个长 opaque Citation ref 时发生单字符漂移，两个 bounded repairs
未收敛。`FINDING-010-246` 因而把 Provider-facing citation proposal 改为 1-based Observation/Citation ordinals，由 trusted Application
解析为 exact Domain refs；不改变 Citation authority、Provider route、预算或 Production。该通用 candidate 通过目标/文档/计划门禁与 clean
commit 后，以 fresh qualification 和 run-114 复验同一 Q4。

clean `912712c… / e40ba2f…` 的 fresh Ark qualification 13/13 PASS 后，run-114 preparation-only、run-115 Ark pre-dispatch unavailable →
DeepSeek definite HTTP 402 与 run-116 fresh Ark success 依次封存；run-116 的 9 个 Ark calls 全部 completed，页面形成
`SUCCEEDED / ACCEPTED`、3 Citation、fresh Review 与 Delivery。周期重试只创建 fresh logical request，仍未重放单个 request 或
post-dispatch unknown。

run-120 以 fresh Ark qualification、7-call `SUCCEEDED / ACCEPTED` 和 DeepSeek/retry/unknown 0 证明网络正常且 direct declaration Citation
修复 live 生效。`FINDING-010-250` 的 independent audit 仍发现答案把 Controller 中存在的 import/delete HTTP mappings 误报为“检索截断、
未确认”，即使同一次 Search 的 exact Controller read 仍可执行；两个 Reviewer 再次漏判。current protocol 升为
`@35 / Primary @34 / Review @24 / preflight @29`，在 Primary decode 禁止非检索诊断问题以 stale resolved-acquisition Boundary 代替
same-Search exact read，并在 Review decode 机械限制其 material classification；clean gate 后以 fresh run-121 同题和异质冻结题复验，route、
budget、standing authority 与 Production hold 不变。

clean `3326fdf… / d3c5385…` 与 fresh Ark qualification 已闭合该 gate。run-121 的 Ark pre-HTTP TLS unavailable 合法激活 DeepSeek，fallback
definite HTTP 402；用户允许的 bounded-delay fresh run-122 随后由 Ark 12 calls 全部 completed 并交付 `SUCCEEDED / ACCEPTED`。然而
`FINDING-010-251` 的 independent audit 发现 3 个 Claim 与零 Boundary ID 没有覆盖完整用户可见正文，DAO return shape、Repository/Template
classification 和 conversion/remote-effect Unknown 绕过了两个 Reviewer。current protocol 升为
`@36 / Primary @34 / Review @25 / preflight @30 / Review output @10`，要求 exact ordered Draft content-unit assessments 并在 Delivery 前
闭合 Claim/Boundary/Finding。目标/相邻测试、文档/计划门禁、clean commit 与 fresh Ark qualification 后，以 run-123 同题复验；route、预算、
standing authority、no-replay 与 Production hold 不变。

clean `71033a5… / 5357729…`、fresh Ark qualification 与 run-123 已验证 content-unit enumeration：Ark 10 calls 全部 completed，26/26 units
均被审核，第一次 Review 还触发了两处 rewrite。但 final Draft 仍把 ``src/main/resources``、``CommonResult.failed()`` 等 exact inline-code
anchors 映射到不包含这些锚点或只表达相反 uncertainty 的 Claim/Boundary。`FINDING-010-252` 将 current protocol 升为
`@37 / Primary @34 / Review @26 / preflight @31 / Review output @10`，由 Application 在 decode、seal 与 Delivery 重算 exact-anchor 必要条件；
门禁和 clean commit 后以 fresh run-124 复验，不扩大 route、预算、standing authority 或 Production 范围。

clean `8130a12… / da62753…`、fresh Ark qualification 与 run-124 证明 exact-anchor gate 会失败关闭：Ark 8 calls 全部 completed，
DeepSeek/retry/unknown 0，页面没有 Review/Delivery。initial Reviewer 同时漏掉 3 个 mapped anchors，并把含 6 个技术 anchors 的事实段标为
`NON_ASSERTIVE`；第一层 repair 只修一项，同属 `CLOSED_OUTPUT_CONTRACT` 的不同 diagnostic 又被 coarse category gate 提前终止。
`FINDING-010-253` 将 current protocol 升为 `@38 / Primary @34 / Review @27 / preflight @32 / Review output @10`，聚合全部 anchor violations、
关闭 nonstructural `NON_ASSERTIVE` 逃逸，并仅在 output 与 exact diagnostic 有进展时使用第二层 repair；门禁后以 fresh run-125 复验。

clean `6a3c04d… / 1e8c974…`、fresh Ark actual `glm-5.3` qualification 与 run-125 已闭合该同题验证：Ark 13 calls 全部 completed，
DeepSeek/retry/unknown 0，页面 `SUCCEEDED / ACCEPTED`，4 个 Citation、18/18 content units、fresh Review 与 Delivery 均存在。聚合 diagnostic
与 progress-sensitive bounded repair 真实推动了多项 Review/Primary closure，独立 exact-revision 源码审核未见物质错误。proposal 仍不把单题
成功当作 Quality/MVP PASS；下一步在相同 route、预算、standing authority 与非 Production 边界内执行至少两个异质冻结题和 current Codex 对照。
