---
id: FINDING-010-071
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-070]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: project-predecessor-package-full-content-and-last-broker-rejection-into-verification-control
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-071：补证控制面必须包含前序 Package 已读路径与最近 Broker 拒绝

## Observation and evidence

run-025 Q2 的 Verification input 按 `FINDING-010-004` 正确只携带 gap 后新增 raw Result；旧调查内容只经 current sealed Package 进入。
但 `consumed_full_content_paths` 只从新 raw Result suffix 计算，没有把 Package `support/citation` 中已经完整读取的 exact-source locator 投影为
已消费路径。补证模型因而在读取 `DynamicAuthorizationManager` 后，又读取前序 Package 已有的
`CommonSecurityConfig` 与 `SecurityConfig`，没有把剩余动作优先用于 gap 明确要求的 `DynamicSecurityMetadataSource`。这不是旧 raw Result
泄漏，而是 Package 内容与单次 locator control 没有闭合。

Q3 的 Review `model_call_bb2939d84b2544018854bee9efd2242d` 正确把最终 401/403 response mapping 识别为缺少自定义 handler
implementation 的 material gap。该实现不在本次 exact 12-file SOURCE allowlist 中；Verification 先执行
`search RestAuthenticationEntryPoint → read → search RestfulAccessDeniedHandler`，随后连续两次提议已执行过的
`search RestAuthenticationEntryPoint`。Broker 两次以 `DUPLICATE_ACTION_INTENT` 拒绝，既有 no-progress fuse 正确关闭该题。完整 Ledger
与 `prior_action_intents` 已含拒绝依据，但 role input 没有直接标出“最近动作已被 Broker 拒绝及原因”；在安全上限只剩一次无进展余量时，
该重要控制状态埋在长 Ledger 中。

## Decision and disposition

- Verification 的 `consumed_full_content_paths` 由 predecessor Package 中 `EXACT_REVISION_SOURCE` 的 full-content locators 与 gap 后新
  Result full reads 做稳定并集；旧 raw Result 仍不进入角色输入。Package 已有完整内容对应的新 search locator 机械移出
  `eligible_locator_references`，模型不能重复读取。
- 角色输入新增可信派生的 `last_broker_rejection`：仅当当前 attempt 最近一次相关 Broker Decision 为 `REJECTED` 时，投影 decision、
  proposal、reason 和固定响应规则；成功的新 Decision 会清空它。它不授予新操作或路径，只把已经在 append-only Ledger 中的控制事实
  提升为显式当前状态。
- Prompt 要求最近拒绝非空时只能选择真正不同的 registered action，或基于当前 Package/Result 诚实 FINISH；不削弱 duplicate/no-progress
  拒绝，不重试、不自动合成结论。

回归覆盖 predecessor Package full path 出现在 consumed set、同路径新 search locator 不再 eligible、最近 duplicate rejection 的 closed
投影以及无拒绝时为 null。该变化保持 Source/FS/Shell/network/credential authority 为 0，不扩大本次 mall allowlist，不读取
`src/main/resources`，不执行 Production Activation。
