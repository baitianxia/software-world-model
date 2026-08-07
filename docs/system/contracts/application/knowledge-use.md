---
id: SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE
kind: system-contract
status: current
authority: normative
owners: [application]
depends_on: [SYS-CONTRACT-KNOWLEDGE-PERSISTENCE, SYS-CONTRACT-KNOWLEDGE-SNAPSHOT-PUBLICATION, SYS-CONTRACT-KNOWLEDGE-CONTEXT-COMPARISON, SYS-CONTRACT-X-CAPABILITY-EXECUTION, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
derived_from: [DD-APP-KNOWLEDGE-USE]
code: [src/software_world_model/application_services/knowledge_use.py, src/software_world_model/infrastructure/sqlite_knowledge_use_repository.py]
tests: [tests/test_knowledge_use.py, tests/test_natural_task.py]
---

# Knowledge Use 与 Sufficiency

## Purpose and scope

Knowledge Use 在固定 Requirement 和 Snapshot 上读取已发布正式知识，逐 Need 判断支持是否充分并形成可重建 Proof 或 Gap。它不读取来源、Artifact、Evidence Quote 或模型记忆补齐答案。

## Ownership

Application 拥有 Requirement Revision、Read Session、Query Result、Need Assessment、Gap、Sufficiency 与 Use Epoch；Knowledge Engine 提供 exact Snapshot 的只读正式知识。

## Invariants

1. Requirement Revision 不可变且不得在执行中弱化；Need 与 Joint Constraint 全部进入评估，不能依据当前 Snapshot 已有内容反向删减问题。
2. Session 打开后固定 exact Scope/Snapshot、Schema、Context、授权与 Coverage；`CURRENT` 只解析一次。
3. 多 Scope 使用固定 compatible exact Snapshot set，不获得跨 Scope 隐式一致性。
4. 空、部分、截断、权限过滤或分页未完成不能形成否定结论。
5. 每个 satisfied Need 都有同一 Session 可重建的 Support Proof；全部 Need/Joint 满足后才能整体 `SUFFICIENT`。
6. Gap 只表示有效 Session 中正式知识对 exact Requirement 的语义不足，不代表现实或来源中不存在答案；Access、Execution、Session、Schema 或权限失败是 Limitation / Failure，不能伪装成 Gap 或 satisfied。
7. 调用方提供新的 exact Publication Receipt 后，Knowledge Use 创建新 Session、增加 Use Epoch 并全量重评；旧部分 Assessment 不继承。Knowledge Use 不触发更新，也不访问来源。
8. Context compatibility 与 Schema readability 是独立门禁；历史 Result 不能绕过当前权限。
9. Sufficiency 与 Requirement formation、investigation / update、answer drafting 和 answer review 使用隔离输入与 Decision Chain；生成或调查方不能自证完整，即使复用同一基础模型也不能复用权威上下文。

## Failure and implementation boundary

Snapshot 漂移、Proof 越界、重复/遗漏 Need、Context/Schema 不成立或分页不完整均拒绝 Sufficiency。DTO、Cursor、查询算法和状态由代码与测试定义。
