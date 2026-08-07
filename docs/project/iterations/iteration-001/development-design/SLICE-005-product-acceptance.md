---
id: ITER-001-SLICE-005
kind: development-slice
status: completed
authority: historical-development
owners: [product, quality, interface]
depends_on: [ITER-001-SLICE-004, SYS-QUALITY-ACCEPTANCE]
code: [validation/product_holdout_iteration_002, src/software_world_model/interface/http_api.py]
tests: [tests/test_product_holdout_execution.py, tests/test_product_validation.py, tests/test_browser_chat_interface.py]
iteration: ITER-001
migration: reconstructed-from-existing-iteration-records
---

# SLICE-005：未见任务产品验收与本机体验

## Outcome

在两个未参与开发调试的冻结工程上，直接调查路径和系统路径使用相同题目、来源与资源限制；六题答案密封后由独立来源逐维度复核。全部不退步后，只在本机回环范围启用浏览器体验。

## Required system semantics

- 输入、Commit、允许文件、资源预算和防篡改 Digest 在运行前冻结；
- 评分规则在两侧答案密封后才提供给独立 Reviewer；
- 任一任务重大错误或任一维度退步使整轮失败，其他任务不能抵消；
- Product PASS 绑定 exact 能力资格和有效期；
- 本机体验启用与 Production Activation 分离。

## Affected implementation

Product Holdout Harness、Product Validation/Activation、Browser UI、loopback HTTP 和启动门禁。

## Non-goals

证明所有软件任务、开放网络服务、认证多用户、长期资格或自动生产部署。

## 阅读与回写

当前下限见[验收原则](../../../../system/quality/acceptance-principles.md)与[安全边界](../../../../system/quality/security-boundaries.md)；实现发现进入本轮 [Findings](../findings/README.md)。

## Acceptance

六题系统答案逐题不低于直接答案且零重大错误；冻结输入重新校验；评审和结果只写一次；过期/漂移时本机模型路径停止；HTTP 非回环绑定被拒绝。
