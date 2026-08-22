---
id: FINDING-010-025
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-024]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: project-exact-disposition-reference-eligibility-into-each-investigation-step
target: src/software_world_model/application_services/engineering_question_answering.py
---

# FINDING-010-025：Ledger basis ID 被误用为 Package support reference

## Observation

Prompt `@6` clean candidate `449e925099fe7db3f13175d1415d7177269e3e83` 执行第八次 `V-WEB-000`。模型完成 Question
Understanding、一次 literal SOURCE search、四次不同 full-content READ，并在第 7 次 dispatch 提交字段组合合法的 `FINISH`：
`evidence_class/query/locator_reference` 均为 `null`，6 个 checklist item 均有 disposition。Package seal 随后拒绝其中的 SUPPORTED
disposition，错误为 `SUPPORTED checklist disposition requires admissible support/citation evidence`；Answer 与 Review 均未执行。

## Evidence and root cause

- 永久 run 目录为 `var/iteration-010/slice-001/run-003-preview/web-v-web-000-011/`；terminal receipt 记录 7 次 completed dispatch、retry 0、
  Provider switch 0、Production Activation `NOT_EXECUTED`，一次 verified TLS handshake 被复用 6 次；
- 最终模型输出把多个 `SOURCE_RESULT` Ledger entry ID（包括 required latest basis）用于 SUPPORTED disposition，也把 latest result entry 用于
  UNKNOWN disposition；
- Package 的 authoritative `support/citation.source_reference` 实际是 coverage-complete READ/PARSE retrieval item ID 或 aligned Cognition item
  ID；`SOURCE_RESULT` Ledger entry 只绑定结果身份，本身既不是 affirmative support reference，也不是 boundary/audit reference；
- 调查输入暴露了 `required_basis_entry_id`，却没有暴露当前 Package 分类规则将接受的 support 与 boundary reference 集合。Prompt `@6` 使用
  “evidence or boundary entry IDs”这一宽泛措辞，模型无法仅从大型 Ledger/Result 投影可靠重建该跨对象分类。

根因属于 `local-implementation / systemic` 的动态角色控制缺口，与 `FINDING-010-020` 的 locator eligibility 同类：Prompt-only 不能可靠表达
每一步随 Cognition、Result、Decision 与 Ledger 变化的精确可引用集合。

## Decision and disposition

- 新增不可变 `ChecklistDispositionReferenceEligibility`，从 Cognition、typed Result、Broker Decision 与当前 Ledger 派生排序、去重且互斥的
  `admissible_support_references` / `admissible_boundary_references`；
- 同一分类 helper 同时驱动调查角色输入和 Package seal parity 检查，防止模型侧 eligibility 与最终 support/boundary partition 静默漂移；
- Application 在写入 FINISH Ledger entry 前机械拒绝集合外引用：SUPPORTED 只能引用 support 集，UNKNOWN/CONFLICT/FAILED 只能引用 boundary
  集；required basis 只绑定动作，不自动获得证据资格；
- Prompt 升级为 `engineering-qa-adaptive-investigation-prompt@7`，INITIAL/VERIFICATION 都只能复制对应 admissible list 中的 opaque 值；
- 保留 Package seal 的最终 fail-closed 重验，不把 Ledger entry ID 静默转换为 retrieval item ID。

该变化实现既有 Package support/citation 与 boundary/audit 语义，处置到 Application/model boundary 与回归测试，不改变 System Contract。

## Verification

新增回归机械证明 latest `SOURCE_RESULT` Ledger entry 不能作为 SUPPORTED evidence reference；完整 Engineering QA
cognition/browser/strategy/preview/application/source/model-source/live focused tests 63/63 PASS；docs 401/401、`py_compile` 与 `git diff --check`
PASS。允许 AF_UNIX 的 full discovery 共 1115 项，其中 1110 PASS；唯一 4 FAIL + 1 ERROR 的 identity、marker 与 Codex
actual/frozen digest `7645c3ca… / 9f6748b4…` 精确保持 `FINDING-008-020` 历史 hold，没有新增失败。第八次 live run 属于 Prompt
`@6` 的永久失败证据，不能追溯证明新的动态 eligibility 与 Prompt `@7`。后续 clean candidate `f38f6cc…` 已通过
`V-WEB-000`，exact live 证据见 `ITER-010-RESULT-V-WEB-000-LIVE-RUN-009`；旧失败仍不改写。
