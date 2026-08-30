---
id: FINDING-010-204
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai-infrastructure, quality, operations]
depends_on: [FINDING-010-179, FINDING-010-198, FINDING-010-203, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_routing.py, tests/test_conversational_engineering_tools.py, tests/test_engineering_chat_browser.py, tests/test_engineering_chat_candidate.py, tests/test_engineering_chat_alpha_cli.py, tests/test_engineering_chat_provider_launcher.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_iteration_010_mvp_value_gate.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: bind-observations-in-application-and-close-unbound-diagnostic-effect-scope-and-review-capacity
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-204：run-082 暴露未声明诊断绕过、caller scope 自相矛盾、复核容量和 Observation ID 抄写四个缺口

## Observation and execution evidence

`FINDING-010-203` 的 candidate 已提交为 product commit/tree
`8208c425ed3bfa6e79bd10ce4fa9a4feae314af6 / a576749d9018a66ff35ffdb2b746d265e12c768a`。首次 exact launcher 准备
`run-081-mvp-experience` 因沿用的官方 pricing check 超过 900 秒 freshness 上限，以
`STOPPED_WITHOUT_DISPATCH / DENIED_PRICING_CHECK` 正确停止；Ark、DeepSeek、Source 和 Turn dispatch 均为 0。turn-scope/session/launch/terminal
文件 SHA-256 分别为
`5174d892ad910a5f7e28953a78d62a687e590304ac19615a680c644284482b7a`、
`56e154ab35e2d843c536803fc8cc69baad0ea97769a2bcbf006a53919b9168ea`、
`adc571765e7bb1b82a9e9dd5e70abca7f62346f65aced323f83ebf729143ddf8`、
`23bba2f61f49e891ab42c0ab0b74e59a8bb64df42eeccc979727ae1eaedb0418`；terminal receipt digest 为
`sha256:44e905e2449cfc87db8ff96d243b2d44c990ff607250c15253273ab12e85b1e6`。这不是 Ark 不可用，也没有触发 fallback。

随后在 in-app Browser 可见地读取 DeepSeek 官方 pricing 页面并形成 fresh capture。页面明确把周一至周五 UTC `01:00-04:00` 和
`06:00-10:00` 列为 peak，其余时间为 off-peak；Asia/Shanghai 周六因此继续匹配既有
`SATURDAY-SUNDAY 00:00-24:00`。capture checked-at 为 `2026-08-30T08:47:45.242Z`，文件 SHA-256 为
`bd99c718d6d7ecdc5c1ca561cfff9542302a39d3eee4b84f0aa512b81e913c93`，可见文本 digest 为
`sha256:9c9dd4d22764599ade403c0ba6cd95abcb947810d5230ee95cb96a56a62d7668`。

fresh `run-082-mvp-experience` 的 DeepSeek preparation admission 为 `ALLOWED_OFF_PEAK`，但 Ark preferred route 全程可用，因此 DeepSeek
保持 0 dispatch。五个冻结 Turn 共形成 4 个 Conversation；Ark dispatch/TLS/credential/HTTP 为 `41/41/41/41`，retry、unknown、人工审批、
DeepSeek dispatch 和 Production Activation 均为 0。turn-scope/session/launch/terminal/Ark DB/DeepSeek DB 文件 SHA-256 分别为
`ae519bfa518a509b95b8e91e110f0a8443da8824f3ceebf17b14917e137b0c4e`、
`84224c62e2381e7c35bbfad29785e18d374568ba6a11212eb37ec376429c1972`、
`657b263a614daa6820cfcbf418f3f43945c3a9680ea6001f9411e3a26163bd55`、
`dfde6e9506725e40d44957295b3883bc3d773f30fdd3ed3d465ad9a119ab2a8e`、
`46172be79aa40bf87868267d28606e26f3a34b1a788d6e978ede86ae49ade349`、
`0f539b3df4c6127e4b2a90005b287ed8e49b3701f314994f6d1ce8e79dd6672c`；terminal receipt digest 为
`sha256:2e71b43e5867426a2269feacd5293d569a2c9b5bea49648c3e8fd8fa72c2f86c`。

逐题结果不是质量 PASS：Q1 与 Q5 为 `SUCCEEDED / ACCEPTED`，Q2 为 `AGENT_MODEL_CALL_REJECTED`，同 Conversation 的 Q3 为
`AGENT_REVIEW_LIMIT_REACHED`，fresh Conversation 的 Q4 继续以 `APPLICATION_INPUT_CLARIFICATION`、Provider dispatch 0 成功。Q5 虽交付，正文仍
披露两次已由 full exact read 闭合的 `SOURCE_SEARCH_FILENAME_MATCH_EARLY_STOP`，并把
`productDao.getAllEsProductList / productRepository.saveAll / deleteById` 的 caller invocation 写成数据库或 Elasticsearch 效果。

## Exact first divergences

1. Q5 最终 focused Review call
   `model_call_fb200f10777a46eea209aec63a2d6793`（output digest
   `sha256:43c8f44f823a398330bf347dec22cd656ae4b734d8e7949a037ec30f78c39eb8`）返回 9 个 caller assessment，却返回 0 个
   boundary relevance assessment。原因不是 resolved-candidate projector 未识别 Search/Read，而是 `@9` 只对
   `draft.boundary_observation_ids` 与 candidate 的交集形成 challenge；Primary 把诊断直接写进 `draft.content` 而未声明 Boundary ID，因而从结构上
   绕过 focused relevance Review。
2. 同一 Review 的 `evidence_boundary` 已明确“只证明 caller invocation、未读 callee implementation”，`draft_scope` 又明确写出数据库读取、
   Elasticsearch 写入/删除，却仍选择 `WITHIN_CALLER_EVIDENCE`。自由文本比较没有闭式语义分类，Application 无法拒绝 Reviewer 自相矛盾的 disposition。
3. Q3 的第三次 Review call `model_call_60cae0c1f32745cfa7e291dc4702d780`（output digest
   `sha256:7ae6284b2b4708e8ff53168c282f143f314ebf4149cf826ddda1b63132826ee9`）正确返回 global no-evidence Finding
   `GLOBAL_COMPLETENESS_TABLE_DB_WRITE_COLUMN_OVERSTATES_EVIDENCE`。该序列已经经过“comprehensive Finding → successor comprehensive approval →
   focused Finding”，需要第四次 focused successor Review 才能闭合；旧 `maximum_reviews=3` 在合法修订到来前失败关闭。
4. Q2 的同包 relevance 修订本身已经删除 World Model diagnostic，但第 20、21 个 Ark call 连续把首个 sealed Observation ID
   `agent_observation_4f68d6052511450d802ca2240d04e936` 分别抄成
   `agent_observation_4f68d605251450d802ca2240d04e936` 和
   `agent_observation_4f68d6052514500d802ca2240d04e936`。两次 raw JSON 都合法，output digest 分别为
   `sha256:8fdf3cd20949f3074e911fd06a9f9493771e7db49c8951122ba152a196dd85a2` 和
   `sha256:b9f373a0950ba16a25242cf88259fd13db6b5287b923dc717e55a0784d9adeee`；Application 因 prefix 不等而正确拒绝。根因是把完全由
   Application 持有、模型没有选择权的 Observation Ledger prefix 作为冗余 Provider copy obligation，既不增加安全性，又消耗一次 repair dispatch。

## Decision and disposition

这是 `system-contract / systemic` Finding；不按 mall、问题文本、语言、数据库、Elasticsearch、方法名、Provider 或 fixture 特判。

1. `engineering-agent-work-state-proposal@2` 删除 Provider-owned `observation_ids` 字段。Application 从 exact current invocation 直接绑定完整有序
   Observation prefix；Provider 若仍输出该字段，closed schema 以 unexpected field 失败关闭。模型仍能读取 current evidence，但不能选择、遗漏、改写或引入
   Observation identity。raw Provider output、exact invocation 和 sealed proposal 保持可重算；该绑定不授予事实、Tool、Review 或 Delivery authority。
2. resolved-acquisition projector 对每个 candidate 形成 challenge，不再与 Draft 声明 ID 求交。challenge 同时密封
   `draft_declared_boundary_reference`。focused Reviewer 必须检查完整正文并在
   `MATERIAL_TO_USER_REQUEST / RESOLVED_AUDIT_ONLY / NOT_DISCLOSED_IN_DRAFT` 中选择：material 只有在用户要求且 Draft 已绑定 Boundary 时可通过；
   未绑定且正文也未披露时可用 `NOT_DISCLOSED_IN_DRAFT` 通过；其余已披露或 stale-reference 的 audit-only 情况必须给出 global no-evidence Finding。
3. 每个 caller challenge assessment 新增 non-empty closed `draft_semantic_scopes`：
   `CALLER_INVOCATION / SOURCE_VISIBLE_LOCAL_ORDER / CALLEE_IMPLEMENTATION_OR_RETURN /
   DATABASE_OR_EXTERNAL_STATE_EFFECT / CONSUMER_VISIBLE_RUNTIME_EFFECT`。没有 cited implementation 时，只允许前两类形成
   `WITHIN_CALLER_EVIDENCE`；Reviewer 若把 effect scope 与 within disposition 组合，Adapter/Application/Response Control 均失败关闭。语义分类仍由 fresh
   Reviewer 承担，Application 不做自然语言关键词判错。
4. Reviewer 上限改为 4，以容纳一次 comprehensive rewrite 和一次 focused rewrite；Agent steps 从 12 收紧为 11，因此最坏组合仍是原有
   `11 + 4 = 15` per-Turn dispatch authority。Tool action 8、Source File/Byte fuse、Provider retry 0、fallback-only-on-trusted-unavailability、总 Session
   budget、外部接收方和 Production 边界均不改变。
5. 协议升级为 `conversational-engineering-agent@10 / conversational-engineering-agent-no-tools-prompt@10 /
   ENGINEERING_AGENT_PRIMARY_INPUT@10 / ENGINEERING_AGENT_REVIEW_INPUT@4 /
   engineering-agent-work-state-proposal@2 / engineering-agent-independent-review-proposal@4`。直接与相邻 Chat 边界共 132 项定向测试通过后，仍必须提交
   clean candidate 并执行 fresh run-083 五题 Browser successor；run-081/082 永久保持 preparation evidence、preferred-route positive evidence 和质量 FAIL，
   不因本次本地处置追认为 MVP。

该变化只细化 Engineering Conversation 现有 Application/Reviewer ownership，没有改变组件职责或架构 owner，故不需要新 ADR。本 Finding 与同步后的
`SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 是 current system write-back。
