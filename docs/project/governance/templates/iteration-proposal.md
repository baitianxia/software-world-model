---
id: ITER-NNN-PROPOSAL
kind: iteration-proposal
status: proposed
authority: project-proposal
owners: [product, engineering]
depends_on: [SYS-PRODUCT-SUCCESS, PROJECT-GOVERNANCE-PLAN-EXECUTION]
code: []
tests: []
iteration: ITER-NNN
coding_input: false
---

# ITER-NNN Proposal：<Outcome>

## Trigger and evidence

## Product goal and cumulative delta

- MVP target reference: `SYS-PRODUCT-SUCCESS`
- Capability-path step and accepted predecessor evidence: <exact-references>
- Current user-visible gap: <real-browser-experience-evidence>
- Accepted capabilities reused in the same chain: <exact-result-refs>
- New capabilities integrated in this iteration: <world-model-agent-source-evidence-review-chat-delta>
- First complete browser experience: <slice-case-launch-address-and-user-visible-boundary>
- Post-experience direction comparison: <same-candidate-at-least-three-heterogeneous-two-unseen-and-actual-current-codex>
- User direction owner and decisions: <owner-and-CONTINUE-REWORK-REDIRECT-REJECT>
- Work unlocked only by `CONTINUE`: <four-arm-causal-ablation-full-regression-hidden-cross-project-hardening>
- End-of-iteration Web capability: <exact-capability-if-accepted>
- Next blocking gap after success: <next-earliest-unproved-capability>

## Critical assumptions and falsification

只列影响方向的少量可证伪假设。首次完整体验后，在同一候选上用真实问题验证最高风险假设；失败默认保持同一长运行动作，先定位最早
偏差，提出可证伪根因并做通用修复和 targeted recheck。单题失败、局部测试失败或 Provider 失败本身都不是新建动作或停止开发的理由。

| 假设 | 最早证据与反证 | 反证后的动作 |
|---|---|---|
| A1：<完整且可证伪的假设原文> | <complete-experience-or-post-experience-case-and-failure-rule> | <root-cause-first-REWORK-or-explicit-redirect-basis> |

## Outcome and users

## Scope and non-goals

## Adopted system IDs

## Development order

当没有代表性 MVP 时，本轮默认只设计两个游标动作：

1. `complete-experience-development`：一个可跨普通提交的长运行产品动作。它必须贯通世界模型认知、主工程 Agent、受控只读源码工具、Evidence/Citation、独立审核与无认证 loopback 浏览器 Chat。第一次完整主链可操作后立即交付，不等待全量回归或 hidden。
2. `user-direction-decision`：基于该体验和同一候选的严格质量比较，由用户决定 `CONTINUE / REWORK / REDIRECT / REJECT`。它不修改产品。

同一候选的质量比较至少覆盖 3 个异质问题，其中至少 2 个未参与历史修复，并与 actual current Codex 作 fresh、隔离、密封、独立评估。系统必须先通过绝对质量门，逐题不得物质落后 current Codex，总体答案质量严格超过它，并证明世界模型至少提供一项非 locator 的有效认知贡献。Codex 是强基线，不是 Oracle 或裁判；source truth 由独立源码证据决定。比较未通过阻止方向 `PASS`、hardening 和下一阶段，不阻止首次体验交付。

只有用户 `CONTINUE` 后，后续 Slice 才执行 direct evidence、同 Agent 仅源码、同 Agent 世界模型认知+源码、current Codex 四路因果消融，以及 full regression、hidden、跨工程、性能和正式验收。不得把这些工作倒置为首次体验前置。

首次体验必须可重复启动、固定本地地址、版本和限制可见、单题失败不关闭服务。若声明 Chat，必须验证同一 Conversation 的语义追问、纠正、总结、逐轮证据/审核和新对话隔离；连续独立问题不能冒充 Chat。

## Failure and repair policy

每个答案问题先在 `Source truth → World Model cognition → conversation/task understanding → Agent work state/plan → tool observation/evidence → answer → independent review → Web` 中定位最早偏差，形成可证伪假设，再修改实现、Prompt、Schema 或 Contract。修复先跑最小复现和未参与修复的相邻案例，再跑一个有界 live canary；同一假设修复一次仍复现时评审架构职责，禁止堆叠题目特判。

首次体验前只运行 targeted impact、startup、safety 和 failure-truthfulness 测试。full regression 只在用户 `CONTINUE` 后运行。

## Authorization continuity

冻结 Slice 本地开发授权、人类 `PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY@1` 和系统派生 one-use runtime receipt 的边界。公开开源、来源/许可证可确认、符合 approved revision policy、clean、allowlisted、只读测试工程，在已批准 route、预算、调度、有效期和 loopback `EVALUATION_ONLY` 范围内不逐 run、逐题、逐 Turn 申请人工授权；每次外部分派仍在网络和 credential 前生成 exact receipt。

只有私有/来源未知/dirty 数据、超出来源或 revision policy、新外部接收方或 route identity、预算增加、外部写入、非 loopback 暴露或 Production 等真实 scope delta 才申请最小授权。批准后自动继续；等待期间继续所有独立安全工作。通用计划不写死 Provider/model 名称。

## Plan execution

Manifest 使用一个长运行 current action、清晰的路径/权限/locks 和一个用户方向后继。普通提交、测试、失败和外部分派不移动游标，不生成 Result。Result 仅在完整体验交接或真正移动游标时密封；runner 只验证交接事实，不复制产品工作流，不引入 Freeze-first、Activation 分钟时钟、逐失败状态机或 whole-Manifest 摘要。

## Risks, rollback and acceptance
