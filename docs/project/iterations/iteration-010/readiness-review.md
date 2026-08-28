---
id: ITER-010-READINESS
kind: iteration-readiness
status: accepted
authority: project-authorization
owners: [project, architecture, quality, product]
depends_on: [ITER-010-PROPOSAL, ITER-010-VERIFICATION, ITER-010-PDR-010, FINDING-010-153, ROADMAP-M-002, ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST, ITER-006-RESULT-ACCEPTANCE, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, FINDING-010-002, FINDING-010-093, FINDING-010-094, FINDING-010-107, FINDING-010-108, FINDING-010-109, SYS-ADR-013, SYS-ADR-014, SYS-ADR-015, SYS-ADR-016, SYS-ADR-017, SYS-ADR-018, SYS-CONTRACT-AI-CAPABILITY-EVALUATION, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS, SYS-CONTRACT-KNOWLEDGE-STRUCTURE-MODEL, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-QUALITY-ACCEPTANCE]
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
critical_assumption_catalog_digest: sha256:e3de1f72a131c150e34ad29639002e9b8c84c867d163999bce5201f2b9679da1
coding_input: false
current_execution_decision_ref: ITER-010-PDR-010
current_execution_finding_refs: [FINDING-010-132, FINDING-010-133, FINDING-010-134, FINDING-010-135, FINDING-010-136, FINDING-010-137, FINDING-010-138, FINDING-010-140, FINDING-010-141, FINDING-010-153]
current_scheduling_finding_ref: FINDING-010-139
---

# ITER-010 Readiness Review

Front matter 的 `coding_input: false` 表示本文件本身不是开发设计；当前编码权威来自 Manifest、Current 和
`ITER-010-SLICE-001 coding_input: true`。

## PDR-010 current readiness

Readiness 结论是：**可以直接开发完整体验版**。当前同一长动作允许 Manifest 白名单内的产品代码、主工程 Agent、Evidence/Reviewer、
配置选择的模型路线、公开工程受控源码和 loopback Web。无需 Activation、Freeze、分钟收据、阶段 Result 或相同 standing scope 的再次人工确认。

执行顺序只有四步：

1. 形成版本化软件世界模型认知、主工程 Agent、按 Gap 受控源码、逐 Turn Evidence/Citation、fresh Review、语义多轮与新 Conversation 隔离的完整浏览器主链；
2. 第一条主链可操作后以 `V-CHAT-EXPERIENCE-001` 立即把启动命令、URL、exact candidate、质量状态和限制交给用户；`requires_result=false`、不移动游标；
3. 在同一候选上运行至少三条异质问题（至少两条未参与修复），并以 actual current Codex 独立作答作严格强基线；
4. 比较完成，或证明一次通用修复后同类重大失败仍存在时，才以 `V-MVP-EXPERIENCE-001` 密封 Result、移动到 `V-PREVIEW-002`，由用户决定 `CONTINUE / REWORK / REDIRECT / REJECT`。

方向 Result/receipt 只记录决定且 direction action 自环。`CONTINUE` 只使 hardening、full regression、第二工程、hidden、完整四路因果消融和后续 Slice 具备下一份计划资格；真正解锁仍需新 PDR、明确用户授权和可信父 cutover。PDR-009 的 Freeze-first、多动作
状态机和分钟 timebox 已被 PDR-010 取代；历史记录可从 [decisions](decisions/README.md)、[findings](findings/README.md) 与
[results](results/README.md) 查阅，不是当前执行指令。

## Reviewed exact inputs

已复核当前 Proposal、Manifest、Verification Matrix、活动 Slice、PDR-010、FINDING-010-153，以及现行产品成功标准、ADR-018、Engineering
Conversation、Agentic Task、Evidence Answering、World Model Answering、Model Gateway、Source Artifact、Security 和 Local Browser 合同。
历史 baseline、公开 mall exact revision、既有分层归因/认知资格/备用路线准入/Web Access Result 继续作为证据；它们不冒充新的完整体验或
答案质量 PASS。

当前机器动作 ID `ITER-010-ACTION-USER-PLAN-RECOVERY-001` 只因可信父提交连续性保留，其 PDR-010 语义是
`V-MVP-EXPERIENCE-001 / mvp-experience-development`，不表示仍需计划恢复。

## Product-goal alignment gate

- 最早产物必须是普通用户能真实操作的完整工程 Chat，而不是页面外壳、POM/模块图、单轮问答、比较 runner 或内部证明。
- 软件世界模型提供版本化的软件认知，不只是手册或检索入口；主工程 Agent 负责理解、调查、综合和对话。
- 受控 Source 用于核实、补全或纠正当前问题，不取代问题前世界模型认知，也不能回填为世界模型贡献。
- 答案必须直接解决用户问题并绑定 Citation；代码走读只作为必要证据，不能成为默认表达。
- 方向质量要求重大错误为 0、逐题不输 current Codex、总体严格超过 Codex，并有非 locator 世界模型贡献；该判断紧随首次完整体验，不阻塞首次交付。

## Architecture reflection gate readiness

A1—A6 继续有效：世界模型概念、主工程 Agent 自适应决策、逐 Turn Evidence/Review、跨工程泛化、相对 current Codex 的产品质量与世界模型
贡献、真正语义多轮 Chat 都必须最终被验证。Slice1 验证 A1/A2/A3/A5/A6 的完整组合；用户 `CONTINUE` 后还须新 PDR、明确授权和可信父 cutover，Slice2 才能做完整四路因果消融
和跨工程 A4；Slice3 完成最终复验。安全熔断只失败关闭，不能通过裁剪证据、Citation 或独立审核换取 PASS。

## Outcome, scope and non-goals

当前 Outcome 是无需认证的本机工程 Chat：同一 Conversation 可以追问、纠正、深入和总结；每个 Turn 都有独立 Request、Evidence、Answer、
Review 和 Delivery；新 Conversation 不继承旧 Work State、Evidence 或 Provider memory。

范围限公开 mall exact revision、Java、预构建世界模型认知、受控只读源码/文档/配置/测试和 loopback。首次用户判向前不做跨重启长期
Memory、第二工程、第二语言、跨仓库、公网、Production、多用户、任意 Shell 或源码写入。

## System contracts and unresolved decisions

默认 System Owner 是 `SYS-ADR-018` 与 `SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION`。模型无直接 Repository/FS/Shell/
network/credential/write 权限；Broker/Worker 拥有受控只读执行权；Ledger 只追加；调查后才 seal；seal 不等于真值；Reviewer 只返回
具体 Finding，补证或重写由主工程 Agent 决定并形成新的 Package/Answer/Review identity。

实现细节可以调整，但不得引入工程、题面、关键词、符号、类、方法、fixture 或 Oracle 特判。具体 Provider/model 是 execution profile
和收据中的配置值，不得进入产品动作、分支或质量标准；产品代码只消费通用 route role、profile ref/digest 和 availability verdict。
备用路线的唯一合法入口是 availability boundary 密封的 `PREFERRED_EXECUTION_PROFILE_UNAVAILABLE`。结构化输出无效、Reviewer 拒绝以及
未经该 boundary 分类的原始 HTTP/outcome 都不得触发备用路线。格式修复或审核返工必须在同一 profile 上作为有界的新 call 执行，使用新
request identity/receipt，不属于 transport request retry；仍失败则如实关闭当前 Turn。

## Slice, dependency and risk closure

Slice1 是唯一 active/coding input。普通失败、定向测试失败、内部候选变化和首次可操作浏览器交付不移动计划游标、不生成 Result、不停止开发。答案失败必须先
保存同一 trace，按世界模型构建/投影、Agent 调查/综合、Evidence/Review、Chat/Web 找到最早偏差；只做一次最小通用修复，并复验原失败
与两个异质案例。同一故障仍复现时停止无新证据外调，交付最后可运行版本、根因证据和限制给用户判向。

首次体验前只运行改动相关测试、启动 smoke、安全与失败真实性检查。full regression、hardening、第二工程和 hidden 在用户 `CONTINUE`
前保持锁定。

## Verification readiness

`V-LAYER-ATTRIBUTION-001`、`V-COGNITION-ELIGIBILITY-001`、`V-FALLBACK-ROUTE-ADMISSION-001` 与 `V-ALPHA-ACCESS-001` 的既有
PASS 可作为输入；`V-MODEL-TRANSPARENT-ROUTING-001`、`V-CHAT-EXPERIENCE-001`、`V-MVP-EXPERIENCE-001` 和 `V-PREVIEW-002`
尚未执行。模型透明 Case 是当前动作内的定向可执行阻断项，不创建新动作或改变游标。第一条完整主链的即时体验交付不要求 Result、不移动游标；仅在同候选完成三条异质问题、两条 unseen 与 Codex 比较形成最终 handoff，
或一次通用修复后同类重大失败仍存在需要用户判向时，由轻量 verifier 密封一次 handoff evidence。

当前公开工程、exact revision、既有披露/预算和配置路线属于 standing scope，人工重复授权请求应为 0。每个真实 Turn/dispatch 仍须在
Source disclosure、credential 和 network 前自动派生 one-use exact receipt；真实 scope delta 继续失败关闭并申请最小增量权限。

## Authorization decision

**CURRENT READINESS ACCEPTED / PDR-010 COMPLETE-EXPERIENCE-FIRST / ITERATION AND SLICE1 AUTHORIZED。**

可以直接开始 `V-MVP-EXPERIENCE-001`。当前授权不扩大到 hardening、full regression、第二工程、hidden、非 loopback、Source 写入、
后续 Slice 或 Production；这些边界只有用户 `CONTINUE`、后续新 PDR、明确用户授权和可信父 cutover 共同成立时才能改变。front matter 中的
本地消息 digest 仅是项目记录的内容证据引用，不代表平台认证身份、签名或可自行扩权的授权。
