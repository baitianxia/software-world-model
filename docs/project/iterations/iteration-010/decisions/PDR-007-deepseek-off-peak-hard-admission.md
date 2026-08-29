---
id: ITER-010-PDR-007
kind: project-decision
status: accepted
authority: project-decision
owners: [product, project, engineering, quality, ai, operations]
depends_on: [ITER-010-PDR-003, ITER-010-PDR-005, ITER-010-PDR-006, FINDING-010-139, FINDING-010-179, SYS-ADR-017, SYS-OPS-CONFIGURATION]
code: [src/software_world_model/application_services/deepseek_dispatch_admission.py, src/software_world_model/interface/engineering_chat_provider_runtime.py, src/software_world_model/interface/engineering_chat_session_artifact.py, src/software_world_model/interface/engineering_chat_alpha_cli.py]
tests: [tests/test_deepseek_dispatch_admission.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_chat_alpha_cli.py]
iteration: ITER-010
decision: REWORK
rework_strategy: HARD_OFF_PEAK_ADMISSION_FOR_ALL_PLANNED_DEEPSEEK_DISPATCH
decision_ref: local-user-message-utf8:sha256:ba8b85ba94ed69c876bf7cf15fa060ee494afb0c3dff383042c7197bdacacc7a
effective_scope: ITER-010-SLICE-001-and-future-project-provider-execution-plans
coding_input: true
---

# PDR-007：DeepSeek 闲时从调度偏好升级为调用前硬门禁

> PDR-008 current authority amendment：`authorization identity` 对 current public mall evaluation 追溯到 standing human authority，并由
> runtime 自动派生逐 run/request machine receipts；允许窗口内不再取得新的 human grant。峰时仍只能使用一次性 exact user override，
> PDR-007 的时间、质量、网络前 fail-closed 和逐 request 重验均不放宽。

> 2026-08-29 current correction：原实现和本文把三个时段错误地套用于一周七天。current policy revision
> `ITER-010-PDR-007@2` 改为工作日使用三个时段，周六、周日全天闲时；相邻闲时按连续区间计算。该修正由
> `FINDING-010-179` 闭合，不改变 Ark 优先、合法 fallback、fresh 价格检查或其他安全边界。

## Context

PDR-003 已规定 Ark 优先并要求 DeepSeek 高成本批量调用尽量放到官方定义的非高峰时段，但“默认/优先”没有成为可验证的调用准入。
PDR-003 生效后仍有多次峰时 DeepSeek run；最新 `run-043` 在北京时间 `11:19–11:27` 执行 `18` 次 DeepSeek HTTP dispatch，且没有
window check 或 override receipt。`FINDING-010-139` 因而将问题归因为计划、实现和执行三层共同缺口。

本决定不改变 Ark→DeepSeek 对用户透明、两个 attempt 隔离、零同 Provider retry、完整质量链或安全边界。它改变的是 DeepSeek
外部 dispatch 的运营准入：开发者不能再把“优先闲时”解释为“峰时也可以直接运行”。

## Decision

### 1. 所有计划性 DeepSeek 调用统一受硬门禁

当前允许窗口固定为 `Asia/Shanghai` 半开区间：

- 周一至周五 `[00:00,09:00)`；
- 周一至周五 `[12:00,14:00)`；
- 周一至周五 `[18:00,24:00)`；
- 周六 `[00:00,24:00)` 与周日 `[00:00,24:00)`，即周末全天。

首尾相接的允许时段属于同一个连续闲时区间，不因午夜换日人为截断；因此普通工作日晚间可连续到次日 `09:00`，周五 `18:00` 可连续到
周一 `09:00`。`valid_until` 仍取连续闲时结束、run 最坏时长和 run/override expiry 的最早值。

门禁覆盖所有由开发或评测安排的 DeepSeek 请求，包括 probe、Conformance、Capability Evaluation、direction canary、Web 体验脚本、
比较、回归和多问题运行；不能通过把批次改名为单题、fallback、smoke 或 live 来规避。截至 `2026-08-29`，DeepSeek 官方峰谷价格已
生效，并明确高峰只发生在周一至周五；后续官方价格事实仍须逐 run fresh 检查，不能由运行器自行猜测或扩张窗口。

当前 ITER-010 尚未进入不可预先安排的生产流量。所有 direction canary 都是 planned run，必须整体安排在允许窗口；本决定不为尚未授权的
Production 设计异步排队协议，也不以该未来问题延迟当前 Web 体验。

### 2. Provider 网络和凭据之前必须有逐 run 准入收据

每个 planned run 在首次 DeepSeek Provider socket/connected descriptor provisioning、TLS acquisition、credential resolution 或 HTTP
dispatch 前必须密封 `DEEPSEEK_DISPATCH_ADMISSION@1`，至少包含：

- trusted UTC time、`Asia/Shanghai` 换算时间、时区数据库/时钟来源和策略版本；
- run 类型、exact product/source/session、Provider/model、最大 calls/tokens/duration；
- 执行时重新检查的 DeepSeek 官方定价页、check time、内容摘要和 `EFFECTIVE / NOT_YET_EFFECTIVE / CHANGED` 事实；缺失或 `CHANGED`
  必须先失败关闭并重新规划，不能自行扩张窗口；
- 命中的允许窗口，或 exact peak override receipt；
- Ark-first/合法 fallback 条件、完整质量预算和授权 identity。

窗口、时钟、官方检查或 override 任一缺失/无效时，DeepSeek 必须在 Provider socket/connected descriptor provisioning、TLS
acquisition、credential resolution 和 HTTP dispatch 前失败关闭，四类实际计数均为 `0`。run receipt 不能替代逐 request 检查；每个新
DeepSeek request 都要回指同一有效 receipt，并重验当前窗口、剩余 calls/tokens/duration 或 exact override。planned run 还必须保证最坏
完整质量链能在当前窗口结束前完成；进入高峰后不得再创建新的 DeepSeek request，已经发出的单个 request 只按既有零重试/结果未知规则
完成和密封。若意外延迟使剩余 Review 无法合规完成，则当前 interaction 失败关闭，不得交付截断质量链的答案。

### 3. 峰时例外只能是一次性 exact user override

普通开发授权、direction canary grant、Ark→DeepSeek route grant 或透明 fallback 权限都不包含峰时例外。确需峰时调用时，必须按
PDR-006 在 exact freeze 后直接申请最小 delta，绑定 Provider/model、exact run/Turn、原因、最大 calls/tokens/duration、有效起止时间和
到期时间。批准只绕过时间门禁，不绕过 Ark-first、attempt 隔离、零重试、完整 Review、披露、安全或 Production 边界；不得形成 standing
override。

等待允许窗口通常不需要申请权限，也不允许开发停工。开发者继续 Ark-only、本地归因、通用修复、mock、targeted tests、artifact seal 和
其他独立安全工作；PDR-008 后，到窗口且 standing authority 的自动 machine receipt 有效即直接继续，只有真正 scope delta 才申请。

### 4. run-043 的处置

run-043 的 Provider、token、失败和答案结果保留为真实审计证据；由于其违反 current scheduling policy，当前 verdict 是
`DEEPSEEK_SCHEDULING_POLICY_FAIL / REWORK / NOT_DIRECTION_ACCEPTANCE_EVIDENCE`。它不能解锁 comparison、hardening 或用户方向裁决，
也不能仅为补一张调度收据立即重跑。

下一步先在本地完成 run-043 的责任层归因，并把调度准入实现为可机械验证的最小 Gate。完成候选冻结后，PDR-008 要求再闭合 standing
authority → machine receipt runtime Gate；该 Gate 与允许窗口同时成立时直接执行一个后继 direction canary，不再等待新 human grant。

### 5. 验证门禁

新增 `V-DEEPSEEK-IDLE-001`，至少验证：

- 使用零剩余时长 fixture 验证半开窗口边界：`08:59:59` 允许、`09:00:00` 阻止、`12:00:00` 允许、`14:00:00` 阻止、
  `18:00:00` 允许；周六、周日任意时刻允许，周一工作日峰时仍阻止；另验证周五晚跨入周末及周末跨午夜不会误阻断，并以非零最坏时长
  验证 latest start 满足 `now + worst_case_duration <= continuous_window_end`；
- 峰时且无 override 时，在 Provider socket/connected descriptor/TLS/credential/HTTP 前失败关闭，相关计数均为 `0`；
- exact override 只覆盖绑定的 run/call/token/time 上限；
- Ark 成功、Application/Source/Security failure 或未授权时 DeepSeek dispatch 为 `0`；
- planned session 不能跨入高峰后继续创建新 DeepSeek requests；
- 每个实际 DeepSeek dispatch 都能回指同一有效 admission receipt；
- 调度门禁不能删减 Evidence、Citation、答案或独立 Review，也不能把失败改判为 PASS。

`V-DEEPSEEK-IDLE-001` 在下一次 DeepSeek 外部 dispatch 前阻断；它不阻断 Ark-only 和本地开发，不要求 full regression，也不创建新的
Iteration/Slice。

## Consequences

- PDR-003/PDR-005 的“默认/优先”措辞由本决定收紧为硬准入；PDR-006 的“持续开发”不能解释成峰时立即调用 DeepSeek。
- 当前产品 runtime 的原始机械 schedule gate 由 clean `03520eb…` 和
  `ITER-010-RESULT-V-DEEPSEEK-IDLE-001` 以零外部调用闭合；`FINDING-010-179` 又把 current policy 修订为 `@2` 并补上 weekday/weekend
  维度。真实 planned run 仍须独立提交 current artifact、fresh 官方检查、允许窗口或 exact override 及逐 dispatch/terminal receipt，不能从
  本地 PASS 推导 live 合规。
- 通用治理和模板必须把 declared provider window 变成可验收 admission policy；现有静态 docs validator 仅作 compatibility，不证明 run
  合规。
- 本决定本身不授权任何 Provider/model call、credential、Source disclosure、Browser、hidden、Production 或后续 Slice；current public mall
  execution authority 由后续 PDR-008 独立拥有，不能从本调度决定反推。
