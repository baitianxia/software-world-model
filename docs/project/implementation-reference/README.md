---
id: PROJECT-IMPLEMENTATION-REFERENCE
kind: project-reference-index
status: current
authority: historical-evidence
owners: [project, engineering]
depends_on: [PROJECT-DOCUMENTATION-REORGANIZATION, SYS-ARCH-BASELINE]
code: []
tests: []
coding_input: false
---

# 实现与运行参考

这里保存从系统契约或架构附录中归位的 Prompt、Schema、Provider、测试夹具、运行收据和局部实现状态。它们用于追溯迁移和理解历史，不是系统规范、当前开发计划或产品能力证明。

| 来源 | 归位文件 | 归位内容 |
|---|---|---|
| `docs/system/contracts/application/engineering-conversation.md` | `engineering-conversation-history.md` | 当前能力 Profile 的实现细节、运行配置和历史结果 |
| `docs/system/contracts/application/engineering-conversation.md` | `engineering-conversation-contract-pre-v1.4.md` | V1.4 重写前的完整契约原文（协议版本、decoder、排序与预算等局部规则） |
| `docs/system/contracts/application/engineering-question-answering.md` | `engineering-qa-history.md` | 兼容协议的实现状态与历史运行记录 |
| `docs/system/architecture/runtime-flows.md` | `runtime-profile-history.md` | Provider、资格和运行配置实例 |
| `docs/system/architecture/deployment.md` | `deployment-history.md` | 启动器、评测和 OS 隔离实现记录 |
| `docs/system/architecture/invariants.md` | `routing-instance-history.md` | 路由实例和历史实现说明 |
| `docs/system/architecture/domain-model.md` | `domain-implementation-status.md` | View/Profile 的实现与验收状态 |
| `docs/system/architecture/decisions/ADR-018-conversational-engineering-agent.md` | `agent-implementation-history.md` | Agent 候选、测试和历史开发结果 |
| `docs/system/architecture/decisions/ADR-017-transparent-qualified-provider-routing.md` | `provider-routing-history.md` | Provider 路由实例和本地候选状态 |
| `docs/system/architecture/decisions/ADR-019-public-source-standing-model-authority.md` | `standing-authority-history.md` | 持续授权实例和版本迁移记录 |
| `docs/system/architecture/decisions/ADR-015-bounded-world-model-investigation.md` | `world-model-investigation-history.md` | 查询预算、Profile 和传输资格的历史细节 |
| `docs/project/iterations/iteration-010/development-design/SLICE-001-engineering-qa-direction-preview.md` | `iteration-010-slice-001-history.md` | 被当前用户价值纵向计划替代的阶段、运行和验收记录 |
| `docs/system/operations/local-browser.md` | `local-browser-history.md` | 旧浏览器入口、Provider 配置和运行记录 |
| `docs/system/quality/security-boundaries.md`、`docs/system/contracts/ai/model-gateway.md` | `provider-configuration-instances.md` | Provider 到 execution profile 的映射、连接策略与实现证据 |

归位采用“原文保留、来源可追溯、现行入口不引用历史运行状态”的原则。若某段内容改变跨模块职责、权威或不变量，不能在这里修订；应回到 `SYS-ARCH-BASELINE`、相应 ADR 或契约 Owner 文档走正式变更流程。
