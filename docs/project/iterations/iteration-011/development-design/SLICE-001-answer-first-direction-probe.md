---
id: ITER-011-SLICE-001
kind: development-slice
status: proposed
authority: proposed-development
owners: [engineering, product, architecture, quality]
depends_on: [ITER-011-PROPOSAL, ITER-011-READINESS, ITER-006-RESULT-ACCEPTANCE, ITER-010-RESULT-SLICE-001-STOP-REDIRECT]
code: [src/software_world_model/application_services, src/software_world_model/ai_infrastructure, src/software_world_model/interface]
tests: [tests]
iteration: ITER-011
coding_input: false
product_goal_gate: V-000
product_goal_accepted_capability_refs: [ITER-006-RESULT-ACCEPTANCE]
product_goal_cross_domain_case_ids: [V-XD-001]
product_goal_web_checkpoint_id: V-WEB-001
product_goal_direction_preview_checkpoint_id: V-PREVIEW-001
product_goal_live_ad_hoc_checkpoint_id: V-ADHOC-001
product_goal_reflection_gate_case_id: V-REFLECT-001
product_goal_slice_gate_case_ids: [V-BASELINE-001, V-ARCH-001, V-HIERARCHY-001, V-REVIEW-001, V-SEC-001, V-XD-001, V-WEB-001, V-ADHOC-001, V-PREVIEW-001, V-REFLECT-001]
---

# SLICE-001：答案优先方向探针

## Status and dependencies

`PROPOSED / NOT AUTHORIZED / NOT CODING INPUT`。本文件只有在 Proposal/Readiness 由新用户收据接受、Manifest 将本 Slice 切换为
`authorized / coding_input=true` 且 `project/current.md` 精确指向后才可开发。规划收据 `7711b359…` 不能替代该授权。

## Product-goal contribution and cumulative integration

- Product gap shortened：把 ITER-010 的自由文本层级与扁平 Claim 改成统一 typed answer hierarchy，并让 Application 与独立 Reviewer
  能机械核对“先回答用户目标、实现按需、重大结论完整且有据”。
- Existing capabilities combined：复用 World Model Cognition、受控自适应调查、Broker/Worker、Ledger/Package、Citation 和同一产品 Web。
- User-visible delta：代码冻结后，先在同一产品 Web 跑 1 条代表题，再由用户现场提出 1 题。
- Stop signal：任一回答继续被类/方法/调用顺序主导；用户可见影响遗漏仍被批准；需要题目/工程/关键词/符号特判；Citation 或安全失败。
- Critical assumption：到期 A1；A2—A4 只记录 early signal。
- Reflection：`V-REFLECT-001`；只有用户新 `CONTINUE` 才可申请 Slice2，PASS 本身不授权后续。

## Direction preview checkpoint

真实入口必须是与最终产品相同的 loopback `ENGINEERING_QA` Web，不是 fixture、CLI、回放或 validation-only 页面。最少执行：

1. 一条可同时使用 World Model Cognition 与 query-time Source Evidence 的代表题；
2. 产品 freeze 后由用户现场提出的一条自然问题。

页面明确标记“方向探针 / 非验收 / 非生产”，展示直接答案或诚实 Limitation、可打开 Citation 和折叠诊断。用户查看实际答案后独立给出
`CONTINUE / REDIRECT / REJECT`。在展示给用户前，独立评测方先对正确性、完整性、Citation、边界与是否特判作出明确裁决；用户不承担
代码事实审核。持久恢复、复杂补证、conflict/dedup、完整性能安全、full regression、hidden、三臂 comparison 不属于
本 Slice 阻断项。

## Current vs expected behavior

当前 ITER-010 可以形成有证据的正文，但答案结构和 Reviewer 不能阻断层级错配。预期本 Slice 只完成最小通用闭环：Question
Understanding 形成 material conclusion checklist 和回答层级；typed Answer Plan 始终先给直接结论，并只在问题或证据实际需要时加入用户可见
流程/影响、实现解释或限制；每个肯定的实质结论绑定 Citation。Answer 前，Application 校验问题理解、Answer Plan 义务和证据可满足性；
Draft 后、Reviewer 前，Application 再机械校验层级字段与 claim-Citation binding；独立 Reviewer 在新上下文按同一版本化质量
contract/schema 从 immutable original question 重建自己的 checklist，先比较两份 checklist 的遗漏，再审答案与证据。

## System contracts and invariants

- 先由 owning System docs 表达 answer hierarchy、Application acceptance 与 Reviewer independence；`V-ARCH-001` 未通过不得编码。
- hierarchy 表达通用职责，不固定标题、字数比例、题型或代码元素；禁止工程/问题/关键词/符号/类/方法/fixture/Oracle 路由。
- Reviewer 与 Application 只共用冻结的质量 contract/schema，不共用 checklist 结论；Reviewer 从原问题独立重建、比较遗漏，且不共享
  会话、Draft 生成状态或 verdict。
- exact revision、Source untrusted、Broker/Worker read-only、Ledger/Package identity、support/citation 与 boundary/audit 分区、Secret 隔离、
  no retry/provider switch、loopback 和失败关闭保持。
- 调用上限不能删除 checklist、Citation 或独立审核；超限按真实失败交付 Limitation 或 fail closed。

## Interfaces and affected code

允许最小修改 Question Understanding/Answer Plan/Answer/Review schema、Application acceptance、对应 Strategy/Model Source、产品 Web 展示及 focused
tests。禁止为探针题新增关键词、工程、符号或答案特例；禁止顺便实现 Slice3 persistence/hardening。

## Compatibility, data and security boundaries

严格 `WORLD_MODEL`、显式 `DIRECT_INVESTIGATION` 和 ITER-006 accepted scope 保持。所有 live 前另行冻结 exact product commit/tree、System
fileset、Provider/model/configuration、credential reference、每个角色完整输入、Source fragments 和一次性授权；ITER-010 grant 不复用。

## Open questions and implementation risks

- typed hierarchy 可能被误做成格式模板；验证关注语义职责和结论顺序，不按固定措辞/段落数评分。
- 一题代表题可能偶然成功；因此 Slice1 只判探针方向，Slice2 才以跨维度 Alpha 再判向。
- 现场题可能是 boundary；用户与独立审核按 freeze 前的 answerable/boundary 规则裁决，不事后改分母。

## Acceptance scenarios

1. `V-BASELINE-001`：exact predecessor/product subject、工作树变化和 ITER-010 rejected 结论分离。
2. `V-ARCH-001`：System Owner 与本 Slice hierarchy/review contract 一致。
3. `V-HIERARCHY-001`：只用代表题所需的最小正例、层级错配反例和改述反例，证明 typed plan 能先给直接答案且不靠特判；跨维度覆盖留给 Slice2。
4. `V-REVIEW-001`：Reviewer 从原问题独立重建 checklist 并先发现 Application checklist 漏项，再阻断层级错配、重大遗漏、无据 Claim
   和错误 Citation；合法答案可批准；裁决上下文独立。
5. `V-SEC-001`：exact/read-only/untrusted/Secret/disclosure/loopback/no-retry 最小真实边界成立。
6. `V-XD-001` 与 `V-WEB-001`：代表题在同一真实 Web、同一答案组合 Cognition 与 Source Evidence，Citation 可打开。
7. `V-ADHOC-001`：用户从同一 freeze 后 Web 现场提 1 题，系统交付可核对答案或诚实 Limitation。
8. `V-PREVIEW-001`：用户根据两个实际答案给出独立方向决定。
9. `V-REFLECT-001`：A1 exact Verdict、A2—A4 early signal、Findings、成本/调用和用户决定完整。

## Architecture reflection checkpoint

Slice Result 必须逐层定位 Source → Cognition → Question Understanding → Answer Hierarchy → Investigation → Package → Draft → Application
Acceptance → Review → Web 的首次偏差。`V-REFLECT-001 PASS` 不表示方向成功；只有用户 exact `CONTINUE` 收据才允许申请 Slice2，
`REDIRECT/REJECT` 立即停止本路线。

## Findings

写入本轮 [Findings](../findings/README.md)，并按[实现发现回写规则](../../../governance/implementation-feedback-policy.md)处置。
