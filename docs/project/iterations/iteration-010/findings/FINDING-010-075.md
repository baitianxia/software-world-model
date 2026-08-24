---
id: FINDING-010-075
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, quality, security]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-073, FINDING-010-074, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py, tests/test_engineering_qa_live.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: require-fresh-evidence-boundary-challenge-before-answer-authorization
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-075：单一 Reviewer 会重复 Investigation 的证据边界扩张，最终授权必须经过第二个 fresh challenge

## Observation and evidence

`FINDING-010-073/074` 的处置形成 clean product commit
`b709fad413f60d19d6f797c91ada386b1a8798a2` / tree
`cd98e66291f5478d9754f2d2c0ef54a95d545323`。run-027 对 exact mall
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` 重新执行 fresh DeepSeek Conformance 2/2 PASS；Conformance Result digest 为
`sha256:47922fc5bd58cbadfe7d58de1e9f0028d4b0955ec774fb68a0527445ad6a58f8`。持续 Browser 会话三题共 23 次
dispatch，retry 0、Provider switch 0；每题只发生一次 TLS handshake，后续分别复用 6/7/7 次。66,000-byte UTF-8 输入继续在
Provider 前拒绝且调用计数保持 23；Browser warning/error 为空，Session/launch/Gateway DB/WAL/SHM/terminal 文件均为 `0600`，
Production Activation 为 `NOT_EXECUTED`。terminal receipt document digest 为
`sha256:84a46df17ee51f6286657b603fb2eed316a3432c8a9734363c5b0ea21673de2a`。

Q1 `engineering_result_60a8a24dfbdb79c4adeae4c267fd91be` 的登录主链可由授权 Controller/Service/JWT implementation 核对，独立
复核为 PASS。Q2 `engineering_result_b8f5d63f7b1388c9c02afd26633ccf13` 和 Q3
`engineering_result_279b5d1b65752c14f32d5fcaab9dfb9e` 都被页面错误标为 `APPROVED`：

- Q2 把 `@Value("${jwt.tokenHeader}")` 和 `@Value("${jwt.tokenHead}")` 扩张成具体 `Authorization` header；本次明确排除
  `src/main/resources`，所以授权证据只能证明配置 key/injection point，不能证明运行值。它还从 Controller 的参数类型推断未挂载
  `UmsAdminLoginParam` 的 `username/password` 字段。
- Q3 再次把占位符扩张成具体 header，并从 `SecurityConfig` 注册关系推断未挂载的
  `RestAuthenticationEntryPoint` / `RestfulAccessDeniedHandler` 分别输出 401/403；它还把 authorization deny 决定直接扩张成 403，
  没有下游 response/exception mapper 的完整实现。

Gateway SQLite 的 23 个调用全部 `COMPLETED`，角色分布为 Question Understanding 3、Initial Investigation 14、Answer 3、Review 3，
没有进入 Verification。Q2/Q3 的 Understanding/FINISH 已把这些结果当成 supported；其唯一 Reviewer 又逐字复述相同扩张，并把五项质量
检查全部标为 PASS。由此可排除 `FINDING-010-073` 的 gap merge/repeat-request 路径：本次根因是 Investigation、Answer 与单一 Review
共享同一个证据所有权盲点，既有文字规则没有提供独立的、机械聚焦的最后挑战面。

## Decision and disposition

- 每个 Draft 先进入 fresh `COMPREHENSIVE` Review；只有该 Review 无 Finding、五项全 PASS 时，Application 才使用另一个 fresh role
  context 执行 `EVIDENCE_BOUNDARY_CHALLENGE`。前者只是 provisional approval；最终 Authorization 必须绑定后者的 finding-free
  `APPROVED` Review。challenge 的 rewrite、missing evidence 或 reject 继续走既有受信 remediation 状态机。
- Review 输入从当前 Package/Draft 机械投影通用 `evidence_boundary_challenges`：默认正文所引用完整内容中的配置占位符；Claim 出现但其
  引用内容没有的具体 HTTP status literal；以及 Draft 提及、同 application import 但实现未按 package-qualified identity 进入 Package
  的类型；另一个 package 的同名 Java 文件不能消除该 lead。投影只是 review lead，
  不替代语义判断：用户观察到的症状或只陈述注册关系可以合法；由占位符推导运行值、由 caller/import 推导 DTO fields/handler output、
  或由上游局部状态推导下游 status 则必须收窄、补证或拒绝。
- Gateway 角色状态机同时记录 expected Review focus：Answer 后只允许 `COMPREHENSIVE`，其空 Finding Result 只允许下一次
  `EVIDENCE_BOUNDARY_CHALLENGE`；challenge 空 Finding 才进入 terminal。焦点缺失或乱序在 Provider 前失败关闭。
- Question Understanding、Initial/Verification Investigation、Answer 与 Review Prompt 共同冻结 `${key}` 只证明 key/injection、未挂载
  parameter/import 只证明签名或关系、handler registration 不证明输出的边界。Strategy/Prompt identity 升级为
  `engineering-qa-adaptive-investigation-local-contract@20` / `engineering-qa-adaptive-investigation-prompt@30`；Provider output schema 不变。
- 每次可授权答案现在预留 Answer + comprehensive Review + challenge Review 三次 role call；默认 Review attempt 上限从 3 调整为 4，支持
  一次同包 rewrite 或一次 preview Verification 后仍完成最终双审。每题 hard 24-call fuse、retry 0、Provider switch 0 均不变。

三模块 focused 回归 78/78 PASS；Engineering QA 扩展组合 115/115 PASS，其中包含 provisional approval 被 challenge 阻断、三类边界
lead 投影、异包同名 type 对抗、Review focus 顺序和 Gateway terminal transition。扩展 docs/oracle/full deterministic Gate 与新 clean/fresh live 由后续 verification
Finding 记录；run-027 永久保持 Q1 PASS + Q2/Q3 FAIL，不因本次处置追认。
