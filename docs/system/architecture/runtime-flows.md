---
id: SYS-ARCH-FLOWS
kind: system-architecture
status: current
authority: normative
owners: [architecture, application]
depends_on: [SYS-ARCH-COMPONENTS, SYS-ARCH-INVARIANTS, SYS-ADR-015, SYS-ADR-016, SYS-ADR-017, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING]
derived_from: [FINDING-008-024, FINDING-008-036, FINDING-010-092, FINDING-010-139]
code: [src/software_world_model/application_services, src/software_world_model/interface]
tests: [tests/test_knowledge_update.py, tests/test_knowledge_use.py, tests/test_agentic_runtime.py]
---

# 运行主流程

## 来源配置

Application 校验管理命令，经 Source Integration 创建稳定 Data Source 和 Binding；Scope Assertion 只证明本次精确修订的生命周期资格。配置成功不证明来源可达、存在 Artifact 或已有知识。

## 知识更新

```text
Build Objective
  + optional Requirement Revision / Gap binding
  → Canonical Build Target
  → authorized bounded source investigation
  → Artifact / Evidence
  → Candidate bundle
  → independent Admission
  → application acceptance
  → atomic Snapshot publication
```

首次、手动、计划和来源事件更新使用自己的 Build Objective，不伪造 Requirement Binding；只有显式任务驱动更新才可以绑定某个 Requirement Revision / Gap。更新不以提问为触发条件。每一步产生自己的权威结果；Proposal、Admission ACCEPT、Application PASS 和 PUBLISHED 不能互相替代，发布失败保持旧 CURRENT。

## 世界模型问答

```text
Explicit WORLD_MODEL request
  → isolated Plan proposal: immutable Requirement + feature terms + generic Query Plan
  → resolve CURRENT once or accept exact Snapshot ID / ordered Read Set
  → verify no-payload exact Snapshot Read Bundle
  → open exact Read Session / Set
  → validate generic Query Plan
  → seal profile-matched Structure/Behavior/Implementation Query Result + Coverage + Support refs
  → assess every Need / Joint Constraint
  → isolated Draft from the sealed Query Result
  → isolated Review from the original question + sealed inputs
  → deterministic Authorization + Delivery, or fail-closed/explicit Knowledge Gap
```

整个请求关闭 Source Provider 与 Knowledge Update Port。答案进程只挂载产品 package 与无 Evidence payload 的 exact Snapshot Read Bundle，不挂载权威数据库、Evidence Store 或来源工作树。答案生成和审核只能读取固定 Snapshot 的查询/View 结果；知识不足不回源、不更新、不伪装满足。新 Snapshot 只影响之后打开的 Session。引用正文由密封结果后的独立 Citation Projector 进程从另一存储投影到浏览器，不能回传答案链。

### Java Source Semantics 有界调查

`JAVA_SOURCE_SEMANTICS@1` 不再要求先唯一选择一个方法。取得新资格的 Strategy 执行：

```text
immutable Requirement
  → first semantic evidence obligations + candidate terms
  → Application-frozen obligation ledger
  → 2—4 次 constrained proposal / compiled typed operation / typed result
  → sealed trace + progress/budget receipts
  → one Draft
  → independent Review
  → Authorization / Delivery
```

首轮 Agent 只用注册 operation/relation vocabulary 提出 bounded evidence obligations 与 search terms；Application 对其归一、去重、
收敛依赖并冻结。candidate discovery 已是强制首 transition，因此 raw `implementation_candidates` evidence alias 被保守向上归一为
`method_implementations`，不能在非零候选后单独关闭 ledger。由于 method Result 已携带 exact supported outgoing `CALLS`，standalone
raw `direct_neighborhood(OUTGOING_CALLS)` 也收敛为 method evidence；path 组合、incoming 与 both directions 保持图义务。每个后续状态由 Application 从 ledger 和 sealed input 推导受限 operation allowlist，再编译 exact Snapshot、前序 Result
binding、Entity Ref、direction/predicate 与 bounds，并校验 obligation、bytes、Support、progress 和剩余预算后执行。模型固定 envelope
中的越权 operation 或过早 FINISH 不改变平台 transition。候选搜索可以返回 0/N；方法
实现查询可在同一 candidate result 内选择最多 3 个 exact method Ref，不取排名第一也不无界展开。至少一个 Result 执行后可以显式
FINISH，但只有 ledger 已关闭或没有合法 evidence-reducing transition 时才获得终态权力；FINISH 本身计作调用，所以零候选、截断
candidate 或其他没有合法 evidence-reducing transition 的 Result 可在 1 query + FINISH 后形成对应 Gap/Limitation。重复 query、无进展、越界或预算耗尽返回具体
Limitation，并保持 Source/Update/Direct fallback 为 0。查询、表示与业务发现三层完整性只由平台通过 progress receipt 投影；没有
同时证明时不得给 bounded absence，评测 Oracle identity 不进入 Answer。

该 Profile 每题实际模型调用为 4—6（调查 2—4、Draft 1、Review 1），不重试。Gateway connection policy 是资格身份，不能从调用
上限推导 descriptor 数。当前 DeepSeek bounded route 使用 `PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@2`：supervisor 预建恰好 3 个
exact connected descriptor 候选；Gateway 在读取 credential 或发送 HTTP 前最多顺序尝试 3 次 verified TLS，并在同一授权 run 内复用
成功 session 承载仍然彼此独立的 stateless request。每条 session 最多 20 次 HTTP dispatch；达到上限或服务端在完整响应后明确关闭
时，下一 logical request 必须在读取 credential 前消费剩余 descriptor。40-call Capability qualification 正常使用 2 条 session 并
保留第 3 次 acquisition 余量；正式产品单题 4—6 calls 通常只使用第一条。任何 HTTP bytes 可能已发送后的失败都立即
`OUTCOME_UNKNOWN` 且不重发。terminal 后关闭未使用 descriptor，审计分别闭合 TLS attempts、successes、reuse、Provider calls、
per-session dispatch bound 与 `provisioned = attempts + unused_closed`。旧 `@1`、旧固定三调用资格、旧一请求一连接资格和 connection
receipt 均不得复用；其他已接受 Profile 保持各自已资格的调用与连接协议。

若候选配置声明多个 Provider，Application 必须在 Session 开始和任何问题 dispatch 前冻结有序 route，以及每条 route 的 current exact
Conformance、同 Strategy/Configuration Capability Qualification、隔离 transport、credential reference 和 disclosure scope。当前
Engineering QA 顺序为 Ark → DeepSeek；不能因 Ark 实现缺口直接跳过 primary。

planned DeepSeek route 还必须执行下列 admission flow：

```text
freeze exact run / route / quality budget
  → verify trusted clock + current official schedule record
  → seal DEEPSEEK_DISPATCH_ADMISSION@1 for an allowed window or exact one-time peak override
  → before every new DeepSeek request, revalidate window / override
  → only then allow socket/connected descriptor provisioning, TLS, credential resolution and HTTP
  → otherwise fail before external network with DeepSeek dispatch = 0
```

完整最坏质量链必须在开始前可安排进允许窗口；窗口结束后不得再创建 DeepSeek request。已经发出的单个 request 继续按零重试和结果未知
规则密封，但未完成 Evidence/Answer/Review 的 interaction 失败关闭，不交付降质答案。调度阻断只阻断 DeepSeek 外部分派，不停止 Ark-only
或本地开发。当前 runtime 已在 Gateway preflight/invoke 与 Artifact Session `@3` 实现该 flow，并由本地 Case PASS；已有 Provider 资格仍
不能替代每次 planned run 的 exact admission receipt。

一次用户提交只产生一个 logical interaction unit；Engineering Conversation 中该单位是密封 Turn，兼容单轮协议中是 logical question。
Ark primary attempt 使用自己的完整问答链和审计；只有该 attempt 密封 terminal、没有
authorized answer，且原因为 Provider unavailable/HTTP error/outcome unknown/output invalid 或 model Review rejected，才创建一次
DeepSeek fallback attempt。后者从 immutable original interaction input、Chat 时 exact relevant Application-sealed Conversation Context，
以及同一 exact Cognition Context 重新运行完整链，不能读取或拼接 Ark Ledger/Package/Draft/Review。Application、Source 或 Security
failure 不 fallback；每个 Provider 内 retry 为 0。迟到 Ark 结果进入 quarantine 且不能覆盖。用户不选择 Provider、不重提问题、不新建
Session；页面和 Result 按 logical interaction unit 汇总，并保留两个 attempt 的
独立身份、调用、Usage、成本、失败分类与 outcome-unknown 重复计费风险。当前 route 与 schedule admission 已本地闭合，运行状态为
`ROUTING_LOCAL_PASS / DEEPSEEK_SCHEDULE_ADMISSION_LOCAL_PASS / EXACT_SESSION_AUTHORITY_REQUIRED / NOT_LIVE`；这与各 Provider 已取得的
Conformance 资格和后继 live receipt 分开。

## 直接源码调查

```text
Original Question
  → immutable Question Checklist
  → authorized read-only source investigation
  → sealed Evidence Packet
  → cited natural Answer Draft
  → independent checklist and grounding Review
  → APPROVED, fixed-packet targeted rewrite, or targeted retrieval
```

生成角色和审核角色都不能访问来源工具。审核发现表达、遗漏或组织问题时，Response Control 把具体 Finding 和同一 Packet Digest 交给生成角色重写，不重新运行调查；审核证明现有包缺少物质性依据时，Application 才执行针对性来源调查并密封新 Packet。未通过、未知或达到安全熔断均不授权用户答案。调用次数限制只能触发失败关闭，不能取消检查项、引用或独立审核。

## 工程 Chat

```text
Explicit Engineering Conversation
  → fixed product / project / exact revision / World Model / tools / Provider route
  → immutable User Turn + sealed relevant Conversation Context + current Agent Work State
  → isolated primary Engineering Agent
  → understand goal and references; form or revise hypotheses, plan and subtasks
  → query exact World Model cognition or propose one registered source operation
  → Application / Source Broker validates; isolated Worker executes read-only exact-revision operation
  → append Proposal / Decision / Observation to Turn Evidence Ledger
  → Agent observes and replans until evidence is sufficient, an honest limitation is reached, or a fuse closes the Turn
  → seal current Question Evidence Package with support/citation and boundary/audit partitions
  → same logical Agent synthesizes a cited conversational Draft
  → fresh independent Reviewer checks current Turn, trusted conversation context, Package and Draft
  → APPROVED Delivery, or specific Finding returned to a new Agent Work State Revision
  → same-package targeted rewrite, or new evidence Attempt through World Model / Broker tools
  → any new evidence creates a new Ledger / Package / Draft and fresh independent Review
```

Conversation 在任何读取和模型调用前固定 exact 工程边界。软件世界模型为主 Agent 提供持久的系统认知，不是手册、地图、聊天记录或
locator 缓存；这些都只是认知的投影。认知缺失、无关或 Coverage 不足是 Ledger/Package 的显式状态，不阻断当前 Turn 在同一授权 exact
revision 中按需驱动只读调查；这不是从 `WORLD_MODEL` 静默切换到 `DIRECT_INVESTIGATION`。

主 Agent 根据每次已密封 Observation 决定下一步并更新 Application-owned Work State，但不直接拥有任何 Tool。Source Broker 把其 Proposal
重新校验、绑定 exact revision/allowlist/remaining fuse 并编译；只有 Retrieval Worker 读取来源。每一步只追加到 Evidence Ledger，已确认
prefix 不可改写。来源内容是不可信 data，不能成为权限或操作指令。

Question Evidence Package 只有一个 seal/identity，但 `support/citation` 仅收可采信条目，`boundary/audit` 必须保留 Gap、Failure、Partial、
Conflict、Unknown、拒绝和资源记录；后者不能支持肯定 Claim。Reviewer 不规划或执行补证，只返回具体 gap；该 gap 由同一逻辑主 Agent 在
新的受信 Work State/Attempt 中处理。正式资格必须预密封 revision/call/operation/bytes/wall-time/no-progress 熔断，answerable 因熔断
未获批准计失败，但熔断不能削减证据、Citation 或独立审核。

至少一个 fresh Reviewer 必须比较 current Turn 目标、用户纠正、Conversation Context、evidence scope 与 Draft scope。配置 placeholder
只证明 key/injection，caller/getter/import 只证明可见关系，上游 local state 只证明局部结果，均不能自动扩张为 runtime value、DTO/
handler behavior 或下游 HTTP mapping。Reviewer Strategy 可以增加隔离 challenge，但固定双 focus 不是长期主流程。

后续 Turn 可以追问、指代、纠正、深入或总结。Application 密封 relevant history 与当前 Work State；先前答案、摘要和 Provider hidden state
不是证据。用户纠正形成新 Conversation Revision，一次 Turn 失败只结束该 Turn，listener 和会话历史继续有效。

已审核包/结论可在 Delivery 后异步提议 Knowledge Update，但必须重走 Evidence、Candidate、Admission 和 Publication，不阻塞当前 Turn。

## 正式知识使用

显式知识查询冻结 Requirement Revision，打开固定 Snapshot 的有效 Read Session，对每个 Need 和 Joint Constraint 建立可重建证明。只有该有效 Session 内的语义不足才形成 Knowledge Gap；访问、执行、Session 或 Schema 失败必须保留为失败或限制。只有全部 Need 满足才可声明 SUFFICIENT。该路径是 `WORLD_MODEL` 的读取基础，但不是 `DIRECT_INVESTIGATION` 的前置门禁。

高质量 Evidence Packet 与已审核答案可以由独立策略在响应完成后提议新的 Knowledge Update，但该更新不是原回答的一部分。Candidate、Admission 和 Publication 仍执行完整正式知识契约，其成功或失败不改变已完成 Direct Investigation 的审核事实。

## 模型资格

Provider Contract Conformance 证明 Adapter 接口成立；Capability Evaluation 证明精确 Strategy 适合业务能力；Product Validation 证明端到端用户价值；显式 Activation 决定可用范围。四者独立且按精确实现、模型、配置和有效期绑定。某一 Provider 的资格不能借给另一 Provider；偏好顺序也不能替代当前资格。
