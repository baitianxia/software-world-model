---
id: ITER-009-DEVELOPMENT-DESIGN
kind: development-design-index
status: current
authority: current-development
owners: [engineering, architecture]
depends_on: [ITER-009-PROPOSAL, ITER-009-READINESS, ITER-009-SLICE-001, ITER-009-SLICE-002, ITER-009-SLICE-003]
code: []
tests: []
iteration: ITER-009
coding_input: false
---

# ITER-009 Development Design

本轮按产品结果而不是内部组件拆成三个依次单独授权的纵向 Slice：

- [SLICE-001：真实本机 Web 方向体验](SLICE-001-local-web-direction-preview.md)
- [SLICE-002：通用证据问答链夯实](SLICE-002-evidence-answer-review-hardening.md)
- [SLICE-003：隐藏评测与正式验收](SLICE-003-formal-product-acceptance.md)

当前只有 `SLICE-001` 是编码输入。`SLICE-002` 必须等待第一段 exact Result、`V-REFLECT-001: CONTINUE` 和新的用户授权；
`SLICE-003` 必须等待第二段 exact Result、`V-REFLECT-002: CONTINUE` 和另一条新的用户授权。每段失败都保留证据并停止后续开发。
