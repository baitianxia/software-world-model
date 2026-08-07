# Software World Model 架构能力 Formal Mapping 静态审计 001

| 元数据 | 值 |
|---|---|
| Document ID | `SWM-ARCH-CAPABILITY-FORMAL-MAPPING-AUDIT-001` |
| Related Case | `DVR-FORMAL-PATH-CAPABILITY-001` |
| Audit Date | 2026-08-05 |
| Status | `Completed — ACV-G02 Static Precheck FAIL` |
| Full Run Status | `Not Executed` |
| Direct Claim Source | `PV-HOLDOUT-001 / H-01…H-05` |
| Target Schema | `swm.local-git.software-knowledge / iter-001.initial.1` |
| Evidence Nature | Non-normative validation evidence |

> 本文是架构能力验证的静态审计产物，不修改或替代一般架构、Accepted 详细设计、Knowledge Schema Definition 或实施方案。审计失败可以触发后续正式修订，但本文本身没有规范授权效力。

## 1. 审计问题与结论

本审计逐项检查 [PV-HOLDOUT-001](../product-value/Product_Value_Holdout_Baseline.md) H-01 至 H-05 的 33 个实质评分点，判断它们能否在 [Iteration 001 INITIAL Knowledge Schema](../../implementation/iteration-001/contracts/ITER-001-Initial-Knowledge-Schema.md) 中获得 exact Fact / Inference / Context / Coverage 路径。

静态结果为：

| 结果 | 数量 | ACV-G02 含义 |
|---|---:|---|
| `SUPPORTED` | 2 | 存在完整的正式表达路径 |
| `PARTIAL` | 22 | 只能表达评分点的一部分，不能把对应 Need 判为满足 |
| `UNSUPPORTED` | 9 | 核心命题没有注册的正式表达路径 |
| **总计** | **33** | Claim Preservation 不是 `100%` |

因此 `ACV-G02 语义可表达` 的静态预检结果为 **FAIL**。完整 Demo Run 尚未执行，其余 Gate 不因本审计自动获得结果。

当前确认的是 Iteration 001 Schema / Provider Profile 的充分性缺口。一般架构与 Accepted DD 已经提供类型化多角色 Fact、正式 Inference、封闭否定观察、Context、Coverage、Schema 依赖和版本化推理规则的通用承载边界；本轮没有发现必须新增顶层模块、反转依赖或修改核心认知分层的证据。

## 2. 判定方法

### 2.1 状态

| 状态 | 判定规则 |
|---|---|
| `SUPPORTED` | 评分点的全部实质语义、目标身份、Context、Modality 和 Coverage 均可由当前 exact Schema 的正式类型支持 |
| `PARTIAL` | 当前 Schema 能表达部分来源观察，但遗漏公式、对象绑定、完整性、隐式语义或其他评分所需实质结论 |
| `UNSUPPORTED` | 评分点的核心结论没有当前 Schema 注册的正式类型、Evidence Representation、Context 或 Coverage 路径 |

`PARTIAL` 不计为 ACV-G02 通过。相关但不蕴含、只显示源码位置、只有 Entity、只有 Evidence Quote 或只能返回 Gap 均不能把一个有来源依据的评分点提升为 `SUPPORTED`。

### 2.2 缺口层级

| 标记 | 含义 |
|---|---|
| `ARCH` | 一般架构没有该认知责任、权威对象或扩展边界 |
| `DD` | 一般架构允许，但 Accepted 详细设计没有可实施的通用 Contract |
| `IS` | 一般架构和 Accepted DD 已允许，Iteration 001 exact Schema / Provider Profile 未注册所需类型或规则 |

本审计中的全部 `PARTIAL | UNSUPPORTED` 项均首先归为 `IS`。没有确认 `ARCH` 或 `DD` 缺口；语言 /框架解释规则的 exact provenance 若在后续 Schema 设计中无法由既有 Schema Dependency 与 Inference Rule Contract 承载，再升级为 DD 问题，不能在当前静态审计中预判升级。

### 2.3 当前正式路径缩写

| 缩写 | exact Contract |
|---|---|
| `F-IM` | `swm.fact.interface-mapping@1` |
| `F-ES` | `swm.fact.execution-step@1` |
| `F-DEP` | `swm.fact.dependency-declaration@1` |
| `F-RP` | `swm.fact.revision-parent@1` |
| `F-RC` | `swm.fact.revision-change@1` |
| `F-SS` | `swm.fact.source-statement@1` |
| `I-BF` | `swm.inference.declared-behavior-flow@1` |
| `I-CI` | `swm.inference.change-impact@1` |
| `CTX-GIT` | `swm.version.git-commit@1`，并保留 `swm.time.observation@1` |
| `CTX-Δ` | `CHANGE_COMPARISON` 中分别绑定 `BEFORE | AFTER` 的 exact Commit Context |

Fact 路径还必须通过 `FACT_DIRECT_COVERAGE@1`；Inference 路径必须具有正式 Premise、Structured Argument、Context 构造与反例；任务完整性必须通过 Knowledge Requirement 的 Criterion Obligation 和同一 Session 的 Need Support Proof。下表没有把 Evidence Quote、Entity metadata、查询摘要或 Agent 解释计为正式支持。

## 3. H-01：Maven 内部模块依赖图

| ID | 实质评分点 | 当前 exact Mapping | 状态 | 缺口层级与原因 |
|---|---|---|---|---|
| H01-01 | 列全根 POM 聚合的 7 个模块 | `software-module` Entity 可由 `MAVEN_POM_MODULE_ROOT_V1` 锚定，`CTX-GIT` | `UNSUPPORTED` | `IS`：Entity 只证明 POM 模块身份；没有根项目 `AGGREGATES` Fact 或封闭成员 Coverage，且会同时存在仓库根模块 |
| H01-02 | 区分聚合、dependencyManagement 和实际 dependency | `F-DEP` 只有 owner、component、version、scope | `UNSUPPORTED` | `IS`：POM Observation 与 Fact 均没有 `AGGREGATES | MANAGES_VERSION | DECLARES_DEPENDENCY` 声明角色 |
| H01-03 | 列全 8 条内部直接依赖边 | `F-DEP(ownerModule, dependency-component)`，每项绑定 POM Evidence 与 `CTX-GIT` | `PARTIAL` | `IS`：能够观察声明，但缺少 `dependency-component ↔ software-module` 的来源锚定绑定，不能形成 module→module 边 |
| H01-04 | 给出正确拓扑分层 | 无注册 Inference | `UNSUPPORTED` | `IS`：缺少以封闭节点/边集为前提的通用 topology Inference |
| H01-05 | 给出全部传递可达关系 | 无注册 Inference | `UNSUPPORTED` | `IS`：缺少显式路径与闭包 Coverage 的 relation-closure Inference |
| H01-06 | 确认图中无环并绑定完整 POM 证据 | 当前 Schema 排除否定 Fact，Evidence Representation 不含封闭 Query Observation | `UNSUPPORTED` | `IS`：没有完整节点/边集合、分页终态、Provider completeness 和 acyclicity Proof |

H-01 汇总：`SUPPORTED=0 / PARTIAL=1 / UNSUPPORTED=5`。

## 4. H-02：会员领取优惠券的控制流与一致性边界

| ID | 实质评分点 | 当前 exact Mapping | 状态 | 缺口层级与原因 |
|---|---|---|---|---|
| H02-01 | 入口与当前会员 | `F-IM → F-ES(INVOKE) → I-BF`，全部绑定 `CTX-GIT` | `SUPPORTED` | 无；被调方法语义仍须先作为正式 Behavior 发布 |
| H02-02 | 四个拒绝条件及顺序 | `F-ES(BRANCH_ON / THROW, stepPath) → I-BF` | `SUPPORTED` | 无；条件、调用和拒绝方法必须有完整连续源码 Evidence |
| H02-03 | 成功时写入 Coupon History 字段 | Setter / write 调用可形成 `F-ES` | `PARTIAL` | `IS`：`F-ES` 不同时表达写入目标、RHS、调用参数、字段绑定和对象状态 |
| H02-04 | 16 位领取码的完整计算规则 | 无表达式或 data-flow Fact | `UNSUPPORTED` | `IS`：字符串切片、随机数字、会员 ID 补齐/截取及连接公式均无类型化表示 |
| H02-05 | stock、receiveCount 的精确更新规则 | 条件和 setter 调用可形成 `F-ES` | `PARTIAL` | `IS`：不能表达 `stock-1`、`null→1`、`else +1` 的赋值与数据流 |
| H02-06 | 所有响应结果 | `F-ES(RETURN / THROW / INVOKE) → I-BF` | `PARTIAL` | `IS`：返回参数、异常传播、GlobalExceptionHandler 映射和终止路径 Coverage 不完整 |
| H02-07 | 区分事务原子性与并发隔离 /竞争保证 | 无 annotation、SQL constraint、lock/update 或框架语义路径 | `UNSUPPORTED` | `IS`：无法形式化 Spring 事务适用条件、默认回滚、read-modify-write、唯一约束缺失及“未建立并发保证” |

H-02 汇总：`SUPPORTED=2 / PARTIAL=3 / UNSUPPORTED=2`。

## 5. H-03：购物车促销计算规则

| ID | 实质评分点 | 当前 exact Mapping | 状态 | 缺口层级与原因 |
|---|---|---|---|---|
| H03-01 | 入口、当前会员购物车和 `cartIds` 条件筛选 | `F-IM + F-ES` 可表示入口、调用和部分条件 | `PARTIAL` | `IS`：lambda/filter 参数、集合成员关系和筛选前后数据流丢失 |
| H03-02 | TreeMap 分组与 DAO 促销资料装配 | `F-ES(INVOKE)` 可表示部分调用 | `PARTIAL` | `IS`：collector key、分组结果、批量查询参数/结果绑定和 TreeMap 语义缺失 |
| H03-03 | promotionType=1 完整规则 | 分支与 setter 调用可形成 `F-ES` | `PARTIAL` | `IS`：SKU 促销价覆盖、原价来源及 `原价-促销价` 公式不可表达 |
| H03-04 | promotionType=3 完整规则 | 分支、调用和词法顺序可形成 `F-ES / I-BF` | `PARTIAL` | `IS`：跨 SKU 聚合、count 降序最高档选择、折扣公式和输出价格继承不可表达 |
| H03-05 | promotionType=4 完整规则 | 分支、调用和词法顺序可形成 `F-ES / I-BF` | `PARTIAL` | `IS`：SPU 总额、比例分摊、`HALF_EVEN` 及输出字段继承不可表达 |
| H03-06 | 默认分支与公共字段 | 分支和 setter 调用可形成 `F-ES` | `PARTIAL` | `IS`：`reduceAmount=0` 参数、`stock-lockStock`、积分/成长值来源绑定缺失 |
| H03-07 | 输出顺序与 Product / SKU 缺失行为 | 无完整正式路径 | `UNSUPPORTED` | `IS`：缺少 TreeMap 排序、组内次序保持、隐式 null 解引用异常和路径完备性规则 |

H-03 汇总：`SUPPORTED=0 / PARTIAL=6 / UNSUPPORTED=1`。

## 6. H-04：JWT 迁移提交的语义影响

| ID | 实质评分点 | 当前 exact Mapping | 状态 | 缺口层级与原因 |
|---|---|---|---|---|
| H04-01 | 父提交与恰好三个修改文件 | `F-RP + F-RC`，绑定 `CTX-Δ` | `PARTIAL` | 父提交和三个单项变化可表达；`IS` 缺少“完整 changed set 恰好为三项”的正式 Coverage 命题 |
| H04-02 | JJWT 版本、management 和直接依赖移除 | before/after `F-DEP + F-RC` | `PARTIAL` | `IS`：缺少 management/actual 角色、元素级 Diff 和封闭 absence，不能正式断言“移除” |
| H04-03 | JWT 生成、Secret bytes 和 exp 变化 | before/after `F-ES → I-CI` | `PARTIAL` | `IS`：调用参数、Secret→UTF-8 bytes、Date→millisecond long 和表达式绑定缺失 |
| H04-04 | 解析/验签、过期、校验与异常变化 | `F-ES(BRANCH_ON / RETURN / INVOKE) → I-CI` | `PARTIAL` | `IS`：调用先后依赖、Map 转换、异常传播、null 防护和 API 语义没有完整正式前提 |
| H04-05 | Long / Date 刷新和 30 分钟规则 | 分支、调用和词法步骤可表达 | `PARTIAL` | `IS`：类型分支、时间算术、返回原 Token 与重新签发的数据流缺失 |
| H04-06 | 默认算法等证据边界 | `F-SS` 保留旧注释 Modality；新调用可形成 `F-ES` | `PARTIAL` | `IS`：没有封闭仓库 Coverage 或 exact Hutool 语义规则，不能证明默认算法；正确结果应保持 Unknown |

H-04 汇总：`SUPPORTED=0 / PARTIAL=6 / UNSUPPORTED=0`。

Local Git Profile 已支持 exact 任意 Commit、父提交和文件级 Diff。本题暴露的是从“文件发生变化”到“依赖、控制流、数据流和行为语义如何变化”的通用正式表达缺口，不是预编码 Commit 限制。

## 7. H-05：listCart 优惠券可用性与边界反例

| ID | 实质评分点 | 当前 exact Mapping | 状态 | 缺口层级与原因 |
|---|---|---|---|---|
| H05-01 | 当前会员且 `use_status=0` 的数据范围 | Java 调用可形成 `F-ES` | `PARTIAL` | `IS`：MyBatis XML 查询谓词、表/列和 Mapper→SQL 绑定没有正式类型 |
| H05-02 | 金额公式与三种 useType 范围 | 分支和调用可形成 `F-ES` | `PARTIAL` | `IS`：算术表达式、集合筛选、关联关系和聚合数据流缺失 |
| H05-03 | 三个分支的精确谓词 | 条件可以成为 `F-ES` Typed Literal | `PARTIAL` | `IS`：total 的来源闭包及 `intValue`、BigDecimal、Date API 语义缺失 |
| H05-04 | 至少两个有效边界反例 | 无公式求值 Inference | `UNSUPPORTED` | `IS`：无法以正式表达式、具体输入、版本化求值规则和结果形成 Counterexample Argument |
| H05-05 | endTime 严格边界及未检查 startTime | `now.before(endTime)` 条件可成为 `F-ES` | `PARTIAL` | `IS`：严格 `<` 需要 Java API Rule；“未检查 startTime”需要闭合方法 control/data-flow Coverage |
| H05-06 | 未识别 useType、请求 type 和 null 分区 | 分支可形成 `F-ES` | `PARTIAL` | `IS`：路径穷尽、未知值去向和 null 隐式 NPE 没有正式规则 |
| H05-07 | 注释与代码证据边界 | `F-SS` 与 CODE Observation Modality 可以分离 | `PARTIAL` | Modality 基础已存在；`IS` 中实现行为、Coverage 和反例仍不完整，不能只凭注释补写代码语义 |

H-05 汇总：`SUPPORTED=0 / PARTIAL=6 / UNSUPPORTED=1`。

## 8. 总体汇总与 Gate 判定

| 题目 | SUPPORTED | PARTIAL | UNSUPPORTED | 合计 |
|---|---:|---:|---:|---:|
| H-01 | 0 | 1 | 5 | 6 |
| H-02 | 2 | 3 | 2 | 7 |
| H-03 | 0 | 6 | 1 | 7 |
| H-04 | 0 | 6 | 0 | 6 |
| H-05 | 0 | 6 | 1 | 7 |
| **总计** | **2** | **22** | **9** | **33** |

[架构能力验证基线](Architecture_Capability_Validation_Baseline.md) 要求每个实质 Direct Claim 都具有同 Context / Modality 的正式支持闭包，Claim Preservation 为 `100%`。本审计只有 `2 / 33` 项达到完整 Mapping；`PARTIAL` 不能形成 SATISFIED Need。因此：

`ACV-G02 = STATIC_PRECHECK_FAIL`

这是静态、确定性的类型闭包失败，不需要等待具体模型运行才能成立。更强模型不能使用未注册 Type，也不能通过 Evidence Quote、自由文本 Fact 或答案阶段源码读取补齐。

## 9. 缺口层级

### 9.1 一般架构：未确认缺口

[一般架构](../../architecture/Software_World_Model_Architecture_Baseline.md) 已规定：

- Fact / Inference 不受图三元组限制。
- Knowledge Schema 可以版本化扩展。
- 生产答案只能使用已发布正式知识。
- Coverage、Context、独立准入、Snapshot 和审核分别承担稳定责任。

本审计没有发现需要新增顶层模块、平行知识体系或直接来源回答路径的证据。

### 9.2 Accepted DD：未确认缺口

- [Fact DD](../../detailed-design/topics/DD-KNW-FACT.md) 已允许多角色关系、条件、量词、调用参数、数据库复合约束和具有封闭观察能力的否定 Fact。
- [Inference DD](../../detailed-design/topics/DD-KNW-INFERENCE-CONFLICT.md) 已允许有界逻辑、条件流程、比较、因果方向、版本化 Rule 和结构化 Argument。
- [Evidence DD](../../detailed-design/topics/DD-KNW-EVIDENCE.md) 已定义固化 Query Observation Artifact 所需的封闭范围、读取一致性、分页终态和 Provider 完整性能力。
- [Knowledge Use DD](../../detailed-design/topics/DD-APP-KNOWLEDGE-USE.md) 已定义枚举 Coverage、Criterion Obligation、Counterexample、Unknown 和逐 Need Support Proof。

Inference 必须等待所需 Fact 先发布到 Base Snapshot，可能增加更新轮次，但不降低可表达性。

### 9.3 Iteration 001 Schema：确认缺口

当前 Schema 只注册 9 类 Fact、5 类 Inference、有限 Entity Kind 和四类 Git Evidence Representation，并明确排除否定 Fact、开放世界完整性、数据库字段、Runtime 事实等能力。它自身要求 Product Adequacy 不足时创建新的 Schema Definition，不能把缺失语义塞入自由字段。

语言 /框架解释规则目前归为缺失的 Schema Dependency / Inference Rule。若后续证明 Accepted DD 的 exact Rule、Dependency 和 Provenance Contract 无法表达该责任，再单独登记 DD 验证问题；本审计不提前扩大结论。

## 10. 最小通用 Schema 修订方向

修订必须创建新的 exact Schema Definition，不原地修改 `iter-001.initial.1`，并避免 Maven 图、JWT、优惠券或促销题目专用 Type。

### 10.1 Build declaration 与通用图推理

- 注册 `AGGREGATES | MANAGES_VERSION | DECLARES_DEPENDENCY` 等声明角色。
- 建立 `software-module ↔ dependency-component` 的来源锚定绑定。
- 注册通用 relation-closure Inference，保存显式路径、拓扑层、循环判断和闭合节点/边 Coverage。

### 10.2 Program Semantics Core

- 将程序观察拆为类型化 control-flow、data-flow、state-effect、exception-flow 和 annotation-application Fact。
- 注册规范 Program Expression Value Object，覆盖 operator、operand、调用参数/结果、lvalue/rvalue、类型转换、集合操作、rounding mode、单位和精度。
- 方法调用名称、公式、字段赋值和条件不能降级为自然语言摘要。

### 10.3 封闭观察与有界否定

- 为 Local Git 注册 Query Observation Artifact / Evidence，固定 selector、exact Revision、范围、分页终态、返回数量和 Provider completeness。
- 注册 scoped absence / closed-set Fact 或 Inference。
- “无唯一约束”“未读取 startTime”“图中无环”只能在确切封闭范围内成立，不能外推为全局不存在。

### 10.4 仓库内 SQL 与 Mapper 声明

- 增加 source-anchored table、column、constraint、SQL statement 和 Mapper operation Entity / Fact。
- 这些对象只表示 Git 中 SQL / Mapper 文件声明的结构，不伪装成运行数据库状态。

### 10.5 版本化语言与框架解释规则

- 用 exact Schema Dependency / Interpretation Rule 表达 Java、Maven、Spring、BigDecimal、Date、TreeMap 等稳定语义。
- 推理绑定依赖版本、配置、调用形态和适用前提；无法证明时保持 Unknown。
- Hutool 默认算法没有正式规则或来源时不得推断；旧注释只保留 `SOURCE_DECLARED` Modality。

### 10.6 Guarantee、Limitation 与 Counterexample

- 注册通用 `execution-guarantee / guarantee-limitation` Inference，区分事务原子性、隔离、竞争保护和“当前来源未建立保证”。
- 注册 typed counterexample Inference，以正式公式、输入、求值步骤和结果支持边界反例。
- “没有证明并发安全”不能被改写为“并发一定出错”。

### 10.7 任意 Revision 的语义 Delta

- 增加 symbol、declaration、expression 粒度的 before/after Formal Mapping。
- 注册通用 semantic-change Inference，按 `DEPENDENCY | INTERFACE | CONTROL_FLOW | DATA_FLOW | STATE_EFFECT | CONFIGURATION` 输出独立结论。
- 枚举 Need 必须具有 changed-set 与 requested-aspect Coverage；一条宽泛 `change-impact` 文本不能宣称语义影响完整。

## 11. 处置与重新进入条件

本审计形成以下验证处置，不直接修改规范：

1. 暂停 WP-1 正式编码；允许继续进行新 Schema Definition、Formal Mapping、Fixture 和有界验证 Demo 工作。
2. 新 Schema 必须对本审计 33 项逐一给出 exact Mapping，并通过独立静态复核；不得删除 Oracle Item 或弱化评分点。
3. 若新 Schema 引入不兼容定义，按治理流程形成新的 Definition Digest、实施基线修订和必要设计追溯，不能覆盖已冻结文件。
4. 静态复核达到 `33 / 33 SUPPORTED` 后，ACV-G02 只恢复为“可执行候选”，不能仅凭文档自动记为 PASS。
5. 随后执行完整 `DVR-FORMAL-PATH-CAPABILITY-001`；只有真实 Candidate、Admission、Publication、来源关闭恢复、复用、Context 和审核 Gate 全部通过，才能解除架构能力验证阻塞。

该处置不改变 [PV-HOLDOUT-001 执行记录](../product-value/Product_Value_Holdout_Run_001.md) 的 `33.75 / 50` 产品失败结论，也不能替代未来使用真实模型和未见项目的新 Product Holdout。
