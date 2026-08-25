---
id: ITER-010-SLICE-003
kind: development-slice
status: proposed
authority: proposed-development
owners: [quality, product, project, architecture, engineering]
depends_on: [ITER-010-PROPOSAL, ITER-010-PDR-004, ITER-006-RESULT-ACCEPTANCE, ITER-010-SLICE-002, SYS-ADR-018, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
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

# SLICE-003：多轮工程 Chat 正式产品验收

## Status and dependencies

`PROPOSED / NOT AUTHORIZED / NOT CODING INPUT`。只有 Slice2 exact Result 为 `PASS + CONTINUE`、A1—A4/A6 均 `SUPPORTED`、A5 early Gate
未失败，并取得该决定之后的新用户开发/运行授权，才可进入本段。授权时必须增加 Slice2 exact Result dependency。

## Product-goal contribution and cumulative integration

- Product gap shortened：在未参与实现的工程与现场自由问题上证明通用工程问答，而不是公开体验或内部测试成功。
- Capability path：正式裁决 `ROADMAP-M-002` 这一实现路线是否推进 MVP。
- Cumulative integration：final `V-XD-003` 同一问题/答案组合 ITER-006 accepted Snapshot 知识与本轮源码、文档、配置或测试 Evidence。
- User-visible delta：两个隐藏真实 Java 工程的多轮 Conversation，包括 answerable/boundary Turn，加 product freeze 后现场对话。
- Stop signal：任何重大错误、实质遗漏、层级错误、无关 Citation、特判、越权 Source、静默 mode fallback、hidden burn、完整认知低于
  成熟 Agent、相对 locator-only/empty 同链没有预提交增益、建模成本遗漏或用户 REDIRECT/REJECT。
- Critical assumptions：按冻结顺序最终验证 A1—A6。
- Reflection：`V-REFLECT-003`；只有所有产品 Gate PASS、A1—A6 `SUPPORTED` 和用户新 `ACCEPT` 才能形成 Acceptance。

## Current vs expected behavior

进入本段时产品代码、System fileset、Strategy/Prompt/schema、Provider route/disclosure、Web launcher 和全部回归应已冻结。预期是用户无需了解
模式和内部代号，在同一 loopback Web 追问、纠正、澄清、深入和总结，并逐轮得到直接、层级匹配、证据支持的答案或诚实 limitation；
代码细节仅在问题要求或支撑结论必要时出现，新对话不继承旧 Context。

本段不通过修改产品来追逐 hidden 结果。披露后任何产品变化都会烧毁输入，退回新候选和新评测，不允许临场修补。

## System contracts and invariants

- ADR-018/Engineering Conversation 的主工程 Agent 多轮 Chat、严格 `WORLD_MODEL` 和显式 `DIRECT_INVESTIGATION` 身份与 current System docs 一致，无 silent fallback。
  旧 `@3`、固定 Investigation/Verification Investigation 角色与双 Review 只作历史/兼容资产，不是 current 验收拓扑。
- World Model 是 exact、持久、版本化的软件外部认知，不是手册或 Source recall Gate；Source 是不可信输入。
- 主 Agent 持续维护 Conversation 目标、假设、子任务和计划，依据 World Model Cognition、relevant sealed Conversation Context 和 prior tool observations 选择受控工具、解释结果并重规划；
  Broker/Worker 只读 exact revision/allowlist 并全审计；主 Agent/Reviewer 直接 repo/source/FS/Shell/network/credential/write access=0。
- Ledger 只追加并在调查结束后 seal Package；Package 的 `support/citation` 仅含 admissible entries，`boundary/audit` 强制保留 gap/failure/
  partial/conflict/unknown 且不能支持肯定 Claim；seal 不等于真值，每个重要肯定结论有 Citation。
- fresh independent Reviewer 只返回具体可验证 Finding；Finding 回主 Agent，由主 Agent 基于 current Context/Work State/Package/Ledger 决定重写或选择新的受控工具补证，
  并形成后继 Ledger/Package/Answer/fresh Review identity。质量不由固定 rewrite/补证次数配额裁剪。
- 质量不会因调用预算删减；正式协议不固定“一轮补证”，exact freeze 预密封 Package revision/model call/Broker operation/source bytes/
  wall-time/no-progress 高安全熔断。answerable 因熔断耗尽未回答计 FAIL。
- hidden suite、三臂、external baseline、rubric、cache、value protocol、Provider disclosure 和现场 Conversation 都绑定 exact freeze。
  产品外部比较中 current Codex 保留其真实客户端/model/reasoning/tools/权限，不是 Oracle/裁判；World Model 因果消融的 source-only 与 full-cognition + source 两系统臂才共享同一主 Agent/model/tool/budget/cache/Reviewer。新增协议必须引用 Slice2 前新收据。
- Production Activation 始终 `NOT_EXECUTED`。

## Interfaces and affected code

本段只允许 freeze、验证、证据记录和验收文档所需的最小变化。若需修改产品、Prompt、schema、Provider/configuration、retrieval operation、
System Contract 或安全边界，hidden evidence 烧毁并退回 Slice2 重新候选，不得在本段按题修补。

## Compatibility, data and security boundaries

最终 Result 绑定 exact Git commit/tree、System fileset、mode/Strategy/Prompt/schema、World Model Read Set、authorized source revision/allowlist、
Provider/model/config/disclosure、qualification/grant、Cognition Context、Ledger/Package/Review、每次 request、Web session、Citation、安全计数和
全部限制。

Secret、raw hidden suite、Oracle、成熟 Agent 输出和未授权源码不进入产品角色。评测 Source 片段只能按 freeze 发给 exact Provider role，
不得扩大 disclosure。

## Open questions and implementation risks

- 现场题可能超出 Java/static evidence 能力；诚实 limitation 是合法结果，但 answerable/boundary 分类由独立评测裁决，不能事后改分母。
- Provider/network unknown 与产品能力失败必须分开；同 Provider request 可能发送后不 retry。跨 Provider 只允许 ADR-017 预授权的同
  logical Turn 独立全链 fallback attempt，从 original Turn、relevant sealed Conversation Context 和 exact Cognition 重跑。
- 若完整认知通过质量门但相对 locator-only/empty 同链既没有预提交质量增益，也没有预提交非 locator 调查成本增益，复杂混合方案不能
  接受。World Model 的建模、更新、存储与 Provider 成本必须按冻结复用周期摊入报告。

## Acceptance scenarios

1. `V-HIDDEN-003`：两个未见工程 10 answerable + 2 boundary；answerable 10/10 supported、boundary 2/2、重大错误 0。
2. `V-COMP-001`（PDR-004 pre-execution revision，旧定义无执行证据）：同一 exact revision/多轮 Conversation 脚本/可比较输出/rubric 下，current Codex 保留实际客户端/model/reasoning/tools/权限作强外部基线；
   source-only 与 full-cognition + source 两系统臂共享同一主 Agent/model/tool/budget/cache/Reviewer。full-cognition 先过零重大错误、对话连续性和 boundary 质量门，再证明相对 source-only 的预提交质量或 normalized non-locator cost 增益；Codex 不是 Oracle/裁判。报告计入
   World Model 建模/更新/存储/Provider 成本与冻结复用周期；旧 source-exposure 指标只作为历史输入，不代替新消融 Gate。
3. `V-SEC-003`：source read 只经 Broker/Worker；主 Agent/Reviewer direct source/FS/Shell/network/credential/write=0；Update/write/silent
   unauthorized/silent-mode fallback、secret exposure、same-Provider hidden retry=0；ADR-017 fallback attempt 完整隔离；loopback only。
4. `V-XD-003` 与 `V-WEB-003`：同一正式 Web 对最终问题组合 accepted Snapshot 与本轮多来源 Evidence，Citation 可人工核对。
5. `V-ADHOC-001`：用户冻结后现场提出两题，至少一题无符号并执行跨域组合。
6. `V-REGRESSION-003`：accepted scope、严格 WORLD_MODEL、显式 DIRECT、Slice1/2 ENGINEERING_QA 和完整回归无新增失败。
7. `V-010`：Production Activation 为 `NOT_EXECUTED`。
8. `V-REFLECT-003`：A1—A6 exact Verdict；用户决定 `ACCEPT / REDIRECT / REJECT`。
9. `V-000`：聚合三个唯一 Slice Result，证明用户可见的通用工程问答增量，而非测试、调用或页面启动成功。

## Architecture reflection checkpoint

最终 Result 必须复核三段证据、全部假设、System 边界、隐藏/现场题、三臂认知消融、World Model 建模成本与复用价值、Source disclosure、时延/成本、安全、
用户体验和全部 Finding。`V-REFLECT-003 PASS` 只表示复盘完整；只有 A1—A6 全部 `SUPPORTED`、全部 Case PASS 且用户新决定为
`ACCEPT`，才能形成 Iteration Acceptance。

## Findings

链接 [Findings](../findings/README.md) 与[实现发现回写规则](../../../governance/implementation-feedback-policy.md)。本 Slice 当前不是编码输入。
