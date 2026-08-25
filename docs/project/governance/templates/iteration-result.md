---
id: ITER-NNN-RESULT-<TYPE>
kind: iteration-result
status: draft
authority: evidence
owners: [project]
depends_on: []
code: []
tests: []
iteration: ITER-NNN
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

## Experience-first delivery report

首个持续 Alpha Slice 的成功或失败 Result 必须绑定 `EXPERIENCE_FIRST_DELIVERY@1`、三个 Case、计时起点和 actual。记录 60 分钟页面、
180 分钟持续 Alpha 是否达成；若到 240 分钟仍未达成，必须记录 hard stop 后新增功能/hardening/外部 dispatch 为 0。首次体验前资格次数
不得超过 1、Provider 前本地/Mock Access smoke 不得超过 1 个、full regression 必须为 0。

`live_attempt_count` 按“一份 sealed version 的一个有界用户交互单元只要触发任一外部 dispatch 就计一次”记录，不按单元内部模型/角色调用数累计；Chat 中每个已 dispatch Turn 分别计数。同一
failure signature 最多重试一次；连续两次无用户可见增量后必须停止外部重跑。Access Case 与 Quality Case 分别报告：Access PASS
只允许页面 availability，不能把质量改写为 PASS；只有质量 PASS 才允许 hardening。限制只能发生在问题之间，已开始问题的完整质量链
截断数必须为 0。

每个失败还必须记录 Source truth 到 Web 的 earliest divergence、可证伪 root-cause hypothesis、假设反证结果、Prompt/Schema/Contract
变更是否发生在假设之后、本地最小复现、两个未参与修复的相邻案例和唯一 live canary。相同 signature 修复一次仍复现时，Result 必须
进入架构职责评审，不能继续追加规则。首次 Alpha 前列出的测试只能是 targeted impact/startup/safety，full regression 计数必须为 0；
后者只在 Alpha `CONTINUE` 后 hardening 与正式验收前执行。

Provider 报告还必须列出 ordered routes、每个独立 attempt 的 sealed identity、trigger/outcome 分类、fallback 是否从 immutable original
interaction input + World Model cognition 重跑完整链，并在 Chat 中携带当前 Turn 的 exact relevant Application-sealed Conversation Context、中间产物复用数、迟到 primary 隔离收据、同 Provider retry 数和用户是否被要求重提。
Provider 输出/schema/模型审核失败可以作为 capability fallback 原因，但不得伪称网络不可用；Application、Source 或 Security 失败不得
通过切 Provider 掩盖。

## Architecture reflection and continuation decision

### Assumption verdicts

| Assumption | Expected | PASS Case IDs | Verdict | Impact |
|---|---|---|---|---|
| A1 | <expected> | <result-or-case-refs> | <SUPPORTED-FALSIFIED-UNRESOLVED> | <impact> |

### Deviation and issue classification

记录预期偏差、问题分类与个案/系统性范围。

### Layer diagnosis and mature-source-Agent comparison

逐层记录 Source ground truth、Snapshot 表示/Coverage、typed query 可达性、investigation trace 使用、Draft/Review 和正式 Web 交付，
并对照 current Codex 的正确性、完整性、无关证据、时延、成本与复杂度。记录 exact Codex identity、fresh task、双方答案 bundle、密封
顺序、随机匿名 commitment/mapping、独立 evaluator identity/context 和 blind report digest。Codex 不是 Oracle 或裁判；产品质量对照与
full cognition/locator-only 因果消融分开报告。

### Findings, alternatives and next risk

记录 Finding 去向、仍成立的替代方案和下一最大风险。

### Decision and rationale

必须先用独立三行 `Decision: CONTINUE / ACCEPT / REWORK / REDIRECT / REJECT`、`Decision owner: <exact-owner>` 和
`Decision ref: codex-user-message:sha256:<exact-message-digest>` 记录唯一决定、Owner 与人工决策收据，再说明
理由。正文决定、metadata 与 Manifest
必须一致。`CONTINUE` 或 `ACCEPT` 要求本 Slice 绑定的全部假设均为 `SUPPORTED`；存在 `FALSIFIED` 或 `UNRESOLVED` 时默认
`REWORK` 并暂停当前 Slice。`REDIRECT` 必须在 `reflection_redirect_basis` 绑定明确用户转向、核心架构证伪或预提交无进展上限已达到；
问题报告、错误答案或复核要求不能作为依据。复盘完成不等于方案通过。

每项假设的 `PASS Case IDs` 必须是本 Slice 所有、已执行并绑定该 Result Evidence 的 Verification Case；不得引用本身的
`V-REFLECT-NNN` 自证。失败封存路径可引用已执行且 Evidence 已解析的 FAIL Case，以说明假设为何被证伪。
`Expected` 必须逐字复制 Proposal 对应假设的完整原文；Result metadata 的 `critical_assumption_catalog_digest` 必须等于 Manifest 与
已接受 Readiness 冻结的摘要，不能在看到结果后改写判定对象。

`reflection_report_digest` 必须等于本 `## Architecture reflection and continuation decision` 标题下 exact UTF-8 正文的 SHA-256。

拥有 early/final 正向价值 Case 的 Result 必须保留下列唯一章节；章节正文只能是 exact JSON，`positive_value_report_digest` 绑定该
正文，`positive_value_report_ref` 为 `<Result-ID>#positive-value-report`。没有正向价值 Case 的普通 Result 删除本章节并保持相关
metadata 为 `pending`。

## Positive value report

{
  "actual": 1,
  "adjudication_owner": "independent-evaluator",
  "adjudication_receipt_ref": "independent-evaluator-result:sha256:<exact-result-digest>",
  "comparison": "at-least",
  "evaluated_question_count": 3,
  "freeze_receipt_ref": "codex-user-message:sha256:<exact-message-digest>",
  "mature_source_agent_cache_policy_digest": "sha256:<exact-digest>",
  "codex_better_question_count": 0,
  "both_fail_question_count": 0,
  "mature_source_agent_identity_digest": "sha256:<exact-digest>",
  "mature_source_agent_protocol_digest": "sha256:<exact-digest>",
  "mature_source_agent_rubric_digest": "sha256:<exact-digest>",
  "system_better_question_count": 1,
  "unresolved_or_invalid_question_count": 0,
  "measurement_input_digest": "sha256:<exact-digest>",
  "metric": "blind-paired-answer-quality-margin",
  "positive_value_protocol_digest": "sha256:<exact-digest>",
  "result_id": "ITER-NNN-RESULT-<TYPE>",
  "reuse_horizon_questions": 1,
  "schema": "software-world-model-positive-value-report/v2",
  "system_absolute_quality_verdict": "PASS",
  "tie_question_count": 2,
  "threshold": 1,
  "unit": "quality-basis-points",
  "verification_case_id": "<V-COMP-or-V-000>"
}

对 `ITER-007+` 的产品增量 Result，上述四个 `product_goal_*` 字段必须分别为 `V-000`、
`user-visible-general-source-qa-delta`、`independent-hidden-plus-live-ad-hoc` 和实际 `PASS` / `FAIL`。只有 `PASS` Result 可被
Verification 的 `product_goal_result_id` 与 V-000 Evidence 同时引用；普通机械 Result 保持 `pending`，不能充当产品证据。

产品 `PASS` Result 还必须绑定 exact subject/report 与 Manifest 的全部冻结 digest，并报告 held-out 前后支持数、重大错误、
三类 fallback、跨域和现场问题计数，以及成熟源码 Agent 对照和正式 Web 人工验证结果。Verification 中每个 Manifest 绑定
Case 的 Evidence 由拥有该 Case 的 Slice Result 持有，格式为 `<Slice Result ID>#<case-id>`，且该行必须为 `PASS / blocking`；
最终 Product Result 依赖并聚合所有 Slice Result，不覆盖已经形成的逐 Case Evidence。

从下一份新产品 Iteration 起，拥有 `V-COMP-ALPHA` 或 `V-000` 的 Result 必须把 `mature_source_agent_comparison` 写为
`strict-answer-quality-superiority`，并使 `mature_source_agent_identity_digest` 与 Manifest 一致。`positive_value_actual` 是盲评量表上的
系统答案质量减 Codex 答案质量；`PASS` 必须达到大于零的预提交阈值且逐题无物质退步；部分问题可判 tie，但总体质量差值为 `0` 或
`system_better_question_count=0` 时必须 `FAIL`。失败封存可如实记录负值，
`evaluated_question_count` 必须等于该 Case 冻结的题数，system-better、tie、Codex-better、both-fail 和 unresolved/invalid 五类计数之和
必须等于 evaluated，不能省略未完成或不利问题。不能省略报告或以成本/时延/复用值替换。技术裁决收据必须来自独立 evaluator Result，不得复用用户授权或方向决定消息。Alpha Result
只决定能否 hardening；最终 held-out `V-000` 必须重新运行。

拥有 early hidden canary 的 Slice Result 还必须绑定所属 Slice 曝光前的 `product_code_freeze_digest`、canary project/suite digest、
披露收据 digest，并证明曝光后产品变更次数为 0。任何曝光后产品变化都使该 Result 不能成为 completed Slice 的证据。

## Findings and system write-back

## Validity / supersession
