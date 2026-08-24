---
id: FINDING-010-042
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [ai-infrastructure, application, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-041]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: update-current-engineering-qa-contract
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-042：异质构建题暴露原子观察上限冲突与 completed-output 失败误分类

## Observation and evidence

账户余额恢复后，fresh DeepSeek Conformance run-010 以 2/2 PASS 签发 Result
`sha256:63a2dbf4fb966092c6c5ac1f3685c9dd02a502ca708cf4666b5a1724afbc39fb`；actual model 为
`deepseek-v4-pro`，request retry 为 0，Production eligibility 仍为 false。由 clean candidate
`7149f736f6fe044a7f5958351018477875b584df` / tree `b734ac8faf0df7a3ff331aae49124eb569f90bd4` 建立的持续会话
`sha256:b63fc4ee5003b005bb164deadf9fb7317292c0ab77f7b7aae30eb88b2bb2e666` 随后完成原登录题，并提交第一道异质题：

> 新开发者要在本地启动并调用 mall-admin 的管理员登录与受保护接口，仓库证据能确认哪些构建依赖和安全接入步骤？哪些运行参数因为本次未授权读取 resources 而必须保留为未知？

该题前 5 次角色调用均完成。第 6 次 Initial Investigation 的 Provider response ID 为
`f85477b3-e8e8-4ee5-a8c1-17b2cdd4a2e9`，model call 为
`model_call_bebda2bb85bc43378aad8d12f5fde79f`；响应是 unique-key JSON，FINISH 对第一项列出 9 条彼此不同的构建与环境事实。
既有 output schema 和 `ChecklistDisposition` 每项最多只接受 8 条，Adapter 因此正确保留 completed response/usage 并标记
`STRUCTURED_OUTPUT_INVALID`。但产品 exact-result fence 只识别无 response 的 `FAILED`，把这类
`COMPLETED + rejected output` 再分类为 `QUALIFICATION_INVALID`；页面显示 Provider binding drift，terminal receipt 也记录了错误 failure code。

这不是 Provider、余额、TLS、credential、model identity 或 Conformance drift：该题恰好 6 次 HTTP dispatch，verified TLS 成功，retry 0、
Provider switch 0，所有 response identity 均为 `deepseek-v4-pro`。它暴露两个相互独立但同时发生的通用缺口：原子完整性要求可能合法地产生
超过 8 条事实，而 completed-output rejection 没有沿 exact binding 保留真实失败语义。

## Decision and disposition

- 每个 Checklist disposition 的原子 observation 上限改为 16，Package 全局 64 条上限保持不变；Application、Initial/Verification
  output schema 和 Prompt 使用同一常量，schema 升级为 `initial/verification-investigation@4`，local contract 升级为 `@6`；不合并或丢弃
  第 9 条事实，也不放宽 evidence/reference closure；
- exact-result fence 新增 `COMPLETED + response + failure_code` 分支，只有 Manifest、provider request、Provider/model/configuration、
  response digest/usage、receipt 与 eligibility 全部精确一致时，才传播真实 `STRUCTURED_OUTPUT_INVALID` 并携带 model call identity；任何一项
  漂移仍保持 `QUALIFICATION_INVALID`；不重试、不消费被拒输出；
- current Engineering QA System Contract 同步写明 1—16/全局 64 的 observation 边界和 completed-output rejection 语义。聚焦 Application、
  Strategy、model-source 测试新增 16/17 边界与 completed rejection 回归；旧会话永久保留为失败证据，不能追认为三题 PASS。
