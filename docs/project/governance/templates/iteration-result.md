---
id: ITER-NNN-RESULT-<TYPE>
kind: iteration-result
status: sealed
authority: evidence
owners: [project]
depends_on: []
code: []
tests: []
iteration: ITER-NNN
# 产品开发动作仅在最终方向 handoff，或一次有证据的通用修复仍失败而迁移计划游标时填写。
# 独立 user-direction action 可另填只记录决定且不扩权的预注册 direction Result/receipt。
# 首次可操作浏览器交付、普通提交、测试、普通失败和 dispatch 不创建 Result。
plan_revision_ref: <exact-active-plan-revision-id>
action_ref: <exact-current-action-id>
verification_case_id: <exact-current-action-case-id>
plan_gate_verdict: <PASS-FAIL-or-INVALID>
evidence_schema: DEVELOPMENT_PLAN_GATE_EVIDENCE@1
evidence_verifier: <exact-versioned-minimal-handoff-verifier-id>
evidence_artifact_path: <exact-pre-registered-json-path>
evidence_artifact_digest: <sha256-of-exact-json-bytes>
runner_identity_digest: <sha256-of-pre-frozen-runner-files>
subject_digest: <sha256-exact-experience-subject>
external_model_call_count: <non-negative-integer>
provider_dispatch_count: <non-negative-integer>
http_dispatch_count: <non-negative-integer>
full_regression_run_count: <zero-before-user-continue>
standing_external_authority_ref: <exact-human-authority-ref-or-not-applicable>
standing_external_authority_scope_digest: <sha256-or-not-applicable>
one_use_runtime_receipt_count: <non-negative-integer>
runtime_scope_mismatch_count: <non-negative-integer>
redundant_human_authorization_request_count: <non-negative-integer>
complete_browser_chain: <true-or-false>
world_model_cognition_used: <true-or-false>
controlled_source_used: <true-or-false>
evidence_citations_present: <true-or-false>
independent_review_completed: <true-or-false>
semantic_chat_verified: <true-or-false>
new_conversation_isolation_verified: <true-or-false>
major_error_count: <non-negative-integer>
heterogeneous_question_count: <non-negative-integer>
unseen_question_count: <non-negative-integer>
actual_current_codex_comparison_status: <PASS-FAIL-INVALID-or-NOT-RUN>
non_locator_world_model_contribution_count: <non-negative-integer>
direction_decision: <CONTINUE-REWORK-REDIRECT-REJECT-or-pending>
direction_decision_ref: <exact-user-message-ref-or-pending>
---

# ITER-NNN Result：<Final direction handoff or proven post-repair failure cursor transition>

## Claim and exact subject

## User-visible experience

- Exact version/commit: <exact-ref>
- Repeatable launch command: <command>
- Fixed loopback address: <address>
- Complete chain: <world-model-agent-source-evidence-citation-independent-review-web>
- Chat behavior: <follow-up-correction-summary-per-turn-review-new-conversation-isolation>
- Visible limitations and failure behavior: <exact-observation>

第一次完整浏览器主链形成后立即交给用户操作，但不密封本 Result、不移动游标，也不等待 strict comparison。只有同一候选完成至少 3 个异质问题、至少 2 个 unseen 与 actual current Codex 比较而形成最终方向 handoff，或一次有证据的通用修复后同类重大失败仍存在时，才填写本 Result。full regression、hidden、跨工程和 hardening 未执行时必须如实写为 `NOT-RUN`。

## Targeted verification

列出实际执行的 targeted impact、startup、safety 和 failure-truthfulness 检查及其输出。用户 `CONTINUE` 前 `full_regression_run_count` 必须为 0。

## Same-candidate quality comparison

在同一体验候选上记录至少 3 个异质真实工程问题（至少 2 个未参与修复）、actual current Codex 的 fresh 隔离身份、双方密封输出、独立 source evidence 和独立 evaluator 结论。报告：

- 系统绝对质量是否 PASS；
- 每题是否存在物质退步；
- 总体答案质量是否严格超过 current Codex；
- 是否存在至少一项非 locator 世界模型贡献；
- 重大错误、遗漏、错误 Citation、虚假未知或无法裁决数量。

current Codex 不是 Oracle 或裁判。质量比较尚未完成时，首次体验仍必须交给用户，但不得生成最终方向 Result。比较未通过后，应先完成一次有证据的通用修复和定向复验；若同类重大失败仍存在，才以失败 Result 进入用户判向。

## Failures, root cause and limitations

失败按 `Source truth → World Model cognition → conversation/task understanding → Agent work state/plan → tool observation/evidence → answer → independent review → Web` 报告最早偏差、可证伪假设、最小复现、两个未参与修复的相邻案例和一个有界 live canary。不要逐次罗列无结论的重试，也不要为普通失败生成新的 Result。

## Authorization and external execution

记录 standing authority、exact scope、每次外部分派的 one-use runtime receipt、真实 scope delta 和失败关闭结果。standing scope 内 `redundant_human_authorization_request_count` 必须为 0；receipt 不能创建权限，scope mismatch 不能事后补写追认。通用 Result 不写死 Provider/model 名称，具体身份只出现在 execution profile 和 runtime receipt。

## Evidence binding

Result 的 ID/path 必须等于 base current action 的预注册目标，并逐字绑定 plan/action/Case/verifier/evidence path。gate 从可信 base 重放预先冻结的最小 runner，并验证 exact evidence bytes。candidate runner 不能验证自身；candidate Manifest/Result 不能扩权自己的 diff。

交接 verifier 只验证完整链、浏览器可操作性、Chat 隔离、质量比较摘要、测试边界和授权收据闭合，不复制产品工作流，不验证 Activation 分钟时钟，不要求 whole-Manifest digest，也不把每个提交、测试、失败或 dispatch 变成状态迁移。

## User direction

在最终方向 handoff 已展示后，记录唯一决定：

`Decision: CONTINUE / REWORK / REDIRECT / REJECT`

`Decision owner: user`

`Decision ref: <exact-user-message-ref>`

本 Result/receipt 只记录方向，不能创建或扩大 standing authority。同一 standing scope 内，`CONTINUE` 或 `REWORK` 直接更新工作顺序并继续；
只有真实 scope delta 才需要新授权。`REWORK` 保持同一 Slice 和长运行动作；只有明确用户转向或核心架构证伪才使用 `REDIRECT`。

当本模板用于独立 user-direction action 时，只填写决定、prior final handoff reference 与必要审计绑定；不得重新声称产品质量、生成新的产品执行权或移动到未预注册的后续动作。
