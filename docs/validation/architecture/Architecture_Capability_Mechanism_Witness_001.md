# Software World Model 架构能力机制见证 001

| 元数据 | 值 |
|---|---|
| Document ID | `SWM-ARCH-CAPABILITY-MECHANISM-WITNESS-001` |
| Related Case | `DVR-FORMAL-PATH-CAPABILITY-001` |
| Run Date | 2026-08-05 |
| Status | `PASS — Bounded Application / Engine Mechanism Only` |
| Test | `demo/tests/test_candidate_only_capability_witness.py` |
| Full Regression | `95 / 95 PASS — historical demo suite; not full ACV` |
| Evidence Nature | Non-normative validation evidence |

> 本见证只见证架构方案中的一个有界局部机制能力，不验证真实模型质量，也不把局部通过提升为 `DVR-FORMAL-PATH-CAPABILITY-001` 整体通过。Candidate Proposal 在该见证中由确定性 Contract Driver 产生；验证目标是平台能否正确承载、校验、发布和恢复 Candidate，而不是证明某个真实模型已经能够提出同等 Candidate。

## 1. 验证问题

在禁用既有确定性 Builder 的条件下，当前 Application Services 与 Knowledge Engine 是否能够：

1. 只接收 Candidate Proposal，先发布直接 Evidence 支持的 Fact。
2. 在新的 `UNCHANGED` 更新中，只引用 exact Base Snapshot 已发布 Fact 形成 Inference。
3. 发布后释放来源调查状态、关闭 Source Integration，并由全新 Answer Provider 与独立 Review Provider 只从正式 Snapshot 恢复答案。
4. 对空 Candidate、错误 canonical target、跨目标混合前提和同 Bundle Candidate 前提失败关闭。

该问题检查正式知识路径有没有两阶段承载能力，不检查模型能否在陌生项目中自主发现全部语义。后者属于独立的 Capability Evaluation（CE），不能用本见证的确定性 Candidate 结果替代。

## 2. Fixture 与禁止捷径

测试在每次运行时创建随机名称、随机方法身份和随机内容的双文件 Git 工程，避免实现依赖固定项目名、类名、Commit 或黄金答案。测试注入的两个 Builder 均为 fail-fast；任何调用都会立即使测试失败。

验证使用两个不同 Requirement：

- Direct Fact Need：要求两个来源文件各自形成直接观察 Fact。
- Final Inference Need：要求第二次更新引用 exact Base Fact IDs，形成跨文件 Behavior Inference。

第一阶段不得宣称已经满足最终 Inference Need。第二阶段不得重新读取源码或使用同批 Fact Candidate；发布后的 Answer / Review 阶段不得调用 Source Integration。

## 3. 执行路径

```text
随机 Git Fixture
  → Candidate-only Update A
  → Evidence + Direct Facts
  → Snapshot S1
  → Candidate-only Update B(exact S1 Fact premises)
  → Inference
  → Snapshot S2
  → release Investigation + Source fail-fast
  → fresh formal-only Answer Provider
  → independent Review Provider
```

两个 Publication 都创建独立 Investigation、Candidate Proposal、Admission 和 Snapshot。第二阶段 Build Target 固定允许使用的 Fact IDs；Knowledge Engine 从 exact CURRENT Base 重读并验证它们，Candidate 不能扩大前提集合。

## 4. 正反例结果

| Case | 预期 | 结果 |
|---|---|---|
| 两文件 Direct Fact → Base Fact Inference → formal-only answer | 两次发布，来源关闭后回答与独立审核通过 | `PASS` |
| 空 Candidate 声明覆盖 Direct Fact Need | 不发布，旧 CURRENT 不变 | `PASS` |
| Candidate Facts 属于错误 exact target | 不发布，旧 CURRENT 不变 | `PASS` |
| Inference 混用目标方法和其他方法的 Fact | 语义审核 / target gate 拒绝 | `PASS` |
| Inference 使用同 Bundle Fact Candidate | Proposal 解析失败，不能进入发布 | `PASS` |

上表列出 `5` 类架构机制 Case；它们由 `4` 个 `unittest` 方法承载，其中 exact target 失败方法合并检查错误目标、目标外 extra Fact 与跨目标混合前提。因此专项自动结果记为 `4 tests / 5 listed cases — PASS`，两种计数不得混写为五个测试。执行：

```bash
PYTHONPATH=demo python3 -m unittest discover -s demo/tests -v
```

关闭未授权 extra Fact loophole 后重新执行当时 Demo 测试套件的全量回归：`95 / 95 PASS`，耗时 `52.236s`，结果 `OK`；`python3 -m compileall -q demo/swm_demo demo/tests` 同时通过。该结果不是 ACV-G00～G10 的完整 ACV Demo Run。

## 5. 可以成立的结论

- Candidate-only 模式能够机械排除既有 Structure / Extended Builder 参与语义生产。
- INITIAL / UNCHANGED 所要求的“Fact 先发布、Inference 后引用正式前提”在 Application / Knowledge Engine seam 上可以执行。
- exact Base Fact ID 白名单、same-bundle premise 禁止和 exact behavior target 对齐可以失败关闭。
- Candidate-only Direct Fact 发布要求每个 delta Fact 都落入某个 exact Build Target selector，不能夹带未授权目标知识。
- Answer Provider 与 Reviewer 可以使用不同实例；来源调用路径关闭后，答案仍能只依赖 Snapshot 中的正式 Inference。
- 这些结果支持现有 Formal Knowledge Single Path 与两阶段 Publication 设计，不要求新增顶层模块。

本轮运行使用 Demo 现有的宽运行时知识结构，只见证与 `iter-001.initial.1` 相容的基础发布机制；运行时没有装载或执行候选 `iter-001.initial.2` exact Schema Definition。因此本结果既不能弥补 `iter-001.initial.1` 的静态表达缺口，也不能作为新 Schema 的 ACV-G02 证据。

## 6. 不能成立的结论

- 公开 `TaskExecutionAgent.execute()` 当前只自动触发一次更新；本见证由 Harness 显式编排两次 Application / Engine 调用，不能宣称公开 Agent 已完成多轮 Gap Resolution。
- 第二阶段 exact premise IDs 由 Fixture 选择并注入；尚未证明真实模型能通过正式知识 Tool 自主发现、选择并冻结正确前提。
- Candidate Proposal 由确定性 Contract Driver 产生；尚未证明真实模型在同一 Authorized Input、Tool 与预算边界内能生成等价 Proposal。该质量问题必须由 CE 单独评测。
- 当前 Demo 的 `covered_need_ids` 仍不是 Accepted 详细设计要求的逐 Criterion Support Proof；本见证通过分离两个 Requirement 避免假满足，但没有实现完整 ACV-G04。
- Source Tool Loop、33 项 Direct Claim 表达、Context 融合、篡改矩阵、受控演化、真实 no-tools Provider 和真实模型泛化均未由本见证执行。
- `release Investigation` 证明访问路径隔离，不表示 Artifact Payload 已物理删除；正式 Evidence 仍按既定保留策略独立管理。

因此，本见证只能作为 ACV-G03 / G05 后续正式 Run 的机制前置证据，不能直接改变任何 Gate 状态。Direct Oracle 没有作为本见证的运行输入，且始终只应作为完整 ACV 的外部验收标准；它不是 Software World Model 的第二条运行路径。本见证运行时，`iter-001.initial.1` 的 ACV-G02 状态仍为 `STATIC_PRECHECK_FAIL`；此后 [Formal Mapping Audit 002](Architecture_Capability_Formal_Mapping_Audit_002.md) 已对候选 `iter-001.initial.2` 给出 `33 / 33 SUPPORTED` 的静态结果，但 ACV-G02 运行和完整 Run 继续为 `NOT_RUN`。

## 7. 设计影响

Accepted 详细设计已经规定 Agent 调用次数由任务结果动态决定、Knowledge Update 后重新打开 Session 并重新评估全部 Need，因此公开 Demo 缺少自动两阶段循环是实现 Harness 缺口，不是新的 Architecture / DD 缺口。

后续实施必须满足：

1. Task Execution 通过公开 Application Use Case 执行有界的多轮 `Gap → Update → Rebind → Reassess`，而不是把私有 Helper 固定为一次。
2. 下一轮 Build Intent 只能从新 Session 已读取的 typed formal claims 中选择 exact premise references。
3. 每次更新分别绑定自己的 Gap / Build Objective、Target Coverage、Candidate、Admission 和 Publication；中间 Fact 发布不能冒充最终 Need 已满足。
4. Schema `33 / 33` 静态表达缺口已由 Formal Mapping Audit 002 对候选契约关闭；完整能力验证仍须按 ACV-G00 至 G10 实际运行，不能把静态审计或本机制见证当作运行结果。
