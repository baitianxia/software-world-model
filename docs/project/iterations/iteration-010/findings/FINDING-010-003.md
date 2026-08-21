---
id: FINDING-010-003
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [ITER-010-SLICE-001, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING]
code: [src/software_world_model/ai_infrastructure/engineering_question_strategy.py]
tests: [tests/test_engineering_question_strategy.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: bind-all-five-structured-role-outputs-to-current-input-manifest-schema-and-trusted-domain-coordinates
target: src/software_world_model/ai_infrastructure/engineering_question_strategy.py
---

# FINDING-010-003：角色输入已封闭，但输出边界仍需机械绑定

## Observation

Slice1 首轮实现已经为 Question Understanding、Initial Investigation、Verification Investigation、Answer 和 Review 构造精确的输入
Manifest，但角色 Protocol 直接返回已构造的领域 Proposal。确定性测试中的脚本角色因此可以绕过真实结构化输出的字段闭包、schema
identity、input Manifest binding 和重复 JSON key 检查。Application 会再次验证领域对象身份，因而这不是已观察到的越权或错误答案；它是
从封闭模型输出到领域 Proposal 之间尚未实现的本地适配缺口。

## Evidence and root cause

- `EngineeringQuestionRoleInputBuilder` 已限制五类角色可见字段并固定 `external_disclosure_status=NOT_AUTHORIZED`；
- 原测试只验证输入闭包，角色脚本直接调用 `QuestionUnderstandingProposal.create`、`InvestigationStepProposal.create`、
  `EngineeringAnswerProposal.create` 和 `EngineeringReviewProposal.create`；
- 因而额外输出字段、重复 JSON key、旧 Manifest 的输出重放和 output receipt identity 篡改此前没有统一拒绝点；
- Investigation 的 request、attempt、role context、Ledger generation/revision/prefix 等可信坐标不应由模型回显后取得权威。

根因是本地纵切先闭合了 Application 权威链，但没有同时提供 Provider 中立的结构化输出适配层。分类为 `local-implementation / systemic`：
它影响五个角色的共同实现边界，但不改变既有 System Owner、权限或语义。

## Decision and disposition

处置到 `src/software_world_model/ai_infrastructure/engineering_question_strategy.py` 及对应测试：

- 为五个角色提供 closed、versioned output schema，并形成统一 output contract digest；
- 每份输出先形成绑定 exact role、fresh role context、input Manifest digest、output schema ref/digest 和 output-text digest 的不可变 receipt；
- 解码时拒绝非对象、额外/缺失字段、错误类型、错误 enum、重复 JSON key、旧 Manifest 重放和 receipt identity 篡改；
- 模型只提交语义字段。request/package/draft digest、attempt、role context、Ledger ID/generation/revision/prefix 等坐标由适配器从可信输入补入，
  再由 Application 按当前状态重验；
- Reviewer 的 Verification Request schema 不包含 operation/path/command 字段，领域边界继续拒绝嵌入 evidence need 的可执行建议；
- 同一确定性 output source 通过五个独立角色实例接入真实 Application 状态机，并覆盖一次 Reviewer 补证、独立 Verification
  Investigation、后继 Ledger/Package、重答和重审。

本处置没有实现或授权 Provider/Gateway、credential、外发、listener、browser session、live validation 或 Production Activation。未来真实
模型 output source 仍须取得独立 live-dispatch 与 disclosure 授权；本 receipt 不是该授权。

## Verification

`tests/test_engineering_question_strategy.py` 覆盖五 schema、完整本地状态机、旧 receipt、额外/重复字段、receipt 篡改和 Reviewer operation
smuggling。相关 Engineering QA 本地测试集继续覆盖 Broker/Worker、Ledger/Package、Git exact-revision 读取和 loopback WSGI 边界。
