# Software World Model 架构可行性复核：JWT 正式知识单路径 002

| 元数据 | 值 |
|---|---|
| Record ID | `SWM-ARCH-FEAS-JWT-002` |
| Date | 2026-08-05 |
| Status | `COMPLETED — MECHANISM FEASIBLE; CAPABILITY NOT PROVEN; DEVELOPMENT NOT AUTHORIZED` |
| Target Repository | `validation-projects/mall` / `macrozheng/mall` |
| Target Commit | `dacce5f28dfc1734f2db09668d928d7fac2a3a7a` |
| Parent | `00bd03591cfd91f82ebe48787315eed613754277` |
| Architecture | `SWM-ARCH@1.2` |
| Reviewed Contract | `SWM-ITER-001-JWT-VALIDATION-FORMAL-CONTRACT@0.1.0` |
| Corrected Candidate | [Revision 002 / 0.2.0-candidate](../../implementation/iteration-001/contracts/ITER-001-JWT-Validation-Formal-Contract-Revision-002.md) |
| Corrected Slice | [SWM-ACV-SLICE-JWT-002](Architecture_Capability_Validation_Slice_JWT_002.md) |
| Harness Source Manifest | [Architecture_Feasibility_Harness_Source_Manifest_002.sha256](Architecture_Feasibility_Harness_Source_Manifest_002.sha256) |
| Production Authorization | `NONE` |

## 1. 验证问题与判定边界

本次复核只回答：

1. 真实工程上的正式知识构建、审核、发布、来源关闭回答链路是否在数据结构和控制机制上可实现。
2. 现有架构和 JWT 详细 Contract 是否存在使“至少和直接读代码 Agent 同样正确、完整”无法被证明的缺陷。
3. 修正后能否取得足够证据授权进入 production 开发。

本次不追求生产代码质量，也不以测试数量、静态映射或人工写出的正确答案替代真实模型能力。确定性 Harness 只能证明机制承载能力；只有真实 no-tools 模型完成完整 Run 并逐 Claim 守恒，才能证明目标能力。

## 2. 输入真实性与基线

独立核对结果：

- `validation-projects/mall` 是完整 Git Repository，HEAD 为 `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`；验证读取始终使用 exact Git Object，不读取 mutable worktree。
- Target Object 存在且类型为 commit，唯一 Parent 为 `00bd03591cfd91f82ebe48787315eed613754277`。
- `git diff-tree` 的完整 terminal changeset 恰有 3 个 `MODIFIED` 成员，byte-order 为：
  - `mall-security/pom.xml`
  - `mall-security/src/main/java/com/macro/mall/security/util/JwtTokenUtil.java`
  - `pom.xml`
- 当前工作区外层没有 `.git`，所以无法诚实记录 Harness implementation commit；修订 Contract 增加 content-manifest source identity。这个环境事实不改变被测 `mall` Git 输入的真实性。
- 旧 Demo 回归在修改前实跑 `95 tests / 47.800s / OK`。

冻结文档文件摘要在复核开始时与 `SWM-DEMO-BASELINE-JWT-001` 一致；后续设计修订有意使旧 Manifest 对新 Run 不再适用，旧文件本身未改写。

## 3. 发现与根因

### F-01 — Requirement 失去 Criterion 与 Obligation

**分类：详细 Contract 设计缺陷；系统性。严重级别：Blocker。**

`DD-APP-KNOWLEDGE-USE@0.1.0` 明确要求每个 Need 保存 Sufficiency Criterion、不可变 Criterion Obligation Manifest，并对可独立失败的断言拆分或形成 Joint Constraint。JWT Contract 0.1.0 的 `RequirementNeedCore` 只有 question 与 required flag；`NeedSupportBinding` 也只要求一个非空正式引用列表。

结果是：只要模型找到一条同主题知识，六个 Need 都可能被判 `SATISFIED`，即使漏掉 Need 内的边界、枚举项或 Unknown。这不是实现遗漏，而是 Contract 无法表达审核责任。

**修正：** Revision 002 恢复 Sufficiency Criterion、Criterion Obligation、Joint Constraint、逐 Obligation Support Role 和双向集合门禁。

### F-02 — 总分比较不能证明逐 Claim 完整性

**分类：验证设计缺陷；系统性。严重级别：Blocker。**

JWT Slice 只要求按 H-04 十分量表不低于 Direct Agent。相同分数可能来自不同遗漏，且一个错误不能可靠地由粗粒度分项暴露。直接源码复核还发现冻结黄金要点没有枚举严格过期边界、`created` 不支持类型、严格 30 分钟端点、dead private helper 和库行为 Unknown 等可独立裁决项。

**修正：** 产品基线增加 E-004 勘误；Revision 002 要求完整 Run 前重新执行 Direct Agent，冻结外部 Direct Claim Oracle，并对 Delivered Claim semantic-key set 做双向 `100%` 守恒。十分量表降为辅助指标。

### F-03 — Manifest 与 Provider Request 无法机械双向证明

**分类：详细 Contract 设计缺陷；系统性。严重级别：Blocker。**

0.1.0 的 Manifest Items 按 digest 排序，但 `RenderedMessage` 只保存 role 和 bytes，没有 Manifest Item Digest 或 Rendering Step Reference；Prompt 指令也只由 Prompt Contract Ref 间接出现。由现有对象不能重建“每个授权 Item 恰好进入一次请求且没有额外输入”。

**修正：** Revision 002 增加 `PROMPT_INSTRUCTION`、`OUTPUT_CONTRACT`、`RenderedInputItem` 和一对一 Rendering closure；Request Body 与 pre-dispatch Receipt Digest 逐字绑定。

### F-04 — Entity 前置条件没有进入运行拓扑

**分类：详细 Contract 设计缺陷；切片系统性。严重级别：High。**

0.1.0 要求所有 Fact Entity Term 在 Fact Attempt 开始时已经是正式 Entity，但完整摘要拓扑从 Tool 直接跳到 Fact Proposal，没有 Entity Materialization、Resolution、Admission 或 Snapshot。Harness 无法决定 source-unit、revision、module 和 symbol 从何获得正式引用。

**修正：** Revision 002 显式增加复用 Base Schema Anchor Contract 的 Entity Bootstrap Manifest、Admission 和 Entity Snapshot；执行顺序固定为 Entity Snapshot → Fact Snapshot → Inference Snapshot。

### F-05 — Mechanical Request 检查与 Live Provider Conformance 混淆

**分类：验证分层缺陷；系统性。严重级别：Blocker。**

本地测试可以证明 Envelope allowlist 和失败关闭，但不能证明真实 Provider 接受该字段组合、实际 dispatch body 与 Receipt 相等、返回模型身份合格，或 Provider Project 没有隐藏会话/附件/Tool 通道。当前只有带工具的 Codex CLI；仓库文档已经正确指出它不是 no-tools Provider。环境中也没有可用于直接 Responses API Run 的 API credential 或已实现 Adapter。

官方 Responses API 当前仍把 Tool 能力放在请求 `tools` 中、支持 `store:false` 和 Structured Outputs；这说明所选直接 HTTPS 方向可实现，但不能替代真实 [CC-MODEL-NO-TOOLS-001](../../implementation/iteration-001/conformance/CC-MODEL-NO-TOOLS-001.md)。

**修正：** Revision 002 把 Mechanical Contract Conformance 与 Live Adapter Conformance 分开；Capability Run Boundary 必须引用后者的真实 PASS Result。

### F-06 — 来源关闭证明遗漏“访问尝试”

**分类：Response Control Contract 缺陷；切片系统性。严重级别：High。**

0.1.0 只要求 Source Operation、Artifact Payload Read 和 Evidence Content Read 的完成计数为零。若 Answer Agent 尝试访问来源但被权限层拒绝，内容虽然没有泄露，该 Answer Attempt 已违反角色输入和控制流，仍可能因完成计数为零获得放行。

**修正：** Revision 002 分别记录 attempt / executed，并对 Source、Artifact、Evidence 和 Investigation Attach 的所有 attempt 要求为零。

### F-07 — 实验实现身份假设外层一定有 Git

**分类：可复现性 Contract 缺陷；环境相关但一般可发生。严重级别：Medium。**

现有 Run 记录要求 implementation commit，而当前分发工作区没有外层 `.git`。伪造 Commit 或省略身份都会使结果不可重放。

**修正：** validation-only Run Source Ref 使用 `CLEAN_GIT_SOURCE | CONTENT_MANIFEST_SOURCE` closed union；production Implementation Baseline 仍要求受控源码仓库。

## 4. 可执行纠偏与验证结果

新增通用 validation-only Harness：

- `demo/swm_demo/formal_validation.py`
- `demo/tests/test_formal_validation.py`

它没有按 H-04、JWT、文件名、类名或黄金答案建立生产 Builder / Predicate / 查询分支。通用模块实现 closed Requirement / Obligation、BuildTarget、Manifest Rendering、no-tools Request allowlist、Artifact / Evidence、Entity / Fact / Inference 分阶段 Publication、Need / Joint Assessment、Answer Authorization、validation / production Reader 隔离、Digest 和 DAG 门禁。真实项目实例和 provisional 答案只存在于测试 Fixture。

执行命令：

```bash
PYTHONPATH=demo python3 -m unittest demo.tests.test_formal_validation -v
```

实际结果：`13 tests / 0.180s / OK`。

| Case | 结果 | 证明边界 |
|---|---|---|
| 01 exact BuildTarget | PASS | full SHA、唯一 Parent、六 Need 与预算可构造；短 SHA、错 Parent、缺 Need 失败 |
| 02 Manifest closure | PASS | Item ↔ Rendered Input 一对一；Answer Source Observation 拒绝 |
| 03 Request / Receipt | PASS | allowlist、空 Tool、Live CC Ref、实际 Body Digest 本地门禁；不是 Live Provider PASS |
| 04 atomic Fact | PASS | 单 Evidence 直接 Term 通过；库默认语义进入 Fact 失败 |
| 05 closed Coverage | PASS | 三文件完整 changeset 与零 literal selection；漏项、partial、nonterminal 失败 |
| 06 Publication order | PASS | Entity → Fact → Inference 三阶段；Fact 无 Entity、同批 Inference 失败 |
| 07 atomic Inference | PASS | 单 entity / aspect / relation 通过；宽泛 History 失败 |
| 08 bounded Unknown | PASS | Boundary + Missing Premise 必需；具体默认算法不能无前提形成 |
| 09 Sufficiency | PASS | 每 Obligation、同 Snapshot、全部 Need 与 Joint 双向覆盖 |
| 10 Answer isolation | PASS | 任一 Source Operation attempt 阻止 Authorization |
| 11 Store isolation | PASS | production Reader 拒绝 validation Snapshot |
| 12 Digest DAG | PASS | 字段篡改和引用环失败 |
| 13 real-project witness | PASS | exact Git 来源上完成 Entity / Fact / Inference Publication、20 个 provisional Obligation、来源关闭答案和双向 provisional Claim 对照 |

随后执行全量回归：`108 tests / 47.905s / OK`；新增 Harness 没有破坏旧 95 项门禁。

## 5. Case 13 能证明与不能证明的内容

能证明：

- exact Commit / Parent / 三文件范围可由只读公共 Git 操作取得。
- 直接源码原子观察、完整零匹配、Unknown、严格边界等语义具有 typed 承载空间。
- Entity、Fact、Inference 分阶段发布与 exact Snapshot premise 可执行。
- 在 Provider 对象关闭后，可以只从 final Snapshot 完成逐 Obligation Assessment、Answer Support、Authorization 和 Delivery Digest。
- validation Snapshot 不会被 production Reader 解析。

不能证明：

- 真实模型会自己规划正确 Tool Loop、形成完整 Candidate、独立审核或生成答案。
- provisional 20 个 Obligation 已经等于完整 Direct Agent Claim 集。
- 本地 `IsolationReceipt.issue` 等于真实 Provider `CC-MODEL-NO-TOOLS-001` PASS。
- Answer Fixture 的正确文本是模型能力；它只是验证 Answer Support / Response Control 的不可信输入。
- 单个 mall Commit 能证明跨项目泛化、产品价值或成本优势。

因此 Case 13 是 `mechanism feasibility witness`，不是 `JWT Capability Run`。

## 6. 架构与详细设计可实现性判断

| 层级 | 判断 | 依据 |
|---|---|---|
| 概要架构 `SWM-ARCH@1.2` | 未发现反例；核心 Formal Knowledge Single Path 可保留 | 缺陷都能在 validation Contract / Requirement / Response 证明对象内修正，不需要新增顶层模块或双路径 |
| Accepted 详细设计主题 | 总体可实现；`DD-APP-KNOWLEDGE-USE` 原设计反而提供了正确的 Obligation / Joint 约束 | JWT Contract 0.1.0 没有忠实投影上游 DD；不是 DD 本身缺失该机制 |
| JWT Formal Contract 0.1.0 | 不可作为 Capability Run 基线 | F-01 至 F-06 存在 Blocker / High 缺陷 |
| JWT Revision 002 candidate | 机械机制可实现，仍未冻结、未 Live Conformance | 13/13 新 Case 通过；真实模型链与 Direct Oracle 未运行 |
| Production Implementation Baseline | 不具备准入条件 | Live Adapter、真实模型 Run、逐 Claim Oracle 和新 Baseline Manifest 均缺失 |

复杂度风险仍然存在：typed Candidate 与逐 Obligation Support 会增加存储、模型调用和审核成本。本次没有性能 / 成本数据，不能断言生产经济性；但没有发现不可实现的循环依赖或必须绕开正式知识链的语义。

## 7. 最终复验与开发准入

已完成以下实际命令并记录真实输出：

```bash
PYTHONPATH=demo python3 -m unittest demo.tests.test_formal_validation -v
PYTHONPATH=demo python3 -m unittest discover -s demo/tests -v
```

- 专项：`13 tests / 0.180s / OK`。
- 全量：`108 tests / 47.905s / OK`。
- Python 编译检查：`formal_validation.py` 与全体 `demo/swm_demo/*.py`、`demo/tests/*.py` 均通过。
- Harness Source Manifest 固定两个运行实现文件的 byte length 与 SHA-256；外层没有 `.git`，没有伪造 implementation commit。

开发准入硬条件仍未满足：

1. Revision 002 尚是 candidate，未形成 exact frozen Payload / Demo Manifest。
2. `CC-MODEL-NO-TOOLS-001` 仍为 `Defined — Not Executed`，没有 Adapter Implementation、API credential、Provider Project Configuration 或 exact eligible model。
3. 没有重新执行并冻结 Direct Agent Answer / Direct Claim Oracle。
4. 没有真实 Investigation Planner、Fact / Inference Proposer、Knowledge Reviewer、Sufficiency Reviewer、Answer Generator、Answer Reviewer 的完整 ModelExecutionRecord。
5. 没有真实 Tool 预算、Token / duration / cost、Artifact / Candidate / Admission / Snapshot / Assessment / Delivery Result 清单。

## 8. 明确结论

**架构方向可实现，修正后的正式对象链机械上可以闭合；但“Software World Model 已经通过真实构建、审核、发布和回答链路达到直接读代码 Agent 的正确性与完整性”尚未得到证明。当前不能进入 production 开发。**

允许的下一步只有：冻结 Revision 002 与新的 Run Configuration，实现并真实运行 no-tools Adapter Conformance，重新建立 Direct Claim Oracle，然后执行一次完整 JWT Capability Run。只有逐 Claim 双向守恒、无实质错误、来源关闭、全部真实 Reviewer 与 Delivery Gate 同时 PASS，才能重新评估 Iteration 001 开发准入。
