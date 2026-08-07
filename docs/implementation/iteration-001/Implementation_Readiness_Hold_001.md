# Software World Model Iteration 001 实施准备暂停记录 001

| 元数据 | 值 |
|---|---|
| Record ID | `SWM-IMP-READINESS-HOLD-001` |
| Status | `AMENDED — OFFLINE DEVELOPMENT HOLD RELEASED` |
| Effective Date | 2026-08-05 |
| Applies To | `SWM-IMP-ITER-001 / WP-1…WP-7` |
| Historical Trigger | `DVR-FORMAL-PATH-CAPABILITY-001 / Audit 001 / ACV-G02 STATIC_PRECHECK_FAIL` |
| Current ACV-G02 State | `STATIC_MAPPING_INVALIDATED — JWT SLICE CLOSURE IN PROGRESS` |
| Previous Baseline | `SWM-IBM-ITER-001-REV-002` |
| Production Coding | `PAUSED` |
| Amended By | [SWM-IMP-DEV-REENTRY-001](Implementation_Development_Reentry_001.md) |

> 本记录保存2026-08-05暂停决定及其证据，不改写已经冻结的 `SWM-IBM-ITER-001-REV-002`。自2026-08-06起，其“禁止全部生产编码”边界由[离线开发再准入记录 001](Implementation_Development_Reentry_001.md)修订：离线开发已经获准，真实Provider联调、模型Strategy激活和生产发布仍被禁止。

## 1. 暂停原因

[Formal Mapping 静态审计 001](../../validation/architecture/Architecture_Capability_Formal_Mapping_Audit_001.md) 对 H-01 至 H-05 的 33 个实质语义点逐项检查，结果为：

- `SUPPORTED = 2`
- `PARTIAL = 22`
- `UNSUPPORTED = 9`

当前 `iter-001.initial.1` Knowledge Schema 因而不能保存直接来源调查已经能够证明的全部任务语义。继续按旧 Schema 编码，会把已知的信息瓶颈固化进实现；更强模型也不能通过未注册的正式类型弥补该缺口。

该结果首先定位为 Iteration 001 的 Schema / Source Interpretation Profile 充分性缺口。现有证据尚未要求新增顶层模块、改变 Formal Knowledge Single Path，或修改 22 个 Accepted 详细设计主题。

为关闭这一缺口，当前已经形成一组新的能力验证候选契约：

- [Local Git Provider Profile Revision 002](contracts/ITER-001-Local-Git-Provider-Profile-Revision-002.md)，`0.2.0 / Withdrawn Draft`；
- [Foundational Software Semantics Rule Pack](contracts/ITER-001-Foundational-Software-Semantics-Rule-Pack.md)，`0.1.0 / Withdrawn Draft`；
- [INITIAL Knowledge Schema Revision 002](contracts/ITER-001-Initial-Knowledge-Schema-Revision-002.md)，`iter-001.initial.2 / Withdrawn Draft`。

三份候选契约随后继续修改；虽然各草案当前Payload可以单独标识，Provider和Schema仍依赖已撤回Pack的旧摘要，Local Rule I/O等类型也尚未闭合，因此不存在有效的传递契约闭包。[Formal Mapping Audit 002](../../validation/architecture/Architecture_Capability_Formal_Mapping_Audit_002.md) 的历史`33 / 33`结论已经撤回，不能作为开工或能力证据。

当前验证范围已收敛到[JWT Commit 架构能力验证切片 001](../../validation/architecture/Architecture_Capability_Validation_Slice_JWT_001.md)。该切片只负责在正式编码前验证H-04六个Need能否通过真实no-tools模型和Formal Knowledge Single Path完成；它不解除本记录对Iteration 001生产实现的暂停。

[JWT 架构可行性复核 002](../../validation/architecture/Architecture_Feasibility_Review_JWT_002.md) 随后证明 0.1.0 Contract 的 `6 / 6 STATIC SUPPORTED` 不足以授权运行：Requirement 丢失 Criterion Obligation / Joint Constraint、Manifest 无法机械映射到 Rendered Request、Entity 阶段缺失，且十分量表不能证明逐 Claim 守恒。新的 [JWT Formal Contract Revision 002 candidate](contracts/ITER-001-JWT-Validation-Formal-Contract-Revision-002.md) 已用真实 mall Git Object 完成 `13 / 13` 机械 Conformance /机制见证，但未执行 Live Adapter Conformance、真实模型链或重新冻结 Direct Claim Oracle；本 Hold 继续有效。

后续完整 Run 只能依据 [JWT Slice 002 candidate](../../validation/architecture/Architecture_Capability_Validation_Slice_JWT_002.md) 建立新的 exact Manifest；Slice 001 / Contract 0.1.0 只保留历史追溯身份。

该切片复用已冻结Provider 0.1和Base Schema `iter-001.initial.1`，通过[JWT Validation Formal Contract](contracts/ITER-001-JWT-Validation-Formal-Contract.md)增加validation-only类型；Provider Revision 002、Foundational Rule Pack和Schema Revision 002继续作为未冻结研究草案保留，不再成为该切片Demo开工的传递依赖。

## 2. 原暂停边界

以下内容记录本记录生效时的原始边界；当前执行边界以`SWM-IMP-DEV-REENTRY-001`为准。

暂停以下活动：

- WP-1 至 WP-7 的生产实现与生产技术栈冻结。
- 宣布详细设计、实施基线或整体架构能力已经通过。
- 以自由文本 Fact、Evidence Quote、题目专用 Builder、答案阶段源码读取或直接 Agent 旁路补齐缺失语义。

仍允许以下设计验证活动：

- 创建新的 exact Knowledge Schema Definition 与必要的 Source Interpretation Profile 版本。
- 对 Direct Claim Oracle 做逐项 Formal Mapping、独立静态复核和反例审查。
- 修改 `demo/` 中只用于回答已登记设计问题的验证 Harness，并运行回归测试。
- 完善 Conformance Fixture、验证记录和新的 Implementation Baseline 候选。

Demo 代码和通过结果均不自动进入生产实现，也不能替代规范修订。

本 Hold 下的 Demo 只用于验证架构方案是否具备 Candidate 单路径、两阶段 Publication、来源关闭恢复等能力。确定性Contract Driver只能证明机械门禁；当前JWT切片的能力结论必须使用真实no-tools模型完成Source Tool Proposal、知识Candidate、Answer Candidate和独立Review。Demo Harness仍不是未来生产实现路径。

## 3. 原完整解除条件

只有以下条件全部满足，才能创建解除记录并重新判定 WP-1：

1. JWT验证切片的Formal Contract保持exact闭合，Revision 002 的13个Mechanical Conformance Case与no-tools Adapter真实边界全部通过。
2. 完整JWT Capability Run使用真实模型、公共Source Tool Loop和Formal Knowledge Single Path完成六个Need；来源关闭后的回答按同题量表不低于Direct Agent。
   在 Revision 002 生效后，本项还要求 SWM Delivered Claim 与运行前冻结的全部实质 Direct Claim Oracle 按 target、context、modality、条件和限制双向守恒；相同总分不能替代逐 Claim 完整性。
3. 验证没有使用题目专用类型、固定答案、直接来源回答旁路、Candidate同批推理、相关知识冒充充分、Fixture冒充模型能力或未授权来源读取。
4. 根据Demo结论选择首个production纵向切片；该切片实际使用的Schema、Provider、Model、Application与Response Contract在编码前完成类型、摘要、依赖和Conformance冻结。
5. 新的Implementation Baseline Manifest只授权该production切片，固定全部现行契约、文件摘要和Gate；旧`SWM-IBM-ITER-001-REV-002`保持历史可追溯。

H-01至H-05的33项继续用于后续切片和产品能力评测，但不再作为开始首个纵向实现前必须一次性形式化完毕的整包门禁。任何尚未实现的切片仍必须在自身编码前取得同等级设计支持。

解除暂停不代表产品验收。真实模型的 Capability Evaluation、Provider Conformance 和未见项目 Product Holdout 仍按各自门禁独立执行。

## 4. 当前权威结论

截至2026-08-05暂停决定形成时：

- 一般架构：保持 `SWM-ARCH@1.2`，未发现必须修改的反例。
- Accepted 详细设计：保持 `SWM-DBM-ITER-001-REV-002`，未发现必须修改的反例。
- 实施 Schema：`iter-001.initial.1` 保留为冻结历史版本，但已确认不满足当前能力目标。
- 候选契约：`0.2.0` Provider Profile、`0.1.0` Rule Pack 与`iter-001.initial.2` Schema处于修订中，当前摘要依赖与类型闭包未通过复核。
- 静态门禁：Formal Mapping Audit 002 已失效；当前只对JWT验证切片重新建立六个Need的形式映射。
- 架构能力验证：Candidate-only 局部机制见证已通过，但 ACV-G00 至 ACV-G10 的完整 Run 尚未执行。
- 实施准备：当时为`WP-1 Held / Schema Revision and Capability Validation in Progress`。
- 正式编码：当时未开始。当前离线开发状态和仍有效的真实集成限制由`SWM-IMP-DEV-REENTRY-001`管理。
