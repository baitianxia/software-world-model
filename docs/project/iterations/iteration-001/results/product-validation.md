---
id: ITER-001-RESULT-PRODUCT
kind: iteration-result
status: pass
authority: evidence
owners: [product, quality]
depends_on: [ITER-001-RESULT-CAPABILITY, ITER-001-SLICE-005]
code: [validation/product_holdout_iteration_002]
tests: [tests/test_product_holdout_execution.py, tests/test_product_holdout_independent_review.py, tests/test_product_validation.py]
iteration: ITER-001
repository_identity_at_run: not-versioned
post_hoc_repository_capture: 476517b5baf62abcc5a6ddda30b33335d262a8f3
strategy_version: 1.38.0
strategy_implementation_digest: sha256:8973e07290336c5443f00a93f00ac27401423fbf2e7e02b17c2b250b3159f301
valid_until: 2026-08-14T03:40:46.485258Z
---

# Product Validation Result

## Historical failure retained

首轮五题 Product Holdout `PV-HOLDOUT-001` 得分 `33.75 / 50`，为 P0 FAIL。它暴露正式知识覆盖不足、真实模型边界和答案能力低于直接调查基线；该失败促成后续设计和实现修正，不能被删除或改写为 PASS。原始记录见 [Product Value Holdout Run 001](../../../../archive/legacy-documents/validation/product-value/Product_Value_Holdout_Run_001.md)。

## Accepted baseline holdout result

2026-08-07 的新一轮输入固定两个未参与开发调试的公开工程，各三个问题，共六题。两条路径使用相同题目、exact Commit、允许文件、模型来源和资源限制；答案密封后，Codex 独立读取冻结源码并逐维度复核。

| 结果 | 值 |
|---|---|
| 六题直接调查答案 | 全部正确且完整 |
| 六题系统辅助答案 | 全部正确且完整 |
| 系统相对直接路径退步 | 0 |
| 重大事实错误 | 0 |
| Final verdict | PASS |

Product Validation Record 为 `product_validation_158ce6cc0a4398e932c497a7fea34110`，Digest `sha256:67b6a7e6db3bbeded2707d00f4e59b013455d93366badcf026948b74197d00f9`，记录时间为 `2026-08-07T03:40:46.485258Z`，日期有效上限为 `2026-08-14T03:40:46.485258Z`。它绑定 Strategy `1.38.0`、接受实现摘要与 Qualification Digest `sha256:9ad50c7a91a8a2726bc055d37c0f978cdeb6307f08e5d4af42cdc283a06dbf94`。

## Limits

结果只覆盖冻结的两个 Java 工程、六题、接受基线的模型/实现/资源和有效期，不证明所有软件任务或生产部署。任何题目、工程、实现、模型、资格或公平性边界变化均需重跑；PASS 不自动 Activation。

本记录只适用于 front matter 与 Manifest 固定的 Strategy `1.38.0` 和实现摘要。任何不同 subject 都使它对该实现 stale；不能仅因日期尚未到期而继续加载，后续工作区状态也不写入本历史结果。

原始答案、Pair、Review 和 Authority DB 位于本机 `var/`，未进入 Git。版本化运行说明见 [Product Holdout Suite 002](../../../../archive/legacy-documents/implementation/iteration-001/Product_Holdout_Suite_002.md)。
