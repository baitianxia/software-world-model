---
id: FINDING-010-124
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, source, ai, security, interface, operations, quality, project]
depends_on: [FINDING-010-123, SYS-ADR-018, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: systemic
disposition: preserve-fifth-live-one-of-five-limitation-and-isolated-new-conversation-pass
target: ITER-010-VERIFICATION
---

# FINDING-010-124：第五次真实五轮 Chat 仍只有 1/5 受限响应，新对话泄漏负测通过

## Authority and artifact preparation

在 `FINDING-010-123` 双资格均 PASS 后，同一用户授权被收窄为 exact product
`34d98ae12fe7429afb3cbe391d273c59a71c4758` / tree `b9100b15a2db30da811157549fc1f2d9affff288`、
`mall@0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` / tree `047d79d8588b76013c260f3f1a9565707301a60a` 的
owner-private Session。Session authorization digest 是本地密封的 exact user-message UTF-8 digest
`sha256:6834f6854008a41355d5dacff7c7aaad6edb56c9e915f9097ad14c82f5447ce4`。

第一次本地 `run-039-chat-alpha` preparation 使用了非 canonical Binding ID，fixed launcher 在 listener、credential、Source read 与 Provider
dispatch 前以 `AUTHORITY_RECORD_INCONSISTENT` 拒绝。该 failed local preparation 只留下 `0600` config 与两个 `0600`、81920-byte Gateway
文件，不是 live attempt，也没有消费外部调用。published World Model projection 已密封的 canonical Binding
`binding_4ef0d3446b3e44c79ed3c0ffc855d5c9` 随后用于新的 `run-040-chat-alpha`，没有篡改 projection 或放宽校验。

有效 Session config 文件 SHA-256 为 `1cc31c33022e8d335103fe7969fbbb039f33f03d6e9e93dc40ffee37f9f8f70f`；launch/terminal
receipt digest 分别为 `sha256:d18a1d00391fae7c0067ae76c46df1d572dce5b80dfdf1e6ac25bdf1b4ed2663` 与
`sha256:a3a600cd37e9972a1d8d702084fa03832b0a7ac1ef58a16932d39284a48a1e76`。它固定 Ark→DeepSeek、五轮问题、
每 Turn/Provider 15 dispatch、每 Provider 总计 75、同 Provider retry 0，并排除 `src/main/resources`、credential values、hidden、
Slice2/3 和 Production Activation。

## Five-Turn execution and leakage probe

固定五轮在同一 `conversation_cb04747a84834800aa28c28ce294175e` 中得到：

| Turn | 固定问题 | 终态 | logical Provider dispatch |
|---|---|---|---:|
| 1 | 登录流程是怎样的？ | `FAILED / AGENT_PROTOCOL_VIOLATION` | 11 |
| 2 | 它失败时会记录什么？ | `SUCCEEDED / REVIEWED_LIMITATION` | 8 |
| 3 | 我指的是认证失败，不是权限不足。 | `FAILED / AGENT_MODEL_CALL_REJECTED` | 2 |
| 4 | 那 401 和 403 分别由谁产生？ | `FAILED / AGENT_MODEL_OUTCOME_UNKNOWN` | 5 |
| 5 | 总结一下，只保留用户能看到的流程。 | `FAILED / AGENT_MODEL_CALL_REJECTED` | 2 |

Turn 2 只交付了受当前证据边界约束的说明：已找到 `/admin/login` 的用户名或密码错误用户响应，但在本次受限 Source 证据中没有确认认证失败
日志。它是诚实且经 fresh Review/Delivery 的 Limitation，不是五轮所需的登录流程答案。因此主 Chat/Quality 仍为 `FAIL / blocking`，不能把
一个技术成功 Turn 记为 canary PASS。旧 Conversation 最终 revision 6，Context digest 为
`sha256:f38af061077aa5b57fe04d0df11860bc3716d200d78eb857354bcc424b5fff19`。

随后新建 `conversation_9091299573824dffb454ce577395e842`：初始 revision 1、`EMPTY CONTEXT`，Context digest
`sha256:b25b423405dd37c6475dfbcee1927ecf86990eff5d106d1c4b97745faf1ac782`。“它呢？”以
`SUCCEEDED / APPLICATION_INPUT_CLARIFICATION / Provider dispatch 0` 要求用户明确对象；没有继承旧 Conversation 的 referent、消息或
Work State，泄漏负测为 PASS。

terminal receipt `sha256:a3a600cd37e9972a1d8d702084fa03832b0a7ac1ef58a16932d39284a48a1e76` 密封 2 Conversation、
6 Turn、28 logical dispatch、request retry 0 和 Production Activation `NOT_EXECUTED`；文件 SHA-256 为
`f49644dd5fa1cdbc43b6914f09e7298f09df954b5a1236923b6613c582940d17`。Ark 13 logical dispatch 中 10 次到达 HTTP，3 次为
credential-free pre-dispatch TLS failure；DeepSeek 15 次全部到达 HTTP，1 次 post-dispatch remote disconnect/outcome unknown，均未重试。
所有 artifact 文件为 `0600`，Browser console 无 warning/error，listener 已正常停止且端口关闭。

## Earliest deviation and disposition

- Turn 1 的 Reviewer 已明确要求补充证据，但 successor Primary input 仍允许普通 Draft，模型只重写同一缺证结论；Application 的现有
  observation-prefix validator 正确失败关闭。
- Turn 3 与 Turn 5 的 DeepSeek fallback 把 previous Work State 中属于先前 Turn 的 Observation IDs 复制到 current Turn；current Turn 没有
  对应 observations，decoder 正确拒绝 sealed Context/Observation prefix drift。
- Turn 5 Ark 又给 `WORLD_MODEL_QUERY` 增加未列出的参数；closed action decoder 正确拒绝。修复不能删除这些校验，也不能提高 Agent、Source、
  Review、Provider、retry 或 wall-time fuse。

本次 live 永久保持 `one-of-five reviewed limitation / overall FAIL`，新 Conversation isolation/clarification 保持 PASS。model-facing
Work State reference domain 与 evidence-required Review transition 由 `FINDING-010-125` 处置。该一次性 grant 已消费，不授权 v5
Conformance、artifact/Browser 重跑或 Production Activation。
