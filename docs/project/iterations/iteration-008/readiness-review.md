---
id: ITER-008-READINESS
kind: iteration-readiness
status: proposed
authority: project-review
owners: [project, architecture, quality]
depends_on: [ITER-008-PROPOSAL, ITER-008-VERIFICATION, ROADMAP-M-002, ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-ACCEPTANCE, ITER-007-RESULT-SLICE-001-STOP-DECISION]
code: []
tests: []
iteration: ITER-008
authorized_by: not-authorized
authorized_at: not-authorized
product_goal_alignment_verdict: not-reviewed
product_goal_alignment_reviewed_by: not-reviewed
product_goal_alignment_review_ref: not-authorized
critical_assumption_catalog_digest: not-frozen-proposal-only
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

当前结论为 **NOT READY**。方向与能力路径明确，但架构、Contract、exact baseline、预算和独立评测尚未冻结。

## Outcome, scope and non-goals

Outcome 是受限 Agent 只查询提问前构建的 World Model，根据 typed result 自适应调查多个候选和方法，然后在正式 Web 交付答案、
Gap 与 Citation，并逐题不低于成熟源码 Agent。

本轮不扩大 Java 语义闭包，不读取 README/配置，不做多语言、通用自治 Agent、问题驱动更新或 Production Activation。Agent 是查询
控制器，不是新的知识权威；回答事实仍只来自可复用 Snapshot。

## System contracts and unresolved decisions

Readiness 前必须全部闭合：

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

任一项仍是 proposal 说明而非 current System Truth 时，不得授权编码。

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

授权前还需冻结：

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

当前 Proposal 已列出 A1—A8，但 **V-PRE-007 尚未执行**。Readiness 接受前必须把该三列表 exact SHA-256 同时写入 Manifest 与本
Readiness metadata，并验证：A1—A6 的最小可行性证据确实在
SLICE-001 到期，A7/A8 只保留早期阻断反证并在 SLICE-002 下最终 Verdict；A6 的正向价值指标、单位、比较方向、数值阈值、
复用周期、计算/重放协议、独立裁决 Owner 与 Agent 缓存政策必须在编码前由用户收据冻结，成熟源码 Agent protocol/rubric 也必须是 exact digest，
且能在 SLICE-001 取得早期实测；Result 必须保存可重放 exact JSON 报告、输入 digest 和独立裁决收据，不能自填 actual；early canary 会用互补 boundary 验证 absence/Limitation，并先密封成熟源码
Agent 同题结果；
`V-DIAG-001` 能定位 Source/Snapshot/Query/Trace/Draft-Review/Web 的首次偏差；每个 Slice 恰好一个 Reflection Case；Result 会逐假设
记录 exact Evidence、问题分类、分层诊断、Agent 对照、Finding 去向、下一风险和明确决定。中间段只有产品 Case 全部 PASS、
`V-REFLECT-001 PASS`、`reflection_decision: CONTINUE` 与用户另行授权四项同时成立，SLICE-002 才能成为活动编码输入。

## Authorization decision

**NOT READY / NOT AUTHORIZED。** 下一步需要先完成架构与 Readiness 材料；本文件本身不授权 System 文档、`src/`、产品测试或
validation 实现。
