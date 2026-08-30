---
id: FINDING-010-196
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [FINDING-010-176, FINDING-010-193, FINDING-010-195, ITER-010-PDR-012]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: counterfactual-answer-relevance-and-direct-provenance-support
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-196：邻接实现细节缺少反事实相关性与 provenance 证据门槛

## Observation

继续审计 `run-076-mvp-experience` 的角色重分配 pre-delivery Draft 后发现，前序修复已经覆盖 false authorization、consumer lifecycle、
audit diagnostic 和 World Model projection 噪声，但 Draft 的普通肯定细节仍只有笼统的“relevance”要求：

1. Draft 把 `adminRoleRelationMapper.deleteByExample(...)` 描述为使用“MyBatis Generator 生成的 Mapper”。current Package 对该结论只有
   `UmsAdminServiceImpl.java` 的 import、field 与 caller expression，没有 mapper declaration、生成清单或工具 provenance Evidence；path、
   package 与类型名不能证明生成工具或来源。
2. 调查和答案还引入 `UmsAdminRoleRelationDao` 不含 delete 方法、相邻 `delResourceListByRole` declaration 等辅助对照。部分对照可以在用户
   明确要求区分机制时有价值，但 current Primary/Reviewer 没有一个确定的 materiality 判据来区分这种情况与“删除该细节后所有 requested
   conclusion 仍完整”的自扩张，也没有明确禁止为 Draft 自己引入的邻接细节继续消费 Source action。

这不是 Source、World Model truth 或 Provider availability 问题。最早剩余偏差是 Primary synthesis 对普通 answer detail 缺少反事实相关性
规则；Reviewer 只有对 acquisition diagnostic 的具体删减规则，不能稳定阻断同类邻接扩张或 provenance 猜测。

## Evidence and first divergence

- run-076 Draft Claim 2/正文步骤 A 直接使用“`MyBatis Generator` 生成”限定；其唯一 Source SUPPORT
  `agent_observation_723c8af99cb546939dc2865e3f6ec9ab` 是完整 `UmsAdminServiceImpl.java`，只显示
  `com.macro.mall.mapper.UmsAdminRoleRelationMapper` import、注入 field 与调用表达式。
- 同一 Draft Claim 4/7 和正文分别加入辅助 DAO 接口的负向成员清单以及未被实际 `updateRole` 调用的替代 cache helper。它们证明“主题相关”
  不足以决定 user-visible materiality；必须比较删除后原问题的 HTTP、旧关系、新关系、实际 cache call 与未知时序是否仍完整。
- `SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING` 已对旧固定角色路径使用相同反事实原则：删除细节后 original request literal
  conclusion 仍完整时不扩大调查。Conversation 路径的 System Contract 只写 Reviewer 检查“相关性”，sealed policy/prompt 未把该判据传给
  Primary/Reviewer。
- zero-dispatch 确定性 Model suite 在修复后 `28/28` PASS；它验证 Primary/Reviewer 对称收到 structured materiality/provenance policy、
  format-repair 仍保留同一规则，且原 closed schema、Tool authority、Evidence disposition 和 remediation state machine 不变。

## Classification and disposition

这是 `system-contract / systemic` Finding，不按 mall、Mapper、DAO、cache、Java、中文或具体题目特判。

1. Primary 在加入每个 user-visible affirmative detail 或 Boundary 前执行 counterfactual relevance test：如果删除该细节后每个 current User
   requested conclusion 仍完整回答并诚实定界，则必须省略；只有用户明确要求，或该细节改变 requested condition、result、comparison 或
   guarantee 时才保留。
2. neighbor declaration、alternate helper/overload、package neighbor 或 implementation provenance 不因共享 artifact/vocabulary 自动
   material。不能只为 Draft 自己引入的邻接细节继续执行 Tool action；应以现有 Package 删除或收窄。
3. code-generation/tool provenance 与 type/catch/database/runtime/external-effect 一样，不能从 path、package、import、symbol name、directory
   convention 或 caller syntax 推断；material claim 必须有直接 current SUPPORT。
4. Reviewer 对称执行反事实测试。删除后仍完整回答的邻接细节形成 `requires_evidence=false` relevance Finding；真正属于原问题且缺证的结论
   才按既有规则请求 Evidence。本修复不让 Application 关键词删除正文，不扩大 Source budget，不改变 Broker、schema、Provider route 或
   Delivery authority。

fresh Browser successor 仍须用未参与修复的异质题验证真实 Primary/Reviewer 行为；本地 Prompt/policy 测试不能取得答案质量或 MVP PASS。
