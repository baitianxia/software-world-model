---
id: ITER-010-READINESS
kind: iteration-readiness
status: accepted
authority: project-authorization
owners: [project, architecture, quality, product]
depends_on: [ITER-010-PROPOSAL, ITER-010-VERIFICATION, ROADMAP-M-002, ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST, ITER-006-RESULT-ACCEPTANCE, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, SYS-ADR-013, SYS-ADR-014, SYS-ADR-015, SYS-ADR-016, SYS-CONTRACT-AI-CAPABILITY-EVALUATION, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS, SYS-CONTRACT-SOURCE-ARTIFACT]
code: []
tests: []
iteration: ITER-010
authorized_by: user
authorized_at: 2026-08-21T07:10:28Z
product_goal_alignment_verdict: accepted
product_goal_alignment_reviewed_by: user
product_goal_alignment_review_ref: codex-user-message:sha256:5cdb7000ba36328f5caa27727c6b689ad4e98e7ad13eca72837fa020d0c270c9
critical_assumption_catalog_digest: sha256:3cbbee84b81acbe7213a6d04aa7d9565b750328f8e0f9fd9a0796749d260c57e
coding_input: false
---

# ITER-010 Readiness Review

## Reviewed exact inputs

已核对产品 baseline commit `1fb997bab6444523f82ebf1a514a1abbf79656c7`、tree
`1369ce932c778c57a118123e8257ede476229d73`。该提交包含 ITER-009 Slice1 的技术实现；其产品方向必须按
`ITER-009-RESULT-SLICE-001-STOP-REDIRECT` 分类为 rejected/redirect，不能继承 Acceptance、旧 live grant、资格或用户方向认可。

已核对 `ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST`、Proposal、Manifest、Verification Matrix、三个 Slice，以及更新后的
current `SYS-PRODUCT-SUCCESS`、ADR-013/014/015/016、Engineering/Evidence/World Model Answering、Agentic Task、Knowledge、Source、
Gateway、安全与 Browser 边界。`FINDING-010-001` 已把原 Source-off 产品边界与新 `ENGINEERING_QA` 的冲突处置到 ADR-016 和 owning
Contract；Slice1 的 `V-ARCH-001` 是持续一致性回归，不是尚未完成的架构决定。

用户先以 `codex-user-message:sha256:1b3270242962b8d099ac9166304dc6188be22054cfc2a685b2ade5616d4cc2f4` 要求准备开发计划，
再以 `codex-user-message:sha256:5cdb7000ba36328f5caa27727c6b689ad4e98e7ad13eca72837fa020d0c270c9` 于
`2026-08-21T07:10:28Z` 明确接受混合架构。`V-PRE-001` 至 `V-PRE-006` 均为 `PASS / readiness blocking`。

## Product-goal alignment gate

- Baseline gap：真实 Web 可运行，但默认答案是方法/分支/调用走读；严格 Source-off 知识边界不能覆盖一般工程用途、运行、配置、故障和
  影响问题。
- Capability path：继续 `ROADMAP-M-002` 的同一最早未证明能力，不建立与通用工程问答无关的 Profile、页面或验证器。
- Cumulative integration：每段 `V-XD` 都要求在同一 Evidence Package/答案中组合 ITER-006 accepted Snapshot 知识与本轮 exact-revision
  源码、文档、配置或测试证据。
- Measurable delta：首段一个真实工程 4 条跨类型题加一条现场题；第二段独立工程 5+2 early canary；最终两个隐藏工程 10+2 和两条
  现场题。隐藏工程和问题在所属代码冻结前由用户持有。
- Earliest Web：Slice1 在架构和最小实现闭合后从同一 product-owned loopback Web 运行，不以 CLI、静态回放或测试代替。
- Positive value：在零重大错误、逐结论不退步前提下，测量 12 题复用周期内相对成熟源码 Agent 的 live Source exposure ratio；调用
  次数不是质量裁剪指标。该比较原样复用 ITER-009 已由收据 `6ca47f7d…` 接受的 protocol/rubric/cache、ratio-ppm、250000 上限和
  12 题周期；没有把本轮架构接受收据冒充为指标冻结。
- Stop/redirect：代码走读仍是默认、任何特判、意图丢失、无关 Citation、越权 Source、无界补检索、审核降级、重大错误、安全失败或
  用户 REDIRECT/REJECT 均阻断。

结论：Outcome 是同一 Web 上可人工判断的通用工程问答增量，不是孤立内部组件，Product-goal alignment 为 `accepted`。

## Architecture reflection gate readiness

Proposal 以 exact catalog digest `sha256:3cbbee84b81acbe7213a6d04aa7d9565b750328f8e0f9fd9a0796749d260c57e` 冻结 A1—A5。
Slice1 验证 A1—A3，并由 `V-XD-001`、`V-SEC-001` 提前反证 A4/A5；Slice2
保持并验证 A1—A4，以 `V-COMP-EARLY-002` 提前反证 A5；Slice3 按顺序覆盖全部 A1—A5。每段恰好一个 Reflection Gate，且下一段
必须绑定前一 exact Result、用户 `CONTINUE` 收据和新的开发授权。

最危险假设 A1 已由本次准备建立 Finding、新 `SYS-ADR-016`、新 Engineering QA Contract、owning current System docs、Manifest
Contract fileset 和治理门禁作为开发输入；`V-ARCH-001` 在 Slice1 继续验证文档—代码—测试一致性。若实现不能保持严格
`WORLD_MODEL`、显式 `DIRECT_INVESTIGATION` 与新 `ENGINEERING_QA` 三种身份，Slice1 必须 REDIRECT。

## Outcome, scope and non-goals

授权 Outcome 是一个明确标记“方向体验 / 非验收 / 非生产”的本机 `ENGINEERING_QA`：World Model 提供工程地图、可复用证据和检索
提示；问题理解同时从原问题 checklist 与 Snapshot hints 形成检索计划；隔离 retrieval worker 对授权 exact revision 的源码、仓库文档、
构建配置和测试只读调查，密封 Evidence Package；Answer/Reviewer 只读包；页面显示结论优先答案或诚实 Limitation 及结论级 Citation。

World Model 不是提问期源码检索的召回硬门禁。Snapshot 为零、无关或 Coverage 不足时，不能阻断由原问题 checklist 驱动的受控检索；
反过来，Source 内容按不可信输入处理，不能借文档/注释指令扩大工具、路径、Provider 或授权。

本轮不包括公网、认证、Production、写仓库、任意命令、第二语言、跨仓库、长期 Memory 或同步知识发布。严格 `WORLD_MODEL` 与显式
`DIRECT_INVESTIGATION` 继续保留，不能成为新模式的静默 fallback。

## System contracts and unresolved decisions

Readiness 的开发输入已包括 `FINDING-010-001`、`SYS-ADR-016`、
`SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING` 以及同步更新的 Product Success、runtime flow、Agentic/Evidence/World
Model/Response/Source Contract、Security、Browser 和 docs gate。Manifest 的 exact fileset digest 绑定该变更后的 current 文档集，
`sha256:2f28325f8b0ddf19578a8d0c78ff98a7032ad353ab3557bc2b456ab1e3fdb53a`，
不是变更前旧边界；严格 WORLD_MODEL、显式 DIRECT 和新 ENGINEERING_QA 的 Owner/身份已闭合。

Evidence Package 的具体 DTO、检索算法、UI 折叠方式和 telemetry 字段属于 Slice1 实现细节，但必须服从已冻结的 original checklist +
Snapshot hints、Source untrusted、`MORE_EVIDENCE_REQUIRED` 受控补检索、role isolation、Provider disclosure 和异步知识沉淀语义；不得由
Prompt 私下改 Owner。

## Slice, dependency and risk closure

`SLICE-001` 是唯一 active/coding Slice；其内部顺序固定为复核 current System boundary → deterministic protocol → minimal product chain → freeze →
另行授权的真实 Web direction preview → Reflection。初始开发授权不会自动越过 live boundary。`SLICE-002/003` 保持 proposed/coding false。

检索只允许 allowlisted exact revision regular files和注册只读操作；路径、symlink、size、binary、secret pattern、prompt injection、revision
drift 和 source-write probe 必须失败关闭。World Model hint 只能缩小候选或增加可复用证据，不能删除原 checklist 的证据需求。Answer
与 Reviewer 无 repo mount/Source tool；Reviewer 只有给出具体 `MORE_EVIDENCE_REQUIRED` 时，Application 才能在同一授权、revision 和预算内
补检索并重封新包。任何 rewrite/reseal 后必须独立复核。

Provider 出网时哪些片段可发往哪个 exact Provider 不是本开发授权的一部分；live freeze 必须另行密封 disclosure allowlist、Provider、
model、endpoint、configuration、secret reference 与每个 role 的输入 digest。

## Verification readiness

Verification Matrix 分离 readiness、Slice blocking、live browser、hidden、Agent comparison、positive value 和 Reflection。Slice1 的
`V-ARCH-001`、`V-QINTENT-001`、`V-HYBRID-001`、`V-ISOLATION-001`、`V-REVIEW-001`、`V-LIMIT-001` 和 `V-SEC-001` 可以先用
本地确定性 fixture 闭合；真实 `V-WEB-001/V-PREVIEW-001` 必须在代码冻结和独立 live grant 后执行。

首段方向体验允许先于 hidden/Agent comparison/全面性能与完整回归，但不延后 System ownership、只读、权限、Secret、revision、Package
seal、role isolation、Citation、独立 Review 和失败真实性。后续 hidden 和 Agent comparison 输入不能用于实现，披露后产品修改会烧毁
对应证据。

## Authorization decision

**ACCEPTED / SLICE-001 DEVELOPMENT AUTHORIZED。** 准备开发的收据
`codex-user-message:sha256:1b3270242962b8d099ac9166304dc6188be22054cfc2a685b2ade5616d4cc2f4` 与架构接受收据
`codex-user-message:sha256:5cdb7000ba36328f5caa27727c6b689ad4e98e7ad13eca72837fa020d0c270c9` 共同构成授权链；后者时间为
`2026-08-21T07:10:28Z` 并作为 Manifest 的终结引用。授权覆盖 Slice1 的 Finding、System/ADR/治理文档、产品代码和本地确定性测试。

不授权 credential、Provider/model call、live Web listener/browser question、源码片段向 Provider 披露、hidden input、Slice2/3 或
Production Activation；这些动作不得复用本收据作为运行 grant。
