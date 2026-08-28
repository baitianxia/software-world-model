---
id: ITER-010-PDR-010
kind: project-decision
status: accepted
authority: project-decision
owners: [product, project, architecture, engineering, quality, ai]
depends_on: [ITER-010-RESULT-V-PLAN-RECOVERY-001, FINDING-010-153, SYS-PRODUCT-SUCCESS, SYS-QUALITY-ACCEPTANCE, SYS-ADR-017, SYS-ADR-018, SYS-ADR-019, PROJECT-GOVERNANCE-DEVELOPMENT-DESIGN, PROJECT-GOVERNANCE-PLAN-EXECUTION]
code: [scripts/docs.py, scripts/plan_gate.py, validation/iteration_010_mvp/value_gate/runner.py]
tests: [tests/test_docs_gate.py, tests/test_plan_gate.py, tests/test_iteration_010_mvp_value_gate.py]
iteration: ITER-010
decision: REWORK
rework_strategy: COMPLETE_MVP_EXPERIENCE_FIRST
decision_ref: local-user-message-utf8:sha256:5ced06d2604020248c5baf69421ccbb4e5c047288b6db5b2202675c558c38cf6
authorization_ref: local-user-message-utf8:sha256:6cf2531ab1119b67ad2010040ae1ac73f817785684fccc26111b3b70ef5fcbe5
effective_scope: ITER-010-SLICE-001
coding_input: true
---

# PDR-010：先形成完整可体验版本，再验证和夯实

## Context

ITER-010 已迭代多轮，但计划不断把内部事实、比较基础设施、动作收据和全量验证放在真实体验之前。失败的重型 PDR-010 候选又把计划
Activation 当作开发时钟起点，并把可变 Manifest 的整体摘要作为前置条件，导致开发尚未开始就越过硬停时间且摘要失配。那些机制既没有
证明产品质量，也阻止了用户尽快验证方向。

问题属于计划与治理设计，不属于产品代码。软件世界模型、主工程 Agent、受控源码、证据、独立审核和语义多轮 Chat 的总体架构不变；
需要改变的是开发顺序和门禁粒度。

## Decision

### 1. 当前只有一项产品开发任务

当前 Slice 直接进入“完整 MVP 体验开发”。机器上为保持可信父提交连续性沿用
`ITER-010-ACTION-USER-PLAN-RECOVERY-001` 这一旧 ID；它不再表示恢复或 Activation，用户和开发文档统一称为“完整体验版开发”。

该动作可以跨多个提交持续完成产品实现、定向测试、公开开源 standing scope 内的模型调用和 loopback 浏览器体验。普通失败、测试未通过、
内部候选变化或调用次数不会移动动作、结束开发或要求用户再次授权。第一条完整浏览器主链由
`V-CHAT-EXPERIENCE-001` 表示；它可操作即向用户交付，`requires_result=false`、不移动游标，也不等待 current Codex 比较。动作只在以下两种情况下由 `V-MVP-EXPERIENCE-001` 形成一次 Result 并进入用户方向决定：

- 同一已交付候选已完成至少三条异质问题、至少两条 unseen 与 actual current Codex 比较，形成最终方向 handoff；
- 已完成一次有证据的通用修复和定向复验仍存在同类重大失败，继续外调只会碰答案。

不再设置 Activation Result、Build/Live/Quality/Attribution/Repair/Recheck 多段动作、旋转治理槽或机器分钟收据。

### 2. 可体验 MVP 是完整功能合取

首次交给用户的版本必须在同一 exact candidate 上同时具备：

1. 软件世界模型针对精确版本提供可查询的结构、实现/行为、职责/边界、来源、Coverage、Gap 和 Unknown 认知；POM、模块图、文字手册或
   locator 单独不成立。
2. 主工程 Agent 保持对话目标、指代和纠正，以世界模型认知为起点，按 Gap 受控读取源码、文档、配置或测试，根据观察调整调查，并直接、
   自然地回答用户，而不是默认输出代码走读。
3. 每 Turn 形成只追加调查记录、密封证据包、真实 Citation 和 fresh 独立审核；证据不足时明确 limitation，审核不能代替主 Agent 写答案。
4. 普通用户可通过无认证 loopback 浏览器完成初始问题、追问或纠正、深入或总结；失败只结束当前 Turn，新 Conversation 不继承旧状态。
5. 产品逻辑不包含工程名、题面、关键词、类名、方法名、固定答案或测试夹具特判。

页面能打开、单轮回答、某个内部组件通过或比较 runner 完成都不叫 MVP。首次体验可以明确标记“质量尚在验证”，但不能缺失上述任一主链能力。

### 3. 体验形成后才做方向质量验证

一旦完整浏览器主链可用，立即以 `V-CHAT-EXPERIENCE-001` 交给用户体验，不等待全量回归或完整评测基础设施；该即时交付不生成 Result、
不移动游标。同时在同一候选上用至少三条异质问题做定向自测，其中至少
两条未参与修复，覆盖世界模型已有认知、需要源码补证和应诚实说明边界中的至少两类。

current Codex 是真实强基线，不是 Oracle、Reviewer 或运行时依赖。方向通过仍要求：目标系统无重大事实错误、物质遗漏、无据结论、错误
Citation 或假 Unknown；逐题无物质退步；总体答案质量严格优于 current Codex；并有至少一项可观察的非 locator 世界模型贡献。该严格标准
不降低，但它验证已经可体验的同一候选，不再阻止首次浏览器交付。比较完成后才形成最终 `V-MVP-EXPERIENCE-001` Result；若比较失败，先做一次通用修复和定向复验，仍有同类重大失败才以失败 Result 进入用户判向。

用户方向 Result/receipt 只记录 `CONTINUE / REWORK / REDIRECT / REJECT`，对应 action 保持自环。`CONTINUE` 只使完整四路因果消融、第二工程、hidden、统计复验和 hardening 具备后续规划资格；真正解锁需要新 PDR、明确用户授权与可信父 cutover。本地用户消息 digest 只是内容证据引用，不是平台认证身份、签名或授权。

### 4. 失败按责任层归因，不按题碰答案

重大失败保留同一 trace，按以下顺序找最早偏差，并记录后续失守层：

`源码事实 → 世界模型构建/准入 → Cognition 投影/查询 → 对话理解 → Agent 调查/综合 → Evidence/Review → Chat/Web`。

在能证明责任层前只补可观测性，不修改 Prompt、搜索排序或答案格式。已证明的根因采用最小通用修复，并通过原失败和两个未参与修复的异质
定向案例。相同故障签名经一次通用修复仍复现时停止规则堆叠和无新证据外调，带着最后可运行版本及归因进入用户方向决定。

### 5. 保留有实际价值的机械边界

保留的机器门只有：clean、可回退 Git 基线；活动 Slice 和变更路径；公开 mall exact revision 与只读 Source；Secret 隔离；standing authority
外的 scope delta 失败关闭；候选 Git commit/tree 必须等于 Result 提交的实际可信父节点；内嵌证据原始字节与摘要、逐 dispatch 的 exact
session/config/input/disclosure/budget/Secret Reference receipt 和执行计数互相绑定；hardening、full regression、第二工程、
hidden、Production、非 loopback 和 Source 写入继续锁定。

机器验证器不能把本地记录的浏览器 capture、答案、Citation、Review 或比较分数变成“真实且正确”的证明，因此不得声称机器认证了这些语义判断。
它只验证交付包确实携带原始记录且没有引用不存在的文件，并明确输出 `local capture authenticity=false / semantic answer quality=false` 的信任边界。
真实浏览器、答案质量、独立审核和相对 current Codex 的判断仍是必须完成的产品证据，但必须原样交给用户审阅，最终方向由用户决定。
因此 `V-MVP-EXPERIENCE-001` 的机器 `PASS` 只表示“最终 handoff 包结构完整且绑定正确”，绝不等于“答案质量 PASS”；严格质量状态作为包内
独立比较结论单独展示。质量通过或一次通用修复后仍失败，都可以形成结构完整的 handoff 并进入用户判向。

当前公开 mall、既有执行路线和披露范围已有持续授权。每 Turn/dispatch 的 exact receipt 由系统自动派生，不是新的人工审批。只有私有或
unknown/dirty Source、不同外部接收方或账户、扩大披露/预算、准入策略例外、hidden、后续 Slice、写入或 Production 才重新申请精确差量权限。
模型与 Provider 只属于 execution profile 配置和运行收据；产品计划、Agent 协议和质量标准仍使用透明的 `preferred/fallback` 角色、
profile ref/digest 与 availability verdict。产品代码不得读取具体 Provider/model 身份形成分支。

### 6. 备用路线只处理真实不可用

Provider availability boundary 是“首选执行配置是否不可用”的唯一 Owner。备用路线只有在该 boundary 密封
`PREFERRED_EXECUTION_PROFILE_UNAVAILABLE` 后才能启动；原始 HTTP/outcome 本身、结构化输出无效、Reviewer 拒绝、实现缺口或质量不通过
都不能自行产生该结论。前一次调用已经返回但不满足应用协议，证明的是本次结果不可交付，不是首选执行配置不可用。

结构化输出无效时，Application 可以在同一 execution profile 上进行有界格式修复；Reviewer 拒绝时，主工程 Agent 可以在同一 profile 上
依据 Finding 有界重写并接受 fresh review。每次修复/重写都是新的 call，必须取得新的 request identity 和 one-use receipt；它不是对 outcome
未知请求进行重发的 transport request retry，也不能在耗尽后切换备用路线碰答案。通用安全/no-progress 边界耗尽后，当前 Turn 如实失败关闭。

`V-MODEL-TRANSPARENT-ROUTING-001` 是当前长动作中的可执行 blocking Case：使用可互换的虚拟 profile 身份验证产品行为只取决于 route role、
profile ref/digest 与 availability verdict，并验证结构化输出失败、审核拒绝和缺少 availability verdict 时备用 dispatch 数为 0。该 Case 不新增
动作、授权、Result、Activation 或游标迁移；它通过前禁止实际 fallback dispatch 和最终方向 handoff。修复完成并使完整主链第一次可操作后，
仍须立即交付，不等待比较、full regression 或额外治理。

## Consequences

- PDR-009 的“先四路 Freeze/Quality，后 Web”顺序被取代；其严格质量目标保留为体验后的方向验证。
- 失败分支 `codex/iter-010-rework` 上的重型 PDR-010 和 Activation 只保留为失败证据，不进入当前分支，也不修改其历史 Result。
- 当前计划提交本身不改产品、不调用 Provider；提交后即可在同一动作内持续开发完整体验版本，无需另做 Activation。
- 首次体验前只运行受影响模块的定向测试、启动与安全 smoke；方向确认前不运行 full regression 或 hardening。即使方向为 `CONTINUE`，后续工作也必须等待新 PDR、明确用户授权与可信父 cutover。
- 模型透明与 availability-only fallback 由当前动作内的定向 executable blocking Case 执行，不再依赖文字约束或具体 Provider/model 的产品分支。
- 计划不再用调用次数或时间盒降低答案、证据或独立审核质量。
