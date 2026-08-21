---
id: ITER-010-READINESS
kind: iteration-readiness
status: accepted
authority: project-authorization
owners: [project, architecture, quality, product]
depends_on: [ITER-010-PROPOSAL, ITER-010-VERIFICATION, ROADMAP-M-002, ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST, ITER-006-RESULT-ACCEPTANCE, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, FINDING-010-002, SYS-ADR-013, SYS-ADR-014, SYS-ADR-015, SYS-ADR-016, SYS-CONTRACT-AI-CAPABILITY-EVALUATION, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS, SYS-CONTRACT-SOURCE-ARTIFACT]
code: []
tests: []
iteration: ITER-010
authorized_by: user
authorized_at: 2026-08-21T09:18:34Z
product_goal_alignment_verdict: accepted
product_goal_alignment_reviewed_by: user
product_goal_alignment_review_ref: codex-user-message:sha256:585f02c4edcf25502b40f880c17a7bdf7f1af71044cd8d1bbe97b055a735ee9e
critical_assumption_catalog_digest: sha256:26769498135692067597a1f59e0fbbc8b82502ebd5336f7fdb033a80e3baff82
coding_input: false
---

# ITER-010 Readiness Review

## Reviewed exact inputs

产品 baseline 固定为 commit `1fb997bab6444523f82ebf1a514a1abbf79656c7`、tree
`1369ce932c778c57a118123e8257ede476229d73`；本次授权复核的 planning commit 为
`01dcfe2233625dfaa021495850fb18ae1323063b`、tree `8e364ae854bfaa48580ab080a3e0d9c9c43c3d6f`。ITER-009 技术资产保留，
但产品方向仍为 rejected/redirect。已复核重制后的 Candidate、Proposal、Manifest、Verification Matrix、三个 Slice 和
`FINDING-010-002`，并把 World Model 定义与提问期调查职责明确分开。

用户收据 `d3b60bda…`（`2026-08-21T08:23:25Z`）确认重新制定计划并更新文档；新收据
`codex-user-message:sha256:585f02c4edcf25502b40f880c17a7bdf7f1af71044cd8d1bbe97b055a735ee9e`（`2026-08-21T09:18:34Z`）
接受本 Readiness，并只授权 `ITER-010-SLICE-001` 开发。修正前设计的旧授权不会被当作本设计的授权。

## Product-goal alignment gate

- Baseline gap：真实 Web 能运行但回答像代码走读；修正前一次性检索/先封包仍不能支持结果驱动的高级工程师式调查。
- Product concept：World Model 始终是持久、版本化、可验证、可更新的软件外部认知，不是手册、缓存或关键词索引。
- Capability path：继续 `ROADMAP-M-002` 最早未证明的 Step 1；提问期 Source 调查核实、补充或纠正认知，不取代问题前建模。
- Cumulative integration：一个链路组合 exact World Model Cognition Context 与本题 source/doc/config/test Evidence。
- Fast checkpoint：Slice1 最小纵切成立后立刻从真实 Web 跑一条跨来源代表问题，再做一个工程 4 条不同维度问题 + 现场题；方向确认后
  才做持久恢复、复杂冲突/去重、完整异常矩阵、跨工程和性能 hardening。
- Later proof：Slice2 独立第二工程 5+2，并对完整 Cognition、locator-only/empty 同链、成熟源码 Agent 做三臂同题消融；Slice3 在最终
  两个工程 10+2 与两条现场题复验。新消融 protocol/阈值/digest 当前未授权，Slice2 前须新用户收据。
- Stop：任何手册化/缓存化概念漂移、一次性固定调查、模型直接 Source 权限、特判、旧包批准、错误 Citation、审核/安全降级均阻断。

结论：Outcome 直接服务通用工程问答 MVP，且首版体验早于大规模夯实；方向对齐材料完整并已由用户接受。

## Architecture reflection gate readiness

Proposal 重新冻结 A1—A5：A1 检查世界模型认知概念、提问期调查与认知消融贡献；A2 检查 Investigation LLM 自适应决策和 Broker/Worker
权限；A3 检查调查后 seal、双分区 Package、Answer 与独立 Verification Investigation；A4 检查跨工程泛化；A5 检查三臂质量、完整
Cognition 的预提交增益、建模成本与复用周期。

Slice1 到期 A1—A3，Slice2 累积到 A4，Slice3 覆盖 A1—A5。每个阶段仍以用户新 `CONTINUE/ACCEPT` 作为下一段条件；安全上限只触发
失败关闭，不能裁剪调查、Evidence、Citation 或 Review。

## Outcome, scope and non-goals

计划 Outcome 是本机 `ENGINEERING_QA`：Investigation LLM 使用不可变原问题、exact World Model Cognition Context 和 append-only
Evidence Ledger 自适应提出下一步；Source Broker 校验/编译，Retrieval Worker 仅执行 exact-revision、allowlisted、read-only、audited
操作；调查结束后 Application 密封双分区 Question Evidence Package。support/citation 仅收 admissible entries；boundary/audit 强制保留
gap/failure/partial/conflict/unknown 且不能支持肯定 Claim。Answer 只读包；Reviewer 无直接 Source 权限，只提出具体可验证缺口；独立
Verification Investigation 在新上下文读取 gap + current Package/Ledger，多步自适应地经 Application/Broker/Worker 形成后继 Ledger、
Package、Answer、Review，不回初始 Investigation。

范围限 loopback、无认证、本地 Git exact revision、Java、World Model 与仓库源码/文档/配置/测试。非目标包括公网、Production、写仓库、
任意 shell、第二语言、跨仓库、长期 Memory 和同步知识发布。严格 `WORLD_MODEL` 与显式 `DIRECT_INVESTIGATION` 保留且不可静默 fallback。

## System contracts and unresolved decisions

系统 Owner 沿用 `SYS-ADR-016` 与 Engineering Question Answering Contract。planning commit 中的 current System docs 与 Manifest
共同表达 `ENGINEERING_QA_ADAPTIVE_INVESTIGATION@1`，system fileset digest 和 investigation budget digest 已按该输入冻结。

DTO、Broker port、抽象 read operation、Ledger storage 和 UI 折叠是实现细节；以下不是实现选择：World Model 不得缩窄为手册；调查必须
由先前结果驱动；模型无直接 FS/Shell/network/credential/source authority；Ledger append-only；调查后才 seal；Package seal 不等于真值；
Reviewer 补证必须由独立新上下文调查生成后继 Package 并重答重审；Slice1 的一次补证上限不得成为 Slice2/3 永久协议；禁止任何题目/
工程/关键词/符号/类/方法/fixture/Oracle 特判。

## Slice, dependency and risk closure

当前只有 Slice1 为 `authorized / coding_input=true`，顺序为：架构/门禁一致性 → 最小协议 → 最小真实
纵切 → deterministic freeze → 独立 live grant → 一题 Web 微检查点 → 4 条跨维度问题和现场题 → Reflection。Slice2/3 继续分别需要前序
exact Result 的 `CONTINUE` 和新授权；Slice2 还须取得新三臂消融及补证 hardening protocol 的用户冻结收据。

首版必须保留 exact revision、allowlist、只读、Source untrusted、Ledger append-only、seal、证据分区、role isolation、Citation、独立
Review、Secret 和失败真实性；持久恢复、复杂冲突/去重、跨工程、全面性能、完整异常矩阵、hidden/三臂 comparison 和正式验收可延后。
Provider/model/source fragment
disclosure 必须在 live 前另行冻结和授权。

## Verification readiness

Verification Matrix 新增并前置 `V-COGNITION-001`、`V-INVESTIGATE-001`、`V-BROKER-001`、`V-LEDGER-001`：它们分别阻断世界模型概念
漂移、非结果驱动调查、模型越权和调查前封包/包身份错误。Slice1 还必须以 `V-REVIEW-001` 证明 Reviewer 只提交具体缺口，并由全新
Verification Investigation 基于 current Package/Ledger 自适应形成后继 Ledger/Package/Answer/Review，而不直接操作 Source 或回到初始
Investigation。

最早体验先跑 `V-WEB-000` 一条代表问题；方向体验再运行 4 条跨维度问题和现场题，不需要先完成持久恢复、复杂矩阵、第二工程、性能、
完整回归、hidden 或三臂 comparison。所有 live Case 仍须在
代码冻结和独立 live grant 后执行；计划或测试不能冒充真实 Web 结果。

## Authorization decision

**ACCEPTED / SLICE-001 AUTHORIZED / DEVELOPMENT READY。** Readiness 的产品目标、架构边界、快速首版和验证输入已由收据
`585f02c4…` 接受；`PROJECT-CURRENT` 只指向 `ITER-010-SLICE-001`。本授权覆盖产品代码修改和本地确定性测试，不覆盖
credential、Provider/model call、live Web/browser、hidden disclosure 或 Production Activation。
Slice2 的三臂消融与 hardening 高安全上限仍是 `proposed / not authorized / not frozen`，必须另取新用户收据，不能复用旧 positive-value
收据。
