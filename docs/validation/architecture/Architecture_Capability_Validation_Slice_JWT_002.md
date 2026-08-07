# Software World Model 架构能力验证切片：JWT Commit 影响分析 002

| 元数据 | 值 |
|---|---|
| Document ID | `SWM-ACV-SLICE-JWT-002` |
| Status | `Candidate — Mechanical Conformance Passed; Live Run Not Authorized` |
| Supersedes For New Runs | [SWM-ACV-SLICE-JWT-001](Architecture_Capability_Validation_Slice_JWT_001.md) |
| Target Repository | `https://github.com/macrozheng/mall.git` |
| Target Commit | `dacce5f28dfc1734f2db09668d928d7fac2a3a7a` |
| Exact Parent | `00bd03591cfd91f82ebe48787315eed613754277` |
| Runtime State | `MECHANICAL_WITNESS_PASS / LIVE_CAPABILITY_NOT_RUN` |
| Formal Contract | [Revision 002 candidate](../../implementation/iteration-001/contracts/ITER-001-JWT-Validation-Formal-Contract-Revision-002.md) |
| Correction Evidence | [SWM-ARCH-FEAS-JWT-002](Architecture_Feasibility_Review_JWT_002.md) |
| Production Authorization | `NONE` |

> 本 Revision 保留 001 的真实项目、问题、六个 Need、正式知识单路径和禁止捷径，只修正完整性 Oracle、Requirement、运行前门禁和结果判定。001 与其旧 Manifest 保留为历史输入，不得通过重算摘要继续运行。

## 1. 唯一验证目标

验证：真实 no-tools 模型能否在同一冻结 Git Boundary 内，经

`Requirement Fidelity → canonical BuildTarget → bounded Source Tool Loop → Artifact / Evidence → Entity / Fact / Inference Candidate → independent Review / Admission → Snapshot Publication → per-Obligation Need / Joint Sufficiency → source-closed Answer → independent Answer Review → Authorization / Delivery`

形成与独立 Direct Agent 全部实质 Claim 双向守恒、且没有额外错误的答案。

它不验证 H-01、H-02、H-03、H-05、跨项目泛化、性能、企业安全、全部 24 个详细设计主题或产品价值。

## 2. 冻结 Requirement

### 2.1 本切片的局部编号

| 标识 | 含义 |
|---|---|
| `JWT` | JSON Web Token。本文件用它标识所选的验证场景，不表示平台要实现认证模块。 |
| `H-04` | [产品留出验证基线](../product-value/Product_Value_Holdout_Baseline.md#h-04jwt-迁移提交的语义影响)中的第 4 个题目，即“JWT 迁移提交的语义影响”。 |
| `JWT-NNN` | 本切片的一项 Knowledge Need；例如 `JWT-N04` 是第 4 项知识需求。表格上下文明确时可缩写为 `N04`。 |
| `JWT-NNN-ONN` | 某个 Need 下必须独立证明的 Criterion Obligation；例如 `JWT-N04-O06`。 |
| `JWT-JNN` | 跨多个 Need 的 Joint Knowledge Constraint；例如 `JWT-J01` 要求所有支持使用同一仓库、目标提交、父提交和比较上下文。 |
| `CC-NT-NN` | no-tools Adapter 的第 `NN` 个 Contract Conformance Case；它与 JWT Need 不是同一编号空间。 |
| `ACV-GNN` | Architecture Capability Validation 的第 `NN` 个 Gate；Gate 编号来自[架构能力验证基线](Architecture_Capability_Validation_Baseline.md#7-硬门禁)。 |
| `Revision 001 / 002` | 本验证切片或契约的文档修订身份，不是目标 Git 仓库的 Commit Revision。目标代码版本始终使用完整 Commit ID 表示。 |

`Need`描述必须回答的问题，`Obligation`把一个 Need 拆成可分别失败和审核的证明义务，`Joint Constraint`约束多个 Need 的共同上下文。三者不能用一个总分互相替代。

### 2.2 Requirement 内容

001 的 `JWT-N01…JWT-N06` 保持不变，但每项必须在 Source Operation 前保存：

- 原 question；
- Sufficiency Criterion；
- 不预填答案的 Criterion Obligation Manifest；
- 与其他 Need 的 Joint Knowledge Constraint。

当前 provisional Obligation 维度至少覆盖：

| Need | 必须分别审核的维度 |
|---|---|
| N01 | exact target / unique parent；完整 changed-file enumeration |
| N02 | root version；root dependency-management；security-module direct dependency |
| N03 | token construction API；signing-key conversion；expiration construction / representation |
| N04 | verify / parse order；invalid result；username null；missing / invalid exp；exact comparison boundary；可达性与 library Unknown |
| N05 | accepted / unsupported created representations；strict interval endpoints；original token / re-sign output |
| N06 | new library defaults、old library String-key semantics、payload serialization / parsed Java type 等缺失正式前提；comment / code modality |

本表只约束 Fidelity Reviewer 不得漏掉已知维度，不是最终黄金答案。完整 Direct Claim Oracle 若在运行前发现额外实质维度，必须先发布新的 Requirement Revision；运行后不得增加、删除或弱化 Obligation。

六个 Need 还必须有一个 Joint Constraint，证明所有 Support 使用同一 Repository、Target、Parent 和 Comparison Context。

## 3. Direct Agent 与 Oracle 冻结

Direct Agent 使用同等级基础模型、同一 Source Boundary 和预先冻结的相称预算，直接读取 exact Git 对象。它只在被测运行之外执行。

在任何 SWM Source Operation 前必须冻结：

1. Direct Answer 原文与 Model / Prompt / Tool / Budget / Trace。
2. 独立核对的 Direct Claim Oracle；每项固定 canonical semantic key、target、context、modality、condition、limitation、coverage、source locator / digest 和 materiality。
3. Claim ↔ Need / Obligation 映射，以及 Oracle Manifest Digest。

Direct Answer、Oracle 文本和期望值禁止进入 SWM 的 Manifest、Tool Observation、Artifact、Evidence、Candidate、Snapshot、Assessment、Answer 或 Review。只有最终 Delivery 完成后，独立 Evaluator 才比较 semantic key。

H-04 历史十分量表与 E-004 勘误继续用于辅助回归，不再充当完整性 Oracle。

## 4. Run 前硬门禁

完整 Live Run 只有全部满足才可启动：

1. Revision 002 Contract、Slice、Run Configuration、Harness Source、Prompt / Output Contract 和全部依赖已形成 exact frozen Manifest。
2. 13 项 Mechanical Contract Conformance 在 frozen Harness Source 上通过。
3. [CC-MODEL-NO-TOOLS-001](../../implementation/iteration-001/conformance/CC-MODEL-NO-TOOLS-001.md) 使用真实 Adapter / Provider / exact model 全部 PASS，Result 未 Stale。
4. 七个 Model Role 的 Authorized Input Matrix、实际 Provider Request、Output Contract、Eligibility 与预算均已冻结。
5. Direct Agent / Direct Claim Oracle 已按第 3 节冻结，且从 SWM Runtime 物理和逻辑隔离。
6. validation Store / CURRENT Namespace 与 production Reader / Premise / Root 解析机械隔离。

任一 Gate 缺失时状态保持 `NOT_AUTHORIZED`；确定性 Fixture、Codex CLI Agent Runtime 或人工答案不能补齐。

## 5. Live Run 必经阶段

1. Requirement Generator / Fidelity Reviewer 在无 Source 输入时冻结 Requirement、Obligation 和 Joint。
2. Application Authority 解析 exact target、unique parent 和 BuildTarget。
3. Investigation Planner 只提 Source Tool Proposal；平台授权并执行通用 `resolve / compare / list / search / read`，记录预算和 Coverage。
4. Entity 使用 Base Schema Anchor Contract 构建、审核并先进入 Entity Snapshot；本 validation-only Revision 选择独立阶段以简化前提证明，不使用裸引用或同批 Candidate-local Entity。
5. Fact Proposer 与独立 Knowledge Reviewer 只处理单 Evidence 原子观察和完整 Coverage Fact；Fact 先独立发布。
6. Inference Proposer 只读取 exact Fact Snapshot；独立 Reviewer 审核一个 entity / aspect / relation、限制和 Unknown；Inference 后独立发布。
7. 来源、Artifact Payload、Evidence Content 和 Investigation Session 关闭；新的 Knowledge Use Session 只读取 final Snapshot。
8. Sufficiency Reviewer 对每个 Obligation 和 Joint 形成 exact Support Proof；平台双向聚合。
9. Answer Generator 只读取 Requirement、Assessment 和 final Snapshot；Answer Reviewer 使用新的 Model Call 独立审核。
10. Response Control 要求全部来源侧 attempt / execution count 为 0 后签发 Authorization / Delivery。
11. 外部 Evaluator 才读取 Direct Claim Oracle 并执行逐 Claim 对照。

## 6. PASS 条件

只有以下全部成立才为 `PASS`：

- BuildTarget、Source Coverage、Entity / Fact / Inference Admission、三阶段 Snapshot、Need / Joint Assessment、Answer Review、Isolation Proof、Authorization 和 Delivery 全部合法且可回放。
- 每个 required Obligation 恰有同 final Snapshot 的 Support；无相关但不蕴含、错 target、错 context、错 modality、Coverage 未闭合或 Unknown 隐藏。
- SWM Delivered Claim semantic-key set 与全部 material Direct Claim Oracle 双向相等，`missing=0`、`extra=0`、语义弱化 / 扩张为 0。
- SWM 没有 Direct Agent 未犯的实质错误；错误不能被其他正确 Claim 或总分抵消。
- 逐 Claim 门禁通过后，SWM H-04 辅助量表分数不低于 Direct Agent。
- Answer / Review Session 的 Source、Artifact Payload、Evidence Content、Investigation Attach 的 attempt 和 execution 全为 0。
- validation State 不被 production Reader、CURRENT、Premise、Continuation 或 Root / State 解析。
- 完整 Run Record 固定 actual model / provider / adapter / prompts / outputs / tool trace / artifacts / decisions / snapshots / assessments / delivery / oracle evaluation / usage / duration / cost 和 source identity。

任一条件 `FAIL | INCONCLUSIVE | NOT_RUN` 时，整体不得 PASS。

## 7. 当前结果与下一动作

当前真实项目机械见证：`13 / 13 PASS`。增加 no-tools Adapter 的12类离线机械Oracle和结构边界回归后，全量测试总数为121；其中Provider Echo仍为录制Fixture，不是Live Conformance。它们证明修订后的对象关系、请求闭包和失败关闭机制可实现，不证明真实Provider边界或任何真实模型角色的质量。

当前 Live Adapter Conformance、exact model / Prompt Run Configuration、Direct Claim Oracle 和完整七角色 Run 均为 `NOT_RUN`。因此当前结论为：

**架构机制可实现；真实能力未证明；不得解除 Implementation Hold 或开始 production 开发。**
