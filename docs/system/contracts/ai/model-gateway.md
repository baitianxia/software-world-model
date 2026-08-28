---
id: SYS-CONTRACT-AI-MODEL-GATEWAY
kind: system-contract
status: current
authority: normative
owners: [ai]
depends_on: [SYS-ADR-015, SYS-ADR-017, SYS-ADR-019, SYS-CONTRACT-X-CAPABILITY-EXECUTION, SYS-QUALITY-SECURITY]
derived_from: [DD-AI-MODEL-GATEWAY, FINDING-008-024, FINDING-008-025, FINDING-008-026, FINDING-008-032, FINDING-008-036, FINDING-010-029, FINDING-010-092, FINDING-010-099, FINDING-010-104, FINDING-010-105, FINDING-010-106, FINDING-010-139, FINDING-010-140]
code: [src/software_world_model/ai_infrastructure, src/software_world_model/application_services, src/software_world_model/interface]
tests: [tests]
---

# Model Gateway

## Purpose and scope

Model Gateway 是所有外部模型调用的唯一入口，负责精确请求身份、授权输入闭包、执行隔离、Adapter 约束和调用结果记录。它不拥有领域 Strategy、业务 Decision、来源 Tool 或知识准入。

## Public contract

调用方提供经过授权的 Capability、Strategy、精确模型资格和 Authorized Input Manifest。Gateway 只能从 Manifest 构造 Provider Request，并返回不可信的模型结果及可验证执行元数据；领域 Owner 决定结果能否封存。对 `SYS-ADR-019` 覆盖的公开来源路径，可信 Application 从 standing authority 自动派生每个 exact Manifest/receipt；Gateway 验证派生链，但不要求每次人工签发。调用方可以先调用 non-dispatching `preflight` 只验证 Adapter、Context、隔离 capability 与可渲染 Manifest；该操作不得 prepare/persist call、解析 Secret 或 dispatch，也不构成调用授权、资格、dispatch admission 或 live receipt。

## Invariants

1. `NO_EXTERNAL_ACCESS` 必须在分派前机械保证，并由绑定 Request Digest 的 Isolation Receipt 证明；提示词禁止工具不是隔离。
2. Gateway 不执行领域 Tool。若任务需要来源调查，模型只产生 Proposal，由 Application 授权 Source Integration 执行。
3. Request model alias 与实际响应 fingerprint 分开记录；资格必须检查 actual identity。
4. 生成、语义审核和答案审核使用隔离上下文；不得依赖 Provider 会话记忆。
5. 响应、Usage、结束原因和 Provider 元数据均不可信，必须经过 closed Schema 和领域语义校验。
6. 迟到或结果未知的调用不能覆盖更新的 Attempt，也不能被写成明确 FAIL、PASS 或零 Usage。
7. 每个新的外部披露必须绑定可验证 authority chain。对已证明为公开开源、clean exact revision 的来源，以及未变化的既定
   Provider/model/endpoint/credential account、披露范围、预算和 loopback `EVALUATION_ONLY` Sink，trusted launcher 从一次 standing human
   authority 与 exact Turn 自动派生 current Session/Turn/run receipt；不再要求逐问题、逐角色或逐调用人工 grant。active Gateway
   entrypoint 必须在读取 credential 或进入已资格 baseline 前验证 standing/delta authority digest、派生 transformation、disclosure digest、
   authority subject/time/expiry/revocation、payload boundary 与 `Production Activation=NOT_EXECUTED`。private/unknown/dirty/local data、新
   Provider/model/endpoint/credential account、预算扩张、外部写、非 loopback 或 Production 必须绑定新的 exact human delta。历史
   Conformance、Capability Qualification、Product Result、package freeze 或 permission 字段只能证明 baseline，不能自行创建 standing
   authority 或授权新边界。
8. 有界可变调用协议必须同时冻结最小/最大调用数、合法角色序列和 terminal 条件。每个实际调用拥有唯一 Authorized Input
   Manifest、workload/role/step identity、model call ID、receipt 和 transport audit；不能用一个 Plan receipt 代表多个调查回合。
   supervisor 只能按已资格且版本化的 connection policy 提供有界 exact connected descriptor set；Gateway 不能自行创建、交换或
   跨题/跨 session 使用连接。默认的独立连接 policy 仍是一请求一 descriptor。显式取得资格的 persistent verified TLS policy 可以在
   **同一派生并授权的 Gateway run** 内为多个 stateless HTTP request 复用已验证 TLS session，但不能合并 Manifest、model call、request ID、
   body/result digest 或 transport audit。该 policy 只允许在读取 credential、构造 Authorization 或发送 HTTP bytes 前，顺序消费下一
   descriptor 进行有界 credential-free TLS acquisition；任一 request 的 bytes 可能已经发送后，连接失败必须立即记为
   `OUTCOME_UNKNOWN`，不得重发该 request。persistent policy 还必须版本化并冻结每条 verified TLS session 的最大 HTTP dispatch
   数，不能把长运行的全部可用性依赖于一条连接无限存活；达到上限后的轮换必须发生在下一次 credential resolution 和 HTTP byte
   之前。execution profile 必须冻结 exact acquisition 和 per-session dispatch 上限，session audit 必须按该 profile 的冻结数值证明
   dispatch bound。Answer terminal 后未消费 descriptor 必须关闭并记录 `UNUSED_CLOSED`；审计分别满足
   `provisioned = TLS attempts + unused_closed`、实际 Provider call 落在调用区间和 `request_retry_count=0`。少于最小、超过最大、缺
   receipt、计数未知或未取得资格的连接复用均失败关闭。
9. 若 Capability 使用 Application-owned constrained transition，Gateway 输入必须同时绑定完整版本化 operation universe 与当前 sealed
   state 的非空受限子集。子集只能由 Application 从冻结 evidence ledger、前序 Result 和预算派生，并按 contract canonical order
   表达；Gateway 拒绝 universe 外 operation、空子集、乱序/重复项或调用方自行扩张。模型 response 中越出子集的 operation 仍作为
   untrusted raw output 记录，但不能由 Gateway 或 Adapter 获得查询/FINISH 权力。
10. 多 execution-profile 路由按 ADR-017/019 在 Session 开始前从 standing authority 或 exact human delta 冻结有序
    `preferred → fallback` route，以及两个角色各自的 exact execution-profile ref/digest。产品、Agent 和 route branch 只能消费通用 route role、profile ref/digest、
    顺序与受信 availability verdict；Provider/model 具体身份只属于配置、资格、Adapter/plugin 和 receipt。每个 profile 必须绑定 current Adapter Conformance、
    同一活动 Strategy/Configuration Capability Qualification、Provider/model/endpoint、secret reference、独立 disclosure scope、预算、transport 和 admission plugin。
    用户的一次提交只创建一个 logical interaction unit；Engineering Conversation 中该单位是一个密封 Turn，兼容单轮协议中是 logical question。每个 route 使用不同
    attempt identity、Manifest、execution-profile/disclosure/dispatch-admission/transport/call/terminal receipts、Ledger/Package/Answer/Review 和 transport audit。
    只有 preferred-route attempt 已密封 terminal、没有 authorized answer，且 preferred profile 登记的受信 availability owner 密封 exact
    `PREFERRED_EXECUTION_PROFILE_UNAVAILABLE` verdict 时，才能透明启动最多一次 fallback-route attempt。Gateway 只保存 raw unavailable/HTTP/outcome 证据，不得直接授予 fallback。
    Output-invalid、Reviewer reject、Capability/qualification、Application、Source、authorization/admission 或 Security failure 均 non-eligible。Fallback attempt 必须从 immutable original
    interaction input、Chat 时 exact relevant Application-sealed Conversation Context，以及同一 exact Cognition Context 重跑完整链，不得读取 preferred attempt 中间态；
    迟到的 preferred response 必须 quarantine 且永不覆盖。同一 Provider request retry 为 0，用户无需重提问题或新建 Session。availability owner 若基于 outcome unknown
    形成 unavailable verdict，后续 fallback 必须记录潜在重复计费风险。
11. 一个 prompt program 可以为不同 Capability 定义不同 semantic authority，但每次调用只能在 Manifest 构造前按 sealed
    execution stage 确定性选择唯一 entry。Manifest 必须记录版本化 selection transformation，prompt program digest 必须绑定全部
    stage-entry-content，Gateway 必须校验 stage、transformation 与所选 content digest；仅在完整 monolithic prompt 中声明其他 section
    “inactive”不构成隔离。Adapter 只能在此选择之后执行 Provider-specific schema rendering，不能重新引入其他 Capability 指令。
12. Gateway `preflight` 与 `invoke` 必须复用同一套 Adapter/Context/Manifest 验证；`preflight` 成功不能跳过 `invoke` 时的 current
    authority chain、资格或 identity 重验，也不能预留或消费 model call ID。每个 one-use disclosure authorization 必须由可信系统从
    standing authority/exact human delta 和 current exact payload 派生，并在实际 `invoke` 边界按 policy 消费；它不是新的人工审批。系统
    必须对 pre-dispatch rejection、fresh dispatch 与 repository replay 分别保留真实计数。
13. Provider transport 在 HTTP bytes 前已知不可用时，只能由 transport owner 产生 typed `ProviderUnavailable`，Gateway 密封为
    `PROVIDER_UNAVAILABLE` failed call；这与 HTTP bytes 已可能发送后的 `ProviderOutcomeUnknown` 不同。只有前者可证明 transport HTTP count
    为 0，后者必须保留潜在副作用/重复成本。两者以及 HTTP status/error 都只是 raw execution evidence，不直接授予 fallback；只有该
    execution profile 登记的受信 availability owner 可以结合 exact profile 与当前收据密封 availability verdict。普通 Domain/Gateway error 不得按字符串相似性取得
    unavailable verdict 或 fallback 权力。
14. Route execution profile 选择 admission plugin 时，每个 planned external run 必须在任何对应 Provider socket/connected descriptor
    provisioning、TLS、credential resolution 或 HTTP 前提交当前有效的通用 dispatch-admission receipt；每个新 request 还必须重验插件要求
    的可信输入或绑定该 request/run 的一次性 exact policy override。Receipt 必须绑定 route role、execution-profile/plugin ref+digest、
    plugin version、trusted input source、run/Provider/model/product/source/session identity、calls/tokens/duration 上限、verdict、standing/delta
    authority chain 和完整质量预算。正常允许 verdict 可由可信系统自动派生；任何策略例外都必须由 profile 声明的 exact authority 提供。
    receipt 缺失、过期、identity/plugin/input 漂移、条件失效或 override 越界都必须在外部网络前失败关闭，并证明该 route 的 socket/
    descriptor、TLS、credential 和 HTTP dispatch 均为 0。这类拒绝是 dispatch admission failure，不得伪装为 `ProviderUnavailable`、HTTP
    error 或 outcome unknown，也不得取得 retry/fallback 权力。条件失效后不得创建该 route 的新 request；已发出的 request 继续沿既有
    零重试/结果未知语义密封，但不能由不完整 Answer/Review 获得交付权。
15. Provider 完成响应但 closed output 无效，或 fresh Reviewer 拒绝 Draft，都不证明 execution profile 不可用。若当前资格、权威和预算允许格式修复、
    同包重写、补证后重答或 fresh Review，每个步骤都必须在同一 exact execution profile 下创建新 model call，重新密封 call identity、Manifest、input digest、
    one-use disclosure/dispatch receipt 与 Usage；不得重发旧 request bytes，也不得改换 route role。无合法新调用时当前 interaction 失败关闭。

## Security and compatibility

Secret 只在 exact endpoint 的 TLS/SNI/certificate 已验证后、HTTP dispatch 前由 Reference 解析，不进入 Request Manifest、日志或持久正文。
每个 execution profile 中的 Provider/Configuration 必须具有明确、版本化且经过 Conformance 的 Adapter compatibility；共享 Adapter 只有在
分别证明 Envelope、隔离和身份语义时才可复用，不能凭协议兼容名称推定兼容。Provider-specific JSON mode 若要求 Adapter 注入 closed
schema，schema authority 与 Gateway 的 leading semantic authority 必须按该 Adapter 已资格的 message rendering contract 组合，不能形成
未经资格的相互竞争 system turns。Route role 是 standing authority 预授权的执行顺序，不是绕过资格的探测。相同 Adapter/Configuration/
endpoint/model/transport/rendering identity 且仍有效的 Conformance 必须复用；领域 Prompt、答案 Schema 或不改变该 identity 的产品变化
不能要求重复 Conformance。Connection policy、最大 credential-free TLS acquisition 次数、session audit schema 和零 same-request
retry 都属于 execution profile、Provider Configuration 与 Capability Qualification 身份；live Result 必须按 logical question 和 provider
attempt 分别证明实际 TLS attempts/successes、HTTP dispatch、connection reuse、credential resolution、raw outcome、availability owner/verdict、fallback reason、late quarantine、
post-dispatch unknown 和潜在重复成本，而不只声明配置。

这里的单轮 `logical question` 审计术语在 Engineering Conversation 中必须投影为密封 Turn；live Result 按 logical interaction unit（Chat
中为 Turn）和 provider attempt 分别闭合，不得把整段 Conversation 合并计为一次 live attempt。Provider 透明只描述产品语义；它不取消
每条 route 自己的 dispatch admission、资格、authority chain、披露和 transport 审计。公开来源 standing authority 只消除重复人工批准，
不消除任何逐调用机器控制。

## Verification ownership

Execution Context、Manifest、Call Record、Provider DTO、重试状态和错误投影由代码与 Adapter Contract Tests 定义。Live Conformance 与具体运行
身份是非规范性执行证据。Provider 资格不等于 route admission；每个 planned run 仍须验证 current actual artifact、execution profile、
admission plugin 的 current inputs/verdict 或 exact override，以及逐 dispatch/terminal receipt。这些 machine receipts 不等于逐 run 人工 grant。

## 当前配置实例与历史实现证据

当前 ITER-010 配置把 Ark 映射到 `preferred` execution profile，把 DeepSeek 映射到 `fallback` execution profile。当前 DeepSeek Adapter
contract 把 schema authority 与 leading semantic authority 合并为恰好一个 leading system message；当前 Ark Engineering Chat profile 固定
每 request 一个 verified TLS session、每 session 一个 HTTP dispatch、`Connection: close`、TLS 后逐 dispatch 解析 credential 与 retry 0。
这些差异由各自 Conformance 和 execution profile 拥有，不定义通用 route 分支。

当前 DeepSeek profile 使用 `PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@2`，每条 session 最多 20 次 dispatch、最多 3 次 acquisition，并
使用 `DEEPSEEK_DISPATCH_ADMISSION@1`。当前产品已用本地确定性测试闭合 logical-Turn/provider-attempt 双层身份、双 route、完整链
fallback、late-result quarantine、typed unavailable raw evidence 与 Ark/DeepSeek Session audit；fresh Ark 与 DeepSeek Conformance 又已分别在 exact
clean identity 上 PASS。当前状态是
`ARK_QUALIFIED / DEEPSEEK_QUALIFIED / DUAL_PROVIDER_QUALIFICATION_CURRENT / DEEPSEEK_SCHEDULE_GATE_LOCAL_PASS /
AVAILABILITY_OWNER_VERDICT_NOT_YET_ATTESTED / STANDING_AUTHORITY_DERIVATION_REQUIRED / NOT_LIVE`。这些名称、策略与状态是当前配置实例和历史实现证据；公开来源 standing authority 到
Session/Turn/call 的可信派生链仍须实现和验证。
