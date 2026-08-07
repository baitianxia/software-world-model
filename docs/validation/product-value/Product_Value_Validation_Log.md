# Software World Model 产品价值验证记录

## PV-EXP-001：未编码 Endpoint Structure 留出题

**日期：2026-08-01**  
**状态：探索性对照完成；未证明产品优势**  
**工程：`macrozheng/mall`**  
**Revision：`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`**

### 1. 目的

本实验用于观察：在同一真实工程和同一问题下，当前 Software World Model Demo 相比通用 Agent 直接调查 Git 工程，是否已经形成准确性、证据、时延或复用方面的优势。

本次是探索性实验，不是预先注册的产品价值验收基线。实验结果只能用于发现问题和设计后续固定基线，不能单独决定继续或停止项目。

### 2. 留出问题

> `POST /returnApply/create` 位于哪个 Maven 模块，并由哪些 Controller、Service 接口及实现方法承接？

选择理由：

- 该 Endpoint、Controller 和 Service 没有出现在 Demo、架构验证问题或 `KnowledgeBuildTarget` 中。
- 问题类型与现有 S-02 同属 Endpoint Structure，能够检验通用结构构建是否推广到未编码对象。
- 不引入新工程和新数据源，暂时隔离跨项目与 Connector 差异。

### 3. 对照方法

#### A：直接仓库调查路径

- 隔离 Agent 只允许读取 `validation-projects/mall`。
- 不允许读取 Demo、Software World Model 数据库、验证配置或另一组输出。
- Agent 直接使用 `rg`、Git 和文件读取工具回答问题。

#### B：Software World Model 路径

- 隔离 Agent 不允许读取或搜索 `validation-projects/mall`。
- 只允许使用 Demo 公开 CLI 和当前数据库。
- 通过 `endpoint`、`snapshot` 和 `explain` 查询正式知识。
- 不允许直接查询 SQLite 内部表。

#### 独立核对

- 第三个隔离 Agent 只读取源码建立黄金答案和 10 分评分量表。
- 核对者先生成黄金答案，之后才接收两组答案摘要并评分。
- 评分只考察事实和证据，不评价文风。

### 4. 环境一致性

- Git 工程 HEAD 与 Software World Model 当前 Snapshot Revision 均为固定 Revision。
- Git 工作树干净。
- 当前 Snapshot 状态为 `CURRENT`。
- 当前数据库为此前 `full-validation` 构建结果，大小 51 MB；其构建成本约 8–10 秒。

### 5. 黄金答案摘要

```text
mall-portal
  → OmsPortalOrderReturnApplyController#create(OmsOrderReturnApplyParam)
  → OmsPortalOrderReturnApplyService#create(OmsOrderReturnApplyParam)
  → OmsPortalOrderReturnApplyServiceImpl#create(OmsOrderReturnApplyParam)
  → OmsOrderReturnApplyMapper#insert(OmsOrderReturnApply)
```

实现方法复制请求属性，设置创建时间和初始状态 `0`，再通过 MyBatis Mapper 插入记录。`mall-admin` 也有类级 `/returnApply` Controller，但没有 `/create`，不承接目标 Endpoint。

### 6. 结果

| 指标 | A：直接仓库 Agent | B：Software World Model |
|---|---:|---:|
| 用户问题核心链 | 7.5 / 7.5 | 6.0 / 7.5 |
| 扩展黄金量表总分 | 8.25 / 10 | 6.25 / 10 |
| 端到端调查耗时 | 约 46 秒 | 约 3–5 分钟 |
| 单次结构查询执行时间 | 不单独计算 | 0.14–0.16 秒 |
| 预构建成本 | 无 | 约 8–10 秒、51 MB |
| 结构化稳定身份 | 无正式 Entity / Fact ID | 有 |
| Snapshot / Revision 绑定 | Agent 主动检查 Git Revision | 查询结果原生携带 |

两组都正确识别了模块、Controller、Service 接口和实现方法，没有产生错误主链。

### 7. Software World Model 的有效结果

- 未编码具体 Endpoint 仍能通过通用 Structure Fact 查询得到正确链路，说明 Java Structure 构建没有只覆盖 S-02 特例。
- 原始 `endpoint` 查询稳定返回结构化 Entity、Fact、Snapshot 和 Revision，五次重复执行均为 0.14–0.16 秒。
- 6 条关系均具有 Fact ID，并可通过公开 `explain` 命令进一步取得 Evidence。
- 回答阶段无需重新读取 Git 工程，具备跨 Agent 复用同一知识状态的基础。

### 8. 暴露的问题

1. **端到端体验没有优势。** 当前公开接口需要先查询 Endpoint，再对 6 个 Fact 分别调用 `explain`；完整核对比直接阅读源码更慢。
2. **复合结论的 Evidence 不完整。** 完整 Endpoint 为 `/returnApply/create`，但 `EXPOSES_ENDPOINT` 的 Evidence quote 只包含方法级 `/create`，没有同时引用类级 `/returnApply`。
3. **模块归属证据不理想。** `mall-portal CONTAINS_TYPE Controller` 的 Evidence 来自 Java 类声明和路径，而不是 Maven POM 对模块边界的正式定义。
4. **预定义 Schema 限制了调查深度。** 当前模型能够返回 Controller→Service→实现链，但没有继续表达实现方法中的属性复制、状态设置、Mapper/XML 落点、返回分支和代理歧义；直接 Agent 可以按问题现场继续深入。
5. **尚未验证完整 Agentic 回答。** Demo 只有确定性 Model Provider，0.14–0.16 秒是结构查询时间，不是自然语言理解、答案生成和 Answer Review 的完整时延。
6. **一次问题不能证明复用收益。** 本实验没有覆盖多个新会话、批量重复问题、版本变化或跨来源任务。

#### 8.1 根因核对

- `EXPOSES_ENDPOINT` 构建器先组合类级与方法级路径形成完整 Endpoint，但只把方法级注解行保存为该 Fact 的 Evidence，因此 `/returnApply` 的来源没有进入同一事实的支持集合。这是 Evidence 构建缺陷，不是源信息不存在。
- 当前 Snapshot 实际已经包含实现方法到 `OmsOrderReturnApplyMapper#insert` 的 `CALLS` Fact，以及 `copyProperties`、`setCreateTime`、`setStatus` 的 `CALLS_OPERATION` Fact；`endpoint_chain` 只遍历 Controller 调用和接口实现关系，到实现方法声明后固定停止，所以这些正式知识没有进入结果。
- MyBatis Mapper XML 虽然作为 Artifact 被采集，但当前 Knowledge Engine 没有将 `<insert>` 及 Java Mapper 方法映射构建为正式 Fact，因而无法只依靠正式知识继续解释 SQL 落点。
- `endpoint_chain` 只按完整 Endpoint 名称做精确匹配，没有执行相同路径前缀、同名 Controller、多个实现、代理或其他候选的反例搜索，因此不会主动报告 `mall-admin` 排除项。
- 当前 Web Chat 使用确定性 Model Provider test double，只能路由少量固定问题；本实验实际由隔离 Agent 手动选择公开 CLI，并未验证平台自身能够动态规划上述补充调查。

这些结果说明当前 Demo 更接近“正式知识的固定查询投影”，尚不是“以正式知识为记忆、并能根据问题动态扩大调查范围的 AI Native 调查系统”。

### 9. 当前判定

本实验支持“通用 Structure 知识能够在未编码对象上复用”，但不支持“当前 Software World Model 已经比直接仓库 Agent 更有产品价值”。在这个单仓库 Structure 留出题中，直接 Agent 的回答更完整，证据更直接，端到端耗时也更短。

因此当前产品价值门禁保持 **未通过、也未判定失败**：需要先固定多问题对照基线，再继续实验。不能在看到本次缺陷后先修改 Demo、再只使用同类问题证明改进有效。

本实验同时确立一个 P0 产品约束：直接仓库调查路径不是需要被淘汰的竞争方案，而是平台必须保留的能力下限。后续实验首先检查平台是否发生任务完成率、正确性或关键证据覆盖退化；只有通过非回归门禁后，才继续评价知识复用带来的额外收益。

这里的“能力下限”只用于隔离测试，不表示生产运行双路径。直接仓库 Agent 的输出不能进入 Software World Model 回答流程；被测路径知识不足时只能通过正常 Knowledge Update 扩展并发布正式知识，再重新回答。

### 10. 下一步约束

- 在修改 Demo 前固定后续问题集、评分规则、成本口径和继续 / 缩小 / 停止阈值。
- 问题集至少区分：未编码 Structure、未编码 Behavior / Business、重复或跨 Agent 复用、真实 Revision 变化、后续跨来源任务。
- 直接路径与 Software World Model 路径尽量使用相同基础模型和相同工具权限。
- 同时记录首次构建成本、单次使用成本、重复使用成本和知识更新成本，不能只比较缓存后的查询时延。

## PV-HOLDOUT-001：五题冻结非回归基线首轮

**日期：2026-08-02**  
**状态：首轮完成；P0 未通过**

完整题目与预注册量表见 [产品价值留出测试基线](Product_Value_Holdout_Baseline.md)，执行过程、逐题得分和架构资格说明见 [首轮执行记录](Product_Value_Holdout_Run_001.md)。冻结黄金答案的事实纠正和源码语义边界澄清统一记录在 [基线勘误](Product_Value_Holdout_Baseline_Errata.md)，原冻结文件、SHA-256 与历史执行记录保持不变。

### 结果摘要

| 指标 | 直接 Git Agent | Software World Model Agent |
|---|---:|---:|
| 五题总分 | 50 / 50 | 33.75 / 50 |
| 相对完成度 | 100% | 67.5% |
| 调查耗时 | 10 分 21 秒 | 约 35 分钟 |
| 正式知识 CLI 调用 | 不适用 | 81 次 |
| 核心事实错误 | 0 | 0 |

H-01 Maven 图达到 `10 / 10`，证明固定 Snapshot 上的通用搜索、单跳关系遍历和 Evidence 解释能够支持未预设的 Structure 问题。H-02、H-03、H-05 分别为 `8.25 / 10`、`7.25 / 10`、`7.25 / 10`；H-04 因目标 Commit 没有进入正式知识仅为 `1 / 10`。

本轮失败的主要原因已经从“固定 View 卡住已有 Fact”转为“模型无法通过任务驱动 Knowledge Update 把缺失语义正式化”。下一阶段必须实现模型主导的 Build Intent、来源调查、Candidate 形成、独立准入、新 Snapshot 发布和 Requirement 全量重评；继续增加预定义 View 或让答案阶段直接读取 Evidence 中未正式化的源码语义，都不能解决该问题。

## PV-CORR-001：任务驱动 Knowledge Update 纠偏机制验证

**日期：2026-08-02**  
**状态：纠偏机制验证通过，产品 P0 仍未通过**  
**工程：`macrozheng/mall`**  
**S0 Revision：`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`**  
**任意 Commit：`dacce5f28dfc1734f2db09668d928d7fac2a3a7a`**

### 1. 验证目的与边界

本次验证针对 PV-HOLDOUT-001 暴露的 H-04 机制缺口：当固定正式知识 Snapshot 不能满足当前任务时，系统是否能够冻结同一个 Knowledge Requirement，通过隔离的 Investigation 调查任意 Git Commit，将新增知识准入并发布为 S1，再只依靠新的正式知识上下文完成原 Requirement。

这不是五题冻结基线的重跑，也不是新的产品价值评分。它只验证纠偏纵向切片的状态、隔离、保留和并发门禁，不把受控测试通过解释为真实模型在未见任务上的准确率或完成度提升。

### 2. 机制验证结果

| 检查点 | 验证结果 |
|---|---|
| S0 Knowledge Gap | S0 的 History 正式知识不包含目标 Commit；首次 Sufficiency Assessment 将对应 Need 判定为 `GAP`，没有用空结果推导现实中不存在该 Commit。 |
| Requirement 冻结 | 发布前后两次 Assessment 使用完全相同的 Requirement 和 Need，不通过改写问题或降低充分条件获得完成。 |
| 任意 Commit 调查 | Build Intent 按任务携带目标 Commit；Git Connector 在固定仓库中解析并读取该 Revision，而不是依赖验证配置预编码 Commit。 |
| S1 发布与重评 | 新知识经 Artifact、Evidence、Candidate、Verifier 和原子发布主干进入 S1；随后在 S1 上对原 Requirement 全量重评并达到完成，答案及独立 Review 均引用正式知识。本 H-04 回放中模型响应没有生成语义 Candidate，History Candidate 由既有确定性 Builder 产生；模型 Candidate 只在独立的简单直接 Fact 场景完成准入验证。 |
| 关闭来源与清空调查上下文 | Candidate 提交后将 Source Integration 替换为失败哨兵并关闭 Investigation Context；后续重评、答案生成和审核仍然完成。Answer payload 不含 Source Artifact、Candidate Bundle、Evidence quote 或源码片段。 |
| Fresh Contexts | S0 Knowledge Use、Investigation、S1 Knowledge Use 和 Answer 分别使用新的 Context；Knowledge Use tool trace 在 S1 从空状态重新开始，各阶段 Context ID 互不复用。 |
| 旧 token 失效 | S1 成为 CURRENT 后，使用 S0 `snapshot_token` 的正式知识查询返回 `STALE_CONTEXT`，不能把旧上下文与新知识混用。 |
| S1 保留旧知识 | S0 的 Entity、Fact、Inference、Artifact 和既有 Evidence 引用均为 S1 的子集；原 Behavior 与 Business Inference 仍可查询，新增 History 知识没有以窄构建覆盖旧知识。 |
| Stale Base 门禁 | 并发 Snapshot 已替换 Current 后，基于旧 Base 的发布返回 `STALE_BASE_SNAPSHOT`；并发发布结果保持 Current，过期构建不能覆盖它。 |

### 3. 当前判定

上述结果证明 H-04 所要求的纠偏控制路径已经闭环：S0 Gap 能触发冻结 Build Intent，任意 Commit 可以进入隔离调查，S1 能在保留旧知识的同时原子发布新增正式知识，答案阶段不依赖来源或调查记忆，旧 Context 与 stale Base 均被拒绝。因此本条目的机制结论为：**纠偏机制验证通过**。该结论不包含“模型已经生成复杂 History Candidate”；本场景的 History 语义仍来自确定性 Builder。

PV-HOLDOUT-001 的原始产品结论保持不变：Software World Model Agent 仍为 `33.75 / 50`，相对直接 Git Agent 的完成度仍为 `67.5%`。本次没有按原冻结协议重新执行五题，也没有在新的未见任务集上达到直接调查能力下限，所以不能回算原分数或把产品 P0 改为通过。当前总状态仍为：**产品 P0 仍未通过**。

### 4. 真实性限制

- 本次使用可回放的确定性 Model Provider 和受控集成测试，证明的是契约与控制流，不证明真实模型形成 Requirement、规划调查、提出通用 Fact / Inference Candidate 或判断充分性的准确率。
- H-04 的模型 Candidate 响应为空；模型提出的 Candidate 仅在另一个单行、简单直接 Fact 样例中验证，尚未覆盖复杂 History、Behavior、Business 或跨文件 Inference。
- 目标只覆盖一个仓库中的一个任意 Commit；尚未验证更大工程、跨来源、分支与合并提交、语义冲突、反例搜索或连续多轮更新。
- “关闭来源”由进程内失败哨兵验证，“清空上下文”由关闭并隔离 Context 及 payload 检查验证；这不是权限逃逸、提示注入或外部模型会话残留的安全测试。
- S1 保留验证检查正式对象和 Evidence 引用的集合包含关系，不等于已经证明跨 Revision 语义冲突解决、删除传播或长期增量维护正确。
- stale Base 验证是受控发布竞态，不是高并发、崩溃恢复或分布式事务压力测试。

下一次产品 P0 判定必须冻结新的未见任务集，使用与直接路径可比的真实模型和来源边界，重新测量任务完成率、正确性、关键证据覆盖、时延与成本；在该结果产生前，纠偏机制通过不能替代产品价值门禁。

## PV-DIAG-001：内置 Agent 真实模型纵向诊断

**日期：2026-08-02**  
**状态：诊断未闭环；非产品门禁；产品 P0 仍未通过**

### 1. 目的与计分边界

本次诊断把真实 Codex CLI Model Provider 接入内置 Agent，用于检查真实模型能否完成已有正式知识上的问答，以及在知识不足时形成复杂 Candidate。它没有按照冻结协议重新执行五题留出集，因此不产生新产品分数，也不能覆盖 `PV-HOLDOUT-001`。

### 2. 实际诊断时间线

| 顺序 | 诊断 | 实际结果 | 产品含义 |
|---:|---|---|---|
| 1 | Behavior 单例 | 完成 8 次 Model Call，总耗时 `83.093s`；Final Response 为 `ANSWERED`，Answer Review 为 `PASS` | 证明一个已有正式知识足够的 Behavior 单例能够走通真实模型路径；不证明 Behavior 泛化或产品 P0 通过。 |
| 2 | H-04，错误 Commit SHA 参数 | 运行目标不是冻结题目的正确 Commit | 这是诊断参数错误，不能用于支持或否定架构、模型能力或 H-04 结论。 |
| 3 | H-04，正确 Commit `dacce5f28dfc1734f2db09668d928d7fac2a3a7a` | 模型到达复杂 Candidate 阶段；轨迹中提出 17 条 Fact Candidate 和 5 条 Inference Candidate。至少一条 Fact 的 `object` 引用了本次提议中未声明的 Entity，严格反序列化拒绝了整个 Candidate | 证明真实模型能够从 Commit Patch 形成非空复杂候选；未证明 Candidate 契约稳定、复杂 History 知识能够准入或 H-04 能够正确回答。 |
| 4 | Candidate contract correction 实现（尚未真实重跑） | 已实现最多 3 次总提议尝试（首提 1 次、纠错重提最多 2 次）：把上一版完整提议和结构化校验错误反馈给同一隔离 Investigation | 当前 Codex Agent 仍不是真正的 no-tools Provider；事后发现工具事件再失败不能撤销已经发生的读取或命令。因此未继续真实重跑，不能宣称修正后的 H-04 已闭环。 |

### 3. 由诊断触发的契约修正

- 空 `ArtifactRequest.include_globs` 现在表示不选择普通仓库文件；Commit 与显式 Revision Comparison Artifact 仍可单独选择，避免目标限定请求意外物化全仓库。
- Structured Output Schema 被明确拆成两层：Provider 兼容的对象形状 Schema 负责尽早拒绝形状错误，平台 Capability owner 必须继续校验数量、长度、唯一性、跨引用和语义。当前严格 owner 校验已覆盖 Candidate、Build Intent 和 Formal Tool 等本轮关键路径，尚未证明全部注册 Capability 都完整覆盖。Provider 接受不等于 Candidate 可以准入。
- Candidate 当前最多允许 3 次总提议尝试（首提 1 次、contract correction / re-proposal 最多 2 次）；每次都重新执行全量本地引用与平台字段校验，失败版本不能增量混入正式知识。
- Answer Review 的权威命题从绑定 Snapshot 的正式知识重新构造，不再把 Answer Candidate 自身当作独立证明；模型返回 `PASS` 但仍列出 unsupported Claim 时，平台强制 `REJECT`。

这些修正目前由自动回归支持，但尚未经过修正后的真实 H-04 重跑，不能记录为真实模型能力闭环。

### 4. 继续验证前的阻塞项

1. 提供执行前机械禁用 shell、文件、Web、MCP 等工具的真正 no-tools Model Provider，或使用外部强隔离模型调用环境。
2. 将 `KnowledgeBuildTarget` 解析为 canonical identity，并与 frozen Gap、ArtifactRequest 和最低发布目标机械绑定。
3. 建立逐 Need、逐实质断言的语义充分性校验，不能用“存在同类型 Fact / Inference”替代目标问题的完整覆盖。
4. 在模型执行安全边界之外实现并验证有预算的 Source Tool Loop，使调查能够搜索、定点读取、比较 Revision，并根据观察继续取证。

### 5. 当前产品判定

产品分数保持不变：Software World Model Agent 为 `33.75 / 50`，相对直接 Git Agent 为 `67.5%`。Behavior 单例成功和 H-04 到达复杂 Candidate 都是诊断进展，不是新的产品门禁；在冻结的新未见任务集完成可比重测前，产品 P0 仍未通过。
