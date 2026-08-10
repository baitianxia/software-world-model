---
id: SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE
kind: system-contract
status: current
authority: normative
owners: [application]
depends_on: [SYS-CONTRACT-KNOWLEDGE-PERSISTENCE, SYS-CONTRACT-KNOWLEDGE-SNAPSHOT-PUBLICATION, SYS-CONTRACT-KNOWLEDGE-CONTEXT-COMPARISON, SYS-CONTRACT-X-CAPABILITY-EXECUTION, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
derived_from: [DD-APP-KNOWLEDGE-USE]
code: [src/software_world_model/application_services/knowledge_use.py, src/software_world_model/application_services/structure_read_session.py, src/software_world_model/application_services/structure_read_bundle.py, src/software_world_model/infrastructure/sqlite_knowledge_use_repository.py, src/software_world_model/infrastructure/sqlite_structure_read_session_repository.py, src/software_world_model/infrastructure/sqlite_structure_read_bundle_repository.py, src/software_world_model/infrastructure/file_structure_read_bundle.py, src/software_world_model/interface/runtime.py, src/software_world_model/interface/cli.py, src/software_world_model/interface/presenters.py]
tests: [tests/test_knowledge_use.py, tests/test_natural_task.py, tests/test_structure_read_session.py, tests/test_structure_read_bundle.py, tests/test_iteration_003_g1_integration.py, tests/test_iteration_003_g2_integration.py]
---

# Knowledge Use 与 Sufficiency

## Purpose and scope

Knowledge Use 在固定 Requirement 和 Snapshot 上读取已发布正式知识，逐 Need 判断支持是否充分并形成可重建 Proof 或 Knowledge Gap。`WORLD_MODEL` 回答只能消费该固定读取结果或受控只读 View；它不读取来源、Artifact 内容、Evidence Packet 或模型记忆补齐知识。Direct Evidence Answering 使用独立契约，不把任务级 Packet 伪装为 Snapshot。

## Ownership

Application 拥有 Requirement Revision、Read Session、Query Result、Need Assessment、Gap、Sufficiency 与 Use Epoch；Knowledge Engine 提供 exact Snapshot 的只读正式知识，并拥有 Session 所引用的 Context Comparison Assessment 与其 Validity。Application 可以声明比较顺序和保存 Assessment，但不能决定兼容 Outcome。

## Invariants

1. Requirement Revision 不可变且不得在执行中弱化；Need 与 Joint Constraint 全部进入评估，不能依据当前 Snapshot 已有内容反向删减问题。
2. 普通 Session 打开后固定 exact Scope/Snapshot、Schema、Context、授权与 Coverage；比较 Session 固定同一 Scope 下有明确 base/target 顺序的 exact Snapshot Read Set，并逐个验证 Schema/Profile/Context 可比较性。隔离读取还必须固定并验证 no-payload Snapshot Read Bundle digest 与其完整成员绑定。每个 `CURRENT` 只解析一次，Read Set 打开后不随指针漂移。
3. 多 Scope 使用固定 compatible exact Snapshot set，不获得跨 Scope 隐式一致性。
4. 空、部分、截断、权限过滤或分页未完成不能形成否定结论。
5. 每个 satisfied Need 都有同一 Session 可重建的 Support Proof；全部 Need/Joint 满足后才能整体 `SUFFICIENT`。
6. Gap 只表示有效 Session 中正式知识对 exact Requirement 的语义不足，不代表现实或来源中不存在答案；Access、Execution、Session、Schema 或权限失败是 Limitation / Failure，不能伪装成 Gap 或 satisfied。
7. 调用方提供新的 exact Publication Receipt 后，Knowledge Use 创建新 Session、增加 Use Epoch 并全量重评；旧部分 Assessment 不继承。Knowledge Use 不触发更新，也不访问来源。
8. Context compatibility 与 Schema readability 是独立门禁；历史 Result 不能绕过当前权限。
9. Sufficiency 与 Requirement formation、investigation / update、answer drafting 和 answer review 使用隔离输入与 Decision Chain；生成或调查方不能自证完整，即使复用同一基础模型也不能复用权威上下文。
10. Formal query 对 Relation Fact 必须返回 typed endpoints、Fact Root/State、Support 与完整性状态；调用方不得通过名称匹配重建图。
11. 世界模型模式遇到 Knowledge Gap 时只返回 Gap 或受支持的部分结果，不触发 Update 或 Direct Investigation。用户随后显式更新或直接调查会形成新的 Attempt/Result，不能改写原查询事实。

## Failure and implementation boundary

Snapshot 漂移、Proof 越界、重复/遗漏 Need、Context/Schema 不成立或分页不完整均拒绝 Sufficiency。DTO、Cursor、查询算法和状态由代码与测试定义。
