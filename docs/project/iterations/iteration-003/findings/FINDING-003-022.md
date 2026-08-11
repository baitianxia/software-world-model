---
id: FINDING-003-022
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, architecture, quality]
depends_on: [ITER-003-SLICE-001, ITER-003-VERIFICATION, FINDING-003-010]
code: [src/software_world_model/ai_infrastructure/pinned_ark_https.py, validation/structure_world_model_iteration_003/g3b/gateway.sb, validation/structure_world_model_iteration_003/g3b/provider_socket_worker.py, validation/structure_world_model_iteration_003/g3b/run_g3b.py]
tests: [tests/test_pinned_ark_https.py, tests/test_iteration_003_g3b.py]
iteration: ITER-003
classification: system-contract
disposition: inherit-one-peer-pinned-connected-socket-and-deny-new-gateway-socket-creation
target: SYS-QUALITY-SECURITY
---

# FINDING-003-022：macOS Seatbelt 不能把公网 TCP capability 限定到单一 remote IP

## Observation

G3b 初版 Gateway profile 尝试用 `(remote tcp "<numeric-ip>:443")` 把 child 的公网 connect
能力限定为预解析 Ark 地址。macOS 本机 profile compiler 对任意数值 remote host 失败关闭并返回
`host must be * or localhost in network address`；`remote tcp "*:443"` 可以编译，但会把 child
能力扩大为任意公网主机的 443 端口，不能证明 Manifest exact endpoint，也不能被描述成
`other_outbound=DENY`。

这不是 Ark adapter 或产品语义问题，而是当前 executor 的 OS capability filter 表达能力限制。仅在
Python 内校验 IP 不能补足受攻陷 child 的 OS 边界；直接改成 `*:443` 也违反最小能力原则。

## Impact and classification

该发现影响 Gateway 的部署安全边界、V-010 证据解释和以后复用的系统规则，分类为
`system-contract`。它不改变 V-009 已取得资格的 Provider、Adapter、Model、Prompt、schema、endpoint
或 baseline，也不授权新的 Provider、来源或 Production Activation。

## Decision and disposition

G3b 使用一个属于 Model Egress Gateway 部署边界的 supervisor/child 拆分：

1. invocation receipt 在首次 DNS/TCP 操作前密封；
2. 独立的标准库 supervisor worker 使用显式清空 `ARK_API_KEY` 的闭合环境；它不接收产品 request/response
   payload，只解析固定 hostname、连接一个带 scope 记录的 external numeric peer TCP 443、验证实际 peer，并通过
   `SCM_RIGHTS` 移交一个 descriptor；worker 不执行 TLS/HTTP；
3. 该唯一 connected descriptor 通过继承交给 distinct sandboxed Gateway child；trusted evaluator 另向
   child 继承一个已绑定、`0600` 的 exact AF_UNIX Gateway listener；
4. child 的 Seatbelt profile只允许两个继承 descriptor 的数据面 I/O，并以 `syscall-unix` 防火墙拒绝
   `SYS_socket`/`SYS_socketpair`，从而不授予任何新 DNS/INET/INET6/AF_UNIX socket 创建能力；
5. child 在解析 credential 前重新验证 inherited peer address/port 和 TLS certificate/SNI，之后继续强制
   exact scheme、Host、port、path 与 qualified Manifest；
6. supervisor connection provisioning 和 child HTTPS/model dispatch 分开计数、分开审计，Result 不声称
   Seatbelt 具备不存在的 remote-IP filter。

该 disposition 的 OS 结论严格限于“不能创建新 socket”。`remote tcp "*:443"` 会允许继承 TCP descriptor 的
数据面；Seatbelt 不能同时证明任意受攻陷 native code 无法用 `disconnectx`/`connectx` 重定向同一 descriptor。
因此本 executor 只授权 digest-sealed 的闭合 Python workload，并要求正常运行审计中 `connect`/`bind` 为零；若
威胁模型包含任意 native code execution，必须改用 VM/container/per-process network namespace 或等价的 exact
destination enforcement，不能继承本结论。

系统 Deployment、Security Boundaries、本 Slice 与 V-010 Matrix 已同步写回这一约束。若将来目标平台
提供可证明的 per-process exact remote-address filter，可以替换 supervisor handoff，但必须保持同等或更窄
的 credential/payload 边界并重新形成 OS 证据。

## Verification after disposition

- transport 单元测试验证 inherited socket 不执行新 connect、wrong peer 在 credential resolution 前拒绝；
- supervisor environment 单元测试验证 credential 不可见；每次实际 handoff 另以 worker PID、闭合 environment
  keys、DNS/TCP/TLS/HTTP/payload 计数和 `SCM_RIGHTS` descriptor 数形成密封收据；
- profile/宿主探针联合验证 remote TCP 规则只服务继承 descriptor，Gateway child 的新 AF_INET/AF_UNIX
  socket 创建均由 `syscall-unix` 防火墙拒绝；
- G3b 外部 preflight 将在任何产品请求前，以独立 child 同时证明 inherited descriptor 已连接 exact peer、
  exact TLS 可用，以及新 Provider TCP、local TCP、DNS、其他 AF_UNIX 与 fork 均被拒绝；
- 每个正式 run 的 Answer/Gateway operation audit、transport audit 与 terminal receipt 将分别记录
  AF_UNIX call、connected descriptor handoff、HTTPS dispatch 和零新 DNS connect；在这些证据实际 PASS
  前，V-010/G3b 仍保持 not-run。
