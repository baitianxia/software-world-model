---
id: ITER-010-DEVELOPMENT-DESIGN
kind: development-design-index
status: current
authority: project-plan
owners: [engineering, architecture, product, quality]
depends_on: [ITER-010-PROPOSAL, ITER-010-READINESS, ITER-010-VERIFICATION, ITER-010-RESULT-SLICE-001-STOP-REDIRECT, ITER-010-PDR-001, ITER-010-PDR-004]
code: []
tests: []
iteration: ITER-010
coding_input: true
---

# ITER-010 Development Design

当前处于 `direction-exploration`，hardening 未解锁。Slice1 的唯一下一出口是先把可启动 Chat 页面交给用户，而不是一次性闭合五轮质量、
三臂比较和全部 Gate；其四个微检查点见 Slice1 文件顶部执行卡。

| Slice | 状态 | 目的 | 进入条件 |
|---|---|---|---|
| [SLICE-001](SLICE-001-engineering-qa-direction-preview.md) | `authorized / active / rework / coding input` | 复用既有安全、证据和 Web 资产，改为主工程 Agent 驱动的真正多轮 Chat；五轮连续对话和新对话隔离后，产出小样本三臂方向信号 | `f76ba3e8…` 已接受 PDR-004 Readiness 并授权产品/System 编码与本地确定性验证；live/Provider 另行授权 |
| [SLICE-002](SLICE-002-cross-project-hardening.md) | `proposed` | Conversation 持久恢复、复杂冲突/去重/异常、跨工程与三臂正式复验 | Slice1 Chat Alpha 经真实体验与方向比较后 `CONTINUE`；再取开发授权及消融/hardening 新冻结收据 |
| [SLICE-003](SLICE-003-formal-product-acceptance.md) | `proposed` | 未见工程、多轮现场对话、三臂、安全和最终验收 | Slice2 exact Result=`CONTINUE`，再取得新授权 |

`ITER-010-RESULT-SLICE-001-STOP-REDIRECT` 保留 Slice1 的执行事实和答案/审核 FAIL；[PDR-001](../decisions/PDR-001-resume-as-rework.md)
纠正了把旧用户消息推断成明确 `REDIRECT` 的项目决定。`32b298de…` 曾恢复旧设计编码，PDR-004 随后暂停该权威；`f76ba3e8…` 现已在
新 Agent/Chat Readiness 上重新授权 Slice1。现有持续单轮问答不能冒充 Chat。Slice2/3 从未授权，继续保持 proposed。
