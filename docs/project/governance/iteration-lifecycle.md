---
id: PROJECT-GOVERNANCE-ITERATION-LIFECYCLE
kind: project-governance
status: current
authority: project-governance
owners: [project, product]
depends_on: [PROJECT-GOVERNANCE-BOUNDARY, SYS-PRODUCT-SUCCESS]
code: []
tests: []
---

# 迭代选择与生命周期

## 产品目标对齐门禁

本门禁从 `ITER-007` 的选择开始强制执行。所有新 Iteration 必须以 `SYS-PRODUCT-SUCCESS` 的“基于预构建世界模型进行通用源码问答”作为共同产品目标。迭代可以缩小
实现范围，但不能另立与该目标无关的局部终点，也不能用改名把解析器、Schema、View、Profile 或固定题型包装成产品结果。

进入候选比较前，每个 Proposal 必须明确并冻结：

1. **目标差距：** 当前 Web 体验相对通用源码问答 MVP 具体缺什么，证据来自哪些真实自由问题；
2. **累积路径：** 本轮如何复用并组合此前已接受的知识和查询能力。只新增一个不能与既有能力联合回答问题的孤立模型，
   不得作为产品迭代 Outcome；
3. **可测增量：** 本轮完成后，哪组未参与实现的真实工程与 held-out 自由问题会从 Gap/失败变成有证据的正确答案，并冻结
   问题总数、baseline 支持数和目标支持数；覆盖率、重大错误、完整性、Source-off 和源码 Agent 对照如何判定；问题由独立
   评测方或用户持有并在实现阶段保持不可见，正式 Web 验收还必须加入至少一条现场临时自由提问；
4. **跨域证明：** 除新能力自身的问题，还必须包含至少一类需要组合既有能力与本轮能力的问题，证明产品能力是累积的；
5. **最早体验点：** 在大量实现前，哪个最小 Slice 会接入同一个正式 Web 入口供人工自由提问；
6. **停止或转向条件：** 若上游知识不足、只能依赖题型/关键词补丁、不能跨域组合或效果低于成熟源码 Agent，何时停止扩张
   并重新审视建模或查询架构。

不满足上述任一项的 Candidate 可以保留为技术实验或证据收集，但不得被选择为下一轮产品开发 Iteration。风险消除可以是
产品 Iteration 的第一个 Slice，但整个 Iteration 仍须计划同一正式 Web 上可人工验证的通用问答增量；若风险结果触发停止，
则记录证据并把本轮判为失败或转向，不能把组件完成或“学到了什么”称为产品进展。

跨域 Gate 不能用“一条旧能力回归 + 一条新能力孤立测试”拼成。至少一个冻结 Case 必须在同一个问题中同时引用此前已验收
能力和本轮 Slice，正式 Web 与现场临时问题 Gate 还必须执行或探测该跨域 Case。这些关系必须写入 Manifest 的结构化
binding；正文中仅仅出现相关 ID 不算绑定证据。

## 每轮内容如何确定

迭代从可验证的变化需求产生，而不是从目录、组件或“还有代码可写”产生。合法触发包括产品差距、上一轮失败、实现发现、运维风险、已满足进入条件的 Roadmap Candidate 或系统 Contract 必须修订。

通过产品目标对齐门禁后，再按顺序回答：

1. **Outcome：** 哪个用户、运营或学习结果会改变？不做的成本是什么？
2. **Evidence：** 现有事实是什么，哪些仍是假设？
3. **Smallest vertical slice：** 能独立证明结果的最小端到端切片是什么？
4. **System impact：** 需要哪些 current Contract；是否依赖尚未接受的系统能力？
5. **Risk and dependency：** 先关闭哪项高风险未知，哪些工作可以明确不做？
6. **Acceptance：** 用什么输入、Oracle、对照和失败条件判定，而不是用完成代码量判定？

Roadmap 只提供候选。只有 Proposal 被明确接受、Manifest 闭合并由 `project/current.md` 指向后，Development Slice 才获得编码授权。

## 新一轮最小启动顺序

1. 按[模板落位表](templates/README.md#最小落位)建立 Iteration Index、Proposal、Manifest、Verification Matrix、Readiness、Development Design 和 Findings Index；全部保持 proposed / non-coding。
2. 冻结 baseline、System IDs、外部输入、风险、Acceptance 和第一个纵向 Slice，不复制上一轮运行身份。
3. Readiness Review 记录用户的明确授权，把 Proposal 与 Readiness 状态改为 `accepted`；未授权字段不得用默认值代替。
4. 把 Iteration Index、Manifest 与第一个 Slice 改为 authorized，把 Slice `authority` 改为 `current-development`，并将 Index/Slice 的 `coding_input` 改为 `true`；Manifest 已规划的后续 Slice 保持 `proposed / proposed-development / coding_input: false`。
5. 最后更新 `project/current.md` 的 `active_iteration`、`active_slice` 与 `depends_on`。`scripts/docs.py check` 只有在这些对象属于同一 Iteration 且必需输入闭合时才通过。

同一 Iteration 的累积 Slice 以 Manifest `new_capability_slice_refs` 的顺序推进：执行态必须为“零个或多个 `completed` + 恰好一个
`authorized/in-progress` + 零个或多个 `proposed`”。每个后续 Slice 必须直接依赖前一个；前一个 Slice 的人工 Web/停止 Gate 完成
并形成 Result 后，用户再明确授权下一个 Slice，随后才移动 `project/current.md.active_slice`。在最终 held-out 验证前，每个 Slice
还必须在本 Slice 产品代码冻结后通过独立持有的隐藏 canary；曝光后修改产品会烧毁 canary 并保留原失败。不得为了通过 Readiness 一次性授权
全部 Slice，也不得跳过失败 Slice。完成的 Slice 使用 `historical-development / coding_input: false`，当前 Slice 使用
`current-development / coding_input: true`，后续 Slice继续保持 proposed。

每个 completed Slice 的 Result 必须绑定该 Slice 的 exact 产品代码冻结 digest。拥有 early hidden canary 的 Result 还必须绑定
Manifest 冻结的 canary project/suite digest、披露收据和“曝光后产品变更数为 0”；否则不得授权下一 Slice。

## 生命周期

```text
roadmap candidate
  → iteration proposal
  → readiness review
  → authorized in current.md
  → development slices + findings
  → verification + result
  → findings disposition
  → acceptance
  → completed / rejected / superseded
```

## Readiness gate

- Proposal 已通过产品目标对齐门禁，目标差距、累积路径、独立持有且对实现隐藏的可测增量、跨域问题、最早 Web 体验点、
  现场临时问题和停止条件均已冻结；
- 一个明确 Outcome 和非目标；
- 所引用 System 文档均 current，或先完成所需 System 设计；
- 每个 Slice 有可验证退出条件和风险边界；
- 外部输入、权限、Secret Reference 和原始证据保存方式已说明；
- Verification Matrix 能区分机械测试、真实能力和产品价值；
- `current.md` 同一时刻最多指向一个活动迭代和一个主要 Slice。

`scripts/docs.py` 只负责检查引用、状态、digest、计数和依赖是否闭合，不能替代产品判断。Readiness Reviewer 必须实际核对
冻结工程、隐藏问题协议、跨域案例和 Web 体验设计，确认它们不是把 parser、Profile/View、CLI 或固定关键词题型重新包装成
产品增量；随机 digest、空洞 case 名和自报 PASS 都不构成证据。该判断必须由用户明确接受并绑定 exact review reference。

## Completion gate

代码完成不是迭代完成。必须有实际 Result、失败/限制、所有 Finding disposition、必要的 System 回写，以及明确的接受、拒绝或后续决策。生产启用若不属于 Proposal，就不能被“剩余工作”自动推入下一轮。

声称产品能力前进的 Iteration 还必须报告相对 baseline 的目标差距变化：同一正式 Web 入口上的 held-out 自由问题支持率、
重大错误、完整性、至少一个新旧知识跨域问题、提问时 Source/Update/Direct fallback 计数，以及与成熟源码 Agent 的逐题对照。
Manifest 绑定的每个跨域、正式 Web、隐藏 canary 和现场临时问题 Case 必须逐项 PASS，并以
`<拥有该 Case 的 Slice Result ID>#<case-id>` 绑定不可变执行证据；最终 Product Result 必须依赖并聚合全部 Slice Result，不能改写
逐 Case Evidence，也不能用 V-000 的 PASS 或汇总计数代替逐项执行。
只证明本轮新增 Profile/View 的封闭题集通过，或只有旧能力回归而没有跨域组合证据，不得标记为完成的产品进展。结果未显示
可测增量时，应保留为失败/学习证据并把 Iteration 判为 rejected/superseded 或重新选路，而不能标记为已完成的产品进展，
更不能继续堆叠下一个孤立知识域。

从 ITER-005 起，任何声称扩展 Software World Model 建模、查询或问答能力的 Iteration，在标记 completed 前必须把本轮新增
能力接入同一个产品代码拥有的本机 Web 问答入口，并由人工提交至少一条支持问题和一条边界/Gap 问题。一次性
`validation.*` launcher、静态回放页、测试计数或 API-only smoke 不能替代该体验。中间 Slice 可以先用 CLI/View 暴露风险，
但整个 Iteration 不得在正式 Web 问答入口尚不可用时完成；这不自动授予公网部署或 Production Activation。
