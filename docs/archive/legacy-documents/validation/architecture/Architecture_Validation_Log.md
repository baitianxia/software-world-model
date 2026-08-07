# Software World Model 架构验证记录

本文件记录真实项目验证结果、反例和架构影响。既有纵向机制验证输入见 [Architecture_Validation_Baseline.md](Architecture_Validation_Baseline.md)；正式知识单路径的方案能力门禁见 [Architecture_Capability_Validation_Baseline.md](Architecture_Capability_Validation_Baseline.md)。

> 第 1～28 节是 V0.7 形成时的历史验证记录，各 Slice 保留其发生时的实验条件和阶段性结论；其中的“当前”“最终”只指该次运行时点。第 29 节起登记正式知识单路径能力验证及后续修订状态，作为本文件的现行验证状态；较新的纠偏结论不回写或抹除历史失败记录。

## Slice 1：Structure 知识主干

**日期：2026-08-01**  
**状态：通过**  
**验证项目：`macrozheng/mall`**  
**Revision：`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`**

### 1. 实现范围

本切片实现了：

- CLI Adapter。
- Management、Knowledge Update 和 Knowledge Use Application Services。
- Local Git Connector 与文件 Source Artifact。
- POM 和 README 的确定性结构提取。
- Evidence、Maven Project/Module Entity、Fact Candidate 和 Fact。
- 独立 Knowledge Verifier。
- 当前 Snapshot 构建、准入失败隔离和整体发布。
- 只读取正式知识的 Structure View Engine。
- SQLite 物理存储及模块级逻辑所有权边界。

本切片未调用模型，也未生成 Inference。

### 2. 实际结果

| 指标 | 结果 | 预期 | 结论 |
|---|---:|---:|---|
| Source Artifact | 9 | 9 | 通过 |
| Entity | 8 | 8 | 通过 |
| Evidence | 22 | 22 | 通过 |
| Fact | 15 | 15 | 通过 |
| 本地 Maven 模块 | 7 | 7 | 通过 |
| 本地模块依赖 | 8 | 8 | 通过 |

识别出的模块：

- `mall-admin`
- `mall-common`
- `mall-demo`
- `mall-mbg`
- `mall-portal`
- `mall-search`
- `mall-security`

识别出的本地依赖：

```text
mall-admin    → mall-mbg
mall-admin    → mall-security
mall-demo     → mall-mbg
mall-mbg      → mall-common
mall-portal   → mall-mbg
mall-portal   → mall-security
mall-search   → mall-mbg
mall-security → mall-common
```

### 3. Evidence 追溯样例

正式 Fact：

```text
mall-admin DEPENDS_ON mall-security
```

追溯结果：

| 项目 | 内容 |
|---|---|
| Fact ID | `fact:a1864900d3a72cdbb3898987` |
| Artifact | `mall-admin/pom.xml` |
| Git Revision | `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` |
| Locator | 第 26 行 |
| Evidence | `<artifactId>mall-security</artifactId>` |
| Artifact Content Hash | `33da6414f2f0358bbb9387ba8f8ad55df7147b44b298bfd6d85d1ae4f6a7bbad` |

每个 `CONTAINS_MODULE` Fact 同时关联两条 Evidence：一条来自根 `pom.xml`，一条来自 `README.md`。两条 Evidence 分别引用各自 Artifact，没有把多个 Artifact 合并成一条 Evidence。

### 4. 自动验证

执行命令：

```bash
PYTHONPATH=demo python3 -m unittest discover -s demo/tests -v
```

通过 5 个自动验证测试：

1. 实际知识数量与固定基线一致。
2. Fact 能够回溯到精确 Artifact、Revision、行号、原文和哈希。
3. 同一 Revision 重复构建时 Entity ID 和 Fact ID 稳定，Snapshot ID 独立。
4. 强制 Knowledge Verifier 拒绝新构建时，旧的当前 Snapshot 仍可查询。
5. Semantic View、Knowledge Engine、Source Integration 和 Application Services 的静态 import 关系不越界。

### 5. Demo 初版实现偏离架构的情况

以下三项均属于 **Demo 实现违规或详细设计边界未明确**，不是一般架构缺陷。它们恰好说明：除业务输出外，还需要把既定模块边界转化为可执行的实现审查规则。

#### 5.1 Demo 中 Semantic View 曾绕过 Knowledge Engine

第一版验证代码中，Structure View Engine 直接读取 SQLite。功能测试能够通过，但违反：

```text
Semantic View Engine → Knowledge Engine → 权威知识存储
```

修正后 Semantic View Engine 只通过 Knowledge Engine 的只读能力获取正式知识，不依赖物理存储。

该实现违规说明：仅检查输出正确不足以验证架构，必须同时验证静态依赖方向；它不要求调整一般架构。

#### 5.2 Demo 中 Application Services 曾直接实例化具体 Connector

第一版 Application Services 直接创建 `LocalGitConnector`，使应用层与具体数据源实现绑定。修正后调用路径为：

```text
Application Services → Source Integration → Local Git Connector
```

Source Integration 负责 Source Binding、Connector 选择和 Artifact 持久化边界；Application Services 只协调用例。

#### 5.3 Demo 中 Artifact 类型曾造成隐式编译期依赖

Knowledge Engine 第一版从 Source Integration 实现模块导入 `SourceArtifact`。虽然没有调用 Connector，但仍形成：

```text
Knowledge Engine → Source Integration 实现
```

修正后 Artifact 作为中立边界契约存在：Source Integration 生产，Application Services 传递，Knowledge Engine 消费。两个核心模块都只依赖契约，不依赖对方实现。自动测试会阻止该依赖重新出现。一般架构的依赖方向保持不变，但详细设计需要明确中立契约的归属。

### 6. 对一般架构的验证结论

| 架构判断 | 结果 | 依据 |
|---|---|---|
| Source Integration 以 Artifact 为边界 | 支持 | Connector 无需理解 Evidence 和 Fact |
| Evidence 与 Fact 分离 | 支持 | 两个 Artifact 的观察归并为一个 Fact |
| 一条 Evidence 只引用一个 Artifact | 支持 | POM 与 README 分别生成 Evidence |
| 一个事实由多条 Evidence 增强 | 支持 | 7 个模块包含关系均关联两条 Evidence |
| Entity 与 Fact 身份可跨 Snapshot 稳定 | 支持 | 相同 Revision 重建的身份集合完全一致 |
| Semantic View 不创造正式知识 | 支持 | View 输出的每条关系均引用已有 Fact ID |
| 当前 Snapshot 可以隔离失败构建 | 支持 | 准入失败后旧 Snapshot 保持 CURRENT |
| 确定性来源解析不需要模型 | 支持 | XML 与明确 Markdown 结构可重复解析 |
| 模块化单体可以保持逻辑所有权 | 支持 | SQLite 共用但写入能力按模块封装 |

Slice 1 没有证伪一般架构主干，因此该切片完成时不需要修改 V0.3 顶层结构；跨 Slice 的边界澄清统一记录在后续 V0.4 优化中。

### 7. 仍需保留的限制

1. POM 与 README 同属一个 Git 仓库，两条 Evidence 增加可复核性，但不构成两个独立来源，不能因 Evidence 数量为 2 就提高事实置信度。
2. 当前只验证一致 Evidence 的归并；Evidence 冲突、片面支持和 Candidate 局部拒绝仍需后续切片验证。
3. Demo 为便于回放保存了完整 POM 和 README 内容，不代表生产 Artifact 必须永久保存完整 Payload。
4. 当前构建目标由 `collect_structure_sources` 隐式表达；详细设计需要形成稳定的构建目标或提取契约，避免 Source Integration 与 Knowledge Engine 依靠方法名约定。
5. 当前只验证模块级技术 Entity，尚未验证 Java 类型身份、重命名、Business Entity 和推断型身份。
6. 强制审核失败验证了 Snapshot 隔离，但尚未验证排除单个非必需 Candidate 后继续发布其余正式知识。

## Slice 2：Java Structure 与 Behavior

**日期：2026-08-01**  
**状态：架构闭环通过**

### 8. Java Artifact Processing

全量验证输入包含 524 个 Java Source Artifact。Source Integration 使用 Tree-sitter 生成 524 个 `java-ast-summary` Derived Artifact，每个 Derived Artifact 只记录通用语法结构和来源位置，并通过 Artifact Lineage 指向唯一 Java Source Artifact。

Knowledge Engine 不依赖 Tree-sitter，也不读取工程文件；它消费 Source Artifact 与 Derived Artifact，并将 Evidence 定位回原始 Java 文件。该结果支持以下判断：

- Java 文件可以继续作为首批 Source Artifact 粒度。
- AST 是可重建的 Derived Artifact，不应伪装成 Fact 或独立权威来源。
- 解析器属于 Source Integration 的 Artifact Processing；Entity、Fact 和 Inference 判断仍属于 Knowledge Engine。
- Java 语法已有确定性解析器时不需要模型解析；模型可以处理更高层语义问题。

固定问题通过显式 `KnowledgeBuildTarget` 传入，`mall` 的方法名、Commit ID 和问题标签只存在于独立验证配置中；通用 Knowledge Builder 不包含 `mall`、类名或预设答案。这样既保持可回放的固定基线，也避免为了通过验证把特例固化进核心算法。

### 9. Structure S-02 结果

`POST /order/generateOrder` 被组织为以下正式知识链：

```text
mall-portal
  → OmsPortalOrderController
  → OmsPortalOrderController#generateOrder(OrderParam)
  → OmsPortalOrderService#generateOrder(OrderParam)
  → OmsPortalOrderServiceImpl#generateOrder(OrderParam)
```

链路使用 `CONTAINS_TYPE`、`DECLARES_METHOD`、`EXPOSES_ENDPOINT`、`CALLS`、`IMPLEMENTS_TYPE` 和 `IMPLEMENTS_METHOD` Fact 表达；每个 Fact 均能回溯到 Controller、接口或实现类的具体代码行。

技术 Entity 使用“完整限定类型名”或“完整限定类型名 + 方法签名”作为来源锚定身份。同名 Java 类型位于不同包时保持独立，没有依靠简单类名强制合并。

### 10. Behavior 结果

形成 3 个正式 `BEHAVIOR_FLOW` Inference：

- B-01 创建订单。
- B-02 超时取消订单。
- B-02 用户取消订单。

B-01 能按来源顺序组织地址校验、库存校验、金额与优惠处理、库存锁定、订单持久化、优惠券与积分更新、购物车删除及延迟取消消息。B-02 能区分超时批量取消和用户单笔取消，并组织订单状态、库存锁定、优惠券和积分处理。

每个 Behavior Inference 同时引用：

- 代码调用与失败条件 Fact，用于反映实际实现。
- 内联注释声明 Fact，用于辅助步骤命名和排序。

因此注释没有被单独当成实际行为证明，最终输出明确标记为“综合实际调用、失败条件与内联注释归纳”的 Inference。

### 11. Slice 2 实现中发现的问题

以下均为 Demo 实现问题，不是一般架构缺陷：

1. 第一版 Structure View 把 Controller 的所有 `CALLS` 都当成 Service 调用，错误包含了 `CommonResult.success`。修正后只有能够由 `IMPLEMENTS_METHOD` 关系承接的调用才进入 Service 链。
2. 第一版 Behavior View 按稳定 Fact ID 组织步骤，导致步骤乱序。稳定 ID 只能表达身份，不能表达时间或执行顺序；修正后使用来源位置和显式 `PRECEDES` Fact。
3. History Evidence 的 revision 曾被错误要求等于当前 Snapshot revision。修正后 Evidence 的版本必须等于其 Artifact 版本；Fact 所在 Snapshot Context 与各来源自身版本分别保留，不能强制相等。

第 3 项没有推翻 V0.3，因为其第 10.2 节已经要求不同 Data Source 独立保留版本；V0.4 将该反例进一步固化为“来源上下文不能被 Snapshot 发布上下文覆盖”的明确不变量。

## Slice 3：Business

**状态：知识边界通过；真实模型效果待专项评测**

### 12. 实际结果

形成：

- 7 个 `HAS_DECLARED_CAPABILITY` Fact，忠实记录 README 对各模块的能力描述。
- 7 个 `BUSINESS_CAPABILITY` Inference，将来源声明组织为模块业务能力。
- 4 个 `HAS_FAILURE_GUARD` Fact，记录下单代码中的地址、库存、优惠券和积分失败条件。
- 4 个 `BUSINESS_CONSTRAINT` Inference，将技术失败条件解释为业务约束。

BU-02 中 `mall-admin`、`mall-portal` 和 `mall-search` 的能力不是根据包名猜测，而是引用 README 来源声明 Fact。BU-01 的约束不是直接写入 Fact，而是引用实际 `if` 条件与 `Asserts.fail` Evidence 的 Business Inference。

独立 Inference Semantic Reviewer 会检查：结论是否包含被引用的约束或能力声明、Behavior 是否同时具备调用支持、History 是否包含提交时间和声明。审核失败的单个非必需 Candidate 可以被排除；只有缺失构建目标要求的最小 Inference 类型时才阻止 Snapshot 发布。

当前候选生产器和语义审核器为可回放的确定性实现。它验证了 Fact/Inference、准入门禁和追溯边界，但没有证明真实大模型在陌生项目上的生成准确率、误拒绝率或泛化能力。

## Slice 4：History

**状态：通过**

### 13. 实际结果

接入两个 Git Commit Artifact：

- `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`：升级支持 Spring Boot 3.5。
- `dd6569c3558f79af5b21aad601349e0f029b9a6d`：后台删除用户时先删除缓存中的用户信息。

Commit、提交时间、提交声明、Changed File、Diff Hunk、行替换和可确认的顺序变化分别形成 Entity 与 Fact。History View 形成 2 个 `HISTORY_IMPACT` Inference：

- H-01 确认提交时间为 `Thu May 14 16:30:28 2026 +0800`，并根据实际 Changed File 归纳影响构建与依赖、配置、接口层、服务实现和文档。
- H-02 确认 `getCacheService().delAdmin(id)` 被移动到 `adminMapper.deleteByPrimaryKey(id)` 之前。

H-02 只能把 Commit Message 当作作者公开声明，把 Diff 当作实际变化依据；输出明确保留“提交信息之外的作者动机未知”。

该切片同时验证了：History Semantic View 描述软件世界的变化，平台旧 Snapshot 描述过去发布的知识状态，二者身份和用途不同。

## Slice 5：Conversational Knowledge Use

**状态：架构闭环通过；真实模型质量待专项评测**

### 14. 实现与结果

实现并验证：

- Web Chat Adapter 只调用 Agent Orchestrator。
- Agent Orchestrator 通过 Model Gateway 理解请求并形成完整 Agent Task，不调用 Application Services。
- Task Execution Agent 先通过模型形成不可变 Knowledge Requirement，再在固定 Snapshot 上通过 Application Services 执行通用正式知识 Tool Loop；固定 Semantic View 不再是其知识发现主路径。
- 通用 Tool Loop 由模型选择 `SEARCH`、`NEIGHBORHOOD`、`EXPLAIN` 或 `STOP`，Application Services 负责执行，Scope 与 Snapshot Token 由 Agent 注入而不是由模型指定。
- 独立 `ASSESSMENT` 模型调用逐项形成 Knowledge Sufficiency Assessment；发现 Knowledge Gap 时显式触发 Knowledge Update，再在新 Snapshot 和新 `KNOWLEDGE_USE` 上下文中从空调查轨迹重新执行同一 Requirement。
- Answer Candidate 绑定原始请求、Agent Task、KnowledgeScope、Snapshot、revision、结构化 Claim 与知识引用。
- Answer Review Agent 独立重新读取同一 Snapshot 的正式知识并调用 Model Gateway 审核。
- 未经审核或审核失败的 Answer Candidate 不成为 Web Chat Final Response。
- CLI 和 Scheduler 绕过 Agent，复用同一个固定 Application Use Case。

当前无 Knowledge Gap 的“创建订单流程”正常路径产生 7 条可追溯 Model Call，分布在 6 个隔离 Phase 中：

1. `ROUTING / route-task`：理解请求并选择具体 Agent。
2. `REQUIREMENT / form-knowledge-requirement`：形成不可变 Knowledge Requirement。
3. `KNOWLEDGE_USE / plan-formal-knowledge-step`：选择 `SEARCH`。
4. `KNOWLEDGE_USE / plan-formal-knowledge-step`：读取上一步结果后选择 `STOP`。
5. `ASSESSMENT / assess-knowledge-sufficiency`：独立判断每个 Need 是否由已发现的正式知识满足。
6. `ANSWER / draft-answer`：只基于已验证正式命题组织 Answer Candidate。
7. `REVIEW / review-answer`：独立审核并决定是否发布 Final Response。

其中 Search、Neighborhood 和 Explain 是 Application Service 工具调用，不是模型调用；模型只规划下一步，平台机械执行并校验上下文。以下反例均被拒绝：

- 在具有合法知识引用的 Candidate 中插入“系统保证所有订单永远库存充足”的无依据 Claim。
- 使用已经不是当前状态的 Snapshot 审核答案。
- Answer 文本与结构化 Claim 不一致。

验证使用确定性 Model Provider test double，以保证自动回放。它验证 Model Gateway、Agent 依赖、动态调用和审核门禁，不代表真实模型语义能力已经达标。

## 跨 Slice 验证

### 15. 全量构建结果

固定 Revision 的一次 `full-validation` 构建结果：

| 指标 | 结果 |
|---|---:|
| Source Artifact | 662 |
| Derived Artifact | 524 |
| Artifact 合计 | 1,186 |
| Entity | 20,362 |
| Evidence | 32,160 |
| Fact | 32,832 |
| Inference | 16 |
| 当前 Demo SQLite 大小 | 51 MB |
| 全量构建耗时 | 约 8–10 秒 |

Artifact 输入包括 524 个 Java 文件、106 个普通 XML、12 个 YAML、9 个 Markdown、8 个 Maven POM、1 个 properties 文件和 2 个 Commit Artifact。Demo 为回放保存完整 Payload，并且对所有 Java 类型、方法和调用进行急切物化。该结果观察到了输入到知识与存储的放大，也为比较构建和 Payload 策略提供了基线；但 8–10 秒和 51 MB 在内部 MVP 中仍可能完全可接受，不能据此证明全量构建不适合作为默认方式，也不能证明增量处理已经成为必需能力。

### 16. 真实二次 Knowledge Update

为避免修改固定验证仓库，实验从原仓库创建临时本地 Git 克隆，只把 Controller 路由从 `/generateOrder` 改为 `/generateOrderV2` 并提交，然后对同一 KnowledgeScope 执行第二次全量更新。

| 观察项 | 结果 |
|---|---|
| 旧端点更新前 | `READY` |
| 新端点更新前 | `KNOWLEDGE_GAP` |
| 旧端点更新后 | `KNOWLEDGE_GAP` |
| 新端点更新后 | `READY` |
| Controller Method Entity ID | 保持稳定 |
| 稳定 Entity | 20,361 / 20,362 |
| 稳定 Fact | 32,831 / 32,832 |
| 旧 Snapshot | `SUPERSEDED` |
| 新 Snapshot | `CURRENT` |

变化只替换端点 Entity 及其 `EXPOSES_ENDPOINT` Fact；方法身份和其余正式知识保持稳定。该结果与 Slice 1 的失败更新隔离共同验证了 Snapshot 的整体切换语义。

### 17. 扩展接缝

- Connector Provider SPI 与 Connector Tool SPI 已通过自定义 Provider/Tool 测试验证：Provider 负责配置、能力和 Tool 创建，Tool 负责有界信息操作。
- Semantic View Registry 可以注册 `Quality` 示例视图；注册和查询没有新增 Fact，证明视图扩展不需要新知识底座。
- Model Gateway 可以替换 Provider，并持久化 provider、model、version、capability、请求哈希和响应。
- Scheduler Adapter 只把时间触发转换为现有 Knowledge Update 用例。
- 未实现独立 Projection、Evolution 或 Initialization 模块，符合当前架构的按需引入原则。

## Slice 6：V0.6 纠偏——通用知识调查与任务驱动更新

**日期：2026-08-02**  
**状态：机制闭环通过；新的产品能力留出门禁待执行**

### 18. 纠偏来源与验证目标

首轮产品价值留出实验保留在 [Product_Value_Holdout_Run_001.md](../product-value/Product_Value_Holdout_Run_001.md) 中：同等级模型直接调查 Git 工程得到 `50 / 50`，只使用 Software World Model 正式知识工具的隔离模型得到 `33.75 / 50`，即 `67.5%`。Software World Model 组没有出现直接组未犯的核心事实错误，但任务完成度与关键细节覆盖不足，P0 非回归门禁未通过。

该实验验证的是“真实模型手动组合公开正式知识 CLI”，不是内置 Web Chat Agent。它同时暴露了两个不同问题：

1. 固定 Semantic View 会遮蔽已经存在的正式知识，不能作为开放式任务的能力上限。
2. 当前正式知识没有表达目标 Commit 或复杂 Behavior / Business 命题时，仅增加读取工具不能弥补知识覆盖缺口。

本轮纠偏没有增加题目专用 View、Extractor 或答案阶段直接来源兜底，而是验证以下纵向机制：

```text
Knowledge Requirement
  → 固定 Snapshot 的通用正式知识 Tool Loop
  → 独立 Knowledge Sufficiency Assessment
  → Gap 派生 Build Intent
  → 隔离的来源 Investigation 与 Candidate Bundle
  → Knowledge Verifier 与原子 Snapshot 发布
  → 新固定 Context 下重跑同一 Requirement
  → Answer Candidate 与独立 Answer Review
```

### 19. 通用正式知识 Tool Loop

Application Services 已提供并由内置 Task Execution Agent 实际编排四类能力：

- `FormalKnowledge.OpenContext`：固定当前 KnowledgeScope、Snapshot、revision、Schema、关系语义与覆盖声明。
- `FormalKnowledge.Search`：搜索正式 Entity 或 Inference，并支持有界分页。
- `FormalKnowledge.Neighborhood`：从 Entity 读取一跳正式 Fact 邻域。
- `FormalKnowledge.ExplainBatch`：批量读取 Fact proposition 或 Inference statement、依赖与来源定位；答案读取面不暴露 Evidence quote 或 Artifact Payload。

本轮专项验证证明：

| 机制 | 验证结果 |
|---|---|
| 固定 View 与通用工具解耦 | 在 Structure、Endpoint 和 Semantic View 调用全部被设置为失败的情况下，Agent 仍通过 `SEARCH → NEIGHBORHOOD → EXPLAIN → STOP` 完成回答 |
| Context 由平台控制 | 所有工具调用使用 Agent 注入的同一 Scope 与 Snapshot Token；模型动作中伪造 Scope 或 Token 会在执行前因未知字段被拒绝 |
| Typed 正式知识 | Agent 从工具结果本身识别 `FACT` 与 `INFERENCE`；同一任务可以组合两种引用，不再根据 `use_case` 猜测引用类型 |
| 独立充分性判断 | Knowledge Use 调查结束后才在独立 `ASSESSMENT` Context 中逐 Need 判断；Assessment 不能引用本轮工具未发现的正式知识 |
| 空结果语义 | 空 Search 只产生 Gap，不形成“不存在”或其他否定 Claim |
| 有界执行 | Tool Loop 最多执行 12 步；完全相同的动作再次出现时，在第二次工具执行前终止 |
| 更新后重新调查 | 新 Snapshot 发布后关闭旧 Context，使用新的 `KNOWLEDGE_USE` Context 和空 Tool Trace 重跑未改变的 Requirement |

12 步是当前 Demo 的回放边界，不是已经冻结的生产预算。工具的 limit、cursor、方向、类型和谓词参数均由平台严格解析；模型负责选择操作，不能绕过 Application Services 直接读取 Knowledge Engine、存储或来源。

### 20. 模型主导、任务驱动的 Knowledge Update

任意 Commit 纠偏场景使用首轮 Snapshot 中不存在的 Commit `dacce5f28dfc1734f2db09668d928d7fac2a3a7a`：

1. Task Execution Agent 从原始问题形成只要求该 Commit 影响的 Knowledge Requirement。
2. S0 的通用 Inference Search 没有找到目标 Commit，只形成 Gap，没有生成否定答案。
3. 模型从 Gap 派生 Build Intent，指定来源边界、目标 Revision、目标 Commit 和最低 Need 集合。
4. Local Git Connector 在不切换工作树的情况下解析任意 Revision，并能读取 Commit、父 Revision、指定 Revision 文件和显式 Revision Diff；脏工作树不会改变不可变对象读取结果。
5. 隔离 Investigation 收集 Source Artifact 并调用模型 Candidate 提议能力；本 H-04 回放中的模型响应没有提出语义 Candidate，History Candidate 仍由既有确定性 Builder 生成。另一个独立的简单 Fact 场景验证了模型提议的严格反序列化：平台从冻结输入重建 Scope、revision、稳定 ID、Evidence quote/hash 和 Model Call provenance，模型不能伪造这些平台字段。
6. Knowledge Verifier 准入后以旧 Snapshot 为 base 执行 Snapshot enrichment，保留未受本次目标调查影响的 Artifact、Entity、Evidence、Fact 和 Inference，并原子发布 S1。
7. Candidate 提议结束后测试会物理关闭 Source Integration。S1 仍能通过通用正式知识 Search/Explain 回答同一 Commit 问题，证明答案不是从 Investigation 对话或 Artifact 内容直接复述而来。
8. S0 与 S1 分别使用独立 `KNOWLEDGE_USE` Context，两轮模型调用看到的 Tool Trace 长度均从 0 开始；旧 Snapshot Token 在 S1 发布后被明确拒绝为 `STALE_CONTEXT`。

该场景还验证了目标限定更新不会因为只收集根 POM 和目标 Commit 而丢失原有 Behavior、Business 与其他正式知识；旧 Fact 的 Evidence 引用在新 Snapshot 中仍可解释。该结论目前只适用于来源 Context 没有发生不兼容变化的 enrichment 场景，不等于已经解决任意源码变更下的知识失效传播。

### 21. 命题准入与失败隔离

本轮把“Evidence 不能扩大正式命题语义范围”转化为可执行门禁：

- 一个 Evidence 仍只引用一个 Artifact；多个 Artifact 必须形成多条 Evidence。
- 模型提出的直接 Fact 必须显式携带 proposition 和 Model Call provenance。
- Candidate Bundle 中每个 Fact / Inference Candidate 的 `model_call_id` 必须与该 Bundle 的 `proposal_model_call_id` 一致，不能通过漏填 provenance 绕过模型候选审核。
- 默认保守 Fact Semantic Reviewer 只允许 proposition 字面存在于其引用的至少一条 Evidence；需要抽象、概括或跨观察组合的结论必须进入 Inference Candidate 与相应审核路径。
- Explain 工具向 Answer 阶段提供正式 proposition / statement 与来源定位，但不提供 Evidence quote 或 Artifact content；答案 Claim 不能借 Evidence 原文补全正式命题没有表达的参数、公式或条件。

以下失败边界已自动验证：

| 失败输入或竞争状态 | 系统行为 |
|---|---|
| Fact proposition 超出 Evidence 字面内容 | Candidate 被拒绝，候选 Snapshot 为 `FAILED`，旧 CURRENT Snapshot 与正式知识保持不变 |
| Fact proposition 字面存在于 Evidence | 可以进入既有 Knowledge Verifier 和原子发布路径，并保留 Model Call provenance |
| Evidence locator 超出所收集 Artifact | 在构造正式 Evidence 前拒绝，不发布候选 Snapshot |
| ArtifactRequest revision 与 Build Intent target revision 不同 | 在来源调查边界拒绝 |
| Assessment 引用当前 Snapshot 中不存在或本轮 Tool Loop 未发现的正式知识 | 标记为无效 Assessment，不能进入答案生成 |
| 旧 Snapshot Token 在新发布后继续查询 | 返回 `STALE_CONTEXT` |
| 基于旧 Snapshot 启动的 enrichment 遭遇并发替换 | 旧 base 不能覆盖新的 CURRENT Snapshot |
| 模型重复工具动作或超过步数 | 受控终止，不调用 Answer Draft，不把空结果解释为事实 |
| Answer Context 包含 Artifact、Candidate、Evidence quote 或 Investigation 字段 | Model Gateway 在调用 Provider 前拒绝 |
| Answer Candidate 篡改 Claim、遗漏 Need、引用越界或绑定旧 Snapshot | Answer Review 拒绝，不形成 Final Response |

### 22. 本轮仍未证明的事项

1. `DeterministicValidationProvider` 只是可回放控制流替身。它对创建订单、业务约束和 Commit 使用固定查询词，不能被当作真实模型已经具备开放式调查规划、反例搜索或查询改写能力的证据。
2. 本轮在真实 Git 仓库上的可回放纵向更新验证了任意 Commit History 知识，以及脚本化 Provider 提出单一直接 Fact 的反序列化与准入；复杂 Behavior / Business 的任意命题、跨文件 Inference Candidate 和冲突 Candidate 仍主要依赖确定性 Builder，尚未证明真实模型可以可靠提出并通过准入。
3. 首轮产品留出实验仍然是失败记录。本轮只修复了已识别的机制断点，必须冻结新的未见任务集，以同模型、同来源和同工具权限重新与直接仓库 Agent 对比；在此之前不能宣称 Software World Model 已达到产品能力下限。
4. Snapshot enrichment 当前证明的是同一来源 Context 下的知识保留。源码 Revision、环境或数据源发生变化时，哪些旧知识可以继承、哪些必须失效或重新验证，仍需详细设计和反例测试。
5. Build Intent 的 Need 集合、Candidate Bundle 的 covered/unresolved 分区以及发布后的全量重评已经可验证；“最低发布结果是否在准入时语义满足每个 Need”仍主要由发布后 Assessment 兜底，尚未形成通用的 Knowledge Engine 语义门禁。
6. Tool Loop 当前只有精确或包含字符串 Search、一跳 Neighborhood 和批量 Explain。语义检索、并行工具调用、预算自适应与持久化 Investigation Trace 是否必要，要由真实模型验证决定，不能提前增加新顶层模块。
7. DB、Log、Trace、部署平台、多 KnowledgeScope 和跨来源冲突尚未进入本轮纠偏；Git 场景通过不能外推为所有 Connector 都已验证。

## Slice 7：真实模型纵向诊断（非产品门禁）

**日期：2026-08-02**  
**状态：单一 Behavior 路径通过；H-04 复杂 Candidate 尚未闭环；因 no-tools 边界未成立而暂停真实重跑**

### 23. 诊断时间线

本 Slice 在独立临时数据库和阶段隔离模型上下文中使用真实 Codex CLI Model Provider 检查内置 Agent，而不是继续以确定性 Provider 代替模型语义。这里的“独立/阶段隔离”不是执行安全隔离；Codex Agent 的工具能力并未被机械禁用。它没有重跑冻结的五题对照实验，也不改变任何产品分数。

在进入下表业务诊断前，真实 Provider smoke test 先暴露并修正了五项通用契约问题：

- Codex Structured Output 不接受 `uniqueItems` 等完整平台约束，因此确立 Provider 可移植形状 Schema 与能力所属模块完整契约校验的分层；不能把前者当作知识准入。当前 Demo 已对 Formal Tool、Build Intent 和 Candidate 等关键路径执行严格 owner 解析，尚未证明全部模型 Capability 都覆盖了完整二次校验。
- `action` 与 `arguments` 若在 Provider Schema 中解耦，模型会产生跨动作参数组合；Formal Tool Step 因而使用 action-specific union，平台仍执行最终解析。
- 旧 Snapshot 缺少当前 Fact proposition，却曾被当作当前知识读取；Snapshot 现显式记录 Knowledge Schema，旧版本读取和跨 Schema enrichment 均拒绝。
- Behavior 首次 Requirement 把模块、逐步输入输出和全部补偿路径扩张成用户未要求的强制条件；Requirement 契约随后加入“必要且相称、不扩张原问题”的约束，重跑后该单例完成。
- 一次过宽 ArtifactRequest 曾把 Candidate 模型输入扩大到约 `2.9M` 字符，超过 Provider 的 `1,048,576` 字符预算。Provider 预检可以受控拒绝，但不能解决调查策略本身；该反例直接支持有界、渐进 Source Investigation，而不是静默截断或默认一次性装入全部 Artifact。

| 顺序 | 诊断 | 实际结果 | 可成立的结论 |
|---:|---|---|---|
| 1 | Behavior 单例 | 完成 8 次 Model Call，总耗时 `83.093s`；Final Response 为 `ANSWERED`，Answer Review 为 `PASS` | 真实模型能够在一个已有正式知识足够的 Behavior 单例中走通 Requirement、Knowledge Use、Assessment、Answer 与 Review。单例成功不证明 Behavior 泛化能力或产品门禁通过。 |
| 2 | H-04，错误 Commit SHA 参数 | 运行使用了错误诊断参数，所得结果不对应冻结题目的目标 Commit | 该次运行只能记录为参数错误，不能用于支持或否定架构、模型能力或 H-04 结论。 |
| 3 | H-04，正确 Commit `dacce5f28dfc1734f2db09668d928d7fac2a3a7a` | 真实模型到达复杂 Candidate 提议阶段；该次轨迹中提出 17 条 Fact Candidate 和 5 条 Inference Candidate。平台在严格反序列化时发现至少一条 Fact 的 `object` 引用了同一提议中未声明的 Entity，因此拒绝 Candidate，未完成发布、重评与回答闭环 | 真实模型已经证明可以从 Commit Patch 形成非空复杂候选，但尚未证明候选契约稳定、复杂 History 知识可准入或 H-04 可正确回答。 |
| 4 | Candidate 修正实现（尚未真实重跑） | 已实现最多 3 次总提议尝试（首提 1 次、contract correction 最多 2 次）：校验失败后把上一版完整提议与结构化错误反馈送回同一隔离 Investigation，要求返回完整替代提议 | 当前 Codex Agent 仍不是真正的 no-tools Provider；安全复核确认“看到工具事件后失败”是事后拒绝，不能撤销已经发生的读取或命令。因此没有继续真实重跑，也不能把修正实现写成闭环通过。 |

### 24. 本轮已落实的边界修正

- `ArtifactRequest.include_globs` 为空现在表示“不物化普通仓库文件”，不再隐式扩展为全仓库；Commit 与显式 Revision Comparison Artifact 仍可独立收集。
- Codex Structured Output 的 Provider Schema 只承担该 Provider 支持的对象形状约束；不支持的长度、数量、唯一性和跨引用规则不能静默丢失，必须继续由平台 Capability owner 校验。当前严格 owner 校验已覆盖 Candidate、Build Intent 和 Formal Tool 等本轮关键路径，但尚未形成全部注册 Capability 的统一完整覆盖。Provider 形状合法不等于业务结果合法。
- Candidate 提议当前可以在同一 Investigation 中进行最多 3 次总尝试（首提 1 次、纠错重提最多 2 次）；每次都重新执行 Entity、Evidence、Fact、Inference、本地引用和平台重建字段校验，错误版本不能增量混入正式知识。
- Answer Review 不再把 Answer Candidate 自身直接当作独立权威来源；`authoritative_claims` 从绑定 Snapshot 中重新读取的正式命题重建，并且模型返回 `PASS` 但同时列出 unsupported Claim 时，平台强制转为 `REJECT`。

上述改动是由真实轨迹暴露问题后实施的契约修正。由于安全边界阻止了新的真实重跑，它们目前只有自动回归支持，不能表述为真实模型已经通过修正后的 H-04。

### 25. 继续真实验证前的阻塞项

1. **真正的 no-tools Model Provider。** 临时空目录、`read-only` sandbox、提示词禁止工具和 JSONL 事后拒绝都不是执行前权限隔离。必须机械禁用 shell、文件、Web、MCP 和其他 Agent 工具，或把调用放入外部强隔离环境，才能继续向真实模型提供内部 Source Artifact。
2. **KnowledgeBuildTarget canonical binding。** Commit、方法和模块目标仍需解析为不可歧义的 canonical identity，并与 frozen Gap、ArtifactRequest 和最低发布目标机械绑定；模型不能通过空 Target、短前缀或无关同类型 Inference 弱化门禁。
3. **逐 Need 的语义充分性。** “存在一条 `HISTORY_IMPACT`”不能证明 H-04 的依赖、令牌生成、解析/验签、过期、校验、刷新和未知项均已覆盖。复杂 Inference 的每个实质断言仍需独立支持与反例验证。
4. **有界 Source Tool Loop。** 当前 Investigation 仍主要由一次 ArtifactRequest 物化来源后整体提交给 Candidate 模型。真实模型是否需要搜索、读取指定文件/行、比较 Revision、观察结果后继续调查的有界 Source Tool Loop，必须在 no-tools 模型执行边界之外由平台工具实现并验证预算。
5. **新的产品门禁。** Behavior 单例成功和 H-04 到达复杂 Candidate 都是诊断证据，不是冻结留出集的重新评分。产品结果仍为 `33.75 / 50`，即直接 Git Agent 的 `67.5%`。

## 总体结论

### 26. 一般架构判定

以下判定记录 V0.7 时点结论。从 Slice 1 到 V0.7 真实模型诊断，没有发现需要增加新顶层模块或反转既有依赖方向的证据。七个纵向切片、真实二次更新、首轮产品留出失败实验和针对失败原因的纠偏实现共同支持以下主干：

```text
Source Integration
  → Artifact / Lineage
  → Knowledge Engine
  → Evidence / Entity / Fact / Inference / Snapshot
  → Application Services
      ├─→ Semantic View → CLI / Scheduler / 确定性用例
      └─→ 通用正式知识 Tool → Task Execution Agent
                                      ↕
                                  Model Gateway
                                      ↓
                            Answer Candidate / Review
```

此前发现并修正的越层依赖、错误调用归类、错误步骤排序、错误 revision 等同、固定 View 成为 Agent 能力上限、模型 Candidate provenance 可绕过以及目标更新丢失旧知识等问题，均通过现有模块内部职责或边界契约完成纠偏。该时点证据不要求引入独立 Workflow、Projection、Evolution、Initialization 或新的顶层知识模型。后续 ACV-G02 静态审计已经证明 Iteration 001 实施 Schema 需要补充通用 exact 类型和规则；这是同一 Knowledge Engine / Semantic Model 边界内的实施契约扩展，不推翻本节的顶层模块判定。

版本演进需要保留其形成背景：

- V0.4 来自首轮五个机制 Slice，把 Artifact 中立边界、构建意图与执行策略分离、稳定身份与顺序分离、来源上下文与 Snapshot 发布上下文分离写成明确约束。
- V0.5 吸收首轮产品价值留出失败，明确“直接仓库 Agent 能力是最低基线”，并冻结题目专用 View 与运行时直接来源兜底路线。
- V0.6 把 Knowledge Requirement、固定 Context 通用 Tool Loop、模型主导任务驱动更新、正式命题级准入、Snapshot enrichment、阶段隔离和全量重新评估落成可回放纵向机制。
- 当前 V0.7 用真实模型正反例进一步收紧 Requirement 忠实性、Provider/no-tools 边界、Candidate correction、Build Target 规范化、逐 Need 语义充分性和有界 Source Investigation 契约；这些新增约束尚未全部实现。

Slice 7 进一步证明真实模型能够在一个无 Gap 的 Behavior 单例中完成内置 Agent 路径，也能够对正确 H-04 Commit 形成复杂候选；同时它暴露了 Candidate 本地引用错误和 Codex Agent 不是 no-tools Provider 两项真实阻塞。因此这一诊断增强了对现有模块边界的认识，但没有把“可回放机制闭环”升级为“真实模型复杂知识闭环”。

因此 V0.7 时点结论是：**一般架构职责保持成立，V0.6 最小纠偏机制获得 Demo 支持，但 V0.7 新增的真实模型边界尚未闭环，产品能力门禁仍未通过。** 机制闭环不能替代新的真实模型留出测试。此后详细设计已经通过独立治理进入 Accepted，但实施准备又因 ACV-G02 被暂停；本段历史措辞不构成当前 WP-1 开工授权。

### 27. 当前仍未被证明的事项

以下事项不阻止确认一般架构，但会阻止直接把 Demo 当成生产 MVP：

1. 本轮 Tool Loop、Candidate 提议和审核主要由确定性 Provider 回放；真实大模型在陌生项目上的 Requirement 完整性、工具规划、复杂 Business/Behavior Candidate、反例搜索和审核效果仍需新的未见任务集验证。
2. Evidence 冲突、片面支持和多个非独立来源的置信处理尚未形成通用语义算法；当前只验证了确定性一致来源和明确代码反例。
3. DB、Log、Trace、部署信息和跨 KnowledgeScope 关联属于后续扩展验证，尚不能据此确认环境融合与跨来源版本推断质量。
4. 当前全量物化 14,143 个 Java Method Entity，观察到知识与存储放大；MVP 详细设计应保留并度量完整 Scope 与目标限定两种构建方式，依据更大工程、更新频率和验收阈值决定是否引入增量，并定义 Artifact Payload 保留规则。当前结果不足以否定全量构建作为 MVP 默认策略。
5. 推断型 Business Entity 的原子创建、重命名继承和高风险同名 Entity Resolution 尚未在本项目中出现真实反例。
6. Web Chat 当前是进程内 Adapter，不是生产 HTTP 服务；企业安全、并发、恢复、可观测性等非功能能力按既定决策后置。
7. Snapshot enrichment 的知识失效、Build Intent 最低结果语义门禁、跨来源冲突和 Tool Loop 生产预算仍需详细设计；具体边界见第 22 节。

### 28. V0.7 历史自动验证基线

执行：

```bash
PYTHONPATH=demo python3 -m unittest discover -s demo/tests -v
```

截至 V0.7 该次运行，全量回归为 `91` 个测试，耗时 `46.624s`，结果 `OK`。范围覆盖 Slice 1 基线、Java Artifact Lineage、S-02、Behavior、Business、History、Inference 准入与单 Candidate 排除、Connector 扩展、Semantic View 扩展、Model Provider 版本记录、Knowledge Requirement 与 Sufficiency Assessment、固定 Context 通用正式知识 Tool Loop、严格工具动作与执行预算、任意 Git Revision / Commit / Diff、空文件选择器、模型 Candidate 反序列化与 contract correction、命题级 Fact 准入、Knowledge Schema 兼容门、Snapshot enrichment 与并发 base 隔离、来源与答案 Context 隔离、Answer Review 防自证、Scheduler 复用、Snapshot 隔离和静态依赖规则。该数字是历史基线；加入 Candidate-only 机制见证后的最新回归见第 33 节。

## 架构能力验证：正式知识单路径能力守恒

**登记日期：2026-08-05**

**Case ID：`DVR-FORMAL-PATH-CAPABILITY-001`**

**状态：`Static Mapping Supported — Full Run Not Executed`**

**基线：[Architecture_Capability_Validation_Baseline.md](Architecture_Capability_Validation_Baseline.md)**

### 29. 登记原因与验证边界

截至第 28 节的既有 Slice 和 91 个自动测试证明了若干模块边界、状态门禁和可回放机制，但没有证明：Direct Agent 能从相同 Git 来源形成的每个实质结论，都能无语义弱化地进入正式知识并在来源关闭后恢复。首轮产品留出仍为 `33.75 / 50`，且 H-04 纠偏中的复杂 History Candidate 仍由确定性 Builder 形成；这些结果不能合并为“方案已经具备直接源码能力下限”。

因此新增本 Case，使用 Direct Claim Oracle 和确定性 Capability Fixture，隔离具体模型质量，验证：

- Direct Claim 在同一 Context、Modality 和 Coverage 下的正式表达与完整恢复。
- Evidence、Candidate、Admission、Snapshot、逐 Need Sufficiency 和 Answer Review 的单路径闭环。
- 来源关闭后的跨任务 / 跨 Agent 复用、Context 正反例、全链追溯和篡改拒绝。
- Revision 更新后的知识延续、重验证和陈旧状态拒绝。

H-01 至 H-05 只作为已见架构回归 Oracle，不重新成为产品 Holdout。真实模型、Provider、Prompt、泛化、延迟、成本和产品体验继续分别由 Capability Evaluation 与新的未见 Product Holdout 判断。

### 30. 待执行门禁

| Gate | 状态 | 待形成证据 |
|---|---|---|
| ACV-G00 基线完整性 | `NOT_RUN` | Oracle / Fixture /实现 /契约 exact Digest 与可回放 Run |
| ACV-G01 来源可达 | `NOT_RUN` | 全部实质 Claim 的 Source Observation Closure |
| ACV-G02 语义可表达 | `STATIC_MAPPING_SUPPORTED — RUNTIME NOT_RUN` | [Formal Mapping Audit 002](Architecture_Capability_Formal_Mapping_Audit_002.md)：`33 SUPPORTED / 0 PARTIAL / 0 UNSUPPORTED`；只恢复运行资格 |
| ACV-G03 准入与发布闭环 | `NOT_RUN` | 正确 Closure 的 Verification、Admission 和原子 Publication |
| ACV-G04 逐 Need 充分性 | `NOT_RUN` | 同一 Session 的 Need / Joint Support Proof 双向覆盖 |
| ACV-G05 来源关闭恢复 | `NOT_RUN` | fail-fast 来源条件下 `100%` Claim 恢复且零 Source Operation |
| ACV-G06 无过度推断 | `NOT_RUN` | 语义扩张、错误否定、错 Context 和目标弱化放行数为零 |
| ACV-G07 认知复用 | `NOT_RUN` | 三个全新消费者、两个问题、同一 Snapshot、零更新复用 |
| ACV-G08 Context 融合 | `NOT_RUN` | 全部兼容正例组合与全部不兼容反例拒绝 |
| ACV-G09 可信审核 | `NOT_RUN` | 全 Claim 追溯闭包及每类篡改拒绝 |
| ACV-G10 受控演化 | `NOT_RUN` | 受影响知识重验证、stale 状态和过期发布拒绝 |

只有全部 Gate 为 `PASS`，本 Case 才能通过。任一已有依据的 Direct Claim 只能返回 Gap、任何题目专用捷径、自由文本语义逃逸或答案阶段来源读取，都直接使相应 Gate 失败。ACV-G02 已获得新的静态表达闭包，但尚未运行；其他 Gate 和完整 Run 同样未执行。

### 31. 当前影响

Audit 001 记录了 `iter-001.initial.1` 的静态预检失败；Audit 002 已对候选 `iter-001.initial.2` 关闭该静态表达缺口，但不把静态分析解释为完整 Demo Run。在首个完整 Run 完成前：

- 不得宣称正式知识单路径已经证明能力守恒。
- 不得宣称复用、Context 融合或可信审核已经形成超过直接源码调查的方案能力。
- 不得用本 Case 覆盖 `PV-HOLDOUT-001` 的失败结果。
- [Formal Mapping Audit 001](Architecture_Capability_Formal_Mapping_Audit_001.md) 确认冻结的 `iter-001.initial.1` 无法完整表达 31 / 33 个实质评分点；[Formal Mapping Audit 002](Architecture_Capability_Formal_Mapping_Audit_002.md) 确认新的候选契约具有 `33 / 33` 静态承载闭包。两者都是方案契约证据，不是具体模型质量证据。
- WP-1 正式编码继续暂停；新的 exact Schema Definition 已具备重新执行 ACV-G02 的资格，但必须先完成完整 ACV Run 和后续实施基线治理。
- 不能通过 Demo 自由字段、题目专用 Type、删除 Oracle Item 或直接来源旁路规避该阻塞。

### 32. 执行前 Demo 可信性审计

**审计状态：`Completed — Run Gates Remain NOT_RUN`**

本审计只判断审计时已有的 91 个回归是否可以被复用为本 Case 的运行证据，不替代 ACV-G00 至 ACV-G10 的正式执行。结论是：这些回归可以作为修改前的机制基线，但不能证明架构能力守恒。

| 观察 | 现有证据 | 对本 Case 的影响 |
|---|---|---|
| H-04 Gap 看似能够闭环 | `propose-knowledge-candidates` 的确定性响应没有产生 Fact / Inference；非 `structure-core` 构建仍由 `ExtendedKnowledgeBuilder` 生成 History 知识 | 该用例证明了更新、enrichment 和阶段输入隔离，不能证明 Candidate 单路径具备通用补知能力；禁止计入 ACV-G02 / G03 / G05 |
| Answer Payload 不含 Artifact / Evidence Quote | Gateway 会拒绝 Answer Context 中的调查字段，测试也会关闭 Source Integration | 同一个 Provider 实例仍跨 Investigation、Assessment、Answer 与 Review 使用；尚未机械排除 Provider 内部记忆，因此不能单独证明 ACV-G05 |
| Candidate 可声明 `covered_need_ids` | 平台检查 Gap Need ID 的集合分区和引用存在性 | 尚未重建逐 Obligation 的语义 Support Proof；相关但不蕴含的正式知识仍可能被 Assessment Proposal 自报为满足，因此不能证明 ACV-G04 / G06 |
| Connector 已提供 `search / read / compare` | Local Git Tool 能读取任意 Revision、Commit 与 Diff | Investigation 仍一次性形成 ArtifactRequest 并把全部已选 Artifact 提交给 Candidate Provider；尚未形成模型逐步提议、平台授权执行的 Source Tool Loop |
| Demo 可在一个 Bundle 中生成 Fact 与 Inference | Inference Verifier 当前把同批 Fact Candidate 当作可用前提 | 这与 Iteration 001 Schema 的 `INITIAL / UNCHANGED` 两阶段正式前提规则冲突；不能用该路径证明当前详细设计可实现 |
| 通用 Fact / Inference 字符串可以保存复杂内容 | Demo 契约比冻结 INITIAL Schema 更宽 | 只有把 Oracle Claim 映射到 exact Schema Type、Context、Modality 与 Coverage 后，才能判断可表达性；不能用 Demo 自由字段替代 ACV-G02 |

因此，正式 Run 前必须先做到：

1. 增加明确的 Candidate-only 构建模式，并使任何确定性或题目专用 Builder 调用立即失败。
2. 使用两次独立 Publication：先发布直接 Fact，再从 exact Base Snapshot 的正式前提构造 Inference。
3. 关闭来源与 Investigation Provider 后，以全新 Provider / Session 只从 Snapshot 完成 Sufficiency、Answer 和 Review。
4. 对同类型但错误目标、部分覆盖、错 Revision 和空 Candidate 建立失败反例。
5. H-01 至 H-05 Direct Claim 的独立审计已完成，见 [Formal Mapping Audit 001](Architecture_Capability_Formal_Mapping_Audit_001.md)；结果为 `2 SUPPORTED / 22 PARTIAL / 9 UNSUPPORTED`，须先创建新的 Schema Definition 并完成实施基线治理，再运行完整 Gate。

在该次审计时，上述条件尚未关闭，91 个测试只保持其原有机制回归含义。后续 Candidate-only 见证与 Formal Mapping Audit 002 分别关闭了部分机制前置项和静态表达缺口；它们仍未把任何运行时 Gate 或 `DVR-FORMAL-PATH-CAPABILITY-001` 完整 Run 改为 `PASS`。

### 33. Candidate-only 两阶段机制见证

**运行状态：`PASS — Bounded Application / Engine Mechanism Only`**

执行记录见 [Architecture Capability Mechanism Witness 001](Architecture_Capability_Mechanism_Witness_001.md)。本轮在运行时随机生成双文件 Git 工程，并使 Structure / Extended Builder fail-fast，验证了：

- 第一次独立更新只从 Candidate Proposal 发布 Direct Facts。
- 第二次独立更新只引用 exact Base Snapshot Fact IDs 形成 Inference；同 Bundle Fact、错误 target 和跨方法混合 premise 均被拒绝；Direct Fact 发布也不能夹带 Build Target 外的 extra Fact。
- 发布后释放 Investigation、把 Source Integration 设为 fail-fast，并以全新 Answer Provider 和独立 Review Provider 只从 Snapshot 完成答案与审核。
- Direct Fact Need 与最终 Inference Need 分离，第一阶段不再借 `covered_need_ids` 冒充最终问题已经满足。

专项由 `4` 个 `unittest` 方法承载上列 `5` 类机制 Case，结果为 `4 tests / 5 listed cases — PASS`；关闭未授权 extra Fact loophole 后，完整回归由原 `91` 项增加为 `95 / 95 PASS`，耗时 `52.236s`，编译检查通过。

该结果证明两阶段正式发布路径在 Application / Engine seam 上可承载一个通用正反例，不证明公开 Agent 已自动完成多轮 Gap Resolution，也不证明模型能够选择正确前提、逐 Need 语义充分或完整 ACV Gate 已通过。Candidate 由确定性 Contract Driver 产生是有意的变量隔离：Demo 验证架构方案能力，真实模型质量另由 CE 评测。运行时没有装载候选 `iter-001.initial.2` exact Schema；因此本见证本身不提供 ACV-G02 证据。后续 Audit 002 已静态确认 33 项可表达，但 ACV-G02 运行和完整 Run 仍为 `NOT_RUN`。

### 34. 候选契约闭合与独立静态复核结果

**当前状态：`33 / 33 Static Mapping Supported — Full ACV Run Not Executed`**

为回应 Audit 001 暴露的表达缺口，已经形成以下三份相互引用的能力验证候选契约：

- [Local Git Provider Profile Revision 002](../../implementation/iteration-001/contracts/ITER-001-Local-Git-Provider-Profile-Revision-002.md)，`ITER-001-LOCAL-GIT-PROVIDER@0.2.0`；
- [Foundational Software Semantics Rule Pack](../../implementation/iteration-001/contracts/ITER-001-Foundational-Software-Semantics-Rule-Pack.md)，`ITER-001-FOUNDATIONAL-SOFTWARE-SEMANTICS@0.1.0`；
- [INITIAL Knowledge Schema Revision 002](../../implementation/iteration-001/contracts/ITER-001-Initial-Knowledge-Schema-Revision-002.md)，`iter-001.initial.2`。

三份文档均处于 `Proposed — Capability Validation`，已经提供 exact Digest、前驱和显式依赖闭包。[Formal Mapping Audit 002](Architecture_Capability_Formal_Mapping_Audit_002.md) 已按不改变 33 个 Oracle Item 的原则独立复核，结果为 `33 SUPPORTED / 0 PARTIAL / 0 UNSUPPORTED`。

该结果关闭 Audit 001 暴露的实施契约静态表达缺口，并恢复 ACV-G02 的重新执行资格；它不登记 ACV-G02 运行 `PASS`，也不解除 `SWM-IMP-READINESS-HOLD-001`。ACV-G00 至 ACV-G10 的完整 Demo Run 仍须执行，真实模型质量仍由 CE 独立验证，Demo Harness 不进入生产路径。

### 35. JWT Formal Contract 可执行性复核 002

**记录：** [SWM-ARCH-FEAS-JWT-002](Architecture_Feasibility_Review_JWT_002.md)  
**状态：** `MECHANICAL CONFORMANCE PASS / LIVE CAPABILITY NOT RUN / DEVELOPMENT NOT AUTHORIZED`

从真实 `mall` Git Object 重新执行 Contract 可构造性检查后，确认 JWT 0.1.0 的 `6 / 6 STATIC SUPPORTED` 结论不足以授权完整 Run。发现的七项根因包括：Requirement 丢失 Criterion Obligation / Joint Constraint、十分量表无法证明逐 Claim 完整性、Manifest 无法回指 Rendered Request、Entity 阶段缺失、本地 Envelope 与真实 Provider Conformance 混淆、答案隔离遗漏访问 attempt、以及外层非 Git 分发快照无法记录实现身份。

对应修订为 [JWT Formal Contract Revision 002 candidate](../../implementation/iteration-001/contracts/ITER-001-JWT-Validation-Formal-Contract-Revision-002.md)。新增通用 validation-only Harness 在真实 target / parent / 三文件 changeset 上执行 `13 / 13 PASS`，包含 Entity → Fact → Inference 三阶段 Publication、逐 Obligation Sufficiency、来源关闭 Answer、validation Store 隔离和 provisional 20-Claim 双向机制见证。该运行全部使用确定性 Candidate / Review / Answer Fixture，不是完整 JWT Capability Run。

当前未执行项保持：`CC-MODEL-NO-TOOLS-001` Live Provider Conformance、真实七 Model Role、重新冻结 Direct Agent / Direct Claim Oracle、真实预算与成本、最终 Answer Review / Delivery Run Record。因而 ACV-G00 至 G10 不因本节变为 PASS，Implementation Readiness Hold 继续生效。
