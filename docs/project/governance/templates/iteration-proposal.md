---
id: ITER-NNN-PROPOSAL
kind: iteration-proposal
status: proposed
authority: project-proposal
owners: [product, engineering]
depends_on: [SYS-PRODUCT-SUCCESS, SYS-ADR-019, PROJECT-GOVERNANCE-PLAN-EXECUTION]
code: []
tests: []
iteration: ITER-NNN
coding_input: false
---

# ITER-NNN Proposal：<Outcome>

## Trigger and evidence

## Product-goal alignment and cumulative delta

- MVP target reference: `SYS-PRODUCT-SUCCESS`
- Capability path reference and current step: <roadmap-milestone-and-step>
- Accepted predecessor evidence: <prior-acceptance-and-failure-evidence>
- Current product gap and real-question evidence: <gap-and-evidence>
- Accepted capabilities reused: <accepted-capability-refs>
- New capabilities integrated into the same answer chain: <new-capability-refs>
- Evaluator/user-owned hidden held-out before/target counts: <measurable-delta-and-isolation>
- Cross-domain questions combining old and new knowledge: <cross-domain-cases>
- Earliest falsifiable value freeze/quality Gate: <four-arm-freeze-quality-cases-and-slice>
- Earliest product-owned Web checkpoint after direction-quality PASS and live ad-hoc questions: <slice-and-gate>
- Minimum direction-preview checkpoint, representative tasks and explicit non-goals: <preview-slice-entry-and-cases>
- First usable-Alpha checkpoint before hardening: <first-slice-sustained-entry-diverse-inputs-and-cases>
- Four-arm direction checkpoint: <direct-evidence-source-only-world-model-plus-source-current-codex-before-product-or-web-change>
- Baseline role and exact identity: <strong-external-baseline-not-oracle-not-adjudicator-and-client-model-reasoning-tools-permissions-digest>
- Strict answer-quality superiority rule: <absolute-pass-per-question-no-regression-positive-blind-margin-tie-fails-no-secondary-compensation>
- World Model causal contrast inside the four-arm Gate: <source-only-versus-world-model-plus-source-under-same-agent-model-chain-budget-cache-and-reviewer>
- Direction decision owner and allowed outcomes before hardening: <owner-and-CONTINUE-REWORK-REDIRECT-REJECT>
- Repeatable experience version: <exact-version-repeatable-launch-fixed-loopback-address-semantic-chat-or-continuous-qa-visible-limitations-turn-failure-isolation>
- Conversational Agent boundary: <lead-agent-goal-hypothesis-plan-observe-replan-complete-plus-platform-authority-and-independent-reviewer>
- Same-Slice rework policy and no-progress limit: <progress-measure-positive-attempt-limit-and-redirect-bases>
- End-of-iteration user-visible Web capability: <exact-capability-if-accepted>
- Next blocking gap after success: <next-earliest-unproved-capability>
- Stop / redirect conditions: <falsifiable-conditions>

## Critical assumptions and falsification plan

列出决定本方案是否成立的少量关键假设。每项必须绑定最早验证 Slice、真实产品证据、反证条件和反证后的动作；第一段优先验证
最高风险假设。任何新产品代码、Prompt/Reviewer、Provider canary 或 Web 变更前，先以零外部调用、零产品代码的 freeze action 冻结至少
三条异质真实工程问题，其中至少两条未参与历史修复且没有 POM-only 问题；随后执行直接相关证据、同 Agent 仅源码、同 Agent 世界模型
认知+源码和 current Codex 四路严格 Gate。完整 hidden/跨工程复验不晚于首个 hardening Slice。

对照不能只要求“质量不退步”。freeze 必须冻结四路 exact identity、独立 source-truth ledger、答案先密封、随机匿名、独立盲评量表和
严格大于零的 Codex 总体答案质量差值。世界模型臂还必须独立通过绝对质量门、逐题不输直接证据/仅源码/current Codex，并证明至少一项
非 locator 世界模型贡献；全体打平、任一物质退步、双方失败、无法裁决或盲化失效都不得 `CONTINUE`。成本、时延、调用数、缓存与复用
另行报告，不能补偿答案质量。

本节必须恰好使用一张三列表，第一列以 `A1：<完整假设原文>` 格式编号；第二、三列分别写最早反证和反证后的动作，均不得留空。

| 假设 | 最早证据与反证 | 反证后的动作 |
|---|---|---|
| A1：<完整且可证伪的假设原文> | <最早-Slice、真实产品证据与失败判据> | <REWORK-by-default-or-explicit-redirect-basis> |

## Outcome and users

## Scope / non-goals

## Adopted system IDs

## Development slices and dependencies

至少明确区分：首个 Slice 先完成四路 freeze/quality Gate，只有该 Gate PASS 后才形成小而多样的非验收可体验 Alpha；只有 Alpha
`CONTINUE` 后才执行工程夯实与正式验收。Gate 前只安排冻结比较所需的验证工具和安全条件，不把产品代码、Web 或全面加固作为前置。
Alpha 必须可重复启动、固定本地地址、版本/限制可见且坏题不关闭
服务；不得用一次性测试运行替代。若目标声明 Chat，必须用至少五轮语义链验证追问、纠正和总结，并用“新对话”负测隔离；连续独立问题
不能冒充 Chat。每次失败默认在同一 Slice `REWORK`，只阻止 PASS、晋级与 hardening；现有本地开发授权覆盖修复时保持 active。只有
scope/Owner 变化、用户明确暂停或本地开发授权失效时才暂停。Proposal 必须冻结无进展的可测定义和尝试上限，并冻结授权连续性：人类
`PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY@1` 与系统派生 exact receipt 分离；公开开源、来源/许可证可确认、允许的 revision selection policy、每次运行的 exact revision、clean、
allowlisted、只读测试在已批准 route、预算、调度、有效期和 loopback evaluation 范围内不逐 run/逐题申请；每次外部动作仍在 Source
disclosure、network 和 credential 前生成回指 standing authority 的 exact receipt 并失败关闭越界。只有私有/未知/仅本机存在/dirty
数据、超出 approved upstream/revision selection policy/allowlist、新外部接收方或 Provider/model/endpoint/credential account、预算增加、超出 fallback admission
policy 的调度范围或需要一次性 override、外部写入、非 loopback
暴露、Production Activation 等 scope delta 才在 exact freeze 后直接申请，批准后自动续跑，等待期间继续独立安全工作。

若任一 Slice 计划使用 fallback route，Proposal 还必须冻结 fallback execution profile、其引用的 admission plugin/Case/receipt schema、全部
planned 调用类型和最坏完整质量链的 calls/tokens/duration，并证明其满足 plugin 定义的准入条件。standing external authority、
系统生成的 admission receipt 与一次性 exact override 是三个不同对象，不能互相推导；standing authority 覆盖政策内调用而不逐 run
授权，例外在批准前只能标记为尚未授权。准入等待期的同阶段 preferred-route-only、本地归因、修复、targeted tests 和 candidate freeze
必须明确列出，不能把等待准入作为停止开发的理由。通用模板不得写死 Provider/model 名称；它们只能由当次 execution profile 配置和执行收据给出。

四路比较是 Web/Alpha 之前的阻断方向 Gate，不得下放到体验之后。直接证据、同 Agent 仅源码、同 Agent 世界模型认知+源码与 current
Codex 必须在同一 exact revision、问题集、Source scope、输出边界和盲评 rubric 下隔离；前三路固定 Provider/model/config，第 2/3 路再
固定 Agent/Prompt/tools/budget/cache/Reviewer，仅切换世界模型认知。

## Machine-enforced plan execution

Manifest 必须使用 `schema_version: 2` / `DEVELOPMENT_PLAN_EXECUTION_CONTROL@1`，且只有一个 `current_action`。Proposal 必须预先说明
plan revision、当前 action/Case/Result、JSON evidence、受保护 runner identity、路径 allowlist/denylist、coding/external flags、locks，
以及 PASS/FAIL/INVALID 的唯一后继；所有直接后继在 trusted base 的 `next_action_contracts` 中完整预注册。迁移只接受 current action
指定路径上的 sealed Result 与 digest-bound JSON 收据组合，并机械重算 runner、report、artifact 摘要和 Verdict 聚合。开发前运行
snapshot，交付前以 trusted base 运行 base-diff gate；候选 Manifest/Result 不能为自身扩权。改变计划必须另有 Finding、accepted PDR
和 exact 用户授权引用。

## Risks and unknowns

## Standing external authority and scope-delta boundary

- Human authority receipt and exact standing-scope digest: <codex-user-message-ref-and-sha256-scope>
- Covered data and purpose: <canonical-public-source-license-exact-commit-tree-clean-allowlist-read-only-disclosure>
- Covered external route and sink: <provider-model-endpoint-credential-account-and-loopback-evaluation-only>
- Covered budget, validity and schedule: <calls-retries-tokens-duration-cost-provider-window-expiry-and-revocation>
- Derived exact controls: <authorized-input-manifest-one-use-disclosure-dispatch-receipt-terminal-audit-and-fail-closed-rule>
- Human scope deltas: <private-unknown-local-dirty-different-or-unverified-source-drift-new-recipient-route-budget-increase-fallback-admission-override-write-non-loopback-production-and-exclusions>

该 standing authority 一经 Readiness 接受即可在 source identity 不变时跨 run、问题和 Turn 复用；上述机器 receipt 逐次生成但不是新的
用户授权。不得把审计精度变成重复审批。

## Verification and acceptance

## Authorization decision

Proposal 本身不授权编码；结论被接受时把状态改为 `accepted`，但仍需 Manifest、Verification Matrix、Readiness Review、已授权 Slice，
以及 `project/current.md` 对 plan revision/current action/Case 的精确镜像共同成立。广义 `coding_input=true` 不能覆盖 action 路径锁。
