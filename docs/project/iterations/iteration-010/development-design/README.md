---
id: ITER-010-DEVELOPMENT-DESIGN
kind: development-design-index
status: current
authority: project-plan
owners: [engineering, architecture, product, quality]
depends_on: [ITER-010-PROPOSAL, ITER-010-READINESS, ITER-010-VERIFICATION]
code: []
tests: []
iteration: ITER-010
coding_input: false
---

# ITER-010 Development Design

| Slice | 状态 | 目的 | 进入条件 |
|---|---|---|---|
| [SLICE-001](SLICE-001-engineering-qa-direction-preview.md) | `authorized / current development` | 一题真实 Web 微纵切，再做 4 题+现场题方向体验；不可延后 exact/read-only/untrusted/Citation/独立审核 | 收据 `585f02c4…` 已接受 Readiness 并授权开发；live 仍另行授权 |
| [SLICE-002](SLICE-002-cross-project-hardening.md) | `proposed` | 持久恢复、复杂冲突/去重/异常、独立多步补证、跨工程与三臂认知消融 | Slice1=`CONTINUE`；再取开发授权及消融/hardening 新冻结收据 |
| [SLICE-003](SLICE-003-formal-product-acceptance.md) | `proposed` | 未见工程、现场题、三臂消融、安全和最终验收 | Slice2 exact Result=`CONTINUE`，再取得新授权 |

`FINDING-010-002` 已把世界模型概念与提问期调查职责分开；Slice1 Phase 0 以 `V-ARCH-001` 复核 ADR-016、Engineering QA Contract、
Manifest 和治理门禁一致。当前只有 Slice1 是 coding input，真实 Web 必须晚于产品 freeze 与独立运行授权；新三臂消融与补证
hardening protocol 还必须在 Slice2 前由新用户收据冻结，不能复用旧 positive-value 收据。
