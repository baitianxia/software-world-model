---
id: FINDING-010-210
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [FINDING-010-209, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_routing.py, tests/test_conversational_engineering_tools.py, tests/test_engineering_chat_browser.py, tests/test_engineering_chat_candidate.py, tests/test_engineering_chat_alpha_cli.py, tests/test_engineering_chat_provider_launcher.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_qa_browser.py, tests/test_iteration_010_mvp_value_gate.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: make-claim-coverage-semantic-and-rewrite-contract-response-kind-aware
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-210：run-087 暴露语义 Claim 覆盖与 Limitation 重写冲突

## Observation and execution evidence

`FINDING-010-209` candidate 已提交为 product commit/tree
`c66bcc47461c0758874903e1d882e1f645fadc2b / 1d82c834a33dd1a3bb8ae6bf028b4639492b81e0`。DeepSeek 官方 pricing 页面在
`2026-08-30T13:42:47.195Z` 由 in-app Browser fresh 可见检查；capture 文件 SHA-256 为
`45ea5152a19e0889b282e9a982aff27513462afbb699f4744808b25230a82ff1`，可见文本 digest 仍为
`sha256:9c9dd4d22764599ade403c0ba6cd95abcb947810d5230ee95cb96a56a62d7668`，周末全天闲时没有变化。

唯一 validated launcher 完成 `run-087-mvp-experience` 的 4 个 Conversation、5 个冻结 Turn；terminal 状态为
`STOPPED_AFTER_DISPATCH`，receipt digest 为
`sha256:eab0e4dc7051f9b134dcf8042b7e9ac6945c3b62cb97c4047c3ad374b3746d4a`。Ark 创建 14 个 call：10 个完成，4 个得到
sealed `429 / AccountQuotaExceeded / TooManyRequests`；这四个 HTTP failure 都符合 trusted unavailable policy。DeepSeek fallback 因而在
first real preflight 取得周末 `ALLOWED_OFF_PEAK` active receipt，共创建 43 个 call：42 个完成，1 个在 request bytes 已发出后发生
`REMOTE_DISCONNECTED / PROVIDER_OUTCOME_UNKNOWN`。Provider retry、人工重复审批和 Production Activation 均为 0。

turn-scope/session/pricing-capture/launch/terminal/Ark DB/DeepSeek DB 文件 SHA-256 分别为：

- `1685f552a8e2e2681acc1faa46f38a7d2dbe0b83621e47d16ebd8d3d0945fdaf`
- `55fdd17abae5beb204f4fa09c9bdf00858927ec23204fd770b7a0a6c0a7c2567`
- `45ea5152a19e0889b282e9a982aff27513462afbb699f4744808b25230a82ff1`
- `3865f280675b7d33e0893b864adb6c6aba0753fe7d32b29066126ccbeb842d79`
- `368b0b955c606976c38c9d26bc1fd992cd7f488decffd758abae86fc0613f068`
- `02c99abaaee0d14f60bf1eac1bce31e5efb2e22d1e4c7c2b4cc02b90fa29a36f`
- `4f4c9dbb9a2737e8d98ec46a8df198402f5e05596a25802d6b75d8317242e695`

逐题 dispatch 为 `26/15/2/0/14`。Q1、Q2、Q5 以 `AGENT_REVIEW_LIMIT_REACHED` 失败；Q3 在 Ark 429 后的
DeepSeek call 成为 post-dispatch unknown，按 no-retry policy 失败关闭；Q4 fresh Conversation 继续以
`APPLICATION_INPUT_CLARIFICATION`、零 dispatch 正确隔离。整体仍为质量 FAIL，不能称 MVP。

## Exact first divergences

1. Q1 的 Ark attempt 已形成 7-Claim Answer，comprehensive Review 通过，focused Review 要求收窄 caller→callee effect；下一次 Ark call
   才返回 429，fresh fallback executor 从 sealed Turn Context 重新执行符合 attempt-local isolation。DeepSeek successor 的 rejected Draft
   Claim 数保持 `4 → 5 → 6 → 6 → 6`，每次 Primary input 的 reviewed Draft digest 都与前一 Review 完全一致，证明
   `FINDING-010-209` 的 exact edit base 已真实生效，不再是无状态重建缺口。
2. 这四次 DeepSeek comprehensive Review 却依次把 exact-revision footer、一个已覆盖所有相关调用的 grouped provenance Claim、已经明确写出
   “删除/插入后调用 cache delete”的 Claim，以及已经单列的 cache exact-revision Claim 判成
   `GLOBAL_COMPLETENESS_MISSING_CLAIM`。Reviewer 在第三、四轮否定的 assertion 已逐字或语义存在于 ordered Claim inventory；当前规则只强调
   “正文物质断言必须有 Claim”，没有同时明确 coverage 是 semantic/many-fragment-to-one，导致 Reviewer 按 phrase/atomic-call 继续拆分。
3. Q2 的 rejected Draft 是合法 `LIMITATION / claims=[] / three Boundaries`。Reviewer 连续要求把“当前证据无法确认 requested sequence”及相邻
   file/search diagnostics 增加为 Claim；Primary 又受 `LIMITATION` 必须零 Claim 的 closed branch 约束，只能原样或局部改写。旧
   `review_rewrite_contract` 的 global-completeness Claim exception 没有按 response kind 收窄，因而同时投影了“可增加 Claim”和“Limitation
   禁止 Claim”两个互斥方向。
4. Q5 先重现同一 Limitation/global-completeness 冲突，随后改为带 Claim 的 Answer；第四次 comprehensive Review 又仅因正文没有命名 opaque
   Boundary ID 或复述 raw Observation 而要求删除 structured Boundary binding。该 ID 本来就是非正文的 Evidence binding；正文只应披露仍未解决的
   material requirement，不应显示 opaque ID 或 raw audit metadata。
5. Q3 的单次 DeepSeek `REMOTE_DISCONNECTED` 是可审计的 post-dispatch unknown，不可 fallback/retry；它不授权本地猜测结果，也不是上述
   Review 收敛问题的修复对象。

## Decision and disposition

这是 `system-contract / systemic` Finding，不按 mall、问题、Provider、语言、类名、revision 字符串或 Finding code 特判。

1. Primary 与 Reviewer 的 Claim coverage 改为 semantic，而不是每个 phrase、call 或 sentence 一个 Claim。一个 grouped Claim 只要完整保留
   category、scope、condition、certainty、negation 和 local ordering qualifiers，且 current SUPPORT 覆盖这些内容，就能覆盖多个正文 fragment；
   Reviewer 在产生 global-completeness Finding 前必须检查全部 ordered Claims，禁止为语义已覆盖 assertion 再制造 redundant Claim。
2. 正文 heading/footer 若只把已枚举结论归属于 `turn.binding.repository_revision` 的 exact revision，则是受信 provenance context，不是新的业务
   domain conclusion；不同或虚构 revision 仍是 concrete defect。纯粹表述“current evidence 未确认/未建立 requested relation、order、effect 或
   guarantee”的 material Boundary 不是 affirmative Claim。关于 file/search/tool/model 内容的 affirmative diagnostic 仍须 SUPPORT-bound，否则从
   Limitation 删除或收窄，不能借 Boundary 逃逸。
3. same-Package rewrite contract 必须投影 rejected `response_kind`。global-completeness 增加 Claim 的 exception 只直接适用于 `ANSWER`；
   `LIMITATION` 必须保持零 Claim，并通过删除/收窄相邻 affirmative diagnostic 收敛为纯 material Boundary。只有原正文已有 assertion、current
   SUPPORT 可绑定且不增加新物质结论时，才可转换为 ANSWER 并枚举它。
4. structured Boundary ID 是 binding，不要求出现在正文或复制 raw Observation。Draft 已陈述 material unresolved requirement 并绑定对应
   Boundary 时，Reviewer 不得仅以 opaque ID 未被命名或 raw metadata 未披露为由返回 Finding。
5. 协议升级为 `conversational-engineering-agent@15 / conversational-engineering-agent-no-tools-prompt@15 /
   ENGINEERING_AGENT_PRIMARY_INPUT@15 / ENGINEERING_AGENT_REVIEW_INPUT@8 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@10`；output schemas 保持
   `engineering-agent-work-state-proposal@2 / engineering-agent-independent-review-proposal@6`。route、15-call Turn authority、4-Review 上限、
   Tool/Source fuse、repair 上限、retry、fallback eligibility、接收方和 Production 边界均不变。直接与相邻 Chat/route/launcher/Browser 共
   144 项定向测试 PASS、外调 0；fresh run-088 仍须验证真实 Answer/Review，run-087 不追认为质量或 MVP PASS。

该变化细化既有 Application/Primary/Reviewer owner，不改变组件职责，故不需要新 ADR。本 Finding 与同步后的
`SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 是 current system write-back。
