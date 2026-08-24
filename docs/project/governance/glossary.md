---
id: PROJECT-GOVERNANCE-GLOSSARY
kind: project-governance
status: current
authority: project-governance
owners: [documentation]
depends_on: [PROJECT-GOVERNANCE-DOCUMENTATION]
code: []
tests: []
---

# 术语

| 术语 | 含义 |
|---|---|
| Baseline | 由精确 Git Commit 或外部对象 Digest 固定、可供验证和回退的一致状态 |
| Manifest | 一轮迭代采用的 System IDs、外部对象、证据和有效期清单 |
| Roadmap Candidate | 值得评估但尚未授权编码的未来结果方向 |
| Iteration | 有独立 Outcome、范围、开发设计、验证和裁决的一轮变化 |
| Development Slice | 当前迭代中可独立编码和验证的最小纵向切片 |
| Finding | 实现/测试中新发现且需要分类处置的事实 |
| ADR | 解释长期系统架构选择及后果的决策记录 |
| PDR | 只影响项目、迭代或实施路径的决策记录 |
| CC | Adapter/Provider 的 Contract Conformance，不证明业务能力 |
| CE | 精确 Strategy 的 Capability Evaluation，不证明产品验收 |
| Product Validation | 冻结用户任务上的端到端产品下限验证 |
| Activation | 把有效资格授权到明确环境、范围和期限的独立决定 |
| `OUTCOME_UNKNOWN` | 外部调用已可能发生但结果尚不可证明；不是失败或零消耗 |
| current | 当前规范/导航生效；不自动表示生产已实现或启用 |
| authorized | 已有明确授权且必需输入闭合；只有与 `current.md` 指针共同成立时才成为当前编码输入 |
| paused | 当前阶段有保留证据和明确返工路径，但没有编码授权；新收据到达后可恢复同一 Slice |
| REWORK | 目标和核心架构仍成立，当前缺陷在同一 Slice 做通用修复；只阻止晋级，不等于转向或拒绝 |
| superseded | 从未执行的计划被后续项目决定替代；不得用于隐藏已经发生的失败 |
| 可体验版本 | 一条固定方式可重复启动、固定本地地址持续服务、同会话连续自由操作、版本/限制可见且单次失败不关闭服务的真实产品版本 |
| amended | 历史决定仍成立，但其部分范围被后续决定修订；不同于完整 superseded |
| not-reconstructed | 迁移时没有伪造缺失的逐条历史记录；空索引不等于机械证明全部关闭 |
| historical-* authority | 只描述已经发生且不可回写的项目/开发事实，不拥有当前 System 语义 |
| `coding_input` | 防止 Roadmap、Proposal 或模板被误作编码授权的机器门；单独为 true 也不能替代 Readiness 与 current 指针 |
