---
id: ITER-008-READINESS
kind: iteration-readiness
status: accepted
authority: project-authorization
owners: [project, architecture, quality]
depends_on: [ITER-008-PROPOSAL, ITER-008-VERIFICATION, ROADMAP-M-002, ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-ACCEPTANCE, ITER-007-RESULT-SLICE-001-STOP-DECISION, SYS-ADR-015, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
code: []
tests: []
iteration: ITER-008
authorized_by: user
authorized_at: 2026-08-14T14:50:51+08:00
product_goal_alignment_verdict: accepted
product_goal_alignment_reviewed_by: user
product_goal_alignment_review_ref: codex-user-message:sha256:eb381cfd1532dec61ec5dba26456c52ffa3c7b92e5a9588f40e98a971c797221
critical_assumption_catalog_digest: sha256:1248eae891fcb2198b373db294213d7c3515369507682a6b1b1631a6e977171c
coding_input: false
---

# Iteration 008 Readiness Review

## Reviewed exact inputs

已核对 ITER-005/006 Acceptance、ITER-007 run-004 与停止裁决、`FINDING-007-008/009`、当前 World Model Answering、Implementation
Query、Agentic Task、Knowledge Update/Use、安全与 Web Contract。

事实结论是：World Model 已持有登录题所需的多个方法和实现事实，当前失败点在固定单方法问答协议；但现有规范又明确要求每题
固定 Plan/Draft/Review 三调用，因此不能在不修改架构与 Contract 的情况下直接开发自适应调查循环。

## Product-goal alignment gate

本轮绑定 `ROADMAP-M-002` Step 1，没有改变最终目标，也没有跳去新的知识域。ITER-005/006 是已接受前置；ITER-007 只提供失败
证据和待重新验收的技术资产。本轮结束时必须让用户从同一正式 Web 以无符号自由问题获得多方法实现答案；查询、表示和业务发现
三层完整时给出有界不存在结论，否则给出具体 Limitation。

结论为 **READY / SLICE-001 ONLY**。方向、能力路径、架构、Contract、exact baseline、预算和独立评测协议均已冻结；后续
SLICE-002 仍由 SLICE-001 的产品 Result、Reflection `CONTINUE` 和新用户授权阻断。

## Outcome, scope and non-goals

Outcome 是受限 Agent 只查询提问前构建的 World Model，根据 typed result 自适应调查多个候选和方法，然后在正式 Web 交付答案、
Gap 与 Citation，并逐题不低于成熟源码 Agent。

本轮不扩大 Java 语义闭包，不读取 README/配置，不做多语言、通用自治 Agent、问题驱动更新或 Production Activation。Agent 是查询
控制器，不是新的知识权威；回答事实仍只来自可复用 Snapshot。

## System contracts and unresolved decisions

以下输入已经闭合：

1. 新增 bounded Agentic World Model investigation ADR，明确为何放弃固定单方法消歧，以及 Agent、平台和 World Model 的 Owner；
2. 修订 World Model Answering、Implementation Query、Agentic Task、runtime flow、Gateway、Capability Evaluation 与安全边界；
3. 将查询结果完整性、知识表示 Coverage、业务语义发现召回完整性分别定义；pagination/total/truncated 只证明第一层，只有三层
   都有独立 Oracle 时才允许 bounded absence；
4. 把当前固定三调用文档门禁升级为“有界可变调查 + 单次 Draft + 独立 Review”的机械校验；
5. 冻结每题最大调查步数和模型调用（均至少为 2）、query/result 单步与总字节、总时长、Support 数量、trace 字节、超限行为和 retry 规则；
6. 冻结 ITER-007 技术资产清单和 exact Git baseline，明确哪些代码复用、哪些协议被废弃；
7. 冻结回答 Agent 的禁止面：Repository、源码文件、原始 Evidence、完整 AST、Knowledge Update 和 Direct fallback 均不可见；
8. 冻结逐 Need/Claim 评分表、重大错误定义、独立裁决人、争议与同分规则，并分别统计 World Model 建模成本、单题问答成本、
   多题摊销成本和源码 Agent 调查成本。
9. 冻结 Proposal A1—A8 三列表的 exact 摘要、最早反证、`V-DIAG-001` 逐层归因、SLICE-001 最小 bounded-absence/Limitation 双反例、每个 Slice 的
   `V-REFLECT` 结构化模板、独立决策 Owner 与语义；复盘 PASS 只代表审查完成，`CONTINUE/ACCEPT` 才代表方案可继续或可接受。

闭合证据为 `SYS-ADR-015`、Manifest 的 `ITER-008-SYSTEM-CONTRACT-SET@1` fileset digest、budget digest
`sha256:edb492b7…1012`、成熟 Agent/rubric/value protocol raw digest，以及
`V-PRE-001`—`V-PRE-007` 的 readiness PASS。任何这些文件或 digest 变化都会使本 Readiness stale，不能静默继承授权。

实现证据随后按治理规则形成 `FINDING-008-019`：run-010 证明原 Owner 允许模型提前 FINISH，用户既有显式 protocol redirect 又要求
集成层适配模型。该 system-contract Finding 已在同一已授权 SLICE-001 范围内写回原 12 份 System 输入；预算、Source-off、三层
完整性、18/18、no-retry、Web/canary/Activation 阻断与 Slice 范围均未扩大。重冻结后的
`ITER-008-SYSTEM-CONTRACT-SET@1` exact digest 为
`sha256:206d0b2ecc1dbd82b632b825f2284f7d6971b886840f903b1d6368f29c28331b`；它取代旧 fileset 作为当前实现输入，且必须由最终 docs gate
重算一致后才可形成 clean candidate。这是显式 Finding/redirect revalidation，不是静默继承原 digest。

run-011 又形成 `FINDING-008-021`：强制 candidate discovery 同时充当 terminal evidence class，会让可理解的模型语义选择与平台
保守证据责任冲突，并在非零候选时留下过早结束风险。该 Finding 将 raw candidate evidence alias 无条件向上归一为 method evidence，
不读取问题、工程、Case、Oracle 或未来 Result；预算、三层完整性、Source-off、no-retry 与所有产品阻断不变。写回后的当前
`ITER-008-SYSTEM-CONTRACT-SET@1` exact digest 为
`sha256:11b8b2d56386451802bc64214547abe253d54f26855a1ba7f9428acb43511a54`，并由 Manifest 与 docs gate 共同约束。

## Slice, dependency and risk closure

本轮有两个依次单独授权的纵向 Slice，不能拆成 Planner、工具、Web、评测等内部组件完成项：

- `SLICE-001`：最小多候选/多方法调查、Source-off、Draft/Review/Citation 和正式 Web；产品代码冻结后执行一份全新早期 canary，
  至少含 1 条无符号多方法 answerable 与 2 条互补 boundary，并先密封成熟源码 Agent 同题结果；产品 Gate、early absence、
  `V-DIAG-001`、early Agent 对照与
  `V-REFLECT-001` 未 PASS，或复盘决定不是 `CONTINUE`，均不得授权下一段；
- `SLICE-002`：分页、三层完整性、cycle/progress、预算与安全加固；再从同一正式 Web 执行两个最终隐藏工程、成熟源码 Agent 对照
  和现场题。

公开 LoginService 仅作回归，不得用于证明泛化。早期 canary 与最终工程不得复用；它们必须在各自 Slice 产品代码冻结前保持
不可见并位于已冻结 Java 语义闭包内。披露后任何产品修改都会烧毁对应项目、问题、baseline 与 target，失败 Result 必须保留。

## Verification readiness

已经冻结：

- 两个小型未见 Java 工程、4 条 answerable、2 条 boundary 的持有与披露协议；
- 至少 2 条多方法题、3 条无符号名题和每工程至少 1 条无符号题；
- 成熟源码 Agent 的 exact 版本、工具权限、revision、预算、运行顺序和密封结果格式；逐 Need/Claim rubric、重大错误定义、
  独立裁决人与争议/同分/失败规则；early 对照必须冻结零重大错误、逐 Need/Claim 不退步和最大时延/成本阈值；
- World Model 建模、单题问答、多题摊销与源码 Agent 调查四类成本的独立统计口径；
- 正式 Web 的 2 条现场题，其中至少 1 条无符号名并执行 `V-XD-002` 的跨域组合；
- 重大错误 0、逐题不退步、Source/Update/Direct fallback 全部为 0；
- 登录/下单回归和所有旧 accepted capability 回归；
- Production Activation `NOT_EXECUTED`。

## Architecture reflection gate readiness

Proposal A1—A8 的 exact section digest `sha256:1248eae8…171c` 已同时写入 Manifest 与本 Readiness metadata，`V-PRE-007`
已执行。A1—A6 的最小可行性证据在
SLICE-001 到期，A7/A8 只保留早期阻断反证并在 SLICE-002 下最终 Verdict；A6 的正向价值指标、单位、比较方向、数值阈值、
复用周期、计算/重放协议、独立裁决 Owner 与 Agent 缓存政策必须在编码前由用户收据冻结，成熟源码 Agent protocol/rubric 也必须是 exact digest，
且能在 SLICE-001 取得早期实测；Result 必须保存可重放 exact JSON 报告、输入 digest 和独立裁决收据，不能自填 actual；early canary 会用互补 boundary 验证 absence/Limitation，并先密封成熟源码
Agent 同题结果；
`V-DIAG-001` 能定位 Source/Snapshot/Query/Trace/Draft-Review/Web 的首次偏差；每个 Slice 恰好一个 Reflection Case；Result 会逐假设
记录 exact Evidence、问题分类、分层诊断、Agent 对照、Finding 去向、下一风险和明确决定。中间段只有产品 Case 全部 PASS、
`V-REFLECT-001 PASS`、`reflection_decision: CONTINUE` 与用户另行授权四项同时成立，SLICE-002 才能成为活动编码输入。

## Authorization decision

**ACCEPTED / ITER-008-SLICE-001 AUTHORIZED。** 用户消息 `codex-user-message:sha256:eb381cfd…7221` 明确要求“开发ITER-008”，
据此接受上述 exact Readiness，并仅授权 `ITER-008-SLICE-001`。授权允许修改该 Slice 列明的 System 实现、`src/`、产品测试和
validation，但不授权新的外部模型分派、早期 canary 披露、SLICE-002、Production Activation、推送或把固定三调用资格当作新
bounded Strategy 资格。SLICE-001 产品代码冻结后，必须先取得绑定 exact freeze 的新披露/Provider 授权。
