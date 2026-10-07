---
id: PROJECT-REFERENCE-STANDING-AUTHORITY-HISTORY
kind: implementation-reference
status: historical
authority: historical-evidence
owners: [engineering, operations, project]
depends_on: [SYS-ADR-019, SYS-ARCH-BASELINE]
code: []
tests: []
coding_input: false
source_path: docs/system/architecture/decisions/ADR-019-public-source-standing-model-authority.md
as_of: 2026-10-02
---

# standing authority implementation history

以下内容从 ADR-019 的项目实例段落迁出，保留具体配置和版本迁移信息。它们不定义持续授权的通用语义。

曾有 execution profile 把 DeepSeek 映射为备用路线，并选择 `DEEPSEEK_DISPATCH_ADMISSION@1` 作为 admission plugin；非高峰窗口是
自动准入条件，峰时运行需要 exact override。曾有 Artifact Session `@4` 以 standing authority 为父对象，由 launcher 重验公开 upstream、
clean HEAD、exact commit/tree 与许可证路径，再派生绑定 product、Source Profile/allowlist、World Model、Chat Binding、route/configuration/
qualification、预算和时窗的 session authority。Provider Session、Turn attempt 和 call disclosure receipt 通过摘要链绑定父对象；旧
Artifact Session `@1—@3` 仅保留兼容语义。以上均是历史实现/配置，不是架构层的第二套权限规则。
