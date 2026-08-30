---
id: FINDING-010-213
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [FINDING-010-212, ITER-010-PDR-007, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_routing.py, tests/test_conversational_engineering_tools.py, tests/test_engineering_chat_browser.py, tests/test_engineering_chat_candidate.py, tests/test_engineering_chat_alpha_cli.py, tests/test_engineering_chat_provider_launcher.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_qa_browser.py, tests/test_iteration_010_mvp_value_gate.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: allow-bounded-distinct-category-repair-and-close-audit-only-finding-binding
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-213：run-090 暴露 repair 校验层回退与 audit-only Finding binding 缺口

## Observation and execution evidence

`FINDING-010-212` candidate 已提交为 product commit/tree
`d7aad4e1300325d3e707296a58156aae39d5029a / 23866d906bcee0f8ec79a52bc42690e561a82154`。DeepSeek 官方 pricing 页面在
`2026-08-30T15:52:22.280Z` 由 in-app Browser fresh 可见检查；capture 文件 SHA-256 为
`41db8c224dce42329e47854adf877525df6df08566758cdef34b31a812db8db3`，可见文本 digest 为
`sha256:9c9dd4d22764599ade403c0ba6cd95abcb947810d5230ee95cb96a56a62d7668`，周末全天闲时规则没有变化。

唯一 validated launcher 完成 `run-090-mvp-experience` 的 4 个 Conversation、5 个冻结 Turn；terminal 状态为
`STOPPED_AFTER_DISPATCH`，receipt digest 为
`sha256:250b99d8b79c7456203c9a8f10ace676b3e49e4fd17e0b8b242e2c8f9884db8e`。Ark 创建 33 个 call：31 个完成，1 个在 HTTP dispatch 前发生
`TLS_FAILURE`，1 个在 request bytes 已发出后发生 `REMOTE_DISCONNECTED / PROVIDER_OUTCOME_UNKNOWN`；TLS attempt/success、credential、HTTP
分别为 `33/32/32/32`，retry 为 0。Ark pre-dispatch unavailable 后，DeepSeek first real preflight 在
`2026-08-30T16:09:34.677075Z` 重验同一价格证据；因 checked-at 已超过 900 秒 freshness 上限，active receipt 以
`DENIED_PRICING_CHECK` 失败关闭，故 DeepSeek dispatch/credential/TLS/HTTP 全部为 0。人工重复审批与 Production Activation 仍为 0。

turn-scope/session/pricing-capture/launch/terminal/Ark DB/DeepSeek DB 文件 SHA-256 分别为：

- `1db14a8258e90331733f6b27a773b7dfdb3b82e60f56f2fbe4a7d2d48cf9c5b4`
- `1ce86d2eb7febb8c0adee1ab2c1b2025daba5744991f37815bd55625ddca6eaf`
- `41db8c224dce42329e47854adf877525df6df08566758cdef34b31a812db8db3`
- `8d05282097611a2619061e6ae3cbc12d12d2ef4dadf969fd911cb681237c325d`
- `92d837282c91686fbe05686e06f005f7491efd47f05b2536ce423b72ea4c0267`
- `6f29d11fde9136222b961540a14d1331e12cbd84a860bc9d11ce2f72a59c921a`
- `0f539b3df4c6127e4b2a90005b287ed8e49b3701f314994f6d1ce8e79dd6672c`

逐题 dispatch 为 `11/12/1/0/9`。Q1、Q2 都以
`REVIEWER_MODEL_CALL_REJECTED / PROVIDER_OUTPUT_INVALID / STRUCTURED_OUTPUT_INVALID` 失败；Q3 在 Ark pre-dispatch TLS failure 后因 DeepSeek
freshness admission 失败而以 `AGENT_PRE_DISPATCH_REJECTED` 关闭；Q4 fresh Conversation 继续以
`APPLICATION_INPUT_CLARIFICATION`、零 dispatch 正确隔离；Q5 是合法 no-retry `REVIEWER_MODEL_OUTCOME_UNKNOWN`。整体仍为质量 FAIL，不能称 MVP。

## Exact first divergences

1. Q1 的 comprehensive Review 已通过。focused Review 初次输出把 Claim 1/2/3 的 caller-effect challenge 判为
   `CLAIM_EXCEEDS_CALLER_EVIDENCE`，但还把没有任何 challenge 的 Claim 4 判为 DEFECT；decoder 以
   `Claim assessments and Findings disagree` 正确拒绝。same-profile repair 随后已把 Claim 4 改为 SUPPORTED，并保持 Claim 1/2/3 与全部
   challenge/Finding coherent，却在 JSON 前增加分析叙述。该输出的语义 contract 已前进、envelope category 却从
   `CLOSED_OUTPUT_CONTRACT` 回退到 `NON_JSON_OBJECT_PREFIX`。旧第二次 repair 只允许 category 按固定序列单向递进，因此没有使用仍存在的第二个
   repair slot，Turn 直接失败。
2. Q2 的初次 focused Review 已把全部 caller challenge 收窄为 `WITHIN_CALLER_EVIDENCE`，但对已由 later full Source Read 闭合的 Search
   Boundary 选择 `RESOLVED_AUDIT_ONLY` 时返回 `finding_code=null / findings=[] / decision=APPROVED`。typed constructor 正确拒绝，但旧
   diagnostic “only an audit-only boundary assessment may bind a Finding code” 同时描述 missing 与 forbidden 两个相反分支；generic repair
   directive 没有明确要求保留 audit-only disposition、绑定 global no-evidence Finding 并改为 FINDINGS，下一 call 因而逐字返回同一无效 Review。
3. Q3 的 Ark TLS failure 是可信 pre-dispatch unavailable；DeepSeek 没有调用不是备用路由被禁止，而是同一 browser pricing capture 在
   first real fallback preflight 时已超过 PDR-007 的 900 秒 freshness。credential、TLS、HTTP 都未发生，符合 fail-closed contract。后续 fresh
   run 必须把官方页面检查放到 artifact/launcher 之前的最后时刻；本 Finding 不放宽 freshness，不把周末日历替代有效价格证据。
4. Q5 的 Ark `REMOTE_DISCONNECTED` 发生在 request bytes 已发送后，结果未知且不可 retry/fallback；它不是本 Finding 的代码变更目标。

## Decision and disposition

这是 `system-contract / systemic` Finding，不按 mall、问题、Provider、语言、Claim index、challenge ID、Finding code 或错误文本特判。

1. 一个 logical role step 仍最多两次 same-profile format repair。第二次只允许前一个 repair 形成 fresh
   `PROVIDER_OUTPUT_INVALID`，但 category 条件改为“与前一失败不同”，不再要求固定序列单向递进；这允许 semantic contract repair 偶发回退为
   envelope/JSON/shape failure 后使用最后一个 slot。相同 category 继续失败关闭。Application 仍不抽取后部 JSON、不静默正规化、不增加预算，且
   repair 不是 Provider retry 或 fallback eligibility。
2. audit-only relevance assessment 的 typed diagnostic 拆成两个单义分支：audit-only 缺少 Finding code，以及 non-audit-only 非法携带 Finding
   code。前者的 closed-contract directive 必须要求 Reviewer 保留 sealed allowed domain 中已选的 audit-only disposition，分配 unique code，
   添加 `claim_index=null / requires_evidence=false` 的 matching global Finding，并把 decision 改为 FINDINGS；不得通过伪改
   MATERIAL/NOT_DISCLOSED 获得 approval。final preflight 冗余投影该 directive，但不新增事实、Evidence、Review 或 Delivery authority。
3. 协议升级为 `conversational-engineering-agent@18 / conversational-engineering-agent-no-tools-prompt@18 /
   ENGINEERING_AGENT_PRIMARY_INPUT@18 / ENGINEERING_AGENT_REVIEW_INPUT@11 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@13`；output schemas 保持
   `engineering-agent-work-state-proposal@2 / engineering-agent-independent-review-proposal@6`。route、15-call Turn authority、4-Review 上限、
   Tool/Source fuse、repair 上限、retry、fallback eligibility、PDR-007 freshness、接收方和 Production 边界均不变。直接模型边界定向测试 34 项、
   相邻十二模块定向测试 148 项均 PASS、外调 0；fresh run-091 仍须执行，run-090 不追认为质量或 MVP PASS。

该变化细化既有 Application/Primary/Reviewer owner，不改变组件职责，故不需要新 ADR。本 Finding 与同步后的
`SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 是 current system write-back。
