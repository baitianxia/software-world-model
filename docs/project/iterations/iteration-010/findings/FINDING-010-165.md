---
id: FINDING-010-165
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [project, quality, engineering]
depends_on: [FINDING-010-164, ITER-010-PDR-011]
code: [scripts/plan_gate.py]
tests: [tests/test_plan_gate.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: distinguish-sealing-action-authority-from-historical-runtime-reconciliation
target: scripts/plan_gate.py
---

# FINDING-010-165：通用 plan gate 把历史调用对账误判为当前治理动作外调

## Observation

`ITER010_MVP_LIGHT@3` 已对 run-052/053 的真实 failure packet 独立 PASS，但首次执行候选 trusted-parent diff 时，通用
`validate_gate_result` 返回 `non-external action evidence must report zero external execution counters`。其连带后果是
`V-MVP-EXPERIENCE-001` 的精确 Result 无法被解析为机械 PASS，方向动作的 prerequisite 也被拒绝。

PDR-011 当前 sealing action 的 `external_execution_allowed=false` 表示该治理动作不得发起新的 Provider 调用；Result 中的 19 次 Ark
dispatch/credential/TLS/HTTP 则是 PDR-010 product candidate 已发生运行的历史对账。通用 gate 把这两个时间与责任域不同的事实当成同一
计数语义。把计数改为 0 会篡改运行证据，打开当前 action 的 external execution 又会错误扩权。

## Classification

这是 plan gate 的系统性治理工具实现缺口，不是产品、Provider、route 或 evidence byte 错误。当前修正前后新增 Provider/browser dispatch
均为 0；run-052/053 与 `QUALITY_FAIL_AFTER_ONE_GENERAL_REPAIR` 保持不变。

## Disposition

- 只对 exact `ITER-010-ACTION-USER-PLAN-RECOVERY-001 / V-MVP-EXPERIENCE-001 / mvp-failure-handoff /
  ITER010_MVP_LIGHT@3` 且 action evidence schema 为 `ITER010_MVP_FAILURE_HANDOFF_PACKET@3` 的 structural PASS，允许非零历史 external
  reconciliation counters。
- 该窄分支仍要求 `coding_allowed=false`、`external_execution_allowed=false` 与 `full_regression_run_count=0`；@3 trusted-parent runner
  继续验证完整 packet、19/0 Provider 对账和所有 digest。
- 其他 non-external action、错误 packet schema、用户方向 action 或非零 full regression 继续失败关闭；新增正反向测试固定该边界。
- `scripts/plan_gate.py` 属于 Result runner identity，故本修正必须先于 Result 单独提交成为新的 trusted parent，再重建 evidence/Result
  digest。它不密封 Result，也不移动计划游标。

该修正属于用户已授权的同一最小 governance recovery；不扩大到产品代码、Prompt、Provider、Web 或 full regression。
