---
id: FINDING-010-219
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [ai, operations, quality]
depends_on: [FINDING-010-218, ITER-010-PDR-012, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-ARCH-FLOWS, SYS-OPS-CONFIGURATION]
code: [src/software_world_model/ai_infrastructure/deepseek_chat_adapter.py]
tests: [tests/test_deepseek_chat_adapter.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: rotate-stale-or-idle-deepseek-session-before-dispatch
target: SYS-CONTRACT-AI-MODEL-GATEWAY
---

# FINDING-010-219：run-095 暴露 DeepSeek 闲置 keep-alive 在下一 Turn 首次 HTTP 时失效

## Observation and execution evidence

`FINDING-010-218` successor 已提交为 product commit
`f82041fdda060e17834ccc95eda2eb445ef6f4ef`。validated launcher 完成
`run-095-mvp-experience` 的 4 个隔离 Conversation、5 个冻结 Turn，terminal 状态为
`STOPPED_AFTER_DISPATCH`。terminal/session-runtime/public-source authority digest 分别为
`sha256:4171225d06b12cd4d74571d8b179c7302d7e90c90c59d37eb1fce227c7dc67b0`、
`sha256:db5eb2a1a863b8776db0281ef303df3c81300b1cb84350f19a8fa00873b04a4c`、
`sha256:5fff2f819f25b047b92f4ec8a683fe0c4c8e139fb4c2ab8e49e9ce37c216ca58`。

Ark 的 4 个真实 dispatch 全部形成 sealed `429 / AccountQuotaExceeded`，每个非 Clarification
Turn 都合法激活既定 DeepSeek fallback。DeepSeek 28 个 dispatch 中 27 个完成、1 个为
`REMOTE_DISCONNECTED / PROVIDER_OUTCOME_UNKNOWN`；各 Turn 总 dispatch 为
`11 / 2 / 7 / 0 / 12`，retry、人工审批和 Production Activation 均为 0。Q1 与 Q5
取得 `SUCCEEDED / ACCEPTED`，Q4 为零 dispatch Clarification；Q2 按 unknown no-retry
失败，Q3 因独立 Reviewer 拒绝而失败。

turn-scope/pricing-capture/session/launch/terminal/Ark DB/DeepSeek DB 文件 SHA-256 分别为：

- `25894dcc9ddb89837a683a293603705c61c6ea21e348a53bbb5f21a5c9cf6920`
- `9818914fe5e05e675b827cdfaaae3f38e3cbf1979285fff63616c05cccc42ade`
- `6bd1495952f4ffbf46c32025329e88c416142e799684418fc4f1192dde4452db`
- `94f0104db7046fcfc60b1b2de09751d7869130b22bc802bedca4a309fe35d8fa`
- `71f010fb346a64c742b52456598d788de59ad0ad2a959d6e8302a6015e2ba516`
- `392cb7d6a3f6c3ac54c29a9906e515280f806c1c5c34b19efe347cf6569c651e`
- `3e8e180cb4d82b1c4c3a3eed844df76a5e9ffe65742c6121fcc7cccf4810db89`

## Exact first divergence

Q1 的最后一个 DeepSeek call 在 `2026-08-30T19:34:36.733397Z` 完成；Q2 的首个
DeepSeek call 在 `19:36:57.688798Z` 创建，并于约 2 ms 后直接成为
`OUTCOME_UNKNOWN`。其 PREPARED、DISPATCHED 与 OUTCOME_UNKNOWN revision 几乎同时发生，
没有 Provider response。terminal audit 为 28 次 HTTP、2 次 TLS、connection reuse 26、
post-dispatch `REMOTE_DISCONNECTED` 1、retry 0。也就是说，旧 transport 在约 141 秒的浏览器
交互间隔后继续复用已由对端关闭、但本地尚未观察到 EOF 的 keep-alive；旧“每条 session 最多
20 dispatch”只限制计数，不能保证闲置连接仍可用。run-094 在相近 connection lifetime 上出现过
同型失败，因此属于 transport lifetime 的系统性缺口，不是 Q2、模型输出或 Ark fallback 缺口。

## Decision and disposition

这是 `system-contract / systemic` Finding，不按问题、等待时长样本或 Provider 响应内容特判。

1. fully consumed HTTP response 后用进程内 monotonic clock 记录最后完成时刻。下一次 credential
   resolution 或 HTTP dispatch 前，如果连接已闲置至少 60 秒，则先关闭连接；clock 回退失败关闭。
2. 下一次 dispatch 前对 fully consumed persistent socket 做 non-blocking readiness probe。可读、
   exceptional 或 probe 失败都表示连接不再是可信 idle session，先关闭再 acquisition；尚未可读才可复用。
3. stale/idle rotation 是 credential-free pre-dispatch acquisition，仍受 transport lifetime 最多 3 次
   TLS handshake 和每条 session 最多 20 dispatch 约束。credential 仍只在 verified TLS 后解析，HTTP
   一旦开始后的失败仍密封 outcome unknown，绝不 replay/retry。
4. `PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@2` 与 Session audit `@2` 的既有最大值和字段均不变；
   exact Adapter bytes 已变化，因此旧 DeepSeek Conformance 不可复用，fresh Conformance 与 run-096
   才能验证真实链。socket-pair stale detection、60 秒 idle rotation、stale probe rotation 与 audit
   回归均已加入；相邻十七模块 `255/255` targeted tests PASS。

该变化细化既有 DeepSeek Adapter owner，不改变 route、Provider、预算、披露、admission 或 Product
职责，故不需要新 ADR。本 Finding 与同步后的 `SYS-CONTRACT-AI-MODEL-GATEWAY`、
`SYS-ARCH-FLOWS`、`SYS-OPS-CONFIGURATION` 是 current system write-back。
