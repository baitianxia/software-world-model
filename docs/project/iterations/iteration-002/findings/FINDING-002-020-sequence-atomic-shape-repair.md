---
id: FINDING-002-020
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-002-SLICE-001, FINDING-002-006, FINDING-002-008, FINDING-002-010]
code: [src/software_world_model/ai_infrastructure/agentic_knowledge_strategy.py]
tests: [tests/test_agentic_knowledge_strategy.py]
iteration: ITER-002
classification: iteration-design
disposition: preserve-strict-contract-with-exact-shape-repair
target: ITER-002-SLICE-001
---

# FINDING-002-020：单数字段格式错误耗尽顺序审核修复次数

## Observation

Strategy `2.0.201` 的产品运行完成 73 次模型调用且全部有完整 Provider 结果。最后一个事实聚焦审核的第一轮把 `c13` 正确判为原子事实；第二轮仍作出相同语义判断，却把 `atomic_references` 项写成单数字段 `reference_id`。平台严格拒绝该格式，但后续两次修复只收到抽象错误和语义性指令，模型连续返回相同单数字段，最终在知识快照发布前失败关闭。

## Evidence / reproduction

证据位于 `var/product-generic-v201-suite205-restricted-positive-preservation/`。调用 `model_call_796827f4de98421aadea4e2478941e6c`、`model_call_a41cbeda875d40dbbf8492def8fb8f9f` 和 `model_call_4ad40c10dc254e44b05052a03f381821` 均返回 `{"need_id":"need_template_render_pipeline","reference_id":"c13"}`；契约要求 `{"need_id":"need_template_render_pipeline","reference_ids":["c13"]}`。三次调用本身均为 `COMPLETED`，因此这不是网络、Provider 结果未知、源码不足或事实判断错误。

## Impact

严格结构化契约是可审计性的组成部分，不能通过接受未声明字段来换取通过。但若错误诊断不指出实际键、期望键和数组形状，固定的低重试次数会在可机械修复的序列化差异上截断后续独立质量审核。这属于通用结构化输出问题，不依赖工程、语言或问题内容。

## Classification rationale

该问题改变当前切片中顺序审核的局部修复策略，但不改变对外接口、事实语义或 System 不变量，归类为 iteration-design。

## Decision and disposition

保持 `atomic_references` 的严格两字段契约，不接受 `reference_id` 别名。顺序审核提示明确给出单项数组的 exact JSON 形状，并要求字段始终为复数 `reference_ids`；平台错误详情同时返回错误项序号、实际键、期望键、期望形状和精确修复动作。顺序阶段的结构化输出修复熔断由三次提高到五次；完整集合审核、两次独立审核、逐调用方聚焦和争议裁决均不减少，语义与证据校验也不放宽。

## Verification after disposition

新增单元测试重放单数 `reference_id`，验证平台拒绝该输出并给出 exact 修复详情。Strategy 升级为 `2.0.202`；`2.0.201` 的能力资格和失败产品运行不能授权新实现。
