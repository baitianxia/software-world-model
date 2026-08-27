---
id: ITER-010-DEVELOPMENT-DESIGN
kind: development-design-index
status: current
authority: project-plan
owners: [engineering, architecture, product, quality]
depends_on: [ITER-010-PROPOSAL, ITER-010-READINESS, ITER-010-VERIFICATION, ITER-010-RESULT-SLICE-001-STOP-REDIRECT, FINDING-010-107, FINDING-010-108, FINDING-010-109, FINDING-010-110, FINDING-010-132, FINDING-010-133, FINDING-010-134, FINDING-010-135, FINDING-010-136, FINDING-010-137, FINDING-010-138, ITER-010-PDR-001, ITER-010-PDR-004, ITER-010-PDR-005, ITER-010-PDR-006, ITER-010-PDR-007]
code: []
tests: []
iteration: ITER-010
coding_input: true
---

# ITER-010 Development Design

当前处于 `direction-exploration / PDR-007 off-peak hard admission / PDR-006 continuous execution / PDR-005 gate`，hardening 未解锁。可启动 Chat 页面已经交付，但 run-035—042 均未形成合格
Chat；唯一 World Model input 只有 Maven 模块/依赖，v7 又在未完成逐层归因时修改 query/review prompt。旧开发链与 v7 已停止。

新的开发对话直接读取 Slice1 顶部 PDR-007/PDR-006/PDR-005 执行卡。离线分层归因、结构+实现/行为 Cognition 资格、
`V-DEEPSEEK-IDLE-001` 和 clean `3a6089f…` successor freeze 已完成；run-043 只保留为质量与调度失败归因证据。当前直接取得新的 exact
grant，允许窗口与 grant 同时成立后才执行一个后继 canary。峰时继续 Ark-only 和本地工作；不得因此停止开发，也不得先做 fresh 双
Provider Conformance、重跑旧五轮或 full regression。

| Slice | 状态 | 目的 | 进入条件 |
|---|---|---|---|
| [SLICE-001](SLICE-001-engineering-qa-direction-preview.md) | `authorized / active / rework / local schedule gate pass / successor frozen / coding input` | 已证明认知资格和故障责任层，并闭合 DeepSeek 硬准入与 v8 semantic-query successor；当前交付合规方向体验 | 峰时本地/Ark-only 继续；允许窗口和新 exact grant 同时成立后只跑一个 canary |
| [SLICE-002](SLICE-002-cross-project-hardening.md) | `proposed` | Conversation 持久恢复、复杂冲突/去重/异常、跨工程与三臂正式复验 | Slice1 Chat Alpha 经真实体验与方向比较后 `CONTINUE`；再取开发授权及消融/hardening 新冻结收据 |
| [SLICE-003](SLICE-003-formal-product-acceptance.md) | `proposed` | 未见工程、多轮现场对话、三臂、安全和最终验收 | Slice2 exact Result=`CONTINUE`，再取得新授权 |

`ITER-010-RESULT-SLICE-001-STOP-REDIRECT` 保留 Slice1 的执行事实和答案/审核 FAIL；[PDR-001](../decisions/PDR-001-resume-as-rework.md)
纠正了把旧用户消息推断成明确 `REDIRECT` 的项目决定。`32b298de…` 曾恢复旧设计编码，PDR-004 随后暂停该权威；`f76ba3e8…` 现已在
新 Agent/Chat Readiness 上重新授权 Slice1。PDR-005 允许全新开发对话接手，PDR-006 要求阶段交付前持续推进并在真正的权限缺口处直接
申请，PDR-007 禁止把持续执行解释成峰时 DeepSeek 调用；三者都不扩大外部权限、不重置旧失败。现有持续单轮问答不能冒充 Chat。
Slice2/3 从未授权，继续保持 proposed。
