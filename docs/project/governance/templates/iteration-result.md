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
# 迁移动作的唯一真源字段；普通非迁移 Result 必须删除本模板中的占位值，不能伪造 verdict。
plan_revision_ref: <exact-active-plan-revision-id>
action_ref: <exact-current-action-id>
verification_case_id: <exact-current-action-case-id>
plan_gate_verdict: <PASS-FAIL-or-INVALID>
evidence_schema: DEVELOPMENT_PLAN_GATE_EVIDENCE@1
evidence_verifier: <exact-versioned-verifier-id>
evidence_artifact_path: <exact-pre-registered-json-path>
evidence_artifact_digest: <sha256-of-exact-json-bytes>
execution_input_digest: <sha256-exact-execution-input>
runner_identity_digest: <sha256-recomputed-from-pre-registered-runner-files>
runner_receipt_digest: <sha256-canonical-runner-receipt>
verification_report_digest: <sha256-canonical-case-outcomes>
subject_digest: <sha256-exact-subject>
external_model_call_count: <non-negative-integer>
product_goal_gate: pending
product_goal_outcome: pending
product_goal_evaluation: pending
product_goal_verdict: pending
product_goal_subject_digest: pending
product_goal_report_digest: pending
evaluation_project_manifest_digest: pending
held_out_suite_digest: pending
baseline_result_digest: pending
mature_source_agent_protocol_digest: pending
mature_source_agent_identity_digest: pending
authorized_software_sources_digest: pending
held_out_question_count: pending
held_out_baseline_supported_count: pending
held_out_actual_supported_count: pending
held_out_boundary_correct_gap_count: pending
held_out_answerable_without_symbol_supported_count: pending
major_error_count: pending
source_fallback_count: pending
update_fallback_count: pending
direct_fallback_count: pending
cross_domain_pass_count: pending
live_ad_hoc_pass_count: pending
live_ad_hoc_without_symbol_pass_count: pending
mature_source_agent_comparison: pending
evaluated_question_count: pending
system_better_question_count: pending
tie_question_count: pending
codex_better_question_count: pending
both_fail_question_count: pending
unresolved_or_invalid_question_count: pending
system_absolute_quality_verdict: pending
positive_value_verdict: pending
positive_value_metric: pending
positive_value_unit: pending
positive_value_comparison: pending
positive_value_threshold: pending
positive_value_actual: pending
positive_value_reuse_horizon_questions: pending
mature_source_agent_cache_policy_digest: pending
mature_source_agent_rubric_digest: pending
positive_value_protocol_digest: pending
positive_value_report_digest: pending
positive_value_report_ref: pending
positive_value_case_id: pending
positive_value_freeze_receipt_ref: pending
positive_value_adjudication_owner: pending
positive_value_adjudication_receipt_ref: pending
direction_quality_gate_schema: pending
direction_quality_report_digest: pending
direction_source_truth_ledger_digest: pending
direction_blinding_mapping_digest: pending
direction_direct_evidence_identity_digest: pending
direction_source_only_identity_digest: pending
direction_world_model_identity_digest: pending
direction_current_codex_identity_digest: pending
direction_non_locator_world_model_contribution_count: pending
direction_non_locator_world_model_contribution_verdict: pending
product_web_manual_verification: pending
product_code_freeze_digest: pending
experience_delivery_policy_schema: pending
experience_delivery_access_case_id: pending
experience_delivery_timebox_case_id: pending
experience_delivery_quality_case_id: pending
experience_delivery_verdict: pending
experience_access_gate_verdict: pending
experience_quality_gate_verdict: pending
experience_timebox_started_at: pending
experience_elapsed_minutes_at_result_seal: pending
page_launchable_elapsed_minutes: pending
sustained_user_operable_alpha_elapsed_minutes: pending
experience_hard_stop_triggered: pending
authorization_continuation_policy_schema: pending
standing_external_authority_schema: pending
standing_external_authority_ref: pending
standing_external_authority_scope_digest: pending
derived_exact_authorized_input_manifest_count: pending
derived_one_use_disclosure_receipt_count: pending
derived_one_use_dispatch_receipt_count: pending
derived_exact_control_report_digest: pending
derived_exact_control_scope_mismatch_count: pending
redundant_per_run_or_question_human_authorization_request_count: pending
scope_delta_detected_count: pending
scope_delta_kinds: pending
# Legacy compatibility field: report standing-authority and exact scope-delta status; do not treat machine receipts as grants.
external_grant_status_at_result: pending
exact_approval_request_ref: pending
independent_safe_work_exhausted: pending
development_status_after_result: pending
development_turn_exit_basis: pending
# 仅在当前 Iteration Manifest 冻结了方向探索微检查点时填写。
experience_checkpoint_handoff_count: pending
experience_checkpoint_handoff_report_digest: pending
completed_live_canary_turn_count: pending
direction_evidence_handoff_elapsed_minutes: pending
direction_decision_elapsed_minutes: pending
pre_first_experience_qualification_count: pending
pre_first_experience_smoke_question_count: pending
pre_first_experience_full_regression_count: pending
live_attempt_count: pending
same_failure_signature_maximum_retry_count: pending
maximum_consecutive_no_user_visible_increment_count: pending
external_dispatch_after_required_stop_count: pending
started_question_quality_chain_truncation_count: pending
provider_route_policy_schema: pending
provider_route_report_digest: pending
preferred_route_execution_profile_ref: pending
preferred_route_execution_profile_digest: pending
fallback_route_execution_profile_ref: pending
fallback_route_execution_profile_digest: pending
fallback_route_admission_plugin_ref: pending
fallback_route_admission_plugin_digest: pending
fallback_route_admission_policy_schema: pending
fallback_route_admission_case_id: pending
fallback_route_admission_verdict: pending
fallback_route_admission_receipt_digest: pending
fallback_route_admission_scope: pending
fallback_route_policy_source_check_status: pending
fallback_route_override_ref: pending
fallback_route_request_count: pending
fallback_route_request_with_valid_admission_count: pending
fallback_route_blocked_before_network_count: pending
fallback_route_dispatch_without_valid_admission_count: pending
fallback_route_post_admission_new_request_count: pending
fallback_route_socket_without_valid_admission_count: pending
fallback_route_tls_without_valid_admission_count: pending
fallback_route_credential_without_valid_admission_count: pending
fallback_route_http_without_valid_admission_count: pending
fallback_provider_attempt_count: pending
same_provider_retry_count: pending
cross_attempt_intermediate_artifact_reuse_count: pending
user_resubmission_or_new_session_count: pending
late_primary_result_overwrite_count: pending
capability_failure_misclassified_as_unavailable_count: pending
application_source_security_failure_fallback_count: pending
canary_project_manifest_digest: pending
canary_suite_digest: pending
canary_disclosure_receipt_digest: pending
canary_product_change_before_result_seal_count: pending
canary_capsule_consumption_status: pending
reflection_gate_case_id: pending
reflection_gate_status: pending
reflection_decision: pending
reflection_redirect_basis: pending
rework_attempt_number: pending
rework_progress_measure: pending
reflection_decision_owner: pending
reflection_decision_ref: pending
reflection_issue_class: pending
reflection_issue_scope: pending
reflection_report_digest: pending
critical_assumption_catalog_digest: pending
---

# ITER-NNN Result：<Type>

## Claim and scope

## Exact inputs / baseline

## Execution and evidence

## Result, failures and limitations

若本文件是 action transition Result，`id` 与路径必须分别等于 base `current_action.result_ref/result_path`。Result 必须逐字绑定 base plan、
action、Case、evidence schema/path/verifier，并与 JSON 原始字节、受保护 runner identity、canonical receipt/report 摘要一致；
`plan_gate_verdict` 只能为 `PASS / FAIL / INVALID`，按预注册 produced Cases 的 `INVALID > FAIL > PASS` 聚合，不得再写 `verdict`、
`gate_verdict` 等别名。候选 Result/Manifest 不能授权自己的 diff；governance plan revision 只能读取此前独立提交并已验证的 PASS Result。

## Experience-first delivery report

本节只适用于四路方向 Gate PASS 后获准的 Web action。首个持续 Alpha Slice 的成功或失败 Result 必须绑定
`EXPERIENCE_FIRST_DELIVERY@1`、三个 Case、计时起点和 actual。记录 60 分钟页面、
180 分钟持续 Alpha 是否达成；180 分钟未交即记 timebox FAIL，181—239 分钟形成的迟到 Alpha 只能作为 `FAIL / REWORK` 证据；若到
240 分钟仍未达成，必须记录 hard stop 后新增功能、hardening、full regression 和无新证据外部重跑为 0；最小体验恢复和本地根因工作仍
继续。首次体验前资格次数不得超过 1、Provider 前本地/Mock
Access smoke 不得超过 1 个、full regression 必须为 0。Manifest 另行冻结方向探索微检查点时，Result 还须记录逐点交付次数、聚合报告
digest、同一冻结 canary 的完成 Turn 数、后续方向证据/决定时间；成功 Result 必须绑定方向 Gate PASS 和用户 `CONTINUE` 收据。

`live_attempt_count` 按“一份 sealed version 的一个有界用户交互单元只要触发任一外部 dispatch 就计一次”记录，不按单元内部模型/角色调用数累计；Chat 中每个已 dispatch Turn 分别计数。同一
failure signature 最多重试一次；连续两次无用户可见增量后必须停止外部重跑。Access Case 与 Quality Case 分别报告：Access PASS
只允许页面 availability，不能把质量改写为 PASS；只有质量 PASS 才允许 hardening。限制只能发生在问题之间，已开始问题的完整质量链
截断数必须为 0；实际进入 hardening 还必须具有用户 `CONTINUE` 决定。

每个失败还必须记录 Source truth 到 Web 的 earliest divergence、可证伪 root-cause hypothesis、假设反证结果、Prompt/Schema/Contract
变更是否发生在假设之后、本地最小复现、两个未参与修复的相邻案例和唯一 live canary。相同 signature 修复一次仍复现时，Result 必须
进入架构职责评审，不能继续追加规则。首次 Alpha 前列出的测试只能是 targeted impact/startup/safety，full regression 计数必须为 0；
后者只在 Alpha `CONTINUE` 后 hardening 与正式验收前执行。

Provider 报告还必须列出 ordered routes、每个独立 attempt 的 sealed identity、trigger/outcome 分类、fallback 是否从 immutable original
interaction input + World Model cognition 重跑完整链，并在 Chat 中携带当前 Turn 的 exact relevant Application-sealed Conversation Context、中间产物复用数、迟到 primary 隔离收据、同 Provider retry 数和用户是否被要求重提。
Provider 输出/schema/模型审核失败可以作为 capability fallback 原因，但不得伪称网络不可用；Application、Source 或 Security 失败不得
通过切 Provider 掩盖。

Fallback-route 准入报告必须覆盖全部 planned 直接调用和 fallback，不按 batch/smoke/live 名称过滤。逐 run 记录 fallback execution
profile 与 admission plugin identity/configuration digest、plugin 要求的 trusted input（如时钟/时区）、完整最坏质量链预算、
`FALLBACK_ROUTE_DISPATCH_ADMISSION@1` receipt digest 和一次性 exact override；逐 request 证明准入条件/override 重验并回指同一 receipt。
无有效准入时 Provider socket/connected descriptor、TLS、credential 和 HTTP 计数必须为 0；任何无有效准入的 dispatch 均使
`V-FALLBACK-ROUTE-ADMISSION` 为 `FAIL / blocking`，不能事后补写收据追认。准入阻断期间 preferred-route-only 和本地工作继续；无法完成
Evidence、Answer、Citation 和独立 Review 时当前交互失败关闭，不交付降质答案。具体 Provider/model 名称只属于 execution profile 配置和执行收据，
不得进入通用字段、action 或 Case ID。

授权连续性报告必须分别记录 Slice 本地授权、active `PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY@1` 的人类收据与 scope digest、每次系统
派生 exact Authorized Input Manifest/one-use disclosure/dispatch receipt、实际 scope delta 和 delta approval request。公开开源、来源/许可证
可确认、位于已批准 revision selection policy 的 exact revision、clean、allowlisted、只读测试在已批准 Provider/model/endpoint/credential account route、预算、调度、有效期和
loopback `EVALUATION_ONLY` Sink 范围内，`redundant_per_run_or_question_human_authorization_request_count` 必须为 0；不同
run/问题的机器收据必须各自冻结实际身份并回指同一 standing authority。

receipt 缺失、失效或 scope mismatch 必须在 Source disclosure、network 或 credential 前失败关闭，不能靠补写追认；receipt 本身也不能为
scope delta 授权。只有
私有/来源或许可证未知/仅本机存在/dirty 数据、超出冻结集合的 project/revision/allowlist、新外部接收方或 route identity、预算增加、
超出 fallback admission policy 的调度范围或需要一次性 override、外部写入、非 loopback 暴露、Production Activation 或其他 exclusion 才记录新的人工申请。若 scope-delta request 尚未实际
发出，不得以“等待授权”作为开发回合退出依据；request 已发出但本地工作尚未穷尽时继续开发，只有二者都满足才可记录
`WAITING_EXACT_GRANT / IN_PROGRESS`。批准后必须自动续跑，不重复确认。

## Architecture reflection and continuation decision

### Assumption verdicts

| Assumption | Expected | PASS Case IDs | Verdict | Impact |
|---|---|---|---|---|
| A1 | <expected> | <result-or-case-refs> | <SUPPORTED-FALSIFIED-UNRESOLVED> | <impact> |

### Deviation and issue classification

记录预期偏差、问题分类与个案/系统性范围。

### Four-arm direction diagnosis and mature-source-Agent comparison

逐题记录独立 Source truth ledger、直接相关证据、同 Agent 仅源码、同 Agent 世界模型认知+源码、current Codex 四路 exact identity 与
输出，连同密封顺序、随机匿名 commitment/mapping、独立 evaluator identity/context 和 blind report digest。Codex 与直接证据都不是
Oracle 或裁判；第 2/3 路除世界模型认知外必须同 Agent/Prompt/tools/budget/cache/Reviewer。报告世界模型臂绝对质量、相对每条基线的逐题
verdict、Codex 总体 margin、非 locator 贡献和 earliest failure layer；不得把四路拆成二元产品对照与后置消融。

### Findings, alternatives and next risk

记录 Finding 去向、仍成立的替代方案和下一最大风险。

### Decision and rationale

必须先用独立三行 `Decision: CONTINUE / ACCEPT / REWORK / REDIRECT / REJECT`、`Decision owner: <exact-owner>` 和
`Decision ref: codex-user-message:sha256:<exact-message-digest>` 记录唯一决定、Owner 与人工决策收据，再说明
理由。正文决定、metadata 与 Manifest
必须一致。`CONTINUE` 或 `ACCEPT` 要求本 Slice 绑定的全部假设均为 `SUPPORTED`；存在 `FALSIFIED` 或 `UNRESOLVED` 时默认
`REWORK` 并阻止 PASS、晋级与 hardening；现有本地开发授权覆盖修复时保持当前 Slice `authorized / in-progress / coding_input=true`。
`REDIRECT` 必须在 `reflection_redirect_basis` 绑定明确用户转向、核心架构证伪或预提交无进展上限已达到；
问题报告、错误答案或复核要求不能作为依据。复盘完成不等于方案通过。

每项假设的 `PASS Case IDs` 必须是本 Slice 所有、已执行并绑定该 Result Evidence 的 Verification Case；不得引用本身的
`V-REFLECT-NNN` 自证。失败封存路径可引用已执行且 Evidence 已解析的 FAIL Case，以说明假设为何被证伪。
`Expected` 必须逐字复制 Proposal 对应假设的完整原文；Result metadata 的 `critical_assumption_catalog_digest` 必须等于 Manifest 与
已接受 Readiness 冻结的摘要，不能在看到结果后改写判定对象。

`reflection_report_digest` 必须等于本 `## Architecture reflection and continuation decision` 标题下 exact UTF-8 正文的 SHA-256。

拥有四路方向或 final 正向价值 Case 的 Result 必须保留下列唯一章节；章节正文只能是替换完所有 `<...>` 后的 exact JSON，
`positive_value_report_digest` 绑定该
正文，`positive_value_report_ref` 为 `<Result-ID>#positive-value-report`。没有正向价值 Case 的普通 Result 删除本章节并保持相关
metadata 为 `pending`。

## Positive value report

{
  "actual": "<strictly-positive-quality-margin>",
  "arms": [
    "direct-relevant-evidence",
    "same-agent-source-only",
    "same-agent-world-model-and-source",
    "current-codex"
  ],
  "adjudication_owner": "independent-evaluator",
  "adjudication_receipt_ref": "independent-evaluator-result:sha256:<exact-result-digest>",
  "comparison": "at-least",
  "evaluated_question_count": "<exact-frozen-question-count>",
  "freeze_receipt_ref": "codex-user-message:sha256:<exact-message-digest>",
  "mature_source_agent_cache_policy_digest": "sha256:<exact-digest>",
  "all_tie_outcome": "FAIL",
  "blinding_validity_verdict": "<PASS-or-FAIL>",
  "both_fail_question_count": "<non-negative-integer>",
  "mature_source_agent_identity_digest": "sha256:<exact-digest>",
  "mature_source_agent_protocol_digest": "sha256:<exact-digest>",
  "mature_source_agent_rubric_digest": "sha256:<exact-digest>",
  "non_locator_world_model_contribution_count": "<positive-integer-for-pass>",
  "non_locator_world_model_contribution_verdict": "<PASS-or-FAIL>",
  "per_question_four_arm_verdict_report_digest": "sha256:<exact-digest>",
  "source_truth_ledger_digest": "sha256:<exact-digest>",
  "unresolved_or_invalid_question_count": "<non-negative-integer>",
  "measurement_input_digest": "sha256:<exact-digest>",
  "metric": "blind-paired-answer-quality-margin",
  "positive_value_protocol_digest": "sha256:<exact-digest>",
  "result_id": "ITER-NNN-RESULT-<TYPE>",
  "reuse_horizon_questions": "<positive-integer>",
  "schema": "software-world-model-four-arm-positive-value-report/v1",
  "system_absolute_quality_verdict": "<PASS-or-FAIL>",
  "threshold": "<strictly-positive-precommitted-threshold>",
  "unit": "quality-basis-points",
  "verification_case_id": "<V-DIRECTION-QUALITY-or-V-000>",
  "world_model_arm_must_not_lose_to_current_codex_verdict": "<PASS-or-FAIL>",
  "world_model_arm_must_not_lose_to_direct_evidence_verdict": "<PASS-or-FAIL>",
  "world_model_arm_must_not_lose_to_source_only_verdict": "<PASS-or-FAIL>"
}

对 `ITER-007+` 的产品增量 Result，上述四个 `product_goal_*` 字段必须分别为 `V-000`、
`user-visible-general-source-qa-delta`、`independent-hidden-plus-live-ad-hoc` 和实际 `PASS` / `FAIL`。只有 `PASS` Result 可被
Verification 的 `product_goal_result_id` 与 V-000 Evidence 同时引用；普通机械 Result 保持 `pending`，不能充当产品证据。

产品 `PASS` Result 还必须绑定 exact subject/report 与 Manifest 的全部冻结 digest，并报告 held-out 前后支持数、重大错误、
三类 fallback、跨域和现场问题计数，以及成熟源码 Agent 对照和正式 Web 人工验证结果。Verification 中每个 Manifest 绑定
Case 的 Evidence 由拥有该 Case 的 Slice Result 持有，格式为 `<Slice Result ID>#<case-id>`，且该行必须为 `PASS / blocking`；
最终 Product Result 依赖并聚合所有 Slice Result，不覆盖已经形成的逐 Case Evidence。

当前及未来拥有 `V-DIRECTION-QUALITY` 或 `V-000` 的 Result 必须把 `mature_source_agent_comparison` 写为
`strict-four-arm-answer-quality-superiority`，并使四路 identity digest 与 Manifest 一致。`positive_value_actual` 是盲评量表上的世界模型臂
答案质量减 Codex 答案质量；`PASS` 必须达到大于零的预提交阈值、逐题不输三个基线、绝对质量 PASS 且具有非 locator 世界模型贡献。
全体打平、任一物质退步、both-fail、unresolved/invalid 或盲化失效必须 `FAIL`。失败封存如实记录负值和未完成问题，不能省略报告或以
成本/时延/复用替换。技术裁决收据必须来自独立 evaluator Result，不得复用用户授权或方向决定消息。方向 Result 只决定能否进入 Web；
最终 held-out `V-000` 必须重新运行。

拥有 early hidden canary 的 Slice Result 还必须绑定所属 Slice 曝光前的 `product_code_freeze_digest`、canary project/suite digest、
披露收据 digest，并证明曝光后产品变更次数为 0。任何曝光后产品变化都使该 Result 不能成为 completed Slice 的证据。

## Findings and system write-back

## Validity / supersession
