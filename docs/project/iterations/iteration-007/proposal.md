---
id: ITER-007-PROPOSAL
kind: iteration-proposal
status: proposed
authority: project-proposal
owners: [product, engineering]
depends_on: [ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-LIVE-RUN-008, SYS-PRODUCT-SUCCESS, SYS-ADR-014, SYS-CONTRACT-KNOWLEDGE-JAVA-STATIC-CALL-MODEL, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING]
code: []
tests: []
iteration: ITER-007
coding_input: false
---

# ITER-007 Proposal：Java 源码实现语义与通用源码问答首个累积切片

## Trigger and evidence

ITER-006 run-008 已证明 Java 类型、方法声明和有限静态调用可以在提问前形成 Snapshot，并从正式 Web Source-off 回答封闭问题，
但它仍等待用户最终 Acceptance。现有代码同时存在四个直接限制：

1. `JAVA_STATIC_CALL_GRAPH@1` 没有条件、状态、return、throw/catch 和调用点上下文；
2. `ProductQuestionInterpreter` 把问题压成固定的 `ProductNeedKind`，不具备通用语义路由；
3. 当前 Java parser 只支持窄语法，不能作为真实项目的稳定前端；
4. 即使新增 `method_implementation`，用户不说类名或方法名时，系统仍找不到相关实现。

因此下一轮不增加孤立 View，也不同时扩 README、配置和多语言。它先验证软件世界模型最关键的架构假设：源码实现语义能否在
问题前形成、被自由问题发现，并在同一正式 Web 中与既有静态调用知识组合成可验证答案。

## Outcome and users

用户先对 exact Local Git Java/Maven revision 执行一次显式更新。系统构建新的 `JAVA_SOURCE_SEMANTICS@1` Snapshot，保留已接受的
Java 声明和 exact `CALLS` 语义，并为语义完整的方法增加最小实现事实：

- 分支条件及其控制的调用、return、throw；
- 可静态确认的状态读取和写入；
- return、throw、catch/finally；
- 调用点的 source modality 和必要顺序关系。

问题入口增加两个通用操作：

- `implementation_candidates`：根据功能/业务描述，在预构建的正式实体和事实中发现相关方法；
- `method_implementation`：读取候选方法的实现语义与完整性。

所以“登录失败时怎样处理”这类不带类名、方法名或签名的问题，也必须先从世界模型定位实现，再组合 `CALLS` 与条件、状态、
返回或异常事实回答。问题阶段 Source Operation、Knowledge Update 和 Direct fallback 增量仍必须为零。

这仍是 **Java 源码通用问答的首个累积切片**，不是任意语言、任意知识源的最终 MVP。

## Product-goal alignment and cumulative delta

- 目标引用：`SYS-PRODUCT-SUCCESS`。
- 复用能力：ITER-005 的 Workspace、独立更新、Bundle/Catalog、正式 Web、Citation；ITER-006 只有最终被用户接受后，才能作为
  本轮 declaration/static-call 的正式累积依赖。
- 新旧同题：三个 Slice 各有一条跨域 Case，并都必须在一条问题的同一 Need/Support chain 中同时使用接受后的 `CALLS` 与本轮
  实现事实；最终 held-out Case 为 `V-XD-003`。
- 无符号自由题：最终 12 条隐藏可回答题中至少 6 条不得出现类名、方法名或签名，每个工程至少 2 条。
- 最早体验：第一段 walking skeleton 完成即从正式产品 Web 人工提问，并在进入下一 Slice 前执行一个真正隐藏的小型 Java canary，
  不等完整 Java Coverage 和最终隐藏评测才第一次暴露泛化问题。
- 止损：最早 Web 不能成立、需要题型/关键词/工程补丁、功能描述找不到代码、成熟源码 Agent 能答而预构建模型持续 Gap，均停止
  扩张并重审表示、查询或 frontend，不能用“新 View 已完成”冒充产品进展。

## Adopted system IDs

继续采用 `SYS-PRODUCT-SUCCESS`、`SYS-ADR-014`、`SYS-CONTRACT-KNOWLEDGE-JAVA-STATIC-CALL-MODEL`、
`SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE`、`SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE`、
`SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING`、`SYS-QUALITY-SECURITY`、`SYS-QUALITY-ACCEPTANCE` 和
`SYS-OPS-LOCAL-BROWSER`。Readiness 前必须接受新的 Java Source Semantics、功能到实现发现、Coverage/no-payload 与三调用
问答 Contract；规划文字不能代替 current System 文档。

## Development slices and dependencies

### SLICE-001：最小正式 Web walking skeleton

只使用一份可见开发工程和一个足以回答真实问题的窄语义闭包。固定成熟 Java parser；先实现 `call + if + return + throw`、
`implementation_candidates`、`method_implementation`、正式 Snapshot/Bundle 和真实模型问答。立即在现有正式 Web 提问一条
**不含类名/方法名**的跨域问题和一条边界问题。禁止 deterministic stub、预制答案和 validation-only launcher。

本 Slice 另绑定 `V-CANARY-001`：独立评测方在本 Slice 产品代码冻结前持有并隐藏一个符合最小语法闭包的小型真实 Java 工程，
工程身份、源码和问题均不向实现方披露，其中至少有一条可回答、无符号名且组合旧 `CALLS` 与新实现语义的问题。冻结后才通过
同一正式产品链执行；曝光后任何产品改动都会烧毁该 canary，原失败必须保留，并由独立方提供全新的工程和问题后才能重试。
canary 未 PASS 时不得进入 SLICE-002。

这一步只证明端到端产品假设，不要求先覆盖所有 Java 语法。

### SLICE-002：可见语料上的语义与 frontend 加固

只在明确标记为 development/qualification 的可见语料上扩展 annotation、interface、inheritance、generic、constructor、overload、
variable receiver、lambda、try/catch，以及状态读写和异常语义；完成 R1→R2、重启持久化、Citation 和正式 Web 多题复验。
本段不得接触最终 held-out 工程或问题。独立评测方另持有一个覆盖 common-Java 边界的小型真实 canary，并在本 Slice 产品代码冻结
前隐藏其身份、源码和问题。它只用于 `V-CANARY-002`，不计入最终 12+4 suite；曝光后任何产品改动都烧毁该 canary 并保留原失败，
且至少有一条 common-Java 可回答无符号问题必须给出有证据答案，不能用 Gap 通过。必须换全新工程和问题重试；canary 未 PASS 时
不得进入 SLICE-003。

### SLICE-003：冻结后的独立产品验证

产品实现冻结后，独立评测方才向执行环境提供两份未参与实现、且此前对实现方隐藏身份与源码的真实工程，以及 12 条 answerable
和 4 条 boundary 问题。任何产品实现变化都会烧毁已曝光的工程和问题集：保留原失败，并同时更换工程与问题集后重新冻结，
不能只换题。最后在正式 Web 现场再问 3 条临时问题。

## Scope / non-goals

本轮只面向受控 Java/Maven 工程的源码实现问题，不承诺任意语言、所有 Java 语义或运行时真相。以下边界同时限定三个 Slice。

### Coverage

本轮不扩张全局 `CoverageCompleteness` 为 PARTIAL。Snapshot 必须完整记录每个授权文件/类型/方法的
`SEMANTICS_COMPLETE / UNSUPPORTED_EXCLUDED / FAILED` disposition；Catalog 的 COMPLETE 表示 disposition manifest 完整，而不是每个
方法都已完整建模。只有 `SEMANTICS_COMPLETE` 方法可支持“没有分支/没有异常”等闭世界结论；其他方法只能给已接纳的正向事实和
明确 Limitation/Gap。

### no-payload

Bundle 只能发布查询所需的 typed semantic atoms、标识和 Support refs，禁止原始源码、注释、token stream、任意表达式文本或可逆的
完整 AST。Readiness 前必须同时冻结“信息保持 Oracle”和“信息越界 Oracle”：前者证明目标答案所需事实仍在，后者证明 Bundle
没有把源码换一种格式搬进回答进程。

已有 `CALLS / JAVA_SOURCE_STATIC_CALL@1` 的含义不得扩张。variable receiver、inheritance 或其他新增解析得到的调用关系必须使用新
predicate/modality；旧 `CALLS` 只按 ITER-006 exact 规则重建并回归一致。

### 模型调用

候选正式协议为每题三次隔离模型调用：第一次只提出 Requirement、功能检索词和通用 Query Plan；平台校验后执行正式查询；
第二次只基于密封 Query Result 生成 Draft；第三次由独立 Reviewer 从原问题重建检查项并核对 Requirement fidelity、query
completeness、grounding、语言和可读性。平台继续确定性校验 schema、typed refs、Support 和 Authorization。Readiness 前必须把
exact 三调用、失败策略、Gateway workload 和 Prompt/operation vocabulary 写入 Contract；SLICE-001 再完成 capability qualification。
如果独立评测证明三次仍不能满足质量契约，必须停止并重审协议，不能为了调用配额弱化 Review。

### 明确不做

- README、ADR、配置、部署拓扑、运行日志和 History；
- 动态 dispatch、反射/DI 实际目标、线程时序、数据库真实状态或设计动机；
- Source/RAG payload、问题时更新或 Direct Investigation；
- 新增 implementation/business/exception 题型 enum、关键词答案或工程特判；
- 自动 Scheduler、Production Activation、提交或推送。

## Risks and unknowns

- 形式语义可能丢失成熟源码 Agent 需要的上下文，也可能因过度保真越过 no-payload 边界；双 Oracle 是首要架构 Gate。
- 功能描述到实现候选的召回与歧义处理尚未被真实工程证明；只会按符号名查询等同于没有关闭产品缺口。
- Coverage 的“disposition manifest COMPLETE + method completeness”会改变 Knowledge Use 对 COMPLETE 的解释，必须全链修订并验证。
- 成熟 parser 的版本、license、离线可用性和 canonicalization 尚未冻结。
- 当前问答只取得单模型调用资格，三调用协议需要新的 capability qualification 和隔离 workload。

## Verification and acceptance

- 12 条 answerable 与 4 条 boundary 分开计数；Gap 不能计入 supported count；
- `V-CANARY-001/002` 是在大规模开发前暴露泛化失败的独立阻断 Gate，不计入最终 12+4 的 supported target；
- answerable target 在 Readiness 前冻结，至少为 `min(12, max(baseline + 4, 8))`；
- 两个工程、功能定位、条件/状态、返回/异常、跨方法调用均有真实增量，重大错误为零；
- 4 条 boundary 必须由独立 Oracle 证明 exact 授权 Java 源不足；若成熟源码 Agent 能从同一源码回答，World Model 的 Gap 记 FAIL；
- 支持答案的逐题正确性和完整性不低于成熟源码 Agent，旧 accepted behavior 不退步；
- 3 条现场问题中至少 2 条不含类名、方法名或签名；
- 构建和提问调用数、Token、时延及同 Snapshot 多问题摊销全部披露；
- Production Activation 无条件 `NOT_EXECUTED`。

### 已知 ITER-006 基线限制

不得在修复代码后继续沿用旧 run-008 结果。推荐做法是：ITER-006 Acceptance 只接受 run-008 exact 已证明的窄范围，并把下列三项
登记为明确限制；修复归入 ITER-007 SLICE-001，并由新 Strategy/Prompt/operation qualification 与正式 Web 重新验证：方法清单按
canonical method signature 排序；“谁调用 X”使用 `INCOMING + CALLS`、“X 调用谁”使用 `OUTGOING + CALLS`；“异常路径”不得误入
`ALL_SIMPLE_PATHS` 或抛实体端点错误。若用户选择先在 ITER-006 修复，则 ITER-006 必须重新 freeze、资格和 Product Validation，
ITER-007 的 baseline 随新 Acceptance 更新。

## Authorization decision

当前为 **PROPOSED / NOT READY**。本 Proposal 不授权编码、外部模型调用、hidden 工程/问题披露、Production Activation、提交或
推送。ITER-006 最终 Acceptance、accepted implementation baseline、上述三项限制的明确 disposition、frontend/semantic/no-payload/query/
model-call Contract、独立 baseline/target 和用户 exact Product-goal review 未闭合前，不得更新 `project/current.md`。
