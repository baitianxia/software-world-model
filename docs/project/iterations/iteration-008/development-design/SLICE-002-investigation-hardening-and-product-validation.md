---
id: ITER-008-SLICE-002
kind: development-slice
status: proposed
authority: proposed-development
owners: [engineering, architecture, quality, product]
depends_on: [ITER-008-PROPOSAL, ITER-008-READINESS, ITER-008-SLICE-001, ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-ACCEPTANCE]
code: [src/software_world_model/application_services, src/software_world_model/knowledge_engine, src/software_world_model/ai_infrastructure, src/software_world_model/interface]
tests: [tests, validation]
iteration: ITER-008
coding_input: false
product_goal_gate: V-000
product_goal_accepted_capability_refs: [ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-ACCEPTANCE]
product_goal_cross_domain_case_ids: [V-XD-002]
product_goal_web_checkpoint_id: V-WEB-002
product_goal_live_ad_hoc_checkpoint_id: V-ADHOC-001
product_goal_reflection_gate_case_id: V-REFLECT-002
product_goal_slice_gate_case_ids: [V-NEG-001, V-HARDEN-001, V-XD-002, V-WEB-002, V-HIDDEN-001, V-COMP-001, V-ADHOC-001, V-REGRESSION-001, V-009, V-REFLECT-002]
---

# SLICE-002：完整性加固与最终产品验证

## Status and dependencies

`HISTORICAL PROPOSAL / NOT EXECUTED / PERMANENTLY NOT AUTHORIZABLE IN REJECTED ITER-008`。SLICE-001 的 Result 决定
`REDIRECT` 而不是 `CONTINUE`，用户也从未授权本段。frontmatter 保留 `proposed` 只表示原计划未执行；以后若需要其中任何内容，
必须在新 Iteration 重新提案、冻结和授权。

## Product-goal contribution and cumulative integration

- Product gap shortened：把最小多方法调查扩展为分页可穷尽、三层完整性可判定、预算与 Reviewer 可稳定失败关闭的产品能力，并在
  未见工程上证明逐题不低于成熟源码 Agent。
- Product capability-path step advanced：完成 `ROADMAP-M-002 / step-1-java-result-driven-world-model-investigation` 的最终产品 Gate。
- Existing capabilities combined：继续复用 ITER-005 Workspace/Update/Web/Citation、ITER-006 declaration/`CALLS` 和 SLICE-001 已封存的
  最小调查闭环。
- User-visible Web questions at slice end：两个最终隐藏工程 4+2、`V-XD-002` 和 2 条现场题全部走同一正式 Web；现场至少 1 条无
  符号名且必须执行跨域组合。
- Slice stop / redirect signal：三层完整性不能独立证明、Agent 对照逐题退步、出现表示缺口/题目补丁/fallback、最小预算失控或正式
  Web 链不一致，均保留 FAIL，不以扩大语法或知识域修补本轮。
- Critical assumptions tested：复核 Proposal A1—A6，并在最终矩阵对 A7/A8 下正式 Verdict；最终覆盖 A1—A8。
- Reflection gate and success decision：`V-REFLECT-002`；只有方案复盘决定 `ACCEPT` 才可申请 Iteration Acceptance。

## Current vs expected behavior

SLICE-001 只证明最小结果驱动调查和三层完整性在一份 early canary 的最小闭包上可行。本段补齐更广的
pagination、total/truncated、progress/cycle、预算、
Reviewer 和负向结论，但不改变 World Model 知识权威。预期系统能区分：

1. 查询结果完整性：所有页已读取且没有截断；
2. 知识表示 Coverage：授权单元均有明确 disposition，相关字段没有因 unsupported/failed 被隐藏；
3. 业务语义发现召回完整性：同义词、不同命名和不同入口反例不会漏掉相关实现。

只有三层均由独立 Oracle 证明时才允许 bounded absence；否则返回具体 Limitation。

## System contracts and invariants

- 继承 SLICE-001 的 exact Snapshot、typed operation、sealed trace、Draft/independent Review、Source-off 和 no-fallback 不变量；
- 候选与查询结果提供稳定 pagination、total/truncated、Coverage/disposition 与 canonical order；
- deterministic progress/cycle detection 防止重复查询或无界展开，超限返回具体 Limitation；
- Reviewer 必须拒绝漏页、漏候选、错误负向结论、Support 缺失和超出 Context/Modality/Coverage 的 Claim；
- 成熟源码 Agent baseline 在 World Model 输出前密封，使用同 revision、同问题和冻结的等价资源上限；
- 逐 Need/Claim rubric、重大错误定义、独立裁决人、争议/同分/失败规则在代码冻结前固定；
- 分别报告 World Model 建模成本、单题问答成本、多题摊销成本和源码 Agent 调查成本；
- 提问不读取 Source、不更新知识、不 Direct fallback；Production Activation `NOT_EXECUTED`。

## Interfaces and affected code

只加固 SLICE-001 已接入的同一 World Model Answering、Implementation Query、Agentic Task、query service、egress qualification、
runtime/HTTP/Web/Citation 链。不得新增平行入口、validation-only 策略或源码 Agent 路径。

最终两个隐藏工程曝光后，本段不得再修改产品代码；validation 只负责执行冻结协议、密封 evidence、对照和逐 Case 裁决。

## Compatibility, data and security boundaries

SLICE-001 Result 与 code freeze 不得被本段追溯改写。本段形成新的 product code freeze；早期 canary 不得复用为最终工程。
ITER-003—006 accepted regression 必须 PASS，且不得用旧 Direct 路径兜底。

最终 trace/Result 必须绑定 exact Snapshot/Bundle、每个 query page、Coverage/disposition、Support、预算、Draft/Review、Citation、Agent
baseline、rubric verdict、四类成本和 terminal audit。

## Open questions and implementation risks

- 业务语义发现召回完整性可能无法在当前表示上证明；这应触发 representation gap，而不是偷偷降低负向结论门槛；
- 多页查询和 Reviewer 会放大时延，必须在冻结预算内实测 P50/P95 和多题摊销；
- 评测者对“完整性不退步”可能分歧，必须由预先指定的独立裁决规则解决；
- 若隐藏工程曝光后才发现当前 Java 语义闭包不足，必须保留 FAIL 并进入 Step 2，不能就地扩 parser。

## Acceptance scenarios

1. pagination/total/truncated、三层完整性、progress/cycle、预算与 Reviewer deterministic matrix 全部 PASS。
2. 正式 Web 执行 `V-WEB-002` 与 `V-XD-002`；页面、Citation、console、terminal 和 audit 可人工检查。
3. 两个代码冻结前未见且不与 early canary 重复的真实 Java 工程，4 answerable 全部 supported、2 boundary 全部正确；至少 2 条
   多方法、3 条无符号名且每工程至少 1 条无符号名。
4. 成熟源码 Agent baseline 先运行并密封；按逐 Need/Claim rubric 无重大错误、逐题不退步；Agent 可答而 World Model Gap/遗漏直接 FAIL。
5. 2 条用户现场题中至少 1 条不含符号名并执行 `V-XD-002`；同一正式 Web、无产品修改、无 fallback。
6. Source/Update/Direct/raw Evidence attempt 全部为 0；四类成本与 P50/P95 如实披露。
7. ITER-003—006 accepted regression PASS；Production Activation `NOT_EXECUTED`。
8. 形成 exact Slice Result 并完成 `V-REFLECT-002`：复核 A1—A8、正向价值阈值、复杂度/收益、全部 Finding 和能力路径，作出
   `ACCEPT / REDIRECT / REJECT`；只有 `ACCEPT` 才可申请 Iteration Acceptance。

## Architecture reflection checkpoint

最终产品 Case PASS 仍必须经过方案复盘，确认 World Model 相对成熟源码 Agent 的质量、成本与复杂度没有让当前架构失去继续投入的
意义。Result 的 `reflection_gate_case_id` 必须为 `V-REFLECT-002`，`reflection_gate_status` 必须为 `PASS`，并单独记录
A1—A8 的结构化证据、问题分类、逐层诊断、独立 Owner 和 `reflection_decision`。Reflection PASS 只证明复盘完整；决定为
`REDIRECT/REJECT` 时不得创建 Acceptance。

## Findings

实现与产品验证发现按 [Implementation Feedback Policy](../../../governance/implementation-feedback-policy.md) 记录。隐藏证据一旦指向
表示缺口，本 Slice 必须停止；不得把公开或隐藏题目转成工程、关键词、符号或 fixture 补丁。
