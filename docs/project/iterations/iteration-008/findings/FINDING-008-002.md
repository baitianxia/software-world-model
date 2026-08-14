---
id: FINDING-008-002
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [ITER-008-SLICE-001, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-AI-MODEL-GATEWAY]
code: [src/software_world_model/application_services/bounded_world_model_investigation.py, src/software_world_model/interface/world_model_product.py, src/software_world_model/interface/world_model_runtime.py, src/software_world_model/ai_infrastructure/pinned_ark_https.py]
tests: [tests/test_bounded_world_model_investigation.py, tests/test_java_source_semantics.py, tests/test_model_egress_gateway.py, tests/test_pinned_ark_https.py]
iteration: ITER-008
classification: iteration-design
disposition: preserve-frozen-envelope-and-report-exact-consumed-call-count
target: ITER-008-SLICE-001
---

# FINDING-008-002：显式 FINISH 占用一个调查调用，descriptor 数量只能是上限

## Observation

实现把每个模型 Proposal 都作为独立 Provider 调用审计。模型必须先取得至少两个 executed Result，之后才能在另一个 Proposal 中返回
`FINISH`；因此当前正常显式终止路径使用 3—4 个 Investigation 调用、总计 5—6 个调用。冻结的 2—4 Investigation / 4—6 total
仍是安全 envelope，但 4-call 下界不是当前显式 `FINISH` 路径的可达成功值。同时 supervisor 必须在答案完成前准备连接，不能预知实际
会在 5 还是 6 次结束。

## Evidence

- `BoundedWorldModelInvestigationSession` 拒绝只有一个 executed Result 时的 `FINISH`；公开多方法 fixture 的实际序列为
  Candidate、method batch、FINISH、Draft、Review，共 5 次；
- 第四个 Investigation Proposal 未 `FINISH` 时形成 `INVESTIGATION_BUDGET_EXHAUSTED` Limitation，随后仍可在总上限 6 内完成
  Draft/Review；
- Gateway sequence policy 接受 2—4 个 Investigation role 后的 Draft/Review，但 Application trace 继续执行更强的 two-executed-
  Results terminal rule；Gateway 不替 Application 伪造 terminal；
- supervisor 预建 6 个 descriptor；5-call fixture 消费 5 个，并将剩余 1 个关闭且记录 `UNUSED_CLOSED`。审计满足
  `provisioned = consumed + unused_closed`。

## Impact and classification

这是冻结预算在当前最小实现中的可达性与报告口径，不扩张 System 上限、安全权限或模型能力，分类为 `iteration-design`。若把
`FINISH` 隐藏为零调用、自动伪造 terminal 或为了凑 4 次而放宽 two-Result 规则，都会破坏已授权协议。

## Decision and disposition

保留冻结的 4—6 total 安全 envelope，不增加调用、不 retry，也不弱化 `FINISH` 前两个 executed Result。产品 Result 必须报告实际
consumed count；runtime 只把 6 当作 descriptor provision 上限，正式 Answer/Page/Gateway audit 接受并交叉验证实际 4—6，所有未消费
descriptor 必须显式关闭。当前 deterministic 正向路径的 expected actual 为 5，预算耗尽路径最多为 6。

主处置进入 `ITER-008-SLICE-001` 的验证与报告口径。若后续要让 4-call Delivery 真正可达，必须另行设计可验证的 platform terminal，
更新 Prompt/trace/qualification identity，并取得新的用户授权；本 Slice 不静默引入。

## Verification after disposition

- tests 覆盖 early FINISH 拒绝、5-call supported path、6-call budget terminal、Gateway 角色顺序、第五 Investigation 拒绝；
- transport 覆盖 6 个 descriptor 中未使用项的关闭审计；
- runtime postcondition 分离 provisioned count=6 与 actual Provider/network count=4—6。
