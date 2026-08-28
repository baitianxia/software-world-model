---
id: ITER-010-DEVELOPMENT-DESIGN
kind: development-design-index
status: current
authority: project-plan
owners: [engineering, architecture, product, quality]
depends_on: [ITER-010-PROPOSAL, ITER-010-READINESS, ITER-010-VERIFICATION, ITER-010-RESULT-SLICE-001-STOP-REDIRECT, FINDING-010-107, FINDING-010-108, FINDING-010-109, FINDING-010-110, FINDING-010-132, FINDING-010-133, FINDING-010-134, FINDING-010-135, FINDING-010-136, FINDING-010-137, FINDING-010-138, FINDING-010-140, FINDING-010-141, FINDING-010-153, ITER-010-PDR-001, ITER-010-PDR-004, ITER-010-PDR-005, ITER-010-PDR-006, ITER-010-PDR-007, ITER-010-PDR-008, ITER-010-PDR-009, ITER-010-PDR-010, PROJECT-GOVERNANCE-PLAN-EXECUTION]
code: []
tests: []
iteration: ITER-010
coding_input: true
---

# ITER-010 Development Design

当前处于 `PDR-010 complete MVP experience first / machine-enforced unique action / direction-exploration`，hardening 未解锁。可启动 Chat 页面、
分层归因、结构+实现/行为 Cognition 资格和执行配置本地准入已经有证据；run-035—043 及 v7 继续作为失败/隔离输入。

新的开发对话直接执行完整体验版开发。Manifest v2 为可信父提交连续性保留机器 ID
`ITER-010-ACTION-USER-PLAN-RECOVERY-001`，但当前 Case 已是 `V-MVP-EXPERIENCE-001`，不再表示 recovery 或 Activation。该动作允许跨提交
持续实现产品、运行受影响模块测试、执行 current public mall standing scope 内的模型调用并做真实 loopback 浏览器体验；普通失败保持在同一
动作内，先归因再做一次通用修复，不因调用次数或测试未全过停止。

| Slice | 状态 | 目的 | 进入条件 |
|---|---|---|---|
| [SLICE-001](SLICE-001-engineering-qa-direction-preview.md) | `authorized / active / rework / complete experience development` | 先交付软件世界模型 + 主工程 Agent + 受控源码 + Evidence/Review + 语义多轮 Web 的完整 MVP，再在同一候选上做异质问题和 current Codex 定向比较 | 无额外 Activation；产品与 standing-scope 外部执行已解锁，hardening/full regression/第二工程/hidden/Production 仍锁定 |
| [SLICE-002](SLICE-002-cross-project-hardening.md) | `proposed` | Conversation 持久恢复、复杂冲突/去重/异常、跨工程与正式复验 | Slice1 完整体验与方向质量经用户 `CONTINUE` 后再授权 |
| [SLICE-003](SLICE-003-formal-product-acceptance.md) | `proposed` | 未见工程、多轮现场对话、严格 Codex 对照、安全和最终验收 | Slice2 exact Result=`CONTINUE`，再取得新授权 |

`ITER-010-RESULT-SLICE-001-STOP-REDIRECT` 保留 Slice1 的执行事实和答案/审核 FAIL；[PDR-001](../decisions/PDR-001-resume-as-rework.md)
纠正了把旧用户消息推断成明确 `REDIRECT` 的项目决定。`32b298de…` 曾恢复旧设计编码，PDR-004 随后暂停该权威；`f76ba3e8…` 现已在
新 Agent/Chat Readiness 上重新授权 Slice1。PDR-005 允许全新开发对话接手，PDR-006 要求阶段交付前持续推进并在真正的权限缺口处直接
申请，PDR-007 禁止把持续执行解释成峰时 DeepSeek 调用；PDR-008 明确 current public mall scope 不再逐次申请 human grant。四者都不重置
旧失败，standing authority 也不扩大到真正 scope delta。PDR-010 已取代 PDR-009 的 Freeze-first 顺序；完整体验主链必须先形成并立即交给
用户，定向质量比较随后验证同一候选。现有持续单轮问答不能冒充 Chat。
Slice2/3 从未授权，继续保持 proposed。
