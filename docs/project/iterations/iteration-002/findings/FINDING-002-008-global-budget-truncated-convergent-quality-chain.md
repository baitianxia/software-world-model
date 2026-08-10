---
id: FINDING-002-008
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-002-VERIFICATION, FINDING-002-006]
code: [validation/product_holdout_iteration_002/suite.json, validation/product_holdout_iteration_002/world_answer.py]
tests: [tests/test_product_holdout_manifest.py, tests/test_product_holdout_world_answer.py]
iteration: ITER-002
classification: verification
disposition: raised-global-safety-fuse-after-convergence-audit
target: ITER-002-VERIFICATION
---

# FINDING-002-008：全局调用熔断再次截断正常收敛的质量链

## Observation

Strategy `2.0.190` 的真实产品运行已发布完整知识快照，通过事实顺序、推理、充分性和答案顺序阶段，并在第三次答案局部修复后准备继续最终审核；Suite `2.0.4` 的 96 次全局调用上限却在下一次分派前终止流程。

## Evidence / reproduction

`var/product-generic-v190-quality-first/` 的运行数据库记录 95 次有完整输出的调用、1 次结果未知的传输调用、694373 个输入 Token 和 45172 个输出 Token。45 次覆盖审核来自多轮增量修复及独立完整性挑战；候选事实持续变化，随后各阶段继续前进，不是无进展循环。终止位置为 `ANSWER_DRAFT_SELECTION` 的下一质量调用，错误为 `BUDGET_EXHAUSTED`。

## Impact

全局计数低于正常质量链的实际需求时，会迫使复杂任务在已经形成正确知识后放弃最终答案。减少覆盖、顺序或答案审核次数会把资源限制转化为质量损失。

## Classification rationale

该问题只影响冻结产品验证的资源策略，不改变生产知识、回答或模型网关契约，因此归类为 verification。

## Decision and disposition

先按 `FINDING-002-006` 要求检查阶段进展和调用分布，确认运行持续收敛后，将留出 Suite 升级为 `2.0.5`。直接路径和系统路径保持完全相同的资源政策；全局模型调用熔断从 96 提高到 192，总输入 Token 从 1000000 提高到 2000000，总输出 Token 从 96000 提高到 192000。各 Strategy 阶段的局部重试、结构合同、无进展检测和失败关闭规则保持不变，仍负责阻止失控循环。

## Verification after disposition

Manifest 测试必须固定 Suite `2.0.5`、新 Digest 和相同的双路径资源政策。V-006 必须从头运行到最终语义审核，并由 Codex 独立按冻结源码复核；不得仅凭未触发新熔断判定 PASS。
