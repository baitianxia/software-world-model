---
id: FINDING-007-003
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [ITER-007-SLICE-001, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING]
code: [src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, src/software_world_model/interface/world_model_product.py, src/software_world_model/ai_infrastructure/java_source_semantics_model_egress_policy.json]
tests: [tests/test_world_model_answer_strategy.py, tests/test_iteration_007_capability_qualification.py]
iteration: ITER-007
classification: system-contract
disposition: version-and-close-feature-concept-and-review-finding-vocabularies
target: SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING
---

# FINDING-007-003：首次资格运行暴露 Plan 概念覆盖与 Review finding vocabulary 未闭合

## Observation

冻结的 source-semantics capability run-001 完成了 exact 12 次 Provider 调用，但只有 9 例通过。Plan order Case 未为问题中的
`return` 概念生成 search term；Review omission Case 正确拒绝了缺少失败分支的 Draft，却返回三个自由生成的近义 finding code，
没有返回资格契约要求的稳定 `MATERIAL_OMISSION`。

## Evidence

- 冻结：`var/iteration-007/capability/run-001-freeze/qualification-freeze.json`，digest
  `sha256:96148054864d830a97b44b63daaa1ff12736a257a538275be7f2986ec464c3f2`；
- 授权：`sha256:c552bf12f5cf31d0adf80a56a54a8325c0e44c1e7e84f3626111457da0aa9f3f`，已消费且没有 retry；
- closed result：`var/iteration-007/capability/run-001-result/closed-evaluation-result.json`，document digest
  `sha256:19667ba344f0f4a19994319cc8815de1c4f36028edb2f2de7611ae3413103a06`；
- `WM-JSS-CE-PLAN-ORDER-003` 的 terms 为 `validate/order/audit/event/record`，缺少明确请求的 return 概念；
- `WM-JSS-CE-REVIEW-OMISSION-010` 返回 `OMITTED_FAILURE_BRANCH`、`INCOMPLETE_BRANCH_COVERAGE`、
  `DRAFT_OMITS_QUERY_RESULT_ATOMS`，语义方向正确但没有遵守稳定 code contract。

## Impact and classification

问题影响模型 Proposal Contract、Prompt、output schema 和 Application 的确定性复核，不是个别测试调参，分类为
`system-contract`。失败的 `1.2.0` Strategy/Prompt/qualification 永久无效，不能通过忽略三例或放宽阈值复用。

## Decision and disposition

升级为 capability/Strategy `1.2.1`、Prompt `@2`、proposal vocabulary `@2`、Review schema `@2` 和 egress policy
`@1.0.1`。Plan 明确要求为用户提出的每个物质功能概念保留 search term。Review schema 使用闭合 finding-code enum；Prompt
定义 omission、unsupported runtime claim 与 payload expansion 的稳定映射；Application 重新拒绝未注册、重复或乱序 code。

12 个 Case、每角色 4 例、全通过阈值、无 retry、无 Oracle/Source/Evidence payload 边界均不放宽。新 suite/oracle 仅更新
contract identity，Case 输入、语义 constraint 与期望结果不因 run-001 输出而改变。

## Verification after disposition

- schema 单测拒绝 run-001 中的自由近义 code；
- Prompt/schema 单测固定概念覆盖规则、finding vocabulary 和唯一顺序；
- 新版本仍须重新冻结、取得新的 post-freeze 用户授权并完成 12/12，才能生成 Gateway qualification。
