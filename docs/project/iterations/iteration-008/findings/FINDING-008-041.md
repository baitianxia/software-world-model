---
id: FINDING-008-041
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai, application, architecture, engineering, quality, project]
depends_on: [ITER-008-SLICE-001, FINDING-008-038, ITER-008-VERIFICATION, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING]
code: [src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_policy.json, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_qualification.py, src/software_world_model/ai_infrastructure/model_egress_gateway.py, src/software_world_model/application_services/world_model_answering.py, src/software_world_model/interface/world_model_runtime.py, src/software_world_model/interface/world_model_runtime_assets/bounded_java_source_semantics_gateway_workload.py, src/software_world_model/interface/world_model_runtime_assets/gateway_authorized_workload.py, validation/structure_world_model_iteration_008/capability/manifest.py, validation/structure_world_model_iteration_008/capability/freeze.py, validation/structure_world_model_iteration_008/capability/suite-1.5.11.json, validation/structure_world_model_iteration_008/capability/oracle-1.5.11.json, validation/structure_world_model_iteration_008/slice1_freeze.py]
tests: [tests/test_world_model_answer_strategy.py, tests/test_iteration_008_capability_harness.py, tests/test_iteration_008_capability_qualification.py, tests/test_world_model_evaluation_grant.py, tests/test_model_egress_gateway.py, tests/test_world_model_gateway_authorization.py]
iteration: ITER-008
classification: system-contract
disposition: application-compile-ordered-behavior-obligations
target: SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING
---

# FINDING-008-041：有序行为与同目标调用次数必须由 Application 编译为终端义务

## Observation

用户以 `codex-user-message:sha256:2f9d88719b037a71b78e17385c7b9fdaa049c58f40f7e9f319efbf048ebe84de`
授权执行绑定 formal report `sha256:42281adee871a1924d9f05e9ec9b87596a12946d137029cc02df941280e1361a`
和 pending grant `sha256:e3c9bed539fdfff0421fa49be39f0a49e339303fbfde97102751808c9301b082` 的 run-010 公开 Web，
并明确不授权 hidden canary、SLICE-002 或 Production Activation。授权后的 exact evaluation grant digest 为
`sha256:56b457ce562dafa0098fbcec722eb086b1bba8bc46cf8eb67ac6ba5c741091dc`。

正式页面首先提交公开问题“登录流程是怎样的？”。request
`wm-472a3dba-cd7d-46d1-b8b3-8f37a7d57292` 完成 3 次 Investigation、1 次 Draft 和 1 次 Review；DeepSeek
5/5 request 均返回，TLS handshake `1/1`、connection reuse `4`、credential `5/5`、retry/unknown `0`。页面、Citation、角色隔离
和 console 均正常，page/terminal digest 为
`sha256:f796b10d04d8db387edd4e28e787e4de009d3f3c2bde222a68aabc0a1b7c7c49` /
`sha256:bbba266da047d6f09a48d08851b2d2e8649d62dcd0c9c049c478c719294aa1dc`。

但用户可见答案只写了一次 `recordFailure()`。exact frozen Source 在 invalid branch 中连续调用两次；正式
`METHOD_IMPLEMENTATION` Result 也以 source ordinal 1/2 保存两个 distinct `CALL_SITE`，legacy `CALLS` relation 的
`call_site_count` 为 2。`V-003` 明确要求组合两次失败记录，所以这是 objective product discrepancy；页面的
`SUCCESS` 和 Reviewer 的 `APPROVE` 不能替代该产品 Oracle。当前没有用户对答案质量的独立 verdict receipt，本 Finding 不伪造
`authorized_by=user` 的裁决。

## Evidence and root cause

逐层重放把首次偏差定位为：

1. Source ground truth PASS：两次调用、throw 与成功路径均存在；
2. Snapshot/typed Query PASS：两个 call-site atom、source order 和 legacy count 完整；
3. sealed investigation trace、Need/Support authority 与 Citation PASS；
4. Draft 首次 FAIL：`model_call_0108ae80cd014df4aeea495b189cab8d` 把两个同目标 opaque Root occurrence 合并成一次泛化调用；
5. Review 二次 FAIL：`model_call_be833bb2317b49d991fa5ec71011762f` 返回 `APPROVE`，没有识别 multiplicity omission；
6. Web 忠实交付了错误 Draft，并未引入新的偏差。

因此根因不是 DeepSeek availability、TLS、Adapter schema、Source parser、Snapshot representation、typed query、Citation 或浏览器。
旧 terminal contract 虽向 Draft/Review 暴露完整 raw Query Result，却仍让模型自行从重复 opaque ID 推导“这是两个必须分别保留的同目标
调用”。这与 `FINDING-008-038` 相同，属于 Application 已拥有、却错误留给模型从复杂 wire state 恢复的确定性适用性语义。

## Decision and disposition

1. terminal compiler 升级为 `java-source-semantics-terminal-authority-compiler@3`。它从 sealed
   `METHOD_IMPLEMENTATION.ordered_atoms` 编译 caller 不可提供的 `behavior_obligation_scope`；调用方预填立即在 dispatch 前失败关闭。
2. projection 逐方法保存 canonical signature、每个 event 的 source order/kind/operator/semantic form/value category，以及可读的
   method/state/event reference。每个唯一目标 `CALL_SITE` 还保存 `same_target_call_ordinal`、`same_target_call_count` 和正式
   `legacy_static_call_site_count`。raw Query Result 仍是 authority，projection 只确定化相同 authority 的行为义务并进入 terminal
   binding digest。
3. Draft 必须保留问题请求的每个适用 ordered event，并明确大于 1 的同目标调用次数；Reviewer 使用同一 projection，对合并 occurrence、
   遗漏 exact multiplicity 或 source order 的 Draft 返回 `MATERIAL_OMISSION`。不加入工程、问题、symbol、Provider、Case 或 Oracle 特判。
4. Capability/Strategy、Prompt/Vocabulary、Gateway policy、suite/oracle identity 升级为
   `1.5.11/@20/@1.4.12/@1.5.11`。18 Case / 18/18 threshold 不变；`REVIEW-018` 增加一个独立 omitted-duplicate Review，故资格调用由
   40 调整为 41。产品每题 2—4 Investigation + Draft + Review 的 4—6 call budget 不变。
5. 新资格 fixture 只要求 sealed Result 实际拥有的 invalid-credential failure behavior：Draft 必须说明两次调用，positive Review 批准
   完整 Draft，第三次 Review 拒绝只写一次的 Draft。它不借 Oracle 要求输入未授权的成功路径事实。
6. run-027 Qualification、run-010 freeze/grant/session 都属于旧 identity，不能授权新实现。旧 run 的下单与跨域公开问题不继续执行；
   新实现必须完成离线 Gate、形成 clean exact candidate，再重新取得 Conformance 与完整 Capability PASS。hidden canary、SLICE-002、
   Reflection 和 Production Activation 仍不执行。

主处置写回 `SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING`；Capability Contract 同步增加这一 production-compiler 资格下限，但不成为
第二个 disposition target，也不改变 Activation 语义。

## Verification and closure

包含 Strategy、Capability、Gateway、freeze/authorize/evaluator 的 expanded focused 执行面 106/106 PASS；新增回归证明完整六事件产品形状可投影、
两个 `recordFailure` occurrence 分别为 ordinal 1/2 且 count 均为 2、success call/return reference 保持可读、caller-owned scope 在
Provider dispatch 前失败关闭。fake qualification 完整执行 18 Case / 41 calls / 18/18，并包含完整 Draft、positive Review 与
`REJECT / MATERIAL_OMISSION` 三条重复调用边界。`compileall` 与 `git diff --check` PASS。

对 run-010 已保存 Draft exact model input 做零网络离线 replay 也得到 `ORDERED_METHOD_BEHAVIOR`、3 个方法、`authenticate` 6 个事件；
两个 failure occurrence 分别为 1/2 和 2/2，legacy count 都为 2，success call 被投影为
`LoginService#issueSession()`，最终 return 指回 ordinal 4 的 call event。该结果证明 compiler 适配真实产品 wire shape，不只适配
synthetic qualification fixture；原 raw model input/output 与 evidence 均未改写。

AF_UNIX 相关 20/20 在允许本机 listener 的既有验证面 PASS；current documents 345/345 PASS。完整执行面现为 1039 项，其中
1034 PASS，只保留 `FINDING-008-020` 已冻结的 exact 4 FAIL + 1 ERROR，identity/reason 未新增或漂移。以上是本地确定性证据，
不是 live Provider Qualification 或新的 Product Result。新 exact candidate、formal freeze Gate、
Conformance/Capability freeze 与 live 结果将在后续证据闭合后记录；当前 V-003/V-WEB-001 继续 blocking。
