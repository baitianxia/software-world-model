---
id: FINDING-010-297
kind: implementation-finding
status: dispositioned
authority: implementation-evidence
owners: [project, architecture, engineering, quality]
depends_on: [SYS-ADR-017]
code: [src/software_world_model/application_services, src/software_world_model/interface, src/software_world_model/ai_infrastructure]
tests: [tests]
iteration: ITER-010
classification: system-contract
disposition: current-system-contract-and-architecture
target: SYS-ARCH-BASELINE
scope: systemic
---

# FINDING-010-297：执行容错被错误提升为应用语义

## Observation

`Model Gateway` 的架构原则要求 Provider、模型和调用方式由基础设施隔离，但当前运行契约又把 `preferred → fallback`、route role、Provider
运行时和 Provider 失败字段放进了 Conversation、Session artifact、Agent executor、Browser projection 和 CLI 组合边界。结果是上层虽然不读取
Provider 名称，却仍然必须理解“首选/备用”并构造两套运行时；Provider 不可用、结构化输出无效和审核失败也容易在错误层被混淆。

## Evidence

- `docs/system/contracts/ai/model-gateway.md` Invariant 10 把有序 route 和 route role 定义为 Session/Application 输入。
- `docs/system/contracts/application/engineering-conversation.md` 的 Binding、Turn 和 Artifact `@4` 要求应用冻结两条 route。
- `ADR-017` 将 preferred/fallback attempt 作为应用可消费的 route 语义。
- `EngineeringChatBrowserApplication.health()`、会话投影和 `EngineeringConversationTurn` 返回 Provider、route、HTTP 和 fallback 字段。
- `engineering_chat_session_artifact.py` 与 alpha CLI 直接构造 Ark/DeepSeek runtime，因此首选路径不能脱离备用路径完成真实入口闭环。

## Root cause

这是跨模块契约边界错误，不是某个 Provider adapter 或某个问题的提示词错误：容错策略的所有权没有停留在 Model Execution Runtime，导致应用层承担了候选选择、
不可用判断、attempt 隔离和 Provider 结果投影。

## Decision / Disposition

接受架构变更 `SYS-ADR-020`。新增唯一的 Provider-neutral `ModelExecutionPort` / Model Execution Runtime 边界：Application、Agent、Session、Artifact、
Response Control、Browser 和 UI 只提交一个 logical interaction，接收一个 logical result 与不透明 execution-audit 引用。Provider candidates、顺序、
availability verdict、admission、attempt isolation、Provider identity、模型和原始 transport evidence 仅由运行时及内部 audit 持有。运行时仍可在受信
不可用裁决后重新启动完整 Agent chain，但上层不得创建、选择或分支 fallback。

本 Finding 不是把旧 route 改名。旧 Provider route classes 只允许作为 infrastructure compatibility adapter；迁移完成前不得新增上层 route 字段、Provider
投影或 Provider-specific 质量规则。迁移按“通用执行端口 → Session/Launcher → Conversation/Browser → 清理旧双路 artifact”推进，每一步须有行为等价和
Provider-transparency 测试。

## Falsifiable acceptance evidence

1. Application/Agent/Session/Browser 的公开对象和 JSON 不再包含 Provider、preferred、fallback、route、model、endpoint 或 Provider HTTP 字段。
2. Provider 选择和完整链 fallback 的行为测试仍证明：首选成功不创建备用 attempt；只有受信不可用才启动一次全链新 attempt；输出无效、Review、Source、权限和安全失败均不切换。
3. 使用两组不同 Provider 配置替换基础设施组合时，Conversation/Agent/Browser 的输入输出契约不变。
4. 旧 route 兼容层只能从 infrastructure composition root 进入；新增 application 代码对 Provider route 的静态泄漏检查失败即阻止提交。

## Alternatives rejected

- 只删除 Browser JSON 中的 Provider 字段：不能修复 Session/Artifact 仍强制两条 route 的根因。
- 将 `preferred/fallback` 改名为 `route-1/route-2`：仍把容错策略暴露给上层。
- 在 Application 内保留候选选择、仅把 Provider 名称隐藏：仍违反单一执行边界，并继续阻塞单路体验。
