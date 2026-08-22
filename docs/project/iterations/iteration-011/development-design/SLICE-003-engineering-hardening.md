---
id: ITER-011-SLICE-003
kind: development-slice
status: proposed
authority: proposed-development
owners: [engineering, architecture, quality, product]
depends_on: [ITER-011-PROPOSAL, ITER-011-READINESS, ITER-006-RESULT-ACCEPTANCE, ITER-011-SLICE-002]
code: [src/software_world_model/application_services, src/software_world_model/ai_infrastructure, src/software_world_model/interface]
tests: [tests, validation]
iteration: ITER-011
coding_input: false
product_goal_gate: V-000
product_goal_accepted_capability_refs: [ITER-006-RESULT-ACCEPTANCE]
product_goal_cross_domain_case_ids: [V-XD-003]
product_goal_web_checkpoint_id: V-WEB-003
product_goal_reflection_gate_case_id: V-REFLECT-003
product_goal_slice_gate_case_ids: [V-GENERAL-003, V-RERETRIEVE-003, V-PERSIST-003, V-CONFLICT-003, V-HARDEN-003, V-SEC-003, V-PERF-003, V-XD-003, V-WEB-003, V-CANARY-003, V-NEG-EARLY-003, V-COMP-EARLY-003, V-DIAG-003, V-REGRESSION-003, V-REFLECT-003]
---

# SLICE-003：用户确认后的工程化夯实

## Status and dependencies

`PROPOSED / NOT AUTHORIZED / NOT CODING INPUT`。Slice2 exact Result 必须为 `PASS + user CONTINUE`，且 A1/A2 均 `SUPPORTED`；随后另取
Slice3 开发授权，并在任何 comparison 编码/执行前由新用户收据冻结三臂 protocol、rubric、cache、预算、价值指标/阈值和成本复用周期。
Slice2 未 `CONTINUE` 时不得启动本段。

## Product-goal contribution and cumulative integration

- Product gap shortened：把已获确认的 Alpha 方向工程化为可恢复、可跨工程、可处理复杂证据冲突并可完整回归的候选。
- User-visible delta：同一 Web 在完整第二工程 canary 上可交付答案/Limitation/Citation，并提供性能、安全和三臂对照的精确报告。
- Stop signal：新工程/复杂 gap 需要特判；补证不收敛；恢复/冲突/去重破坏 Ledger/Package identity；越权/泄密；性能或回归 Gate 失败；
  完整 Cognition 自身质量不合格或 early value Gate 失败。
- Critical assumptions：累积到 A1—A3，并以 `V-COMP-EARLY-003` 提前判断 A4。
- Reflection：`V-REFLECT-003`；只有用户新 `CONTINUE` 才可申请正式验收。

## Direction preview checkpoint

本段引用 `V-PREVIEW-002` 的 exact `CONTINUE` Result，不再重复方向探针。它必须形成独立工程化 Result 和用户可见 Web checkpoint，不能
用单元测试、CLI 或 hidden 计数代替。

## Current vs expected behavior

进入本段时产品方向已由 Probe 和 Alpha 两次真实体验确认，但 persistence、复杂 verification investigation、conflict/dedup、跨工程
完整 canary、security/performance 和 full regression 尚未证明。预期同一协议在这些条件下保持答案优先、证据支持、独立审核和失败关闭。

## System contracts and invariants

- hierarchy/checklist、Investigation、Broker/Worker、Ledger/Package、Answer/Application acceptance/Reviewer identities 全部版本化并可恢复。
- Verification Investigation 可按 prior Result 多步补证；不固定一轮。package revision、model calls、Broker operations、source bytes、wall time、
  no-progress 以高安全熔断控制，不能为了调用次数降低质量。
- conflict、partial、unknown、failure 和 rejected decision 必须保留在 boundary/audit，不能支持肯定 Claim；去重不能丢失不同 provenance。
- Source/FS/Shell/network/credential direct authority 对 Investigation/Answer/Reviewer 仍为 0；只有 Broker/Worker 受控只读。
- 三臂固定同 revision/model/questions/resource budget/cache/rubric/evaluator；完整 Cognition 和成熟 Agent 先分别过质量 Gate，再判断增益。

## Interfaces and affected code

允许持久 Ledger/Package、恢复、复杂补证状态机、conflict/dedup、资格/安全/性能 instrumentation、hidden/comparison runner、
同一 Web developer details 和完整 tests/validation。禁止项目 adapter、题目 classifier 或 validation-only 产品入口。

## Compatibility, data and security boundaries

严格 WORLD_MODEL、显式 DIRECT、ITER-003—006 accepted scope 和 Slice1/2 exact Result 完整回归。early canary 的问题在 Slice3 code freeze 后
由用户披露；披露后产品/Prompt/schema/route/disclosure 变化烧毁输入并保留 Result。Secret/raw hidden/Oracle 不进入产品角色或 Git。

## Open questions and implementation risks

- Slice3 才首次引入独立第二工程；工程 manifest 与 canary 问题集在 Slice3 code freeze 后由用户披露，不能把公开 Alpha 输入冒充 hidden。
- persistence 与恢复可能引入旧包/旧 Review 混用；所有 predecessor/seal identity 必须机械重验。
- 三臂可能证明 World Model 没有独立增益；这是真实架构裁决，不允许移动阈值或隐藏建模成本。

## Acceptance scenarios

1. `V-GENERAL-003`：跨工程、目录、命名、框架和来源组合无特判，答案层级正确。
2. `V-RERETRIEVE-003`：复杂 omission/citation gap/no-progress 多步补证形成新 Ledger/Package/Answer/Review，不回旧上下文。
3. `V-PERSIST-003`：中断、恢复、并发/陈旧 identity 和损坏记录全部正确恢复或失败关闭。
4. `V-CONFLICT-003`：冲突、partial、unknown、duplicate provenance 和 bounded absence/coverage limitation 不混淆。
5. `V-HARDEN-003`：pagination/truncation/oversize/cycle/drift/fuse/旧包审批等完整矩阵闭合。
6. `V-SEC-003` 与 `V-PERF-003`：完整授权/隔离/Secret/loopback/no-retry/资源和预提交时延吞吐 Gate PASS。
7. `V-CANARY-003` 与 `V-NEG-EARLY-003`：新冻结的 5 answerable + 2 boundary 全部正确，重大错误 0，披露后产品变化 0。
8. `V-XD-003` 与 `V-WEB-003`：同一 Web 在 canary 组合 accepted cognition 与多来源 Evidence，Citation 可核对。
9. `V-COMP-EARLY-003`：三臂质量前置门和预提交 World Model 增益 Gate PASS，完整计入建模/更新/存储/Provider 成本与复用周期。
10. `V-DIAG-003`：按层定位首次偏差，不从最终答案猜根因。
11. `V-REGRESSION-003`：accepted scope、三模式、Probe/Alpha 和 full suite 无新增失败。
12. `V-REFLECT-003`：A1—A3 exact Verdict、A4 early verdict、全部 Finding 和用户决定完整。

## Architecture reflection checkpoint

`V-REFLECT-003 PASS` 只表示工程化复盘完整。A1—A3 必须 `SUPPORTED`、A4 early comparison 不得 FAIL，且用户必须给出新的 exact
`CONTINUE`；否则 `REDIRECT/REJECT`，不得进入 Slice4。

## Findings

写入本轮 [Findings](../findings/README.md)，并按[实现发现回写规则](../../../governance/implementation-feedback-policy.md)处置。
