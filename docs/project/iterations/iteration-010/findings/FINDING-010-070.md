---
id: FINDING-010-070
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-067, FINDING-010-069]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: treat-successful-verification-finish-as-one-gap-delta-and-trusted-merge
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-070：Verification FINISH 是单 gap delta，不是完整 Checklist 重报

## Observation and evidence

clean candidate `7fb7e7c059c2beece3dc93e15aded0ea0e6ab657` / tree
`a2cfc0f541f0afe5c803a1ef450cece897544f72` 先通过 run-025 fresh DeepSeek Conformance 2/2；Result digest
为 `sha256:35585d6e81dd8c52df3da23d895ac6e2cdc570f90e5122e39edaa0c72265ca45`、文件 SHA-256 为
`cb4d11eb61c3e3e469198bd1306f0913a019713cf9f090ce898daf9ca936c764`，actual model `deepseek-v4-pro`、
request/retry 为 2/0，一次 verified TLS handshake、一次 connection reuse。

fresh Session Authority
`sha256:01d33e64d29c5f7a7ec76d77baca7be96cf3f60cec230ab3096bc3fd81022a09` 绑定该 candidate、mall exact
revision `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`、Source Profile 与 root authorization。持续 Alpha
顺序提交三题，dispatch 为 8/13/12，共 33 次；retry/switch 均为 0，每题一次 verified TLS handshake。66,000-byte UTF-8 输入在
Provider 前拒绝，listener 仍可用。terminal receipt document digest 为
`sha256:7e75662d442275d26ffeb76ce1ba7862dbb93533f3e16265dac6d7806be77f11`、文件 SHA-256 为
`8f9e084695bda48201496d32112ee87577c1962be0affe3908aa04c3457a36ca`；DB/launch/terminal 分别为
`0600`，Production Activation `NOT_EXECUTED`，listener 已正常停止。

Q1 以 8 次 dispatch 获得独立可接受的 `APPROVED`，四个 Citation 均打开并核对。Q2 的 Review
`model_call_8153b9f83a854b948a2d37804d15a2e7` 正确返回 typed
`INVESTIGATE_MISSING_EVIDENCE`，可信 Application 也正确派生只绑定 `check-3` 的 Verification Request。补证角色随后读取
`DynamicAuthorizationManager` 并在
`model_call_dea7b60ff69f4bec97303d443af4bfee` 合法返回：`checklist_item_ids=[check-3]`、一个
`check-3/SUPPORTED` disposition。它的 closed input 只有该 gap Request；要求它重报其他三个非 gap disposition 会越过 Reviewer 授权，
也会让独立角色重新生成前序 Package 状态。

Application Domain 却始终把任何 FINISH 与原 Question Understanding 的四项完整 Checklist 比较，因而以
`FINISH must disposition every Checklist item exactly once` 拒绝这个正确 delta。Initial FINISH 的完整集规则本身正确；错误在于 Initial 与
Verification 共用同一个授权集合，属于系统性协议错配。

## Decision and disposition

- Initial Investigation 的 authorized checklist scope 仍是完整 Question Checklist，FINISH 必须 exact-once 覆盖全部项。
- Verification Investigation 的 authorized scope 只有 `verification_request.checklist_item_id`；每步及成功 FINISH 只能绑定该项，FINISH
  exact-once 返回一个 gap disposition。任何其他 checklist ID 或多项 delta 在 Domain 层失败关闭。
- 成功 Verification Ledger seal 后，可信 Application 以 prior Package 的稳定顺序替换唯一目标 disposition；所有非 gap disposition
  对象/digest 原样保留。目标不存在、重复、Request/Package identity 不同或 delta 非单项均拒绝。失败关闭的 Verification 不做 delta
  merge，继续使用系统生成的完整失败 dispositions。
- successor Ledger 的 FINISH 记录 gap delta；新 Package 通过 predecessor digest、successor Ledger seal、完整累计 Evidence partitions
  与合并后的全量 disposition set 取得新身份。旧 Answer/Review 仍不能放行新 Package。

owning Contract、ADR、Slice 与 Verification Matrix 已同步该 gap-delta / trusted-merge 语义。Initial/Verification output schema identity
升为 `@10`，strategy identity 升为 `@18`，Prompt identity 升为 `@28`。回归覆盖 Verification 单 gap FINISH、越权 checklist 拒绝、
保序替换与非目标对象不变。run-025 Q2 保留为失败证据，不被修复后测试追认为 live PASS。
