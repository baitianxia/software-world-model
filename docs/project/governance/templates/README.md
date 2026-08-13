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

每个新 Iteration 还必须完整填写模板中的 `Product-goal alignment`：绑定 `SYS-PRODUCT-SUCCESS`，说明相对通用源码问答 MVP
的 baseline gap、与既有能力的累积组合、由独立评测方或用户持有且实现阶段不可见的 held-out 自由问题增量、跨域问题、
最早正式 Web 体验点、验收现场临时问题和停止条件。任何一项仍为占位符时不得通过 Readiness；孤立 Profile/View/组件的
完成不能替代该门禁。

Manifest 还必须冻结评测工程/版本、held-out suite、baseline Result、成熟源码 Agent protocol 和授权软件来源范围的 exact
digest，以及前后支持题数。完成时 `V-000` Evidence 必须引用本轮一个带完整 `product_goal_*` 元数据的 PASS Result，不能填写
普通文字、机械测试 Result 或风险实验 Result 代替。

机械 Gate 只能验证这些对象之间的闭合关系。Readiness 仍必须由用户查看 exact 冻结输入和案例后作语义判断；随机 digest、
看似正确的字段名或自报 PASS 不能证明候选真的形成通用源码问答增量。跨域 Case、正式 Web 和现场临时问题之间的关系以
Manifest 的结构化 binding 为准，不从正文是否碰巧出现某个 ID 推断。
