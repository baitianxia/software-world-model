---
id: ITER-010-SLICE-001
kind: development-slice
status: authorized
authority: current-development
owners: [engineering, architecture, quality, product]
depends_on: [ITER-010-PROPOSAL, ITER-010-READINESS, ITER-010-VERIFICATION, ITER-010-PDR-010, ITER-006-RESULT-ACCEPTANCE, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, SYS-ADR-017, SYS-ADR-018, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-KNOWLEDGE-STRUCTURE-MODEL, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-QUALITY-ACCEPTANCE, SYS-QUALITY-SECURITY]
code: [src/software_world_model/knowledge_engine, src/software_world_model/application_services, src/software_world_model/ai_infrastructure, src/software_world_model/interface]
tests: [tests, validation/iteration_010_mvp]
iteration: ITER-010
coding_input: true
current_execution_decision_ref: ITER-010-PDR-014
current_execution_finding_refs: [FINDING-010-256, FINDING-010-257, FINDING-010-258, FINDING-010-259, FINDING-010-260, FINDING-010-261, FINDING-010-262, FINDING-010-263, FINDING-010-264, FINDING-010-265]
product_goal_gate: V-000
product_goal_accepted_capability_refs: [ITER-006-RESULT-ACCEPTANCE]
product_goal_cross_domain_case_ids: [V-CHAT-XD-001]
product_goal_web_checkpoint_id: V-CHAT-EXPERIENCE-001
direction_preview_web_checkpoint_id: V-CHAT-EXPERIENCE-001
product_goal_direction_preview_checkpoint_id: V-PREVIEW-002
product_goal_reflection_gate_case_id: V-PREVIEW-002
product_goal_slice_gate_case_ids: [V-BROWSER-CHAT-MVP-BUILD-001, V-AGENT-FIRST-CONVERGENCE-001, V-PUBLIC-OSS-AUTHORITY-ADMISSION-001, V-MODEL-TRANSPARENT-ROUTING-001, V-CHAT-EXPERIENCE-001, V-CHAT-001, V-CHAT-XD-001, V-DIRECTION-QUALITY-001, V-PREVIEW-002]
---

# SLICE-001：世界模型与主工程 Agent 能力恢复

## Status and dependencies

`AUTHORIZED / PDR-014 CAPABILITY-SEPARATED RECOVERY / coding_input=true`。

本 Slice 继续使用 PDR-012 的 standing authority 和 Manifest action，但执行内容完全由 PDR-014 定义。PDR-013、run-127 以前的 Answer/Review/
preflight 协议和未提交 `@40` candidate 只保留历史证据，不得继续开发或重新运行。

## Product-goal contribution and cumulative integration

普通用户在无认证 loopback Web 中与一个真正的主工程 Agent 持续对话。Agent 先使用提问前构建的软件世界模型获得系统认知，再按真实 Gap
受控读取源码、文档、配置或测试，根据观察修改计划，并交付自然答案、可打开 Citation 和 fresh 独立审核。同一 Conversation 支持追问、
纠正、深入和总结；新 Conversation 隔离。

首个浏览器 Alpha 用于尽快确认方向，不冒充 MVP。MVP 仍要求五个异质问题无重大错误、逐题不低于 current Codex、总体严格更好，并证明
世界模型带来非 locator 的实质增益。

## Current vs expected behavior

- 可复用：Provider-neutral Gateway、standing authority、只读 Source Broker/Worker、Conversation/Turn、Evidence/Citation、Web 和已有
  formal/structure/Java static-semantics 资产；
- 不可继续：把回答拆成不断扩张的封闭 Claim/Boundary/content-unit 证明协议，用 Markdown/标题/substring 判断语义，或针对一个已知问题
  增加 Prompt/Schema/Validator 后只重放该题；
- 现有 prompt-heavy 模型边界是迁移来源和失败基线，不是新候选必须兼容的产品本体；
- 产品失败必须能在 knowledge construction、cognition retrieval、Agent harness/tool use、answer synthesis、review 或 Web 中定位最早责任层。

## Development order and effort limits

上限只触发自动简化或换路，开发继续；不得用它降低答案质量或申请新授权。

### Phase A — source-only Agent 诊断基线（累计 ≤2h）

实现最小 Provider-neutral Agent loop：保留 Conversation 目标和紧凑 Work State，模型自主选择只读 search/read，Application 返回 Observation，
模型据此重规划并回答。接通现有浏览器，以两个异质问题和一个追问真实运行；一旦可操作立即交付。该候选用于判断 harness/工具是否基本合格，
不是世界模型产品或 MVP。

验收关注 trajectory 中是否真实出现目标保持、合理工具选择、观察驱动重规划、停止判断、自然答案和 Citation。若明显弱于成熟源码 Agent，
直接替换 Agent loop、memory 或工具接口；不得用回答协议遮盖。

### Phase B — 世界模型最小认知纵切（累计 ≤6h）

从 exact revision 在提问前构建并发布一份可跨问题复用的认知，至少覆盖：

- module/package/file/type/method 实体与包含层级；
- import/inherit/invoke 等跨文件关系；
- 可遍历的入口—协作者行为路径，以及源码直接证明的条件、异常、状态读写或外部调用；
- 每项认知的来源、Coverage、Conflict/Unknown 和 exact revision。

复用现有知识内核和 Java 资产，以最小通用增量补齐缺口，不另建平行知识库。提供三类 Agent-facing 职责：搜索认知、按类型/方向/深度遍历
关系、取得实体或行为详情。结果紧凑、可分页、带稳定身份和证据，不把整份 Snapshot 平铺给模型。

用至少五个未参与实现的任务独立检验构建正确性、material evidence 可检索性、Coverage/Unknown 真实性和跨问题复用。此阶段不生成最终
答案，也不以 Prompt 调整修复知识错误。

### Phase C — 世界模型增强浏览器 Alpha（累计 ≤8h）

把 Phase B 工具加入 Phase A 的同一个 Agent。Agent 默认先搜索/遍历认知，再按 Gap 使用 Source。用三个异质问题和一个语义追问贯通
World Model → Agent → Source → Answer/Citation → fresh Reviewer → Web；页面折叠展示 trajectory、认知命中和 Source 补证。首次贯通立即
交付用户，不等待全量回归、hidden、跨工程或 Codex 比较。

同一 candidate 同时保存 source-only 和 World Model + source 两臂。后者至少必须增加一个正确的非 locator 结论，或让一个 source-only
失败/遗漏的问题完整正确，且不产生物质退步；否则不得宣称世界模型有产品价值，直接回到 Phase B 的构建/查询归因。

### Phase D — 质量与方向 Gate

同一 candidate 运行五个异质问题和一段多轮 Chat，至少三个问题未参与实现。actual current Codex 在相同 exact revision、问题和输出目标下
独立回答；双方完成前互不可见。独立评测方直接读 exact Source，逐题判断正确性、完整性、相关性、Citation 和 Unknown。

只有系统重大错误为 0、Reviewer 无重大漏判、逐题不低于 Codex、总体严格更好且世界模型有非 locator 增益时，才称为 MVP 并进入用户方向
决定。失败保持当前开发动作，按最早责任层通用修复；不创建逐失败 PDR/Result，不暂停，不重复授权。

## System contracts and invariants

`SYS-ADR-018` 继续拥有世界模型与主工程 Agent 的职责分离；Engineering Conversation、Agentic Task、Evidence/World Model Answering、
Knowledge Structure、Source Artifact、Security 和 Acceptance 继续拥有跨模块契约。Conversation/Turn 属 Application；模型不直接取得文件、
Shell、网络、凭据或写权限；Source 固定 exact revision 且只读；重要结论绑定真实 Citation；fresh Reviewer 独立于回答生成。PDR-014 只改变
实现与验证顺序，不降低这些边界，也不把具体模型或 Provider 写进产品语义。

## Agent and tool contract for this Slice

Agent runtime 必须是模型/Provider 透明的小循环，不是固定角色流水线。最小职责是：

`conversation goal → current plan → tool proposal → trusted observation → revised plan or finish → answer → independent review`

世界模型工具返回实体、关系、行为和边界；Source 工具返回 exact-revision 只读证据。工具命名和参数应像给新工程师使用的接口一样明确，支持
搜索、过滤、遍历深度、分页和可行动错误；不得要求模型制造 opaque identity 或重复 Application 已知字段。

Reviewer 在 fresh 上下文中读取原问题、相关 Conversation context、完整答案、Citation 和必要 Source evidence，一次返回 verdict 与全部
重大缺陷。Application 只校验身份、Citation 存在、结构可解析和失败真实性；不按正文词语或 Markdown 判断技术含义。现有证据足够时最多
一次整体重写；需要新证据时回 Agent loop 调查并重新审核。

## Mechanical drift control

第一开发提交必须加入一个轻量方向检查，且不得发展成答案协议：

1. 旧 `conversational_engineering_model.py` 及对应测试相对 PDR-014 产品基线净行数不得增长，只能删除、简化或薄适配；
2. 拒绝新增 `ENGINEERING_AGENT_*@N` 协议版本、正文词法/Markdown/substring 语义验证和测试工程专有题面/类/方法/path 分支；
3. Phase B 完成声明必须有知识构建/查询 diff 和独立 knowledge evidence；Phase C 必须有 Agent 工具循环、世界模型调用和真实 Browser Turn；
4. 每两小时生成 `knowledge / agent / browser / prompt-schema` 四项进度。仅 Docs/Test/Prompt/Schema 变化时标记
   `NO_PRODUCT_PROGRESS`，下一任务自动回到最早缺失 Phase，开发不停；
5. 改 Prompt/Schema 前必须有 trajectory 和替换实验确认它是最早偏差；一个修复同时复验原问题和两个异质问题。

## Failure attribution

| 观察 | 最早责任层 | 允许的下一动作 |
|---|---|---|
| 正确实体/关系未被构建或内容错误 | knowledge construction | 修解析、准入、表示或 Coverage；不动回答 Prompt |
| 认知存在但搜不到、噪声过大或无法多跳 | cognition retrieval/tools | 修索引、ranking、遍历或工具返回；不补题面规则 |
| source-only Agent 就不会调查或重规划 | Agent harness / ACI | 换 loop、memory、工具接口或成熟 harness adapter |
| source-only 正常，加入认知后退步 | cognition projection/integration | 修工具选择、认知粒度或 Context，不改答案格式协议 |
| 证据充分但答案错误/遗漏 | synthesis | 先检查模型能力与精简任务说明；只做一项通用变更 |
| 答案有明确缺陷但 Reviewer 批准 | reviewer | 改独立审核策略或 Reviewer 能力，不增加 Application 正文规则 |
| 内部结果正确但页面错误 | Web/presentation | 只修显示/会话绑定 |

Provider/network failure 独立记录，不得被归为任何产品语义层，也不得触发答案逻辑改变。

## Interfaces and affected code

允许按最早偏差修改 `src/software_world_model/knowledge_engine/`、现有 Application Agent/Tool、模型网关薄适配和 loopback Web，以及对应的
`tests/` 与 `validation/iteration_010_mvp/`。不得预先扩张重构范围；旧 prompt-heavy 模型边界只允许删除、绕过或薄适配，不能继续净增长。
具体类、文件和接口由 Phase A/B 的 trajectory 与 knowledge evidence 决定，而不是由已知问题题面预设。

## Acceptance scenarios

| Case | Exit condition |
|---|---|
| V-PLAN-DIVERGENCE-001 | 方向检查阻止旧协议净增长，四项进度能把无产品增量自动拉回最早缺失 Phase |
| V-HARNESS-BASELINE-001 | source-only 浏览器基线完成两个异质问题和一个追问，trajectory 证明观察驱动重规划 |
| V-WORLD-MODEL-COGNITION-001 | 五个独立任务证明结构、关系、行为、来源和 Coverage/Unknown 可正确构建、检索和复用 |
| V-INTEGRATED-ALPHA-001 | 三个异质问题和一个追问真实贯通，浏览器立即可体验，WM+Source 对 source-only 有非 locator 正增益 |
| V-BROWSER-CHAT-MVP-BUILD-001 | Phase D 五题、多轮、独立审核和 Codex Gate 全部通过后才取得 MVP 名称 |
| V-PREVIEW-002 | 用户查看真实 Alpha/MVP、比较和已知限制后决定 CONTINUE / REWORK / REDIRECT / REJECT |

## Deferred work

方向确认前不执行 full regression、hidden、第二工程、大型持久化/恢复、性能调优、完整安全矩阵、Production 或大规模重构。最小 exact、
只读、Secret、Citation、独立审核和失败真实性边界始终保留。

## Compatibility, data and security boundaries

现有 `WORLD_MODEL` 与显式诊断基线入口不得静默串线；Phase C 的两臂必须共享 Agent、问题、exact revision 和质量口径，只改变世界模型工具
是否可用。Secret 不进入仓库、Prompt、日志、Evidence 或页面；late/unknown/不合格结果不能覆盖已交付答案。首次体验前只运行受影响、启动、
只读安全和失败真实性测试，方向确认后再做 full regression、hidden、跨工程与 Production 验收。

## Architecture reflection checkpoint

Phase C 首次真实体验后立即判断：Agent 是否像高级工程师一样使用认知并按需读源码；世界模型是否提供了非 locator 的正确增益；多轮
Conversation 是否保持目标；平台安全边界是否仍清晰。任一答案为否，按消融结果回到 Phase A 或 B，不把一次可运行页面解释成架构通过。
Phase D 再判断总体质量是否严格超过 current Codex；Codex 是强基线，不是 Oracle 或裁判。

## Open questions and implementation risks

- 现有 Java 认知资产能否在六小时上限内形成包含行为、条件、异常和状态影响的真实纵切；
- 现有 Agent 工具接口是否足够紧凑、可遍历，还是需要替换 loop/ACI；
- 世界模型增强是否在陌生问题上产生稳定增益，而不是增加噪声或只改善定位；
- fresh Reviewer 能否发现物质错误而不重新演化成正文证明协议；
- 旧 prompt-heavy 路径与三处未提交候选是否会污染基线。

这些风险分别用 knowledge task、trajectory、same-Agent 消融、独立 exact-source 评测和 Git/direction check 回答，不用新增题面规则回答。

## Findings

`FINDING-010-256` 保存投入结构和计划失效的 Git 证据；`FINDING-010-257` 保存成熟 harness、Agent 工具和图认知研究揭示的能力缺口；
`FINDING-010-263—265` 保存 Phase C 首个真实 Browser 的事务漏判、cognition ranking 替换实验，以及 run-005 暴露的 source-native lexical
query 工具契约缺口。后续实现若改变系统边界、认知模型、Agent 工具职责或质量口径，按 implementation feedback policy 写入新的 Finding 并同步唯一 Owner；普通答案失败只形成
最早偏差证据，不形成停工 PDR。

## Authorization

公开 mall exact revision、只读 Source、既有首选/备用执行配置、披露、预算和 loopback evaluation 已在 standing scope 内；新问题、Turn、
候选和同范围外调不重复申请。首选配置成功时备用调用为 0；只有可信不可用结论触发一次透明备用执行。真实 scope delta 才申请最小新增权限。

开发只能因用户明确 STOP/REDIRECT/REJECT、scope delta 请求已实际发出且所有独立工作穷尽，或不可绕过的安全禁止而等待。普通失败和时间上限
都只改变下一实现动作，不结束开发。
