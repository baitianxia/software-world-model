---
id: PROJECT-REFERENCE-ROUTING-INSTANCE-HISTORY
kind: implementation-reference
status: historical
authority: historical-evidence
owners: [engineering, project]
depends_on: [SYS-ARCH-BASELINE]
code: []
tests: []
coding_input: false
source_path: docs/system/architecture/invariants.md
as_of: 2026-10-01
---

# routing instance history

以下内容从 `docs/system/architecture/invariants.md` 的实现/运行记录原样移出，保留当时措辞；其中“当前”“下一步”“须执行”均为历史语境，不是现行任务、架构决策或能力验收。读取最新工作状态应回到 [current](../current.md)。

## 当前配置实例与历史实现证据

当前 ITER-010 配置把 Ark 映射到 `preferred`、DeepSeek 映射到 `fallback`；备用 execution profile 选择的调度插件以
`DEEPSEEK_DISPATCH_ADMISSION@1` 收据和 `V-DEEPSEEK-IDLE-001` 证据验证。该映射、名称与插件实例只是可替换的当前配置和历史实现证据，
不定义 INV-018 的分支、质量、授权或 fallback 语义。
