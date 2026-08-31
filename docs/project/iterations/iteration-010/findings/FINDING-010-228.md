---
id: FINDING-010-228
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai, quality]
depends_on: [FINDING-010-227, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_tools.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: bind-each-answer-claim-to-a-minimal-exact-citation-reference-set
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-228：run-100 的 Q5 因引用一个 broad Search Observation 而把 70 个 Citation 全部投影到答案

## Observation and execution evidence

`run-100-mvp-experience` 的 Q5 在 product commit/tree
`18c2e15653fe0dc3c82b38725cbe23e51f52defd / c71bf18b2e1dbe18ce66eec5265d54d8f845ebc2` 上以 DeepSeek fallback
完成 `11` 个 dispatch，并形成 `SUCCEEDED / ACCEPTED`。答案正文对 `mall-search` 的 Elasticsearch import/update/delete path 给出了有用的
分类，但 Browser 显示 70 个 Citation。

sealed Draft 的一个 Claim 同时引用了 full exact Source Read 与一个 broad `SOURCE_SEARCH` SUPPORT Observation。旧
`_draft_citations` 只知道 Claim 的 `support_observation_ids`，会把每个已引用 Observation 的全部 `citation_refs` 投影到 Turn。该 Search
Observation 保留几十个合法逐行 hit，所以其中只有少量 material refs 时，整个检索清单仍被暴露。Citation identity、exact revision 与
authority receipt 都是合法的；错误是答案投影粒度，不是 Source 搜索越权或伪造 Citation。

run-100 的 route、terminal 与 artifact hashes 由 `FINDING-010-227` 共同记录。Q5 的 70-Citation 结果使整体质量保持 FAIL，不能因正文可读或
Reviewer APPROVED 而称为 MVP。

## Exact first divergence

旧 Claim contract 只有 `statement + support_observation_ids`。Observation 是 Evidence/audit acquisition unit，不等于用户答案的最小
Citation surface；当一个合法 Observation 含多个独立 Source hit 时，Application 无法区分哪些 ref 直接支持该 Claim。把 Search 的 refs
全部投影是旧 contract 的确定性结果，Reviewer 也没有可审核的 selected-ref body。

这是通用 Claim/Citation contract 缺口，不是 `mall-search`、Elasticsearch、文件数量或某个 Provider 特例。

## Decision and disposition

1. `EngineeringAgentClaimProposal` 新增 ordered unique `support_citation_refs`。每个 Claim 选择的、含 Citation 的 SUPPORT Observation 至少
   贡献一个 exact ref；所有 selected refs 必须属于该 Claim 的 selected Observations。没有 Citation 的 World Model/other SUPPORT 仍可按
   Observation ID 支撑 Claim，不制造 ref。
2. Primary input 与 final preflight 为每个 allowed SUPPORT Observation 投影 exact Citation-ref copy domain。Prompt 要求选择直接支撑 Claim
   的最小集合，禁止因一个 Search hit material 而复制整个 Search inventory。decoder 与 Draft seal 从原 Observation 独立重算 subset 和
   per-Observation coverage。
3. successful Turn 只从 Claim selected refs 构造 Citation；material Boundary 仍按其绑定 Observation 投影。每个 selected ref 必须存在于
   authority receipt 且 identity 完全一致；同一 ref 在多个 selected Observations 中出现时必须逐 receipt 比较，identity drift 失败关闭。
4. Draft proposal、sealed Answer 与 reviewed-Draft identity 分别升级到 `ENGINEERING_AGENT_DRAFT_PROPOSAL@2 / ENGINEERING_AGENT_ANSWER@2 /
   ENGINEERING_AGENT_REVIEWED_DRAFT@2`；Primary output schema 升为 `engineering-agent-work-state-proposal@3`。route、Source retrieval、
   Citation authority、预算、retry、fallback 与 Production 边界不变。
5. regression 覆盖每个 selected citation-bearing Observation 的最小 ref、跨 Observation ref subset、review rewrite digest，以及两个 cognition
   Observation 原有 3 refs 只投影各 1 个直接 ref。当前六模块相邻定向测试为 `157/157`、路由测试 `19/19` PASS；fresh Browser
   successor 仍须执行。

这项变化写回 `SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 与 active Slice，不改变组件职责，故不需要新 ADR。run-100 保持真实
Quality FAIL；fresh run-101 必须验证 Q5 Citation surface 收敛且答案完整性不退化。
