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

## 每轮内容如何确定

迭代从可验证的变化需求产生，而不是从目录、组件或“还有代码可写”产生。合法触发包括产品差距、上一轮失败、实现发现、运维风险、已满足进入条件的 Roadmap Candidate 或系统 Contract 必须修订。

选择时按顺序回答：

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
4. 把 Iteration Index、Manifest 与第一个 Slice 改为 authorized，把 Slice `authority` 改为 `current-development`，并将 Index/Slice 的 `coding_input` 改为 `true`。
5. 最后更新 `project/current.md` 的 `active_iteration`、`active_slice` 与 `depends_on`。`scripts/docs.py check` 只有在这些对象属于同一 Iteration 且必需输入闭合时才通过。

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

- 一个明确 Outcome 和非目标；
- 所引用 System 文档均 current，或先完成所需 System 设计；
- 每个 Slice 有可验证退出条件和风险边界；
- 外部输入、权限、Secret Reference 和原始证据保存方式已说明；
- Verification Matrix 能区分机械测试、真实能力和产品价值；
- `current.md` 同一时刻最多指向一个活动迭代和一个主要 Slice。

## Completion gate

代码完成不是迭代完成。必须有实际 Result、失败/限制、所有 Finding disposition、必要的 System 回写，以及明确的接受、拒绝或后续决策。生产启用若不属于 Proposal，就不能被“剩余工作”自动推入下一轮。
