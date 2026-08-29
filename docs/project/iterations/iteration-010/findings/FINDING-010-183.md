---
id: FINDING-010-183
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, quality]
depends_on: [FINDING-010-182, ITER-010-PDR-012]
code: [src/software_world_model/application_services/conversational_engineering_agent.py]
tests: [tests/test_conversational_engineering_agent.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: preserve-package-origin-across-same-package-targeted-rewrite
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-183：同包针对性重写的 successor Work State 被 Response Control 错误拒绝

## Observation

同一 `run-073-mvp-experience` Turn 在不完整 Source 调查后仍形成了一个可审核 Draft。第一次 fresh Reviewer 对两个未枚举的 material
conclusion 返回 `COMPLETENESS_MISSING_CLAIM`，两项均明确 `requires_evidence=false`。Application 正确把 Findings 返回同一主 Agent，
Agent 使用完全相同的 Evidence Package 形成新 Work State Revision 和修订 Draft；第二次 fresh Reviewer 对 14 个 Claim 全部评为
`SUPPORTED` 并返回 `APPROVED / findings=[]`。

最终 Delivery 却被 `SealedEngineeringAgentResponseControl` 以 `AGENT_PROTOCOL_VIOLATION` 拒绝。实现要求当前 Delivery Work State digest
必须等于 Package 的 `origin_work_state_digest`；但 Package origin 按定义是第一次封装该证据集时的 Work State。同包重写必须产生 successor
Work State，因此合规路径必然违反这个错误等式。现行 Engineering Conversation 合同已经要求 `requires_evidence=false` 走同包针对性重写，
实现与合同发生系统性冲突。

## Evidence and first divergence

- 第一次 Review 绑定 Work State `sha256:2bc7dab311f6795c38a997f733141d4dcb7969cf935628386d1f2cec527e9b61` 与
  Package `sha256:aaa56846996be4f7984e40201e9336ce2fb2401d7440f090cf11ab70175f624b`；Package origin 与该首次封装状态相同。
- Reviewer 返回两项 `requires_evidence=false` Finding 后，修订 Work State 为
  `sha256:8eb60ff7c479cc07e3321676fba5278a471f87fc0df243acd12e12d6d61ed946`，其 `previous_digest` 精确指向上述首次封装状态；
  Package ID/digest/origin 保持不变。
- 第二次 Review 绑定 successor Work State、同一 Package 与新 Draft
  `sha256:e0ca7a9517d04f9bebeb4f5a254661e43e56ad956fc6813e07568a4c84f9a89f`，返回 `APPROVED` 且 14/14 Claim
  assessment 为 `SUPPORTED`。页面显示 Evidence Package、Answer 和 fresh Review，但 `Delivery Authorization NOT PRESENT`。
- Response Control 是所有模型调用之后的最早终态偏差；Ark 10 次调用均 `COMPLETED`，不存在 Provider unavailable、fallback 或 retry 因素。

## Classification and disposition

这是 `system-contract / systemic` Finding；修复不弱化交付链：

1. Evidence Package 的 `origin_work_state_digest` 固定表示“首次密封这一 exact Observation 集合的 Work State”，不是后续 Delivery Work
   State。Package 在同包重写中保持 immutable；任何新 Observation 仍必须形成新 Package。
2. Response Control 重算并验证 Package identity、Support/Boundary partition 和 Observation ID 唯一性，再要求当前 Work State、Draft、
   Review、Package 与同一 Turn 的 exact digest chain 全部匹配。它只移除 `current work state == package origin` 这一错误条件。
3. Draft seal 同样重验 immutable Package identity、同一 Turn 和 exact sealed observations；伪造 origin 而不重算 Package digest 继续以
   `AUTHORITY_RECORD_INCONSISTENT` 失败关闭，重复授权继续被拒。
4. 原同包 rewrite 回归现改为经过真实 `SealedEngineeringAgentResponseControl`，并新增 forged Package identity 负测；包含相关八模块的
   受影响组合 `225 tests / 3 skipped / 0 failure`。run-073 的历史失败不追认，fresh Browser successor 仍待新 product/run identity。
