---
id: FINDING-008-013
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai, architecture, engineering, quality]
depends_on: [ITER-008-SLICE-001, FINDING-008-012, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
code: [src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_policy.json, validation/structure_world_model_iteration_008/capability/manifest.py]
tests: [tests/test_world_model_answer_strategy.py, tests/test_model_egress_gateway.py, tests/test_iteration_008_capability_harness.py, tests/test_iteration_008_capability_qualification.py]
iteration: ITER-008
classification: iteration-design
disposition: disambiguate-progress-positive-finish-ref-copy-and-review-precedence
target: ITER-008-SLICE-001
---

# FINDING-008-013：`1.3.1` 将能力提高到 13/18，剩余失败暴露四项通用判定歧义

## Observation

`FINDING-008-012` 的 clean candidate `d9f401f290bd229f95e03853caa7e4089cf96873`（tree
`0a1818d58e03b4fbb5cc0663f11d6421026e9112`）先以 preflight
`sha256:f4dc39bdc0622f0066ee442502f587335794e7ca53d1b32ad1ca24f6a13ab71b` 完成 DeepSeek Conformance run-005。用户在 freeze 前已明确
授予今晚持续自主执行权限，该 standing grant 以 exact user-message ref 密封到 post-freeze authorization
`sha256:8c5c6837f3dd02333542dd2ea56aebd48ff6a80f052b0e783eeeb9c39db2b3c5`。runner 恰好执行 2 次 synthetic request，12/12 Case
PASS，唯一模型 identity 为 `deepseek-v4-pro`，input/output tokens 为 369/83，result digest 为
`sha256:9d2aa4a2c511cb2449828888c26d314956683fba6892abd0242a1afd99bb80ae`；raw prompt/response 未持久化，授权已消费。

同候选 Capability run-005 绑定 freeze
`sha256:5f8e06889286243ffdc4e4e3d060e800501a80bc7a1177c912f4984304386750` 与 single-use authorization
`sha256:3a86a701b7213bcfed74c167653baa1007a2ab9e5592ee0454a5a3b0ea40e3c4`。runner 无 retry 地完成全部 39 次 Provider request 与
18 个 Case，`unknown_count=0`，唯一模型 identity 为 `deepseek-v4-pro`，input/output tokens 为 117180/10108。closed Result
`var/iteration-008/capability/run-005-capability-result/closed-evaluation-result.json` 的 result/document digest 为
`sha256:271033468489b50107366d2cbff6e97fba3b4840f34bd6c26c8356eb96a75775` /
`sha256:aed052c6ad3db156fdb0de0b57f22e0aeb3fef7a551573917585ed3e69fadd02`。

`1.3.1` 将上一轮 2/18 提高到 13/18。candidate、0/N、batch、direct/path/all-path、cycle/progress、Ref provenance、三类负向、
Draft 等 13 个 Case 均 PASS；剩余 FAIL 固定为 `DECLARED-INVENTORY-005`、`LEGAL-FINISH-009`、`MAX-FOUR-010`、
`BUDGET-EXHAUSTION-011` 与 `REVIEW-018`。因此仍无 Capability Qualification 或 Production Activation。

## Evidence and root cause

五个 Case 的 normalized output 与 unchanged Oracle 逐字段对照收敛为四项通用歧义：

- declared-set enumeration 同时出现“implement/implementation”语义时，模型把 primary Need 误判为方法行为读取，选择
  `method_implementations` 而不是 `declared_method_inventory`；另一个 later-step call 甚至重启 step-1 candidate search，说明
  `previous_result` 对 operation selection 的优先级仍不够绝对；
- 正向“已有足够实现/关系支持”的 `FINISH` 被只适用于负向 absence 的 discovery-recall 规则覆盖，两个 finish reason 错写为
  “无法证明不存在”，虽然 operation projection 已正确；
- `remaining_budget.model_calls=1` 表示仍可执行最后一个授权 query，却被解释为 budget 已耗尽并提前 `FINISH`；同一 Case 的一个
  重复字符 Ref 被重新键入时多出两个字符，证明“保持 exact Ref”还需要明确禁止重建 identifier；
- Reviewer 已正确 `REJECT` 并包含 `QUERY_INCOMPLETE`，但又把同一个超越完整性权限的 absence assertion 重复归类为
  `UNSUPPORTED_RUNTIME_CLAIM`；该 code 应只用于从静态事实推导实际 runtime guarantee。

这些偏差跨 operation state、预算语义、正/负 FINISH 与 finding-code taxonomy，都是 Proposal Contract 的通用输入解释问题。它们不是
DeepSeek、Case ID、工程、符号或答案特例；也没有证据支持改变 Oracle、放宽 exact Ref、接受多余 finding code 或降低 18/18 阈值。

## Impact and classification

System Contract 已规定 result-driven progression、exact Ref provenance、2—4 调查回合、三层负向证明和独立 Reviewer，但没有把
`remaining_budget` 当前回合含义、正/负 FINISH precedence 或 Review code precedence 写成系统级新语义。本处置只是把这些既有
Owner 边界投影为模型可执行的 Proposal rules，因此仍分类为 `iteration-design`，无需修改 `docs/system/` 或 ADR。

Prompt/Strategy/policy 与 Capability input identity 再次变化；run-005 Conformance 与 Capability Result 永久保留，但不能授权新候选。

## Decision and disposition

将 active bounded contract 版本化为 capability/Strategy `1.3.2`、prompt/vocabulary `@6`、bounded egress policy `@1.0.2` 和
suite/oracle identity `@1.3.2`。保留原 18 Case、39 calls、Oracle projections、semantic constraints、forbidden events、metric、阈值、
Provider contract 与 no-retry 规则。

新 Prompt 以通用规则明确：later step 不得在 non-null previous Result 上重启 candidate search；declared-set enumeration 的 primary Need
优先于实现行为词；Ref object 与四个 identifier 必须逐字符复制而不能重建；remaining budget 计入当前仍可授权的 proposal；FINISH 先
区分正向 support sufficiency 与负向 absence；完整性不足的 absence Draft 只形成 `QUERY_INCOMPLETE`，不重复标为 runtime claim。

完成 deterministic verification 与 clean commit 后，只再执行一轮同候选 2-call Conformance 和一轮 39-call Capability。该轮若仍
FAIL，不在没有新架构证据的情况下继续迭代 Prompt 或重复消耗 Provider calls；转为保留证据并评估模型能力/协议替代方案。

## Verification after disposition

- contract/policy/capability focused tests 39/39 PASS，受影响范围回归 115/115 PASS；
- full discovery 975/975 PASS；仅出现既有 SQLite connection `ResourceWarning`，没有 test failure/error，退出码为 0；
- `python3 scripts/docs.py check` 对 317 份 current documents PASS，`git diff --check` PASS；
- suite/oracle 保持 18 Case / 39 calls，活动代码和资格资产没有残留 `1.3.1` pin；正式 runtime 仍保持 Ark。

live Gate 仍使用新的 single-use freeze/authorization、无 retry、不继承 run-005 授权；正式 Web、hidden canary、SLICE-002 与 Production
Activation 均不执行。
