---
id: ITER-006-PROPOSAL
kind: iteration-proposal
status: accepted
authority: project-proposal
owners: [product, engineering]
depends_on: [ITER-005-RESULT-ACCEPTANCE, ROADMAP-CANDIDATE-SEMANTIC-VIEW, SYS-PRODUCT-VISION, SYS-PRODUCT-SUCCESS, SYS-QUALITY-ACCEPTANCE]
code: []
tests: []
iteration: ITER-006
coding_input: false
---

# ITER-006 Proposal：Java 静态调用行为世界模型

## Trigger and evidence

ITER-005 已证明用户指定 Maven Workspace 的模块结构可独立更新、Source-off 复用并从正式本机 Web 入口问答，但明确不表达
Java 类型、方法或调用。当前产品因此只能回答模块级 `DEPENDS_ON`，面对“某方法直接调用什么”“是否存在静态调用路径”时
只能返回 Gap。Roadmap 的 Semantic View Candidate 已要求后续每种 View 用真实任务、完整性 Oracle 和独立 Iteration 验证。

最小有价值缺口不是泛化为“理解所有 Java”，而是建立一条可证伪的源码级静态调用闭环：exact revision 的声明和直接调用先
成为正式知识，问题阶段只读 Snapshot；无法唯一解析或超出静态语义的情况安全关闭或返回明确边界。

## Outcome and users

本机开发者或评测者可以在没有 Question/Task/Session 时，对一个受支持的本机 Git Java 工程显式构建或更新，并随后：

1. 查看 exact Snapshot 中的 Java 类型、方法签名、声明关系和静态直接调用关系；
2. 关闭源码和权威数据库访问后，从同一个产品 Web 入口询问方法清单、直接调用、调用路径和相邻 Snapshot 差异；
3. 对运行时分派、反射、框架 wiring、业务意图或不受支持语法得到 Knowledge Gap / Limitation，而不是猜测；
4. 通过独立 Citation Projection 查看每条声明或调用的 exact source locator，正文不回流 Answer worker。

## Scope / non-goals

本轮接受候选 Profile `JAVA_STATIC_CALL_GRAPH@1`，只覆盖配置的 repository-relative Java source root 下 UTF-8 `.java` 文件。
冻结子集只形成：

- `JAVA_TYPE` 和 `JAVA_METHOD` Entity；
- `DECLARES_METHOD / JAVA_SOURCE_DECLARATION@1`；
- 对目标方法可由本 Profile 在 exact source closure 中唯一解析的
  `CALLS / JAVA_SOURCE_STATIC_CALL@1`。

Profile 的完整性规则、支持语法和拒绝条件由新的 Knowledge Contract 固定，并用独立 Oracle 验证。它不会把静态调用描述为
JVM 运行时调用、动态分派结果、Spring wiring、反射目标、数据流、异常流、Behavior 总体、Business 或 History。

明确不做：

- 对已有 Maven Structure Scope 采用不同 Schema；每个 Java Behavior Workspace 使用新的 SYSTEM Scope 和 `INITIAL` Schema；
- Java 全语言前端、依赖下载、classpath 推断、字节码分析或执行应用；
- 变量接收者类型推断、虚调用目标集、反射、lambda/method reference、生成源码或 annotation processor 输出；
- 其他语言、多仓融合、自动刷新、Scheduler、认证、公网部署或 Production Activation；
- 提问触发 Update、Source 回退或在 Answer worker 中重解析源码。

## Adopted system IDs

- `SYS-CONTRACT-KNOWLEDGE-SCHEMA-CORE`
- `SYS-CONTRACT-KNOWLEDGE-SNAPSHOT-PUBLICATION`
- `SYS-CONTRACT-KNOWLEDGE-JAVA-STATIC-CALL-MODEL`
- `SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE`
- `SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE`
- `SYS-CONTRACT-APPLICATION-BEHAVIOR-VIEW`
- `SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING`
- `SYS-CONTRACT-SOURCE-ARTIFACT`
- `SYS-QUALITY-SECURITY`
- `SYS-QUALITY-ACCEPTANCE`
- `SYS-OPS-LOCAL-BROWSER`

## Development slices and dependencies

### SLICE-001：Java 静态调用 Snapshot → Behavior View → 产品 Web 问答

单一纵向 Slice 先冻结受支持 fixture 的两个 exact commits 与独立声明/调用 Oracle，再实现：受控 Source collection、候选构建、
独立 replay verifier、Admission/Publication、Workspace/Bundle/Catalog、Source-off Behavior View、World Model planning/drafting、
Citation 和本机 Web 展示。任何上游完整性失败都保持旧 CURRENT；不得先在问题解释器加入答案分支掩盖建模缺口。

## Risks and unknowns

1. **Java 语法边界：** 无第三方 parser 的小型前端很容易把注释、字符串、嵌套类型、重载或接收者当成调用。Profile 必须先
   缩小并拒绝未知，不用正则命中数量冒充解析正确性。
2. **静态与运行时混淆：** `CALLS` 只表示 Profile 唯一解析的源码调用；UI、答案和 Citation 必须持续显示 modality。
3. **Schema 影响：** 扩展通用 typed graph enum 不能改变 `MAVEN_REACTOR_STRUCTURE@1` 的冻结 Coverage 集合或旧 digest；新
   Schema 只能在无 CURRENT 的新 Scope `INITIAL` 采用。
4. **Coverage 负向结论：** 只有全部 source files、声明和 Profile 内 invocation sites 都完成分类后，边缺席或零路径才可形成
   支持性否定；任何不支持或歧义调用使本次 Candidate 拒绝，不能发布伪 COMPLETE。
5. **产品资格漂移：** Answer/Prompt/Strategy/role package 改变会使继承资格失效。编码和确定性测试不授权外部调用；真实
   Product Validation 需要 implementation 后重新 freeze 并取得用户的 exact disclosure grant。
6. **兼容性：** 旧 Maven Workspace、Catalog 和 Web 问答必须保持逐行为兼容；混合 Profile Read Set 不在本轮支持。

## Verification and acceptance

阻断 Gate 包括：

- 独立 lexer/parser Oracle 对声明、重载签名、直接调用、证据 byte range 与两个 revision diff 完全一致；
- 评论/字符串伪调用、歧义重载、变量接收者、动态调用、截断读取和 tamper 均失败关闭；
- 初始发布、相同 revision 幂等、有效 R1→R2 replacement、无效 R3 保持 R2 CURRENT；
- Source-off 新进程只挂载 Catalog/Bundle，完成方法 inventory、direct calls、path、diff、Gap 与 Citation；
- 正式本机 Web 入口人工提交至少一条支持问题和一条边界/Gap 问题；问题前后 Update/CURRENT/Source Operation 不变；
- Maven Structure 聚焦回归和完整测试套件无退步；文档检查通过；所有 Finding 已处置；
- 若进入真实模型 Gate，逐题重大错误为 0、完整性不低于同资源的受控 Direct 与成熟 Source Agent 较强者，且所有失败保留。

代码完成不等于 Iteration 完成。真实 Provider 调用与最终 Acceptance 均需后续独立用户决定；Production Activation 始终不在
本 Proposal 范围。

## Authorization decision

用户于 `2026-08-12T09:18:11+08:00` 明确要求“开发 ITER-006”，接受上述最小 Outcome 与安全边界并授权
`ITER-006-SLICE-001` 编码。该消息不包含任何源码/问题向外部 Provider 的披露授权，也不授权 Production Activation。

实现与 exact run-003 suite 冻结后，用户另行回复“同意授权”，但 external dispatch review 认定该措辞未明确点名两个目的地
与 Java 源码 payload，拒绝执行且没有外部调用。run-003 仍等待明确披露授权；Production Activation、提交或推送未授权。

用户随后以绑定 suite `sha256:32de10fb…` 的完整消息明确授权 Ark、OpenAI Codex、exact sealed Java closure 与 World Model
no-payload boundary。run-003 已执行，但 World Model 两个 generic planning case 因新增 Java operation vocabulary 没有新的
closed qualification 而在 Provider 前失败；详见 `ITER-006-RESULT-LIVE-RUN-003`。该授权已经消耗于 frozen run-003，不能用于
修改后候选或新 suite；Production Activation、提交与推送仍未授权。

根因修复 freeze 后，用户又以绑定 capability freeze `sha256:7a3948a3…` 与 suite `sha256:93be2f87…` 的精确消息，仅授权八个
synthetic case 向 Ark 各执行一次。该授权已消费并取得 8/8 `PASS_VALID`；没有产品问题、Java 源码、Evidence payload 或 Codex
披露。后续 run-007 product candidate 已在零 Provider 下冻结，但尚未获得绑定新 suite `sha256:66192cdf…` 的三路披露授权。
这些后续事实不扩大原 Proposal，也仍不授权 Production Activation、提交或推送。

用户随后又精确授权 run-007 suite 与三路 payload boundary。Direct/Codex 各 6/6；World Model 六次 Ark call 均完成，但授权
wrapper 的 Java baseline digest 键冲突使外层 postcondition 6/6 fail-closed。该授权已消费，不能用于本地修复后的重跑；run-007
Result 为 FAIL。Production Activation、提交与推送仍未授权、未执行。

最小 wrapper 修复随后形成全新零 Provider run-008 freeze：56/56 focused、18/18 candidate Answer package、836/836 full
regression 与安全门 PASS，外部调用为 0。其 freeze report `sha256:a036921c…`、suite `sha256:0793db73…` 和 disclosure set
`sha256:1ffb8aa6…` 需要另一份精确授权；此前任何授权都不可复用。该候选不扩大 Proposal，也不授权 Production Activation、
提交、推送或最终 Acceptance。

用户随后提交该独立 run-008 授权；三路各 6/6、comparison `sha256:857085c4…` PASS，且没有 retry、failure filter 或 missing
output interpolation。该执行闭合 Product Validation，但不能自行接受 Iteration；最终 Acceptance、Production Activation、提交
与推送仍分别未授权、未执行。

用户随后于 `2026-08-13T11:45:33+08:00` 接受 exact run-008 已证明的 Java static-call `EVALUATION_ONLY` 窄范围，最终裁决见
`ITER-006-RESULT-ACCEPTANCE`。该后续 Acceptance 不改变本 Proposal 的非目标，也不接受当前评测页为正式最终 Web Chat；
Production Activation、提交和推送仍未执行。
