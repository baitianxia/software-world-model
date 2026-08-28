---
id: PROJECT-GOVERNANCE-PLAN-EXECUTION
kind: project-governance
status: current
authority: project-governance
owners: [project, engineering, quality]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, PROJECT-GOVERNANCE-DEVELOPMENT-DESIGN, PROJECT-GOVERNANCE-VERIFICATION]
code: [.githooks/plan-pre-commit, scripts/docs.py, scripts/plan_gate.py]
tests: [tests/test_docs_gate.py, tests/test_plan_gate.py]
---

# 开发计划机械执行门禁

## 目的

自然语言计划只能解释意图，不能阻止实现者扩大范围或把候选计划写成自己的授权。机械门禁只负责执行少量高价值边界：当前做什么、
哪些路径可以改变、能否调用外部系统、哪些安全锁仍然生效，以及什么时候可以把游标交给下一动作。它不能把开发拆成行政动作迷宫，也
不能把“收据齐全”冒充产品方向正确。

## 唯一长运行动作

采用 `DEVELOPMENT_PLAN_EXECUTION_CONTROL@1` 的 Manifest 必须且只能有一个 `current_action`。它至少绑定：

- 计划修订、活动 Slice、Verification Case、动作类型和状态；
- 是否允许产品编码和外部执行；
- 允许与禁止变更的路径；
- 始终锁定的 hardening、full regression、Production 和未授权外部范围；
- 体验交接时唯一 Result/evidence 路径，以及交接 Verdict 对应的后继动作。

首次缺少代表性 MVP 时，`current_action` 应是一个完整体验开发动作。它可以跨多个普通提交、定向测试、局部失败、根因诊断和通用修复
持续运行，直到完整用户主链可交接或出现真正需要停止的安全/权限边界。普通失败留在同一动作：保留原输入、输出、证据、最早偏差、
downstream guard failure、根因假设和反事实验证，但不按每次失败、提交、测试或外部调用生成 Result，不移动游标。

`PROJECT-CURRENT` 必须复制计划修订、动作 ID 和 Case ID，并与 Manifest 精确一致。活动 Slice 的广义 `coding_input=true` 不能覆盖
动作级路径白名单；候选 Manifest 不能授权自己的 diff。

## Result 与状态转换

Result 是体验交接或计划游标迁移的密封收据，不是开发过程日志。只有当前动作达到以下任一交接点时才生成唯一 Result：

- 完整可体验主链已经按当前 Case 交给用户；
- 用户在体验和独立质量比较后作出方向决定；
- 当前 scope 确实需要改变，必须迁移到新的治理动作；
- 不可绕过的安全禁止或用户明确 `STOP / REDIRECT / REJECT` 结束当前动作。

前进一步必须由 trusted base Manifest 预注册后继，并同时满足：当前动作指定的 Result/evidence 已生成；证据经 base 已冻结的轻量 verifier
验证；Verdict 与后继一致；候选 diff 未越过 base 路径白名单和锁。Result 必须绑定动作、Case、subject/execution identity、实际执行计数和
Verdict；外部动作还要聚合逐 dispatch runtime receipt。历史 sealed Result 保持不可变，但不得反向要求它补造后来新增的字段。

失败证据可以在动作工作目录和最终交接 evidence 中聚合。`FAIL` 只阻止 PASS、晋级与 hardening，不自动撤销当前产品编码权；只要 scope、
Owner、架构目标和安全边界不变，就在同一动作先归因最早责任层，再做一次通用修复和定向复验。`INVALID` 先修复输入、身份、盲化或
执行完整性。任何 Verdict 都不得授权针对单题表象堆 Prompt、关键词或特殊规则。

## 轻量 evidence verifier

交接 evidence 使用与动作规模相称的自包含 runner。runner 只验证本次交接的核心事实，例如：

- 完整主链、浏览器入口、语义多轮、新对话隔离和失败真实性是否实际成立；
- 异质问题、未参与开发的问题、current Codex 强基线、独立评审和非 locator 世界模型贡献是否达到冻结阈值；
- 普通失败是否完成分层根因归因和通用修复，而不是单题碰答案；
- 首次体验前是否只运行 targeted impact、startup 与 safety 测试，`full_regression_run_count` 是否为零；
- 每个真实外部 dispatch 是否有回指 standing authority 的 exact runtime receipt，Secret 是否只通过 Reference 使用。

runner 与其验证的 Result 不能在同一提交中引入；trusted gate 从 base 读取 runner 并以 evidence 原始 bytes 重放，候选 runner 不能自签。
但门禁不得要求对整个 Manifest、每个仓库文件或每个中间工件维护人工摘要，也不得用数千行 verifier 重建一套产品状态机。摘要只绑定
真正影响交接身份和证据真实性的工件。

若交接 Result 声称执行了外部模型，外部调用、Provider dispatch 和 HTTP dispatch 计数必须与逐次 runtime receipt 一致；未执行则如实为
零。首次体验前 `full_regression_run_count` 必须为零。质量失败不能伪称网络失败，`OUTCOME_UNKNOWN` 不能改写成 PASS 或确定 FAIL。

## 安全与权限边界

以下边界在长运行动作中始终机械执行，不能后置：

- 只访问 Manifest 允许的 active Slice/path；源码访问保持授权范围内只读；
- Secret 只通过 Secret Reference 解析，不写入仓库、日志、Prompt 或 Result；
- 外部执行必须落在 active standing authority 的 source、revision policy、receiver route、预算、调度与 Sink 范围内；
- 每次真实 dispatch 前生成 one-use exact runtime receipt，并冻结 source/product/session/turn/route/disclosure/budget；receipt 只证明符合既有
  权限，不能创建或扩大权限；
- 只有 scope delta 才申请新的人类授权；同一公开开源、clean、allowlisted、只读 standing scope 内的新问题、Turn 或 run 不重复申请；
- hardening、full regression、跨工程、hidden、性能和 Production 在用户体验与质量决定 `CONTINUE` 前保持锁定。

Activation Result、分钟级时间盒收据、迟到即非法、每次失败单独动作、Build/Live/Quality/Attribution/Repair/Recheck 链和 rotating governance
slot 都不是通用合法性条件。进度应频繁对用户可见；长时间没有可见增量时停止扩域与无证据重跑、回到根因和主链收敛，但不让人工时钟
使仍在范围内的开发自动失权。

## 两类检查

- `python3 scripts/docs.py check` 校验当前树的文档引用、唯一动作、活动 Slice、Current 镜像、路径与锁一致性。
- `python3 scripts/plan_gate.py diff --base <git-ref>` 用 trusted base 校验候选 diff 没有自扩权；只有发生 Result 交接/游标迁移时，才额外重放
  evidence verifier 并校验单步后继。

首次启用或修订计划只允许治理 cutover，禁止夹带产品代码。cutover 后，产品开发可在同一个 current action 中形成多个小提交；这些提交
只需持续满足 base action 的路径、权限和锁，不要求每个提交产生新 Result。一个 Product Result 只在体验交接时密封。

本地开发仓库应安装 `.githooks/plan-pre-commit`，用 trusted `HEAD` 的 gate 检查暂存 diff；远端 CI 仍应在候选代码执行前进行 trusted-parent
检查。二者防止普通误操作和候选自扩权，但没有远端不可变 required workflow/ruleset 与独立签名时，不得声称管理员绝对不可绕过。

紧急安全事件可以停止动作。需要改变计划时，先形成 Finding、Project Decision 与明确用户授权引用，再由一个治理 cutover 提交修改计划；
不得把候选产品代码与自授权计划混在同一提交。

## 冻结 verifier 表达能力恢复

如果当前动作已经达到文档规定的终止/交接条件，但 frozen verifier 无法表示实际证据，且填写其必填字段会伪造未发生的产品输出，则先停止
产品修改和外部执行并形成 Finding。若该 verifier 同时阻止动作进入预注册 governance action，普通 Result 与 plan revision 因而形成机械自锁，
可以在用户对 exact 最小差量作出明确授权后执行一次 trust-root recovery，但必须同时满足：

- 绑定 exact trusted base commit/tree、fresh 一次性用户消息内容引用和 forward-only PDR；
- 明确声明 recovery commit 不冒充被中断动作或旧 gate 合规；
- 只修改治理、Manifest、冻结 runner 及其定向测试，不夹带产品代码、Prompt、Provider 调用或 Result；
- coding、external execution、Web、hardening、full regression 和 Production 全部锁定；
- runner 先独立提交成为新 trusted parent，后续提交才可生成并密封 Result；
- machine PASS 只证明新 failure-handoff 包的结构、identity、digest 和执行计数闭合，不得追认缺失的 Answer、Citation、Review 或语义质量。

新计划设计应给每个外部/产品长动作预留不依赖该动作待验证 Result 的治理恢复入口。该入口只解决 verifier 或计划表达能力错误，不得成为普通
失败、质量不通过、未完成开发或扩大 scope 的旁路。
