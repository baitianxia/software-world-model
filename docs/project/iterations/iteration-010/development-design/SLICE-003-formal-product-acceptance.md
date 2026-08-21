---
id: ITER-010-SLICE-003
kind: development-slice
status: proposed
authority: proposed-development
owners: [quality, product, project, architecture, engineering]
depends_on: [ITER-010-PROPOSAL, ITER-006-RESULT-ACCEPTANCE, ITER-010-SLICE-002]
code: [src/software_world_model/application_services, src/software_world_model/ai_infrastructure, src/software_world_model/interface]
tests: [tests, validation]
iteration: ITER-010
coding_input: false
product_goal_gate: V-000
product_goal_accepted_capability_refs: [ITER-006-RESULT-ACCEPTANCE]
product_goal_cross_domain_case_ids: [V-XD-003]
product_goal_web_checkpoint_id: V-WEB-003
product_goal_live_ad_hoc_checkpoint_id: V-ADHOC-001
product_goal_reflection_gate_case_id: V-REFLECT-003
product_goal_slice_gate_case_ids: [V-HIDDEN-003, V-COMP-001, V-SEC-003, V-XD-003, V-WEB-003, V-ADHOC-001, V-REGRESSION-003, V-010, V-REFLECT-003]
---

# SLICE-003：ENGINEERING_QA 正式产品验收

## Status and dependencies

`PROPOSED / NOT AUTHORIZED / NOT CODING INPUT`。只有 Slice2 exact Result 为 `PASS + CONTINUE`、A1—A4 均 `SUPPORTED`、A5 early Gate
未失败，并取得该决定之后的新用户开发/运行授权，才可进入本段。授权时必须增加 Slice2 exact Result dependency。

## Product-goal contribution and cumulative integration

- Product gap shortened：在未参与实现的工程与现场自由问题上证明通用工程问答，而不是公开体验或内部测试成功。
- Capability path：正式裁决 `ROADMAP-M-002` 这一实现路线是否推进 MVP。
- Cumulative integration：final `V-XD-003` 同一问题/答案组合 ITER-006 accepted Snapshot 知识与本轮源码、文档、配置或测试 Evidence。
- User-visible delta：两个隐藏真实 Java 工程 10 answerable + 2 boundary，加两条 product freeze 后现场题。
- Stop signal：任何重大错误、实质遗漏、层级错误、无关 Citation、特判、越权 Source、静默 mode fallback、hidden burn、Agent 退步、价值
  阈值未达或用户 REDIRECT/REJECT。
- Critical assumptions：按冻结顺序最终验证 A1—A5。
- Reflection：`V-REFLECT-003`；只有所有产品 Gate PASS、A1—A5 `SUPPORTED` 和用户新 `ACCEPT` 才能形成 Acceptance。

## Current vs expected behavior

进入本段时产品代码、System fileset、Strategy/Prompt/schema、Provider route/disclosure、Web launcher 和全部回归应已冻结。预期是用户无需了解
模式和内部代号，在同一 loopback Web 自由提问并得到直接、层级匹配、证据支持的答案或诚实 limitation；代码细节仅在问题要求或支撑
结论必要时出现。

本段不通过修改产品来追逐 hidden 结果。披露后任何产品变化都会烧毁输入，退回新候选和新评测，不允许临场修补。

## System contracts and invariants

- exact `ENGINEERING_QA`、严格 `WORLD_MODEL` 和显式 `DIRECT_INVESTIGATION` 身份与 current System docs 一致，无 silent fallback。
- 原问题 checklist 与 Snapshot hints 共同驱动检索；World Model 不是 Source recall Gate，Source 是不可信输入。
- retrieval worker 只读 exact revision/allowlist，操作全审计；Answer/Reviewer repo/source access=0。
- Package 是事实权威；每个重要结论有结论级 Citation；unknown/limitation 不扩张 absence/coverage。
- 同包最多一次 rewrite；只在具体 evidence gap 后最多一次补检索/重封；任何变化后独立 Review。
- 质量不会因调用预算删减；高安全资源上限只触发失败关闭。
- hidden suite、Agent baseline、rubric、cache、value protocol、Provider disclosure 和用户现场题都绑定 exact freeze。
- Production Activation 始终 `NOT_EXECUTED`。

## Interfaces and affected code

本段只允许 freeze、验证、证据记录和验收文档所需的最小变化。若需修改产品、Prompt、schema、Provider/configuration、retrieval operation、
System Contract 或安全边界，hidden evidence 烧毁并退回 Slice2 重新候选，不得在本段按题修补。

## Compatibility, data and security boundaries

最终 Result 绑定 exact Git commit/tree、System fileset、mode/Strategy/Prompt/schema、World Model Read Set、authorized source revision/allowlist、
Provider/model/config/disclosure、qualification/grant、Evidence Package/Review、每次 request、Web session、Citation、安全计数和全部限制。

Secret、raw hidden suite、Oracle、成熟 Agent 输出和未授权源码不进入产品角色。评测 Source 片段只能按 freeze 发给 exact Provider role，
不得扩大 disclosure。

## Open questions and implementation risks

- 现场题可能超出 Java/static evidence 能力；诚实 limitation 是合法结果，但 answerable/boundary 分类由独立评测裁决，不能事后改分母。
- Provider/network unknown 与产品能力失败必须分开；任何 request 可能发送后不 retry、不切换 Provider。
- 若质量持平但 World Model reuse 正向价值未达，复杂混合方案不能接受。

## Acceptance scenarios

1. `V-HIDDEN-003`：两个未见工程 10 answerable + 2 boundary；answerable 10/10 supported、boundary 2/2、重大错误 0。
2. `V-COMP-001`：逐结论不低于成熟源码 Agent，且 12 题复用周期的 World Model live-source exposure ratio 不高于 250000 ppm。
3. `V-SEC-003`：source read 只在 retrieval worker；Answer/Reviewer source=0；Update/write/silent fallback/secret/hidden retry=0；loopback only。
4. `V-XD-003` 与 `V-WEB-003`：同一正式 Web 对最终问题组合 accepted Snapshot 与本轮多来源 Evidence，Citation 可人工核对。
5. `V-ADHOC-001`：用户冻结后现场提出两题，至少一题无符号并执行跨域组合。
6. `V-REGRESSION-003`：accepted scope、严格 WORLD_MODEL、显式 DIRECT、Slice1/2 ENGINEERING_QA 和完整回归无新增失败。
7. `V-010`：Production Activation 为 `NOT_EXECUTED`。
8. `V-REFLECT-003`：A1—A5 exact Verdict；用户决定 `ACCEPT / REDIRECT / REJECT`。
9. `V-000`：聚合三个唯一 Slice Result，证明用户可见的通用工程问答增量，而非测试、调用或页面启动成功。

## Architecture reflection checkpoint

最终 Result 必须复核三段证据、全部假设、System 边界、隐藏/现场题、Agent 对照、World Model 复用价值、Source disclosure、时延/成本、安全、
用户体验和全部 Finding。`V-REFLECT-003 PASS` 只表示复盘完整；只有 A1—A5 全部 `SUPPORTED`、全部 Case PASS 且用户新决定为
`ACCEPT`，才能形成 Iteration Acceptance。

## Findings

链接 [Findings](../findings/README.md) 与[实现发现回写规则](../../../governance/implementation-feedback-policy.md)。本 Slice 当前不是编码输入。
