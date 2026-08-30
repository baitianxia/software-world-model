---
id: FINDING-010-214
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [FINDING-010-213, ITER-010-PDR-007, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_routing.py, tests/test_conversational_engineering_tools.py, tests/test_engineering_chat_browser.py, tests/test_engineering_chat_candidate.py, tests/test_engineering_chat_alpha_cli.py, tests/test_engineering_chat_provider_launcher.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_qa_browser.py, tests/test_iteration_010_mvp_value_gate.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: retain-review-obligations-across-evidence-and-separate-answer-from-pure-limitation
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-214：run-091 暴露补证后 Findings 丢失、混合 Limitation 与无关 cognition literal 修复缺口

## Observation and execution evidence

`FINDING-010-213` candidate 已提交为 product commit/tree
`9564760c096c24516112752dea42a163ab905f52 / 2c2211d6f58d2d1dc95a221213dca8e776275dbe`。DeepSeek 官方 pricing 页面在
`2026-08-30T16:41:45.304Z` 由 in-app Browser fresh 可见检查；capture 文件 SHA-256 为
`6ca9bfb4fb86eb03d980a10b288ccb5bce7601ca210a8e11973bb8ef63ed31b8`，可见文本 digest 仍为
`sha256:9c9dd4d22764599ade403c0ba6cd95abcb947810d5230ee95cb96a56a62d7668`。validated launcher preparation 在
`2026-08-30T16:43:03.575710Z` 返回 `ALLOWED_OFF_PEAK`，receipt digest 为
`sha256:0f5e9af55fa40c09fc67ef9d9859fae5710eeda355a2d71a3ec0b9947d1c872e`；credential、Source Read 和 Provider dispatch 在 preparation
时均为 0。

唯一 launcher 完成 `run-091-mvp-experience` 的 4 个隔离 Conversation、5 个冻结 Turn。terminal 状态为
`STOPPED_AFTER_DISPATCH`，内部 receipt digest 为
`sha256:0aa74901b73a2062166dc803c7185da69c132e4ae82dab6c6fb1032bcaef3394`。Ark 38 个 call 中 37 个完成，1 个在 request bytes 已发送后发生
`REMOTE_DISCONNECTED / PROVIDER_OUTCOME_UNKNOWN`；TLS/credential/HTTP 均为 `38/38/38`，pre-dispatch failure 为 0，retry 为 0。
DeepSeek 没有形成 first-real-fallback，dispatch/credential/TLS/HTTP 均为 0；人工重复审批与 Production Activation 仍为 0。

turn-scope/pricing-capture/session/launch/terminal/Ark DB/DeepSeek DB 文件 SHA-256 分别为：

- `192c9475a944b20b6db166abcc2ae20e979d9c1cc9ef947ecfe77f79cad02751`
- `6ca9bfb4fb86eb03d980a10b288ccb5bce7601ca210a8e11973bb8ef63ed31b8`
- `8ee08fda5b9385db66f5d123733dc447bba5ad3bf5415636c8e838191574e8b6`
- `f90b000c93195bb1ec84a3096d48fbaf5fca97a4d4575465711e6c060d2b8f49`
- `33598ecd9037031fd0341a6e7b12e120e202951c6f41f2018c421e76e5fe7f5a`
- `8ae89d12da98a7eb3930d15db305ea6855ac8d201ef59d065f0868ae0b531b09`
- `0f539b3df4c6127e4b2a90005b287ed8e49b3701f314994f6d1ce8e79dd6672c`

逐题 dispatch 为 `6/15/3/0/14`。Q1 以 `REVIEWED_LIMITATION` 成功、Q4 以零 dispatch
`APPLICATION_INPUT_CLARIFICATION` 成功；Q2 在 Turn 15-call 上限处以 `REVIEWER_PRE_DISPATCH_REJECTED` 失败，Q3 以
`AGENT_MODEL_CALL_REJECTED / PROVIDER_OUTPUT_INVALID / STRUCTURED_OUTPUT_INVALID` 失败，Q5 是合法 no-retry
`REVIEWER_MODEL_OUTCOME_UNKNOWN`。Q1 页面虽然交付，但把多项已确认源码调用写进零 Claim 的 LIMITATION，Citation 数为 0，未满足 exact-revision
引用要求；因此 run-091 整体仍为质量 FAIL，不能称 MVP。

## Exact first divergences

1. Q1 的 Primary 已取得当前 SUPPORT 与一个 material BOUNDARY，却选择 `LIMITATION / claims=[]`，并在正文陈述旧关系删除、新关系写入和缓存调用等
   肯定事实。现行结构只要求 LIMITATION 零 Claim 且至少一个 Boundary，Reviewer 又漏掉 global completeness defect，因而形成“成功但零 Citation”的
   混合事实/边界答案。mixed current SUPPORT + BOUNDARY 必须改由 ANSWER 的 Claim/Citation 与 Boundary 共同表达；LIMITATION 只允许零 SUPPORT 的纯
   material unresolved boundary。
2. Q2 的初次 focused Review 经 `FINDING-010-213` 新的 distinct-category slot 成功走完
   `valid FINDINGS → non-JSON prefix → valid FINDINGS`，证明 run-090 修复生效。该 Review 同时包含需补证 caller-effect Findings 和无需补证的
   audit-only Finding。Primary 选择 Source action 后，Application 立即把整组 `review_findings/pending_review` 清空；后续 Package 扩张、Draft 重建时看不到
   原 rejected Draft 与 Findings，又绑定三个 resolved/non-material acquisition Boundary。最终 focused Review 的 Claim/evidence assessment 全部闭合，
   但仍产生三个 global audit-only Findings，并错误返回 `decision=APPROVED`；第 15 个 call 后已无 repair/redraft authority，Turn 在下一 Reviewer
   pre-dispatch 失败。最早偏差是补证动作错误消费 Review correction state，不是 15-call authority 本身。
3. Q3 的 current-Turn World Model 只投影四个 mall-admin `OmsOrder*ServiceImpl` literal，均不指向用户所问 mall-portal 路径。Primary 选择未列入
   `allowed_exact_values` 的 `OmsPortalOrderServiceImpl`，decoder 以 “the first Source search query must copy one cognition-derived target
   literal” 正确拒绝；generic repair 又逐字返回同一非法搜索。若 allowed cognition literal 均不 material，bounded repair 必须改走不同、更加
   source-native 的合法 WORLD_MODEL_QUERY，而不是重复非法 literal 或为了过校验选择无关 literal。
4. Q5 的 post-dispatch unknown 仍不可 retry/fallback；Ark 全程没有 pre-dispatch unavailable，故 DeepSeek 0 dispatch 是正确 route 结果，不是
   DeepSeek 被禁止或人工授权缺失。

## Decision and disposition

这是 `system-contract / systemic` Finding，不按 mall、题号、Provider、语言、类名、Finding code 或 Observation ID 特判。

1. evidence-required Review 仍先强制一个合法 Tool action，且 replacement Draft 仍须至少新增一个 Observation。执行该 action 后，Application 不再清空
   sealed rejected Draft、Review digest 与全部 ordered Findings；它把状态标记为 post-evidence correction，允许继续补证或基于扩张后的 current
   Package redraft，但新 Evidence 不得抹掉任何 no-evidence Finding。只有真正产生 replacement Draft 后才消费这组 correction state；exact rejected
   Draft 继续被拒绝。
2. `LIMITATION` 只在 current SUPPORT 为 0 且至少有一个 current material BOUNDARY 时可用，正文只能表达纯 unresolved boundary。只要 current
   SUPPORT 非空，混合事实与边界必须使用 `ANSWER`，每项肯定事实进入 Claim 并绑定 current SUPPORT/Citation；这使 Q1 类零 Citation 成功在 Primary
   output boundary 失败关闭，而不再依赖 Reviewer 猜测。
3. final output preflight 冗余列出 resolved-acquisition candidate IDs，明确它们不是 complete-Package inventory；除非 current User Message 明确询问
   acquisition diagnostic 且正文实际回答该诊断，不得为“保险”复制到 Draft Boundary。first-Source cognition-literal diagnostic 则映射到单义
   `USE_A_MATERIAL_ALLOWED_COGNITION_LITERAL_OR_A_DIFFERENT_WORLD_MODEL_QUERY` directive；相同非法搜索继续失败关闭。
4. 协议升级为 `conversational-engineering-agent@19 / conversational-engineering-agent-no-tools-prompt@19 /
   ENGINEERING_AGENT_PRIMARY_INPUT@19 / ENGINEERING_AGENT_REVIEW_INPUT@11 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@14`；output schemas、两次 repair、
   15-call Turn authority、4-Review 上限、Tool/Source fuse、route、retry、fallback eligibility、PDR-007 freshness、接收方和 Production 边界均不变。
   Agent/Model 边界 58 tests、相邻十二模块 148 tests 均 PASS，外调 0；fresh run-092 仍须执行，run-091 不追认为质量或 MVP PASS。

该变化细化既有 Application/Primary owner，不改变组件职责，故不需要新 ADR。本 Finding 与同步后的
`SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 是 current system write-back。
