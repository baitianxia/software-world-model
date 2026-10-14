---
id: PROJECT-CURRENT
kind: project-current
status: current
authority: current-development
owners: [project]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, PROJECT-GOVERNANCE-DEVELOPMENT-DESIGN, PROJECT-GOVERNANCE-PLAN-EXECUTION, ROADMAP-M-002, ITER-010-INDEX, ITER-010-SLICE-001, ITER-010-PDR-012, ITER-010-PDR-014, FINDING-010-256, FINDING-010-257, FINDING-010-260, FINDING-010-261, FINDING-010-262, FINDING-010-263, FINDING-010-264, FINDING-010-265, FINDING-010-266, FINDING-010-269, FINDING-010-270, FINDING-010-273, FINDING-010-274, FINDING-010-275, FINDING-010-276, FINDING-010-277, FINDING-010-278, FINDING-010-279, FINDING-010-280, FINDING-010-281, FINDING-010-282, FINDING-010-283, FINDING-010-297, FINDING-010-298, SYS-ADR-018, SYS-ADR-020, SYS-ADR-021]
code: []
tests: []
as_of: 2026-10-11
active_iteration: ITER-010-INDEX
active_slice: ITER-010-SLICE-001
worktree_status: development-candidate-dirty
strategy_relation: dual-core-world-model-cognition-and-conversational-lead-engineering-agent
live_model_path: preferred-execution-profile-first-fallback-only-on-trusted-unavailability
plan_revision_ref: ITER-010-PDR-012
execution_decision_ref: ITER-010-PDR-014
execution_plan_ref: ITER-010-EXECUTION-PLAN-CURRENT
plan_shape: USER_VALUE_VERTICAL_SLICE@1
current_task: TASK-1-MINIMUM-COMPLETE-EXPERIENCE
readiness_status: READY
next_action: ITER-010-ACTION-USER-DIRECTION-DECISION-001
next_action_case_id: V-BROWSER-CHAT-MVP-BUILD-001
---

# 当前工作上下文

## 当前结论

### 入口字段的唯一解释

`plan_revision_ref: ITER-010-PDR-012` 只表示本轮仍沿用的 standing authority；它不是任务顺序。
`execution_decision_ref: ITER-010-PDR-014` 表示当前决策边界；`execution_plan_ref:
ITER-010-EXECUTION-PLAN-CURRENT` 才是唯一的开发顺序和当前任务来源。Proposal、Readiness、Verification、PDR
正文中的旧阶段、旧运行记录和旧协议只能作为历史证据，不能生成新的任务顺序或前置门槛。

状态只保留一套机器控制：Manifest 的 `plan_execution_control.current_action`、`locks` 和授权布尔值；本页的
`next_action`、`next_action_case_id` 与任务计划中的 `current_task` 是该控制的必要镜像，不是第二套开关。不开新建
`execution_mode`、状态转换表或监督状态；本轮按当前 action 执行 TASK-1，不改变授权范围。
迭代总索引中的旧状态行仅作历史导航，不是当前状态来源；当前状态以本页、引用的执行计划和对应 Manifest 为准。

ITER-010 的产品目标和总体架构不变，但任务拆分已改为面向用户价值的单一纵向主线。Git 投入审计证明过去 186 个提交主要增长了回答、审核
和输出协议，知识引擎没有获得相称投入；因此不得继续把旧模型边界、正文证明协议或逐题修复当作产品主线。

当前唯一产品任务是 `TASK-1-MINIMUM-COMPLETE-EXPERIENCE`，当前正在执行。在一个真实精确版本工程上同时贯通最小软件世界模型、Provider 透明 Agent、源码补证、
自然答案、真实 Citation、fresh 独立复核和持续浏览器 Chat。它是方向体验出口，不冒充最终 MVP；必须先交付它，再进行异质问题判向和后续夯实。

旧的 Phase A/B/C/D、C0/C1/C1.5/C2/C3/C4、N0/N1/N2/N3 只保留为历史或验收背景，不再作为当前任务顺序。当前执行顺序唯一见
`ITER-010-EXECUTION-PLAN-CURRENT`。

默认入口接入主 Agent、验证工程准备、Provider 现场验证和首条真实浏览器闭环属于该任务的实现或运行准备，不能倒置成开始实现的前提。

历史 Proposal、PDR、Verification 和 Finding 中出现的箭头只记录当时的验证、归因或交付语境，不是当前运行时链路。当前运行时唯一有效的
关系是 Agent 主导的可往返循环：世界模型与精确版本只读源码是并列证据路径，Reviewer 的缺口可以反馈回同一 Agent，Chat 负责承载和呈现结果。

PDR-012 继续拥有可信 standing authority 和 Manifest 兼容 action；PDR-014 只在其范围内替换执行路线。Manifest 中的
`ITER-010-ACTION-USER-DIRECTION-DECISION-001 / V-BROWSER-CHAT-MVP-BUILD-001` 保留为当前兼容 action 身份，不新增第二套执行游标。

本轮讨论进一步明确运行分工：软件世界模型是指定版本工程的结构、关系、行为、边界、覆盖范围、来源和检索入口组成的系统认知，不是文字手册或
答案库；Agent 负责理解问题、自适应选择认知和源码证据、组织答案及处理追问；模型负责推理与表达；源码是最终事实依据。World Model + source
优于 source-only 是必须用同一 Agent 的成对实验验证的产品假设，不能预先宣称成立。认知覆盖不足时必须降级到通用源码检索，不能用错误导航候选
或固定动作替代事实。

## 唯一开发入口与下一动作

当前执行顺序唯一见 `ITER-010-EXECUTION-PLAN-CURRENT`。该执行卡只保留四项用户价值任务：最小完整体验、方向与归因验证、通用能力增量、MVP
夯实验收。旧 Proposal/Readiness/PDR 中的阶段和历史 Finding 不得重新生成另一套前置顺序。

- 唯一开发分支：`codex/development`；唯一监督分支：`codex/supervision`；`main` 只接收已验收成果。
- 其他本地开发分支全部转换为 `archive/branches/*` 标签后删除。旧临时工作树和 dirty candidate 只作恢复来源，不再作为开发或监督目标。
- 当前 `codex/development` 的 HEAD 是已提交的文档基线；当前工作树是 TASK-1 的开发候选。原始候选变更保存在
  stash `654e1e6de26aa749850bddef7eeb5738287e5b4f`，被忽略的 `var/` 运行产物另存于 `/private/tmp/software-world-model-iter010-ignored-var-20261007.tar.gz`
  和 `/private/tmp/software-world-model-iter010-var-20261007`；它们只能作为恢复来源，不能作为当前开发或监督目标。
- 内部实现可以并行，但只能由端到端结果合并验收；配置、Provider 收据、监督、定向测试和报告不再是浏览器体验的前置任务。
- 最小可操作闭环形成后立即交付 loopback 地址、启动方式、精确版本、已知限制和可复现问题；不等待 Codex、全量回归、隐藏题或工程夯实。
- 方向判定使用同一 Agent 的 source-only 与 World Model + source 两臂；只有方向成立后才进入多问题、多轮、Codex 比较和正式夯实。
- `next_action: ITER-010-ACTION-USER-DIRECTION-DECISION-001` 是机器兼容标识，不表示等待用户决定；在当前 standing scope 内，开发任务无需逐次授权，实际顺序只看 `TASK-1` 至 `TASK-4`。
- 普通失败按最早责任层修复：先区分 Source truth、World Model 认知、Agent 规划与工具使用、Evidence/Answer、Review 或 Web 呈现的偏差，
  再做一次通用修复；这些是诊断层次，不表示运行时必须按这个顺序执行，也不回写题面规则。

监督协议要求在每次 HEAD/工作树/运行证据变化以及最长 30 分钟间隔检查，并同时写入 heartbeat 和独立 assessment。
当前仓库没有内置定时器或开发分支 CI；Codex heartbeat `iter-010` 已创建但已按用户停止要求暂停，当前状态为
`SUPERVISION_UNVERIFIED`。它只监督开发准备，不启动开发、不发送 Provider 请求、不修改代码；在用户重新允许并完成首次运行确认前，不得宣称监督已经生效。
目标分支、工作树或 baseline 不匹配时，只修复监督绑定，不能把开发误判为完成、暂停或重新授权。

时间上限只触发自动简化或换实现，不触发暂停、失败 Result、重复授权或质量降低。第一个可操作候选立即交付；full regression、hidden、
跨工程、性能和工程化只在用户确认方向后开始。

## 开发纪律

- 旧 `conversational_engineering_model.py` 及其测试在 MVP 前只可缩减或薄适配，净行数不得增长；不得新增协议版本或正文词法语义校验。
- Prompt/Schema 变化必须先有分层 trajectory 和替换实验，证明最早偏差确在模型交互层；否则不进入候选。
- 知识、Agent、集成和最终答案分别出证据。只增加 Docs/Test/Prompt/Schema 时状态为 `NO_PRODUCT_PROGRESS`，开发自动回到最早缺失能力。
- 每次通用修复同时复验原失败和两个异质未参与问题；只改善原题时必须换责任层或实现策略。
- 普通答案、测试、Provider 或网络失败不停止开发。首选执行配置成功时不运行备用；只有可信不可用结论才透明回退。
- 受信证据确认 HTTP/model dispatch 为 0 的临时 Provider 失败必须按 5/15/30 分钟 fresh logical-run cadence 自动重试；不等待用户、不重复
  授权、不重放同一请求。post-dispatch outcome unknown 继续禁止 replay。

## 授权与边界

现有公开 mall exact revision、只读 Source、既有执行配置、披露、预算和 loopback evaluation 继续位于 standing authority 内。同范围的新
Conversation、Turn、问题、候选、定向测试和外调不重复申请授权；每次外调仍自动生成 exact runtime record。只有私有/新 Source、新接收方
或账户、扩大披露/预算、外部写入、非 loopback、Production 或破坏性操作才属于 scope delta。

持续授权范围：`AUTHORIZED / NON-PRODUCTION`。本轮已进入 TASK-1 产品开发；Provider 外调和监督仍按任务内真实运行条件处理，不把历史收据当作本轮结果。
