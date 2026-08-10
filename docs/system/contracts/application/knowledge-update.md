---
id: SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE
kind: system-contract
status: current
authority: normative
owners: [application]
depends_on: [SYS-CONTRACT-SOURCE-ARTIFACT, SYS-CONTRACT-KNOWLEDGE-SNAPSHOT-PUBLICATION, SYS-CONTRACT-KNOWLEDGE-ADMISSION, SYS-CONTRACT-X-CAPABILITY-EXECUTION, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
derived_from: [DD-APP-KNOWLEDGE-UPDATE]
code: [src/software_world_model/application_services/knowledge_update.py, src/software_world_model/infrastructure/sqlite_knowledge_update_repository.py]
tests: [tests/test_knowledge_update.py]
---

# Knowledge Update

## Purpose and scope

Knowledge Update 用同一契约处理首次构建和后续更新：从显式授权的 Build Objective 出发，可选绑定 Requirement Gap / Requirement，并把目标解析为 Canonical Build Target；随后经受控来源调查、Candidate、Admission、Application Acceptance 和 Publication 形成新 Snapshot。它是显式或后台知识沉淀能力，不是同步 Evidence Answer 的前置门禁。Knowledge Use 不得因缺少知识而隐式访问 Source。

## Ownership

Application 拥有 Update Attempt、Publication Policy、编排和 Result；具体 Capability Strategy 归提供该能力的业务模块。Source Integration 止于 Artifact；Knowledge Engine 独占 Evidence、Candidate Admission 与 Snapshot Publication。

## Invariants

1. Build Target Proposal、Canonical Target、Build Intent、Application Acceptance 与 Sufficiency 是不同对象，不能互相推导。
2. Attempt 固定 Scope、Binding、expected current、Schema、Context、Catalog、Target、资源授权和全部 exact upstream Snapshot dependencies；分派前重新校验 exact Scope / Binding Assertion。
3. 模型只提出调查或知识 Candidate；Source Tool 由平台逐步授权，预算、观察和停止可回放。
4. Candidate 和半成品不得进入 Knowledge Use；最终 Bundle 必须完整封存，批处理不能静默丢项。
5. Admission ACCEPT、Application PASS 与 PUBLISHED 三门分离；发布成功也不证明原 Requirement 已充分。
6. Target Coverage 绑定 exact source → Artifact → Candidate → Publication Member；无关同类知识不能冒充目标覆盖。
7. Schema 变化形成新 Candidate/Snapshot；在 Evolution Contract 接受前，不执行跨 Schema Adoption。
8. 每次 Publication 只在单个 Scope 内原子完成，不建立跨 Scope 事务；跨 Scope 依赖始终固定 exact upstream Snapshot。
9. 对任务驱动的更新，Knowledge Use / 调用方在收到 Publication Receipt 后使用其 exact Snapshot 新建 Read Session、推进 Use Epoch，并对全部 Need 重新评估；Knowledge Update 不拥有 Sufficiency Decision。

## Failure, recovery and implementation boundary

歧义、越界、预算耗尽、无进展、部分 Candidate、CAS 冲突或审核失败均保持旧 CURRENT。任一已分派的 Source Operation、Model Call 或 Publication 结果不可证明时，Update Result 保持 `OUTCOME_PENDING/UNKNOWN`；恢复必须查询或继续原 Attempt 与原幂等键，在解析前不得重发同一副作用、创建竞争发布或报告确定失败。旧 CURRENT 保持可读不等于该 Attempt 已失败。对象字段、Tool-loop 算法、状态机和错误表由代码与测试定义。
