---
id: SYS-QUALITY-SECURITY
kind: system-quality
status: current
authority: normative
owners: [security, architecture]
depends_on: [SYS-ARCH-INVARIANTS]
code: [src/software_world_model/ai_infrastructure, src/software_world_model/source_integration, src/software_world_model/application_services/citation_projection.py, src/software_world_model/infrastructure/file_structure_read_bundle.py, src/software_world_model/infrastructure/file_citation_observation_store.py, src/software_world_model/interface, validation/structure_world_model_iteration_003/isolation, validation/structure_world_model_iteration_003/g3b, validation/structure_world_model_iteration_007/slice1_live_evaluator.py]
tests: [tests/test_model_gateway.py, tests/test_source_operations.py, tests/test_browser_chat_interface.py, tests/test_structure_read_bundle.py, tests/test_structure_view_cli.py, tests/test_citation_projector.py, tests/test_iteration_003_g2_isolation.py, tests/test_iteration_003_g3b.py, tests/test_model_egress_gateway.py, tests/test_pinned_ark_https.py, tests/test_world_model_http.py, tests/test_world_model_evaluation_grant.py, tests/test_world_model_gateway_authorization.py, tests/test_iteration_007_slice1_freeze.py, tests/test_iteration_007_slice1_live_evaluator.py]
---

# 安全边界

## 不可信输入

用户输入、软件来源内容、模型响应、Provider 元数据、外部工具输出和交付确认均不可信。它们必须通过其 Owner 的授权、Schema、身份和语义检查后才能影响权威状态。

## 权限规则

- 模型不能获得 shell、Web、MCP、文件或来源工具；领域 Tool Proposal 由平台授权执行。
- Source Operation 必须绑定当前授权、精确 Binding、Target 和预算，且只读。
- Secret 只保存 Reference，在网络分派前解析；不得进入文档、命令参数、数据库正文、日志或 Result。
- 编码、Conformance、Capability Qualification、历史 Product PASS 或历史披露许可都不能推导新的外部分派授权。每次新的
  `EVALUATION_ONLY` 问题披露必须由 exact grant 记录用户、时间、authorization ref 和 payload boundary；未授权 grant 必须在
  创建 session、Provider socket 或 listener 前拒绝。Gateway 必须再验证由同一 grant 派生的当前 session receipt，才能解析
  credential 或进入 qualified baseline；历史 permission 只能保留为 capability baseline provenance。
- 生成与审核使用隔离上下文，Provider 会话记忆不能成为正式输入。
- `JAVA_SOURCE_SEMANTICS@1` 的 Plan、Draft 与 Review 是三个独立 Gateway workload：Plan 不得读取正式知识 payload，Draft 不得
  读取 Reviewer 或 Citation observation，Review 不得读取 Provider 会话记忆或 Source。三者只能通过平台密封的 Requirement/
  Plan/Query Result/Draft 逐阶段传递；role package、socket/session receipt 与调用审计不可复用。
- `WORLD_MODEL` 答案进程的应用输入只能读取 package 与不含 Evidence payload 的 exact Snapshot Read Bundle；解释器、系统 runtime、精确 ancestor directory traversal 和独立输出 capability 必须单列，且不得包含目标来源、工作树、权威/旧数据库、Evidence/Citation Store 或另一角色输出。其网络默认拒绝：无模型阶段禁止全部出站；真实模型阶段只能连接 evaluator-owned exact Model Egress Gateway，由网关校验 Manifest 固定的 Provider scheme/host/port/path 并注入 credential。答案进程不能直连 DNS、公网、Source remote 或 Citation Projector。若本机 OS 不能按单一公网 IP 过滤 Gateway connect，允许由无 credential、无请求/响应 payload port 的 Gateway supervisor 预解析，并为每个已授权 Provider 调用建立一个 exact peer TCP socket，再把这些 connected descriptor 与 evaluator 已绑定的 exact `0600` AF_UNIX listener 交给 sandboxed Gateway child；descriptor 数量必须与 Profile 的 exact call contract 相同。固定 Ark transport 明确发送 `Connection: close`，所以 `JAVA_SOURCE_SEMANTICS@1` 必须在 Answer 启动前一次性获得三个不同的 connected descriptor，分别供 Plan、Draft、Review 消费；少于、多于、重复或跨角色复用均失败关闭。地址 scope 必须如实区分标准 public unicast 与 executor 明确提供的 synthetic external peer，loopback、普通 private、link-local 与其他 reserved 地址仍拒绝，不能把 synthetic 地址误报成公网 IP。若 Seatbelt 对继承 TCP 数据面仍要求 remote-port `network-outbound`，该规则只能与拒绝 `SYS_socket`/`SYS_socketpair`/`SYS_socket_delegate` 的 syscall firewall 联合使用；child 必须无法创建任何新 AF_UNIX/INET/INET6 socket，并在解析 credential 前复核 peer、TLS certificate/SNI 与 exact HTTP scheme/Host/port/path。该组合只证明 digest-sealed 闭合 workload 的新 socket 创建被 OS 拒绝：它不是抵抗任意 native code execution 的 exact destination firewall，因为 Darwin `disconnectx`/`connectx` 可重定向既有 descriptor。正常 workload 必须另以 digest seal、禁止 fork 与 `connect`/`bind` 零计数审计闭合；若威胁模型包含任意 native code execution，必须改用 VM/container/per-process network namespace 或等价的 exact destination enforcement。preflight 必须真实执行继承 descriptor 已连接 exact peer、继承 listener 往返、继承 TLS 和新 socket denial；审计必须分列 supervisor connection provisioning、listener handoff 与 child Provider dispatch，并验证三者数量与角色顺序，不能把 remote-port 规则单独描述为 endpoint allowlist，也不能声称 OS 提供了实际不存在的 remote-IP filter。
- Evidence observation 只由 trusted broker 在密封 Result 后通过窄 Knowledge owner Port 读取，并按该 Result allowlist 物化新的 disposable Citation Store。独立 Projector 只能读取 package、Result seal 与这个 exact Store；不能直接挂载权威数据库或完整 Evidence Store，不出网，没有模型、Query、Update 或答案回传端口。Store 缺失、额外、重复、换序或 digest 不匹配均失败关闭。
- OS 隔离证据必须区分应用输入、runtime/ancestor traversal、输出与拒绝目标，绑定实际 policy 和 capability 参数。若 exact ancestor directory capability 可枚举其直接条目名，必须把名称披露作为 executor limitation，不能误称为 metadata-only；这不等于允许读取子文件内容。使用 capability sandbox 时只能声称相关操作被 OS 拒绝，不能声称未实际建立的 mount/network namespace；固定探针、产品 workload 必须分进程，计划、Mock、probe-only 或进程自报不是执行证据。候选冻结还必须在 role 实际使用的隔离解释器 flags、环境和 package root 下导入每个真实 entrypoint；普通测试环境可见的 `site-packages` 不能充当隔离 role dependency closure。source-off Answer 的包初始化不得因无关的 Update/export convenience import 获得 parser 或 Source dependency。
- 无认证 HTTP 服务只能绑定回环地址；非本机部署必须先补认证、授权和威胁模型。

失败、配置缺失、资格过期、身份漂移、输入截断或结果未知都采用 fail-closed 行为，但不得把未知伪装成确定失败。
