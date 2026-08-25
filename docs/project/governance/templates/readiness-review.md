---
id: ITER-NNN-READINESS
kind: iteration-readiness
status: proposed
authority: project-authorization
owners: [project, architecture, quality]
depends_on: [ITER-NNN-PROPOSAL, ITER-NNN-VERIFICATION]
code: []
tests: []
iteration: ITER-NNN
authorized_by: pending
authorized_at: pending
product_goal_alignment_verdict: pending
product_goal_alignment_reviewed_by: pending
product_goal_alignment_review_ref: pending
critical_assumption_catalog_digest: pending
---

# Iteration NNN Readiness Review

## Reviewed exact inputs

## Product-goal alignment gate

核对 Proposal/Manifest 已冻结通用源码问答 MVP 的 baseline gap、已有能力累积路径、独立持有且对实现隐藏的 held-out 自由
问题增量、至少一个跨域问题、最早正式 Web 体验点、现场临时问题和停止条件。任一项缺失，或 Outcome 只是孤立
Profile/View/组件，Readiness 必须保持 `proposed`。

- Reviewed evidence and baseline gap: <exact-reference-and-verdict>
- Capability-path step, predecessor evidence, end capability and next gap: <exact-reference-and-verdict>
- Accepted/new capability integration and cross-domain path: <exact-reference-and-verdict>
- Hidden held-out ownership, before/target counts and live Web questions: <exact-reference-and-verdict>
- Stop / redirect decision: <exact-reference-and-verdict>
- Direction preview can precede hardening: <real-entry-minimum-cases-deferred-hardening-and-owner>
- High-risk Alpha can precede hardening: <second-small-diverse-live-checkpoint-or-documented-merge-rationale>
- Current Codex Alpha comparison: <original-failure-plus-two-heterogeneous-including-at-least-one-post-freeze-live-question-exact-identity-fresh-task-sealed-answers-independent-blind-judge-and-blocking-case>
- Strict superiority and tie rule: <absolute-quality-pass-per-question-no-regression-positive-quality-margin-tie-fails-no-secondary-compensation>

## Architecture reflection gate readiness

核对 Proposal 已冻结关键假设、最早反证、成熟替代方案对照和反证后的动作；Manifest 为每个 Slice 恰好绑定一个
`V-REFLECT-NNN`。第一段必须优先验证最高风险架构假设，每个 Slice Result 必须形成独立复盘结论；没有 `CONTINUE` 决定和用户
再次授权时，后续 Slice 不得进入开发。
失败默认进入同一 Slice 的 `REWORK`。Proposal 必须冻结无进展定义和正整数尝试上限；只有明确用户转向、核心架构证伪或达到该上限
才允许 `REDIRECT`。
每段 Reflection 必须绑定 exact 用户决策消息收据；后续 Slice 的授权必须引用同一条前序 Reflection 决策消息，且不能复用更早
授权。current Codex 的 client/binary/model/reasoning/tools/permissions identity、fresh 隔离任务、答案先密封、protocol/rubric/cache policy、
严格答案质量 metric/unit/direction/正阈值/replay protocol 和独立裁决 Owner 必须在首个持续 Web Alpha 授权前冻结；完整 hidden 与跨工程
复验仍可后置到夯实阶段。调查步数与模型调用上限至少为 2，并结构化冻结 query/result 单步与总字节、总时长、Support、trace 和超限语义。

## Outcome, scope and non-goals

## System contracts and unresolved decisions

## Slice, dependency and risk closure

核对第一个用户可感知 Slice 会直接形成明确标注、小而多样的非验收可体验 Alpha，并由用户实际使用后判向。全面契约、回归、性能、
资格和正式验收只能放在 Alpha `CONTINUE` 之后。早期真实运行仍需闭合安全、权限、Secret、外部披露和失败真实性；除此之外的加固
不得被误列为 Alpha 的阻断。

核对首个体验 Slice 交付可重复启动、固定本地地址、版本和限制可见、单题失败不关闭服务的真实版本，而不是一次性验证运行。若声明
Chat，还必须冻结 Conversation/Turn/Context、追问、纠正、总结、逐轮证据/审核和新对话隔离；仅共享 Session Authority 不算 Chat。

核对主工程 Agent 拥有用户目标、假设、计划、上下文选择、工具选择、观察解释、重规划、完成判断和自然答案综合；平台继续拥有 exact
版本、授权、只读工具执行、证据身份、预算与审计，独立 Reviewer 继续阻断错误。不得把模型 hidden memory、用户陈述或旧答案写成事实权威。

同时核对输入持有者、独立技术评测方和用户方向决策者是不同职责：独立评测先裁决正确性、完整性、Citation、边界和特判；用户只根据
已复核且限制可见的真实结果决定 `CONTINUE / REWORK / REDIRECT / REJECT`。

同时核对 current Codex 只作为强基线候选，不是 Oracle 或 adjudicator；Codex 与系统答案相互不可见并先密封，评测方未参与任一答案
生成且只在匿名 A/B 上依据同一 exact evidence 裁决。产品对照与 full cognition/locator-only 因果消融必须使用不同 binding。

## Verification readiness

## Authorization decision

只有明确授权后才把 `status` 改为 `accepted`，填写非 `pending` 的 `authorized_by` / `authorized_at`，再更新 Iteration、Slice 与 `project/current.md`。本记录不能自行推定用户授权。
