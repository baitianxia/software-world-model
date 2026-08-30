---
id: FINDING-010-221
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai, quality]
depends_on: [FINDING-010-219, FINDING-010-220, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: anchor-caller-scope-review-to-exact-current-claim-and-strengthen-repeat-rewrite
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-221：run-096 暴露 caller-only Claim 可被 Reviewer 重新解释为数据库效果并触发原样 rewrite

## Observation and execution evidence

唯一 validated Engineering Chat launcher 在 product commit/tree
`63b10ddd4e7563e842e085410187aba9e57c392c / f857e6f8073f3f8c3844193eead27ba43be2bcd9`
上完成 `run-096-mvp-experience` 的 4 个隔离 Conversation、5 个冻结 Turn，并以
`STOPPED_AFTER_DISPATCH` 正常密封。terminal 内部 receipt digest 为
`sha256:1113d51f240e47f2ca6739a8a02123d02c2a91c9eefc95e081ef7639f84c56ce`。

Ark 的 4 个真实 dispatch 全部形成 sealed `429 / AccountQuotaExceeded`；每个非 Clarification
Turn 都合法激活既定 DeepSeek fallback。DeepSeek 的 37 个 call 全部 `COMPLETED`，transport 为
37 dispatch、3 次成功 TLS acquisition、37 次 credential resolution、37 次 HTTP dispatch、0 retry、
0 post-dispatch unknown，证明 `FINDING-010-219` 的 stale/idle rotation 已越过 run-095 的 Q2
最早偏差。人工审批与 Production Activation 均为 0。

逐题 dispatch 为 `11 / 11 / 7 / 0 / 12`：Q1 为 `SUCCEEDED / ACCEPTED`（2 个 exact Source
Citation），Q2 为 `FAILED / AGENT_MODEL_CALL_REJECTED / PROVIDER_OUTPUT_INVALID /
STRUCTURED_OUTPUT_INVALID`，Q3 为 `SUCCEEDED / REVIEWED_LIMITATION`，Q4 为零 dispatch
`APPLICATION_INPUT_CLARIFICATION`，Q5 为 `SUCCEEDED / ACCEPTED`（69 个 exact Source Citation）。
run-096 因而仍为 Quality FAIL，不是 MVP。

turn-scope、pricing capture、session、launch、terminal、Ark DB、DeepSeek DB 文件 SHA-256 分别为：

- `c50998a5eac4af04cc0cb9ca7c4f5acf570747b5ec559379fe1e7bdb41313745`
- `bd3a0809977b66c356d18a841eac3c560824559e4227e8bbde6fdf4e22f40a71`
- `20b9e1019db6671908e52c2e79b94e410fd380ee93da3adc8f29e767e353775a`
- `a0be2c4929dcb29caf36888c802b66e1642c6862146b9583ad62119fcd50535d`
- `2a135e87faa2b77af33894eb8eb7d9cdcafd044bf0f3d5c6f5263cd62c8cd63c`
- `063713a983ded183a2af9873ffa1769b154bcc4147de33bdf0be75d5d96c5b48`
- `6182d2ece5f2e8c625ca928aa999be3900bd097120a9a3062eb480c049ca555b`

## Exact first divergence

Q2 call 14 的初稿把 `orderMapper.insert(order)` 与 `orderItemDao.insertList(orderItemList)` 描述为
数据库写入；focused Reviewer call 16 正确要求把两者收窄为 caller invocation/local order。Primary
call 17 已同时修改正文与 Claim，删除“写入数据库”效果，只保留“调用 expression”的源码局部顺序。

fresh focused Reviewer call 18 却没有只解释该 exact current Claim。它重新声称 Claim “asserts ...
writes ... to the database”，把 `CALLER_INVOCATION` 同时分类成
`DATABASE_OR_EXTERNAL_STATE_EFFECT`，并原样返回同两个 Finding。当前 review input 虽包含完整 Draft，
caller challenge 本身却没有把 exact challenged Claim statement 与“method name 不产生 effect semantics”
作为独立 closed anchor 投影；Reviewer 因而把用户要求、method vocabulary 或先前 Finding 的语义重新
导入当前 Claim。

Primary call 19 发现 current rejected Draft 已经是要求的 caller-only 表述，逐字返回同一 Draft；本地
validator 正确拒绝 `same-Package review rewrite returned the exact rejected Draft`。repair call 20 收到的
generic directive 只说要改变 replacement，仍逐字返回相同对象，同一 validator category 因而按上限
失败关闭。这里不是 Provider transport、fallback、Source authority、dispatch budget或 Adapter JSON
问题；37 个 DeepSeek Provider call 都有完整、parseable、`stop` 输出。

Q3 在 Q2 未交付后只能从当前 Turn 重新调查；它选择了源码中不存在的 `insertBatch` literal，Source
Search 零匹配后诚实交付 Limitation。该结果保留为后续连续性证据，但当前修复先关闭更早的 Q2
Reviewer/Primary 偏差；Q2 成功后的 fresh successor 才能判断 Q3 是否仍有独立问题。

## Decision and disposition

这是 `system-contract / systemic` Finding，不按 mall、题号、中文动词、具体 method、Finding code 或
Provider 特判。

1. 每个 caller/callee challenge 在 `ENGINEERING_AGENT_REVIEW_INPUT@15` 中直接投影
   `exact_challenged_claim_statement`，并明确 scope 只能来自该 exact ordered Claim；User requirement、
   邻接正文、先前 Review/Finding 与 method/call-expression name 都不能给 Claim 增加 effect semantics。
2. Reviewer prompt 与 final preflight 对称重复该闭合规则；语义 scope 仍由 fresh Reviewer 分类，
   Application 不按自然语言关键词或 operation name 自动批准/拒绝。
3. same-Package exact-repeat repair 对 caller-effect Finding 使用更具体的通用收敛：在正文和 Claim 中
   显式区分 observed invocation/local order 与未确认 callee/database/remote/consumer effect，或删除
   不必要的 challenged assertion；不得再次返回 exact rejected Draft。
4. 协议族升级为 `conversational-engineering-agent@23 /
   conversational-engineering-agent-no-tools-prompt@23 / ENGINEERING_AGENT_PRIMARY_INPUT@23 /
   ENGINEERING_AGENT_REVIEW_INPUT@15 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@18`；wire output schemas、
   两次 distinct-category repair 上限、15-call authority、route、budget、retry 与 Production 边界不变。
   model-boundary targeted regression 为 `34/34` PASS，相邻 16 模块为 `261/261` PASS；文档/可信父门禁、提交与
   fresh run-097 仍按当前连续工作计划执行。

该变化细化既有 Application/Reviewer owner，不改变组件职责，故不需要新 ADR。本 Finding 与同步后的
`SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 是 current system write-back。
