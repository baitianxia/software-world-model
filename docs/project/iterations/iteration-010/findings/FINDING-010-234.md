---
id: FINDING-010-234
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [operations, quality, project]
depends_on: [FINDING-010-233, ITER-010-PDR-007, ITER-010-PDR-012, ITER-010-VERIFICATION]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: individual-case
disposition: record-user-triggered-ark-first-recheck-as-provider-availability-only-with-no-product-quality-verdict
target: ITER-010-VERIFICATION
---

# FINDING-010-234：run-105 Ark-first recheck 仍为 429，DeepSeek 峰时零 dispatch

## Observation and execution evidence

用户明确要求“使用 Ark 继续”后，validated Engineering Chat launcher 在 current product commit/tree
`d2c5b10649979a881cc3c7f3ce58cebfa11b3e1c / 5cad6041484998251b882cdfbdd8079ce825c6a0` 上启动
`run-105-mvp-experience`。第一次本地启动因新 session file mode 为 `0644` 被 owner-private canonical-file check 在 listener、Source、credential
和 Provider 前拒绝；将文件模式收紧为与既有 artifact 相同的 `0600` 后，第二次启动成功。该本地准备错误没有外部 effect，也不改变产品或
Provider verdict。

Browser 于 `2026-08-31T07:59:11Z` fresh 读取 DeepSeek 官方 pricing page；visible-text digest 仍为
`sha256:9c9dd4d22764599ade403c0ba6cd95abcb947810d5230ee95cb96a56a62d7668`。session preparation 位于周一
`16:01 CST`，DeepSeek 因 `MONDAY-FRIDAY 06:00-10:00 UTC` peak window 密封 `DENIED_PEAK_WINDOW`，未解析 credential、未建 TLS、未发 HTTP。

本次按 Ark-first 与同签名停止边界执行两个 Turn：

- Q1：Ark 真实发出 1 个 request，TLS、credential 与 HTTP 均为 1；Gateway 密封 `HTTP 429 / AccountQuotaExceeded /
  TooManyRequests`。随后 DeepSeek first-preflight 在 `2026-08-31T08:02:55.423473Z` 以 receipt
  `sha256:9f7d6427c8bebba0f4b162556aaf687ac646a37d898a94baf6250c527d84521b` 于网络前拒绝，Turn 为
  `FAILED / AGENT_PRE_DISPATCH_REJECTED / Provider dispatch 1`；
- Q4：fresh Conversation 的省略指代形成
  `SUCCEEDED / APPLICATION_INPUT_CLARIFICATION / Provider dispatch 0`，旧 Context/消息未进入新 Conversation。

Q2/Q3/Q5 在同一 Ark 429 + DeepSeek peak-denial signature 下未发送。terminal 为 `STOPPED_AFTER_DISPATCH`，2 Turn / 2 Conversation /
1 dispatch；Ark 0 completed、1 failed，DeepSeek 0 dispatch，retry、人工审批、post-dispatch unknown 与 Production 均为 0。terminal、preparation、
session runtime、public-source session authority、Ark runtime、DeepSeek runtime 与 shared logical-Turn budget digest 分别为：

- `sha256:2149c098daff4084b9456c5dc3150118830924b2c327ef4c7f14d5bb5dd93276`
- `sha256:23922a32db129c8c4b893ed7eb259b3371ee4b50a56b8b04c6369f50a9012e86`
- `sha256:283132c9f6e4ee4be9d086f4a1da9a6638588ab33ac8113e4fa2dda81598bfeb`
- `sha256:7d335397833fd7540b832f71ec5aa14084689890ce40f1ed260a1b66de095d1f`
- `sha256:210af7deef0675236af0bdf17e2ad271bedcd74093d01c1a618306009f302d8f`
- `sha256:e15f5eed53c4d6e326ce52de909799f78b4369f3ef101ace69730581c55a68d7`
- `sha256:e5b1b90115dd62136301801ed59eeee159ac0d4b221b828863b62bb40e2c42c6`

session、turn scope、pricing capture、launch、terminal、Ark DB 与 DeepSeek DB file SHA-256 分别为
`4eca03adc3ced03899ab4406685a0371633c018e517f73282b33e2ed3d78b6d4`、
`2b0f2fbf11a1ea2ee44706da48dde5428226165ea7fa1d401ed509692969bb86`、
`47773f88b17f23a20717cbfc14c63bb6f2b364d0624ff1ee9b7077e9a090838d`、
`e2282341f63e1c4bbbdb165930561588e25b5f3fb7b0b5eedda28c057b27276a`、
`c61eac6912da0f9e77faff9050c68eefe55db3dcee9b4f9fca7166ed44ebaded`、
`c4519647366e8e0d1c9bae08384416154f956bdb7a7c010f291c3f95cfe29ac8` 与
`0f539b3df4c6127e4b2a90005b287ed8e49b3701f314994f6d1ce8e79dd6672c`。

## Decision and disposition

1. run-105 证明 Ark 在本次 fresh request 上仍不可用；它不是“因 Ark 不可用而不允许使用 DeepSeek”，而是 DeepSeek 在当前 weekday peak
   按现行 PDR-007 于网络前拒绝。两条 route 都按各自规则正确执行。
2. Q1 没有任何 Provider-completed model output，故 current `@30/@20/@24` 未取得 live quality evidence；不得据此修改 Prompt、Review、Source、
   route 或预算，也不得把 Q4 的隔离 PASS 补偿为产品质量 PASS。
3. 用户触发的本次 Ark recheck 已完成。新的同签名 Ark dispatch 仍须 materially new Ark availability evidence；同一 standing scope 下取得该
   evidence 后可以直接继续，不需要重复人工授权。
4. 本 Finding 只更新 current verification/execution truth，不改变 System Contract、standing authority、fallback eligibility、DeepSeek
   schedule、retry 或 Production contracts。
