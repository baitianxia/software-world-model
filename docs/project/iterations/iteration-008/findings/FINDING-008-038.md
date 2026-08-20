---
id: FINDING-008-038
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai, application, architecture, engineering, quality, project]
depends_on: [ITER-008-SLICE-001, FINDING-008-037, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING]
code: [src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_policy.json, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_qualification.py, src/software_world_model/ai_infrastructure/model_egress_gateway.py, validation/structure_world_model_iteration_008/capability/live_runner.py, validation/structure_world_model_iteration_008/capability/manifest.py, validation/structure_world_model_iteration_008/capability/suite-1.5.10.json, validation/structure_world_model_iteration_008/capability/oracle-1.5.10.json]
tests: [tests/test_world_model_answer_strategy.py, tests/test_iteration_008_capability_harness.py, tests/test_iteration_008_capability_qualification.py, tests/test_model_egress_gateway.py, tests/test_world_model_evaluation_grant.py]
iteration: ITER-008
classification: system-contract
disposition: application-compile-review-completeness-applicability
target: SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING
---

# FINDING-008-038：Review completeness 适用性必须由 Application 编译

## Observation

`FINDING-008-037` 的 clean candidate `ec2201abb96c8b2badb27835fe4508906681538d` / tree
`1eded0e1526c5a920b951c5f6df43a5da7e7bd67` 已执行 run-026。Conformance freeze/result/terminal digest 为
`sha256:a40590baf44b3e21609cc466139e2a3aa1a74a828811c12e43b18006462ab719` /
`sha256:9542e5d5e12776c66fccfe6eecd43f846f55a650a662a26ec521541acb79f939` /
`sha256:2d36a4ba159ba0a82d965efa9424dd80b107ebc7f56418d46861e3b834395507`，2/2 calls / 12/12 PASS；TLS
`1/1`、reuse `1`、HTTP/credential `2/2`、unknown/retry `0`。

Capability freeze/authorization digest 为
`sha256:20ffd6ed5e5f75035b25b70e5b0f9a916d54bf415c13a78a5965aa16df542b13` /
`sha256:ad6d3b26651baab68f2c075e04f8273ac2500d89445d0375dfa6f1a5410c0eb4`。运行完整执行 40 calls / 18 Case，
17 PASS、1 FAIL，input/output tokens `83,190/2,478`；result/closed-document/terminal digest 为
`sha256:5c03b7385159d1ab0c1fc249d07819f3134844dd89a7303891b644f32472a55b` /
`sha256:b5da8910999578b4521154117cba54a14b5a9410937125c17c52962792996fde` /
`sha256:a7fbdfb576edcad270a3e586dab5751fa0b6d14f9a92404719fa9662199eef3f`。TLS `2/2`、reuse `38`、
HTTP/credential `40/40`、unknown/retry `0`，所以唯一失败不是网络或 Provider availability。

## Evidence and root cause

唯一失败是 `WM-JSS-I8-REVIEW-018` 的第 2 次 positive Review：

1. 第 1 次 bounded-negative 输入按预期返回 `REJECT / QUERY_INCOMPLETE`；第 2 次输入为 COMPLETE Query/knowledge、SATISFIED Need
   和完整正向行为 Draft，Oracle 要求 `APPROVE`；
2. Prompt `@18` 已逐字说明 UNKNOWN recall 不应阻断正向 supported answer，但两次模型输出仍完全相同，output digest 都是
   `sha256:2c0317e09dc60a1e8f9e9b0ab9827102ac3fc489e880b65b2fb97e8fc2ac7e7c`；第 2 次 normalized digest 为
   `sha256:2396cfb90269af5c9d756e84dc8931132674159b588f54eaf3c1494a6322a057`；
3. exact model manifest 解释了原因：positive input 虽有 `assessment.outcome=SATISFIED`，仍同时暴露
   `business_discovery_recall=UNKNOWN`、`bounded_absence_allowed=false` 和名为
   `BUSINESS_DISCOVERY_RECALL_UNPROVEN` 的 `missing_limitation_codes`。这些字段对正向 Need 不适用，却在 wire 上表现为明确缺陷；
4. 因此 Prompt 要求模型忽略一个仍被平台标成 missing limitation 的字段集合，Contract 在语义上正确、wire state 却互相冲突。
   DeepSeek 没有义务从自然语言优先级中恢复 Application 已经知道的适用性。

根因是 Review completeness applicability 的 Owner 仍隐含落在模型，而不是 Application。run-026 授权已经消费，不得 retry；没有
Qualification、formal product、hidden canary 或 Activation。

## Decision and disposition

1. terminal compiler 升级为 `java-source-semantics-terminal-authority-compiler@2`。它从 sealed Need Assessment 编译不可由调用方
   提供的 `review_completeness_scope`；调用方预填该字段立即失败关闭。
2. 当所有 Need outcome 均为 `SATISFIED` 时，scope 为 `POSITIVE_SUPPORTED_ONLY`，business recall 明确为
   `NOT_APPLICABLE`，bounded-negative claim policy 为 `REJECT`；model-visible Trace 删除
   `business_discovery_recall`、`bounded_absence_allowed`、`missing_limitation_codes`。原 sealed Trace、Assessment、raw model output
   与审计证据均不改写。
3. 其他 outcome 使用 `THREE_LAYER_REVIEW`，保留原三层字段；bounded-negative claim 仍只有在三层 COMPLETE 时才可通过。
   该投影不是放宽 negative Gate，也不允许正向 Draft 偷带 absence claim。
4. Contract/Strategy、Prompt/Vocabulary、policy 与 suite/oracle 升级为 `1.5.10/@19/@1.4.11/@1.5.10`。suite 仍为
   18 Case / 40 calls / 18/18，`REVIEW-018` 两次调用不变；Adapter `@7`、connection/audit `@2/@2`、Investigation compiler `@7`、
   no-retry 和 1000-token budget 不变。
5. run-026 Conformance/Capability 与 run-007 product freeze/session 均不适用于新 identity。新 clean candidate 必须重新执行
   2-call Conformance 与完整 Capability；PASS 前不得生成 formal product freeze。

该改变把既有语义决定放到能确定性执行的 Owner，不新增 ADR；System Owner 写回 World Model Answering Contract。

## Verification and closure

Application/Reviewer/Capability/Gateway/authorization 定向执行面 64/64 PASS，其中新增回归逐一证明：全部 SATISFIED 时仅向模型投影
`POSITIVE_SUPPORTED_ONLY` 且删除三项不适用字段；非全 SATISFIED 时保持 `THREE_LAYER_REVIEW` 与完整三层 receipt；调用方伪造
`review_completeness_scope` 在 dispatch 前失败关闭。fake transport 在同一执行面完整执行 40 calls / 18 Case / 18/18，包含
`REVIEW-018` 的 bounded-negative REJECT 与 supported-positive APPROVE。

formal-freeze focused 89/89、fresh temporary candidate-package 37/37、current documents 342/342 PASS；`compileall`、
`git diff --check` 与仅输出路径的 credential-shaped secret scan 均 PASS。允许 AF_UNIX 的完整执行面共 1038 项，其中 1033 PASS；
raw exit 1，唯一 4 FAIL + 1 ERROR 的 exact test identity 与 failure marker 仍完全等于 `FINDING-008-020` 的历史 ITER-003
preserved hold，没有新增失败。活动 prompt program / Strategy implementation / output Contract digest 分别为
`sha256:3e966d4f6bbd484359fee38b23355d45980b902ab341b2688aef6fb866fae319` /
`sha256:7dd77458c08539b07f4f3fafccdd46854234cfd5aa39dacd08f6b57e43a01b4c` /
`sha256:9c2f3505c87d677d416c277ea853649f3bf865ffd7dfcaeaea6bc708e080e775`；suite/oracle/policy raw digest 与 pin 一致。

本地实现处置已闭合；下一步从 clean candidate 执行新的 2-call live Conformance 与完整 40-call Capability。取得 Qualification 前
V-002、V-003 与 V-WEB-001 继续 blocking。
