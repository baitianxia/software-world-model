---
id: FINDING-010-209
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [FINDING-010-208, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_routing.py, tests/test_conversational_engineering_tools.py, tests/test_engineering_chat_browser.py, tests/test_engineering_chat_candidate.py, tests/test_engineering_chat_alpha_cli.py, tests/test_engineering_chat_provider_launcher.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_qa_browser.py, tests/test_iteration_010_mvp_value_gate.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: seal-rejected-draft-and-repeat-exact-draft-reference-domains
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-209：run-086 暴露 Reviewer successor 丢失 rejected Draft

## Observation and execution evidence

`FINDING-010-208` candidate 已提交为 product commit/tree
`9939d92c3a94fb508f0691c1b437874aa4870d52 / a1c0bf24c4f9e9320f47decabe6675a95cc30e7f`。DeepSeek 官方 pricing 页面在
`2026-08-30T12:45:52.674Z` 由 in-app Browser fresh 可见检查；capture 文件 SHA-256 为
`cf0099638d861cd6968f94bb023630a569df460cf8c1ead05215666d61f693f0`，可见文本 digest 仍为
`sha256:9c9dd4d22764599ade403c0ba6cd95abcb947810d5230ee95cb96a56a62d7668`，周末全天闲时没有变化。

唯一 validated launcher 完成 `run-086-mvp-experience` 的 4 个 Conversation、5 个冻结 Turn；terminal 状态为
`STOPPED_AFTER_DISPATCH`，receipt digest 为
`sha256:0051ade701cb4a2dded21d91a637f7bfc185e7b903463ba922429f93681bb705`。Ark 共完成 49 次真实 HTTP dispatch：47 次
`COMPLETED`、2 次在 bytes 已发送后发生 `REMOTE_DISCONNECTED / PROVIDER_OUTCOME_UNKNOWN`。Provider retry、人工重复审批和
Production Activation 均为 0。没有 Ark HTTP 前 trusted unavailable，故 DeepSeek dispatch/TLS/credential/HTTP 保持
`0/0/0/0` 正确；两个 post-dispatch unknown 都不能改路重发。

turn-scope/session/pricing-capture/launch/terminal/Ark DB/DeepSeek DB 文件 SHA-256 分别为：

- `e63322e59fd2e627b52d572a0d69556ce3355b7aacacb15aa24746b6aa716cf1`
- `2e3389416bf2cbdd86a884b109e1a5b4f57ee0d3b856354a987ca4f51910c10d`
- `cf0099638d861cd6968f94bb023630a569df460cf8c1ead05215666d61f693f0`
- `f2d2a776a3001082787b7880af0154db91e2d3907356ca210a9d384a1ccfed92`
- `ba6f0dd769ecc095d065d17b096389d1af212b85c9731e42b139ae11833648a7`
- `a317cf836dd4fd1fd0e657101c909efef9a48306165ce4c7d61f67e5caa59ff6`
- `0f539b3df4c6127e4b2a90005b287ed8e49b3701f314994f6d1ce8e79dd6672c`

逐题 dispatch 为 `14/11/15/0/9`。Q1、Q5 分别在 Reviewer call 发出后 outcome unknown；Q2 在 Primary
`CLOSED_OUTPUT_CONTRACT` repair 后以 JSON 尾随字符失败；Q3 在下一 Reviewer 前耗尽原有 15 次 Turn authority；Q4 fresh Conversation
继续以 `APPLICATION_INPUT_CLARIFICATION` 零 dispatch 正确隔离。整体仍为质量 FAIL，不能称 MVP。

## Exact first divergences

1. Q2 的初始 Answer 使用一个 BOUNDARY Observation ID 作为 Claim SUPPORT。sealed Primary input 已有两个分开的 exact reference arrays，
   但 final preflight 没有重复这些 exact domains。第一次 repair 删除了错误 ID，却多输出一个末尾 `}`，从 closed contract 倒退到 JSON
   syntax；既有 bounded repair policy 正确禁止再次调用。不能通过删改 Provider 文本、放宽 disposition 或增加 repair 次数来掩盖该偏差。
2. Q3 的 Application loop 本地保存了 `last_draft` 和 exact Review，但 successor `EngineeringAgentInvocation` 只传
   `review_findings/review_digest`，没有传被拒绝 Draft。Primary 是无状态模型，只能从 Findings、Work State 和 Evidence 重建原稿；连续重写的
   Claim 数因而从 `5 → 10 → 7 → 13`，每轮都引入新的相邻断言和新的审核缺口，而不是对同一 Package 做 targeted rewrite。
3. 最后一次扩张又加入“没有方法级 `@Transactional` 就没有事务原子性保证、已完成写入不会自动回滚”等现有 Source 并未证明的结论。这表明
   缺失 exact edit base 是通用合同问题，不是某个 mall 类、问题或 Provider 的单点措辞问题。
4. Q1/Q5 的 post-dispatch outcome unknown 没有本地可修的先行产品偏差，也不构成 DeepSeek fallback eligibility；route、retry 和预算保持原样。

## Decision and disposition

这是 `system-contract / systemic` Finding，不按题面、工程、Provider、类名、Claim 文本或 Observation ID 特判。

1. Reviewer 返回 Findings 后，Application 必须把 exact rejected `EngineeringAgentAnswerDraft` 与 Findings、Review digest 一起传给下一次 Primary
   invocation。三者必须共同存在或共同缺席；Draft 的 Turn、origin Work State、canonical digest 和 SUPPORT/BOUNDARY references 必须与当前
   invocation 精确一致，任何缺失或错配都在 Provider 前失败关闭。
2. `ENGINEERING_AGENT_PRIMARY_INPUT@14` 的 `review_feedback` 投影 rejected Draft 的 exact rewrite surface、ordered Claim index、exact
   support/boundary bindings 和 Draft digest，不向 Provider 重发无编辑用途的内部 identity fields。同 Package、无需新 Evidence 的 successor
   必须以它为 edit base，只删除、收窄、限定、重排或重述 Finding 指向的内容；不得
   从 Work State 重建全文、增加新的用户可见物质断言或相邻细节。只有 global completeness Finding 明确指出原正文已有但 Claim inventory
   未枚举的断言时，才能增加对应 Claim entry；rejected Draft 本身仍是 untrusted model-authored data，不是 Evidence。
3. `ENGINEERING_AGENT_OUTPUT_PREFLIGHT@9` 必须再次列出当前 ANSWER Claim SUPPORT 与 Draft Boundary 的两个 exact allowed ID domains，明确
   cross-disposition 和 unknown reference 均 forbidden；同时重复 active rewrite contract。该 preflight 只重复 sealed input 的限制，不新增
   Evidence、Tool、Review 或 Delivery authority。
4. 协议升级为 `conversational-engineering-agent@14 / conversational-engineering-agent-no-tools-prompt@14 /
   ENGINEERING_AGENT_PRIMARY_INPUT@14 / ENGINEERING_AGENT_REVIEW_INPUT@7 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@9`；output schemas 保持
   `engineering-agent-work-state-proposal@2 / engineering-agent-independent-review-proposal@6`。route、15-call Turn authority、repair 上限、
   Tool/Source fuse、retry、fallback eligibility、接收方和 Production 边界均不变。直接与相邻 Chat/route/launcher/Browser 共 144 项定向测试
   PASS、外调 0；fresh run-087 仍须验证真实 Answer/Review，run-086 不追认为质量或 MVP PASS。

该变化细化既有 Application/Primary owner，不改变组件职责，故不需要新 ADR。本 Finding 与同步后的
`SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 是 current system write-back。
