---
id: FINDING-010-036
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-033, FINDING-010-035]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_model_source.py, tests/test_engineering_question_strategy.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: system-contract
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-036：coverage-only Limitation 不能被强迫错绑 supported observation

## Observation

clean candidate `fc827ce9a55029c1ae7ed31a248ead1ea8de55eb` 与 current DeepSeek Conformance
`sha256:c6f6a0f970e8fa4c60785a0f1ccbe7f7bb5214db2141df1a2bdf6cdeda0aadca` 的首道持续 Alpha 原题
`登录流程是怎样的？` 在 5 次 role dispatch 后失败关闭。Package 已正确枚举登录认证、SecurityContext、JWT、失败结果以及
`loginLogMapper.insert` 数据库审计写入，Answer 正文也表达了这些事实；随后模型增加一个诚实的 evidence coverage limitation，却因 schema
要求每个 Claim 的 `material_observation_ids` 非空而把全部 supported observations 错绑到该 limitation，Application 以
`answer claim kind differs from its material observation` 拒绝 Draft。

该会话 retry/switch 均为 0，TLS 1 次成功并复用 4 次，Gateway 主文件与 live WAL/SHM 均为 `0600`，停止后 terminal receipt 为
`STOPPED_AFTER_DISPATCH`，Production Activation 为 `NOT_EXECUTED`。它证明 fail-closed 有效，但不构成答案或体验 PASS。

## Root cause

答案层级要求存在 evidence gap/conflict/coverage boundary 时明确 Limitation；Package observation closure 则只把原问题所需 material facts
放进各 disposition。一个只说明已保留 coverage boundary 的末尾 Limitation 因而可能没有对应 Package material observation。`@3` 初版把
“每个 material-fact Claim 必须闭合 observation”错误实现成“每个 Claim 的 observation 集合都必须非空”，使两个正确约束互相冲突。

这是通用 contract 组合缺口，不是 mall、登录关键词、类、方法或 fixture 特例。

## Decision and disposition

- `material_observation_ids` 字段继续必填且必须唯一；affirmative、process、impact、implementation，以及直接回答 non-supported checklist 的
  limitation 继续要求非空并闭合对应 observations/evidence；
- 只有答案末尾 `kind=LIMITATION` 且 `content_role=LIMITATION` 的 coverage-only Claim 可以使用空集合，并且只能引用 retained
  `boundary/audit` entries；它不得附带 supported observation、承载 affirmative fact 或替代任一 observation 的默认正文覆盖；
- Reviewer 独立审核该 Claim 的真实性与 Citation；当其不表达原问题要求的 material fact 时，不得仅因空 link 报 Application observation
  omission；
- 通过 domain/schema/prompt 回归固定上述边界。新 candidate、current Conformance 与原题 + 两道异质题 + 受控失败仍须重新执行。
