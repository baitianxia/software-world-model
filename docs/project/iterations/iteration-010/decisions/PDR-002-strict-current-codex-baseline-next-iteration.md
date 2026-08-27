---
id: ITER-010-PDR-002
kind: project-decision
status: accepted
authority: project-decision
owners: [product, project, architecture, quality]
depends_on: [ITER-010-PDR-001, SYS-PRODUCT-SUCCESS, SYS-QUALITY-ACCEPTANCE, PROJECT-GOVERNANCE-VERIFICATION]
code: []
tests: []
iteration: ITER-010
decision: NEXT_NEW_ITERATION_REQUIRES_STRICT_CURRENT_CODEX_QUALITY_SUPERIORITY
decision_ref: codex-user-message:sha256:47f61813d7c05e607a63482d1ec443c5893c6c01a41d0005a19c241f79c921b5
effective_scope: first-new-product-iteration-after-iter-010-and-later
coding_input: false
---

# PDR-002：下一轮起必须在答案质量上严格超过当前 Codex

## Context and evidence

项目过去虽多次声明要与成熟源码 Agent 对照，但现行规则仍允许把正式比较推迟到工程夯实阶段，也允许答案质量打平后用成本、时延或复用
指标证明“正向价值”。ITER-010 的成熟 Agent 对照也尚未执行。因此，已有同题比较设计不能证明真实产品已经优于用户可直接使用的强
Agent。

用户以 `codex-user-message:sha256:47f61813d7c05e607a63482d1ec443c5893c6c01a41d0005a19c241f79c921b5`
明确决定：从下一轮迭代开始，软件世界模型系统的最低产品标准是超过 Agent。

## Decision

从 ITER-010 形成终态后新建的第一轮产品迭代开始，执行以下强制规则。按现有编号顺序，该轮应为 `ITER-012`；本决定不创建或授权
ITER-012，也不复活执行前已作废的 ITER-011。

1. **当前 Codex 是强外部基线，不是标准答案或裁判。** 对照使用运行时实际可用的当前 Codex 正常工程工作方式，并冻结客户端版本与
   二进制摘要、实际模型、reasoning effort、工具、权限、Source scope、工程 exact revision、问题原文、输出约束和运行时间。任一关键
   身份漂移都必须重新生成基线。
2. **事实只来自同一精确工程证据。** Codex 输出和系统输出都只是候选答案；Oracle 是原问题与授权 exact revision 上可核验的源码、
   仓库文档、配置和测试证据。双方都可能失败。
3. **答案相互隔离并盲评。** Codex 对每题使用全新独立任务，不能读取本项目对话、世界模型产物、系统答案或既有裁决；其答案先密封，
   系统在不可见该答案的条件下生成并密封自己的答案。独立评测方随机匿名化两份答案，在不知道来源的条件下根据原问题和精确证据裁决；
   评测方不得参与任一答案生成。
4. **首次持续 Web Alpha 就比较，不新增前置阶段。** 首个可重复启动、固定本机地址、同会话自由提问的 Alpha 使用至少三条小而异质的
   同题输入：一条原失败题，另外至少两条相邻或异质问题；后两条中至少一条必须在产品冻结后由现场提出。比较是 Alpha 是否进入夯实阶段的阻断 Case，
   不是延后体验的独立 Slice。
5. **“超过”只按答案质量成立。** 系统先独立满足零重大事实错误、零物质遗漏、零无据实质结论、边界正确、重要结论引用可核验等绝对
   门槛；再要求每题答案质量不低于 Codex，且预提交盲评量表上的总体答案质量差值严格大于零。全体打平、任一物质性逐题退步、双方失败、
   无法裁决或盲化失效均为 `FAIL`。报告必须对冻结的全部问题逐题完成并分类，分类计数总和与冻结题数不一致时无效。成本、时延、调用数、
   缓存或复用只作次级报告，不能把质量打平或退步改判为 `PASS`。
6. **Alpha 与正式验收都执行。** Alpha 用小样本快速判向；后续 hidden/跨工程正式套件在产品冻结后重复同一严格规则。Alpha 结果不能
   替代最终 held-out 结果。
7. **产品基线与因果消融分开。** “系统 vs 当前 Codex”回答用户为何不用现成 Agent；“完整 World Model Cognition vs
   locator-only/empty”在相同系统模型、链路和预算下证明世界模型的独立贡献。不得再把两者混成同一组三臂等预算对照。

比较失败默认暂停并在同一 Slice `REWORK`；单次落后不能自动推导核心架构失效或新建迭代。独立技术评测先给出质量结论，用户继续只对
产品方向和是否接受作决定，不承担源码真值裁判职责。

> Current amendment：`ITER-010-PDR-006` 已将上述“默认暂停”收窄为 active same-Slice `REWORK`。现有本地开发授权覆盖修复时继续开发；
> 只有 scope/Owner 变化、用户明确暂停或本地授权失效时才进入 paused。严格质量阈值不变。

## Scope and consequences

- ITER-010 继续使用已冻结的当前计划、Manifest 和 Gate；本决定不追溯改写它的假设、运行结果或验收门槛。
- ITER-011 保持 `superseded / never executed`。
- 下一份新 Iteration Proposal、Manifest、Readiness、首个持续 Web Alpha、Verification Matrix、Slice Result 和最终 Acceptance 必须冻结
  并报告上述身份、隔离、盲评和严格胜出规则。
- 本决定只修改未来计划、治理和验收规则，不授权产品/System 实现、Provider 调用、源码披露、live Web、hidden suite 或 Production
  Activation。

## Revisit condition

可以提高样本量、盲评量表或严格胜出阈值，但不得把最低门槛降回“质量不退步”，也不得允许次级效率指标补偿答案质量平局或退步。
