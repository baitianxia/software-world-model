---
id: FINDING-010-199
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai, architecture, operations, quality]
depends_on: [FINDING-010-198, ITER-010-PDR-012, SYS-ADR-017]
code: [src/software_world_model/ai_infrastructure/provider_http_failure_evidence.py, src/software_world_model/ai_infrastructure/model_egress_gateway.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py, src/software_world_model/infrastructure/sqlite_model_gateway_repository.py, src/software_world_model/interface/engineering_chat_provider_runtime.py]
tests: [tests/test_model_gateway.py, tests/test_model_egress_gateway.py, tests/test_conversational_engineering_model.py, tests/test_engineering_chat_provider_runtime.py, tests/test_ark_chat_conformance.py, tests/test_deepseek_chat_conformance.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: preserve-provider-conformance-identity-with-gateway-evidence-decorator
target: SYS-ADR-017
---

# FINDING-010-199：HTTP 证据修复误触 Provider Conformance 身份，需移到不改 request path 的 Gateway 装饰层

## Observation

`FINDING-010-198` 的首版直接修改 `model_gateway.py`。`run-078-mvp-experience` 第一次用修复提交启动时，artifact loader 在 listener、Source、
credential、TLS 与 HTTP 前返回 `QUALIFICATION_INVALID`：Ark/DeepSeek Conformance manifest 都有意包含该文件的 raw digest，所以即使
Adapter、Configuration、endpoint、model、transport 与 rendering 均未变化，两份资格也被机械判 stale。

这次门禁不是 Ark 不可用、DeepSeek 不可用或 standing authority 缺失。它揭示首版修复把“新的失败证据消费/持久化责任”放进了
Provider request path 的资格 identity，违反 ADR-017 对未变化 execution-profile Provider 身份复用 current Conformance 的要求。

## Evidence and first divergence

- 首次 `run-078` launcher 在 pre-dispatch 返回 `QUALIFICATION_INVALID`，没有创建 listener 或 Provider call。
- Ark fresh Conformance 随后真实 `2/2` PASS，requested/actual identity 与既有配置一致，result 为
  `CC-ARK-CHAT-NO-TOOLS-001-ccrun_39aefe53047b4f9c9a92f88810e62997.json`、digest
  `sha256:b66bc0fda8fbb49dc4606068dc25d2d80a45c028dbf2fe21cef0accb13af00e1`。这只证明 Ark 可达和首版 bytes 可资格，不证明设计归属正确。
- 两次 DeepSeek Conformance 尝试都在受限开发命令的 DNS/TLS acquisition 前失败，credential/HTTP 为 0，不能产生新资格，也不能被描述为
  DeepSeek 服务不可用。项目约束禁止以提权命令绕过该网络边界。
- 将证据逻辑移出 conformance-bound core 后，current `model_gateway.py` raw SHA-256 恢复为
  `1045669daf49cf97ce841b432af29363c2dc9852ce4c98cc25cb34f762ed1067`；Ark/DeepSeek current implementation aggregate 又分别精确等于既有
  PASS Result 的 `sha256:6053c96dd8ab32b3582b84109cc45359f8f13cc8e282d94e418b3f461d81878f` 与
  `sha256:a680b0c8d99ce320dd9abc2096bef90d98420490e441b352e9a2994b741dbb07`。loader 的 exact digest、fixture、配置、model 与有效期检查均未放宽或绕过。
- 新 `ProviderHTTPFailureCapturingAdapter` 只把同一 immutable `ProviderRequest` 原样委托给已资格 Adapter，在 terminal
  `PROVIDER_HTTP_ERROR` 时截取安全 details；`ProviderHTTPFailureEvidenceGateway` 只在 inner Gateway 已密封 terminal Result 后绑定
  call/request/isolation、写入独立 SQLite 表并 enrich result。它不能改 request bytes、credential/TLS/HTTP、response 或 fallback verdict。
- 相邻产品组合 `162/162`、Ark/DeepSeek Conformance 本地合同与 Model Egress evidence round-trip `10/10` PASS；fresh Browser 尚未重启，
  本 Finding 不取得 route/live/MVP PASS。

## Classification and disposition

这是 `system-contract / systemic` Finding，不是为某一 Provider、HTTP status 或 sandbox 编写的资格例外。

1. Provider Conformance 继续对现有 manifest 全量 exact 校验；不得白名单 candidate digest、伪造 successor Result、忽略过期或在 loader 中
   降级。既有 Result 只有在其 Adapter/Configuration/endpoint/model/transport/rendering 和当前 manifest raw bytes 全部仍一致时才可复用。
2. 不改变 Provider request/transport 的 post-terminal 证据职责由独立 Gateway decorator 拥有：capture wrapper 原样委托 exact Adapter；
   evidence wrapper 只消费 inner Gateway Result，使用独立 append-only repository API，并在 replay/egress/Application 投影中重验。
3. 核心 Gateway 仍只持久化通用 failure code；auxiliary evidence 与 call root 通过 model-call、provider-request、isolation-receipt 和 failure code
   四重绑定。写入失败、缺失或漂移只会让 availability fail closed，不能改变已密封 call 或取得 fallback。
4. 该分层不替代真实 route 验证。修复提交后必须重新生成 exact product/turn-scope Session，并仅用固定 launcher 让 current Ark outcome、
   availability owner 与 fresh DeepSeek admission 决定是否创建 fallback attempt。
