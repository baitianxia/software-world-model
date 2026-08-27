---
id: ITER-010-SLICE-002
kind: development-slice
status: proposed
authority: proposed-development
owners: [engineering, architecture, quality, product]
depends_on: [ITER-010-PROPOSAL, ITER-010-PDR-004, ITER-006-RESULT-ACCEPTANCE, ITER-010-SLICE-001, SYS-ADR-018, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
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

# SLICE-002：跨工程多轮 Chat 与主工程 Agent 夯实

## Status and dependencies

`PROPOSED / NOT AUTHORIZED / NOT CODING INPUT`。只有 Slice1 四路方向 Gate 与最小 Web Chat exact Result 为 `PASS + CONTINUE`、A1—A3/A6
`SUPPORTED`，并取得 Slice1 决定之后的新用户开发授权，才可把本文件切换为 current-development。届时 `depends_on` 必须增加 exact
Slice1 Result；当前 Readiness/架构收据不可复用。

## Product-goal contribution and cumulative integration

- Product gap shortened：证明主 Agent 的多轮目标/Context/重规划不是单工程错觉，并把 World Model cognition、Conversation/Turn、
  Broker、逐轮 Ledger/Package、Review、Citation、资格和安全收敛为可跨工程复用的合同。
- Capability path：在同一 `ENGINEERING_QA` Web 加深 `ROADMAP-M-002`，不增加新入口或第二语言。
- Cumulative integration：同一答案组合 ITER-006 prebuilt declaration/`CALLS` 与第二工程的源码、文档、构建配置或测试证据。
- User-visible delta：第二真实工程 early canary 5 answerable + 2 boundary，以及相同 Web 的公开跨类型问题。
- Stop signal：新工程需要特判；World Model 被降级为手册或召回硬门禁；调查不是 prior-result driven；bounded absence/coverage limitation
  混淆；补证/rewrite 不收敛；Agent 质量退步；
  正向价值阈值未达；Source/Provider disclosure、安全或回归失败。
- Critical assumptions：保留并验证 A1—A6；`V-COMP-EARLY-002` 在第二工程以同一四路协议复验 direct relevant evidence、same-agent
  source-only、same-agent full World Model cognition + source 与 current Codex。新输入、阈值和 digest 当前未冻结或获授权。
- Reflection：`V-REFLECT-002`；只有 `CONTINUE` 与新的后续授权才可进入 Slice3。

## Current vs expected behavior

进入本段时，Slice1 应已证明一个工程上的答案方向与基本协议。尚未证明的是不同命名/目录/框架、来源冲突、分页/截断、复杂配置、测试
与代码关系、补检索边界、资格性能和相对成熟源码 Agent 的价值。

预期行为是在第二工程和通用 fixture 上保持同一主 Agent、Conversation/Turn/Context、World Model Cognition、Broker/Worker、逐轮
Evidence Ledger/Package、Answer、Review 和 Web 主链；没有按工程、题目、关键词、符号、类名、方法名、fixture 或 Oracle 的 routing。World
Model 提供完整外部系统认知而不是 hint 集合；其覆盖不足不能阻断主工程 Agent 在授权内选择必要的 exact-revision 受控读取工具。

## System contracts and invariants

- 只实现 Slice1 已正式写入 ADR-018 和 Engineering Conversation Contract 的主工程 Agent 多轮 Chat；旧 `@3`、固定 Investigation/Verification Investigation 角色、双 Review 只作历史/兼容资产。发现边界变化先写 Finding 并同步 Owner 文档。
- Source 内容继续按不可信输入处理；任何 prompt/tool/path/provider 指令都不能改变权限和 disclosure。
- Ledger schema 覆盖认知查询、模型提议、Broker decision、源码/文档/配置/测试 Result、origin/revision/coverage/conflict/provenance；只追加，
  不回写历史。Package 只能在本轮调查结束后密封；`support/citation` 仅收 admissible entries，`boundary/audit` 必须保留 Gap、Failure、
  Partial、Conflict、Unknown、拒绝和资源记录且不能支持肯定 Claim；seal 不等于真值。
- fresh independent Reviewer 只返回原 Turn 结论清单中具体、可验证的 Finding，不携带可执行路径/命令/操作。Finding 回到主 Agent；主 Agent 读取 current Context/Work State/Package/Ledger，
  决定基于已有证据重写，或选择新的 World Model/Source 受控工具补证。新证据只能形成后继 Ledger Revision、Package、Answer 和 fresh Review identity；旧 Review 不得批准新包。
- Slice2/3 不设永久“一轮补证”上限。每个 exact freeze 必须预密封 Package Revision、model call、Broker operation、source bytes、
  wall-time 和 no-progress 高安全熔断，并证明数值足以容纳正常独立调查；达到熔断失败关闭，answerable 未回答计 FAIL。不得把输出解析修正
  或 Provider retry 伪装成补证。
- 新包不是同包 rewrite；任一最终 Answer 必须由对应 exact Package 的 fresh independent Review 批准。rewrite/补证不设为降低质量的固定次数配额，只受预密封的高安全熔断与 no-progress 约束。
- bounded absence 需要来源查询完整性、授权内容覆盖与业务发现 recall 三层证明；否则是具体 coverage limitation。
- 高质量 Evidence/结论只可异步提议 Knowledge Update，正常 Admission/Publication 失败不影响已交付 Answer，也不取得自动资格。
- 主 Agent/Reviewer 都无直接 Source/FS/Shell/network/credential/write 权限；只有 Broker/Worker 具有受控读能力。
- current Provider/Strategy/role-disclosure 资格按 exact identity 重建；同 Provider 分派后不 retry。跨 Provider 只允许 ADR-017 预授权的
  同 logical Turn 独立全链 fallback attempt，从 original Turn、relevant sealed Conversation Context 和 exact Cognition 重跑，不共享中间态或 late result 权威。
- 调用/资源上限只负责失败关闭，不降低 checklist、证据、Citation、Review 或 hidden Case 质量；Slice1 的一次 preview 补证上限不进入
  Slice2 正式协议。
- 完成跨重启 Conversation 恢复；新对话不继承 transcript、working state、referent、Turn evidence 或 Provider session。异步知识沉淀仍
  走正式 Admission/Publication，不把 Conversation memory 直接写成世界模型事实。

## Interfaces and affected code

新授权后允许夯实主 Agent Work State/计划/工具观察/重规划、Conversation/Turn/Context 持久恢复、Broker policy、Ledger/Package revision/conflict/dedup、
Response Control、Agent/Reviewer Gateway disclosure、
async persistence proposal、Web developer details、qualification/validation 工具和对应 tests。禁止添加项目 adapter、问题 classifier 路由、
演示答案或 validation-only Web。

## Compatibility, data and security boundaries

严格 WORLD_MODEL、显式 DIRECT、ITER-003—006 accepted scope和 Slice1 exact Result 都必须回归。第二工程和 early hidden 输入只在 Slice2
产品代码 freeze 后披露；披露后任何产品、Prompt、schema、route 或 Provider disclosure 改动烧毁该组证据并保留失败 Result。

Secret 不进 Package/Answer/Review/telemetry。Provider 只能看到 freeze 明确允许的 role/input/fragment，Source 原文最小披露；主 Agent 和
Reviewer 仍无直接 repo access。loopback、read-only、no update/write、no silent fallback、zero request retry 不变。

## Open questions and implementation risks

- 文档与源码冲突可能无法自动裁决；正确结果可以是呈现冲突及其版本/来源，而不是强行单一答案。
- 配置继承、generated source、annotation processing 或运行时行为可能超过静态 exact-revision 证据；不能把无法观察写成不存在。
- 产品外部基线与 World Model 因果贡献必须在同一四路 Gate 中判读。current Codex 与 direct-evidence arm 都不是 Oracle/裁判；
  same-agent source-only 与 full-cognition + source 两臂固定同一主 Agent/model/tool/budget/cache/Reviewer。目标臂绝对质量 PASS、逐题不输
  三条基线、总体严格超过 Codex 且有非 locator 世界模型贡献才通过；质量失败不能由成本优势补偿。报告仍必须计 exact 建模/更新/存储/
  Provider 成本并按新冻结的复用周期摊销，不能只报告提问期 Source bytes。
- early canary 曝光后若发现实现缺口，本组输入立即烧毁，不允许针对题目修补再复用。

## Acceptance scenarios

1. `V-GENERAL-002`：跨不同措辞、目录、框架和来源组合，无任何特判，答案层级与用户目标一致。
2. `V-RERETRIEVE-002`（PDR-004 pre-execution revision，旧定义无执行证据）：Reviewer Finding 回主 Agent；主 Agent 基于 current Context/Work State/Package/Ledger 选择重写或多步结果驱动补证，
   新包重封/重审；复杂 conflict/dedup/recovery/no-progress 与不可修复失败关闭闭合。
3. `V-ASYNC-002`：Delivery 不等待知识沉淀；异步 proposal 重新走 Update/Admission/Publication，失败不改写 Answer。
4. `V-HARDEN-002`：持久恢复、pagination、truncation、conflict、dedup、oversize、cycle/no-progress、六类高安全熔断、revision drift、
   Ledger/Package provenance 全部闭合；answerable 熔断耗尽计 FAIL。
5. `V-SEC-002`：Source injection、symlink/path/write/network/secret/disclosure/role escape、outcome unknown 全部失败关闭。
6. `V-CANARY-002` 与 `V-NEG-EARLY-002`：第二工程 5 answerable + 2 boundary 全部正确，bounded absence 与 coverage limitation 不混淆。
7. `V-XD-002` 与 `V-WEB-002`：同一 Web 在第二工程组合 accepted Snapshot 与新来源 Evidence。
8. `V-COMP-EARLY-002`：同一 exact revision/Conversation 脚本/可比较输出/rubric 下重跑四路：direct relevant evidence、same-agent
   source-only、same-agent full-cognition+source、current Codex。四路先密封并由独立 exact-source ledger 盲评；目标臂必须绝对质量 PASS、
   逐题不输三条基线、总体严格超过 Codex 且证明非 locator 世界模型贡献。全体打平或任何物质退步均 FAIL；建模成本和冻结复用周期只作
   次级报告，不得补偿质量。
9. `V-DIAG-002`：按 Source truth → World Model Cognition → Conversation Context/Turn goal → Agent Work State/plan/tool observation/replan → Broker/Worker → Ledger/Package →
   Answer → independent Review → Web 定位首次偏差。
10. `V-REGRESSION-002`：accepted scope、严格 WORLD_MODEL、显式 DIRECT 和 Slice1 主线无退步。
11. `V-REFLECT-002`：A1—A4/A6 exact Verdict、A5 early verdict、全部 Finding 与用户新决定完整。

## Architecture reflection checkpoint

Result 必须复核两个工程、early canary、四路严格价值 Gate、安全、建模与提问成本/时延、复用周期、Source exposure、模式复杂度、
知识沉淀边界与全部 Finding。`V-REFLECT-002 PASS` 不等于接受；A1—A4/A6 必须 `SUPPORTED`，A5 early comparison 不得 FAIL，用户须给出新的
`CONTINUE`，否则 `REDIRECT/REJECT`。

## Findings

按 [Findings](../findings/README.md) 和[实现发现回写规则](../../../governance/implementation-feedback-policy.md)处置。任何 Source、模式、
Package、Review、Provider disclosure 或知识沉淀边界变化必须同步 owning System 文档。
