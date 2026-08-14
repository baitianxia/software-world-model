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
canary_project_manifest_digest: pending
canary_suite_digest: pending
canary_disclosure_receipt_digest: pending
canary_product_change_before_result_seal_count: pending
canary_capsule_consumption_status: pending
reflection_gate_case_id: pending
reflection_gate_status: pending
reflection_decision: pending
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

## Architecture reflection and continuation decision

### Assumption verdicts

| Assumption | Expected | PASS Case IDs | Verdict | Impact |
|---|---|---|---|---|
| A1 | <expected> | <result-or-case-refs> | <SUPPORTED-FALSIFIED-UNRESOLVED> | <impact> |

### Deviation and issue classification

记录预期偏差、问题分类与个案/系统性范围。

### Layer diagnosis and mature-source-Agent comparison

逐层记录 Source ground truth、Snapshot 表示/Coverage、typed query 可达性、investigation trace 使用、Draft/Review 和正式 Web 交付，
并对照成熟源码 Agent 的正确性、完整性、无关证据、时延、成本与复杂度。

### Findings, alternatives and next risk

记录 Finding 去向、仍成立的替代方案和下一最大风险。

### Decision and rationale

必须先用独立三行 `Decision: CONTINUE / ACCEPT / REDIRECT / REJECT`、`Decision owner: <exact-owner>` 和
`Decision ref: codex-user-message:sha256:<exact-message-digest>` 记录唯一决定、Owner 与人工决策收据，再说明
理由。正文决定、metadata 与 Manifest
必须一致。`CONTINUE` 或 `ACCEPT` 要求本 Slice 绑定的全部假设均为 `SUPPORTED`；存在 `FALSIFIED` 或 `UNRESOLVED` 时只能
`REDIRECT` 或 `REJECT`。复盘完成不等于方案通过。

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
  "actual": 0,
  "adjudication_owner": "user",
  "adjudication_receipt_ref": "codex-user-message:sha256:<exact-message-digest>",
  "comparison": "at-most",
  "freeze_receipt_ref": "codex-user-message:sha256:<exact-message-digest>",
  "mature_source_agent_cache_policy_digest": "sha256:<exact-digest>",
  "mature_source_agent_protocol_digest": "sha256:<exact-digest>",
  "mature_source_agent_rubric_digest": "sha256:<exact-digest>",
  "measurement_input_digest": "sha256:<exact-digest>",
  "metric": "<frozen-metric>",
  "positive_value_protocol_digest": "sha256:<exact-digest>",
  "result_id": "ITER-NNN-RESULT-<TYPE>",
  "reuse_horizon_questions": 1,
  "schema": "software-world-model-positive-value-report/v1",
  "threshold": 0,
  "unit": "<frozen-unit>",
  "verification_case_id": "<V-COMP-or-V-000>"
}

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
