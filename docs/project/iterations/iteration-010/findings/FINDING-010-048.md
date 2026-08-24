---
id: FINDING-010-048
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-043, FINDING-010-047]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_model_source.py, tests/test_engineering_question_strategy.py, tests/test_engineering_qa_live.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: add-required-path-closure-and-structurally-unique-direct-answer
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-048：class 闭包仍可漏决定性文件，扁平 Answer Schema 允许多直答

## Observation and evidence

`FINDING-010-047` 的处置形成 clean candidate
`5ce5ab0f9c99d42cfd8892e3b1a5d91a65e9fa4b` / tree
`b915335cc188b9b158db41cab50110b007ceba47`。fresh DeepSeek Conformance run-015 以 2/2 request PASS，Result
`sha256:38706e7ced6108ea47b35662ac681c1ee25056521de16e8d489d02283f3733f8`，retry 0，actual model
`deepseek-v4-pro`。同候选持续 Alpha 在 fixed mall revision `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` 上依次提交三题；原始
Gateway SQLite 复核证明页面状态不足以代表答案正确：

- “登录流程是怎样的？”执行 9 次 dispatch 后显示 `APPROVED`。它实际读取 Controller 与 Service 实现并回答 `/admin/login`、用户名密码、
  账户校验、`SecurityContext`、JWT、成功/失败返回，但 Package、Draft 和独立 Review 都再次漏掉完整 Service 源码中登录成功调用
  `insertLoginLog` 及管理员 ID、时间、IP 的持久化审计副作用；该 `APPROVED` 是质量失败，不能追认为现场题 PASS；
- 本地启动/安全接入/排除 resources 的混合题执行 11 次 dispatch。Investigation 已形成前两项 `SUPPORTED`、运行参数
  `UNKNOWN` 的合法 Package，Answer 却在同一数组输出一个 affirmative `DIRECT_ANSWER` 和第二个 limitation `DIRECT_ANSWER`。
  Application 的既有 exactly-one invariant 正确失败关闭，Review 未发生；
- 401/403 排障题执行 12 次 dispatch 后显示 `APPROVED`。它读取 `JwtAuthenticationTokenFilter.java`、
  `CommonSecurityConfig.java`、`SecurityConfig.java` 和 README，却没有读取已授权的
  `DynamicAuthorizationManager.java` 或 `DynamicSecurityMetadataSource.java`；Package/答案只证明过滤器链选择了 manager，仍把被委托
  manager 的权限集合取得、authority 比较与 deny 语义写成已支持行为。Reviewer 再次把 wiring 当成决定性实现而错误批准。

会话已优雅停止。terminal receipt
`sha256:9ac1011c9348157a1e585fe6b346f95d542ba693687ca75ba4543f0c37939c79` 记录 3 个 accepted question、32 次
dispatch、retry 0、Provider switch 0、Production Activation `NOT_EXECUTED`；Gateway、launch、session、terminal 文件均为 `0600`。
同一 listener 上的 22,000 字符受控超限题仍在 Provider 前拒绝，dispatch 不增加且服务保持可用。

## Root cause

- `required_evidence_classes` 只能证明本题需要 `SOURCE`，不能区分 caller/wiring 与被委托实现，也不能表达一条流程中多个决定性实现文件；
  模型读取同 class 的任意文件后即可提交全 `SUPPORTED` FINISH；
- Question Understanding 看得到 exact authorized paths，却没有受控的 mandatory-read path obligation；Application 因而无法在 FINISH 前判断
  已声明的决定性实现是否真正完整读取，SEARCH 或截断内容也没有独立闭包语义；
- Answer closed schema 仍是允许所有合法 Claim variant 的扁平数组。Domain 能拒绝两个 `DIRECT_ANSWER`，但 Provider-facing schema 无法在
  输出边界构造性地保证唯一直接回答；混合 support/unknown 的表达规则也未反映在结构上；
- Question Understanding、Investigation 与 Reviewer 的宽泛“阶段、状态、副作用”提示仍允许把状态变化当成全部 effect，未强制逐独立
  checklist 审核持久化、审计、缓存、通知或外部交互。这是通用 flow/lifecycle 完整性问题，不是登录日志、JWT、mall 文件名或题目特判。

## Decision and disposition

- Question Understanding closed output 新增 1—8 个去重 `required_evidence_paths`。每个路径必须位于 immutable Request allowlist，且由绑定
  Source Profile 唯一解析到一个 registered evidence class；该 class 也必须出现在本题 `required_evidence_classes`；
- Initial Investigation 向角色投影 required/unread path。任意 FINISH——包括全 `SUPPORTED`——只要仍有 unread required path，就由
  Application 追加命名路径与 class 的 GAP 并继续；只有无行范围且 `coverage_complete=true` 的 READ/PARSE 才消费义务，SEARCH 与截断读取
  都不能闭包。确定性测试覆盖 caller 已读但 delegate 未读时的 premature FINISH；
- Answer output 改为结构上唯一、必填的 `direct_answer` 对象，加一个禁止 `DIRECT_ANSWER` 的 follow-up `claims` 数组；两处分别用 closed
  kind/content-role variants。混合 Package 只能用 affirmative direct summary 回答 supported 部分，unknown/conflict/failure 必须进入末尾
  limitation follow-up；只有全部 non-supported 时 direct answer 才能是 limitation；
- flow/lifecycle 的 Question Understanding 必须把成功/失败结果、状态变化和持久化/审计/缓存/通知/外部交互副作用拆成独立 checklist；
  Investigation 与 Reviewer 必须扫描每个相关 full-content 实现 entry 的成功/失败分支，不能用返回值或 `SecurityContext` 状态变化覆盖其他
  material effect。多机制/检查面必须读取每个决定性机制自身实现，caller/configuration 不能替代；
- current Engineering QA System Contract、Strategy/Prompt identity 与确定性测试在同一变更中更新。Engineering QA/Web/CLI 组合 96/96、
  docs 442/442 PASS；允许本机 AF_UNIX 的完整 1162 项中 1157 PASS，raw 唯一 4 FAIL + 1 ERROR 精确仍为冻结 V-009 adapter drift 与本机
  Codex binary digest drift，没有 ITER-010 新失败。默认沙箱额外 6 ERROR + 1 FAIL 精确属于 socket permission noise；raw full suite 不写成
  PASS。clean candidate、fresh Conformance 与三题持续现场验证仍须重新执行，run-015 的两个错误 `APPROVED` 和一个 fail-closed 均只保留为
  诊断证据。
