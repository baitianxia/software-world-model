---
id: FINDING-003-025
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, architecture, quality, security]
depends_on: [ITER-003-SLICE-001, ITER-003-VERIFICATION, FINDING-003-022, FINDING-003-024]
code: [src/software_world_model/ai_infrastructure/model_egress_gateway.py, src/software_world_model/ai_infrastructure/pinned_ark_https.py, validation/structure_world_model_iteration_003/g3b/gateway.sb, validation/structure_world_model_iteration_003/g3b/gateway_workload.py, validation/structure_world_model_iteration_003/g3b/os_probe_worker.py, validation/structure_world_model_iteration_003/g3b/run_g3b.py, validation/structure_world_model_iteration_003/g3b/evaluate_results.py]
tests: [tests/test_model_egress_gateway.py, tests/test_pinned_ark_https.py, tests/test_iteration_003_g3b.py]
iteration: ITER-003
classification: system-contract
disposition: inherit-provider-and-listener-descriptors-while-denying-all-new-socket-syscalls
target: SYS-QUALITY-SECURITY
---

# FINDING-003-025：Seatbelt 对继承 TCP 数据面仍要求 network-outbound capability

## Observation

容量修复后的正式 G3b checkpoint `1b24d8ebf36ee1364cbaecac51a94f7451272780` 完成三个 role 的
结构化 preflight。Answer 与 Citation Projector 全部 PASS、受保护 stage 未变化；Gateway 的文件、credential
边界、exact AF_UNIX bind、新 Provider/local connect、DNS、其他 AF_UNIX 与 fork 探针均符合预期，但对已连接
Provider descriptor 执行 TLS 时被 Seatbelt 以 `EPERM` 拒绝。因此，仅“不授予 network-outbound”不能同时实现
“使用继承 TCP descriptor”和“拒绝新 TCP connect”。该失败发生在任何 HTTP、模型请求或产品 payload 发送前。

随后最小宿主探针确认：`remote tcp "*:443"` 可让已连接 descriptor 完成固定 Ark hostname 的 TLS certificate
验证；同时显式 `deny syscall-unix`，再只允许除 `SYS_socket`/`SYS_socketpair`/`SYS_socket_delegate` 外的 syscall，
可使继承 descriptor 继续收发而所有新 AF_INET/AF_UNIX socket 创建均以 `EPERM` 失败。macOS 的 `/etc` 是别名路径，Gateway 还必须
优先从已授权 canonical `/private/etc/ssl/cert.pem` 加载 CA，不能为了别名穿越扩大 `/etc` 目录 capability。

更强的反例探针也确认了机制边界：在同一 `remote tcp "*:443"` 规则下，一个由父进程继承但尚未连接的 INET
descriptor 可以执行普通 `connect()`；本机 Darwin 上，已连接 TCP descriptor 经 `disconnectx()` 后还能用
`connectx()` 重定向。对 `SYS_connect*` 增加 `require-not` 不能形成可继承的数据面与 connect syscall 的可靠分离。
因此“Seatbelt 拒绝所有新连接”是不成立的声明；可证明事实只是 child 不能创建新 socket，且正式 child 根本不继承
任何未连接 INET descriptor。

## Evidence

- `var/iteration-003/g3b/1b24d8ebf36ee1364cbaecac51a94f7451272780/dispatch/preflight.json` 记录
  Answer/Projector PASS、Gateway 唯一失败探针 `allowed_inherited_exact_provider_tls`、`errno=1` 与
  `protected_stage_unchanged=true`；
- 同一 dispatch 的 bootstrap 与 Gateway provisioning 收据均为无 credential、无产品 payload、零 TLS、零 HTTP；
- 本机最小探针在无 credential、无 HTTP/payload 条件下得到 `tls-cert True`，随后新 AF_INET socket 得到
  `PermissionError errno=1`；
- 无 credential、无 HTTP/payload 的反例探针证明 inherited unconnected INET descriptor 的 `connect()` 可成功，
  且本机 `disconnectx`/`connectx` 可重定向既有 TCP descriptor；这些反例阻止扩大 OS 结论；
- disposition 后的三角色诊断 preflight 得到 Answer/Gateway/Projector 全部 PASS、Gateway inherited AF_UNIX
  round trip 为 true、所有 probe failures 为空、stage unchanged；
- 36 项聚焦测试覆盖 prebound exact listener、wrong path failure、profile syscall firewall、receipt 与 evaluator
  binding，全部通过。

## Impact and classification

该事实改变 G3b 在 macOS 上“新网络能力由 OS 拒绝”的可证明机制与 Result 解释，属于跨模块安全不变量，分类为
`system-contract`。只添加 `*:443` 而不限制 socket 创建会扩大 child 的网络能力，不可接受；只做 Python audit
也不能替代新 socket 创建的 OS enforcement。另一方面，现有 Seatbelt 组合不是任意 native-code compromise 下的
exact destination firewall，文档与 Result 也不得作此声明。

## Decision and disposition

可信 evaluator 在 child 启动前创建两项最小 capability：无 credential/payload supervisor 连接并 peer-pin 一个
Provider TCP descriptor；evaluator 另绑定、`0600`、listen 一个 exact AF_UNIX Gateway listener。sandboxed
Gateway child 只继承这两个 descriptor。profile 允许这两个继承数据面的 AF_UNIX 和 remote TCP 443 I/O，但以
`syscall-unix` 防火墙拒绝 `SYS_socket`、`SYS_socketpair` 与 `SYS_socket_delegate`，因此 child 不能创建新的
DNS、INET、INET6 或 AF_UNIX socket。child 仍须在 credential resolution 前复核 Provider peer、TLS hostname/certificate 和 exact HTTP
scheme/Host/port/path。

preflight 必须同时证明：继承 Provider descriptor 已连接 exact peer（普通重复 `connect` 返回 `EISCONN`）、继承
AF_UNIX listener 的真实 request/response 往返、继承 Provider TLS 成功、新 AF_INET 与 AF_UNIX socket 创建被
OS 拒绝、DNS/connect/fork/越界文件拒绝、credential 只在 Gateway 可见，以及 stage unchanged。每个产品 run
必须保存独立 listener handoff 收据并绑定 invocation 的 exact socket staging root；evaluator 逐项重算摘要并验证 terminal、
Gateway summary 与 batch capability 声明。`remote tcp "*:443"` 不能单独被描述为 endpoint allowlist；安全结论
来自“可信预连接 exact peer + 禁止 child 创建任何新 socket + child TLS/HTTP 复核”的联合证据。

正式 Gateway 仅运行 digest-sealed package/runtime，`python -I -S -B` 关闭非密封启动扩展，禁止 fork；正常 workload
operation audit 必须证明 `connect`/`bind` 为零。该闭合代码执行前提与 OS socket-creation denial 共同构成本 Gate
的 executor 边界；它不等于抵抗任意 native code execution。若该威胁进入范围，必须使用 VM/container/per-process
network namespace 或等价的 exact destination enforcement 后重新验证。

## Verification after disposition

聚焦测试、完整回归与新 checkpoint 的正式 preflight/60-run batch 共同裁决。旧 `1b24d8e…` preflight 失败目录
保持不变；它不能被升级为正式 Product Result。Production Activation 继续为 `NOT_EXECUTED`。
