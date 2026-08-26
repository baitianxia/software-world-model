---
id: FINDING-010-113
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai, quality, security]
depends_on: [FINDING-010-099, FINDING-010-111, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: project-trusted-draft-reference-domains-without-normalizing-invalid-model-output
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-113：只在 Observation 对象中携带 disposition 不足以形成可复制的 Draft 引用域

## Root cause and decision

run-036 Turn 3 的 Ark Draft 已进入 `RESPONSE_READY`，却把一个 `BOUNDARY` ID 放进 affirmative Claim 的
`support_observation_ids`。Prompt 已有自然语言规则，Application decoder 也正确拒绝，但 model input 没有把当前动态 ID 明确投影为两个
closed copy domains。让模型在长 Observation 数组中自行重建 ID→disposition 映射，是 Provider 重复维护跨字段等式，和受信 Application 已知
的状态重复。

Primary input 升级为 `ENGINEERING_AGENT_PRIMARY_INPUT@2`，model strategy/prompt 升级为
`conversational-engineering-agent@2` / `conversational-engineering-agent-no-tools-prompt@2`。Application 现在从 exact current-Turn
observations 确定性投影 `draft_reference_policy`：

- `answer_claim_support_observation_ids` 只列当前 SUPPORT ID；
- `limitation_boundary_observation_ids` 只列当前 BOUNDARY ID；
- cross-disposition 和 unknown ID 均显式禁止。

Prompt 要求只从对应数组复制 ID。closed decoder 的原有重算与 fail-closed 校验保持不变；Application 不删除错误 Claim、不替换引用、不把
Boundary 提升为 Support，也不自动授权 Draft。这个变化减少 Provider 重建受信引用域的职责，但不削弱证据闭合。

## Verification and disposition

Model boundary 测试证明 exact sealed input/disclosure 中包含新引用域和禁止位，既有 closed output、Gateway receipt、credential exclusion 与
失败分类仍通过，并直接证明混合 SUPPORT/BOUNDARY observations 被投影到互斥的 exact ID 数组；联合 Source/Agent/Model 聚焦组合当前
63/63 PASS，相邻 Chat/Source/docs 组合 217/217 PASS。完整 docs/full-regression 基线由 `FINDING-010-112` 保留。System truth 写回
Engineering Conversation Contract。由于 prompt、strategy 和 primary-input identity 已改变，`FINDING-010-105/106` 的旧 Conformance
只能保留为历史执行证据，不能资格化 successor live artifact；fresh Ark/DeepSeek Conformance 是下一外部 Gate。
