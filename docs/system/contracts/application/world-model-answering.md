---
id: SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING
kind: system-contract
status: current
authority: normative
owners: [application, quality]
depends_on: [SYS-ADR-014, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-STRUCTURE-VIEW, SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
code: [src/software_world_model/application_services, src/software_world_model/ai_infrastructure/world_model_answer_strategy.py, src/software_world_model/interface]
tests: [tests/test_knowledge_use.py, tests/test_browser_chat_interface.py, tests/test_world_model_answering.py, tests/test_world_model_evaluation.py, tests/test_world_model_answer_strategy.py, tests/test_iteration_003_g3a_integration.py]
---

# World Model Answering

## Purpose and scope

本契约定义 `WORLD_MODEL` 自然语言回答：从原问题形成不可变 Requirement/Needs，在一个 exact Snapshot 或有序 exact Snapshot Read Set 的已验证 Snapshot Read Bundle 上执行受控正式查询/View，综合可读答案并独立复核。它不调查 Source、不形成知识，也不触发更新。

## Ownership

Application 拥有 World Model Question、Requirement Revision、validated Query Plan、Read Session/Set 和 Query Result；Structure View 只执行通用只读操作；Response Control 独占 Answer Draft、Review、Authorization 与 Delivery。模型只能提出 Requirement、Query Plan、Draft 或 Review Proposal。

## Invariants

1. Request 固定 `WORLD_MODEL`、原问题、响应语言、Scope、Snapshot selector/read-set selector、Profile、权限和资源上限；模式不能在 Attempt 内变化。
2. Requirement 必须保留全部问题、条件、比较、关系和输出约束。每个 Need 显式映射到一个或多个 validated generic View/query operation，或映射到明确 Knowledge Gap。
3. Query Plan 只能选择 Capability Registry 已接受的通用操作，例如 entity candidates、inventory、direct neighborhood、path existence、all simple paths 和 ordered snapshot diff。自然语言 mention 必须先经过同一 Read Session 的受控 candidate lookup；后续 typed argument 只接受用户给出的 exact Ref 或已密封的唯一 candidate。0/N 候选形成 Entity Resolution Limitation，不能由模型猜选。Application 重新校验 Snapshot、EntityRef、方向、分页和预算；工程名、固定问题文本或显示名称不能成为隐藏分支。
4. Query Result 固定 exact Read Session/Set、Read Bundle digest、operation inputs、Coverage、completeness、Support Map 和 digest。答案进程不挂载权威数据库或 Evidence Store，网络默认拒绝；真实模型阶段只能通过 Manifest 固定的 exact Model Egress Gateway 访问已取得资格的 Provider endpoint，不能直连 DNS、公网、Source remote 或 Citation Projector。模型无 Source、Repository、Artifact/Evidence 内容或 Direct Investigation 工具，只能看到已发布 typed State、Gap 以及 Support ref/locator/digest。独立 Citation Projector 不出网，其 observation 只能进入浏览器展示，且不得回流到答案链。
5. 每个 Answer Claim 必须绑定同一 Query Result 中的正式 Entity/Fact/Gap；所有 Need 和 Joint Constraint 分别评估。部分支持不得被流畅总结扩张为完整答案。
6. 独立 Reviewer 从原问题重建检查项，核对 Requirement fidelity、query completeness、grounding、比较方向、语言和可读性。重写只能使用同一 Read Set/Query Result；缺知识只能返回 Gap，不能补检索源码。
7. Requirement、Query Plan、Query Result、Need Assessment、Draft、Review、Authorization 和 Delivery 都保存稳定引用与 digest，可供人工重建完整权威链。
8. Product Validation 必须包含措辞变化、不同 Entity 标识、同名歧义、负向/无路径和不受支持问题；同一核心实现不得按工程、commit 或冻结题目硬编码答案。

## Failure and implementation boundary

模式漂移、Read Set 不兼容、未知操作、EntityRef 歧义、查询不完整、Support 越界、Need 遗漏、审核未知或调用熔断均失败关闭。DTO、planner 算法和通用 operation catalog 由代码与测试定义，但不能改变以上固定输入、完整性和无 Source 边界。
