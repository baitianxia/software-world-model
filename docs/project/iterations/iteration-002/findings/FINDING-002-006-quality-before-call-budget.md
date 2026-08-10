---
id: FINDING-002-006
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-002-VERIFICATION]
code: [validation/product_holdout_iteration_002/suite.json, validation/product_holdout_iteration_002/world_answer.py]
tests: [tests/test_product_holdout_manifest.py, tests/test_product_holdout_world_answer.py]
iteration: ITER-002
classification: verification
disposition: raised-resource-circuit-breaker-with-bounded-quality-stages
target: ITER-002-VERIFICATION
---

# FINDING-002-006：资源上限不应成为答案质量目标

## Observation

产品运行在 48 次调用内已完成需求、事实形成、独立覆盖、顺序、充分性和答案选择，调用上限却在最终语义审核前触发。该限制截断了质量链路，而不是阻止无进展循环。

## Evidence / reproduction

`product-generic-v160-acceptance` 的运行数据库记录 48 次全部完成调用、274722 个输入 Token 和 22946 个输出 Token。阶段包含 13 条正式事实、充分性 PASS、答案选择和答案顺序分析；下一阶段分派前 `_BudgetedModelGateway` 返回 `BUDGET_EXHAUSTED`。

## Impact

旧上限会让复杂但正常的问题无法进入最终审核。降低复核次数会直接损失事实覆盖或顺序质量，违背本轮 Outcome。

## Classification rationale

问题属于产品验收资源策略与质量 Gate 的关系，不改变生产 Owner 或正式知识契约，因此归类为 verification。

## Decision and disposition

将冻结套件升级为 `2.0.4`：直接路径和系统路径保持相同资源政策，调用上限从 48 提高到 96，总输入从 500000 提高到 1000000，总输出从 48000 提高到 96000。该上限是异常失控的高位安全熔断，不是答案质量目标；各 Strategy 阶段仍通过自身的有界重试、无进展和结构化契约停止。

## Verification after disposition

Manifest 测试固定新版本、Digest 和资源政策；V-006 必须重新运行到完整答案和最终语义审核，并由 Codex 对照源码复核。若仍触及 96 次，应调查阶段循环而不是继续盲目提高。
