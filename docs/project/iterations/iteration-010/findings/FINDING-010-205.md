---
id: FINDING-010-205
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai-infrastructure, quality, operations]
depends_on: [FINDING-010-204, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_routing.py, tests/test_conversational_engineering_tools.py, tests/test_engineering_chat_browser.py, tests/test_engineering_chat_candidate.py, tests/test_engineering_chat_alpha_cli.py, tests/test_engineering_chat_provider_launcher.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_qa_browser.py, tests/test_iteration_010_mvp_value_gate.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: layer-output-repair-and-challenge-every-boundary-by-trusted-resource-identity
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-205：run-083 暴露分层输出修复与全 Boundary materiality challenge 缺口

## Observation and execution evidence

`FINDING-010-204` candidate 已提交为 product commit/tree
`9589694a7597b1c08b61ddc0c4e66d57baebdb3c / 78d4e1f6e69a1071873b0b7eee117fc225836220`。DeepSeek 官方 pricing 页面在
`2026-08-30T09:45:11.631Z` 由 in-app Browser 再次可见检查；capture 文件 SHA-256 为
`22b578502e4529261b0d1ba10e205771b2b1cf1cac7d296bfd4e93f8855eb5ed`，可见文本 digest 仍为
`sha256:9c9dd4d22764599ade403c0ba6cd95abcb947810d5230ee95cb96a56a62d7668`。因此 fresh
`run-083-mvp-experience` 的 DeepSeek admission 正确匹配周末全天 `ALLOWED_OFF_PEAK`。

首次 exact launcher 调用因 session config 文件 mode 为 `0644`，在 listener、Source、credential、TLS 和 Provider dispatch 前以
`CONTROL_STATE_DENIED` 拒绝；它没有产生 launch/terminal artifact 或外部 dispatch。将同一 canonical 文件收紧为 owner-private `0600` 后，使用唯一
validated launcher 成功运行五个冻结问题。该本地文件保护失败不是 Ark unavailable，也不满足 fallback 条件。

成功执行共形成 4 个 Conversation、5 个 Turn，terminal 状态为 `STOPPED_AFTER_DISPATCH`，receipt digest 为
`sha256:c9761ca9621f5b59e6ec9d4ac262459e04b417c84c08c8151d1ce6813e2807e4`。Ark
dispatch/TLS/credential/HTTP 为 `43/43/43/43`，post-dispatch unknown、retry、人工审批和 Production Activation 均为 0；DeepSeek
dispatch/TLS/credential/HTTP 为 `0/0/0/0`。preferred route 全程可信可用，所以不调用 DeepSeek 是正确行为，不是等待或权限缺口。

turn-scope/session/pricing-capture/launch/terminal/Ark DB/DeepSeek DB 文件 SHA-256 分别为：

- `33be9c2941b000829fd983e9693ee348f307d87b04fe2facd7cc61e172cb01ea`
- `d3f766a5a0926562773fec48fc04fddb0b5202e1054b573e50d13ec2a7ad953e`
- `22b578502e4529261b0d1ba10e205771b2b1cf1cac7d296bfd4e93f8855eb5ed`
- `baf38abbe8abd06d0c3a359aae29c0253123be20d690c5171f71d1df5f7d7776`
- `5e7ed47cb5d575f1c5eb9c9832edf38aaad6ea053621e462543b8394da664b7f`
- `5b050fdfd07d74ea273be8841e5231e3e5d42088493c025a435f864fc53887bf`
- `0f539b3df4c6127e4b2a90005b287ed8e49b3701f314994f6d1ce8e79dd6672c`

逐题结果仍不是质量或 MVP PASS。Q1、同 Conversation 的 Q3 和异质 Q5 为 `SUCCEEDED / ACCEPTED`；Q4 fresh Conversation 继续以
`APPLICATION_INPUT_CLARIFICATION`、Provider dispatch 0 正确隔离；Q2 为
`FAILED / AGENT_MODEL_CALL_REJECTED / PROVIDER_OUTPUT_INVALID / STRUCTURED_OUTPUT_INVALID`。Q5 已关闭 run-082 的两个目标缺陷：不再披露
filename-search diagnostic，也只把 `save/saveAll/delete*` 描述为 caller expression/local order，并明确数据库、Elasticsearch、remote
commit/refresh effect 未确认。Q1 却仍披露与当前结论无关的 World Model `559/866` 全局清单数字，并绑定一个正文未披露的 stale Search Boundary ID。

## Exact first divergences

1. Q2 第 6 个 Primary call `model_call_0aa18737a8024d19a709599db53bc8b8`（output digest
   `sha256:673260eeddc5cfaece6e714ce161b8883afcbdd12c92e578185e71f02d210a77`）在 JSON string 内产生未转义换行，首先只能得到
   `JSON_SYNTAX_ERROR`。同 profile repair call `model_call_998db682e77a4cfc91738d0f82416b18`（output digest
   `sha256:4798b5b605039c93618fa85818e6c23b1219ef5468e0951e3d2c5ab39c6c4e15`）修复语法后，仍把
   BOUNDARY Observation `agent_observation_662321aaad5c4904afafee7338fd8e62` 放入 affirmative Claim 的
   `support_observation_ids`，违反 Application 的 closed disposition domain。
2. 旧格式修复只能调用一次，而且第一次 JSON 无法解析时不能提前观察内部 closed-output-contract 缺陷；repair 又被要求保留 prior existing value。
   因此两个独立、按 validator 顺序才可观察的缺陷被错误压成一次修复义务。该失败不是 Provider retry、availability 或 fallback 问题。
3. Q1 的 Search SUPPORT 行 locator 与后续 full Source Read 指向同一 exact resource，却由不同 operation 签发不同 opaque
   `locator_reference`。旧 projector 只比较 reference ID，因而没有把该 Search diagnostic 识别为 resolved acquisition candidate；Q1/Q5 的全部
   focused Review 均得到 0 个 relevance challenge。
4. 即使修复上述 resource matching，旧 projector 仍只挑战 resolved Search diagnostic。Q1 已绑定的 World Model Boundary 同时携带 material
   state/constraint gap 和无关 global inventory metrics，却没有 deterministic review lead；focused Reviewer 因而未被要求逐 Boundary 判断完整 Draft
   materiality。Q1 最终 Review 也没有发现正文未披露但仍绑定的 stale Search Boundary reference。

## Decision and disposition

这是 `system-contract / systemic` Finding；不按 mall、问题文本、语言、数字、Source path、Provider/model 或 fixture 特判。

1. 同一 logical role step 的 structured-output repair 上限改为 2。第二次只允许前一个 repair 产生 fresh
   `PROVIDER_OUTPUT_INVALID`，且 local validator category 严格从
   `NON_JSON_OBJECT_PREFIX → JSON_SYNTAX_ERROR → CLOSED_SCHEMA_SHAPE → CLOSED_OUTPUT_CONTRACT` 的较早阶段前进到较晚阶段；相同或倒退 category
   继续在原两次 call 后失败关闭。每次 repair 都是 same execution profile 下的新 request/Manifest/one-use receipt，不是 Provider retry，不能触发
   fallback，也不能扩大事实、Tool 或 Review authority。
2. 第二次 repair 只能消耗现有 per-Turn 15 dispatch authority 的剩余 slot。若 authority 已耗尽，Authorizer 在 Provider boundary 前拒绝；不提高
   Agent step 11、Review 4、Tool action 8、Source File/Byte、Session、output token、duration、接收方或 Production 边界。
3. resolved-acquisition matching 先保留 exact opaque reference equality，再从 Application-sealed retrieval item 取得 exact canonical resource
   locator；只删除规范化的 `:Lstart[-end]` 行后缀，并要求 authorized Citation、`EXACT_STATIC_SOURCE_TEXT` 与 full Read
   `coverage_complete=true`。不同完整 path、basename 相似或模糊匹配均不能闭合。
4. focused Review 对 Package 中每个 Boundary 都形成 ordered challenge。`RESOLVED_ACQUISITION` 必须绑定 non-empty resolving SUPPORT；其他
   Boundary 使用 `BOUNDARY_MATERIALITY` 且不伪造 resolver。Reviewer 检查 complete Draft：只有每个实际披露 fragment 都 material 且 Draft 绑定该
   Boundary 时可用 `MATERIAL_TO_USER_REQUEST`；未绑定且未披露可用 `NOT_DISCLOSED_IN_DRAFT`；其余 resolved 情况用
   `RESOLVED_AUDIT_ONLY`，其余非物质 Boundary 用 `NON_MATERIAL_AUDIT_ONLY`，两者都必须绑定
   `claim_index=null / requires_evidence=false` Finding。一个 material gap 不能顺带使同 Observation 内的 global metric material。
5. 协议升级为 `conversational-engineering-agent@11 / conversational-engineering-agent-no-tools-prompt@11 /
   ENGINEERING_AGENT_PRIMARY_INPUT@11 / ENGINEERING_AGENT_REVIEW_INPUT@5 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@6 /
   engineering-agent-work-state-proposal@2 / engineering-agent-independent-review-proposal@5`。直接、相邻、路由、启动和浏览器边界共 144 项定向测试
   PASS、外调 0；仍须提交 clean candidate 并立即执行 fresh run-084 五题 Browser successor。run-083 永久保留 preferred-route positive evidence
   与质量 FAIL，不因本次本地修复追认为 MVP。

该变化只细化 Engineering Conversation 现有 Application/Reviewer owner，没有改变组件职责或架构 owner，故不需要新 ADR。本 Finding 与同步后的
`SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 是 current system write-back。
