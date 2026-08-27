---
id: FINDING-010-137
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [project, engineering, quality, security]
depends_on: [ITER-010-PDR-005, PROJECT-GOVERNANCE-DEVELOPMENT-DESIGN, PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ITER-010-RESULT-V-COGNITION-ELIGIBILITY-001]
code: []
tests: []
iteration: ITER-010
classification: iteration-design
scope: systemic
disposition: make-authorization-boundary-nonterminal-and-request-exact-grant-just-in-time
target: ITER-010-PDR-006
---

# FINDING-010-137：缺少执行授权不应被当成开发终点

## Observation

PDR-005 的离线分层归因和工程认知资格已经通过，活动 Slice 的本地开发授权仍然有效；随后取得的
`local-user-message-utf8:sha256:15a8f8100f8cb6ac333edf85166cf572bb67a5e69d5a731a75c574d36fa5a4e4` 还授权了一次受限
direction canary，尚未消费。既有治理却把检查点、Gate failure、timebox hard stop、`REWORK` 和授权边界多次表述成暂停 Slice、关闭
coding input 或停止后续工作，容易让开发者在阶段交付前结束开发：已有 grant 时没有继续冻结和执行，真正缺少 grant 时又只报告
“当前未授权”而没有实际发起审批。

用户明确指出开发未完成时不应自行停下，需要新增权限时应直接申请。该消息的本地 UTF-8 摘要为
`sha256:13a1931f084e1196fef5edca39a3f7d8d01da88c4e8abedfd088ef042541e399`；它是执行治理决定依据，不是任意外部调用的 grant。

## Evidence

- `ITER-010-RESULT-V-LAYER-ATTRIBUTION-001` 与 `ITER-010-RESULT-V-COGNITION-ELIGIBILITY-001` 已 PASS，本地下一阶段不是未知；
- Manifest 当前记录一次 direction-canary root grant 为 `authorized-pending-clean-candidate`，但没有把“先冻结并复用 active grant；确有
  identity/scope gap 时立即申请最小 delta”定义为必须动作；
- Development Design Policy 与 Iteration Lifecycle 把多个失败或停止条件扩大为默认 `paused / coding_input=false`，没有区分“停止一次受控
  外部动作”和“终止整个开发目标”；
- exact grant、Secret、只读、重试和 Production 边界仍然必要，不能用持续开发原则绕过。
- 现有 `scripts/docs.py` 的 ITER-010 兼容校验只认识“exact runtime receipt 尚未签发/历史 grant 已消费”，不认识“人类 root grant 已授权、
  freeze 后内部派生 runtime receipt”两层状态；Manifest 必须显式标记旧字段为 compatibility-only，并以
  `authorization_continuation_policy` 拥有 current authority，不能让旧字段驱动重复人工授权。

## Decision and disposition

该发现处置到 `ITER-010-PDR-006`，并向通用项目治理与模板传播：

- Slice 开发授权与外部执行 grant 分开。active 且覆盖 exact action 的 grant 必须复用；缺少、消费、过期或漂移的 grant 只阻断对应
  exact action，不自动撤销仍有效的本地开发授权；
- 到达权限边界后，开发者先完成所有必要的本地 preflight 和 exact identity/disclosure freeze，然后直接发起一次最小化 exact approval
  request；不能先问“是否要申请”，也不能只描述缺少权限后结束；
- grant 批准后在其 exact scope 内自动继续，不再请求重复确认；未批准时继续所有不依赖该 grant 的安全工作；
- timebox、无增量和同签名停止规则只终止扩域、hardening 或无新证据的外部重跑，不终止最小体验目标和本地根因修复；
- 只有用户明确停止/转向/拒绝、不可绕过的安全禁止，或 exact request 已实际发出且所有安全替代工作穷尽，开发回合才可让出。后者状态是
  `WAITING_EXACT_GRANT / IN_PROGRESS`，不是完成、失败或停止。
- 文档门禁代码的两层授权原生建模和当前失败单测属于后续治理工具修复，不允许阻塞 ITER-010 当前方向体验，也不得由本次 docs-only
  决定越权修改；在此之前 current Manifest 的 compatibility 标记与 PDR-006 共同消除人工执行歧义。
