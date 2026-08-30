---
id: FINDING-010-198
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai, application, operations, quality]
depends_on: [FINDING-010-187, FINDING-010-190, ITER-010-PDR-012]
code: [src/software_world_model/ai_infrastructure/model_gateway.py, src/software_world_model/ai_infrastructure/model_egress_gateway.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py, src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/application_services/conversational_engineering_routing.py, src/software_world_model/application_services/engineering_conversation.py, src/software_world_model/infrastructure/sqlite_model_gateway_repository.py, src/software_world_model/interface/engineering_chat_browser.py, src/software_world_model/interface/engineering_chat_provider_launcher.py]
tests: [tests/test_model_gateway.py, tests/test_model_egress_gateway.py, tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_routing.py, tests/test_engineering_chat_browser.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: seal-http-failure-evidence-for-trusted-availability
target: SYS-ADR-017
---

# FINDING-010-198：Provider HTTP 失败证据在 Gateway 边界丢失，使可信备用路线不可达

## Observation

`run-076-mvp-experience` 的最后 5 个 Ark call 与 `run-077-mvp-experience` 的首个 Ark call 都以
`PROVIDER_HTTP_ERROR` 结束；standing authority、preferred route dispatch 与周末 DeepSeek admission 均仍有效，但 fallback attempt 始终为
0。沿真实 Adapter → Gateway → model receipt → Turn → route availability owner 追踪后确认：Ark Adapter 已产生经过清洗的
`http_status/provider_error_code/provider_error_type/provider_request_id`，Model Gateway 却只保存通用 failure code，导致生产 availability
owner 只能看到字符串分类，不能证明 exact execution profile 的可信不可用状态。

因此停在 Ark 后不是用户授权缺失，也不是 DeepSeek 周末不可调用；最早偏差是 AI Infrastructure 在持久化边界丢失了 availability owner
所需的原始、受限 HTTP 证据。历史 call record 没有该字段，不能在事后按日志文字补判或补造 fallback。

## Evidence and first divergence

- Ark Adapter 的 `ProviderHTTPError.details` 已包含受限 status/code/type/request-id，不包含 response body、credential 或 Secret Reference。
- 修复前 Gateway 的 `DomainError(PROVIDER_HTTP_ERROR)` 分支只把 `exc.code` 写入 `ModelCallRecord.failure`；repository、Model Egress、model
  boundary receipt、Turn 与 attempt receipt 都没有 status 或其证据 digest。
- current local candidate 新增 `MODEL_PROVIDER_HTTP_FAILURE_EVIDENCE@1`：Gateway 只接受 `100..599` 的整数 status 与字符集/长度受限的可选
  code/type/request-id，绑定 model-call、provider-request 与 isolation receipt 后密封；SQLite 持久化、replay 和 Model Egress round-trip
  均重验 digest 与父 identity。
- exact status 与 evidence digest 经 model boundary receipt、Turn outcome、attempt receipt 传到 availability owner。确定性测试证明密封
  `503` 与 `402` 可形成 unavailable verdict 并启动一个独立 fallback attempt；`400/401/403/404/409/422`、缺 evidence digest 的 `503`、
  output-invalid 和 Reviewer reject 都保持 fallback 0。
- 相邻 Application/AI/Browser/launcher/runtime 组合 `162/162` PASS；新增 Model Egress serializer round-trip 与相关 routing/model 组合
  `62/62` PASS。完整 socket 型 Model Egress 测试在当前 sandbox 因 AF_UNIX bind/connect 被拒，属于环境限制，不改变非 socket 定向证据。
  尚未执行修复后的真实 Provider run，故本 Finding 不取得 live 或 MVP PASS。

## Classification and disposition

这是 `system-contract / systemic` Finding；修复不按 Ark、DeepSeek、错误正文、问题内容或历史 run 特判。

1. Provider HTTP failure 必须由 Gateway 密封最小安全证据并贯穿持久化、replay、Model Egress、model receipt、Turn 与 route attempt；原始
   response body、header、credential、Secret Reference 与任意错误字符串不得进入该证据。
2. Gateway 只保存 raw evidence，不授予 fallback。当前受信 availability owner 仅在 preferred attempt 已 terminal、没有 authorized answer、
   exact dispatch/call receipt 成立，且 Gateway-sealed status 属于 `{402,408,425,429,500,502,503,504}` 时密封
   `PREFERRED_EXECUTION_PROFILE_UNAVAILABLE`。其中 `402` 只表示当前 execution profile 的付款/资源服务能力不可用，不改判为授权例外。
3. `400/401/403/404/409/422` 代表请求、认证、权限、配置/资源身份或应用语义风险，不能以 fallback 掩盖；没有 Gateway evidence digest 的
   raw status、owner code 或相似字符串同样 fail closed。以后若要改变 status policy，必须由新的可信 owner contract 和 Finding 明确拥有。
4. availability verdict 不替代 fallback profile 自身的资格、standing authority 派生、披露、预算或 dispatch admission。Fallback 仍是 retry 0
   的全新 attempt，从 immutable Turn input、exact Conversation Context 与 exact Cognition 重启完整 Agent/Source/Answer/Review 链。
5. `run-076/077` 因缺失密封证据不能追溯重分类。唯一有效验证是以修复后的 clean product identity 创建 fresh Session，并让 launcher 对
   current Ark outcome 与 fresh DeepSeek admission 作逐 dispatch 裁决。
