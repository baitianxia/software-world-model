---
id: FINDING-010-188
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, interface, quality]
depends_on: [FINDING-010-109, FINDING-010-187, ITER-010-PDR-012]
code: [src/software_world_model/application_services/engineering_conversation.py]
tests: [tests/test_engineering_conversation.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: close-empty-context-plural-and-class-demonstrative-referents
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-188：空新会话的复数指示表达没有在 Provider 前澄清

## Observation and root cause

run-076 在新 Conversation、EMPTY CONTEXT 下提交“这些失败也会回滚吗？”，Application 没有返回 input Clarification，而是创建了 Ark
attempt。现行 `_EmptyContextZhCnReferentPolicy` 只登记“它/它们/前者/后者/上述/前述”等 marker，没有覆盖“这些/那些/这类/那类/此类”这组
同样依赖先行集合或类别的 zh-CN 表达。问题不在 Conversation 隔离、Provider、路由或模型理解；最早偏差是 Provider 前的确定性 policy
覆盖不完整。

## Decision and disposition

这是 `system-contract / systemic` Finding；它闭合 `FINDING-010-109` 已拥有的语义，不按 mall、失败、回滚、数据库、消息或任何业务名词特判。

- 对真正空的 Conversation，current zh-CN policy 同时识别单数、复数和类别性指示 marker；命中后仍只生成
  `APPLICATION_INPUT_CLARIFICATION`，Provider/credential/World Model/Source dispatch 全 0。
- 非空 Conversation、已有 Work State/reviewed conclusion 和不含先行依赖 marker 的普通显式首问保持原路径。policy 仍只能决定是否澄清，
  不能生成工程结论、选择 Provider 或解释指代。
- `EMPTY_CONTEXT_REFERENT_CLARIFICATION_ZH_CN@1` 保持，因为本次是修复该既有 versioned capability 对同一语法类别的不完整实现，不改变
  Binding 字段、澄清结果 schema、权限或语言注册边界；exact product revision 继续密封实现 identity。
- deterministic tests 覆盖“这些失败”“那些写入”“此类副作用”和既有“它失败”四种零 dispatch Clarification，并保持显式“登录流程”
  首问到达 executor。该修复不发起外部调用，run-076 的失败 Turn 不被追认。
