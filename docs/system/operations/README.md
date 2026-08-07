---
id: SYS-OPS-INDEX
kind: system-operations-index
status: current
authority: operational
owners: [operations]
depends_on: [SYS-ARCH-DEPLOYMENT, SYS-QUALITY-SECURITY]
code: [src/software_world_model/interface]
tests: [tests/test_interface_runtime.py]
---

# 当前运维说明

- [非敏感 Provider 配置](configuration.md)
- [本机浏览器体验](local-browser.md)

这些说明只覆盖可重复的本地运行边界，不构成生产部署设计。点时运行证明、有效期和当前工作状态不是 System 运维规范的一部分。
