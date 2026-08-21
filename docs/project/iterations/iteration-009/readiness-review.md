---
id: ITER-009-READINESS
kind: iteration-readiness
status: accepted
authority: project-authorization
owners: [project, architecture, quality]
depends_on: [ITER-009-PROPOSAL, ITER-009-VERIFICATION, ROADMAP-M-002, ROADMAP-CANDIDATE-LOCAL-WEB-DIRECTION-PREVIEW-RECOVERY, ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-ACCEPTANCE, ITER-007-RESULT-SLICE-001-STOP-DECISION, ITER-008-INDEX, SYS-ADR-015, SYS-CONTRACT-AI-CAPABILITY-EVALUATION, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS]
code: []
tests: []
iteration: ITER-009
authorized_by: user
authorized_at: 2026-08-21T03:19:16Z
product_goal_alignment_verdict: accepted
product_goal_alignment_reviewed_by: user
product_goal_alignment_review_ref: codex-user-message:sha256:6ca47f7daa8bff61fa53e99d1c19b16098207d45fbf210427c3af19e5c9999ed
critical_assumption_catalog_digest: sha256:3ca13e4768159698cd69092946d820b7e04059fa6292b316c75b5c07cb0a659a
coding_input: false
---

# ITER-009 Readiness Review

## Reviewed exact inputs

已核对 product baseline `2cd743b2ba74c5a79cd4d38433830786de09e753`（tree
`1769f7d0aa84b7445a942eb90c280ac796d82fa4`）、planning commit `967e41bcaa25112ea6b18620d0ac8e0aa5a4a42a`（tree
`c8e9ce06becc9c1b72e3da60c654c9ba8bff2e16`）和归档 experiment
`c4ed92ea44383557dd25e6d327569cff13bb6d65`（tree `f8a2479b43321e95c6845531727fca893f8a5827`）。本轮分支从 planning
commit 开始，产品代码来自 2cd743b；归档实验不在本轮 baseline。

已核对本机 run-012 正向和边界证据：formal report file digest
`sha256:776a3afd5dca957a0bc2bd2b29a36bbea4b943ac2f7caa3d54f836f79fa84e6c`；positive browser result file digest
`sha256:d1a8a9760ecd3673504d1bdd0dc5f4e1dbb6c233f5f2c509888fc6cb40175c91`；boundary terminal file digest
`sha256:c4812a82b576ce79cc8b4be871a10cd038b60f2ccc91c7c34b06068c75abb4eb`。这些证明正向 Web 曾成功和 Limitation/Review
衔接存在缺口，不构成 ITER-008 Acceptance，也不授权复用旧运行 grant 或资格。

已核对 Proposal、Manifest、Verification Matrix、三个 Slice、方向体验优先治理规则、现行 System Contract、安全边界、成熟源码 Agent
对照和隐藏披露协议。`V-PRE-001` 至 `V-PRE-006` 均为 PASS。

## Product-goal alignment gate

- Reviewed evidence and baseline gap：accepted 能力止于 ITER-005/006；现有代码能交付 supported Web answer，但 boundary 会在
  Draft/Review 交付处内部失败，且方向未由用户在明确体验版上确认。
- Capability-path step, predecessor evidence, end capability and next gap：继续 `ROADMAP-M-002` Step 1；结束时普通用户通过本机 Web
  获取可引用答案或具体限制；下一 gap 是常见 Java/跨类/框架工程广度。
- Accepted/new capability integration and cross-domain path：三个 `V-XD` 分别绑定 ITER-006 accepted declaration/`CALLS` 与所属 Slice
  的方向体验、通用合同和最终交付能力。
- Hidden held-out ownership, before/target counts and live Web questions：用户持有最终两个工程 4+2，代码冻结前对实现隐藏；最终还有两条
  现场题。early canary 与 final suite 互不复用。
- Stop / redirect decision：无法快速形成新 Web result、特判、错误/无关 Citation、boundary 编造、fallback、弱化 Review、安全失败或
  用户 REDIRECT/REJECT 均立即停止。
- Direction preview can precede hardening：`SLICE-001 / V-PREVIEW-001` 使用真实 loopback Web 和三个代表性任务；只先做运行/安全/交付
  必需工作，全面合同、跨工程、回归、资格与验收留到用户 CONTINUE 后。

结论：本 Proposal 直接缩短用户可见 Web 问答差距，不是孤立 Profile/View/组件，Product-goal alignment 为 `accepted`。

## Architecture reflection gate readiness

Proposal 以 exact catalog digest `sha256:3ca13e4768159698cd69092946d820b7e04059fa6292b316c75b5c07cb0a659a`
冻结 A1—A5。Slice1 验证 A1—A3，并以 `V-XD-001`、`V-SEC-001` 提前反证 A4/A5；Slice2 保留并验证 A1—A4，以
`V-SEC-002` 提前反证 A5，同时承接 deferred early canary、成熟方案对照和逐层诊断；Slice3 按原顺序覆盖 A1—A5。每段恰好一个
Reflection Gate，后续 Slice 必须绑定前一 exact Result 和
新的用户授权消息。

成熟源码 Agent protocol/rubric/cache policy、ratio-ppm、at-most 250000、reuse horizon 12 与 replay protocol 在编码前冻结；用户是
独立裁决 Owner。调查仍为 2—4 次、每步/总 query-result bytes、总时长、Support、trace 和失败语义均由 Manifest 固定，不以调用次数
限制降低独立 Review 或答案质量。

## Outcome, scope and non-goals

授权 Outcome 是尽快形成带“方向体验 / 非验收 / 非生产”标识的真实本机 Web，然后依用户证据决定是否进入通用夯实和正式验收。
范围为 loopback、无普通用户认证、Java 源码、问题前 World Model、Source-off、自然答案/typed Limitation、独立 Review 与 Citation。

不包括公网、Production Activation、认证、第二语言、多内容类型、多工程管理、完整知识图谱重建或通用自治 Agent。归档 `1.5.12`
不是可继承实现。

## System contracts and unresolved decisions

现行 Contract set继续拥有 Snapshot/Update、typed query、no-payload use、bounded investigation、Gateway、Citation 和安全语义。
`SLICE-001` 不静默改变 Owner。若方向 `CONTINUE` 后证据要求 Evidence Package、typed Limitation、targeted rewrite 或异步知识沉淀改变
系统边界，`SLICE-002` 必须先创建 Finding，并同步更新 owning Contract 和必要 ADR。

当前未决项是 boundary 的首次偏差层、targeted rewrite 是否需要增加调用预算，以及第二工程是否暴露表示缺口。这些均有最早 Case，
不阻断方向体验开发，也不能靠 Prompt 猜测解决。

## Slice, dependency and risk closure

`SLICE-001` 已授权且是唯一 active Slice；`SLICE-002/003` metadata、Manifest 与设计均保持 proposed/coding false。第一段只先提供真实
Web 并形成方向 Reflection；small canary/comparison/diagnostic 与全面合同、跨工程、性能、完整资格和正式验收没有被列为页面首次可体验
的前置条件。

安全、权限、Secret、run identity、loopback、只读、Citation、独立 Review、零隐藏 retry 和失败真实性继续是硬门禁。初始用户消息只
授权开发；Provider/Web/live dispatch、credential 读取、browser question、hidden disclosure 与 Production 必须另行取得 exact 授权。

## Verification readiness

Verification Matrix 已为每个 Slice 冻结独立 cross-domain、Web、security 和 Reflection Case；hidden/early、comparison、diagnostic
与完整 regression 从 Slice2 开始绑定，不阻塞 Slice1 方向体验。Readiness Case 与 Slice-owned blocking Case 完全分离。最终 4+2、
现场题、成熟源码 Agent 比较和正向价值报告只能在 product code freeze 后执行。

本地确定性验证可以在开发授权下执行；任何真实模型或浏览器运行需要后续 run-specific grant。旧 run-012、run-028 或 ITER-008
qualification 仅为历史证据，不可直接授权新 identity。

## Authorization decision

**ACCEPTED / SLICE-001 DEVELOPMENT AUTHORIZED。** 用户消息
`codex-user-message:sha256:6ca47f7daa8bff61fa53e99d1c19b16098207d45fbf210427c3af19e5c9999ed` 于
`2026-08-21T03:19:16Z` 要求把环境准备到 ITER-009 可进入开发，故授权 Slice1 编码与本地确定性验证。

该授权明确不包含 Provider/Web/live dispatch、credential、正式 Web 会话、隐藏题披露、`SLICE-002/003` 或 Production Activation。
