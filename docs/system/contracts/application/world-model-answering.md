---
id: SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING
kind: system-contract
status: current
authority: normative
owners: [application, quality]
depends_on: [SYS-ADR-014, SYS-ADR-015, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-STRUCTURE-VIEW, SYS-CONTRACT-APPLICATION-BEHAVIOR-VIEW, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY, SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
code: [src/software_world_model/application_services, src/software_world_model/ai_infrastructure/world_model_answer_strategy.py, src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, src/software_world_model/interface]
tests: [tests/test_knowledge_use.py, tests/test_browser_chat_interface.py, tests/test_world_model_answering.py, tests/test_world_model_evaluation.py, tests/test_world_model_answer_strategy.py, tests/test_iteration_003_g3a_integration.py, tests/test_iteration_006_capability_qualification.py, tests/test_iteration_007_capability_qualification.py, tests/test_java_source_semantics.py, tests/test_world_model_gateway_authorization.py]
---

# World Model Answering

## Purpose and scope

本契约定义 `WORLD_MODEL` 自然语言回答：从原问题形成不可变 Requirement/Needs，在一个 exact Snapshot 或有序 exact Snapshot Read Set 的已验证 Snapshot Read Bundle 上执行受控正式查询/View，综合可读答案并独立复核。它不调查 Source、不形成知识，也不触发更新。

## Ownership

Application 拥有 World Model Question、Requirement Revision、validated Query Plan、Read Session/Set 和 Query Result；
Structure/Behavior View 只执行与 Bundle Profile 匹配的通用只读操作；Response Control 独占 Answer Draft、Review、
Authorization 与 Delivery。模型只能提出 Requirement、Query Plan、Draft 或 Review Proposal。

## Invariants

1. Request 固定 `WORLD_MODEL`、原问题、响应语言、Scope、Snapshot selector/read-set selector、Profile、权限和资源上限；模式不能在 Attempt 内变化。
2. Requirement 必须保留全部问题、条件、比较、关系和输出约束。每个 Need 显式映射到一个或多个 validated generic View/query operation，或映射到明确 Knowledge Gap。
3. Query Plan 只能选择 Capability Registry 对当前 Profile 已接受的通用操作，例如 entity candidates、module/method inventory、direct neighborhood、path existence、all simple paths、ordered snapshot diff、`implementation_candidates` 与 `method_implementation`。模型 proposal contract 必须同时绑定 Profile、capability/Strategy version、Prompt、proposal vocabulary 与 exact operation set；Profile 引入新操作或改变映射时必须形成新 contract 和 closed Capability Evaluation，旧 qualification 不得继承、fallback 或通过放宽 Gateway policy 复用。自然语言 exact mention 必须先经过同一 Read Session 的受控 entity lookup；功能发现候选则按 Implementation Query Contract 保留 0/N 集合与排名依据。后续模型只提出 semantic intent；typed argument 只接受用户给出的 exact Ref 或同一 Session 已密封 Result 中由 Application deterministic 编译的 Ref，不能由模型猜造、复制或重建。Application 重新校验 Snapshot、Result/EntityRef、predicate/modality、方向、分页和预算；工程名、固定问题文本或显示名称不能成为隐藏分支。
4. Query Result 固定 exact Read Session/Set、Read Bundle digest、operation inputs、Coverage、completeness、Support Map 和 digest。答案进程不挂载权威数据库或 Evidence Store，网络默认拒绝；真实模型阶段只能通过 Manifest 固定的 exact Model Egress Gateway 访问已取得资格的 Provider endpoint，不能直连 DNS、公网、Source remote 或 Citation Projector。模型无 Source、Repository、Artifact/Evidence 内容或 Direct Investigation 工具，只能看到已发布 typed State、Gap 以及 Support ref/locator/digest。独立 Citation Projector 不出网，其 observation 只能进入浏览器展示，且不得回流到答案链。
5. 每个 Answer Claim 必须绑定同一 Query Result 中的正式 Entity/Fact/Gap；所有 Need 和 Joint Constraint 分别评估。部分支持不得被流畅总结扩张为完整答案。
6. 独立 Reviewer 从原问题重建检查项，核对 Requirement fidelity、query completeness、grounding、比较方向、语言和可读性。重写只能使用同一 Read Set/Query Result；缺知识只能返回 Gap，不能补检索源码。
7. Requirement、Query Plan、Query Result、Need Assessment、Draft、Review、Authorization 和 Delivery 都保存稳定引用与 digest，可供人工重建完整权威链。
8. Product Validation 必须包含措辞变化、不同 Entity 标识、同名歧义、负向/无路径和不受支持问题；同一核心实现不得按工程、commit 或冻结题目硬编码答案。
9. `JAVA_SOURCE_SEMANTICS@1` 的 bounded-investigation Strategy 每个成功 Delivery 使用隔离角色且不重试：
   1. Investigation 执行 2—4 个模型回合。第一个回合只读取原问题、语言、exact Read Authority、Profile/capability schema 与
      operation vocabulary，并提出通用 search terms 与一个由注册 operation/relation 表达的 bounded evidence-request 集合；该集合
      描述原问题需要的方法、声明清单、直接关系或路径证据，不是题型 enum，也不含 Ref、bound 或隐藏答案。Application 做
      operation-discriminated normalization、去重、依赖收敛和预算可达性校验后将它冻结。candidate discovery 是强制首 transition，
      不单独构成 canonical terminal evidence；raw `implementation_candidates` evidence alias 一律向上归一为 `method_implementations`，
      从而不允许非零候选仅凭存在性结束，同时不对零候选/截断结果执行伪查询。之后每回合只增加前一轮 sealed typed result、
      冻结 evidence ledger、progress/budget receipt、平台计算的三层 completeness projection、当前受限 `available_operations` 与完整
      trace digest。模型不输出 step/trace/Snapshot、Result binding、Entity Ref、direction/predicate 或 graph bounds。search terms 必须覆盖问题中的动作、
      对象、顺序/审计、分支、return/throw 等物质概念；通用 canonical term 可以归一语言/词形，但不得加入工程、题目或符号专用词典；
      平台在最多 12 个 raw term 的输入上按 Unicode casefold 去重并保留首次拼写/顺序，该无损规范化不得改变权限、
      Snapshot、operation 或 query bound；Ref 和其他 authority collection 仍严格拒绝重复；
   2. Application 从冻结 evidence ledger、sealed Result 和剩余预算 deterministic 推导当前合法 transition 子集，并编译一个完整 typed
      proposal；固定模型 envelope 中越出该子集的 operation/FINISH/terminal reason 只作为不可信 raw output 审计，不获得查询、终态或
      完整性解释权力。Application
      在每轮前后校验 operation shape、Snapshot/Bundle、Ref provenance、query/result bytes、Support、progress/cycle、trace bytes、
      wall time、调用预算与 obligation fulfillment。Result 未密封不得进入下一回合；只有义务已覆盖或没有合法 evidence-reducing
      transition 才允许 `FINISH`，且至少发生在一个已执行调查 Result 之后并占用一个回合，因此 candidate Result 已关闭全部义务时
      1 query + FINISH 是合法的 2-call investigation；`remaining_budget=1` 仍允许 ledger 中最后一个能减少明确证据缺口的 query；该
      query 执行后由 Session 自动密封
      `LIMITATION / INVESTIGATION_BUDGET_EXHAUSTED`，不再要求第五个 `FINISH` 回合。cycle 以已执行 operation 与 exact Result progress
      token 判定，不能仅因两个不同 sealed state 选择同名 operation 而推导；
   3. Draft Call 只读取原问题、不可变 Requirement、完整 sealed trace、Need Assessment 和允许的 Support/Gap，生成逐 Claim 绑定的
      Draft；它不读取 Source、调查角色私有输出、Citation observation 或 Reviewer；
   4. Review Call 在全新上下文中读取原问题、同一 Requirement/trace/assessment 和 Draft，独立核对 fidelity、候选与查询完整性、
      grounding、方向、三层负向证明、语言与可读性。
   completeness projection 只能来自同一正式 Read Authority 的平台判定，不得把评测 Oracle identity 或隐藏期望送入 Answer。
   Review finding code 必须来自版本化 vocabulary；遗漏候选/方法、查询未穷尽、无依据负向结论、静态事实不支持的运行时断言与
   Source/Evidence payload 展开使用不同稳定 code。Schema 和 Application 同时拒绝未注册、重复或乱序 code。平台在每次 Call 前后
   重验 role package、input/output schema、Snapshot/Bundle/result/trace digest、operation/Support allowlist 和 grant。实际 Provider
   调用数为 4—6（Investigation 2—4、Draft 1、Review 1），每次有唯一 receipt；supervisor 预建的上限 6 个 connected descriptor
   只能按角色顺序消费，未用 descriptor 必须销毁并审计。任一 Call/validation 未完成即停止后续角色，不 retry、不降级为
   deterministic answer、旧三调用 Strategy 或 Direct Investigation。
10. `BOUNDED_ABSENCE` 必须同时绑定 Query result completeness、Knowledge representation Coverage 与 Business discovery recall 三个
    独立 COMPLETE verdict。零候选、空页、`truncated=false` 或全局 Coverage COMPLETE 中任一项单独都不充分；未知层必须形成具体
    Limitation，执行/权限失败不能伪装成 Gap。

## Failure and implementation boundary

模式漂移、Read Set 不兼容、未知操作、EntityRef provenance 不成立、查询/trace 不完整、无进展或 cycle、Support/byte/time/call 预算
越界、Need 遗漏、审核未知或调用熔断均失败关闭。DTO、planner 算法和通用 operation catalog 由代码与测试定义，但不能改变以上
固定输入、三层完整性、预算和无 Source 边界。
