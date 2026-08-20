---
id: SYS-CONTRACT-AI-CAPABILITY-EVALUATION
kind: system-contract
status: current
authority: normative
owners: [application]
depends_on: [SYS-ADR-015, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-X-CAPABILITY-EXECUTION]
derived_from: [DD-MGT-CAPABILITY-EVALUATION]
code: [src/software_world_model/application_services/evaluation.py, src/software_world_model/application_services/activation.py, src/software_world_model/ai_infrastructure/agentic_capability_evaluation.py, src/software_world_model/ai_infrastructure/world_model_capability_evaluation.py]
tests: [tests/test_capability_evaluation.py, tests/test_strategy_activation.py, tests/test_evaluation_runner.py]
---

# Capability Evaluation 与 Activation

## Purpose and scope

本契约定义一个精确模型 Strategy 如何获得、失去和使用业务能力资格。它不规定具体数据集、阈值、模型或某次运行结果。

## Ownership

业务模块拥有 Evaluation Contract 与 Oracle 语义；Application 拥有 Definition、Run、Result、Validity 和 Activation。Model Gateway 和领域 Core 不读写 Activation。

## Invariants

1. 只有 closed、PASS 且当前 `VALID` 的 Result 才可能支持 Activation；Conformance PASS 不能替代 Capability PASS。
2. 实现、模型、Prompt、Tool、Strategy、Adapter 或任何影响行为与资格的实质配置变化不得继承旧身份；滚动 alias 必须显式处理漂移。
3. Validity 只能从有效单调进入 stale/revoked；不能通过修改旧记录恢复。
4. Activation 绑定 Capability 声明的 normalized Activation Scope、单调 revision 和当前有效资格；environment、expiration 等维度只在该 Capability Contract 声明时生效。评测通过不会自动激活。
5. evaluation-only Sink 与生产 Sink 隔离，历史评测输出不得进入正式知识或生产答案。
6. 回退不能降低权限、隔离、输入闭包或产品边界。
7. Result-driven Strategy 的 Definition 必须覆盖首轮 evidence-obligation freeze、每个调查阶段、0/N candidate、obligation 已关闭或
   无合法缩小缺口 transition 时的 FINISH、多 Result 转换、
   最大步数、budget/cycle/progress、Ref provenance、Draft、独立 Review 与三层负向证明。模型只输出 semantic intent 时，Definition
   还必须经同一个 production argument compiler 验证 exact typed proposal；synthetic previous Result、progress completeness 与 operation
   transition 必须是正式产品可达状态。一个 Case 包含首轮时，后续 ledger/allowlist 必须与该轮实际 normalized obligation exact 一致；
   独立抽样 later state 时，必须绑定另一个预冻结且产品可达的 ledger fixture，而不是把该 Case 的 Oracle 期望注入 model-visible input。
   资格不能为满足 Oracle 伪造 scope Ref 或按回合序号改变同一 Result 的语义。固定三调用或单方法
   Qualification 不能授权 bounded investigation；operation set、Prompt/schema、argument compiler、预算、role sequence、Gateway
   connection policy 或 trace contract 任一变化均需新 closed Result。Qualification 必须保存每个 step 的 exact input/result/trace digest
   与真实调用计数，汇总 PASS 不能替代逐 Case 证据。
8. Oracle 可以在运行前为一个 sealed state 冻结有限、唯一且同等合法的 exact typed projection 集合；实际输出必须
   精确命中其中一项，不得在看到结果后追加选项或放宽字段/语义约束。资格 Case 中分别评估的 sealed-state 调用互相独立；
   相邻样本选择相同 operation 名称不构成 cycle。`QUERY_REPEATED` 只能由同一产品 Session 执行后的 exact query/result progress
   token 重复或等价的已密封审计证据推导。
9. semantic constraint 必须只要求 System Contract 规定且产品输入可证明拥有的概念，不得把一种可能的实现机制提升为唯一等价表达。
   对通用 search term 的评估可以要求覆盖原问题 material concept 及其已声明 normalization，但不能因为抽象 success/failure flow
   额外要求原问题未请求的 return/throw；这种 evaluator 假阴性必须版本化修正并保留旧结果，不能据此降低 operation Oracle、Case、
   threshold、Ref provenance、budget 或完整性规则。
10. 当产品正式接受与 source identifier 不同 writing system 的问题时，Result-driven Definition 必须至少包含一个真实 cross-script
    首轮 Case：model-visible input 保留该产品语言，Oracle 要求每个 material concept 的 common source-identifier translation，且仍禁止
    project dictionary、symbol hint 或 evaluator-only synonym。同一原文概念存在多个通用 English identifier translation 时，Oracle 应在
    新运行前冻结一个有界的 question-derived equivalence group，不能把单一 surface form 当成唯一正确翻译；看到旧运行结果后的修订只能
    形成新版本 Definition，旧 verdict 与证据保持不变。只用英文资格问题不能证明中文产品检索可用；平台 Unicode parser PASS 也不能
    替代 semantic translation Case。

## Failure and evidence boundary

运行结果未知保持 unknown；失败和过期结果永久保留但不能授权新 Activation。具体数据集、阈值、运行和产品对照是非规范性验证证据，必须绑定可重放的 exact implementation identity 与外部输入身份。

## Verification ownership

Definition/Run/Case/Result/Activation 的字段、状态机和恢复由代码及测试定义。
