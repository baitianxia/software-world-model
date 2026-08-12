---
id: ITER-005-FINDINGS
kind: iteration-findings-index
status: dispositioned
authority: development-evidence
owners: [engineering, architecture]
depends_on: [PROJECT-GOVERNANCE-IMPLEMENTATION-FEEDBACK, ITER-005-PROPOSAL]
code: []
tests: []
iteration: ITER-005
---

# Iteration 005 Findings

本轮当前登记十条实现发现，均已处置：

- [FINDING-005-001](FINDING-005-001.md)：Catalog pointer 已发布而 receipt 中断、且恢复前 Entry set 又变化时，必须先补录
  连续 revision 再发布下一版；代码与故障回归测试已闭合。
- [FINDING-005-002](FINDING-005-002.md)：把新增 launcher 的 pre-coding contract freeze 与实现后的 pre-listen exact
  provenance seal 分开；真实外部分派仍需单独披露授权。
- [FINDING-005-003](FINDING-005-003.md)：补齐显式未知/同名 artifact 的 ZERO/AMBIGUOUS candidate Limitation；该通用
  Answer 变更使继承的旧 Answer package 资格失效，候选 package 必须重新密封并完整验证。
- [FINDING-005-004](FINDING-005-004.md)：历史 Gateway freeze 只能作为资格基线；当前 session 必须用 exact grant/disclosure
  receipt 重新授权，未授权时在进入 qualified Gateway baseline 前失败。
- [FINDING-005-005](FINDING-005-005.md)：candidate evaluation grant 只要求 pre-run qualification；Product Result/对照是本次
  运行的输出，不能成为首次运行的循环前置条件，也不能把候选提前称为 accepted。
- [FINDING-005-006](FINDING-005-006.md)：完整正向 grant 暴露 qualification/suite schema 摘要不兼容；loader 改为验证
  schema-bound digest，freeze 还必须在 exact staged Answer package 上重跑产品测试并复核 stage 未漂移。
- [FINDING-005-007](FINDING-005-007.md)：`run-002` 的负向路径题错误地用同名短名作为唯一 Entity；新 freeze 改用完整
  GA，并要求全部密封问题先通过 deterministic product probe；`run-003` 已闭合该问题。
- [FINDING-005-008](FINDING-005-008.md)：成熟 Source Agent 的内部 Provider 调用次数不能从 CLI terminal 精确观测；
  comparison schema 已区分外部 task 与可观测 Provider call，并在 `run-005` suite 中冻结 exact baseline protocol/source
  closure、baseline-first 顺序和授权前短路。
- [FINDING-005-009](FINDING-005-009.md)：真实浏览器验收发现长 Read Set identity 会撑开三列 Grid，让后两张选择卡被
  result panel 遮挡；代码与静态资产回归测试已加入收缩和换行约束，修改后候选必须重新密封。
- [FINDING-005-010](FINDING-005-010.md)：两个独立 live run 证明 controlled Direct 的 1000-token/隐含 JSON 响应
  信封不足；新协议密封 4096-token 与严格 JSON-only contract，同时保留单次无重试和全部历史失败。

全部 Finding disposition 不自动接受 SLICE-002 或 ITER-005。`run-006` 的正式浏览器 PASS、V-009 FAIL 保留；新候选已在
绑定 exact suite 的当前用户授权下完成三条真实披露，`run-007` comparison 与浏览器均 PASS。Proposal 的进入前证据——动态
浏览器固定数据以及 Coverage copy 过度宣称——分别由本轮 Slice 边界与 V-002 处理。当前只等待用户 Acceptance 裁决，
Production Activation 未执行。
