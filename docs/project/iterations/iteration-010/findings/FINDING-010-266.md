---
id: FINDING-010-266
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [project, engineering, operations, quality]
depends_on: [ITER-010-PDR-014, FINDING-010-265]
code: []
tests: [validation/iteration_010_mvp]
iteration: ITER-010
classification: iteration-design
scope: systemic
disposition: schedule-fresh-logical-runs-after-proven-pre-http-provider-failure
target: ITER-010-PDR-014
---

# FINDING-010-266：已证明未进入 HTTP 的 Provider 失败必须定时续跑，不能把开发任务置为等待

## Observation

`pdr014-browser-alpha-run-006/007` 各执行三个真实 Turn。两次运行的 Ark 都是 TLS handshake `3/3` 失败、HTTP dispatch `0`、credential
resolution `0`、post-dispatch outcome unknown `0`、same-request retry `0`；DeepSeek 均在网络前被 weekday pricing window 拒绝。开发 Agent
随后把 online successor 写成“唯一阻塞”并结束任务，尽管 PDR-014 已规定 Provider/network failure 不停止开发。

这说明“不得停工”的文字没有定义下一次自动动作。执行器把“当前运行不能继续”和“整个开发任务必须等待”混为一体，造成没有产品完成、
没有真实 scope/safety blocker 时仍结束开发。

## Evidence

- run-006 terminal digest：`sha256:f1baf51596e6c7eb457c5d8a529b050f096ca85decf4e90581cd655be5bb72e6`；
- run-007 terminal digest：`sha256:25a3cfdae455cf286fa5bee53347fb505a0d358a0812a7582cf3b1f9ffa7f27e`；
- 两次合计 6 个 Ark logical dispatch attempt、6 个 pre-HTTP TLS failure、0 个 HTTP dispatch、0 个 outcome-unknown、0 个 same-request retry；
- 两次 DeepSeek admission 都在网络和凭据前 `DENIED_PRICING_CHECK`，不构成 Provider 调用或产品证据；
- branch `codex/iter-010-capability-alpha` 在 `14d6ebe` 结束时 Phase C successor、same-Agent ablation 与 Phase D 仍未完成。

## Root cause

分类为 **iteration-design / systemic**。PDR-014 正确区分了产品失败和 Provider 失败，却缺少可执行的时间调度、fresh logical-run identity、
取消条件和“没有本地工作时仍保持活动”的规则。因而执行者可以用一份失败回执证明诚实，却没有被要求产生下一次恢复动作。

## Disposition

对于有受信证据证明 HTTP/model dispatch 尚未发生、结果不可能未知的首选路线失败，自动调度新的 logical run：首次 5 分钟、再次 15 分钟、
之后每 30 分钟，直至首选路线恢复或出现允许停止的真实边界。每次都使用新的 run/request identity 和 runtime record；同一 request 的 retry/
replay 始终为 0，post-dispatch outcome unknown 仍不得重放。

计时期间继续所有不依赖 Provider 的实现、测试、证据审计和浏览器准备；若这些工作已穷尽，开发任务进入带下一次唤醒时间的 active retry
状态，而不是 Final、Pause 或 Waiting-for-user。到达备用路线允许窗口时，新的 logical run 仍先执行首选路线；只有本次形成可信不可用结论
才透明使用备用。既有 standing authority 覆盖这些 successor，不重复申请人工授权。
