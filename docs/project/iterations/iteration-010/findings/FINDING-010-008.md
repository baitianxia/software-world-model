---
id: FINDING-010-008
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, quality, security]
depends_on: [ITER-010-SLICE-001, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING]
code: [src/software_world_model/application_services/engineering_question_answering.py]
tests: [tests/test_engineering_question_answering.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: recheck-wall-time-after-every-untrusted-role-worker-and-projector-boundary-before-accepting-state
target: src/software_world_model/application_services/engineering_question_answering.py
---

# FINDING-010-008：wall-time 熔断不能只在外部调用前检查

## Observation

Slice1 状态机原先主要在角色、Cognition Projector 或 Worker 调用前检查 wall-time。若一个 Investigation 角色恰好在 deadline 返回
`FINISH`，或 Reviewer 恰好在 deadline 返回 `APPROVED`，Application 仍可能接受该输出并密封 Package 或授权答案。调用本身已消耗完
预冻结预算，但其返回值取得了超时后的状态转换权。

## Evidence and root cause

- deadline 前进入角色调用、返回时 elapsed time 等于上限的 fixture，原实现会记录 `FINISH`；
- Reviewer 在同一边界返回 `APPROVED` 时，原实现仍可形成 delivery authorization；
- Question Understanding 或 World Model Projector 也可能在返回后已经耗尽预算，却继续创建下游 Ledger；
- 根因是 wall-time 被当作“是否允许开始调用”的检查，而规范语义是“达到上限即失败关闭”，所以任何不可信或潜在慢边界返回后都必须在
  接受结果前重新检查。

该问题影响所有问题和角色，但不改变现有预算 Owner、数值或失败语义，分类为 `local-implementation / systemic`。

## Decision and disposition

- 所有角色、Cognition Projector 和 Worker 返回后，在接受 Proposal/Result、追加 Ledger、密封 Package 或签发 Answer Authorization 前
  重新计算 elapsed wall time；
- deadline 比较统一为 `elapsed >= maximum`，达到上限即耗尽；
- Understanding/Projector 尚未产生 Ledger 时抛出 `BUDGET_EXHAUSTED`；调查、Answer 或 Review 已进入状态机时形成可审计的
  `FAILED_CLOSED` Result，且不记录超时后 `FINISH`、不授权超时后 `APPROVED`；
- 不增加 retry、fallback 或补偿调用。

处置只进入 Application 和确定性测试，无需改变 System Contract；契约已经拥有达到安全上限失败关闭的语义。

## Verification

测试分别冻结 Understanding、Investigation `FINISH` 与 Review `APPROVED` 恰好在 deadline 返回，验证 cognition/下游调用、FINISH
entry 和 delivery authorization 均不会发生；既有正常预算、角色保留和完整状态机测试继续通过。
