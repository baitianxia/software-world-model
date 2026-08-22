---
id: FINDING-010-024
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-023]
code: [src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_model_source.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: expose-operation-specific-investigation-field-combinations-in-the-model-prompt
target: src/software_world_model/ai_infrastructure/engineering_question_model_source.py
---

# FINDING-010-024：FINISH 的冗余 evidence class 触发领域契约失败关闭

## Observation

用户取消本次 ITER-010 的累计 DeepSeek 调用上限后，candidate
`31b1a19135183f0a8198b39dc373a2a85712b0d4` 以每题 24-call 安全熔断执行第七次 `V-WEB-000`。模型完成 Question
Understanding、一次 literal SOURCE search、四次不同 full-content READ，并在第 7 次 role dispatch 提交覆盖 5 个 checklist item 的
`FINISH`。该输出仍携带 `evidence_class: "SOURCE"`，Application 因而以 `STRUCTURED_OUTPUT_INVALID` 失败关闭；Answer 与 Review 均未执行。

## Evidence and root cause

- 永久 run 目录为 `var/iteration-010/slice-001/run-003-preview/web-v-web-000-010/`；Gateway 保存了 7 个完整 Provider output，terminal receipt
  记录 7 次 completed dispatch、retry 0、Provider switch 0、Production Activation `NOT_EXECUTED`；
- 第 7 个输出的 `operation`、checklist dispositions、basis 和 boundary reference 均已形成，但 `evidence_class` 沿用了前一个 READ 的
  SOURCE；`query` 与 `locator_reference` 已正确为 `null`；
- `InvestigationStepProposal.create()` 的既有领域 invariant 明确要求 FINISH 只能携带完整 dispositions，不能携带 evidence class、query 或
  locator；该 invariant 正确拒绝了不一致 Proposal；
- Prompt `@5` 说明了 locator、basis、重复读取和 FINISH disposition 约束，却没有逐操作列出这四个字段的合法组合。通用 JSON Schema 只能约束
  各字段类型，不能在当前受支持的 Schema 子集内表达跨字段条件。

根因属于 `local-implementation / systemic` 的模型边界表达缺口：同一提示下任何调查题在从 SOURCE/TEST/BUILD/DOCUMENT 动作切换到 FINISH
时都可能沿用 evidence class；不是授权、TLS、预算、Broker 或领域 invariant 缺陷。

## Decision and disposition

- 保留领域对象与 Application 的 fail-closed 校验，不忽略、不静默归一化模型提交的冗余 authority field；
- Prompt 升级为 `engineering-qa-adaptive-investigation-prompt@6`，对 INITIAL 与 VERIFICATION investigation 都逐项冻结：SEARCH 的
  evidence class/query 非空，READ/PARSE 的 evidence class/eligible locator 非空，FINISH 的 evidence class/query/locator 全为 `null`，且
  只有 FINISH 携带非空 dispositions；
- 明确禁止把前一个 action 的 evidence class 带入 FINISH；
- 该变化只使既有领域契约对模型可见，处置到 prompt 与机械回归，不改变 System Contract。

## Verification

affected prompt/model-source tests 9/9 PASS；Engineering QA cognition/strategy/application/model-source/preview-CLI focused tests 45/45 PASS；docs
400/400、`py_compile` 与 `git diff --check` PASS。允许 AF_UNIX 的 full discovery 共 1114 项，其中 1109 PASS；唯一 4 FAIL + 1 ERROR 的测试
identity、`QUALIFICATION_INVALID: V-009 Adapter Conformance implementation drifted` marker 与 Codex actual/frozen digest
`7645c3ca… / 9f6748b4…` 精确保持 `FINDING-008-020` 历史 hold，没有新增失败。第七次 live run 属于旧 Prompt `@5` 的永久失败证据，
不能追溯证明 `@6`；须以新的 clean candidate、Prompt-bound grant 与新 run 重新执行 `V-WEB-000`。
