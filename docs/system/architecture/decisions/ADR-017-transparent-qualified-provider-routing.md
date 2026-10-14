---
id: SYS-ADR-017
kind: system-decision
status: accepted
authority: normative
semantic_owner: SYS-ARCH-BASELINE
authority_scope: execution-routing-decision-rationale
owners: [architecture, ai, application, security, operations, quality]
depends_on: [SYS-ADR-008]
derived_from: [FINDING-010-092, FINDING-010-100, FINDING-010-101, FINDING-010-139, FINDING-010-140, FINDING-010-156, FINDING-010-198, FINDING-010-199, FINDING-010-236]
amended_by: [SYS-ADR-020]
code: [src/software_world_model/ai_infrastructure/model_gateway.py, src/software_world_model/ai_infrastructure/provider_http_failure_evidence.py, src/software_world_model/ai_infrastructure/model_egress_gateway.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py, src/software_world_model/ai_infrastructure/volcengine_ark_chat_adapter.py, src/software_world_model/ai_infrastructure/deepseek_chat_adapter.py, src/software_world_model/application_services/conversational_engineering_routing.py, src/software_world_model/application_services/deepseek_dispatch_admission.py, src/software_world_model/infrastructure/sqlite_model_gateway_repository.py, src/software_world_model/interface/engineering_chat_browser.py, src/software_world_model/interface/engineering_chat_provider_launcher.py, src/software_world_model/interface/engineering_chat_provider_runtime.py, src/software_world_model/interface/engineering_chat_session_artifact.py, src/software_world_model/interface/engineering_qa_live.py, src/software_world_model/interface/engineering_qa_alpha_cli.py]
tests: [tests/test_model_gateway.py, tests/test_model_egress_gateway.py, tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_routing.py, tests/test_engineering_chat_browser.py, tests/test_deepseek_dispatch_admission.py, tests/test_engineering_chat_provider_launcher.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_volcengine_ark_chat_adapter.py, tests/test_deepseek_chat_adapter.py, tests/test_engineering_qa_live.py, tests/test_engineering_qa_alpha_cli.py]
---

# ADR-017：对用户透明的合格执行配置有序路由

> 范围说明：本文定义通用 route role、attempt 隔离、受信不可用裁决、零重试、失败关闭和持续授权边界。Provider/model/endpoint、HTTP 状态、字段、transport、receipt、预算和 admission plugin 的具体规则属于 Model Gateway/Provider Routing Contract 与 Operations；它们不能成为产品分支、默认 Chat 编排或顶层架构语义。

> **ADR-020 amendment:** 本文的 route、preferred/fallback 和 attempt 术语自 ADR-020 起仅描述 Model Execution Runtime 内部策略。Application、Agent、Session、Response Control、Browser 和 UI 不再冻结、读取或投影这些术语；其唯一边界是 Provider-neutral ModelExecutionPort 的 logical request/result 与 opaque audit ref。

## Context

普通用户询问软件工程问题时不应理解、选择或重试底层模型。系统能够冻结一个 exact execution profile，并坚持同 Provider request
不重试；但既有规则把 Provider 返回的 HTTP/outcome 信号、结构化输出失败和模型审核拒绝并列为备用路线条件。这会把
“执行配置真实不可用”与“当前调用结果未通过应用合同或质量审核”混为一件事，让路由通过更换模型规避格式、答案或应用问题。
备用执行配置必须是真实可用性容错，不是输出质量逃生通道。

简单地把半途失败的请求转发给另一个 Provider 也不可接受：两个模型可能看到不同输入、共享不完整 Ledger 或产生迟到结果覆盖，破坏
证据、审核和调用审计。需要把用户的 logical interaction unit（Chat 中为 Turn）与内部 provider attempt 分成两个身份层级。

## Decision

1. Model Execution Runtime 在任何用户交互 dispatch 前，从 `SYS-ADR-019` 的有效 standing authority 或 exact human delta 冻结内部有序候选
   policy。产品、Agent、Session 和 route branch 只调用 ModelExecutionPort，不消费 route role、顺序或 availability verdict，也不得读取 Provider/model
   名称做分支、质量标准或故障分类。Runtime Authority 同时冻结每个 execution profile 各自的
   Adapter/plugin、Provider/model、Configuration、current Conformance、Strategy Capability Qualification、endpoint、credential reference、
   disclosure/redaction scope、预算、transport policy 和 dispatch admission policy。这些具体身份只能出现在执行配置、资格、
   Adapter/plugin 实现和 runtime receipt 中。未预授权、identity 漂移或未满足已声明 admission policy 的 route 不可临时加入或发起外部连接。
2. 用户只提交一次 immutable logical interaction input。对 Chat，该输入是 current Turn Request，并绑定 Application 为该 Turn 密封的
   exact relevant Conversation Context。系统先创建独立 preferred-route attempt；Provider 对用户透明，页面只需如实显示当前/最终
   attempt 状态，不要求用户选择模型、重提当前 Turn 或启动新 Session/Conversation。
3. 只有 preferred execution profile 已密封 terminal、没有 authorized answer，且该 profile 登记的受信 availability owner
   对 exact profile ref/digest、当前时间与运行边界密封 `PREFERRED_EXECUTION_PROFILE_UNAVAILABLE` verdict 时，才可自动创建最多一个
   fallback-route attempt。Gateway 必须把 Provider HTTP failure 的最小安全字段密封为绑定 model call、provider request 与 isolation
   receipt 的 digest evidence；该 evidence 只允许 status、受限 provider code/type、optional parameter-name 与 request-id，并在 repository
   replay、Model Egress 与 Application receipt 投影中重验。parameter-name 只用于 request-field 诊断且不得参与 availability/routing；不得持久化 response body、header、
   credential、Secret Reference 或任意错误正文。Raw `PROVIDER_UNAVAILABLE`、HTTP error/status 或 `PROVIDER_OUTCOME_UNKNOWN` 只是
   availability owner 可验证的输入证据；它们不得被 Gateway、Adapter、Application 或字符串映射直接转成 fallback eligibility。
   当前通用 availability owner 只接受 typed pre-HTTP unavailable，或由 Model Gateway Contract 定义、且经 dispatch/call receipt 与
   Gateway-sealed evidence 绑定的受信 transport/provider verdict。具体 HTTP status、provider code/type、字段限制及其映射由 Model Gateway
   Contract 唯一负责，本 ADR 不复制这些值；缺少完整 evidence digest、普通 owner code 或相似字符串都必须 fail closed。没有该 exact verdict
   就必须视为 `FALLBACK_NOT_ELIGIBLE`。`PROVIDER_OUTPUT_INVALID`、`MODEL_REVIEW_REJECTED`、Capability/qualification failure、Application
   orchestration failure、Source/Broker/Worker failure、authorization/dispatch-admission failure 和 Security failure 都明确不具备 fallback
   资格，不得伪装成 unavailable。
   Availability verdict 只证明 fallback route 可被考虑，不替代 fallback profile 自身的资格、披露、预算和 dispatch admission。
4. Fallback 是新的 Provider attempt，不是同一个外部 request 的 retry。它只能从 immutable original interaction input、同一 exact World Model
   Cognition Context、当前 Turn 的 exact relevant Application-sealed Conversation Context（若为 Chat）和 Session 的受信
   控制输入重新执行完整主工程 Agent 循环、Broker/Worker 受控调查、新 Ledger/Package、Answer 和 independent Review。显式
   选择历史 `ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3` 兼容策略时，才按其 Question Understanding/Investigation/Answer/Review
   链重启。preferred attempt 的部分响应、Ledger、Evidence、Package、Draft、Review、Provider 会话或模型隐藏状态
   均不得进入 fallback attempt。
5. 结构化输出无效时，Application 只能在当前 preferred execution profile 内按已资格化的通用修复协议发起格式修复；
   Reviewer 拒绝时，只能按具体 Finding 在同一 profile 内发起答案重写或新的受控补证。每次格式修复、答案重写、补证后重答和
   fresh Review 都是新的 authorized model call，必须有新 call identity、Manifest、one-use disclosure/dispatch receipt、预算消费和原始输出审计。
   它们不是对同一 Provider request 的 retry，不得重发旧 request bytes；未预留该类新调用的资格、权威或预算时，当前 interaction 失败关闭，不 fallback。
6. 每个 attempt 拥有唯一 identity、Manifest、role receipts、disclosure grants、transport/usage/cost audit 与 terminal result。公开开源
   exact revision 且 route/预算/候选运行边界未变化时，这些 exact run/Turn/call 对象由可信系统从 standing authority 自动
   派生，不是逐 attempt 的人工审批；派生对象仍是 one-use 且不得跨 Turn 或扩张 payload。每个
   Provider 内 request retry 为 0；每个 logical interaction unit 的 fallback attempt 上限为 1，Chat 中不得将整段 Conversation
   合并成一次。preferred outcome unknown 终止后仍然只有受信 availability owner 已密封 unavailable verdict 才可以 fallback，并必须
   单列潜在重复计算和计费风险。
7. 迟到的 primary response 进入隔离 quarantine，只能作为该 attempt 的审计输入；它永远不能覆盖、合并或追认 fallback attempt 或已经
   密封的 logical-interaction result。Logical result 只从一个完整、独立审核并获授权的 attempt 派生。
8. preferred 是首个 route role，但实现缺口不算 preferred unavailable。相同 exact Adapter/Configuration/endpoint/model/transport/rendering identity 且仍在
   有效期内的 Conformance 必须复用；与该 identity 无关的领域 Prompt、答案 Schema 或产品变化不触发重复 Conformance。
   不改变 Provider request/response/transport 的 post-terminal availability-evidence 处理必须位于独立 Gateway decorator：它只可把同一
   immutable request 原样委托给 exact qualified Adapter，并在 inner Gateway terminal 后写入 call/request/isolation-bound auxiliary evidence。
   decorator、repository 或 Application 失败只使 availability fail closed，不能改写 Provider call。不得因这类外围证据实现变化让未变化的
   Provider identity 资格失效，也不得以 decorator 为理由跳过既有资格记录的精确身份、配置和有效期校验。
9. 成本只在 logical interaction unit 开始前决定是否允许完整的 preferred + fallback 最坏成本，不能在 attempt 开始后删减 Evidence、Citation、
   Answer 或 Review。所有 fallback 外部执行必须遵守其 execution profile 的运行准入策略：在建立外部连接或发送 request 前密封通用
   route-admission receipt，并在每个新外部 request 前重验该策略要求的边界、资格或 exact override。
   合法 receipt 可由可信系统从 standing authority 自动派生；普通 standing Session、canary、route 或 fallback authority 不自动包含策略例外。
   计划者必须保证完整最坏质量链满足插件准入；策略条件失效后不得创建新的 fallback request，已发出的单个 request 仍按零重试和
   outcome-unknown 规则密封。无法完成独立审核时
   当前 logical interaction fail closed，不能交付删减质量的答案。

## Consequences

- 用户得到一个 logical interaction unit 的单一产品语义，Provider 切换成为内部、可审计的容错，不成为交互步骤。
- 系统必须维护 logical-interaction identity 与 provider-attempt identity 的父子关系；Chat 还要维护 Conversation/Turn 父子
  关系和相关 Context 摘要。两条完整链分别计量成本；fallback 可能增加成本，
  特别是 primary outcome unknown 时。
- 不能以 fallback 掩盖格式、审核、Capability、Application、Source 或 Security 缺陷，也不能把两个 attempt 的“最好部分”拼成答案。
- Provider 对用户和上层 Agent 语义透明，不表示 Provider 的资格、授权、披露、预算或 admission plugin 可以省略。未满足备用配置准入只阻断
  fallback 外部分派；preferred route 和本地开发继续。新的 planned fallback 外部执行仍须插件要求的 fresh 检查、策略 verdict 或 exact
  override 及逐 dispatch/terminal receipt；standing scope 内的 receipt 应从 standing authority 自动派生，不再要求逐 run 人工 grant。
  该派生链在实现与验证前仍标记为
  `STANDING_AUTHORITY_DERIVATION_REQUIRED / NOT_DISPATCHABLE`。
- 具体 Provider、模型、执行配置、资格收据和运行状态属于可替换的 Operations/Implementation 实例，不属于本 ADR 的路由语义。
  它们必须在项目实现参考和运行记录中分别说明，不能反向改变 `preferred → fallback` 的准入条件、attempt 隔离或失败关闭规则。

## Rejected alternatives

- **要求用户在失败后选择具体 fallback Provider 并重新提问。** 泄漏基础设施细节，丢失 logical interaction unit 的单一产品语义。
- **在失败点继续使用另一个 Provider。** 会混用不完整中间态和角色上下文，无法证明 Ledger/Package/Review identity。
- **同 Provider 自动重试。** 可能重复执行 outcome unknown request，违反零重试和成本真实性。
- **把结构化输出无效或 Reviewer 拒绝当作备用路线条件。** 它们是当前执行配置内的应用合同或质量处理，不能证明该 profile 不可用。
- **任何失败都 fallback。** 会掩盖 Application、Source 或 Security 根因，降低失败关闭边界。
