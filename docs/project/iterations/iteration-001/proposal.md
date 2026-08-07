---
id: ITER-001-PROPOSAL
kind: iteration-proposal
status: completed
authority: historical-project
owners: [product, engineering]
depends_on: [SYS-PRODUCT-SUCCESS, SYS-ARCH-INVARIANTS]
code: [src/software_world_model]
tests: [tests, validation]
iteration: ITER-001
migration: reconstructed-from-existing-iteration-records
---

# Iteration 001 Proposal：正式知识单路径的最小产品闭环

## Trigger and evidence

历史架构 Demo 证明模块边界可行，但首轮产品留出仅 `33.75 / 50`，暴露了正式知识覆盖、目标绑定、逐 Need 充分性、模型隔离和答案复核不足。需要用生产模块化单体完成一个不依赖来源旁路的端到端切片，并在陌生工程上与直接源码调查比较。

## Outcome

用户能够连接精确 Local Git 来源，通过受控来源调查形成正式知识；后续回答固定 Snapshot、逐 Need 判断充分性、独立审核并在本机浏览器交付。管理 CLI 只提供配置、更新和知识查询入口，不冒充自然语言答案交付路径。系统答案在相同资源约束下不得低于直接调查基线。

## Scope

- Source/Binding 配置、精确 Git Target 和受控只读 Artifact；
- INITIAL Schema 下 Evidence、Entity、Fact、Inference、Admission 与原子 Snapshot；
- 任务驱动 Knowledge Update、Knowledge Use、Gap 和全量重评；
- Agentic Task、Answer Candidate、独立 Review 与幂等交付；
- no-tools Model Gateway、Ark Chat Adapter、CC、CE 和未见任务 Product Validation；
- 仅回环地址的本机浏览器体验。

## Non-goals

生产网络部署、认证/多租户、Schema Evolution、专门 Semantic View、跨 Scope 原子事务、物理 Cleanup/Projection、通用 Workflow 平台和自动生产启用。

## Acceptance

生产测试与历史 Demo 分别通过；exact Adapter Live CC 通过；通用模型职责 CE 通过；冻结陌生工程上的系统答案逐题不低于同条件直接调查答案且无重大错误；本机体验安全关闭边界成立。生产 Activation 不属于本轮完成定义。
