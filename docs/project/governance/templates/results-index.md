---
id: ITER-NNN-RESULTS-INDEX
kind: iteration-result-index
status: draft
authority: evidence
owners: [project, quality]
depends_on: [ITER-NNN-VERIFICATION]
code: []
tests: []
iteration: ITER-NNN
---

# Iteration NNN Results

结果只记录 exact subject 上实际发生的运行、证据、失败和限制，不拥有 System 规范。开发中的普通提交、中间检查、Provider dispatch、
普通失败以及首次可操作浏览器即时交付都不创建 Result；它们保留 trace、测试输出或 Finding。只有最终体验方向 handoff，或证明一次
有证据的通用修复后同类重大失败仍存在而需要移动计划游标时，才创建 Manifest 预注册的唯一 Result，并最终链接 Acceptance。
失败证据必须保留；`REWORK` 留在同一 Slice，不能被改写为方向转向。

独立 user-direction action 可以生成其预注册的 direction-only Result/receipt，但它只记录用户决定并保持 action 自环，不属于开发中间 Gate
Result，也不解锁下一阶段。

每个 machine action 只能由 Manifest 指定的唯一 Result ID/path 驱动迁移。该 transition Result 必须精确填写 `plan_revision_ref`、
`action_ref`、`verification_case_id` 和 `plan_gate_verdict`；最后一项只能是 `PASS / FAIL / INVALID`，不得使用别名。Result 记录事实，不能
修改 allowlist、预注册 contract 或为同一 candidate diff 创建权限。

用户方向 Result/receipt 只记录方向，不能自行解锁后续动作；`CONTINUE` 仍需新 PDR、明确用户授权和可信父 cutover。本地消息 digest 不能
冒充平台认证身份、签名或授权。
