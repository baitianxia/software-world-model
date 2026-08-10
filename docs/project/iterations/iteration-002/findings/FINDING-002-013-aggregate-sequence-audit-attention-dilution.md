---
id: FINDING-002-013
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-002-SLICE-001, FINDING-002-012]
code: [src/software_world_model/ai_infrastructure/agentic_knowledge_strategy.py]
tests: [tests/test_agentic_knowledge_strategy.py]
iteration: ITER-002
classification: iteration-design
disposition: add-fact-boundary-policy-and-final-focused-sequence-audits
target: ITER-002-SLICE-001
---

# FINDING-002-013：整体顺序审核仍会因注意力稀释漏掉组合事实

## Observation

Strategy `2.0.194` 已把返回值使用和调用后状态检查纳入通用顺序语义，并通过对应六角色能力评估。产品路径随后完成 96 次模型调用并机械封存，但 Codex 独立复核仍发现最终两次整体答案顺序审核都把组合调用方判为原子。结果再次把调用、返回后分支和被调内部行为排成不可能的执行顺序。

## Evidence / reproduction

`var/product-generic-v194-suite205-return-dependency/document-render-two-stage-pipeline--world_assisted.json` 中，答案先完整陈述调用 `findPolicy` 及其返回后分支，下一条才解释 `RunTemplate.findPolicy` 内部；也先陈述 `DelegatePolicy.invoke` 后的文档状态检查，之后才解释 `DelegatePolicy.invoke` 内部。运行数据库中的最后两份 `ANSWER_SEQUENCE_ANALYSIS` 都把全部 17 条引用列为原子，说明规则语义已覆盖该模式，但大集合整体判断仍可能漏审单条引用。

## Impact

只强化整体提示不能把模型注意力稀释转化为可审核的系统保证。复杂答案即使事实阶段执行过逐引用审核，最终选择和重排也可能重新包含或保留组合事实；若答案阶段只做整体审核，机械封存仍可能接受顺序不成立的答案。

## Classification rationale

问题来自所有大型引用集合都可能出现的审核粒度，不依赖工程、语言、框架、符号或具体问题，因此归类为当前切片的通用 iteration-design 修订。

## Decision and disposition

事实生成状态增加高优先级通用边界规则：主动帮助调用与同一调用方的返回后行为必须优先生成独立事实，返回值或绑定值条件在没有显式时间词时仍属于返回后行为。顺序分析的单引用挑战采用固定语义步骤，先枚举主动调用，再检查后续返回依赖行为，最后与所有被调主题比较。最终答案对大型引用集合也逐条执行两次互相独立的聚焦审核；只有两次都报告同一调用方/被调跨度时才拒绝，以免单次误判把平行分派当成时序。

调用次数和 Token 上限继续只作高位安全熔断。不得为压低调用数跳过这些审核；若完整质量链接近资源上限，应提高安全熔断并保留全部必要检查，而不是降低验收标准。

## Verification after disposition

新增回归测试模拟两次整体审核都漏报，但两次单引用答案审核一致识别真实调用返回跨度，验证答案在封存前失败关闭。既有返回依赖正例、平行分派反例和事实拆分修复测试继续保留。Strategy 升级为 `2.0.195`，`2.0.194` 的能力资格和产品结果不能继承。
