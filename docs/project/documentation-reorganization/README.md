---
id: PROJECT-DOCUMENTATION-REORGANIZATION
kind: project-documentation-reorganization
status: current
authority: documentation-maintenance
owners: [project, architecture]
depends_on: [SYS-ARCH-BASELINE, PROJECT-GOVERNANCE-DOCUMENTATION, PROJECT-GOVERNANCE-BOUNDARY]
code: []
tests: []
coding_input: false
as_of: 2026-10-01
---

# 文档重整登记

本文记录本次文档重整的边界和映射。它不是新的系统架构、开发计划或授权；ITER-010 产品开发保持暂停。

## 整理后的唯一入口

1. [系统文档入口](../../system/README.md) 只负责导航。
2. [完整架构基线](../../system/architecture/architecture-baseline.md) 是架构语义、模块职责、视图、运行流、不变量和九张架构图的唯一系统基线。
3. `docs/system/architecture/decisions/` 只记录改变架构语义的 ADR。ADR 本身不能替代基线；生效的 ADR 必须在基线的修订记录中被整合。
4. `docs/system/contracts/` 由各契约 Owner 维护稳定边界。契约可以细化基线，但不能删减架构维度或把实现策略提升为架构事实。
5. `docs/project/` 保存迭代、结果、发现和执行记录。它们解释项目如何验证系统，不得反向改写系统架构。
6. `docs/archive/` 保存历史材料，`docs/_generated/` 只保存生成索引，二者都不是规范入口。

## 本次修复

- 恢复了原始完整架构的十三个章节和九张 Mermaid 图；原章节不以摘要或模块清单替代。
- 已将后续确认的语义修正直接合并回原有正文及相关图：世界模型是完整的软件认知；主 Agent 可以按问题在认知和源码之间选择或交替；Reviewer 复核既有答案与证据，不重新作答；本轮证据只在本轮有效；发现世界模型与源码冲突时产生知识维护任务。旧的“原条款 + 第 14 节覆盖”草稿已被消除；第 14 节仅保留非规范审计映射，不再承载当前语义或修改正文优先级。
- 把“架构是否改变”与“当前实现是否完成”分开。实现状态、Provider 运行记录、测试夹具、Prompt/Schema 和具体调用预算不再作为架构入口。
- 不改变 ITER-010 的产品状态、授权或执行字段；其 proposal、readiness、slice、result 和 finding 仍由原迭代文档负责。
- 保留旧文档的身份、来源和追溯关系；没有通过删正文来制造“干净”版本。发现与旧契约发生语义冲突时，先标记冲突，再由架构基线或明确 ADR 收束。

> 更正：上一版整理草稿曾误改 ITER-010 的状态和执行字段。本次已撤回该误改；架构整理不负责启动、暂停、授权或重排任何开发 Iteration。Iteration 目录和 Manifest 仅在架构语义确实变化时维护系统文档引用，不在本次整理中改变产品执行状态。

## 权威判定顺序

阅读或开发前按以下顺序判定：

`PROJECT-CURRENT → architecture-baseline → applicable ADR → contract owner → iteration evidence`。

当较低层文档与较高层文档冲突时，不能用项目计划、运行结果或单个测试通过来默默覆盖系统语义；应记录冲突并停止受影响的产品动作。普通文档排版、索引和历史说明的修复不等于架构变更。

## 尚未自动化的检查

现有文档脚本可以检查元数据、链接、依赖和部分迭代状态，但不能证明旧架构正文与完整基线在语义上等价，也不能自动识别一段实现细节何时越过了契约边界。本登记不把机械检查结果冒充语义审计；后续架构变更必须人工对照完整基线的章节和图，并在同一变更中更新 ADR 与契约 Owner。
