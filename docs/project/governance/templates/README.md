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

每轮还必须绑定 Roadmap 中从最终目标反推的能力步骤，列出前置接受/失败证据、本轮通过后用户在正式 Web 上能新做什么，
以及下一个最早阻断差距。不得用“新组件已完成”、“为后续打基础”或没有 Web 用户能力变化的风险下降替代这四个字段。

从 ITER-008 起，每轮还必须冻结关键方案假设、最早反证和备选路线；Manifest、Readiness 与 Result 用同一个 Proposal 假设表摘要
锁定原文，不能在看到结果后改写。每个 Slice 恰好绑定一个 `V-REFLECT-NNN`。Slice 的固定结束
顺序是正式 Web/本阶段适用的验证、形成 Result、完成方案复盘、作出 `CONTINUE / ACCEPT / REWORK / REDIRECT / REJECT`；体验 Alpha 使用可见输入，
Alpha `CONTINUE` 后的 hardening 才承担 early hidden。缺少复盘，或中间段
决定不是 `CONTINUE` 时，不得授权下一 Slice；机械测试 PASS 不能替代方案判断。

产品计划必须把“可体验 Alpha、工程夯实、正式验收”分开。第一个 Slice 用真实入口和小而多样的问题与现场输入直接形成非验收 Alpha；
只有 Alpha 的 `CONTINUE` 后才安排全面契约、回归、性能、能力资格、hidden canary 和正式验收。安全、权限、Secret 与失败真实性不能
延后，但不得把完备证明材料误作 Alpha 的前置目标。

首次方向体验必须是真正可持续操作的版本：精确版本可重复启动、固定本地地址、同一会话连续自由提问、版本和限制可见，且单题失败不
关闭服务。一次性验证运行或只能回答启动前冻结问题的页面不算体验版本。阻断失败默认记录为 `REWORK` 并暂停当前 Slice；同一目标和
总体架构下使用新的用户授权恢复同一 Slice。只有明确用户转向、核心架构证伪或达到预提交无进展上限才允许 `REDIRECT`。

Manifest 还必须冻结评测工程/版本、held-out suite、baseline Result、成熟源码 Agent protocol 和授权软件来源范围的 exact digest，
以及前后支持题数。体验 Alpha 期间可使用明确、失败关闭的 deferred/user-held marker；最迟在拥有对应 hidden/对照的 hardening 或 final
Slice 授权前替换为 exact freeze，不能反向阻塞早期可见结果。完成时 `V-000` Evidence 必须引用本轮一个带完整 `product_goal_*` 元数据的 PASS Result，不能填写
普通文字、机械测试 Result 或风险实验 Result 代替。

机械 Gate 只能验证这些对象之间的闭合关系。Readiness 仍必须由用户查看 exact 冻结输入和案例后作语义判断；随机 digest、
看似正确的字段名或自报 PASS 不能证明候选真的形成通用源码问答增量。跨域 Case、正式 Web 和现场临时问题之间的关系以
Manifest 的结构化 binding 为准，不从正文是否碰巧出现某个 ID 推断。
