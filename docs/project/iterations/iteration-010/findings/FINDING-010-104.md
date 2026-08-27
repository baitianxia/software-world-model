---
id: FINDING-010-104
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai, security, application, interface, operations, quality, project]
depends_on: [FINDING-010-103, SYS-ADR-017, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-QUALITY-SECURITY, SYS-OPS-CONFIGURATION, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/volcengine_ark_chat_adapter.py, src/software_world_model/ai_infrastructure/ark_chat_conformance.py, src/software_world_model/ai_infrastructure/model_gateway.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py, src/software_world_model/interface/provider_cli.py, src/software_world_model/interface/engineering_chat_provider_runtime.py, src/software_world_model/interface/engineering_chat_session_artifact.py, src/software_world_model/interface/engineering_chat_session_runtime.py, validation/structure_world_model_iteration_003/v009/inputs.py]
tests: [tests/test_volcengine_ark_chat_adapter.py, tests/test_ark_chat_conformance.py, tests/test_agentic_capability_live_harness.py, tests/test_conversational_engineering_model.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_model_gateway.py, tests/test_iteration_003_v009.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: ark-transport-session-audit-local-candidate-fresh-conformance-required
target: SYS-CONTRACT-AI-MODEL-GATEWAY
---

# FINDING-010-104：Ark transport Session audit 与 typed unavailable fallback 形成本地候选

## Observation

`FINDING-010-103` 的 terminal receipt 只能验证 DeepSeek transport Session audit。既有 Ark urllib transport 在建立并验证 TLS 之前解析
Bearer credential，并把连接建立失败与 HTTP bytes 已发送后的断连都归为 `ProviderOutcomeUnknown`。这既不满足 secret-after-verified-TLS
边界，也无法证明 TLS/credential/HTTP/retry 的数量关系；同时，HTTP 前的已知零 dispatch 不可用会被 Model Gateway 归为普通内部失败，
因此不会触发 ADR-017 已预授权的 Ark→DeepSeek 独立 fallback attempt。

## Evidence

- Ark transport 现固定为 exact host/path 的 direct verified TLS HTTP/1.1，每个请求恰好新建一个 TLS session、每个 session 最多一个 HTTP
  dispatch、显式 `Connection: close`、request retry 0。peer certificate 验证并记录 digest 后才解析 credential；TLS 前失败时 credential
  与 HTTP count 都保持 0，HTTP dispatch 开始后的网络失败才是 outcome unknown。响应 body 仍受 16 MiB closed limit 约束。
- 新 `SWM-VOLCENGINE-ARK-TRANSPORT-SESSION-AUDIT@1` 分列 TLS attempt/success/pre-dispatch failure、certificate digest、credential
  resolution/success、HTTP dispatch、connection reuse、post-dispatch unknown 与 retry。`RecordingChatCompletionsTransport` 只委托经过 strict
  verifier 的 audit；Engineering Chat terminal receipt 现在对 Ark 和 DeepSeek 两条 route 都要求有效 transport audit。
- Model Gateway 新增 owner-typed `ProviderUnavailable`：它只表示 Provider transport 在 HTTP 前已知不可用。Gateway 将其密封为
  `PROVIDER_UNAVAILABLE` failed call；Engineering Agent model boundary 再将该 exact Gateway result 映射为
  `EngineeringAgentModelFailureKind.PROVIDER_UNAVAILABLE`，从而允许既有 router 创建最多一个隔离 DeepSeek fallback。普通 Gateway、
  qualification、Application 或 Source failure 仍不能借字符串伪装为 Provider unavailable。
- Ark configuration fingerprint/public status 现绑定 connection policy、每 request TLS 上限、每 session HTTP 上限、credential resolution
  policy 与 retry false。Ark Conformance fixture 升级为 `1.7.0`、result schema 升级为 `@2`，新增 `CC-ARK-13`，并把 transport Session
  audit 纳入 execution evidence 与 PASS verifier。Conformance runner 不再在 TLS 前解析实际 secret。旧 Ark Conformance 因 fixture、
  implementation digest 与 configuration fingerprint drift 明确失效，不能追认为 current qualification。
- Ark/Agent/Gateway/artifact 最小组合实际 48/48 PASS；包含 Ark/DeepSeek Conformance、Agent、Route、Provider runtime、artifact、Browser、
  CLI 与 Gateway 的相邻聚焦组合实际 141/141 PASS。相关 `compileall`、`git diff --check` 通过。冻结 V-009 定向模块仍精确呈现既有
  3 FAIL + 1 ERROR 的 `V-009 Adapter Conformance implementation drifted` historical hold，没有被新 fixture identity 改写成另一类失败；
  current documentation check 为 504/504 PASS。
  本次没有读取 mall Source/resources、解析真实 credential、访问网络、调用 Provider/model、启动 listener/browser 或执行 Production
  Activation。
- 后继候选的离线回归诊断发现 `tests/test_agentic_capability_live_harness.py` 中旧 Echo transport 没有实现上述 mandatory Session audit，
  因而被 current Conformance 正确 fail-close；夹具补齐同一 `@1` audit 后，该离线能力流定向测试 PASS。该修复只恢复测试夹具与现行
  Ark 契约的一致性，不刷新资格、不访问网络，也不改变既有 V-009/Codex binary historical hold。

## Decision and disposition

- 本地状态增加 `ARK_TRANSPORT_SESSION_AUDIT_LOCAL_CANDIDATE`；artifact fixed-command terminal 已不再有
  `ARK_TRANSPORT_SESSION_AUDIT_NOT_WIRED` 缺口。该状态只证明本地实现、typed classification 和 receipt shape，不证明任何真实 TLS、
  credential、Provider response、fallback 或 Chat 质量。
- 旧 Ark Conformance qualification 必须保持 stale。下一外部步骤仍是先冻结 clean candidate，以新 identity 执行 fresh Ark
  Conformance；随后生成 current actual owner-private artifact，并另取 exact Provider/source-disclosure/browser grant 执行冻结五轮 Chat。
  在这些证据齐全前，`V-CHAT-*`、答案质量、Acceptance 与 Production Activation 全部保持 `NOT-RUN / blocking`。
