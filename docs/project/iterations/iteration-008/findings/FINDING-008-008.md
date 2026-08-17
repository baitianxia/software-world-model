---
id: FINDING-008-008
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai, quality, security]
depends_on: [ITER-008-SLICE-001, FINDING-008-005, FINDING-008-007, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-QUALITY-SECURITY]
code: [src/software_world_model/ai_infrastructure/direct_https.py, src/software_world_model/ai_infrastructure/volcengine_ark_chat_adapter.py, validation/structure_world_model_iteration_008/capability/cli.py]
tests: [tests/test_volcengine_ark_chat_adapter.py, tests/test_iteration_008_capability_harness.py]
iteration: ITER-008
classification: iteration-design
disposition: hold-live-qualification-until-external-tls-path-is-restored
target: ITER-008-SLICE-001
---

# FINDING-008-008：direct 与 proxy TLS 均在证书验证前被 EOF 关闭

## Observation

绑定修复后 clean candidate 的 run-002 获得新的单次 2-call Conformance 授权。实际执行在第 1 次 Provider request 返回
`PROVIDER_OUTCOME_UNKNOWN / TLS_FAILURE`，runner 随即密封 failure 与 terminal；第 2 次调用未发生。当前 `@8` 仍没有 PASS
Conformance Result，39-call Capability Gate 继续关闭。

## Evidence

- candidate commit 为 `60e1081e89705882fab17a67fc75dcb152b7994d`，tree 为
  `ef50fe224d4ca973962d2c3c2cf6368696cea37d`；preflight digest 为
  `sha256:86874caa477b5bc0edee5845db3e9ce11ea6cfbd6012527636f6b07ad23fad45`；
- exact 用户授权 ref 为
  `codex-user-message:sha256:75238553f14e011f8565e2d18b67cea51b3ade5bbdee5a7705e2b0e1056c32d7`，authorization digest 为
  `sha256:5ca3fddb0a95abf43f455042059b3cdb549e1107b38c9833b3342e38a4f672a3`；
- sealed invocation、failure、terminal document digest 分别为
  `sha256:3d40ed19e89da1b2a4dd84fc0852cf0b71d53cde5f490d1319a5d45e4bc82a6f`、
  `sha256:ea6c9b2945442e355f56a2f77706e5aa9a80d3bc453534e80848e644b4e051df`、
  `sha256:bf60992c6381b825b64cea100278ba95265ea75f77bdd77678747e9a0c5797a2`；
- failure 明确记录 `attempted_provider_request_count: 1`、一个 request body digest、`provider_outcome_reason_code: TLS_FAILURE`、
  `authorization_consumed: true` 和 `retry_permitted_with_same_authorization: false`；原始 prompt/response 与 credential 均未持久化；
- credential status 为 configured，不能据此证明 TLS root cause；Python 3.14.6 / OpenSSL 1.1.1w 的默认 CA path 为空，但 direct opener
  会加载本机存在的 `/etc/ssl/cert.pem`；
- 11 天前的 Adapter `@7` PASS 结果使用同一 Python 3.14.6、同一 endpoint、同一 direct HTTPS implementation digest 和 proxy-disabled
  network mode。当前环境存在小写 proxy variables，但 transport 按安全设计显式忽略 ambient proxy。现有证据不足以判断 CA、远端 TLS、
  直连网络策略或瞬态握手中的哪一项是根因。

随后独立授权的 credential-free TLS diagnostic run-001 绑定 freeze file
`sha256:84664c79a5eabe2c43ec98ce911ebd2f3d43b23ecf45cd6cf8ee0d8c12a6b86b`，只对 exact host/SNI 建立一次 direct
TLS handshake。Result file digest 为 `sha256:78ec3d31d4bb4c0b878c169995a62848da4d582698a31f2df6cf628b3e78df50`，terminal file
digest 为 `sha256:fc66da26262faf909b129367455eb5758b5c544e091c0ace4c9d92bcb80a43b6`。结果为 `SSLEOFError` / errno 8：

- TCP connect 已完成，TLS handshake attempt count 恰好为 1；
- `/etc/ssl/cert.pem` fallback 已加载，但没有到达 certificate verification，`verify_code` / `verify_message` 均为空；
- credential、HTTP request 和 application payload byte 均为 0；
- 当前小写 `http_proxy` / `https_proxy` 指向无凭据的 `127.0.0.1:7897`，`all_proxy` 指向同一端口的 SOCKS5；该存在性不能单独
  证明 proxy 路径可用或应被产品采用。

因此可以排除 DNS、TCP connect 和 CA certificate verification 作为这一次失败阶段，却仍不能只凭 EOF 区分远端关闭与 direct egress
路径中的中间策略。

独立授权的 proxy TLS diagnostic run-002 随后绑定 freeze file
`sha256:2cb110d71ec0d0a647440a1d90e33d779ccecf0e04a1e5b6b650028e13a54e99`。Result file digest 为
`sha256:f3ebe7a9d9b2bbf6fafa44235adeaddea136e7cdb18fb6f84b4190283f4b93d5`，terminal file digest 为
`sha256:c830cf59164a732558c2d8f9a3f40e2e8f0a3b0503c6a0dd0bcbead9b53a2ad5`。该对照也只执行一次：

- loopback proxy 可连接并接受唯一一条 `CONNECT ark.cn-beijing.volces.com:443`；
- CONNECT 完成后唯一一次 verified TLS handshake 同样以 `SSLEOFError` / errno 8 结束，仍未到达 certificate verification；
- proxy authorization、credential、Ark HTTP request 与 target application payload 均未发送；
- 授权已消费且不可重试。

这排除了“loopback proxy 不可达”以及“仅因产品 transport 忽略 ambient proxy”作为当前失败解释。direct 与 proxy tunnel 在共同的下游
TLS 阶段得到同一 EOF；现有应用代码没有可由该证据支持的修复点。

## Impact and classification

该失败阻断的是本 Iteration 的 live 资格顺序，没有证据表明 Provider Contract、Gateway Owner 或安全不变量需要改变。直接改为使用 ambient
proxy 会改变 bearer credential 的目标边界，不能作为未经设计和授权的修补；再次运行 Conformance 也只是盲目消耗 Provider 授权。因此
分类为 `iteration-design`，主处置写回当前 Slice 的 live Gate 顺序。

## Decision and disposition

run-002 Conformance、direct diagnostic 与 proxy diagnostic evidence 保持原样，三个授权都不得重用。当前 live qualification 进入
environment/external-state hold：在 exact Ark host 的 TLS 路径由网络环境或 Provider 侧恢复，并由不消费 Conformance grant 的独立证据确认
之前，不生成 run-003，不修改 Adapter，不启用 ambient proxy，不关闭证书验证，也不申请新的 Provider 调用。

恢复条件是 verified handshake 能到达证书验证并完成；仅有 proxy 变量、TCP connect、CONNECT 200 或历史 PASS 都不满足。恢复后仍须从
新的 clean exact candidate 重新生成 2-call Conformance preflight，并取得新的用户授权；不得从诊断 PASS 推导 Provider、Capability 或
Production 资格。

## Verification after disposition

- run-002 exact attempt count 为 1，第二次 Conformance call、Capability、正式 Web、hidden canary 与 Production Activation 均未执行；
- runner 在返回控制前密封 sanitized failure 和 terminal，验证了 `FINDING-008-007` 的处置；
- 本机检查没有访问 Ark，且未读取或输出 credential；
- direct diagnostic 恰好执行一次 handshake 并以 `SSLEOFError` 关闭，未发送 HTTP/application payload；
- proxy diagnostic 恰好执行一次 CONNECT 和一次 handshake；CONNECT 完成，但 TLS 同样在证书验证前以 `SSLEOFError` 关闭；
- 当前证据支持“direct 与 proxy tunnel 的共同下游 TLS 路径不可用”，不把应用代码、proxy 存在或历史 PASS 外推为已确认 root cause。
