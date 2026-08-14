---
id: SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING
kind: system-contract
status: current
authority: normative
owners: [application, quality]
depends_on: [SYS-ADR-014, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-STRUCTURE-VIEW, SYS-CONTRACT-APPLICATION-BEHAVIOR-VIEW, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY, SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
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
3. Query Plan 只能选择 Capability Registry 对当前 Profile 已接受的通用操作，例如 entity candidates、module/method inventory、direct neighborhood、path existence、all simple paths、ordered snapshot diff、`implementation_candidates` 与 `method_implementation`。模型 proposal contract 必须同时绑定 Profile、capability/Strategy version、Prompt、proposal vocabulary 与 exact operation set；Profile 引入新操作或改变映射时必须形成新 contract 和 closed Capability Evaluation，旧 qualification 不得继承、fallback 或通过放宽 Gateway policy 复用。自然语言 exact mention 必须先经过同一 Read Session 的受控 entity lookup；功能发现候选则按 Implementation Query Contract 保留 0/N 集合与排名依据。后续 typed argument 只接受用户给出的 exact Ref 或同一 Session 已密封 candidate result 中的 Ref，不能由模型猜造。Application 重新校验 Snapshot、EntityRef、predicate/modality、方向、分页和预算；工程名、固定问题文本或显示名称不能成为隐藏分支。
4. Query Result 固定 exact Read Session/Set、Read Bundle digest、operation inputs、Coverage、completeness、Support Map 和 digest。答案进程不挂载权威数据库或 Evidence Store，网络默认拒绝；真实模型阶段只能通过 Manifest 固定的 exact Model Egress Gateway 访问已取得资格的 Provider endpoint，不能直连 DNS、公网、Source remote 或 Citation Projector。模型无 Source、Repository、Artifact/Evidence 内容或 Direct Investigation 工具，只能看到已发布 typed State、Gap 以及 Support ref/locator/digest。独立 Citation Projector 不出网，其 observation 只能进入浏览器展示，且不得回流到答案链。
5. 每个 Answer Claim 必须绑定同一 Query Result 中的正式 Entity/Fact/Gap；所有 Need 和 Joint Constraint 分别评估。部分支持不得被流畅总结扩张为完整答案。
6. 独立 Reviewer 从原问题重建检查项，核对 Requirement fidelity、query completeness、grounding、比较方向、语言和可读性。重写只能使用同一 Read Set/Query Result；缺知识只能返回 Gap，不能补检索源码。
7. Requirement、Query Plan、Query Result、Need Assessment、Draft、Review、Authorization 和 Delivery 都保存稳定引用与 digest，可供人工重建完整权威链。
8. Product Validation 必须包含措辞变化、不同 Entity 标识、同名歧义、负向/无路径和不受支持问题；同一核心实现不得按工程、commit 或冻结题目硬编码答案。
9. `JAVA_SOURCE_SEMANTICS@1` 的 accepted Strategy 每个成功 Delivery 固定三个隔离模型角色且不重试：
   1. Plan Call 只读取原问题、语言、exact Read Authority、Profile/capability schema 与通用 operation vocabulary，提出不可变
      Requirement、功能 search terms 和 Query Plan；search terms 必须逐项保留问题中明确要求的动作、对象、顺序/审计、分支结果及
      return/throw 等物质概念，不能因其他词更像标识符而漏项。Profile vocabulary 必须把这些静态语义的常见语言/词形归一到
      稳定 canonical term（例如 return、throw、order、audit、validate），但不得加入工程、题目或符号专用词典；它不读取
      Entity/Fact/implementation Query Result；
   2. Draft Call 只读取原问题、平台已验证 Requirement/Plan 和密封 Query Result，生成逐 Claim 绑定 typed Support/Gap 的 Draft；
      它不读取 Source、planner 私有输出、Citation observation 或 Reviewer；
   3. Review Call 在全新上下文中读取原问题、已验证 Requirement/Plan、同一密封 Query Result 和 Draft，从原问题独立重建检查项，
      核对 fidelity、candidate/query completeness、grounding、方向、method completeness、语言与可读性。
   Review 的 finding code 必须来自版本化 proposal vocabulary；遗漏、静态事实不支持的运行时断言、Source/Evidence payload 展开等
   类别使用各自稳定 code，Schema 和 Application 同时拒绝未注册、重复或不按 vocabulary 顺序的 code，不能依靠自由文本近义词。
   平台在每次 Call 前后重验 role package、input/output schema、Snapshot/Bundle/Result digest、operation/Support allowlist 和 grant。
   固定 Ark transport 每次请求关闭连接；supervisor 因此必须在 Answer 启动前建立三个不同的 exact Provider connection，Gateway
   按角色顺序各消费一个且不能新建、复用或交换 descriptor。成功 Answer 必须恰好有三张唯一 Gateway receipt；任一 Call/validation 未完成即失败关闭且不调用后续角色，不 retry、不降级为
   deterministic answer、旧单调用 Strategy 或 Direct Investigation。Capability/Product Verification 中所有 intended supported
   Case 都必须完成三次；少于或多于三次均为 Case FAIL。

## Failure and implementation boundary

模式漂移、Read Set 不兼容、未知操作、EntityRef 歧义、查询不完整、Support 越界、Need 遗漏、审核未知或调用熔断均失败关闭。DTO、planner 算法和通用 operation catalog 由代码与测试定义，但不能改变以上固定输入、完整性和无 Source 边界。
