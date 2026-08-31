---
id: FINDING-010-247
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai, quality, operations]
depends_on: [FINDING-010-196, FINDING-010-228, FINDING-010-232, FINDING-010-233, FINDING-010-246, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: project-trusted-citation-locators-and-forbid-acquisition-intent-echo-as-evidence
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-247：run-116 交付后发现 Citation locator 不透明与检索意图事实化

## Observation and execution evidence

run-114 绑定 product commit/tree
`640dc65bba42acb2f728049ef8a6108e83847b04 / b600e83e295f41e60ec89835bb676e3507d9255b`，只完成 immutable Session、Turn scope、Gateway DB 与 launch receipt 准备。
第一次相对 Session config 被本地拒绝，第二次因 sandbox listener `Operation not permitted` 在 Provider dispatch 前停止；按 immutable fresh-DB
规则，已创建的 Gateway DB 没有被重用或覆盖。Ark/DeepSeek HTTP dispatch 均为 0，run-114 永久保留为 preparation-only evidence。

run-115 使用 fresh Session 和同一冻结 Q4。Ark call 1 完成，call 2 在 HTTP 前形成 typed TLS `PROVIDER_UNAVAILABLE`；trusted availability
owner 因而合法开启周末 `ALLOWED_OFF_PEAK` DeepSeek fallback。DeepSeek 取得 TLS/credential/HTTP `1/1/1`，但返回 definite HTTP 402，Turn
如实失败；Ark dispatch root/TLS/TLS success/credential/HTTP 为 `2/2/1/1/1`，DeepSeek dispatch 1，request retry 与 post-dispatch unknown 均为
0。terminal receipt digest 为 `sha256:b7274a33e05835a31c674cd0fdbbefeeb7f0ed1260b83661b07d206cb83f191c`。

按“确认 pre-dispatch network unavailable 后创建 fresh logical request、绝不重放 outcome unknown”的周期重试规则，run-116 使用新的
Session/Turn identity 再次提交 Q4。Ark `glm-5.3` 的 9 个 model calls 全部 completed，TLS/credential/HTTP 为 `9/9/9`，DeepSeek、request
retry 与 post-dispatch unknown 均为 0。页面形成 `SUCCEEDED / ACCEPTED`、3 个 Citation、fresh comprehensive/focused Review 和 Delivery
Authorization；terminal receipt digest 为 `sha256:a906848ea1124fd4dd957ba8edd2d961f12584e9fb7b7ad48b76750c11d93a61`。这证明
`FINDING-010-246` 的 ordinal output/repair 已走通真实长链，也证明当前不再因 Ark 网络等待。

独立 exact-revision 源码复核随后发现两个 Reviewer 漏判：

1. 答案断言“数据库行到 `EsProduct` 文档的字段映射（SpEL/DTO 转换）位于被排除的 `src/main/resources`（如 mapper XML）”。`SpEL/DTO`
   首次只出现在 Primary call 1 自己编写的 `evidence_need/hypotheses`，并被 World Model/Source Boundary 的 query/request echo 带入后续输入；授权
   Java SUPPORT 与 original User Message 都没有建立该机制或位置。独立本地审计只看到 excluded `EsProductDao.xml` 的 MyBatis `resultMap`，也
   不能把它追写成当时 live Package 的 Evidence。
2. Claim 5 同时断言 `EsProductDao.getAllEsProductList`、`EsProductRepository extends ElasticsearchRepository<EsProduct, Long>` 及二者被
   `EsProductServiceImpl` 注入，却只解析出 Search 中 `EsProductDao.java:L16` 与 full `EsProductServiceImpl.java` 两个 Citation；没有选择
   `EsProductRepository.java` 的 exact declaration Citation。Primary 只能看到长 opaque ref domain 的 ordinal，Reviewer 也只看到 Claim 的 opaque
   resolved refs，二者都没有可靠的 ref-to-locator 对照。comprehensive 与 focused Review 均错误 APPROVED。

## Exact first divergence

第一处系统偏差不是 Ark 网络、Source 检索、ordinal decoder 或 Browser projection，而是 Provider-facing evidence semantics：Application 没有把
每个 Citation ordinal/ref 对应的 trusted exact locator、evidence class、modality、revision 与 content digest 投影给 Primary/Reviewer。
同一个 broad Search Observation 中的 sibling hits 因而容易被误当成互相支持；跨资源 Claim 也无法可靠审核是否为每个独立资源选择了 exact
Citation。

第二处偏差是 acquisition intent 与 Evidence 的分层不完整。模型编写的 action argument、query、`evidence_need`、hypothesis、plan/open item
本来只是待验证意图；当工具或 Boundary 为审计而回显这些字节时，现有 Prompt/Policy 没有明确禁止后续角色把回显当成新的技术事实。seal 只能
证明字节来源与完整性，不能把模型自己的猜测变成 Source truth。

这是跨问题、跨 Provider、跨 Source operation 的系统性证据契约缺口，不是 `mall-search`、`SpEL/DTO`、Repository 类名或 Q4 特判。

## Decision and disposition

1. trusted Application 从每个 SUPPORT Observation 的 authority receipt 重算 ordered Citation options，逐项投影 1-based ordinal、exact opaque
   ref、evidence class、source revision、locator、modality 与 content digest；无 receipt、ref 不存在、revision/identity 不一致或重复必须在模型调用
   前失败关闭。Primary output 仍只返回 ordinal selector，Domain/Browser 仍使用 exact refs。
2. Primary final preflight 只重复每个 Observation 的 ordinal base/count，避免复制整份 locator catalog；语义选择只来自 sealed Primary input。
   Reviewer 的 Package view 单独取得同一 trusted ref-to-locator map，以 exact Draft refs 审核真实引用覆盖。
3. Source Search Citation 只支持自己 exact locator 的结果，不支持同一 Observation 的 sibling hit。一个 Claim 若命名多个独立 material resource
   declaration/behavior，必须为每个资源选择 exact Citation，或拆分/收窄 Claim；import、typed field 或 injection use 不证明被引用类型的声明、继承
   或实现。
4. model-authored tool proposal、argument、query/search text、`evidence_need`、hypothesis、plan、open item 及其 echo 全部只是 acquisition intent，
   不是事实 Evidence。Boundary 只能报告受信结构化 failure/coverage/exclusion/unknown，或保留 original User Message 明确提出的不确定性；不得把只在
   acquisition intent 中出现的机制、位置、关系或行为事实化。
5. 协议族升级为 `conversational-engineering-agent@32 / prompt@32 / ENGINEERING_AGENT_PRIMARY_INPUT@31 /
   ENGINEERING_AGENT_REVIEW_INPUT@21 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@26`。Primary output `@4`、Review output `@9`、Domain、Source、route、
   budget、fallback、adapter qualification 与 Production hold 不变；写回 owner System Contract，无需 ADR。

## Verification

定向回归验证 trusted ordinal-to-locator option 的顺序与字段、缺失 authority receipt 的失败关闭、preflight ordinal base/count、Reviewer policy 与
query-echo prohibition；model boundary、Agent、Tool、route、Conversation、runtime、Browser、holdout、live harness 与 model-source 相邻集合共
`159/159` PASS，文档检查 `653 current documents` PASS。trusted-base plan gate、clean commit 与 fresh run-117 仍在本 Finding 同一开发闭环中
继续，未完成前不得把 run-116 追认为质量或 MVP PASS。
