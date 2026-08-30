---
id: FINDING-010-211
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [FINDING-010-210, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py, src/software_world_model/application_services/conversational_engineering_agent.py]
tests: [tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_routing.py, tests/test_conversational_engineering_tools.py, tests/test_engineering_chat_browser.py, tests/test_engineering_chat_candidate.py, tests/test_engineering_chat_alpha_cli.py, tests/test_engineering_chat_provider_launcher.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_qa_browser.py, tests/test_iteration_010_mvp_value_gate.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: close-focused-review-body-and-resolve-all-findings-per-rewrite
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-211：run-088 暴露 focused Review 自相矛盾与逐缺陷收敛

## Observation and execution evidence

`FINDING-010-210` candidate 已提交为 product commit/tree
`1825efc99d5f2ee40e441cc743b8405bb205d9c0 / 5e754564f26df2ea0e50b3421eb8f7144770fdea`。DeepSeek 官方 pricing 页面在
`2026-08-30T14:23:47.077Z` 由 in-app Browser fresh 可见检查；capture 文件 SHA-256 为
`de6ebe9ea1e1c951a2bc9c91a209cef85e6803f1442fe6dc07b45ea2bb21be20`，可见文本 digest 仍为
`sha256:9c9dd4d22764599ade403c0ba6cd95abcb947810d5230ee95cb96a56a62d7668`，周末全天闲时没有变化。

唯一 validated launcher 完成 `run-088-mvp-experience` 的 4 个 Conversation、5 个冻结 Turn；terminal 状态为
`STOPPED_AFTER_DISPATCH`，receipt digest 为
`sha256:fe9b5a10c382c91f8e31226b7ece0a85dd336f206ea6555e2ca742da58e39d2b`。Ark 创建 4 个 call，全部得到 sealed
`429 / AccountQuotaExceeded / TooManyRequests`，均符合 trusted unavailable policy。DeepSeek fallback 在 first real preflight 取得周末
`ALLOWED_OFF_PEAK` active receipt `sha256:c6ee6ecec6aa4a0afbfa1720a9d0e8f74054e69b0ec337e5e43d18420660f569`，共创建 53 个
call：52 个完成，1 个在 request bytes 已发出后发生 `REMOTE_DISCONNECTED / PROVIDER_OUTCOME_UNKNOWN`。Provider retry、人工重复审批和
Production Activation 均为 0。

turn-scope/session/pricing-capture/launch/terminal/Ark DB/DeepSeek DB 文件 SHA-256 分别为：

- `3691c55d7159474ac0fe67553e76b964760ce75dd6dace489cd56c567cf8c761`
- `f449181234e769613746aec81189188c210ee13be4c115f241228140328a73a6`
- `de6ebe9ea1e1c951a2bc9c91a209cef85e6803f1442fe6dc07b45ea2bb21be20`
- `b0a07c80f40fd00c2d94b3be0657580d2fafd38e8fae46d866904e800bde7aa6`
- `29ae5c98bdeb9426aac01ee2561064f4f5cedcf53d5676e629806020d423c9c6`
- `136d64368ddce4110ba1949feec0de3444f2baf7b6a8ec44b74c9ffe5659641b`
- `dabb5a0ed3a4b6b479b04922e9d0d21f5e86c581be67c4523225ea536fffe412`

逐题 dispatch 为 `16/15/12/0/14`。Q1 以 `REVIEWER_PRE_DISPATCH_REJECTED`、Q2 以
`AGENT_REVIEW_LIMIT_REACHED`、Q3 以 `AGENT_MODEL_OUTCOME_UNKNOWN`、Q5 以 `REVIEWER_PRE_DISPATCH_REJECTED` 失败；Q4 fresh
Conversation 继续以 `APPLICATION_INPUT_CLARIFICATION`、零 dispatch 正确隔离。整体仍为质量 FAIL，不能称 MVP。

## Exact first divergences

1. Q1 的初始 Draft 已把 transaction/cache unknown 留在 Boundary。comprehensive Review 与 focused Review 各两次复用 Finding code；旧
   decoder 因 identity 重复各触发一次 same-profile repair。后续 Reviewer 又逐轮只报告一个新的 global-completeness 或 unsupported
   diagnostic defect，Primary 也只修当前一个局部，15 个 DeepSeek slot 在下一次 Review 前耗尽。Finding code 只是本 Review 内的引用身份，
   identity 冲突不应在不改变 Finding message、binding、顺序或 remediation 的情况下浪费独立语义 call。
2. Q2 的 comprehensive Review 先只指出 caller effect 扩张；Primary 收窄后，后续 Review 才依次提出纯 Boundary 不应加 Claim、正文 relevance
   和 “set orderId/orderSn before insertList” qualifier。最后一次 rewrite 已补 qualifier，但第 4 次 Review 结束后没有确认容量。根因不是需要第
   5 次 Review，而是 Reviewer 没有在一次完整 Draft audit 中同时报告已经可见的全部独立 material defects，Primary 也没有被明确要求在一个
   replacement 中解决全部 ordered Findings。
3. Q3 的 `LIMITATION / claims=[]` 在 unsupported diagnostic 删除后已成为纯 material Boundary，comprehensive Review 也返回 APPROVED。
   focused Review 随后把所有 challenge 判为 closed、`findings=[]`，却返回 `decision=FINDINGS`。structured repair 没有只把 redundant decision
   改为 APPROVED，反而制造 `MISSING_MATERIAL_BOUNDARY_FINDING`；下一轮又声称 sealed input 中已存在的 Boundary IDs 缺失，最终发生合法
   post-dispatch unknown。Application 不能把 Reviewer 明示的 FINDINGS 静默升级为 APPROVED；正确闭合是同 profile repair 只改冗余
   decision，并继续由 Reviewer 自己署名 approval。
4. Q5 的 focused Review 对五个 caller challenge 都给出
   `draft_semantic_scopes=[CALLER_INVOCATION,SOURCE_VISIBLE_LOCAL_ORDER] / disposition=WITHIN_CALLER_EVIDENCE`，却同时把 Claim 0 标为
   DEFECT 并返回 `CLAIM_EXCEEDS_CALLER_EVIDENCE` Finding；它还为未在 Draft 披露的 resolved acquisition Boundaries 生成 audit-only
   Findings。Primary 只删除 Boundary references，没有收窄被 Finding 指名的 Claim/content，第二次 focused Review 重复同一矛盾并再次复用
   Finding code。旧 decoder 只校验 “EXCEEDS 必须有 Finding”，没有校验反方向闭合，因而允许 assessment、Claim verdict 和 Finding body
   彼此冲突。

## Decision and disposition

这是 `system-contract / systemic` Finding，不按 mall、问题、Provider、语言、类名、revision 字符串或具体 Finding code 特判。

1. Reviewer 必须先审核完整 Draft，并在一次 Review 中报告全部已经观察到的独立 material defects；不得故意逐轮只返回一个。每个独立
   Finding 使用不同 local code。code 只作本 Review 内引用 identity：只有完全未被任何 focused assessment 引用的重复 code，model-boundary
   adapter 才可以只做稳定后缀 disambiguation；message、requires-evidence、Claim binding 和顺序均不得改变。任何被 assessment 引用的重复
   code 保持原值并由 decoder 失败关闭，不能按数组位置猜测引用关系。
2. focused Review 必须双向闭合：exact DEFECT Claim index set 等于
   `CLAIM_EXCEEDS_CALLER_EVIDENCE` challenge 投影；exact Finding code set 等于 exceeded caller challenge 与 audit-only Boundary relevance
   assessment 引用的 code set。`WITHIN_CALLER_EVIDENCE` 不能与未绑定的 caller-effect Finding 并存，focused Review 不能引入 comprehensive
   global-completeness Finding。Decoder 与 Application seal 分别在 model boundary 和 typed port boundary 重算其可见的 exact closure。
3. `decision` 是 typed body 的冗余摘要：findings non-empty 才是 FINDINGS；全部 Claim/focused assessment closed 且 findings empty 时必须是
   APPROVED。若 repair diagnostic 指出 “non-approved Review requires Findings” 且 prior body 已成功闭合，Reviewer 只把 decision 改为
   APPROVED；不得制造 Review-contract Finding。Application 不生成或静默升级 approval。
4. same-Package Primary rewrite 必须在一个 replacement 中解决全部 ordered Findings。caller-effect Finding 同时收窄 challenged Claim 与对应
   content fragment；unsupported diagnostic 删除或收窄为纯 material Boundary，不得只改无关 Boundary reference，也不得把 Boundary 提升为新
   affirmative Claim。返回仍保留 Finding 指名语义缺陷的 replacement 继续失败关闭。
5. 协议升级为 `conversational-engineering-agent@16 / conversational-engineering-agent-no-tools-prompt@16 /
   ENGINEERING_AGENT_PRIMARY_INPUT@16 / ENGINEERING_AGENT_REVIEW_INPUT@9 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@11`；output schemas 保持
   `engineering-agent-work-state-proposal@2 / engineering-agent-independent-review-proposal@6`。route、15-call Turn authority、4-Review 上限、
   Tool/Source fuse、repair 上限、retry、fallback eligibility、接收方和 Production 边界均不变。直接与相邻 Chat/route/launcher/Browser 共
   146 项定向测试 PASS、外调 0；fresh run-089 仍须验证真实 Answer/Review，run-088 不追认为质量或 MVP PASS。

该变化细化既有 Application/Primary/Reviewer owner，不改变组件职责，故不需要新 ADR。本 Finding 与同步后的
`SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 是 current system write-back。
