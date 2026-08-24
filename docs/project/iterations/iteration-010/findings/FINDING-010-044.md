---
id: FINDING-010-044
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-043]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_model_source.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: update-current-engineering-qa-contract
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-044：Observation 集合闭包仍允许冗余正文，需确定性投影而非整题拒绝

## Observation and evidence

`FINDING-010-042/043` 修复后的 clean candidate `34f0496e09e3e55ad2e771df03a7af4b2804fabc` / tree
`5479d65093c70723d5b43b1036239b9ab64ec8ac` 先取得 fresh DeepSeek Conformance 2/2 PASS，Result digest
`sha256:e3f1b58c3e2fdafd41fc736453a083160d648723aae3d1e8edd75591d922ceca`，request 2、retry 0、actual model
`deepseek-v4-pro`。随后 fresh Session Authority
`sha256:f8f790fa504024a58e9cb28ceef9bff5b448d502e8b166079b325f6aa6ebb8fc` 提交原现场题“登录流程是怎样的？”。

该题完成 Understanding、4 次 Investigation 和 Answer，共 7 次 dispatch；model call
`model_call_57532d45e8994486926e1813d4db0590` 返回的 DIRECT_ANSWER 已简洁、完整覆盖 Controller → Service 密码校验/disabled 检查 →
`SecurityContextHolder` → JWT → 登录审计，并另有成功/失败结果与日志字段 Claim。但 Answer 还生成一个 USER_VISIBLE_PROCESS Claim，重复
绑定 DIRECT_ANSWER 已完整覆盖的同 7 个 observation。既有“跨用户可见 Claim 不得重复 observation”规则将整题以
`material observations must not repeat across user-visible answer claims` 失败关闭，Review 未发生。

这次 failure 证明硬拒绝能防止重复正文，却不符合最小正确处置：后续 Claim 没有新 observation，也没有新用户可见事实；保留首次覆盖的
DIRECT_ANSWER、把完全冗余 Claim 留在开发者详情即可得到不丢事实且不重复的正文。只有“既重复旧 observation 又引入新 observation”的
部分交叠无法安全拆句，仍必须失败关闭。

会话已优雅停止；terminal receipt digest
`sha256:7cef9c589773c8bb7f56dee3cf6a805df7b5ea185185089d24a880a34e43ec06`，accepted question 1、dispatch 7、retry/switch 0、
Production Activation `NOT_EXECUTED`，Gateway/launch/terminal 文件均为 `0600`。旧 run 只作为失败证据。

## Decision and disposition

- Application 按 Claim 顺序构造 default body：首次 observation 覆盖保留；后续 Claim 的 observation 若已被完整覆盖，则从默认正文确定性投影
  到开发者详情；若只部分交叠则 `CONTROL_STATE_DENIED`；coverage-only 空 observation Limitation 继续保留；
- 默认正文最终仍须覆盖 Package observation 的精确全集，不能借投影丢失新事实、拆改模型文本或伪造 Claim；Answer Prompt 明确该规则但不依赖
  Prompt 才保证去重；
- current Engineering QA System Contract 与 Application 测试同步拥有“全冗余投影 / 部分交叠拒绝”语义。该变更不是题目、工程、类名或
  Provider 特判，必须以新的 clean candidate、fresh Conformance 和 fresh session 重跑三题。
