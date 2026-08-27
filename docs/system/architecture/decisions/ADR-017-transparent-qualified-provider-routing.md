---
id: SYS-ADR-017
kind: system-decision
status: accepted
authority: normative
owners: [architecture, ai, application, security, operations, quality]
depends_on: [SYS-ADR-008]
derived_from: [FINDING-010-092, FINDING-010-100, FINDING-010-101, FINDING-010-139, FINDING-010-140]
code: [src/software_world_model/ai_infrastructure/model_gateway.py, src/software_world_model/ai_infrastructure/model_egress_gateway.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py, src/software_world_model/ai_infrastructure/volcengine_ark_chat_adapter.py, src/software_world_model/ai_infrastructure/deepseek_chat_adapter.py, src/software_world_model/application_services/conversational_engineering_routing.py, src/software_world_model/application_services/deepseek_dispatch_admission.py, src/software_world_model/interface/engineering_chat_provider_launcher.py, src/software_world_model/interface/engineering_chat_provider_runtime.py, src/software_world_model/interface/engineering_chat_session_artifact.py, src/software_world_model/interface/engineering_qa_live.py, src/software_world_model/interface/engineering_qa_alpha_cli.py]
tests: [tests/test_model_gateway.py, tests/test_model_egress_gateway.py, tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_routing.py, tests/test_deepseek_dispatch_admission.py, tests/test_engineering_chat_provider_launcher.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_volcengine_ark_chat_adapter.py, tests/test_deepseek_chat_adapter.py, tests/test_engineering_qa_live.py, tests/test_engineering_qa_alpha_cli.py]
---

# ADR-017：对用户透明的合格 Provider 有序路由

## Context

普通用户询问软件工程问题时不应理解、选择或重试底层模型。系统能够冻结一个 exact execution profile，并坚持同 Provider request
不重试；但既有规则把一次 Session 固定为单一 Provider，任何 dispatch 后都禁止换 Provider。这会把 Provider 的可用性、结构化输出或
模型审核失败直接暴露成用户必须重提的问题，也使“首选路线优先、备用路线容错”无法成为稳定产品能力。

简单地把半途失败的请求转发给另一个 Provider 也不可接受：两个模型可能看到不同输入、共享不完整 Ledger 或产生迟到结果覆盖，破坏
证据、审核和调用审计。需要把用户的 logical interaction unit（Chat 中为 Turn）与内部 provider attempt 分成两个身份层级。

## Decision

1. Engineering Session 在任何用户交互 dispatch 前，从 `SYS-ADR-019` 的有效 standing authority 或 exact human delta 冻结有序 route
   `preferred → fallback`。Session Authority 同时冻结两个
   route 各自的 Adapter、model、Configuration、current Conformance、Strategy Capability Qualification、endpoint、credential reference、
   disclosure/redaction scope、预算、transport policy，以及适用的 Provider dispatch admission policy。未预授权、identity 漂移或未满足
   已声明 admission policy 的 route 不可临时加入或发起外部连接。
2. 用户只提交一次 immutable logical interaction input。对 Chat，该输入是 current Turn Request，并绑定 Application 为该 Turn 密封的
   exact relevant Conversation Context。系统先创建独立 preferred-route attempt；Provider 对用户透明，页面只需如实显示当前/最终
   attempt 状态，不要求用户选择模型、重提当前 Turn 或启动新 Session/Conversation。
3. 只有 preferred attempt 已密封为 terminal 且没有 authorized answer，并由可信 Application 分类为以下之一时，才可自动创建最多一个
   fallback-route attempt：`PROVIDER_UNAVAILABLE`、`PROVIDER_HTTP_ERROR`、`PROVIDER_OUTCOME_UNKNOWN`、
   `PROVIDER_OUTPUT_INVALID` 或 `MODEL_REVIEW_REJECTED`。分类和原始 provider outcome 都必须保存；Capability failure 不得伪装成
   unavailable。Application orchestration、Source/Broker/Worker、authorization 或 Security failure 不允许 fallback。Fallback eligibility 只
   证明 fallback route 可以被考虑，不替代当前配置插件的 dispatch admission；插件拒绝不得再获得 retry 或另一层 fallback 权力。
4. Fallback 是新的 Provider attempt，不是同一个外部 request 的 retry。它只能从 immutable original interaction input、同一 exact World Model
   Cognition Context、当前 Turn 的 exact relevant Application-sealed Conversation Context（若为 Chat）和 Session 的受信
   控制输入重新执行完整主工程 Agent 循环、Broker/Worker 受控调查、新 Ledger/Package、Answer 和 independent Review。显式
   选择历史 `ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3` 兼容策略时，才按其 Question Understanding/Investigation/Answer/Review
   链重启。preferred attempt 的部分响应、Ledger、Evidence、Package、Draft、Review、Provider 会话或模型隐藏状态
   均不得进入 fallback attempt。
5. 每个 attempt 拥有唯一 identity、Manifest、role receipts、disclosure grants、transport/usage/cost audit 与 terminal result。公开开源
   exact revision 且 route/预算/loopback evaluation 边界未变化时，这些 exact run/Turn/call 对象由可信系统从 standing authority 自动
   派生，不是逐 attempt 的人工审批；派生对象仍是 one-use 且不得跨 Turn 或扩张 payload。每个
   Provider 内 request retry 为 0；每个 logical interaction unit 的 fallback attempt 上限为 1，Chat 中不得将整段 Conversation
   合并成一次。preferred outcome unknown 终止后可以 fallback，但必须
   单列潜在重复计算和计费风险。
6. 迟到的 primary response 进入隔离 quarantine，只能作为该 attempt 的审计输入；它永远不能覆盖、合并或追认 fallback attempt 或已经
   密封的 logical-interaction result。Logical result 只从一个完整、独立审核并获授权的 attempt 派生。
7. preferred 是首个 route role，但实现缺口不算 preferred unavailable。相同 exact Adapter/Configuration/endpoint/model/transport/rendering identity 且仍在
   有效期内的 Conformance 必须复用；与该 identity 无关的领域 Prompt、答案 Schema 或产品变化不触发重复 Conformance。
8. 成本只在 logical interaction unit 开始前决定是否允许完整的 preferred + fallback 最坏成本，不能在 attempt 开始后删减 Evidence、Citation、
   Answer 或 Review。所有 planned development/evaluation fallback 工作必须遵守其 execution profile 选择的 Operations admission plugin：在任何
   Provider socket/connected descriptor provisioning、TLS、credential resolution 或 HTTP 前密封通用 route-admission receipt，并在每个新外部 request 前重验插件要求的价格、时间、资格或 exact override。
   合法 receipt 可由可信系统从 standing authority 自动派生；普通 standing Session、canary、route 或 fallback authority 不自动包含策略例外。
   计划者必须保证完整最坏质量链满足插件准入；策略条件失效后不得创建新的 fallback request，已发出的单个 request 仍按零重试和
   outcome-unknown 规则密封。无法完成独立审核时
   当前 logical interaction fail closed，不能交付删减质量的答案。

## Consequences

- 用户得到一个 logical interaction unit 的单一产品语义，Provider 切换成为内部、可审计的容错，不成为交互步骤。
- 系统必须维护 logical-interaction identity 与 provider-attempt identity 的父子关系；Chat 还要维护 Conversation/Turn 父子
  关系和相关 Context 摘要。两条完整链分别计量成本；fallback 可能增加成本，
  特别是 primary outcome unknown 时。
- 不能以 fallback 掩盖应用、Source 或安全缺陷，也不能把两个 attempt 的“最好部分”拼成答案。
- Provider 对用户和上层 Agent 语义透明，不表示 Provider 的资格、授权、披露、预算或 admission plugin 可以省略。未满足备用配置准入只阻断
  fallback 外部分派；preferred route 和本地开发继续。新的 planned fallback 外部执行仍须插件要求的 fresh 检查、策略 verdict 或 exact
  override 及逐 dispatch/terminal receipt；standing scope 内的 receipt 应从 standing authority 自动派生，不再要求逐 run 人工 grant。
  该派生链在实现与验证前仍标记为
  `STANDING_AUTHORITY_DERIVATION_REQUIRED / NOT_DISPATCHABLE`。
- 当前 ITER-010 配置实例把 Ark 映射到 `preferred`、DeepSeek 映射到 `fallback`，并由 `V-DEEPSEEK-IDLE-001` 验证该备用配置的专属调度插件。
  这是可替换配置和历史执行证据，不是本 ADR 的动作、分支或质量语义。
- `FINDING-010-100` 已以 Application-owned typed classification、两个独立 attempt authority/runtime/receipt、committed Work State 隔离、
  logical Turn 分账、duplicate-cost risk 和 non-starting fixed Browser composition 形成确定性本地候选。该候选没有执行真实 Adapter/transport、
  credential、Provider 或 Browser；Operations 必须标记为 `LOCAL_COMPOSITION_CANDIDATE / REAL_RUNTIME_NOT_ATTESTED / NOT_QUALIFIED /
  NOT_LIVE`，不得宣称透明 fallback 已可供用户使用。
- `FINDING-010-101` 已把生产 Ark/DeepSeek Adapter、credential-lazy direct transport、Model Gateway、Session Disclosure Authorizer 和
  Conversational Agent model boundary 接入同一 non-starting composition，形成 `PROVIDER_RUNTIME_COMPOSITION_LOCAL_CANDIDATE`。该证据只用
  本地构造的 typed qualification identity，未加载 current sealed Conformance、Source/World Model Session 或执行 dispatch，故仍不得写成
  qualified/live 产品 route。

## Rejected alternatives

- **要求用户在失败后选择具体 fallback Provider 并重新提问。** 泄漏基础设施细节，丢失 logical interaction unit 的单一产品语义。
- **在失败点继续使用另一个 Provider。** 会混用不完整中间态和角色上下文，无法证明 Ledger/Package/Review identity。
- **同 Provider 自动重试。** 可能重复执行 outcome unknown request，违反零重试和成本真实性。
- **任何失败都 fallback。** 会掩盖 Application、Source 或 Security 根因，降低失败关闭边界。
