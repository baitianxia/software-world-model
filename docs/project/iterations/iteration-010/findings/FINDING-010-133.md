---
id: FINDING-010-133
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, knowledge, source, ai, quality, interface, project]
depends_on: [FINDING-010-130, FINDING-010-131, FINDING-010-132, SYS-QUALITY-ACCEPTANCE]
code: []
tests: []
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: require-layer-attribution-before-changing-answer-path
target: SYS-QUALITY-ACCEPTANCE
---

# FINDING-010-133：run-042 是多层故障，v7 不能作为根因修复

## Observation

run-042 的 3/5 Limitation 和两个失败不能由一个 Source query 排序或 Reviewer scope 提示解释：

1. **知识构建/认知层：** 唯一 World Model input 是 Maven 模块与依赖，行为问题没有相应正式认知；
2. **Agent 调查层：** 授权源码中实际存在 `UmsAdminController.login → UmsAdminServiceImpl.login`、认证异常日志、成功登录审计写入、
   `SecurityConfig` 的 handler wiring 以及两个 handler 的未认证/无权限输出实现，但 Agent 没有完成这些决定性读取和综合；
3. **Reviewer 守门层：** Reviewer 批准“当前证据无法确认”的 Limitation，却没有识别已授权来源仍有未调查的 material need；另一方面也曾
   扩张到当前问题不要求的前端/UI 细节；
4. **交付层：** Web 如实显示了内部终态，当前没有证据说明 UI 是 first divergence。

因此，同一题既有上游 Cognition coverage 缺口，也有 Agent investigation failure 和 Reviewer guard failure。旧诊断直接把“Reviewer
扩题 + path-relevance 未投影”称为 earliest deviation，没有用替换实验排除其他层。

## Evidence

- `FINDING-010-014/132` 与 run-042 Session config 证明 Maven-only cognition；
- exact Source 中 `UmsAdminServiceImpl.java:99` 的登录实现、`:114` 的 `insertLoginLog`、`:116` 的认证异常日志，`SecurityConfig.java:60`
  的两个 handler wiring，以及 `RestAuthenticationEntryPoint` / `RestfulAccessDeniedHandler` 的输出实现证明事实在授权来源中存在；
- `FINDING-010-130` 的 terminal receipt 证明 Turn 2—4 只交付 Limitation、Turn 1/5 失败且 Reviewer 实际参与；
- `FINDING-010-131` 的测试只证明两个 policy 字段被投影，没有证明根因、真实答案修复或跨题泛化。

## Decision and disposition

以后任何答案失败必须先密封同一 immutable run 的逐层表：

`Source truth → Knowledge construction/admission → Cognition projection/query → Conversation understanding → Agent investigation →
Evidence Package → Answer synthesis → Independent Review → Web`

每个 material fact 分别记录 first divergence、downstream guard failure 和 display failure。归因采用替换实验，而不是观察最终答案猜原因：

- Source truth 与 Snapshot/Capability Manifest 对照知识构建；
- Snapshot 与实际 Cognition projection/Package 对照投影与检索；
- 同 Agent source-only 与 cognition+source 对照 Agent/认知贡献；
- complete-evidence bypass 对照答案综合；
- seeded-good/seeded-bad Draft 盲审对照 Reviewer；
- authorized Result 与页面对照 Web。

没有该报告，不得修改 Prompt、Schema、Tool policy、检索排序或 Review 文案。修复只进入最早有证据的 Owner 层，并须通过原失败和至少两个
未参与修复的异质问题；单题答对不构成通用修复。

## Verification after disposition

该发现处置到 `SYS-QUALITY-ACCEPTANCE` 的逐层归因门。ITER-010 以 `V-LAYER-ATTRIBUTION-001` 作为恢复后的第一阻断 Case；使用现有
run/source/package/review 产物离线完成，外部模型调用为 0。v7 保持未接受症状实验，归因完成前不取得 current Contract、Provider
Conformance 或 live 重跑资格。
