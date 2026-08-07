# 治理模板

复制最小模板并替换占位符，不要预建没有消费者的空文档：

- `iteration-proposal.md`
- `iteration-index.md`
- `manifest.yaml`
- `development-design-index.md`
- `development-slice.md`
- `findings-index.md`
- `verification-matrix.md`
- `readiness-review.md`
- `implementation-finding.md`
- `system-adr.md`
- `project-decision.md`
- `iteration-result.md`
- `results-index.md`
- `iteration-acceptance.md`

模板不属于当前权威索引，也不作为示例内容的事实来源。替换所有 `NNN`、`<...>` 和 `pending` 后再运行文档检查；不得复制上一轮的 Commit、模型、Digest、测试数字或有效期。

## 最小落位

| 目标位置 | 模板 |
|---|---|
| `iterations/iteration-NNN/README.md` | `iteration-index.md` |
| `iterations/iteration-NNN/proposal.md` | `iteration-proposal.md` |
| `iterations/iteration-NNN/manifest.yaml` | `manifest.yaml` |
| `iterations/iteration-NNN/verification-matrix.md` | `verification-matrix.md` |
| `iterations/iteration-NNN/readiness-review.md` | `readiness-review.md` |
| `iterations/iteration-NNN/development-design/README.md` | `development-design-index.md` |
| `iterations/iteration-NNN/development-design/SLICE-NNN-*.md` | `development-slice.md` |
| `iterations/iteration-NNN/findings/README.md` | `findings-index.md` |
| `iterations/iteration-NNN/findings/FINDING-NNN-*.md` | `implementation-finding.md` |
| `iterations/iteration-NNN/results/README.md` | `results-index.md` |
| `iterations/iteration-NNN/results/<type>.md` | `iteration-result.md` |
| `iterations/iteration-NNN/results/acceptance.md` | `iteration-acceptance.md` |

先以 `proposed` 状态完成 Proposal、Manifest、Slice、Verification 与 Readiness。得到用户明确授权后，把 Proposal 与 Readiness 改为 `accepted` 并填写授权字段，把 Iteration Index、Manifest 和当前 Slice 改为 `authorized`，将 Index/Slice 的 `coding_input` 改为 `true`，最后原子更新 `project/current.md` 的两个指针及 `depends_on`。在这之前不得把模板存在本身解释为授权。
