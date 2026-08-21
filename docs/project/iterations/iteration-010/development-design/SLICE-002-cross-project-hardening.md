---
id: ITER-010-SLICE-002
kind: development-slice
status: proposed
authority: proposed-development
owners: [engineering, architecture, quality, product]
depends_on: [ITER-010-PROPOSAL, ITER-006-RESULT-ACCEPTANCE, ITER-010-SLICE-001]
code: [src/software_world_model/application_services, src/software_world_model/ai_infrastructure, src/software_world_model/interface]
tests: [tests, validation]
iteration: ITER-010
coding_input: false
product_goal_gate: V-000
product_goal_accepted_capability_refs: [ITER-006-RESULT-ACCEPTANCE]
product_goal_cross_domain_case_ids: [V-XD-002]
product_goal_web_checkpoint_id: V-WEB-002
product_goal_reflection_gate_case_id: V-REFLECT-002
product_goal_slice_gate_case_ids: [V-GENERAL-002, V-RERETRIEVE-002, V-ASYNC-002, V-HARDEN-002, V-SEC-002, V-XD-002, V-WEB-002, V-CANARY-002, V-NEG-EARLY-002, V-COMP-EARLY-002, V-DIAG-002, V-REGRESSION-002, V-REFLECT-002]
---

# SLICE-002：跨工程通用化与自适应调查链夯实

## Status and dependencies

`PROPOSED / NOT AUTHORIZED / NOT CODING INPUT`。只有 Slice1 exact Result 的 Reflection 为 `PASS + CONTINUE`、到期假设全部
`SUPPORTED`，并取得 Slice1 决定之后的新用户开发授权，才可把本文件切换为 current-development。届时 `depends_on` 必须增加 exact
Slice1 Result；当前 Readiness/架构收据不可复用。

## Product-goal contribution and cumulative integration

- Product gap shortened：证明方向体验不是单工程/公开问题错觉，并把认知上下文、自适应调查、Broker、Ledger/Package、独立补证、
  Review、Citation、资格和安全收敛为可跨工程复用的合同。
- Capability path：在同一 `ENGINEERING_QA` Web 加深 `ROADMAP-M-002`，不增加新入口或第二语言。
- Cumulative integration：同一答案组合 ITER-006 prebuilt declaration/`CALLS` 与第二工程的源码、文档、构建配置或测试证据。
- User-visible delta：第二真实工程 early canary 5 answerable + 2 boundary，以及相同 Web 的公开跨类型问题。
- Stop signal：新工程需要特判；World Model 被降级为手册或召回硬门禁；调查不是 prior-result driven；bounded absence/coverage limitation
  混淆；补证/rewrite 不收敛；Agent 质量退步；
  正向价值阈值未达；Source/Provider disclosure、安全或回归失败。
- Critical assumptions：保留并验证 A1—A4；`V-COMP-EARLY-002` 以完整 World Model Cognition、locator-only/empty 同调查链和成熟源码
  Agent 三臂同题消融同时检验 A1/A5。新增消融 protocol、阈值和 digest 当前未获授权，Slice2 编码或执行前必须用新的用户收据冻结。
- Reflection：`V-REFLECT-002`；只有 `CONTINUE` 与新的后续授权才可进入 Slice3。

## Current vs expected behavior

进入本段时，Slice1 应已证明一个工程上的答案方向与基本协议。尚未证明的是不同命名/目录/框架、来源冲突、分页/截断、复杂配置、测试
与代码关系、补检索边界、资格性能和相对成熟源码 Agent 的价值。

预期行为是在第二工程和通用 fixture 上保持同一 World Model Cognition Context、Investigation LLM、Broker/Worker、Evidence Ledger、
调查后 Package、Answer、Review 和 Web 主链；没有按工程、题目、关键词、符号、类名、方法名、fixture 或 Oracle 的 routing。World
Model 提供完整外部系统认知而不是 hint 集合；其覆盖不足不能阻断 Investigation LLM 在授权内提出必要的 exact-revision 读取。

## System contracts and invariants

- 只实现 Slice1 已正式写入 current System docs 的 `ENGINEERING_QA`，发现边界变化先写 Finding 并同步 Owner 文档。
- Source 内容继续按不可信输入处理；任何 prompt/tool/path/provider 指令都不能改变权限和 disclosure。
- Ledger schema 覆盖认知查询、模型提议、Broker decision、源码/文档/配置/测试 Result、origin/revision/coverage/conflict/provenance；只追加，
  不回写历史。Package 只能在本轮调查结束后密封；`support/citation` 仅收 admissible entries，`boundary/audit` 必须保留 Gap、Failure、
  Partial、Conflict、Unknown、拒绝和资源记录且不能支持肯定 Claim；seal 不等于真值。
- `MORE_EVIDENCE_REQUIRED` 必须列出原问题结论清单中的具体可验证缺口，不能携带可执行路径/命令/操作。合法 gap 启动全新上下文的独立
  Verification Investigation：它读取 gap、current Package/Ledger，依据每步结果多步自适应提议，再由 Application/Broker/Worker 逐步
  校验执行，追加新 Ledger Revision、重封新包后 Answer/Review 从新 identity 重做；不回初始 Investigation，不继承 Reviewer 会话。
- Slice2/3 不设永久“一轮补证”上限。每个 exact freeze 必须预密封 Package Revision、model call、Broker operation、source bytes、
  wall-time 和 no-progress 高安全熔断，并证明数值足以容纳正常独立调查；达到熔断失败关闭，answerable 未回答计 FAIL。不得把输出解析修正
  或 Provider retry 伪装成补证。
- 同包表达修复最多一次；新包不是同包 rewrite；任一最终 Draft 必须由对应 exact Package 的独立 Review 批准。
- bounded absence 需要来源查询完整性、授权内容覆盖与业务发现 recall 三层证明；否则是具体 coverage limitation。
- 高质量 Evidence/结论只可异步提议 Knowledge Update，正常 Admission/Publication 失败不影响已交付 Answer，也不取得自动资格。
- Investigation/Answer/Reviewer 都无直接 Source/FS/Shell/network/credential 权限；只有 Broker/Worker 具有受控读能力。
- current Provider/Strategy/role-disclosure 资格按 exact identity 重建；分派后不 retry、不切换 Provider。
- 调用/资源上限只负责失败关闭，不降低 checklist、证据、Citation、Review 或 hidden Case 质量；Slice1 的一次 preview 补证上限不进入
  Slice2 正式协议。

## Interfaces and affected code

允许夯实通用 Investigation/Verification Investigation operation/schema、Broker policy、Ledger/Package 持久恢复、revision/conflict/dedup、
Response Control、role-specific Gateway disclosure、
async persistence proposal、Web developer details、qualification/validation 工具和对应 tests。禁止添加项目 adapter、问题 classifier 路由、
演示答案或 validation-only Web。

## Compatibility, data and security boundaries

严格 WORLD_MODEL、显式 DIRECT、ITER-003—006 accepted scope和 Slice1 exact Result 都必须回归。第二工程和 early hidden 输入只在 Slice2
产品代码 freeze 后披露；披露后任何产品、Prompt、schema、route 或 Provider disclosure 改动烧毁该组证据并保留失败 Result。

Secret 不进 Package/Draft/Review/telemetry。Provider 只能看到 freeze 明确允许的 role/input/fragment，Source 原文最小披露；Answer 和
Reviewer 仍无 repo access。loopback、read-only、no update/write、no silent fallback、zero request retry 不变。

## Open questions and implementation risks

- 文档与源码冲突可能无法自动裁决；正确结果可以是呈现冲突及其版本/来源，而不是强行单一答案。
- 配置继承、generated source、annotation processing 或运行时行为可能超过静态 exact-revision 证据；不能把无法观察写成不存在。
- 三臂消融可能证明完整 Cognition 相对 locator-only/empty 同链没有质量或非 locator 调查成本增益，或不如成熟源码 Agent；这种失败说明
  预构建 World Model 没有抵消混合链复杂度，应 REDIRECT/REJECT，而非改阈值。报告必须计 exact 建模/更新/存储/Provider 成本，并按
  新收据冻结的复用周期摊销，不能只报告提问期 Source bytes。
- early canary 曝光后若发现实现缺口，本组输入立即烧毁，不允许针对题目修补再复用。

## Acceptance scenarios

1. `V-GENERAL-002`：跨不同措辞、目录、框架和来源组合，无任何特判，答案层级与用户目标一致。
2. `V-RERETRIEVE-002`：同包 rewrite 与独立 Verification Investigation 机械区分；新上下文基于 gap + current Package/Ledger 多步自适应，
   新包重封/重审；复杂 conflict/dedup/recovery/no-progress 与不可修复失败关闭闭合。
3. `V-ASYNC-002`：Delivery 不等待知识沉淀；异步 proposal 重新走 Update/Admission/Publication，失败不改写 Answer。
4. `V-HARDEN-002`：持久恢复、pagination、truncation、conflict、dedup、oversize、cycle/no-progress、六类高安全熔断、revision drift、
   Ledger/Package provenance 全部闭合；answerable 熔断耗尽计 FAIL。
5. `V-SEC-002`：Source injection、symlink/path/write/network/secret/disclosure/role escape、outcome unknown 全部失败关闭。
6. `V-CANARY-002` 与 `V-NEG-EARLY-002`：第二工程 5 answerable + 2 boundary 全部正确，bounded absence 与 coverage limitation 不混淆。
7. `V-XD-002` 与 `V-WEB-002`：同一 Web 在第二工程组合 accepted Snapshot 与新来源 Evidence。
8. `V-COMP-EARLY-002`：三臂固定 same revision/model/questions/budget/cache/rubric。完整认知与成熟 Agent 先满足零重大错误、boundary 正确
   且完整认知逐结论不退步；locator control 的失败不得降低此门。随后完整认知相对 locator-only/empty 同链达到新收据预提交的质量或
   normalized non-locator cost 增益；报告包含建模成本和冻结复用周期，且可重放。
9. `V-DIAG-002`：按 Source observation → World Model Cognition → Question Understanding → Investigation → Broker/Worker → Ledger/Package →
   Draft → Review → Web 定位首次偏差。
10. `V-REGRESSION-002`：accepted scope、严格 WORLD_MODEL、显式 DIRECT 和 Slice1 主线无退步。
11. `V-REFLECT-002`：A1—A4 exact Verdict、A5 early verdict、全部 Finding 与用户新决定完整。

## Architecture reflection checkpoint

Result 必须复核两个工程、early canary、三臂认知消融、正向价值、安全、建模与提问成本/时延、复用周期、Source exposure、模式复杂度、
知识沉淀边界与全部 Finding。`V-REFLECT-002 PASS` 不等于接受；A1—A4 必须 `SUPPORTED`，A5 early comparison 不得 FAIL，用户须给出新的
`CONTINUE`，否则 `REDIRECT/REJECT`。

## Findings

按 [Findings](../findings/README.md) 和[实现发现回写规则](../../../governance/implementation-feedback-policy.md)处置。任何 Source、模式、
Package、Review、Provider disclosure 或知识沉淀边界变化必须同步 owning System 文档。
