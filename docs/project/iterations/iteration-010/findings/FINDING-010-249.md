---
id: FINDING-010-249
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai, quality, operations]
depends_on: [FINDING-010-247, FINDING-010-248, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: explicit-java-declaration-requires-direct-selected-declaration-citation
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-249：run-119 的显式 Repository 继承声明仍由 caller typed use 取得证据资格

## Observation and execution evidence

run-118 与 run-119 均绑定 product commit/tree
`200b326b8023b8a58ddf6775a9dc117d101c46f2 / 1f05e4043b2169a3856a09b28a486df18fe0d276`、mall exact revision
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` 以及 fresh Ark `glm-5.3` qualification
`CC-ARK-CHAT-NO-TOOLS-001:sha256:b1529aadb00d18e4c46791944e8050917d26b85193cd131150f0daeb9f8291fa`。

run-118 的冻结 Q4 先完成 9 个 Ark HTTP dispatch；第 10 个 Ark logical dispatch 在 credential 与 HTTP 前发生 verified-TLS failure，故
trusted-unavailable verdict 合法激活 DeepSeek fallback。DeepSeek 的唯一 dispatch 明确返回 HTTP 402，Turn 以
`AGENT_MODEL_CALL_REJECTED` 失败关闭。Ark TLS/credential/HTTP 为 `10/9/9`，DeepSeek 为 `1/1/1`，request retry 与 post-dispatch unknown
均为 0；terminal receipt digest 为 `sha256:cef1610ada551cdfbf265a69d07bc9312ca7074c45bebe0a437ef03c9a5341ff`。

按 bounded delay 建立的 fresh run-119 随后由 Ark 完成 9 个 model calls，TLS/credential/HTTP 为 `9/9/9`，DeepSeek、request retry 与
post-dispatch unknown 均为 0。Browser 显示 `SUCCEEDED / ACCEPTED`、2 个 Citation、fresh comprehensive/focused Review 与 Delivery
Authorization；terminal receipt digest 为 `sha256:3ef5f34ae9c32e3846fc433d016f04a1b0d68325a6731242b3c280c1c05431b9`。
该答案已把 `FINDING-010-248` 的 transformation location 收窄为“本 Turn 未读取、无法确认”，证明 declared-shape 修复方向生效。

独立 exact-revision 复核仍发现 Claim 与正文明确写出
`EsProductRepository extends ElasticsearchRepository<EsProduct, Long>`，但该 Claim 只选择完整
`EsProductServiceImpl.java` SUPPORT/Citation；页面也只投影 Controller 与 Service 两个 Citation。Service 的 import、injected field 与 receiver
calls 可以证明 caller typed use，却不能证明另一个资源中 Repository interface 的 declaration 或 inheritance。run-119 因而继续 Quality FAIL。

## Exact first divergence

Primary prompt、typed policy 和 Reviewer prompt 已声明 import/typed use 不能证明 referenced type declaration，但 decoder 只机械验证 selected
Citation ref 属于该 Claim 的 selected SUPPORT Observation，没有验证 Claim 中显式 source-shaped declaration 与 selected Citation content 的
关系。Primary 第五个 Claim 因此把 caller typed use 提升为 Repository inheritance；comprehensive Reviewer 把它评为 `SUPPORTED`，focused
Reviewer 又只在同一 Claim 中摘取 receiver-call scopes，漏掉显式 `extends` assertion，最终错误 APPROVED。

这是通用 Citation directness 缺口，不是 Elasticsearch 或 mall 特判：任何 `Type extends Base`、`Type implements Contract` 或中文等价的显式
Java declaration assertion，都必须由该 Claim 实际选择的直接 declaration Source 支撑；同 Package 中未选择的 Citation、import、field、receiver
call 或其他 typed use 都不能替代。

## Decision and disposition

1. Primary 与 Reviewer policy 把显式 Java declaration/inheritance 视为独立 material assertion；缺少 direct Citation 时必须删除、收窄或先取得
   并选择 exact declaration Source。
2. Application 在 Primary decode 后从 sealed current SUPPORT 解析 Claim 实际选择的 Citation content，按 canonical Java resource 组合片段并
   验证 exact declaring type、`extends/implements` relation 与 target type。只有 import、field、receiver call 或 typed use 时返回
   `STRUCTURED_OUTPUT_INVALID`，允许既有最多两次 fresh same-profile format repair；Application 不补造 Claim、不自动扩 Evidence，也不重试
   Provider request。
3. 该机械规则只处理显式 source-shaped declaration；一般自然语言语义仍由 Claim direct-support 与 fresh Review 合同负责。route、budget、
   Source authority、fallback eligibility 与 Production hold 不变。
4. 协议族升级为 `conversational-engineering-agent@34 / prompt@34 / ENGINEERING_AGENT_PRIMARY_INPUT@33 /
   ENGINEERING_AGENT_REVIEW_INPUT@23 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@28`。Primary output `@4` 与 Review output `@9` 不变。

## Verification

定向 model-boundary 回归覆盖 caller import/field/call 不能支撑显式 inheritance，以及选择 exact Repository declaration 后通过；Primary/Reviewer
prompt、typed policy、comparison contract 与 final preflight 均冗余投影该规则。model boundary 模块 `38/38` PASS；Agent、Tool、route、
Conversation、runtime、Browser、artifact、live harness、model-source、public authority 与 MVP gate 相邻集合 `180/180` PASS，文档检查
`655 current documents` PASS。可信父计划门禁、clean commit 与 fresh Ark successor run 仍在本 Finding 的同一开发闭环中。run-118/119
只分别证明安全 fallback 与 Ark 网络恢复，不取得质量或 MVP PASS。
