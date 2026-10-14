# 治理模板

复制最小模板并替换占位符，不要复制上一轮的 Commit、模型、Digest、测试数字、时间点或结果：

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

模板不是当前事实来源。替换全部 `NNN`、`<...>` 和需要冻结的 `pending` 后再运行文档检查。

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

## 默认迭代顺序（2026-10-14 起）

按 `PROJECT-GOVERNANCE-ITERATION-LIFECYCLE`：一页 Proposal（价值假设、最早实验、时间盒、退出条件）→ 用户确认 → 带截止日期的任务 →
检查点（交付包 + 架构评审 + 对照结果）→ 用户决定 `CONTINUE / REWORK / REDIRECT / STOP`。

## 门禁

- 开发前运行 `python3 scripts/plan_gate.py snapshot`，交付前运行 `python3 scripts/plan_gate.py diff --base <trusted-base-ref>`；
- 修改文档后运行 `python3 scripts/docs.py generate` 与 `python3 scripts/docs.py check`；
- Manifest 只需 `current_action` 的身份、类型、编码许可和允许/禁止路径；系统文档、治理文档与门禁文件只在 `kind: governance` 动作下修改。
