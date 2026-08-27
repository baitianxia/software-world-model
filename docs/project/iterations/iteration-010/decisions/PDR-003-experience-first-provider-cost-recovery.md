---
id: ITER-010-PDR-003
kind: project-decision
status: accepted
authority: project-decision
owners: [product, project, architecture, engineering, quality, ai, operations]
depends_on: [ITER-010-PDR-001, FINDING-010-091, FINDING-010-092, SYS-ADR-017, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-OPS-CONFIGURATION, SYS-OPS-LOCAL-BROWSER]
code: []
tests: []
iteration: ITER-010
decision: EXPERIENCE_FIRST_RECOVERY_WITH_ARK_PRIMARY_AND_COST_GATED_DEEPSEEK_BACKUP
decision_ref: codex-user-message:sha256:47a3421d48fe3f36000e45696ea9c41b49b7e362332bc724306c10ca42fe119c
effective_scope: ITER-010-SLICE-001-recovery-and-subsequent-live-attempts
coding_input: false
---

# PDR-003：先恢复可体验 Web，并收紧 Provider 与 live 重跑成本

> PDR-008 current authority amendment：对固定 Apache-2.0 mall exact revision，现有 Slice/root authorization 是持续 human authority；
> Ark/current route 与 PDR-007 允许窗口内的合法 DeepSeek fallback 不再逐 run 申请。run/Turn/dispatch 仍自动派生 exact machine receipt；
> 峰时 DeepSeek 和其他真正 scope delta 仍须用户授权。本决定后文“另取 external grant”仅保存 PDR-008 前历史语义。

> Current execution amendment：`ITER-010-PDR-007` 把本决定的 DeepSeek“默认/优先”调度收紧为所有 planned dispatch 的调用前硬门禁；
> `ITER-010-PDR-006` 保留时间盒、Provider、成本和质量不可裁剪规则，但 hard stop 只结束扩域、hardening、full regression、规则堆叠与
> 无新证据的外部重跑；它不结束最小体验恢复或本地根因修复。权限 gap 必须在 exact freeze 后直接申请。

## Context and evidence

ITER-010 已有可复用的 Web、World Model Cognition、受控源码调查、Evidence、Citation 和独立 Review 资产，但本轮返工约 14 小时后仍
没有交付新的可体验版本。同期反复执行 DeepSeek Conformance 和多角色、多问题 live run，内部协议持续变严，用户却无法及时看到方向
是否改善。`FINDING-010-091/092` 分别把它定位为体验交付拆分缺陷和 Provider route/cost policy 缺口。

用户收据 `codex-user-message:sha256:47a3421d48fe3f36000e45696ea9c41b49b7e362332bc724306c10ca42fe119c`
同时确认 Ark 应是优先模型，并要求 DeepSeek 的高 token 成本批量调用尽量安排在其定义的非高峰时段。同轮后续纠正把备用条件扩展并
收紧为 attempt 级协议：Ark attempt 必须先密封终止且没有 authorized answer；只有可信分类的 Provider/model availability 或 capability
reason 才能对同一 logical question 透明启动一次完全隔离的 DeepSeek attempt，用户无需重提或新建 Session。

## Decision

### 1. Access 与答案 Quality 分开

Slice1 的下一交付是现有产品路径上的真实 Web，明确显示“质量未验收 / 非生产”。它必须可重复启动、固定
`http://127.0.0.1:8765/`、普通用户无需认证或内部运行参数、可提交问题，并真实显示 Provider 未资格、请求失败、答案或 Limitation；不能
用静态回放冒充可操作 Alpha。

`V-ALPHA-ACCESS-001` 只裁决页面和请求通路是否可操作；`V-ANSWER-REWORK-001` 独立裁决用户可见答案质量。Access PASS 不证明答案
正确，Quality FAIL/NOT-RUN 也不能抹掉已经形成的可体验 Access 结果。只有 Quality PASS 才允许进入 hardening。

### 2. 用 60/180/240 分钟硬时限阻止再次无限内循环

从 Slice 授权后的第一个产品代码变化起，计划检查点是：60 分钟内页面可启动；180 分钟内形成持续、用户可操作的 Alpha；240 分钟为
硬停止点。该时间线已经被本轮约 14 小时经过反证，因此当前不是重置计时后继续扩张，而是立即执行 hard-stop recovery：停止新功能、
Schema/Prompt/Contract 扩张和外部批量调用，只保留启动、安全、失败真实性、一个 current Provider qualification 与一个 live smoke 所需的
最小闭环。

硬停止后的恢复顺序固定为：先在本地闭合页面 Access → 冻结一个最小候选 → 按 Provider policy 最多取得一次必要资格 → 只跑一题 live
canary → 独立复核。如果 canary 未通过，不运行三题集；保存失败并回到本地诊断。只有 canary 技术链与答案质量均通过，才允许在同一冻结
版本上运行“原失败题 + 两个异质题”并请求用户体验。

### 3. 失败先定位根因，不再追着答案加规则

过去的长循环主要在追逐每次错误答案的表象，而没有先证明最早发生偏差的系统层。每次失败必须按 `Source truth → World Model
Cognition → Question Understanding → Investigation → Evidence Package → Answer → Review → Web` 顺序定位最早偏差，并先写出可证伪的
root-cause hypothesis。没有该假设和最小复现，不得修改 Prompt、Schema 或 Contract。

一次修复必须先通过本地最小复现和两个未参与修复的相邻案例，之后才允许一题 live canary。同一 failure signature 修一次后仍复现，立即
停止继续堆规则，转入架构职责评审。首次体验前只跑 targeted impact、startup、safety 与失败真实性检查；full regression 只允许在用户对
Alpha 作出 `CONTINUE` 后的 hardening 阶段，以及正式验收前执行。

### 4. live attempt 必须轻量计数

- 一个 sealed 产品版本上的 question run 只要到达任何外部模型 dispatch，就计为一次 live attempt；调用次数多少、是否完成 Answer 或
  是否得到 HTTP 成功都不改变计数。
- 同一 failure signature 最多允许一个 successor live attempt。连续两次 live attempt 没有产生用户可见增量时，停止外部重跑并回到本地
  诊断；Prompt、Schema、Contract 或内部测试数量变化本身不是用户可见增量。
- 首次可体验版本前最多执行一次 current Provider qualification 和一个 live smoke，不执行 full regression。Access 形成后也不能据此
  启动完整回归；只有答案质量通过、用户对方向作出 `CONTINUE` 后，才在 hardening 和正式验收前执行 full regression。

### 5. Ark primary，DeepSeek 是同一问题内透明的独立 fallback attempt

Session 在任何产品问题 dispatch 前预封有序 `VOLCENGINE_ARK → DEEPSEEK` route，以及两个 Provider 各自的 exact
model/configuration/qualification/credential-reference/disclosure scope。普通用户只提交一次问题，不选择模型，不因 fallback 重提问题或
重新启动 session。

每个 logical question 先执行 Ark primary attempt。只有 Ark attempt 已密封为没有 authorized answer 的 terminal，且原因被可信分类为
Provider unavailable、HTTP error、outcome unknown、output invalid 或 model Review rejected，才允许自动启动最多一次 DeepSeek fallback
attempt。Application、Source 或 Security failure 不允许 fallback；实现缺口也不能伪装成 Ark unavailable。

Fallback 不是延续或重试 Ark 的外部 request。它使用新的 attempt identity，从 immutable original question 与同一 World Model Cognition
重新执行 Question Understanding、Investigation、Broker/Worker、Ledger/Package、Answer 和 Review 完整链；不得读取或拼装 Ark attempt 的
Ledger、Evidence、Package、Draft、Review 或部分响应。每个 Provider 内 retry 为 0。Ark 的迟到响应隔离为 late result，永远不能覆盖
fallback 或已封存的 logical-question result。Ark outcome unknown 后 fallback 还必须显式记录潜在重复计费风险。

同一 Adapter/Configuration/endpoint/model/transport/rendering identity 下仍有效的 Conformance 直接复用。领域 Prompt、答案 Schema 或
产品代码中与该 identity 无关的变化不触发 fresh Conformance。identity 变化、有效期结束或证据明确失效时才重新取得。

DeepSeek 所有计划性开发、资格、canary、比较、回归和多问题调用必须安排在北京时间 `[00:00,09:00)`、`[12:00,14:00)`、
`[18:00,24:00)`。每次 run 开始前必须检查并记录 DeepSeek 官方定价页；是否已正式执行峰谷定价不影响项目门禁。窗口外没有一次性
exact user override 时，必须在 credential/HTTP 前关闭且 DeepSeek dispatch 为 `0`。具体准入收据和验证由 PDR-007 拥有。

### 6. 成本不能降低已经开始的问题质量

余额、单价和 token 预算只用于决定是否启动 question/batch。开始后必须保持冻结的 Evidence、Citation、独立 Review 和质量标准；不能
因即将进入高峰、调用多或余额不足而缩短调查、跳过审核或把 Quality FAIL 改成 PASS。若无法承担完整问题预算，则在 dispatch 前不启动。

## Scope and consequences

- 本决定修订 ITER-010/Slice1 的执行顺序和 Provider policy，不废弃现有实现与失败证据，也不追认 run-033/034 或旧答案。
- 从现在到新 Web Access 形成前，不继续建设新的答案/审核 Schema、Prompt 或 Contract；只处理最短 Access/route/真实失败阻断。
- 当前透明 Ark-first/fallback attempt route、Conformance reuse 与 DeepSeek scheduling 尚未由产品代码和确定性测试证明；相关文档明确记录
  为目标与当前偏差。
- PDR-001 的现有 Slice1 编码授权仍是产品变化的授权来源；本决定本身不新增 credential、Provider/model 调用、动态源码披露、live browser、
  hidden、Slice2/3 或 Production Activation 权限。每次外部运行仍需 exact freeze 与适用授权。

## Revisit condition

只有用户已经实际操作新的 Web、`V-ALPHA-ACCESS-001` 有真实证据且一题 canary 完成独立复核后，才能恢复答案协议扩张或三题 live。任何
方案若再次要求在首次体验前完成 full regression、多题套件或无界 Prompt/Schema/Contract 闭环，直接违反本决定并触发
`V-TIMEBOX-001 FAIL`。
