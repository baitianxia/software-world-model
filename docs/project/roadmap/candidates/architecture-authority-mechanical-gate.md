---
id: ROADMAP-CANDIDATE-ARCHITECTURE-AUTHORITY-MECHANICAL-GATE
kind: roadmap-candidate
status: candidate
authority: planning-only
owners: [architecture, project, engineering]
depends_on: [SYS-ARCH-BASELINE, PROJECT-GOVERNANCE-ARCHITECTURE-CHANGE, PROJECT-GOVERNANCE-DOCUMENTATION]
code: []
tests: []
coding_input: false
deferred_until: current architecture and documentation audit is closed and the documentation check is green
---

# 待办：架构唯一入口机械门禁

## 状态

已登记，暂缓处理。本条目不授权修改 `scripts/docs.py`、提交钩子、CI、产品代码或任何 Iteration 状态。

## 背景

当前架构目录已经建立唯一顶层基线，但“只能有一个顶层架构入口、附录/ADR/Contract 不得成为平级架构来源”仍主要依靠文档约定和人工阅读。需要在其他架构和文档问题收敛、基线文档检查恢复绿色后，再把这项治理规则实现为低成本本地和远端门禁。

## 计划范围

1. 为顶层基线、架构附录、兼容投影、ADR 和 Contract 增加机器可读的文档角色及父基线引用。
2. 在 `scripts/docs.py check` 中检查顶层基线唯一性、角色归属、父基线、受保护章节和架构图完整性。
3. 检查第 14 节只能是非规范审计记录，不能重新声明覆盖或替代正文。
4. 将检查接入本地提交钩子和远端必需工作流；架构检查失败时阻止该文档变更，但不阻塞无关产品代码变更。
5. 为架构语义变更要求基线与 ADR 的可追溯差分；不通过静态检查伪装成已完成语义等价审计。

## 完成条件

- 任意时刻只有一个 `SYS-ARCH-BASELINE` 顶层架构入口。
- 附录、ADR、兼容投影和 Contract 无法声明自己拥有顶层架构语义。
- 基线章节、受保护概念和架构图缺失时检查失败。
- 架构变更未同步唯一基线或角色声明不完整时检查失败。
- 检查失败不会产生授权、暂停或新的 Iteration；只拒绝不合规文档变更。

## 暂不处理

本条目不改变架构内容、不新增 View、不改变 Agent/Reviewer 职责、不修改模型或 Provider 策略，也不替代人工架构语义审计。
