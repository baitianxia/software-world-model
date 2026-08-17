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
disposition: require-bounded-tls-diagnosis-before-another-conformance-freeze
target: ITER-008-SLICE-001
---

# FINDING-008-008：run-002 在第一次 TLS 握手失败后关闭

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

## Impact and classification

该失败阻断的是本 Iteration 的 live 资格顺序，没有证据表明 Provider Contract、Gateway Owner 或安全不变量需要改变。直接改为使用 ambient
proxy 会改变 bearer credential 的目标边界，不能作为未经设计和授权的修补；再次运行 Conformance 也只是盲目消耗 Provider 授权。因此
分类为 `iteration-design`，主处置写回当前 Slice 的 live Gate 顺序。

## Decision and disposition

run-002 与其三份 evidence 保持原样，授权不得重用。不得立即生成 run-003 Conformance freeze。下一外部步骤必须先形成独立、credential-free
且有界的 TLS 诊断范围：只允许对 exact Ark host 做最多一次 TLS handshake，不发送 bearer、HTTP request body、产品题、源码、Evidence 或
hidden canary；该网络动作仍需新的明确用户授权。

只有诊断形成可复核 root cause，并完成必要的 environment/configuration 或实现处置及本地回归后，才允许基于新的 clean exact candidate
生成 Conformance preflight，再申请新的 2-call 授权。任何修复都不得静默启用 ambient proxy、关闭证书验证或复用 run-002 grant。

## Verification after disposition

- run-002 exact attempt count 为 1，第二次 Conformance call、Capability、正式 Web、hidden canary 与 Production Activation 均未执行；
- runner 在返回控制前密封 sanitized failure 和 terminal，验证了 `FINDING-008-007` 的处置；
- 本机检查没有访问 Ark，且未读取或输出 credential；
- 当前证据只支持 `TLS_FAILURE` 分类，不把代理存在、CA fallback 或历史 PASS 外推为已确认 root cause。
