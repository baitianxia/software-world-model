---
id: SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE
kind: system-contract
status: current
authority: normative
owners: [application]
depends_on: [SYS-CONTRACT-KNOWLEDGE-PERSISTENCE, SYS-CONTRACT-KNOWLEDGE-SNAPSHOT-PUBLICATION, SYS-CONTRACT-KNOWLEDGE-CONTEXT-COMPARISON, SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS, SYS-CONTRACT-X-CAPABILITY-EXECUTION, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
derived_from: [DD-APP-KNOWLEDGE-USE, FINDING-010-136]
code: [src/software_world_model/application_services/knowledge_use.py, src/software_world_model/application_services/structure_read_session.py, src/software_world_model/application_services/structure_read_bundle.py, src/software_world_model/application_services/read_set_catalog.py, src/software_world_model/application_services/engineering_question_cognition.py, src/software_world_model/infrastructure/sqlite_knowledge_use_repository.py, src/software_world_model/infrastructure/sqlite_structure_read_session_repository.py, src/software_world_model/infrastructure/sqlite_structure_read_bundle_repository.py, src/software_world_model/infrastructure/sqlite_maven_workspace_repository.py, src/software_world_model/infrastructure/file_structure_read_bundle.py, src/software_world_model/infrastructure/file_read_set_catalog.py, src/software_world_model/interface/runtime.py, src/software_world_model/interface/cli.py, src/software_world_model/interface/read_set_catalog_cli.py, src/software_world_model/interface/presenters.py]
tests: [tests/test_knowledge_use.py, tests/test_natural_task.py, tests/test_structure_read_session.py, tests/test_structure_read_bundle.py, tests/test_engineering_question_cognition.py, tests/test_maven_workspace.py, tests/test_iteration_003_g1_integration.py, tests/test_iteration_003_g2_integration.py]
---

# Knowledge Use 与 Sufficiency

## Purpose and scope

Knowledge Use 在固定 Requirement 和 Snapshot 上读取已发布正式知识，逐 Need 判断支持是否充分并形成可重建 Proof 或 Knowledge Gap。`WORLD_MODEL` 回答只能消费该固定读取结果或受控只读 View；它不读取来源、Artifact 内容、Evidence Packet 或模型记忆补齐知识。Direct Evidence Answering 使用独立契约，不把任务级 Packet 伪装为 Snapshot。

## Ownership

Application 拥有 Requirement Revision、Read Session、Queryable Read Set Registration、Query Result、Need Assessment、Gap、
Sufficiency 与 Use Epoch；Knowledge Engine 提供 exact Snapshot 的只读正式知识，并拥有 Session 所引用的 Context Comparison
Assessment 与其 Validity。Application 可以声明比较顺序和保存 Assessment，但不能决定兼容 Outcome。Source-off Catalog 是
这些 Registration 的密封传输 manifest，不拥有或重解释正式知识。

Engineering Conversation 的 Cognition Binding 可以引用同一 repository Binding 与 exact revision 上一个或多个 profile-specific exact
Read Authority。每次查询仍在各自 Schema/Profile/Read Set Contract 内执行；Application 只组合逐项保留 authority、Profile、Coverage、
Support 和 Unknown 的只读投影，不创建 mixed-profile Snapshot/Read Set，也不执行跨 Schema Adoption。

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
12. 只有已提交 exact Snapshot/ordered Session、全部 Coverage `COMPLETE`、Bundle Availability `AVAILABLE`，且 Bundle
    Receipt 与文件 manifest 已机械验证时，Application Knowledge Use 才能建立 immutable queryable Read Set
    Registration。单 Snapshot 与 ordered base→target 的 ID 和顺序均固定；后续 CURRENT 或 Catalog current pointer 移动
    不改变已登记或已选择的 Read Set。
13. Source-off Catalog canonical schema 固定为 `SWM-READ-SET-CATALOG@1`。文档顶层只包含 schema、catalog ID/revision、
    producer commit/tree、generated-at、entries、previous catalog digest 与 document digest；Entry 只包含 read-set、
    workspace、Scope、ordered Snapshot/source revision、Schema/Context/Profile/Coverage ref+digest、完整 Bundle Receipt、
    Bundle-root-relative normalized locator、完整 file manifest/digest 与 availability。自由扩展字段、repository/source/authority
    DB locator、Entity/Fact、Evidence/Artifact payload 均拒绝。
14. Trusted Knowledge Use 先以 canonical encoding 写 immutable Catalog manifest，再以 compare-and-set 更新只含 exact
    catalog ID/revision/digest 的 current pointer。读取方必须重算 document digest、验证 pointer、Entry、embedded Receipt 和
    Bundle file manifest 后才枚举；Catalog 缺失可由 Owner Registration/Receipt 重建，不能成为第二权威。
15. `READ_BUNDLE_UNAVAILABLE`、非 COMPLETE Coverage、Receipt/file digest 漂移、非规范 locator、Catalog tamper 或 stale
    pointer CAS 均不得进入 queryable Catalog；失败不删除旧 Catalog 或旧 queryable Read Set。
16. 对带 unit disposition/facet completeness 的 Profile，全局 `COMPLETE` 只证明授权单元分类 manifest 完整。Application 必须按
    exact method/facet completeness 判断穷尽或负向结论；`UNSUPPORTED_EXCLUDED`/`FAILED` 的缺失事实只能形成 Limitation/Gap，
    不能被空查询结果解释为“没有”。
17. Result-driven investigation 的每个 typed result 必须绑定前一 trace digest、canonical operation/input、稳定 total/returned/
    truncated/cursor、Coverage/facet disposition、Support、serialized byte count 与 progress token。Query result completeness、
    Representation Coverage、Business discovery recall 是三个不同 Verdict；只有三者都由独立 Oracle 判为 COMPLETE，Application 才能
    把零结果解释为 `BOUNDED_ABSENCE`。Agent、自报 trace、排名或分页结束不能拥有这些 Verdict。
18. 用于工程 Chat 的 Cognition Capability Manifest 必须固定 exact repository/revision、ordered profile-specific Read Authorities、每个
    Profile 的 Schema/Context/Coverage/digest、允许的 query/view capability+version、已覆盖认知维度和显式 unsupported/partial/unknown。
    Question Eligibility Assessment 必须先从原问题的 material Need 得到所需维度，再与该 Manifest 对照；单个窄 Profile 的
    `COMPLETE`、同一整包记录或 Source 命中均不能补成多域认知资格。Source 可以支持当前 Turn，却不得被回填为 World Model 贡献。

## Failure and implementation boundary

Snapshot 漂移、Proof 越界、重复/遗漏 Need、Context/Schema 不成立或分页不完整均拒绝 Sufficiency。DTO、Cursor、查询算法和状态由代码与测试定义。
