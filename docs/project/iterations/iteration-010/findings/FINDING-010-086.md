---
id: FINDING-010-086
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [engineering, quality, project]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-085]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: material-observation-entry-resolution-and-layer-precedence-required
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-086：run-032 暴露 material observation 使用了错误的 Package ID 域

## Observation and evidence

新 clean candidate commit `3bd3c04677abcff9ad4163a743d26c5bc73048d9`、tree
`1d9d2a63a30f25db205383d027c25d3ed29a9730`，归档 SHA-256 为
`131ebed95e26e9008f0cbecb570bc3aea0447933dcee4b7ebd0025be5f1dc75d`；mall 保持 exact clean
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`。fresh DeepSeek Conformance run
`ccrun_9226b74590494790bae317ef8b88943e` 为 2/2 PASS，result digest
`sha256:7aa28460c1e4d018cad3d2fbecafc10eac2b1a0012bd8dd4b41db947fe880d1f`，Provider request IDs 为
`1e668fef-84cf-4ac5-85ed-977704fc83f0` 与 `8fe67f39-432e-4dfe-aba4-8d146c466dea`，request retry 0，
Production eligible false。

run-032 在一个持续 Browser / Server 会话中按原顺序提交三题。Q1 使用 12 次 dispatch，结果
`engineering_result_63a0e3fb7ca0ef896d3bffdbba2a9a25` 为 `APPROVED`；raw Answer 与两轮 Review 覆盖登录请求、密码与启用检查、
SecurityContext、token、失败分支、登录日志和未挂载类型/配置值边界，独立复核为 PASS。Q2 使用 9 次 dispatch 后以
`PROVIDER_RESPONSE_INVALID` 失败关闭；最后一个 completed Review request ID
`41ed6e5c-f6b7-4c26-881b-64a3fe5c0789`、output digest
`sha256:9bfae9f9b48a290b702580a6f00ac43bf9cfd7da86f69861cb87d654e0d63989`。其 full-entry scan 同时识别登录日志持久化与
`getCacheService().setAdmin(admin)` 缓存写入，却把 omission 选为 `DEFAULT_DRAFT`；Application 以
`Draft-only material-effect omissions require exact Package observations and a rewrite Finding bound to the challenged entry` 正确拒绝。

raw role input 证明根因不只是 Provider 选错枚举：Q2 sealed Package 已有 exact side-effect observation
`登录成功后调用 insertLoginLog 记录登录日志，包括管理员 ID、时间和 IP。`，其 evidence reference 为
`retrieval_item_3ebaa114d0e6d4bb2bccff2271eb1ab2`；对应 `UmsAdminServiceImpl.java` support entry 的
`source_reference` 正是该值、Package entry ID 则为 `support_entry_1ea7025f25a920289602d41c1209ca55`。但 challenge view 与
`EngineeringAnswerReview.accept` 都错误地用 `support_entry_*` 直接比较 observation 的 `retrieval_item_*` references，因而投影出空的
`application_material_observations_for_entry`，并把 Application 的 statement membership set 也错误计算为空。代码与测试此前共同固化了这个
ID-domain mismatch，`FINDING-010-085` 的“exact observation table 已投影”结论因此被 live 证伪。

Q3 随后证明逐题隔离仍成立：前 5 次 dispatch completed，第 6 次 Answer dispatch 后发生 `REMOTE_DISCONNECTED`，Gateway 将
`model_call_a7add43e9c73437e9463b2134d6fc7d2` 封存为 `OUTCOME_UNKNOWN / PROVIDER_OUTCOME_UNKNOWN`，严格零重试并只关闭当前题；这项远端
post-dispatch unknown 不归因于上述 ID-domain bug，也不得补发或追认。随后浏览器实际写入 66,000 字符并提交，产品在 Provider 前以
`request body is empty or exceeds the local preview limit` 拒绝；accepted question 仍为 3、dispatch 仍为 27。

终止收据 document digest 为
`sha256:475c791c4aca3ad2e0a0458ea5c4b083e13f0d8f0aa1333279e4bd0f4bd8dfe2`，记录 Q1/Q2/Q3 分别 12/9/6 dispatch、总 27、
request retry/provider switch 均为 0、Q3 post-dispatch outcome unknown 1、Production `NOT_EXECUTED`。clean stop 后 Gateway
`PRAGMA quick_check` 为 `ok`、checkpoint `0|0|0`、无 WAL/SHM、8765 无 listener、所有会话文件为 `0600`。

## Decision and disposition

- Question Evidence Package 必须以 exact support entry 的 `source_reference` 解析 observation evidence references；challenge view 与
  Application membership Gate 必须复用同一 Application-owned resolver，不得直接比较不同 ID 域。
- challenge 必须投影该 entry 真正对应的 exact observations。空投影且存在非空 effect omission 时，`DEFAULT_DRAFT` 不可能；若同次扫描既有
  Application-Package 缺口又有 draft-only 缺口，先只返回缺少 observation 的 effects 并走 `APPLICATION_PACKAGE` Verification，后继 Package
  再审核剩余 draft-only omission。
- 不放宽 rewrite、Review 或 24-call fuse，不增加 Provider retry，不把 Q3 的远端断连改写为产品通过。run-032 永久保持 Q1 PASS、Q2 FAIL、
  Q3 OUTCOME_UNKNOWN、66,000-byte Provider-before-call PASS，总体 live FAIL；Production 不执行。
- corrective implementation 使用统一 entry resolver，修正 strategy projection 与 Review membership 重算，并把上述优先级加入
  `@25/@35` Strategy/Prompt。新的 deterministic Gate 与 clean/fresh live 必须另行形成证据，不能追认 run-032。
