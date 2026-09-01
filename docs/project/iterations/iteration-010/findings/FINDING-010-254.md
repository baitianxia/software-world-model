---
id: FINDING-010-254
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai, quality, operations]
depends_on: [FINDING-010-253, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: whole-assertion-claim-replica-and-nonassertive-body-closure
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-254：run-126 的分类正文比 mapped Claim 更宽且两个 Reviewer 均错误批准

## Observation and execution evidence

run-126 绑定 clean product commit/tree
`ee1024a227c2316d188ebcb8ecd33736a62cd019 / 4f5275bff7807e4c18edffd960599447707cefd8` 与 exact mall revision
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`。其 Ark implementation/config/model 与 clean
`6a3c04d7a1d3349005735ceb641ae62e3a127840` 的 fresh qualification
`ccrun_d706d40e67344b37bd907d6bf29d22b6` 相同；该 qualification 为 13/13 cases PASS、actual `glm-5.3`、
TLS/credential/HTTP `2/2/2`、retry/unknown 0，有效至 `2026-09-30T23:36:02.820416Z`。

冻结 Q1 最终在 Browser 显示 `SUCCEEDED / ACCEPTED`，形成 Conversation
`conversation_3e7bfecd32c2433896f389c0c2b36526`、Package
`agent_evidence_package_86101d9b197e423fbf55cbe1e5c19ac2`、Answer
`agent_answer_125a6f37cb7d4bec8321a7033c43ee8a`、Review
`agent_review_381e192fdffc46c29494e454bbd3b4dd` 与 Delivery
`engineering-agent-delivery:sha256:cf426752d49eaec9906ae448d89121f88d26cf3c8f1b103785b51793c2e64e49`。
Ark 11 个 calls 全部 completed，TLS/credential/HTTP `11/11/11`；DeepSeek dispatch、request retry、pre-dispatch failure 与
post-dispatch unknown 均为 0，Production 未执行。因此这不是 Ark 网络、fallback 或 transport 失败。

session config 初始模式为 `0600`，文件 SHA-256 为
`900f980d830c7512d71a5e99a366d9c01da9a06936d3c5e9e73db02ee9b6abda`；terminal digest/file SHA-256 分别为
`sha256:992e4f6bfb21048e0c982e005587605717fc595af118ac878a88d1a5e5916957 / 4292d9c069265b6a633d7f51487104f1c8d66e096ac300f9ad43d4ebf6c1d98e`。
Ark/DeepSeek Gateway 文件 SHA-256 分别为
`f83643194baabfbc319b688650194e7e377ff633c0127dbf3b2517ade402c188 / e951c232a7d6ed051340cc5c530fac95e52102bd12a024363fad1e8a340af239`。

## Exact first divergence

最终正文第 9 个 content unit 写道：

> **分类说明**：步骤 1–5 是对 Mapper/Service 的调用（调用方源码可见的数据库写入调用），步骤 7 是消息发送调用。

comprehensive Review 将它映射到 Claims 0/1，focused Review 将它映射到 Claim 1 和一个 Boundary，二者都 `APPROVED`。但 Claim 0 只陈述
`generateOrder` 的本地调用顺序；Claim 1 只枚举 caller-visible 调用形式，并没有断言步骤 1–5 全部属于数据库写入。唯一 Citation 是
`OmsPortalOrderServiceImpl.java`：其中步骤 5 只显示 caller expression `memberService.updateIntegration(...)`，并不能证明 callee 的数据库
实现；其实现实际位于未读取、未引用的 `UmsMemberServiceImpl.java`。正文还未把步骤 6 的购物车清理明确归入数据库或非数据库副作用。

因此最早系统偏差不是 Claim 自身的 citation selector，也不是 caller challenge；而是 `COVERED` content unit 可以把一条更宽的用户可见断言
映射给只共享若干 identifier/主题的较窄 Claim。既有 inline-code anchor gate 只保证 lexeme 出现，不保证整条 category/scope/certainty 断言进入
Claim-level assessment。自然语言 Reviewer 已被明确告知 full semantic coverage，但两个 fresh roles 仍共同漏判，证明该下界不能继续只靠模型判断。

## Decision and disposition

1. 当 `COVERED` unit 映射任何 affirmative Claim 时，Application 必须对 visible fragment 与每个 mapped Claim 做同一有限 presentation
   normalization：删除一个 leading Markdown list marker、inline-code backticks 与 paired bold markers，并折叠 whitespace。完整 normalized
   fragment 必须作为一个连续 substring 出现在至少一个 mapped Claim statement；较窄相关 Claim、跨 Claim 拼接或 identifier overlap 均不通过。
2. 该 assertion replica 只是把完整用户可见断言送进 Claim/evidence/Reviewer 闭环的保守词法下界，不证明事实正确，也不替代 semantic Review。
   pure Boundary-only coverage 仍由 exact Boundary mapping 和 fresh Reviewer 判断；mixed affirmative/boundary prose 必须拆成独立 visible units。
3. 对 `ANSWER` 与 `LIMITATION`，除 pure Markdown heading 或 standalone bold label 外，普通 body prose 不得标为 `NON_ASSERTIVE`，即使它没有
   inline-code anchor。`CLARIFICATION` 的澄清问题或指令仍可合法使用 `NON_ASSERTIVE`。
4. decode 必须在同一 bounded diagnostic 中聚合 assertion-replica、exact-anchor 与 nonassertive-body 违规；seal 与 Delivery 各自重算。
   format repair 必须一次修复所有 listed units，不能通过 narrower Claim、普通 body `NON_ASSERTIVE` 或 mixed-line Boundary 绕过。
5. 协议族升级为 `conversational-engineering-agent@39 / prompt@39 / ENGINEERING_AGENT_PRIMARY_INPUT@34 /
   ENGINEERING_AGENT_REVIEW_INPUT@28 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@33`。Primary output `@4`、Review output `@10`、sealed Review `@5`、
   route、Provider adapters、Source/Tool/dispatch budget、fallback、no-replay 与非 Production 边界不变。

## Verification

新增 domain fixture 证明 run-126-like“步骤 1–5 是数据库写入调用”不能映射到只陈述 local invocation 的较窄 Claim，并证明去除 list/backtick/
bold presentation 后完整 assertion replica 可通过。新增 decoder fixture 证明无 inline-code 的同类分类仍以
`COVERED_ASSERTION_REPLICA_ABSENT_FROM_MAPPED_CLAIM` 失败；普通 ANSWER body 误标 `NON_ASSERTIVE` 以
`NONSTRUCTURAL_NONASSERTIVE_BODY` 失败，而 heading 与 CLARIFICATION 保持合法。Agent/Model/Tool 定向集合为 90/90 PASS；包含 route、Conversation、
Browser/CLI、Artifact Session 及 Ark/DeepSeek adapter/conformance 的相邻集合为 224/224 PASS；660 份 current documents check 与 trusted-parent
plan snapshot/diff gate PASS。clean commit、fresh Ark qualification 与至少两个异质冻结题仍待完成，因此 run-126 永久保持 Quality FAIL，本 Finding
尚未取得 live PASS。
