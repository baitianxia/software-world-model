---
id: SYS-QUALITY-SECURITY
kind: system-quality
status: current
authority: normative
owners: [security, architecture]
depends_on: [SYS-ARCH-INVARIANTS]
code: [src/software_world_model/ai_infrastructure, src/software_world_model/source_integration, src/software_world_model/application_services/citation_projection.py, src/software_world_model/infrastructure/file_structure_read_bundle.py, src/software_world_model/infrastructure/file_citation_observation_store.py, src/software_world_model/interface, validation/structure_world_model_iteration_003/isolation]
tests: [tests/test_model_gateway.py, tests/test_source_operations.py, tests/test_browser_chat_interface.py, tests/test_structure_read_bundle.py, tests/test_structure_view_cli.py, tests/test_citation_projector.py, tests/test_iteration_003_g2_isolation.py]
---

# 安全边界

## 不可信输入

用户输入、软件来源内容、模型响应、Provider 元数据、外部工具输出和交付确认均不可信。它们必须通过其 Owner 的授权、Schema、身份和语义检查后才能影响权威状态。

## 权限规则

- 模型不能获得 shell、Web、MCP、文件或来源工具；领域 Tool Proposal 由平台授权执行。
- Source Operation 必须绑定当前授权、精确 Binding、Target 和预算，且只读。
- Secret 只保存 Reference，在网络分派前解析；不得进入文档、命令参数、数据库正文、日志或 Result。
- 生成与审核使用隔离上下文，Provider 会话记忆不能成为正式输入。
- `WORLD_MODEL` 答案进程的应用输入只能读取 package 与不含 Evidence payload 的 exact Snapshot Read Bundle；解释器、系统 runtime、精确 ancestor directory traversal 和独立输出 capability 必须单列，且不得包含目标来源、工作树、权威/旧数据库、Evidence/Citation Store 或另一角色输出。其网络默认拒绝：无模型阶段禁止全部出站；真实模型阶段只能连接 evaluator-owned exact Model Egress Gateway，由网关校验 Manifest 固定的 Provider scheme/host/port/path 并注入 credential。答案进程不能直连 DNS、公网、Source remote 或 Citation Projector。
- Evidence observation 只由 trusted broker 在密封 Result 后通过窄 Knowledge owner Port 读取，并按该 Result allowlist 物化新的 disposable Citation Store。独立 Projector 只能读取 package、Result seal 与这个 exact Store；不能直接挂载权威数据库或完整 Evidence Store，不出网，没有模型、Query、Update 或答案回传端口。Store 缺失、额外、重复、换序或 digest 不匹配均失败关闭。
- OS 隔离证据必须区分应用输入、runtime/ancestor traversal、输出与拒绝目标，绑定实际 policy 和 capability 参数。若 exact ancestor directory capability 可枚举其直接条目名，必须把名称披露作为 executor limitation，不能误称为 metadata-only；这不等于允许读取子文件内容。使用 capability sandbox 时只能声称相关操作被 OS 拒绝，不能声称未实际建立的 mount/network namespace；固定探针、产品 workload 必须分进程，计划、Mock、probe-only 或进程自报不是执行证据。
- 无认证 HTTP 服务只能绑定回环地址；非本机部署必须先补认证、授权和威胁模型。

失败、配置缺失、资格过期、身份漂移、输入截断或结果未知都采用 fail-closed 行为，但不得把未知伪装成确定失败。
