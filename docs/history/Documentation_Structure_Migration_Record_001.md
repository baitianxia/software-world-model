# Software World Model Documentation Structure Migration Record 001

| 元数据 | 值 |
|---|---|
| Record ID | SWM-DOC-MIG-001 |
| Status | Completed |
| Executed At | 2026-08-05 |
| Scope | 文档物理目录、导航链接与完整文件摘要 |
| Semantic Change | None |

## 1. 目的

将长期维护文档从平铺目录调整为职责清晰的 `architecture / detailed-design / implementation / validation / history` 结构，同时保留迁移前 Frozen Manifest 的可验证副本。

本次迁移没有改变架构职责、详细设计不变量、主题状态、实施选择或 Conformance 结论。Document ID 和语义版本保持不变；由于相对链接属于完整文件内容，迁移后使用新的 Manifest Revision。

## 2. 基线关系

| 类型 | 迁移前 | 当前 |
|---|---|---|
| Design Baseline | `SWM-DBM-ITER-001` | [SWM-DBM-ITER-001-REV-002](../detailed-design/governance/Design_Baseline_Manifest_Iteration_001_Revision_002.md) |
| Implementation Baseline | `SWM-IBM-ITER-001` | [SWM-IBM-ITER-001-REV-002](../implementation/iteration-001/Implementation_Baseline_Manifest_Iteration_001_Revision_002.md) |
| 开发迭代 | Iteration 001 | Iteration 001；未创建新的开发迭代 |

迁移前两个 Manifest 自身的 SHA-256：

- Design Manifest：`f7f32f959d06b08515352e606003e632bd3c5e81abd86ce5d9e09bc687b105af`
- Implementation Manifest：`bc62b09f863dcb61466a0ca8edabc82e508f3ec122fad99046f5b16d9b6b6f51`

## 3. 目录映射

| 迁移前 | 当前 |
|---|---|
| `docs/Software_World_Model_Architecture_Baseline.md`、`Architecture_Decision_Log.md` | `docs/architecture/` |
| `docs/Software_World_Model_Detailed_Design.md` | `docs/detailed-design/` |
| `docs/detailed-design/DD-*.md` | `docs/detailed-design/topics/` |
| Design Manifest、Review Record、Acceptance Record | `docs/detailed-design/governance/` |
| Implementation Plan、Implementation Manifest | `docs/implementation/iteration-001/` |
| `docs/implementation-baseline/ITER-001-*.md` | `docs/implementation/iteration-001/contracts/` |
| `docs/conformance/` | `docs/implementation/iteration-001/conformance/` |
| Architecture / Product Value Validation 文档 | `docs/validation/architecture/`、`docs/validation/product-value/` |
| 被替代的 Architecture Design 与 MVP Detailed Design | `docs/history/` |

## 4. 迁移前快照

- [SWM-Documentation-Baseline-Pre-Reorganization-2026-08-05.tar.gz](snapshots/SWM-Documentation-Baseline-Pre-Reorganization-2026-08-05.tar.gz)
- [SHA-256](snapshots/SWM-Documentation-Baseline-Pre-Reorganization-2026-08-05.tar.gz.sha256)
- Archive SHA-256：`b1df52b64241a979ea1af0e18d765bfe1f085b049568ccbeb1f67747dc1950ed`

该压缩包保存迁移前完整 `docs/` 树。旧 Design Manifest、Implementation Manifest 和 Holdout Baseline 可在解压后的原相对层级中复核。

## 5. 完成条件

1. 当前文档只存在一个 canonical 路径。
2. 全部本地 Markdown 链接和入口链接有效。
3. Revision 002 的 Design Manifest 与 Implementation Manifest 全部摘要通过。
4. Schema Definition Digest、Local Git Profile Contract Digest 与 Golden Vector 不因导航迁移变化。
5. Product Value Holdout Baseline 的独立 SHA-256 继续通过。
6. `demo/` 和 `validation-projects/` 不进入正式文档权威边界。

## 6. 执行结果

| 检查 | 结果 |
|---|---|
| 当前 Markdown 本地链接 | `237 / 237 PASS` |
| Markdown fenced code block 配对 | `PASS` |
| Revision 002 Design Manifest | `24 / 24 PASS` |
| Revision 002 Implementation Manifest | `5 / 5 PASS` |
| 迁移前快照中的原 Design Manifest | `24 / 24 PASS` |
| 迁移前快照中的原 Implementation Manifest | `5 / 5 PASS` |
| Schema Definition Digest | `PASS` |
| Local Git Profile Contract Digest | `PASS` |
| Local Git codec Golden Vector | `2 / 2 PASS` |
| 当前与迁移前 Product Value Holdout SHA-256 | `PASS` |
| 迁移前压缩快照 SHA-256 | `PASS` |
