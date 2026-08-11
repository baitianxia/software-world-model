---
id: FINDING-003-023
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, architecture, quality, security]
depends_on: [ITER-003-SLICE-001, ITER-003-VERIFICATION, FINDING-003-022]
code: [src/software_world_model/ai_infrastructure/pinned_ark_https.py, validation/structure_world_model_iteration_003/g3b/provider_socket_worker.py, validation/structure_world_model_iteration_003/g3b/run_g3b.py]
tests: [tests/test_pinned_ark_https.py, tests/test_iteration_003_g3b.py]
iteration: ITER-003
classification: system-contract
disposition: classify-and-seal-executor-synthetic-external-peers-with-exact-tls-provider-binding
target: SYS-QUALITY-SECURITY
---

# FINDING-003-023：executor 合成外联地址不能被误报为公网 IP

## Observation

首次 G3b credential-free Provider socket supervisor 实测在发送任何 TLS、HTTP 或模型请求前失败关闭。
固定 hostname `ark.cn-beijing.volces.com` 在当前 executor 的外联网络中解析为 `198.18.0.26`；该地址属于
RFC 2544 benchmark 网段 `198.18.0.0/15`，Python 正确地将其判定为非 global，因此原先“只接受 public
unicast”的地址分类拒绝了 executor 提供的合成外联 peer。

随后只修改地址分类并重跑相同的无 credential、无 payload supervisor smoke，成功得到
`EXECUTOR_SYNTHETIC_EXTERNAL`、credential/payload 均不可见、一次 TCP connect 与一次 descriptor handoff
的收据。该成功只证明 socket provisioning；它没有执行 TLS/HTTP、Provider 模型调用或 Production
Activation。

## Evidence

- 固定 DNS 复现结果为 `198.18.0.26`；首次 supervisor 终态为 `ValueError`、descriptor/payload 均为 0；
- 修改后 supervisor handoff schema 为 `swm.iter-003.g3b-provider-socket-handoff@1`，地址 scope 为
  `EXECUTOR_SYNTHETIC_EXTERNAL`，`credential_visible=false`、`product_request_payload_visible=false`、
  `tcp_connect_count=1`、`descriptor_transfer_count=1`；
- transport 和 runner 单元测试分别覆盖 executor synthetic 地址接受，以及 loopback/private 地址拒绝；
- 正式 G3b preflight/batch 仍须保存 DNS 地址/scope、实际 peer、TLS certificate/SNI 与 exact HTTP endpoint
  的独立证据；在这些证据完成前 V-010 保持 not-run。

## Impact and classification

问题来自 executor 网络虚拟化，不是 Ark Provider、Adapter、Model 或产品语义漂移。若继续声称该地址是公网
IP，会把没有观察到的事实写进 Result；若无条件接受全部 private/reserved 地址，又会扩大 SSRF/本机路由
边界。它改变跨运行环境的 Gateway 安全证据解释，分类为 `system-contract`。

## Decision and disposition

G3b 只接受两类由固定 Provider hostname 解析并逐次密封的外联地址：标准 `PUBLIC_UNICAST`，或当前
executor 明确使用的 RFC 2544 `198.18.0.0/15`，记为 `EXECUTOR_SYNTHETIC_EXTERNAL`。loopback、RFC1918、
link-local、unspecified、multicast 和其他 reserved 地址全部拒绝。后续 reconnect 只能使用 bootstrap
收据中的 exact canonical numeric address。

IP scope 只证明连接路由，不能证明 Provider 身份。sandboxed Gateway child 仍必须复核 inherited peer
address/443，以固定 Ark hostname 验证 TLS certificate/SNI，并强制 exact scheme、Host、port 与 path；
credential 继续只在这些检查之后由 child 解析。Result 必须如实记录 scope，不能把 executor synthetic
地址改写为 public IP，也不能因 TLS 成功而省略 supervisor/OS denial 证据。

## Verification after disposition

聚焦单元测试和正式 G3b 外部 preflight 分别验证分类函数、credential-free handoff、inherited TLS 与
Gateway 新 DNS/INET/INET6 denial。正式 Product Result 仍由 V-010/V-011 独立裁决；本 Finding 不提前
声明产品 PASS。
