---
id: SYS-INDEX
kind: system-index
status: current
authority: normative
owners: [architecture]
depends_on: []
code: [src/software_world_model]
tests: [tests]
---

# 当前系统文档

本目录描述“系统是什么以及任何实现都不能破坏什么”。它独立于迭代、排期、测试计数和某次运行状态。`current` 表示设计当前生效，不等于所有可选能力均已实现或已生产启用。

## 阅读路径

1. [产品定位](product/vision.md)与[能力地图](product/capability-map.md)
2. [架构概览](architecture/overview.md)、[组件边界](architecture/components.md)与[架构不变量](architecture/invariants.md)
3. 当前切片引用的[系统契约](contracts/README.md)
4. [质量属性](quality/attributes.md)、[安全边界](quality/security-boundaries.md)与[验收原则](quality/acceptance-principles.md)
5. 需要本地运行时再读取[运维说明](operations/README.md)

## 唯一所有者

| 问题 | 唯一文档所有者 |
|---|---|
| 为什么构建、面向什么结果 | `product/` |
| 顶层关系、组件边界和不可破坏规则 | `architecture/` |
| 跨模块输入输出、权威和一致性语义 | `contracts/` |
| 系统级质量、安全和产品下限 | `quality/` |
| 当前可重复运行和配置方式 | `operations/` |

字段、私有状态、算法、错误枚举和数据库布局不在这里复制；除非它们影响调用方、安全、不可逆数据或跨模块一致性，否则由代码、Schema 和测试定义。
