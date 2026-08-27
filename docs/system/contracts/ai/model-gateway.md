---
id: SYS-CONTRACT-AI-MODEL-GATEWAY
kind: system-contract
status: current
authority: normative
owners: [ai]
depends_on: [SYS-ADR-015, SYS-ADR-017, SYS-CONTRACT-X-CAPABILITY-EXECUTION, SYS-QUALITY-SECURITY]
derived_from: [DD-AI-MODEL-GATEWAY, FINDING-008-024, FINDING-008-025, FINDING-008-026, FINDING-008-032, FINDING-008-036, FINDING-010-092, FINDING-010-099, FINDING-010-104, FINDING-010-105, FINDING-010-106, FINDING-010-139]
code: [src/software_world_model/ai_infrastructure/model_gateway.py, src/software_world_model/ai_infrastructure/openai_responses_adapter.py, src/software_world_model/ai_infrastructure/volcengine_ark_chat_adapter.py, src/software_world_model/ai_infrastructure/ark_chat_conformance.py, src/software_world_model/ai_infrastructure/deepseek_chat_adapter.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py, src/software_world_model/ai_infrastructure/model_egress_gateway.py, src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, src/software_world_model/ai_infrastructure/pinned_ark_https.py, src/software_world_model/ai_infrastructure/pinned_deepseek_https.py, src/software_world_model/application_services/deepseek_dispatch_admission.py, src/software_world_model/interface/engineering_chat_provider_runtime.py, src/software_world_model/interface/world_model_runtime.py, src/software_world_model/interface/world_model_runtime_assets/gateway_authorized_workload.py]
tests: [tests/test_model_gateway.py, tests/test_openai_responses_adapter.py, tests/test_volcengine_ark_chat_adapter.py, tests/test_ark_chat_conformance.py, tests/test_deepseek_chat_adapter.py, tests/test_conversational_engineering_model.py, tests/test_deepseek_dispatch_admission.py, tests/test_engineering_chat_provider_runtime.py, tests/test_model_egress_gateway.py, tests/test_pinned_ark_https.py, tests/test_pinned_deepseek_https.py, tests/test_world_model_gateway_authorization.py, tests/test_world_model_evaluation_grant.py]
---

# Model Gateway

## Purpose and scope

Model Gateway 是所有外部模型调用的唯一入口，负责精确请求身份、授权输入闭包、执行隔离、Adapter 约束和调用结果记录。它不拥有领域 Strategy、业务 Decision、来源 Tool 或知识准入。

## Public contract

调用方提供经过授权的 Capability、Strategy、精确模型资格和 Authorized Input Manifest。Gateway 只能从 Manifest 构造 Provider Request，并返回不可信的模型结果及可验证执行元数据；领域 Owner 决定结果能否封存。调用方可以先调用 non-dispatching `preflight` 只验证 Adapter、Context、隔离 capability 与可渲染 Manifest；该操作不得 prepare/persist call、解析 Secret 或 dispatch，也不构成调用授权、资格、dispatch admission 或 live receipt。

## Invariants

1. `NO_EXTERNAL_ACCESS` 必须在分派前机械保证，并由绑定 Request Digest 的 Isolation Receipt 证明；提示词禁止工具不是隔离。
2. Gateway 不执行领域 Tool。若任务需要来源调查，模型只产生 Proposal，由 Application 授权 Source Integration 执行。
3. Request model alias 与实际响应 fingerprint 分开记录；资格必须检查 actual identity。
4. 生成、语义审核和答案审核使用隔离上下文；不得依赖 Provider 会话记忆。
5. 响应、Usage、结束原因和 Provider 元数据均不可信，必须经过 closed Schema 和领域语义校验。
6. 迟到或结果未知的调用不能覆盖更新的 Attempt，也不能被写成明确 FAIL、PASS 或零 Usage。
7. 每个新的外部披露评测必须绑定当前用户授权；历史 Conformance、Capability Qualification、Product Result 或 package
   freeze 只能证明能力与实现身份，不能授权新问题。trusted launcher 从 exact evaluation grant 派生当前 session receipt；
   active Gateway entrypoint 必须在读取 credential 或进入已资格 baseline 前验证 grant digest、disclosure digest、用户、授权时间、
   authorization ref、payload boundary 与 `Production Activation=NOT_EXECUTED`。历史 permission 字段只能标为 baseline-only。
8. 有界可变调用协议必须同时冻结最小/最大调用数、合法角色序列和 terminal 条件。每个实际调用拥有唯一 Authorized Input
   Manifest、workload/role/step identity、model call ID、receipt 和 transport audit；不能用一个 Plan receipt 代表多个调查回合。
   supervisor 只能按已资格且版本化的 connection policy 提供有界 exact connected descriptor set；Gateway 不能自行创建、交换或
   跨题/跨 session 使用连接。默认的独立连接 policy 仍是一请求一 descriptor。显式取得资格的 persistent verified TLS policy 可以在
   **同一授权 Gateway run** 内为多个 stateless HTTP request 复用已验证 TLS session，但不能合并 Manifest、model call、request ID、
   body/result digest 或 transport audit。该 policy 只允许在读取 credential、构造 Authorization 或发送 HTTP bytes 前，顺序消费下一
   descriptor 进行有界 credential-free TLS acquisition；任一 request 的 bytes 可能已经发送后，连接失败必须立即记为
   `OUTCOME_UNKNOWN`，不得重发该 request。persistent policy 还必须版本化并冻结每条 verified TLS session 的最大 HTTP dispatch
   数，不能把长运行的全部可用性依赖于一条连接无限存活；达到上限后的轮换必须发生在下一次 credential resolution 和 HTTP byte
   之前。当前 DeepSeek `PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@2` 每条 session 最多 20 次 dispatch，最多 3 次 acquisition；
   session audit 必须证明 `dispatches <= successful_sessions * 20`。Answer terminal 后未消费 descriptor 必须关闭并记录
   `UNUSED_CLOSED`；审计分别满足
   `provisioned = TLS attempts + unused_closed`、实际 Provider call 落在调用区间和 `request_retry_count=0`。少于最小、超过最大、缺
   receipt、计数未知或未取得资格的连接复用均失败关闭。
9. 若 Capability 使用 Application-owned constrained transition，Gateway 输入必须同时绑定完整版本化 operation universe 与当前 sealed
   state 的非空受限子集。子集只能由 Application 从冻结 evidence ledger、前序 Result 和预算派生，并按 contract canonical order
   表达；Gateway 拒绝 universe 外 operation、空子集、乱序/重复项或调用方自行扩张。模型 response 中越出子集的 operation 仍作为
   untrusted raw output 记录，但不能由 Gateway 或 Adapter 获得查询/FINISH 权力。
10. 多 Provider 路由按 ADR-017 在 Session 开始前冻结有序 route、每条 route 的 current Adapter Conformance、同一活动
    Strategy/Configuration Capability Qualification、exact endpoint、secret reference、独立 disclosure scope、预算和 transport。当前
    `ENGINEERING_QA` 顺序为 `VOLCENGINE_ARK → DEEPSEEK`。用户的一次提交只创建一个 logical interaction unit；Engineering
    Conversation 中该单位是一个密封 Turn，兼容单轮协议中是 logical question。每个 Provider 使用不同 attempt
    identity、Manifest、grant、Ledger/Package/Answer/Review 和 transport audit。只有 Ark attempt 已密封 terminal、没有 authorized answer，
    且可信分类为 provider unavailable/HTTP error/outcome unknown/output invalid 或 model Review rejected 时，才能透明启动最多一次
    DeepSeek attempt。Application/Source/Security failure 不允许 fallback。DeepSeek 必须从 immutable original interaction input、Chat 时
    exact relevant Application-sealed Conversation Context，以及同一 exact Cognition Context 重跑完整链，不得读取 Ark 中间态；迟到 Ark
    response 必须 quarantine 且永不覆盖。每个 Provider 内 request retry 为 0，用户无需重提问题或新建
    Session。Ark outcome unknown 后的 fallback 必须记录潜在重复计费风险。
11. 一个 prompt program 可以为不同 Capability 定义不同 semantic authority，但每次调用只能在 Manifest 构造前按 sealed
    execution stage 确定性选择唯一 entry。Manifest 必须记录版本化 selection transformation，prompt program digest 必须绑定全部
    stage-entry-content，Gateway 必须校验 stage、transformation 与所选 content digest；仅在完整 monolithic prompt 中声明其他 section
    “inactive”不构成隔离。Adapter 只能在此选择之后执行 Provider-specific schema rendering，不能重新引入其他 Capability 指令。
12. Gateway `preflight` 与 `invoke` 必须复用同一套 Adapter/Context/Manifest 验证；`preflight` 成功不能跳过 `invoke` 时的 current
    authorization、资格或 identity 重验，也不能预留或消费 model call ID。调用方若使用 one-use disclosure authorization，必须在实际
    `invoke` 边界按自身 policy 消费，并对 pre-dispatch rejection、fresh dispatch 与 repository replay 分别保留真实计数。
13. Provider transport 在 HTTP bytes 前已知不可用时，只能由 transport owner 产生 typed `ProviderUnavailable`，Gateway 密封为
    `PROVIDER_UNAVAILABLE` failed call；这与 HTTP bytes 已可能发送后的 `ProviderOutcomeUnknown` 不同。只有前者可证明 transport HTTP count
    为 0，后者必须保留潜在副作用/重复成本。普通 Domain/Gateway error 不得按字符串相似性取得 unavailable 分类或 fallback 权力。
14. Route 声明 dispatch schedule policy 时，每个 planned external run 必须在任何对应 Provider socket/connected descriptor provisioning、
    TLS、credential resolution 或 HTTP
    前提交当前有效的 admission receipt；每个新 request 还必须重验可信时钟命中的允许窗口，或绑定该 request/run 的一次性 exact override。
    receipt 必须绑定 policy version、时区/时钟来源、run/Provider/model/product/source/session identity、calls/tokens/duration 上限、官方策略
    检查、窗口判定、授权和完整质量预算。缺失、过期、identity 漂移、窗口关闭或 override 越界都必须在外部网络前失败关闭，并证明该
    Provider 的 socket/descriptor、TLS、credential 和 HTTP dispatch 均为 0。这类拒绝是 dispatch admission failure，不得伪装为
    `ProviderUnavailable`、HTTP error 或 outcome unknown，也不得取得 retry/fallback 权力。当前 planned DeepSeek 使用
    `DEEPSEEK_DISPATCH_ADMISSION@1`；窗口结束后不得创建新 DeepSeek request。已发出的 request 继续沿既有零重试/结果未知语义密封，
    但不能由不完整 Answer/Review 获得交付权。

## Security and compatibility

Secret 只在 exact endpoint 的 TLS/SNI/certificate 已验证后、HTTP dispatch 前由 Reference 解析，不进入 Request Manifest、日志或持久正文。每个 Provider / Configuration 必须具有明确、版本化且经过 Conformance 的 Adapter compatibility；共享 Adapter 只有在分别证明 Envelope、隔离和身份语义时才可复用，不能凭“OpenAI-compatible”等名称推定兼容。Provider-specific JSON mode 若要求 Adapter 注入 closed schema，schema authority 与 Gateway 的 leading semantic authority 必须按该 Adapter 已资格的 message rendering contract 组合，不能形成未经资格的相互竞争 system turns。当前 DeepSeek contract 将两者合并为恰好一个 leading system message，保持其余消息顺序，并由 live Conformance 同时验证单一 system、任务语义和 closed schema；该结论不自动适用于 Ark 或其他 OpenAI-format Provider。Provider preference 是预授权 attempt route，不是绕过资格的探测。相同 Adapter/Configuration/endpoint/model/transport/rendering identity 且仍有效的 Conformance 必须复用；领域 Prompt、答案 Schema 或不改变该 identity 的产品变化不能要求重复 Conformance。Connection policy、最大 credential-free TLS acquisition 次数、session audit schema 和零 same-Provider request retry 都属于 Provider Configuration 与 Capability Qualification 身份；live Result 必须按 logical question 和 provider attempt 分别证明实际 TLS attempts/successes、HTTP dispatch、connection reuse、credential resolution、fallback reason、late quarantine、post-dispatch unknown 和潜在重复成本，而不只声明配置。Ark Engineering Chat policy 固定每 request 一个 verified TLS session、每 session 一个 HTTP dispatch、`Connection: close`、TLS 后逐 dispatch 解析 credential 与 retry 0；其 Conformance 必须携带通过 strict verifier 的 Session audit，不能由旧 urllib transport 或旧 sealed Result 继承。

这里的单轮 `logical question` 审计术语在 Engineering Conversation 中必须投影为密封 Turn；live Result 按 logical interaction unit（Chat
中为 Turn）和 provider attempt 分别闭合，不得把整段 Conversation 合并计为一次 live attempt。Provider 透明只描述产品语义；它不取消
每条 route 自己的 dispatch admission、资格、授权、披露和 transport 审计。

## Verification ownership

Execution Context、Manifest、Call Record、Provider DTO、重试状态和错误投影由代码与 Adapter Contract Tests 定义。Live Conformance 与具体运行身份是非规范性执行证据。当前产品已用本地确定性测试闭合 logical-Turn/provider-attempt 双层身份、预授权双 route、完整链 fallback、late-result quarantine、typed unavailable 与 Ark/DeepSeek Session audit；fresh Ark 与 DeepSeek Conformance 又已分别在 exact clean identity 上 PASS。Provider 资格不等于调度准入：当前状态是 `ARK_QUALIFIED / DEEPSEEK_QUALIFIED / DUAL_PROVIDER_QUALIFICATION_CURRENT / DEEPSEEK_SCHEDULE_GATE_LOCAL_PASS / SESSION_AUTHORITY_REQUIRED / NOT_LIVE`；`DEEPSEEK_DISPATCH_ADMISSION@1` 已在 Gateway preflight 与 invoke 前机械执行，但 current actual `@3` artifact、fresh 官方检查、允许窗口或 exact override、新 external grant 与逐 dispatch/terminal receipt 仍必须由每次 planned run 单独取得和验证。
