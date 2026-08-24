---
id: SYS-ARCH-FLOWS
kind: system-architecture
status: current
authority: normative
owners: [architecture, application]
depends_on: [SYS-ARCH-COMPONENTS, SYS-ARCH-INVARIANTS, SYS-ADR-015, SYS-ADR-016, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING]
derived_from: [FINDING-008-024, FINDING-008-036]
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

若候选配置声明多个 Provider 偏好，Application 必须在 product freeze 和任何 socket、credential 或 request dispatch 之前，按顺序
选择第一个同时拥有 current exact Conformance、同 Strategy/Configuration Capability Qualification 与完整隔离 transport 的 route。
选择结果作为单一 Provider subject 贯穿 evaluation grant、session receipt、supervisor DNS/TCP provisioning、Gateway TLS/SNI/path、
Answer/Gateway role environment 和公开 Result；运行时只注入所选 Provider 的 credential。资格不完整的首选项只会被跳过，不会被
试调用；任何 request 已分派或 outcome unknown 后都禁止切换 Provider，同一问题若要选择新 route 必须重新 freeze 并取得新授权。

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

## 工程问答

```text
Explicit ENGINEERING_QA request
  → immutable original question + Question Understanding / Checklist
  → exact World Model Cognition Context
  → independent Investigation LLM proposes next search/read/parse from question + cognition + sealed ledger prefix
  → Source Broker validates and compiles one registered exact-revision read-only operation
  → isolated Retrieval Worker executes; Application appends Proposal/Decision/Result to Evidence Ledger
  → repeat adaptive investigation until a valid FINISH disposition or fail-closed fuse
  → seal one Question Evidence Package with admissible support/citation and retained boundary/audit partitions
  → fresh isolated conclusion-first Answer with claim citations
  → independent Review against original question and current package
  → Application derives APPROVED Delivery, same-package rewrite/re-review, or one typed-Finding Verification gap Request
  → fresh independent Verification Investigation reads gap + current Package/Ledger and adaptively proposes through Broker/Worker
  → on supplemental evidence: new Ledger Revision → new Package → new Answer → new Review
```

该流程的模式在任何读取和模型调用前已固定。软件世界模型为 Investigation LLM 提供持久的系统认知，不是手册、地图或 locator 缓存；这些都只是 World Model Cognition Context 的投影。认知缺失、无关或 Coverage 不足是 Ledger/Package 的显式状态，不阻断原 Checklist 在同一授权 exact revision 中驱动只读调查；这不是从 `WORLD_MODEL` 静默切换到 `DIRECT_INVESTIGATION`。

Investigation LLM 根据每次已密封 Result 自适应决定下一步，但不直接拥有任何 Tool。Source Broker 把其 Proposal 重新校验、绑定 exact revision/allowlist/remaining fuse 并编译；只有 Retrieval Worker 读取来源。每一步只追加到 Evidence Ledger，已确认 prefix 不可改写。来源内容是不可信 data，不能成为权限或操作指令。

Question Evidence Package 只有一个 seal/identity，但 `support/citation` 仅收可采信条目，`boundary/audit` 必须保留 Gap、Failure、Partial、
Conflict、Unknown、拒绝和资源记录；后者不能支持肯定 Claim。Reviewer 不规划补证操作，只返回具体 gap；补证由另一个全新上下文的
Verification Investigation 多步推进，不回到初始调查。非验收方向体验可以临时限制最多一次补证调查；正式 hardening/验收不得固定一轮，
必须预密封 revision/call/operation/bytes/wall-time/no-progress 熔断，answerable 因熔断未获批准计失败。

已审核包/结论可在 Delivery 后异步提议 Knowledge Update，但必须重走 Evidence、Candidate、Admission 和 Publication，不阻塞本题。

## 正式知识使用

显式知识查询冻结 Requirement Revision，打开固定 Snapshot 的有效 Read Session，对每个 Need 和 Joint Constraint 建立可重建证明。只有该有效 Session 内的语义不足才形成 Knowledge Gap；访问、执行、Session 或 Schema 失败必须保留为失败或限制。只有全部 Need 满足才可声明 SUFFICIENT。该路径是 `WORLD_MODEL` 的读取基础，但不是 `DIRECT_INVESTIGATION` 的前置门禁。

高质量 Evidence Packet 与已审核答案可以由独立策略在响应完成后提议新的 Knowledge Update，但该更新不是原回答的一部分。Candidate、Admission 和 Publication 仍执行完整正式知识契约，其成功或失败不改变已完成 Direct Investigation 的审核事实。

## 模型资格

Provider Contract Conformance 证明 Adapter 接口成立；Capability Evaluation 证明精确 Strategy 适合业务能力；Product Validation 证明端到端用户价值；显式 Activation 决定可用范围。四者独立且按精确实现、模型、配置和有效期绑定。某一 Provider 的资格不能借给另一 Provider；偏好顺序也不能替代当前资格。
