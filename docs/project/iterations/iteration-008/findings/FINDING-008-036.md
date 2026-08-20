---
id: FINDING-008-036
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai, architecture, engineering, quality, project]
depends_on: [ITER-008-SLICE-001, FINDING-008-024, FINDING-008-035, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-ARCH-FLOWS]
code: [src/software_world_model/ai_infrastructure/deepseek_chat_adapter.py, src/software_world_model/ai_infrastructure/deepseek_chat_conformance.py, src/software_world_model/ai_infrastructure/model_egress_gateway.py, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_policy.json, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_qualification.py, src/software_world_model/interface/world_model_runtime.py, src/software_world_model/interface/world_model_runtime_assets/bounded_java_source_semantics_gateway_workload.py, src/software_world_model/interface/world_model_runtime_assets/gateway_authorized_workload.py, validation/structure_world_model_iteration_008/capability/freeze.py]
tests: [tests/test_deepseek_chat_adapter.py, tests/test_deepseek_chat_conformance.py, tests/test_iteration_008_deepseek_diagnostic.py, tests/test_iteration_008_capability_harness.py, tests/test_iteration_008_capability_qualification.py, tests/test_model_egress_gateway.py, tests/test_world_model_gateway_authorization.py, tests/test_iteration_008_slice1_freeze.py]
iteration: ITER-008
classification: system-contract
disposition: bounded-persistent-deepseek-session-rotation
target: SYS-CONTRACT-AI-MODEL-GATEWAY
---

# FINDING-008-036：长资格运行不能依赖单条 TLS session 无限存活

## Observation

exact candidate `1725b44e8c92382eaa7c288919a25139934d0d80`（tree
`79a748a9a2e72215a6199899f1b12816b75ffe72`）的 run-024 Conformance preflight/authorization/result/terminal digest 为
`sha256:6760f9d51c208753f9899368b700ae05fcfccbcd6115798ce79bf1ceaee47901` /
`sha256:7dd1a2638214a79295e5454bb3c70e5774efd14d2b84451cd49678f3a2207645` /
`sha256:10dbfa34b982fb620f57c56e003354132264c29af517ff715f277215778fffe9` /
`sha256:c89fed6e60f9c9fab0fa96028a6f21f4b0e4e38eab5f191564ea6db4476c69cc`，恰好 2 calls / 12/12 PASS。

同候选 Capability freeze/authorization digest 为
`sha256:fa119ba7903863391d2c2edecaf9e897bb409a326bbbd75a5fb9238ff9a90acf` /
`sha256:490a1c6a32c64b653829ea95724ac1d0cbb42c525066513b8e5107195d0779a0`。运行完成前 39 个 response 和 17 个 Case，
第 40 次 HTTP 已 dispatch 后收到 `REMOTE_DISCONNECTED`；failure/terminal digest 为
`sha256:4f13c0e26c5a88e61155fceaeed7e49385d72f3ac5b1c6111d0292dc78ba771a` /
`sha256:3cf8ccd71555132deb15a2d527b94a9ebaaa2478ad1699ae425e468e1c7573f8`。授权已消费，结果按
`PROVIDER_OUTCOME_UNKNOWN` 失败关闭且不得用同一授权重试；hidden canary 与 Production Activation 均未执行。

## Evidence and root cause

这不是 terminal authority compiler 或模型能力失败：

1. transport 审计为 TLS attempt/success `1/1`、reuse `39`、HTTP dispatch `40`、credential resolution `40/40`、request retry `0`；
   唯一 post-dispatch unknown 是最后的 `REMOTE_DISCONNECTED`；
2. `DRAFT-017` 已完成并 PASS。raw output 以 `stop`、104 output tokens 返回，`step_result_ids` 与 `support_digests` 均为空；
   output digest 为 `sha256:c2ce22d515acfa0c7b15fd4600196193a8ae1f0d95e49c0c8517a9536cb70ddd`。这直接证明
   `FINDING-008-035` 的 raw-empty / normalized-exact Owner 调整跨过了旧 1000-token 截断点；
3. run-023 曾在约 80 秒内以同一 session 完成 40 calls；run-024 invocation 与 terminal 文件时间相隔约 120 秒，最后的 Review
   从未形成 completed model output。证据不能区分 EOF 来自 DeepSeek edge、TUN 节点还是其间链路，但可以排除“第 40 个 response
   已完成后本地 evaluator 拒绝”的解释；
4. `FINDING-008-024` 已允许一次授权运行最多 3 次 credential-free TLS acquisition，却没有给每条成功 session 设置 HTTP dispatch
   上限。40-call 资格运行因而不必要地把全程可用性押在一条连接的存活期上。该无界复用是 transport policy 缺口，不应要求模型、
   Prompt 或 evaluator 适配网络中间层。

## Decision and disposition

1. DeepSeek Adapter 升级为 `deepseek-chat-completions-no-tools@7`；connection policy 升级为
   `PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@2`，session audit 升级为 `SWM-DEEPSEEK-TRANSPORT-SESSION-AUDIT@2`。
2. 每条 verified TLS session 最多承载 20 次 HTTP dispatch。第 21 次 logical request 在 credential resolution、Authorization 构造和
   HTTP byte 之前主动关闭旧 session，再消费下一次 credential-free TLS acquisition。40-call qualification 正常使用 2 条 session，
   保留第 3 次 attempt 作为 pre-dispatch acquisition 失败余量。
3. request-level 语义不变：每次调用仍有独立 manifest/request ID/receipt；任何 HTTP byte 可能发出后的失败继续
   `OUTCOME_UNKNOWN`，绝不重发该 request、绝不切换 Provider。正式产品每题 4—6 calls，仍低于单 session 20-call 上限。
4. 配置 fingerprint、Capability resource policy、freeze/authorization scope、正式 Gateway summary 与 public validator 都显式绑定
   `maximum_http_dispatches_per_tls_session=20`。审计 verifier 同时要求 `dispatches <= successful_tls_sessions * 20`，不能只声明新 policy。
5. bounded egress policy 升级为 `@1.4.9`。Capability/Strategy `1.5.8`、Prompt/Vocabulary `@17`、Investigation compiler `@7`、
   terminal compiler `@1`、suite/oracle `@1.5.8`、18 Case / 40 calls / 18/18、temperature 0、1000-token output 与 no-request-retry
   均不改变。旧 run-024 只能保留为失败证据；新 Adapter identity 必须重新执行 Conformance 和完整 Capability。

该改变细化现有 persistent verified TLS 架构，不改变 Answer/Gateway 隔离、Provider selection 或 request outcome-unknown 原则，
因此不新增 ADR；System Owner 回写到 Model Gateway Contract 与 Runtime Flows。

## Verification and closure

新增 transport 回归直接执行 21 个 logical request，证明第 21 次前轮换、TLS success `2`、HTTP `21`、reuse `19`、credential
`21/21`、retry `0`，第一条 socket 已关闭。包含 Adapter/Conformance/diagnostic/Capability/Gateway/authorization/slice freeze、
HTTP/runtime 与 docs gate 的定向执行面 151/151 PASS；current documents 340/340、`compileall`、`git diff --check` 与 task-file
credential-shaped secret scan PASS。

允许 AF_UNIX 的完整执行面共 1036 项，其中 1031 PASS；raw exit 1，唯一 4 FAIL + 1 ERROR 的 exact test identity 与 failure marker
仍全部属于 `FINDING-008-020`：三项 `test_iteration_003_v009` Conformance implementation drift FAIL、一项同源 ERROR，以及一项
prepared Codex binary digest drift FAIL。没有新增 failure/error，该事实不冒充 raw full-suite PASS。新 live Conformance/Capability
仍须等待 clean candidate；在此之前 V-002 继续 `NOT-RUN / blocking`。

当前确定性 identity 为：

- Adapter aggregate `sha256:2e5038b14bc3a861e35c3c6624b73fff0eb05c7005e2b14616b5497504117310`；
- configuration fingerprint `sha256:c3d8ee6932e8b3bb63dcdf9c8fd001ee03315a34c5fb48dbdf397082577b508b`；
- bounded policy raw digest `sha256:bd444a802b108aa875421912de6b969514c3729143b9ae79d84eb31cbed6a858`；
- qualification resource policy digest `sha256:331ddc3cd8792a6db43f729b72c847053a81bf6af5f9473f9a4a2d32b6d4e8c0`；
- packaged bounded Gateway workload raw SHA-256
  `e3de5d3ea8f7adee737964fc71e716dd93225f2847ccff1b8d646a4d315fc500`。
- System fileset digest：ITER-008
  `sha256:61ebccc713f462a3001deecd484d777b64a774fe0d22824983009ef7a91036f8`；共享文档使 ITER-007 同步重算为
  `sha256:bdbd563dca944b9899f5dacb12170005d630320e82ca2645f0d00b7a037c5e94`。

System/code/test 处置形成 clean exact candidate `34048ae770944a11aa4e01d0249b90933a30e8c7` / tree
`153c2dc625fd3e72e6b49c6d6cf94be95a3ef894`，随后完成 run-025：

- Conformance preflight/authorization/result/terminal digest 为
  `sha256:b5590984ae031142c8fa61da043a25b53defc4b8089041920b2773e4ccdd69f0` /
  `sha256:9e79ef2fafae3a22fe34e208ded9c731b4e6578a9e02166c24c3b9f12d05fc6d` /
  `sha256:476f4d871ff4e269ca8e0c90a4b84361f390a3346d32deb578a0af0697af0518` /
  `sha256:9e1151ac2dc8426d4193757ea90179311cba6be52ed637bde3c5d055aee34049`。恰好 2 requests / 12/12 PASS，
  TLS `1/1`、reuse `1`、HTTP/credential `2/2`、unknown/retry `0`，唯一 response identity 为 `deepseek-v4-pro`；
- Capability freeze/authorization digest 为
  `sha256:011544d5fc63175d9383688137c9780430f7073f91dbe8906e1e1389bd024924` /
  `sha256:7955eb9692389b4de20fa7be972a0990cc4bf94cbb32174d8abf51f3b1ce15a2`。运行完成 40 calls / 18 Case /
  18/18 PASS，input/output tokens `84,420/2,463`，failure/unknown 均为 0；
- transport 为 TLS attempt/success `2/2`、reuse `38`、HTTP/credential `40/40`、post-dispatch unknown/request retry `0`，
  `maximum_http_dispatches_per_tls_session=20`。两次 certificate digest 相同，但分别来自两条 verified session；这是真实执行证据，
  不是从配置推导；
- result/closed-document/qualification-proof/qualification-document/terminal digest 为
  `sha256:caf062a2a49fd28e6046937fd10f633c5155f9c47c60565a8d422c2a7b98cc11` /
  `sha256:53fe0e402ee737ec4200ecc408618e4b42fff42dfaf6ae3bd9b5ec358fc1570a` /
  `sha256:b407f6ad708d6a3b071325d599e9616af89cce249f7202b38e740f02eb948453` /
  `sha256:7d3b4ea2c5527f1e621e5d268105626f5ccf06c00cc9e7b74ae3dcea6bea208a` /
  `sha256:b0dd529152e6c7e43b231a3d439e65de38ea95542cc173b5a25dbe124564a8d6`；
- Qualification ref 为 `capability-evaluation:evaluation_result_81d1cb091ea249e78bbdf562aabc7403`，valid until
  `2026-08-27T13:19:05.298209+00:00`。exact loader 已用该 evidence 创建六调用 `@1.4.9` Gateway policy；全部 85 份 JSON
  为 `0600`，完整 run-025 目录 credential-shaped secret scan 无命中。两份授权均已消费且不可重试；hidden canary 未披露，
  Production Activation 为 `NOT_EXECUTED`。

因此 V-002 对当前 `1.5.8/@17/@1.4.9` + Adapter/connection/audit `@7/@2/@2` exact identity PASS；下一阻断重新变为从本次
证据写回后的 clean producer 生成全新 formal product freeze，再执行公开 Web。该 PASS 不授权 canary、SLICE-002 或 Activation。
