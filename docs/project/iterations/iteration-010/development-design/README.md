---
id: ITER-010-DEVELOPMENT-DESIGN
kind: development-design-index
status: current
authority: project-plan
owners: [engineering, architecture, product, quality]
depends_on: [ITER-010-PROPOSAL, ITER-010-READINESS, ITER-010-VERIFICATION, ITER-010-RESULT-SLICE-001-STOP-REDIRECT, FINDING-010-107, FINDING-010-108, FINDING-010-109, FINDING-010-110, FINDING-010-132, FINDING-010-133, ITER-010-PDR-001, ITER-010-PDR-004, ITER-010-PDR-005]
code: []
tests: []
iteration: ITER-010
coding_input: true
---

# ITER-010 Development Design

当前处于 `direction-exploration / PDR-005 restart`，hardening 未解锁。可启动 Chat 页面已经交付，但 run-035—042 均未形成合格
Chat；唯一 World Model input 只有 Maven 模块/依赖，v7 又在未完成逐层归因时修改 query/review prompt。旧开发链与 v7 已停止。

新的开发对话直接读取 Slice1 顶部 PDR-005 执行卡，顺序是：离线分层归因（外部调用 0）→结构+实现/行为 Cognition 资格→复用现有 Web
交付一条真实语义链和两个未参与修复的异质问题→一个 Ark direction canary session/方向比较。不得先做 fresh 双 Provider Conformance、
重跑旧五轮或 full regression。

| Slice | 状态 | 目的 | 进入条件 |
|---|---|---|---|
| [SLICE-001](SLICE-001-engineering-qa-direction-preview.md) | `authorized / active / rework / PDR-005 restart / no live authority / coding input` | 先证明认知资格和故障责任层，再让主工程 Agent 在现有 Web 交付一条语义链、两个未参与修复的异质问题及方向信号 | `V-LAYER-ATTRIBUTION-001` 离线先行；Maven-only 不得充当行为认知；live/Provider 必须另取 exact grant |
| [SLICE-002](SLICE-002-cross-project-hardening.md) | `proposed` | Conversation 持久恢复、复杂冲突/去重/异常、跨工程与三臂正式复验 | Slice1 Chat Alpha 经真实体验与方向比较后 `CONTINUE`；再取开发授权及消融/hardening 新冻结收据 |
| [SLICE-003](SLICE-003-formal-product-acceptance.md) | `proposed` | 未见工程、多轮现场对话、三臂、安全和最终验收 | Slice2 exact Result=`CONTINUE`，再取得新授权 |

`ITER-010-RESULT-SLICE-001-STOP-REDIRECT` 保留 Slice1 的执行事实和答案/审核 FAIL；[PDR-001](../decisions/PDR-001-resume-as-rework.md)
纠正了把旧用户消息推断成明确 `REDIRECT` 的项目决定。`32b298de…` 曾恢复旧设计编码，PDR-004 随后暂停该权威；`f76ba3e8…` 现已在
新 Agent/Chat Readiness 上重新授权 Slice1。PDR-005 允许全新开发对话接手，但不扩大外部权限、不重置旧失败。现有持续单轮问答不能冒充
Chat。Slice2/3 从未授权，继续保持 proposed。
