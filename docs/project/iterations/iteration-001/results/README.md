---
id: ITER-001-RESULTS-INDEX
kind: iteration-result-index
status: completed
authority: evidence
owners: [project, quality]
depends_on: [ITER-001-VERIFICATION]
code: []
tests: []
iteration: ITER-001
---

# Iteration 001 Results

这些结果从 pre-Git 旧记录重建历史完成事实。提交 `476517b` 只冻结迁移前仓库状态，不是原始运行输入；各结果只适用于 Manifest 能够精确固定的 subject，不能从该提交反推缺失的历史身份，也不追随后续工作区状态。

- [Architecture Validation](architecture-validation.md)：阶段性失败、机制见证和最终影响。
- [Implementation](implementation.md)：生产实现、回归和本机体验。
- [Contract Conformance](contract-conformance.md)：Ark @8 Live CC。
- [Capability Evaluation](capability-evaluation.md)：JWT 专项和六类通用资格。
- [Product Validation](product-validation.md)：旧 Holdout FAIL 与新六题 PASS。
- [Acceptance](acceptance.md)：本轮最终裁决。

这些文件是已版本化的结果摘要/attestation。大部分原始运行数据库、模型输出和封存文件位于本机 `var/`，已按安全和体积边界排除 Git；不能声称本仓库保存了完整 Runtime Evidence。
