---
id: ITER-007-SLICE-003
kind: development-slice
status: proposed
authority: proposed-development
owners: [quality, product]
depends_on: [ITER-007-PROPOSAL, ITER-007-READINESS, ITER-007-SLICE-002, ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-ACCEPTANCE]
code: [validation]
tests: [tests, validation]
iteration: ITER-007
coding_input: false
product_goal_gate: V-000
product_goal_accepted_capability_refs: [ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-ACCEPTANCE]
product_goal_cross_domain_case_ids: [V-XD-003]
product_goal_web_checkpoint_id: V-WEB-003
product_goal_live_ad_hoc_checkpoint_id: V-ADHOC-001
product_goal_slice_gate_case_ids: [V-XD-003, V-WEB-003, V-007, V-007A, V-008, V-ADHOC-001, V-009]
---

# SLICE-003：代码冻结后的 held-out 产品验证

## Status and dependencies

`HISTORICAL PROPOSAL / NOT EXECUTED / PERMANENTLY NOT AUTHORIZABLE IN REJECTED ITER-007`。本 Slice 的前置 SLICE-001 已
产品 FAIL，SLICE-002 也未执行。frontmatter 保留 `proposed` 只表示原计划未执行；任何后续 held-out 验证必须在新 Iteration 重新
冻结项目、问题、baseline、target 和用户授权。

## Product-goal contribution and cumulative integration

- Product gap shortened: 证明能力不只适用于参与开发的工程，而能在两个真正未见工程上产生可测的通用 Java 源码问答增量。
- Existing capabilities combined: `V-XD-003` 同题组合接受后的 `CALLS` 与本轮功能发现、condition/state/return/exception facts。
- User-visible Web questions at slice end: 12 条 answerable、4 条 boundary 和 3 条现场题全部通过正式 Web 执行。
- Slice stop / redirect signal: target 未达、重大错误、Agent 可答而模型 Gap、held-out 污染或 fallback 均使 Iteration FAIL/redirect。

## Current vs expected behavior

开发结束后才由独立评测方提供两份此前隐藏身份与源码的真实 Java/Maven 工程。系统先无问题构建 Snapshot，再运行隐藏自由题、
成熟源码 Agent 对照和现场问题。评测不能继续推动 parser、Schema、query、prompt 或 runtime 修改。

## System contracts and invariants

- 工程身份、源码和问题在产品代码冻结前对实现团队不可见，baseline 由独立环境运行；
- 从披露到最终 Result seal 的任何产品变化都使原结果永久保留，并要求两工程、完整 12+4 suite、baseline 与 target 同时更换后
  重新冻结；seal 后 capsule consumed；
- 12 条 answerable 是唯一 supported count 分母，至少 6 条无符号名且每工程至少 2 条；
- target 至少 `min(12, max(baseline + 4, 8))`，两个工程和四类问题均须有增量；
- 4 条 boundary 独立 4/4 Gap；若成熟 Agent 仅用同一源码可答，模型 Gap 直接 FAIL；
- 每题 exact 三调用；问题阶段 Source/Update/Direct fallback delta=0；Production Activation 无条件 `NOT_EXECUTED`。

## Interfaces and affected code

只新增/执行独立 validation assets、exact manifests、disclosure receipts、Agent comparison 和 Product Result；不修改 `src/` 产品代码。
正式人工体验仍使用产品拥有的 HTTP/Web/Citation 入口。

## Compatibility, data and security boundaries

held-out Source 只在独立 Update 执行边界内授权；答案模型仍看不到 Source、Artifact/Evidence payload 或 Direct tools。Result 必须保存
code freeze、disclosure、source/suite digest、模型调用、fallback、Citation 和成本收据。

## Open questions and implementation risks

- 如果 held-out 工程曝光后才发现 frontend 缺口，本次结果必须失败，不能就地修复；
- boundary 题不能按“反射/DI”标签预设 Gap，必须由独立 Oracle 先证明 exact source 不足；
- 构建成本可能只在多问题复用时划算，必须如实报告 break-even。

## Acceptance scenarios

1. 两工程无问题形成 Snapshot/Bundle；disclosure log 证明冻结前实现方未见工程身份/源码/问题。
2. 12 条 answerable 达到 target，重大错误 0，旧 baseline 支持题不退步。
3. 4 条 boundary 正确 Gap；支持答案逐题正确性/完整性不低于同资源成熟源码 Agent。
4. `V-XD-003` 与 3 条现场题通过正式 Web；现场至少 2 条无符号名，包含 answerable 跨域题和真实 boundary。
5. 每题严格 3 次模型调用；构建/提问调用数、Token、时延和多问题摊销完整披露。
6. ITER-003—006 回归 PASS；Production Activation 为 `NOT_EXECUTED`。

## Findings

链接本轮 [Findings](../findings/README.md) 与[实现发现回写规则](../../../governance/implementation-feedback-policy.md)。
