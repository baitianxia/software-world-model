---
id: FINDING-010-043
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-042]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_model_source.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: update-current-engineering-qa-contract
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-043：组件接线不能替代行为证据，默认答案不得重复同一观察

## Observation and evidence

`FINDING-010-042` 的旧候选会话在第二题失败后继续接受第三题，证明 request failure 没有停止 listener：

> 管理员登录已返回 JWT，但携带令牌调用受保护接口时出现 401 或 403，应怎样沿请求链定位问题？请区分令牌提取与校验、认证上下文建立、动态权限判定三个检查面，并给出可核对依据。

该题 8 次 dispatch、retry/switch 0，Result `engineering_result_950f72532d9d168695129b39d7b8a1d9` 和 Review
`model_call_8079c544468345e3b7db5967a26570d4` 显示 `APPROVED`。但 raw Package/Answer/Review 复核证明该批准不可信：

- Investigation 读取了 `JwtAuthenticationTokenFilter.java`、`CommonSecurityConfig.java` 和 `SecurityConfig.java`，随后仅凭
  `SecurityConfig` 把请求接到 `dynamicAuthorizationManager` 就把“动态权限判定逻辑”标为 SUPPORTED；它没有读取已授权的
  `DynamicSecurityMetadataSource.java` 或 `DynamicAuthorizationManager.java`，因此没有回答请求属性如何映射权限、authority 如何比较以及
  无匹配/不满足时怎样 deny；
- Draft 的 `DIRECT_ANSWER` 绑定全部 18 个 material observation，后续 5 个默认可见 Claim 又重复绑定同一批 observation，页面因而先给
  一整段细节，再逐段重复相同内容；既有 Application 只比较 observation ID 集合，未拒绝跨用户可见 Claim 的重复。

页面随后提交 22,000 字问题，正确在 Provider 前返回 `request body is empty or exceeds the local preview limit`，health 保持 `READY`、
submit 恢复、model-call root 保持 21。优雅停止后的 terminal receipt digest 为
`sha256:d7f510a5b668a63fbfe727f31a689e3afa2ca5ebce952ef34603f895b757bc2f`，accepted question 3、dispatch 21、retry/switch 0、
Production Activation `NOT_EXECUTED`，SQLite/launch/terminal 文件均为 `0600`。这些运行事实不补救第三题的语义与正文质量缺口。

## Decision and disposition

- Initial/Verification Investigation 与 Reviewer 的通用 Prompt 明确：setup 只证明 setup，声明、依赖、注册或 wiring 只证明关系；它们不证明
  被委托组件内部的条件、比较、状态变化、结果、失败语义或相邻流程。how/why/条件/排障问题在授权和预算可达时必须读取决定性实现证据，
  否则形成 non-supported disposition 或 more-evidence request；不加入 mall、JWT、类名或题目特判；
- Answer Prompt 要求 `DIRECT_ANSWER` 简洁并把细粒度事实分配给后续 Claim。Application 机械要求每个 Package observation 在默认用户可见
  Claim 中恰好出现一次；默认隐藏的 `IMPLEMENTATION_EVIDENCE` 仍可复用 observation 提供开发者细节；
- current Engineering QA System Contract 同步拥有上述语义。旧 `APPROVED` 只保留为 Reviewer 漏判证据，最终候选必须从 fresh session
  重跑原题与两道异质题。
