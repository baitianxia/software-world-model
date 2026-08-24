---
id: FINDING-010-053
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-051, FINDING-010-052]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_model_source.py, tests/test_engineering_question_strategy.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: keep-uniquely-material-requested-implementation-evidence-user-visible
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-053：用户明确要求的核对依据被默认实现详情投影隐藏

## Observation and evidence

`FINDING-010-051/052` 的处置形成 clean candidate
`88e33bdd40bcea4c3cbb9f2bb13b8a7f07cc1b6c` / tree
`70f9a1fdc2125e8a776bac1208dea9c8513c647f`。fresh DeepSeek Conformance run-018 以 2/2 request PASS，Result
`sha256:37e3a3485990acbbac13e30721745700494cfdd521d1f444b6bc24ffe8d72836`，actual model
`deepseek-v4-pro`、retry 0。随后在固定 mall revision
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` 的同一持续 Alpha 中依次提交三题：

- 原现场登录题以 13 次 dispatch 得到 `APPROVED`，正文与 Citation 覆盖登录输入、用户/密码/启用验证、SecurityContext、JWT、失败返回、
  无状态 filter 接入与 `insertLoginLog` 审计副作用；
- 本地构建/安全接入/resources unknown 混合题以 15 次 dispatch 得到 `APPROVED`，确认 POM 依赖、登录/刷新/受保护接口与安全 wiring，
  并把未授权 resources 中数据库连接、JWT 密钥和端口保留为未知；
- 401/403 排障题以 8 次 dispatch 完整读取 `JwtAuthenticationTokenFilter`、`DynamicSecurityMetadataSource` 与
  `DynamicAuthorizationManager` 并进入 Answer。Provider 正确用 3 个 `USER_VISIBLE_PROCESS` claims 区分 token、SecurityContext、动态权限，
  用 1 个 impact claim 区分 401/403，并把问题明确要求的三个源码核对位置作为独立 `IMPLEMENTATION_EVIDENCE` claim。该 claim 独自绑定
  check-5 的 3 个 material observations；Application 在 `USER_VISIBLE_EXPLANATION` 下无条件排除全部 implementation claims 后，又要求默认
  正文覆盖所有 Package observations，因而在 Review 前以 `every material observation must appear in the default user-visible answer`
  失败关闭。

terminal receipt
`sha256:08d8404580043c4c1e0a52aa78f46d785eef2b321e1b67b5c2ddbce49c2d609c` 记录 3 个 accepted question、
36 次 dispatch（13/15/8）、retry 0、Provider switch 0、Production Activation `NOT_EXECUTED`；全部 transport audit 为 verified TLS、无
post-dispatch outcome unknown。session、launch、Gateway SQLite 和 terminal receipt 均为 `0600`。同一 listener 上的 22,000 字符输入在本地
预检失败关闭，Gateway call root 在提交前后均为 36，证明没有外发；服务随后优雅停止。

## Root cause

System Contract 同时要求每个 material observation 在默认用户正文出现一次，并要求 `USER_VISIBLE_EXPLANATION` 无条件把
`IMPLEMENTATION_EVIDENCE` 排除到开发者详情。只要 Question Understanding 把用户明确要求的“可核对依据”正确保留为 material checklist，
Answer 又把它正确分类为实现证据，该 observation 就没有合法的默认正文 carrier，两个不变量形成确定性矛盾。旧运行曾把相同内容误标为
`USER_VISIBLE_PROCESS` 而绕过矛盾；这不能作为正确 contract。该缺陷与具体工程、类名或 401/403 关键词无关。

## Decision and disposition

- `IMPLEMENTATION_DETAIL` 继续默认展开全部 implementation claims；在 `USER_VISIBLE_EXPLANATION` 下，若一个 implementation claim 的
  observations 已被其他非实现用户可见 claims 完整覆盖，则继续只保留在开发者详情；若它不是完全冗余、且最终是一个或多个 material
  observations 的唯一 carrier，则必须进入默认正文；
- implementation claim 与既有用户可见 observations 完全重复时仍确定性投影；只部分交叠时仍失败关闭，不能拆句、重标 role 或静默丢弃；
  checklist/observation/evidence closure、detail budget 和 Reviewer 完整性 Gate 均不放宽；
- Answer 角色输入新增 exact conditional-visibility invariant，Prompt/Strategy/Draft identity 分别升级为 `@21/@12/@5`。current System
  Contract、ADR、Slice/Manifest/Verification 与确定性回归在同一变更中同步；Engineering QA 99/99 PASS。新的 clean candidate、fresh
  Conformance 和三题 live 必须重新执行，本次 2 PASS + 1 FAIL 只作为诊断证据，不能追认为体验或答案质量 PASS。
