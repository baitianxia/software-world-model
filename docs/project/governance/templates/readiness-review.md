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
plan_revision_ref: pending
current_action_ref: pending
current_action_case_id: pending
plan_execution_control_verdict: pending
standing_external_authority_schema: PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY@1
standing_external_authority_ref: pending
standing_external_authority_scope_digest: pending
---

# Iteration NNN Readiness Review

## Reviewed exact inputs

## Product-goal alignment

核对 Proposal/Manifest 已说明 baseline 的真实浏览器体验缺口、既有能力如何进入同一回答链、本轮首次完整体验、同候选质量比较、用户方向决定和 `CONTINUE` 后工作。孤立组件、测试数量或“有页面”不能替代完整体验。

- Baseline gap and predecessor evidence: <exact-reference-and-verdict>
- Complete experience boundary: <world-model-agent-source-evidence-citation-review-semantic-chat>
- First operable browser delivery Case and launch entry: <V-CHAT-EXPERIENCE-NNN-requires-result-false-no-cursor-move>
- Final experience handoff Case: <V-MVP-EXPERIENCE-NNN-requires-result-true-after-comparison-or-proven-post-repair-failure>
- Post-experience heterogeneous/Codex comparison: <three-questions-two-unseen-exact-current-codex-and-independent-review>
- Work locked until `CONTINUE`: <four-arm-ablation-full-regression-hidden-cross-project-hardening>
- Stop/redirect basis: <exact-falsifiable-conditions>

## Executable-plan readiness

核对 Manifest 使用 `schema_version: 2` / `DEVELOPMENT_PLAN_EXECUTION_CONTROL@1`，且只有一个长运行 `current_action`。它必须完整绑定 plan revision、Slice、最终 handoff Case/Result、coding/external 权限、allowed/forbidden paths 和 locks；`project/current.md` 精确镜像当前 action/Case。Manifest 还必须用独立字段把首次可操作浏览器交付 Case 与最终 Result handoff Case 分开，并明确前者 `requires_result=false`、不移动游标，后者 `requires_result=true`。

完整体验开发可跨多个普通提交。第一次完整浏览器主链可操作即交付，但不创建 Result、不移动游标。Result 和最小 runner 只用于最终方向 handoff，或证明一次通用修复后同类重大失败仍存在而移动计划游标；不能要求每次提交、测试、失败或 Provider dispatch 建立动作/Result；不得引入 Freeze-first、Activation 分钟时钟、whole-Manifest 摘要或复制产品工作流的 verifier 状态机。

开发前运行 snapshot，交接或合并前用 trusted base 运行 diff gate。candidate Manifest 不能给自身 diff 扩权；runner 必须先于其验证的 Result 冻结。

## Complete-experience readiness

核对第一项产品工作就是完整纵向体验，而非先建评测设施或进行全量回归：

- 世界模型认知实际进入回答链，并提供的不只是 locator；
- 主工程 Agent 负责理解目标、形成/修订计划、选择和解释工具观察、综合自然答案；
- 源码访问受控、精确版本、只读，答案绑定 Evidence/Citation；
- 独立 Reviewer 检查正确性、完整性、引用和未知边界；
- 无认证 loopback 浏览器可重复启动，版本/限制可见，单题失败不关闭服务；
- Chat 支持语义追问、纠正、总结、逐轮证据/审核和新对话隔离。

首次完整主链可操作后必须以 `V-CHAT-EXPERIENCE-NNN` 立即交给用户，不等待 strict comparison、full regression、hidden、跨工程或 hardening；此次交付不生成 Result、不移动游标。首次交付前只允许 targeted impact、startup、safety 和 failure-truthfulness 检查。

## Post-experience quality readiness

核对同一体验候选随后会回答至少 3 个异质真实工程问题，其中至少 2 个未参与修复，并与 actual current Codex 的 fresh 隔离答案进行密封、独立评估。事实来自独立源码证据；Codex 不是 Oracle 或裁判。

系统必须通过绝对质量门，逐题无物质落后，总体答案质量严格超过 current Codex，并至少证明一项非 locator 世界模型贡献。失败、平局、无法裁决或重大错误只阻止方向 `PASS`、hardening 和晋级，不阻止已经形成的首次体验交付；失败回到同一开发动作做根因归因和通用修复。

只有最终 `V-MVP-EXPERIENCE-NNN` Result 已密封并进入用户判向后才记录方向。`CONTINUE` direction receipt 只使后续工作具备规划资格；必须再有新 PDR、明确用户授权和可信父 cutover，才执行 direct evidence、同 Agent 仅源码、同 Agent 世界模型认知+源码、current Codex 四路因果消融，以及 full regression、hidden、跨工程和正式验收。本地消息 digest 不能冒充平台认证身份或授权。

## Root-cause and repair readiness

核对计划要求沿 `Source truth → World Model cognition → conversation/task understanding → Agent work state/plan → tool observation/evidence → answer → independent review → Web` 定位最早偏差，并在任何 Prompt/Schema/Contract/代码修改前形成可证伪假设。修复后先做最小复现和至少两个未参与修复的相邻案例，再做一个有界 live canary；不允许题目特判或反复重跑碰答案。

普通失败保持当前 Slice `IN_PROGRESS / coding_input=true`。只有用户明确停止/转向、真实 scope delta 等待且所有独立安全工作已穷尽，或不可绕过的安全禁止，才允许结束开发回合。

## Authorization continuity

核对 Slice 开发授权、人类 `PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY@1` 与每次系统派生 exact runtime receipt 已分离。公开开源、来源/许可证可确认、符合 revision policy、clean、allowlisted、只读的测试工程，在已批准 route、预算、调度、有效期和 loopback `EVALUATION_ONLY` 范围内不逐 run、逐题、逐 Conversation/Turn 申请人工授权；每次外部分派仍须在 Source disclosure、network 和 credential 前生成 one-use receipt。

只有真实 scope delta 才申请最小授权，例如私有/来源未知/dirty 数据、来源或 revision policy 漂移、新外部接收方或 route identity、预算增加、外部写入、非 loopback 或 Production。receipt 不得创建或扩大权限，缺失/失配必须在外部分派前失败关闭。通用计划不写死 Provider/model 名称。

## Outcome, scope, risks and unresolved decisions

## Verification readiness

## Authorization decision

只有明确用户授权后才把 `status` 改为 `accepted`，填写 `authorized_by` / `authorized_at`，并同步 Iteration、Slice、Manifest 和 `project/current.md`。本记录不能自行推定授权。
