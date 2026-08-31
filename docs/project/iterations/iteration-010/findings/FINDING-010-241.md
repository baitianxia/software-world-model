---
id: FINDING-010-241
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [ai, operations, quality]
depends_on: [FINDING-010-238, FINDING-010-240, ITER-010-VERIFICATION]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: individual-case
disposition: record-run-108-post-dispatch-unknown-and-zero-dispatch-isolation-without-retry-or-fallback
target: ITER-010-VERIFICATION
---

# FINDING-010-241：run-108 越过旧 Ark 参数拒绝后在 HTTP dispatch 后结果未知

## Observation and evidence

run-108 绑定 clean product `556a9a8695b3a0ad3c69d3eda0b3c2eceb8cc972 / ccc9f64444b97eddc99367ee615de54e787634b5`、
fresh Ark `glm-5.3/@9` Conformance result
`sha256:5cc4d3662573c06dd1ad174121c4c9a9565ae4743805d51b120ea502415a2363` 和 exact 五问 Turn scope
`74590929343dbeb4840bacba2c4ac15938c663e38da10896a743962aa4df4950`。Session file/runtime receipt digests 分别为
`sha256:a41e2b11f0f15984f9048c4444aa9332ab4f893810565f5df495a96dd6f40e37` 与
`sha256:9237d9c739d6e9fdfc8a18932ffd5214f43f6b876baacfdd8818801b6a6cdd53`；人工审批请求和 Production activation 均为 0。

按 run-107 后冻结的执行顺序，Browser 首先发送 Q5（后台用户角色重分配）到 Conversation
`conversation_3dc862ab6a9943be8423dbbbbf4025a4`。Ark model call
`model_call_4f5cc5a9b4ec4c73911d6850d0196eee` 使用 requested alias `glm-5-2-260617`、Adapter
`openai-chat-completions-no-tools@9`，持久化状态依次为 `PREPARED → DISPATCHED → OUTCOME_UNKNOWN`。transport 收据证明 TLS
attempt/success、credential resolution/success 和 HTTP dispatch 均为 `1/1`；HTTP dispatch 后收到 `REMOTE_DISCONNECTED`，因此安全 failure
为 `PROVIDER_OUTCOME_UNKNOWN`。没有安全可确认的 Provider request ID、actual fingerprint、usage 或 output，request retry 为 0。

该证据证明旧 `thinking` field 引起的 HTTP 400 client rejection 已不再是最早偏差，因为 `@9` request 已越过 Provider HTTP dispatch；它不证明
Provider 已完成或拒绝处理。post-dispatch outcome unknown 不是 trusted unavailable，不能在可能重复处理/计费的情况下 retry，也不能据此激活
DeepSeek fallback。DeepSeek preparation admission 在周一 `19:23 CST` 为 `ALLOWED_OFF_PEAK`，但 activation=false，credential/TLS/HTTP/
dispatch 均为 0。

随后在 fresh Conversation `conversation_f1ffdc3a1a3e473e9412d8074901b196` 执行 Q4 省略指代 probe“这些失败也会回滚吗？”。Application
以零 Provider dispatch 返回 `APPLICATION_INPUT_CLARIFICATION`，说明当前新对话没有可解析的先行对象并要求明确组件、流程或请求；新 Conversation
隔离继续通过。最终 terminal receipt
`sha256:a093618c256b06d676aaf245e39f6bbe93be61f8b96e0e8e740aaf67e171ea61` 密封 2 Conversation、2 Turn、Ark 1、DeepSeek 0、retry 0、
human approval 0 和 Production `NOT_EXECUTED`。

fresh official-pricing Browser capture checked at `2026-08-31T11:15:40Z`，visible-text digest 仍为
`sha256:9c9dd4d22764599ade403c0ba6cd95abcb947810d5230ee95cb96a56a62d7668`，capture file SHA-256 为
`190a8f964485e9f9859d11c30596be4f5600f306e0f0f5b76f8433c84ae11867`。launch internal/file digests 为
`sha256:b3490b10f66d25f0784c7150041b49218e92ff69d27917b82202a9c8f724862a` /
`ef68d18ace00eda3db80e7c72134ade4ab415fa54991032381f1ef19d5778ff9`；terminal file SHA-256 为
`3bb7eee6375d51ce7391f5fe6af51957668cfa6797eab00b475c134a33301c96`。final Ark/DeepSeek Gateway DB file SHA-256 分别为
`717c007389b3224918228d39d24aaeaed3e153c42a3e3ed15e71c36ab5ede750` 与
`e951c232a7d6ed051340cc5c530fac95e52102bd12a024363fad1e8a340af239`；Provider runtime 与 shared logical-Turn budget digests 分别为
`sha256:f10f632b2ee122445f92d86db74ea7a332471c195626b72eb53e89882ab105db`、
`sha256:070562d0cd7f5d00aadfe77d32295368f4434b90fd9b816a2a147d2be5f45c97` 与
`sha256:e84960c44f89255778a518e044a1dbc873767535eb3edcb23d3c8966f8b0c8a6`。

在 final Session 前有两个本地 preparation failure：一处 cognition Snapshot ID 输入错误在 Provider dispatch 前以 `INVALID_ARGUMENT` 关闭；
一次 listener bind 受 sandbox 拒绝且 Provider dispatch 0。失败数据库的 model root 均为 0，证据已保留且没有覆盖为成功记录。

## Decision and disposition

1. run-108 如实封存为 Q5 post-dispatch outcome unknown 加 Q4 zero-dispatch isolation PASS；它不是五问完整执行，也不产生答案质量、MVP 或方向 verdict。
2. 不把 outcome unknown 重分类为 unavailable，不 retry，不发送 DeepSeek。这样同时遵守用户“仅在 Ark 可信不可用时”授权和现有 duplicate-cost/no-retry
   contract。
3. 本次没有可归因的本地 product contract 偏差，也没有安全的 model output 可用于 Draft/Review 修复。Q1—Q3 与 fresh Q5 successor 的外部执行等待
   materially new Ark network evidence；这只关闭当前重复风险，不停止同 standing scope 的本地开发与证据工作。
