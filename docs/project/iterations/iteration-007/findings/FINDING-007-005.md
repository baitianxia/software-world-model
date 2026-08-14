---
id: FINDING-007-005
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [ITER-007-SLICE-001, FINDING-007-003, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING]
code: [src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, src/software_world_model/ai_infrastructure/java_source_semantics_model_egress_policy.json]
tests: [tests/test_world_model_answer_strategy.py, tests/test_iteration_007_capability_qualification.py]
iteration: ITER-007
classification: system-contract
disposition: canonicalize-explicit-static-semantic-concepts-in-versioned-prompt-vocabulary
target: SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING
---

# FINDING-007-005：原则性概念覆盖提示不足以稳定保留 returning 语义

## Observation

run-002 已关闭 run-001 的动作顺序与 Review finding-code 问题，达到 11/12；唯一失败仍是
`WM-JSS-CE-PLAN-ORDER-003`。Prompt `@2` 已明确“每个 material concept 都要对应 term”并点名 return，但模型仍输出
`validate/order/audit/event/record`，没有把问题中的英文 `returning` 归一为 `return`。

## Evidence

- run-002 freeze digest：`sha256:35fecccaa51a28fe0ec720900ca6554a097fe5612792b70c4ba8ccadc2d008b8`；
- run-002 authorization digest：`sha256:8ecf5312ae8d3239aad7f8a735982c8deb75edcaa807890e09a7711c783668ec`，已消费、无 retry；
- closed result：`var/iteration-007/capability/run-002-result/closed-evaluation-result.json`，document digest
  `sha256:8d853e685b271b50a27823a7ff4a7e89711e6f9d4a653c439022e29d89191683`；
- 11 个其他 Case 全部通过，包括 `MATERIAL_OMISSION` stable code 与正确 validate → persist → return 顺序；
- run-001 与 run-002 对该 Case 都遗漏 return，说明原则性措辞没有形成可执行的词形归一规则。

## Impact and classification

缺失会降低功能到实现检索的 recall，且发生在版本化 Plan vocabulary 边界，分类为 `system-contract`。不能降低全 12 例阈值、
删除 return constraint、增加 retry，或按该 Case ID/完整题目写分支。

## Decision and disposition

升级 capability/Strategy `1.2.2`、Prompt `@3`、proposal vocabulary `@3` 和 egress policy `@1.0.2`。Plan 在输出前建立
material-concept checklist，并对 Profile 已拥有的静态语义做 language-independent canonicalization：return、throw、order、
audit、validate 的常见英语词形及中文语义映射到稳定 canonical term。该 vocabulary 只来自 Java Source Semantics Contract，
不包含工程名、符号名、Case ID 或完整问题文本。

suite 的 12 个输入、隐藏 semantic constraints、期望结果、12/12 阈值、一次调用和无 retry 均保持不变；只更新 exact contract
identity。run-001/002 失败结果永久保留且不形成 Gateway qualification。

## Verification after disposition

- Prompt 单测固定 returning→return 等静态语义 canonicalization；
- 独立 evaluator 继续要求所有问题概念组出现并拒绝漏项；
- `1.2.2` run-003 freeze digest 为
  `sha256:ae597aa59c6ca663ea6a93d1abf55ca3d6c77ef0c6b2eaaa120a15dd6bbca4bf`；
- exact post-freeze 用户授权 digest 为
  `sha256:ddd102d3c789ea3afc9260cf7716ac5b699d68b6a196e866437a86d1ab1fb8aa`，已一次性消费；
- run-003 恰好执行 12 次 Provider request、无 retry，12/12 case PASS，failure/unknown 均为 0；closed result document
  digest 为 `sha256:3b0a6eca360f00fa41e1db86ce13c5e43e3d1e098c4d6c214bfc726484f1825f`，qualification digest 为
  `sha256:f7466141339ba78de31393126fb33e1ba903456fb7e340530e1954e0213d1a41`；
- `PASS_VALID` capability gate 已关闭，正式产品 Web、现场问题与隐藏 canary 仍须在产品代码冻结后独立验证。
