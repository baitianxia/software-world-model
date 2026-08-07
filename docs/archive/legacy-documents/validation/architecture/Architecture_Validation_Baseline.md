# Software World Model 架构验证基线

**版本：V0.2**  
**状态：首轮五个纵向切片已完成；真实模型效果与扩展数据源另行验证**  
**对应架构：Software World Model 一般架构设计 V0.4**

## 1. 验证目的

本验证不以证明预设架构正确为目标，而是使用一个真实项目检验以下问题：

- Artifact、Evidence、Entity、Fact、Inference 和 Semantic View 的边界能否在真实代码中成立。
- Source Integration、Knowledge Engine 和 Semantic View Engine 的职责是否足够清晰，是否出现跨层补偿。
- 确定性程序与模型能力能否按照信息性质分工，而不是为了 AI Native 在所有步骤使用模型。
- 当前 Snapshot、知识准入和来源追溯能否形成可运行的最小闭环。
- 四种 Semantic View 是否能够复用统一知识底座，而不是各自构建知识。

验证中发现架构假设不成立时，应记录反例并修改架构；不能通过针对 `mall` 项目硬编码结论使验证通过。

## 2. 固定验证对象

| 项目 | 固定值 |
|---|---|
| 项目 | `macrozheng/mall` |
| 本地路径 | `validation-projects/mall` |
| KnowledgeScope | `system:mall` |
| Git Revision | `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` |
| 分支 | `master` |
| 首批语言与生态 | Java 17、Maven、Spring Boot 3.5、MyBatis |
| 输入边界 | 当前 Revision 下的源代码、POM、配置、测试、仓库文档和完整 Git 历史 |
| 排除范围 | 外部网站文档、前端独立仓库、数据库实例、Redis、RabbitMQ、Elasticsearch 和运行日志 |

验证基线固定后，不因输出结果不理想而更换 Revision 或输入边界。确需升级基线时必须记录原因，并将新旧结果分开比较。

## 3. 首批验证问题

### 3.1 Structure

| ID | 问题 | 预期知识性质 | 主要依据 |
|---|---|---|---|
| S-01 | 系统包含哪些 Maven 模块，模块之间有哪些本地依赖？ | Entity + Fact | 根 `pom.xml`、各模块 `pom.xml`、README 组织结构 |
| S-02 | `/order/generateOrder` 入口位于哪个模块，并由哪些 Controller、Service 和实现类承接？ | Entity + Fact | `OmsPortalOrderController`、`OmsPortalOrderService`、`OmsPortalOrderServiceImpl` |

### 3.2 Behavior

| ID | 问题 | 预期知识性质 | 主要依据 |
|---|---|---|---|
| B-01 | 创建订单时依次执行哪些校验、金额计算、库存处理、持久化和后续动作？ | Fact + Inference | `OmsPortalOrderServiceImpl.generateOrder` 及其调用方法 |
| B-02 | 未支付订单超时或被用户取消时，订单、库存、优惠券和积分如何处理？ | Fact + Inference | `cancelTimeOutOrder`、`cancelOrder` 及 DAO 映射 |

Behavior 输出必须区分代码明确规定的行为 Fact、跨方法归纳的 Behavior Inference，以及仅由注释或文档声明的预期行为。

### 3.3 Business

| ID | 问题 | 预期知识性质 | 主要依据 |
|---|---|---|---|
| BU-01 | 系统实现了哪些下单业务约束，分别由哪些技术行为落实？ | Business Inference + 底层 Fact | 收货地址、库存、优惠券、积分及订单状态相关代码 |
| BU-02 | `mall-admin`、`mall-portal`、`mall-search` 分别承载什么业务能力？ | Business Inference + 来源声明 Fact | README、模块结构、Controller 与 Service 集合 |

Business 结论不得仅根据包名生成；名称只能形成调查线索，正式 Inference 必须引用能够支持该含义的 Fact。

### 3.4 History

| ID | 问题 | 预期知识性质 | 主要依据 |
|---|---|---|---|
| H-01 | 项目何时升级到 Spring Boot 3.5，升级影响了哪些主要技术区域？ | 变化 Fact + 影响 Inference | Commit `0504e86` 及其 Diff |
| H-02 | 管理员删除逻辑为何调整缓存与数据库删除顺序，具体改变是什么？ | 变化 Fact + 原因边界 | Commit `dd6569c`、Commit Message 与单文件 Diff |

History 可以确认“提交声明了什么”和“代码改变了什么”；超出 Commit、Issue 或代码能够支持的作者动机必须保留为未知，不能由模型补写。

## 4. 验证顺序

1. **Slice 1 — Structure 主干**：本地 Git 与文件 Connector、Artifact、Evidence、Entity、Fact、Knowledge Verifier、当前 Snapshot、Structure View 和 CLI。
2. **Slice 2 — Behavior**：在不改变 Slice 1 知识对象的前提下增加 Java 方法和调用事实，并验证跨方法 Behavior Inference。
3. **Slice 3 — Business**：引入模型辅助提议和独立验证，检验业务身份与业务含义不能伪装成 Fact。
4. **Slice 4 — History**：增加 Commit Artifact 和 Diff Evidence，验证软件历史与平台 Snapshot 历史的分离。
5. **Slice 5 — Conversational Use**：增加 Agent Orchestrator、Task Execution Agent、Answer Candidate 和 Answer Review Agent。

只有前一切片暴露的架构问题得到结论后才进入下一切片，避免同时引入多个变量。

## 5. Slice 1 验收标准

### 5.1 预期结果

- 识别根聚合项目和 7 个本地 Maven 模块，共 8 个稳定 Entity。
- 形成 7 个 `CONTAINS_MODULE` Fact。
- 形成 8 个本地 `DEPENDS_ON` Fact。
- 根 POM 与 README 对同一模块的观察形成不同 Evidence，并归并到同一个 Fact。
- 每条 Evidence 只引用一个 Artifact，并包含文件、Revision、行定位和内容哈希。
- 每个 Fact 至少具有一条通过复核的 Evidence，查询结果能够反向解释到具体文件行。
- Structure View 返回 7 个模块和 8 条本地依赖，不产生新的正式知识。
- Snapshot 只在全部待发布 Fact 通过一致性校验后成为当前 Snapshot。
- 在相同 Revision 上重复构建时，Entity ID 和 Fact ID 保持稳定。

### 5.2 明确不验证

- 不使用模型解析 POM；XML 结构明确，确定性解析足够可靠。
- 不在 Slice 1 生成 Behavior、Business 或 History 结论。
- 不运行 `mall` 业务系统及其外部基础设施。
- 不实现 Web Chat、Scheduler、Agent、模型路由或企业级非功能能力。

## 6. 首批待证伪假设

| 假设 | Slice 1 观察方式 |
|---|---|
| 文件可以作为代码与配置类 Source Artifact 的初始粒度 | 比较来源定位精度、重复构建稳定性和变更影响范围 |
| Artifact 不需要统一内容结构 | 同时处理 XML POM 与 Markdown README，仅统一身份、来源和内容引用 |
| 多个 Evidence 可以归并为一个 Fact | 使用根 POM 与 README 对 7 个模块的重复观察 |
| Entity 身份可以与版本状态分离 | 在同一 Scope 中使用模块坐标形成稳定身份，以 Revision 限定 Fact |
| Semantic View 可以只组织正式知识 | Structure View 只读取 Entity 和 Fact，不读取源文件 |
| 模型不应参与确定性来源解析 | 比较无模型情况下的完整性、可追溯性与可重复性 |
| 当前 Snapshot 发布可以隔离半成品 | 在验证失败场景中确认旧 Snapshot 仍可查询 |

## 7. 结果记录规则

每个 Slice 完成后记录：

- 实际输入、运行命令和固定 Revision。
- 生成的 Artifact、Evidence、Entity、Fact 和 Inference 数量。
- 验收标准通过或失败的可回放依据。
- 暴露的是实现缺陷、详细设计缺陷还是一般架构缺陷。
- 是否需要修改架构文档，以及修改前后的理由。

## 8. 首轮完成判定

截至 2026-08-01，Slice 1–5、真实二次 Knowledge Update、Scheduler 复用以及 Connector/Semantic View 扩展接缝已经完成可回放验证。详细结果见 [Architecture_Validation_Log.md](Architecture_Validation_Log.md)。

“首轮完成”表示一般架构主干、职责边界、静态依赖、知识对象形成关系和关键门禁已在固定真实项目上形成运行证据，不表示：

- Demo 已具备生产质量或可以直接作为 MVP 实现。
- 真实大模型准确率、跨项目泛化和审核误拒绝率已经达标。
- DB、Log、Trace、部署平台、跨 Scope 和企业非功能需求已经验证。

这些事项继续保留在一般架构第 14 节的后续验证清单中，不通过扩大本基线的固定问题集来伪装为已完成。
