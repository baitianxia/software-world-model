---
id: FINDING-010-191
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [FINDING-010-176, FINDING-010-186, FINDING-010-187, ITER-010-PDR-012]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: separate-authority-evidence-and-producer-consumer-runtime-semantics
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-191：Draft 混同证据缺口、授权边界与消费者可见运行时效果

## Observation

`run-076-mvp-experience` 的角色重分配题在 Provider repair 失败前形成了完整 Primary Draft
`model_call_4fa2fc7f4a5c4f698761cdd228d79ea6`。Application 已因另一个 Claim 把 BOUNDARY observation 当作 SUPPORT 而正确拒绝该 Draft；
对 pre-delivery Draft 的后续分层审计又发现两个更一般的质量缺口：

1. Draft 把 World Model 缺少 `CONSTRAINT/STATE` 维度写成“事务边界分析超出当前授权范围”。该 Turn 的公开 Source Profile 实际允许
   `mall-admin`、`mall-security` 等模块的 Java，最终 input 仍有 `tool_action_budget remaining=1` 和合法 `SOURCE_SEARCH`；认知覆盖不足、
   尚未读取实现和授权拒绝不是同一事实。
2. Draft 只取得 `UmsAdminServiceImpl` 的 full Source Read，却断言“已登录用户的 `UserDetails` 不会自动更新，除非重新登录或 token
   刷新”。当前 Package 没有 `JwtAuthenticationTokenFilter` 的请求侧实现，也没有消费者何时重载权限的 Evidence；生产者侧
   `getCacheService().delResourceList(adminId)` 调用及其局部顺序不能证明缓存删除成功、请求侧可见时点或登录态生命周期。

该 Draft 没有进入 Reviewer 或 Delivery，不能作为已交付错误；但它是当前 exact Primary evidence-to-answer synthesis 的真实输出，可用于
在下一次外调前关闭通用合同缺口。

## Evidence and first divergence

- Primary output digest 为 `sha256:ee55b8cc24a661c92b87324220f412ee6bf0e6ed82aec12dc494707d376e28fe`，Manifest digest 为
  `sha256:723e32a975422543e797a35d14357f456c2d68b2356c85252b4cd5c23b251723`。最终 sealed input 含 7 个 SUPPORT、2 个
  BOUNDARY、`used=7 / maximum=8 / remaining=1`，effective catalog 仍含 `WORLD_MODEL_QUERY/SOURCE_SEARCH`。
- current-Turn Source Read 只覆盖 `UmsAdminController`、`UmsAdminRoleRelationDao` 与 `UmsAdminServiceImpl`；SUPPORT content 不含
  `JwtAuthenticationTokenFilter`。因此关于后继 request/session/security-context 何时看到新权限的结论没有 current consumer-path
  Evidence。
- exact Source `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` 的
  `mall-security/.../JwtAuthenticationTokenFilter.java` blob `9e43c509f5e82a59e7e9e3850e18e2d8ed8a5257` 在每次满足条件的 request
  中调用 `userDetailsService.loadUserByUsername(username)`；这至少证明 Draft 的“必须重新登录或 token 刷新”不是已读生产者源码可以推出的
  安全结论。该离线对照只定位缺口，不追认它为 run-076 的 current-Turn Evidence。
- first divergence 位于 Primary 把 Coverage/Tool/Authority 与 producer/consumer runtime semantics 混合的 synthesis；Application 的
  cross-disposition guard 正确阻断了另一个错误，但不能靠语言关键词机械改写此类语义。Reviewer 是尚未执行、下一次必须独立阻断的后继
  guard。

## Classification and disposition

这是 `system-contract / systemic` Finding，不按 mall、角色、缓存、JWT、中文措辞或具体问题特判。

1. Primary 与 Reviewer 必须区分 authorization、Evidence Coverage、Tool availability 和 runtime outcome。只有 current BOUNDARY 明确记录
   exact authority/Source Profile denial 时，答案才能称某事实或来源“未授权/超出授权”；认知 Gap、未读实现、无 locator、预算耗尽或
   Provider failure 必须按其真实边界表述。
2. producer-side invalidation/publish/refresh/update/commit/remote-write 调用只支持 invocation 与源码局部顺序；声称调用实现、执行成功或
   consumer-visible effect 时必须有 invoked implementation SUPPORT。声称另一个 request/session/cache consumer/security context/
   transaction observer/remote system 的可见时点时，还必须有 consumer-path SUPPORT。
3. 用户确实要求该运行时效果且合法工具仍可缩小缺口时，Primary 应选择 targeted action；否则报告 exact Evidence boundary，不能用生命周期
   假设补齐。Reviewer 对同类混淆返回 concrete Finding，并按 materiality 选择补证或现有 Package 收窄。
4. `draft_reference_policy` 与 `review_reference_policy` 对称投影上述不变量；Prompt 和 sealed policy 共同进入 exact dispatch digest。
   Application 不增加关键词 lint、不自动删句或提升 Boundary。模型边界直接单测 `28/28`、相邻 Application/Conversation/Browser/
   Candidate/Session 组合 `77/77` PASS，外部 dispatch 0；fresh Browser successor
   仍须用未参与修复的异质题验证真实 Primary/Reviewer 行为。
