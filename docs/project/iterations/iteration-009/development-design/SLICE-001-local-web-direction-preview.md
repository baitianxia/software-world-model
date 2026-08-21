---
id: ITER-009-SLICE-001
kind: development-slice
status: authorized
authority: current-development
owners: [engineering, architecture, quality, product]
depends_on: [ITER-009-PROPOSAL, ITER-009-READINESS, ROADMAP-CANDIDATE-LOCAL-WEB-DIRECTION-PREVIEW-RECOVERY, ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-ACCEPTANCE, ITER-008-INDEX]
code: [src/software_world_model/application_services, src/software_world_model/ai_infrastructure, src/software_world_model/interface]
tests: [tests, validation]
iteration: ITER-009
coding_input: true
product_goal_gate: V-000
product_goal_accepted_capability_refs: [ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-ACCEPTANCE]
product_goal_cross_domain_case_ids: [V-XD-001]
product_goal_web_checkpoint_id: V-WEB-001
product_goal_direction_preview_checkpoint_id: V-PREVIEW-001
product_goal_reflection_gate_case_id: V-REFLECT-001
product_goal_slice_gate_case_ids: [V-BASELINE-001, V-001, V-SOURCEOFF-001, V-SEC-001, V-ANSWER-001, V-LIMIT-001, V-XD-001, V-WEB-001, V-PREVIEW-001, V-REFLECT-001]
---

# SLICE-001：真实本机 Web 方向体验

## Status and dependencies

`AUTHORIZED / CURRENT DEVELOPMENT`。授权收据为
`codex-user-message:sha256:6ca47f7daa8bff61fa53e99d1c19b16098207d45fbf210427c3af19e5c9999ed`，时间为
`2026-08-21T03:19:16Z`。本 Slice 是唯一编码输入；`SLICE-002/003` 保持 proposed。

本授权允许在 product baseline `2cd743b2ba74c5a79cd4d38433830786de09e753` 上开发和执行本地确定性测试，不授权读取真实
credential、建立 Provider socket、发起模型请求、启动正式 Web 运行、提交浏览器问题或披露隐藏 canary。每个 live 动作仍需单独的
exact freeze 和用户授权，且不得把本消息复用为 dispatch grant。

## Product-goal contribution and cumulative integration

- Product gap shortened：把已有正向 Web 证据推进为普通用户可操作、限制清晰的方向体验，并最早暴露 supported answer 与 typed
  Limitation 的 Answer/Review 交付问题。
- Product capability-path step advanced：恢复 `ROADMAP-M-002` Step 1 的用户体验验证，不增加新知识域。
- Existing capabilities combined：ITER-005 的 Workspace/Update/Web/Citation 与 ITER-006 的 declaration/`CALLS`。
- User-visible Web questions at slice end：一个多步骤流程题、一个不含类名或方法名的等价改述和一个 boundary；隐藏 canary 留到
  用户确认方向后的 Slice2。
- Slice stop / redirect signal：半个工程日内无法得到新 Web 结果；依赖题目或工程特判；Citation 不支持结论；boundary 产生无关证据、
  内部失败或伪造；需要 Source/Update/Direct fallback、弱化 Review 或开放公网监听。
- Critical assumptions tested：本段正式验证 A1—A3；`V-XD-001` 和 `V-SEC-001` 分别作为 A4/A5 的提前反证。
- Reflection gate and success decision：`V-REFLECT-001`；只有全部到期假设 `SUPPORTED`、产品 Case PASS 且用户给出新的 `CONTINUE`
  收据，才可申请 `SLICE-002` 授权。

## Direction preview checkpoint

真实入口是现有 product-owned 本机 Web，仅监听 `127.0.0.1`，普通用户无需认证。页面必须显示“方向体验 / 非验收 / 非生产”，并允许
用户提交新问题；旧 browser result 或静态回放只可辅助诊断，不能计为体验完成。

最小任务为：一个已有证据支持的多步骤问题、一个无符号等价改述、一个证据边界问题。用户从输入自然度、答案组织、Citation 可核对性
和限制表达四方面给出 `CONTINUE / REDIRECT / REJECT`。`REDIRECT/REJECT` 立即停止；只有本 Slice 的方向体验、安全、跨域和
Reflection Gate 完成且决定为 `CONTINUE`，才可申请下一段开发授权。隐藏 canary、成熟源码 Agent 对照和逐层诊断由 `SLICE-002`
承担，不得回到首次体验之前。

体验前只允许完成启动、安全、exact identity、通用答案交付和 Citation 所必需的最小工作。不把完整 4+2、全面回归、性能优化、
Production、第二工程广度或知识沉淀重构列为本 checkpoint 前置。

## Current vs expected behavior

基线已经在正式 Web 成功回答 supported 登录流程并给出四个 Citation；同一运行的 boundary 问题在 Draft 正确形成 Limitation 后被
Review 拒绝，用户只看到内部失败。预期行为是：supported 问题形成自然答案；证据不足问题形成具体 Limitation；两者均由独立 Review
按对应 answer type 检查并以真实 Citation 或明确证据缺口交付。

本段首先尝试不改产品逻辑复现可用 Web。若 exact baseline 不能启动，记录最早阻断；只允许修复形成方向体验所需的最小通用缺陷，
不得提前重写整套 Prompt、Schema、Oracle 或资格协议。

## System contracts and invariants

- 问题前构建 exact Snapshot/Bundle，问题和 suite 不进入 Update；提问前后知识 identity 不变。
- 调查只使用 typed World Model query result；Answer worker 看不到 Repository、Source、raw Evidence、Update 或 Direct tools。
- 调查保持 2—4 次有界模型决策，随后恰好一次 Draft 和一次独立 Review；不得因调用次数目标降低完整性或审核质量。
- Draft 只从 sealed evidence package 形成 supported answer 或 typed Limitation；Reviewer 依据 answer type 检查实质遗漏、错误推断和
  Citation coverage。
- 如果 Review 指出具体缺口，只有同一 sealed evidence package 上的一次针对性重写方案经过 Contract/预算冻结后才可实施；本段不引入
  无界循环或隐藏 retry。
- Source、Update、Direct fallback、credential 泄露和公网监听始终禁止；任何 outcome unknown 失败关闭且不跨 Provider retry。
- 不加入问题文本、工程名、关键词、类名、方法名、fixture 或 Oracle 特判。
- Production Activation 为 `NOT_EXECUTED`。

## Interfaces and affected code

允许检查和最小修改现有 World Model answering application service、model egress boundary、local HTTP/Web presenter、方向体验状态标识与
相应测试/验证资产。必须沿用一个 product-owned Web 入口，不新建 validation-only 平行产品链。

每个开发任务提示只包含一个明确目标、不可变边界、输出合同和验证命令。外部开发工具再次拒绝最小正常任务时保存 receipt 并停止该
执行面，不对被拒内容做编码、拆字、混淆或自动重试。

## Compatibility, data and security boundaries

ITER-005/006 的 accepted Workspace、Update、Snapshot、View、Web、Citation 和 Java static-call 行为保持。ITER-008 代码提交只作为
技术 baseline，不继承 Acceptance；归档提交 `c4ed92ea44383557dd25e6d327569cff13bb6d65` 不得 cherry-pick 或批量复制。

本机 Web 只监听 loopback，页面不显示 secret、raw prompt、hidden rubric 或内部授权对象。live Provider 只能在新的 exact candidate、
current qualification、run-specific grant 和 pre-dispatch identity 复核全部闭合后使用；当前 Slice 编码授权不满足该条件。

## Open questions and implementation risks

- 当前 boundary 首次偏差可能在 Review applicability，也可能存在更早的 evidence completeness 差异；必须按 Source → Snapshot → Query
  → evidence package → Draft → Review → Web 顺序定位。
- 若最小通用修复改变 Strategy、Adapter、Prompt、Schema 或 Provider configuration identity，旧资格和 run-012 grant 全部不可继承。
- 若只在公开演示工程上成功，仍可能是过拟合；本 Slice 只裁决方向，不声称跨工程泛化。代码冻结后的 early canary 和成熟源码 Agent
  小规模对照属于 `SLICE-002` 的阻断项。
- 页面方向标识不能被误解为正式验收或 Production。

## Acceptance scenarios

1. `V-BASELINE-001`：精确证明 product baseline、planning commit 与归档实验三者分离，工作树不含归档资产。
2. `V-001` 与 `V-SOURCEOFF-001`：问题前更新、提问期 Source-off 与状态不变全部 PASS。
3. `V-ANSWER-001`：真实 Web 对 supported 多步骤题及无符号等价改述给出无重大错误、可读、Citation 完整的答案。
4. `V-LIMIT-001`：真实 Web 对证据不足题交付具体 Limitation，不显示内部证明记录、无关证据或伪造否定。
5. `V-XD-001` 与 `V-WEB-001`：同一正式入口组合已接受 `CALLS` 与本轮证据组织/审核交付能力。
6. `V-PREVIEW-001`：用户看到三个最小任务并形成方向决定；该决定不等于下一 Slice 授权。
7. `V-SEC-001`：只读、Secret、loopback、预算、Reviewer 隔离、零 fallback/隐藏 retry PASS。
8. `V-REFLECT-001`：逐项记录 A1—A3 Verdict、A4/A5 early signal、Finding 和用户 exact decision receipt。

live Case 只有取得后续 run-specific 授权并实际执行才可 PASS；当前开发授权本身不构成任何运行证据。

## Architecture reflection checkpoint

产品 Gate 后必须形成独立 Slice Result，比较预期与实际 Web、首次偏差层、复杂度与 Findings，并明确记录成熟源码 Agent 对照和
价值指标尚未执行、不得推导质量结论。
`V-REFLECT-001 PASS` 只表示复盘完整；用户必须另给 `CONTINUE` 才能授权下一段。A1—A3 任一 `FALSIFIED/UNRESOLVED`，或 A4/A5
提前反证 Case FAIL 时，只能 `REDIRECT/REJECT`，不得继续堆叠工程夯实。隐藏 canary、成熟源码 Agent 对照和逐层诊断在本段明确
deferred，不能反过来阻塞最早方向体验。

## Findings

发现系统边界、Contract、质量规则或迭代决定变化时，写入 [Findings](../findings/README.md)，并按
[实现发现回写规则](../../../governance/implementation-feedback-policy.md) 处置。
