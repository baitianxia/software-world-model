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

## Product-goal alignment gate

核对 Proposal/Manifest 已冻结通用源码问答 MVP 的 baseline gap、已有能力累积路径、独立持有且对实现隐藏的 held-out 自由
问题增量、至少一个跨域问题、最早可证伪四路价值 Gate、该 Gate PASS 后的最早正式 Web 体验点、现场临时问题和停止条件。任一项缺失，或 Outcome 只是孤立
Profile/View/组件，Readiness 必须保持 `proposed`。

- Reviewed evidence and baseline gap: <exact-reference-and-verdict>
- Capability-path step, predecessor evidence, end capability and next gap: <exact-reference-and-verdict>
- Accepted/new capability integration and cross-domain path: <exact-reference-and-verdict>
- Hidden held-out ownership, before/target counts and live Web questions: <exact-reference-and-verdict>
- Stop / redirect decision: <exact-reference-and-verdict>
- Earliest four-arm value Gate before product/Web change: <freeze-quality-cases-direct-evidence-source-only-world-model-plus-source-current-codex>
- Gate-PASS direction preview before hardening: <real-entry-minimum-cases-deferred-hardening-and-owner>
- Strict superiority and tie rule: <absolute-quality-pass-no-per-question-loss-to-any-baseline-positive-codex-margin-non-locator-contribution-tie-fails-no-secondary-compensation>

## Machine-enforced plan readiness

核对 Manifest 是 `schema_version: 2` / `DEVELOPMENT_PLAN_EXECUTION_CONTROL@1`，且恰好一个 `current_action` 完整绑定 plan revision、唯一
Slice/Case/Result ID+path、前置、coding/external flags、allowed/forbidden paths 和六类 locks。`PASS / FAIL / INVALID` 必须各有唯一后继，
所有直接后继已在 trusted base 的 `next_action_contracts` 中完整预注册 action/transition/locks；`project/current.md` 精确镜像 plan
revision/action/Case。迁移 Result 只允许 exact `plan_revision_ref`、`action_ref`、`verification_case_id`、`plan_gate_verdict`，禁止别名。

核对开发前 snapshot 与交付/合并前 `diff --base <trusted-base-ref>` 已列为必需 Gate；base action 而非 candidate Manifest 审核 diff。
计划修订必须预先绑定 Finding、accepted PDR 和 exact 用户授权，不能与成功 Result 同变更自授权。首次治理 cutover 只可包含治理、计划、
验证工具及其测试，不得夹带产品代码。任一项未闭合时 Readiness 保持 `proposed`。

## Architecture reflection gate readiness

核对 Proposal 已冻结关键假设、最早反证、成熟替代方案对照和反证后的动作；Manifest 为每个 Slice 恰好绑定一个
`V-REFLECT-NNN`。第一段必须优先验证最高风险架构假设，每个 Slice Result 必须形成独立复盘结论；没有 `CONTINUE` 决定和用户
再次授权时，后续 Slice 不得进入开发。
失败默认进入同一 Slice 的 `REWORK`。现有本地开发授权覆盖修复时保持该 Slice `authorized / in-progress / coding_input=true`；失败只
阻止 PASS、晋级与 hardening。只有 scope/Owner 变化、用户明确暂停或本地授权失效时才暂停。Proposal 必须冻结无进展定义和正整数尝试
上限；只有明确用户转向、核心架构证伪或达到该上限才允许 `REDIRECT`。
每段 Reflection 必须绑定 exact 用户决策消息收据；后续 Slice 的授权必须引用同一条前序 Reflection 决策消息，且不能复用更早
授权。四路 exact identity、独立 source-truth ledger、fresh 隔离任务、答案先密封、protocol/rubric/cache policy、严格答案质量
metric/unit/direction/正阈值/replay protocol 和独立裁决 Owner 必须在任何产品/Web 变更前的 freeze action 中冻结；完整 hidden 与跨工程
复验仍可后置到夯实阶段。调查步数与模型调用上限至少为 2，并结构化冻结 query/result 单步与总字节、总时长、Support、trace 和超限语义。

## Authorization continuity readiness

核对 Manifest 已把 Slice 本地开发授权、人类 `PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY@1`、系统派生 exact Authorized Input Manifest/
one-use disclosure/dispatch receipt 与一次性 scope-delta grant 分开。standing authority 必须冻结 canonical public source、许可/公开性记录、
revision selection policy、每次运行的 exact commit/tree、clean 状态、allowlist/只读披露、Provider/model/endpoint/credential account route、调用/重试/token/时长预算、调度、有效期/
撤销条件、结果保存、loopback `EVALUATION_ONLY` Sink 和 exclusions；source identity 不变时，不因新的 run、Conversation、Turn 或问题逐次
请求用户授权。

核对每次外部动作仍在网络和 credential 前生成回指 standing authority 的 exact machine receipt，且 receipt 不能创建或扩大权限；缺失、
失效、scope mismatch 或越界必须失败关闭。只有私有/来源或许可证未知/仅本机存在/dirty 数据、超出 approved upstream/revision selection policy/allowlist、
新外部接收方或 Provider/model/endpoint/credential account、预算增加、超出 fallback admission policy 的调度范围或需要一次性 override、外部写入、
非 loopback 暴露、Production Activation
或其他 exclusion 才提交最小 exact delta request。pending delta 不得重复，批准后
自动续跑，等待期间继续全部独立安全工作。

开发回合退出条件必须收窄为阶段交付、actual scope-delta request 已发出且独立安全工作穷尽、用户明确 `STOP/REDIRECT/REJECT`，或不可绕过的
安全禁止。`WAITING_EXACT_GRANT` 必须同时保持 `IN_PROGRESS`；“需要授权”、局部 Gate PASS/FAIL 或 timebox FAIL 本身不是退出条件。

## Fallback route dispatch admission readiness

核对 Manifest 已冻结 fallback execution profile 以及它引用的 admission plugin/Case/receipt schema。该硬门禁必须覆盖所有 planned fallback-route
probe、Conformance、Capability、canary、fallback、Web 体验、比较和回归；run receipt 与逐 request 准入条件/一次性 exact override 重验必须
早于 Provider socket/connected descriptor、TLS、credential 和 HTTP。冻结 plugin identity/configuration digest、trusted input（如时钟与时区）、
exact route identity、calls/tokens/duration、完整最坏质量链、override bounds、零计数失败语义和 `V-FALLBACK-ROUTE-ADMISSION-NNN`。Provider
qualification、fallback eligibility、standing development/canary/route authority 均不能替代 admission plugin verdict，也不能推出 override；政策范围内调用则不得再逐 run 申请用户授权。
等待准入必须继续 preferred-route-only 和本地工作；当前 runtime 若缺少机械门禁，Readiness 必须明确只阻断 fallback-route 外部分派，不撤销本地 Slice
coding input。通用模板不得写死 Provider/model 名称；具体名称只能出现在当次 execution profile 配置和执行收据中。

## Outcome, scope and non-goals

## System contracts and unresolved decisions

## Slice, dependency and risk closure

核对第一个活动 Slice 先以零外部调用、零产品代码 freeze 并执行四路严格方向 Gate；只有 Gate PASS 才解锁明确标注、小而多样的非验收
可体验 Alpha，并由用户实际使用后判向。全面契约、回归、性能、
资格和正式验收只能放在 Alpha `CONTINUE` 之后。早期真实运行仍需闭合安全、权限、Secret、外部披露和失败真实性；除此之外的加固
不得被误列为 Alpha 的阻断。

核对首个体验 Slice 交付可重复启动、固定本地地址、版本和限制可见、单题失败不关闭服务的真实版本，而不是一次性验证运行。若声明
Chat，还必须冻结 Conversation/Turn/Context、追问、纠正、总结、逐轮证据/审核和新对话隔离；仅共享 Session Authority 不算 Chat。

核对主工程 Agent 拥有用户目标、假设、计划、上下文选择、工具选择、观察解释、重规划、完成判断和自然答案综合；平台继续拥有 exact
版本、授权、只读工具执行、证据身份、预算与审计，独立 Reviewer 继续阻断错误。不得把模型 hidden memory、用户陈述或旧答案写成事实权威。

同时核对输入持有者、独立技术评测方和用户方向决策者是不同职责：独立评测先裁决正确性、完整性、Citation、边界和特判；用户只根据
已复核且限制可见的真实结果决定 `CONTINUE / REWORK / REDIRECT / REJECT`。

同时核对 current Codex 和直接相关证据都不是 Oracle 或 adjudicator；四路答案相互不可见并先密封，评测方未参与任一答案生成，只依据
独立 exact source ledger 匿名裁决。第 2/3 路除世界模型认知外固定同一 Agent/Prompt/tools/budget/cache/Reviewer，用同一 Gate 完成因果归因。

## Verification readiness

## Authorization decision

只有明确授权后才把 `status` 改为 `accepted`，填写非 `pending` 的 `authorized_by` / `authorized_at`，再更新 Iteration、Slice 与
`project/current.md` 的 plan revision/action/Case 镜像。本记录不能自行推定用户授权，广义 Slice `coding_input=true` 不能放宽 action allowlist。
