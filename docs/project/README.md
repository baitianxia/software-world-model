---
id: PROJECT-INDEX
kind: project-index
status: current
authority: project-governance
owners: [project]
depends_on: [SYS-INDEX]
code: []
tests: []
---

# 项目文档

本目录回答“下一步为什么做、这一轮做什么、开发中发现了什么、实际结果如何”。它不拥有永久系统语义。

## 日常入口

- [当前工作上下文](current.md)：唯一活动状态和 Agent 开发入口。
- [Roadmap](roadmap/README.md)：结果方向与候选，不直接授权编码。
- [Iterations](iterations/README.md)：按轮次保存开发输入、发现、决策和结果。
- [Governance](governance/README.md)：选择迭代、写开发设计、验证和回写规则。

每轮开发必须从明确的 Proposal 和 Development Slice 开始。实现过程中出现的新事实先进入该轮 `findings/`，再被吸收到系统文档、本轮设计、Roadmap 或代码/测试；不能留成无人处置的日志。
