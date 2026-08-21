---
id: ITER-009-INDEX
kind: iteration-index
status: authorized
authority: current-development
owners: [product, project, architecture, engineering, quality]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ROADMAP-M-002, ROADMAP-CANDIDATE-LOCAL-WEB-DIRECTION-PREVIEW-RECOVERY, ITER-008-INDEX, ITER-009-PROPOSAL, ITER-009-READINESS, ITER-009-VERIFICATION, ITER-009-SLICE-001, ITER-009-SLICE-002, ITER-009-SLICE-003]
code: []
tests: []
iteration: ITER-009
coding_input: true
---

# ITER-009：本机 Web 方向体验恢复

## Status and authorization

`AUTHORIZED / SLICE-001 CURRENT DEVELOPMENT / SLICE-002 AND SLICE-003 NOT AUTHORIZED`。

用户消息 `codex-user-message:sha256:6ca47f7daa8bff61fa53e99d1c19b16098207d45fbf210427c3af19e5c9999ed`
接受本轮 Readiness，并只授权进入 `SLICE-001` 开发。授权对象是代码开发，不包含读取 Provider credential、建立公网连接、发起模型
调用、启动正式 Web 会话、披露隐藏题或执行 Production Activation；这些动作仍须按现行 Contract 形成独立的 exact freeze 和
运行授权。

本轮产品代码基线固定为 `2cd743b2ba74c5a79cd4d38433830786de09e753`，规划提交为
`967e41bcaa25112ea6b18620d0ac8e0aa5a4a42a`。未验收的 `1.5.12` 实验仅保存在归档提交
`c4ed92ea44383557dd25e6d327569cff13bb6d65`，不是本轮基线，不能整包继承。

## Required inputs

- [Proposal](proposal.md)
- [Manifest](manifest.yaml)
- [Verification Matrix](verification-matrix.md)
- [Readiness Review](readiness-review.md)
- [Development Design](development-design/README.md)
- [Findings](findings/README.md)
- [Results](results/README.md)

执行顺序固定为：先提供真实本机 Web 方向体验；方向决定为 `CONTINUE` 后才授权通用工程夯实；夯实再次决定 `CONTINUE` 后才授权
正式验收。任何一次 `REDIRECT` 或 `REJECT` 都停止后续 Slice，不以测试数量或内部组件完成替代用户体验结论。
