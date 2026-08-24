---
id: FINDING-010-088
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [engineering, quality, project]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-087]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: verification-target-supported-observations-require-monotonic-preservation
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-088：run-033 暴露 Verification target replacement 会静默丢失既有 supported observations

## Observation and evidence

`FINDING-010-087` 后的 clean candidate commit 为 `d70a3e6d06ad977aecf9dacf566d75cf687642a9`、tree
`3aa5ec3074663039b20a673612e9964560047a5b`，归档 SHA-256 为
`3f9c1500635e66ed0ef0e018aec4a20dc861f31987a0dd06c7038d21e02bf591`；mall 保持 exact clean
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`。fresh DeepSeek Conformance
`ccrun_eed7d05fdf8b4ba48b3a9dc4dbcedf48` 为 2/2 PASS，result digest
`sha256:f9ac0c8620ff17344cb5141c0ecb15dbdac27524110bdd00f819e950b10036e6`，request IDs 为
`e20fb270-e031-459b-a332-a7b77004885a`、`54dcd9b9-b840-46b0-ba83-e7ddd48cfe2a`，retry 0。

run-033 使用同一持续 Browser / Server 会话提交三道已冻结问题。Q1 使用 15 次 dispatch；第一次 challenge Review
`eb8cfe15-af5e-4e22-99d0-f2dd49a0ccd6` 已正确选择 `APPLICATION_PACKAGE`，识别 full-content Service 中的 cache interaction，并派生
check-6 Verification。其 evidence need 却扩大为未挂载 `UmsAdminCacheService` 的具体实现。Verification 已经持有 predecessor Package
full content 和 support，却继续 search/read，最终 request `e2ea1909-9b6b-4d33-ad9c-ff5ab25efba5` 返回单一 `UNKNOWN` limitation。

Application 当时只检查 delta 是否恰好绑定 target，然后用该 `UNKNOWN` disposition 整体替换 predecessor check-6。这个覆盖删除了
predecessor 中仍然安全、仍有 exact support 的流程与副作用 observations，包括登录日志写入；单 outcome disposition 又不能在
`UNKNOWN` 下同时承载 affirmative observations。后续 challenge `f014a881-bcd8-43b3-9a49-00b474e5757d` 因而观察到先前事实消失，并在
多项 challenge 上返回错绑 Claim 的 Findings；Application 以
`non-passing evidence-boundary assessment must bind a Finding on one challenged Claim` 正确失败关闭。根因不是 Review 最后一处错绑，而是
successor merge 允许“补一个 gap”静默删除 target 中已支持的事实。

Q2 使用 8 次 dispatch，未到 Answer。最后一个 Initial Investigation request
`86c8a11e-5046-4ece-b4d8-9e1a1113f8d3` 的 `FINISH` 为 resources-excluded unknowns 自造
`cognition-unknown-1/2/3`，而不是逐字复制 `admissible_boundary_references` 中的 opaque reference；Application 以
`FINISH disposition requires an admissible boundary/audit reference` 正确失败关闭。这是独立 Provider structured-output failure，不是上述
merge bug，也不允许放宽 evidence reference Gate。

Q3 使用 8 次 dispatch，完成 Question Understanding、4 次 Initial Investigation、Answer 和第一轮 Review；第二轮 Review 在 HTTP dispatch
后发生 `NETWORK_FAILURE`，model call `model_call_0faf0df59c524dc9ac027aa10a49b795` 封存为
`OUTCOME_UNKNOWN / LIVE_INTEGRATION_HELD`。按用户冻结的零重试策略只关闭 Q3，不补发、不切 Provider。随后 Browser 实际装载并提交
66,000 字符，页面在 Provider 前返回 `request body is empty or exceeds the local preview limit`；Gateway call roots 保持 31。

terminal receipt file SHA-256 为
`b2befc97d9a8f57aa05838b984b87150de42db8d6db781ce07f9da2ce77530bf`，document digest 为
`sha256:0a8bbeadb5047096c7bf3d3af97717e4cc82198c5ea984d644d94348f745a60a`。它记录三题分别 15/8/8、总 31 dispatch，
request retry/provider switch 均为 0，Q3 post-dispatch outcome unknown 1，Production `NOT_EXECUTED`。clean stop 后 formal SQLite SHA-256
为 `5944aaff87c78f8181350e45750f329d055a6a3450ee774d279a27a4538e305d`，`quick_check=ok`、checkpoint `0|0|0`、无 WAL/SHM、
8765 无 listener，DB、launch receipt 与 terminal receipt 均为 `0600`。

## Decision and disposition

- Verification target replacement 对 `SUPPORTED` predecessor 必须单调保留：Application 向角色投影 exact preservation contract，列出
  predecessor target 的全部 material observations；replacement 可以增加新 observation，但每个旧 observation 必须以相同 identity 和相对
  顺序继续存在。删除、改写、重排或改成不能承载 affirmative facts 的 non-supported outcome，必须在 successor Package seal 前以
  `PROVIDER_RESPONSE_INVALID` 失败关闭。
- non-supported predecessor 的 boundary 可以被真实新证据替换，不把旧 limitation 永久冻结；非目标 disposition 继续原样保留。
- `APPLICATION_PACKAGE` effect gap 的 semantic need 必须要求把 challenged full-content entry 已可见的 helper/cache/write/notification/
  external interaction 形成 caller-boundary typed observation。它不得要求未挂载 callee 内部实现，也不得借 caller invocation 推断 callee
  隐藏语义。
- 不放宽 Q2 的 admissible reference Gate，不重试或追认 Q3 unknown。run-033 永久保持 Q1 FAIL、Q2 FAIL、Q3 OUTCOME_UNKNOWN、
  66,000-byte Provider-before-call PASS，总体 live FAIL；新的 deterministic Gate 与 clean/fresh live 必须另行形成，Production 不执行。
