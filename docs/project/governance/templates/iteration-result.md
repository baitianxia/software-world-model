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
product_web_manual_verification: pending
product_code_freeze_digest: pending
canary_project_manifest_digest: pending
canary_suite_digest: pending
canary_exposure_receipt_digest: pending
canary_product_change_after_exposure_count: pending
---

# ITER-NNN Result：<Type>

## Claim and scope

## Exact inputs / baseline

## Execution and evidence

## Result, failures and limitations

对 `ITER-007+` 的产品增量 Result，上述四个 `product_goal_*` 字段必须分别为 `V-000`、
`user-visible-general-source-qa-delta`、`independent-hidden-plus-live-ad-hoc` 和实际 `PASS` / `FAIL`。只有 `PASS` Result 可被
Verification 的 `product_goal_result_id` 与 V-000 Evidence 同时引用；普通机械 Result 保持 `pending`，不能充当产品证据。

产品 `PASS` Result 还必须绑定 exact subject/report 与 Manifest 的五个冻结 digest，并报告 held-out 前后支持数、重大错误、
三类 fallback、跨域和现场问题计数，以及成熟源码 Agent 对照和正式 Web 人工验证结果。Verification 中每个 Manifest 绑定
Case 的 Evidence 由拥有该 Case 的 Slice Result 持有，格式为 `<Slice Result ID>#<case-id>`，且该行必须为 `PASS / blocking`；
最终 Product Result 依赖并聚合所有 Slice Result，不覆盖已经形成的逐 Case Evidence。

拥有 early hidden canary 的 Slice Result 还必须绑定所属 Slice 曝光前的 `product_code_freeze_digest`、canary project/suite digest、
披露收据 digest，并证明曝光后产品变更次数为 0。任何曝光后产品变化都使该 Result 不能成为 completed Slice 的证据。

## Findings and system write-back

## Validity / supersession
