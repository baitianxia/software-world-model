# PV-HOLDOUT-001 首轮执行记录

## 1. 结论

**P0 非回归门禁未通过。**

同等级模型直接调查 Git 工程的量表覆盖为 `50 / 50`；只使用 Software World Model 正式知识工具的隔离模型为 `33.75 / 50`，即直接路径的 `67.5%`。执行时修正冻结黄金答案自身的一处事实笔误后，没有发现 Software World Model 组独有的核心事实错误；失败性质是正式知识覆盖与任务完成度不足，而不是模型主动编造答案。后续发现的其他语义边界问题统一保存在基线勘误中，不静默改写本执行记录或既有分数。

本轮证明四类通用正式知识工具能够释放已存在但被固定 Semantic View 卡住的知识，也证明它们不足以单独满足产品门禁。当前系统仍不能进入 MVP 详细开发冻结。

## 2. 实验身份

- 执行日期：2026-08-02
- 冻结基线：[Product_Value_Holdout_Baseline.md](Product_Value_Holdout_Baseline.md)
- 冻结文件 SHA-256：`d5ebc4921fcddbfdf942f7bf2a63fb4a396237a242af858530285c56a33a0587`
- 基线勘误：[Product_Value_Holdout_Baseline_Errata.md](Product_Value_Holdout_Baseline_Errata.md)
- 被测工程 Revision：`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`
- Software World Model Snapshot：`snapshot:9d2f8973-1262-4e0d-bc69-9798253ced82`

题目、黄金要点、量表、隔离规则和门禁先于通用 Tool 实现及测试执行冻结。勘误没有修改冻结文件或实现：E-001 纠正 H-03 的“SKU 促销价 / SKU 原价”客观笔误并据固定 Revision 重算当时受影响评分；E-002、E-003 进一步澄清缺 SKU 分支与满减比较器的源码语义边界，不在本文中追溯改写冻结题目或既有执行结果。

## 3. 被测改动

本轮在不加入题目专用 View 或规则的前提下实现：

- 打开并固定当前正式知识 Snapshot Context。
- 搜索正式 Entity / Inference，支持稳定分页。
- 读取一个或多个 Entity 的一跳正式 Fact 邻域，支持稳定分页。
- 批量解释 Fact / Inference 及 Evidence。
- 显式返回 Predicate 语义、查询限制、Schema Version 与 `coverage=UNDECLARED`。
- 新 Snapshot 发布后拒绝旧 Context，返回 `STALE_CONTEXT`。
- 完整 Endpoint 由类级与方法级 Mapping 组合时，同一 Fact 分别关联两个独立 Evidence。
- 增加 Knowledge Requirement 与逐项 Knowledge Sufficiency Assessment 的最小不可变契约。

Demo 回归测试 `36 / 36` 通过。

## 4. 数据与成本

### 4.1 Snapshot 构建

| 指标 | 结果 |
|---|---:|
| 构建耗时 | 约 9 秒 |
| SQLite 文件 | 约 51 MB |
| Artifact | 1,186 |
| Entity | 20,362 |
| Evidence | 32,206 |
| Fact | 32,832 |
| Inference | 16 |

### 4.2 调查

| 指标 | 直接 Git Agent | Software World Model Agent |
|---|---:|---:|
| 五题总调查耗时 | 10 分 21 秒 | 约 35 分钟 |
| Software World Model CLI 调用 | 不适用 | 81 次 |
| 直接读取源码 | 是 | 否 |
| 读取 SQLite 内部表 / Artifact Payload | 否 | 否 |
| 违规越界读取 | 否 | 否 |

Software World Model Agent 的 81 次调用中有 4 次空查询被 CLI 正确拒绝。该组只使用固定 Snapshot Token 的四类公开知识能力；没有使用旧固定 View、源码、SQLite 查询或直接 Agent 输出。

## 5. 独立评分

| 题目 | 直接 Git Agent | Software World Model | 差距性质 |
|---|---:|---:|---|
| H-01 Maven 内部依赖图 | 10.00 | 10.00 | 已发布 Structure Fact 足够；缺 coverage 但未妨碍量表内容 |
| H-02 领券控制流 | 10.00 | 8.25 | 缺领取码规则、事务与数据库并发约束知识 |
| H-03 购物车促销 | 10.00 | 7.25 | 缺分支映射、最高档完整证明、TreeMap 与缺资料行为 |
| H-04 JWT 迁移 Commit | 10.00 | 1.00 | 目标 Commit 与父 Commit 完全没有进入正式知识 |
| H-05 优惠券可用性 | 10.00 | 7.25 | 缺 DAO 状态范围、返回分类、开始时间与未知值处理 |
| **总分** | **50.00** | **33.75** | **67.5%** |

门禁结果：

- 无直接组未犯的核心事实错误：**通过**。
- 每题不低于直接组 90% 且不低于 8 分：**失败**，仅 H-01 通过。
- 总分不低于直接组 95%：**失败**，要求至少 47.5 分。
- 覆盖不明时不把空结果当作不存在：**通过**。
- 实质 Claim 均由正式知识在其语义范围内支持：**尚不能判定通过**，见第 7 节。

## 6. 可以成立的结论

### 6.1 通用知识工具是有效改进

- H-01 在没有专用 Maven 问题 View 的情况下取得满分。
- H-02、H-03 和 H-05 都能从同一通用接口动态找到入口、调用、Guard、赋值和计算相关正式 Fact。
- 类级与方法级 Endpoint Evidence 已完整组合。
- 固定 Snapshot Token、稳定分页和 `coverage=UNDECLARED` 阻止了混读与错误否定结论。

因此，PV-EXP-001 中“固定 `endpoint_chain` 提前停止”的问题已经被一般化解决，不需要继续增加 Controller→Service→Mapper 专用遍历。

### 6.2 当前主要瓶颈是正式知识构建，不是查询

- H-04 失败不是搜索失败，而是构建配置只发布两个固定 Commit。
- 复杂 Behavior / Business 问题需要参数值、分支、返回、事务、数据库约束和缺失关联行为；当前 Fact Schema 只覆盖方法调用、Operation Mention、少量 Guard 和注释步骤。
- 全量 Artifact 已经保存不等于这些语义已经成为正式知识。
- Agent 能准确发现 Gap，但当前系统没有模型主导、任务驱动的 Knowledge Update 来补齐 Gap。

### 6.3 当前没有证明产品价值

本轮 Software World Model 更慢、调用更多且完成度更低。稳定身份、Snapshot 和 Evidence 追溯已经可用，但在非回归门禁未通过前，不能用这些附加属性抵消核心任务缺失，也不能开始评价重复复用收益。

## 7. 必须保留的资格说明

### 7.1 尚未验证平台内置 Agent

本轮实验组是隔离的真实模型手动组合公开 CLI，验证的是“模型—通用正式知识工具”契约。Demo 内置 Task Execution Agent 和 Answer Review Agent 仍使用固定 View，尚未接入 Knowledge Requirement、固定 Context 和通用 Tool Loop；因此本轮不能被描述为 Web Chat 生产流程已经通过验证。

### 7.2 Knowledge Sufficiency 门禁尚未真正执行

当前数据类型可以表达 Requirement 与 Assessment，但任意非空字符串仍可伪装成正式引用，`AnswerCandidate.assessment_reference` 也是可选的。平台尚未机械验证：引用是否存在于 Assessment Snapshot、是否属于 Fact / Inference、是否在语义上满足对应 Need。该缺口是下一轮 P0，而不是非功能性增强。

### 7.3 Evidence 不能成为隐性源码回答路径

当前很多 `CALLS_OPERATION` Fact 只正式表示“方法包含某个命名调用”，其 Evidence quote 却包含实参和完整表达式。若 Agent 从 quote 推出公式、参数值或控制流，而对应 Fact / Inference 并未正式表达这些语义，就超过了被引用知识的结论范围。

Evidence 可以用于追溯和审核正式知识；从 Evidence 新发现的语义必须先形成 Fact / Inference Candidate、通过 Knowledge Verifier 并发布新 Snapshot，之后才能支持 Answer Claim。否则“只读取 Evidence quote”会成为一种受限但仍然不合规的直接源码路径。本轮内容评分按冻结量表保留，但不能据此宣称所有得分都已通过正式知识蕴含审核。

## 8. 架构调整结论

下一纵向切片的 P0 不再是增加更多预定义 Semantic View，而是实现模型主导的任务驱动 Knowledge Update：

1. Task Execution Agent 从原始问题形成不可变 Knowledge Requirement。
2. 在固定正式 Snapshot 上逐 Need 评估，产生可验证的 Gap。
3. 从 Gap 派生独立 Build Intent；模型在隔离的 Knowledge Update 调查上下文中使用 Connector Tool 和 Artifact。
4. 模型提出带精确 Evidence 锚点和 KnowledgeContext 的 Entity / Fact / Inference Candidate；不能把调查答案直接写入 Answer Candidate。
5. Knowledge Verifier 分别检查来源定位、Fact / Inference 语义范围、冲突、依赖和最低发布结果。
6. 新 Snapshot 发布后销毁调查上下文，重新打开只读正式知识 Context，并对原 Requirement 全量重评。
7. Assessment 的每个 `SATISFIED` 必须机械验证正式引用存在，并由独立语义审核确认引用确实满足充分条件。
8. Answer Review 反向检查 Requirement 完整性、Assessment、Claim 与答案，任何 Evidence 中新发现但未正式化的语义都退回 Knowledge Update。

Connector / Knowledge Update 还必须支持按任务读取任意 Git Commit、父 Commit、Diff 和所需 Artifact，不能继续由固定 `KnowledgeBuildTarget.history_commits` 决定系统能力。

## 9. 后续验证纪律

- H-01 至 H-05 可以用于缺陷回归，但不能再作为下一版本的未见产品验收集。
- 实现模型主导 Knowledge Update 和内置 Agent 门禁后，先用本组做诊断回归，再冻结新的未见问题集。
- 新基线继续使用相同模型、隔离规则与直接 Git Agent 能力下限。
- 只有新基线通过 P0，才开始验证重复查询、跨 Agent 共享、版本更新和跨来源知识带来的额外收益。
