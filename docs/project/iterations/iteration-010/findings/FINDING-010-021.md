---
id: FINDING-010-021
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-020]
code: [src/software_world_model/interface/engineering_qa_preview_cli.py]
tests: [tests/test_engineering_qa_preview_cli.py, tests/test_engineering_question_answering.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: bind-request-role-call-fuse-to-the-exact-run-dispatch-grant
target: src/software_world_model/interface/engineering_qa_preview_cli.py
---

# FINDING-010-021：Preview Request 的角色调用熔断未与 exact run dispatch grant 对齐

## Observation

第五次 `V-WEB-000` run 后累计已消费 21/28 次授权调用，剩余新 run 上限为 7。检查 prepared preview 发现，Gateway configuration 与 run
authorization 会把 `--maximum-dispatches` 精确冻结为 Provider dispatch 上限，但 `EngineeringQuestionRequest` 仍使用默认
`maximum_total_model_role_calls=24`。Application 的独立 Review 预留判断读取 Request limit，而 Gateway 最终执行另一份更小的 run grant。

因此当 grant 小于 24 时，Application 可能继续申请 Investigation 调用，直到 Gateway 才拒绝；它不能在调用前按真实上限保留 Answer 与
independent Review。此前 run 没有触发这一边界，但新的 7-call 余额使该不一致成为可执行风险。

## Evidence and root cause

- `prepare_engineering_question_preview()` 用 `arguments.maximum_dispatches` 构造 model configuration 和 run authorization；
- 同一函数构造 Request 时没有传入 `EngineeringQuestionResourceLimits`；
- `_run_investigation()` 的 `usage.total_role_calls + 3` 检查正确保留当前 Investigation、Answer 与 Review，但它只能看到 Request 内的 24；
- Gateway 的 exact grant 会正确拒绝超过 7 的 ordinal，所以安全边界最终仍 fail closed；缺口是 Application 无法提前形成
  `INDEPENDENT_REVIEW_RESERVE_EXHAUSTED`，而不是重试或越权。

根因属于 `local-implementation / systemic` 的同一资源上限双重表达未绑定，不涉及 Provider 特例。

## Decision and disposition

Preview launcher 现在用 `maximum_dispatches` 同时构造 Request 的 `maximum_total_model_role_calls`、Provider configuration 和 exact run
authorization。该 limit 进入 Request digest、evaluation subject 与 role-input authority chain，因此不能在 dispatch 后漂移。

模型仍看不到剩余调用数，不能为了余额删减 Checklist、证据要求或 Review；当完整调查无法在 exact 上限内完成时，Application 在保留 Answer 与
Review 所需容量之前停止并失败关闭。此变化实现 Manifest 已有的 `safety_budget_reserves_independent_review`，不把调用次数变成质量裁剪目标，故
处置到 launcher 与既有 reserve 回归测试。

## Verification

Preview preparation 回归断言 Request total-role limit 与 exact maximum dispatches 相同；Application 既有低预算 fixture 继续断言在没有 Draft/Review
的情况下以 `INDEPENDENT_REVIEW_RESERVE_EXHAUSTED` 关闭。该断言已包含在 focused 117/117 与 full 1113/1108 exact historical-hold gate 中。
新的 live run 若使用剩余 7 次授权，最多允许 Question Understanding、4 次 Investigation、Answer 和 Review；若第 4 次 Investigation 未合法
FINISH，则在下一次 Provider dispatch 前安全停止。
