---
id: ITER-010-RESULT-V-USER-DIRECTION-DECISION-001
kind: iteration-result
status: sealed
authority: evidence
owners: [product, project, architecture, engineering, quality]
depends_on: [ITER-010-PDR-011, ITER-010-RESULT-V-MVP-EXPERIENCE-001, ITER-010-VERIFICATION]
code: [validation/iteration_010_mvp/value_gate/runner.py]
tests: [tests/test_iteration_010_mvp_value_gate.py, tests/test_plan_gate.py]
iteration: ITER-010
plan_revision_ref: ITER-010-PDR-011
action_ref: ITER-010-ACTION-USER-DIRECTION-DECISION-001
verification_case_id: V-PREVIEW-002
plan_gate_verdict: PASS
evidence_schema: DEVELOPMENT_PLAN_GATE_EVIDENCE@1
evidence_verifier: ITER010_MVP_LIGHT@3
evidence_artifact_path: docs/project/iterations/iteration-010/results/evidence/v-user-direction-decision-001.json
evidence_artifact_digest: sha256:b5ec4a5599b3bdac7fba44f3d426c43dbd895bc9d31c23f3b7fecb2c31150023
execution_input_digest: sha256:ee9ddd15fccfe67255ba9df30368c65b114c204482de0f31eec5409a42c70ced
runner_identity_digest: sha256:bb9006ae25b9d24de42c7fdaa14f142dfb9eb8f1a1d80ced08c040479bd55087
runner_receipt_digest: sha256:4488906fdb5227a99a2323b483991df0c58c4e7c391a9e064c676db6023e4296
verification_report_digest: sha256:888ed4bb6054a5aaed27d32f2eac8cf5cbf4e55385d8516a55ebc351a13ebfd0
subject_digest: sha256:ad90f60931b1c252a72d7881278c98910cf3e9d5856167cdc74c0efbf43971dd
external_model_call_count: 0
---

# ITER-010 用户方向记录

## 决定

`V-PREVIEW-002: PASS / REWORK`。

用户要求把重点放回完成产品目标且不偏离目标，并停止把主要精力投入阻塞开发的门禁。该决定不是接受现有失败候选，也不是进入工程
夯实；它要求在同一 `ITER-010 / SLICE-001` 内恢复产品开发，先形成真实可体验的浏览器 Chat，再以实际体验纠偏。

## 边界

- 本记录没有执行产品代码、模型调用、网络、凭据解析、全量回归或生产动作，所有计数均为零。
- PDR-011 的冻结 verifier 仍把本记录描述为“不直接解锁后续工作”；这只是旧计划转换格式，不是后续计划的长期授权模型。
- 后续计划修订必须把持续有效的授权边界与可调整的工作计划分开：范围内任务调整不得再次申请人工授权，只有真实 scope delta 才需新权限。

## 后继

下一份计划修订只负责重新打开同一 Slice 的产品开发并删除计划自锁；不得借此增加新的 verifier、收据状态机或产品外工作。
