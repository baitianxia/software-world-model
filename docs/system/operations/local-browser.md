---
id: SYS-OPS-LOCAL-BROWSER
kind: system-operations
status: current
authority: operational
owners: [operations, interface]
depends_on: [SYS-ARCH-DEPLOYMENT, SYS-ADR-014, SYS-ADR-015, SYS-ADR-016, SYS-ADR-017, SYS-ADR-018, SYS-ADR-019]
code: [pyproject.toml, src/software_world_model/interface/engineering_chat_alpha_cli.py]
tests: [tests/test_engineering_chat_alpha_cli.py, tests/test_engineering_chat_browser.py]
---

# 本机浏览器当前入口

当前唯一产品体验入口是 `swm-engineering-chat`。它是唯一允许用于方向判断和用户体验的浏览器入口。

以下入口只用于兼容或评估，不得当作产品 Chat：

- `swm-http-evaluation`
- `swm-browser-evaluation`
- `swm-engineering-qa-evaluation`
- `swm-engineering-qa-preview-evaluation`
- 独立 World Model evaluation 页面

## 使用边界

- 只允许 loopback 访问，不提供生产入口。
- 必须使用当前开发计划指定的精确工程、版本和 session 配置。
- 首问、追问、新问题和单题失败后继续服务必须进入同一条 Agent 主路径。
- 不得用静态回放、Evidence-first 旧路径或独立 World Model 页面代替产品体验。
- 模型、源码或复核失败必须显示真实限制，不得静默切换到另一套产品实现。

旧启动命令、配置细节和运行记录属于历史参考，不是当前开发输入。
