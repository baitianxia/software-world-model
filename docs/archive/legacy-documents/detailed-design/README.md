# 详细设计

本目录保存阶段无关、可跨迭代复用的详细设计。某次迭代的技术选择位于 `implementation/`，不能反向成为一般设计。

## 治理入口

| 文档 | 作用 |
|---|---|
| [详细设计总纲](Software_World_Model_Detailed_Design.md) | 主题划分原则、依赖、状态与变更规则 |
| [Design Baseline Manifest — Revision 002](governance/Design_Baseline_Manifest_Iteration_001_Revision_002.md) | 固定当前可采用的 22 个 Accepted 主题 |
| [Review Record 001](governance/Detailed_Design_Review_Record_001.md) | 保存静态评审事实 |
| [Acceptance Record 001](governance/Detailed_Design_Acceptance_Record_001.md) | 保存主题接受决定 |

## 主题索引

当前共有 24 个主题：22 个 `Accepted`，2 个 `In Review`。

## 共享执行、模型与观测

| 主题 | 状态 |
|---|---|
| [DD-X-CAPABILITY-EXECUTION](topics/DD-X-CAPABILITY-EXECUTION.md) | Accepted |
| [DD-AI-MODEL-GATEWAY](topics/DD-AI-MODEL-GATEWAY.md) | Accepted |
| [DD-MGT-CAPABILITY-EVALUATION](topics/DD-MGT-CAPABILITY-EVALUATION.md) | Accepted |
| [DD-X-TELEMETRY-COST](topics/DD-X-TELEMETRY-COST.md) | Accepted |

## Scope、来源与管理

| 主题 | 状态 |
|---|---|
| [DD-KNW-KNOWLEDGE-SCOPE](topics/DD-KNW-KNOWLEDGE-SCOPE.md) | Accepted |
| [DD-SRC-DATA-SOURCE](topics/DD-SRC-DATA-SOURCE.md) | Accepted |
| [DD-SRC-SOURCE-ARTIFACT](topics/DD-SRC-SOURCE-ARTIFACT.md) | Accepted |
| [DD-APP-MANAGEMENT](topics/DD-APP-MANAGEMENT.md) | Accepted |

## Knowledge Core

| 主题 | 状态 |
|---|---|
| [DD-KNW-REFERENCE-CONTEXT](topics/DD-KNW-REFERENCE-CONTEXT.md) | Accepted |
| [DD-KNW-SCHEMA-CORE](topics/DD-KNW-SCHEMA-CORE.md) | Accepted |
| [DD-KNW-CONTEXT-COMPARISON](topics/DD-KNW-CONTEXT-COMPARISON.md) | Accepted |
| [DD-KNW-EVIDENCE](topics/DD-KNW-EVIDENCE.md) | Accepted |
| [DD-KNW-ENTITY](topics/DD-KNW-ENTITY.md) | Accepted |
| [DD-KNW-FACT](topics/DD-KNW-FACT.md) | Accepted |
| [DD-KNW-INFERENCE-CONFLICT](topics/DD-KNW-INFERENCE-CONFLICT.md) | Accepted |
| [DD-KNW-ADMISSION](topics/DD-KNW-ADMISSION.md) | Accepted |
| [DD-KNW-SNAPSHOT-PUBLICATION](topics/DD-KNW-SNAPSHOT-PUBLICATION.md) | Accepted |
| [DD-KNW-PERSISTENCE](topics/DD-KNW-PERSISTENCE.md) | Accepted |
| [DD-KNW-SCHEMA-EVOLUTION](topics/DD-KNW-SCHEMA-EVOLUTION.md) | In Review；仅跨 Schema Adoption 时启用 |

## Application 与响应可信链

| 主题 | 状态 |
|---|---|
| [DD-APP-KNOWLEDGE-UPDATE](topics/DD-APP-KNOWLEDGE-UPDATE.md) | Accepted |
| [DD-APP-KNOWLEDGE-USE](topics/DD-APP-KNOWLEDGE-USE.md) | Accepted |
| [DD-APP-AGENTIC-TASK](topics/DD-APP-AGENTIC-TASK.md) | Accepted |
| [DD-APP-RESPONSE-CONTROL](topics/DD-APP-RESPONSE-CONTROL.md) | Accepted |

## 条件语义能力

| 主题 | 状态 |
|---|---|
| [DD-SEM-SEMANTIC-VIEW](topics/DD-SEM-SEMANTIC-VIEW.md) | In Review；首个切片不依赖稳定 View |

`In Review` 主题不能被当前实现隐式使用。需要启用时，必须先完成接受决定并建立新的 Design / Implementation Baseline。
