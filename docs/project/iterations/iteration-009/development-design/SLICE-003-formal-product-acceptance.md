---
id: ITER-009-SLICE-003
kind: development-slice
status: proposed
authority: proposed-development
owners: [engineering, architecture, quality, product]
depends_on: [ITER-009-PROPOSAL, ITER-009-READINESS, ITER-009-SLICE-001, ITER-009-SLICE-002, ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-ACCEPTANCE]
code: [src/software_world_model/application_services, src/software_world_model/knowledge_engine, src/software_world_model/ai_infrastructure, src/software_world_model/interface]
tests: [tests, validation]
iteration: ITER-009
coding_input: false
product_goal_gate: V-000
product_goal_accepted_capability_refs: [ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-ACCEPTANCE]
product_goal_cross_domain_case_ids: [V-XD-003]
product_goal_web_checkpoint_id: V-WEB-003
product_goal_live_ad_hoc_checkpoint_id: V-ADHOC-001
product_goal_reflection_gate_case_id: V-REFLECT-003
product_goal_slice_gate_case_ids: [V-HIDDEN-003, V-COMP-001, V-SEC-003, V-XD-003, V-WEB-003, V-ADHOC-001, V-REGRESSION-003, V-009, V-REFLECT-003]
---

# SLICE-003：隐藏评测与正式验收

## Status and dependencies

`PROPOSED / NOT AUTHORIZED / NOT EXECUTED`。`SLICE-001` 已决定 `REDIRECT`，`SLICE-002` 从未授权，因此本 Slice 的进入条件没有成立，
且在已拒绝的 ITER-009 中不可再授权。隐藏评测、正式 Acceptance 与 Production Activation 均未执行。

## Product-goal contribution and cumulative integration

- Product gap shortened：用未参与实现的工程、现场题和成熟源码 Agent 对照验证本机 Web 是否真正具备可接受的通用证据问答能力。
- Product capability-path step advanced：为 `ROADMAP-M-002` Step 1 形成接受、转向或拒绝的最终产品裁决。
- Existing capabilities combined：accepted Workspace/Update/Snapshot/Web/Citation/declaration/`CALLS` 与前两段重新验收的证据、答案、审核、
  rewrite 和 Limitation 主线。
- User-visible Web questions at slice end：两个隐藏工程的 4 answerable + 2 boundary、至少一个无符号跨域问题和两条用户现场题。
- Slice stop / redirect signal：任何重大错误、answerable Gap、boundary 编造、Citation 不支持结论、Agent 实质更完整、价值阈值未达、
  fallback、安全失败、产品冻结后修改或用户非 `ACCEPT`。
- Critical assumptions tested：最终按冻结顺序复核 A1—A5。
- Reflection gate and success decision：`V-REFLECT-003`；只有用户新的 `ACCEPT` 收据才可申请 Iteration Acceptance。

## Direction preview checkpoint

本段不是方向体验。它必须引用前两段 exact `CONTINUE` Result，并在同一 Web 入口进行正式验证；方向体验的公开题和 Slice2 early canary
不得复用为最终隐藏输入。

## Current vs expected behavior

进入本段时产品代码、配置、System Contract、qualification、两个最终工程披露协议、成熟源码 Agent protocol/rubric/cache policy 和
价值指标全部冻结。本段原则上不开发新功能；发现产品缺陷时保持失败并烧毁受影响 hidden 输入，返回前一阶段形成新候选，不能在看到题目
后修补再继续使用同一套验收题。

## System contracts and invariants

- 最终工程、源码和问题在 product code freeze 前对实现方不可见；披露后产品变化为 0。
- 成熟源码 Agent 先按同 revision、同问题、等价资源和冻结 cache policy 运行并密封，再运行 World Model Web。
- 逐 Need/Claim 裁决、重大错误、争议、同分、失败与价值计算使用预提交 protocol，不事后更换。
- 正式 Web 与前两段是同一 product-owned chain；CLI、validation launcher 或静态回放不能替代。
- 提问期 Source、Update、Direct fallback 为 0；独立 Review、真实 Citation、零隐藏 retry 与失败关闭保持。
- Production Activation 为 `NOT_EXECUTED`，本机 Acceptance 不自动授权生产。

## Interfaces and affected code

本段只允许冻结、验证、证据记录和验收文档所需的最小变化。若必须改产品代码、Prompt、Schema、Adapter、Provider config 或安全边界，
本轮 hidden evidence 烧毁并退回 `SLICE-002` 重新形成候选，不得在本段针对题目修补。

## Compatibility, data and security boundaries

最终 Result 必须绑定 exact Git commit/tree、System Contract fileset、Strategy/Adapter/model/configuration、Snapshot/Bundle、授权、运行 ID、
每次 request、Web session、Citation、安全计数和全部限制。Secret、raw hidden suite、Oracle 答案和未授权源码不得进入产品 Answer worker。

## Open questions and implementation risks

- 用户现场问题不可预先知道，可能揭示新知识表示范围；该结果应诚实决定 redirect，而不是临场扩大 scope。
- 网络或 Provider outcome unknown 与能力失败必须分开；禁止同请求 retry 或看到失败后切换 Provider。
- 质量持平但预提交正向价值阈值未达，不能接受复杂度更高的方案。

## Acceptance scenarios

1. `V-HIDDEN-003`：两个未见真实 Java 工程、4 answerable + 2 boundary；answerable 4/4 supported、boundary 2/2 正确、重大错误 0。
2. `V-COMP-001`：逐 Need/Claim 不低于成熟源码 Agent，且 Source exposure ratio 在 12 题复用周期内不高于 250000 ppm。
3. `V-SEC-003`：Source/Update/Direct fallback=0，Secret/授权/Reviewer/zero retry/loopback 全部 PASS。
4. `V-XD-003` 与 `V-WEB-003`：正式 Web 执行旧+新能力组合，答案或 Limitation 与 Citation 可人工核对。
5. `V-ADHOC-001`：用户现场提出两条问题，至少一条无符号且执行跨域组合。
6. `V-REGRESSION-003`：accepted 能力、前两段产品链和完整回归无新增失败。
7. `V-009`：Production Activation 明确为 `NOT_EXECUTED`。
8. `V-REFLECT-003`：A1—A5 全部有 exact Verdict；用户作出 `ACCEPT / REDIRECT / REJECT`。
9. `V-000`：聚合全部唯一 Slice Result，证明用户可见的通用源码问答增量，而非只报告测试或模型调用成功。

## Architecture reflection checkpoint

最终 Result 必须复核三段证据、全部关键假设、复杂度与收益、成熟方案差距、成本/时延、安全、用户现场反馈和全部 Finding。
`V-REFLECT-003 PASS` 只表示复盘完整；只有 A1—A5 全部 `SUPPORTED`、全部 blocking Case PASS 且用户新决定为 `ACCEPT`，才能形成
Iteration Acceptance。否则保留 `REDIRECT/REJECT` 证据。

## Findings

链接 [Findings](../findings/README.md) 与[实现发现回写规则](../../../governance/implementation-feedback-policy.md)。本 Slice 当前不是编码输入。
