---
id: FINDING-010-227
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai, quality]
depends_on: [FINDING-010-226, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_tools.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: require-exact-current-user-requirement-coverage-assessment-in-every-review
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-227：run-100 的 Q3 重复旧答案，而 fresh Reviewer 没有审核本轮 requirement coverage

## Observation and execution evidence

唯一 validated Engineering Chat launcher 在 product commit/tree
`18c2e15653fe0dc3c82b38725cbe23e51f52defd / c71bf18b2e1dbe18ce66eec5265d54d8f845ebc2`
上完成 `run-100-mvp-experience` 的 4 个隔离 Conversation、5 个冻结 Turn，并正常停止。terminal receipt digest 为
`sha256:4e154295dbdd68283d10f81f201ebc878869aafdbe0537a0925b4c2e4047548d`。

逐题 dispatch 为 `12 / 10 / 6 / 0 / 11`。Q1、Q2、Q3、Q5 的 UI 均显示 `SUCCEEDED / ACCEPTED`，Q4 继续以零 dispatch
形成 `APPLICATION_INPUT_CLARIFICATION`。Q2 首次通过 run-099 后新增的 navigation-only opaque READ 取得完整
`OmsPortalOrderServiceImpl.java` 与真实 `generateOrder` 实现，证明 `FINDING-010-226` 的 Source 修复已越过旧偏差。

Q3 的 exact current User Message 是：沿用上一轮，在订单项批量插入失败的条件下，分类哪些后续数据库写入一定尚未执行，以及哪些消息或
其他副作用仅凭当前源码不能确认。Primary 第一个 Q3 call 已收到该原文、prior Conversation、previous Work State 与同文件 exact-source
revalidation option，且成功执行 full Source Read；最终 Draft 却几乎逐字重复 Q2 的普通下单流程答案，没有回答失败点之后的顺序分类和
Unknown。comprehensive Reviewer 随后把全部 Claim 标为 `SUPPORTED` 并返回 `APPROVED`；focused Reviewer 也没有产生与本轮目标相关的
Finding。UI 的 ACCEPTED 因而是 Reviewer 漏判，不是质量 PASS。

Ark 4 个 dispatch 均形成 sealed `429 / AccountQuotaExceeded / PROVIDER_HTTP_ERROR` trusted unavailable；DeepSeek 随后 35/35
completed，TLS acquisition/reuse 为 `3/32`。post-dispatch unknown、retry、人工审批和 Production 均为 0。因此本问题不是 Ark、DeepSeek、
fallback admission、standing authority 或 transport 不可用。

session、turn scope、pricing capture、launch、terminal、Ark DB 与 DeepSeek DB 的文件 SHA-256 分别为：

- `9c36c3a10cd3a5f1aec299e7860c267a3f07cda5ad011a19f6ded79770855293`
- `28040b2ea4ca0a7a47d7b8838c8af4029f532053ba0a00855f1b2a7192341fb0`
- `58eb7914fc5d219e9cb7224acc480169bddb9c40afe8cf1b5bbfa61f38842bf5`
- `0a3fc5c82183f6ee65c917cad5075736c52c127db30f93d579f84a92a4060934`
- `043feeaacfae48a271882aa1fe85a53a22dee76c1e6500360c5c8b58bc2c6847`
- `23a22ed7a3c627bb4166df11450d1ca0ae59e6482931b95547238efc98b32447`
- `51c8f19e2ccfae523c15d03dfbe9d722efcfb3ab4692626534a3d681854a3ca3`

## Exact first divergence

旧 Review contract 只要求逐 Claim 的 evidence `SUPPORTED/DEFECT` assessment、完整 Draft audit 与 global completeness Finding。它没有一项
typed、可封存且必须逐字绑定 current User Message 的 requirement-coverage assessment。于是“Draft 中已有的 Claim 都受证据支持”可以与
“Draft 回答的是上一轮问题而非本轮问题”同时成立，Application 仍只能按旧 typed body 授权交付。自由文本 Prompt 中已有 current User
requirement 不足以让 Application 重算该审核结论。

这是 Review/Delivery 跨模块语义缺口，不是 Q3 题面、订单方法名、中文措辞或 DeepSeek 特例。

## Decision and disposition

1. 每个 comprehensive 和 focused Review 都必须返回一个 typed `requirement_coverage_assessment`，包含 exact
   `current_user_requirement`、non-empty `coverage_summary`、closed disposition 与 nullable `finding_code`。
2. `current_user_requirement` 必须逐字等于 current User Message。`FULLY_ADDRESSED` 只能使用 null finding；若 Draft 回答旧问题，或遗漏、
   反转、错分本轮要求的 material category/distinction/order/Unknown，则使用
   `MATERIAL_REQUIREMENT_MISSING_OR_MISALIGNED` 并绑定一个 `claim_index=null` 的 global Finding。Finding 是否要求补证仍由实际缺口决定。
3. Application 在 model decode、sealed Review identity 与 Delivery closure 三层重算 exact requirement、disposition、Finding 与 decision；未
   fully addressed 的 Review 不能 `APPROVED` 或交付。focused Review 的 exact Finding set 允许加入且只允许加入这一 typed coverage Finding，
   不恢复其他 unbound comprehensive Finding。
4. Review input 与 final preflight 显式投影 current-requirement challenge、prior Answer/Work State 不可替代本轮目标，以及 supported Claims
   不等于 requirement coverage。exact-repeat prior assistant content 作为 review lead 投影，不由 Application 以文本启发式自动拒绝合法的
   “请重复”请求。
5. protocol family 升级到 `conversational-engineering-agent@27 / prompt@27 / ENGINEERING_AGENT_PRIMARY_INPUT@27 /
   ENGINEERING_AGENT_REVIEW_INPUT@17 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@22`，Review output 为
   `engineering-agent-independent-review-proposal@9`，sealed Review 为 `ENGINEERING_AGENT_REVIEW@4`。route、15-call authority、4-Review、
   Tool/Source budget、fallback、retry 与 Production 边界不变。

这项变化写回 `SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 与 active Slice。它不改变组件职责，故不需要新 ADR。run-100 永久保持
Quality FAIL；六模块相邻定向测试 `157/157` 与路由测试 `19/19` PASS，fresh run-101 才能验证真实 Reviewer 是否阻断或修正同类追问错答。
