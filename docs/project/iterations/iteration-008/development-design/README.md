---
id: ITER-008-DEVELOPMENT-DESIGN
kind: development-design-index
status: proposed
authority: proposed-development
owners: [engineering, architecture]
depends_on: [ITER-008-PROPOSAL, ITER-008-READINESS, ITER-008-SLICE-001, ITER-008-SLICE-002]
code: []
tests: []
iteration: ITER-008
coding_input: false
---

# ITER-008 Development Design

本轮有两个依次单独授权、都能从正式 Web 人工验证的纵向开发 Slice：

- [SLICE-001：最小调查闭环与早期正式 Web Gate](SLICE-001-bounded-agentic-world-model-answering.md)
- [SLICE-002：完整性加固与最终产品验证](SLICE-002-investigation-hardening-and-product-validation.md)

每个 Slice 都把 Contract/typed 查询、调查循环、Draft/Review 与正式 Web 组合成交付，不允许按内部组件分别宣称完成。每段产品
Gate 后还必须形成方案复盘 Result，明确 `CONTINUE / ACCEPT / REDIRECT / REJECT`。SLICE-001 的早期隐藏 Gate、成熟源码 Agent
同题对照、`V-REFLECT-001`、exact 用户决策收据或 `CONTINUE` 任一缺失时，SLICE-002 永远保持 proposed。当前两段都不是编码输入。
