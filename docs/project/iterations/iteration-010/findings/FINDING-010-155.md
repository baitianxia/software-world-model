---
id: FINDING-010-155
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [source, application, ai, quality]
depends_on: [FINDING-010-110, FINDING-010-154, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/application_services/conversational_engineering_tools.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_engineering_question_answering.py, tests/test_conversational_engineering_tools.py, tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: enforce-the-final-source-file-slot-at-model-and-broker-boundaries
target: SYS-CONTRACT-SOURCE-ARTIFACT
---

# FINDING-010-155：late SEARCH 仍可吞掉已为 exact READ 保留的最后文件槽位

## Observation

`run-045-mvp-experience` 首次把 Artifact Session `@4`、双 Cognition、主工程 Agent、Source、Evidence/Review 和 Browser 放进同一真实链。
公开 mall exact revision 中，`UmsAdminServiceImpl.login` 明确调用 `jwtTokenUtil.generateToken(userDetails)`，并由 `insertLoginLog` 记录登录日志；
`JwtTokenUtil.generateToken` 再调用 JWT 实现。真实 Turn 却先给出“`UmsAdminServiceImpl.login` 不可用”的错误 Limitation，随后两个追问分别以
`AGENT_MODEL_OUTCOME_UNKNOWN` 和 `AGENT_REVIEW_LIMIT_REACHED` 失败。

不可变 trace 显示最早可操作偏差发生在 Source 文件预算的模型/Broker 边界，而不是 mall 事实、World Model 或 Web：

- 第一次 `SOURCE_SEARCH("login")` 实际扫描 56 个文件；第二次 `SOURCE_SEARCH("token")` 再扫描 7 个，累计 `63/64`，同时已有未读取的
  opaque locator；
- model-facing closed tool catalog 仍同时暴露 `SOURCE_SEARCH` 和 `SOURCE_READ`，第三次 `SOURCE_SEARCH("generateToken")` 因而合法消耗
  最后 1 个文件槽位；
- 随后的 exact `SOURCE_READ` 被 `SOURCE_FILE_FUSE_EXHAUSTED` 拒绝。Agent 在 Reviewer 三次指出 `MISSING_CLAIMS` 后才利用已有 Support
  形成肯定草稿，但 fresh Review 的调用上限已经耗尽，不能交付。

这不是题面、关键词、类或方法特例。`FINDING-010-110` 与 current Source Contract 已要求 late SEARCH 保留一个 exact locator READ，
但 Broker 的实现只在 `remaining_files > 1` 时把 SEARCH 编译为 `remaining_files - 1`；当恰好只剩 1 个槽位时，它仍允许 SEARCH。
同时 `RESOURCE_RECEIPT` 只投影 actual usage，没有向可信模型边界提供 `maximum_source_files`，所以 Application 无法从现有 closed
tool catalog 中机械删除该 SEARCH。

## Disposition

在不改变任何总预算、单次 SEARCH 上限、Source allowlist、Provider 路线或 Prompt/schema 字段的前提下，完成一个通用双层修复：

1. 每个可信 `RESOURCE_RECEIPT` 同时记录 actual `source_files` 和 Request-bound `maximum_source_files`；
2. model boundary 从 current Turn 的受校验 Ledger receipt 推导剩余预算；当 usage 恰为 `maximum - 1` 且存在未读 locator 时，动态
   tool catalog 只保留 `SOURCE_READ`，structured decoder 对 SEARCH 失败关闭；预算已经耗尽时两个 Source operation 都不再暴露；
3. Source Broker 增加调用方无关的 backstop：只剩 1 个文件槽位、READ/PARSE 已注册且 Ledger 中仍有未读 locator resource 时，任何
   SEARCH 在 Worker 前以 `SOURCE_SEARCH_READ_SLOT_RESERVED` 拒绝；没有未读 locator 时仍允许使用最后槽位，不做过度收紧；
4. 同一路径的多个 locator 按 resource path 归并；已尝试 READ/PARSE 的 resource 不会继续占用保留判定。

确定性回归重现两次 SEARCH：第一次 `56`、第二次 `7`，然后 opaque locator READ 使用最后 `1` 个槽位，累计仍为 `64`；模型目录、decoder、
Broker backstop 和无 locator 兼容路径均通过。三个直接受影响模块共 `73/73 PASS`。该修复不追认 run-045：
`var/iteration-010/slice-001/run-045-mvp-experience/terminal.json` 的 digest 为
`sha256:00ad46545e8d31699ace4ff1f7fa8b6b8cf662a04e86f480698684f1cbf9914f`，保留 2 个 Conversation、4 个 Turn、28 次 dispatch、retry 0、
human approval request 0 和原质量失败。必须用 fresh successor candidate 复验；run-045 不重试、不封存 Result、不移动计划游标。
