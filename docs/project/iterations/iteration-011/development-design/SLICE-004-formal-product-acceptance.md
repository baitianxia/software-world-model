---
id: ITER-011-SLICE-004
kind: development-slice
status: proposed
authority: proposed-development
owners: [quality, product, project, architecture, engineering]
depends_on: [ITER-011-PROPOSAL, ITER-011-READINESS, ITER-006-RESULT-ACCEPTANCE, ITER-011-SLICE-003]
code: [src/software_world_model/application_services, src/software_world_model/ai_infrastructure, src/software_world_model/interface]
tests: [tests, validation]
iteration: ITER-011
coding_input: false
product_goal_gate: V-000
product_goal_accepted_capability_refs: [ITER-006-RESULT-ACCEPTANCE]
product_goal_cross_domain_case_ids: [V-XD-004]
product_goal_web_checkpoint_id: V-WEB-004
product_goal_live_ad_hoc_checkpoint_id: V-ADHOC-004
product_goal_reflection_gate_case_id: V-REFLECT-004
product_goal_slice_gate_case_ids: [V-HIDDEN-004, V-COMP-004, V-SEC-004, V-XD-004, V-WEB-004, V-ADHOC-004, V-REGRESSION-004, V-010, V-REFLECT-004]
---

# SLICE-004：ENGINEERING_QA 正式产品验收

## Status and dependencies

`PROPOSED / NOT AUTHORIZED / NOT CODING INPUT`。只有 Slice3 exact Result=`PASS + user CONTINUE`、A1—A3 `SUPPORTED`、A4 early Gate 未失败，
并取得该决定之后的新 Slice4 开发/运行授权，才可进入本段。授权时必须增加 exact Slice3 Result dependency。

## Product-goal contribution and cumulative integration

- Product gap shortened：在未参与实现的真实工程和 freeze 后现场题上裁决通用工程问答，而不是公开方向题、内部测试或调用成功。
- User-visible delta：两个最终 held-out Java 工程 10 answerable + 2 boundary，以及两条用户现场题，全部从同一正式 Web 交付。
- Stop signal：任何重大错误/实质遗漏/层级错配/无关 Citation/特判/越权/hidden burn；完整 Cognition 质量或预提交增益失败；用户拒绝。
- Critical assumptions：最终覆盖 A1—A4。
- Reflection：`V-REFLECT-004`；只有全部 Gate PASS 且用户新 `ACCEPT` 才可申请 Iteration Acceptance。

## Direction preview checkpoint

本段引用 Slice1 与 Slice2 的两次方向 `CONTINUE` 以及 Slice3 工程化 `CONTINUE`。早期体验只决定继续，不进入验收分子；本段不再通过
修改产品追逐 hidden 结果。披露后任何产品/Prompt/schema/route/disclosure 变化都烧毁输入并退回新候选。

## Current vs expected behavior

进入本段时产品代码、System fileset、answer hierarchy、Investigation/Package/Review、Provider route/disclosure、Web launcher、performance
和全部回归应已冻结。预期普通用户无需内部代号即可获得直接、层级匹配、证据支持的答案或诚实 Limitation；实现细节仅在问题要求或支撑
结论必要时出现。

## System contracts and invariants

- exact ENGINEERING_QA、严格 WORLD_MODEL、显式 DIRECT 身份与 current System docs 一致，无 silent fallback。
- Question Understanding、typed hierarchy、Application acceptance 与 independent Reviewer 使用同一版本化质量 contract/schema；Reviewer 从
  immutable original question 独立重建 checklist、比较 Application 漏项，且 verdict 独立。
- World Model Cognition、Source evidence、Ledger/Package、Citation 和角色权限/披露 identity 精确绑定；旧 Review 不批准新 Package。
- hidden、三臂、Agent baseline、rubric/cache/value protocol、现场题都绑定 final freeze；任何 request 可能发送后不 retry、不换 Provider。
- Production Activation 始终 `NOT_EXECUTED`。

## Interfaces and affected code

本段只允许 freeze、验证、证据记录和验收文档所需最小变化。若需修改产品、Prompt、schema、Source/Provider disclosure 或 System Contract，
hidden 输入烧毁并退回 Slice3，不得按题修补。

## Compatibility, data and security boundaries

最终 Result 绑定 exact Git commit/tree、System fileset、三种 mode、World Model Read Set、Source revision/allowlist、Provider/model/config/
disclosure、qualification/grant、Hierarchy/Ledger/Package/Review、request、Web session、Citation、安全计数和限制。Secret/raw hidden/Oracle/Agent
输出不进入产品角色或 Git。

## Open questions and implementation risks

- 现场题可能超出当前 Java/static evidence 能力；分类由 freeze 前协议和独立评测裁决，不能事后改分母。
- Provider/network unknown 与产品能力失败必须分开，不允许重试掩盖。
- 完整 Cognition 若无独立价值，即使答案质量合格也不能接受复杂架构；成本必须包含建模、更新、存储和 Provider。

## Acceptance scenarios

1. `V-HIDDEN-004`：两个未见工程 10 answerable + 2 boundary；10/10 supported、2/2 boundary、重大错误 0、披露后产品变化 0。
2. `V-COMP-004`：完整 Cognition、locator-only/empty 同链、成熟源码 Agent 三臂最终复验；质量门与预提交增益 Gate PASS。
3. `V-SEC-004`：Source 只经 Broker/Worker；模型 direct source/FS/Shell/network/credential=0；write/fallback/secret/retry=0；loopback only。
4. `V-XD-004` 与 `V-WEB-004`：同一正式 Web 对最终问题组合 accepted cognition 与多来源 Evidence，Citation 可人工核对。
5. `V-ADHOC-004`：final freeze 后用户现场提出 2 题，至少一题无符号且跨域。
6. `V-REGRESSION-004`：accepted scope、三模式和 Slice1—3 exact Results 无新增失败。
7. `V-010`：Production Activation=`NOT_EXECUTED`。
8. `V-REFLECT-004`：A1—A4 exact Verdict；用户决定 `ACCEPT / REDIRECT / REJECT`。
9. `V-000`：聚合四个唯一 Slice Result，证明用户可见增量与 World Model 独立价值。

## Architecture reflection checkpoint

最终 Result 必须复核四段证据、全部假设、两次早期方向决定、System 边界、hidden/现场题、三臂对照、成本/时延、安全和全部 Finding。
`V-REFLECT-004 PASS` 只表示复盘完整；只有 A1—A4 全部 `SUPPORTED`、全部 Gate PASS 且用户新决定=`ACCEPT` 才能形成 Acceptance。

## Findings

写入本轮 [Findings](../findings/README.md)，并按[实现发现回写规则](../../../governance/implementation-feedback-policy.md)处置。
