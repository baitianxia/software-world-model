---
id: FINDING-010-162
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [project, quality, engineering]
depends_on: [FINDING-010-161, ITER-010-PDR-010]
code: [scripts/plan_gate.py, validation/iteration_010_mvp/value_gate/runner.py]
tests: [tests/test_plan_gate.py, tests/test_iteration_010_mvp_value_gate.py]
iteration: ITER-010
classification: iteration-design
scope: systemic
disposition: stop-before-result-and-require-forward-governance-revision
target: ITER-010-SLICE-001
---

# FINDING-010-162：冻结 handoff verifier 无法表达答案生成前的失败分支

## Observation

`ITER-010-PDR-010` 允许两种最终 handoff：完成三条异质问题与 current Codex 比较，或一次通用修复和原失败加两个异质复验后同类重大失败仍存在。
`FINDING-010-161` 已满足后一停止条件，但冻结 `ITER010_MVP_LIGHT@2` 只接受“已有三个完整系统答案”的包，无法诚实表示当前
`AGENT_MODEL_CALL_REJECTED` 前答案失败。

具体冲突如下：

- `_validate_questions` 无条件要求至少三条问题、三个固定 category，并要求每题恰好引用 `system-answer`、`current-codex-answer`、
  `independent-review` 和 `question-comparison` 四类附件；
- `system-answer` 无条件要求非空 `citation_labels`，且每个 label 必须解析到 mall exact source-truth citation；当前失败 Turn 没有授权
  Answer、Citation、Package 或 fresh Review，填写这些字段会伪造产品输出；
- browser capture 无条件要求单个 session ID、至少三次 semantic Turn、至少两个 Conversation，所有 runtime receipt 又必须绑定该单一
  session；PDR 的失败复验只要求同一候选，当前原失败在 run-052、两个异质案例在 run-053，不能改写成同一 Session；
- 每个 runtime receipt 又被要求 `external_model_call_count/provider_dispatch_count/http_dispatch_count` 都等于 1，因而不能表示 run-051
  那个合法的 pre-HTTP unavailable attempt；
- verifier 只接受 envelope 与 Case 的 `plan_gate_verdict=PASS`。`scripts/plan_gate.py` 在动作迁移时强制从可信父重新运行该 verifier，
  所以不能用 `FAIL/INVALID` Result 或自报说明绕过。

## Evidence

- frozen runner：`validation/iteration_010_mvp/value_gate/runner.py` 的 `_validate_questions`、`_validate_attachment_payloads`、
  `_validate_runtime_receipts` 与 `_validate_experience`；对应 fixture 的 `QUALITY_FAIL_AFTER_ONE_GENERAL_REPAIR` 仍构造三份完整系统答案、
  Citation、Codex 答案和逐题比较，而不是前答案失败。
- trusted transition gate：`scripts/plan_gate.py::validate_gate_result` 要求 Result/evidence 同提交变化、zero-exit runner receipt，并以可信父 runner
  实际执行 `verify-plan-evidence`；candidate runner 不能验证自身。
- actual failure：run-052/053 的页面、terminal 和 Gateway SQLite 只有 clarification 与失败 Turn；没有可授权 Answer/Citation/Review。run-053
  本身有三个页面 Turn，但只覆盖 clarification 和两个问题类别；把 clarification 或失败文本追认为第三条系统答案同样不真实。

## Disposition

当前动作明确禁止修改 `validation/iteration_010_mvp/value_gate/**`、`tests/test_iteration_010_mvp_value_gate.py`、`scripts/plan_gate.py` 和
`docs/project/iterations/iteration-010/decisions/**`；候选 Manifest 也不能给自身扩权。因此不生成伪造的
`v-mvp-experience-001.json`，不密封 Result，不移动到 `V-PREVIEW-002`，当前 Manifest 游标保持不变。

`ITER-010-SLICE-001` 现记录唯一合法下一步：取得用户对最小 forward governance revision 的明确授权，再从可信父提交修订 PDR/Manifest 与
冻结 runner，使失败分支能够内嵌“原失败 + 两个异质复验”的真实 Browser/terminal/Gateway bytes、允许多个 exact artifact Session、以失败
Turn record 代替不存在的系统答案/Citation/Review/Codex 比较，并继续明确机器 PASS 只表示 failure handoff 包闭合。该治理修订必须先提交并成为
新的 trusted parent，之后才能在后续提交密封唯一 Result；不得在当前候选中同时改 runner 与 Result。
