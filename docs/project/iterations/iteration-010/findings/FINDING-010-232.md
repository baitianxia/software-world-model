---
id: FINDING-010-232
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai, quality, operations]
depends_on: [FINDING-010-229, FINDING-010-230, FINDING-010-231, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: preserve-focused-reviewer-semantic-choices-during-contract-repair-and-separate-failure-local-reachability-from-effects
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-232：run-103 暴露 Review repair 语义擦除与 failure follow-up 目标漂移

## Observation and execution evidence

validated Engineering Chat launcher 在 product commit/tree
`9b60eac249bb9c17d377f47cc9e06f4332563c78 / a286362b38e2d20d3a0dc149c847e5fa01a33151` 上完成
`run-103-mvp-experience` 的 4 个隔离 Conversation、5 个冻结 Turn，并正常停止。Browser 在
`2026-08-31T04:13:10Z` fresh 读取 DeepSeek 官方 pricing page；visible-text digest 仍为
`sha256:9c9dd4d22764599ade403c0ba6cd95abcb947810d5230ee95cb96a56a62d7668`，当前周一 `12:13 CST` 命中
PDR-007 的 `MONDAY-FRIDAY 12:00-14:00` 闲时。Ark 每个有模型调用的 Turn 都形成一个 sealed
`429 / AccountQuotaExceeded`，DeepSeek fallback 因而在 first real preflight 激活 `ALLOWED_OFF_PEAK` receipt。

逐题结果为：

- Q1：`FAILED / REVIEWER_MODEL_CALL_REJECTED / STRUCTURED_OUTPUT_INVALID`，Ark 1 + DeepSeek 13 = 14 dispatch；
- Q2：`SUCCEEDED / ACCEPTED`，Ark 1 + DeepSeek 9 = 10 dispatch，1 个 exact Source Citation 与 fresh Review/Delivery；
- Q3：同一 Conversation 的 failure follow-up 为 `FAILED / AGENT_MODEL_CALL_REJECTED / STRUCTURED_OUTPUT_INVALID`，Ark 1 + DeepSeek 7 = 8；
- Q4：fresh Conversation 的“这些失败也会回滚吗？”形成 `APPLICATION_INPUT_CLARIFICATION`，dispatch 0；
- Q5：`FAILED / AGENT_PRE_DISPATCH_REJECTED`，Ark 1 + DeepSeek 10 = 11；最后一个 DeepSeek call 在 active receipt 到期前完成，下一次
  preflight 发生在 600 秒 valid-until 之后。由于 terminal 没有密封该次 rejected decision 的独立 reason code，“duration expiry”只作为
  时间证据支持的 inference，不冒充已密封 owner verdict。

terminal receipt digest 为
`sha256:14a10f7353e11e4a71e6769f99080b5b0849345d0296044138c244a48d169ec9`，状态
`STOPPED_AFTER_DISPATCH`。总 dispatch 43；Ark 4 个全部为 sealed HTTP failure，TLS/credential/HTTP 均为 `4/4/4`；DeepSeek
`39/39` completed，3 次 TLS acquisition、36 次 connection reuse，post-dispatch unknown、retry、人工审批与 Production 均为 0。
shared logical-Turn budget 因此把每题合计保持在 15 以内，`FINDING-010-230` 的安全修复取得完整 live 证据。

session、turn scope、pricing capture、launch、terminal、Ark DB 与 DeepSeek DB 的 SHA-256 分别为：

- `789f0d64a1ee3d9a45d487506a1ac526dce26e8dbe1c286fc13534a0b1300d59`
- `e2772c96c552111b03a3f49b5badca77623a0850c0941e3e436a483ce07e008b`
- `652e60ff4aed810ae15afcea3ebdf6cc8c81cab2b88f5297f4e9a36741e4ba41`
- `973ea3a65282283e99beb71ecdec01260068ff6c9b48de6ea5d6814eca2520a7`
- `848a896597d3375d9e440f7e552e159ebee744796d0e1bd8e52c5812df6fc766`
- `28ae4cac0c60e389e3ca5b1b00686ee4b66bf1193e7531398455782ca9e8a23f`
- `c1be11cf735171a8f0023a799062bb12dcbecb912120936f5b992b4a9d4fe2b9`

## Exact first divergences

Q1 的 focused Reviewer 已把 caller-only Source 无法证明 delete/insert/cache 等 effect label 识别为 concrete Claim defect，并创建
claim-scoped Finding；但同一 Review 的 challenge assessments 又全部返回 `WITHIN_CALLER_EVIDENCE`，触发 focused closure validator。
旧 closed-contract repair 虽有“不得删除真实缺陷”的 prompt，却允许 replacement 任意改写所有 Review fields。repair 随即把 `DEFECT`
改成 `SUPPORTED`、删除 concrete Finding；最后一次还留下 `decision=FINDINGS + findings=[]`，只因另一个 redundancy guard 才偶然阻止错误
交付。最早偏差因此是 Application 没有把 Reviewer 已作出的语义选择变成 repair 守恒面，而不是 decision 文案本身；把空 Findings 自动升级
为 APPROVED 会把真实 defect 错误放行。

Q3 的每个 Primary invocation 继续把 Q2 的“普通下单顺序”作为 goal，`resolved_referents` 为空。comprehensive Reviewer 虽发现本轮要求
缺失，但同包 rewrite 只追加“transaction/exception/commit 未确认”的通用 caveat并重复上一答案；最后的 exact-repeat repair 仍逐字返回 rejected
Draft。这里还存在一个语义折叠：若 full caller Source 显示 `orderItemDao.insertList` 之后的有序语句且没有 local recovery，条件式
“该调用 throw/abrupt completion 时后续 local statements 未到达”是 caller control-flow 结论；早先调用是否成功、是否持久化、commit/rollback
与外部消息效果则分别未知。旧 Reviewer 把 transaction/effect unknown 反向扩散成 local reachability 也 unknown，无法给 Primary 一个
evidence-safe 的完整 correction。

两处都是跨工程的 Review/Conversation 合同缺口，不是 mall、订单、中文“失败”、具体方法或 DeepSeek 特例。

## Decision and disposition

1. focused DEFECT/exceeded closure mismatch 的 repair input 从 prior Review 投影 exact
   `decision / claim_assessments / requirement_coverage_assessment / findings` semantic anchor；final preflight 重复 projection、source receipt 与
   digest。Application 在 decode 前机械恢复这些字段，repair 只能修改 focused challenge assessment arrays。anchor 穿过不同 category 的
   第二个 bounded repair；不能删除 defect 或静默取得 approval。无法闭合时仍失败关闭。
2. semantic anchor 仍是 untrusted Reviewer choice，不是 Evidence、事实或 trusted Finding instruction；它只保留同一 Reviewer repair 前后的
   选择一致性。Application 不生成 Finding、不把 decision 改为 APPROVED，也不扩大两次 repair 或 15-dispatch authority。
3. Primary `work_state_reference_policy` 明确 current User Message 是当前 goal authority，previous goal 只是 Context；active rewrite contract
   明确当前 requirement 是 edit target，旧 Answer、通用 caveat或 Work State goal 不能替代本轮 delta。
4. Primary/Reviewer 对 generic failure 必须区分 exception/abrupt completion 与 unsuccessful normal return；source-visible local reachability、
   prior-call/callee effect、persistence、commit/rollback 和 remote/consumer effect 分别审核。缺少 transaction evidence 不能抹掉 full caller
   Source 已支持的 local reachability，也不能让 local order 证明持久化或回滚。
5. protocol family 升级到 `conversational-engineering-agent@29 / prompt@29 / ENGINEERING_AGENT_PRIMARY_INPUT@29 /
   ENGINEERING_AGENT_REVIEW_INPUT@19 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@24`。Review output、Draft/Answer、Tool/Source、route、budget、fallback、
   retry 与 Production contracts 不变。

模型协议测试 `37/37`、相邻 Engineering Chat/route/authority 定向测试 `137/137` PASS；第一次误包含不存在 test module 的组合命令以
`ModuleNotFoundError` 退出，不计 PASS，随后用实际 test files 重跑通过。run-103 永久保持 Quality FAIL；fresh committed successor 必须在
同一 standing scope、fresh official off-peak evidence 与 600 秒 active receipt 内紧凑执行原五问，验证 Q1 defect-preserving closure 与 Q3
current-requirement failure semantics，同时不得把 Q5 的时间 inference 写成 Provider availability failure。
