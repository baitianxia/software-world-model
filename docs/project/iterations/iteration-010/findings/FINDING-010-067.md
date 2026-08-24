---
id: FINDING-010-067
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-066]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: derive-review-action-and-verification-request-from-typed-finding-remediation
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-067：Review 的补证或重写动作不能与 Finding 语义分离声明

## Observation and evidence

run-024 Q2 共完成 14 次 Provider dispatch：Question Understanding、八次 Initial Investigation、首个 Answer/Review、同 Package
rewrite Answer/Review；全部调用 completed、retry/switch 0。首个 Reviewer 明确记录：Package 未提供 `DynamicAuthorizationManager` 与
`DynamicSecurityMetadataSource` 的实现，无法确认受保护接口的动态授权规则；还记录自定义 response handler implementation 未提供。
但同一 closed output 另行声明 `decision=REWRITE_REQUIRED` 与 `verification_request=null`。Application 依协议对相同 Package 执行一次
rewrite；第二个 Reviewer 再次写出相同缺证事实，并再次返回 `REWRITE_REQUIRED + null`，于是
`SAME_PACKAGE_REWRITE_FUSE_EXHAUSTED` 正确失败关闭。

现有 Domain 只校验 `REWRITE_REQUIRED` 时 Finding 非空且 request 为空、`MORE_EVIDENCE_REQUIRED` 时 Finding 非空且 request 非空；它
无法从自由文本 description 可靠判断“当前 Package 缺少决定性 implementation”是否与所选 action 一致。Provider 因而被要求分别维护
Finding prose、顶层 decision 和 verification request 三份耦合状态。安全熔断避免了错误批准，但把 Reviewer 已正确识别的可验证 evidence
gap 送入注定无效的同 Package rewrite，属于系统性可用性缺陷。

独立复核同时区分两种情形：Q2 原问题要求受保护接口的安全接入，dynamic authorization implementation 是 material evidence gap；原问题
没有要求精确 401/403 response mapping，若 Draft 自行扩张该外部结果，应基于现有 Package 删除/收窄或标成边界，而不能仅因 Reviewer 新增
非必要结论就扩大调查。补证必须服务于原问题的 material checklist/claim，不是 Reviewer 自创范围。

## Decision and disposition

- Provider-facing Review 删除独立 `decision` 与 `verification_request`。每条 Finding 使用 closed remediation variant：
  `REWRITE_WITH_EXISTING_EVIDENCE` 必须绑定当前 Package 的 exact evidence entry IDs；`INVESTIGATE_MISSING_EVIDENCE` 必须绑定一个
  material checklist/claim、受控 evidence class 与不可执行的 concrete evidence need；`REJECT_UNRECOVERABLE` 只表达不可通过重写或补证
  修复的失败。
- 可信 Adapter/Application 按受控优先级从 Finding 集合确定性派生 `REJECT`、`MORE_EVIDENCE_REQUIRED`、`REWRITE_REQUIRED` 或空 Finding
  的 `APPROVED`。仅当最终派生 action 为 `MORE_EVIDENCE_REQUIRED` 时，首个 evidence-gap Finding 才确定性形成版本化 Verification Request；reject 优先时 request 保持为空。不再接受 Provider 自行组合互相矛盾的顶层动作与 request。
- Application 重验 rewrite references 必须属于当前 Package，gap need 不含 path/URL/command/tool operation，并继续使用独立 Verification
  Investigation。Reviewer 只能为原问题/accepted checklist 中 material 的缺口请求证据；仅由 Draft 扩张产生的无据细节优先删除或收窄。

owning System Contract、ADR、相关 current contracts 与 Slice 已改为 typed remediation → derived action/request。Provider Review Schema
删除独立 decision/request，Review output identity 升为 `@5`；Domain 重建 Finding identity、验证 remediation 字段组合与 current-Package
rewrite entries，并从首个 material gap 构造 Verification Request。定向回归覆盖 gap → Verification、rewrite → same-Package Answer、reject
优先级、旧顶层字段关闭与 path-like need 拒绝。run-024 Q2 保留为 fail-closed evidence，不追认其答案，不增加 Provider retry，也不扩张
resources 或 Production 权限。
