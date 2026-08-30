---
id: FINDING-010-203
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [FINDING-010-191, FINDING-010-193, FINDING-010-196, FINDING-010-202, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: require-typed-focused-review-for-resolved-acquisition-relevance-and-caller-callee-evidence-boundaries
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-203：run-080 的 fresh Review 仍放行已解决 Search 诊断和 caller→callee 效果扩张

## Observation

run-080 在 product commit/tree
`27b8dadf5369dbf958352990a263a4c4d0341cda / 585775a9e42ff8434773655132425f1277650bc1` 上完成五个冻结 Turn：四个工程答案
均形成 `SUCCEEDED / ACCEPTED`，fresh Conversation 的复数省略指代继续在本地零 dispatch Clarification。Ark 共 32 次调用，TLS handshake、
credential resolution 和 HTTP dispatch 均为 `32/32`，post-dispatch unknown、request retry、人工审批和 Production Activation 均为 0；没有
trusted unavailable verdict，因此 DeepSeek 0 次是 preferred route 持续可用时的正确结果，不是停工或 fallback 失败。

fresh Answer/Review 仍暴露两个系统性质量缺口：

1. 普通订单题已经完整读取 `OmsPortalOrderServiceImpl`，却仍把早期 filename-cohort Search 的
   `PARTIAL / SOURCE_SEARCH_FILENAME_MATCH_EARLY_STOP` 和检查文件数写入答案；该诊断已不限制用户要求的主调用链，Reviewer 仍批准。
2. 角色分配、订单和 `mall-search` 三题都把 full Source 中的 caller expression 扩张成 invoked callee 的数据库、消息或 Elasticsearch 效果。
   典型例子是只读 `EsProductServiceImpl` 后，把 `productDao.getAllEsProductList` 直接称为数据库读取、把
   `productRepository.save/saveAll/delete*` 直接称为 Elasticsearch 写入/删除；DAO/Repository implementation 未读，Reviewer 仍将全部 Claim
   判为 `SUPPORTED`。Q5 结束时 Tool action 仅用 `5/8`、Source file 仅用 `5/64`，仍有一个已签发的 `EsProductService.java` read option，
   因而这也不是预算耗尽造成的诚实收窄。

## Evidence and first divergence

- exact source revision/tree：
  `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7 / 047d79d8588b76013c260f3f1a9565707301a60a`。
- turn-scope/session/launch/terminal file SHA-256 分别为
  `663ce1bcc2342f47b7bb0661d0bff73dc9dfb17007eaab858cfed854e8a48cdb`、
  `5145f13f522118444b0a27c94518811becd83fd7cf51bcf664464b1785c003a9`、
  `74ee0197fbf03a18a89b1d3f13ca90e4b9f3128f53e14e33a88321804864eb85`、
  `4ee8311f5f8a5dfaa2e443e1dd6086fa780a98586de436d2fa030f02fa1608a8`。
- terminal receipt digest 为
  `sha256:62ca74b2a52e1ed50b1a115d1db18a94ae2af297a29585aff4ff5f8f989becfd`；public Source Session authority digest 为
  `sha256:628ba6e440a9d04ad9cf76db4c8b6c8dced5ef4ef33ae4b90a85de241e675440`。
- Q2 的 Search SUPPORT 已签发随后由 full exact Source Read 消费的 locator；同一 Search 的 Boundary 仍被 Draft 引用。不可变 Package 保留它
  是正确 audit 行为，first divergence 是现有 Primary/Reviewer policy 没有把“用户明确问该诊断”与“后续 Source 已闭合 acquisition need”做成
  exact 可重算的复核义务。
- Q1/Q2/Q5 的 cited full Java Source 直接包含 receiver call expression，但 cited Claim 没有绑定对应 callee implementation Observation。
  first divergence 是 comprehensive Reviewer 只收到自然语言规则，没有收到由 Application 从 Source/Claim 结构投影的 exact challenge set。
- run-080 的 fresh Reviewer approval 是下游漏判证据；它不能把这些答案追认为质量或 MVP PASS。

## Classification and disposition

这是 `system-contract / systemic` Finding；不按 mall、Java class、数据库、Elasticsearch、问题文本、业务词或 Provider 特判。

1. Application 对 Source Search Boundary 做只读结构投影：同一 Search 的 SUPPORT locator 被后续 current-Turn、full、exact Source Read 消费时，
   该 Boundary 成为 `resolved acquisition candidate`。candidate 仍在 audit 和合法 Draft copy domain；系统不能自动删除，因为用户可能明确询问
   Search 诊断本身。只有 Draft 实际引用 candidate 时才形成 exact relevance challenge。
2. focused Reviewer 必须把 current original User requirement、candidate Boundary scope 与 exact resolving Source Read 分开比较，并逐 challenge
   返回 `MATERIAL_TO_USER_REQUEST` 或 `RESOLVED_AUDIT_ONLY`。前者只允许用户明确要求该诊断，或它仍限制 material requested conclusion；后者
   必须绑定 `claim_index=null / requires_evidence=false` 的 Finding，使 Primary 在同包删除诊断而不新增 Tool action。
3. Application 从 cited full Java Source 与 Claim 结构投影 exact caller/callee challenge：Claim 引用该 Source 且复现其中 receiver method call 时，
   challenge 绑定 Claim、Source、call expression、declared receiver type，以及 Package/cited callee implementation Observation IDs。它只是 review
   lead，不是关键词判错器。focused Reviewer 独立决定 Claim 是否只陈述 invocation/source-visible local order；把未引用的 callee implementation、
   external write/effect、return semantics 或 consumer-visible result写入 Claim 时，必须返回
   `CLAIM_EXCEEDS_CALLER_EVIDENCE` 并绑定该 Claim Finding。
4. 每个 Draft 先取得 comprehensive Review；存在结构 challenge 时再取得 fresh focused Review。一个 Turn 的 Reviewer call 上限仍为 3，
   per-Turn disclosure/dispatch authority 仍为 15；focused Finding 的 successor Draft 可直接按其仍存在的 challenge focus 复审。Response Control
   必须重算 exact ordered challenge/assessment set，只有 caller challenge 全部 `WITHIN_CALLER_EVIDENCE`、relevance challenge 全部
   `MATERIAL_TO_USER_REQUEST` 且无 Finding 时才放行。
5. 协议升级为 `conversational-engineering-agent@9 / conversational-engineering-agent-no-tools-prompt@9 /
   ENGINEERING_AGENT_PRIMARY_INPUT@9 / ENGINEERING_AGENT_REVIEW_INPUT@3 /
   engineering-agent-independent-review-proposal@3`。没有增加 Source/Provider authority、Tool/File fuse、retry、fallback、角色、外部接收方或
   Production；没有以 failure code、题目或自然语言关键词静默改写 Provider output。

该变化只实现 Engineering Conversation owner 已允许的多个隔离 Reviewer view/challenge，没有改变组件职责或架构 Owner，故不需要新 ADR；
本 Finding 与更新后的 `SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 是唯一 current contract write-back。run-081 必须用 fresh exact
Browser Session 验证 diagnostic relevance、caller/callee scope、Reviewer Finding/rewrite 和既有 Ark→DeepSeek availability-only route。
