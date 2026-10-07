---
id: PROJECT-GOVERNANCE-ARCHITECTURE-CHANGE
kind: project-governance
status: current
authority: project-governance
owners: [architecture, project, engineering]
depends_on: [PROJECT-GOVERNANCE-BOUNDARY, PROJECT-GOVERNANCE-DOCUMENTATION]
code: [scripts/docs.py, scripts/plan_gate.py]
tests: [tests/test_docs_gate.py, tests/test_plan_gate.py]
---

# 架构变更规则

本规则把架构文档从普通实现输入中隔离出来，防止开发过程中通过修改文档改变系统目标。它不增加新的产品架构，只规定当前架构的唯一所有者、变更路径和开发边界。

## 架构设计的最简原则

架构只保留实现已确认目标所必需的职责、边界、关系和约束。新增组件、View、数据流或治理边界，必须说明现有架构无法承担的具体目标；如果现有职责可以满足目标，不新增抽象。最简不等于删减长期目标，也不允许把 MVP 的暂时范围改写成架构边界，更不允许用实现细节充实架构。

## 唯一权威

`docs/system/architecture/architecture-baseline.md`（`SYS-ARCH-BASELINE`）是唯一完整架构基线，拥有顶层组件、职责、关系、运行流程、领域概念、架构图和不可破坏约束。

- `docs/system/architecture/decisions/` 只记录为什么作出选择，以及如何迁移；ADR 被基线吸收前不能单独改变系统语义。
- `docs/system/architecture/*.md` 是基线附录，只能细化基线，不能删减未明确废弃的概念或关系。
- `docs/system/contracts/` 只记录跨模块稳定语义；实现协议、Prompt、Provider、局部 Schema、测试夹具和运行状态不属于架构权威。
- `docs/project/` 只记录计划、实现选择、发现、验证和结果；它可以引用 System，但不能反向定义 System。
- `docs/archive/` 和 `docs/_generated/` 不能作为当前架构输入。

## 什么时候算架构变更

下列任一变化都属于架构变更，不是普通文档整理：

- 删除或收窄基线章节、组件、View、Owner、关系、运行流程或架构图；
- 改变 World Model、Knowledge Engine、Source Integration、Agent、Reviewer 或 Response Control 的权威和依赖；
- 改变正式知识形成、来源事实、证据生命周期、Snapshot 发布或跨模块一致性；
- 把默认产品路径改为另一条模式、固定角色流水线或 Source-off/Source-only 边界；
- 把实现协议提升为跨模块必需语义，或把系统语义下沉为某次实现选择。

仅修改类、字段、算法、文件布局、Prompt、模型配置、测试夹具或错误枚举，且不改变上述边界时，属于项目实现，不得借此修改架构基线。

## 架构文档冻结规则

当前开发检出的 `docs/system/architecture/` 已按用户明确指示冻结。冻结期间，以下任何变化都必须先取得用户明确同意，不能由普通开发授权、测试结果、收据或自动化流程推断同意：

- 修改任意现有架构文件的内容，包括格式、空白、链接、来源标注、章节顺序和历史记录；
- 新增、删除、重命名、移动或替换架构文件、目录和符号链接；
- 修改基线、附录、ADR、架构索引，或执行架构迁移、整理、生成和回写。

因此，冻结期间不存在“纯文档重排”“索引修复”或“历史状态修复”的免确认例外。普通产品开发可以继续修改代码、测试和其授权范围内的项目文档，但不得借此更新架构文档或刷新冻结清单。冻结清单不会因检查失败、测试通过或提交而自动更新。

本次机械锁定只覆盖当前开发检出；其他克隆、工作树或分支不能被假定为已锁定。只有在用户明确同意变更范围后，才能解除保护、完成架构变更流程，并由用户同意后的新基线重新冻结。

## 唯一变更流程

1. 在 `docs/project/` 登记问题、证据、受影响的基线章节、替代方案和最早可证伪方式。
2. 创建或修订 ADR，明确新增、修改、废弃条款以及迁移和回退方式。
3. 接受决策后，在同一变更中增量更新 `architecture-baseline.md`，保留未受影响的原章节、概念、关系和架构图。
4. 同步修正附录、Contract、`docs/project/current.md` 和活动 Manifest 的引用；清理被替代的 `current` 条款，不能并列保留冲突解释。
5. 重新生成索引，运行 `python3 scripts/docs.py check`；同时执行基线语义差分，确认没有未经批准的章节、关键概念、组件关系或图被删除。
6. 只有新的干净基线提交完成后，受该架构变更影响的产品 action 才能继续；开发 action 不得把自己的局部结果写回架构作为授权依据。该流程不会解除用户已经声明的产品开发暂停。

## 当前已知的机械缺口

现有 `docs.py` 和 `plan_gate.py` 能检查文档结构、路径和计划收据，但尚未完整检查架构章节、关键概念和架构图的语义保留。因此在专门的基线语义检查落地前，涉及架构语义的变化必须按本规则人工对照基线并由架构负责人确认；“文档检查通过”不能替代架构变更批准。当前检出另有独立的冻结清单和机械检查，用于阻止架构文件集或内容在未经同意时发生变化；它不会自动更新清单，也不能替代用户批准和架构变更流程。
