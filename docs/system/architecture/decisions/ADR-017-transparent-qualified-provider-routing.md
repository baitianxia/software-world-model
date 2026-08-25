---
id: SYS-ADR-017
kind: system-decision
status: accepted
authority: normative
owners: [architecture, ai, application, security, operations, quality]
depends_on: [SYS-ADR-008]
derived_from: [FINDING-010-092]
code: [src/software_world_model/ai_infrastructure/model_gateway.py, src/software_world_model/ai_infrastructure/model_egress_gateway.py, src/software_world_model/ai_infrastructure/volcengine_ark_chat_adapter.py, src/software_world_model/ai_infrastructure/deepseek_chat_adapter.py, src/software_world_model/interface/engineering_qa_live.py, src/software_world_model/interface/engineering_qa_alpha_cli.py]
tests: [tests/test_model_gateway.py, tests/test_model_egress_gateway.py, tests/test_volcengine_ark_chat_adapter.py, tests/test_deepseek_chat_adapter.py, tests/test_engineering_qa_live.py, tests/test_engineering_qa_alpha_cli.py]
---

# ADR-017：对用户透明的合格 Provider 有序路由

## Context

普通用户询问软件工程问题时不应理解、选择或重试底层模型。系统当前能够分别冻结 Ark 或 DeepSeek 的 exact route，并坚持同 Provider
request 不重试；但既有规则把一次 Session 固定为单一 Provider，任何 dispatch 后都禁止换 Provider。这会把 Provider 的可用性、结构化
输出或模型审核失败直接暴露成用户必须重提的问题，也使 Ark 优先、DeepSeek 备用无法成为产品能力。

简单地把半途失败的请求转发给另一个 Provider 也不可接受：两个模型可能看到不同输入、共享不完整 Ledger 或产生迟到结果覆盖，破坏
证据、审核和调用审计。需要把用户的 logical question 与内部 provider attempt 分成两个身份层级。

## Decision

1. `ENGINEERING_QA` Session 在任何问题 dispatch 前预授权有序 route `VOLCENGINE_ARK → DEEPSEEK`。Session Authority 同时冻结两个
   route 各自的 Adapter、model、Configuration、current Conformance、Strategy Capability Qualification、endpoint、credential reference、
   disclosure/redaction scope、预算与 transport policy。未预授权或 identity 漂移的 route 不可临时加入。
2. 用户只提交一次 immutable logical question。系统先创建独立 Ark primary attempt；Provider 对用户透明，页面只需如实显示当前/最终
   attempt 状态，不要求用户选择模型、重提问题或启动新 Session。
3. 只有 primary attempt 已密封为 terminal 且没有 authorized answer，并由可信 Application 分类为以下之一时，才可自动创建最多一个
   DeepSeek fallback attempt：`PROVIDER_UNAVAILABLE`、`PROVIDER_HTTP_ERROR`、`PROVIDER_OUTCOME_UNKNOWN`、
   `PROVIDER_OUTPUT_INVALID` 或 `MODEL_REVIEW_REJECTED`。分类和原始 provider outcome 都必须保存；Capability failure 不得伪装成
   unavailable。Application orchestration、Source/Broker/Worker、authorization 或 Security failure 不允许 fallback。
4. Fallback 是新的 Provider attempt，不是同一个外部 request 的 retry。它只能从 immutable original question、同一 exact World Model
   Cognition Context 和 Session 的受信控制输入重新执行 Question Understanding → Investigation → Broker/Worker → 新 Ledger → 新 Package →
   Answer → independent Review 完整链。Ark attempt 的部分响应、Ledger、Evidence、Package、Draft、Review、Provider 会话或模型隐藏状态
   均不得进入 DeepSeek attempt。
5. 每个 attempt 拥有唯一 identity、Manifest、role receipts、disclosure grants、transport/usage/cost audit 与 terminal result。每个
   Provider 内 request retry 为 0；每个 logical question 的 fallback attempt 上限为 1。Ark outcome unknown 终止后可以 fallback，但必须
   单列潜在重复计算和计费风险。
6. 迟到的 primary response 进入隔离 quarantine，只能作为该 attempt 的审计输入；它永远不能覆盖、合并或追认 fallback attempt 或已经
   密封的 logical-question result。Logical result 只从一个完整、独立审核并获授权的 attempt 派生。
7. Ark 是 primary，但实现缺口不算 Ark unavailable。相同 exact Adapter/Configuration/endpoint/model/transport/rendering identity 且仍在
   有效期内的 Conformance 必须复用；与该 identity 无关的领域 Prompt、答案 Schema 或产品变化不触发重复 Conformance。
8. 成本只在 logical question 开始前决定是否允许完整的 primary + fallback 最坏成本，不能在 attempt 开始后删减 Evidence、Citation、
   Answer 或 Review。DeepSeek 批量运行可按运营策略优先安排 Provider 声明的非高峰窗口，但价格状态必须在每批开始前重新核对。

## Consequences

- 用户得到一个 logical question 的单一产品语义，Provider 切换成为内部、可审计的容错，不成为交互步骤。
- 系统必须维护 logical-question identity 与 provider-attempt identity 的父子关系，并为两条完整链分别计量成本；fallback 可能增加成本，
  特别是 primary outcome unknown 时。
- 不能以 fallback 掩盖应用、Source 或安全缺陷，也不能把两个 attempt 的“最好部分”拼成答案。
- `FINDING-010-092` 记录当前实现只支持单 Provider frozen session，尚未证明本决定。ADR/Contract 是目标 System 语义；在产品代码、测试和
  live audit 闭合前，Operations 必须标记为 `NOT_IMPLEMENTED / NOT_QUALIFIED`，不得宣称透明 fallback 已可用。

## Rejected alternatives

- **要求用户在失败后选择 DeepSeek 并重新提问。** 泄漏基础设施细节，丢失 logical question 的单一产品语义。
- **在失败点继续使用另一个 Provider。** 会混用不完整中间态和角色上下文，无法证明 Ledger/Package/Review identity。
- **同 Provider 自动重试。** 可能重复执行 outcome unknown request，违反零重试和成本真实性。
- **任何失败都 fallback。** 会掩盖 Application、Source 或 Security 根因，降低失败关闭边界。
