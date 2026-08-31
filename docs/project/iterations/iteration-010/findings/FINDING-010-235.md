---
id: FINDING-010-235
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [operations, quality, project]
depends_on: [FINDING-010-234, ITER-010-PDR-007, ITER-010-PDR-012, ITER-010-VERIFICATION, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: individual-case
disposition: record-ark-traffic-recovery-six-completed-calls-followed-by-bounded-format-repair-outcome-unknown-with-no-local-contract-change
target: ITER-010-VERIFICATION
---

# FINDING-010-235：run-106 证明 Ark 流量恢复，格式修复调用远端断连

## Observation and execution evidence

用户报告“Ark 流量问题已处理”后，validated Engineering Chat launcher 在 current product commit/tree
`d779cb836add5af4fde7efb2a742caed74714c4b / 4a721abf54827637fc2f788c2362f3947c7f5681` 上启动
`run-106-mvp-experience`。Browser 于 `2026-08-31T08:18:38Z` fresh 读取 DeepSeek 官方 pricing page；visible-text digest 仍为
`sha256:9c9dd4d22764599ade403c0ba6cd95abcb947810d5230ee95cb96a56a62d7668`。session preparation 位于周一
`16:21 CST`，DeepSeek preparation receipt 为 `DENIED_PEAK_WINDOW`，未解析 credential、未建 TLS、未发 HTTP。

本次实际执行两个 Turn：

- Q1 的 Ark preferred route 连续完成 6 个 verified TLS/credential/HTTP call，证明 run-105 的 AccountQuotaExceeded 流量阻塞已经越过。
  前 5 个 call 完成 World Model/Source 调查；第 6 个 Primary output 也由 Ark 完整返回，但末尾只关闭了嵌套 Draft object，缺少顶层 JSON
  object 的最后一个 `}`。Application 将其准确分类为
  `STRUCTURED_OUTPUT_INVALID / JSON_SYNTAX_ERROR`（character 8512，`Expecting ',' delimiter`），并在同一 Ark profile 创建 fresh、零 retry 的
  bounded format-repair call。第 7 个 call 在 verified TLS、credential 与 HTTP dispatch 之后由 transport 密封
  `REMOTE_DISCONNECTED / PROVIDER_OUTCOME_UNKNOWN`，因此 Turn 按 `AGENT_MODEL_OUTCOME_UNKNOWN` 失败关闭。该 unknown 没有可信
  unavailable verdict，DeepSeek dispatch 保持 0，避免 ambiguous outcome 下的重复执行；
- Q4 在 fresh Conversation 中形成
  `SUCCEEDED / APPLICATION_INPUT_CLARIFICATION / Provider dispatch 0`，旧 Context/消息没有进入新 Conversation。

Q2/Q3/Q5 没有在已经出现 post-dispatch unknown 的同一 Session 中继续发送。terminal 为 `STOPPED_AFTER_DISPATCH`，2 Turn / 2 Conversation /
7 dispatch；Ark 6 completed、1 outcome unknown，DeepSeek 0 dispatch，request retry、人工审批与 Production 均为 0。terminal、preparation、
session runtime、public-source session authority、Ark runtime、DeepSeek runtime 与 shared logical-Turn budget digest 分别为：

- `sha256:25379701dee6d5a35271bdba8c23f6821b29bda8b4bc4febf912cecd8b10c61c`
- `sha256:02bf8601c907bea5641f6b8b01609114676a776d2547fb6689dae069653e462b`
- `sha256:c747c6fa325d58162cde99be61753b8142e9b8eec7d254e98fccb1c377f78272`
- `sha256:1ba00e6c4cf13d90ce0ef386bca6d13c8f1754a68251caefde55c95f6c5f3e2d`
- `sha256:342614c46af78b6aa113d6c80704830390f48cf8dcdb1af304be0a79dd3a2ad2`
- `sha256:97be52f10b65a59015e4e89fd69a9a9fd389b5f84d3974fc05cc24de1962fc3d`
- `sha256:174deb461f83181c8d2971b0109c2b6f5b2b2b1207a183d42ca6a186ffc92c10`

session、turn scope、pricing capture、launch、terminal、Ark DB 与 DeepSeek DB file SHA-256 分别为
`04b2ec49446228edd33280b2385304bfb4520f8a6b0848459a1c5bb84cf4241a`、
`da96ef2a76078623da6685569dca990dee2180567a082987c3f0e53f8b6d6d3a`、
`6d2792a6dd4c86f6a3b2712b86bf945493c64a92fe680e97494ca3558e853b66`、
`92596353d621efb94494b039247f6218bee4a352a9244db86a7396e4fa734369`、
`ea31ba57829633044060b789f28d7e3436de487442f095eb6db259e68ca28596`、
`108046b07e6865bac6068f3adb9c34ae40868754189a57ecef0ef50785e4ec0d` 与
`0f539b3df4c6127e4b2a90005b287ed8e49b3701f314994f6d1ce8e79dd6672c`。

## Decision and disposition

1. run-106 以 6 个 completed Ark call 证明用户报告的流量恢复已经作用于真实 preferred route；它不再是 run-105 的 sealed 429 signature。
2. 第 6 个 output 的 JSON syntax defect 已由既有 closed-output validator 精确阻断，并创建 current Contract 允许的 fresh same-profile repair；第 7 个
   call 的 post-dispatch outcome unknown 又按 no-retry/no-fallback contract 失败关闭。没有证据表明本地 schema、repair、route 或 Browser 实现
   偏离 current Contract，因此本 Finding 不修改产品代码或 System Contract。
3. 未获 Delivery/Review 的第 6 个 Draft 不构成答案质量 PASS，也不能把其未交付内容当作 current product answer。run-103 仍是最近完整五问
   quality verdict，current `@30/@20/@24` 仍待 live qualification。
4. 下一 fresh run-107 先执行未重复的 Q2/Q3/Q4/Q5，以异质问题验证 Ark 稳定性与 current candidate；仅在没有重复 unknown/availability stop
   signature 时再执行 Q1。Source、五个冻结问题、披露、shared budget、route、fallback 与 Production 边界均不改变，也不需要重复人工授权。
