---
id: SYS-ARCH-FLOWS
kind: system-architecture
status: current
authority: normative
owners: [architecture, application]
depends_on: [SYS-ARCH-COMPONENTS, SYS-ARCH-INVARIANTS, SYS-ADR-015]
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
`method_implementations`，不能在非零候选后单独关闭 ledger。每个后续状态由 Application 从 ledger 和 sealed input 推导受限 operation allowlist，再编译 exact Snapshot、前序 Result
binding、Entity Ref、direction/predicate 与 bounds，并校验 obligation、bytes、Support、progress 和剩余预算后执行。模型固定 envelope
中的越权 operation 或过早 FINISH 不改变平台 transition。候选搜索可以返回 0/N；方法
实现查询可在同一 candidate result 内选择最多 3 个 exact method Ref，不取排名第一也不无界展开。至少一个 Result 执行后可以显式
FINISH，但只有 ledger 已关闭或没有合法 evidence-reducing transition 时才获得终态权力；FINISH 本身计作调用，所以零候选、截断
candidate 或其他没有合法 evidence-reducing transition 的 Result 可在 1 query + FINISH 后形成对应 Gap/Limitation。重复 query、无进展、越界或预算耗尽返回具体
Limitation，并保持 Source/Update/Direct fallback 为 0。查询、表示与业务发现三层完整性只由平台通过 progress receipt 投影；没有
同时证明时不得给 bounded absence，评测 Oracle identity 不进入 Answer。

该 Profile 每题实际模型调用为 4—6（调查 2—4、Draft 1、Review 1），不重试。Gateway supervisor 可以预建上限 6 个独立 Provider
connection；Gateway 按实际角色顺序消费，未使用 descriptor 在 terminal 后销毁并审计。旧固定三调用资格和 connection receipt 不得
复用。其他已接受 Profile 保持原调用协议。

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

## 正式知识使用

显式知识查询冻结 Requirement Revision，打开固定 Snapshot 的有效 Read Session，对每个 Need 和 Joint Constraint 建立可重建证明。只有该有效 Session 内的语义不足才形成 Knowledge Gap；访问、执行、Session 或 Schema 失败必须保留为失败或限制。只有全部 Need 满足才可声明 SUFFICIENT。该路径是 `WORLD_MODEL` 的读取基础，但不是 `DIRECT_INVESTIGATION` 的前置门禁。

高质量 Evidence Packet 与已审核答案可以由独立策略在响应完成后提议新的 Knowledge Update，但该更新不是原回答的一部分。Candidate、Admission 和 Publication 仍执行完整正式知识契约，其成功或失败不改变已完成 Direct Investigation 的审核事实。

## 模型资格

Provider Contract Conformance 证明 Adapter 接口成立；Capability Evaluation 证明精确 Strategy 适合业务能力；Product Validation 证明端到端用户价值；显式 Activation 决定可用范围。四者独立且按精确实现、模型、配置和有效期绑定。
