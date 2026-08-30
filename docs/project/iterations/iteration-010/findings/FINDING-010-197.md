---
id: FINDING-010-197
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, knowledge, quality]
depends_on: [FINDING-010-194, FINDING-010-195, ITER-010-PDR-012]
code: [src/software_world_model/application_services/engineering_question_cognition.py]
tests: [tests/test_engineering_question_cognition.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: explicit-source-scope-profile-coverage-gate
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-197：显式 Source scope 未约束多 Profile cognition 投影

## Observation

继续以 `run-076-mvp-experience` 的冻结异质问题审计 current cognition projection 时发现，`FINDING-010-195` 已关闭公共 path、表示层 token
和弱尾部噪声，但 relevance ranking 仍在所有 question-eligible Profile item 上运行，没有先比较问题明确点名的 Source scope 与各 Profile
正式 Coverage root：

1. `mall-search` 商品文档生命周期题在当前实现中收到 7 个 `mall-admin` Java item，包括 OSS callback、Role DAO 与
   `UmsAdminController.refreshToken`。这些 item 只因 `ID/request/refresh/list` 等通用词命中；对应 Java Profile 的 Coverage root 明确是
   `mall-admin/src/main/java`。
2. `mall-portal` 优惠券下单题碰巧没有 Java affirmative item，却仍继承同一 `mall-admin` Profile 的 559/866 全局 implementation gap。
3. current User Message 已精确点名 `mall-search` / `mall-portal`，而 sealed Source allowlist 也包含这些 top-level scope；模型生成的 relevance
   query 不应有权忽略或改写该可信范围信息。

这不是 Source authority、Snapshot 污染或 Provider 问题。最早偏差是 Application 的 multi-Profile query projection 在 Profile selection 与
gap projection 之前没有应用 formal Coverage-root compatibility。

## Evidence and first divergence

- run-076 Session 的 `JAVA_SOURCE_SEMANTICS@1` Snapshot Coverage root 为 `mall-admin/src/main/java`；Maven Profile root 为 repository-wide
  `pom.xml`。Session Source allowlist 同时列出 `mall-admin`、`mall-portal`、`mall-search` 等获准 top-level paths。
- 修复前以 Q5 冻结原文和通用 query token 本地投影得到 7 个 `mall-admin` Java affirmative item；Q2 得到 0 个 affirmative item，但仍包含
  Java Profile 的 `INCOMPLETE_IMPLEMENTATION_METHODS:559/866` gap。
- 修复后同一 artifact、revision、authority 与零 Provider dispatch 复演：Q2 只投影 1 个 `mall-portal` Maven module item，Q5 只投影 1 个
  `mall-search` Maven module item；两者均披露 Java Profile root mismatch，且不再携带 `mall-admin` affirmative item 或 559/866 gap。
- 新集成测试证明 scope 从 immutable original question 与 sealed allowlist 推导；同一 query 在未点名 scope 时会直接命中异域 Java
  `authenticate/credentials/session` item，而 original question 明确点名 `search` 后只保留 repository-wide Maven partial cognition，异域
  Profile 不能进入 affirmative/gap projection。认知模块当前 `11/11` PASS。

## Classification and disposition

这是 `system-contract / systemic` Finding，不按 mall、module name、Java、Elasticsearch、优惠券、语言或具体问题特判。

1. 当 original User Message 精确点名 sealed Source allowlist 中一个或多个 top-level Source scope 时，Application 必须在 relevance ranking
   前比较该 scope 集与每个 cognition Profile 的 formal Coverage root scope。具有非 repository-wide root 且与显式 scope 完全不相交的
   Profile 不得贡献 affirmative item 或 Profile gap。
2. scope selector 只可由 immutable original question 对 allowlist top-level segment 做 exact boundary match；Provider/model 生成的
   relevance query 不能扩大、缩小或改写它。问题未明确点名已知 scope 时不猜测，也不按业务词推导 module。
3. repository-wide root 继续可提供相容的 partial cognition；异域 Profile mismatch 形成具体 Coverage Boundary，不得表述为 Source 未授权。
   Snapshot、Read Authority、Capability Manifest、Source Profile、Broker allowlist 与 Citation identity 均不改变。

fresh Browser successor 仍须用未参与修复的异质题验证真实 Primary/Reviewer 行为；本地 projection replay 与测试不能取得答案质量或 MVP
PASS。
