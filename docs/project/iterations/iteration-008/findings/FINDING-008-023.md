---
id: FINDING-008-023
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [architecture, ai, application, engineering, quality, security, project]
depends_on: [ITER-008-SLICE-001, FINDING-008-010, FINDING-008-022, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-QUALITY-SECURITY]
code: [src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_policy.json, src/software_world_model/ai_infrastructure/model_egress_gateway.py, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_qualification.py, src/software_world_model/ai_infrastructure/pinned_deepseek_https.py, src/software_world_model/interface/world_model_runtime.py, src/software_world_model/interface/world_model_runtime_assets/bounded_java_source_semantics_gateway_workload.py, src/software_world_model/interface/world_model_runtime_assets/provider_socket_worker.py]
tests: [tests/test_iteration_008_capability_qualification.py, tests/test_iteration_008_slice1_freeze.py, tests/test_iteration_008_slice1_live_authorize.py, tests/test_iteration_008_slice1_live_evaluator.py, tests/test_model_egress_gateway.py, tests/test_pinned_deepseek_https.py, tests/test_provider_socket_worker.py, tests/test_world_model_evaluation_grant.py, tests/test_world_model_gateway_authorization.py, tests/test_world_model_live_execution.py, tests/test_world_model_product.py]
iteration: ITER-008
classification: system-contract
disposition: pre-dispatch-qualified-provider-selection-with-no-request-retry
target: SYS-CONTRACT-AI-MODEL-GATEWAY
---

# FINDING-008-023：DeepSeek 已资格化但正式 Gateway 仍把 Ark 写死为唯一 Provider

## Observation

clean candidate `a93666ce51f24149a487581a3c12283691cbd14b` 的 run-013 已取得 DeepSeek Conformance 12/12 与 Capability
40 calls / 18 Case、18/18 PASS；唯一模型 identity 为 `deepseek-v4-pro`，qualification digest 为
`sha256:61f18bd62d217ad68ac778a5aa4e8537eff180f4009067a75c8e2c011102a0c1`。但正式 bounded product egress policy、Gateway
policy class、Gateway workload、socket supervisor、runtime provider subject 和 credential handoff 仍只接受
`VOLCENGINE_ARK/openai-chat-completions-no-tools@8/glm-5-2-260617`。

因此，当前代码不能把已通过的 DeepSeek Capability Result 用于正式 Web；反过来把该 Result 填入 Ark Gateway 也会把另一个模型的
Capability 资格错配给 Ark。Ark 当前没有绑定 `1.5.2` Strategy 的 current Conformance + Capability closed Result，所以“Ark 优先”
不能被解释为忽略资格直接尝试 Ark。

## Evidence and classification

- `bounded_java_source_semantics_model_egress_policy.json` 的唯一 provider 是 Ark；
- `QualifiedJavaSourceSemanticsModelEgressGatewayPolicy` 对 bounded 与旧 fixed policy 共用 Ark exact constants，并把 actual fingerprint
  固定为 `glm-5.2`；
- bounded Gateway workload 只构造 Ark configuration、Ark Conformance loader、Ark Adapter 和 pinned Ark transport；
- `world_model_runtime.py`、`provider_socket_worker.py` 和 role environment 只识别 Ark host、port 与 `ARK_API_KEY`；
- run-013 closed Result 的 definition/model 与所有 attempt identity 均为 `deepseek-v4-pro`。

这是 formal Model Gateway Provider binding 与安全 Owner 的 system-contract 缺口，不是 Prompt、模型输出或网络重试问题。

## Decision and required disposition

用户要求的“Ark 优先，Ark 不可用则 DeepSeek”按安全边界解释为 **dispatch 前的 exact qualification route selection**：

1. Provider route 必须分别拥有 current Adapter Conformance、同 Strategy/模型/configuration 的 Capability Qualification、exact endpoint、
   secret reference 与隔离 transport；不得跨 Provider 借用 Result；
2. 选择器按 `VOLCENGINE_ARK → DEEPSEEK` 排序，只从当前完整资格 route 中选择；本轮 Ark 不合格而 DeepSeek 合格，因此正式
   ITER-008 candidate 选择 DeepSeek；
3. 选择结果在 product freeze/grant 前密封为一个 exact Provider subject，Gateway 仍只获得单一 host/model/credential route；
4. 一旦任何 Provider request 已分派或 outcome unknown，不得向第二 Provider 重试。同授权、同问题的 request-level fallback 会违反
   no-retry、调用预算和未知结果语义；
5. Ark 将来只有取得同一活动 Contract 的全新 Conformance + Capability 后，才能在新的 product freeze 中恢复优先级。

活动 bounded egress policy 必须改为本轮 exact DeepSeek route 并版本化；runtime socket supervisor 只接受内部注册的 provider enum，
不能开放任意 host；DeepSeek 必须获得与 Ark 同等级的 inherited-connected-socket、TLS hostname/certificate、exact path、credential-late
resolution、six-descriptor 与 unused-close 审计。System Model Gateway、security/runtime flow、开发设计、代码和测试在同一变更闭合。

## Verification and disposition

活动 bounded policy 已版本化为 `@1.3.0`，只允许资格选择器按偏好顺序在 dispatch 前选出一个完整、current 的 exact route；本轮
DeepSeek route 绑定 `deepseek-chat-completions-no-tools@2`、`deepseek-v4-pro`、exact configuration/endpoint/credential reference 与
独立 pinned transport。选择结果贯穿 policy、grant、Gateway package、socket/TLS 与 audit，未选择 Provider 不取得 socket、credential
或 diagnostic probe；任何 request dispatch 或 outcome unknown 后均禁止跨 Provider retry。Ark fixed/accepted Profile 的历史行为保持不变。

资格 loader 还必须绑定当前静态 qualification resource policy：
`ITER-008-BOUNDED-JAVA-SOURCE-SEMANTICS-QUALIFICATION-RESOURCE-POLICY@1:sha256:e4e4952158a1b317856e801b556ac5f1a457be5764a13aaa84639064ccaa057b`。
因此 run-013 被确定性拒绝为
`QUALIFICATION_INVALID: bounded source-semantics Result does not bind the exact contract`；它只保留为能力发现证据，不得授权新 route。

实现验证取得：资格/冻结定向 25/25、DeepSeek Adapter/Conformance/diagnostic 20/20、Gateway/runtime/product/Slice 92/92、AF_UNIX
handoff 13/13、文档 327/327 PASS。完整 suite 为 1001/1006；唯一五项仍是 `FINDING-008-020` 已隔离的 ITER-003 historical Codex CLI
binary drift，不得记为 full-suite PASS。

处置完成后将受影响的 capability、Gateway、runtime、HTTP/Web、evaluation、DeepSeek transport 与 Slice freeze/authorization/evaluator
测试合并重跑，取得 211/211 PASS；该聚合结果未发起 live Provider request。

该 system-contract Finding 已分别写回 Model Gateway、runtime flow、security boundary、ADR-015、开发设计、代码和测试，故状态为
`dispositioned`。这不等于 live route 已资格化：必须从新的 clean candidate 形成全新 Conformance 与 18-case / 40-call Capability
closed Result，随后才能冻结正式 product candidate。正式 Web、hidden canary、SLICE-002 与 Production Activation 继续 blocking。
