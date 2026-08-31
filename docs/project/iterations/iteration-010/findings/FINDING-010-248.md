---
id: FINDING-010-248
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai, quality, operations]
depends_on: [FINDING-010-196, FINDING-010-227, FINDING-010-247, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: declared-api-shape-does-not-prove-transformation-location-and-narrow-claim-does-not-cover-broader-content
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-248：run-117 把返回类型与调用者无转换错误提升为 DAO 映射位置

## Observation and execution evidence

run-117 绑定 product commit/tree
`6047baebf64964b0e274df9362e8f367f3596e95 / 4bca053587e52309990bd4fd01562aea59c428bf` 与 mall exact revision
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`。第一次 launcher 在 Provider、Source 与 listener 前因新 Session config 为 `0644` 而被
owner-private gate 拒绝；修正为 `0600` 后，同一 preparation 创建 listener，Provider dispatch 仍从 0 开始。

冻结 Q4 随后由 Ark `glm-5.3` 完成 8 个 model calls，TLS/credential/HTTP 为 `8/8/8`，DeepSeek、request retry 与 post-dispatch unknown
均为 0。Browser 显示 `SUCCEEDED / ACCEPTED`、4 个 Citation、fresh comprehensive/focused Review 与 Delivery Authorization；Repository
声明已正确绑定 exact `EsProductRepository.java:L12`，说明 `FINDING-010-247` 的 locator/cross-resource 修复生效。terminal receipt digest 为
`sha256:bc626946e1eeba5dc9af98e20aa9026c4a3a2e90dbf4fc28b726e39d6e4473ea`。

独立 exact-revision 复核仍发现答案把“`EsProductDao.getAllEsProductList` 声明返回 `List&lt;EsProduct&gt;`，Service 没有单独 Java 转换”提升为
“实体到 Elasticsearch 文档的转换发生在该 DAO 查询的结果映射中”。本次授权 Evidence 没有读取 mapper/DAO implementation，且
`src/main/resources` 被明确排除；返回类型与 caller 中缺少显式转换都不能定位值在 DAO、mapper、framework 或其他层如何被填充或转换。

## Exact first divergence

Primary 的第五个结构化 Claim 只陈述 declared return shape、Service 直接传递结果、caller 内无单独 Java conversion，以及 Repository
declaration；正文却额外断言转换发生在 DAO result mapping。现有 semantic Claim coverage 指令没有让模型把“转换位置”识别为更宽的独立
affirmative assertion。comprehensive Reviewer 又把窄 Claim 误当作覆盖该正文，focused Reviewer 只审核 Application 从结构化 Claims
生成的 caller/callee challenges，因此两层均错误 APPROVED。

这不是 mall、DAO 或 Elasticsearch 特判，而是任意接口签名、返回类型、泛型、caller omission 与 unread implementation 之间都存在的通用
证据边界：declared shape 不能证明 population/mapping/conversion/loading/persistence 的实际位置；一个较窄 Claim 也不能替正文中的较宽位置
断言取得证据资格。

## Decision and disposition

1. Primary policy 明确 declared parameter/return/generic type 只证明 API shape；一个已读 caller 没有显式 transformation，不能把转换定位到
   callee、mapper、framework 或其他 unread implementation。
2. 若正文断言值在某一层被 populated/mapped/converted/loaded/persisted，该位置必须由独立 Claim 原样枚举并绑定 direct implementation
   SUPPORT；只声明 type shape 或 caller absence 的 Claim 不构成 semantic coverage。缺少证据时必须陈述 implementation location 未建立。
3. comprehensive Reviewer 必须据此拒绝更宽正文；focused caller challenge 的既有职责、Domain、Source、route、budget、fallback 与
   Production hold 不变。
4. 协议族升级为 `conversational-engineering-agent@33 / prompt@33 / ENGINEERING_AGENT_PRIMARY_INPUT@32 /
   ENGINEERING_AGENT_REVIEW_INPUT@22 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@27`。Primary output `@4` 与 Review output `@9` 不变。

## Verification

定向 model-boundary 回归覆盖 Primary/Reviewer prompt、Primary/Reviewer typed policy、comparison contract 与 final preflight 冗余投影；
model boundary、Agent、Tool、route、Conversation、runtime、Browser、holdout、live harness 与 model-source 相邻集合共 `159/159` PASS，文档检查
`654 current documents` PASS。clean commit 与 fresh Ark run-118 同题复验仍在本 Finding 的同一开发闭环中；run-117 只证明网络与 Citation
locator 修复生效，不取得质量或 MVP PASS。
