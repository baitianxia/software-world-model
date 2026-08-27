---
id: ITER-010-PDR-006
kind: project-decision
status: accepted
authority: project-decision
owners: [product, project, architecture, engineering, quality, security]
depends_on: [ITER-010-PDR-002, ITER-010-PDR-005, FINDING-010-137, PROJECT-GOVERNANCE-DEVELOPMENT-DESIGN, PROJECT-GOVERNANCE-ITERATION-LIFECYCLE]
code: []
tests: []
iteration: ITER-010
decision: REWORK
rework_strategy: CONTINUOUS_EXECUTION_WITH_JUST_IN_TIME_EXACT_AUTHORIZATION
decision_ref: local-user-message-utf8:sha256:13a1931f084e1196fef5edca39a3f7d8d01da88c4e8abedfd088ef042541e399
effective_scope: ITER-010-SLICE-001-and-project-development-governance
coding_input: true
---

# PDR-006：开发持续到阶段交付，权限在需要时直接申请

> Current execution amendment：`ITER-010-PDR-007` 明确持续开发不等于峰时立即调用 DeepSeek。窗口外继续 Ark-only 和本地工作；
> DeepSeek 必须等待允许窗口和 runtime admission receipt，确需峰时例外时才直接申请一次性 exact override。

## Context and authority

PDR-005 已完成离线分层归因与工程认知资格两个本地 Gate。PDR-006 接受时，活动 Slice、本地产品/System 编码和确定性验证授权仍有效，
随后取得的一次受限 direction-canary root grant 尚未消费；该时间点状态现仅作决定背景，run-043 后续已消费该 grant。彼时停止而不冻结
候选、派生精确执行收据或继续运行，会再次把可体验版本推迟；未来
真正出现权限缺口时，只报告“需要授权”后退出，同样混淆 Slice 开发授权与一次性外部执行授权。

用户要求开发未完成时不得自行停下，需要权限时直接申请。本决定接受该执行规则，但不把它伪装成 Provider/model、credential、动态
Source disclosure、Browser、hidden、后续 Slice 或 Production 的具体 grant；这些动作仍须逐次满足 exact freeze 和最小授权。

## Decision

### 1. 权限缺口只阻断对应动作

缺少、消费、过期、拒绝或 identity 漂移的 external grant 只阻断其 exact side-effect action。只要 Slice 的本地开发授权仍有效，Iteration/
Slice 保持 `AUTHORIZED / IN_PROGRESS / coding_input=true`；不得因为 `NOT_REQUESTED / PENDING / DENIED` 把开发冒充为 `COMPLETED`，也不得
自动改成 `paused`。产品 Gate FAIL 只阻止 PASS 声明、Slice 晋级和 hardening，默认继续同 Slice 的证据保留、归因和最小通用修复。

### 2. 到达权限边界必须直接申请

实现者确认下一必要动作跨越现有权限时，必须在同一开发回合：

1. 完成所有不需要该权限的 preflight，并冻结 exact product/source revision、artifact/session、Provider/model/endpoint、问题或输入类别、
   disclosure/redaction、credential reference、读写/网络范围、调用/重试/时长上限、Ark→DeepSeek 条件式 fallback、结果保存与 exclusions；
2. 检查相同 request identity 是否已有 active 或 pending grant；active 且未消费则复用，pending 不重复请求，consumed/expired/drifted 不复用；
3. 直接调用平台审批能力；平台没有审批入口时，直接提交一条完整的 exact-grant request。不得先问用户“要不要申请”，也不得只报告
   “需要授权”后结束；
4. grant 到达后在其 exact scope 内自动继续，不再要求用户重复确认计划。新增范围只申请 delta，不能把一次 direction canary 扩成未来版本、
   hidden、hardening、任意问题或 Production 授权。

### 3. 等待授权时仍继续安全工作

request 尚未批准时，继续所有与该 action 独立的已授权工作，包括本地根因归因、fixture/mock、targeted test、代码/文档一致性、artifact
seal 和 credential-free preflight。只有 exact request 已实际发出、所有这些工作都已穷尽时，才可让出开发回合；状态必须记录为
`WAITING_EXACT_GRANT / IN_PROGRESS`，并给出 request identity、唯一受阻动作、已完成的本地工作和批准后自动执行的下一动作。

request 被拒绝时不得绕过或重复催促；继续安全替代路径，只有范围或证据实质变化才可提交更窄的新 request。没有替代路径时仍是等待或
用户决策，不是开发完成。

### 4. hard stop 停止失控路径，不终止开发目标

timebox、连续无用户可见增量和同 failure signature 上限继续有效，但只停止扩域、hardening、full regression、规则堆叠和无新证据的
外部重跑。它们必须密封真实 FAIL/REWORK 证据并立即交付现状，同时继续最小体验纵切的本地归因与收敛；需要新权限时按上一节直接申请。
它们不能被解释为放弃当前 Slice 的可体验目标或允许开发者无申请地结束。

未授权动作、Secret/Source/write/network/Production 越界、破坏性目标不清、post-dispatch outcome unknown 同 Provider 重试等安全边界仍
fail closed。持续开发不扩大任何 capability authority。

### 5. 开发回合退出条件

实现者只能在以下任一条件成立时结束当前开发回合：

- 当前阶段的用户可见交付已实现、按阶段验证并交给用户；
- exact approval request 已实际发出，所有不依赖它的安全工作已穷尽，状态明确为等待授权；
- 用户明确 `STOP / REDIRECT / REJECT`；
- 命中不可通过申请或安全替代路径绕开的安全禁止。

“还需要授权”“一个本地 Gate 已完成”“timebox FAIL”或“当前外部权限为 0”本身都不是退出条件。

本条覆盖 PDR-002 中“比较失败默认暂停”的执行措辞：比较失败仍为同一 Slice `REWORK`，但现有本地开发授权覆盖修复时保持 active；只在
scope/Owner 变化、用户明确暂停或本地授权失效时进入 paused。PDR-002 的严格 Codex 质量阈值和不自动新建 Iteration 规则保持不变。

## ITER-010 action and current amendment

PDR-006 接受时，`V-LAYER-ATTRIBUTION-001`、`V-COGNITION-ELIGIBILITY-001` 与 `V-ALPHA-ACCESS-001` 已 PASS；当时的动作是先冻结
PDR-005 direction canary 的 exact product/artifact/session 与披露包，并校验当时尚未消费的
`local-user-message-utf8:sha256:15a8f8100f8cb6ac333edf85166cf572bb67a5e69d5a731a75c574d36fa5a4e4` 是否覆盖该 identity。覆盖时直接派生
精确执行收据并继续，不得再申请相同授权；只有 identity 漂移或范围不足时，才立即申请最多一个 Ark direction canary session 所需的
最小 delta。DeepSeek 仅作为同一冻结 Session 中 ADR-017 允许的条件式 fallback。随后继续执行真实语义链和两个未参与修复的异质问题，
不再停下来申请第二次确认。

run-043 已消费该 direction grant，但违反 PDR-007 的 DeepSeek 闲时门禁，只能作为失败与归因证据。当前状态改为
`DEEPSEEK_GATE_LOCAL_PASS / SUCCESSOR_FROZEN / EXACT_EXTERNAL_GRANT_REQUIRED`：调度 Gate 与 clean `3a6089f…` candidate 已闭合，当前
直接申请必要 external delta；等待允许窗口不等于等待权限，更不允许停止本地开发。该状态不解锁 full regression、三臂比较、后续
Slice、hidden 或 Production。
