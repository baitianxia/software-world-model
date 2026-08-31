---
id: FINDING-010-251
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai, quality, operations]
depends_on: [FINDING-010-250, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_tools.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: exhaustive-draft-content-unit-review-coverage
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-251：run-122 的正文事实绕过 Claim 与 Boundary 审核

## Observation and execution evidence

clean product commit/tree
`3326fdfcc1a5704d02cf461d07d221ec7b03b2ab / d3c5385305ecf2e974ccb7d3a8db542928e45ace` 上，fresh Ark qualification
`ccrun_5f40765e553f4bcd8567da4b85edea49` 以 actual `glm-5.3`、13/13 cases、TLS/credential/HTTP `2/2/2`、retry/unknown 0
通过；result digest 为 `sha256:ab3ca920b1b971c172c57add59f1c6c400749fc22e2bdfdb7f587028a83d34ac`。

run-121 的唯一 Ark attempt 在 HTTP 前形成 typed `TLS_FAILURE / PROVIDER_UNAVAILABLE`，因此 availability-only route 合法进入 DeepSeek；
DeepSeek 在当前 off-peak admission 下完成 TLS/credential/HTTP 后返回 definite HTTP 402。Ark/DeepSeek 各 dispatch 1、request retry 与
post-dispatch unknown 均为 0，terminal digest 为
`sha256:abceabf29e6b879f7c5b36867a5f0bbfb86326ab7b0a445d7b8f9332c025eb64`。用户允许周期性重试后，约三分钟的 bounded delay 只创建新的
logical run-122，没有重放 run-121 的任一 request。

run-122 的 Ark 12 个 calls 全部 `COMPLETED`，TLS/credential/HTTP `12/12/12`；DeepSeek dispatch、request retry、pre-dispatch failure 与
post-dispatch unknown 均为 0。页面形成 `SUCCEEDED / ACCEPTED`、3 Citation、fresh comprehensive/focused Review 与 Delivery，terminal
digest 为 `sha256:788b16677e4ad48699dc74be5eb2a11a51e0eb980e36081f5f955a72e1f409d1`，Production 未执行。该运行证明
`FINDING-010-250` 的 stale resolved-acquisition repair 已越过旧失败，也证明当时 Ark 网络可用。

独立审计仍判定质量 FAIL。最终 Draft 只有 3 个 Claim，分别覆盖 Controller HTTP 调用、Service 接口方法与 ServiceImpl 中的本地调用顺序；
`boundary_observation_ids=[]`。用户可见正文却另行断言 `EsProductDao.getAllEsProductList` 的返回类型“直接是 Elasticsearch 文档实体
EsProduct”、`EsProductRepository` 是 Spring Data repository、`ElasticsearchTemplate` 仅用于搜索/推荐/聚合且不在写链，并陈述转换实现、
Mapper/XML scope 与远程提交/刷新/一致性未知。这些正文语义没有逐项进入 Claim/Citation 或 Boundary binding。comprehensive Reviewer 只审核
3 个 Claim 和 requirement coverage；focused Reviewer 只审核 caller/relevance challenge arrays，最终均返回 `APPROVED`。因此 3 个结构化
Claim 都受支持不等于完整可见答案已受审核。

## Exact first divergence

既有合同允许 Reviewer 对“未枚举的正文结论”返回 global completeness Finding，却没有要求输出一个与完整 `draft.content` 等长、可重算的
覆盖集合。Reviewer 可以跳过不在 Claim inventory、也没有 exact Boundary ID 的句子，再以完整 Claim assessments 和 challenge assessments
通过结构闭合。heading、standalone label 与正文 fragment 的继承语义也只存在 Prompt 规则，没有出现在 sealed Review identity 中。

这是通用 Draft-to-Review coverage 缺口，不是 mall、Elasticsearch、DAO、Repository、转换或中文特判。任何自然答案都可能把实质事实或
Unknown 放在 Claim/Boundary 之外；只验证已枚举对象永远不能证明完整正文已经审核。

## Decision and disposition

1. Application 从 exact `draft.content` 按非空可见行投影 ordered content units，并为每项密封 index、fragment、继承的 Markdown heading/
   standalone-label context 与 digest；超过 128 项时只允许确定性连续分组，不能遗漏正文。每个 comprehensive/focused Review 都必须按 exact
   顺序返回一个 assessment。
2. assessment 使用闭集：`COVERED` 必须绑定至少一个 exact Claim index 或 focused exact Boundary observation ID；
   `BOUNDARY_REVIEW_DEFERRED` 只允许 comprehensive Review 在 Package 确有但被该 focus 隐去 Boundary 时使用，focused Review 禁止继续
   defer；`NON_ASSERTIVE` 不绑定 Claim/Boundary；`DEFECT` 必须绑定一个现有 Finding，且不伪造 coverage reference。Reviewer 必须结合每项
   inherited context 判断完整语义，不能以 identifier overlap 代替语义覆盖，也不能把 material prose 标成 `NON_ASSERTIVE`。
3. final preflight 从 trusted role input 重算 exact Draft content digest、ordered unit identity、Claim/Boundary domains、focus-specific deferral
   policy 和完整 output shape；decode、sealed Review 与 Response Control 再次重算。缺项、乱序、未知 Claim、未选择 Boundary、focused defer、
   unbound defect 或 focused Finding 集不精确均失败关闭。Delivery 还拒绝任何 `DEFECT` 或 `BOUNDARY_REVIEW_DEFERRED`。
4. 该机制机械保证“每个正文单元必须被 Reviewer 显式分类并绑定到 current Draft”，但事实是否真的被某 Claim/Boundary 语义覆盖仍是独立
   Reviewer 的判断；它不伪称本地字符串算法能证明自然语言真值。fresh run 必须验证模型不会把 material prose 滥标为 `NON_ASSERTIVE` 或绑定
   到无关 Claim。
5. 协议族升级为 `conversational-engineering-agent@36 / prompt@36 / ENGINEERING_AGENT_PRIMARY_INPUT@34 /
   ENGINEERING_AGENT_REVIEW_INPUT@25 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@30`；Review output 升为
   `engineering-agent-independent-review-proposal@10`，sealed Review record 升为 `ENGINEERING_AGENT_REVIEW@5`。Primary output `@4` 不变。
   route、Provider adapter、资格、数据披露、Source/Tool/dispatch budget、no-retry 与非 Production 边界均不改变。

## Verification

定向回归使用 run-122-like Draft：heading 下的未枚举 Elasticsearch 文档分类和证据边界句必须各有 ordered content assessment；focused
`BOUNDARY_REVIEW_DEFERRED` 必须失败，两个未闭合正文单元只有各自绑定 global Finding 才能形成 coherent `FINDINGS`。既有 Agent/Model/Tool
fixture 已迁移到新 closed shape；Agent/Model/Tool 直接集合 `82/82` PASS，Conversation、Browser、候选装配、Provider/Session artifact、route、
live harness、model-source、公开 Source authority 与 MVP gate 相邻 15 模块合计 `182/182` PASS。文档门禁 PASS；计划门禁、clean commit、fresh
Ark qualification 和 run-123 同题 live successor 仍须依次完成。run-122 只证明 transport 与旧 exact-read repair，不取得质量或 MVP PASS。
