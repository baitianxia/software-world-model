---
id: ITER-010-PDR-005
kind: project-decision
status: accepted
authority: project-decision
owners: [product, project, architecture, engineering, quality, ai, interface, security]
depends_on: [ITER-010-PDR-003, ITER-010-PDR-004, FINDING-010-130, FINDING-010-131, FINDING-010-132, FINDING-010-133, SYS-ADR-017, SYS-ADR-018, SYS-QUALITY-ACCEPTANCE]
code: []
tests: []
iteration: ITER-010
decision: REWORK
rework_strategy: FREEZE_V7_AND_RESTART_WITH_LAYER_ATTRIBUTION_AND_ENGINEERING_COGNITION
decision_ref: local-user-message-utf8:sha256:291f60538287486c899e285ebe74d587b9c8b5ba11937ccc12bfd9122fb08499
effective_scope: ITER-010-SLICE-001-direction-recovery
coding_input: true
---

# PDR-005：冻结逐题修补，按认知资格和责任层归因重启 ITER-010

> Current execution amendment：`ITER-010-PDR-007` 把 DeepSeek 闲时变为 planned dispatch 硬门禁并将 run-043 标记为调度 FAIL；
> `ITER-010-PDR-006` 保留本决定的 Gate，但把检查点、hard stop、REWORK 和授权边界收窄为非终止性控制。真正的权限 gap 在 exact
> freeze 后直接申请；现有本地授权覆盖修复时持续开发。

## Context and authority

run-035—042 连续消耗大量开发时间和 Provider token，仍没有形成可由用户确认方向的合格 Chat。每次失败后又修改 Prompt、Schema、工具
copy domain、查询提示或 Reviewer 输入，再执行双 Provider Conformance 和同一五轮重跑；该循环没有先证明最早故障属于世界模型、认知
投影、Agent、答案还是 Reviewer，也没有遵守“先体验判向、再夯实”的项目原则。

用户明确停止这条旧执行链，并要求把全部讨论落实到文档后由一个新的开发对话重启；同时指出只用 Maven 模块与依赖构建知识根本不能
体现工程问题。本条消息按 exact UTF-8 原文在本地密封为
`local-user-message-utf8:sha256:291f60538287486c899e285ebe74d587b9c8b5ba11937ccc12bfd9122fb08499`；它不是平台消息收据，
不冒充 PDR-004 Readiness 的正式授权 identity。

本决定没有改变产品目标、双核心职责、安全边界或总体数据流，故决定仍是 `REWORK`，不是 `REDIRECT`。PDR-004 的 accepted Readiness 与
Slice1 产品/System 编码及本地确定性验证范围继续作为正式权限锚点；旧开发对话、旧执行待办和 v7 假设不再具有权威。开发可以在名为
“开发 ITER-010”的全新对话中直接接手，不要求复用原对话上下文。当前沿用 Slice1 是为了复用已授权项目入口并保留失败和 timebox 责任，
不是把开发绑定在旧对话或永远禁止另建 Slice；只有后续证据确需改变交付边界时才按治理流程切换 Slice，换对话本身不触发该流程。

## Decision

### 1. 冻结 v7 和同题碰答案循环

`FINDING-010-131` 的 path-relevance query guidance 与 review-scope policy 只保留为未接受的本地症状实验。逐层归因完成前：

- 不把 v7 写入 current System Contract，不从 fresh Conformance 或第八次同五轮重跑继续；
- 不再修改 Prompt、Schema、Tool policy、搜索排序或 Reviewer 文案；
- 不删除 dirty candidate，也不整批追认；归因支持的最小部分以后可以在正确 Owner 层重新设计。

### 2. Maven-only 不是工程认知

Maven 模块和 POM 本地依赖是正确但狭窄的 Structure Profile。它能回答模块组成与构建依赖，不能表达实现、行为、职责、调用链、业务规则、
条件、状态、副作用、配置接线或异常。它的 `COMPLETE` 不等于问题充分或工程认知有资格，不能再命名为 `full cognition`。

World Model 概念从始至终不变：它维护 exact revision 上持久、版本化、可验证、可更新的软件认知。工程 Conversation 以 Cognition
Capability Manifest 绑定同一 revision 上多个 profile-specific Read Authority，并按原问题 material Need 判断认知资格。多域组合发生在
Application 只读投影层，不制造 mixed-profile Snapshot/Read Set。对于行为问题，可体验纵切至少包含结构与实现/行为认知；Source 可核实、
补全或纠正当前 Turn，却不能被回填成 World Model 贡献。

### 3. 失败必须先逐层归因

恢复后的第一阻断 Gate 使用现有产物、exact Source 和零外部模型调用，密封：

`Source truth → Knowledge construction/admission → Cognition projection/query → Conversation understanding → Agent investigation →
Evidence Package → Answer synthesis → Independent Review → Web`

每个 material fact 分别记录 first divergence、没有阻断错误的 downstream guard failure 与 display failure；一题可以有多个故障。归因通过
替换实验而不是最终答案猜测：World Model only、同 Agent source-only、同 Agent eligible cognition+source、complete-evidence bypass、
Reviewer seeded-good/seeded-bad 和 authorized Result→Web 分别隔离各层。下一项产品修改只能进入最早有证据的 Owner 层。

run-042 的当前可接受结论只有：Maven-only 对行为问题无认知资格；Agent 没有取得授权源码中的多个决定性事实；Reviewer 既批准了不完整
Limitation，也曾扩大当前问题；Web 当前没有 first-divergence 证据。不能再把它归结为单一提示词问题。

### 4. 快速恢复检查点

旧 14 小时和 PDR-003 的 timebox FAIL 永久保留，不追认为合格，也不以改计划重置。新的开发对话使用附加 recovery hard stop：

| 从首个新产品代码改动起 | 必须交付 | 调用与测试边界 | 未达到时 |
|---:|---|---|---|
| T+60 分钟 | 现有 run/source/package/review 的逐层归因报告；此前应尽量在代码改动前完成 | 外部模型 0；允许只读检查和本地离线投影 | 交付唯一最早阻塞，禁止改 Prompt/Schema/Tool/Review |
| T+180 分钟 | exact revision 上有行为含义的多域 Cognition Manifest、问题相关投影，并接回现有可启动 Web | 只跑相关单测、启动和安全 smoke；不跑 full regression | 停止扩域，交付最后可运行版本和 Gap |
| T+240 分钟 | 浏览器可体验版；一条真实语义链和两个未参与修复的异质问题，真实限制可见 | live 前另取 exact grant；最多一个 Ark direction canary session，不批量重跑 | 立即交用户体验并记 `FAIL / REWORK`；停止外部调用和新增功能 |

体验在实现前冻结问题类别和判定规则，不为具体答案写逻辑：至少一组 Turn 必须体现初问→省略指代追问或纠正→深入/总结的真实语义链，
另有两个未参与修复的异质问题；整体覆盖世界模型确实覆盖的结构、行为/调用流程、职责/失败边界/Unknown。同一 Session 中三个互不相关的
独立问答不算 Chat，单题答对无效。已有 Web Access PASS 复用，不重新建设页面壳。

### 5. 世界模型与 Agent 的独立价值门

- `engineering-cognition-eligible + source` 必须先过绝对质量门，不得弱于同 Agent `source-only`；
- 必须产生至少一项非 locator、与问题直接相关并可追溯到 World Model 的认知贡献；每题机械返回相同整包不算检索贡献；
- 未满足时 A1 保持未证明，不能用 Source 最终找到了答案冒充 World Model 有效；
- current Codex 是强外部基线，不是 Oracle、Reviewer 或 Source truth。它在方向体验后作为隔离参赛者；事实依据来自 exact Source、配置、
  测试与正式 World Model Support。

### 6. Provider、成本和验证

- Ark 始终是 primary；DeepSeek 只在同一 Turn 的 Ark attempt 已密封且满足 ADR-017 fallback 原因时透明重跑完整链，不用于“同时比较模型”；
- Adapter/Configuration/endpoint/model/transport/rendering identity 未变化且资格未过期时复用 Conformance。领域 Prompt、答案 Schema 或产品
  变化本身不触发 Ark/DeepSeek Conformance；需要验证的是对应 Agent Strategy/Capability，不是重复测传输兼容；
- DeepSeek 所有 planned development/evaluation dispatch 必须通过 PDR-007 非高峰硬准入；planned Turn 不得在峰时开始后再以完整质量为由
  触发 fallback。已合法开始的单个 request 仍按既有零重试和结果密封规则结束，调查、Citation 和独立 Review 不因 token 费用裁剪；
- Alpha 前只执行 targeted impact、startup、security、failure-truth checks；full regression 在用户 `CONTINUE` 后进入 hardening。

## Scope and authorization consequences

- 文档检查通过后，`ITER-010-SLICE-001` 继续为 `authorized / current-development / coding_input=true`；全新的“开发 ITER-010”对话可
  直接接手，无需再次确认相同的产品/System 编码和本地确定性验证权限，也不需要复现旧对话过程。
- 本消息不新增 Provider/model、credential、动态 mall Source/resource disclosure、live Browser、hidden、Slice2/3 或 Production
  Activation 权限；所有旧 live grant 已消费，当前仍无 external execution authority。
- 新对话第一项工作是 `V-LAYER-ATTRIBUTION-001`，不是运行测试全集、fresh 双 Provider Conformance、修 v7 或重跑旧五轮。

## Revisit condition

只有 `V-LAYER-ATTRIBUTION-001` 密封 first divergence，且 `V-COGNITION-ELIGIBILITY-001` 证明多域认知对三个异质问题具备准确 Coverage/
Gap 和问题相关投影，才允许一个新的 Ark direction canary。浏览器体验交付后立即由用户判断 `CONTINUE / REWORK / REDIRECT / REJECT`；
只有 `CONTINUE` 才解锁 hardening 与 full regression。
