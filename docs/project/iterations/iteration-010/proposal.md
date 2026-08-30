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
current_execution_finding_refs: [FINDING-010-132, FINDING-010-133, FINDING-010-134, FINDING-010-135, FINDING-010-136, FINDING-010-137, FINDING-010-138, FINDING-010-140, FINDING-010-141, FINDING-010-153, FINDING-010-161, FINDING-010-162, FINDING-010-163, FINDING-010-164, FINDING-010-165, FINDING-010-180, FINDING-010-204, FINDING-010-205, FINDING-010-206, FINDING-010-207, FINDING-010-208, FINDING-010-209, FINDING-010-210]
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
