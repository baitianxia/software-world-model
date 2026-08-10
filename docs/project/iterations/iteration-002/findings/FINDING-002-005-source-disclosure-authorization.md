---
id: FINDING-002-005
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-002-SLICE-001]
code: [validation/product_holdout_iteration_002/world_answer.py]
tests: [tests/test_product_holdout_world_answer.py]
iteration: ITER-002
classification: iteration-design
disposition: recorded-explicit-external-disclosure-gate
target: ITER-002-SLICE-001
---

# FINDING-002-005：产品验收需要单独的源码外发授权

## Observation

产品级真实模型验收会读取冻结测试工程源码，并把完成问题所需的片段发送给外部火山模型。允许调用 API 或配置 API Key 不自动等于允许向该 Provider 披露源码。

## Evidence / reproduction

2026-08-09 执行 V-006 时，联网分派在 Provider 调用前被权限审查拒绝，理由是缺少对“把这些源码发送给火山模型”的明确授权。结果目录没有产生运行文件。

## Impact

本地测试和六类合成能力评估可完成，但真实陌生工程产品验证和本机可验收结论不能在该权限缺失时闭合。

## Classification rationale

这是本轮外部输入和安全边界，不要求改变 System Owner 或绕过现有失败关闭规则，因此归类为 iteration-design。

## Decision and disposition

在 Slice 和 Verification Matrix 中登记独立的源码披露权限 Gate。没有明确授权时不重试、不改用间接命令，也不把本地测试或合成能力 PASS 当作产品 PASS。

## Verification after disposition

用户随后已明确授权将公开冻结测试工程的必要源码片段发送给火山模型。权限 Gate 已闭合；后续运行仍须保持冻结路径、只读来源和 Codex 独立复核。
