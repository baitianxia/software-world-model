# Software World Model 软件世界模型平台架构设计说明书

> **文档状态：历史输入稿。** 本文保留最初架构方案及其原始措辞，不再作为当前设计基线。当前生效的 V1.2 概要架构见 [Software_World_Model_Architecture_Baseline.md](../architecture/Software_World_Model_Architecture_Baseline.md)；其他文档与当前基线冲突时，以当前基线为准。

**版本：V1.0**\
**文档类型：架构设计文档（Architecture Design Document）**

------------------------------------------------------------------------

# 1. 文档概述

## 1.1 文档目的

本文档定义 Software World
Model（软件世界模型）平台的总体架构、核心设计原则、领域模型、模块边界、数据模型、演化机制以及扩展机制。

本文档作为后续详细设计、接口设计、研发拆解和技术评审的基础。

------------------------------------------------------------------------

# 2. 背景与建设目标

## 2.1 背景

现代企业软件系统具有以下特点：

-   系统数量持续增长
-   业务流程跨多个系统
-   技术架构持续演化
-   文档与代码逐渐失同步
-   核心知识依赖少数专家

传统方式依靠：

-   阅读代码
-   查询文档
-   人工经验

无法满足复杂系统理解需求。

同时，大模型具备强大的推理能力，但缺少企业私有软件系统的结构化认知。

因此需要构建 Software World Model。

------------------------------------------------------------------------

## 2.2 建设目标

构建一个：

> 面向 AI 推理的软件系统数字孪生。

支持：

-   软件结构理解
-   业务流程理解
-   运行状态分析
-   架构演化分析
-   影响范围分析
-   AI 辅助架构决策

------------------------------------------------------------------------

# 3. 核心设计原则

## 3.1 Source First

所有知识必须来源于事实。

知识必须包含：

-   来源
-   证据
-   时间
-   置信度

------------------------------------------------------------------------

## 3.2 Fact 与 Inference 分离

### Fact Layer

事实来源：

-   代码
-   Trace
-   数据库
-   配置

### Inference Layer

推理结果：

-   Behavior
-   Business

------------------------------------------------------------------------

## 3.3 可重建原则

知识库不是人工维护结果。

采用：

    Source

    ↓

    Knowledge Compiler

    ↓

    Software World Model

------------------------------------------------------------------------

## 3.4 持续演化原则

系统通过事件驱动持续更新：

    Change Event

    ↓

    Impact Analysis

    ↓

    Knowledge Update

    ↓

    Validation

------------------------------------------------------------------------

# 4. 总体架构

                             User

                              |

                              v

                    Reasoning Platform

                    - Query Planner
                    - LLM Agent
                    - Tool Runtime


                              |

                              v

                    Answer Validation


    ================================================


                  Software World Model


    ================================================


     Structure | Behavior | Business

     Runtime   | History  | Environment


    ================================================


                 Knowledge Governance


    ================================================


                 Knowledge Compiler


    ================================================


     Source Systems

     Code / Git / Docs / DB / Logs / Trace

------------------------------------------------------------------------

# 5. Software World Model 核心模型

## 5.1 Entity Model

系统所有知识围绕实体展开。

实体分类：

### Technical Entity

包括：

-   System
-   Service
-   Module
-   Class
-   Function
-   API
-   Database
-   Table
-   Event
-   Config

### Business Entity

包括：

-   Customer
-   Order
-   Payment
-   Inventory

### Evolution Entity

包括：

-   Requirement
-   Issue
-   PR
-   Commit
-   ADR

------------------------------------------------------------------------

## 5.2 Relation Model

技术关系：

-   CALLS
-   DEPENDS_ON
-   READS
-   WRITES
-   PUBLISHES
-   CONSUMES

业务关系：

-   IMPLEMENTS
-   BELONGS_TO
-   GOVERNS
-   APPLIES_TO

演化关系：

-   CAUSED_BY
-   CHANGED_BY
-   EVOLVED_FROM
-   IMPACTS

------------------------------------------------------------------------

# 6. Knowledge Compiler

Knowledge Compiler 负责将原始数据转换为 Software World Model。

主要模块：

    Knowledge Compiler

     ├── Source Connector
     ├── Entity Extractor
     ├── Relation Extractor
     ├── Entity Resolver
     ├── Inference Engine
     └── Knowledge Writer

------------------------------------------------------------------------

# 7. Source Connector 设计

目标：

屏蔽不同数据来源。

统一接口：

``` java
interface SourceConnector {

    collect();

    normalize();

    emitEvent();

}
```

支持：

-   Git
-   Code Repository
-   Database
-   Document
-   Log
-   Trace

------------------------------------------------------------------------

# 8. 五维软件世界模型

# 8.1 Structure Model

描述：

> 系统由什么组成。

输出：

-   服务地图
-   调用关系
-   API关系
-   数据依赖

来源：

-   CodeQL
-   Tree-sitter
-   SCIP

------------------------------------------------------------------------

# 8.2 Behavior Model

描述：

> 系统如何运行。

输出：

-   Workflow
-   State Machine
-   Event Flow

示例：

    Create Order

    ↓

    Payment

    ↓

    Inventory

    ↓

    Shipment

------------------------------------------------------------------------

# 8.3 Business Model

描述：

> 为什么这样运行。

包括：

-   Domain
-   Business Capability
-   Business Rule

示例：

    支付成功才能发货

    退款金额超过5000需要审核

------------------------------------------------------------------------

# 8.4 Runtime Model

描述：

> 生产环境真实状态。

来源：

-   Log
-   Trace
-   Metric

输出：

-   服务状态
-   调用链
-   故障信息

------------------------------------------------------------------------

# 8.5 History Model

描述：

> 为什么演化成现在这样。

模型：

    Requirement

    ↓

    Architecture Decision

    ↓

    Code Change

    ↓

    Deployment

    ↓

    Runtime Impact

------------------------------------------------------------------------

# 9. Environment Model

Environment 用于描述上下文：

包括：

-   Production
-   Staging
-   Testing
-   Development

用于区分：

同一个实体在不同环境中的实际状态。

------------------------------------------------------------------------

# 10. Validation 与 Governance

目标：

保证知识可信。

包括：

## Evidence

每条知识必须绑定：

-   来源
-   文件位置
-   生成方式

------------------------------------------------------------------------

## Confidence

示例：

  来源              可信度
  ----------------- --------
  AST               1.0
  Trace             0.95
  Static Analysis   0.9
  LLM推理           0.7

------------------------------------------------------------------------

## Conflict Detection

检测：

-   文档与代码冲突
-   配置与代码冲突
-   Runtime与模型冲突

------------------------------------------------------------------------

## Regression Evaluation

包括：

-   Golden Question
-   Hidden Test
-   自动生成测试问题

------------------------------------------------------------------------

# 11. Evolution Engine

负责知识持续演化。

输入：

``` json
{
eventType:"CODE_CHANGED",
entity:"PaymentService",
version:"abc123"
}
```

处理：

    Change Event

    ↓

    Impact Analysis

    ↓

    Fact Update

    ↓

    Behavior Recompute

    ↓

    Business Review

    ↓

    World Model Update

------------------------------------------------------------------------

# 12. Reasoning Platform

负责：

-   问题理解
-   查询规划
-   工具调用
-   推理生成

流程：

    Question

    ↓

    Intent Analysis

    ↓

    Context Planning

    ↓

    World Model Query

    ↓

    LLM Reasoning

    ↓

    Answer Validation

    ↓

    Response

------------------------------------------------------------------------

# 13. 数据存储设计

逻辑存储：

## Graph Store

保存：

-   Entity
-   Relation

------------------------------------------------------------------------

## Fact Store

保存：

-   原始事实

------------------------------------------------------------------------

## Vector Store

保存：

-   代码语义
-   文档语义

------------------------------------------------------------------------

## Event Store

保存：

-   演化事件

------------------------------------------------------------------------

## Time Series Store

保存：

-   Runtime数据

------------------------------------------------------------------------

# 14. 扩展设计

采用插件化。

支持：

## 新数据源

通过 Connector。

## 新语言

通过 Parser Plugin。

## 新业务领域

通过 Ontology Extension。

------------------------------------------------------------------------

# 15. 建设路线

## Phase 1

Structure Intelligence

目标：

理解代码结构。

------------------------------------------------------------------------

## Phase 2

Behavior Intelligence

目标：

理解业务流程。

------------------------------------------------------------------------

## Phase 3

Runtime Intelligence

目标：

生产问题分析。

------------------------------------------------------------------------

## Phase 4

Business Intelligence

目标：

业务规则理解。

------------------------------------------------------------------------

## Phase 5

Evolution Intelligence

目标：

持续演化。

------------------------------------------------------------------------

# 16. 总结

Software World Model 不是：

-   RAG系统
-   Chatbot
-   代码搜索工具

而是：

> 一个持续演化的软件数字孪生，为 AI 提供理解企业软件系统的认知基础。

核心能力：

-   事实可追溯
-   知识可验证
-   推理可解释
-   模型可重建
-   系统可演化
