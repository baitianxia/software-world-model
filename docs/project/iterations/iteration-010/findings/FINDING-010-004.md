---
id: FINDING-010-004
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, security, quality]
depends_on: [ITER-010-SLICE-001, FINDING-010-003, SYS-QUALITY-SECURITY]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: restrict-verification-role-raw-results-to-the-current-gap-successor-ledger-suffix
target: src/software_world_model/application_services/engineering_question_answering.py
---

# FINDING-010-004：补证角色不应重新获得旧调查的 raw Result

## Observation

首轮 Application 在启动 Verification Investigation 时，正确传入了 current sealed Package 和 successor Ledger，却同时把初始调查累计的
全部 typed Retrieval Result 作为角色输入。后续每一步也持续传入这组历史 raw Result。规范要求补证角色只消费具体 gap、current
Package/Ledger 和该 gap 之后逐步产生的新 Result；旧调查内容只能经 current Package 的 support/citation 或 boundary/audit 分区进入补证
上下文。

## Evidence and root cause

- `EngineeringQuestionAnsweringService._run_investigation()` 以 `results = list(existing_results)` 初始化完整结果集；
- Verification 分支原样使用 `retrieval_results=tuple(results)`，因此补证首步已经能看到所有 prior raw Result；
- `VerificationInvestigationInput.model_view()` 把这些内容投影到角色 Manifest；
- current Package 已经按 admissibility 分区并密封旧调查内容，重复提供 raw Result 会绕过该包的内容边界，即使 Broker、Ledger 与最终
  Claim 校验仍会阻止直接取得操作或交付权威。

根因是 Package 构造需要“全量结果集”，而角色输入需要“当前补证 attempt 的增量结果集”，首轮编排复用了同一个列表而没有建立 suffix
边界。分类为 `local-implementation / systemic`；既有 Engineering QA Contract 和 `SYS-QUALITY-SECURITY` 已明确拥有正确语义，因此无需
修改 Owner 或架构决策。

## Decision and disposition

- Application 在每个 Investigation Attempt 开始时记录累计 Result offset；Initial Investigation 仍按本 attempt 的全部新 Result 自适应，
  Verification Investigation 只收到 successor gap 之后新增的 Result suffix；
- `VerificationInvestigationInput` 从 Ledger 中定位最后一条 `VERIFICATION_REQUEST`，要求输入 Result 的 `(result_id, digest)` 有序集合与其后
  `SOURCE_RESULT` 条目完全相等；旧 Result、漏项、重排或伪造均以 authority inconsistency 失败关闭；
- 角色 Manifest 将字段明确命名为 `new_typed_retrieval_results`。首步为空；每次 Broker/Worker 合法追加 Result 后才递增；
- Application 仍保留全量 Result 用于后继 Package 构造，因而修复输入隔离不会丢失审计或证据。

处置写入代码和确定性测试。它没有授权或执行 Provider 外发、listener/browser、live validation 或 Production Activation。

## Verification

结构化五角色完整状态机测试验证补证首步的新 Result 集为空，后续 search/parse 仍能按本 attempt 的 prior Result 自适应；构造时注入旧调查
Result 会被拒绝。原有 successor Ledger/Package、独立 Answer/Review 和完整结果集密封测试继续通过。
