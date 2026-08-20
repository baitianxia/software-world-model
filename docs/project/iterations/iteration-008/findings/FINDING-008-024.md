---
id: FINDING-008-024
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [architecture, ai, engineering, quality, security, project]
depends_on: [ITER-008-SLICE-001, FINDING-008-020, FINDING-008-023, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-QUALITY-SECURITY]
code: [src/software_world_model/ai_infrastructure/deepseek_chat_adapter.py, src/software_world_model/ai_infrastructure/deepseek_chat_conformance.py, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_qualification.py, src/software_world_model/ai_infrastructure/pinned_deepseek_https.py, src/software_world_model/interface/world_model_runtime.py, src/software_world_model/interface/world_model_runtime_assets/bounded_java_source_semantics_gateway_workload.py, validation/structure_world_model_iteration_008/capability/cli.py, validation/structure_world_model_iteration_008/capability/freeze.py]
tests: [tests/test_deepseek_chat_adapter.py, tests/test_deepseek_chat_conformance.py, tests/test_pinned_deepseek_https.py, tests/test_iteration_008_deepseek_diagnostic.py, tests/test_iteration_008_capability_harness.py, tests/test_iteration_008_capability_qualification.py, tests/test_model_egress_gateway.py, tests/test_world_model_gateway_authorization.py, tests/test_world_model_live_execution.py, tests/test_world_model_product.py]
iteration: ITER-008
classification: system-contract
disposition: persistent-verified-tls-session-with-bounded-credential-free-acquisition
target: SYS-CONTRACT-AI-MODEL-GATEWAY
---

# FINDING-008-024：每次请求重建 TLS 使当前 TUN 路径无法可靠完成 bounded 调用序列

## Observation

clean candidate `5ffb6ef1def72be56c3343d2fc97a4398208fd16` 的 run-014 Conformance 恰好 2 calls / 12/12 PASS；其后
Capability run-014 前 3 Case / 3 requests PASS，第 4 次请求在 TLS certificate verification 前以 `TLS_FAILURE / PROVIDER_OUTCOME_UNKNOWN`
密封关闭。网络恢复对照后形成的独立 run-015 前 5 Case / 9 requests PASS，第 10 次请求再次以同一 TLS failure 关闭。两个
single-use authorization 均已消费、均没有 retry 或 Provider 切换，不能合并为一份资格证据。

同一时段的 credential-free 对照只建立 verified TLS、不读取 credential、不发送 HTTP：第一组 5 次中 4 次 PASS、一次
`SSLEOFError`，后续带 0.5 秒间隔的 12/12 次全部 PASS；成功连接均为 TLS 1.3、同一 certificate digest 与 TUN synthetic peer
`198.18.1.8:443`。因此故障不是 DeepSeek model identity、JSON contract、temperature、thinking、Oracle 或本地 evaluator 偏差，而是
当前 TUN 数据路径对大量独立 TLS session 的间歇性 EOF。

另一个无凭据对照在一个 verified TLS connection 上向 exact `/chat/completions` 连续发送两次空的未授权 HTTP/1.1 request。两次均
得到预期 401，response 都明确 `Connection: keep-alive` 且 `will_close=false`。这证明该 endpoint 和当前路径支持在一个授权运行内复用
verified TLS session；它不构成模型调用或 Capability 证据。

## Root cause and classification

活动 direct qualification transport 与 formal pinned product transport 都为每个 Provider request 强制新建 TLS connection；product
还冻结 `Connection: close` 和六个不同 descriptor。该选择不是 DeepSeek wire contract 的必需条件，却把 4—6 次产品序列以及
40-call qualification 放大为相同数量的独立 TLS failure opportunity。run-013 曾偶然完成 42 次连接并不能否定 run-014/015 的重复
现场故障，也不能把不稳定路径写成 current qualification。

根因分类为 Gateway connection-policy 与当前 environment 的系统性交互，不是要求模型改变输出的适配问题。简单重跑资格会继续消费
授权且没有可靠性依据；在已发送 HTTP 后加入 retry 又会违反 outcome-unknown、预算与 no-request-retry 不变量。

## Decision and required disposition

将 DeepSeek connection policy 版本化为一个授权运行内的 persistent verified TLS session：

1. direct Conformance/Capability 与 pinned product transport 都先完成 exact host/SNI/certificate TLS，再解析 credential，随后使用
   HTTP/1.1 keep-alive 承载独立 stateless request；每个 HTTP request 仍有唯一 request ID、body digest、response 与调用审计；
2. 一次运行最多预备三个 exact connected descriptor。只有在 credential 尚未解析、Authorization/HTTP bytes 尚未发送时，才可消费
   下一 descriptor 重新取得 TLS；该动作是 credential-free connection acquisition，不增加 Provider request count；
3. 若一个 response 已完整返回且服务端明确关闭 connection，可为**下一**逻辑 request 使用剩余 descriptor；若任一 request 的 bytes
   可能已经发送后连接失败，则立即密封 `OUTCOME_UNKNOWN`，不得重发该 request、不得切 Provider；
4. 审计必须分列 Provider request count、TLS handshake attempts/successes、connection reuse、descriptor consumed/unused-close，并保持
   `provisioned = consumed + unused_closed`；不得把握手尝试伪报为模型调用，也不得隐藏 request retry；
5. DeepSeek Adapter、configuration fingerprint、model-egress policy、qualification resource policy、System Contract、runtime freeze 和
   evaluator 必须一同升级。旧 run-014/015 永久保留为失败证据，新的 clean candidate 必须重新取得 Conformance 与完整 Capability
   qualification。

正式 Web、hidden canary、SLICE-002 与 Production Activation 继续 blocking；历史 Ark fixed Profile 不受该 DeepSeek route 处置影响。

## Verification required before disposition

- direct transport 证明一个 TLS session 承载多次 request、credential 只在 handshake 成功后读取、最多三次 pre-HTTP handshake、HTTP
  dispatch 后任何失败均不 retry；
- pinned transport 证明 exact peer/SNI/certificate/path、三个 descriptor 的消费/关闭方程、keep-alive reuse、response cap 与
  outcome-unknown 语义；
- runtime/Gateway/grant/product freeze 和独立 evaluator 验证新的 connection audit，同时保持 4—6 Provider calls、Source-off 与
  selected DeepSeek only；
- 受影响回归、完整 suite 与 docs gate 如实记录；随后只从新的 clean candidate 创建全新 live qualification chain。

## Implementation and verification evidence

活动实现已完成上述处置，并以互相绑定的机械身份拒绝旧资格：

- DeepSeek Adapter `deepseek-chat-completions-no-tools@3`，configuration fingerprint
  `sha256:71b77c37c5549d78804c535ee6ed2640c7d9f427b8d6447e6190144283014d1b`；
- Conformance fixture `1.1.0` / Result `swm.deepseek-chat-conformance-result@2`，fixture digest
  `sha256:d1f412dbbe70b6c7e05e7c0abe1ca13069036c30241ddb5dca429ab4312fb297`；
- model-egress policy `ITER-008-BOUNDED-JAVA-SOURCE-SEMANTICS-MODEL-EGRESS-GATEWAY@1.4.0`，raw digest
  `sha256:9613fb5e02c0b0f104acd851faa4000808382a2e22e7f7ceb613d9a4b1b460c4`；qualification resource policy
  `ITER-008-BOUNDED-JAVA-SOURCE-SEMANTICS-QUALIFICATION-RESOURCE-POLICY@1:sha256:2c56c734689ec2c3566da17ce3f359e0b511ace75a3850c1f06376a51d3ff0e0`；
- product Gateway workload raw SHA-256
  `40146d71768edb5386cefbd164e3df5c32239e8ada140db4425e529ec5b6ab6d`，与 authorized wrapper 的 exact allowlist 一致；
- System Owner fileset `ITER-008-SYSTEM-CONTRACT-SET@1` digest
  `sha256:b1193e2a97f8c4c8db26dd2d3cbe98ff0b8fb7d6e8414fb15b71d1e0536b5df7`。

Direct transport 显式创建 TCP 与 verified TLS socket，不依赖 `http.client` 的隐式重连；每次 dispatch 前才读取一次 credential。Pinned
transport 接收恰好三个 inherited connected descriptor，分列 TLS handshake 与 HTTP dispatch audit，并在 credential 解析失败但尚未
发送 HTTP 时保持 Provider dispatch count 为 0。Conformance、Capability 与 model diagnostic 的 freeze scope 都机械绑定 connection
policy、最多三次 pre-dispatch handshake、late credential policy、session audit schema 与 `request_retry_allowed: false`；资格 loader、
runtime postcondition 与 product authorized wrapper 对相同计数关系失败关闭。

本地证据为：核心 transport/freeze/qualification 50/50 PASS；全部本次修改测试模块中非 AF_UNIX 部分 60/60 PASS，允许 Unix listener
的执行面 `tests.test_model_egress_gateway` 13/13 PASS；runtime、freeze、历史 Provider 与产品链扩展回归 89/89 PASS；`compileall` 与
`git diff --check` PASS。完整执行面为 1010/1015；唯一四项 failure 与一项 error 仍是 `FINDING-008-020` 已保留的 ITER-003 exact
Codex binary/runtime drift，不涉及本 Finding 的 DeepSeek、TLS、Gateway 或 runtime assertion，因此不得写成 full-suite PASS。文档
生成与门禁为 328/328 PASS。

System Contract、ADR、security boundary、runtime flow、active development design 与验证矩阵已接受该处置，Finding 状态为
`dispositioned`。这只表示 connection-policy 变更及本地验证已经闭合；新的 exact clean candidate 仍必须取得全新 2-call
Conformance 与 18-case / 40-call Capability PASS，才可解除 product Gate。正式 Web、canary、SLICE-002 与 Production Activation
继续阻断。
