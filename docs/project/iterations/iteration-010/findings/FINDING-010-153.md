---
id: FINDING-010-153
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [project, engineering, quality]
depends_on: [PROJECT-GOVERNANCE-PLAN-EXECUTION]
code: [scripts/docs.py, scripts/plan_gate.py, validation/iteration_010_plan_recovery/value_gate/runner.py, validation/iteration_010_mvp/value_gate/runner.py]
tests: [tests/test_docs_gate.py, tests/test_plan_gate.py, tests/test_iteration_010_plan_recovery.py, tests/test_iteration_010_mvp_value_gate.py]
iteration: ITER-010
classification: iteration-design
scope: systemic
disposition: replace-unreachable-action-maze-with-long-running-mvp-experience-action
target: ITER-010-PDR-010
---

# FINDING-010-153：执行图缺少用户主动改计划的治理出口

## Observation

用户在 `ITER-010-PDR-009 / ITER-010-ACTION-DIRECTION-FREEZE-001` 尚未执行时重新定义了 MVP：Web 页面本身不是 MVP，最早应形成的是包含软件世界模型认知、
主工程 Agent、受控源码补证、证据与独立审核、语义多轮 Web 的完整纵向候选；首次严格方向比较应验证同一个已可体验候选，而不是先建设
比较基础设施再形成产品，完整四路因果消融则在用户确认方向后执行。

现有动作图没有从 Freeze 到治理计划修订的可达路径。`scripts/plan_gate.py` 又正确要求只有已密封 PASS Result 的 governance action 才能修订计划，导致用户明确改变计划后，
仓库既不能合法继续旧动作，也不能合法接受新计划。这是计划执行机制的活性缺陷，不是产品实现或模型配置问题。

## Evidence and root cause

- 当前 PDR-009 动作的 PASS/FAIL/INVALID 只通向 Quality、Freeze Rework 或自身，均不能表达“用户中断旧图并改变计划”；
- governance action 只在 Quality 或 Web 已执行后的分支中可达，因而无法处理执行前或执行中的新用户方向；
- 候选 Manifest 不能授权自己的计划修订，这是必要安全边界，因此不能用普通候选改动绕过；
- 用户另行授权一次治理恢复，授权消息的本地 UTF-8 引用是
  `local-user-message-utf8:sha256:6cf2531ab1119b67ad2010040ae1ac73f817785684fccc26111b3b70ef5fcbe5`。该授权只允许恢复计划治理活性，不允许产品代码或外部执行。

根因是动作图只建模运行结果，没有把 fresh 用户方向变更建模成可机械验证、不可伪造业务 PASS/FAIL 的治理中断。

## Disposition

一次性 `V-PLAN-RECOVERY-001` 已以零产品、零外部调用恢复采纳 PDR-010 的治理能力。该 Result 只证明两条用户消息和治理边界得到可信父 runner
重放；它没有生成、验证或解锁产品，产品执行权威来自随后独立提交的 PDR-010 与 Manifest。旧 Freeze 与未跟踪旧 runner 继续保持
`INTERRUPTED / QUARANTINED / NOT_INPUT`。

PDR-010 以一个可跨提交持续运行的“完整体验版开发”动作取代 Freeze/Quality/Activation 动作迷宫；普通失败留在同一动作内归因和修复，形成
完整候选或确认无法继续碰答案时才密封一次 Result 并进入用户方向决定。用户改变方向由这个显式方向分支和后续独立 PDR 处理，不再为每个动作
预注册 rotating slot、分钟收据或整份 Manifest 摘要。可信父差分、动作级文件边界和 Result 绑定继续防止候选自授权。
