---
id: FINDING-010-250
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai, quality, operations]
depends_on: [FINDING-010-249, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: unused-same-search-exact-read-blocks-stale-acquisition-unknown
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-250：run-120 把仍可读取的 Controller 误报为检索截断 Unknown

## Observation and execution evidence

clean product commit/tree
`a2e707390ed080ead9399bb6104919e4fe4c8d80 / b252e08a3f47c88cc697f6dfc36331113eaffce2` 上，fresh Ark qualification
`ccrun_39c9ec884fd44498839091acd9ec578d` 以 actual `glm-5.3`、TLS/credential/HTTP `2/2/2`、retry/unknown 0 通过；result
digest 为 `sha256:e63bcf8fe36ae5cb0be512f657b10d2f5cad0bec6b35d2da34f1634533934ca1`。run-120 绑定同一 product、mall
exact revision `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` / tree
`047d79d8588b76013c260f3f1a9565707301a60a`、同一冻结 Q4 与 standing scope。

Browser 真实 Turn 形成 `SUCCEEDED / ACCEPTED`、5 Citation、fresh comprehensive/focused Review 与 Delivery。Ark 7 个 model calls 均为
`COMPLETED`，TLS/credential/HTTP `7/7/7`；DeepSeek dispatch、request retry、pre-dispatch TLS failure 与 post-dispatch outcome unknown 均为
0，Production 未执行。terminal receipt digest 为
`sha256:049e72843bc4fd0266aef0aa0a9eca9d8986c78aa4eac800243a1fcfc2128fde`。run-119 后加入的 direct-declaration gate 已 live 生效：
答案为 `EsProductRepository extends ElasticsearchRepository<EsProduct, Long>` 选择了 Repository L12 的 direct Citation。

独立 exact-revision 复核仍发现答案把“`importAll` 与删除操作在 Controller 层的 HTTP 入口（URL 映射）”表述为“未在当前已读源码中确认，
检索为部分截断结果”。实际 `EsProductController.java` L26 给出 class-level `/esProduct`，L31-L35 给出 POST `/importAll`，L39-L43
给出 GET `/delete/{id}`，L47-L51 给出 POST `/delete/batch`；这些结果已由同一次 `SOURCE_SEARCH` 返回，而且当前 Primary 调用仍有
Controller exact `SOURCE_READ` option 与足够工具预算。Primary 只完整读取 Service 后就把 acquisition diagnostic 绑定为 material Boundary；
comprehensive Reviewer 判定全部要求已覆盖，focused Reviewer 又把该 resolved acquisition Boundary 评为
`MATERIAL_TO_USER_REQUEST`，最终错误 APPROVED。run-120 因物质遗漏与假 Unknown 继续 Quality FAIL，未继续消耗 Q1/Q2/Q5 调用。

## Exact first divergence

Prompt 与 typed policy 已说明 resolved acquisition candidate 默认仅用于审计，但 decoder 没有机械阻止 Primary 在同一次 Search 的 exact
`SOURCE_READ` 仍可用时，选择该 candidate 并据此完成答案。现有 coarse “任一 downstream full read 与 Search support 重叠即可 resolved”
只说明检索过程已有后续动作，不说明每个 material sibling resource 都已读取；Reviewer decoder 也允许模型仅凭题面需要 HTTP 入口，就把
检索截断诊断本身分类为 material。

这是通用 acquisition-completeness 缺口，不是 mall、Controller、HTTP 或 `EsProduct` 特判：已知 exact resource 的可用读取与未知外部事实
不同。用户没有明确询问检索过程、截断状态或覆盖诊断时，Agent 不能保留 stale acquisition diagnostic 来替代仍可执行的 material exact read。

## Decision and disposition

1. 若 Draft 选择 `RESOLVED_ACQUISITION` candidate，Application 必须把它配对到同一 `SOURCE_SEARCH` 的 SUPPORT，并从 trusted literal
   results 与 preissued read options 重算尚未使用的 exact `SOURCE_READ`。只要这样的读取仍可执行且当前 User Message 没有明确询问 Source
   acquisition/search diagnostic，Primary 不得 finalize；它必须选择一个 material read，或删除 stale diagnostic 并只基于已取得的 SUPPORT
   作答。
2. focused Reviewer 仅可在 exact current User Message 明确询问 Source acquisition/search 的截断、覆盖、预算、失败、结果或状态时，把
   `RESOLVED_ACQUISITION` 判为 `MATERIAL_TO_USER_REQUEST`；其他情况必须使用既有 `RESOLVED_AUDIT_ONLY` 与 global no-evidence
   reference-removal Finding。Application 在 decode 时重算这一条件，不信任 Reviewer 自报。
3. 规则复用 current sealed Search request、authority receipt、canonical resource、tool-reference policy 与 effective available operations；不
   自动读取 Source、不补造 Citation、不扩大授权、route 或预算，也不重试 Provider request。post-dispatch unknown 继续禁止重放；可信
   pre-dispatch Ark network failure 只允许 bounded delay 后创建 fresh logical request。
4. 协议族升级为 `conversational-engineering-agent@35 / prompt@35 / ENGINEERING_AGENT_PRIMARY_INPUT@34 /
   ENGINEERING_AGENT_REVIEW_INPUT@24 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@29`。Primary output `@4` 与 Review output `@9` 不变。

## Verification

定向回归以同一次 truncated Search 同时返回已读 Service 与未读 Controller 为 fixture：普通 HTTP-entry 请求若选择 resolved acquisition
Boundary 且 Controller exact read 仍可用，Primary decode 必须失败并返回 closed repair directive；显式询问 Source Search diagnostic 的
Reviewer material classification 通过，普通工程问题上的同一 classification 失败。model boundary 模块 `38/38` PASS；Agent、Tool、route、
Conversation、runtime、Browser、artifact、live harness、model-source、public authority 与 MVP gate 相邻集合 `180/180` PASS。fresh Ark
qualification 与 run-121 是下一连续验证；run-120 只证明 direct declaration 修复与 transport 正常，不取得质量或 MVP PASS。
