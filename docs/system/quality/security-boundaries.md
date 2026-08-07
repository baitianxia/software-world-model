---
id: SYS-QUALITY-SECURITY
kind: system-quality
status: current
authority: normative
owners: [security, architecture]
depends_on: [SYS-ARCH-INVARIANTS]
code: [src/software_world_model/ai_infrastructure, src/software_world_model/source_integration, src/software_world_model/interface]
tests: [tests/test_model_gateway.py, tests/test_source_operations.py, tests/test_browser_chat_interface.py]
---

# 安全边界

## 不可信输入

用户输入、软件来源内容、模型响应、Provider 元数据、外部工具输出和交付确认均不可信。它们必须通过其 Owner 的授权、Schema、身份和语义检查后才能影响权威状态。

## 权限规则

- 模型不能获得 shell、Web、MCP、文件或来源工具；领域 Tool Proposal 由平台授权执行。
- Source Operation 必须绑定当前授权、精确 Binding、Target 和预算，且只读。
- Secret 只保存 Reference，在网络分派前解析；不得进入文档、命令参数、数据库正文、日志或 Result。
- 生成与审核使用隔离上下文，Provider 会话记忆不能成为正式输入。
- 无认证 HTTP 服务只能绑定回环地址；非本机部署必须先补认证、授权和威胁模型。

失败、配置缺失、资格过期、身份漂移、输入截断或结果未知都采用 fail-closed 行为，但不得把未知伪装成确定失败。
