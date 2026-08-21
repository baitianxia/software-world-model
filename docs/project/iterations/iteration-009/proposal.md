---
id: ITER-009-PROPOSAL
kind: iteration-proposal
status: accepted
authority: project-proposal
owners: [product, project, architecture, engineering, quality]
depends_on: [SYS-PRODUCT-SUCCESS, ROADMAP-M-002, ROADMAP-CANDIDATE-LOCAL-WEB-DIRECTION-PREVIEW-RECOVERY, ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-ACCEPTANCE, ITER-007-RESULT-SLICE-001-STOP-DECISION, ITER-008-INDEX, SYS-ADR-015, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS, SYS-QUALITY-SECURITY, SYS-OPS-LOCAL-BROWSER]
code: []
tests: []
iteration: ITER-009
coding_input: false
---

# ITER-009 Proposal：先验证真实 Web 方向，再夯实证据问答链

## Trigger and evidence

ITER-008 后续开发因用户报告的外部开发工具提示词准入错误无法继续。项目文档和本机产品运行证据中没有该错误的 request、model、
provider 或 dispatch receipt，因此本轮把它归类为开发执行面阻断，而不是已经证明的产品运行时故障，也不尝试混淆、改写或重复提交
被拒文本来规避策略。

可直接复用的产品证据更明确：ITER-008 run-012 已形成正式冻结；同一候选在本机 Web 对“登录流程”给出了自然答案和四个真实
Citation。第二个边界问题已经由 Draft 形成证据不足的 Limitation，但独立 Review 以 `QUERY_INCOMPLETE` 拒绝交付。当前应先验证
“问题理解—有界证据—自然答案或具体限制—独立审核—引用”的用户主线，而不是继续扩大 Prompt、资格套件或正式知识中间对象。

本轮从产品代码提交 `2cd743b2ba74c5a79cd4d38433830786de09e753` 开始。提交
`967e41bcaa25112ea6b18620d0ac8e0aa5a4a42a` 只增加方向体验优先的规划规则；归档提交
`c4ed92ea44383557dd25e6d327569cff13bb6d65` 中的未验收 `1.5.12` 改动不得进入 baseline。

## Product-goal alignment and cumulative delta

- MVP target reference：`SYS-PRODUCT-SUCCESS`。
- Capability path reference and current step：`ROADMAP-M-002 / step-1-java-result-driven-world-model-investigation`；本轮恢复该步骤的
  用户体验验证，不跳到新的知识域。
- Accepted predecessor evidence：`ITER-005-RESULT-ACCEPTANCE` 与 `ITER-006-RESULT-ACCEPTANCE`；ITER-007 的停止裁决和 ITER-008
  代码只作为失败证据与待重新验证的技术资产。
- Current product gap and real-question evidence：supported 流程题已能从 Web 返回可引用答案；证据不足的 boundary 在 Draft/Review
  交付合同处变成内部失败，且当前方向尚未由用户在清晰标注的体验版上确认。
- Accepted capabilities reused：本机 Workspace、问题前更新、Snapshot/Bundle、Source-off、Citation 与 Java declaration/static
  `CALLS`。
- New capabilities integrated into the same answer chain：面向普通用户的真实 Web 方向体验、通用 typed Limitation 交付、审核意见驱动的
  针对性重写，以及方向确认后的跨工程夯实。
- Evaluator/user-owned hidden held-out before/target counts：最终两个未参与实现的真实 Java 工程，4 条 answerable + 2 条 boundary；
  代码冻结后才由用户披露，target 在披露后同基线逐题测量。
- Cross-domain questions combining old and new knowledge：每个 Slice 至少一题在同一答案链组合 ITER-006 已接受的 declaration/`CALLS`
  与本轮的证据组织、审核或 Limitation 交付能力。
- Earliest product-owned Web checkpoint and live ad-hoc questions：`SLICE-001 / V-WEB-001` 是最早真实入口；最终在 `SLICE-003 /`
  `V-ADHOC-001` 接收两条现场问题。
- Minimum direction-preview checkpoint, representative tasks and explicit non-goals：`SLICE-001 / V-PREVIEW-001` 使用一个 supported 多步骤题、
  一个无符号等价改述和一个 boundary；不以此声称泛化、性能、生产可用或正式验收。
- Direction decision owner and allowed outcomes before hardening：用户拥有 `CONTINUE / REDIRECT / REJECT`；没有 Slice Result 中的新
  `CONTINUE` 收据，`SLICE-002` 不得授权。
- End-of-iteration user-visible Web capability：普通用户无需认证即可在本机浏览器提出自然语言 Java 源码问题，获得证据支持的自然答案
  或具体、诚实的限制，并核对真实 Citation；最终验证覆盖两个未见工程。
- Next blocking gap after success：常见 Java 语法、跨类多文件与真实框架工程广度，然后才是第二语言和其他内容类型。
- Stop / redirect conditions：真实 Web 无法在 timebox 内形成新结果；只能靠题目、工程、关键词或符号特判通过；需要 Source、Update、
  Direct fallback、公网监听或取消独立审核；supported 答案重大错误；Citation 不支持结论；boundary 编造或引用无关证据；用户选择
  `REDIRECT` 或 `REJECT`。

## Critical assumptions and falsification plan

| 假设 | 最早证据与反证 | 反证后的动作 |
|---|---|---|
| A1：以 2cd743b 产品代码为基线，可以在不进行广泛重构的条件下快速形成可交互的本机 Web 方向体验 | SLICE-001 的 V-WEB-001 和 V-PREVIEW-001；若半个工程日内不能让普通用户提交新问题并得到答案或诚实限制，或启动必须先扩大架构，则反证 | REDIRECT；保留启动证据，先修最早产品链阻断，不继续扩展内部组件 |
| A2：统一的证据包、自然答案、独立审核和针对性重写协议可以同时交付 supported answer 与 typed Limitation，不需要任何问题或工程特判 | SLICE-001 的 supported、无符号改述、boundary、V-LIMIT-001 与 Review 对照；任一题依赖关键词分支、无关证据或取消审核才可交付即反证 | REJECT 特判方案；若缺口位于可复用 Answer/Review 合同则 REDIRECT 为最小通用修复 |
| A3：在全面工程夯实前，少量真实代表性任务足以让用户判断交互、答案组织、引用和限制表达的产品方向 | SLICE-001 的 V-PREVIEW-001 与用户决策；若用户无法据此判断，或体验必须先完成完整资格、隐藏套件和性能工程才有意义，则反证 | REDIRECT 体验范围与入口；不提前执行后续全面夯实 |
| A4：方向确认后的通用修复能够在第二个未参与实现的工程和互补边界问题上保持正确，而不只修复公开演示问题 | SLICE-002 的 V-CANARY-002、V-NEG-EARLY-002 和 V-XD-002；若新工程暴露题目特判、表示缺口或同类 boundary 仍内部失败，则反证 | REDIRECT 到首次偏差所属的表示、检索、答案或审核层；禁止增加专用规则 |
| A5：保留只读、Source-off、真实 Citation、独立审核、零隐藏重试和失败关闭后，最终答案质量仍能达到成熟源码 Agent 基线且不因调用次数目标受损 | SLICE-002 用 V-COMP-EARLY-002 和 V-SEC-002 尽早验证，SLICE-003 用最终 4+2、V-COMP-001、V-SEC-003 和现场题裁决；重大错误、实质遗漏、安全边界失守或价值阈值未达即反证 | REDIRECT 或 REJECT；不得用减少模型调用、弱化审核或 Direct fallback 换取通过 |

第一段优先验证 A1—A3，并以跨域体验和安全 Case 防止 A4/A5 的明显反证被推迟；隐藏 canary、成熟方案对照和逐层诊断明确留到
方向 `CONTINUE` 后的第二段。第二段复核 A1—A4 并正式验证通用化；最终段
覆盖 A1—A5。成熟源码 Agent 对照继续使用已冻结 protocol、rubric、cache policy 和正向价值指标：在 12 题复用周期内，每个正确
结果的 Source exposure bytes ratio 必须不高于 250000 ppm，同时重大错误为 0、逐 Need/Claim 不退步。用户消息
`codex-user-message:sha256:6ca47f7daa8bff61fa53e99d1c19b16098207d45fbf210427c3af19e5c9999ed` 冻结该沿用口径。

## Outcome and users

首要用户是希望直接通过浏览器理解工程行为、但不愿先配置认证或学习内部代号的普通开发者。用户只输入自然语言问题；系统从问题前
构建、精确版本的授权知识中检索证据，组织自然答案或具体限制，由独立 Reviewer 检查遗漏、错误推断和引用覆盖，再向用户展示答案与
Citation。

本轮先交付带有“方向体验 / 非验收 / 非生产”标识的 loopback 页面。知识沉淀、复杂正式知识对象和完整产品加固不再阻塞方向判断；
但只读、Secret 隔离、授权、Citation、独立审核、零隐藏重试和失败关闭不能延后。

## Scope / non-goals

本轮范围固定为本机 `127.0.0.1`、无需用户认证的 Java 源码问答体验，复用已有 Workspace、Snapshot/Bundle、bounded investigation、
Draft/Review、Citation 和 Web surface。`SLICE-001` 只实现方向体验所需的最小通用 Answer/Review/Limitation 交付，以及 Reviewer 指出
具体缺口后同一 evidence package 上至多一次的针对性重写；`SLICE-002` 再统一夯实这些合同、跨工程回归和必要资格；`SLICE-003`
只做正式隐藏评测、现场问题和验收收口。

本轮不包括公网部署、Production Activation、认证、团队权限、多工程管理界面、第二语言、README/配置/部署/运行观测问答、通用自治
Agent、长期 Memory 或知识图谱重建。当前归档 `1.5.12` 资产不得整包移植；只有在 `SLICE-002` 中由 Finding 证明必要且通用的最小变化
才能重新实现或选择性吸收。

## Adopted system IDs

- `SYS-PRODUCT-SUCCESS`
- `SYS-ADR-015`
- `SYS-CONTRACT-AI-CAPABILITY-EVALUATION`
- `SYS-CONTRACT-AI-MODEL-GATEWAY`
- `SYS-CONTRACT-APPLICATION-AGENTIC-TASK`
- `SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY`
- `SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE`
- `SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE`
- `SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING`
- `SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS`
- `SYS-OPS-LOCAL-BROWSER`
- `SYS-QUALITY-SECURITY`

`SLICE-001` 服从这些现行 ID，不静默重定义系统。若方向 `CONTINUE` 后证据要求把知识沉淀移出聊天关键路径或改变 Answer/Review Owner，
`SLICE-002` 必须先记录 Finding，并在同一变更中更新 owning System Contract 和必要 ADR。

## Development slices and dependencies

1. `SLICE-001`：快速方向体验。先复用现有产品链形成真实 Web，再只修方向体验所必需的通用阻断；执行少量代表性任务和 Reflection。
   用户必须形成新 `CONTINUE / REDIRECT / REJECT`，隐藏 canary 和成熟源码 Agent 对照不阻塞首次方向决定。
2. `SLICE-002`：通用工程夯实。仅在 `SLICE-001` Result 为 `CONTINUE` 且用户再次授权后，统一夯实证据包、typed Limitation、独立审核
   和针对性重写合同，完成跨工程、安全、回归和当前 identity 所需资格；结束后再次 `CONTINUE / REDIRECT / REJECT`。
3. `SLICE-003`：正式验收。仅在 `SLICE-002` Result 为 `CONTINUE` 且用户再次授权后，冻结产品代码，执行最终两个隐藏工程 4+2、成熟
   源码 Agent 对照、两条现场题、成本/时延报告和最终 Reflection；只有 `ACCEPT` 才可形成 Iteration Acceptance。

首次体验前不执行完整隐藏 4+2、全面性能工程、最终资格重复、生产准备或知识域扩张。运行必需的安全和 exact authorization 仍是硬门禁。

## Risks and unknowns

- run-012 的正向答案可用，但 boundary 的首次偏差尚需在新 Slice 的 exact Result 中重新定位；不能只凭错误码修改 Prompt。
- Provider 资格具有 exact identity 和有效期；代码或配置变化后不得继承旧资格，也不能因调用成本减少调查或独立 Review。
- 当前 System Contract 仍以 World Model bounded investigation 为正式模式；若新证据证明主线需要更简化的 Evidence Package，必须通过
  Finding、Contract 和 ADR 正式改动，不能在 Prompt 内私下改变 Owner。
- 外部开发工具的准入错误没有本机 receipt；它不阻塞正常的小任务开发，但若最小正常任务仍被拒，必须记录并切换到受支持的开发执行面，
  不做策略规避。
- 少量公开体验题容易产生过拟合错觉，因此产品逻辑禁止题目、工程、关键词、类名和方法名分支，且后续 hidden 输入必须保持隔离。

## Verification and acceptance

`SLICE-001` 的最早成功定义是普通用户从同一真实 Web 新提交三个代表性任务，看到 supported answer 或具体 Limitation、可打开 Citation，
且 Source/Update/Direct fallback 为 0；页面必须明确标记非验收、非生产。静态回放、CLI、测试或旧 browser result 均不能替代。

`SLICE-002` 必须用通用 fixture 覆盖 answerable、insufficient coverage、bounded negative、review omission 与 targeted rewrite，并在第二个
真实工程、early canary 和成熟源码 Agent 小规模对照上验证无特判。`SLICE-003` 才执行最终两个隐藏工程 4 answerable + 2 boundary、
成熟源码 Agent 逐题对照和两条现场问题。
最终要求重大错误为 0、answerable 全部 supported、boundary 全部正确、逐 Need/Claim 不退步、正向价值阈值 PASS、真实 Citation 支持
结论、Source/Update/Direct fallback 为 0，Production Activation 为 `NOT_EXECUTED`。

任何方向体验 `CONTINUE` 都不是产品 Acceptance；只有 `SLICE-003` 的完整 Result、`V-REFLECT-003: ACCEPT` 和用户的新验收收据才能
接受本轮。

## Authorization decision

**ACCEPTED FOR SLICE-001 DEVELOPMENT ONLY。** 用户消息
`codex-user-message:sha256:6ca47f7daa8bff61fa53e99d1c19b16098207d45fbf210427c3af19e5c9999ed` 要求把当前环境准备到
ITER-009 可进入开发，因此接受本 Proposal/Readiness 并授权 `SLICE-001` 编码。该消息不授权 Provider/Web/live dispatch、credential
访问、隐藏输入披露、`SLICE-002`、`SLICE-003` 或 Production Activation。
