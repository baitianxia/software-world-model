---
id: FINDING-010-046
kind: implementation-finding
status: superseded
authority: execution-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-038, FINDING-010-045]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_model_source.py, tests/test_engineering_question_strategy.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: update-current-engineering-qa-contract
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
superseded_by: FINDING-010-047
---

# FINDING-010-046：Prompt 级跨 evidence-class 提醒不能阻止过早全局 Unknown

## Observation and evidence

clean candidate `8565fa552bf3ddc2db66205256a0561fe3433ab4` 绑定 fresh DeepSeek
Conformance Result `sha256:77e3d8fef91b1942b103928205a41fd1b40a2fa0016f9be6091b7cff5503f5d6`
启动持续 Alpha，并再次提交用户现场题“登录流程是怎样的？”。Question Understanding 把题目接受为
`USER_VISIBLE_EXPLANATION`，但 evidence needs 只列文档、UI/交互与日志，并附加“避免实现细节”的响应约束。
Initial Investigation 随后只搜索并读取 `REPOSITORY_DOCUMENT/README.md`，在第 3 个调查 Proposal
把全部 checklist disposition 为 `UNKNOWN`，声称没有其他已授权证据；实际 Request/Source Profile 明确仍允许
Controller、Service、JWT Filter、Token Util 和 Security Config 等 `SOURCE` 文件。

Answer/Review 在这个不完整 Package 上经历一次 rewrite 后把 limitation 答案标成 `APPROVED`。页面交付内容因而只说
“当前授权证据未包含登录流程”，没有回答 `/admin/login`、凭据验证、`SecurityContextHolder`、JWT、失败分支或登录审计。
该 Reviewer decision 只证明 Draft 与错误 Package/checklist 一致，不构成用户问题质量 PASS。

会话已优雅停止。terminal receipt `sha256:8f4fcc04691582e3e69d1e7dc4f142e763868ffe5c5117afe0a556a1c4cea48a`
记录 1 个 accepted question、8 次 dispatch、retry 0、Provider switch 0、TLS handshake 1 次成功并复用 7 次，
Production Activation `NOT_EXECUTED`；Gateway、launch 和 terminal 文件均为 `0600`。原始 Gateway 行保留 3 次
Initial Investigation、2 次 Answer 和 2 次 Review 的 provider request ID、model identity、output 与 usage。

## Root cause

- `FINDING-010-038` 只在 Prompt 中要求 non-supported FINISH 前检查其他 evidence class；Application 没有可执行的
  registered-class closure，因而仍会密封模型的过早 FINISH；
- Investigation role input 只有总 source allowlist 和 registered operation names，没有从 exact Source Profile 导出的
  `registered / investigated / untried evidence classes`，Prompt 所说的“registered evidence classes”不是一个明确输入字段；
- Question Understanding 把答案抽象层级错误地当作调查证据边界。用户可见答案可以隐藏实现术语，但工程流程事实仍通常需要 exact Source
  behavior 来证明；
- 这是所有 feature flow、lifecycle、authorization 与 troubleshooting 问题都可能触发的系统性闭包缺口，不是 mall、中文、登录、文件名、
  关键词、fixture 或 DeepSeek 特例。

## Decision and disposition

- Source Broker 从 Request 绑定的 exact Source Profile 导出稳定有序的 registered retrieval evidence classes；Application 为每个
  Investigation Attempt 独立记录实际产生 Result 的 investigated classes，并把 registered、investigated 和 untried 三个集合投影给角色；
- 任何包含 `UNKNOWN / CONFLICT / FAILED` disposition 的 FINISH，只要 untried registered class 非空，就不再密封 Ledger；Application
  追加一个命名下一个 required class 的 GAP，让 fresh Step 消费并继续调查。全部 disposition 已 SUPPORTED 时不强迫读取无关 class；
  Verification Attempt 只对 Reviewer concrete gap 指定的 class 执行同一闭包；
- Question Understanding Prompt 明确：抽象层级控制交付表现，不控制调查证据；询问 feature/flow/lifecycle/authorization/failure behavior
  时必须保留 exact Source behavior evidence need；
- System Contract、Prompt/Strategy identity 和确定性回归在同一变更中更新。定向 Engineering QA 集合 93/93 PASS；完整回归
  1154 项中 1149 PASS，raw 精确保留既有 V-009 Adapter freeze 与 Codex binary drift 的 4 FAIL + 1 ERROR，状态为
  `PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD`。fresh Conformance 和新的三题持续会话仍须在 clean candidate 上执行，旧
  `APPROVED` 不得追认。
