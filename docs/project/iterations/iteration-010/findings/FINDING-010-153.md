---
id: FINDING-010-153
kind: implementation-finding
status: open
authority: development-evidence
owners: [project, engineering, quality]
depends_on: [ITER-010-PDR-009, PROJECT-GOVERNANCE-PLAN-EXECUTION]
code: [scripts/docs.py, scripts/plan_gate.py, validation/iteration_010_plan_recovery/value_gate/runner.py]
tests: [tests/test_docs_gate.py, tests/test_plan_gate.py, tests/test_iteration_010_plan_recovery.py]
iteration: ITER-010
classification: iteration-design
scope: systemic
disposition: pending
target: pending
---

# FINDING-010-153：执行图缺少用户主动改计划的治理出口

## Observation

用户在 `ITER-010-PDR-009 / ITER-010-ACTION-DIRECTION-FREEZE-001` 尚未执行时重新定义了 MVP：Web 页面本身不是 MVP，最早应形成的是包含软件世界模型认知、
主工程 Agent、受控源码补证、证据与独立审核、语义多轮 Web 的完整纵向候选；严格四路比较应验证同一个已可体验候选，而不是先建设比较基础设施再形成产品。

现有动作图没有从 Freeze 到治理计划修订的可达路径。`scripts/plan_gate.py` 又正确要求只有已密封 PASS Result 的 governance action 才能修订计划，导致用户明确改变计划后，
仓库既不能合法继续旧动作，也不能合法接受新计划。这是计划执行机制的活性缺陷，不是产品实现或模型配置问题。

## Evidence and root cause

- 当前 PDR-009 动作的 PASS/FAIL/INVALID 只通向 Quality、Freeze Rework 或自身，均不能表达“用户中断旧图并改变计划”；
- governance action 只在 Quality 或 Web 已执行后的分支中可达，因而无法处理执行前或执行中的新用户方向；
- 候选 Manifest 不能授权自己的计划修订，这是必要安全边界，因此不能用普通候选改动绕过；
- 用户另行授权一次治理恢复，授权消息的本地 UTF-8 引用是
  `local-user-message-utf8:sha256:6cf2531ab1119b67ad2010040ae1ac73f817785684fccc26111b3b70ef5fcbe5`。该授权只允许恢复计划治理活性，不允许产品代码或外部执行。

根因是动作图只建模运行结果，没有把 fresh 用户方向变更建模成可机械验证、不可伪造业务 PASS/FAIL 的治理中断。

## Temporary disposition

本次建立一次性 `ITER-010-ACTION-USER-PLAN-RECOVERY-001`。它保持所有执行锁关闭，先独立提交自包含 runner，再由下一提交密封恢复 Result；恢复 PASS 只允许后续独立
PDR-010 修订，不直接授权产品或外部调用。旧 Freeze 与未跟踪旧 runner 均为 `INTERRUPTED / QUARANTINED / NOT_INPUT`。

最终处置必须由 PDR-010 完成：除修订 MVP 顺序外，还要为以后每个动作预注册可轮换、不可复用的 fresh 用户方向治理出口，防止再次发生同类死锁。
