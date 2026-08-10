---
id: FINDING-002-010
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-002-SLICE-001, FINDING-002-006, FINDING-002-008]
code: [src/software_world_model/ai_infrastructure/agentic_knowledge_strategy.py]
tests: [tests/test_agentic_knowledge_strategy.py]
iteration: ITER-002
classification: iteration-design
disposition: strengthened-targeted-language-repair-and-raised-local-safety-fuse
target: ITER-002-SLICE-001
---

# FINDING-002-010：局部重试熔断截断可收敛的语言修复

## Observation

Strategy `2.0.191` 的产品运行在事实覆盖修复阶段得到了一组语义可用的候选，但其中一条中文候选把来源语言的控制流词直接当作叙述，仅包含一个中文自然语言字符。平台正确报告 `RESPONSE_LANGUAGE_INVALID`；模型在后续局部修复中多次原样返回该候选，固定五次契约重试先结束了仍可修复的质量链。

## Evidence / reproduction

`var/product-generic-v191-suite205-quality-first/` 的运行数据库记录五次候选修复调用均得到完整 Provider 结果。最后一次错误明细仍为 `required_response_script: CJK`、`actual_script_character_count: 1`、`minimum_required_script_characters: 2`，并以 `fact proposer exhausted bounded contract retries` 结束。该错误不证明来源不足、事实错误或质量检查无法完成，只证明修复指令没有使模型改变被点名的语句。

## Impact

若把响应语言门槛降低，英文或源码式内部表述可能重新出现在中文用户答案中；若保留过低的局部固定次数，则一个小的结构化或语言缺陷可能使完整产品链提前失败。两者都会降低真实体验质量。

## Classification rationale

变化只调整当前切片内模型契约修复的提示和高位安全熔断，不改变正式知识、外部接口或系统不变量，因此归类为 iteration-design。

## Decision and disposition

保留原有响应语言门槛以及事实、来源、覆盖和顺序审核。契约修复现在根据精确诊断强制修改每条语言违规语句：保留字面标识符、值和消息，把充当叙述的来源语言控制流词改为所需自然语言，达到最小字符数且不得弱化、遗漏或发明含义。复杂补丁的局部契约尝试上限由五次提高到八次，只作为防止失控的高位安全熔断，不作为质量目标或提前发布依据。

## Verification after disposition

新增回归测试先连续返回五次同一语言违规候选，再在第六次修复成功，证明流程不会在旧上限处截断；原有测试继续证明八次均无进展时失败关闭，不能发布最后一份无效候选。Strategy 升级为 `2.0.192`，必须重新执行六角色资格和产品留出验证。
