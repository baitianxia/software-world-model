---
id: ITER-010-SLICE-001
kind: development-slice
status: authorized
authority: current-development
owners: [engineering, architecture, quality, product]
depends_on: [ITER-010-PROPOSAL, ITER-010-READINESS, ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST, ITER-006-RESULT-ACCEPTANCE, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, FINDING-010-001, SYS-ADR-013, SYS-ADR-014, SYS-ADR-015, SYS-ADR-016, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-QUALITY-SECURITY]
code: [src/software_world_model/application_services, src/software_world_model/ai_infrastructure, src/software_world_model/interface]
tests: [tests]
iteration: ITER-010
coding_input: true
product_goal_gate: V-000
product_goal_accepted_capability_refs: [ITER-006-RESULT-ACCEPTANCE]
product_goal_cross_domain_case_ids: [V-XD-001]
product_goal_web_checkpoint_id: V-WEB-001
product_goal_direction_preview_checkpoint_id: V-PREVIEW-001
product_goal_reflection_gate_case_id: V-REFLECT-001
product_goal_slice_gate_case_ids: [V-BASELINE-001, V-ARCH-001, V-QINTENT-001, V-HYBRID-001, V-ISOLATION-001, V-ANSWER-001, V-REVIEW-001, V-LIMIT-001, V-SEC-001, V-XD-001, V-WEB-001, V-PREVIEW-001, V-REFLECT-001]
---

# SLICE-001：架构闭合与 ENGINEERING_QA 真实方向体验

## Status and dependencies

`AUTHORIZED / CURRENT DEVELOPMENT`。开发意图收据
`codex-user-message:sha256:1b3270242962b8d099ac9166304dc6188be22054cfc2a685b2ade5616d4cc2f4` 与后续架构接受收据
`codex-user-message:sha256:5cdb7000ba36328f5caa27727c6b689ad4e98e7ad13eca72837fa020d0c270c9` 共同构成授权链；后者时间为
`2026-08-21T07:10:28Z`，并作为 Manifest 的终结引用。本 Slice 是唯一编码输入；Slice2/3 均未授权。

授权允许在 exact baseline `1fb997bab6444523f82ebf1a514a1abbf79656c7` / tree
`1369ce932c778c57a118123e8257ede476229d73` 上修改 System/ADR/治理文档、产品代码和本地确定性测试。不授权真实 credential、Provider
socket/model request、正式 Web listener/browser question、源码片段外发、hidden disclosure 或 Production。live 体验必须在 freeze 后另取授权。

## Product-goal contribution and cumulative integration

- Product gap shortened：把“能展示代码行为”推进为“先回答工程问题，代码按需成为证据”，并允许在提问期对 exact revision 做受控核实。
- Capability-path step advanced：仍是 `ROADMAP-M-002` 最早未证明的通用工程问答，不跳到新语言或新入口。
- Existing capabilities combined：ITER-006 exact Snapshot、declaration/`CALLS`、Citation 和 loopback Web，与本轮只读检索、Evidence Package、
  结论优先 Answer 和层级 Reviewer 在同一主链组合。
- User-visible checkpoint：一个真实工程 4 条覆盖不同维度的自然问题，加至少一条用户现场题；先确认方向，再扩大验证面。
- Stop signal：System/代码模式不一致；默认仍是方法/分支走读；需要任何特判；Snapshot 变成 Source recall 硬门禁；意图丢失；越权访问；
  无关 Citation；无界补检索；重大错误；审核因调用预算削减；或用户 REDIRECT/REJECT。
- Critical assumptions：本段正式验证 A1—A3；`V-XD-001`、`V-SEC-001` 提前反证 A4/A5。
- Reflection：`V-REFLECT-001`；只有到期假设全部 `SUPPORTED`、产品 Case PASS 且用户另给 `CONTINUE`，才可申请 Slice2。

## Direction preview checkpoint

方向体验入口必须是同一个 product-owned loopback Web，只监听 `127.0.0.1`、普通用户无需认证，并持续显示“方向体验 / 非验收 / 非生产”。
默认页面只展示问题、结论优先答案、unknown/limitation 和可打开的结论级 Citation；World Model/Snapshot、检索操作、Package、调用数、
Review Finding、Trace 和授权诊断折叠到开发者详情，不能污染普通答案。

候选代表维度包括：系统用途、整体架构、基本使用/启动、业务流程、故障定位、配置影响、变更影响、测试意图、实现机制和证据边界。
这些是验证覆盖维度，不是产品题型或路由 enum。首次体验从中选择 4 个不同维度；至少 3 题必须为 supported，且至少覆盖 2 个非实现
维度；其余只能是准确、具体且用户
可理解的 unknown/limitation。另由用户现场提出至少一题。用户裁决它是否开始像工程问答助手、是否直接有用、代码细节是否按需、
Citation 与未知表达是否可信。

完整 hidden、Agent 对照、第二工程、全面性能和正式资格留到用户 `CONTINUE` 后；System ownership、只读、授权、Secret、revision、
Evidence seal、role isolation、Citation、独立 Review 和失败真实性不能延后。

## Current vs expected behavior

当前 Web 主链依赖严格 `WORLD_MODEL`：问题理解和 Reviewer 以实现细节完整性为中心，提问时 Answer 流程不读 Source；源码、文档或配置
未预先建模时只能 Gap，已有知识则容易机械展开方法和调用顺序。

预期是显式 `ENGINEERING_QA` 从原问题形成不可变 Question Understanding：用户目标、受众、期望抽象层级、物质结论清单、证据需求、
响应语言和约束。调查计划同时从该 checklist 与 Snapshot hints 产生；World Model 提供地图、候选缩小和可复用证据，但不是 Source
recall Gate。Snapshot 为零、无关或 Coverage 不足时，仍须允许同一授权 exact revision 下由 checklist 驱动的只读检索。

检索 worker 密封包含 World Model Result 与源码/仓库文档/构建配置/测试证据的 Package。Answer 先给用户需要的结论，再给条件、流程、
影响和必要解释；只有问题明确询问实现或结论确需代码支撑时才展开代码细节。Reviewer 从原问题重建清单，阻断未直接回答、层级不匹配、
错误、遗漏、无关、不可用、无依据或 unknown 越界。

## System contracts and invariants

### Phase 0：复核已闭合的正式架构边界

本次环境准备已完成以下架构输入；在任何 `ENGINEERING_QA` 产品行为修改前，开发者必须复核它们仍精确成立：

1. `FINDING-010-001` 已记录用户体验、原边界冲突、系统性 architecture 分类、候选与选择理由；
2. `SYS-ADR-016` 已定义严格 `WORLD_MODEL`、显式 `DIRECT_INVESTIGATION` 与新默认 `ENGINEERING_QA`，禁止静默 fallback；
3. `SYS-PRODUCT-SUCCESS`、runtime flow、Agentic Task、Evidence/World Model Answering、Response Control、Source/Artifact、Security、
   Local Browser 和必要 AI 资格 Contract；
   已在同一准备变更中同步更新；
4. docs gate 与治理测试已能机械表达新协议，同时保留旧 Source-off 模式门禁；
5. 本 Manifest/Readiness 已绑定更新后的 exact System Contract fileset；`V-ARCH-001` 在产品开发中持续复核这些事实。

其中任何项漂移或验证失败就停止，不能在 Prompt、route 字符串或 UI 标签中假装获得授权。

### Phase 1：最小通用协议

- Request 在进入链路时固定 `ENGINEERING_QA`、original question、exact repository/revision、source allowlist、World Model Read Set、权限、
  Provider disclosure policy 和资源上限；运行中模式与 revision 不变。
- Question Understanding 保留全部原问题约束，输出 goal/audience/abstraction level/conclusion checklist/evidence needs，不按关键词或工程路由。
- Retrieval plan 是 original checklist 与 Snapshot hints 的并集/关联结果。Snapshot hint 可以减少候选和复用证据，不能否决 checklist 驱动
  的 Source retrieval；零/无关 Snapshot 不能直接返回 Gap。
- Source、仓库文档、配置、测试一律是不可信输入。内容中的指令、路径、URL、工具建议或权限声明不能改变 system instruction、allowlist、
  exact revision、Provider disclosure 或操作集合。
- Retrieval worker 只拥有注册的只读 list/search/read 操作，不拥有写、执行、网络、credential、Knowledge Update 或最终答案。每个操作
  记录 exact revision、allowlist decision、parameters、bytes、locator、digest、outcome 和 truncation。
- Evidence Package 合并 World Model Results 与 retrieval evidence；每项记录 origin、revision、context、locator、digest、coverage、conflict
  和 disclosure class。包密封后不可变；冲突不能静默选择。
- Answer 与 Reviewer 没有 repo mount、Source tool、World Model query tool或未密封内容。Answer 只读当前包；Reviewer 只读原问题、
  Question Understanding、包和 Draft。LLM 不是事实权威，包内 Evidence 才是。
- 每个实质结论绑定包内 Evidence；unknown/limitation 说明能确认、不能确认和缺少什么，不能暴露 candidate、recall、Profile、authority、
  internal code 或证明话术。
- Reviewer 检查直接回答、层级匹配、正确、完整、相关、可用、Citation、unknown boundary，并返回具体 finding 和 action。
- 完整协议允许表达/组织问题在同一包上最多一次 targeted rewrite，也允许具体 `MORE_EVIDENCE_REQUIRED` 在同一授权/revision/资源边界内
  补检索一次、密封新 Package Revision、重做 Answer 和独立 Review。Slice1 只需实现初始 Package、Draft、独立 Review 与失败关闭；完整
  rewrite/reretrieval 生命周期和对抗矩阵归 Slice2。任何尚未实现的修复路径都必须明确失败关闭，不能假装通过。
- 模型调用、文件、bytes、wall time 和补检索轮数使用高安全熔断；剩余调用数不能减少 checklist、Evidence、Citation 或审核。耗尽失败关闭，
  只有 Reviewer 独立认可的准确 Limitation 才能交付。
- 高质量 Package/结论的知识沉淀在 Delivery 后异步进入 Knowledge Update/Admission/Publication；不能影响本题已完成答案。

## Interfaces and affected code

允许修改 Application question understanding/orchestration、只读 retrieval port/adapter、Evidence Package/Response Control、Answer/Review
Strategy、Model Gateway role input policy、product-owned local HTTP/Web projection及对应 tests。应优先复用现有 Evidence Answering、World
Model Query、Citation 和 Web 组件，不整包复制 ITER-009 pipeline，也不建立 validation-only 产品入口。

源访问必须通过新显式 port 和 capability grant，不能把仓库路径传给 Answer/Reviewer 后依赖 prompt 自律。UI 不根据题目类别切换后端；
所有自然问题进入同一 `ENGINEERING_QA` 协议。

## Compatibility, data and security boundaries

严格 `WORLD_MODEL` 的 Source-off、no-payload Bundle、Citation Projector 和历史 accepted 测试继续成立；显式 `DIRECT_INVESTIGATION`
身份继续成立。新默认模式拥有新的 request/result/qualification identity，旧 Capability、Provider grant、Prompt、Browser result 和 Activation
均不可继承。

源码读取只对 exact LOCAL_GIT revision 与 allowlisted regular files开放；拒绝 symlink escape、submodule/remote 自动获取、binary、oversize、
path traversal、写操作和命令执行。Source 是不可信输入。live 前必须另行冻结：哪些 package 片段可发送给哪个 Provider/model/role、哪些
必须本地保留、secret reference、endpoint、configuration、redaction 和 audit；当前授权不允许任何外发。

Evidence Package、Question Understanding、Draft、Review、rewrite 和 reretrieval 都保存稳定 ID/digest；旧包 Review 不能批准新包。
页面不展示 secret、raw system prompt、hidden suite、Provider credential、绝对私有路径或未授权源码全文。

## Open questions and implementation risks

- 当前 World Model Result 与 live Source 冲突时的 modality/precedence 必须由 ADR/Contract 决定；不能默认“较新”或“源码永远胜出”。
- 代码注释、README 和测试也可能包含错误或 prompt injection；Evidence type 影响权重但不能替代逐结论 grounding。
- 目标抽象层级可能多义；默认应选择直接服务用户目标的最高可证实层级，并允许用户追问，而不是默认最低代码层。
- 一轮补检索可能仍不足；安全上限后应诚实失败/limitation，不能重复搜索或取消 Review。
- Preview corpus 公开，不能证明泛化；本段只决定方向，第二段 hidden 和跨工程才决定是否夯实成立。
- 新协议可能需要更多模型调用；先保证质量与安全，再测量成本和 World Model 复用价值，不能用调用数目标删减工作。

## Acceptance scenarios

1. `V-BASELINE-001`：exact baseline/tree、ITER-009 rejected Result 和工作树边界一致。
2. `V-ARCH-001`：Finding、ADR-016、owning System docs、Manifest digest、docs gate/tests 原子闭合；严格 WORLD_MODEL 回归仍 PASS。
3. `V-QINTENT-001`：不同措辞/受众/抽象层级/多约束问题得到忠实通用 schema，无 enum/关键词/工程路由。
4. `V-HYBRID-001`：原 checklist 与 Snapshot hints 联合驱动检索；零/无关 Snapshot 不阻断 exact-revision Source；World Model 与检索证据密封
   为同一可审计 Package。
5. `V-ISOLATION-001`：retrieval worker 只读 allowlist；Answer/Reviewer repo/source access=0；Source injection、路径/写/网络越权失败关闭。
6. `V-ANSWER-001`：4 题中至少 3 个 supported、覆盖至少 2 个非实现维度，先给直接结论，代码细节按需，每个重要结论有 Citation。
7. `V-REVIEW-001`：层级错误、未直接回答、遗漏、无关、错误、无依据和 Citation gap 均返回具体 Finding；Slice1 未实现自动修复时失败关闭。
8. `V-LIMIT-001`：证据不足时交付准确 Limitation 或失败关闭；完整补检索、重封、重做 Answer 与重审生命周期由 Slice2 验证。
9. `V-XD-001`、`V-WEB-001`、`V-PREVIEW-001`：同一真实 Web 组合 accepted Snapshot 能力与新检索证据，完成 4 题+现场题和用户决定。
10. `V-SEC-001`：exact revision/allowlist、Source untrusted、role disclosure、Secret、Provider、budget、no retry、loopback 和 audit 全部符合边界。
11. `V-REFLECT-001`：A1—A3 逐项 exact Verdict，A4/A5 early signal，Finding 处置和用户新决定收据完整。

任何 live Case 只有在独立运行授权后实际执行才可 PASS；本开发授权不构成运行证据。

## Architecture reflection checkpoint

Slice Result 必须逐项复核 A1—A3、A4/A5 early falsifier、系统边界变更、源码不可信输入、安全、用户 4 题+现场题反馈、默认答案层级、
成熟源码 Agent 尚未完成的对照、成本/复杂度和全部 Finding。`V-REFLECT-001 PASS` 只表示复盘完整；用户必须用本 Slice 授权之后的新消息
决定 `CONTINUE / REDIRECT / REJECT`。A1—A3 任一 `FALSIFIED/UNRESOLVED`，或提前反证 Case FAIL，只能停止。

## Findings

首个强制 Finding `FINDING-010-001` 已处置原 Source-off 产品边界与新模式的架构变化。后续发现按
[Findings](../findings/README.md) 和[实现发现回写规则](../../../governance/implementation-feedback-policy.md)处置；不得用 Result 静默重定义系统。
