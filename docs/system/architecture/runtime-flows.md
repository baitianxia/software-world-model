---
id: SYS-ARCH-FLOWS
kind: system-architecture
status: current
authority: normative
semantic_owner: SYS-ARCH-BASELINE
authority_scope: controlled-architecture-appendix
owners: [architecture, application]
depends_on: [SYS-ARCH-BASELINE, SYS-ARCH-COMPONENTS, SYS-ARCH-INVARIANTS, SYS-ADR-015, SYS-ADR-016, SYS-ADR-017, SYS-ADR-019, SYS-ADR-020, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING]
derived_from: [FINDING-008-024, FINDING-008-036, FINDING-010-029, FINDING-010-092, FINDING-010-139, FINDING-010-140, FINDING-010-156, FINDING-010-198, FINDING-010-199, FINDING-010-219, FINDING-010-236]
code: [src/software_world_model/application_services, src/software_world_model/interface]
tests: [tests/test_knowledge_update.py, tests/test_knowledge_use.py, tests/test_agentic_runtime.py]
---

# 运行主流程

> 本文件是架构基线的运行附录。默认 Engineering Conversation 的主流程以自适应组合为准；严格 `WORLD_MODEL`、`DIRECT_INVESTIGATION` 和兼容问答协议只是显式边界 Profile。本文只定义系统级 Owner、边界和状态转换；语言专用查询词汇、Provider/模型身份、Prompt、字段、HTTP/TLS、预算、收据和准入插件属于相应 Contract 或运行实现，不得反向成为默认架构语义。

## 来源配置

Application 校验管理命令，经 Source Integration 创建稳定 Data Source 和 Binding；Scope Assertion 只证明本次精确修订的生命周期资格。配置成功不证明来源可达、存在 Artifact 或已有知识。

## 知识更新

```text
Build Objective
  + optional Requirement Revision / Gap binding
  → Canonical Build Target
  → authorized bounded source investigation
  → Artifact
  → Knowledge Engine extracts Evidence
  → Candidate bundle
  → independent Admission
  → application acceptance
  → atomic Snapshot publication
```

首次、手动、计划和来源事件更新使用自己的 Build Objective，不伪造 Requirement Binding；显式任务驱动更新可以绑定 Requirement Revision / Gap。
当前回合发现世界模型与精确源码冲突时，Application 产生最小 Knowledge Maintenance Task；该任务异步进入同一 Knowledge Update 契约，
不阻塞当前回答、不修改当前 Snapshot。任务只保留对象、版本、定位、冲突类型、去重键和状态，不保存完整答案或当前回合证据。每一步产生自己的权威结果；
Proposal、Admission ACCEPT、Application PASS 和 PUBLISHED 不能互相替代，发布失败保持旧 CURRENT。

## 世界模型问答

```text
Explicit WORLD_MODEL request
  → isolated Plan proposal: immutable Requirement + feature terms + generic Query Plan
  → resolve CURRENT once or accept exact Snapshot ID / ordered Read Set
  → verify no-payload exact Snapshot Read Bundle
  → open exact Read Session / Set
  → validate generic Query Plan
  → seal profile-matched query result + Coverage + Support refs
  → assess every Need / Joint Constraint
  → isolated Draft from the sealed Query Result
  → isolated Review from the original question + sealed inputs
  → deterministic Authorization + Delivery, or fail-closed/explicit Knowledge Gap
```

这里的 Structure/Behavior/Profile-specific Query Projection 只是某个调查 Profile 的投影示例，不是完整认知维度目录；完整维度以架构基线 §6.9 为准，
具体输入、覆盖与结果由相应 Profile Contract 负责。

整个请求关闭 Source Provider 与 Knowledge Update Port。答案进程只挂载产品 package 与无 Evidence payload 的 exact Snapshot Read Bundle，不挂载权威数据库、Evidence Store 或来源工作树。答案生成和审核只能读取固定 Snapshot 的查询/View 结果；知识不足不回源、不更新、不伪装满足。新 Snapshot 只影响之后打开的 Session。引用正文由密封结果后的独立 Citation Projector 进程从另一存储投影到浏览器，不能回传答案链。

### Java Source Semantics 有界调查

`JAVA_SOURCE_SEMANTICS@1` 不再要求先唯一选择一个方法。该显式 Profile 的稳定运行边界是：调查由模型提出受控证据义务，
由 Application 冻结义务、编译合法查询、校验结果并决定是否继续；它不把模型输出当作权限、查询结果或最终答案。

```text
immutable Requirement
  → first semantic evidence obligations + candidate terms
  → Application-frozen obligation ledger
  → bounded proposal / compiled typed operation / typed result
  → sealed trace + progress/budget receipts
  → one Draft
  → independent Review
  → Authorization / Delivery
```

首轮 Agent 只能使用注册的 operation/relation vocabulary 提出 evidence obligations 与 search terms；Application 负责归一、去重、
依赖收敛、Snapshot/Result 绑定、进度和资源校验，并冻结后续合法 operation。候选发现、方法实现和调用关系的具体 vocabulary、
别名归一规则、结果数量上限以及 FINISH 条件属于该 Profile 的详细 Contract，不在本概要附录重复定义。所有已执行查询必须形成
不可变 trace；没有合法 evidence-reducing transition、发生重复/无进展、越界或资源熔断时，返回具体 Limitation，不转入 Source
或其他模式。查询、表示和业务发现的完整性必须分别得到平台证据，不能从单一分页结束或候选数量推出业务不存在。

该 Profile 必须具备有界调查、零重试、精确执行身份、独立 Draft/Review 和真实资源收据。调用次数、连接复用、descriptor、
TLS、dispatch 和收据字段由 Profile Contract、资格和运行实现分别定义；它们不是本概要架构的部署参数。任何 request bytes 可能
已发送后的失败都必须保持 `OUTCOME_UNKNOWN`，不得重发。

若候选配置声明多个 execution profile，Model Execution Runtime 在自己的内部边界冻结候选顺序和 exact execution-profile ref/digest。Application、
Agent、Conversation、Session Artifact、Response Control 与 Browser 只调用一个 Provider-neutral Model Execution Port，不读取候选、route role、
Provider/model 名称或 availability verdict。Profile 的运行配置内部绑定 current exact Conformance、同 Strategy/Configuration Capability Qualification、
Provider/model/endpoint、Adapter/plugin、隔离 transport、credential reference、disclosure scope、预算和 admission policy。不能因 preferred
execution profile 的实现、输出或质量缺口把它伪装成 terminal unavailable，也不能临时跳过运行时的内部候选规则。

公开来源本机体验先执行下列 authority flow：

```text
one standing human authority
  → verify public upstream + license/provenance + clean exact revision
  → freeze approved model-execution policy / disclosure / budgets / loopback candidate boundary
  → user submits an exact Turn
  → trusted Application derives exact Session / Turn authority; Model Execution Runtime derives private attempts
  → Gateway derives one-use Manifest and disclosure / dispatch receipt for every call
  → terminal audit closes actual payload / Usage / transport / cost
```

这个 flow 中只有第一步和 material delta 是人工决定；Turn/run/dispatch receipt 是受信系统对同一边界的逐次派生，不得成为新的人工等待点。
若 payload 进入 private/unknown/dirty/local data，新 Provider/model/endpoint/credential account，预算扩张，外部写入、非 loopback 或
Production，则停止派生并要求 exact human delta。公开来源仍经 Broker/Worker 只读执行，Source 内容仍按 prompt-injection-capable 的不可信
data 处理。

任何 execution profile 选择 admission plugin 时，Model Execution Runtime 必须执行下列通用 admission flow；该流程不向 Application/Agent 暴露候选：

```text
derive exact run / internal execution policy / quality budget from standing authority or exact human delta
  → execute the frozen admission plugin against its trusted inputs and seal a non-dispatching preparation decision when the plugin uses JIT activation
  → at the route's first real request preflight, re-evaluate every time-sensitive input and seal the active generic dispatch-admission receipt, or bind an exact policy-specific override
  → before every new request on that route, revalidate the plugin verdict / override
  → only then allow socket/connected descriptor provisioning, TLS, credential resolution and HTTP
  → otherwise fail before external network with that internal attempt's dispatch = 0
```

完整最坏质量链必须在 active receipt 激活前满足插件的允许条件；preparation decision 不提前消耗 active duration，也不授权外调。条件失效后
不得再创建该 route 的 request。已经发出的单个 request 继续按零重试和结果未知
规则密封，但未完成 Evidence/Answer/Review 的 interaction 失败关闭，不交付降质答案。准入阻断只阻断该 execution profile 的外部分派，
不停止其他合格 route 或本地开发。已有 Provider 资格不能替代每次 planned run 的 exact dispatch-admission receipt；standing scope 内的
receipt 由可信系统派生，不是逐 run 人工审批。

一次用户提交只产生一个 logical interaction unit；Engineering Conversation 中该单位是密封 Turn，兼容单轮协议中是 logical question。
Model Execution Runtime 为每个内部 attempt 使用独立的完整问答链和审计。只有当前 attempt 密封 terminal、没有 authorized answer，且受信
availability owner 从 exact raw receipts 密封“当前执行配置不可用”裁决，运行时才可以创建一次新的内部 attempt。Raw unavailable/HTTP/outcome
信号只是裁决输入，不能直接开启新 attempt。Output-invalid、Reviewer reject、Capability/qualification、Application、Source、authorization/admission
或 Security failure 均为 non-eligible。格式修复、答案重写、补证后重答和 fresh Review 只能在当前执行配置内以新的 authorized model call 进行；无合法新调用时当前 interaction 失败关闭。
Provider HTTP failure 先由原样委托 qualified Adapter 的 Gateway decorator 只密封受限的 transport/provider evidence，inner terminal 后绑定
call/request/isolation，再经 auxiliary repository、Model Egress、model receipt、Turn 与 attempt 逐层重验。具体 status、error code/type、
字段限制及其 unavailable 映射由 Model Gateway Contract 唯一负责；没有完整 evidence digest 或仅凭字符串相似性都 fail closed。用于定位
Provider 明确指出的 request field 的参数名不得进入 availability、route 或 retry 判定。
新的内部 attempt 从 immutable original interaction input、Chat 时 exact relevant Application-sealed Conversation Context，以及同一 exact Cognition
Context 重新运行完整链，不能读取或拼接先前 attempt 的 Ledger/Package/Draft/Review。迟到结果进入 quarantine 且不能覆盖。用户不选择 Provider、
不重提问题、不新建 Session；页面和 Result 按 logical interaction unit 汇总，只得到通用 execution status、dispatch count 和不透明 audit ref。
Provider/model、availability、transport、成本、失败分类与 outcome-unknown 风险只留在 Model Execution Runtime 的内部审计。

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
  → fixed product / project / exact revision / World Model / tools / preferred/fallback execution profiles / standing authority
  → immutable User Turn + sealed relevant Conversation Context + current Agent Work State
  → isolated primary Engineering Agent
  → understand goal and references; form or revise hypotheses, plan and subtasks
  → query exact World Model cognition or propose one registered source operation
  → Application / Source Broker validates; isolated Worker executes read-only exact-revision operation
  → append Proposal / Decision / Observation to Turn Evidence Ledger
  → Agent observes and replans until evidence is sufficient, an honest limitation is reached, or a fuse closes the Turn
  → seal current Question Evidence Package with support/citation and boundary/audit partitions
  → same logical Agent synthesizes a cited conversational Draft
  → fresh independent Reviewer checks current Turn, trusted conversation context, Package and Draft; may issue bounded read-only verification reads via Broker (kept out of the Package); returns only verdict/Finding, never a second answer
  → APPROVED Delivery, or specific Finding returned to a new Agent Work State Revision
  → same-package targeted rewrite, or new evidence Attempt through World Model / Broker tools (routed by Application from a concrete gap)
  → any new evidence creates a new Ledger / Package / Draft and fresh independent Review
  → terminal Turn: Ledger / Package / Draft / Review become a non-authoritative Turn Trace under retention policy (V1.4)
```

Conversation 在任何读取和模型调用前固定 exact 工程边界。软件世界模型为主 Agent 提供持久的系统认知，不是手册、地图、聊天记录或
locator 缓存；这些都只是认知的投影。认知缺失、无关或 Coverage 不足是 Ledger/Package 的显式状态，不阻断当前 Turn 在同一授权 exact
revision 中按需驱动只读调查；这不是从 `WORLD_MODEL` 静默切换到 `DIRECT_INVESTIGATION`。

主 Agent 根据每次已密封 Observation 决定下一步并更新 Application-owned Work State，但不直接拥有任何 Tool。V1.4 起 Broker 提供的只读工具目录须满足基线 7.7 节的工具对等要求，read candidate 不再是读取前置条件。Source Broker 把其 Proposal
重新校验、绑定 exact revision/allowlist/remaining fuse 并编译；只有 Retrieval Worker 读取来源。每一步只追加到 Evidence Ledger，已确认
prefix 不可改写。来源内容是不可信 data，不能成为权限或操作指令。

Question Evidence Package 只有一个 seal/identity，但 `support/citation` 仅收可采信条目，`boundary/audit` 必须保留 Gap、Failure、Partial、
Conflict、Unknown、拒绝和资源记录；后者不能支持肯定 Claim。Reviewer 不规划或执行补证，只返回具体 gap；它可以做有界只读核验读取以发现误引和包外物质遗漏，核验观察不进入 Package（V1.4）；该 gap 由同一逻辑主 Agent 在
新的受信 Work State/Attempt 中处理。正式资格必须预密封 revision/token/bytes/wall-time/no-progress 熔断（调用次数只作安全兜底）；熔断后主 Agent 基于已有证据形成带限制的 Draft 并照常审核，
评测中 answerable 因熔断未获批准计失败，但熔断不能削减证据、Citation 或独立审核（V1.4）。

至少一个 fresh Reviewer 必须比较 current Turn 目标、用户纠正、Conversation Context、evidence scope 与 Draft scope。配置 placeholder
只证明 key/injection，caller/getter/import 只证明可见关系，上游 local state 只证明局部结果，均不能自动扩张为 runtime value、DTO/
handler behavior 或下游 HTTP mapping。Reviewer Strategy 可以增加隔离 challenge，但固定双 focus 不是长期主流程。

后续 Turn 可以追问、指代、纠正、深入或总结。Application 密封 relevant history 与当前 Work State；先前答案、摘要和 Provider hidden state
不是证据。用户纠正形成新 Conversation Revision，一次 Turn 失败只结束该 Turn，listener 和会话历史继续有效。

已审核包/结论可在 Delivery 后异步提议 Knowledge Update，但必须重走 Evidence、Candidate、Admission 和 Publication，不阻塞当前 Turn。V1.4 起该提议从 Turn Trace 形成 Crystallization Proposal（基线 8.5 节），Trace 正文不作为正式 Evidence。

## 正式知识使用

显式知识查询冻结 Requirement Revision，打开固定 Snapshot 的有效 Read Session，对每个 Need 和 Joint Constraint 建立可重建证明。只有该有效 Session 内的语义不足才形成 Knowledge Gap；访问、执行、Session 或 Schema 失败必须保留为失败或限制。只有全部 Need 满足才可声明 SUFFICIENT。该路径是 `WORLD_MODEL` 的读取基础，但不是 `DIRECT_INVESTIGATION` 的前置门禁。

高质量 Evidence Packet 与已审核答案可以由独立策略在响应完成后提议新的 Knowledge Update，但该更新不是原回答的一部分。Candidate、Admission 和 Publication 仍执行完整正式知识契约，其成功或失败不改变已完成 Direct Investigation 的审核事实。

## 模型与 Strategy 边界

Provider/Adapter 的接口兼容、Capability Strategy 的资格和受控 Activation 是相互独立的生命周期边界，必须按精确实现、配置、范围和有效期绑定。
显式 Activation 决定某个 Strategy 可进入的运行范围；身份漂移、资格失效或边界变化时必须失败关闭。具体业务质量判断不属于本运行视图。

## 实现与运行记录

具体 Profile 配置、数值预算、连接策略和运行记录统一归位至项目路径
`docs/project/implementation-reference/runtime-profile-history.md`。这些记录不能覆盖架构基线、证明当前代码已满足本契约，
或恢复被用户暂停的开发。
