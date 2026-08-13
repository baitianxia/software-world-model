---
id: ITER-007-DEVELOPMENT-DESIGN
kind: development-design-index
status: proposed
authority: proposed-development
owners: [engineering]
depends_on: [ITER-007-PROPOSAL, ITER-007-READINESS, ITER-007-SLICE-001, ITER-007-SLICE-002, ITER-007-SLICE-003]
code: []
tests: []
iteration: ITER-007
coding_input: false
---

# ITER-007 Development Design

三个 Slice 都是 proposed，不是编码输入：

1. [SLICE-001：最小实现语义正式 Web walking skeleton](SLICE-001-java-source-semantics-walking-skeleton.md)
2. [SLICE-002：可见语料上的 Java 语义加固](SLICE-002-java-semantic-hardening.md)
3. [SLICE-003：代码冻结后的 held-out 产品验证](SLICE-003-held-out-product-validation.md)

SLICE-001 先用真实模型、正式 Web 和冻结后的独立隐藏 canary 证明最小产品链；SLICE-002 只在可见语料加固，再以第二个独立隐藏
canary 做早期泛化止损；SLICE-003 才执行最终两份 held-out 工程。任一前序 Slice 的 Web/canary Gate 未 PASS 并形成 Result，下一
Slice 都保持 proposed。
